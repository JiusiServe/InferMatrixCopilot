"""Provenance: unrecorded knowledge changes pause auto-merge, block activation and get reverted."""

from __future__ import annotations

import subprocess
import time
from dataclasses import replace

from infermatrix_copilot.kb_service.audit import AUDIT_CURSOR, GRACE, audit_main  # noqa: F401
from infermatrix_copilot.kb_service.scheduler import Scheduler
from test_kb_flow import _flow_runtime
from test_kb_intake_gate import PAGE


def _git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout.strip()


def _land(origin, rel: str, text: str, message: str) -> str:
    target = origin / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    _git(origin, "add", "-A")
    _git(origin, "-c", "user.name=t", "-c", "user.email=t@e", "commit", "-q", "-m", message)
    return _git(origin, "rev-parse", "HEAD")


def _setup(tmp_path):
    rt, lifecycle = _flow_runtime(tmp_path)
    rt.clock = lambda: time.time() + GRACE + 60          # every commit made in the test is old enough
    rt.lease_owner = rt.ledger.acquire_lease("scheduler")
    scheduler = Scheduler(rt)
    assert audit_main(rt, scheduler._pause) == []        # the first run records the baseline
    assert rt.ledger.get_cursor("*", AUDIT_CURSOR) == rt.knowledge.main_sha()
    return rt, lifecycle, scheduler, tmp_path / "origin"


def test_a_knowledge_change_without_a_record_pauses_auto_merge(tmp_path):
    rt, lifecycle, scheduler, origin = _setup(tmp_path)
    page = origin / "knowledge" / PAGE
    sha = _land(origin, f"knowledge/{PAGE}", page.read_text() + "\n<!-- pushed around the gate -->\n",
                "hotfix knowledge directly")
    (finding,) = audit_main(rt, scheduler._pause)
    assert sha[:12] in finding and "(no PR)" in finding
    assert rt.ledger.repo_state("demo")["paused"]
    assert any("provenance" in item["reason"] for item in rt.ledger.human_queue("demo"))
    assert rt.ledger.get_cursor("*", AUDIT_CURSOR) == sha
    assert audit_main(rt, scheduler._pause) == []        # audited once


def test_recorded_merges_and_code_changes_pass(tmp_path):
    rt, lifecycle, scheduler, origin = _setup(tmp_path)
    _land(origin, "src/app.py", "x = 1\n", "a code change (#40)")
    page = origin / "knowledge" / PAGE
    merged = _land(origin, f"knowledge/{PAGE}", page.read_text() + "\n<!-- via the gate -->\n",
                   "Merge pull request #42 from JiusiServe/kb/demo/x")
    changeset = rt.ledger.new_changeset_id("demo", "intake")
    rt.ledger.stage_intake(rt.lease_owner, "demo", changeset, detail={}, status="merged",
                           verdicts=[], human_reason="", drafted_events=[])
    rt.ledger.update_changeset(changeset, pr_number=42, merge_sha=merged)
    assert audit_main(rt, scheduler._pause) == []
    assert not rt.ledger.repo_state("demo")["paused"]
    assert rt.ledger.get_cursor("*", AUDIT_CURSOR) == merged


def test_our_own_merge_waiting_for_its_receipt_is_not_unknown(tmp_path):
    rt, lifecycle, scheduler, origin = _setup(tmp_path)
    before = rt.ledger.get_cursor("*", AUDIT_CURSOR)
    _git(origin, "checkout", "-q", "-b", "kb/demo/r")
    page = origin / "knowledge" / PAGE
    head = _land(origin, f"knowledge/{PAGE}", page.read_text() + "\n<!-- ours -->\n", "knowledge change")
    _git(origin, "checkout", "-q", "main")
    _git(origin, "-c", "user.name=q", "-c", "user.email=q@e", "merge", "-q", "--no-ff", "-m", "merged by us", head)
    changeset = rt.ledger.new_changeset_id("demo", "intake")
    rt.ledger.stage_intake(rt.lease_owner, "demo", changeset, detail={}, status="merge_requested",
                           verdicts=[], human_reason="", drafted_events=[])
    rt.ledger.update_changeset(changeset, pr_number=46, head_sha=head)
    assert audit_main(rt, scheduler._pause) == []        # the receipt is on its way
    assert not rt.ledger.repo_state("demo")["paused"]
    assert rt.ledger.get_cursor("*", AUDIT_CURSOR) == before   # looked at again next tick


def test_repositories_not_in_auto_merge_are_only_traced(tmp_path):
    from infermatrix_copilot.trace_store import TraceStore

    rt, lifecycle, scheduler, origin = _setup(tmp_path)
    rt.registry["demo"] = replace(rt.registry["demo"], mode="shadow")
    rt.traces = TraceStore(tmp_path / "traces", environ={})
    page = origin / "knowledge" / PAGE
    _land(origin, f"knowledge/{PAGE}", page.read_text() + "\n<!-- shadow -->\n", "shadow change")
    assert len(audit_main(rt, scheduler._pause)) == 1
    assert not rt.ledger.repo_state("demo")["paused"]
    (record,) = rt.traces.query(kind="outcome")
    assert record["result"]["outcome"] == "unrecorded_merge" and record["result"]["paused"] == []


def test_knowledge_outside_a_repository_scope_pauses_everything(tmp_path):
    rt, lifecycle, scheduler, origin = _setup(tmp_path)
    _land(origin, "knowledge/tools/check.md", "changed around the gate\n", "tools")
    assert len(audit_main(rt, scheduler._pause)) == 1
    assert rt.ledger.repo_state("*")["paused"]


def test_a_commit_message_citing_a_recorded_pr_is_no_proof(tmp_path):
    rt, lifecycle, scheduler, origin = _setup(tmp_path)
    page = origin / "knowledge" / PAGE
    merged = _land(origin, f"knowledge/{PAGE}", page.read_text() + "\n<!-- via the gate -->\n",
                   "Merge pull request #42 from JiusiServe/kb/demo/x")
    changeset = rt.ledger.new_changeset_id("demo", "intake")
    rt.ledger.stage_intake(rt.lease_owner, "demo", changeset, detail={}, status="merged",
                           verdicts=[], human_reason="", drafted_events=[])
    rt.ledger.update_changeset(changeset, pr_number=42, merge_sha=merged)
    sneaky = _land(origin, f"knowledge/{PAGE}", page.read_text() + "\n<!-- sneaked in -->\n",
                   "Follow-up correction (#42)")
    (finding,) = audit_main(rt, scheduler._pause)
    assert sneaky[:12] in finding and rt.ledger.repo_state("demo")["paused"]


def test_a_queue_merge_of_the_recorded_head_is_proof(tmp_path):
    rt, lifecycle, scheduler, origin = _setup(tmp_path)
    _git(origin, "checkout", "-q", "-b", "kb/demo/y")
    page = origin / "knowledge" / PAGE
    head = _land(origin, f"knowledge/{PAGE}", page.read_text() + "\n<!-- branch -->\n", "knowledge change")
    _git(origin, "checkout", "-q", "main")
    _git(origin, "-c", "user.name=q", "-c", "user.email=q@e", "merge", "-q", "--no-ff", "-m", "queue merge", head)
    changeset = rt.ledger.new_changeset_id("demo", "intake")
    rt.ledger.stage_intake(rt.lease_owner, "demo", changeset, detail={}, status="merged",
                           verdicts=[], human_reason="", drafted_events=[])
    rt.ledger.update_changeset(changeset, pr_number=43, head_sha=head, merge_sha="")
    assert audit_main(rt, scheduler._pause) == []


def test_a_merge_of_a_recorded_head_with_extra_edits_is_caught(tmp_path):
    rt, lifecycle, scheduler, origin = _setup(tmp_path)
    _git(origin, "checkout", "-q", "-b", "kb/demo/z")
    page = origin / "knowledge" / PAGE
    head = _land(origin, f"knowledge/{PAGE}", page.read_text() + "\n<!-- branch -->\n", "knowledge change")
    _git(origin, "checkout", "-q", "main")
    _git(origin, "-c", "user.name=q", "-c", "user.email=q@e", "merge", "-q", "--no-ff", "--no-commit", head)
    (origin / "knowledge" / "repos" / "demo" / "core" / "_index.md").write_text("# core\n\nsmuggled\n")
    _git(origin, "add", "-A")
    _git(origin, "-c", "user.name=q", "-c", "user.email=q@e", "commit", "-q", "-m", "merge with extras")
    changeset = rt.ledger.new_changeset_id("demo", "intake")
    rt.ledger.stage_intake(rt.lease_owner, "demo", changeset, detail={}, status="merged",
                           verdicts=[], human_reason="", drafted_events=[])
    rt.ledger.update_changeset(changeset, pr_number=44, head_sha=head, merge_sha="")
    (finding,) = audit_main(rt, scheduler._pause)
    assert "unrecorded knowledge change" in finding and rt.ledger.repo_state("demo")["paused"]


def test_a_merge_that_adds_an_executable_bit_is_caught(tmp_path):
    rt, lifecycle, scheduler, origin = _setup(tmp_path)
    _git(origin, "checkout", "-q", "-b", "kb/demo/m")
    page = origin / "knowledge" / PAGE
    head = _land(origin, f"knowledge/{PAGE}", page.read_text() + "\n<!-- branch -->\n", "knowledge change")
    _git(origin, "checkout", "-q", "main")
    _git(origin, "-c", "user.name=q", "-c", "user.email=q@e", "merge", "-q", "--no-ff", "--no-commit", head)
    _git(origin, "update-index", "--chmod=+x", f"knowledge/{PAGE}")
    _git(origin, "-c", "user.name=q", "-c", "user.email=q@e", "commit", "-q", "-m", "merge with a mode change")
    changeset = rt.ledger.new_changeset_id("demo", "intake")
    rt.ledger.stage_intake(rt.lease_owner, "demo", changeset, detail={}, status="merged",
                           verdicts=[], human_reason="", drafted_events=[])
    rt.ledger.update_changeset(changeset, pr_number=45, head_sha=head, merge_sha="")
    assert len(audit_main(rt, scheduler._pause)) == 1
