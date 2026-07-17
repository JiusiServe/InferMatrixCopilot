from pathlib import Path

from eval.tasks.pr_review.benchmark.io import load_benchmark, sha256_file


ROOT = Path(__file__).resolve().parents[4]
MANIFEST = (
    ROOT
    / "eval"
    / "data"
    / "pr_review"
    / "benchmarks"
    / "pr-review-pilot-v0.1.0-dev"
    / "manifest.yaml"
)


def test_frozen_pilot_benchmark_is_loadable_and_balanced():
    manifest, items = load_benchmark(MANIFEST)

    assert manifest.benchmark_version == "pr-review-pilot-v0.1.0-dev"
    assert len(items) == 5
    assert sum(item.clean_status.value == "buggy" for item in items) == 3
    assert sum(item.clean_status.value == "auto_certified_clean" for item in items) == 2
    assert any(finding.merge_blocking for item in items for finding in item.gt_findings)
    assert {finding.category.value for item in items for finding in item.gt_findings} >= {
        "compatibility_api",
        "correctness",
        "test",
    }


def test_frozen_pilot_uses_full_shas_and_hashes_every_item():
    manifest, items = load_benchmark(MANIFEST)

    assert all(len(item.base_sha) == 40 and len(item.head_sha) == 40 for item in items)
    assert all(entry.sha256 for entry in manifest.entries)
    for entry in manifest.entries:
        assert sha256_file(MANIFEST.parent / entry.item) == entry.sha256


def test_clean_items_have_private_certification_and_no_gt():
    _, items = load_benchmark(MANIFEST)
    private = MANIFEST.parent / "private" / "jury" / "clean-certification"

    clean = [item for item in items if item.clean_status.value == "auto_certified_clean"]
    assert len(clean) == 2
    for item in clean:
        assert item.expected_verdict.value == "APPROVE"
        assert item.gt_findings == []
        assert (private / f"pr-{item.pr_number}.yaml").is_file()


def test_buggy_items_have_gt_jury_records():
    _, items = load_benchmark(MANIFEST)
    private = MANIFEST.parent / "private" / "jury" / "gt"

    buggy = [item for item in items if item.clean_status.value == "buggy"]
    assert len(buggy) == 3
    for item in buggy:
        assert item.gt_findings
        assert (private / f"pr-{item.pr_number}.yaml").is_file()
