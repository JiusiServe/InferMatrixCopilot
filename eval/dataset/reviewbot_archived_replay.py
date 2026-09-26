#!/usr/bin/env python3
"""Replay one frozen, now-merged PR through an installed ReviewBot release.

This evaluation-only adapter supplies the historical open snapshot and the
frozen file list to the normal Direct pipeline. The GitHub transport is
read-only, and the pipeline is always called with post=False. Production PR
eligibility and publication code are neither imported from source nor changed.
"""
from __future__ import annotations

import argparse
import os
import re
from dataclasses import replace
from pathlib import Path

SHA = re.compile(r"[0-9a-f]{40}\Z")
FILE_HEADER = re.compile(r"diff --git a/(.+) b/(.+)\Z")


def frozen_files(diff: str) -> list[dict[str, object]]:
    """Project the checked-in Git patch into ReviewBot's ChangedFile fields."""
    files: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    patch: list[str] = []
    in_hunk = False

    def finish() -> None:
        if current is not None:
            current["patch"] = "\n".join(patch) + "\n" if patch else None
            files.append(current)

    for line in diff.splitlines():
        if line.startswith("diff --git "):
            finish()
            match = FILE_HEADER.fullmatch(line)
            if match is None or match.group(1) != match.group(2):
                raise ValueError(f"unsupported frozen file header: {line}")
            current = {
                "path": match.group(2), "status": "modified",
                "additions": 0, "deletions": 0,
            }
            patch = []
            in_hunk = False
        elif current is None:
            raise ValueError("frozen diff has content before its first file")
        elif line.startswith("new file mode "):
            current["status"] = "added"
        elif line.startswith("deleted file mode "):
            current["status"] = "removed"
        elif line.startswith("rename from ") or line.startswith("copy from "):
            raise ValueError("frozen diff rename/copy needs explicit projection")
        elif line.startswith("Binary files ") or line == "GIT binary patch":
            raise ValueError("binary frozen diffs need explicit projection")
        elif line.startswith("@@ "):
            in_hunk = True
            patch.append(line)
        elif in_hunk:
            patch.append(line)
            if line.startswith("+"):
                current["additions"] = int(current["additions"]) + 1
            elif line.startswith("-"):
                current["deletions"] = int(current["deletions"]) + 1
    finish()
    if not files:
        raise ValueError("frozen diff contains no files")
    paths = [str(item["path"]) for item in files]
    if len(paths) != len(set(paths)):
        raise ValueError("frozen diff repeats a file")
    return files


def historical_pull(pull, *, pr: int, head: str, base: str):
    """Verify the live archived identity before presenting the frozen view."""
    if pull.number != pr or pull.head_sha != head:
        raise ValueError(f"pr{pr} no longer has the pinned head")
    if pull.state != "closed" or not pull.merged_at:
        raise ValueError(f"pr{pr} is not a merged archived PR")
    return replace(
        pull, state="open", base_sha=base, merged_at="", merge_commit_sha="",
    )


def shadow_candidate(body: str, inline_comments: list[dict]) -> str:
    """Include the inline payload that a COMMENT review would publish.

    The normal review-body artifact intentionally omits placed findings. A
    judge reading that artifact alone would score a review with inline
    findings as though it made none.
    """
    if not inline_comments:
        return body
    if "No actionable findings." in body:
        raise ValueError("review body contradicts its inline findings")
    parts = [body.rstrip(), "", "### Inline findings", ""]
    for comment in inline_comments:
        parts.extend([
            f"#### {comment['path']}:{comment['line']} ({comment['side']})",
            "",
            str(comment["body"]).strip(),
            "",
        ])
    return "\n".join(parts).rstrip() + "\n"


def write_shadow_artifact(outcome, inline_comments: list[dict] | None, state_dir: Path) -> None:
    """Complete only this evaluation's shadow artifact with placed comments."""
    if outcome.status != "shadow":
        return
    metrics = outcome.metrics or {}
    if inline_comments is None or metrics.get("inline_placed") != len(inline_comments):
        raise RuntimeError("shadow inline payload differs from publication metrics")
    if "See inline comments below." in outcome.body and not inline_comments:
        raise RuntimeError("review body references missing inline findings")
    if outcome.artifact_path is None:
        raise RuntimeError("shadow review has no artifact")
    artifact = Path(outcome.artifact_path).resolve(strict=True)
    if artifact.parent != (state_dir / "artifacts").resolve():
        raise RuntimeError("shadow artifact escaped the evaluation state")
    artifact.write_text(
        shadow_candidate(artifact.read_text(encoding="utf-8"), inline_comments),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--diff", type=Path, required=True)
    args = parser.parse_args()
    if os.environ.get("REVIEWBOT_EVAL_ARCHIVED_REPLAY") != "1":
        parser.error("archived replay requires REVIEWBOT_EVAL_ARCHIVED_REPLAY=1")
    if os.environ.get("POST_MODE") != "shadow":
        parser.error("archived replay requires POST_MODE=shadow")
    if os.environ.get("REVIEW_CONTEXT_MODE") != "no_discussion":
        parser.error("archived replay requires REVIEW_CONTEXT_MODE=no_discussion")
    if args.pr <= 0 or not SHA.fullmatch(args.expected_head) or not SHA.fullmatch(args.base):
        parser.error("invalid PR number or pinned commit SHA")
    if args.diff.name != f"pr{args.pr}.diff" or not args.diff.is_file():
        parser.error("diff must be the frozen patch for the selected PR")

    # Import only the paired wheel installed in the runner's private venv.
    from omni_reviewbot.cli import build_runtime
    from omni_reviewbot.config import Settings
    from omni_reviewbot.models import ChangedFile
    from omni_reviewbot import publication

    settings = Settings.from_env()
    if settings.post or settings.review_context_mode != "no_discussion":
        parser.error("installed ReviewBot settings violate shadow replay")
    diff_files = [
        ChangedFile(**fields)
        for fields in frozen_files(args.diff.read_text(encoding="utf-8"))
    ]
    runtime = build_runtime(settings, recover_running=False)
    github = runtime.github
    request = github._request

    def read_only(method, path, payload=None):
        if method != "GET" or payload is not None:
            raise RuntimeError("archived evaluation rejects GitHub writes")
        return request(method, path, payload)

    github._request = read_only
    original_get_pull = github.get_pull

    def get_pull(number):
        if number != args.pr:
            raise RuntimeError("archived evaluation rejects another PR")
        return historical_pull(
            original_get_pull(number),
            pr=args.pr, head=args.expected_head, base=args.base,
        )

    def list_files(number):
        if number != args.pr:
            raise RuntimeError("archived evaluation rejects another PR")
        return list(diff_files)

    github.get_pull = get_pull
    github.list_files = list_files
    original_inline = publication.inline_review_comments
    captured: list[dict] | None = None

    def capture_inline(*call_args, **call_kwargs):
        nonlocal captured
        comments, indexes = original_inline(*call_args, **call_kwargs)
        captured = list(comments)
        return comments, indexes

    publication.inline_review_comments = capture_inline
    try:
        outcome = runtime.pipeline.run(
            pr_number=args.pr, expected_head=args.expected_head, post=False,
        )
    finally:
        publication.inline_review_comments = original_inline
    write_shadow_artifact(outcome, captured, settings.state_dir)
    print(outcome.body)
    print(f"status: {outcome.status}")
    metrics = outcome.metrics or {}
    if "review_context_mode" in metrics:
        print(
            f"review_context: {metrics['review_context_mode']} "
            f"({metrics['review_context_count']} threads)"
        )
    if "changed_files" in metrics:
        print(f"changed_files: {metrics['changed_files']}")
    if outcome.artifact_path:
        print(f"artifact: {outcome.artifact_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
