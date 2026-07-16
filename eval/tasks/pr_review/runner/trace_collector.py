"""Append-only evaluation trace and resource accounting."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from pydantic import BaseModel, ConfigDict, Field


class ToolCallStats(BaseModel):
    model_config = ConfigDict(extra="forbid")
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    refused: int = 0
    returned_bytes: int = 0


class RunMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: str
    benchmark_version: str
    benchmark_id: str
    agent_version: str
    model: str
    model_parameters: dict[str, Any] = Field(default_factory=dict)
    prompt_version: str
    tool_policy_version: str
    repository_sha: str
    started_at: str
    finished_at: str
    output_contract_valid: bool = True
    output_contract_repaired: bool = False
    output_contract_failure: bool = False
    agent_failure: bool = False
    failure_reason: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    wall_time_ms: int = 0
    tool_calls: dict[str, ToolCallStats] = Field(default_factory=dict)
    policy_violations: list[str] = Field(default_factory=list)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class TraceCollector:
    path: Path
    _started: float = field(default_factory=time.monotonic)

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, kind: str, **fields: Any) -> None:
        event = {"ts": time.time(), "kind": kind, **fields}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")

    def events(self) -> Iterator[dict[str, Any]]:
        if not self.path.exists():
            return
        with self.path.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    value = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict):
                    yield value

    @property
    def wall_time_ms(self) -> int:
        return int((time.monotonic() - self._started) * 1000)
