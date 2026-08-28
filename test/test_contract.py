"""The public contract surface: the structured review result, the capability
handshake, and the import direction that keeps them stable. All offline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infermatrix_copilot import contract
from infermatrix_copilot import run_status as rs


def _run(tmp_path: Path, *, state: str = rs.DONE, updates: dict | None = None,
         events: list[dict] | None = None, note: str = "") -> Path:
    """A finished run directory with just the artifacts the assembler reads."""
    run_dir = tmp_path / "run-20260828-101010-abc123"
    run_dir.mkdir(parents=True, exist_ok=True)
    rs.init_queued(run_dir, run_id=run_dir.name, owner_server_id="S1",
                   owner_server_pid=1)
    rs.mark(run_dir, state, note=note)
    (run_dir / "progress.json").write_text(json.dumps({
        "completed": {"review": {"summary": "ok",
                                 "outputs": {"state_updates": updates or {}}}},
    }), encoding="utf-8")
    if events:
        (run_dir / "run_trace.jsonl").write_text(
            "\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    return run_dir


# ── the structured result ─────────────────────────────────────────────────────
def test_result_reads_the_verdict_as_a_field_not_from_markdown(tmp_path):
    """Scraping `**Verdict:** …` back out of prose would make a wording change
    silently change what a bot posts."""
    run_dir = _run(tmp_path, updates={
        "review_verdict": "REQUEST CHANGES",
        "review_summary": "2 findings.\n\n**Verdict:** REQUEST CHANGES",
        "pr_head_sha": "a" * 40,
    })
    result = contract.build_review_result(run_dir)
    assert result["verdict"] == "REQUEST CHANGES"
    assert result["reviewed_head_sha"] == "a" * 40
    assert result["state"] == rs.DONE
    assert result["contract_version"] == contract.STRICT_API_VERSION


def test_result_whitelists_comment_fields(tmp_path):
    """Internal bookkeeping seen on real runs must not cross the boundary."""
    run_dir = _run(tmp_path, updates={"review_comments": [{
        "file": "a.py", "line": 3, "severity": "major", "comment": "c",
        "evidence": "e", "suggestion": "s",
        "_verified": True, "_anchor_unverified": False,
        "corroborated_by": ["lens-1"],
    }]})
    (comment,) = contract.build_review_result(run_dir)["comments"]
    assert comment == {"file": "a.py", "line": 3, "severity": "major",
                       "comment": "c", "evidence": "e", "suggestion": "s"}


def test_unknown_comment_keys_are_dropped_by_default(tmp_path):
    """An allow-list, so a future internal key is excluded without anyone
    remembering to exclude it."""
    run_dir = _run(tmp_path, updates={
        "review_comments": [{"file": "a.py", "some_future_internal": 1}]})
    assert contract.build_review_result(run_dir)["comments"] == [{"file": "a.py"}]


def test_stale_head_is_a_terminal_structured_fact(tmp_path):
    """The executor checkpoints only successful steps, so the mismatch has to
    survive in the trace — and it has to reach the caller as `stale`, not as
    prose they must parse."""
    run_dir = _run(tmp_path, state=rs.BLOCKED, note="head moved",
                   events=[{"ts": 1, "kind": "expected_head_mismatch", "pr": 7,
                            "expected": "b" * 40, "actual": "c" * 40}])
    result = contract.build_review_result(run_dir)
    assert result["stale"] is True
    assert result["expected_head_sha"] == "b" * 40
    assert result["actual_head_sha"] == "c" * 40
    assert result["state"] == rs.BLOCKED and result["note"] == "head moved"


def test_result_degrades_for_a_run_that_died_before_reviewing(tmp_path):
    """No progress.json, no trace: state plus empty fields, never an exception."""
    run_dir = tmp_path / "run-20260828-101010-dead01"
    run_dir.mkdir()
    rs.init_queued(run_dir, run_id=run_dir.name, owner_server_id="S1",
                   owner_server_pid=1)
    rs.mark(run_dir, rs.FAILED, note="tier not configured")
    result = contract.build_review_result(run_dir)
    assert result["state"] == rs.FAILED and result["note"] == "tier not configured"
    assert result["verdict"] == "" and result["comments"] == []
    assert result["stale"] is False


def test_result_surfaces_planner_and_capability_diagnostics(tmp_path):
    run_dir = _run(tmp_path, events=[
        {"ts": 1, "kind": "review_plan", "depth": "standard",
         "planner": "llm-fallback", "planner_error": "unavailable"},
        {"ts": 2, "kind": "capability_gap", "capability": "review.planner",
         "effect": "empty_reply (stop_reason=max_tokens)"},
    ])
    diagnostics = contract.build_review_result(run_dir)["diagnostics"]
    assert diagnostics["review_plan"][0]["planner_error"] == "unavailable"
    assert diagnostics["capability_gap"][0]["capability"] == "review.planner"


def test_unknown_run_is_explicit_not_an_error():
    """A bot holding an id it can no longer match must be able to tell "lost"
    from "still running"."""
    result = contract.unknown_run_result("run-nope")
    assert result["state"] == "unknown" and result["run_id"] == "run-nope"


# ── handshake ─────────────────────────────────────────────────────────────────
def test_capabilities_reports_the_real_worker_count():
    """The MCP server drains its queue with one worker, so Strict requests
    serialize; advertising anything else would invite a bot to fan out."""
    caps = contract.capabilities(max_strict_workers=1)
    assert caps["max_strict_workers"] == 1
    assert caps["strict_api_version"] == contract.STRICT_API_VERSION
    assert caps["supports_expected_head"] is True
    assert caps["supports_structured_result"] is True


def test_capabilities_reports_missing_file_locking():
    assert contract.capabilities(supports_file_locking=False)[
        "supports_file_locking"] is False


# ── import direction ──────────────────────────────────────────────────────────
def test_contract_imports_no_server_module():
    """The servers import down into `contract`, never the reverse. A cycle here
    is what would make the "only supported import surface" claim false."""
    import ast

    src = Path(contract.__file__).read_text(encoding="utf-8")
    imported: set[str] = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
            imported.update(a.name for a in node.names)
    assert not {"mcp_server", "thin_mcp_server"} & imported


def test_get_result_attaches_the_structured_result(settings, tmp_path):
    """The additive `result` key, alongside the report paging kept for hosts
    that already page it."""
    from infermatrix_copilot.mcp_server import CopilotMCP

    core = CopilotMCP(settings)
    try:
        run_dir = _run(Path(settings.run_root),
                       updates={"review_verdict": "APPROVE"})
        (run_dir / "RUN_REPORT.md").write_text("# report", encoding="utf-8")
        out = core.get_result(run_dir.name)
        assert out["result"]["verdict"] == "APPROVE"
        assert out["report"] == "# report"  # back-compat preserved
    finally:
        core.close()


def test_get_result_on_an_unknown_run_id_does_not_raise(settings):
    from infermatrix_copilot.mcp_server import CopilotMCP

    core = CopilotMCP(settings)
    try:
        out = core.get_result("run-20260828-101010-0f0f0f")
        assert out["state"] == "unknown"
        assert out["result"]["state"] == "unknown"
    finally:
        core.close()


@pytest.mark.parametrize("bad", ["../escape", "not-a-run-id", "",
                                 "run-20260828-101010-../../x"])
def test_get_result_still_refuses_a_malformed_run_id(settings, bad):
    """`unknown` is for a well-formed id that merely does not exist. A malformed
    or escaping id is a rejected argument, not a polite empty result — softening
    it would turn the traversal guard into a silent no-op."""
    from infermatrix_copilot.mcp_server import CopilotMCP

    core = CopilotMCP(settings)
    try:
        with pytest.raises(ValueError):
            core.get_result(bad)
    finally:
        core.close()
