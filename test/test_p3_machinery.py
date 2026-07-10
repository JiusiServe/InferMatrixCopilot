"""P3 machinery (design §V2.2.5, §V2.3.3 Stage 4, §V2.3.5) — offline:
decay/drift, gated consolidation, read-only judge, the profile ablation
switch, and invariance scoring. The paid eval runs consume these; nothing
here calls an API.
"""

import asyncio
import json
import time

from omni_copilot.engine.steps import register_builtin_steps
from omni_copilot.engine.registry import StepRegistry
from omni_copilot.engine.step import StepContext
from omni_copilot.llm import Block, Reply
from omni_copilot.plugins.base import load_plugin
from omni_copilot.profiles.consolidate import decay_stale, detect_drift
from omni_copilot.profiles.store import ProfileStore

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))
from invariance import (ablation_verdict, invariance_index,  # noqa: E402
                        replicate_mean, score_invariance)


def _registry():
    return register_builtin_steps(StepRegistry())


def _ctx(settings, trace, tmp_path, state, llm=None):
    return StepContext(settings=settings, state=state, params={},
                       run_dir=tmp_path / "run", trace=trace, llm=llm)


def _fact_op(fact_id, text, module="repo-wide", channel="briefing"):
    return {"op": "add_fact", "id": fact_id, "module": module,
            "kind": "command", "channel": channel, "text": text,
            "source": "agent", "evidence": [f"evidence for {fact_id}"]}


def _plugin_with_profile(settings, git_repo, facts):
    root = settings.plugins_dir / "myrepo"
    root.mkdir(parents=True)
    (root / "plugin.yaml").write_text(
        f"name: myrepo\nstatus: active\nrepo:\n  path: {git_repo}\n"
        "modules:\n  core:\n    local_paths: [core/]\n")
    store = ProfileStore(root / "profile")
    store.apply_ops(facts)
    return load_plugin(root), store


# -- decay & drift ---------------------------------------------------------------

def test_decay_flips_old_facts_to_stale(settings, git_repo, tmp_path):
    plugin, store = _plugin_with_profile(settings, git_repo,
                                         [_fact_op("old", "Old directive"),
                                          _fact_op("fresh", "Fresh directive")])
    old = store.facts["old"]
    old.last_confirmed = time.strftime(
        "%Y-%m-%d", time.localtime(time.time() - 200 * 86_400))
    store.save()

    stale = decay_stale(ProfileStore(plugin.profile_dir), days=90)
    assert stale == ["old"]
    reloaded = ProfileStore(plugin.profile_dir)
    assert reloaded.facts["old"].status == "stale"     # excluded, not deleted
    assert reloaded.facts["fresh"].status == "active"
    assert "Old directive" not in reloaded.render_briefing()


def test_detect_drift_reports_never_fixes(settings, git_repo):
    plugin, store = _plugin_with_profile(
        settings, git_repo,
        [_fact_op("orphan", "Joined to a gone module", module="ghost_module")])
    findings = detect_drift(plugin, store)
    assert any("core/" in f for f in findings)          # declared path missing
    assert any("ghost_module" in f for f in findings)   # orphaned join
    assert ProfileStore(plugin.profile_dir).facts["orphan"].status == "active"


# -- consolidation & judge steps ---------------------------------------------------

class ScriptedLLM:
    def __init__(self, replies):
        self._replies = list(replies)
        self.calls = []
        self.available = True

    def create(self, *, system, messages, tools=None, model=None,
               max_tokens=None, on_text=None):
        self.calls.append({"system": system, "messages": [*messages]})
        return self._replies.pop(0)


def _contract(extra):
    return Reply(blocks=[Block(type="text", text=json.dumps({
        "status": "success", "summary": "done", "findings": [],
        "files_read": [], "files_modified": [], "tests_requested": [],
        "tests_run": [], "assumptions": [], "blockers": [],
        "confidence": "high", "failure_kind": None, "next_action": "",
        **extra}))])


def test_consolidate_applies_gated_ops(settings, trace, tmp_path, git_repo):
    plugin, store = _plugin_with_profile(settings, git_repo, [
        _fact_op("a", "Run `make check` before committing"),
        _fact_op("b", "Before committing run `make check`"),
        _fact_op("stable", "Protected branch main is never pushed"),
    ])
    for _ in range(3):
        store.apply_ops([{"op": "bump_confirmed", "id": "stable"}])

    llm = ScriptedLLM([_contract({"ops": [
        {"op": "merge_facts", "into": "a", "from": "b"},
        # gate must reject: stable fact rewritten to drop its evidence
        {"op": "rewrite_fact", "id": "stable", "text": "short", "evidence": []},
        {"op": "add_fact", "id": "x", "text": "t"},     # wrong tier op-kind? no:
        # add_fact IS allowed in consolidate tier but lacks evidence -> rejected
    ]})])
    state = {"task_spec": {"repo": "myrepo"}, "repo_path": str(git_repo),
             "plugin_root": str(plugin.root)}
    result = asyncio.run(_registry().get("agent.profile_consolidate").handler(
        _ctx(settings, trace, tmp_path, state, llm=llm)))
    assert result.ok
    assert result.outputs["applied"] == 1
    assert len(result.outputs["rejected"]) == 2
    reloaded = ProfileStore(plugin.profile_dir)
    assert reloaded.facts["b"].status == "merged"
    assert reloaded.facts["stable"].text.startswith("Protected branch")


def test_consolidate_skips_without_llm(settings, trace, tmp_path, git_repo):
    plugin, _ = _plugin_with_profile(settings, git_repo, [_fact_op("a", "T")])
    state = {"task_spec": {"repo": "myrepo"}, "repo_path": str(git_repo),
             "plugin_root": str(plugin.root)}
    result = asyncio.run(_registry().get("agent.profile_consolidate").handler(
        _ctx(settings, trace, tmp_path, state)))
    assert result.ok and "skipped (no LLM)" in result.summary
    assert any(e["capability"] == "llm"
               for e in trace.events("capability_gap"))


def test_judge_reports_but_never_mutates(settings, trace, tmp_path, git_repo):
    plugin, store = _plugin_with_profile(settings, git_repo,
                                         [_fact_op("a", "Suspicious claim")])
    before = (plugin.profile_dir / "profile.yaml").read_text()
    llm = ScriptedLLM([_contract({"audit_findings": [
        {"fact_id": "a", "issue": "unsupported", "why": "evidence is vague"}]})])
    state = {"task_spec": {"repo": "myrepo"}, "repo_path": str(git_repo),
             "plugin_root": str(plugin.root)}
    result = asyncio.run(_registry().get("profile.judge").handler(
        _ctx(settings, trace, tmp_path, state, llm=llm)))
    assert result.ok and "1 finding" in result.summary
    report = (plugin.profile_dir / "JUDGE_REPORT.md").read_text()
    assert "unsupported" in report and "nothing auto-fixed" in report
    assert (plugin.profile_dir / "profile.yaml").read_text() == before


def test_consolidate_playbook_is_candidate_only(settings):
    from omni_copilot.playbooks.store import PlaybookStore
    from test_v2_p0 import REPO_ROOT

    store = PlaybookStore(REPO_ROOT / "playbooks", _registry())
    pb = store.get("profile-consolidate")
    assert pb is not None and pb.status == "candidate"
    # the planner never recalls it — repo-profile stays the NL-triggered one
    assert store.find("repo_profile", "any", {"repo.path"}).name == "repo-profile"


# -- ablation switch (§V2.3.5) -----------------------------------------------------

def test_briefing_ablation_switch(settings, trace, tmp_path, git_repo):
    from omni_copilot.engine.agent_runtime import run_agent_step

    plugin, _ = _plugin_with_profile(
        settings, git_repo, [_fact_op("uv", "Use `uv pip install` only")])
    settings.profile_briefing_enabled = False
    llm = ScriptedLLM([_contract({})])
    ctx = _ctx(settings, trace, tmp_path,
               {"task_spec": {"repo": "myrepo"}, "repo_path": str(git_repo)},
               llm=llm)
    result, _ = asyncio.run(run_agent_step(
        ctx, step_name="t", purpose="p", evidence={"e": "x"}))
    assert result.ok
    assert "REPO BRIEFING" not in llm.calls[0]["messages"][0]["content"]


# -- invariance scoring ------------------------------------------------------------

def test_replicate_mean_and_index():
    assert replicate_mean([]) is None
    assert replicate_mean([0.6, 0.8]) == 0.7
    assert invariance_index({"a": 0.7}) is None          # one repo = unmeasured
    idx = invariance_index({"a": 0.8, "b": 0.6})
    assert abs(idx - 0.6 / 0.7) < 1e-9


def test_score_invariance_report():
    report = score_invariance({
        "vllm-omni": {"pr_review": [0.7, 0.65], "pr_debug": [0.5]},
        "repo-b": {"pr_review": [0.6, 0.62]},
    })
    assert report.passing["pr_review"] is True           # 0.61/0.6425 mean band
    assert report.index_per_kind["pr_debug"] is None     # single repo
    assert report.passing["pr_debug"] is False


def test_ablation_verdict_gates_promotion():
    v = ablation_verdict([0.66, 0.68], [0.60, 0.62],
                         cost_with=1.2, cost_without=1.0)
    assert v.promote and v.quality_delta > 0
    v = ablation_verdict([0.55], [0.62])
    assert not v.promote and "ETH failure mode" in v.reason
    v = ablation_verdict([0.66], [0.65], cost_with=2.0, cost_without=1.0)
    assert not v.promote and "cost ratio" in v.reason
    v = ablation_verdict([], [0.6])
    assert not v.promote and "replicate runs" in v.reason
