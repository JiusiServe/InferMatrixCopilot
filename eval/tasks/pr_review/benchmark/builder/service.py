"""Automatic construction of high-confidence buggy benchmark candidates."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from ...adjudication.jury import JudgeBackend
from ...repository.cache import RepositoryCache
from ...repository.snapshot import changed_files_between, merge_base, read_file_at, verify_commit
from ..schema import BenchmarkItem, BenchmarkManifest, BenchmarkManifestEntry, CleanStatus, CommitInfo, Verdict
from ..versioning import freeze_manifest, write_item
from .deduplicator import cluster_candidates
from .github_collector import GitHubCollector
from .gt_jury import build_gt_from_cluster
from .review_candidate_extractor import extract_review_candidates
from .snapshot_selector import select_review_preceding_head


def _snippet(text: str, start_line: int, end_line: int, context: int = 40) -> dict:
    lines = text.splitlines()
    start = max(1, start_line - context)
    end = min(len(lines), end_line + context)
    return {"start_line": start, "end_line": end, "text": "\n".join(lines[start - 1:end])}


def build_buggy_benchmark(
    *,
    repository: str,
    collector: GitHubCollector,
    repository_cache: str | Path,
    judges: list[JudgeBackend],
    output_dir: str | Path,
    pr_numbers: list[int] | None = None,
    candidate_limit: int = 30,
    benchmark_version: str = "pr-review-benchmark-v0.1.0",
    rubric_version: str = "pr-review-rubric-v0.1",
    judge_version: str = "pr-review-jury-v0.1",
) -> Path:
    """Build/freeze buggy items; clean certification is a separate explicit stage."""
    output = Path(output_dir)
    items_dir = output / "items"
    private_dir = output / "private" / "github"
    items_dir.mkdir(parents=True, exist_ok=True)
    private_dir.mkdir(parents=True, exist_ok=True)
    cache = RepositoryCache(repository_cache)
    repo = cache.require(repository)

    if pr_numbers is None:
        pr_numbers = [int(pr["number"]) for pr in collector.list_closed_pull_requests(repository)[:candidate_limit]]

    entries: list[BenchmarkManifestEntry] = []
    for pr_number in pr_numbers:
        raw = collector.collect_pr(repository, pr_number)
        (private_dir / f"pr-{pr_number}.json").write_text(
            json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        try:
            head_sha = select_review_preceding_head(raw)
        except ValueError:
            continue
        current_base_sha = str(raw["pr"]["base"]["sha"])
        verify_commit(repo, current_base_sha)
        verify_commit(repo, head_sha)
        base_sha = merge_base(repo, current_base_sha, head_sha)
        candidates = extract_review_candidates(raw)
        if not candidates:
            continue
        gt_findings = []
        for index, cluster in enumerate(cluster_candidates(candidates), start=1):
            primary = cluster.candidates[0]
            try:
                head_file = read_file_at(repo, head_sha, primary.path)
            except Exception:
                continue
            final_sha = str(raw["pr"]["head"]["sha"])
            final_context = None
            if final_sha != head_sha:
                try:
                    verify_commit(repo, final_sha)
                    final_context = _snippet(read_file_at(repo, final_sha, primary.path), primary.start_line, primary.end_line)
                except Exception:
                    final_context = None
            evidence = {
                "head_sha": head_sha,
                "pre_review_context": _snippet(head_file, primary.start_line, primary.end_line),
                "historical_diff_hunks": [candidate.diff_hunk for candidate in cluster.candidates],
                "post_review_context": final_context,
                "pr_title": raw["pr"].get("title", ""),
                "pr_body": raw["pr"].get("body") or "",
            }
            finding = build_gt_from_cluster(
                cluster,
                evidence_bundle=evidence,
                judges=judges,
                gt_id=f"GT-{index:03d}",
            )
            if finding is not None:
                gt_findings.append(finding)
        if not gt_findings:
            continue
        expected = Verdict.REQUEST_CHANGES if any(f.merge_blocking for f in gt_findings) else Verdict.APPROVE
        commits = []
        for commit in raw.get("commits", []):
            commits.append(CommitInfo(
                sha=str(commit.get("sha", "")),
                message=str((commit.get("commit") or {}).get("message") or ""),
            ))
            if commit.get("sha") == head_sha:
                break
        item = BenchmarkItem(
            benchmark_id=f"pr-review-{repository.replace('/', '-')}-{pr_number}",
            repository=repository,
            pr_number=pr_number,
            base_branch=str(raw["pr"]["base"].get("ref") or "main"),
            base_sha=base_sha,
            head_sha=head_sha,
            title=str(raw["pr"].get("title") or ""),
            body=str(raw["pr"].get("body") or ""),
            commits=commits,
            changed_files=changed_files_between(repo, base_sha, head_sha),
            expected_verdict=expected,
            clean_status=CleanStatus.BUGGY,
            gt_findings=gt_findings,
        )
        item_relative = f"items/{item.benchmark_id}.yaml"
        write_item(item, output / item_relative)
        entries.append(BenchmarkManifestEntry(benchmark_id=item.benchmark_id, item=item_relative))

    manifest = BenchmarkManifest(
        benchmark_version=benchmark_version,
        rubric_version=rubric_version,
        judge_version=judge_version,
        created_at=datetime.now(timezone.utc).isoformat(),
        entries=entries,
    )
    manifest = freeze_manifest(manifest, output)
    manifest_path = output / "manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(manifest.model_dump(mode="json"), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return manifest_path
