from pathlib import Path

from omni_copilot.scopes import PathScope, ToolScope, post_plan_scope, pre_plan_scope, read_only_scope
from omni_copilot.tools import dispatch


def test_pre_plan_scope_blocks_source_writes(tmp_path: Path):
    plan_dir = tmp_path / "plans"
    scope = pre_plan_scope(plan_dir)

    ok = scope.check("write_file", write_path=plan_dir / "plan-v0.md")
    assert ok.allowed and not ok.out_of_scope

    refused = scope.check("write_file", write_path=tmp_path / "src" / "core.py")
    assert not refused.allowed

    # run_shell is not in the pre-plan tool set at all
    assert not scope.check("run_shell").allowed


def test_post_plan_scope_records_out_of_scope(tmp_path: Path):
    ws = tmp_path / "ws"
    scope = post_plan_scope(ws, primary=(f"{ws.as_posix()}/mod_a*",))
    inside = scope.check("write_file", write_path=ws / "mod_a.py")
    assert inside.allowed and not inside.out_of_scope
    outside = scope.check("write_file", write_path=ws / "mod_b.py")
    assert outside.allowed and outside.out_of_scope
    wall = scope.check("write_file", write_path=tmp_path / "elsewhere.py")
    assert not wall.allowed


def test_read_only_scope_refuses_writes():
    scope = read_only_scope()
    assert scope.check("read_file").allowed
    assert not scope.check("write_file", write_path="/tmp/x").allowed
    assert not scope.check("edit_file", write_path="/tmp/x").allowed


def test_dispatch_enforces_scope_and_traces(tmp_path: Path, trace):
    plan_dir = tmp_path / "plans"
    scope = pre_plan_scope(plan_dir)

    out = dispatch("write_file", {"path": str(tmp_path / "src.py"), "content": "x"},
                   scope=scope, trace=trace)
    assert not out["ok"] and "refused" in out["error"]
    assert not (tmp_path / "src.py").exists()
    assert any(True for _ in trace.events("tool_refused"))

    out = dispatch("write_file", {"path": str(plan_dir / "plan.md"), "content": "p"},
                   scope=scope, trace=trace)
    assert out["ok"]
    assert (plan_dir / "plan.md").read_text() == "p"


def test_dispatch_out_of_scope_executes_and_records(tmp_path: Path, trace):
    ws = tmp_path / "ws"
    scope = ToolScope(
        name="post_plan", allowed_tools=frozenset({"write_file"}),
        path_scope=PathScope(writable=(f"{ws.as_posix()}/*",),
                             primary=(f"{ws.as_posix()}/mod_a*",)),
    )
    out = dispatch("write_file", {"path": str(ws / "mod_b.py"), "content": "b"},
                   scope=scope, trace=trace)
    assert out["ok"] and out["out_of_scope"]
    assert (ws / "mod_b.py").exists()
    events = list(trace.events("out_of_scope_edit"))
    assert len(events) == 1 and events[0]["path"].endswith("mod_b.py")


def test_edit_file_requires_unique_match(tmp_path: Path):
    f = tmp_path / "f.txt"
    f.write_text("aaa bbb aaa")
    out = dispatch("edit_file", {"path": str(f), "old": "aaa", "new": "ccc"})
    assert not out["ok"] and "matches 2 times" in out["error"]
    out = dispatch("edit_file", {"path": str(f), "old": "bbb", "new": "ccc"})
    assert out["ok"] and f.read_text() == "aaa ccc aaa"


def test_relative_paths_resolve_against_scope_root(tmp_path):
    """A scope.root makes the agent's repo-relative tool paths resolve against
    the repo tree (a per-PR worktree), not the process cwd — the read_file/grep
    failures on PR-added files. Absolute paths are left untouched."""
    from dataclasses import replace

    from omni_copilot.scopes import read_only_scope
    from omni_copilot.tools import dispatch

    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "new_file.py").write_text("MARKER = 1\n")
    scope = replace(read_only_scope(), root=str(tmp_path))

    rel = dispatch("read_file", {"path": "pkg/new_file.py"}, scope=scope)
    assert rel["ok"] and "MARKER = 1" in rel["result"]

    g = dispatch("grep", {"pattern": "MARKER", "path": "pkg"}, scope=scope)
    assert g["ok"] and "new_file.py" in g["result"]

    ab = dispatch("read_file", {"path": str(tmp_path / "pkg" / "new_file.py")},
                  scope=scope)
    assert ab["ok"] and "MARKER = 1" in ab["result"]  # absolute untouched

    # no root -> legacy behavior (resolves against cwd; relative miss is fine)
    bare = replace(read_only_scope(), root="")
    miss = dispatch("read_file", {"path": "pkg/new_file.py"}, scope=bare)
    assert not miss["ok"]  # not found against cwd
