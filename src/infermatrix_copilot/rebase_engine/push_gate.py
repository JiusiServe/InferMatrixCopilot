"""`rebase.push_gate` decision — Rev 8 §2.3's failure taxonomy, computed
deterministically from substate before any push.

- STRUCTURAL failures always block (unless `push_with_failures=true`,
  explicit and logged): failed modules, red precommit the run introduced,
  and phase-3 INFRASTRUCTURE failures (harness crashes, timeouts, missing
  dependencies, corrupt/empty manifest, agent dispatch failures) — these
  are never classified as ordinary test failures. A precommit red that
  PRE-EXISTS the run (`failed_preexisting`: the same command is red on
  the pre-run baseline tree) passes through FLAGGED instead — repo-wide
  debt the run did not create must not gate every push forever (live
  full run 2026-08-23).
- TEST ASSERTION failures pass through FLAGGED (parent-parity CI-feedback
  workflow); `strict_push_gate=true` makes them blocking.
- Blocking ⇒ FORBIDDEN ⇒ the run terminates per the transition table
  (blocked / exit 3). Vacuous in report_only/local_ci.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .modes import resolve_push_gate_conflict


@dataclass(frozen=True)
class GateDecision:
    allowed: bool
    reasons: tuple[str, ...] = ()
    flagged: tuple[str, ...] = ()   # pass-through test failures, surfaced


def _structural_failures(substate: Mapping) -> list[str]:
    out: list[str] = []
    for module, spec in (substate.get("modules") or {}).items():
        if (spec or {}).get("status") == "failed":
            out.append(f"module {module} failed")
    precommit = ((substate.get("tests") or {}).get("precommit") or {})
    if precommit.get("result") == "failed":
        out.append("precommit red")
    infra = ((substate.get("tests") or {}).get("infra_failures") or [])
    out.extend(f"phase-3 infrastructure failure: {i}" for i in infra)
    if substate.get("manifest_empty"):
        out.append("test manifest empty/corrupt")
    return out


def _assertion_failures(substate: Mapping) -> list[str]:
    pipeline = ((substate.get("tests") or {}).get("pipeline") or {})
    out = [f"test failure: {t}"
           for t in (pipeline.get("failed_tests") or [])]
    precommit = ((substate.get("tests") or {}).get("precommit") or {})
    if precommit.get("result") == "failed_preexisting":
        out.append("precommit red pre-exists the run (baseline red too)")
    return out


def evaluate_push_gate(substate: Mapping, params: Mapping) -> GateDecision:
    """The gate ruling. Raises ModeConflictError on the
    strict+with-failures conflict (Decision 3) before any evaluation."""
    resolve_push_gate_conflict(params)
    structural = _structural_failures(substate)
    assertions = _assertion_failures(substate)

    if structural and not params.get("push_with_failures"):
        return GateDecision(False, reasons=tuple(structural),
                            flagged=tuple(assertions))
    if assertions and params.get("strict_push_gate"):
        return GateDecision(False, reasons=tuple(
            f"strict gate: {a}" for a in assertions))
    return GateDecision(True, flagged=tuple(assertions),
                        reasons=tuple(f"pushed despite (explicit): {s}"
                                      for s in structural))
