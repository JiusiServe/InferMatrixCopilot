"""The release audit in each sweep: page hints and the adapter-baseline companion."""

from __future__ import annotations

import subprocess
from dataclasses import replace

import yaml

from infermatrix_copilot.kb_service.config import ReleaseConfig
from infermatrix_copilot.kb_service.sweep_audit import audit_sweep, baseline_text, stage_baseline_companion
from infermatrix_copilot.knowledge_service.release_audit import ReleaseAuditResult
from test_kb_flow import _flow_runtime, _items

COMMITTED = """schema_version: 1

upstream:
  repository: org/up
  audited_sha: aaaa

# fingerprints are generated
inventories:
  models:
    count: 1
    sha256: old

path_owners:
  core:
  - core/
"""
SWEEP = {"tag": "v2", "from_sha": "a" * 40, "to_sha": "b" * 40, "reason": "release"}


class Upstream:
    path = "/nonexistent"


def test_only_the_generated_blocks_change_and_comments_survive():
    text = baseline_text(COMMITTED, {"upstream": {"repository": "org/up", "audited_sha": "bbbb"},
                                     "inventories": {"models": {"count": 2, "sha256": "new"}}})
    assert "# fingerprints are generated" in text and "path_owners:\n  core:\n  - core/\n" in text
    data = yaml.safe_load(text)
    assert data["upstream"]["audited_sha"] == "bbbb" and data["inventories"]["models"]["count"] == 2
    assert data["path_owners"] == {"core": ["core/"]} and data["schema_version"] == 1


def _with_plugin(tmp_path, body: str):
    rt, lifecycle = _flow_runtime(tmp_path)
    adapter = tmp_path / "demoadapter"
    adapter.mkdir()
    (adapter / "plugin.py").write_text(body)
    lifecycle = replace(lifecycle, adapter_dir=adapter, release=ReleaseConfig(trigger="github_release",
                                                                             auditor="plugin.py"))
    rt.registry["demo"] = lifecycle
    return rt, lifecycle


PLUGIN = '''
def audit_for_knowledge(*, upstream_repo, from_ref, to_ref, knowledge_root, project_root):
    return {"upstream": {"from": {"sha": from_ref}, "to": {"sha": to_ref}},
            "issues": [{"kind": "stale_knowledge_source", "document": "knowledge/repos/demo/core/rules.md",
                        "detail": "gone"}],
            "reconciliation": [{"kind": "baseline_pin_mismatch"}],
            "generated_baseline": {"upstream": {"repository": "org/up", "audited_sha": to_ref},
                                   "inventories": {"models": {"count": 2, "sha256": "new"}}},
            "baseline_file": "release_baseline.yaml"}
'''


def test_audit_issues_become_page_hints(tmp_path):
    rt, lifecycle = _with_plugin(tmp_path, PLUGIN)
    hints, result = audit_sweep(rt, lifecycle, SWEEP, Upstream(), rt.knowledge.fetch())
    assert list(hints) == ["repos/demo/core/rules.md"] and hints["repos/demo/core/rules.md"][0]["detail"] == "gone"
    assert len(result.reconciliation) == 1
    assert audit_sweep(rt, lifecycle, {**SWEEP, "from_sha": "b" * 40}, Upstream(), rt.knowledge.fetch()) == ({}, None)  # nothing moved


def test_a_failing_audit_goes_to_people_once_and_never_blocks(tmp_path):
    rt, lifecycle = _with_plugin(tmp_path, "def audit_for_knowledge(**kw):\n    raise RuntimeError('boom')\n")
    assert audit_sweep(rt, lifecycle, SWEEP, Upstream(), rt.knowledge.fetch()) == ({}, None)
    assert audit_sweep(rt, lifecycle, SWEEP, Upstream(), rt.knowledge.fetch()) == ({}, None)
    assert [i for i in rt.ledger.human_queue("demo") if "release audit" in i["reason"]].__len__() == 1


def test_baseline_drift_becomes_one_companion_pr_per_sweep(tmp_path):
    rt, lifecycle = _with_plugin(tmp_path, PLUGIN)
    origin = tmp_path / "origin"
    target = origin / "adapters" / "demoadapter" / "release_baseline.yaml"
    target.parent.mkdir(parents=True)
    target.write_text(COMMITTED)
    subprocess.run(["git", "-C", str(origin), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(origin), "-c", "user.name=t", "-c", "user.email=t@e", "commit", "-qm", "b"],
                   check=True)
    rt.lease_owner = rt.ledger.acquire_lease("scheduler")
    _hints, result = audit_sweep(rt, lifecycle, SWEEP, Upstream(), rt.knowledge.fetch())
    companion_id = stage_baseline_companion(rt, lifecycle, rt.lease_owner, SWEEP, result, rt.knowledge.fetch())
    assert companion_id is not None
    (item,) = _items(tmp_path, "open_companion_pr")
    (path,) = item["body"]["files"]
    assert path == "adapters/demoadapter/release_baseline.yaml"
    assert f"audited_sha: {'b' * 40}" in item["body"]["files"][path] and "# fingerprints are generated" in item["body"]["files"][path]
    assert "release baseline" in item["body"]["title"]
    assert stage_baseline_companion(rt, lifecycle, rt.lease_owner, SWEEP, result, rt.knowledge.fetch()) is None   # once per sweep
    assert any("baseline update" in i["reason"] for i in rt.ledger.human_queue("demo"))


def test_no_reconciliation_means_no_companion(tmp_path):
    rt, lifecycle = _flow_runtime(tmp_path)
    clean = ReleaseAuditResult("a" * 40, "b" * 40, (), (), {}, {"baseline_file": "release_baseline.yaml"})
    assert stage_baseline_companion(rt, lifecycle, "owner", SWEEP, clean, "0" * 40) is None


def test_the_audit_reads_the_fetched_revision_not_a_stale_checkout(tmp_path):
    plugin = PLUGIN.replace('"detail": "gone"',
                            '"detail": (__import__("pathlib").Path(knowledge_root) / "repos/demo/core/rules.md").read_text()[-30:]')
    rt, lifecycle = _with_plugin(tmp_path, plugin)
    origin = tmp_path / "origin"
    page = origin / "knowledge" / "repos" / "demo" / "core" / "rules.md"
    page.write_text(page.read_text() + "\n<!-- only on remote main -->\n")
    subprocess.run(["git", "-C", str(origin), "-c", "user.name=t", "-c", "user.email=t@e", "commit", "-qam", "m"],
                   check=True)
    hints, _result = audit_sweep(rt, lifecycle, SWEEP, Upstream(), rt.knowledge.fetch())
    assert "only on remote main" in hints["repos/demo/core/rules.md"][0]["detail"]


def test_comments_inside_a_block_do_not_split_it():
    committed = "upstream:\n  repository: org/up\n# pinned by hand\n  audited_sha: aaaa\n\n# next\ninventories: {}\n"
    text = baseline_text(committed, {"upstream": {"repository": "org/up", "audited_sha": "bbbb"}})
    assert "aaaa" not in text and yaml.safe_load(text)["upstream"]["audited_sha"] == "bbbb"
    assert "# next\ninventories: {}" in text


def test_a_failing_baseline_companion_never_blocks_the_sweep(tmp_path, monkeypatch):
    from infermatrix_copilot.kb_service import scheduler as scheduler_module
    from infermatrix_copilot.kb_service.scheduler import Scheduler

    rt, lifecycle = _with_plugin(tmp_path, PLUGIN)
    lifecycle = replace(lifecycle, full_name="org/up")
    rt.registry["demo"] = lifecycle
    ran = []

    def boom(*args, **kwargs):
        raise RuntimeError("github down")

    monkeypatch.setattr(scheduler_module, "detect_release", lambda *a, **k: dict(SWEEP))
    monkeypatch.setattr(scheduler_module, "audit_sweep", lambda *a, **k: ({"p.md": []}, None))
    monkeypatch.setattr(scheduler_module, "stage_baseline_companion", boom)
    monkeypatch.setattr(scheduler_module, "run_sweep", lambda *a, **k: ran.append(k) or {
        "changesets": [], "breaker": "", "complete": False})
    Scheduler(rt, intake_every=10**9)._repo_tick(lifecycle)
    assert ran and ran[0]["audit_hints"] == {"p.md": []}
    assert any("baseline update" in i["reason"] for i in rt.ledger.human_queue("demo"))


def test_a_companion_that_keeps_failing_to_publish_never_blocks_later_sweeps(tmp_path, monkeypatch):
    from infermatrix_copilot.kb_service import scheduler as scheduler_module
    from infermatrix_copilot.kb_service.scheduler import Scheduler

    rt, lifecycle = _with_plugin(tmp_path, PLUGIN)
    lifecycle = replace(lifecycle, full_name="org/up")
    rt.registry["demo"] = lifecycle
    rt.lease_owner = rt.ledger.acquire_lease("scheduler")
    staged = rt.ledger.new_changeset_id("demo", "companion")
    rt.ledger.stage_intake(rt.lease_owner, "demo", staged, kind="companion", status="companion_staged",
                           verdicts=[], human_reason="", drafted_events=[], detail={"for_changeset": ""})
    ran = []

    def boom(*args, **kwargs):
        raise RuntimeError("outbox unavailable")

    monkeypatch.setattr(scheduler_module, "publish_companion", boom)
    monkeypatch.setattr(scheduler_module, "detect_release", lambda *a, **k: dict(SWEEP))
    monkeypatch.setattr(scheduler_module, "audit_sweep", lambda *a, **k: ({}, None))
    monkeypatch.setattr(scheduler_module, "run_sweep", lambda *a, **k: ran.append(1) or {
        "changesets": [], "breaker": "", "complete": False})
    scheduler = Scheduler(rt, intake_every=10**9, release_every=0)
    scheduler._repo_tick(lifecycle)
    scheduler._repo_tick(lifecycle)                        # the second tick after the failure
    assert len(ran) == 2
