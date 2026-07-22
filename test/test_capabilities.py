"""Repo-neutral playbooks + capability matching (design §V2.2.3-4): playbook
`requires:` vs the repo profile's capabilities; explicit repo scoping wins;
capability gaps degrade loudly, never silently."""

import pytest

from infermatrix_copilot.engine.steps import register_builtin_steps
from infermatrix_copilot.engine.planner import Planner, PlanningError
from infermatrix_copilot.engine.registry import StepRegistry
from infermatrix_copilot.playbooks.store import PlaybookStore
from infermatrix_copilot.adapters.base import load_adapter
from infermatrix_copilot.task_spec import TaskSpec

from test_v2_p0 import REPO_ROOT


@pytest.fixture()
def stack():
    registry = register_builtin_steps(StepRegistry())
    store = PlaybookStore(REPO_ROOT / "playbooks", registry)
    return store, Planner(store, registry)


def test_adapter_zero_capabilities():
    adapter = load_adapter(REPO_ROOT / "adapters" / "vllm_omni")
    assert {"repo.path", "language.python", "ci.provider",
            "upstream.fork_tracking", "modules",
            "orchestrator.external"} <= adapter.capabilities


def test_neutral_playbooks_match_second_repo(stack):
    store, planner = stack
    caps = {"repo.path"}
    for kind, name in (("pr_review", "pr-review"), ("pr_rebase", "pr-rebase"),
                       ("pr_debug", "pr-debug"), ("issue_answer", "issue-answer"),
                       ("issue_filter", "issue-triage"),
                       ("repo_profile", "repo-profile")):
        pb = store.find(kind, "some-second-repo", caps)
        assert pb is not None and pb.name == name, kind
    res = planner.resolve(TaskSpec(kind="pr_rebase", repo="some-second-repo",
                                   pr=7), capabilities=caps)
    assert res.mode == "reuse" and res.playbook.name == "pr-rebase"


def test_missing_capability_blocks_write_kinds_loudly(stack):
    _, planner = stack
    with pytest.raises(PlanningError) as err:
        planner.resolve(TaskSpec(kind="pr_rebase", repo="bare-repo", pr=7),
                        capabilities=set())
    assert "capability gap" in str(err.value)
    assert "repo.path" in str(err.value) and "repo_profile" in str(err.value)


def test_missing_capability_degrades_read_only_to_generate(stack):
    _, planner = stack
    res = planner.resolve(TaskSpec(kind="pr_review", repo="bare-repo", pr=7),
                          capabilities=set())
    assert res.mode == "generate" and res.requires_review


def test_repo_scoped_playbook_still_wins_for_its_repo(stack):
    store, _ = stack
    adapter = load_adapter(REPO_ROOT / "adapters" / "vllm_omni")
    pb = store.find("repo_rebase", "vllm-omni", adapter.capabilities)
    assert pb is not None and pb.name == "repo-rebase" and pb.locked
    # ...and never leaks to other repos (requires orchestrator.external)
    assert store.find("repo_rebase", "other-repo", {"repo.path"}) is None


def test_unknown_capabilities_keep_v1_behavior(stack):
    store, _ = stack
    # capabilities=None (v1 callers): no filtering, neutral playbooks match
    pb = store.find("pr_review", "any-repo")
    assert pb is not None and pb.name == "pr-review"
