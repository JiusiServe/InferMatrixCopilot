#!/usr/bin/env python3
"""Run the Copilot / Copilot+Skill / Skill-only PR-review experiment.

Candidate generation can run without judge plugins. Supplying --judge completes
adjudication and globally-consistent scoring for all three arms.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from eval.tasks.pr_review.repository.cache import RepositoryCache
from eval.tasks.pr_review.subjects.matrix import (
    adjudicate_experiment_matrix,
    run_experiment_matrix,
    score_experiment_matrix,
)

DEFAULT_MANIFEST = (
    PROJECT_ROOT
    / "eval/data/pr_review/benchmarks/pr-review-pilot-v0.1.0-dev/manifest.yaml"
)
DEFAULT_SMOKE_MATRIX = (
    PROJECT_ROOT
    / "eval/configs/pr_review/experiments/three-arms-smoke.yaml"
)
DEFAULT_FORMAL_MATRIX = (
    PROJECT_ROOT
    / "eval/configs/pr_review/experiments/three-arms-formal.yaml"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the three-arm offline PR-review benchmark experiment."
    )
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--matrix", help="Override the experiment matrix YAML")
    parser.add_argument(
        "--formal",
        action="store_true",
        help="Use the three-repetition formal matrix instead of the one-run smoke matrix",
    )
    parser.add_argument("--repository-cache", required=True)
    parser.add_argument(
        "--repository-source",
        help=(
            "Optional local vllm-omni checkout containing all frozen benchmark SHAs. "
            "It is imported into --repository-cache before the run."
        ),
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--benchmark-id", action="append")
    parser.add_argument(
        "--judge",
        action="append",
        help="module:object JudgeBackend; repeat to complete adjudication and scoring",
    )
    parser.add_argument("--round2-judge", action="append")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest = Path(args.manifest).expanduser().resolve()
    matrix = Path(
        args.matrix
        or (DEFAULT_FORMAL_MATRIX if args.formal else DEFAULT_SMOKE_MATRIX)
    ).expanduser().resolve()
    cache = RepositoryCache(args.repository_cache)
    if args.repository_source:
        cache.import_local("vllm-project/vllm-omni", args.repository_source)

    matrix_root = run_experiment_matrix(
        matrix_path=matrix,
        manifest_path=manifest,
        repository_cache=args.repository_cache,
        output_root=args.output,
        benchmark_filter=set(args.benchmark_id) if args.benchmark_id else None,
    )

    result: dict[str, object] = {
        "matrix_root": str(matrix_root),
        "candidate_generation_complete": True,
        "adjudication_complete": False,
        "reports": None,
    }
    if args.judge:
        adjudicate_experiment_matrix(
            matrix_run_root=matrix_root,
            manifest_path=manifest,
            repository_cache=args.repository_cache,
            judge_specs=args.judge,
            round2_judge_specs=args.round2_judge,
        )
        reports = score_experiment_matrix(
            matrix_run_root=matrix_root,
            manifest_path=manifest,
        )
        result["adjudication_complete"] = True
        result["reports"] = str(reports)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not args.judge:
        print(
            "\nCandidate reviews were generated. Full precision/recall metrics require "
            "independent JudgeBackend plugins; rerun with repeated --judge module:object."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
