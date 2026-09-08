"""AFD local validation must describe executed tests and the checked tree."""

from __future__ import annotations

import asyncio
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from infermatrix_copilot.engine.step import StepContext
from infermatrix_copilot.engine.steps import rebase_v3
from infermatrix_copilot.rebase_engine import pytest_results
from infermatrix_copilot.rebase_engine.push_gate import evaluate_push_gate
from infermatrix_copilot.rebase_engine.pytest_results import pytest_result, runtime_identity
from infermatrix_copilot.rebase_engine.substate import Substate
from infermatrix_copilot.rebase_engine.test_loop import TestRunResult, run_test_loop
from infermatrix_copilot.testing.runner import TestOutcome as RunnerOutcome, TestRunner


def run_failed_job(tmp_path, current, baseline, *, allow_preexisting=True):
    debugged, compared = [], []

    async def debug(*args):
        debugged.append(args[0])
        return False

    result = asyncio.run(run_test_loop(
        [{"slug": "unit", "min_gpus": 0}],
        substate=Substate(tmp_path, "review"), run_fn=lambda _: current,
        baseline_fn=lambda slug: compared.append(slug) or baseline,
        debug_fn=debug, allow_preexisting=allow_preexisting))
    return result, debugged, compared


@pytest.mark.parametrize("baseline", [
    TestRunResult(1),
    TestRunResult(1, failures=(("test_old", "AssertionError", "old"),)),
    TestRunResult(1, failures=(("test_new", "AssertionError", "different error"),)),
    TestRunResult(2, infra="pytest collection failure"),
])
def test_double_red_cannot_hide_new_or_unproven_failure(tmp_path, baseline):
    current = TestRunResult(1, failures=(
        ("test_old", "AssertionError", "old"),
        ("test_new", "AssertionError", "new")))
    result, debugged, _ = run_failed_job(tmp_path, current, baseline)
    assert result["failed_tests"] == ["unit"]
    assert result["skipped_tests"] == []
    assert debugged == ["unit"]
    assert not evaluate_push_gate(
        {"tests": {"pipeline": result}}, {"strict_push_gate": True}).allowed


def test_other_modes_can_recognize_matching_assertion_failures(tmp_path):
    failure = TestRunResult(1, failures=(("test_old", "AssertionError", "old"),))
    result, debugged, compared = run_failed_job(tmp_path, failure, failure)
    assert result["skipped_tests"] == ["unit"]
    assert debugged == [] and compared == ["unit"]


def test_local_rebase_never_uses_new_runtime_as_old_baseline_proof(tmp_path):
    failure = TestRunResult(1, failures=(("test_old", "AssertionError", "old"),))
    result, debugged, compared = run_failed_job(
        tmp_path, failure, failure, allow_preexisting=False)
    assert result["failed_tests"] == ["unit"]
    assert debugged == ["unit"] and compared == []


def test_junit_counts_errors_and_optional_skips(tmp_path):
    report = tmp_path / "results.xml"
    report.write_text('<testsuite><testcase name="pass"/>'
                      '<testcase name="npu"><skipped message="no ascend"/>'
                      '</testcase></testsuite>')
    result = pytest_result(RunnerOutcome(0), report)
    assert result.rc == 0 and not result.infra
    assert result.counts == {"collected": 2, "passed": 1, "failed": 0,
                             "errors": 0, "skipped": 1}
    required = pytest_result(RunnerOutcome(0), report, runtime_required=True)
    assert required.rc != 0 and "required runtime tests skipped" in required.infra
    report.write_text('<testsuite><testcase name="collection"><error '
                      'message="ModuleNotFoundError: torch"/></testcase></testsuite>')
    failure = pytest_result(RunnerOutcome(2), report)
    assert failure.counts["errors"] == 1
    assert "collection" in failure.infra


def test_required_runtime_all_skip_or_missing_report_cannot_pass(tmp_path):
    report = tmp_path / "results.xml"
    report.write_text('<testsuite><testcase name="runtime"><skipped/>'
                      '</testcase></testsuite>')
    result = pytest_result(RunnerOutcome(0), report, runtime_required=True)
    assert result.rc != 0 and result.counts["passed"] == 0
    report.unlink()
    assert pytest_result(RunnerOutcome(0), report).infra


@pytest.mark.parametrize(("source", "expected"), [
    ('import pytest\ndef test_runtime(): pytest.skip("no torch")\n', "skipped"),
    ('import missing_afd_review_dependency\n', "errors"),
])
def test_real_pytest_skip_and_collection_reports(tmp_path, source, expected):
    tests = tmp_path / "test_runtime.py"
    tests.write_text(source)
    report = tmp_path / "result.xml"
    run = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(tests), f"--junitxml={report}"],
        cwd=tmp_path, capture_output=True, text=True, check=False, timeout=30)
    result = pytest_result(RunnerOutcome(run.returncode), report, runtime_required=True)
    assert result.counts[expected] == 1
    assert result.infra and result.rc != 0


def test_runtime_identity_checks_real_interpreter_version_source_and_commit(git_repo):
    package = git_repo / "review_runtime.py"
    package.write_text('__version__ = "0.28.0"\n')
    metadata = git_repo / "review_runtime-0.28.0.dist-info"
    metadata.mkdir()
    (metadata / "METADATA").write_text(
        "Metadata-Version: 2.1\nName: review-runtime\nVersion: 0.28.0\n")
    commit = subprocess.run(
        ["git", "-C", str(git_repo), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True).stdout.strip()
    env = {**os.environ, "PYTHONPATH": str(git_repo)}
    identity = runtime_identity(
        sys.executable, "review_runtime", "0.28.0", env=env,
        cwd=git_repo, upstream=str(git_repo), commit=commit)
    assert identity["version"] == "0.28.0"
    assert identity["commit"] == commit
    assert Path(identity["origin"]) == package
    with pytest.raises(ValueError, match="version mismatch"):
        runtime_identity(sys.executable, "review_runtime", "0.26.0",
                         env=env, cwd=git_repo)
    with pytest.raises(ValueError, match="selected commit"):
        runtime_identity(sys.executable, "review_runtime", "0.28.0", env=env,
                         cwd=git_repo, upstream=str(git_repo), commit="0" * 40)
    with pytest.raises(ValueError, match="not selected source"):
        runtime_identity(sys.executable, "review_runtime", "0.28.0", env=env,
                         cwd=git_repo, upstream=str(git_repo / "other"), commit=commit)


@pytest.fixture()
def validation_context(git_repo, settings, trace, tmp_path, monkeypatch):
    manifest = {
        "repo": {"venv": str(Path(sys.executable).parent.parent)},
        "upstream": {"target_version": "0.28.0"},
        "modules": {"plugin_boundary": {}},
        "rebase": {
            "wheel": {"package": "vllm"},
            "local_tests": {"pytest_junit": True, "require_runtime": True,
                            "jobs": [
                                {"label": "unit", "command": "python -m pytest",
                                 "min_gpus": 0, "module": "plugin_boundary"},
                                {"label": "runtime", "command": "python -m pytest",
                                 "min_gpus": 0, "runtime_required": True,
                                 "module": "plugin_boundary"}]},
            "test_manifest": {"yaml_dir": ".ci", "pipelines": {},
                              "queue_map": {"cpu": [0, "cpu"]},
                              "default_queue": "cpu"},
            "precommit": {"command": "pre-commit run --all-files"},
        },
    }
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    ctx = StepContext(
        settings=settings, run_dir=run_dir, trace=trace, params={},
        state={"repo_path": str(git_repo), "run_id": "review",
               "upstream_path": str(git_repo), "upstream_commit": "a" * 40,
               "task_spec": {"repo": "afd-plugin",
                             "params": {"rebase_mode": "local_rebase"}}})
    monkeypatch.setattr(rebase_v3, "_adapter_manifest", lambda _: manifest)
    monkeypatch.setattr(rebase_v3, "_ensure_checkout_locks", lambda *args: None)
    monkeypatch.setattr(pytest_results, "runtime_identity", lambda *args, **kwargs: {
        "package": "vllm", "version": "0.28.0", "origin": "/target/vllm/__init__.py"})
    return ctx, manifest


def write_job_report(env, body):
    report = next(arg.split("=", 1)[1] for arg in shlex.split(env["PYTEST_ADDOPTS"])
                  if arg.startswith("--junitxml="))
    Path(report).write_text("<testsuite>" + body + "</testsuite>")


def test_local_loop_records_required_runtime_execution(validation_context, monkeypatch):
    ctx, _ = validation_context

    def run(self, job, env, **kwargs):
        body = ('<testcase name="runtime"><skipped/></testcase>'
                if job.key == "runtime" else '<testcase name="cpu"/>')
        write_job_report(env, body)
        return RunnerOutcome(0)

    monkeypatch.setattr(TestRunner, "run", run)
    result = asyncio.run(rebase_v3._v3_test_loop(ctx))
    data = Substate(ctx.run_dir, "review").read()
    assert result.ok
    assert data["tests"]["pipeline"]["complete"]
    assert data["tests"]["pipeline"]["test_counts"]["skipped"] == 1
    assert data["tests"]["jobs"]["runtime"]["status"] == "infra"
    assert not evaluate_push_gate(data, {}).allowed
    assert data["afd_validation_sha"] == result.outputs["state_updates"]["afd_validation_sha"]


def test_local_rebase_requires_declared_runtime_job(validation_context, monkeypatch):
    ctx, manifest = validation_context
    manifest["rebase"]["local_tests"]["jobs"].pop()

    def run(self, job, env, **kwargs):
        write_job_report(env, '<testcase name="cpu"/>')
        return RunnerOutcome(0)

    monkeypatch.setattr(TestRunner, "run", run)
    result = asyncio.run(rebase_v3._v3_test_loop(ctx))
    data = Substate(ctx.run_dir, "review").read()
    assert result.ok and not data["tests"]["pipeline"]["complete"]
    assert not evaluate_push_gate(data, {}).allowed


def test_precommit_source_fix_rechecks_tests_and_final_digest(validation_context, monkeypatch):
    ctx, _ = validation_context
    sub = Substate(ctx.run_dir, "review")
    sub.update({"phase3_progress": {"completed": ["unit", "runtime"]}})
    before = rebase_v3._worktree_digest(ctx.state["repo_path"])
    ctx.state["afd_validation_worktree_digest"] = before
    calls = []

    def run(self, job, env, **kwargs):
        calls.append(job.key)
        if job.key == "__precommit__":
            (Path(ctx.state["repo_path"]) / "mod_a.py").write_text("A = 2\n")
        else:
            write_job_report(env, '<testcase name="contract"/>')
        return RunnerOutcome(0)

    monkeypatch.setattr(TestRunner, "run", run)
    result = asyncio.run(rebase_v3._v3_precommit(ctx))
    assert result.ok and calls == ["__precommit__", "unit", "runtime"]
    data = sub.read()
    assert data["tests"]["precommit"]["tests_rechecked"]
    assert data["tests"]["pipeline"]["passed"] == 2
    digest = rebase_v3._worktree_digest(ctx.state["repo_path"])
    assert digest != before
    assert data["afd_validation_worktree_digest"] == digest
    assert result.outputs["state_updates"]["afd_validation_worktree_digest"] == digest


def test_precommit_recheck_cannot_debug_away_a_new_failure(validation_context, monkeypatch):
    ctx, _ = validation_context

    def run(self, job, env, **kwargs):
        if job.key == "__precommit__":
            (Path(ctx.state["repo_path"]) / "mod_a.py").write_text("A = 2\n")
        else:
            write_job_report(env, '<testcase name="contract"><failure '
                             'message="new failure"/></testcase>')
        return RunnerOutcome(0 if job.key == "__precommit__" else 1)

    def no_agent(*args):
        raise AssertionError("Post-hook verification must not edit the checked tree")

    monkeypatch.setattr(TestRunner, "run", run)
    monkeypatch.setattr(rebase_v3, "_tier_client", no_agent)
    result = asyncio.run(rebase_v3._v3_precommit(ctx))
    data = Substate(ctx.run_dir, "review").read()
    assert result.ok
    assert data["tests"]["pipeline"]["failed"] == 2
    assert result.outputs["state_updates"]["phase3_failed"] == ["unit", "runtime"]
    assert not evaluate_push_gate(data, {"strict_push_gate": True}).allowed


def test_resume_reuses_results_only_for_identical_tree(validation_context, monkeypatch):
    ctx, _ = validation_context
    calls = []

    def run(self, job, env, **kwargs):
        calls.append(job.key)
        write_job_report(env, '<testcase name="contract"/>')
        return RunnerOutcome(0)

    monkeypatch.setattr(TestRunner, "run", run)
    assert asyncio.run(rebase_v3._v3_test_loop(ctx)).ok
    assert asyncio.run(rebase_v3._v3_test_loop(ctx)).ok
    assert calls == ["unit", "runtime"]
    (Path(ctx.state["repo_path"]) / "mod_a.py").write_text("A = 3\n")
    assert asyncio.run(rebase_v3._v3_test_loop(ctx)).ok
    assert calls == ["unit", "runtime", "unit", "runtime"]


def test_later_runtime_fix_rechecks_previously_passing_cpu_job(validation_context, monkeypatch):
    ctx, _ = validation_context
    fixed = []
    calls = []

    def run(self, job, env, **kwargs):
        calls.append(job.key)
        fails = (job.key == "runtime" and not fixed) or (job.key == "unit" and fixed)
        body = ('<testcase name="contract"><failure message="regression"/></testcase>'
                if fails else '<testcase name="contract"/>')
        write_job_report(env, body)
        return RunnerOutcome(1 if fails else 0)

    async def fix(*args):
        fixed.append(True)
        (Path(ctx.state["repo_path"]) / "mod_a.py").write_text("A = 4\n")
        return "done"

    monkeypatch.setattr(TestRunner, "run", run)
    monkeypatch.setattr(rebase_v3, "_tier_client", lambda _: (None, None))
    monkeypatch.setattr(rebase_v3, "_run_debug_agent", fix)
    result = asyncio.run(rebase_v3._v3_test_loop(ctx))
    data = Substate(ctx.run_dir, "review").read()
    assert result.ok and fixed == [True]
    assert calls == ["unit", "runtime", "runtime", "unit", "runtime"]
    assert data["tests"]["pipeline"]["failed_tests"] == ["unit"]
    assert data["tests"]["jobs"]["unit"]["status"] == "failed"
