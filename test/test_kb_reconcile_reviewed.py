"""Supervised owner-merged admission stays distinct from automatic gating."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from infermatrix_copilot.kb_service import reconcile
from infermatrix_copilot.kb_service.activate import activate
from infermatrix_copilot.kb_service.accept import request_accept, accept_pending
from infermatrix_copilot.kb_service.audit import audit_main, open_unknown, provenance_problems, publish_trusted
from infermatrix_copilot.knowledge_service.signing import SignatureError, verify
from test_kb_audit import _setup, _land, _git


class MergeGitHub:
    def __init__(self, sha):
        self.actor = "owner"
        self.pr = {"number": 41, "html_url": "https://github.com/org/kb/pull/41", "merged_at": "2026-10-06T01:00:00Z",
                   "merge_commit_sha": sha, "merged_by": {"login": "owner"}, "head": {"sha": sha},
                   "base": {"repo": {"full_name": "org/kb"}}}
        self.checks = [{"id": 1, "name": "suite", "head_sha": sha, "status": "completed", "conclusion": "success"}]

    def get(self, path, **_params):
        if path == "/user":
            return {"login": self.actor}
        if path.endswith("/pulls"):
            return [self.pr]
        if path.endswith("/pulls/41"):
            return self.pr
        if path.endswith("/check-runs"):
            return {"check_runs": self.checks}
        if path.endswith(("/statuses", "/reviews")):
            return []
        raise AssertionError(path)


@pytest.fixture
def world(tmp_path, monkeypatch):
    rt, lifecycle, scheduler, origin = _setup(tmp_path)
    _land(origin, "knowledge/AGENTS.md", "# Agent instructions\n", "baseline entry")
    for name in ("check_knowledge_tree.py", "check_wiki_lint.py"):
        _land(origin, f"knowledge/tools/{name}", "import subprocess\nsubprocess.run(['git','ls-files','--error-unmatch','knowledge/AGENTS.md'], check=True, capture_output=True)\nprint('fixture validation passed')\n", "baseline validator")
    baseline = rt.knowledge.fetch()
    # This fixture baseline precedes the recovery target, exactly as deployment.
    rt.ledger.set_cursor("*", "audit_main_sha", baseline)
    activate(rt, baseline)
    sha = _land(origin, "knowledge/README.md", "# Knowledge\n\nHuman-maintained onboarding.\n", "owner administration (#41)")
    audit_main(rt, scheduler._pause)
    rt.github = MergeGitHub(sha)
    monkeypatch.setattr(reconcile, "_repository", lambda knowledge: "org/kb")
    monkeypatch.setenv("KB_KNOWLEDGE_CLONE", str(rt.knowledge.path))
    return SimpleNamespace(rt=rt, scheduler=scheduler, origin=origin, sha=sha, base=baseline,
                           key=rt.outbox._key, options=dict(target=sha, allow_mergers=["owner"],
                                                          required_checks=["suite"], reason="authorized owner recovery"))


def test_supervised_admission_passes_real_activation_without_disposing_or_changing_modes(world):
    w = world
    request_accept(w.rt.ledger, w.sha, at=w.rt.clock())
    assert "refused" in accept_pending(w.rt)[0]  # automatic accept still refuses top-level pages
    plan = reconcile.make_plan(w.rt, w.key, **w.options)
    assert open_unknown(w.rt) == [w.sha]  # preparing never grants trust
    receipt = reconcile.apply_plan(w.rt, plan, w.key)
    assert reconcile.apply_plan(w.rt, plan, w.key) == receipt
    assert open_unknown(w.rt) == []
    assert w.rt.ledger.get_cursor("*", "disposed:" + w.sha) is None
    assert w.rt.ledger.repo_state("*")["paused"]
    assert w.rt.ledger.repo_state("demo")["mode"] == "auto_merge"
    assert provenance_problems(w.rt, w.sha) == []
    assert activate(w.rt, w.sha).name == w.sha
    payload = verify(reconcile.RECEIPT_PURPOSE, json.loads(receipt.read_text()), w.key.public_key())
    assert payload["actor"] == "owner" and payload["commits"][0]["pr"]["reviews"] == []


@pytest.mark.parametrize("failure", ["missing_check", "pending_check", "failed_check", "wrong_head", "wrong_merge", "merger", "actor"])
def test_unproven_github_evidence_cannot_create_receipts(world, failure):
    w = world
    if failure == "missing_check":
        w.rt.github.checks = []
    elif failure in {"pending_check", "failed_check"}:
        w.rt.github.checks[0]["conclusion"] = "failure" if failure == "failed_check" else None
        w.rt.github.checks[0]["status"] = "completed" if failure == "failed_check" else "queued"
    elif failure == "wrong_head":
        w.rt.github.checks[0]["head_sha"] = "f" * 40
    elif failure == "wrong_merge":
        w.rt.github.pr["merge_commit_sha"] = "f" * 40
    elif failure == "merger":
        w.rt.github.pr["merged_by"]["login"] = "untrusted"
    else:
        w.rt.github.actor = "untrusted"
    with pytest.raises(reconcile.ReconciliationError):
        reconcile.make_plan(w.rt, w.key, **w.options)
    assert open_unknown(w.rt) == [w.sha]
    assert not (w.rt.state_dir / "reconciliations").exists()


def test_target_drift_and_plan_tampering_refuse_before_admission(world):
    w = world
    plan = reconcile.make_plan(w.rt, w.key, **w.options)
    damaged = json.loads(json.dumps(plan))
    damaged["payload"]["reason"] = "another reason"
    with pytest.raises(SignatureError):
        reconcile.apply_plan(w.rt, damaged, w.key)
    _land(w.origin, "src/app.py", "x=1\n", "new main")
    with pytest.raises(reconcile.ReconciliationError, match="main differs"):
        reconcile.apply_plan(w.rt, plan, w.key)
    assert not (w.rt.state_dir / "reconciliations").exists()


def test_new_knowledge_merge_stays_unknown_after_receipt_and_nonknowledge_descendant_is_allowed(world):
    w = world
    reconcile.apply_plan(w.rt, reconcile.make_plan(w.rt, w.key, **w.options), w.key)
    code = _land(w.origin, "src/app.py", "x=1\n", "code only")
    assert w.rt.knowledge.fetch() == code and provenance_problems(w.rt, code) == []
    assert reconcile.trusted_commits(w.rt) == {w.sha}
    newer = _land(w.origin, "knowledge/README.md", "# Changed later\n", "new knowledge")
    audit_main(w.rt, w.scheduler._pause)
    assert open_unknown(w.rt) == [newer]
    assert any(newer[:12] in p for p in provenance_problems(w.rt, w.rt.knowledge.fetch()))


def test_corrupt_or_missing_receipt_never_renews_cached_control_trust(world):
    w = world
    receipt = reconcile.apply_plan(w.rt, reconcile.make_plan(w.rt, w.key, **w.options), w.key)
    publish_trusted(w.rt)
    assert w.sha not in json.loads(w.rt.ledger.get_cursor("*", "trusted_merges"))
    assert w.sha in w.rt.outbox.refresh_control()["provenance"]["trusted"]
    original = receipt.read_bytes()
    receipt.write_text("{}")
    with pytest.raises(reconcile.ReconciliationError):
        open_unknown(w.rt)
    with pytest.raises(reconcile.ReconciliationError):
        w.rt.outbox.refresh_control()
    receipt.write_bytes(original)
    receipt.unlink()
    assert open_unknown(w.rt) == [w.sha]
    assert w.sha not in w.rt.outbox.refresh_control()["provenance"]["trusted"]


def test_plan_signature_cannot_be_installed_as_receipt(world):
    w = world
    plan = reconcile.make_plan(w.rt, w.key, **w.options)
    directory = w.rt.state_dir / "reconciliations"
    directory.mkdir()
    (directory / (reconcile._digest(plan) + ".json")).write_text(json.dumps(plan))
    with pytest.raises(SignatureError):
        reconcile.trusted_commits(w.rt)


def test_failing_validator_keeps_previous_active_snapshot_and_pause(world):
    w = world
    newer = _land(w.origin, "knowledge/tools/check_wiki_lint.py", "raise SystemExit(1)\n", "broken validator (#41)")
    w.rt.github = MergeGitHub(newer)
    # Keep one commit in the planned interval to isolate mandatory validation.
    w.rt.ledger.record_activation(w.sha, {})
    with pytest.raises(reconcile.ReconciliationError, match="check_wiki_lint.py failed"):
        reconcile.make_plan(w.rt, w.key, **{**w.options, "target": newer})
    assert w.rt.ledger.active_snapshot() == w.sha
    assert w.rt.ledger.repo_state("*")["paused"]


def test_only_first_parent_baseline_is_eligible(world):
    w = world
    _git(w.origin, "checkout", "-q", "-b", "side", w.base)
    side = _land(w.origin, "src/side.py", "x=1\n", "side")
    _git(w.origin, "checkout", "-q", "main")
    _git(w.origin, "-c", "user.name=t", "-c", "user.email=t@e", "merge", "-q", "--no-ff", side)
    main = w.rt.knowledge.fetch()
    assert w.rt.knowledge.is_ancestor(side, main)
    with pytest.raises(reconcile.ReconciliationError, match="first-parent"):
        reconcile._commits(w.rt.knowledge, side, main)


def test_pending_revert_requires_resolution_before_supervised_admission(world):
    w = world
    record = json.loads(w.rt.ledger.get_cursor("*", "unknown:" + w.sha))
    w.rt.ledger.set_cursor("*", "unknown:" + w.sha, json.dumps({**record, "state": "revert_pending"}))
    with pytest.raises(reconcile.ReconciliationError, match="pending revert"):
        reconcile.make_plan(w.rt, w.key, **w.options)


def test_only_latest_check_attempt_governs_reconciliation(world):
    w = world
    older = {**w.rt.github.checks[0], "id": 0, "conclusion": "failure"}
    w.rt.github.checks.insert(0, older)
    plan = reconcile.make_plan(w.rt, w.key, **w.options)
    assert plan["payload"]["commits"][0]["pr"]["checks"][0]["id"] == 1
    w.rt.github.checks[-1]["conclusion"] = "cancelled"
    with pytest.raises(reconcile.ReconciliationError, match="required check"):
        reconcile.make_plan(w.rt, w.key, **w.options)


def test_pending_accept_request_requires_resolution(world):
    w = world
    request_accept(w.rt.ledger, w.sha, at=w.rt.clock())
    with pytest.raises(reconcile.ReconciliationError, match="pending acceptance"):
        reconcile.make_plan(w.rt, w.key, **w.options)
