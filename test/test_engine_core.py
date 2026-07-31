"""PR4a — engine core, unwired: substate, loop-scoped runtime registry, the
rebase tool pack behind tools.dispatch, the agent loop, and the planner's
exact-repo requires filter.

`test_agent_loop_partial_e2e` drives the real loop + real dispatch + real
filesystem tools with a scripted fake client through the full contract:
plan-gate tool withholding → decision unlock → scoped edits (in-scope,
out-of-scope-recorded, out-of-wall-refused) → completion.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from infermatrix_copilot.playbooks.store import Playbook, PlaybookStore
from infermatrix_copilot.rebase_engine import agent_loop as loop_mod
from infermatrix_copilot.rebase_engine.agent_loop import run_agent_loop
from infermatrix_copilot.rebase_engine.rebase_tools import (
    RebaseBackends, RebasePaths, build_rebase_tools, load_tool_schemas)
from infermatrix_copilot.rebase_engine.runctx import (
    CheckoutLock, RebaseRuntime, RuntimeRegistry)
from infermatrix_copilot.rebase_engine.substate import Substate, SubstateError
from infermatrix_copilot.scopes import PathScope, ToolScope
from infermatrix_copilot.tools import dispatch

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = REPO_ROOT / "adapters/vllm_omni/rebase/tool_schemas.json"


# -- substate ------------------------------------------------------------------

def test_substate_merge_never_clobbers_siblings(tmp_path):
    s = Substate(tmp_path, "run-1")
    s.update({"modules": {"a": {"status": "running"}, "b": {"status": "pending"}}})
    s.update({"modules": {"a": {"status": "done", "exit_code": 0}}})
    data = s.read()
    assert data["modules"]["a"] == {"status": "done", "exit_code": 0}
    assert data["modules"]["b"] == {"status": "pending"}   # sibling survives
    assert data["run_id"] == "run-1"
    # dotted helpers (parent get/update_state_field parity)
    s.set_field("tests.pipeline.failed", 2)
    assert s.get("tests.pipeline.failed") == 2
    assert s.get("tests.pipeline.missing", "dflt") == "dflt"


def test_substate_refuses_foreign_run(tmp_path):
    Substate(tmp_path, "run-1").update({"phase": "init"})
    other = Substate(tmp_path, "run-2")
    with pytest.raises(SubstateError, match="belongs to run"):
        other.read()
    with pytest.raises(SubstateError, match="belongs to run"):
        other.update({"phase": "hijack"})
    # and the original still reads its own state
    assert Substate(tmp_path, "run-1").get("phase") == "init"


def test_substate_corrupt_file_fails_closed(tmp_path):
    (tmp_path / "substate.json").write_text("{not json")
    with pytest.raises(SubstateError, match="unreadable"):
        Substate(tmp_path, "run-1").read()


# -- runtime registry ----------------------------------------------------------

def test_registry_is_loop_scoped(tmp_path):
    reg = RuntimeRegistry()

    async def acquire():
        return reg.get_or_create(tmp_path, "run-1")

    async def acquire_with_loop():
        return reg.get_or_create(tmp_path, "run-1"), asyncio.get_running_loop()

    rt1, loop1 = asyncio.run(acquire_with_loop())
    rt2, loop2 = asyncio.run(acquire_with_loop())
    # a fresh asyncio.run means a fresh loop — the runtime must NOT carry
    # over (its primitives would belong to the dead loop). Keeping loop1
    # alive here also pins that a REUSED id(loop) address cannot alias:
    # the registry keys on the loop OBJECT (weakly), never its id.
    assert loop1 is not loop2
    assert rt1 is not rt2

    async def acquire_twice():
        return reg.get_or_create(tmp_path, "run-1"), \
               reg.get_or_create(tmp_path, "run-1")

    a, b = asyncio.run(acquire_twice())
    assert a is b                       # same loop: one runtime
    with pytest.raises(Exception, match="registered to run"):
        asyncio.run(_acquire_conflict(reg, tmp_path))


async def _acquire_conflict(reg, run_dir):
    reg.get_or_create(run_dir, "run-A")
    reg.get_or_create(run_dir, "run-B")


def test_teardown_bounds_a_hung_finalizer(tmp_path):
    """A blocked finalizer must not hang teardown past the window: it is
    joined against the remaining budget, abandoned, and reported — later
    finalizers still run."""
    import threading as _th
    rt = RebaseRuntime(tmp_path, "run-1")
    ran = []
    release = _th.Event()
    rt.add_finalizer("early", lambda: ran.append("early"))
    rt.add_finalizer("hang", release.wait)          # blocks until released
    rt.add_finalizer("late", lambda: ran.append("late"))
    t0 = __import__("time").monotonic()
    failures = rt.teardown(timeout_sec=0.5)
    elapsed = __import__("time").monotonic() - t0
    release.set()                                   # let the daemon die
    assert elapsed < 5
    assert ran == ["late"]        # newest ran; the hang exhausted the window
    assert any("hung past the teardown window" in f for f in failures)
    # the finalizer behind the hang is skipped AND reported, never silent
    assert any("early" in f and "skipped" in f for f in failures)


def test_runtime_teardown_reverse_order_never_raises(tmp_path):
    rt = RebaseRuntime(tmp_path, "run-1")
    order = []
    rt.add_finalizer("first", lambda: order.append("first"))
    rt.add_finalizer("boom", lambda: (_ for _ in ()).throw(RuntimeError("x")))
    rt.add_finalizer("last", lambda: order.append("last"))
    failures = rt.teardown()
    assert order == ["last", "first"]            # newest-first
    assert failures and "boom" in failures[0]
    assert rt.teardown() == []                   # idempotent
    with pytest.raises(Exception, match="torn down"):
        rt.add_finalizer("late", lambda: None)


def test_checkout_lock_excludes_and_releases(tmp_path):
    a = CheckoutLock(tmp_path, "omni")
    b = CheckoutLock(tmp_path, "omni")
    assert a.acquire()
    assert b.acquire(blocking=False) is False    # excluded
    a.release()
    assert b.acquire(blocking=False) is True
    b.release()
    # runtime-owned lock is released by teardown
    rt = RebaseRuntime(tmp_path, "run-1")
    assert rt.acquire_checkout_lock(tmp_path, "omni")
    assert a.acquire(blocking=False) is False
    rt.teardown()
    assert a.acquire(blocking=False) is True
    a.release()


# -- rebase tool pack ----------------------------------------------------------

@pytest.fixture()
def omni_repo(tmp_path):
    repo = tmp_path / "omni"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "checkout", "-q", "-B", "main"], cwd=repo, check=True)
    for k, v in (("user.name", "t"), ("user.email", "t@e.c")):
        subprocess.run(["git", "config", k, v], cwd=repo, check=True)
    (repo / "mod.py").write_text("def f():\n    return 1\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    subprocess.run(["git", "update-ref", "refs/remotes/origin/main", "HEAD"],
                   cwd=repo, check=True)
    return repo


def _tools(omni_repo, backends=None):
    defs = load_tool_schemas(SCHEMAS)
    return defs, build_rebase_tools(
        defs, RebasePaths(omni_path=str(omni_repo), vllm_path=str(omni_repo)),
        backends)


def test_tool_schemas_load_in_parent_dispatcher_order():
    defs = load_tool_schemas(SCHEMAS)
    assert [d["name"] for d in defs] == [
        "run_shell", "read_file", "write_file", "edit_file", "grep",
        "run_pytest", "run_import_check", "git_show_test_baseline",
        "reproduce", "run_precommit",
        "git_show_upstream", "git_show_omni_main", "git_log_upstream",
        "git_diff", "git_diff_tests_upstream",
        "request_plan_review", "search_debug_memory", "record_debug_memory",
        "skill_manage", "search_skills",
    ]
    with pytest.raises(ValueError, match="has no handler"):
        build_rebase_tools([{"name": "mystery", "description": "?",
                             "input_schema": {}}],
                           RebasePaths(omni_path="/x", vllm_path="/x"))


def test_tool_handlers_parent_shapes(omni_repo):
    _, tools = _tools(omni_repo)

    def call(name, **kw):
        return json.loads(dispatch(name, kw, extra=tools)["result"])

    r = call("read_file", file_path=str(omni_repo / "mod.py"))
    assert r["content"].startswith("1\tdef f():") and r["total_lines"] == 3
    r = call("edit_file", file_path=str(omni_repo / "mod.py"),
             old_string="return 1", new_string="return 2")
    assert r["occurrences"] == 1
    r = call("edit_file", file_path=str(omni_repo / "mod.py"),
             old_string="nope", new_string="x")
    assert r["error"] == "old_string not found in file"
    r = call("run_shell", command="echo hi")
    assert r["exit_code"] == 0 and "hi" in r["stdout"]
    r = call("git_show_omni_main", file_path="mod.py")
    assert "return 1" in r["content"]           # origin/main, pre-edit
    r = call("git_diff")
    assert "mod.py" in r["changed_files"]
    r = call("grep", pattern="return", path=str(omni_repo))
    assert r["count"] >= 1
    # unwired backends fail CLOSED with a visible instruction
    r = call("search_debug_memory", keyword="x")
    assert "not wired" in r["error"]


def test_extra_tool_opt_in_write_scoping(omni_repo, trace):
    _, tools = _tools(omni_repo)
    scope = ToolScope(
        name="module", allowed_tools=frozenset(),
        path_scope=PathScope(writable=(f"{omni_repo}/*",),
                             primary=(f"{omni_repo}/mod.py",)))
    inside = dispatch("write_file",
                      {"file_path": str(omni_repo / "mod.py"), "content": "x"},
                      scope=scope, trace=trace, extra=tools)
    assert inside["ok"] and not inside["out_of_scope"]
    beside = dispatch("write_file",
                      {"file_path": str(omni_repo / "other.py"), "content": "x"},
                      scope=scope, trace=trace, extra=tools)
    assert beside["ok"] and beside["out_of_scope"]     # recorded, never silent
    outside = dispatch("write_file",
                       {"file_path": "/etc/nope", "content": "x"},
                       scope=scope, trace=trace, extra=tools)
    assert not outside["ok"] and "refused" in outside["error"]
    assert not Path("/etc/nope").exists()
    assert any(True for _ in trace.events("out_of_scope_edit"))
    # extras WITHOUT write_path_arg keep the historical bypass
    reads = dispatch("read_file", {"file_path": str(omni_repo / "mod.py")},
                     scope=scope, trace=trace, extra=tools)
    assert reads["ok"]
    # read-only scope refuses declared writes outright
    ro = ToolScope(name="ro", allowed_tools=frozenset(), read_only=True)
    denied = dispatch("write_file",
                      {"file_path": str(omni_repo / "mod.py"), "content": "y"},
                      scope=ro, extra=tools)
    assert not denied["ok"] and "read-only" in denied["error"]


# -- agent loop ----------------------------------------------------------------

def _blk_text(text):
    return SimpleNamespace(type="text", text=text)


def _blk_tool(name, tid, tinput):
    return SimpleNamespace(type="tool_use", name=name, id=tid, input=tinput)


class FakeStream:
    def __init__(self, response, capture, kwargs):
        self._response = response
        capture.append(kwargs)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def __aiter__(self):
        async def gen():
            if False:  # pragma: no cover
                yield None
        return gen()

    async def get_final_message(self):
        if isinstance(self._response, Exception):
            raise self._response
        return self._response


class FakeClient:
    """Scripted responses; records every request's kwargs."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.requests: list[dict] = []
        self.messages = SimpleNamespace(stream=self._stream)

    def _stream(self, **kwargs):
        return FakeStream(self._responses.pop(0), self.requests, kwargs)


def _resp(blocks, stop_reason="end_turn"):
    return SimpleNamespace(content=blocks, stop_reason=stop_reason)


def test_agent_loop_partial_e2e(omni_repo, trace, tmp_path):
    plan_backend_calls = []

    def plan_review(**kw):
        plan_backend_calls.append(kw)
        return {"verdict": "lgtm", "critique": "fine"}

    defs, tools = _tools(omni_repo,
                         RebaseBackends(request_plan_review=plan_review))
    scope = ToolScope(
        name="module", allowed_tools=frozenset(),
        path_scope=PathScope(writable=(f"{tmp_path}/*", f"{omni_repo}/*",),
                             primary=(f"{omni_repo}/mod.py",)))
    plan = tmp_path / "plans" / "plan-v0.json"
    decision = tmp_path / "plans" / "plan-v0.decision.md"

    client = FakeClient([
        _resp([_blk_text("planning"),
               _blk_tool("write_file", "t1",
                         {"file_path": str(plan), "content": "{}"}),
               _blk_tool("request_plan_review", "t2",
                         {"plan_json_path": str(plan)})]),
        _resp([_blk_tool("write_file", "t3",
                         {"file_path": str(decision), "content": "accept"})]),
        _resp([_blk_tool("edit_file", "t4",
                         {"file_path": str(omni_repo / "mod.py"),
                          "old_string": "return 1", "new_string": "return 3"}),
               _blk_tool("write_file", "t5",
                         {"file_path": str(omni_repo / "notes.md"),
                          "content": "n"})]),
        _resp([_blk_text("module rebased; all checks green")]),
    ])

    result = asyncio.run(run_agent_loop(
        client, "SYSTEM PROMPT", model="fake-model", tool_defs=defs,
        extra_tools=tools, scope=scope, trace=trace,
        plan_write_prefix=str(tmp_path / "plans"),
        agent_log=str(tmp_path / "agent.log")))

    assert result == {"done": True,
                      "text": "module rebased; all checks green", "turns": 4}
    # plan gate: turns 1-2 must NOT offer the gated tools; turn 3 must
    names_by_turn = [[t["name"] for t in req["tools"]]
                     for req in client.requests]
    for gated in ("edit_file", "run_pytest", "run_precommit"):
        assert gated not in names_by_turn[0] and gated not in names_by_turn[1]
        assert gated in names_by_turn[2]
    # the work actually happened through real dispatch
    assert (omni_repo / "mod.py").read_text().count("return 3") == 1
    assert plan_backend_calls == [{"plan_json_path": str(plan)}]
    # out-of-scope write executed AND recorded (notes.md outside primary)
    assert (omni_repo / "notes.md").exists()
    assert any(True for _ in trace.events("out_of_scope_edit"))
    # tool_result contents are parent-shaped JSON (the captured kwargs share
    # the live messages list, so look the result up by tool_use_id)
    results = {tr["tool_use_id"]: tr
               for m in client.requests[-1]["messages"]
               if isinstance(m.get("content"), list)
               for tr in m["content"]
               if isinstance(tr, dict) and tr.get("type") == "tool_result"}
    assert json.loads(results["t1"]["content"])["written"] == str(plan)
    assert json.loads(results["t4"]["content"])["occurrences"] == 1
    log = (tmp_path / "agent.log").read_text()
    assert "PLAN-REVIEW-DECISION COMPLETE" in log


def test_gate_unlocks_only_on_successful_decision_write(omni_repo, tmp_path):
    """A refused (out-of-wall) or failing decision write must NOT unlock the
    gated tools, and a gated call emitted while locked is rejected at
    dispatch — the tools list only controls advertisement."""
    defs, tools = _tools(omni_repo)
    scope = ToolScope(name="m", allowed_tools=frozenset(),
                      path_scope=PathScope(writable=(f"{tmp_path}/*",)))
    client = FakeClient([
        # decision write OUTSIDE the writable wall -> refused -> still locked
        _resp([_blk_tool("write_file", "t1",
                         {"file_path": "/etc/plan-v0.decision.md",
                          "content": "x"})]),
        # the model tries edit_file anyway while locked -> rejected
        _resp([_blk_tool("edit_file", "t2",
                         {"file_path": str(omni_repo / "mod.py"),
                          "old_string": "return 1", "new_string": "H"})]),
        # a SUCCESSFUL decision write unlocks
        _resp([_blk_tool("write_file", "t3",
                         {"file_path": str(tmp_path / "plans" / "p.decision.md"),
                          "content": "accept"})]),
        _resp([_blk_tool("edit_file", "t4",
                         {"file_path": str(omni_repo / "mod.py"),
                          "old_string": "return 1", "new_string": "return 9"})]),
        _resp([_blk_text("done")]),
    ])
    result = asyncio.run(run_agent_loop(
        client, "P", model="m", tool_defs=defs, extra_tools=tools, scope=scope,
        plan_write_prefix="/"))
    assert result["done"] is True
    assert not Path("/etc/plan-v0.decision.md").exists()
    assert "return 1" in (omni_repo / "mod.py").read_text() or         "return 9" in (omni_repo / "mod.py").read_text()
    # gated tools were withheld through turn 3 and offered on turn 4
    names_by_turn = [[t["name"] for t in req["tools"]]
                     for req in client.requests]
    assert "edit_file" not in names_by_turn[1]
    assert "edit_file" not in names_by_turn[2]
    assert "edit_file" in names_by_turn[3]
    # t2 (locked edit) was rejected, not executed
    results = {tr["tool_use_id"]: tr
               for m in client.requests[-1]["messages"]
               if isinstance(m.get("content"), list)
               for tr in m["content"]
               if isinstance(tr, dict) and tr.get("type") == "tool_result"}
    assert "locked until the plan-review decision" in         json.loads(results["t2"]["content"])["error"]
    assert json.loads(results["t4"]["content"])["occurrences"] == 1
    assert (omni_repo / "mod.py").read_text().count("return 9") == 1


def test_gate_confines_pre_decision_writes_to_plan_dir(omni_repo, tmp_path):
    """While the plan gate is closed, write_file may only land under the
    plan directory — overwriting product code pre-decision is the exact
    bypass the gate exists to prevent."""
    defs, tools = _tools(omni_repo)
    before = (omni_repo / "mod.py").read_text()
    client = FakeClient([
        _resp([_blk_tool("write_file", "t1",
                         {"file_path": str(omni_repo / "mod.py"),
                          "content": "SABOTAGE"})]),
        _resp([_blk_text("ok I will plan first")]),
    ])
    result = asyncio.run(run_agent_loop(
        client, "P", model="m", tool_defs=defs, extra_tools=tools,
        plan_write_prefix=str(tmp_path / "plans")))
    assert result["done"] is True
    assert (omni_repo / "mod.py").read_text() == before   # untouched
    results = {tr["tool_use_id"]: tr
               for m in client.requests[-1]["messages"]
               if isinstance(m.get("content"), list)
               for tr in m["content"]
               if isinstance(tr, dict) and tr.get("type") == "tool_result"}
    err = json.loads(results["t1"]["content"])["error"]
    assert "outside the plan directory" in err
    # a REQUIRED prefix: the gate cannot be configured bypassable
    with pytest.raises(ValueError, match="plan_write_prefix"):
        asyncio.run(run_agent_loop(client, "P", model="m", tool_defs=defs,
                                   extra_tools=tools))


def test_agent_loop_model_mismatch_fails_closed(omni_repo):
    """A served model differing from the requested one aborts the run —
    repo invariant: model substitution fails by default."""
    defs, tools = _tools(omni_repo)
    resp = _resp([_blk_text("hello")])
    resp.model = "cheap-substitute"
    client = FakeClient([resp])
    r = asyncio.run(run_agent_loop(client, "P", model="claude-real",
                                   tool_defs=defs, extra_tools=tools,
                                   require_plan_review=False))
    assert r["done"] is False and "Model mismatch" in r["text"]
    assert "cheap-substitute" in r["text"]


def test_agent_loop_partial_input_reaches_guard_not_dispatch(omni_repo):
    """A write with a path but truncated-away content (the common truncation
    shape) must hit the guard, not a cryptic dispatch TypeError."""
    defs, tools = _tools(omni_repo)
    client = FakeClient([
        _resp([_blk_tool("write_file", "t1",
                         {"file_path": "/tmp/x.py"})], stop_reason="max_tokens"),
        _resp([_blk_tool("edit_file", "t2",
                         {"file_path": str(omni_repo / "mod.py"),
                          "old_string": "return 1"})]),
        _resp([_blk_text("stopping")]),
    ])
    r = asyncio.run(run_agent_loop(client, "P", model="m", tool_defs=defs,
                                   extra_tools=tools,
                                   require_plan_review=False))
    assert r["done"] is True
    results = {tr["tool_use_id"]: tr
               for m in client.requests[-1]["messages"]
               if isinstance(m.get("content"), list)
               for tr in m["content"]
               if isinstance(tr, dict) and tr.get("type") == "tool_result"}
    for tid in ("t1", "t2"):
        assert "missing required input" in             json.loads(results[tid]["content"])["error"]


def test_extra_tool_audit_classifies_parent_shaped_errors(tmp_path, trace):
    """Parent-shaped failures are ordinary strings: the transport payload
    stays ok (the bytes ARE the result) but the trace records ok=False, so
    failure accounting sees missing files and unwired backends."""
    from infermatrix_copilot.rebase_engine.rebase_tools import (
        RebasePaths, build_rebase_tools, load_tool_schemas)
    tools = build_rebase_tools(load_tool_schemas(SCHEMAS),
                               RebasePaths(omni_path=str(tmp_path),
                                           vllm_path=str(tmp_path)))
    bad = dispatch("read_file", {"file_path": str(tmp_path / "absent.py")},
                   trace=trace, extra=tools)
    assert bad["ok"] and "File not found" in bad["result"]   # bytes unchanged
    unwired = dispatch("search_skills", {}, trace=trace, extra=tools)
    assert unwired["ok"] and "not wired" in unwired["result"]
    events = [e for e in trace.events("tool_call")]
    assert [e.get("ok") for e in events] == [False, False]
    good = dispatch("write_file",
                    {"file_path": str(tmp_path / "ok.py"), "content": "x"},
                    trace=trace, extra=tools)
    assert good["ok"]
    events = [e for e in trace.events("tool_call")]
    assert events[-1].get("ok") is True


def test_agent_loop_truncated_text_only_not_done(omni_repo):
    """A text-only response cut off at max_tokens is an involuntary ending —
    deliberate divergence from the parent, which reported done=True."""
    defs, tools = _tools(omni_repo)
    client = FakeClient([_resp([_blk_text("half a summar")],
                               stop_reason="max_tokens")])
    r = asyncio.run(run_agent_loop(client, "P", model="m", tool_defs=defs,
                                   extra_tools=tools,
                                   require_plan_review=False))
    assert r["done"] is False and "Truncated at max_tokens" in r["text"]


def test_agent_loop_incomplete_write_guard(omni_repo, tmp_path):
    defs, tools = _tools(omni_repo)
    client = FakeClient([
        _resp([_blk_tool("write_file", "t1", {})], stop_reason="max_tokens"),
        _resp([_blk_text("giving up")]),
    ])
    result = asyncio.run(run_agent_loop(
        client, "P", model="m", tool_defs=defs, extra_tools=tools,
        require_plan_review=False))
    assert result["done"] is True
    content = json.loads(
        client.requests[1]["messages"][-1]["content"][0]["content"])
    assert "missing required input" in content["error"]
    assert "truncated at the output token limit" in content["error"]


def test_agent_loop_truncation_streak_aborts(omni_repo):
    defs, tools = _tools(omni_repo)
    burst = [_resp([_blk_tool("git_diff", f"t{i}", {})],
                   stop_reason="max_tokens") for i in range(3)]
    client = FakeClient(burst)
    result = asyncio.run(run_agent_loop(
        client, "P", model="m", tool_defs=defs, extra_tools=tools,
        require_plan_review=False))
    assert result == {"done": False,
                      "text": "Aborted: repeated output truncation", "turns": 3}


def test_agent_loop_error_classification(omni_repo):
    defs, tools = _tools(omni_repo)
    fatal = FakeClient([RuntimeError("401 Unauthorized: invalid_api_key")])
    r = asyncio.run(run_agent_loop(fatal, "P", model="m", tool_defs=defs,
                                   extra_tools=tools,
                                   require_plan_review=False))
    assert not r["done"] and r["text"].startswith("Fatal API error")
    transient = FakeClient([ConnectionError("read timeout"),
                            _resp([_blk_text("unreached")])])
    r = asyncio.run(run_agent_loop(transient, "P", model="m", tool_defs=defs,
                                   extra_tools=tools,
                                   require_plan_review=False))
    assert not r["done"] and r["text"].startswith("Stream error (turn 1)")


def test_agent_loop_turn_budget(omni_repo):
    defs, tools = _tools(omni_repo)
    client = FakeClient([_resp([_blk_tool("git_diff", f"t{i}", {})])
                         for i in range(3)])
    r = asyncio.run(run_agent_loop(client, "P", model="m", tool_defs=defs,
                                   extra_tools=tools, max_turns=3,
                                   require_plan_review=False))
    assert r == {"done": False, "text": "Agent exceeded max turns", "turns": 3}


# -- planner requires filter ---------------------------------------------------

def _pb(name, repos, requires, kind="repo_rebase"):
    return Playbook(name=name, version=1, task_kinds=[kind], repos=repos,
                    requires=requires, status="active", steps=[{"id": "s"}])


def test_store_exact_repo_requires_filter(tmp_path):
    from infermatrix_copilot.engine.registry import StepRegistry
    store = PlaybookStore(tmp_path, StepRegistry())
    store._playbooks = {"x": _pb("x", ["repo-a"], ["orchestrator.external"])}
    # unknown capabilities (no adapter): v1-compatible skip
    assert store.find("repo_rebase", "repo-a", None) is not None
    # authoritative capabilities without the requirement: filtered out...
    assert store.find("repo_rebase", "repo-a", {"repo.path"}) is None
    # ...and the gap is REPORTED for the exact-repo playbook (repo-scoped)
    assert store.missing_capabilities("repo_rebase", {"repo.path"},
                                      repo="repo-a") == {
        "x": ["orchestrator.external"]}
    # satisfied: recalled
    assert store.find("repo_rebase", "repo-a",
                      {"repo.path", "orchestrator.external"}) is not None
    # gap reporting is repo-scoped: another repo's exact playbook is noise
    assert store.missing_capabilities("repo_rebase", {"repo.path"},
                                      repo="repo-b") == {}
    assert store.missing_capabilities("repo_rebase", {"repo.path"},
                                      repo="repo-a") == {
        "x": ["orchestrator.external"]}


def test_extra_write_file_records_full_file_write(tmp_path, trace):
    """A whole-.py rewrite through an extra write tool must arm the same
    full-file-fallback audit event as the builtin branch."""
    from infermatrix_copilot.rebase_engine.rebase_tools import (
        RebaseBackends, RebasePaths, build_rebase_tools, load_tool_schemas)
    tools = build_rebase_tools(load_tool_schemas(SCHEMAS),
                               RebasePaths(omni_path=str(tmp_path),
                                           vllm_path=str(tmp_path)))
    scope = ToolScope(name="m", allowed_tools=frozenset(),
                      path_scope=PathScope(writable=(f"{tmp_path}/*",)))
    out = dispatch("write_file",
                   {"file_path": str(tmp_path / "big.py"), "content": "x"},
                   scope=scope, trace=trace, extra=tools)
    assert out["ok"]
    assert any(True for _ in trace.events("full_file_write"))


def test_resolve_fails_closed_on_malformed_known_adapter(tmp_path, settings,
                                                         git_repo):
    """A malformed KNOWN adapter must be a hard failure, not fail open into
    capabilities=None and recall a playbook whose requirements were never
    established."""
    import shutil
    from infermatrix_copilot.cli import Copilot
    from infermatrix_copilot.config import _REPO_ROOT
    from infermatrix_copilot.task_spec import TaskSpec
    settings.playbooks_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(_REPO_ROOT / "playbooks" / "repo-rebase.yaml",
                settings.playbooks_dir / "repo-rebase.yaml")
    settings.repo_paths = {"vllm-omni": str(git_repo)}
    bad = Path(settings.adapters_dir) / "vllm_omni"
    bad.mkdir(parents=True, exist_ok=True)
    (bad / "manifest.yaml").write_text("{not yaml: [")
    with pytest.raises(Exception):
        Copilot(settings).resolve(TaskSpec(kind="repo_rebase"))
