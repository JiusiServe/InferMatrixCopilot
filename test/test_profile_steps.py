"""Profile establishment pipeline (design §V2.3.3 Stages 0-1.5): fingerprint,
deterministic drafts, human-doc ingestion, evidence-gated profiling agent,
redundancy filter, and the repo-profile playbook/task-kind plumbing."""

import asyncio
import json

from omni_copilot.engine.steps import register_builtin_steps
from omni_copilot.engine.steps.review import _sweep_targets
from omni_copilot.engine.planner import Planner
from omni_copilot.engine.registry import StepRegistry
from omni_copilot.engine.step import StepContext
from omni_copilot.llm import Block, Reply
from omni_copilot.playbooks.store import PlaybookStore
from omni_copilot.plugins.base import load_plugin
from omni_copilot.profiles.establish import (build_doc_corpus, extract_directives,
                                             is_redundant, scan_modules)
from omni_copilot.profiles.store import ProfileStore
from omni_copilot.task_spec import TaskSpec

from test_v2_p0 import REPO_ROOT


def _registry():
    return register_builtin_steps(StepRegistry())


def _ctx(settings, trace, tmp_path, state, llm=None):
    return StepContext(settings=settings, state=state, params={},
                       run_dir=tmp_path / "run", trace=trace, llm=llm)


def _run(settings, trace, tmp_path, step, state, llm=None):
    return asyncio.run(_registry().get(step).handler(
        _ctx(settings, trace, tmp_path, state, llm=llm)))


# -- establish helpers -----------------------------------------------------------

def test_redundancy_filter_shingles():
    corpus = ("install the project with pip install dot then run pytest "
              "to execute the offline test suite")
    assert is_redundant("run pytest to execute the offline test suite", corpus)
    assert not is_redundant("use uv pip install, never bare pip — the lockfile "
                            "is authoritative here", corpus)
    assert is_redundant("run pytest", corpus)          # short fact: phrase match
    assert not is_redundant("run tox", corpus)
    assert not is_redundant("anything", "")            # no docs -> keep


def test_extract_directives_bounds():
    text = ("# Title\n- Use `make check` before every commit\n"
            "- no\n"                                   # too short
            "* Star bullets work too for this parser\n"
            "prose line is ignored\n- " + "w " * 61)   # too long
    assert extract_directives(text) == [
        "Use `make check` before every commit",
        "Star bullets work too for this parser"]


def test_scan_modules_skips_non_code_dirs(tmp_path):
    for name, n in (("core", 3), ("docs", 5), ("tiny", 1)):
        d = tmp_path / name
        d.mkdir()
        for i in range(n):
            (d / f"f{i}.py").write_text("x = 1\n")
    (tmp_path / ".hidden").mkdir()
    modules = scan_modules(tmp_path, "python")
    assert set(modules) == {"core"}
    assert modules["core"] == {"local_paths": ["core/"], "wave": 1}
    assert scan_modules(tmp_path, "unknown-lang") == {}


# -- deterministic steps ---------------------------------------------------------

def test_fingerprint_drafts_then_resolves(settings, trace, tmp_path, git_repo):
    state = {"task_spec": {"repo": "r"}, "repo_path": str(git_repo)}
    result = _run(settings, trace, tmp_path, "profile.fingerprint", state)
    assert result.ok and result.outputs["created"]
    assert state["plugin_root"]
    assert result.outputs["state_updates"]["repo_language"] == "python"
    plugin = load_plugin(state["plugin_root"])
    assert plugin.status == "draft"                    # human gate (Stage 2)

    again = _run(settings, trace, tmp_path, "profile.fingerprint",
                 {"task_spec": {"repo": "r"}, "repo_path": str(git_repo)})
    assert again.ok and not again.outputs["created"]   # resolves, no duplicate


def test_structure_scan_drafts_modules_once(settings, trace, tmp_path, git_repo):
    pkg = git_repo / "engine"
    pkg.mkdir()
    for i in range(3):
        (pkg / f"m{i}.py").write_text("x = 1\n")
    state = {"task_spec": {"repo": "r"}, "repo_path": str(git_repo)}
    _run(settings, trace, tmp_path, "profile.fingerprint", state)
    result = _run(settings, trace, tmp_path, "profile.structure_scan", state)
    assert result.ok
    plugin = load_plugin(state["plugin_root"])
    assert "engine" in plugin.modules

    # declared modules are never overwritten
    again = _run(settings, trace, tmp_path, "profile.structure_scan", state)
    assert "kept as-is" in again.summary


def test_ingest_docs_filters_redundant(settings, trace, tmp_path, git_repo):
    (git_repo / "README.md").write_text(
        "Install with pip install -e . and run pytest for the test suite.\n")
    (git_repo / "AGENTS.md").write_text(
        "# Agents\n"
        "- Install with pip install -e . and run pytest for the test suite\n"
        "- Never commit to main directly, always branch and open a PR\n")
    state = {"task_spec": {"repo": "r"}, "repo_path": str(git_repo)}
    _run(settings, trace, tmp_path, "profile.fingerprint", state)
    result = _run(settings, trace, tmp_path, "profile.ingest_docs", state)
    assert result.ok
    assert result.outputs == {"applied": 1, "dropped": 1,
                              **{k: v for k, v in result.outputs.items()
                                 if k not in ("applied", "dropped")}}
    store = ProfileStore(load_plugin(state["plugin_root"]).profile_dir)
    facts = store.active(channel="briefing")
    assert len(facts) == 1
    assert facts[0].source == "human" and facts[0].evidence == ["AGENTS.md"]
    assert "Never commit to main" in store.render_briefing()


# -- profiling agent step ---------------------------------------------------------

class ScriptedLLM:
    def __init__(self, replies):
        self._replies = list(replies)
        self.calls = []
        self.available = True

    def create(self, *, system, messages, tools=None, model=None,
               max_tokens=None, on_text=None):
        self.calls.append({"system": system, "messages": [*messages]})
        return self._replies.pop(0)


def _facts_reply(facts, checklist=None):
    return Reply(blocks=[Block(type="text", text=json.dumps({
        "status": "success", "summary": "profiled", "findings": [],
        "files_read": [], "files_modified": [], "tests_requested": [],
        "tests_run": [], "assumptions": [], "blockers": [],
        "confidence": "high", "failure_kind": None, "next_action": "",
        "profile_facts": facts, "review_checklist": checklist or []}))])


def test_profile_agent_applies_gated_facts(settings, trace, tmp_path, git_repo):
    (git_repo / "README.md").write_text(
        "Run pytest for the offline test suite of this project.\n")
    state = {"task_spec": {"repo": "r"}, "repo_path": str(git_repo)}
    _run(settings, trace, tmp_path, "profile.fingerprint", state)

    llm = ScriptedLLM([_facts_reply([
        {"module": "repo-wide", "kind": "command", "channel": "briefing",
         "text": "Use `uv pip install`, never bare pip — lockfile authoritative",
         "evidence": ["read Makefile: uv target"]},
        {"module": "repo-wide", "kind": "note", "channel": "briefing",
         "text": "Run pytest for the offline test suite of this project",
         "evidence": ["README"]},                       # doc-redundant -> dropped
        {"module": "repo-wide", "kind": "command", "channel": "machine",
         "text": "pytest -q", "evidence": ["read Makefile"]},
        {"module": "repo-wide", "kind": "trap", "channel": "retrieved",
         "text": "GPU tests need CUDA 12", "evidence": []},  # no evidence -> rejected
    ], checklist=["Check the KV-cache layout invariants on runner changes"])])
    result = _run(settings, trace, tmp_path, "agent.profile_repo", state, llm=llm)
    assert result.ok
    assert result.outputs["applied"] == 2
    assert result.outputs["redundant_dropped"] == 1
    assert len(result.outputs["rejected"]) == 1

    plugin = load_plugin(state["plugin_root"])
    store = ProfileStore(plugin.profile_dir)
    briefing = store.render_briefing()
    assert "never bare pip" in briefing
    assert "pytest -q" not in briefing                  # machine channel
    assert (plugin.profile_dir / "review.md").read_text().count("KV-cache") == 1
    assert (plugin.profile_dir / "PROFILE_REPORT.md").exists()


def test_profile_agent_skips_without_llm(settings, trace, tmp_path, git_repo):
    state = {"task_spec": {"repo": "r"}, "repo_path": str(git_repo)}
    _run(settings, trace, tmp_path, "profile.fingerprint", state)
    result = _run(settings, trace, tmp_path, "agent.profile_repo", state)
    assert result.ok and "skipped (no LLM)" in result.summary


# -- planner / intent / review plumbing -------------------------------------------

def test_planner_recalls_repo_profile_for_any_repo():
    registry = _registry()
    store = PlaybookStore(REPO_ROOT / "playbooks", registry)
    spec = TaskSpec(kind="repo_profile", repo="some-new-repo")
    assert spec.tier == "L2" and spec.confirm_required
    resolution = Planner(store, registry).resolve(spec)
    assert resolution.mode == "reuse"
    assert resolution.playbook.name == "repo-profile"


def test_intent_parses_profile_command():
    # intent is LLM-only; verify repo_profile maps end-to-end through a fake reply
    from omni_copilot.intent import parse_intent
    from omni_copilot.llm import Block, Reply

    class _LLM:
        available = True

        def create(self, **kw):
            return Reply(blocks=[Block(type="text", text=json.dumps(
                {"kind": "repo_profile", "confidence": 0.9}))])

    r = parse_intent("profile the repo", llm=_LLM())
    assert r.spec is not None and r.spec.kind == "repo_profile"


def test_sweep_targets_language_degrades_to_files():
    diff = ("+++ b/pkg/main.go\n@@ +1\n+if err != nil {\n+x := xs[0]\n"
            "+++ b/pkg/main_test.go\n@@ +1\n+func TestX(t *testing.T) {}\n")
    go = _sweep_targets(diff, "go")
    assert "NON-TEST FILES TOUCHED" in go
    assert "NEW/CHANGED BRANCHES" not in go            # python heuristics off
    py = _sweep_targets("+++ b/a.py\n@@ +1\n+if x:\n+y = xs[0]\n", "python")
    assert "NEW/CHANGED BRANCHES" in py and "INDEXED/FIRST-ELEMENT" in py


def test_review_guidance_from_profile(settings, trace, tmp_path, git_repo):
    """agent.review_diff appends the repo profile's review.md to its guidance."""
    plugin_root = settings.plugins_dir / "myrepo"
    (plugin_root / "profile").mkdir(parents=True)
    (plugin_root / "plugin.yaml").write_text(
        f"name: myrepo\nstatus: active\nrepo:\n  path: {git_repo}\n"
        "  language: python\n")
    (plugin_root / "profile" / "review.md").write_text(
        "- Check the wave-1 module import contract\n")

    llm = ScriptedLLM([_facts_reply([])])  # contract-shaped reply suffices
    state = {"task_spec": {"repo": "myrepo", "pr": 5},
             "repo_path": str(git_repo), "diff_text": "+++ b/a.py\n@@ +1\n+x=1"}
    result = _run(settings, trace, tmp_path, "agent.review_diff", state, llm=llm)
    assert result.ok
    assert "wave-1 module import contract" in llm.calls[0]["system"]
