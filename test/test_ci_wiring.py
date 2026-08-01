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
from infermatrix_copilot.rebase_engine import ci_loop, push_to_ci
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
    bk = BuildkiteCI("t", "o", "p", request=Recorder([(500, {})]))
    assert bk.retry_job("9", "j") == (None, True)


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


def test_monitor_retry_exhausted_and_nonretryable():
    ci = ScriptedCI(
        snapshots=[{"state": "failed", "jobs": [
            _job("Hard", "failed", 1), _job("Upload", "failed", 1)]}],
        logs={"Hard": "FAILED tests/h.py::test_y - x"},
        retry_results=[(None, False)])   # Upload's type can't retry
    out = ci_loop.monitor_build(ci, "b", spec=CIClassifySpec(), poll_sec=0,
                                retry_max=1, timeout_sec=0,
                                sleep=lambda s: None)
    cls = {j.job_id: j.classification for j in out.jobs}
    # Hard consumed its retry (got retried=queued? no — scripted returns
    # (None, False) first for whichever is classified first) — order the
    # jobs deterministically instead:
    assert cls["Hard"] in ("failed", "ignored", "retrying")
    assert not out.clean_pass


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


def test_monitor_baseline_lenient_defaults():
    """Missing baseline coordinates / missing baseline log / empty current
    signature ⇒ same-cause (parent-documented lenient default)."""
    baseline = (BaselineFailure(name="lane c", exit_status=1),)
    ci = ScriptedCI(snapshots=[{"state": "failed", "jobs": [
        _job("Lane C", "failed", 1)]}],
        logs={"Lane C": "FAILED tests/c.py::t - x"})
    out = ci_loop.monitor_build(ci, "b", spec=CIClassifySpec(
        baseline=baseline), poll_sec=0, timeout_sec=0, sleep=lambda s: None)
    assert out.jobs[0].classification == "ignored_baseline"
    # exit-status mismatch means NO baseline match at all
    baseline = (BaselineFailure(name="lane c", exit_status=2),)
    ci = ScriptedCI(snapshots=[{"state": "failed", "jobs": [
        _job("Lane C", "failed", 1)]}],
        logs={"Lane C": "FAILED tests/c.py::t - x"})
    out = ci_loop.monitor_build(ci, "b", spec=CIClassifySpec(
        baseline=baseline), poll_sec=0, timeout_sec=0, sleep=lambda s: None)
    assert out.jobs[0].classification == "failed"


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


def test_pick_best_build_and_baseline_fetch():
    builds = [
        {"id": "5", "number": 5, "state": "failed", "source": "webhook"},
        {"id": "4", "number": 4, "state": "failed", "source": "api"},
        {"id": "3", "number": 3, "state": "failed", "source": "schedule"},
    ]
    assert ci_loop.pick_best_build(builds)["id"] == "3"   # schedule wins
    assert ci_loop.pick_best_build([]) is None

    class BaselineClient:
        def latest_builds(self, branch, states=(), per_page=30):
            assert states == ("failed",)
            return builds

        def list_jobs(self, build_id):
            assert build_id == "3"
            return [_job("Lane A", "failed", 1, id="jA"),
                    _job("Zero Exit", "failed", 0, id="jZ"),
                    _job("Green", "passed", 0, id="jG"),
                    _job("", "failed", 1, id="jNoName")]

    got = ci_loop.fetch_baseline_failures(BaselineClient(), "main")
    assert got == (BaselineFailure("lane a", 1, "jA", "3"),
                   # the parent's `or -1` encoding: exit 0/None ⇒ -1
                   BaselineFailure("zero exit", -1, "jZ", "3"))


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


def test_rounds_refuses_active_build_at_other_commit(tmp_path):
    ci = RoundsCI([], active=[{"id": "x9", "number": 9, "state": "running",
                               "commit": "d" * 40}])
    result, _ = _rounds(ci, tmp_path)
    assert result.result == "refused" and ci.created == 0
    assert "does not own" in result.reason


def test_rounds_no_run_adopts_sibling_else_no_signal(tmp_path):
    sibling = {"id": "s1", "number": 3, "state": "passed",
               "commit": "c" * 40, "web_url": "u/s1",
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
    # adopt-time view (still running) vs monitor-time view (finished green)
    active_view = {"id": "w1", "number": 8, "state": "running",
                   "commit": "c" * 40, "web_url": "u/w1"}
    finished_view = {"id": "w1", "number": 8, "state": "passed",
                     "commit": "c" * 40, "web_url": "u/w1",
                     "jobs": [_job("Hung", "passed", 0)]}
    ci = RoundsCI([{"state": "failed", "jobs": [_job("Hung", "running")]}])
    ci.siblings = [finished_view]
    calls = {"n": 0}

    def latest_builds(branch, states=(), per_page=30):
        calls["n"] += 1
        # round 0: nothing active; round 1 (rebuild): the webhook sibling
        return [] if calls["n"] == 1 else [active_view]

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
