"""On-disk run bundle format shared by CLI stages."""

from __future__ import annotations

import json
from pathlib import Path

from .adjudication.models import AdjudicationRow
from .benchmark.schema import BenchmarkItem
from .metrics.models import PRResultInput
from .runner.output_schema import AgentReview
from .runner.trace_collector import RunMetadata


class RunBundle:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.predictions = self.root / "predictions"
        self.adjudications = self.root / "adjudications"
        self.metadata = self.root / "metadata"
        self.traces = self.root / "traces"
        for path in (self.predictions, self.adjudications, self.metadata, self.traces):
            path.mkdir(parents=True, exist_ok=True)

    def write_prediction(self, benchmark_id: str, review: AgentReview) -> Path:
        return _write_json(self.predictions / f"{benchmark_id}.json", review.model_dump(mode="json", exclude_none=True))

    def write_adjudications(self, benchmark_id: str, rows: list[AdjudicationRow]) -> Path:
        return _write_json(
            self.adjudications / f"{benchmark_id}.json",
            [row.model_dump(mode="json", exclude_none=True) for row in rows],
        )

    def write_metadata(self, benchmark_id: str, metadata: RunMetadata) -> Path:
        return _write_json(self.metadata / f"{benchmark_id}.json", metadata.model_dump(mode="json", exclude_none=True))

    def load_result(self, item: BenchmarkItem) -> PRResultInput:
        prediction_path = self.predictions / f"{item.benchmark_id}.json"
        adjudication_path = self.adjudications / f"{item.benchmark_id}.json"
        metadata_path = self.metadata / f"{item.benchmark_id}.json"
        review = AgentReview.model_validate_json(prediction_path.read_text(encoding="utf-8")) if prediction_path.exists() else None
        rows = (
            [AdjudicationRow.model_validate(value) for value in json.loads(adjudication_path.read_text(encoding="utf-8"))]
            if adjudication_path.exists() else []
        )
        metadata = RunMetadata.model_validate_json(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else None
        return PRResultInput(item=item, review=review, adjudications=rows, run_metadata=metadata)


def _write_json(path: Path, value) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)
    return path
