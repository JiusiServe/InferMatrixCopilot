"""MCP server guardrails: read-only policy (incl. tamper defense), single-writer
run_status + ownership-aware reconciliation, report pagination, and the fact that
the exposed tool set is read-only only. All offline."""

from __future__ import annotations

import asyncio
import json
import os
import stat

import pytest

from omni_copilot import run_status as rs
from omni_copilot.cli.copilot import Copilot
from omni_copilot.mcp_policy import PolicyError, enforce_mcp_policy
from omni_copilot.task_spec import READ_ONLY_KINDS, TaskSpec

ALLOW = ["vllm-omni"]


# ── policy gate (the structural read-only guarantee) ──────────────────────────
def test_policy_accepts_read_only_kinds_and_forces_post_off():
    for kind, extra in [("pr_review", {"pr": 5}),
                        ("issue_answer", {"issue": 9}),
                        ("issue_filter", {})]:
        spec = enforce_mcp_policy({"kind": kind, "repo": "vllm-omni", **extra},
                                  allowed_repos=ALLOW)
        assert spec.kind == kind
        assert spec.post is False and spec.report_only is False


@pytest.mark.parametrize("bad", [
    {"kind": "pr_rebase", "repo": "vllm-omni"},      # write-capable
    {"kind": "pr_debug", "repo": "vllm-omni"},       # mutates (checkout_branch)
    {"kind": "repo_profile", "repo": "vllm-omni"},   # writes knowledge
    {"kind": "pr_review", "repo": "some-other-repo"},  # off allowlist
    {"kind": "pr_review", "repo": "vllm-omni", "pr": -3},  # non-positive
    {"kind": "pr_review", "repo": "vllm-omni", "pr": "abc"},  # non-int
    {"kind": None, "repo": "vllm-omni"},             # missing kind
])
def test_policy_refuses_unsafe_requests(bad):
    with pytest.raises(PolicyError):
        enforce_mcp_policy(bad, allowed_repos=ALLOW)


def test_policy_strips_unknown_params_and_post_flag():
    spec = enforce_mcp_policy(
        {"kind": "issue_answer", "repo": "vllm-omni", "issue": 1,
         "post": True, "params": {"force_push": True, "x": 1}},
        allowed_repos=ALLOW)
    assert spec.post is False
    assert spec.params == {}  # a tampered step knob cannot ride through


# ── run_status: single writer + preserved ownership ───────────────────────────
def test_status_lifecycle_preserves_ownership(tmp_path):
    run_dir = tmp_path / "run-20260715-101010-abc123"
    rs.init_queued(run_dir, run_id=run_dir.name, owner_server_id="S1",
                   owner_server_pid=os.getpid())
    assert rs.read_status(run_dir)["state"] == rs.QUEUED
    rs.mark_child_started(run_dir, child_pid=4242)
    rs.mark(run_dir, rs.RUNNING)
    final = rs.mark(run_dir, rs.DONE)
    assert final["state"] == rs.DONE
    assert final["child_pid"] == 4242          # child pid preserved
    assert final["owner_server_id"] == "S1"    # ownership preserved across writes


# ── reconciliation ────────────────────────────────────────────────────────────
def test_pid_alive_treats_windows_invalid_pid_as_dead(monkeypatch):
    def invalid_pid(_pid, _signal):
        raise OSError(87, "The parameter is incorrect")

    monkeypatch.setattr(rs.os, "kill", invalid_pid)
    assert rs.pid_alive(4242) is False


def test_reconcile_after_wait_terminalizes_only_non_terminal(tmp_path):
    live = tmp_path / "run-20260715-101010-aaa111"
    rs.init_queued(live, run_id=live.name, owner_server_id="S", owner_server_pid=os.getpid())
    rs.mark(live, rs.RUNNING)
    assert rs.reconcile_after_wait(live)["state"] == rs.INTERRUPTED

    done = tmp_path / "run-20260715-101011-bbb222"
    rs.init_queued(done, run_id=done.name, owner_server_id="S", owner_server_pid=os.getpid())
    rs.mark(done, rs.DONE)
    rs.reconcile_after_wait(done)
    assert rs.read_status(done)["state"] == rs.DONE  # untouched


def test_reconcile_if_dead_respects_live_owner(tmp_path):
    run_root = tmp_path
    # live owner -> its queued run must be left alone (the multi-server bug)
    rs.register_server(run_root, "LIVE", os.getpid())
    live = tmp_path / "run-20260715-101012-ccc333"
    rs.init_queued(live, run_id=live.name, owner_server_id="LIVE", owner_server_pid=os.getpid())
    rs.reconcile_if_dead(live, run_root)
    assert rs.read_status(live)["state"] == rs.QUEUED

    # dead owner + no child -> reconciled to interrupted
    dead = tmp_path / "run-20260715-101013-ddd444"
    rs.init_queued(dead, run_id=dead.name, owner_server_id="GONE", owner_server_pid=2 ** 31 - 1)
    assert rs.reconcile_if_dead(dead, run_root)["state"] == rs.INTERRUPTED

    # dead owner but a LIVE child -> left (the child will write its own terminal)
    childrun = tmp_path / "run-20260715-101014-eee555"
    rs.init_queued(childrun, run_id=childrun.name, owner_server_id="GONE", owner_server_pid=2 ** 31 - 1)
    rs.mark_child_started(childrun, child_pid=os.getpid())  # our pid = alive
    rs.reconcile_if_dead(childrun, run_root)
    assert rs.read_status(childrun)["state"] != rs.INTERRUPTED


# ── reserve / execute_reserved (the child path) ───────────────────────────────
def test_reserve_run_is_fast_and_persists_queued(settings):
    cop = Copilot(settings)
    run_id = cop.reserve_run(TaskSpec(kind="pr_review", repo="vllm-omni", pr=1),
                             owner_server_id="S1", owner_server_pid=1234)
    run_dir = settings.run_root / run_id
    assert rs.read_status(run_dir)["state"] == rs.QUEUED
    req = run_dir / "request.json"
    assert json.loads(req.read_text())["kind"] == "pr_review"
    assert stat.S_IMODE(req.stat().st_mode) == 0o600  # least-privilege perms
    # no LLM was needed (the fixture LLM is unconfigured anyway)
    assert cop.llm.available is False


def test_execute_reserved_refuses_tampered_request_in_process(settings):
    cop = Copilot(settings)
    run_id = cop.reserve_run(TaskSpec(kind="pr_review", repo="vllm-omni", pr=2),
                             owner_server_id="S1", owner_server_pid=1234)
    run_dir = settings.run_root / run_id
    # a same-user process rewrites the reserved request to a write-capable task
    (run_dir / "request.json").write_text(json.dumps(
        {"kind": "pr_rebase", "repo": "evil", "pr": 2, "post": True}))
    code = cop.execute_reserved(run_id)
    st = rs.read_status(run_dir)
    assert code == 1
    assert st["state"] == rs.FAILED
    assert "not permitted" in st["note"]
    assert st["child_pid"] is not None  # child wrote its own pid first


def test_contained_run_dir_rejects_traversal(settings):
    cop = Copilot(settings)
    for bad in ["../etc", "run-x", "run-20260715-101010-abc123/../..", "", "nope"]:
        with pytest.raises(ValueError):
            cop._contained_run_dir(bad)


def test_cli_declined_confirm_leaves_no_run_dir(settings, monkeypatch):
    """CLI path is unchanged: it gates (plan-review + confirm) BEFORE creating a
    run dir, so a declined confirmation leaves no run-* directory behind. (The
    reserve-before-plan shape is MCP-only.)"""
    monkeypatch.setattr("builtins.input", lambda *a, **k: "n")
    cop = Copilot(settings)
    rc = cop.run_task(TaskSpec(kind="pr_review", repo="vllm-omni", pr=1), assume_yes=False)
    assert rc == 1  # user aborted
    dirs = list(settings.run_root.glob("run-*")) if settings.run_root.exists() else []
    assert dirs == []


# ── server core: pagination + status shape + read-only tool set ───────────────
def _core(settings):
    from omni_copilot.mcp_server import CopilotMCP
    return CopilotMCP(settings)


def test_get_result_pagination(settings):
    core = _core(settings)
    rid = "run-20260715-120000-abc123"
    rd = settings.run_root / rid
    rd.mkdir(parents=True)
    rs.init_queued(rd, run_id=rid, owner_server_id=core.server_id, owner_server_pid=core.pid)
    rs.mark(rd, rs.DONE)
    (rd / "RUN_REPORT.md").write_text("A" * 50)
    core.settings.mcp_report_max_bytes = 20
    r0 = core.get_result(rid, 0)
    assert len(r0["report"]) == 20 and r0["next_offset"] == 20
    assert r0["report_path"].endswith("RUN_REPORT.md")
    r2 = core.get_result(rid, 40)
    assert r2["next_offset"] is None  # last page
    core.close()


def test_get_result_running_has_no_report(settings):
    core = _core(settings)
    rid = "run-20260715-120001-def456"
    rd = settings.run_root / rid
    rd.mkdir(parents=True)
    rs.init_queued(rd, run_id=rid, owner_server_id=core.server_id, owner_server_pid=core.pid)
    rs.mark(rd, rs.RUNNING)  # owner is this live server -> not reconciled
    out = core.get_result(rid)
    assert out["state"] == rs.RUNNING and "report" not in out
    core.close()


def test_get_status_returns_status_and_optional_progress(settings):
    core = _core(settings)
    rid = "run-20260715-120002-aaa111"
    rd = settings.run_root / rid
    rd.mkdir(parents=True)
    rs.init_queued(rd, run_id=rid, owner_server_id=core.server_id, owner_server_pid=core.pid)
    out = core.get_status(rid)
    assert out["status"]["state"] == rs.QUEUED and out["progress"] is None
    (rd / "progress.json").write_text(json.dumps({"completed": {"fetch": {}}}))
    assert core.get_status(rid)["progress"] == {"completed": {"fetch": {}}}
    core.close()


def test_mcp_docs_are_repo_scoped(settings, tmp_path):
    k = tmp_path / "knowledge"
    (k / "general").mkdir(parents=True)
    (k / "general" / "guide.md").write_text(
        "GENERAL SEARCH NEEDLE", encoding="utf-8")
    (k / "repos" / "vllm-omni").mkdir(parents=True)
    (k / "repos" / "vllm-omni" / "rules.md").write_text(
        "REPO SEARCH NEEDLE", encoding="utf-8")
    (k / "repos" / "other").mkdir(parents=True)
    (k / "repos" / "other" / "secret.md").write_text(
        "OTHER SECRET", encoding="utf-8")
    adapter = settings.adapters_dir / "vllm_omni"
    adapter.mkdir(parents=True)
    (adapter / "manifest.yaml").write_text(json.dumps({
        "name": "vllm_omni", "repo": {"path": str(tmp_path / "repo")},
        "knowledge": {"repo_subdir": "repos/vllm-omni"},
    }), encoding="utf-8")
    settings.knowledge_dir = k
    core = _core(settings)
    assert core.doc_search("SEARCH NEEDLE")["matches"]
    assert "REPO SEARCH" in core.doc_read("repos/vllm-omni/rules.md")["content"]
    with pytest.raises(ValueError, match="outside the selected"):
        core.doc_read("repos/other/secret.md")
    core.close()


def test_exposed_tools_are_read_only_only(settings):
    pytest.importorskip("mcp")
    from omni_copilot.mcp_server import build_mcp

    mcp = build_mcp(settings)
    names = sorted(t.name for t in asyncio.run(mcp.list_tools()))
    assert names == ["doc_read", "doc_search", "get_result", "get_status",
                     "list_playbooks",
                     "start_issue_answer", "start_issue_triage", "start_review"]
    assert not any(bad in n for n in names
                   for bad in ("post", "push", "debug", "rebase"))


def test_subprocess_tamper_defense(settings):
    """Full child-subprocess path: `python -m omni_copilot --execute-reserved`
    re-enforces policy on a rewritten request.json and terminalizes to failed,
    with its stdout isolated to console.log."""
    core = _core(settings)
    run_id = core.copilot.reserve_run(
        TaskSpec(kind="pr_review", repo="vllm-omni", pr=3),
        owner_server_id=core.server_id, owner_server_pid=core.pid)
    rd = settings.run_root / run_id
    (rd / "request.json").write_text(json.dumps(
        {"kind": "pr_rebase", "repo": "evil", "pr": 3, "post": True,
         "params": {"force_push": True}}))
    core._launch(run_id)  # real subprocess; blocks until it exits
    st = rs.read_status(rd)
    assert st["state"] == rs.FAILED
    assert st["owner_server_id"] == core.server_id
    assert (rd / "console.log").exists()
    core.close()
