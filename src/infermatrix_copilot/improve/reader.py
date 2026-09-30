"""Reading trace/1 into units of work (design §3.1).

A *unit* is every record that shares a ``context.unit_id`` (one step call or
one agent loop). Records without a unit id — the knowledge service's own
decisions, the review bot's per-attempt records — fall back to
``"<run_id>:<step>"`` and finally to the record id, so nothing written to the
store is invisible to Tier 1. A unit's *workflow* is ``context.workflow``
when the step is enrolled, else ``"<playbook>.<step>"`` marked undeclared.
"""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from ..trace_store import TraceStore


@dataclass
class Unit:
    unit_id: str
    workflow: str
    playbook: str
    step: str
    declared: bool
    item: str = ""
    fingerprint: str = ""
    records: list[dict] = field(default_factory=list)

    @property
    def model_calls(self) -> list[dict]:
        return [r for r in self.records if r["kind"] == "model_call"]

    @property
    def tool_calls(self) -> list[dict]:
        return [r for r in self.records if r["kind"] == "tool_call"]

    @property
    def decisions(self) -> list[dict]:
        return [r for r in self.records if r["kind"] == "decision"]

    @property
    def started(self) -> float:
        return min(r["at"] for r in self.records)

    @property
    def ended(self) -> float:
        return max(r["at"] for r in self.records)

    @property
    def seconds(self) -> float:
        return sum(float(r.get("seconds") or 0.0) for r in self.records)

    def tokens(self) -> tuple[int, int]:
        i = o = 0
        for r in self.model_calls:
            u = r.get("usage") or {}
            i += int(u.get("input_tokens") or 0)
            o += int(u.get("output_tokens") or 0)
        return i, o


def unit_key(record: dict) -> str:
    ctx = record.get("context") or {}
    if ctx.get("unit_id"):
        return str(ctx["unit_id"])
    if ctx.get("run_id"):
        return f"{ctx['run_id']}:{ctx.get('step') or ctx.get('playbook') or ''}"
    return str(record["id"])


def workflow_key(record: dict) -> tuple[str, bool]:
    ctx = record.get("context") or {}
    if ctx.get("workflow"):
        return str(ctx["workflow"]), True
    playbook, step = str(ctx.get("playbook") or ""), str(ctx.get("step") or "")
    if playbook or step:
        return f"{playbook or '?'}.{step or '?'}", False
    return "unknown", False


def records_between(store: TraceStore, since: float, until: float) -> Iterator[dict]:
    """Records with ``since <= at < until`` from the JSONL files (the source of
    truth); files are named by UTC day, so only the days in range are read."""
    first_day = dt.datetime.fromtimestamp(since, dt.timezone.utc).date() - dt.timedelta(days=1)
    for path in sorted((store.root / "records").glob("*.jsonl")):
        try:
            day = dt.date.fromisoformat(path.stem)
        except ValueError:
            continue
        if day < first_day:
            continue
        text = path.read_text(encoding="utf-8")
        lines = text.split("\n")
        # a writer may be mid-append: an unterminated last line is deferred
        # to the next read rather than aborting the cycle
        if text and not text.endswith("\n"):
            lines = lines[:-1]
        for line in lines:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue  # a torn line: the writer's next append rewrites nothing, so skip it
            if since <= float(record.get("at") or 0) < until:
                yield record


UNIT_LOOKBACK = 2 * 24 * 3600.0   # how far before `since` a unit may have started
UNIT_GRACE = 3600.0               # a unit with no terminal decision is complete once it has been quiet this long


def unit_complete(unit: "Unit", until: float, *, grace: float = UNIT_GRACE) -> bool:
    """Completion evidence: a terminal ``decision`` after the unit's last
    model/tool call, or silence for ``grace`` before ``until`` (a unit that
    died without a decision still gets counted, and L14 says so)."""
    calls = unit.model_calls + unit.tool_calls
    last_call = max((r["at"] for r in calls), default=None)
    if unit.decisions and (last_call is None or unit.decisions[-1]["at"] >= last_call):
        return True
    return until - unit.ended >= grace


def collect_units(store: TraceStore, since: float, until: float, *, lookback: float = UNIT_LOOKBACK,
                  counted: set[str] | None = None, deferred: set[str] | None = None,
                  origin: float | None = None, contiguous: bool = True,
                  grace: float = UNIT_GRACE, legacy_cutoff: float | None = None) -> tuple[dict[str, Unit], set[str]]:
    """``(units to count, units deferred)`` for the window ``[since, until)``.

    A unit is attributed to exactly one cycle. Its records are read from up
    to ``lookback`` before ``since`` (a unit longer than that loses its head,
    and says so in L14). The latest record seen is not completion evidence —
    a unit still running at the cutoff would be counted now and again once
    its final records arrive — so a unit counts only when it is complete
    (`unit_complete`) and its id is not in ``counted``. An incomplete unit is
    DEFERRED: its id is returned so the cursor remembers the actual state
    rather than re-deriving it from timestamps later (a record can become
    visible after the cutoff — a torn trailing line — which a timestamp
    check would mistake for work completed before the window).

    A complete unit whose last record precedes ``since`` counts when it was
    explicitly deferred, or when it lies inside the engine's contiguous
    coverage (``origin`` = the first cycle's start and this window continues
    the previous one): such a unit was invisible last time, never counted,
    and must not be lost. Otherwise it is historical work (before the engine
    started, or before an explicit ``--since``) and belongs to no cycle.
    ``legacy_cutoff`` is the one-time migration of a cursor written before
    the deferred set existed: the old cycle counted every unit complete at
    its cutoff, so a pre-window unit is recovered as pending only when its
    own records show it was NOT complete then (a record that became visible
    late is the residual risk of that single migration, never of a normal
    cycle). Filtering records instead of units would split a unit across two
    cycles and hide every lint that needs both halves."""
    units: dict[str, Unit] = {}
    counted = counted or set()
    deferred = deferred or set()
    for record in records_between(store, since - lookback, until):
        key = unit_key(record)
        unit = units.get(key)
        if unit is None:
            ctx = record.get("context") or {}
            workflow, declared = workflow_key(record)
            unit = Unit(unit_id=key, workflow=workflow, playbook=str(ctx.get("playbook") or ""),
                        step=str(ctx.get("step") or ""), declared=declared,
                        item=str(ctx.get("item") or ""), fingerprint=str(ctx.get("fingerprint") or ""))
            units[key] = unit
        unit.records.append(record)
        ctx = record.get("context") or {}
        if not unit.fingerprint and ctx.get("fingerprint"):
            unit.fingerprint = str(ctx["fingerprint"])
        if not unit.item and ctx.get("item"):
            unit.item = str(ctx["item"])
    out: dict[str, Unit] = {}
    deferred_now: set[str] = set()
    for key, unit in units.items():
        unit.records.sort(key=lambda r: (r["at"], r["id"]))
        if key in counted or unit.ended >= until:
            continue
        if not unit_complete(unit, until, grace=grace):
            deferred_now.add(key)
            continue
        if unit.ended >= since or key in deferred:
            out[key] = unit
        elif legacy_cutoff is not None:
            if not _complete_as_of(unit, legacy_cutoff, grace):
                out[key] = unit      # pending at the old cutoff: recovered, not replayed
        elif contiguous and origin is not None and unit.ended >= origin:
            out[key] = unit          # late-visible inside continuous coverage
    return out, deferred_now


def units_between(store: TraceStore, since: float, until: float, *, lookback: float = UNIT_LOOKBACK,
                  counted: set[str] | None = None, deferred: set[str] | None = None,
                  origin: float | None = None, contiguous: bool = True,
                  grace: float = UNIT_GRACE) -> dict[str, Unit]:
    """The units to count (see `collect_units`)."""
    return collect_units(store, since, until, lookback=lookback, counted=counted, deferred=deferred,
                         origin=origin, contiguous=contiguous, grace=grace)[0]


def _complete_as_of(unit: Unit, moment: float, grace: float) -> bool:
    """Whether the unit, seen with only its records before ``moment``, would
    have counted as complete at ``moment`` (the legacy-cursor migration)."""
    earlier = [r for r in unit.records if r["at"] < moment]
    if not earlier:
        return False
    snapshot = Unit(unit.unit_id, unit.workflow, unit.playbook, unit.step, unit.declared,
                    unit.item, unit.fingerprint, earlier)
    return unit_complete(snapshot, moment, grace=grace)


def blob_text(store: TraceStore, ref: str) -> str:
    try:
        return store.blob(ref)
    except (KeyError, ValueError, OSError):
        return ""


def blob_ok(store: TraceStore, ref: str) -> bool:
    digest = str(ref).removeprefix("sha256:")
    return (store.root / "blobs" / digest[:2] / f"{digest}.gz").exists()


def output_text(store: TraceStore, record: dict) -> str:
    """The record's main output blob as text (reply, review body, result)."""
    outputs = record.get("outputs") or {}
    for key in ("reply", "review", "result", "body"):
        if key in outputs:
            return blob_text(store, outputs[key])
    return ""


def week_bounds(now: float) -> tuple[float, float]:
    """The previous seven days ``[now - 7d, now)`` — the default cycle window."""
    return now - 7 * 24 * 3600.0, now


def cursor_path(ledger_dir: Path) -> Path:
    return Path(ledger_dir) / "cursor.json"
