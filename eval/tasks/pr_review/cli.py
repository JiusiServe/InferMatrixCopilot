"""Command-line interface for the versioned PR-review evaluator."""

from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
from typing import Any

from .adjudication.engine import adjudicate_review
from .adjudication.evidence import RepositoryEvidenceProvider
from .benchmark.builder import GitHubCollector, build_buggy_benchmark
from .benchmark.io import load_benchmark
from .metrics.aggregate import aggregate_results
from .metrics.campaign import score_campaign
from .metrics.models import PerPRMetrics, SummaryMetrics
from .reports import (
    render_compare,
    render_per_pr,
    render_summary,
    render_validity,
    summarize_replicates,
)
from .repository.cache import RepositoryCache
from .runner.evaluation_runner import run_benchmark
from .subjects.factory import load_and_build_agent_adapter
from .subjects.matrix import (
    adjudicate_experiment_matrix,
    run_experiment_matrix,
    score_experiment_matrix,
)
from .storage import RunBundle


def _load_object(spec: str) -> Any:
    if ":" not in spec:
        raise ValueError("plugin spec must use module:object syntax")
    module_name, object_name = spec.split(":", 1)
    value = getattr(importlib.import_module(module_name), object_name)
    return value() if isinstance(value, type) else value


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")



def command_benchmark_build(args: argparse.Namespace) -> int:
    judges = [_load_object(spec) for spec in args.judge]
    collector = GitHubCollector(token=args.github_token or os.environ.get("GITHUB_TOKEN", ""))
    path = build_buggy_benchmark(
        repository=args.repo,
        collector=collector,
        repository_cache=args.repository_cache,
        judges=judges,
        output_dir=args.output,
        pr_numbers=args.pr_number,
        candidate_limit=args.limit,
        benchmark_version=args.version,
    )
    print(path)
    return 0


def command_benchmark_validate(args: argparse.Namespace) -> int:
    manifest, items = load_benchmark(args.manifest, verify_hashes=not args.skip_hashes)
    buggy = sum(bool(item.gt_findings) for item in items)
    clean = len(items) - buggy
    print(f"valid {manifest.benchmark_version}: {len(items)} items ({buggy} buggy, {clean} clean)")
    return 0


def command_run(args: argparse.Namespace) -> int:
    if args.agent_config:
        config, adapter = load_and_build_agent_adapter(args.agent_config)
        model = args.model or getattr(adapter, "model", config.model)
        prompt_version = (
            args.prompt_version
            if args.prompt_version != "unknown"
            else config.prompt_version
        )
        model_parameters = config.model_parameters
    else:
        adapter = _load_object(args.adapter)
        model = args.model
        prompt_version = args.prompt_version
        model_parameters = {}
    output = run_benchmark(
        manifest_path=args.manifest,
        repository_cache=args.repository_cache,
        output_dir=args.output,
        adapter=adapter,
        model=model,
        model_parameters=model_parameters,
        prompt_version=prompt_version,
        benchmark_filter=set(args.benchmark_id) if args.benchmark_id else None,
    )
    print(output)
    return 0


def command_run_matrix(args: argparse.Namespace) -> int:
    output = run_experiment_matrix(
        matrix_path=args.matrix,
        manifest_path=args.manifest,
        repository_cache=args.repository_cache,
        output_root=args.output,
        benchmark_filter=set(args.benchmark_id) if args.benchmark_id else None,
    )
    print(output)
    return 0


def command_adjudicate_matrix(args: argparse.Namespace) -> int:
    output = adjudicate_experiment_matrix(
        matrix_run_root=args.matrix_run_root,
        manifest_path=args.manifest,
        repository_cache=args.repository_cache,
        judge_specs=args.judge,
        round2_judge_specs=args.round2_judge,
    )
    print(output)
    return 0


def command_score_matrix(args: argparse.Namespace) -> int:
    output = score_experiment_matrix(
        matrix_run_root=args.matrix_run_root,
        manifest_path=args.manifest,
        output_dir=args.output,
    )
    print(output)
    return 0


def command_repository_import(args: argparse.Namespace) -> int:
    cache = RepositoryCache(args.repository_cache)
    output = cache.import_local(args.repo, args.source)
    print(output)
    return 0


def command_adjudicate(args: argparse.Namespace) -> int:
    _, items = load_benchmark(args.manifest)
    bundle = RunBundle(args.run_dir)
    backends = [_load_object(spec) for spec in args.judge]
    round2 = [_load_object(spec) for spec in args.round2_judge] if args.round2_judge else None
    repository_cache = RepositoryCache(args.repository_cache)
    for item in items:
        prediction_path = bundle.predictions / f"{item.benchmark_id}.json"
        metadata_path = bundle.metadata / f"{item.benchmark_id}.json"
        if not prediction_path.exists() or not metadata_path.exists():
            continue
        result = bundle.load_result(item)
        if result.review is None or result.run_metadata is None or result.run_metadata.output_contract_failure:
            continue
        repository = repository_cache.require(item.repository)
        rows = adjudicate_review(
            run_id=result.run_metadata.run_id,
            item=item,
            review=result.review,
            judge_backends=backends,
            round2_backends=round2,
            evidence_provider=RepositoryEvidenceProvider(repository, item),
        )
        bundle.write_adjudications(item.benchmark_id, rows)
    return 0


def command_score(args: argparse.Namespace) -> int:
    manifest, items = load_benchmark(args.manifest)
    bundle = RunBundle(args.run_dir)
    inputs = [bundle.load_result(item) for item in items]
    per_pr, summary = aggregate_results(
        inputs,
        benchmark_version=manifest.benchmark_version,
        rubric_version=manifest.rubric_version,
        judge_version=manifest.judge_version,
    )
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    _write_json(output / "per_pr.json", [row.model_dump(mode="json", exclude_none=True) for row in per_pr])
    _write_json(output / "summary.json", summary.model_dump(mode="json", exclude_none=True))
    (output / "summary.md").write_text(render_summary(summary), encoding="utf-8")
    (output / "per_pr.md").write_text(render_per_pr(per_pr), encoding="utf-8")
    (output / "validity.md").write_text(render_validity(summary), encoding="utf-8")
    print(output)
    return 0


def command_report(args: argparse.Namespace) -> int:
    summary = SummaryMetrics.model_validate_json(Path(args.summary).read_text(encoding="utf-8"))
    text = render_summary(summary)
    if args.per_pr:
        rows = [PerPRMetrics.model_validate(value) for value in json.loads(Path(args.per_pr).read_text(encoding="utf-8"))]
        text += "\n" + render_per_pr(rows)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    return 0


def command_compare(args: argparse.Namespace) -> int:
    output = Path(args.output)
    if args.baseline_run or args.candidate_run:
        if not (args.manifest and args.baseline_run and args.candidate_run):
            raise ValueError("run comparison requires --manifest, --baseline-run and --candidate-run")
        manifest, items = load_benchmark(args.manifest)
        arms = {
            "baseline": [RunBundle(args.baseline_run).load_result(item) for item in items],
            "candidate": [RunBundle(args.candidate_run).load_result(item) for item in items],
        }
        scored, invalidated = score_campaign(manifest, arms)
        output.mkdir(parents=True, exist_ok=True)
        summaries: dict[str, SummaryMetrics] = {}
        for name, (per_pr, summary) in scored.items():
            summaries[name] = summary
            _write_json(
                output / f"{name}_per_pr.json",
                [row.model_dump(mode="json", exclude_none=True) for row in per_pr],
            )
            _write_json(output / f"{name}_summary.json", summary.model_dump(mode="json", exclude_none=True))
            (output / f"{name}_summary.md").write_text(render_summary(summary), encoding="utf-8")
        _write_json(output / "invalidated_benchmark_ids.json", sorted(invalidated))
        (output / "compare.md").write_text(
            render_compare(summaries["baseline"], summaries["candidate"]), encoding="utf-8"
        )
        print(output)
        return 0

    if not (args.baseline_summary and args.candidate_summary):
        raise ValueError("summary comparison requires --baseline-summary and --candidate-summary")
    baseline = SummaryMetrics.model_validate_json(Path(args.baseline_summary).read_text(encoding="utf-8"))
    candidate = SummaryMetrics.model_validate_json(Path(args.candidate_summary).read_text(encoding="utf-8"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_compare(baseline, candidate), encoding="utf-8")
    return 0



def command_replicates(args: argparse.Namespace) -> int:
    summaries = [SummaryMetrics.model_validate_json(Path(path).read_text(encoding="utf-8")) for path in args.summary]
    per_pr_runs = None
    if args.per_pr:
        if len(args.per_pr) != len(args.summary):
            raise ValueError("--per-pr must be repeated once for each --summary")
        per_pr_runs = [
            [PerPRMetrics.model_validate(value) for value in json.loads(Path(path).read_text(encoding="utf-8"))]
            for path in args.per_pr
        ]
    payload = summarize_replicates(summaries, per_pr_runs)
    _write_json(Path(args.output), payload)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m eval.tasks.pr_review")
    commands = parser.add_subparsers(dest="command", required=True)

    benchmark = commands.add_parser("benchmark")
    benchmark_commands = benchmark.add_subparsers(dest="benchmark_command", required=True)
    build = benchmark_commands.add_parser("build")
    build.add_argument("--repo", required=True)
    build.add_argument("--repository-cache", required=True)
    build.add_argument("--judge", action="append", required=True, help="module:object JudgeBackend; repeat for a jury")
    build.add_argument("--output", required=True)
    build.add_argument("--pr-number", type=int, action="append")
    build.add_argument("--limit", type=int, default=30)
    build.add_argument("--version", default="pr-review-benchmark-v0.1.0")
    build.add_argument("--github-token", default="")
    build.set_defaults(func=command_benchmark_build)

    validate = benchmark_commands.add_parser("validate")
    validate.add_argument("--manifest", required=True)
    validate.add_argument("--skip-hashes", action="store_true")
    validate.set_defaults(func=command_benchmark_validate)

    repository = commands.add_parser("repository")
    repository_commands = repository.add_subparsers(
        dest="repository_command", required=True
    )
    repository_import = repository_commands.add_parser("import-local")
    repository_import.add_argument("--repo", required=True)
    repository_import.add_argument("--source", required=True)
    repository_import.add_argument("--repository-cache", required=True)
    repository_import.set_defaults(func=command_repository_import)

    run = commands.add_parser("run")
    run.add_argument("--manifest", required=True)
    run.add_argument("--repository-cache", required=True)
    adapter_group = run.add_mutually_exclusive_group(required=True)
    adapter_group.add_argument(
        "--adapter", help="module:object implementing AgentAdapter"
    )
    adapter_group.add_argument(
        "--agent-config", help="versioned evaluated-agent YAML configuration"
    )
    run.add_argument("--output", required=True)
    run.add_argument("--model", default="")
    run.add_argument("--prompt-version", default="unknown")
    run.add_argument("--benchmark-id", action="append")
    run.set_defaults(func=command_run)

    matrix = commands.add_parser("run-matrix")
    matrix.add_argument("--matrix", required=True)
    matrix.add_argument("--manifest", required=True)
    matrix.add_argument("--repository-cache", required=True)
    matrix.add_argument("--output", required=True)
    matrix.add_argument("--benchmark-id", action="append")
    matrix.set_defaults(func=command_run_matrix)

    adjudicate_matrix = commands.add_parser("adjudicate-matrix")
    adjudicate_matrix.add_argument("--matrix-run-root", required=True)
    adjudicate_matrix.add_argument("--manifest", required=True)
    adjudicate_matrix.add_argument("--repository-cache", required=True)
    adjudicate_matrix.add_argument("--judge", action="append", required=True)
    adjudicate_matrix.add_argument("--round2-judge", action="append")
    adjudicate_matrix.set_defaults(func=command_adjudicate_matrix)

    score_matrix = commands.add_parser("score-matrix")
    score_matrix.add_argument("--matrix-run-root", required=True)
    score_matrix.add_argument("--manifest", required=True)
    score_matrix.add_argument("--output")
    score_matrix.set_defaults(func=command_score_matrix)

    adjudicate = commands.add_parser("adjudicate")
    adjudicate.add_argument("--manifest", required=True)
    adjudicate.add_argument("--run-dir", required=True)
    adjudicate.add_argument("--repository-cache", required=True)
    adjudicate.add_argument("--judge", action="append", required=True, help="module:object JudgeBackend; repeat for a jury")
    adjudicate.add_argument("--round2-judge", action="append")
    adjudicate.set_defaults(func=command_adjudicate)

    score = commands.add_parser("score")
    score.add_argument("--manifest", required=True)
    score.add_argument("--run-dir", required=True)
    score.add_argument("--output", required=True)
    score.set_defaults(func=command_score)

    report = commands.add_parser("report")
    report.add_argument("--summary", required=True)
    report.add_argument("--per-pr")
    report.add_argument("--output", required=True)
    report.set_defaults(func=command_report)

    compare = commands.add_parser("compare")
    compare.add_argument("--manifest")
    compare.add_argument("--baseline-run")
    compare.add_argument("--candidate-run")
    compare.add_argument("--baseline-summary")
    compare.add_argument("--candidate-summary")
    compare.add_argument("--output", required=True)
    compare.set_defaults(func=command_compare)

    replicates = commands.add_parser("replicates")
    replicates.add_argument("--summary", action="append", required=True)
    replicates.add_argument("--per-pr", action="append")
    replicates.add_argument("--output", required=True)
    replicates.set_defaults(func=command_replicates)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))
