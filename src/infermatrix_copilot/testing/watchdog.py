"""Two-tier log watchdog — port of the rebase agent's test_watchdog.sh.

The target engine can fail silently (internal errors that never make pytest
exit), so a watchdog tails the test log while pytest runs:

* Tier 1 — catastrophic patterns: kill immediately, no review.
* Tier 2 — broad error patterns: strip noise, then ask a cheap reviewer
  (KILL / CONTINUE); **timeouts and missing verdicts default to CONTINUE** —
  wedging a run on a warning is worse than missing a kill.

Patterns are data (`WatchdogPatterns.from_yaml`, adapter-side); the reviewer,
killer, and decision recorder are injected so the logic tests offline.
Matching semantics preserved from the shell: tier matching case-insensitive,
noise filtering case-sensitive, simulation allowlist fixed-substring, and the
matched line reported is the LAST match in the 150-line tail.
"""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

TAIL_LINES = 150
REPORT_TAIL_LINES = 300


@dataclass
class WatchdogPatterns:
    critical: list[str]
    review: list[str]
    simulation_allowlist: list[str]
    noise: list[str]
    simulated_test_name: str
    pytest_header: str

    def __post_init__(self):
        self._critical = [re.compile(p, re.I) for p in self.critical]
        self._review = [re.compile(p, re.I) for p in self.review]
        self._noise = [re.compile(p) for p in self.noise]  # case-sensitive
        self._sim_name = re.compile(self.simulated_test_name, re.I)
        self._header = re.compile(self.pytest_header)

    @classmethod
    def from_yaml(cls, path: Path, overlay: Path | None = None
                  ) -> "WatchdogPatterns":
        """Load the adapter seed file; `overlay` (runtime-learned noise) only
        ever appends to `noise` — learning may silence, never sharpen."""
        import yaml

        doc = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        if overlay and Path(overlay).exists():
            extra = yaml.safe_load(Path(overlay).read_text(encoding="utf-8")) or {}
            doc["noise"] = list(doc.get("noise", [])) + list(extra.get("noise", []))
        return cls(
            critical=doc.get("critical", []), review=doc.get("review", []),
            simulation_allowlist=doc.get("simulation_allowlist", []),
            noise=doc.get("noise", []),
            simulated_test_name=doc.get("simulated_test_name", r"(?!x)x"),
            pytest_header=doc.get("pytest_header", r"(?!x)x"),
        )

    # -- shell-equivalent predicates --
    def last_match(self, lines: list[str], tier: str) -> Optional[str]:
        pats = self._critical if tier == "critical" else self._review
        matched = [ln for ln in lines if any(p.search(ln) for p in pats)]
        return matched[-1] if matched else None

    def is_noise(self, line: str) -> bool:
        return any(p.search(line) for p in self._noise)

    def strip_noise(self, lines: list[str]) -> list[str]:
        return [ln for ln in lines if not self.is_noise(ln)]

    def is_simulated(self, line: str, test_name: str = "") -> bool:
        if any(s in line for s in self.simulation_allowlist):
            return True
        if test_name and self._sim_name.search(test_name):
            return True
        return bool(self._header.search(line))


@dataclass
class WatchdogResult:
    triggered: bool = False
    tier: int = 0
    matched_line: str = ""
    decisions: list[dict] = field(default_factory=list)


class LogWatchdog:
    """Poll a growing log; kill the test tree on a confirmed engine failure.

    Injected collaborators (all optional, so unit tests run offline):
    `review_fn(test_name, snippet) -> "KILL"|"CONTINUE"` — the Tier-2 verdict
    (caller wraps its own timeout; any exception or unknown reply is
    CONTINUE); `kill_fn(pid)` — terminate the test tree; `record_fn(pattern,
    verdict, test)` — the watchdog-learn decision log; `report_fn(test_name,
    trigger, log_tail) -> None` — post-mortem writer."""

    def __init__(self, patterns: WatchdogPatterns, log_file: Path, pid: int,
                 test_name: str, *, check_interval: float = 10.0,
                 review_fn: Callable[[str, str], str] | None = None,
                 kill_fn: Callable[[int], None] | None = None,
                 record_fn: Callable[[str, str, str], None] | None = None,
                 report_fn: Callable[[str, str, str], None] | None = None,
                 pid_alive: Callable[[int], bool] | None = None):
        self.patterns = patterns
        self.log_file = Path(log_file)
        self.pid = pid
        self.test_name = test_name
        self.check_interval = check_interval
        self.review_fn = review_fn
        self.kill_fn = kill_fn or self._default_kill
        self.record_fn = record_fn or (lambda *a: None)
        self.report_fn = report_fn or (lambda *a: None)
        self.pid_alive = pid_alive or self._default_alive
        self.result = WatchdogResult()
        self._stop = threading.Event()
        self._last_size = 0
        self._thread: threading.Thread | None = None

    # -- one poll cycle, extracted for deterministic tests --
    def check_once(self) -> bool:
        """Inspect the log tail once. Returns True when the watchdog killed
        (the caller's loop should stop)."""
        if not self.log_file.exists():
            return False
        size = self.log_file.stat().st_size
        if size == self._last_size:
            return False
        self._last_size = size
        tail = self._tail(TAIL_LINES)

        # Tier 1 — instant kill
        line = self.patterns.last_match(tail, "critical")
        if line is not None:
            if self.patterns.is_simulated(line, self.test_name):
                pass  # ignored (test-simulated); fall through to Tier 2
            else:
                self._kill(1, line)
                return True

        # Tier 2 — noise-stripped, reviewer-confirmed
        filtered = self.patterns.strip_noise(tail)
        line = self.patterns.last_match(filtered, "review")
        if line is None:
            return False
        if self.patterns.is_simulated(line, self.test_name):
            return False
        if self.patterns.is_noise(line):
            return False
        if self.review_fn is None:
            return False  # no reviewer available: never kill on Tier 2 alone
        verdict = self._reviewed_verdict(line, "\n".join(tail))
        self.record_fn(line, verdict, self.test_name)
        self.result.decisions.append({"pattern": line, "verdict": verdict})
        if verdict == "KILL":
            self._kill(2, line)
            return True
        return False

    def _reviewed_verdict(self, line: str, snippet: str) -> str:
        try:
            raw = (self.review_fn(self.test_name, snippet) or "").upper()
        except Exception:
            return "CONTINUE"  # reviewer stall/failure never wedges the run
        found = re.findall(r"(KILL|CONTINUE)", raw)
        return found[-1] if found else "CONTINUE"

    def _kill(self, tier: int, matched_line: str) -> None:
        self.result.triggered = True
        self.result.tier = tier
        self.result.matched_line = matched_line
        # Mark the test log itself so post-mortem readers see the cause
        # without cross-referencing the watchdog report (shell parity format).
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"\n[watchdog/kill] tier={tier} test={self.test_name} "
                        f"pid={self.pid}\n"
                        f"[watchdog/kill] matched: {matched_line}\n")
        except OSError:
            pass
        self.kill_fn(self.pid)
        trigger = (f"Critical pattern: `{matched_line}`" if tier == 1
                   else f"Agent-reviewed error: `{matched_line}`")
        self.report_fn(self.test_name, trigger,
                       "\n".join(self._tail(REPORT_TAIL_LINES)))

    def _tail(self, n: int) -> list[str]:
        try:
            return self.log_file.read_text(encoding="utf-8",
                                           errors="replace").splitlines()[-n:]
        except OSError:
            return []

    # -- background thread --
    def start(self) -> "LogWatchdog":
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self

    def _loop(self) -> None:
        while not self._stop.is_set() and self.pid_alive(self.pid):
            if self._stop.wait(self.check_interval):
                break
            if self.check_once():
                break

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=30)

    @staticmethod
    def _default_kill(pid: int) -> None:
        from .process_tree import kill_tree
        kill_tree([pid])

    @staticmethod
    def _default_alive(pid: int) -> bool:
        import os
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
