import subprocess

from eval.pr_review.adjudication.evidence import RepositoryEvidenceProvider
from eval.pr_review.benchmark.schema import BenchmarkItem
from eval.pr_review.runner.output_schema import AgentFinding


def _git(repo, *args):
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def test_round2_evidence_is_pinned_to_base_and_head(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "a@b.c"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "a"], cwd=repo, check=True)
    (repo / "cache.py").write_text("def key(x):\n    return x\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
    base = _git(repo, "rev-parse", "HEAD")

    (repo / "cache.py").write_text("def key(x):\n    return 0  # buggy head\n")
    (repo / "test_cache.py").write_text("from cache import key\n\ndef test_key():\n    assert key(1) == 1\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "head"], cwd=repo, check=True)
    head = _git(repo, "rev-parse", "HEAD")

    (repo / "cache.py").write_text("def key(x):\n    return x  # review-after fix\n")
    subprocess.run(["git", "commit", "-qam", "after review"], cwd=repo, check=True)

    item = BenchmarkItem.model_validate({
        "benchmark_id": "pr-1",
        "repository": "org/repo",
        "pr_number": 1,
        "base_sha": base,
        "head_sha": head,
        "title": "change key",
        "changed_files": ["cache.py", "test_cache.py"],
        "expected_verdict": "REQUEST_CHANGES",
        "clean_status": "buggy",
        "gt_findings": [{
            "id": "G1",
            "summary": "key is constant",
            "description": "key ignores x",
            "severity": "Blocker",
            "category": "correctness",
            "merge_blocking": True,
            "accepted_locations": [{"file": "cache.py", "start_line": 1, "end_line": 2, "symbol": "key"}],
            "evidence": [{"file": "cache.py", "start_line": 2, "end_line": 2}],
        }],
    })
    prediction = AgentFinding.model_validate({
        "id": "P1",
        "title": "constant cache key",
        "description": "all x values collide",
        "severity": "Blocker",
        "category": "correctness",
        "location": {"file": "cache.py", "start_line": 2, "end_line": 2, "symbol": "key"},
        "evidence": [{"file": "cache.py", "start_line": 2, "end_line": 2, "reason": "constant"}],
    })

    package = RepositoryEvidenceProvider(repo, item).for_match(prediction, item.gt_findings[0])
    rendered = str(package)
    assert "buggy head" in rendered
    assert "review-after fix" not in rendered
    assert "test_cache.py" in rendered
    assert "key" in package["symbol_references"]
