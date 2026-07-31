"""CI build lifecycle — the guarded-creation/recovery contract (Rev 8 §3.2)
plus the parent monitor's deterministic core (poll loop, no-run terminal
states, pure log classifiers, ported verbatim where pure).

Every build CREATION goes through `create_build_guarded`: a durable
``{op_id, state: intent}`` record precedes the API call, the build is
stamped with ``imx_op_id``/``imx_run_id`` metadata, and crash recovery
matches EXACTLY on that op id — zero matches re-polls boundedly (API
eventual consistency) then ESCALATES; multiple matches ESCALATE; a build is
NEVER re-created on uncertainty. Cancellation/rebuild is only ever allowed
for op-recorded builds.

The HTTP client is injected (a `CIClient` protocol) — the adapter's
provider wiring supplies the real one; everything here tests offline.
The agent-driven CI debug dispatch stays external (assembly wiring), same
as the test loop's debug_fn.
"""

from __future__ import annotations

import calendar
import errno
import json
import logging
import os
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal, Mapping, Protocol, Sequence

log = logging.getLogger(__name__)

BUILD_NO_RUN_STATES = ("skipped", "not_run")

_DIR_FSYNC_TOLERATED = {errno.EINVAL, errno.EOPNOTSUPP,
                        getattr(errno, "ENOTSUP", errno.EOPNOTSUPP),
                        errno.EACCES, errno.EPERM, errno.EISDIR, errno.EBADF}


class CIOpError(RuntimeError):
    """The build-op ledger is unusable or the recovery contract escalated."""


class CIClient(Protocol):  # pragma: no cover - structural typing only
    def create_build(self, *, branch: str, commit: str, message: str,
                     meta_data: Mapping[str, str]) -> dict: ...
    def get_build(self, build_id: str) -> dict: ...
    def find_builds_by_meta(self, key: str, value: str) -> list[dict]: ...
    def cancel_build(self, build_id: str) -> dict: ...
    def get_job_log(self, build_id: str, job_id: str) -> str: ...


# ── build-op ledger ──────────────────────────────────────────────────────────

@dataclass
class BuildOp:
    op_id: str
    run_id: str
    purpose: str            # gate | initial | retry | rebuild
    branch: str
    commit: str
    state: Literal["intent", "created", "cancelled"] = "intent"
    build_id: str = ""
    build_url: str = ""
    created_at: float = field(default_factory=time.time)

    def path(self, ops_dir: Path) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,100}", self.op_id):
            raise CIOpError(f"unsafe op_id for a ledger filename: "
                            f"{self.op_id!r}")
        return Path(ops_dir) / f"{self.op_id}.json"


def _durable_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    try:
        dfd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except OSError as e:
        if e.errno not in _DIR_FSYNC_TOLERATED:
            raise CIOpError("build-op ledger fsync failed — durability "
                            "cannot be guaranteed") from e


def load_ops(ops_dir: Path) -> list[BuildOp]:
    out: list[BuildOp] = []
    ops_dir = Path(ops_dir)
    if not ops_dir.is_dir():
        return out
    for p in sorted(ops_dir.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            op = BuildOp(**data)
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as e:
            raise CIOpError(f"corrupt build-op record {p}: {e}") from e
        if op.state not in ("intent", "created", "cancelled"):
            raise CIOpError(f"corrupt build-op record {p}: "
                            f"unknown state {op.state!r}")
        out.append(op)
    return out


def create_build_guarded(client: CIClient, ops_dir: Path, *,
                         op_id: str, run_id: str, purpose: str,
                         branch: str, commit: str, message: str,
                         repoll_attempts: int = 3,
                         repoll_delay: float = 60.0,
                         sleep: Callable[[float], None] = time.sleep) -> BuildOp:
    """Durable intent → API create (op-id stamped) → durable created.

    Re-entry with an existing intent record RECOVERS instead of re-creating:
    the provider is searched for a build carrying exactly this op id; one
    match adopts it; zero matches re-poll `repoll_attempts` times (eventual
    consistency) then ESCALATE; multiple matches ESCALATE. Uncertainty never
    creates a second build."""
    op = BuildOp(op_id=op_id, run_id=run_id, purpose=purpose,
                 branch=branch, commit=commit)
    path = op.path(ops_dir)
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        existing = BuildOp(**data)
        # an op id names ONE operation: re-entry with different parameters
        # is a caller bug — adopting the old build under new intent would
        # silently monitor the wrong world
        mismatch = [f"{k}: {getattr(existing, k)!r} != {v!r}"
                    for k, v in (("run_id", run_id), ("purpose", purpose),
                                 ("branch", branch), ("commit", commit))
                    if getattr(existing, k) != v]
        if mismatch:
            raise CIOpError(
                f"build-op {op_id}: recorded identity differs from this "
                f"request ({'; '.join(mismatch)}) — op ids are single-use, "
                "refusing to adopt")
        if existing.state == "created" and existing.build_id:
            return existing
        if existing.state != "intent":
            # cancelled (or any other terminal) op is CONSUMED — recovery
            # must never resurrect it to "created"
            raise CIOpError(
                f"build-op {op_id}: state {existing.state!r} is terminal — "
                "a new operation needs a new op id")
        # crash between intent and acknowledgment: recover by exact op id
        for attempt in range(1, max(1, repoll_attempts) + 1):
            matches = client.find_builds_by_meta("imx_op_id", op_id)
            if len(matches) == 1:
                existing.state = "created"
                existing.build_id = str(matches[0].get("id", ""))
                existing.build_url = str(matches[0].get("web_url", ""))
                _durable_write(path, asdict(existing))
                return existing
            if len(matches) > 1:
                raise CIOpError(
                    f"build-op {op_id}: {len(matches)} builds carry this op "
                    "id — human review required, refusing to guess")
            if attempt < repoll_attempts:
                sleep(repoll_delay)
        raise CIOpError(
            f"build-op {op_id}: intent recorded but no build carries the op "
            "id after re-polling — the create may have half-happened; "
            "human review required, refusing to re-create")

    _durable_write(path, asdict(op))
    build = client.create_build(
        branch=branch, commit=commit, message=message,
        meta_data={"imx_op_id": op_id, "imx_run_id": run_id})
    op.state = "created"
    op.build_id = str(build.get("id", ""))
    op.build_url = str(build.get("web_url", ""))
    _durable_write(path, asdict(op))
    return op


def cancel_build_guarded(client: CIClient, ops_dir: Path, op_id: str) -> bool:
    """Cancellation is allowed ONLY for op-recorded builds (never a build
    this run cannot prove it created)."""
    for op in load_ops(ops_dir):
        if op.op_id == op_id and op.state == "created" and op.build_id:
            client.cancel_build(op.build_id)
            op.state = "cancelled"
            _durable_write(op.path(ops_dir), asdict(op))
            return True
    return False


# ── monitor core ─────────────────────────────────────────────────────────────

@dataclass
class JobResult:
    name: str
    job_id: str
    state: str
    exit_status: int = 0
    classification: str = ""       # passed|failed|ignored|budget_timeout|...


@dataclass
class MonitorOutcome:
    build_state: str
    jobs: list[JobResult] = field(default_factory=list)

    @property
    def no_run(self) -> bool:
        return self.build_state in BUILD_NO_RUN_STATES

    @property
    def failed_jobs(self) -> list[JobResult]:
        return [j for j in self.jobs if j.classification == "failed"]

    @property
    def incomplete_jobs(self) -> list[JobResult]:
        """Jobs that never reached a per-job terminal state inside a
        terminal build (running/waiting/canceled/blocked/unknown) —
        STRUCTURAL, never counted as passed."""
        return [j for j in self.jobs if j.classification == "incomplete"]


@dataclass(frozen=True)
class CIClassifySpec:
    """Adapter data: which job names/log contents are ignorable."""

    ignorable_name_patterns: Sequence[str] = ()
    ignorable_log_patterns: Sequence[str] = ()


def monitor_build(client: CIClient, build_id: str, *,
                  spec: CIClassifySpec,
                  poll_sec: float = 60.0,
                  timeout_sec: float = 4 * 3600,
                  sleep: Callable[[float], None] = time.sleep,
                  now: Callable[[], float] = time.monotonic) -> MonitorOutcome:
    """Poll to a terminal build state; classify jobs deterministically:
    no-run build states are TERMINAL (never treated as failure or success —
    the caller escalates); ignorable jobs/logs are recorded `ignored`;
    budget-timeout kills are `budget_timeout` (an operator problem, never a
    code-debug dispatch); the rest split passed/failed by exit status."""
    deadline = now() + timeout_sec
    terminal = ("passed", "failed", "canceled", "cancelled", "blocked",
                *BUILD_NO_RUN_STATES)
    while True:
        build = client.get_build(build_id)
        state = str(build.get("state", ""))
        if state in terminal:
            break
        if now() > deadline:
            state = "monitor_timeout"
            break
        sleep(poll_sec)

    outcome = MonitorOutcome(build_state=state)
    if state in BUILD_NO_RUN_STATES:
        return outcome
    for job in build.get("jobs", []) or []:
        name = str(job.get("name", "") or "")
        if not name:
            continue
        raw_exit = job.get("exit_status")
        jr = JobResult(name=name, job_id=str(job.get("id", "")),
                       state=str(job.get("state", "")),
                       exit_status=int(raw_exit or 0))
        if any(re.search(p, name) for p in spec.ignorable_name_patterns):
            jr.classification = "ignored"
        elif jr.state not in ("passed", "finished", "failed", "timed_out") \
                or (jr.state == "finished" and raw_exit is None):
            # a terminal BUILD can still carry non-terminal or torn JOBS
            # (running, waiting, canceled, blocked, unknown, or a finished
            # job whose exit_status never landed) — a missing exit code is
            # NOT zero; incomplete is structural, never "passed"
            jr.classification = "incomplete"
        elif jr.state == "passed" or jr.exit_status == 0 and \
                jr.state not in ("failed", "timed_out"):
            jr.classification = "passed"
        else:
            log_text = client.get_job_log(build_id, jr.job_id)
            if any(re.search(p, log_text)
                   for p in spec.ignorable_log_patterns):
                jr.classification = "ignored"
            elif jr.state == "timed_out" and is_budget_timeout(log_text):
                jr.classification = "budget_timeout"
            else:
                jr.classification = "failed"
        outcome.jobs.append(jr)
    return outcome


# ── pure log classifiers (parent-verbatim) ───────────────────────────────────

_BK_TS_RE = re.compile(r"\x1b_bk;t=(\d+)\x07")
_ISO_TS_PARSE_RE = re.compile(
    r"\[(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})Z?\]")
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
_CANCEL_MARKERS = (
    "Received cancellation signal",
    "Exceeded maximum job timeout",
    "The command was interrupted by a signal",
)
_BK_MARKER_RE = re.compile(r"\x1b?_bk;t=\d+\x07?")
_ISO_TS_RE = re.compile(r"\[\d{4}-\d{2}-\d{2}T[\d:.]+Z?\]\s*")
_FLOAT_RE = re.compile(r"\d+\.\d+")


def _log_timestamps(segment: str) -> list[float]:
    ts = [int(m.group(1)) / 1000.0 for m in _BK_TS_RE.finditer(segment)]
    if ts:
        return ts
    out: list[float] = []
    for m in _ISO_TS_PARSE_RE.finditer(segment):
        y, mo, d, h, mi, s = (int(g) for g in m.groups())
        out.append(float(calendar.timegm((y, mo, d, h, mi, s, 0, 0, 0))))
    return out


def is_budget_timeout(log_text: str) -> bool:
    """A timed_out job killed by its minutes budget while tests were still
    PASSING (needs a bigger budget or a job split, never a code-debug agent):
    cancellation banner present, ≥1 PASSED and no FAILED before the kill,
    and output within 5 min of the kill (a hang shows a long silent gap)."""
    if not log_text:
        return False
    cancel_pos = -1
    for marker in _CANCEL_MARKERS:
        cancel_pos = log_text.find(marker)
        if cancel_pos != -1:
            break
    if cancel_pos == -1:
        return False
    body = _ANSI_RE.sub("", log_text[:cancel_pos])
    if not re.search(r"\bPASSED\b", body):
        return False
    if re.search(r"\bFAILED\b", body):
        return False
    kill_ts = _log_timestamps(log_text)
    if not kill_ts:
        return True
    output_ts = _log_timestamps(log_text[:max(0, cancel_pos - 40)])
    if not output_ts:
        return False
    return (max(kill_ts) - output_ts[-1]) <= 300.0


def normalize_log_line(line: str) -> str:
    """Strip run-specific noise so the same failure compares equal."""
    line = _BK_MARKER_RE.sub("", line)
    line = _ANSI_RE.sub("", line)
    line = _ISO_TS_RE.sub("", line)
    line = _FLOAT_RE.sub("<N>", line)
    return line.strip()


def extract_failed_test_ids(log_text: str) -> set[str]:
    """pytest node ids (`path::Class::test[param]`) from FAILED lines."""
    ids: set[str] = set()
    for line in log_text.split("\n"):
        if "FAILED" not in line or "::" not in line:
            continue
        m = re.search(r"([\w./-]+\.py::[\w:]+(?:\[[^\]]*\])?)",
                      normalize_log_line(line))
        if m:
            ids.add(m.group(1))
    return ids


def extract_error_signature(log_text: str,
                            extra_exception_names: Sequence[str] = ()) -> str:
    """Key error lines, normalized so two runs of one failure compare equal.
    Repo-specific exception class names arrive as adapter data."""
    base = (r"RuntimeError|AssertionError|TypeError|ValueError"
            r"|ModuleNotFoundError|ImportError|CalledProcessError"
            r"|torch\.OutOfMemoryError|CUDA out of memory"
            r"|exit status|SyntaxError|KeyError|AttributeError")
    names = "|".join([base, *map(re.escape, extra_exception_names)])
    rx = re.compile(rf".*({names}).*")
    lines = log_text.split("\n")
    sig_lines = [n for n in (normalize_log_line(ln) for ln in lines)
                 if n and rx.match(n)]
    failures = [normalize_log_line(ln) for ln in lines
                if "FAILED" in ln and "::" in ln]
    result = sig_lines[-3:] if sig_lines else []
    if failures:
        result.extend(failures[-3:])
    return "\n".join(result[-8:])
