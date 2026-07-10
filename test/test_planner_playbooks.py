import pytest

from omni_copilot.engine.steps import register_builtin_steps
from omni_copilot.engine.planner import Planner, PlanningError
from omni_copilot.engine.registry import StepRegistry
from omni_copilot.playbooks.store import PlaybookStore
from omni_copilot.task_spec import TaskSpec

LOCKED_PB = """\
name: repo-rebase
version: 1
status: locked
task_kinds: [repo_rebase]
repos: [vllm-omni]
params:
  report_only: {type: bool}
steps:
  - {id: guard, step: workspace.guard_clean}
  - {id: rebase, step: rebase.run_external}
  - {id: report, step: report.final_summary}
"""

ACTIVE_PB = """\
name: pr-debug
version: 2
status: active
task_kinds: [pr_debug]
repos: [vllm-omni]
params:
  max_groups: {type: int}
steps:
  - {id: guard, step: workspace.guard_clean}
  - {id: report, step: report.final_summary}
"""


@pytest.fixture()
def stack(settings):
    settings.playbooks_dir.mkdir(parents=True)
    (settings.playbooks_dir / "repo-rebase.yaml").write_text(LOCKED_PB)
    (settings.playbooks_dir / "pr-debug.yaml").write_text(ACTIVE_PB)
    registry = register_builtin_steps(StepRegistry())
    store = PlaybookStore(settings.playbooks_dir, registry)
    return store, Planner(store, registry)


def test_store_rejects_unknown_step(settings):
    settings.playbooks_dir.mkdir(parents=True)
    (settings.playbooks_dir / "bad.yaml").write_text(
        "name: bad\nstatus: active\ntask_kinds: [pr_review]\n"
        "steps: [{id: x, step: no.such.step}]\n"
    )
    registry = register_builtin_steps(StepRegistry())
    with pytest.raises(ValueError, match="unregistered step"):
        PlaybookStore(settings.playbooks_dir, registry)


def test_reuse_locked_playbook_is_L0(stack):
    _, planner = stack
    res = planner.resolve(TaskSpec(kind="repo_rebase"))
    assert res.mode == "reuse"
    assert res.playbook.name == "repo-rebase" and res.playbook.locked
    assert res.tier == "L0" and not res.requires_review


def test_declared_params_still_reuse(stack):
    _, planner = stack
    res = planner.resolve(TaskSpec(kind="repo_rebase", params={"report_only": True}))
    assert res.mode == "reuse"


def test_locked_playbook_refuses_adaptation(stack):
    _, planner = stack
    with pytest.raises(PlanningError, match="locked"):
        planner.resolve(TaskSpec(kind="repo_rebase", params={"custom_wave": ["x"]}))


def test_active_playbook_adapts_with_review(stack):
    _, planner = stack
    res = planner.resolve(TaskSpec(kind="pr_debug", pr=7,
                                   params={"extra_pipeline": "amd"}))
    assert res.mode == "adapt" and res.requires_review and res.tier == "L1"


def test_generate_only_for_read_only_kinds(stack):
    _, planner = stack
    res = planner.resolve(TaskSpec(kind="pr_review", pr=12))
    assert res.mode == "generate" and res.requires_review and res.tier == "L2"
    assert res.playbook.status == "candidate"
    # every generated step is read/report risk
    with pytest.raises(PlanningError, match="not allowed for code-modifying"):
        planner.resolve(TaskSpec(kind="pr_rebase", pr=12))  # no pr-rebase playbook


def test_candidate_save_roundtrip(stack, settings):
    store, planner = stack
    res = planner.resolve(TaskSpec(kind="pr_review", pr=12))
    path = store.save_candidate(res.playbook)
    assert path.exists()
    store.load()
    saved = store.get("generated-pr_review")
    assert saved is not None and saved.status == "candidate"
    # candidates are never recalled by find()
    assert store.find("pr_review") is None
