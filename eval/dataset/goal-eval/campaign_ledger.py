#!/usr/bin/env python3
"""Append-only campaign spend ledger with preventive hard-max reservations
(eval plan v3 §ceilings + round-5/6 fixes).

Every paid event is appended AS IT HAPPENS (generation attempts incl. canaries,
invalid dirs, and failed invocations that produced no artifact; judge calls
incl. retries). Before each paid batch, `reserve()` atomically checks
settled + reserved + hard_max <= ceiling and REFUSES the batch otherwise —
no run-then-notice overshoot. Hard maxima are derived from request-level
ceilings (max_tokens x price), not estimates. The conditional final-
confirmation budget is EARMARKED at campaign start.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

LEDGER = Path(__file__).parent / "campaign_ledger.jsonl"
CEILING_USD = 150.0
FINAL_EARMARK_USD = 30.0   # reserved at start for the conditional confirmation


def _entries() -> list[dict]:
    if not LEDGER.exists():
        return []
    out = []
    for line in LEDGER.read_text().splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _append(rec: dict) -> None:
    rec["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def totals() -> dict:
    settled = reserved = 0.0
    open_res: dict[str, float] = {}
    earmark = 0.0
    for e in _entries():
        k = e.get("kind")
        if k == "settle":
            settled += float(e.get("usd") or 0.0)
            open_res.pop(e.get("rid", ""), None)
        elif k == "reserve":
            open_res[e.get("rid", "")] = float(e.get("hard_max_usd") or 0.0)
        elif k == "release":
            open_res.pop(e.get("rid", ""), None)
        elif k == "earmark":
            earmark = float(e.get("usd") or 0.0)
    reserved = sum(open_res.values())
    return {"settled": round(settled, 4), "reserved_open": round(reserved, 4),
            "earmark": earmark,
            "available": round(CEILING_USD - settled - reserved - earmark, 4)}


def earmark_final(usd: float = FINAL_EARMARK_USD) -> None:
    """Set aside the conditional confirmation budget before any spend."""
    if not any(e.get("kind") == "earmark" for e in _entries()):
        _append({"kind": "earmark", "usd": usd})


def release_earmark() -> None:
    _append({"kind": "earmark", "usd": 0.0})


def reserve(rid: str, hard_max_usd: float, note: str = "") -> bool:
    """Atomic-enough for our single-driver campaign (one process appends)."""
    t = totals()
    if hard_max_usd > t["available"]:
        _append({"kind": "refused", "rid": rid, "hard_max_usd": hard_max_usd,
                 "available": t["available"], "note": note})
        return False
    _append({"kind": "reserve", "rid": rid, "hard_max_usd": hard_max_usd,
             "note": note})
    return True


def settle(rid: str, usd: float, note: str = "") -> None:
    _append({"kind": "settle", "rid": rid, "usd": usd, "note": note})


def release(rid: str) -> None:
    _append({"kind": "release", "rid": rid})


if __name__ == "__main__":
    print(json.dumps(totals(), indent=1))
