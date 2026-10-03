"""Operator tools for freezing historical traces and importing human annotations."""
from __future__ import annotations
import json
from pathlib import Path
import time
from .artifacts import ArtifactError, atomic_json, safe_path


def operate(args, store):
    name = safe_path(args.case)
    if "/" in name: raise ArtifactError("case must be one directory name")
    root = Path(args.meta_dir) / "cases" / name
    if args.action == "export":
        from .reader import units_between
        from .meta import export_case
        if root.exists(): raise ArtifactError("case already exists; choose a new immutable case")
        if not args.unit_id or not args.gold_file: raise ArtifactError("export needs --unit-id and --gold-file")
        unit = units_between(store, 0, time.time() + 3601).get(args.unit_id)
        if unit is None: raise ArtifactError("historical unit not found")
        from .gold import load_gold
        gold = load_gold(Path(args.gold_file))
        if gold.item != unit.item or gold.status != "curated": raise ArtifactError("gold must be curated for this unit item")
        export_case(store, unit, Path(args.gold_file), {}, root)
        data = json.loads((root / "case.json").read_text())
        data.update(split="development", label_source="unannotated")
        atomic_json(root / "case.json", data)
        return {"case": str(root), "annotation_required": True, "gold_ids": [g.gold_id for g in gold.entries]}
    if not args.labels_file or not args.human_verified:
        raise ArtifactError("annotate needs --labels-file and --human-verified; model labels are not accepted")
    from .gold import load_gold
    from .forensics import STAGES
    labels = json.loads(Path(args.labels_file).read_text())
    gold = load_gold(root / "gold.json")
    eligible = {g.gold_id for g in gold.entries}
    if not isinstance(labels, dict) or not labels or set(labels) - eligible or any(v not in STAGES for v in labels.values()):
        raise ArtifactError("labels must map eligible gold IDs to stage names S0–S10")
    data = json.loads((root / "case.json").read_text())
    data.update(labels=labels, label_source="human", split=args.split)
    atomic_json(root / "case.json", data)
    return {"case": str(root), "labelled_cells": len(labels), "split": args.split}
