from eval.pr_review.runner.tool_policy import ToolDecision, ToolPolicy


def test_readonly_git_is_allowed_and_mutation_is_refused(tmp_path):
    policy = ToolPolicy(workspace=tmp_path, allowed_commits={"a" * 40})
    assert policy.check_command("git diff").decision == ToolDecision.ALLOW
    result = policy.check_command("git checkout main")
    assert result.decision == ToolDecision.REFUSE
    assert result.violation == "repository_mutation"


def test_code_execution_and_network_are_refused(tmp_path):
    policy = ToolPolicy(workspace=tmp_path, allowed_commits=set())
    assert policy.check_command("pytest -q").violation == "code_execution"
    assert policy.check_command("curl https://example.com").violation == "network_access"


def test_path_escape_is_refused(tmp_path):
    policy = ToolPolicy(workspace=tmp_path, allowed_commits=set())
    assert policy.check_path("../gt.json").decision == ToolDecision.REFUSE
