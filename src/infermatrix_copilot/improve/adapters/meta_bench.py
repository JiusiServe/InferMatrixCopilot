"""The engine's own outcome adapter (design §11.2): the frozen meta-benchmark.

A unit is one ``improve.forensics`` step call over one meta case
(item ``meta:<case>``). Gold = the case's HUMAN stage-of-loss labels, one
entry per labelled cell; the outcome = the ``meta_eval`` record the step
wrote (the engine's labels for the same cells). ``match()`` is a plain
comparison: hit when the engine's label equals the human's, disputed when
the two investigator families disagreed, unlabeled when the engine said S0
(it never guesses), miss otherwise. ``review_scores()`` carries Cohen's
kappa over the attributed cells and the Tier 1 catalogue's recall on the
injected lint samples, both computed by the step from human material, so
no judge is involved (``human_labelled``): the cross-family rule for
self-experiments holds by construction.
"""

from __future__ import annotations

from pathlib import Path

from ...trace_store import TraceStore
from ..reader import Unit
from . import FindingLabel, Gold, GoldEntry, Match, Outcome

ITEM_PREFIX = "meta:"


class MetaBenchAdapter:
    name = "meta_bench"
    descriptive_only = False
    human_labelled = True

    def __init__(self, *, meta_dir: str | Path = "eval/dataset/meta"):
        self.meta_dir = Path(meta_dir)

    def _case_dir(self, item: str) -> Path | None:
        if not item.startswith(ITEM_PREFIX):
            return None
        name = item[len(ITEM_PREFIX):]
        if not name or "/" in name or name.startswith("."):
            return None
        case_dir = self.meta_dir / "cases" / name
        return case_dir if (case_dir / "case.json").is_file() else None

    def gold(self, item: str) -> Gold | None:
        import json

        from ..meta import case_version

        case_dir = self._case_dir(item)
        if case_dir is None:
            return None
        labels = json.loads((case_dir / "case.json").read_text(encoding="utf-8")).get("labels") or {}
        if not labels:
            return None
        entries = tuple(GoldEntry(gold_id=str(gid), path="", concern=f"human stage label {stage}", kind="stage")
                        for gid, stage in sorted(labels.items()))
        return Gold(item=item, entries=entries, version=case_version(case_dir), status="curated")

    def fetch(self, unit: Unit, store: TraceStore) -> Outcome | None:
        records = store.query(kind="outcome", unit_id=unit.unit_id, limit=10_000)
        if not any((r.get("result") or {}).get("type") == "meta_eval" for r in records):
            return None
        return Outcome(unit.unit_id, tuple(records))

    @staticmethod
    def _eval(outcome: Outcome) -> dict | None:
        evals = outcome.of_type("meta_eval")
        return evals[-1] if evals else None

    def match(self, unit: Unit, gold: Gold, outcome: Outcome) -> list[Match]:
        rec = self._eval(outcome)
        if rec is None:
            return [Match(e.gold_id, "unlabeled") for e in gold.entries]
        res = rec.get("result") or {}
        engine, human = res.get("engine") or {}, res.get("human") or {}
        disputed = set(res.get("disputed") or [])
        out = []
        for e in gold.entries:
            got = engine.get(e.gold_id)
            if got is None or got == "S0":
                status = "unlabeled"
            elif e.gold_id in disputed:
                status = "disputed"
            elif got == human.get(e.gold_id):
                status = "hit"
            else:
                status = "miss"
            out.append(Match(e.gold_id, status, evidence=(rec["id"],)))
        return out

    def findings(self, unit: Unit, outcome: Outcome) -> list[FindingLabel]:
        return []

    def review_scores(self, unit: Unit, outcome: Outcome) -> dict[str, float] | None:
        rec = self._eval(outcome)
        if rec is None:
            return None
        res = rec.get("result") or {}
        scores = {}
        for key in ("kappa", "lint_recall", "agreement"):
            value = res.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                scores[key] = float(value)
        return scores or None
