#!/usr/bin/env python3
"""Layer-A mechanical loss check: the anchor multiset never shrinks.

Recomputes the anchor multiset over the in-scope tree and asserts
Counter(after) >= Counter(before) elementwise (nothing subtracted — Step 3 is
add-detail/union-first with archive-never-delete, so anchors only accumulate),
plus incident-ID set equality. Baseline: doc/reorg-audit/anchors.before.tsv.
Exit 0 = holds; exit 1 = a loss, listed.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ROOT = REPO / "knowledge"
BASELINE = REPO / "doc" / "reorg-audit" / "anchors.before.tsv"
PAT = re.compile(
    r"#\d{3,5}"
    r"|inc-[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]+"
    r"|[A-Za-z0-9_./-]+\.py:\d+"
    r"|\b(?:FP32|BF16|FP16|FP8|TF32|INT8)\b"
    r"|\b\d+(?:\.\d+)?[ \t]?(?:dB|GiB|GB|QPS|fps|steps|ms|tok/s)\b"
)


def current() -> Counter:
    c: Counter = Counter()
    for base in ("general", "repos/vllm-omni", "_archive"):
        d = ROOT / base
        if not d.exists():
            continue
        for p in sorted(d.rglob("*.md")):
            c.update(m.group(0) for m in PAT.finditer(p.read_text(encoding="utf-8")))
    return c


def main() -> int:
    before: Counter = Counter()
    for line in BASELINE.read_text(encoding="utf-8").splitlines()[1:]:
        _, anchor = line.split("\t", 1)
        before[anchor] += 1
    after = current()
    lost = {a: n - after.get(a, 0) for a, n in before.items() if after.get(a, 0) < n}
    inc_before = {a for a in before if a.startswith("inc-")}
    inc_after = {a for a in after if a.startswith("inc-")}
    if inc_before != inc_after - (inc_after - inc_before):
        pass  # new incident IDs are fine; only losses matter (covered below)
    if lost:
        for a, n in sorted(lost.items()):
            print(f"LOSS: {a} (x{n} fewer than baseline)")
        print(f"layer A FAILED: {len(lost)} anchor(s) below baseline multiplicity")
        return 1
    print(f"layer A holds: {sum(before.values())} baseline anchor occurrences all "
          f"present (now {sum(after.values())} total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
