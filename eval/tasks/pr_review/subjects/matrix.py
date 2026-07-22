"""Run and score reproducible matrices of evaluated PR-review subjects."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from ..adjudication.engine import adjudicate_review
from ..adjudication.evidence import RepositoryEvidenceProvider
from ..benchmark.io import load_benchmark
from ..metrics.campaign import score_campaign
from ..metrics.models import SummaryMetrics
from ..reports import render_per_pr, render_summary, render_validity
from ..repository.cache import RepositoryCache
from ..runner.evaluation_runner import run_benchmark
from ..storage import RunBundle
from .config import load_agent_config, load_experiment_matrix, resolve_relative
from .factory import build_agent_adapter


def _load_object(spec: str) -> Any:
    if ":" not in spec:
        raise ValueError("plugin spec must use module:object syntax")
    module_name, object_name = spec.split(":", 1)
    value = getattr(importlib.import_module(module_name), object_name)
    return value() if isinstance(value, type) else value


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _matrix_payload(root: str | Path) -> dict[str, Any]:
    path = Path(root).resolve() / "matrix.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("runs"), list):
        raise ValueError(f"invalid matrix run index: {path}")
    return value


def run_experiment_matrix(
    *,
    matrix_path: str | Path,
    manifest_path: str | Path,
    repository_cache: str | Path,
    output_root: str | Path,
    benchmark_filter: set[str] | None = None,
) -> Path:
    """Generate candidate reviews for every configured arm and repetition."""

    resolved_matrix, matrix = load_experiment_matrix(matrix_path)
    root = Path(output_root).resolve() / matrix.name
    root.mkdir(parents=True, exist_ok=True)
    runs: list[dict[str, Any]] = []
    for agent_ref in matrix.agents:
        agent_path = resolve_relative(agent_ref, config_path=resolved_matrix)
        config_path, config = load_agent_config(agent_path)
        for replicate in range(1, matrix.repetitions + 1):
            adapter = build_agent_adapter(config, config_path=config_path)
            llm = getattr(adapter, "llm", None)
            if llm is not None and not llm.available:
                raise RuntimeError(
                    "LLM is not configured. Set ANTHROPIC_API_KEY and, when "
                    "needed, ANTHROPIC_BASE_URL before running the matrix."
                )
            run_dir = root / config.name / f"run-{replicate:02d}"
            output = run_benchmark(
                manifest_path=manifest_path,
                repository_cache=repository_cache,
                output_dir=run_dir,
                adapter=adapter,
                model=getattr(adapter, "model", config.model),
                model_parameters=config.model_parameters,
                prompt_version=config.prompt_version,
                benchmark_filter=benchmark_filter,
            )
            runs.append(
                {
                    "agent": config.name,
                    "kind": config.kind,
                    "version": adapter.version,
                    "model": getattr(adapter, "model", config.model),
                    "replicate": replicate,
                    "config": str(config_path),
                    "run_dir": str(output),
                }
            )
    _write_json(
        root / "matrix.json",
        {
            "schema_version": matrix.schema_version,
            "name": matrix.name,
            "matrix_config": str(resolved_matrix),
            "manifest": str(Path(manifest_path).resolve()),
            "repository_cache": str(Path(repository_cache).resolve()),
            "runs": runs,
        },
    )
    return root


def adjudicate_experiment_matrix(
    *,
    matrix_run_root: str | Path,
    manifest_path: str | Path,
    repository_cache: str | Path,
    judge_specs: list[str],
    round2_judge_specs: list[str] | None = None,
) -> Path:
    """Adjudicate every candidate run with the same independent judge jury."""

    if not judge_specs:
        raise ValueError("at least one --judge module:object is required")
    matrix_root = Path(matrix_run_root).resolve()
    payload = _matrix_payload(matrix_root)
    _, items = load_benchmark(manifest_path)
    backends = [_load_object(spec) for spec in judge_specs]
    round2 = (
        [_load_object(spec) for spec in round2_judge_specs]
        if round2_judge_specs
        else None
    )
    cache = RepositoryCache(repository_cache)

    for run in payload["runs"]:
        bundle = RunBundle(run["run_dir"])
        for item in items:
            prediction_path = bundle.predictions / f"{item.benchmark_id}.json"
            metadata_path = bundle.metadata / f"{item.benchmark_id}.json"
            if not prediction_path.exists() or not metadata_path.exists():
                continue
            result = bundle.load_result(item)
            if (
                result.review is None
                or result.run_metadata is None
                or result.run_metadata.output_contract_failure
                or result.run_metadata.agent_failure
            ):
                continue
            repository = cache.require(item.repository)
            rows = adjudicate_review(
                run_id=result.run_metadata.run_id,
                item=item,
                review=result.review,
                judge_backends=backends,
                round2_backends=round2,
                evidence_provider=RepositoryEvidenceProvider(repository, item),
            )
            bundle.write_adjudications(item.benchmark_id, rows)

    _write_json(
        matrix_root / "adjudication.json",
        {
            "judge_specs": judge_specs,
            "round2_judge_specs": round2_judge_specs or [],
            "run_count": len(payload["runs"]),
        },
    )
    return matrix_root


def _summary_row(name: str, summary: SummaryMetrics) -> str:
    def pct(value: float | None) -> str:
        return "N/A" if value is None else f"{value * 100:.2f}%"

    return (
        f"| {name} | {pct(summary.raw_recall_macro)} | "
        f"{pct(summary.weighted_recall_macro)} | "
        f"{pct(summary.valid_finding_precision)} | "
        f"{pct(summary.verdict_accuracy)} | "
        f"{pct(summary.merge_blocking_miss_rate)} | "
        f"{summary.total_tokens} | {summary.wall_time_ms / 1000:.2f}s |"
    )


def score_experiment_matrix(
    *,
    matrix_run_root: str | Path,
    manifest_path: str | Path,
    output_dir: str | Path | None = None,
) -> Path:
    """Score all arms together so clean-PR invalidation is globally consistent."""

    matrix_root = Path(matrix_run_root).resolve()
    payload = _matrix_payload(matrix_root)
    manifest, items = load_benchmark(manifest_path)
    arms: dict[str, list[Any]] = {}
    run_meta: dict[str, dict[str, Any]] = {}
    for run in payload["runs"]:
        key = f"{run['agent']}/run-{int(run['replicate']):02d}"
        arms[key] = [RunBundle(run["run_dir"]).load_result(item) for item in items]
        run_meta[key] = run

    scored, invalidated = score_campaign(manifest, arms)
    report_root = (
        Path(output_dir).resolve() if output_dir else matrix_root / "reports"
    )
    report_root.mkdir(parents=True, exist_ok=True)
    index: dict[str, Any] = {}
    summaries: dict[str, SummaryMetrics] = {}
    for key, (per_pr, summary) in scored.items():
        summaries[key] = summary
        destination = report_root / key
        destination.mkdir(parents=True, exist_ok=True)
        _write_json(
            destination / "per_pr.json",
            [row.model_dump(mode="json", exclude_none=True) for row in per_pr],
        )
        _write_json(
            destination / "summary.json",
            summary.model_dump(mode="json", exclude_none=True),
        )
        (destination / "summary.md").write_text(
            render_summary(summary), encoding="utf-8"
        )
        (destination / "per_pr.md").write_text(
            render_per_pr(per_pr), encoding="utf-8"
        )
        (destination / "validity.md").write_text(
            render_validity(summary), encoding="utf-8"
        )
        index[key] = {
            **run_meta[key],
            "report_dir": str(destination),
            "summary": summary.model_dump(mode="json", exclude_none=True),
        }

    lines = [
        f"# Three-arm PR Review Evaluation — {manifest.benchmark_version}",
        "",
        "No composite score is produced. All arms below were scored in one campaign,",
        "so a VALID_NEW finding on an Auto-certified Clean PR invalidates that PR",
        "for every arm consistently.",
        "",
        "| Arm / replicate | Raw Recall | Weighted Recall | Valid Precision | Verdict Accuracy | Merge-blocking Miss | Tokens | Wall time |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    lines.extend(_summary_row(name, summary) for name, summary in summaries.items())
    lines.extend(
        [
            "",
            "## Globally invalidated benchmark items",
            "",
            *(f"- `{item}`" for item in sorted(invalidated)),
        ]
        if invalidated
        else ["", "## Globally invalidated benchmark items", "", "None."]
    )
    (report_root / "matrix-summary.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    _write_json(
        report_root / "matrix-scores.json",
        {
            "benchmark_version": manifest.benchmark_version,
            "invalidated_benchmark_ids": sorted(invalidated),
            "runs": index,
        },
    )
    return report_root
