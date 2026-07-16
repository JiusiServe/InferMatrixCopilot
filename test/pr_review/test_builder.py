from eval.pr_review.benchmark.builder.deduplicator import cluster_candidates
from eval.pr_review.benchmark.builder.review_candidate_extractor import ReviewCandidate
from eval.pr_review.benchmark.builder.snapshot_selector import select_review_preceding_head


def test_snapshot_is_last_commit_before_first_substantive_review():
    raw = {
        "reviews": [{"state": "CHANGES_REQUESTED", "submitted_at": "2026-01-03T00:00:00Z", "body": "bug"}],
        "review_comments": [],
        "commits": [
            {"sha": "a" * 40, "commit": {"author": {"date": "2026-01-01T00:00:00Z"}}},
            {"sha": "b" * 40, "commit": {"author": {"date": "2026-01-02T00:00:00Z"}}},
            {"sha": "c" * 40, "commit": {"author": {"date": "2026-01-04T00:00:00Z"}}},
        ],
    }
    assert select_review_preceding_head(raw) == "b" * 40


def test_candidate_dedup_requires_same_file_and_similar_root_cause():
    base = dict(
        source_id="1",
        body="cache key omits request state and returns wrong result",
        path="a.py",
        start_line=10,
        end_line=12,
        created_at="x",
        reviewer="r",
        review_state="CHANGES_REQUESTED",
        diff_hunk="",
        original_commit_id=None,
    )
    a = ReviewCandidate(**base)
    b = ReviewCandidate(**{**base, "source_id": "2", "body": "cache key omits request state, producing a wrong result", "start_line": 14})
    c = ReviewCandidate(**{**base, "source_id": "3", "path": "b.py"})
    clusters = cluster_candidates([a, b, c])
    assert sorted(len(cluster.candidates) for cluster in clusters) == [1, 2]

from eval.pr_review.benchmark.builder.clean_certifier import certify_clean_pr
from eval.pr_review.runner.output_schema import AgentReview


def test_clean_certification_rejects_request_changes_even_without_findings():
    review = AgentReview.model_validate({
        "verdict": "REQUEST_CHANGES",
        "summary": "block",
        "findings": [],
    })
    result = certify_clean_pr([review, review, review], [[], [], []], certification_votes=5)
    assert result.certified is False
    assert any("REQUEST_CHANGES" in reason for reason in result.reasons)
