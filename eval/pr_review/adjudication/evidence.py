"""Fixed-snapshot evidence packages for disputed round-2 jury decisions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from ..benchmark.schema import BenchmarkItem, GroundTruthFinding, SourceLocation
from ..repository.snapshot import GitSnapshotError, diff_between, read_file_at, run_git
from ..runner.output_schema import AgentFinding


@dataclass(frozen=True)
class RepositoryEvidenceProvider:
    """Collect bounded evidence from only the benchmark's base/head snapshots.

    The provider runs on the trusted evaluator side. Every Git query is pinned to
    ``base_sha`` or ``head_sha``; it never reads a branch tip or review-after ref.
    """

    repository: str | Path
    item: BenchmarkItem
    context_lines: int = 80
    max_file_bytes: int = 400_000
    max_diff_bytes: int = 1_500_000
    max_reference_bytes: int = 250_000

    def for_match(self, prediction: AgentFinding, gt: GroundTruthFinding) -> dict[str, Any]:
        locations = [prediction.location, *prediction.evidence, *gt.accepted_locations, *gt.evidence]
        return self._package(locations=locations, symbols=self._symbols(prediction, gt))

    def for_validity(self, prediction: AgentFinding) -> dict[str, Any]:
        return self._package(
            locations=[prediction.location, *prediction.evidence],
            symbols=self._symbols(prediction, None),
        )

    def for_duplicate(
        self,
        prediction: AgentFinding,
        accepted_prediction: AgentFinding,
        gt: GroundTruthFinding,
    ) -> dict[str, Any]:
        return self._package(
            locations=[
                prediction.location,
                *prediction.evidence,
                accepted_prediction.location,
                *accepted_prediction.evidence,
                *gt.accepted_locations,
                *gt.evidence,
            ],
            symbols=self._symbols(prediction, gt) | self._symbols(accepted_prediction, gt),
        )

    def _package(self, *, locations: list[SourceLocation], symbols: set[str]) -> dict[str, Any]:
        unique_locations: dict[tuple[str, int, int], SourceLocation] = {}
        for location in locations:
            unique_locations[(location.file, location.start_line, location.end_line)] = location

        contexts = [self._location_context(location) for location in unique_locations.values()]
        contexts = [context for context in contexts if context]
        return {
            "base_sha": self.item.base_sha,
            "head_sha": self.item.head_sha,
            "location_contexts": contexts,
            "base_head_diff": self._bounded_diff(),
            "symbol_references": {
                symbol: references
                for symbol in sorted(symbols)
                if (references := self._symbol_references(symbol))
            },
            "related_tests": self._related_tests(unique_locations.values(), symbols),
        }

    def _location_context(self, location: SourceLocation) -> dict[str, Any] | None:
        path = PurePosixPath(location.file)
        if path.is_absolute() or ".." in path.parts:
            return None
        versions: dict[str, Any] = {}
        for label, sha in (("head", self.item.head_sha), ("base", self.item.base_sha)):
            try:
                text = read_file_at(self.repository, sha, path.as_posix(), max_bytes=self.max_file_bytes)
            except GitSnapshotError:
                continue
            lines = text.splitlines()
            start = max(1, location.start_line - self.context_lines)
            end = min(len(lines), location.end_line + self.context_lines)
            versions[label] = {
                "sha": sha,
                "start_line": start,
                "end_line": end,
                "text": "\n".join(f"{number:>6}  {lines[number - 1]}" for number in range(start, end + 1)),
            }
        if not versions:
            return None
        return {
            "file": path.as_posix(),
            "requested_start_line": location.start_line,
            "requested_end_line": location.end_line,
            "symbol": location.symbol,
            "versions": versions,
        }

    def _bounded_diff(self) -> str:
        try:
            return diff_between(
                self.repository,
                self.item.base_sha,
                self.item.head_sha,
                max_bytes=self.max_diff_bytes,
            )
        except GitSnapshotError as exc:
            return f"<diff unavailable: {exc}>"

    def _symbol_references(self, symbol: str) -> str:
        if not symbol or len(symbol) > 200 or any(char in symbol for char in "\n\r\0"):
            return ""
        try:
            return run_git(
                self.repository,
                "grep",
                "-n",
                "-I",
                "-F",
                "-e",
                symbol,
                self.item.head_sha,
                "--",
                max_bytes=self.max_reference_bytes,
            )
        except GitSnapshotError:
            return ""

    def _related_tests(self, locations, symbols: set[str]) -> list[dict[str, str]]:
        changed_stems = {PurePosixPath(location.file).stem.lower() for location in locations}
        try:
            files = run_git(
                self.repository,
                "ls-tree",
                "-r",
                "--name-only",
                self.item.head_sha,
                max_bytes=1_000_000,
            ).splitlines()
        except GitSnapshotError:
            return []
        candidates = [
            file
            for file in files
            if "test" in PurePosixPath(file).parts or PurePosixPath(file).name.lower().startswith("test_")
        ]
        relevant = [
            file
            for file in candidates
            if PurePosixPath(file).stem.lower() in changed_stems
            or any(stem and stem in file.lower() for stem in changed_stems)
        ][:12]
        if not relevant and symbols:
            relevant = candidates[:4]
        results: list[dict[str, str]] = []
        for file in relevant:
            try:
                text = read_file_at(self.repository, self.item.head_sha, file, max_bytes=120_000)
            except GitSnapshotError:
                continue
            if symbols and not any(symbol in text for symbol in symbols):
                continue
            results.append({"file": file, "text": text[:120_000]})
        return results

    @staticmethod
    def _symbols(prediction: AgentFinding, gt: GroundTruthFinding | None) -> set[str]:
        symbols = {prediction.location.symbol} if prediction.location.symbol else set()
        if gt is not None:
            symbols.update(location.symbol for location in gt.accepted_locations if location.symbol)
        return {symbol for symbol in symbols if symbol}
