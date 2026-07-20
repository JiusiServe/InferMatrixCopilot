#!/usr/bin/env python3
"""Val-split campaign driver (eval plan v3, all review rounds folded).

Stages, each ledger-reserved (derivable hard max) then settled to actual:
  a0-judge   re-judge existing copilot_v2_t4_r{1,2,3} val outputs
  a1-gen     generate copilot_v3_r{1,2,3}   (MOA_WHEN=off)
  a1-judge   judge them
  a2-gen     generate copilot_v3_moa_r{1,2,3} (MOA_WHEN=always)
  a2-judge   judge them
Provenance is asserted before every stage; every replicate is
validate_replicate-gated; invalid ⇒ retry judge once, else marked .invalid.

Hard-max derivations (round-6 #5 — request-level ceilings, not estimates):
  generation/item: <=60 llm calls x 16k out-tokens x $1.10/M (deepseek out)
                   + MoA cap $1.50 when MOA on  => $1.20 / $2.70 per item
  judging/verdict: 1 call x 8k out x Sonnet $15/M + ~50k in x $3/M => $0.30

Usage: run_campaign.py <stage>   (stages above, run in order)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
DS = HERE.parent                      # eval/dataset
ROOT = DS.parent.parent
PY = "/rebase/.venv/bin/python"

sys.path.insert(0, str(HERE))
import campaign_ledger as ledger      # noqa: E402
from validate_replicate import validate  # noqa: E402

GEN_ITEM_MAX = 1.20
GEN_ITEM_MAX_MOA = 2.70
JUDGE_VERDICT_MAX = 0.30
A0_ARMS = [f"copilot_v2_t4_r{k}" for k in (1, 2, 3)]
A1_ARMS = [f"copilot_v3_r{k}" for k in (1, 2, 3)]
A2_ARMS = [f"copilot_v3_moa_r{k}" for k in (1, 2, 3)]
MOA_MEMBERS = ["mimo-v2.5", "qwen3.6-plus"]


def _assert_provenance() -> None:
    r = subprocess.run([PY, str(HERE / "snapshot_provenance.py"), "--assert"])
    if r.returncode != 0:
        raise SystemExit("provenance drift — stop the campaign")


def _settle_actual_generation(rid: str, arm: str) -> float:
    out = subprocess.run(
        [PY, str(DS / "aggregate_costs.py"), str(DS / "arms" / arm)],
        capture_output=True, text=True).stdout
    try:
        usd = float(json.loads(out).get(
            "attempt_service_totals", {}).get("usd") or 0.0)
    except (ValueError, json.JSONDecodeError):
        usd = 0.0
    ledger.settle(rid, usd, note=f"gen {arm}")
    return usd


def _generate(arm: str, moa: bool) -> None:
    env = dict(os.environ, ARM_OUT=arm,
               MOA_WHEN="always" if moa else "off",
               PR_CONTEXT_MODE="no_discussion")
    rid = f"gen-{arm}"
    per_item = GEN_ITEM_MAX_MOA if moa else GEN_ITEM_MAX
    if not ledger.reserve(rid, 10 * per_item, note=f"generate {arm}"):
        raise SystemExit(f"ledger refused {rid} — stop")
    t0 = time.time()
    r = subprocess.run([PY, str(DS / "run_copilot_arm.py"), "val"],
                       env=env, cwd=str(ROOT))
    usd = _settle_actual_generation(rid, arm)
    print(f"[campaign] {arm}: rc={r.returncode} usd={usd:.3f} "
          f"wall={time.time() - t0:.0f}s", flush=True)


def _judge(arm: str, moa: bool) -> None:
    jdir = DS / "judgments" / f"val_{arm}"
    rid = f"judge-{arm}"
    if not ledger.reserve(rid, 30 * JUDGE_VERDICT_MAX, note=f"judge {arm}"):
        raise SystemExit(f"ledger refused {rid} — stop")
    for attempt in (1, 2):
        env = dict(os.environ, SPLIT="val",
                   ARM_A_DIR=str(DS / "arms" / arm), JUDGE_OUT=str(jdir))
        subprocess.run([PY, str(DS / "judge_val.py")], env=env, cwd=str(DS))
        errs = validate(DS / "arms" / arm, jdir,
                        MOA_MEMBERS if moa else None)
        if not errs:
            break
        print(f"[campaign] {arm} judge attempt {attempt}: "
              f"{len(errs)} problems: {errs[:4]}", flush=True)
    # settle at hard max proxy: judge spans aren't traced locally (headless
    # CLI) — count verdict files actually produced this run at the ceiling
    n = len(list(jdir.glob("*.json")))
    ledger.settle(rid, min(n, 30) * JUDGE_VERDICT_MAX, note=f"judge {arm} n={n}")
    if errs:
        print(f"[campaign] {arm}: STILL INVALID after retry — {errs[:6]}",
              flush=True)
        raise SystemExit(1)
    print(f"[campaign] {arm}: judged VALID ({n} verdicts)", flush=True)


def main() -> None:
    stage = sys.argv[1] if len(sys.argv) > 1 else ""
    ledger.earmark_final()
    _assert_provenance()
    if stage == "a0-judge":
        for arm in A0_ARMS:
            _judge(arm, moa=False)
    elif stage == "a1-gen":
        for arm in A1_ARMS:
            _generate(arm, moa=False)
    elif stage == "a1-judge":
        for arm in A1_ARMS:
            _judge(arm, moa=False)
    elif stage == "a2-gen":
        for arm in A2_ARMS:
            _generate(arm, moa=True)
    elif stage == "a2-judge":
        for arm in A2_ARMS:
            _judge(arm, moa=True)
    else:
        raise SystemExit(__doc__)
    print("[campaign] stage complete:", stage, "| ledger:", ledger.totals(),
          flush=True)


if __name__ == "__main__":
    main()
