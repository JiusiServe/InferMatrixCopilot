"""Watchdog auto-learning — port of the rebase agent's watchdog_learn.py.

Tracks Tier-2 KILL/CONTINUE decisions and auto-promotes consistently benign
patterns into a noise **overlay YAML** (data), where the shell version edited
test_watchdog.sh in place (code). Promotion rules unchanged: ≥ `min_count`
matches, all CONTINUE, spanning ≥ `min_days` days, not already covered.
Append-only: learning may silence noise, never remove or sharpen patterns.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path

try:  # POSIX-only, same guard as run_status.py
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None  # type: ignore

PROMOTE_MIN_COUNT = 3
PROMOTE_MIN_DAYS = 5


def _unescape(pattern: str) -> str:
    """Invert `re.escape` (every escape it emits is a single backslash)."""
    return re.sub(r"\\(.)", r"\1", pattern)


def normalize_pattern(pattern: str) -> str:
    """A stable key from a full matched line: drop `(Proc pid=NNN)` prefixes,
    cap the length — raw lines carry pids and payloads that never repeat."""
    p = pattern.strip()
    p = re.sub(r"^\s*\([^)]+\)\s*", "", p)
    if len(p) > 120:
        p = p[:117] + "..."
    return p


def record(decision_log: Path, *, pattern: str, verdict: str, test: str = "",
           module: str = "", run: str = "") -> None:
    """Append one decision (flock + fsync: watchdog threads race)."""
    decision_log = Path(decision_log)
    decision_log.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pattern": normalize_pattern(pattern),
        "verdict": verdict.upper(),
        "test": test, "module": module, "run": run,
    }
    with open(decision_log, "a", encoding="utf-8") as fh:
        if fcntl is not None:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        finally:
            if fcntl is not None:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def read_decisions(decision_log: Path) -> list[dict]:
    if not Path(decision_log).exists():
        return []
    out = []
    for line in Path(decision_log).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def eligible_patterns(decisions: list[dict], *, existing: set[str],
                      min_count: int = PROMOTE_MIN_COUNT,
                      min_days: int = PROMOTE_MIN_DAYS) -> list[str]:
    """Patterns meeting the promotion rules and not already covered (exact or
    either-direction substring against `existing`)."""
    by_pattern: dict[str, list[dict]] = {}
    for d in decisions:
        by_pattern.setdefault(normalize_pattern(d.get("pattern", "")), []).append(d)

    promoted = []
    for pattern, entries in sorted(by_pattern.items()):
        if not pattern or len(entries) < min_count:
            continue
        if not all(e.get("verdict") == "CONTINUE" for e in entries):
            continue
        stamps = []
        for e in entries:
            try:
                stamps.append(datetime.strptime(e["ts"], "%Y-%m-%d %H:%M:%S"))
            except (KeyError, ValueError):
                continue
        if len(stamps) >= 2 and (max(stamps) - min(stamps)).days < min_days:
            continue
        if len(stamps) < 2:  # a single-day burst never qualifies
            continue
        if any(ep and (ep in pattern or pattern in ep) for ep in existing):
            continue
        promoted.append(pattern)
    return promoted


def promote(decision_log: Path, overlay: Path, *, seed_noise: list[str],
            min_count: int = PROMOTE_MIN_COUNT,
            min_days: int = PROMOTE_MIN_DAYS) -> list[str]:
    """Append newly eligible patterns to the overlay YAML's `noise:` list.
    `seed_noise` is the adapter seed file's list, so a promoted pattern never
    duplicates seed coverage. Promoted lines are escaped with `re.escape` —
    decisions record raw log lines, not regexes."""
    import yaml

    overlay = Path(overlay)
    doc = {}
    if overlay.exists():
        doc = yaml.safe_load(overlay.read_text(encoding="utf-8")) or {}
    current = list(doc.get("noise", []))
    # overlay entries are escaped regexes while candidates are raw lines —
    # compare both forms, else every promote() re-appends the same pattern
    existing = set(seed_noise) | set(current) | {
        _unescape(e) for e in current}

    new = eligible_patterns(read_decisions(decision_log), existing=existing,
                            min_count=min_count, min_days=min_days)
    if not new:
        return []
    doc["noise"] = current + [re.escape(p) for p in new]
    overlay.parent.mkdir(parents=True, exist_ok=True)
    tmp = overlay.with_name(overlay.name + ".tmp")
    tmp.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False),
                   encoding="utf-8")
    os.replace(tmp, overlay)
    return new
