"""Repo profile store (doc/DESIGN.md §V2.3.2): typed ops, write tiers,
provenance, stability gate, dormancy, briefing budget, dispatch injection."""

import asyncio
import json

import pytest

from omni_copilot.profiles.store import ProfileStore, STABLE_CONFIRMATIONS


def _fact_op(fact_id="fmt", channel="briefing", **over):
    return {"op": "add_fact", "id": fact_id, "module": "repo-wide",
            "kind": "command", "channel": channel,
            "text": f"Run `make check` before committing ({fact_id}).",
            "source": "agent", "evidence": ["read Makefile: check target"],
            **over}


def test_add_requires_evidence_and_persists(tmp_path):
    store = ProfileStore(tmp_path / "profile")
    rejected = store.apply_ops([_fact_op(evidence=[])])
    assert "without evidence" in rejected[0]
    assert store.apply_ops([_fact_op()]) == [""]
    reloaded = ProfileStore(tmp_path / "profile")
    fact = reloaded.facts["fmt"]
    assert fact.confirmations == 1 and fact.first_seen and fact.evidence
    assert (tmp_path / "profile" / "PROFILE_REPORT.md").exists()
    log = (tmp_path / "profile" / "ops_log.jsonl").read_text().splitlines()
    assert json.loads(log[0])["tier"] == "run"


def test_duplicate_add_is_confirmation(tmp_path):
    store = ProfileStore(tmp_path / "profile")
    store.apply_ops([_fact_op(), _fact_op(evidence=["second sighting"])])
    fact = store.facts["fmt"]
    assert fact.confirmations == 2
    assert "second sighting" in fact.evidence


def test_run_tier_cannot_rewrite_or_merge(tmp_path):
    store = ProfileStore(tmp_path / "profile")
    store.apply_ops([_fact_op()])
    results = store.apply_ops([
        {"op": "rewrite_fact", "id": "fmt", "text": "new"},
        {"op": "merge_facts", "into": "fmt", "from": "fmt"},
        {"op": "mark_stale", "id": "fmt"},
    ])
    assert all("not allowed in tier 'run'" in r for r in results)
    assert store.facts["fmt"].text.startswith("Run `make check`")


def test_stability_gate_and_history(tmp_path):
    store = ProfileStore(tmp_path / "profile")
    store.apply_ops([_fact_op()])
    for _ in range(STABLE_CONFIRMATIONS):
        store.apply_ops([{"op": "bump_confirmed", "id": "fmt"}])
    # a rewrite may never leave a fact evidence-free
    r = store.apply_ops([{"op": "rewrite_fact", "id": "fmt", "text": "short",
                          "evidence": []}], tier="consolidate")
    assert "never be left without evidence" in r[0]
    # dropping cited evidence from a stable fact is refused
    r = store.apply_ops([{"op": "rewrite_fact", "id": "fmt", "text": "short",
                          "evidence": ["something else entirely"]}],
                        tier="consolidate")
    assert "may not drop evidence" in r[0]
    # evidence-preserving rewrite is allowed; old text goes to history
    r = store.apply_ops([{"op": "rewrite_fact", "id": "fmt",
                          "text": "Run `make check` first."}], tier="consolidate")
    assert r == [""]
    fact = store.facts["fmt"]
    assert fact.text == "Run `make check` first."
    assert any("fmt" in h for h in fact.history)


def test_merge_leaves_pointer_stub(tmp_path):
    store = ProfileStore(tmp_path / "profile")
    store.apply_ops([_fact_op("a"), _fact_op("b")])
    assert store.apply_ops([{"op": "merge_facts", "into": "a", "from": "b"}],
                           tier="consolidate") == [""]
    assert store.facts["b"].status == "merged"
    assert store.facts["b"].merged_into == "a"
    assert store.facts["a"].confirmations == 2
    # merged stubs never render
    assert "(b)" not in store.render_briefing()


def test_briefing_budget_channel_and_staleness(tmp_path):
    store = ProfileStore(tmp_path / "profile")
    store.apply_ops([
        _fact_op("keep"),
        _fact_op("machine-only", channel="machine"),
        _fact_op("stale-one"),
    ])
    store.apply_ops([{"op": "bump_confirmed", "id": "keep"}])
    store.apply_ops([{"op": "mark_stale", "id": "stale-one"}], tier="consolidate")
    briefing = store.render_briefing()
    assert "(keep)" in briefing
    assert "(machine-only)" not in briefing      # machine channel never in prompt
    assert "(stale-one)" not in briefing         # stale facts drop out
    # hard word budget: most-confirmed facts win the cut
    assert "(keep)" in store.render_briefing(budget_words=10)
    assert store.render_briefing(budget_words=1) == ""


def test_briefing_reaches_agent_dispatch(settings, trace, tmp_path, git_repo):
    from omni_copilot.engine.agent_runtime import run_agent_step
    from omni_copilot.llm import Block, Reply

    adapter_root = settings.adapters_dir / "myrepo"
    adapter_root.mkdir(parents=True)
    (adapter_root / "manifest.yaml").write_text(
        f"name: myrepo\nstatus: active\nrepo:\n  path: {git_repo}\n")
    ProfileStore(adapter_root / "profile").apply_ops(
        [_fact_op("uv", text="Use `uv pip install`, never bare pip.")])

    class OneShotLLM:
        available = True

        def __init__(self):
            self.calls = []

        def create(self, *, system, messages, tools=None, model=None,
                   max_tokens=None, on_text=None):
            self.calls.append({"system": system, "messages": [*messages]})
            return Reply(blocks=[Block(type="text", text=json.dumps({
                "status": "success", "summary": "ok", "findings": [],
                "files_read": [], "files_modified": [], "tests_requested": [],
                "tests_run": [], "assumptions": [], "blockers": [],
                "confidence": "high", "failure_kind": None, "next_action": ""}))])

    from omni_copilot.engine.step import StepContext

    llm = OneShotLLM()
    ctx = StepContext(settings=settings, params={}, run_dir=tmp_path / "run",
                      trace=trace, llm=llm,
                      state={"task_spec": {"repo": "myrepo"},
                             "repo_path": str(git_repo)})
    result, _ = asyncio.run(run_agent_step(
        ctx, step_name="t", purpose="p", evidence={"e": "x"}))
    assert result.ok
    prompt = llm.calls[0]["messages"][0]["content"]
    assert "REPO BRIEFING" in prompt
    assert "Use `uv pip install`, never bare pip." in prompt


def test_no_profile_no_briefing_section(settings, trace, tmp_path, git_repo):
    from omni_copilot.engine.agent_runtime import AgentDispatchContext

    rendered = AgentDispatchContext(task={}, step={}, repo={}).render()
    assert "REPO BRIEFING" not in rendered


@pytest.mark.parametrize("bad", [
    {"op": "add_fact", "text": "", "evidence": ["e"]},
    {"op": "add_fact", "text": "t", "evidence": ["e"], "channel": "prompt"},
    {"op": "bump_confirmed", "id": "nope"},
    {"op": "unknown_op"},
])
def test_malformed_ops_rejected_individually(tmp_path, bad):
    store = ProfileStore(tmp_path / "profile")
    results = store.apply_ops([_fact_op(), bad], tier="consolidate")
    assert results[0] == "" and results[1] != ""
    assert "fmt" in store.facts  # the good op still applied
