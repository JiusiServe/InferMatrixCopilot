"""RunTrace — append-only factual record of a run (facts recorded freely).

Never injected into prompts by default; consumed by diff summaries, patch-review
triggers, escalation reports, and audits.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Iterator


class RunTrace:
    """Append-only JSONL event log for one run. A shared lock lets concurrent
    agent steps write to the same file safely; each line is one timestamped
    event."""

    def __init__(self, path: Path):
        """Open the trace at `path`, creating parent dirs, and set up the write
        lock shared across concurrent writers."""
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()  # concurrent agent steps share one trace

    def record(self, kind: str, **fields: Any) -> None:
        """Append one event of type `kind` with arbitrary `fields`, stamped with
        the current time. Non-serializable values fall back to `str`."""
        event = {"ts": time.time(), "kind": kind, **fields}
        with self._lock, self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")

    def events(self, kind: str | None = None) -> Iterator[dict]:
        """Yield recorded events in order, optionally filtered to `kind`. Missing
        file yields nothing; malformed lines are skipped so a partial write can
        never break a reader."""
        if not self.path.exists():
            return
        with self.path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if kind is None or ev.get("kind") == kind:
                    yield ev
