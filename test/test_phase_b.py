"""CLI phase B: when-gating, compound commands, resume, inline plan review."""

import asyncio
import shutil

import pytest

from omni_copilot.cli import Copilot
from omni_copilot.config import _REPO_ROOT
from omni_copilot.engine import Executor, StepRegistry, StepResult, StepSpec
from omni_copilot.engine.steps import register_builtin_steps
from omni_copilot.intent import parse_intents
from omni_copilot.llm import Block, Reply
from omni_copilot.notify import Notifier
from omni_copilot.playbooks.store import Playbook, PlaybookStep
from omni_copilot.run_trace import RunTrace
from omni_copilot.task_spec import TaskSpec


def test_when_gating_skips_steps(settings, trace, tmp_path):
    registry = StepRegistry()
    ran = []

    def make(name):
        async def h(ctx):
            ran.append(name)
            return StepResult(True, summary=name)
        return StepSpec(name, "deterministic", "read", h)

    registry.register(make("s.always"))
    registry.register(make("s.push_only"))
    registry.register(make("s.post_only"))
    pb = Playbook(name="pb", version=1, status="active", task_kinds=["pr_debug"],
                  repos=[], steps=[
                      PlaybookStep("a", "s.always"),
                      PlaybookStep("b", "s.push_only", when="not report_only"),
                      PlaybookStep("c", "s.post_only", when="post"),
                  ])
    run_dir = tmp_path / "r1"
    notifier = Notifier(settings, run_dir, trace, "r1")
    executor = Executor(registry, settings, run_dir=run_dir, trace=trace,
                        notifier=notifier)
    state = {"task_spec": {"kind": "pr_debug", "report_only": True, "post": False}}
    outcome = asyncio.run(executor.run(pb, state))
    assert outcome.status == "done"
    assert ran == ["s.always"]
    assert "skipped (when: not report_only)" in outcome.step_results["b"].summary
    assert "skipped (when: post)" in outcome.step_results["c"].summary


def test_compound_command_parsing_carries_target():
    results = parse_intents("rebase pr 12, then review it")
    assert all(r.spec for r in results)
    assert [r.spec.kind for r in results] == ["pr_rebase", "pr_review"]
    assert [r.spec.pr for r in results] == [12, 12]  # "it" carries PR 12

    results = parse_intents("review pr 12 then triage the new issues")
    assert [r.spec.kind for r in results] == ["pr_review", "issue_filter"]

    # ambiguous segment surfaces a clarification, nothing runs
    results = parse_intents("rebase pr 12; do magic")
    assert any(r.needs_clarification for r in results)

    # single command unaffected
    results = parse_intents("debug the ci of pr 99, report only")
    assert len(results) == 1 and results[0].spec.kind == "pr_debug"
    assert results[0].spec.report_only


@pytest.fixture()
def copilot(settings, git_repo):
    settings.playbooks_dir.mkdir(parents=True)
    for pb in ("repo-rebase", "pr-review"):
        shutil.copy(_REPO_ROOT / "playbooks" / f"{pb}.yaml",
                    settings.playbooks_dir / f"{pb}.yaml")
    settings.repo_paths = {"vllm-omni": str(git_repo)}
    settings.rebase_orchestrator_cmd = "echo ok"
    return Copilot(settings)


def test_queue_stops_on_blocked(copilot, git_repo, capsys):
    (git_repo / "dirty.txt").write_text("x")  # first task will block on guard
    specs = [TaskSpec(kind="repo_rebase"), TaskSpec(kind="repo_rebase")]
    code = copilot.run_queue(specs, assume_yes=True)
    assert code == 3
    out = capsys.readouterr().out
    assert "queued 2 tasks" in out and "queue stopped: 1 task(s) not run" in out
    # only ONE run dir was created — task 2 never started
    assert len(list(copilot.settings.run_root.iterdir())) == 1


def test_resume_reenters_first_incomplete_step(copilot, git_repo, capsys):
    (git_repo / "dirty.txt").write_text("x")
    assert copilot.run_task(TaskSpec(kind="repo_rebase"), assume_yes=True) == 3
    (git_repo / "dirty.txt").unlink()  # human fixed the workspace

    code = copilot.resume_last()
    assert code == 0
    out = capsys.readouterr().out
    assert "resuming" in out and "✓ rebase" in out
    # still only one run dir: resume reused it
    run_dirs = list(copilot.settings.run_root.iterdir())
    assert len(run_dirs) == 1
    assert (run_dirs[0] / "RUN_REPORT.md").exists()


class BlockingReviewer:
    available = True

    def create(self, **kwargs):
        return Reply(blocks=[Block(type="text",
                                   text='{"verdict": "block", "critiques": ["unsafe plan"]}')])


def test_generated_plan_blocked_by_plan_review(settings, git_repo, capsys):
    settings.playbooks_dir.mkdir(parents=True)  # empty store -> pr_review generates
    settings.repo_paths = {"vllm-omni": str(git_repo)}
    copilot = Copilot(settings)
    copilot.llm = BlockingReviewer()
    code = copilot.run_task(TaskSpec(kind="pr_review", pr=1), assume_yes=True)
    assert code == 3
    out = capsys.readouterr().out
    assert "plan review: block" in out and "plan blocked" in out
    assert not copilot.settings.run_root.exists() or \
        not list(copilot.settings.run_root.iterdir())  # nothing executed


def test_pr_review_now_resolves_via_reuse(copilot):
    res = copilot.resolve(TaskSpec(kind="pr_review", pr=4830))
    assert res.mode == "reuse" and res.playbook.name == "pr-review"
    assert not res.requires_review  # vetted playbook, no generation


def test_all_shipped_playbooks_validate():
    registry = register_builtin_steps(StepRegistry())
    from omni_copilot.playbooks.store import PlaybookStore

    store = PlaybookStore(_REPO_ROOT / "playbooks", registry)
    names = {p.name for p in store.all()}
    assert {"repo-rebase", "pr-rebase", "pr-debug", "pr-review",
            "issue-answer", "issue-triage"} <= names
    assert store.get("repo-rebase").locked
    for kind in ("repo_rebase", "pr_rebase", "pr_debug", "pr_review",
                 "issue_answer", "issue_filter"):
        assert store.find(kind) is not None, f"no playbook recalls {kind}"
