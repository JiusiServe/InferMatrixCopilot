from omni_copilot.agent_loop import run_agent
from omni_copilot.llm import Block, Reply
from omni_copilot.scopes import pre_plan_scope


class ScriptedLLM:
    """Yields scripted replies; records what it was sent."""

    def __init__(self, replies):
        self._replies = list(replies)
        self.sent_messages = []
        self.available = True

    def create(self, *, system, messages, tools=None, model=None, max_tokens=None):
        self.sent_messages = [*messages]  # snapshot at call time
        return self._replies.pop(0)


def test_agent_loop_tools_and_final_text(tmp_path, trace):
    plan_dir = tmp_path / "plans"
    scope = pre_plan_scope(plan_dir)
    llm = ScriptedLLM([
        Reply(blocks=[Block(type="tool_use", id="t1", name="write_file",
                            input={"path": str(plan_dir / "plan.md"), "content": "# plan"})]),
        Reply(blocks=[Block(type="text", text="plan written")]),
    ])
    outcome = run_agent(llm, system="s", prompt="write the plan", scope=scope, trace=trace)
    assert outcome.text == "plan written"
    assert outcome.tool_calls == 1
    assert (plan_dir / "plan.md").read_text() == "# plan"


def test_agent_loop_scope_refusal_fed_back(tmp_path, trace):
    scope = pre_plan_scope(tmp_path / "plans")
    llm = ScriptedLLM([
        Reply(blocks=[Block(type="tool_use", id="t1", name="write_file",
                            input={"path": str(tmp_path / "src" / "core.py"),
                                   "content": "evil"})]),
        Reply(blocks=[Block(type="text", text="ok I will not")]),
    ])
    outcome = run_agent(llm, system="s", prompt="p", scope=scope, trace=trace)
    assert outcome.refusals and "refused" in outcome.refusals[0]
    assert not (tmp_path / "src" / "core.py").exists()
    # the refusal was surfaced to the model as a tool_result error
    last_user = llm.sent_messages[-1]
    assert last_user["role"] == "user"
    assert last_user["content"][0]["is_error"] is True


def test_agent_loop_max_iters_forces_final_answer(tmp_path, trace):
    scope = pre_plan_scope(tmp_path / "plans")
    loop_reply = Reply(blocks=[Block(type="tool_use", id="t", name="read_file",
                                     input={"path": str(tmp_path / "nope.txt")})])
    final = Reply(blocks=[Block(type="text", text="best effort answer")])
    llm = ScriptedLLM([loop_reply] * 3 + [final])
    outcome = run_agent(llm, system="s", prompt="p", scope=scope, trace=trace, max_iters=3)
    assert outcome.truncated
    # the investigation is not discarded: a forced no-tools final call runs
    assert outcome.text == "best effort answer"
    last_call = llm.sent_messages[-1]
    assert "budget is exhausted" in str(last_call)


def test_final_round_nudge_follows_tool_results(trace):
    """The budget-2 nudge must come AFTER tool_result blocks in the user
    message — a leading text block violates the API contract (tool_use ids
    must be immediately followed by tool_results; caused live 400s at T4)."""
    from omni_copilot.agent_loop import run_agent
    from omni_copilot.llm import Block, Reply
    from omni_copilot.scopes import read_only_scope

    class LLM:
        available = True

        def __init__(self):
            self.calls = []

        def create(self, *, system, messages, tools=None, model=None,
                   max_tokens=None, on_text=None):
            self.calls.append([*messages])
            return Reply(blocks=[Block(type="tool_use", id=f"t{len(self.calls)}",
                                       name="list_dir", input={"path": "/tmp"})])

    llm = LLM()
    run_agent(llm, system="s", prompt="p", scope=read_only_scope(),
              trace=trace, max_iters=2)
    # find the nudge-carrying user message: results FIRST, text LAST
    nudged = [m["content"] for m in llm.calls[-1]
              if isinstance(m.get("content"), list)
              and any(isinstance(b, dict) and b.get("type") == "text"
                      and "FINAL ROUND" in b.get("text", "")
                      for b in m["content"])]
    assert nudged, "nudge message missing"
    kinds = [b["type"] for b in nudged[0] if isinstance(b, dict)]
    assert kinds[0] == "tool_result" and kinds[-1] == "text"
