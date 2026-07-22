import json
from pathlib import Path
from types import SimpleNamespace

from omni_copilot.llm import Block, Reply

from eval.tasks.pr_review.runner.input_builder import AgentInput
from eval.tasks.pr_review.runner.output_schema import parse_agent_output
from eval.tasks.pr_review.runner.tools import StaticToolExecutor
from eval.tasks.pr_review.runner.trace_collector import TraceCollector
from eval.tasks.pr_review.subjects.config import (
    AgentSubjectConfig,
    CopilotConfig,
    load_agent_config,
    read_verified_skill,
)
from eval.tasks.pr_review.subjects.copilot_adapter import CopilotAgentAdapter
from eval.tasks.pr_review.subjects.factory import load_and_build_agent_adapter
from eval.tasks.pr_review.subjects.skill_adapter import SkillOnlyAgentAdapter


ROOT = Path(__file__).resolve().parents[4]
AGENTS = ROOT / "eval/configs/pr_review/agents"


class ScriptedLLM:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []
        self.available = True
        self.settings = SimpleNamespace(agent_model="fake-review-model")

    def create(self, *, system, messages, tools=None, model=None, max_tokens=None, on_text=None):
        self.calls.append(
            {
                "system": system,
                "messages": [*messages],
                "tools": tools or [],
                "model": model,
            }
        )
        return self.replies.pop(0)


def _agent_input() -> AgentInput:
    return AgentInput(
        benchmark_id="fixture-pr-1",
        repository="vllm-project/vllm-omni",
        pr_number=1,
        title="Fix behavior",
        body="Regression fix",
        base_branch="main",
        base_sha="1" * 40,
        head_sha="2" * 40,
        commits=[],
        changed_files=["a.py"],
        diff="diff --git a/a.py b/a.py\n@@ -1 +1 @@\n-old\n+new",
    )


def _executor(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "a.py").write_text("new\n", encoding="utf-8")
    trace = TraceCollector(tmp_path / "trace.jsonl")
    tools = StaticToolExecutor(
        workspace=workspace,
        allowed_commits={"1" * 40, "2" * 40},
        trace=trace,
    )
    return workspace, trace, tools


def _strict_review_reply() -> Reply:
    payload = {
        "schema_version": "pr-review-output-v0.1",
        "verdict": "REQUEST_CHANGES",
        "summary": "One issue found.",
        "findings": [
            {
                "id": "finding-1",
                "title": "Wrong behavior",
                "description": "The changed branch returns the wrong value.",
                "severity": "Major",
                "category": "correctness",
                "location": {"file": "a.py", "start_line": 1, "end_line": 1},
                "evidence": [
                    {
                        "file": "a.py",
                        "start_line": 1,
                        "end_line": 1,
                        "reason": "Read the changed file.",
                    }
                ],
            }
        ],
    }
    return Reply(
        blocks=[Block(type="text", text=json.dumps(payload))],
        usage={"input_tokens": 10, "output_tokens": 5},
    )


def _copilot_contract_reply() -> Reply:
    payload = {
        "status": "success",
        "summary": "One issue found.",
        "findings": [],
        "files_read": ["a.py"],
        "files_modified": [],
        "tests_requested": [],
        "tests_run": [],
        "assumptions": [],
        "blockers": [],
        "confidence": "high",
        "failure_kind": None,
        "next_action": "request changes",
        "review_comments": [
            {
                "file": "a.py",
                "line": 1,
                "severity": "major",
                "category": "correctness",
                "comment": "The changed branch returns the wrong value.",
                "evidence": "Read a.py:1 and compared the changed branch.",
            }
        ],
    }
    return Reply(
        blocks=[Block(type="text", text=json.dumps(payload))],
        usage={"input_tokens": 20, "output_tokens": 8},
    )


def test_three_versioned_agent_configs_load_and_skill_is_pinned():
    kinds = set()
    for path in sorted(AGENTS.glob("*.yaml")):
        config_path, config = load_agent_config(path)
        kinds.add(config.kind)
        if config.skill:
            skill_path, text, digest = read_verified_skill(
                config.skill, config_path=config_path
            )
            assert skill_path.name == "SKILL.md"
            assert "# vLLM-Omni PR Review" in text
            assert digest == config.skill.sha256
    assert kinds == {"copilot", "copilot_with_skill", "skill_only"}


def test_factory_builds_all_three_subjects_with_same_injected_llm():
    llm = ScriptedLLM([])
    adapters = []
    for path in sorted(AGENTS.glob("*.yaml")):
        config, adapter = load_and_build_agent_adapter(path, llm=llm)
        adapters.append((config.kind, adapter))
        assert adapter.llm is llm
        assert adapter.version
    assert {kind for kind, _ in adapters} == {
        "copilot",
        "copilot_with_skill",
        "skill_only",
    }


def test_skill_only_adapter_uses_offline_contract_and_static_tools(tmp_path):
    workspace, trace, tools = _executor(tmp_path)
    config = AgentSubjectConfig(
        name="skill-only-test",
        kind="skill_only",
        version="test-v1",
        skill={"path": "unused"},
        copilot=CopilotConfig(review_ensemble=False),
    )
    llm = ScriptedLLM([_strict_review_reply()])
    adapter = SkillOnlyAgentAdapter(config, skill_text="BLOCKER scan", llm=llm)

    raw = adapter.review(
        _agent_input(), workspace=str(workspace), tools=tools, trace=trace
    )
    review, repaired = parse_agent_output(raw, repo_root=workspace)

    assert not repaired
    assert review.verdict.value == "REQUEST_CHANGES"
    assert "OFFLINE" in llm.calls[0]["system"]
    assert "BLOCKER scan" in llm.calls[0]["messages"][0]["content"]
    assert {tool["name"] for tool in llm.calls[0]["tools"]} == {
        "read_file",
        "list_dir",
        "grep",
        "git_readonly",
    }
    assert any(event["kind"] == "model_usage" for event in trace.events())


def test_copilot_adapter_runs_real_review_step_with_injected_offline_tools(tmp_path):
    workspace, trace, tools = _executor(tmp_path)
    config = AgentSubjectConfig(
        name="copilot-skill-test",
        kind="copilot_with_skill",
        version="test-v1",
        model="fake-review-model",
        skill={"path": "unused"},
        copilot=CopilotConfig(
            review_depth="light",
            review_ensemble=False,
            profile_briefing_enabled=False,
            builtin_skills_enabled=False,
        ),
    )
    llm = ScriptedLLM([_copilot_contract_reply()])
    adapter = CopilotAgentAdapter(
        config, external_skill_text="EXTERNAL REVIEW SKILL", llm=llm
    )

    raw = adapter.review(
        _agent_input(), workspace=str(workspace), tools=tools, trace=trace
    )
    review, repaired = parse_agent_output(raw, repo_root=workspace)

    assert not repaired
    assert review.findings[0].category.value == "correctness"
    prompt = llm.calls[0]["messages"][0]["content"]
    assert "EXTERNAL REVIEW SKILL" in prompt
    tool_names = {tool["name"] for tool in llm.calls[0]["tools"]}
    assert {"read_file", "list_dir", "grep", "git_readonly"} <= tool_names
    assert "gh_pr_view" not in tool_names
    assert any(
        event["kind"] == "subject_result" and event["subject_kind"] == "copilot_with_skill"
        for event in trace.events()
    )


def _git(cwd: Path, *args: str) -> str:
    import subprocess

    proc = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return proc.stdout.strip()


def test_candidate_generation_runs_end_to_end_with_concrete_subject(tmp_path):
    import hashlib
    import yaml

    from eval.tasks.pr_review.repository.cache import RepositoryCache
    from eval.tasks.pr_review.runner.evaluation_runner import run_benchmark

    source = tmp_path / "source"
    source.mkdir()
    _git(source, "init", "-q")
    _git(source, "config", "user.email", "eval@example.com")
    _git(source, "config", "user.name", "Eval")
    (source / "a.py").write_text("old\n", encoding="utf-8")
    _git(source, "add", "a.py")
    _git(source, "commit", "-qm", "base")
    base_sha = _git(source, "rev-parse", "HEAD")
    (source / "a.py").write_text("new\n", encoding="utf-8")
    _git(source, "commit", "-qam", "head")
    head_sha = _git(source, "rev-parse", "HEAD")

    benchmark = tmp_path / "benchmark"
    items = benchmark / "items"
    items.mkdir(parents=True)
    item_path = items / "fixture.yaml"
    item = {
        "schema_version": "pr-review-item-v0.1",
        "benchmark_id": "fixture-pr-1",
        "repository": "example/repo",
        "pr_number": 1,
        "base_branch": "main",
        "base_sha": base_sha,
        "head_sha": head_sha,
        "title": "Change a.py",
        "body": "",
        "commits": [{"sha": head_sha, "message": "head"}],
        "changed_files": ["a.py"],
        "expected_verdict": "APPROVE",
        "clean_status": "auto_certified_clean",
        "split": "dev",
        "gt_findings": [],
        "invalidated": False,
    }
    item_path.write_text(yaml.safe_dump(item, sort_keys=False), encoding="utf-8")
    digest = hashlib.sha256(item_path.read_bytes()).hexdigest()
    manifest_path = benchmark / "manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "pr-review-manifest-v0.1",
                "benchmark_version": "fixture-v1",
                "rubric_version": "rubric-v1",
                "judge_version": "judge-v1",
                "created_at": "2026-07-17T00:00:00Z",
                "entries": [
                    {
                        "benchmark_id": "fixture-pr-1",
                        "item": "items/fixture.yaml",
                        "sha256": digest,
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    cache_root = tmp_path / "cache"
    RepositoryCache(cache_root).import_local("example/repo", source)
    clean_reply = {
        "schema_version": "pr-review-output-v0.1",
        "verdict": "APPROVE",
        "summary": "No actionable issue found.",
        "findings": [],
    }
    llm = ScriptedLLM(
        [
            Reply(
                blocks=[Block(type="text", text=json.dumps(clean_reply))],
                usage={"input_tokens": 3, "output_tokens": 2},
            )
        ]
    )
    config = AgentSubjectConfig(
        name="skill-only-e2e",
        kind="skill_only",
        version="test-v1",
        skill={"path": "unused"},
        copilot=CopilotConfig(review_ensemble=False),
    )
    adapter = SkillOnlyAgentAdapter(config, skill_text="Review carefully.", llm=llm)
    output = run_benchmark(
        manifest_path=manifest_path,
        repository_cache=cache_root,
        output_dir=tmp_path / "run",
        adapter=adapter,
        model="fake-review-model",
        prompt_version="test",
    )

    prediction = json.loads(
        (output / "predictions/fixture-pr-1.json").read_text(encoding="utf-8")
    )
    metadata = json.loads(
        (output / "metadata/fixture-pr-1.json").read_text(encoding="utf-8")
    )
    assert prediction["verdict"] == "APPROVE"
    assert metadata["output_contract_valid"] is True
    assert metadata["agent_failure"] is False
    assert metadata["input_tokens"] == 3


def test_matrix_scoring_handles_three_arms_in_one_campaign(tmp_path):
    import hashlib
    import subprocess
    import yaml

    from eval.tasks.pr_review.repository.cache import RepositoryCache
    from eval.tasks.pr_review.runner.evaluation_runner import run_benchmark
    from eval.tasks.pr_review.subjects.matrix import score_experiment_matrix

    source = tmp_path / "source"
    source.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=source, check=True)
    subprocess.run(["git", "config", "user.email", "eval@example.com"], cwd=source, check=True)
    subprocess.run(["git", "config", "user.name", "Eval"], cwd=source, check=True)
    (source / "a.py").write_text("old\n", encoding="utf-8")
    subprocess.run(["git", "add", "a.py"], cwd=source, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=source, check=True)
    base_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    (source / "a.py").write_text("new\n", encoding="utf-8")
    subprocess.run(["git", "commit", "-qam", "head"], cwd=source, check=True)
    head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()

    benchmark = tmp_path / "benchmark"
    (benchmark / "items").mkdir(parents=True)
    item_path = benchmark / "items/item.yaml"
    item_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "pr-review-item-v0.1",
                "benchmark_id": "fixture-pr-1",
                "repository": "example/repo",
                "pr_number": 1,
                "base_branch": "main",
                "base_sha": base_sha,
                "head_sha": head_sha,
                "title": "Change a.py",
                "body": "",
                "commits": [],
                "changed_files": ["a.py"],
                "expected_verdict": "APPROVE",
                "clean_status": "auto_certified_clean",
                "split": "dev",
                "gt_findings": [],
                "invalidated": False,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    manifest_path = benchmark / "manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "pr-review-manifest-v0.1",
                "benchmark_version": "fixture-v1",
                "rubric_version": "rubric-v1",
                "judge_version": "judge-v1",
                "created_at": "2026-07-17T00:00:00Z",
                "entries": [
                    {
                        "benchmark_id": "fixture-pr-1",
                        "item": "items/item.yaml",
                        "sha256": hashlib.sha256(item_path.read_bytes()).hexdigest(),
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    cache = tmp_path / "cache"
    RepositoryCache(cache).import_local("example/repo", source)
    clean = json.dumps(
        {
            "schema_version": "pr-review-output-v0.1",
            "verdict": "APPROVE",
            "summary": "No issue.",
            "findings": [],
        }
    )
    run_dirs = []
    for index in range(3):
        llm = ScriptedLLM([Reply(blocks=[Block(type="text", text=clean)])])
        config = AgentSubjectConfig(
            name=f"arm-{index}",
            kind="skill_only",
            version="test-v1",
            skill={"path": "unused"},
            copilot=CopilotConfig(review_ensemble=False),
        )
        adapter = SkillOnlyAgentAdapter(config, skill_text="Review.", llm=llm)
        run_dirs.append(
            run_benchmark(
                manifest_path=manifest_path,
                repository_cache=cache,
                output_dir=tmp_path / f"run-{index}",
                adapter=adapter,
            )
        )

    matrix_root = tmp_path / "matrix"
    matrix_root.mkdir()
    (matrix_root / "matrix.json").write_text(
        json.dumps(
            {
                "runs": [
                    {
                        "agent": f"arm-{index}",
                        "kind": "skill_only",
                        "version": "test-v1",
                        "replicate": 1,
                        "run_dir": str(run_dir),
                    }
                    for index, run_dir in enumerate(run_dirs)
                ]
            }
        ),
        encoding="utf-8",
    )
    reports = score_experiment_matrix(
        matrix_run_root=matrix_root,
        manifest_path=manifest_path,
    )
    scores = json.loads((reports / "matrix-scores.json").read_text(encoding="utf-8"))
    assert len(scores["runs"]) == 3
    assert scores["invalidated_benchmark_ids"] == []
    assert "arm-0/run-01" in (reports / "matrix-summary.md").read_text(encoding="utf-8")
