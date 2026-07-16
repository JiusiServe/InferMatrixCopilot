from eval.pr_review.adjudication.engine import adjudicate_review
from eval.pr_review.adjudication.models import JudgeVote
from eval.pr_review.benchmark.schema import BenchmarkItem
from eval.pr_review.runner.output_schema import AgentReview


class Judge:
    def __init__(self, judge_id):
        self.judge_id = judge_id
        self.model_family = judge_id

    def decide(self, *, task, payload, position):
        if task.startswith("finding_match"):
            prediction_id = payload["prediction"]["id"]
            decision = "MATCH" if prediction_id in {"P1", "P3"} else "NO_MATCH"
            return JudgeVote(
                judge_id=self.judge_id,
                model_family=self.model_family,
                position=position,
                decision=decision,
                confidence=0.95,
                rationale="deterministic",
                severity="Blocker",
                category="correctness",
                location_correct=True,
            )
        if task.startswith("duplicate"):
            return JudgeVote(
                judge_id=self.judge_id,
                model_family=self.model_family,
                position=position,
                decision="DUPLICATE",
                confidence=0.9,
                rationale="same root cause",
                severity="Blocker",
            )
        if task.startswith("finding_validity"):
            return JudgeVote(
                judge_id=self.judge_id,
                model_family=self.model_family,
                position=position,
                decision="VALID_NEW",
                confidence=0.9,
                rationale="real independent issue",
                severity="Minor",
                category="maintainability",
            )
        raise AssertionError(task)


def item():
    return BenchmarkItem.model_validate({
        "benchmark_id": "pr-1",
        "repository": "org/repo",
        "pr_number": 1,
        "base_sha": "a" * 40,
        "head_sha": "b" * 40,
        "title": "change",
        "changed_files": ["a.py"],
        "expected_verdict": "REQUEST_CHANGES",
        "clean_status": "buggy",
        "gt_findings": [{
            "id": "G1",
            "summary": "cache key omits state",
            "description": "cache key omits request state",
            "severity": "Blocker",
            "category": "correctness",
            "merge_blocking": True,
            "location_required": True,
            "accepted_locations": [{"file": "a.py", "start_line": 10, "end_line": 12, "symbol": "key"}],
            "evidence": [{"file": "a.py", "start_line": 10, "end_line": 12}],
        }],
    })


def finding(fid, title, line, severity="Blocker", category="correctness"):
    return {
        "id": fid,
        "title": title,
        "description": title + " under request condition",
        "severity": severity,
        "category": category,
        "location": {"file": "a.py", "start_line": line, "end_line": line, "symbol": "key"},
        "evidence": [{"file": "a.py", "start_line": line, "end_line": line, "reason": "code"}],
    }


def test_engine_matches_globally_marks_duplicate_and_valid_new():
    review = AgentReview.model_validate({
        "verdict": "REQUEST_CHANGES",
        "summary": "three",
        "findings": [
            finding("P1", "cache key omits state", 10),
            finding("P2", "separate maintainability issue", 100, "Minor", "maintainability"),
            finding("P3", "cache key misses request state", 11),
        ],
    })
    rows = adjudicate_review(
        run_id="r",
        item=item(),
        review=review,
        judge_backends=[Judge("a"), Judge("b"), Judge("c")],
    )
    by_id = {row.prediction_id: row for row in rows}
    statuses = {row.final_status.value for row in rows}
    assert statuses == {"MATCHED_GT", "DUPLICATE", "VALID_NEW"}
    matched = [row for row in rows if row.final_status.value == "MATCHED_GT"]
    duplicate = [row for row in rows if row.final_status.value == "DUPLICATE"]
    assert matched[0].gt_id == "G1"
    assert matched[0].location_correct is True
    assert duplicate[0].duplicate_of == matched[0].prediction_id
    assert by_id["P2"].jury_severity.value == "Minor"
