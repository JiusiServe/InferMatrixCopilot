#!/usr/bin/env python3
"""Manifest completeness gate: every external source unit in
enrichment-baseline/skill-manifest.tsv is either PRESENT in its destination
page (a `^[<marker>]` provenance marker) or EXPLICITLY excluded with a reason.
Silent omission fails. Marker forms: `^[SK-<skill-name>]`, `^[DM-<id>]`,
`^[DOC-<name>]`, `^[CFG-<name>]`.

Exit 0 = complete; 1 = losses listed. Pass --allow-pending to only check rows
whose destination page already exists (used mid-flight between batches; the
final acceptance run uses the strict mode).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
BASE = REPO / "doc" / "reorg-audit" / "enrichment-baseline"


def marker_for(source_id: str) -> str:
    if source_id.startswith("DM-"):
        return "^[DM-" + source_id.split("-")[1] + "]"
    return f"^[{source_id}]"


def dest_page(dest: str) -> Path | None:
    if dest == "excluded":
        return None
    md = dest.split(".md")[0] + ".md"
    return REPO / md


def main() -> int:
    allow_pending = "--allow-pending" in sys.argv
    errors: list[str] = []
    checked = excluded = pending = 0
    lines = (BASE / "skill-manifest.tsv").read_text(encoding="utf-8").splitlines()
    for line in lines[1:]:
        source_id, _src, dest, note = (line.split("\t") + ["", "", ""])[:4]
        if dest == "excluded":
            excluded += 1
            if not note.strip():
                errors.append(f"excluded without a reason: {source_id}")
            continue
        page = dest_page(dest)
        if page is None or not page.exists():
            if allow_pending:
                pending += 1
                continue
            errors.append(f"destination page missing: {source_id} -> {dest}")
            continue
        text = page.read_text(encoding="utf-8")
        if marker_for(source_id) not in text:
            errors.append(f"marker {marker_for(source_id)} absent from {dest}")
            continue
        checked += 1
    for e in errors:
        print(f"LOSS: {e}")
    status = "FAILED" if errors else "complete"
    print(f"manifest {status}: {checked} present, {excluded} excluded, "
          f"{pending} pending, {len(errors)} losses")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
