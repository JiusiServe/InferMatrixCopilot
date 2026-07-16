import pytest
from pydantic import ValidationError

from eval.tasks.pr_review.benchmark.schema import BenchmarkItem, GroundTruthFinding


def finding(**updates):
    value = {
        "id": "GT-1",
        "summary": "bad cache key",
        "description": "request state is omitted",
        "severity": "Blocker",
        "category": "correctness",
        "merge_blocking": True,
        "location_required": True,
        "accepted_locations": [{"file": "a.py", "start_line": 1, "end_line": 3, "symbol": "f"}],
        "evidence": [{"file": "a.py", "start_line": 1, "end_line": 4}],
    }
    value.update(updates)
    return value


def item(**updates):
    value = {
        "benchmark_id": "pr-1",
        "repository": "org/repo",
        "pr_number": 1,
        "base_sha": "a" * 40,
        "head_sha": "b" * 40,
        "title": "change",
        "changed_files": ["a.py"],
        "expected_verdict": "REQUEST_CHANGES",
        "clean_status": "buggy",
        "gt_findings": [finding()],
    }
    value.update(updates)
    return value


def test_gt_severity_merge_blocking_constraints():
    with pytest.raises(ValidationError):
        GroundTruthFinding.model_validate(finding(severity="Critical", merge_blocking=False))
    with pytest.raises(ValidationError):
        GroundTruthFinding.model_validate(finding(severity="Nit", merge_blocking=True))


def test_verdict_is_derived_from_gt():
    with pytest.raises(ValidationError):
        BenchmarkItem.model_validate(item(expected_verdict="APPROVE"))


def test_clean_pr_has_no_gt():
    clean = BenchmarkItem.model_validate(item(
        expected_verdict="APPROVE",
        clean_status="auto_certified_clean",
        gt_findings=[],
    ))
    assert clean.gt_findings == []


def test_relative_locations_only():
    with pytest.raises(ValidationError):
        GroundTruthFinding.model_validate(finding(
            accepted_locations=[{"file": "../secret", "start_line": 1, "end_line": 2}]
        ))
