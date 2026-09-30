"""The frozen meta-benchmark (design §11.2).

``eval/dataset/meta/`` holds what the engine is measured against and may only
read: historical forensics cases (the unit's trace records and blobs, the
curated gold, the HUMAN stage-of-loss label per miss cell) and, under
``lints/``, injected-defect samples for the Tier 1 catalogue. Cases are added
by human pull requests only; a fingerprint diff that touches this directory
refuses a self-experiment.

Layout::

    meta/cases/<case>/case.json      {"item", "workflow", "unit_id", "labels": {gold_id: stage}}
    meta/cases/<case>/records.jsonl  the unit's trace/1 records
    meta/cases/<case>/blobs/         the blobs those records reference (sha256.gz)
    meta/cases/<case>/gold.json      the curated gold for the item
    meta/lints/<lint>/records.jsonl  a unit that must trigger exactly that lint
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from ..trace_store import TraceStore
from .adapters import Gold
from .gold import load_gold
from .reader import Unit, unit_key, workflow_key

META_DIRNAME = "meta"


@dataclass
class MetaCase:
    name: str
    item: str
    workflow: str
    unit: Unit
    gold: Gold
    labels: dict[str, str]        # gold_id -> human stage label (miss cells only)
    store: TraceStore


def _unit_from(records: list[dict]) -> Unit:
    first = records[0]
    ctx = first.get("context") or {}
    workflow, declared = workflow_key(first)
    unit = Unit(unit_id=unit_key(first), workflow=workflow, playbook=str(ctx.get("playbook") or ""),
                step=str(ctx.get("step") or ""), declared=declared, item=str(ctx.get("item") or ""),
                fingerprint=str(ctx.get("fingerprint") or ""), records=sorted(records, key=lambda r: (r["at"], r["id"])))
    return unit


def load_cases(meta_dir: Path) -> list[MetaCase]:
    cases: list[MetaCase] = []
    for case_dir in sorted((meta_dir / "cases").glob("*")):
        if not (case_dir / "case.json").exists():
            continue
        meta = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
        records = [json.loads(line) for line in (case_dir / "records.jsonl").read_text(encoding="utf-8").splitlines()
                   if line.strip()]
        if not records:
            continue
        store = TraceStore(case_dir)          # blobs/ lives right there; records/ is not used
        unit = _unit_from(records)
        gold = load_gold(case_dir / "gold.json")
        cases.append(MetaCase(case_dir.name, str(meta.get("item") or unit.item), str(meta.get("workflow") or unit.workflow),
                              unit, gold, {str(k): str(v) for k, v in (meta.get("labels") or {}).items()}, store))
    return cases


def export_case(store: TraceStore, unit: Unit, gold_path: Path, labels: dict[str, str], dest: Path) -> Path:
    """Freeze one unit as a meta case: its records, the blobs they reference,
    the gold file and the human labels (written by a human via PR)."""
    dest.mkdir(parents=True, exist_ok=True)
    with (dest / "records.jsonl").open("w", encoding="utf-8") as fh:
        for r in unit.records:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    for r in unit.records:
        for ref in list((r.get("inputs") or {}).values()) + list((r.get("outputs") or {}).values()):
            digest = str(ref).removeprefix("sha256:")
            src = store.root / "blobs" / digest[:2] / f"{digest}.gz"
            if src.exists():
                target = dest / "blobs" / digest[:2] / f"{digest}.gz"
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, target)
    shutil.copy2(gold_path, dest / "gold.json")
    (dest / "case.json").write_text(json.dumps({"item": unit.item, "workflow": unit.workflow, "unit_id": unit.unit_id,
                                                "labels": labels}, ensure_ascii=False, indent=1), encoding="utf-8")
    return dest


def lint_samples(meta_dir: Path) -> dict[str, list[Unit]]:
    """``{lint_id: [units that must trigger it]}`` from ``meta/lints/``."""
    out: dict[str, list[Unit]] = {}
    for lint_dir in sorted((meta_dir / "lints").glob("L*")):
        for path in sorted(lint_dir.glob("*.jsonl")):
            records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            if records:
                out.setdefault(lint_dir.name, []).append(_unit_from(records))
    return out
