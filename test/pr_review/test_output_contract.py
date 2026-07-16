import json

import pytest

from eval.pr_review.runner.output_schema import OutputContractError, parse_agent_output


def valid_output():
    return {
        "verdict": "REQUEST_CHANGES",
        "summary": "one issue",
        "findings": [{
            "id": "F-1",
            "title": "broken",
            "description": "fails under x",
            "severity": "Major",
            "category": "correctness",
            "location": {"file": "a.py", "start_line": 1, "end_line": 1},
            "evidence": [{"file": "a.py", "start_line": 1, "end_line": 1, "reason": "x"}],
        }],
    }


def test_parse_valid_and_validate_repo_lines(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n")
    review, repaired = parse_agent_output(json.dumps(valid_output()), repo_root=tmp_path)
    assert review.findings[0].severity.value == "Major"
    assert repaired is False


def test_single_format_repair_normalizes_fence_case_and_aliases(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n")
    value = valid_output()
    value["verdict"] = "request changes"
    value["findings"][0]["severity"] = "major"
    value["findings"][0]["location"] = {"path": "a.py", "start": 1, "end": 1}
    raw = "```json\n" + json.dumps(value) + "\n```"
    review, repaired = parse_agent_output(raw, repo_root=tmp_path)
    assert repaired is True
    assert review.verdict.value == "REQUEST_CHANGES"


def test_more_than_twenty_findings_fails():
    value = valid_output()
    value["findings"] = [dict(value["findings"][0], id=f"F-{i}") for i in range(21)]
    with pytest.raises(OutputContractError):
        parse_agent_output(json.dumps(value))


def test_nonexistent_file_fails(tmp_path):
    with pytest.raises(OutputContractError):
        parse_agent_output(json.dumps(valid_output()), repo_root=tmp_path)
