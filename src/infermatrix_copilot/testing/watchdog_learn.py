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


def _to_noise_regex(pattern: str) -> str:
    """A normalized (possibly truncated) raw line as a noise regex. The
    truncation marker becomes a real wildcard — escaping the literal `...`
    would demand three dots the original line never had, so promoted long
    patterns would never match their own source lines."""
    if pattern.endswith("..."):
        return re.escape(pattern[:-3]) + ".*"
    return re.escape(pattern)


def normalize_pattern(pattern: str) -> str:
    """A stable key from a full matched line: drop `(Proc pid=NNN)` prefixes,
    cap the length — raw lines carry pids and payloads that never repeat."""
    p = pattern.strip()
    p = re.sub(r"^\s*\([^)]+\)\s*", "", p)
    if len(p) > 120:
        p = p[:117] + "..."
    return p


def repair_tail(fh) -> None:
    """Truncate a torn final record (crash mid-append) back to the last
    newline-terminated line. Must be called under the file's flock, on a
    handle open for update. The fragment was never durable — dropping it is
    the accepted crash-during-write semantics; what this prevents is a
    RESUMED writer fusing its next record onto the fragment, producing one
    malformed line that silently swallows a real decision at harvest."""
    fh.seek(0, os.SEEK_END)
    size = fh.tell()
    if size == 0:
        return
    fh.seek(size - 1)
    if fh.read(1) == b"\n":
        return
    # walk back to the previous newline (bounded chunks, files are small)
    pos = size - 1
    chunk = 4096
    while pos > 0:
        start = max(0, pos - chunk)
        fh.seek(start)
        buf = fh.read(pos - start)
        nl = buf.rfind(b"\n")
        if nl != -1:
            fh.truncate(start + nl + 1)
            fh.flush()
            os.fsync(fh.fileno())
            return
        pos = start
    fh.truncate(0)
    fh.flush()
    os.fsync(fh.fileno())


def record(decision_log: Path, *, pattern: str, verdict: str, test: str = "",
           module: str = "", run: str = "", attempt: str = "",
           job_key: str = "", seq: int | None = None) -> None:
    """Append one decision (flock + fsync: watchdog threads race). The
    optional `run`/`attempt`/`job_key`/`seq` fields form the stable identity
    the curator's exactly-once harvest dedups on. Before appending, a torn
    tail left by a crashed writer is repaired under the same lock, so a
    resumed writer can never fuse its record onto a fragment."""
    decision_log = Path(decision_log)
    decision_log.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pattern": normalize_pattern(pattern),
        "verdict": verdict.upper(),
        "test": test, "module": module, "run": run,
    }
    if attempt:
        entry["attempt"] = attempt
    if job_key:
        entry["job_key"] = job_key
    if seq is not None:
        entry["seq"] = int(seq)
    with open(decision_log, "a+b") as fh:
        if fcntl is not None:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            repair_tail(fh)
            fh.seek(0, os.SEEK_END)
            fh.write((json.dumps(entry, ensure_ascii=False) + "\n")
                     .encode("utf-8"))
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


def _identity(entry: dict) -> tuple:
    """The exactly-once harvest key. Entries carrying the stable identity
    fields dedup on (run, attempt, job_key, seq); legacy entries (recorded
    before the fields existed) fall back to their full content — weaker,
    but a legacy duplicate is then at worst re-counted once, never lost."""
    if entry.get("seq") is not None:
        return ("id", entry.get("run", ""), entry.get("attempt", ""),
                entry.get("job_key", ""), int(entry["seq"]))
    return ("legacy", entry.get("ts", ""), entry.get("pattern", ""),
            entry.get("verdict", ""), entry.get("test", ""))


def harvest(state_log: Path, checkpoint_file: Path, source_files: list,
            *, lock_path: Path) -> int:
    """Exactly-once move of per-run decision files into the STATE log
    (design D4). The state log ITSELF is the dedup authority: under the
    state lock, its torn tail (if any) is repaired first, its identity set
    is scanned, and only missing entries are appended (complete lines,
    fsync'd) — THEN the per-source digest checkpoint is updated
    (tmp+rename), purely as a fast-path to skip re-reading unchanged
    sources. A crash after append/before checkpoint re-scans and appends
    nothing; a crash mid-append leaves a tail the next harvest repairs.
    Returns the number of newly appended decisions."""
    state_log = Path(state_log)
    checkpoint_file = Path(checkpoint_file)
    lock_path = Path(lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        if fcntl is not None:
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
        checkpoint: dict = {}
        if checkpoint_file.exists():
            try:
                checkpoint = json.loads(
                    checkpoint_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                checkpoint = {}
        state_log.parent.mkdir(parents=True, exist_ok=True)
        appended = 0
        with open(state_log, "a+b") as fh:
            repair_tail(fh)
            seen = {_identity(e) for e in read_decisions(state_log)}
            for source in source_files:
                source = Path(source)
                if not source.is_file():
                    continue
                import hashlib
                digest = hashlib.sha256(source.read_bytes()).hexdigest()
                if checkpoint.get(str(source)) == digest:
                    continue
                for entry in read_decisions(source):
                    ident = _identity(entry)
                    if ident in seen:
                        continue
                    seen.add(ident)
                    fh.seek(0, os.SEEK_END)
                    fh.write((json.dumps(entry, ensure_ascii=False) + "\n")
                             .encode("utf-8"))
                    appended += 1
                checkpoint[str(source)] = digest
            fh.flush()
            os.fsync(fh.fileno())
        tmp = checkpoint_file.with_name(checkpoint_file.name + ".tmp")
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as cf:
            json.dump(checkpoint, cf, indent=1)
            cf.flush()
            os.fsync(cf.fileno())
        os.replace(tmp, checkpoint_file)
        return appended
    finally:
        if fcntl is not None:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)


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

    # seed patterns are compared raw (either-direction substring); overlay
    # dedup compares in regex space — the one representation each side
    # actually stores — so repeated promote() calls append nothing
    candidates = eligible_patterns(
        read_decisions(decision_log), existing=set(seed_noise),
        min_count=min_count, min_days=min_days)
    new = [p for p in candidates if _to_noise_regex(p) not in set(current)]
    if not new:
        return []
    doc["noise"] = current + [_to_noise_regex(p) for p in new]
    overlay.parent.mkdir(parents=True, exist_ok=True)
    tmp = overlay.with_name(overlay.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False))
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, overlay)
    from ..memory.skills import _fsync_dir
    _fsync_dir(overlay.parent)
    return new
