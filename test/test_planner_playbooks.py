import pytest

from infermatrix_copilot.engine.steps import register_builtin_steps
from infermatrix_copilot.engine.planner import Planner, PlanningError
from infermatrix_copilot.engine.registry import StepRegistry
from infermatrix_copilot.playbooks.store import PlaybookStore
from infermatrix_copilot.task_spec import TaskSpec

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
  - {id: rebase, step: report.final_summary}
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


def test_real_pr_review_playbook_reuses_with_review_depth():
    """The shipped pr-review.yaml declares review_depth, so a spec carrying it
    resolves as reuse (L0) — an undeclared param would demote to adapt (L1,
    review-gated), which the MCP --execute-reserved child cannot gate."""
    from infermatrix_copilot.config import _REPO_ROOT

    registry = register_builtin_steps(StepRegistry())
    store = PlaybookStore(_REPO_ROOT / "playbooks", registry)
    planner = Planner(store, registry)
    res = planner.resolve(
        TaskSpec(kind="pr_review", pr=7, params={"review_depth": "full"}),
        capabilities={"repo.path"})
    assert res.mode == "reuse" and not res.requires_review
    assert res.playbook.name == "pr-review"


# -- plan-review gate: no human ⇒ no pass (PR1) -------------------------------
# A non-`lgtm` verdict is only ever SURFACED — the human `[y/N]` is what gates
# it. `--yes` deletes that human, so the same verdict must stop the run.
# Measured on the release matrix: an unparseable reviewer reply ("revise") let
# three of four backends run a pr-rebase plan through to its push gate, while
# the one backend whose reviewer parsed cleanly BLOCKED the very same plan.

def _gate(settings, verdict_kind, *, assume_yes, monkeypatch):
    """Drive Copilot._plan_review_gate with a scripted plan reviewer over a
    resolution that requires review (adapted/generated plans and explicit
    --playbook overrides; exact reuse never reaches this gate)."""
    from infermatrix_copilot.cli import Copilot
    from infermatrix_copilot.cli import copilot as copilot_mod
    from infermatrix_copilot.engine.planner import Resolution
    from infermatrix_copilot.review.reviewer import ReviewVerdict
    from infermatrix_copilot.task_spec import TaskSpec

    monkeypatch.setattr(
        copilot_mod, "run_plan_review",
        lambda *a, **kw: ReviewVerdict(verdict_kind, ["scripted"]))
    settings.playbooks_dir.mkdir(parents=True, exist_ok=True)
    (settings.playbooks_dir / "pr-debug.yaml").write_text(ACTIVE_PB)
    registry = register_builtin_steps(StepRegistry())
    store = PlaybookStore(settings.playbooks_dir, registry)
    resolution = Resolution(mode="adapt", playbook=store.get("pr-debug"),
                            tier="L1", requires_review=True)
    return Copilot(settings)._plan_review_gate(
        resolution, TaskSpec(kind="pr_debug", pr=1), assume_yes)


@pytest.mark.parametrize("verdict_kind", ["revise", "unavailable"])
def test_headless_run_is_blocked_by_a_non_lgtm_plan_review(
        settings, monkeypatch, verdict_kind):
    assert _gate(settings, verdict_kind, assume_yes=True,
                 monkeypatch=monkeypatch) is False, (
        f"--yes + {verdict_kind} must not execute an unvetted plan: there is "
        "no human left to read the verdict it was surfaced to")


def test_headless_run_still_proceeds_on_lgtm(settings, monkeypatch):
    assert _gate(settings, "lgtm", assume_yes=True,
                 monkeypatch=monkeypatch) is True


def test_block_stops_regardless_of_the_human(settings, monkeypatch):
    for assume_yes in (True, False):
        assert _gate(settings, "block", assume_yes=assume_yes,
                     monkeypatch=monkeypatch) is False


@pytest.mark.parametrize("verdict_kind", ["revise", "unavailable"])
def test_interactive_run_surfaces_and_defers_to_the_confirm(
        settings, monkeypatch, verdict_kind):
    """Unchanged interactively: the verdict is printed and the user's [y/N]
    remains the gate — this fix removes nothing a human still sees."""
    assert _gate(settings, verdict_kind, assume_yes=False,
                 monkeypatch=monkeypatch) is True
