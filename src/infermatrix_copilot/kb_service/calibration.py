"""Judge calibration: known-good and known-bad knowledge changes per repository.

A case is ``cases/<id>.json``::

    {"id": "...", "expected": "pass" | "reject", "note": "...",
     "base": {path: text}, "head": {path: text}, "evidence": [...]}

``base``/``head`` hold only the pages involved. The runner derives L1 blocks,
asks the pinned judge exactly as the gate does, and scores: every ``reject``
case must end in fail or human (never pass), and at most 20 % of ``pass``
cases may be rejected. A repository stays in shadow mode until its set passes,
and the set is re-run whenever the judge model or version changes.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from ..knowledge_service.l1 import check_changeset
from .gate import changes_between, check_consistency, judge_block

MAX_FALSE_REJECT = 0.20


@dataclass(frozen=True)
class CalibrationReport:
    cases: int
    bad_total: int
    bad_caught: int
    good_total: int
    good_rejected: int
    details: tuple[dict, ...]

    @property
    def passed(self) -> bool:
        if not self.bad_total or not self.good_total:
            return False
        return self.bad_caught == self.bad_total and \
            self.good_rejected / self.good_total <= MAX_FALSE_REJECT

    def to_dict(self) -> dict:
        return {"cases": self.cases, "bad_caught": f"{self.bad_caught}/{self.bad_total}",
                "good_rejected": f"{self.good_rejected}/{self.good_total}",
                "passed": self.passed, "details": list(self.details)}


def case_set_digest(directory: str | Path) -> str:
    """Identity of a case set: a passing calibration only counts for the exact
    cases it ran on."""
    digest = hashlib.sha256()
    for path in sorted(Path(directory).glob("cases/*.json")):
        digest.update(path.name.encode("utf-8") + b"\0" + path.read_bytes() + b"\0")
    return "sha256:" + digest.hexdigest()


def load_cases(directory: str | Path) -> list[dict]:
    cases = []
    for path in sorted(Path(directory).glob("cases/*.json")):
        case = json.loads(path.read_text(encoding="utf-8"))
        if case.get("expected") not in ("pass", "reject") or not case.get("head"):
            raise ValueError(f"malformed calibration case: {path}")
        cases.append(case)
    return cases


def run_calibration(directory: str | Path, *, gateway, judge) -> CalibrationReport:
    details = []
    bad_total = bad_caught = good_total = good_rejected = 0
    for case in load_cases(directory):
        base, head = case.get("base") or {}, case["head"]
        l1 = check_changeset(base, head, changes_between(base, head))
        verdicts = [judge_block(b, base=base, head=head, evidence=case.get("evidence") or [],
                                gateway=gateway, judge=judge) for b in l1.blocks]
        outcome = "pass"
        if not l1.ok or any(v.verdict == "fail" for v in verdicts):
            outcome = "fail"
        elif any(v.verdict == "human" for v in verdicts):
            outcome = "human"
        else:
            dirs = sorted({str(Path(b.path).parent) for b in l1.blocks})
            consistency = check_consistency(head, dirs, gateway=gateway, judge=judge)
            if any(c["verdict"] == "conflict" for c in consistency):
                outcome = "fail"
            elif any(c["verdict"] == "unsure" for c in consistency):
                outcome = "human"
        if case["expected"] == "reject":
            bad_total += 1
            bad_caught += outcome != "pass"
        else:
            good_total += 1
            good_rejected += outcome != "pass"
        details.append({"id": case["id"], "expected": case["expected"], "outcome": outcome,
                        "l1": [i.code for i in l1.issues],
                        "blocks": [{"rule_id": v.block.rule_id, "op": v.block.op,
                                    "verdict": v.verdict, "dimensions": v.dimensions} for v in verdicts]})
    return CalibrationReport(len(details), bad_total, bad_caught, good_total, good_rejected, tuple(details))
