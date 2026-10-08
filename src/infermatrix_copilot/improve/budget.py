"""The weekly budget envelope, enforced per model call (design §10).

Two hard envelopes per ISO week, persisted under the ledger directory and
serialized across processes: dollars (`improve_budget_usd_week`) and judge
CLI calls (`improve_budget_judge_calls_week`). A call is RESERVED before it
is sent and SETTLED after, so ``settled + reserved <= envelope`` holds at
every instant, concurrent workers and processes included; a reservation
that does not fit raises `BudgetRefused` and the call is never made.

Every reservation is pinned to the week it was taken in (its id carries the
week), and its settlement or release goes to THAT week's file: a call that
spans the weekly boundary neither strands its reservation nor charges a
week whose envelope it never checked.

The reservation is a true upper bound: output tokens are the request's
``max_tokens`` (the API enforces it); input tokens — including cache reads
and cache writes, which are prompt tokens billed at their own rates — are
bounded by the request's UTF-8 byte count for the visible payload. Gateways
can inject hidden prompts; configure their exact models in
``improve_input_context_limits`` with the provider's full context ceiling.
The larger bound is priced at the dearest configured input/cache rate.
Settlement charges the cache-aware cost exactly as `metrics.cost_from_spans`
does. Prices come from the metrics price table; a model with no price cannot
be reserved and is refused, never priced at zero. If a settlement ever
exceeds its reservation the governor records a ``budget_breach`` in the
week's file; every governor instance and process refuses from then on
until an operator clears it (fail closed, not "note and continue").

Named reservations (`reserve_named`/`release_named`) hold an experiment's
planning estimate from registration until it runs, so two registrations
cannot claim the same funds and a forensics pass cannot spend them.

`governed(governor)` binds the governor for the choke points
(`LLM.create`, `judges.run_judge`); with nothing bound, calls are unmetered.
A shadow subprocess binds its own governor from the environment
(`IMPROVE_GOVERNED=1` + `IMPROVE_LEDGER_DIR`) against the same files.
"""

from __future__ import annotations

import contextvars
import datetime as dt
import json
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from ..trace_store import current_store, file_lock

_GOVERNOR: contextvars.ContextVar["Governor | None"] = contextvars.ContextVar("improve_governor", default=None)


class BudgetRefused(RuntimeError):
    """The reservation does not fit the envelope: the call was not made."""


class BudgetBreach(RuntimeError):
    """A settlement exceeded its reservation: the cycle must abort."""


def iso_week(now: float) -> str:
    d = dt.datetime.fromtimestamp(now, dt.timezone.utc).isocalendar()
    return f"{d[0]}-W{d[1]:02d}"


def request_bytes(kwargs: dict) -> int:
    """The UTF-8 size of everything the request carries (system, messages,
    tool definitions): the prompt-token upper bound."""
    payload = {k: kwargs.get(k) for k in ("system", "messages", "tools")}
    return len(json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8"))


def worst_case_usd(model: str, req_bytes: int, max_tokens: int, settings: Any = None) -> float:
    from ..metrics import CACHE_CREATE_FACTOR, CACHE_READ_FACTOR, model_price, model_price_known

    if not model_price_known(model, settings):
        raise BudgetRefused(f"no price for model {model!r}: it cannot be reserved (never priced at zero)")
    pin, pout = model_price(model, settings)
    limits = getattr(settings, "improve_input_context_limits", {}) or {}
    limit = limits.get(model, 0)
    if type(limit) is not int or limit < 0:
        raise BudgetRefused(f"invalid input context ceiling for model {model!r}")
    input_bound = max(req_bytes, limit)
    read_factor = float(getattr(settings, "cache_read_price_factor", 0) or 0) or CACHE_READ_FACTOR
    input_factor = max(1.0, CACHE_CREATE_FACTOR, read_factor)
    return input_bound / 1e6 * pin * input_factor + max(0, int(max_tokens or 0)) / 1e6 * pout


def actual_usd(model: str, usage: dict | None, settings: Any = None) -> float:
    """The cache-aware cost of a call, as `metrics.cost_from_spans` prices it."""
    from ..metrics import CACHE_CREATE_FACTOR, CACHE_READ_FACTOR, model_price

    pin, pout = model_price(model, settings)
    read_f = float(getattr(settings, "cache_read_price_factor", 0) or 0) or CACHE_READ_FACTOR
    u = usage or {}
    tin = int(u.get("input_tokens") or 0)
    tout = int(u.get("output_tokens") or 0)
    cread = int(u.get("cache_read_input_tokens") or u.get("cache_read_tokens") or 0)
    ccreate = int(u.get("cache_creation_input_tokens") or u.get("cache_creation_tokens") or 0)
    return (tin / 1e6 * pin + tout / 1e6 * pout + cread / 1e6 * pin * read_f
            + ccreate / 1e6 * pin * CACHE_CREATE_FACTOR)


class Governor:
    def __init__(self, ledger_dir: str | Path, *, usd_week: float, judge_calls_week: int,
                 settings: Any = None, clock=time.time):
        self.dir = Path(ledger_dir) / "budget"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.usd_week = float(usd_week)
        self.judge_calls_week = int(judge_calls_week)
        self.settings = settings
        self._clock = clock
        self.breached = False

    # -- state per week ---------------------------------------------------------------
    def week(self) -> str:
        return iso_week(self._clock())

    def _path(self, week: str) -> Path:
        return self.dir / f"{week}.json"

    def _load(self, week: str) -> dict:
        path = self._path(week)
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {"week": week, "usd_settled": 0.0, "reservations": {}, "named": {}, "judge_calls": 0,
                "judge_reserved": 0, "breaches": [], "refused": 0}

    def _save(self, week: str, state: dict) -> None:
        path = self._path(week)
        tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex[:6]}.tmp")
        tmp.write_text(json.dumps(state, indent=1), encoding="utf-8")
        tmp.replace(path)

    @contextmanager
    def _locked(self, week: str) -> Iterator[dict]:
        with file_lock(self.dir / "budget.lock", blocking=True, timeout=30.0) as held:
            if not held:
                raise BudgetRefused("the budget ledger is locked by another process")
            state = self._load(week)
            try:
                yield state
            finally:
                self._save(week, state)   # a refusal counted before the raise is state too

    @staticmethod
    def _reserved(state: dict) -> float:
        return sum(float(v["usd"]) for v in state["reservations"].values()) + \
            sum(float(v) for v in state["named"].values())

    def _stop_if_breached(self, state: dict) -> None:
        if state["breaches"] or self.breached:
            self.breached = True
            raise BudgetRefused("the budget governor is breached (recorded for this week); no further calls until cleared")

    def remaining(self, week: str | None = None) -> dict:
        week = week or self.week()
        state = self._load(week)
        reserved = self._reserved(state)
        return {"week": week, "usd_envelope": self.usd_week, "usd_settled": round(state["usd_settled"], 6),
                "usd_reserved": round(reserved, 6), "named": {k: round(float(v), 6) for k, v in state["named"].items()},
                "usd_remaining": round(self.usd_week - state["usd_settled"] - reserved, 6),
                "judge_calls_envelope": self.judge_calls_week, "judge_calls_used": state["judge_calls"],
                "judge_calls_reserved": state["judge_reserved"],
                "judge_calls_remaining": self.judge_calls_week - state["judge_calls"] - state["judge_reserved"],
                "breached": bool(state["breaches"]) or self.breached, "refused": state["refused"]}

    # -- dollars ------------------------------------------------------------------------
    def reserve_call(self, model: str, req_bytes: int, max_tokens: int, *, purpose: str = "") -> str:
        """Reserve the worst case for one model call in the current week;
        the id pins the week. Raises BudgetRefused."""
        est = worst_case_usd(model, req_bytes, max_tokens, self.settings)
        week = self.week()
        with self._locked(week) as state:
            self._stop_if_breached(state)
            if state["usd_settled"] + self._reserved(state) + est > self.usd_week + 1e-12:
                state["refused"] += 1
                raise BudgetRefused(
                    f"reserving ${est:.4f} for {model} would exceed the weekly envelope "
                    f"(${self.usd_week:.2f}; settled ${state['usd_settled']:.4f}, reserved ${self._reserved(state):.4f})")
            rid = f"{week}|{uuid.uuid4().hex[:10]}"
            state["reservations"][rid] = {"usd": est, "model": model, "at": self._clock(), "purpose": purpose}
        return rid

    @staticmethod
    def _week_of(reservation_id: str) -> str:
        return reservation_id.split("|", 1)[0]

    def settle_call(self, reservation_id: str, usage: dict | None, model: str) -> float:
        """Replace the reservation by the actual cache-aware cost, in the
        reservation's week; a cost above the reservation is a breach
        (persisted, governor marked, exception)."""
        actual = actual_usd(model, usage, self.settings)
        week = self._week_of(reservation_id)
        breached = False
        with self._locked(week) as state:
            reservation = state["reservations"].pop(reservation_id, None)
            state["usd_settled"] += actual
            if reservation is not None and actual > float(reservation["usd"]) + 1e-9:
                state["breaches"].append({"reservation": reservation_id, "reserved": reservation["usd"],
                                          "actual": actual, "model": model, "at": self._clock()})
                breached = True
        if breached:
            self.breached = True
            self._record_breach(reservation_id, model, actual)
            raise BudgetBreach(f"settlement ${actual:.4f} exceeded its reservation for {model}: cycle aborted")
        return actual

    def release_call(self, reservation_id: str) -> None:
        """Drop a reservation for a call that failed BEFORE it was sent."""
        with self._locked(self._week_of(reservation_id)) as state:
            state["reservations"].pop(reservation_id, None)

    def forfeit_call(self, reservation_id: str) -> float:
        """A call that was sent but whose usage is unknown (an interrupted
        stream, a transport error after billing may have happened): the whole
        reservation is charged as spent — the conservative side."""
        with self._locked(self._week_of(reservation_id)) as state:
            reservation = state["reservations"].pop(reservation_id, None)
            charged = float(reservation["usd"]) if reservation else 0.0
            state["usd_settled"] += charged
        return charged

    # -- named (planned) reservations -----------------------------------------------------
    def reserve_named(self, name: str, usd: float) -> None:
        """Hold ``usd`` under ``name`` (an experiment's planning estimate)
        in the current week until released; refused when it does not fit."""
        week = self.week()
        with self._locked(week) as state:
            self._stop_if_breached(state)
            already = float(state["named"].get(name, 0.0))
            if state["usd_settled"] + self._reserved(state) - already + float(usd) > self.usd_week + 1e-12:
                state["refused"] += 1
                raise BudgetRefused(f"holding ${float(usd):.2f} for {name} would exceed the weekly envelope")
            state["named"][name] = float(usd)

    def release_named(self, name: str, week: str | None = None) -> float:
        """Release a named hold (the experiment now reserves per call)."""
        with self._locked(week or self.week()) as state:
            return float(state["named"].pop(name, 0.0))

    # -- judge calls ----------------------------------------------------------------------
    def reserve_judge_call(self) -> str:
        """Reserve one judge call in the current week; returns a token that
        pins the week, so a call crossing the boundary settles where it was
        reserved."""
        week = self.week()
        with self._locked(week) as state:
            self._stop_if_breached(state)
            if state["judge_calls"] + state["judge_reserved"] + 1 > self.judge_calls_week:
                state["refused"] += 1
                raise BudgetRefused(f"the weekly judge-call envelope ({self.judge_calls_week}) is exhausted")
            state["judge_reserved"] += 1
        return f"{week}|judge|{uuid.uuid4().hex[:8]}"

    def settle_judge_call(self, token: str | None = None) -> None:
        week = self._week_of(token) if token else self.week()
        with self._locked(week) as state:
            state["judge_reserved"] = max(0, state["judge_reserved"] - 1)
            state["judge_calls"] += 1

    def clear_breach(self, week: str | None = None) -> None:
        """Operator action: forget the week's breach records."""
        with self._locked(week or self.week()) as state:
            state["breaches"] = []
        self.breached = False

    def _record_breach(self, reservation_id: str, model: str, actual: float) -> None:
        store = current_store()
        if store is None:
            return
        try:
            store.append("decision", context={"playbook": "workflow-improve"},
                         result={"type": "incident", "kind": "budget_breach", "reservation": reservation_id,
                                 "model": model, "actual_usd": actual, "severity": "severe"})
        except Exception:  # noqa: BLE001 - the week's file already holds the breach
            pass


@contextmanager
def governed(governor: "Governor | None") -> Iterator["Governor | None"]:
    token = _GOVERNOR.set(governor)
    try:
        yield governor
    finally:
        _GOVERNOR.reset(token)


def current_governor() -> "Governor | None":
    return _GOVERNOR.get()
