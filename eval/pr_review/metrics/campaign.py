"""Cross-agent campaign scoring with globally consistent benchmark invalidation."""

from __future__ import annotations

from ..adjudication.models import FinalStatus
from ..benchmark.schema import BenchmarkManifest, CleanStatus
from .aggregate import aggregate_results
from .models import PRResultInput


def campaign_invalidated_ids(arms: dict[str, list[PRResultInput]]) -> set[str]:
    invalidated: set[str] = set()
    for results in arms.values():
        for result in results:
            if result.item.invalidated:
                invalidated.add(result.item.benchmark_id)
            elif result.item.clean_status == CleanStatus.AUTO_CERTIFIED_CLEAN and any(
                row.final_status == FinalStatus.VALID_NEW for row in result.adjudications
            ):
                invalidated.add(result.item.benchmark_id)
    return invalidated


def score_campaign(
    manifest: BenchmarkManifest,
    arms: dict[str, list[PRResultInput]],
):
    invalidated = campaign_invalidated_ids(arms)
    scored = {
        name: aggregate_results(
            results,
            benchmark_version=manifest.benchmark_version,
            rubric_version=manifest.rubric_version,
            judge_version=manifest.judge_version,
            forced_invalidated_ids=invalidated,
        )
        for name, results in arms.items()
    }
    return scored, invalidated
