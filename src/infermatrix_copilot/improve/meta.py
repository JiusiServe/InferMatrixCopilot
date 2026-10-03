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


# -- the engine measured against the benchmark (design §11.2) ---------------------------------

def case_version(case_dir: Path) -> str:
    """sha256 of case.json: the labels ARE the benchmark, so their file is
    the gold version an experiment freezes."""
    import hashlib

    return hashlib.sha256((case_dir / "case.json").read_bytes()).hexdigest()


def stage_case(meta_dir: Path, case: str, dest: Path) -> Path:
    """Copy ONE case (and the lint samples) into a shadow directory: the
    self-experiment's child reads only that copy. Nothing narrative travels
    with it — no doc/, no judgments — so the investigator cannot recite a
    report (§11.2, the blind-test rule)."""
    src = meta_dir / "cases" / case
    if not (src / "case.json").is_file():
        raise FileNotFoundError(f"no meta case {case!r} under {meta_dir}")
    target = dest / "cases" / case
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(src, target, ignore=shutil.ignore_patterns("index.db*", "*.md", "doc", "judgments"))
    lints = meta_dir / "lints"
    if lints.is_dir():
        if (dest / "lints").exists():
            shutil.rmtree(dest / "lints")
        shutil.copytree(lints, dest / "lints", ignore=shutil.ignore_patterns("index.db*"))
    forbidden = [str(p) for p in dest.rglob("*") if p.is_dir() and p.name in ("doc", "judgments")]
    if forbidden:
        raise RuntimeError(f"staged meta case carries narrative material: {forbidden}")
    return dest


def lint_recall(meta_dir: Path) -> tuple[float | None, dict[str, bool]]:
    """The Tier 1 catalogue's recall on the injected samples: the share of
    ``lints/<L##>/`` units on which that lint fires. None without samples."""
    from .lints import Baseline, run_lints

    hits: dict[str, bool] = {}
    for lint_id, units in lint_samples(meta_dir).items():
        store = TraceStore(meta_dir / "lints" / lint_id)
        for unit in units:
            found = {f.lint for f in run_lints(unit, store, Baseline())}
            hits[f"{lint_id}/{unit.unit_id}"] = lint_id in found
    if not hits:
        return None, hits
    return sum(hits.values()) / len(hits), hits


def run_case(sink: TraceStore, case: MetaCase, agents: dict, *, meta_dir: Path, max_cells: int = 40) -> dict:
    """Attribute every labelled cell of ONE case with the engine's own
    forensics role (two families when configured), compare with the human
    labels and write the ``outcome`` record the meta adapter reads
    (``meta_eval``: engine labels, human labels, agreement, kappa, lint
    recall). The trace context of the caller (the unit) is inherited."""
    from .forensics import Cell, attribute
    from .stats import cohen_kappa

    cells = [Cell(gold_id, case.unit.unit_id, "miss") for gold_id in sorted(case.labels)]
    attributions = attribute(case.store, {case.unit.unit_id: case.unit}, {case.item: case.gold}, cells,
                             agents=agents, max_cells=max_cells) if agents else []
    engine = {a.gold_id: a.stage for a in attributions}
    disputed = sorted(a.gold_id for a in attributions if a.disputed)
    human = {gid: case.labels[gid] for gid in sorted(case.labels)}
    scored = [gid for gid in human if engine.get(gid) not in (None, "S0")]
    agreement = (sum(1 for gid in scored if engine[gid] == human[gid]) / len(scored)) if scored else None
    kappa = None
    if len(scored) >= 2:
        try:
            kappa = cohen_kappa([human[g] for g in scored], [engine[g] for g in scored])
        except ValueError:
            kappa = None
    recall, hits = lint_recall(meta_dir)
    result = {"type": "meta_eval", "case": case.name, "item": case.item, "human": human, "engine": engine,
              "disputed": disputed, "agreement": agreement, "kappa": kappa, "lint_recall": recall,
              "lint_hits": hits, "families": sorted(agents), "cells": len(cells), "attributed": len(scored)}
    # Legacy agreement/kappa remain diagnostic; evolution uses full-denominator accuracy.
    result["accuracy"] = sum(engine.get(g) == human[g] and g not in disputed for g in human) / len(human) if human else None
    # the caller's unit context (the engine's forensics unit, item meta:<case>)
    # is inherited; `of` names the investigated unit
    sink.append("outcome", context={"of": case.unit.unit_id}, result=result)
    return result
