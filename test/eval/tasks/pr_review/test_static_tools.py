import subprocess

import pytest

from eval.tasks.pr_review.runner.tools import StaticToolExecutor, ToolRefused
from eval.tasks.pr_review.runner.trace_collector import TraceCollector


def test_static_tools_are_bounded_and_trace_policy_violations(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "a@b.c"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "a"], cwd=repo, check=True)
    (repo / "a.py").write_text("alpha\nbeta\n")
    subprocess.run(["git", "add", "a.py"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    trace = TraceCollector(tmp_path / "trace.jsonl")
    tools = StaticToolExecutor(workspace=repo, allowed_commits={sha}, trace=trace)
    assert tools.read_file("a.py", start_line=2) == "beta"
    assert tools.search_text("alpha")[0]["line"] == 1
    assert "a.py" in tools.git("show", "--name-only", sha)
    with pytest.raises(ToolRefused):
        tools.git("checkout", "main")
    assert any(event["kind"] == "policy_violation" for event in trace.events())
