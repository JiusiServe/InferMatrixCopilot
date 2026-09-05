"""Remote-CI wiring (the v3_ci unblock): the Buildkite provider client,
the parent-parity monitor extensions (per-job retry, baseline root-cause
comparison, pending-job wait, authoritative reconciliation), and the
phase-4 round orchestrator `run_ci_rounds` — all offline against fakes.

The complete remote_ci pipeline runs live in test_v3_complete_e2e.py; this
file pins the pieces and their contracts."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from infermatrix_copilot.ci.buildkite import BuildkiteCI, BuildkiteError
from infermatrix_copilot.rebase_engine import (ci_loop, debug_patch_policy,
                                               push_to_ci)
from infermatrix_copilot.rebase_engine.ci_loop import (BaselineFailure,
                                                       CIClassifySpec)


# ── BuildkiteCI over an injected request fn ──────────────────────────────────

class Recorder:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls: list[tuple] = []

    def __call__(self, method, url, body=None, raw=False):
        self.calls.append((method, url, body, raw))
        return self.responses.pop(0)


def test_buildkite_create_build_normalizes_and_sends_env():
    rec = Recorder([(201, {"number": 42, "state": "scheduled",
                           "web_url": "https://x/b/42"})])
    bk = BuildkiteCI("tok", "acme org", "pipe/one",
                     build_env={"OPT_IN": "1"}, request=rec)
    b = bk.create_build(branch="dev", commit="c" * 40, message="m",
                        meta_data={"imx_op_id": "op-1"})
    # id is the build NUMBER (the REST-routable identity), not a UUID
    assert b["id"] == "42" and b["web_url"] == "https://x/b/42"
    method, url, body, raw = rec.calls[0]
    assert method == "POST" and url.endswith("/builds") and raw is False
    # org/pipeline are URL-quoted; env carries the adapter's opt-ins
    assert "acme%20org" in url and "pipe%2Fone" in url
    assert body["meta_data"] == {"imx_op_id": "op-1"}
    assert body["env"] == {"OPT_IN": "1"}


def test_buildkite_create_build_error_raises_before_op_created():
    bk = BuildkiteCI("t", "o", "p", request=Recorder([(500, {"m": "boom"})]))
    with pytest.raises(BuildkiteError, match="create_build failed"):
        bk.create_build(branch="b", commit="c", message="m", meta_data={})


def test_buildkite_create_build_branch_filter_override_is_opt_in():
    """Schedule-only orgs (provider build_branches=false) refuse ordinary
    API creates with 422; the documented remedy is the create-body
    override `ignore_pipeline_branch_filters` (write_builds scope only).
    Adapter data opts in (rebase.ci.ignore_branch_filters); the default
    body must NOT carry the override."""
    rec = Recorder([(201, {"number": 7, "state": "scheduled"})])
    bk = BuildkiteCI("t", "o", "p", ignore_branch_filters=True, request=rec)
    bk.create_build(branch="b", commit="c" * 40, message="m", meta_data={})
    assert rec.calls[0][2]["ignore_pipeline_branch_filters"] is True
    rec = Recorder([(201, {"number": 8, "state": "scheduled"})])
    bk = BuildkiteCI("t", "o", "p", request=rec)
    bk.create_build(branch="b", commit="c" * 40, message="m", meta_data={})
    assert "ignore_pipeline_branch_filters" not in rec.calls[0][2]
    # positional-compat: a 5th positional arg is still the request fn
    # (the new option is keyword-only), and defaults leave the flag off
    rec = Recorder([(201, {"number": 9, "state": "scheduled"})])
    bk = BuildkiteCI("t", "o", "p", {"E": "1"}, rec)
    bk.create_build(branch="b", commit="c" * 40, message="m", meta_data={})
    assert rec.calls, "positional request fn was not used"
    assert "ignore_pipeline_branch_filters" not in rec.calls[0][2]


def test_buildkite_create_build_policy_4xx_is_typed_refusal():
    """Live remote_ci launch (2026-08-23): the org disabled provider
    branch builds (schedule-only pipeline) and create_build returned
    HTTP 422 "Branches have been disabled for this pipeline" - which
    crashed the ci step as an unhandled BuildkiteError. Deterministic
    policy 4xx (retrying can never succeed) raises the typed
    BuildCreationRefused; transport-class failures keep raising
    BuildkiteError."""
    from infermatrix_copilot.rebase_engine.ci_loop import (
        BuildCreationRefused,
    )
    bk = BuildkiteCI("t", "o", "p", request=Recorder(
        [(422, {"message": "Branches have been disabled for this "
                           "pipeline"})]))
    with pytest.raises(BuildCreationRefused, match="422"):
        bk.create_build(branch="b", commit="c", message="m", meta_data={})
    # every OTHER failure is operational and stays BuildkiteError: auth
    # (401), authz (403), missing pipeline (404), malformed request
    # (400), non-policy validation 422, rate limit (429), server (500)
    for status, payload in ((400, {"message": "malformed"}),
                            (401, {"message": "bad token"}),
                            (403, {"message": "forbidden"}),
                            (404, {"message": "no such pipeline"}),
                            (422, {"message": "invalid commit"}),
                            # an unrelated "disabled" 422 must NOT earn
                            # the schedule-only guidance
                            (422, {"message": "Pipeline has been "
                                              "disabled"}),
                            (429, {}), (500, {})):
        bk = BuildkiteCI("t", "o", "p",
                         request=Recorder([(status, payload)]))
        with pytest.raises(BuildkiteError):
            bk.create_build(branch="b", commit="c", message="m",
                            meta_data={})


def test_acquire_build_converts_policy_refusal_to_refused_outcome(
        tmp_path):
    """The round loop turns BuildCreationRefused into the structured
    (None, reason) refusal - the same path as a foreign active build -
    so the run terminates `refused` with guidance instead of an
    unhandled-error crash."""
    from infermatrix_copilot.rebase_engine.ci_loop import (
        BuildCreationRefused, _acquire_build,
    )

    class RefusingClient:
        def latest_builds(self, branch, states=None):
            return []

        def builds_for_commit(self, branch, commit):
            return []

        def create_build(self, **kwargs):
            raise BuildCreationRefused("create_build refused: HTTP 422")

        def get_build(self, build_id):
            return {}

    rec, reason = _acquire_build(
        RefusingClient(), tmp_path, run_id="r1", round_idx=0,
        purpose="initial", branch="dev/x", commit="c" * 40, message="m",
        owned_commits=set(), owned_ids=set(), sleep=lambda s: None)
    assert rec is None
    assert "refused build creation" in reason and "schedule" in reason


def test_buildkite_meta_lookup_raises_on_error_never_empty():
    """An API error must NEVER read as 'no matches' — guarded recovery
    would escalate correctly, but silently returning [] could eventually
    hit the re-create refusal with a misleading story."""
    bk = BuildkiteCI("t", "o", "p", request=Recorder([(502, [])]))
    with pytest.raises(BuildkiteError, match="refusing to treat"):
        bk.find_builds_by_meta("imx_op_id", "op-1")
    rec = Recorder([(200, [{"number": 7, "state": "running"}])])
    bk = BuildkiteCI("t", "o", "p", request=rec)
    out = bk.find_builds_by_meta("imx_op_id", "op x")
    assert out[0]["id"] == "7"
    assert "meta_data%5Bimx_op_id%5D=op+x" in rec.calls[0][1]


def test_buildkite_polling_reads_degrade():
    bk = BuildkiteCI("t", "o", "p",
                     request=Recorder([(500, {}), (404, "nope")]))
    assert bk.get_build("9") == {}
    assert bk.get_job_log("9", "j") == ""


def test_buildkite_get_job_log_raw():
    rec = Recorder([(200, "raw log text")])
    bk = BuildkiteCI("t", "o", "p", request=rec)
    assert bk.get_job_log("9", "j 1") == "raw log text"
    method, url, body, raw = rec.calls[0]
    assert url.endswith("/builds/9/jobs/j%201/log.txt") and raw is True


def test_buildkite_retry_job_contract():
    bk = BuildkiteCI("t", "o", "p", request=Recorder([(200, {"id": "new"})]))
    assert bk.retry_job("9", "j") == ("new", True)
    bk = BuildkiteCI("t", "o", "p", request=Recorder([(400, {})]))
    assert bk.retry_job("9", "j") == (None, False)   # type can't retry
    # round-1 review: an API failure is NOT a code failure — mutating-call
    # policy raises so the monitor records the job structurally instead of
    # dispatching a mutation agent
    bk = BuildkiteCI("t", "o", "p", request=Recorder([(500, {})]))
    with pytest.raises(BuildkiteError, match="retry_job failed"):
        bk.retry_job("9", "j")


def test_buildkite_transport_errors_degrade_on_polling_reads():
    """Round-1 review: _urllib_request raises BuildkiteError on transport
    (OSError) failures — polling reads must still degrade, not abort a
    monitor mid-build."""
    def broken(method, url, body=None, raw=False):
        raise BuildkiteError("Buildkite API unreachable: boom")

    bk = BuildkiteCI("t", "o", "p", request=broken)
    assert bk.get_build("9") == {}
    assert bk.get_job_log("9", "j") == ""


def test_src_has_no_python312_only_fstring_quote_reuse():
    """Round-1 review: requires-python is >=3.11, but a same-quote reuse
    inside an f-string expression (PEP 701) only parses on 3.12+ — a
    SyntaxError at import time on 3.11. `ast.parse(feature_version=...)`
    cannot catch this (tokenizer-level), so on 3.12+ scan the token
    stream; on 3.11 (round-2 review: FSTRING_START does not exist there)
    plain compile() flags the defect natively."""
    import sys
    import tokenize
    src_root = Path(__file__).resolve().parents[1] / "src"
    offenders = []
    for path in sorted(src_root.rglob("*.py")):
        if sys.version_info < (3, 12):
            try:
                compile(path.read_bytes(), str(path), "exec")
            except SyntaxError as exc:
                offenders.append(f"{path}:{exc.lineno}")
            continue
        stack: list[str | None] = []
        with open(path, "rb") as fh:
            for tok in tokenize.tokenize(fh.readline):
                if tok.type == tokenize.FSTRING_START:
                    triple = tok.string.endswith(('"""', "'''"))
                    stack.append(None if triple else tok.string[-1])
                elif tok.type == tokenize.FSTRING_END:
                    stack.pop()
                elif tok.type == tokenize.STRING and stack:
                    inner = tok.string.lstrip("rbufRBUF")
                    if inner and any(q == inner[0] for q in stack if q):
                        offenders.append(f"{path}:{tok.start[0]}")
    assert not offenders, (
        "3.12-only f-string quote reuse (breaks python>=3.11): "
        + ", ".join(offenders))


def test_buildkite_list_jobs_fallbacks():
    # the /jobs endpoint can answer with the build OBJECT; only a genuine
    # list (or its embedded jobs) is trusted
    bk = BuildkiteCI("t", "o", "p", request=Recorder(
        [(200, [{"id": "j1"}, "noise", {"id": "j2"}])]))
    assert [j["id"] for j in bk.list_jobs("9")] == ["j1", "j2"]
    bk = BuildkiteCI("t", "o", "p", request=Recorder(
        [(200, {"jobs": [{"id": "j3"}]})]))
    assert [j["id"] for j in bk.list_jobs("9")] == ["j3"]
    bk = BuildkiteCI("t", "o", "p", request=Recorder(
        [(404, {}), (200, {"number": 9, "jobs": [{"id": "j4"}]})]))
    assert [j["id"] for j in bk.list_jobs("9")] == ["j4"]


def test_buildkite_build_lookups():
    rec = Recorder([(200, [{"number": 1, "state": "running"}])])
    bk = BuildkiteCI("t", "o", "p", request=rec)
    assert bk.builds_for_commit("dev", "c" * 40)[0]["id"] == "1"
    assert "branch=dev" in rec.calls[0][1] and "commit=cccc" in rec.calls[0][1]
    rec = Recorder([(200, [{"number": 2, "state": "failed"}])])
    bk = BuildkiteCI("t", "o", "p", request=rec)
    assert bk.latest_builds("main", states=("failed",))[0]["id"] == "2"
    assert "state%5B%5D=failed" in rec.calls[0][1]
    bk = BuildkiteCI("t", "o", "p", request=Recorder([(500, [])]))
    with pytest.raises(BuildkiteError):
        bk.builds_for_commit("dev", "c" * 40)


# ── monitor parity: a scripted poll client ───────────────────────────────────

class ScriptedCI:
    """get_build pops snapshots (last one sticks); everything else is
    scripted per-instance."""

    def __init__(self, snapshots, logs=None, retry_results=None,
                 auth_jobs=None):
        self.snapshots = list(snapshots)
        self.logs = dict(logs or {})
        self.retry_results = list(retry_results or [])
        self.retry_calls: list[tuple] = []
        self.auth_jobs = auth_jobs

    def get_build(self, build_id):
        if len(self.snapshots) > 1:
            return self.snapshots.pop(0)
        return self.snapshots[0]

    def get_job_log(self, build_id, job_id):
        return self.logs.get(job_id, "")

    def list_jobs(self, build_id):
        if self.auth_jobs is not None:
            return list(self.auth_jobs)
        return list(self.snapshots[0].get("jobs") or [])

    def retry_job(self, build_id, job_id):
        self.retry_calls.append((build_id, job_id))
        if self.retry_results:
            return self.retry_results.pop(0)
        return None, True


def _job(name, state, exit_status=0, **kw):
    return {"id": kw.pop("id", name), "name": name, "state": state,
            "exit_status": exit_status, **kw}


def test_monitor_per_job_retry_flaky_recovery():
    """A failed job with retry budget is retried; the retry attempt's green
    run makes the build clean — the original is recorded `retrying`, never
    `failed`."""
    ci = ScriptedCI(
        snapshots=[
            {"state": "failed", "jobs": [_job("Flaky", "failed", 1)]},
            {"state": "passed", "jobs": [
                _job("Flaky", "failed", 1, retried=True),
                _job("Flaky", "passed", 0, id="Flaky-retry")]},
        ],
        logs={"Flaky": "FAILED tests/f.py::test_x - boom"},
        retry_results=[("Flaky-retry", True)])
    out = ci_loop.monitor_build(ci, "b", spec=CIClassifySpec(), poll_sec=0,
                                retry_max=2, sleep=lambda s: None)
    cls = {(j.job_id): j.classification for j in out.jobs}
    assert cls == {"Flaky": "retrying", "Flaky-retry": "passed"}
    assert out.clean_pass
    assert ci.retry_calls == [("b", "Flaky")]


def test_monitor_retry_nonretryable_type_stays_failed():
    """Round-4 review: a failed job whose TYPE the provider refuses to
    retry (HTTP 400) has still failed — the parent's ignored_infra here
    was a false-green vector."""
    ci = ScriptedCI(
        snapshots=[{"state": "failed",
                    "jobs": [_job("Odd Lane", "failed", 1)]}],
        logs={"Odd Lane": "FAILED tests/u.py::t - x"},
        retry_results=[(None, False)])   # provider: this TYPE can't retry
    out = ci_loop.monitor_build(ci, "b", spec=CIClassifySpec(), poll_sec=0,
                                retry_max=1, timeout_sec=0,
                                sleep=lambda s: None)
    assert out.jobs[0].classification == "failed"
    assert not out.clean_pass


def test_monitor_retry_exhausted_stays_failed():
    ci = ScriptedCI(
        snapshots=[
            {"state": "failed", "jobs": [_job("Hard", "failed", 1)]},
            {"state": "failed", "jobs": [
                _job("Hard", "failed", 1, retried=True),
                _job("Hard", "failed", 1, id="Hard-retry")]},
        ],
        logs={"Hard": "FAILED tests/h.py::t - x",
              "Hard-retry": "FAILED tests/h.py::t - x"},
        retry_results=[("Hard-retry", True)])
    out = ci_loop.monitor_build(ci, "b", spec=CIClassifySpec(), poll_sec=0,
                                retry_max=1, sleep=lambda s: None)
    cls = {j.job_id: j.classification for j in out.jobs}
    assert cls == {"Hard": "retrying", "Hard-retry": "failed"}
    assert [j.job_id for j in out.failed_jobs] == ["Hard-retry"]


def test_monitor_unobserved_retry_never_passes():
    """Round-1 review: a retry attempt we requested but never saw again
    must not leave its original as `retrying` — clean_pass would wave the
    build through with unfinished work aboard."""
    ci = ScriptedCI(
        snapshots=[
            {"state": "failed", "jobs": [_job("Ghost", "failed", 1)]},
            # terminal build; the retry job NEVER materializes
            {"state": "failed",
             "jobs": [_job("Ghost", "failed", 1, retried=True)]},
        ],
        logs={"Ghost": "FAILED tests/g.py::t - x"},
        retry_results=[("Ghost-retry", True)])
    out = ci_loop.monitor_build(ci, "b", spec=CIClassifySpec(), poll_sec=0,
                                timeout_sec=0, retry_max=1,
                                sleep=lambda s: None)
    assert out.jobs[0].classification == "incomplete"
    assert not out.clean_pass


def test_monitor_retry_api_error_is_structural():
    """Round-1 review: a retry API failure is neither a pass nor a
    code-debug dispatch — the job lands `incomplete` (structural)."""
    class RaisingRetry(ScriptedCI):
        def retry_job(self, build_id, job_id):
            raise BuildkiteError("retry_job failed: HTTP 500")

    ci = RaisingRetry(
        snapshots=[{"state": "failed", "jobs": [_job("Flap", "failed", 1)]}],
        logs={"Flap": "FAILED tests/f.py::t - x"})
    out = ci_loop.monitor_build(ci, "b", spec=CIClassifySpec(), poll_sec=0,
                                timeout_sec=0, retry_max=2,
                                sleep=lambda s: None)
    assert out.jobs[0].classification == "incomplete"
    assert not out.failed_jobs and not out.clean_pass


def test_monitor_soft_failed_and_broken_are_ignored():
    ci = ScriptedCI(snapshots=[{"state": "passed", "jobs": [
        _job("Soft", "failed", 1, soft_failed=True),
        _job("Broken", "broken"),
        _job("Green", "passed", 0)]}])
    out = ci_loop.monitor_build(ci, "b", spec=CIClassifySpec(), poll_sec=0,
                                sleep=lambda s: None)
    cls = {j.name: j.classification for j in out.jobs}
    assert cls == {"Soft": "ignored", "Broken": "ignored",
                   "Green": "passed"}
    assert out.clean_pass


def test_monitor_waits_for_pending_jobs_in_terminal_build():
    """Build-level state flips terminal while jobs still run (provider
    semantics) — the monitor keeps polling; nothing lands `incomplete`
    when the job finishes inside the budget."""
    ci = ScriptedCI(snapshots=[
        {"state": "failed", "jobs": [_job("Slow", "running")]},
        {"state": "failed", "jobs": [_job("Slow", "passed", 0)]},
    ])
    out = ci_loop.monitor_build(ci, "b", spec=CIClassifySpec(), poll_sec=0,
                                sleep=lambda s: None)
    assert [j.classification for j in out.jobs] == ["passed"]


def test_monitor_reconciliation_catches_missed_jobs():
    """A dynamically-added step never seen by the poll snapshots is
    classified by the authoritative final list — a partial build can never
    read as passed."""
    ci = ScriptedCI(
        snapshots=[{"state": "passed", "jobs": [_job("Seen", "passed")]}],
        logs={"Hidden": "FAILED tests/h.py::t - x"},
        auth_jobs=[_job("Seen", "passed"),
                   _job("Hidden", "failed", 1),
                   _job("NonScript", "failed", 1, type="waiter"),
                   _job("Retried", "failed", 1, retried=True),
                   _job("Hung", "running")])
    out = ci_loop.monitor_build(ci, "b", spec=CIClassifySpec(), poll_sec=0,
                                sleep=lambda s: None)
    cls = {j.name: j.classification for j in out.jobs}
    assert cls == {"Seen": "passed", "Hidden": "failed",
                   "Hung": "incomplete"}
    assert not out.clean_pass


def test_monitor_baseline_same_and_different_root_cause():
    baseline = (BaselineFailure(name="lane a", exit_status=1,
                                job_id="mainA", build_id="mb"),
                BaselineFailure(name="lane b", exit_status=1,
                                job_id="mainB", build_id="mb"))
    ci = ScriptedCI(
        snapshots=[{"state": "failed", "jobs": [
            _job("Lane A", "failed", 1),
            _job("Lane B", "failed", 1)]}],
        logs={"Lane A": "RuntimeError: same boom\n"
                        "FAILED tests/a.py::t - x",
              "mainA": "RuntimeError: same boom\n"
                       "FAILED tests/a.py::t - x",
              "Lane B": "RuntimeError: fresh regression\n"
                        "FAILED tests/b.py::t_new - y",
              "mainB": "RuntimeError: old failure\n"
                       "FAILED tests/b.py::t_old - z"})
    out = ci_loop.monitor_build(ci, "b", spec=CIClassifySpec(
        baseline=baseline), poll_sec=0, timeout_sec=0, sleep=lambda s: None)
    cls = {j.name: j.classification for j in out.jobs}
    # same signature ⇒ pre-existing (ignored_baseline); different ⇒ a REAL
    # new failure even though the same job also fails on the baseline
    assert cls == {"Lane A": "ignored_baseline", "Lane B": "failed"}


def test_monitor_baseline_fails_closed_on_missing_evidence():
    """Round-4 review (deliberate divergence from the parent's lenient
    defaults): missing baseline coordinates, an unavailable baseline log,
    or an empty current signature mean the comparison CANNOT be made —
    the failure stays actionable, never waved through as pre-existing."""
    log = "RuntimeError: boom\nFAILED tests/c.py::t - x"
    # no baseline job/build coordinates
    baseline = (BaselineFailure(name="lane c", exit_status=1),)
    ci = ScriptedCI(snapshots=[{"state": "failed", "jobs": [
        _job("Lane C", "failed", 1)]}], logs={"Lane C": log})
    out = ci_loop.monitor_build(ci, "b", spec=CIClassifySpec(
        baseline=baseline), poll_sec=0, timeout_sec=0, sleep=lambda s: None)
    assert out.jobs[0].classification == "failed"
    # baseline log unavailable (API outage degrades log reads to "")
    baseline = (BaselineFailure(name="lane c", exit_status=1,
                                job_id="mainC", build_id="mb"),)
    ci = ScriptedCI(snapshots=[{"state": "failed", "jobs": [
        _job("Lane C", "failed", 1)]}], logs={"Lane C": log})
    out = ci_loop.monitor_build(ci, "b", spec=CIClassifySpec(
        baseline=baseline), poll_sec=0, timeout_sec=0, sleep=lambda s: None)
    assert out.jobs[0].classification == "failed"
    # empty CURRENT signature: nothing to compare — still actionable
    ci = ScriptedCI(snapshots=[{"state": "failed", "jobs": [
        _job("Lane C", "failed", 1)]}],
        logs={"Lane C": "no recognizable error grammar here",
              "mainC": log})
    out = ci_loop.monitor_build(ci, "b", spec=CIClassifySpec(
        baseline=baseline), poll_sec=0, timeout_sec=0, sleep=lambda s: None)
    assert out.jobs[0].classification == "failed"
    # Exit-status mismatch alone is not failure identity: the same pytest
    # fingerprint may be followed by a teardown timeout on only one side.
    baseline = (BaselineFailure(name="lane c", exit_status=2,
                                job_id="mainC", build_id="mb"),)
    ci = ScriptedCI(snapshots=[{"state": "failed", "jobs": [
        _job("Lane C", "failed", 1)]}],
        logs={"Lane C": log, "mainC": log})
    out = ci_loop.monitor_build(ci, "b", spec=CIClassifySpec(
        baseline=baseline), poll_sec=0, timeout_sec=0, sleep=lambda s: None)
    assert out.jobs[0].classification == "ignored_baseline"
    assert out.jobs[0].baseline_build_id == "mb"
    assert out.jobs[0].baseline_job_id == "mainC"
    assert out.jobs[0].classification_reason


def test_monitor_baseline_matches_cause_checked_error_subset():
    """A current ERROR-only subset matches a noisier baseline job, while a
    new cause on the same node remains actionable."""
    baseline = (BaselineFailure(name="lane", exit_status=1,
                                job_id="main", build_id="mb"),)
    baseline_log = (
        "ValueError: triton is not supported for NvFP4 MoE\n"
        "ERROR tests/nvfp4.py::test_marlin - RuntimeError: init failed\n"
        "AssertionError: audio mismatch\n"
        "FAILED tests/audio.py::test_stream - AssertionError: audio mismatch")
    current = (
        "ValueError: triton is not supported for NvFP4 MoE\n"
        "ERROR tests/nvfp4.py::test_marlin - RuntimeError: init failed")
    ci = ScriptedCI(
        snapshots=[{"state": "failed",
                    "jobs": [_job("Lane", "failed", 1)]}],
        logs={"Lane": current, "main": baseline_log})
    out = ci_loop.monitor_build(ci, "b", spec=CIClassifySpec(
        baseline=baseline), poll_sec=0, timeout_sec=0,
        sleep=lambda s: None)
    assert out.jobs[0].classification == "ignored_baseline"
    assert "subset" in out.jobs[0].classification_reason

    ci.logs["Lane"] = (
        "ValueError: a new regression\n"
        "ERROR tests/nvfp4.py::test_marlin - RuntimeError: different")
    out = ci_loop.monitor_build(ci, "b", spec=CIClassifySpec(
        baseline=baseline), poll_sec=0, timeout_sec=0,
        sleep=lambda s: None)
    assert out.jobs[0].classification == "failed"


def test_monitor_structural_suite_creation_failure_never_ignored():
    """Round-4 review: a failed pipeline upload/load lane suppressed every
    dynamic test job — STRUCTURAL (incomplete), even though its name would
    otherwise be ignorable in the parent; and a build whose only jobs are
    ignored can never pass (zero jobs actually PASSED)."""
    spec = CIClassifySpec(
        ignorable_name_patterns=("(?i)statistics",),
        structural_name_patterns=(r"(?i):pipeline:\s*(upload|load)",))
    ci = ScriptedCI(snapshots=[{"state": "failed", "jobs": [
        _job(":pipeline: upload", "failed", 1),
        _job("Testcase Statistics", "failed", 1)]}])
    out = ci_loop.monitor_build(ci, "b", spec=spec, poll_sec=0,
                                timeout_sec=0, sleep=lambda s: None)
    cls = {j.name: j.classification for j in out.jobs}
    assert cls == {":pipeline: upload": "incomplete",
                   "Testcase Statistics": "ignored"}
    assert not out.clean_pass
    # a PASSED upload lane stays unremarkable (passed)
    ci = ScriptedCI(snapshots=[{"state": "passed", "jobs": [
        _job(":pipeline: upload", "passed", 0),
        _job("Real Test", "passed", 0)]}])
    out = ci_loop.monitor_build(ci, "b", spec=spec, poll_sec=0,
                                sleep=lambda s: None)
    assert out.clean_pass
    # all-ignored build (nothing actually PASSED) is never clean
    ci = ScriptedCI(snapshots=[{"state": "failed", "jobs": [
        _job("Testcase Statistics", "failed", 1)]}])
    out = ci_loop.monitor_build(ci, "b", spec=spec, poll_sec=0,
                                timeout_sec=0, sleep=lambda s: None)
    assert not out.clean_pass


def test_monitor_pending_ignorable_job_is_incomplete():
    """Round-5 review: an UNFINISHED job is unfinished work even when its
    name would be ignorable once terminal — a pending stats lane at the
    monitor deadline must land `incomplete`, never `ignored`, or one
    passed job would make the build a false clean pass."""
    spec = CIClassifySpec(ignorable_name_patterns=("(?i)statistics",))
    ci = ScriptedCI(snapshots=[{"state": "failed", "jobs": [
        _job("Real Test", "passed", 0),
        _job("Testcase Statistics", "running")]}])
    out = ci_loop.monitor_build(ci, "b", spec=spec, poll_sec=0,
                                timeout_sec=0, sleep=lambda s: None)
    cls = {j.name: j.classification for j in out.jobs}
    assert cls == {"Real Test": "passed",
                   "Testcase Statistics": "incomplete"}
    assert not out.clean_pass


def test_rounds_schedule_build_at_owned_commit_is_foreign(tmp_path):
    """Round-5 review: pushing a commit does not confer ownership of
    every later build at that commit — a schedule/api build another run
    started there is unowned, and the next fix push must refuse rather
    than cancel it. Our own push's WEBHOOK artifact stays exempt."""
    def scripted_rounds(source):
        ci = RoundsCI([
            {"state": "failed", "jobs": [_job("Red", "failed", 1)]},
            {"state": "passed", "jobs": [_job("Red", "passed", 0)]},
        ])
        ci.logs["Red"] = "FAILED tests/r.py::t - x"
        calls = {"n": 0}

        def latest_builds(branch, states=(), per_page=30):
            calls["n"] += 1
            if calls["n"] == 1:
                return []
            # before the round-1 fix push: an active build appeared at
            # the commit round 0 pushed
            return [{"id": "other", "number": 7, "state": "running",
                     "commit": "c" * 40, "source": source}]

        ci.latest_builds = latest_builds

        async def debug(jr):
            return True

        return _rounds(ci, tmp_path / source, changes=[True], debug=debug)

    result, push_calls = scripted_rounds("schedule")
    assert result.result == "refused" and "does not own" in result.reason
    assert push_calls == [0]            # the fix push never happened
    result, push_calls = scripted_rounds("webhook")
    assert result.result == "passed"    # our own artifact never blocks
    assert push_calls == [0, 1]


def test_rounds_adopted_build_id_confers_no_push_ownership(tmp_path):
    """Verification round 1: an adopted build is monitor-only — its id
    must NOT join the ownership set, or a debug-fix push after a
    monitor-timeout would cancel the still-running adopted build."""
    sibling = {"id": "s1", "number": 3, "state": "failed",
               "commit": "c" * 40, "web_url": "u/s1", "source": "api",
               "jobs": [_job("Red", "failed", 1),
                        _job("Hung", "running")]}
    ci = RoundsCI([{"state": "not_run", "jobs": []}], siblings=[sibling])
    ci.logs["Red"] = "FAILED tests/r.py::t - x"
    calls = {"n": 0}

    def latest_builds(branch, states=(), per_page=30):
        calls["n"] += 1
        # round 0 pre-push: nothing active; before the fix push, the
        # adopted build is STILL running (monitor hit its deadline)
        return [] if calls["n"] == 1 else \
            [{"id": "s1", "number": 3, "state": "running",
              "commit": "c" * 40, "source": "api"}]

    ci.latest_builds = latest_builds

    async def debug(jr):
        return True

    result, push_calls = _rounds(ci, tmp_path, changes=[True], debug=debug)
    assert result.result == "refused" and "does not own" in result.reason
    assert push_calls == [0]            # the fix push never happened


def test_rounds_same_commit_full_suite_build_adopted_on_initial(tmp_path):
    """Verification round 1: a schedule/api build that appeared at the
    just-pushed commit during the settle window is ADOPTED on the initial
    round too — creating over it would cancel a build this run does not
    own (only webhook artifacts of our own push are built over)."""
    ci = RoundsCI([])
    ci.siblings = [{"id": "sched1", "number": 4, "state": "passed",
                    "commit": "c" * 40, "source": "schedule",
                    "jobs": [_job("Green", "passed", 0)]}]
    calls = {"n": 0}

    def latest_builds(branch, states=(), per_page=30):
        calls["n"] += 1
        # pre-push scan: quiet; the schedule build appears during the
        # settle window, so the acquire-time scan sees it
        return [] if calls["n"] == 1 else \
            [{"id": "sched1", "number": 4, "state": "running",
              "commit": "c" * 40, "source": "schedule",
              "web_url": "u/sched1"}]

    ci.latest_builds = latest_builds
    result, push_calls = _rounds(ci, tmp_path)
    assert result.result == "passed"
    assert ci.created == 0              # adopted, never created over
    assert [(r.purpose, r.adopted) for r in result.rounds] == \
        [("adopted", True)]
    assert ci_loop.load_ops(tmp_path / "ops") == []


def test_monitor_non_script_jobs_skipped_in_poll_too():
    """Verification round 2: waiter/trigger steps are pipeline plumbing —
    the poll path must skip them exactly like the reconciliation path, or
    an early-observed failed waiter dispatches a debug agent at a
    non-job."""
    ci = ScriptedCI(snapshots=[{"state": "passed", "jobs": [
        _job("Gate", "failed", 1, type="waiter"),
        _job("Real Test", "passed", 0)]}])
    out = ci_loop.monitor_build(ci, "b", spec=CIClassifySpec(), poll_sec=0,
                                sleep=lambda s: None)
    assert [j.name for j in out.jobs] == ["Real Test"]
    assert out.clean_pass and not out.failed_jobs
    # a PENDING non-script job is excluded from the pending-wait count —
    # this call returning promptly (default 4h deadline, no-op sleep) IS
    # the proof the loop never waited on it
    ci = ScriptedCI(snapshots=[{"state": "passed", "jobs": [
        _job("Gate", "waiting", type="waiter"),
        _job("Real Test", "passed", 0)]}])
    out = ci_loop.monitor_build(ci, "b", spec=CIClassifySpec(), poll_sec=0,
                                sleep=lambda s: None)
    assert [j.name for j in out.jobs] == ["Real Test"]
    assert out.clean_pass


def test_rounds_same_commit_manual_build_refuses(tmp_path):
    """Verification round 2: a same-commit UI/manual build is neither
    full-suite evidence (no adoption) nor ours to cancel (no create-over)
    — it refuses like any other unowned active build."""
    ci = RoundsCI([])
    calls = {"n": 0}

    def latest_builds(branch, states=(), per_page=30):
        calls["n"] += 1
        return [] if calls["n"] == 1 else \
            [{"id": "ui1", "number": 5, "state": "running",
              "commit": "c" * 40, "source": "ui"}]

    ci.latest_builds = latest_builds
    result, push_calls = _rounds(ci, tmp_path)
    assert result.result == "refused" and "does not own" in result.reason
    assert ci.created == 0 and push_calls == [0]


def test_rounds_stale_intent_never_approves_new_commit(tmp_path):
    """Verification round 2: a recovered intent whose commit is STALE
    (the checkout advanced since the crash) must not be monitored as this
    round's build — its green result would approve an untested commit.
    The settled build is ours: cancelled if active, then a fresh
    op-recorded build tests the CURRENT commit."""
    from dataclasses import asdict
    intent = ci_loop.BuildOp(op_id="run-1-ci-r0", run_id="run-1",
                             purpose="initial", branch="dev",
                             commit="a" * 40)          # the OLD commit
    ci_loop._durable_write(intent.path(tmp_path / "ops"), asdict(intent))

    class CancelOK(RoundsCI):
        def __init__(self, bodies):
            super().__init__(bodies)
            self.cancelled: list[str] = []

        def cancel_build(self, build_id):
            self.cancelled.append(build_id)
            self.builds[build_id]["state"] = "canceled"
            return self.builds[build_id]

    ci = CancelOK([{"state": "passed",
                    "jobs": [_job("Green", "passed", 0)]}])
    # the crashed create landed: an orphan ACTIVE build at the old commit
    orphan = ci.create_build(branch="dev", commit="a" * 40, message="m",
                             meta_data={"imx_op_id": "run-1-ci-r0"})
    ci.builds[orphan["id"]]["state"] = "running"
    ci.bodies = [{"state": "passed",
                  "jobs": [_job("Green", "passed", 0)]}]
    # this run pushes the NEW commit c*40 (Push default)
    result, push_calls = _rounds(ci, tmp_path)
    assert result.result == "passed"
    assert ci.cancelled == [orphan["id"]]      # the stale build, ours
    ops = {o.op_id: o for o in ci_loop.load_ops(tmp_path / "ops")}
    assert ops["run-1-ci-r0"].state == "cancelled"
    fresh = [o for o in ops.values() if o.op_id != "run-1-ci-r0"]
    assert len(fresh) == 1 and fresh[0].commit == "c" * 40
    assert fresh[0].state == "created"
    # the monitored build is the FRESH one at the new commit
    assert result.rounds[0].build_id == fresh[0].build_id
    assert result.rounds[0].jobs == [{
        "name": "Green", "job_id": "Green", "state": "passed",
        "exit_status": 0, "classification": "passed", "log_file": "",
        "classification_reason": "", "baseline_build_id": "",
        "baseline_job_id": "",
    }]


def test_rounds_active_intent_orphan_is_owned_at_prepush(tmp_path):
    """Extra verification round: an unsettled intent's orphan build is
    OURS even though the intent record carries no build id — the pre-push
    scan must resolve it by op-id metadata instead of refusing as
    foreign, and the settle path then cancels the stale-commit orphan and
    builds the current commit."""
    from dataclasses import asdict
    intent = ci_loop.BuildOp(op_id="run-1-ci-r0", run_id="run-1",
                             purpose="initial", branch="dev",
                             commit="a" * 40)          # the OLD commit
    ci_loop._durable_write(intent.path(tmp_path / "ops"), asdict(intent))

    class CancelOK(RoundsCI):
        def __init__(self, bodies):
            super().__init__(bodies)
            self.cancelled: list[str] = []

        def cancel_build(self, build_id):
            self.cancelled.append(build_id)
            self.builds[build_id]["state"] = "canceled"
            return self.builds[build_id]

    ci = CancelOK([])
    orphan = ci.create_build(branch="dev", commit="a" * 40, message="m",
                             meta_data={"imx_op_id": "run-1-ci-r0"})
    ci.builds[orphan["id"]].update({"state": "running", "source": "api"})
    ci.bodies = [{"state": "passed",
                  "jobs": [_job("Green", "passed", 0)]}]
    # the ACTIVE orphan is visible to every branch scan
    ci.latest_builds = lambda branch, states=(), per_page=30: \
        [ci.builds[orphan["id"]]]
    result, push_calls = _rounds(ci, tmp_path)
    assert result.result == "passed", result.reason   # never refused
    assert push_calls == [1]          # resume: index 0 is ledger-taken
    assert ci.cancelled == [orphan["id"]]             # stale orphan, ours
    ops = {o.op_id: o for o in ci_loop.load_ops(tmp_path / "ops")}
    assert ops["run-1-ci-r0"].state == "cancelled"
    fresh = [o for o in ops.values() if o.op_id != "run-1-ci-r0"]
    assert len(fresh) == 1 and fresh[0].commit == "c" * 40


def test_monitor_clean_pass_guards():
    # zero job signal is never a pass
    ci = ScriptedCI(snapshots=[{"state": "passed", "jobs": []}])
    out = ci_loop.monitor_build(ci, "b", spec=CIClassifySpec(), poll_sec=0,
                                sleep=lambda s: None)
    assert not out.clean_pass
    # a monitor timeout is never a pass, even with all-green visible jobs
    ci = ScriptedCI(snapshots=[{"state": "running",
                                "jobs": [_job("G", "passed", 0)]}])
    out = ci_loop.monitor_build(ci, "b", spec=CIClassifySpec(), poll_sec=0,
                                timeout_sec=0, sleep=lambda s: None)
    assert out.build_state == "monitor_timeout" and not out.clean_pass
    # round-3 review: a CANCELED/blocked build with visible green jobs is
    # never a pass — cancellation may have prevented later dynamic jobs
    # from ever appearing
    for state in ("canceled", "cancelled", "blocked"):
        ci = ScriptedCI(snapshots=[{"state": state,
                                    "jobs": [_job("G", "passed", 0)]}])
        out = ci_loop.monitor_build(ci, "b", spec=CIClassifySpec(),
                                    poll_sec=0, timeout_sec=0,
                                    sleep=lambda s: None)
        assert not out.clean_pass, state
    # ...while a completed build whose only failures are baseline/ignored
    # remains clean (state "failed" with everything explained)
    ci = ScriptedCI(snapshots=[{"state": "failed", "jobs": [
        _job("G", "passed", 0),
        _job("Testcase Statistics", "failed", 1)]}])
    out = ci_loop.monitor_build(ci, "b", spec=CIClassifySpec(
        ignorable_name_patterns=("(?i)statistics",)), poll_sec=0,
        timeout_sec=0, sleep=lambda s: None)
    assert out.clean_pass


def test_pick_best_build_and_baseline_fetch():
    builds = [
        {"id": "5", "number": 5, "state": "failed", "source": "webhook"},
        {"id": "4", "number": 4, "state": "failed", "source": "api"},
        {"id": "3", "number": 3, "state": "failed", "source": "schedule"},
    ]
    assert ci_loop.pick_best_build(builds)["id"] == "3"   # schedule wins
    assert ci_loop.pick_best_build([]) is None

    class BaselineClient:
        def __init__(self, builds):
            self.builds = builds

        def latest_builds(self, branch, states=(), per_page=30):
            # round-4 review: COMPLETED builds, not failed-only — a stale
            # failed build must not outlive a newer green baseline run
            assert states == ("passed", "failed")
            return self.builds

        def list_jobs(self, build_id):
            if build_id == "9":
                return [_job("Lane A", "passed", 0, id="jA9"),
                        _job("Zero Exit", "passed", 0, id="jZ9")]
            assert build_id == "3"
            return [_job("Lane A", "failed", 1, id="jA"),
                    _job("Zero Exit", "failed", 0, id="jZ"),
                    _job("Green", "passed", 0, id="jG"),
                    _job("", "failed", 1, id="jNoName")]

    got = ci_loop.fetch_baseline_failures(BaselineClient(builds), "main")
    assert got == (BaselineFailure("lane a", 1, "jA", "3"),
                   # the parent's `or -1` encoding: exit 0/None ⇒ -1
                   BaselineFailure("zero exit", -1, "jZ", "3"))
    # round-4 review: a NEWER green run on the same trust tier wins — the
    # stale failed build contributes NO baseline (its failures are fixed)
    fresh_green = [
        {"id": "9", "number": 9, "state": "passed", "source": "schedule"},
        {"id": "3", "number": 3, "state": "failed", "source": "schedule"},
    ]
    assert ci_loop.fetch_baseline_failures(
        BaselineClient(fresh_green), "main") == ()

    # A recurring older failure remains valid intermittent-baseline evidence
    # even when the newest same-tier build happens to pass.
    recurring = [
        {"id": "9", "number": 9, "state": "passed", "source": "schedule"},
        {"id": "3", "number": 3, "state": "failed", "source": "schedule"},
        {"id": "2", "number": 2, "state": "failed", "source": "schedule"},
    ]

    class RecurringBaselineClient(BaselineClient):
        def list_jobs(self, build_id):
            if build_id == "9":
                return [_job("Lane A", "passed", 0, id="jA9")]
            return [_job("Lane A", "failed", 1, id=f"jA{build_id}")]

    got = ci_loop.fetch_baseline_failures(
        RecurringBaselineClient(recurring), "main")
    assert got == (
        BaselineFailure("lane a", 1, "jA3", "3"),
        BaselineFailure("lane a", 1, "jA2", "2"),
    )


# ── run_ci_rounds ────────────────────────────────────────────────────────────

class Push:
    def __init__(self, pushed=True, commit="c" * 40, dry_run=False,
                 reason=""):
        self.pushed = pushed
        self.pushed_commit = commit
        self.dry_run = dry_run
        self.reason = reason


class RoundsCI:
    """Guarded-create-capable fake whose created builds pop from a script
    of build bodies."""

    def __init__(self, bodies, active=None, siblings=None):
        self.bodies = list(bodies)     # dicts: state + jobs for each create
        self.builds: dict[str, dict] = {}
        self.active = list(active or [])
        self.siblings = list(siblings or [])
        self.created = 0
        self.logs: dict[str, str] = {}

    def create_build(self, *, branch, commit, message, meta_data):
        self.created += 1
        bid = f"b{self.created}"
        body = self.bodies.pop(0) if self.bodies else {"state": "passed",
                                                       "jobs": []}
        self.builds[bid] = {"id": bid, "web_url": f"u/{bid}",
                            "branch": branch, "commit": commit,
                            "meta_data": dict(meta_data), **body}
        return self.builds[bid]

    def get_build(self, build_id):
        return self.builds.get(build_id) \
            or next((s for s in self.siblings if s["id"] == build_id), {})

    def find_builds_by_meta(self, key, value):
        return [b for b in self.builds.values()
                if b["meta_data"].get(key) == value]

    def cancel_build(self, build_id):
        raise AssertionError("run_ci_rounds must never cancel builds")

    def get_job_log(self, build_id, job_id):
        return self.logs.get(job_id, "")

    def list_jobs(self, build_id):
        return list(self.get_build(build_id).get("jobs") or [])

    def retry_job(self, build_id, job_id):
        return None, True

    def latest_builds(self, branch, states=(), per_page=30):
        return list(self.active)

    def builds_for_commit(self, branch, commit):
        return [s for s in self.siblings if s.get("commit") == commit]


def _run(coro):
    return asyncio.run(coro)


async def _noop_sleep(_s):
    return None


def _rounds(client, tmp_path, *, push_results=None, changes=None,
            debug=None, **kw):
    pushes = list(push_results or [Push()])
    push_calls = []

    def push_fn(rnd):
        push_calls.append(rnd)
        return pushes.pop(0) if pushes else Push()

    changes_iter = iter(changes or [])

    def changes_fn():
        return next(changes_iter, False)

    kw.setdefault("job_retry_max", 0)
    result = _run(ci_loop.run_ci_rounds(
        client=client, ops_dir=tmp_path / "ops", run_id="run-1",
        branch="dev", spec=CIClassifySpec(), push_fn=push_fn,
        changes_fn=changes_fn, debug_fn=debug, settle_sec=0, poll_sec=0,
        timeout_sec=0, sleep=lambda s: None, asleep=_noop_sleep, **kw))
    return result, push_calls


def test_rounds_clean_pass_first_round(tmp_path):
    ci = RoundsCI([{"state": "passed",
                    "jobs": [_job("Green", "passed", 0)]}])
    result, push_calls = _rounds(ci, tmp_path)
    assert result.result == "passed" and push_calls == [0]
    # the build went through the §3.2 ledger with a fresh per-round op id
    ops = ci_loop.load_ops(tmp_path / "ops")
    assert [(o.op_id, o.purpose, o.state) for o in ops] == \
        [("run-1-ci-r0", "initial", "created")]
    assert ci.builds["b1"]["meta_data"]["imx_op_id"] == "run-1-ci-r0"


def test_rounds_push_gating(tmp_path):
    ci = RoundsCI([])
    result, _ = _rounds(ci, tmp_path,
                        push_results=[Push(dry_run=True, pushed=False,
                                           reason="ALLOW_PUSH not set")])
    assert result.result == "push_dry_run" and ci.created == 0
    result, _ = _rounds(ci, tmp_path,
                        push_results=[Push(pushed=False, reason="denied")])
    assert result.result == "push_failed" and "denied" in result.reason


def test_rounds_refuses_foreign_active_build_before_push(tmp_path):
    """Round-3 review: the refusal must land BEFORE the push — the push's
    own webhook build could already cancel the unowned active build under
    cancel-running-branch-builds semantics."""
    ci = RoundsCI([], active=[{"id": "x9", "number": 9, "state": "running",
                               "commit": "d" * 40}])
    result, push_calls = _rounds(ci, tmp_path)
    assert result.result == "refused" and ci.created == 0
    assert "does not own" in result.reason
    assert push_calls == []             # nothing was pushed


def test_rounds_prepush_exempts_adoptable_schedule_build(tmp_path):
    """Live nightly-adopt run (2026-08-24): the org pipeline builds only
    by schedule; the nightly built OUR pushed head, but the PRE-PUSH
    foreign scan refused before _acquire_build's same-commit adoption
    could run - with a clean tree the push is a ref no-op that cancels
    nothing, so an adoption-qualifying build at the head must be exempt
    from that scan and end up ADOPTED (monitor-only)."""
    head = "h" * 40
    running = {"id": "x9", "number": 9, "state": "running",
               "commit": head, "source": "schedule", "web_url": "u/x9"}
    finished = {"id": "x9", "state": "passed", "commit": head,
                "source": "schedule", "web_url": "u/x9",
                "jobs": [_job("Green", "passed", 0)]}
    ci = RoundsCI([], active=[running], siblings=[finished])
    result, push_calls = _rounds(ci, tmp_path,
                                 push_results=[Push(commit=head)],
                                 head_commit=head)
    assert result.result == "passed"
    assert [(r.purpose, r.adopted) for r in result.rounds] == \
        [("adopted", True)]
    assert ci.created == 0                      # monitor-only adoption
    assert push_calls == [0]                    # the no-op push still ran


def test_rounds_prepush_exemption_needs_clean_tree_and_schedule_source(
        tmp_path):
    """The exemption is NARROW: local changes mean the push would move
    the ref (and could cancel the build), and a ui/manual build is
    neither evidence nor ours - both keep the refusal."""
    head = "h" * 40
    sched = {"id": "x9", "number": 9, "state": "running",
             "commit": head, "source": "schedule", "web_url": "u/x9"}
    ci = RoundsCI([], active=[sched])
    result, push_calls = _rounds(ci, tmp_path, head_commit=head,
                                 changes=[True])
    assert result.result == "refused" and push_calls == []
    ui = dict(sched, source="ui")
    ci = RoundsCI([], active=[ui])
    result, push_calls = _rounds(ci, tmp_path, head_commit=head)
    assert result.result == "refused" and push_calls == []


def test_rounds_no_run_adopts_sibling_else_no_signal(tmp_path):
    sibling = {"id": "s1", "number": 3, "state": "passed",
               "commit": "c" * 40, "web_url": "u/s1",
               "source": "schedule",
               "jobs": [_job("Green", "passed", 0)]}
    ci = RoundsCI([{"state": "not_run", "jobs": []}], siblings=[sibling])
    result, _ = _rounds(ci, tmp_path)
    assert result.result == "passed"
    assert [(r.purpose, r.adopted) for r in result.rounds] == \
        [("initial", False), ("adopted", True)]
    # adopted builds are MONITOR-ONLY: no op record exists for them
    assert [o.op_id for o in ci_loop.load_ops(tmp_path / "ops")] == \
        ["run-1-ci-r0"]

    ci = RoundsCI([{"state": "skipped", "jobs": []}])
    result, _ = _rounds(ci, tmp_path)
    assert result.result == "no_signal"
    assert "not going to be tested" in result.reason


def test_rounds_partial_webhook_sibling_is_not_evidence(tmp_path):
    """Round-4 review: a webhook/manual sibling runs WITHOUT the trigger
    env's opt-in suite — a passing partial build must never green-light
    the commit; only schedule/api sources qualify for adoption."""
    webhook = {"id": "s1", "number": 3, "state": "passed",
               "commit": "c" * 40, "web_url": "u/s1",
               "source": "webhook",
               "jobs": [_job("Green", "passed", 0)]}
    ci = RoundsCI([{"state": "not_run", "jobs": []}], siblings=[webhook])
    result, _ = _rounds(ci, tmp_path)
    assert result.result == "no_signal"


def test_rounds_adopted_builds_are_never_retried(tmp_path):
    """Round-4 review: adopted = monitor-only (§3.2) — retry_job must
    never mutate a build with no ownership record, even with retry budget
    configured."""
    sibling = {"id": "s1", "number": 3, "state": "failed",
               "commit": "c" * 40, "web_url": "u/s1", "source": "api",
               "jobs": [_job("Red", "failed", 1)]}

    class NoRetry(RoundsCI):
        def retry_job(self, build_id, job_id):
            raise AssertionError("retry_job called on an adopted build")

    ci = NoRetry([{"state": "not_run", "jobs": []}], siblings=[sibling])
    ci.logs["Red"] = "FAILED tests/r.py::t - x"
    result, _ = _rounds(ci, tmp_path, job_retry_max=2)
    assert result.result == "failed"
    assert result.unfixed_jobs == ["Red"]


def test_rounds_debug_fix_then_green_second_build(tmp_path):
    ci = RoundsCI([
        {"state": "failed", "jobs": [_job("Red", "failed", 1)]},
        {"state": "passed", "jobs": [_job("Red", "passed", 0)]},
    ])
    ci.logs["Red"] = "FAILED tests/r.py::t - x"
    dispatched = []

    async def debug(jr):
        dispatched.append(jr.name)
        return True

    result, push_calls = _rounds(ci, tmp_path, changes=[True],
                                 debug=debug)
    assert result.result == "passed"
    assert dispatched == ["Red"] and result.fixed_jobs == ["Red"]
    # the fix round PUSHED (round 1) and built under a FRESH op id
    assert push_calls == [0, 1]
    assert sorted(o.op_id for o in ci_loop.load_ops(tmp_path / "ops")) == \
        ["run-1-ci-r0", "run-1-ci-r1"]
    assert [o.purpose for o in ci_loop.load_ops(tmp_path / "ops")] == \
        ["initial", "retry"]


def test_rounds_serialized_debug_dispatch(tmp_path):
    ci = RoundsCI([{"state": "failed", "jobs": [
        _job("A", "failed", 1), _job("B", "failed", 1)]}])
    in_flight = {"n": 0, "max": 0}

    async def debug(jr):
        in_flight["n"] += 1
        in_flight["max"] = max(in_flight["max"], in_flight["n"])
        await asyncio.sleep(0)
        in_flight["n"] -= 1
        return False

    result, _ = _rounds(ci, tmp_path, debug=debug)
    assert result.result == "failed"
    assert in_flight["max"] == 1        # one agent at a time, always
    assert sorted(result.unfixed_jobs) == ["A", "B"]


def test_rounds_no_fixes_fails_immediately(tmp_path):
    ci = RoundsCI([{"state": "failed", "jobs": [_job("Red", "failed", 1)]}])
    result, push_calls = _rounds(ci, tmp_path)   # no debug_fn at all
    assert result.result == "failed"
    assert result.unfixed_jobs == ["Red"] and push_calls == [0]
    assert ci.created == 1              # never rebuilt without a fix


def test_rounds_budget_timeout_is_operator_problem(tmp_path):
    ci = RoundsCI([{"state": "failed",
                    "jobs": [_job("Budget", "timed_out", 255)]}])
    ci.logs["Budget"] = (
        "\x1b_bk;t=1000000\x07 many tests PASSED with healthy output\n"
        "\x1b_bk;t=1100000\x07 Exceeded maximum job timeout")
    dispatched = []

    async def debug(jr):
        dispatched.append(jr.name)
        return True

    result, _ = _rounds(ci, tmp_path, debug=debug)
    assert result.result == "failed" and "budget" in result.reason
    assert dispatched == []             # never debugged
    assert result.unfixed_jobs == ["Budget"]


def test_rounds_incomplete_only_rebuilds_then_adopts_same_commit(tmp_path):
    """No code changes + unfinished jobs ⇒ a rebuild round; an ACTIVE build
    at the same commit is adopted (monitor-only) instead of duplicated."""
    # adopt-time view (still running) vs monitor-time view (finished
    # green); a full-suite source — partial webhook siblings don't qualify
    active_view = {"id": "w1", "number": 8, "state": "running",
                   "commit": "c" * 40, "web_url": "u/w1", "source": "api"}
    finished_view = {"id": "w1", "number": 8, "state": "passed",
                     "commit": "c" * 40, "web_url": "u/w1",
                     "jobs": [_job("Hung", "passed", 0)]}
    ci = RoundsCI([{"state": "failed", "jobs": [_job("Hung", "running")]}])
    ci.siblings = [finished_view]
    calls = {"n": 0}

    def latest_builds(branch, states=(), per_page=30):
        calls["n"] += 1
        # round 0 (pre-push scan + acquire): nothing active; round 1
        # (rebuild acquire): the full-suite sibling has appeared
        return [] if calls["n"] <= 2 else [active_view]

    ci.latest_builds = latest_builds
    result, push_calls = _rounds(ci, tmp_path, max_retries=1)
    assert push_calls == [0] and ci.created == 1
    assert result.result == "passed"
    assert [(r.purpose, r.adopted) for r in result.rounds] == \
        [("initial", False), ("adopted", True)]


def test_rounds_exhaustion(tmp_path):
    ci = RoundsCI([
        {"state": "failed", "jobs": [_job("Hung", "running")]},
        {"state": "failed", "jobs": [_job("Hung", "running")]},
    ])
    # rebuild rounds create fresh builds (no active sibling here)
    result, _ = _rounds(ci, tmp_path, max_retries=1)
    assert result.result == "failed" and "after 2 round" in result.reason
    assert [o.purpose for o in ci_loop.load_ops(tmp_path / "ops")] == \
        ["initial", "rebuild"]
    assert result.unfixed_jobs == ["Hung"]


# ── push_to_ci pin data-gating ───────────────────────────────────────────────

def test_commit_and_push_pin_none_skips_dockerfile_preflight(tmp_path):
    """A wheel-less adapter (pin=None) must not be forced through the
    Dockerfile-pin preflight; the 40-hex upstream-commit preflight still
    rules."""
    import subprocess
    repo = tmp_path / "r"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", repo], check=True)
    subprocess.run(["git", "-C", repo, "-c", "user.name=t", "-c",
                    "user.email=t@t", "commit", "-q", "--allow-empty",
                    "-m", "seed"], check=True)
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", remote], check=True)
    subprocess.run(["git", "-C", repo, "remote", "add", "origin",
                    str(remote)], check=True)
    with pytest.raises(push_to_ci.PushPreflightError, match="40-hex"):
        push_to_ci.commit_and_push(
            repo, upstream_commit="nope", pin=None, branch="dev",
            message_template="m {short}", unstage_globs=[],
            author_name="a", author_email="a@b",
            protected_branches=["main"], wal_dir=tmp_path / "wal",
            op_id="op1")
    # a valid commit sails past BOTH preflights and stops at the guard
    # (allowed=False) — proving no Dockerfile pin was demanded
    out = push_to_ci.commit_and_push(
        repo, upstream_commit="c" * 40, pin=None, branch="dev",
        message_template="m {short}", unstage_globs=[],
        author_name="a", author_email="a@b", protected_branches=["main"],
        wal_dir=tmp_path / "wal", op_id="op1", allowed=False)
    assert not out.pushed and "denied" in out.reason


# ── round-1 review regressions: resume, digest, abort cleanup ────────────────

def test_rounds_resume_never_reuses_op_ids(tmp_path):
    """A resumed invocation starts op indices AFTER the durable ledger's
    highest — round zero of the re-entry must not collide with the crashed
    run's `-r0` operations (op ids are single-use identities)."""
    seed = RoundsCI([{"state": "failed", "jobs": []}])
    ci_loop.create_build_guarded(
        seed, tmp_path / "ops", op_id="run-1-ci-r0", run_id="run-1",
        purpose="initial", branch="dev", commit="c" * 40, message="m")
    assert ci_loop.op_index_base(
        ci_loop.load_ops(tmp_path / "ops"), "run-1") == 1
    # foreign run ids never shift this run's base
    assert ci_loop.op_index_base(
        ci_loop.load_ops(tmp_path / "ops"), "run-2") == 0

    ci = RoundsCI([{"state": "passed",
                    "jobs": [_job("Green", "passed", 0)]}])
    result, push_calls = _rounds(ci, tmp_path)
    assert result.result == "passed"
    # the resumed run pushed and built under index 1, not 0
    assert push_calls == [1]
    assert sorted(o.op_id for o in ci_loop.load_ops(tmp_path / "ops")) == \
        ["run-1-ci-r0", "run-1-ci-r1"]


def test_worktree_digest_sees_content_edits_porcelain_misses(tmp_path):
    """`status --porcelain` output is identical before/after a content
    edit to an ALREADY-dirty or untracked file — the digest must not
    be."""
    import subprocess

    from infermatrix_copilot.engine.steps.rebase_v3 import _worktree_digest
    repo = tmp_path / "r"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", repo], check=True)
    (repo / "a.py").write_text("x = 1\n")
    subprocess.run(["git", "-C", repo, "add", "-A"], check=True)
    subprocess.run(["git", "-C", repo, "-c", "user.name=t", "-c",
                    "user.email=t@t", "commit", "-qm", "seed"], check=True)

    (repo / "a.py").write_text("x = 2\n")           # dirty
    d1 = _worktree_digest(repo)
    (repo / "a.py").write_text("x = 3\n")           # SAME porcelain line
    d2 = _worktree_digest(repo)
    assert d1 != d2

    (repo / "new.py").write_text("n = 1\n")          # untracked
    d3 = _worktree_digest(repo)
    (repo / "new.py").write_text("n = 2\n")          # SAME porcelain line
    d4 = _worktree_digest(repo)
    assert d3 != d4
    # and an unchanged tree digests stably
    assert _worktree_digest(repo) == d4


def test_debug_patch_policy_rejects_oracle_weakening(tmp_path):
    """A locally green run cannot authorize an agent to lower a test oracle."""
    import subprocess

    repo = tmp_path / "r"
    (repo / "tests").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", repo], check=True)
    helper = repo / "tests" / "audio_helpers.py"
    helper.write_text("def check(score):\n    assert score > 0.8\n")
    subprocess.run(["git", "-C", repo, "add", "-A"], check=True)
    before = debug_patch_policy.capture_patch_policy(repo)

    helper.write_text("def check(score):\n    assert score > 0.7\n")
    decision = debug_patch_policy.evaluate_debug_patch(
        repo, before, local_verdict="passed")
    assert not decision.allowed
    assert decision.paths == ("tests/audio_helpers.py",)
    assert "assertions or tolerances" in decision.reason


def test_debug_patch_policy_requires_local_pass_for_test_edits(tmp_path):
    import subprocess

    repo = tmp_path / "r"
    (repo / "tests").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", repo], check=True)
    test_file = repo / "tests" / "test_widget.py"
    test_file.write_text("def test_widget():\n    pass\n")
    source = repo / "widget.py"
    source.write_text("VALUE = 1\n")
    subprocess.run(["git", "-C", repo, "add", "-A"], check=True)

    before = debug_patch_policy.capture_patch_policy(repo)
    test_file.write_text("def test_widget():\n    # new coverage\n    pass\n")
    skipped = debug_patch_policy.evaluate_debug_patch(
        repo, before, local_verdict="skipped")
    assert not skipped.allowed
    assert "passing local verification" in skipped.reason
    assert debug_patch_policy.evaluate_debug_patch(
        repo, before, local_verdict="passed").allowed

    subprocess.run(["git", "-C", repo, "checkout", "--", "."], check=True)
    before = debug_patch_policy.capture_patch_policy(repo)
    source.write_text("VALUE = 2\n")
    assert debug_patch_policy.evaluate_debug_patch(
        repo, before, local_verdict="unavailable").allowed


def test_cancel_owned_active_builds_on_abort(tmp_path):
    """Abort cleanup cancels ONLY our still-active op-recorded builds:
    terminal builds and adopted (ledger-less) builds are untouched, and a
    second invocation is idempotent."""
    from infermatrix_copilot.engine.steps.rebase_v3 import \
        _cancel_owned_active_builds

    class AbortCI(RoundsCI):
        def __init__(self, bodies):
            super().__init__(bodies)
            self.cancelled: list[str] = []

        def cancel_build(self, build_id):
            self.cancelled.append(build_id)
            self.builds[build_id]["state"] = "canceled"
            return self.builds[build_id]

    ci = AbortCI([{"state": "running", "jobs": []},
                  {"state": "failed", "jobs": []}])
    ci_loop.create_build_guarded(ci, tmp_path / "ops", op_id="r-ci-r0",
                                 run_id="r", purpose="initial",
                                 branch="dev", commit="c" * 40,
                                 message="m")
    ci_loop.create_build_guarded(ci, tmp_path / "ops", op_id="r-ci-r1",
                                 run_id="r", purpose="retry",
                                 branch="dev", commit="c" * 40,
                                 message="m")
    # an adopted build exists in the provider but NOT in the ledger
    ci.builds["adopted"] = {"id": "adopted", "state": "running",
                            "meta_data": {}}
    events = []
    got = _cancel_owned_active_builds(ci, tmp_path / "ops",
                                      trace=lambda e, **kw:
                                      events.append((e, kw)))
    assert got == ["b1"] and ci.cancelled == ["b1"]      # running only
    assert ci.builds["adopted"]["state"] == "running"    # never touched
    assert events[0][0] == "ci_build_cancelled_on_abort"
    # idempotent: the cancelled op is consumed in the ledger
    assert _cancel_owned_active_builds(ci, tmp_path / "ops") == []


# ── round-2 review regressions ───────────────────────────────────────────────

def test_baseline_logs_fetched_from_baseline_pipeline_client():
    """Round-2 review: BaselineFailure.build_id belongs to the BASELINE
    pipeline — resolving it on the build-under-test client 404s into the
    lenient same-cause path, wrongly ignoring real regressions."""
    baseline = (BaselineFailure(name="lane", exit_status=1,
                                job_id="mainJ", build_id="42"),)
    asked = []

    def baseline_log(build_id, job_id):
        asked.append((build_id, job_id))
        return "RuntimeError: the OLD failure\nFAILED tests/l.py::t_old - z"

    ci = ScriptedCI(
        snapshots=[{"state": "failed",
                    "jobs": [_job("Lane", "failed", 1)]}],
        logs={"Lane": "RuntimeError: a NEW regression\n"
                      "FAILED tests/l.py::t_new - y"})
    out = ci_loop.monitor_build(
        ci, "b", spec=CIClassifySpec(baseline=baseline,
                                     baseline_log_fn=baseline_log),
        poll_sec=0, timeout_sec=0, sleep=lambda s: None)
    # the baseline log came from the BASELINE client, and its differing
    # signature makes this a REAL failure, not ignored_baseline
    assert asked == [("42", "mainJ")]
    assert out.jobs[0].classification == "failed"


def test_monitor_reconciliation_failure_never_passes():
    """Round-2 review: when neither the jobs endpoint nor the build is
    readable at reconciliation time, retrieval failure must not read as
    'nothing missed' — clean_pass is off even with green polled jobs."""
    class OutageCI(ScriptedCI):
        def list_jobs(self, build_id):
            raise BuildkiteError("list_jobs failed")

    ci = OutageCI(snapshots=[
        {"state": "passed", "jobs": [_job("Green", "passed", 0)]},
        {},                          # the API outage begins
    ])
    out = ci_loop.monitor_build(ci, "b", spec=CIClassifySpec(), poll_sec=0,
                                sleep=lambda s: None)
    assert out.reconciled is False and not out.clean_pass
    # with the build still readable, a raising jobs endpoint degrades to
    # the embedded snapshot and reconciliation stands
    ci = OutageCI(snapshots=[
        {"state": "passed", "jobs": [_job("Green", "passed", 0)]}])
    out = ci_loop.monitor_build(ci, "b", spec=CIClassifySpec(), poll_sec=0,
                                sleep=lambda s: None)
    assert out.reconciled is True and out.clean_pass


def test_buildkite_list_jobs_raises_when_nothing_readable():
    bk = BuildkiteCI("t", "o", "p",
                     request=Recorder([(500, {}), (500, {})]))
    with pytest.raises(BuildkiteError, match="build itself is unreadable"):
        bk.list_jobs("9")


def test_rounds_resume_recovers_intent_before_new_index(tmp_path):
    """Round-2 review: a crash between durable intent and create ack must
    RECOVER that op (adopt by op-id metadata) — never advance to a fresh
    index while the earlier creation is uncertain."""
    intent = ci_loop.BuildOp(op_id="run-1-ci-r0", run_id="run-1",
                             purpose="initial", branch="dev",
                             commit="c" * 40)
    from dataclasses import asdict
    ci_loop._durable_write(intent.path(tmp_path / "ops"), asdict(intent))
    ci = RoundsCI([])
    # the crashed create actually LANDED: an orphan build carries the op id
    orphan = ci.create_build(branch="dev", commit="c" * 40, message="m",
                             meta_data={"imx_op_id": "run-1-ci-r0"})
    ci.builds[orphan["id"]].update(
        {"state": "passed", "jobs": [_job("Green", "passed", 0)]})
    result, push_calls = _rounds(ci, tmp_path)
    assert result.result == "passed"
    assert ci.created == 1                      # adopted, never re-created
    ops = ci_loop.load_ops(tmp_path / "ops")
    assert [(o.op_id, o.state, o.build_id) for o in ops] == \
        [("run-1-ci-r0", "created", orphan["id"])]
    assert result.rounds[0].op_id == "run-1-ci-r0"

    # ...and when NO build carries the op id, recovery ESCALATES (refused)
    intent2 = ci_loop.BuildOp(op_id="run-2-ci-r0", run_id="run-2",
                              purpose="initial", branch="dev",
                              commit="c" * 40)
    ci_loop._durable_write(intent2.path(tmp_path / "ops2"),
                           asdict(intent2))
    ci2 = RoundsCI([])
    result2 = _run(ci_loop.run_ci_rounds(
        client=ci2, ops_dir=tmp_path / "ops2", run_id="run-2",
        branch="dev", spec=CIClassifySpec(), push_fn=lambda i: Push(),
        changes_fn=lambda: False, settle_sec=0, poll_sec=0, timeout_sec=0,
        job_retry_max=0, sleep=lambda s: None, asleep=_noop_sleep))
    assert result2.result == "refused"
    assert "refusing to re-create" in result2.reason
    assert ci2.created == 0


def test_rounds_resume_reattaches_active_created_build(tmp_path):
    """Round-2 review companion: a `created` op whose build is still
    ACTIVE at this commit (crash during monitor) is re-attached — not
    duplicated, not treated as a foreign active build."""
    class TwoViewCI(RoundsCI):
        def __init__(self):
            super().__init__([])
            self.views = 0

        def get_build(self, build_id):
            b = dict(super().get_build(build_id))
            if b:
                self.views += 1
                b["state"] = "running" if self.views == 1 else "passed"
                if b["state"] == "passed":
                    b["jobs"] = [_job("Green", "passed", 0)]
            return b

        def list_jobs(self, build_id):
            return [_job("Green", "passed", 0)]

    ci = TwoViewCI()
    ci_loop.create_build_guarded(ci, tmp_path / "ops",
                                 op_id="run-1-ci-r0", run_id="run-1",
                                 purpose="initial", branch="dev",
                                 commit="c" * 40, message="m")
    assert ci.created == 1
    # the still-running build is OURS (op-recorded): visible in the
    # pre-push active scan, it must NOT trip the foreign-build refusal
    ci.active = [{"id": "b1", "number": 1, "state": "running",
                  "commit": "c" * 40}]
    result, push_calls = _rounds(ci, tmp_path)
    assert result.result == "passed"
    assert ci.created == 1                      # re-attached, no new build
    assert result.rounds[0].op_id == "run-1-ci-r0"
    assert result.rounds[0].build_id == "b1"


def test_restore_worktree_restores_untracked_content(tmp_path):
    """Round-2 review: `stash create` skips untracked files — the snapshot
    must capture their CONTENT so a rejected attempt's edit (or deletion)
    of a pre-existing untracked file is rolled back, not preserved."""
    import subprocess

    from infermatrix_copilot.rebase_engine import test_loop as tl
    repo = tmp_path / "r"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", repo], check=True)
    (repo / "tracked.py").write_text("t = 1\n")
    subprocess.run(["git", "-C", repo, "add", "-A"], check=True)
    subprocess.run(["git", "-C", repo, "-c", "user.name=t", "-c",
                    "user.email=t@t", "commit", "-qm", "seed"], check=True)
    # an earlier ACCEPTED fix left an untracked file behind
    (repo / "accepted_fix.py").write_text("good bytes\n")

    (repo / "accepted_fix.py").chmod(0o644)

    snap, untracked = tl.snapshot_worktree(repo)
    assert set(untracked) == {"accepted_fix.py"}
    # the rejected attempt edits BOTH, and creates a new file
    (repo / "tracked.py").write_text("t = 666\n")
    (repo / "accepted_fix.py").write_text("rejected bytes\n")
    (repo / "brand_new.py").write_text("n\n")
    tl.restore_worktree(repo, snap, untracked)
    assert (repo / "tracked.py").read_text() == "t = 1\n"
    assert (repo / "accepted_fix.py").read_text() == "good bytes\n"
    assert not (repo / "brand_new.py").exists()
    # deletion of the pre-existing untracked file also rolls back
    (repo / "accepted_fix.py").unlink()
    tl.restore_worktree(repo, snap, untracked)
    assert (repo / "accepted_fix.py").read_text() == "good bytes\n"
    # round-3 review: a chmod-only attempt rolls back too
    (repo / "accepted_fix.py").chmod(0o755)
    tl.restore_worktree(repo, snap, untracked)
    assert ((repo / "accepted_fix.py").stat().st_mode & 0o777) == 0o644
    # ...and a file-to-directory type change
    (repo / "accepted_fix.py").unlink()
    (repo / "accepted_fix.py").mkdir()
    (repo / "accepted_fix.py" / "inner.txt").write_text("x\n")
    tl.restore_worktree(repo, snap, untracked)
    assert (repo / "accepted_fix.py").is_file()
    assert (repo / "accepted_fix.py").read_text() == "good bytes\n"


def test_worktree_digest_sees_chmod_and_symlink_changes(tmp_path):
    """Round-3 review companion: mode bits and symlink targets are part
    of the digest — a chmod-only or retarget-only attempt is a change."""
    import os
    import subprocess

    from infermatrix_copilot.engine.steps.rebase_v3 import _worktree_digest
    repo = tmp_path / "r"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", repo], check=True)
    subprocess.run(["git", "-C", repo, "-c", "user.name=t", "-c",
                    "user.email=t@t", "commit", "-q", "--allow-empty",
                    "-m", "seed"], check=True)
    (repo / "u.sh").write_text("#!/bin/sh\n")
    (repo / "u.sh").chmod(0o644)
    d1 = _worktree_digest(repo)
    (repo / "u.sh").chmod(0o755)                 # chmod-only
    d2 = _worktree_digest(repo)
    assert d1 != d2
    os.symlink("u.sh", repo / "link")
    d3 = _worktree_digest(repo)
    (repo / "link").unlink()
    os.symlink("elsewhere", repo / "link")       # retarget-only
    d4 = _worktree_digest(repo)
    assert d3 != d4
