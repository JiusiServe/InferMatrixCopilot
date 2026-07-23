#!/usr/bin/env python3
"""20-case PR-review campaign driver: 3 generation replicates over every
`pr_review` item in the dataset (10 train / 5 val / 5 test), judged blind
against the recorded CC+Opus baseline, with FULL trace capture.

Differences from the val campaign (`run_campaign.py`), all deliberate:

- **PR items only, all three splits** (`KINDS=pr_review`, splits train,val,test)
  — 20 items per replicate instead of 5 PRs + 5 issues.
- **Replicates run STRICTLY SEQUENTIALLY.** PR-time worktrees live at the
  shared path `~/.infermatrix-copilot/worktrees/<repo>-pr<N>`; two concurrent
  runs of the same PR can race `worktree remove --force` against a live read.
- **Payload capture on** (`AGENT_TRACE_IO=1`, `AGENT_TRACE_IO_FULL=1`): every
  run keeps trace.jsonl + run_trace.jsonl + events.jsonl, gated by
  `verify_traces.py` before the replicate is accepted.
- **Its own ledger** (`campaign_ledger_pr20.jsonl`): the val ledger is settled
  at $92.36 of its $150 ceiling and would refuse this campaign's reservations.
- **Knowledge-write watch**: skill-candidate files are snapshotted before and
  after, so anything a frozen-test item proposed is visible, not silent.

Leakage controls (asserted, never assumed): PR_CONTEXT_MODE=no_discussion keeps
the review discussion — which IS the ground truth — out of the prompt, and
validate_replicate demands the `PR-TIME TREE` note with the independently
frozen head SHA on every PR item.

Usage:
  run_pr20_campaign.py heads          freeze expected_pr_heads.json for 20 PRs
  run_pr20_campaign.py snapshot       provenance + skill-candidate baseline
  run_pr20_campaign.py gen <r>        generate replicate r (1..3)
  run_pr20_campaign.py judge <r>      judge replicate r
  run_pr20_campaign.py replicate <r>  gen + verify + judge for r
  run_pr20_campaign.py all            replicates 1..3, sequentially
  run_pr20_campaign.py status         ledger + progress
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
DS = HERE.parent                      # eval/dataset
ROOT = DS.parent.parent               # repo root
PY = sys.executable

# Both of these are read at MODULE IMPORT time by the modules below, so they
# must be in os.environ before the imports — putting them only in the subprocess
# env dict would leave the in-process snapshot()/ledger writing to the val
# campaign's files and silently overwrite another campaign's record.
os.environ.setdefault("CAMPAIGN_LEDGER", str(HERE / "campaign_ledger_pr20.jsonl"))
os.environ.setdefault("CAMPAIGN_CEILING_USD", "150.0")
os.environ.setdefault("PROVENANCE_OUT", str(HERE / "provenance_pr20.json"))

sys.path.insert(0, str(HERE))
import campaign_ledger as ledger              # noqa: E402
from snapshot_provenance import campaign_prs, freeze_heads, snapshot  # noqa: E402
from validate_replicate import validate       # noqa: E402

ARM = "copilot_v4_pr20"
JUDGE_PREFIX = "pr20"
REPLICATES = (1, 2, 3)

# Request-level hard maxima (not estimates), same derivation as the val
# campaign: generation <=60 llm calls x 16k out-tokens x $1.10/M deepseek out;
# judging 1 call x 8k out at Sonnet $15/M + ~50k in at $3/M.
GEN_ITEM_MAX = 1.20
JUDGE_VERDICT_MAX = 0.30

CANDIDATE_FILES = (
    ROOT / "skills" / "_candidates.json",
    ROOT / "adapters" / "vllm_omni" / "skills" / "_candidates.json",
)
CANDIDATE_SNAPSHOT = HERE / "skill_candidates_before.json"
PROVENANCE = HERE / "provenance_pr20.json"

# The campaign runs the shipped configuration with MoA OFF: that is the arm
# whose numbers `doc/EVAL-goal-report.md` records (A1), the shipped default
# `full` would engage MoA on every non-light PR at ~3x generation cost, and the
# report already measured MoA regressing grounding/completeness.
CAMPAIGN_ENV = {
    "PR_CONTEXT_MODE": "no_discussion",   # mandatory GT leakage control
    "MOA_WHEN": "off",
    "REVIEW_DEPTH": "auto",
    "ALLOW_POST": "0",
    "ALLOW_PUSH": "0",
    "AGENT_TRACE": "1",
    "AGENT_TRACE_IO": "1",
    "AGENT_TRACE_IO_FULL": "1",
    "KINDS": "pr_review",
    "PROVENANCE_OUT": str(PROVENANCE),
    "OMNI_REPO": os.environ.get("OMNI_REPO", "/rebase/vllm-omni"),
}


def stems() -> list[str]:
    return [f"pr{n}" for n in campaign_prs()]


def _env(**extra) -> dict:
    return {**os.environ, **CAMPAIGN_ENV, **{k: str(v) for k, v in extra.items()}}


def arm_dir(rep: int) -> Path:
    return DS / "arms" / f"{ARM}_r{rep}"


def judge_dir(rep: int) -> Path:
    return DS / "judgments" / f"{JUDGE_PREFIX}_{ARM}_r{rep}"


# ── stages ────────────────────────────────────────────────────────────────────
def stage_heads() -> int:
    """Freeze head SHAs for all 20 PRs. Existing entries are re-resolved and any
    change is REPORTED, never overwritten: a force-push since the val campaign
    means the affected item is not comparable to its recorded numbers."""
    r = freeze_heads()
    print(json.dumps({k: v for k, v in r.items() if k != "heads"}, indent=1))
    print(f"frozen heads: {len(r['heads'])}/{len(campaign_prs())}")
    if r["drift"]:
        print("!! HEAD DRIFT — frozen values kept; these items are NOT "
              "comparable to previously recorded numbers:", list(r["drift"]))
    if r["unresolved"]:
        print("!! UNRESOLVED (gh returned no commits):", r["unresolved"])
    return 1 if r["unresolved"] else 0


def _candidate_digest() -> dict:
    out = {}
    for p in CANDIDATE_FILES:
        out[str(p.relative_to(ROOT))] = (
            hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None)
    return out


def stage_snapshot() -> int:
    prov = snapshot()
    CANDIDATE_SNAPSHOT.write_text(json.dumps(_candidate_digest(), indent=1))
    print(json.dumps({k: prov[k] for k in
                      ("head", "tracked_diff_sha256",
                       "untracked_source_sha256")}, indent=1))
    print("skill-candidate baseline:", CANDIDATE_SNAPSHOT.name)
    return 0


def check_candidates() -> list[str]:
    """Any skill candidate written since the baseline — the one channel by which
    a frozen-test item could reach the knowledge base. Candidates are inert
    (`SkillStore.find` returns active skills only), but they must be visible."""
    if not CANDIDATE_SNAPSHOT.exists():
        return []
    before = json.loads(CANDIDATE_SNAPSHOT.read_text())
    now = _candidate_digest()
    return [k for k in now if before.get(k) != now[k]]


def stage_gen(rep: int) -> int:
    out = arm_dir(rep)
    rid = f"gen-r{rep}"
    n_items = len(campaign_prs())
    if not ledger.reserve(rid, n_items * GEN_ITEM_MAX, note=f"generate {out.name}"):
        print(f"ledger REFUSED {rid}: {ledger.totals()}")
        return 1
    t0 = time.time()
    r = subprocess.run(
        [PY, str(DS / "run_copilot_arm.py"), "train,val,test"],
        env=_env(ARM_OUT=out.name), cwd=str(ROOT))
    usd = _settle_generation(rid, out)
    print(f"[pr20] gen r{rep}: rc={r.returncode} usd=${usd:.3f} "
          f"wall={time.time() - t0:.0f}s", flush=True)
    return 0


def _settle_generation(rid: str, out: Path) -> float:
    res = subprocess.run([PY, str(DS / "aggregate_costs.py"), str(out)],
                         capture_output=True, text=True)
    try:
        usd = float(json.loads(res.stdout).get(
            "attempt_service_totals", {}).get("usd") or 0.0)
    except (ValueError, json.JSONDecodeError, AttributeError):
        usd = 0.0
    ledger.settle(rid, usd, note=f"gen {out.name}")
    return usd


def stage_verify(rep: int) -> int:
    out = arm_dir(rep)
    inv = HERE / f"trace_inventory_r{rep}.json"
    rc = subprocess.run([PY, str(HERE / "verify_traces.py"), str(out),
                         "--json", str(inv)]).returncode
    return rc


def stage_judge(rep: int) -> int:
    out, jdir = arm_dir(rep), judge_dir(rep)
    jdir.mkdir(parents=True, exist_ok=True)
    st = stems()
    rid = f"judge-r{rep}"
    n_verdicts = len(st) * 3
    if not ledger.reserve(rid, n_verdicts * JUDGE_VERDICT_MAX,
                          note=f"judge {out.name}"):
        print(f"ledger REFUSED {rid}: {ledger.totals()}")
        return 1
    errs: list[str] = []
    for attempt in (1, 2, 3):
        subprocess.run([PY, str(DS / "judge_val.py")],
                       env=_env(SPLIT="all_pr", ARM_A_DIR=str(out),
                                JUDGE_OUT=str(jdir)), cwd=str(DS))
        errs = validate(out, jdir, stems=st)
        if not errs:
            break
        print(f"[pr20] judge r{rep} attempt {attempt}: {len(errs)} problems: "
              f"{errs[:4]}", flush=True)
    n = len(list(jdir.glob("*.r*.json")))
    # judge spend is not locally traced (headless CLI) — settle produced
    # verdicts at the per-verdict ceiling; `_cost_usd` on each verdict is the
    # actual, aggregated in the report
    actual = 0.0
    for f in jdir.glob("*.r*.json"):
        try:
            actual += float(json.loads(f.read_text()).get("_cost_usd") or 0.0)
        except (OSError, ValueError, json.JSONDecodeError):
            pass
    ledger.settle(rid, actual or min(n, n_verdicts) * JUDGE_VERDICT_MAX,
                  note=f"judge {out.name} n={n}")
    if errs:
        print(f"[pr20] r{rep}: STILL INVALID after retries — {errs[:8]}")
        return 1
    print(f"[pr20] r{rep}: judged VALID ({n} verdicts, ${actual:.2f})")
    return 0


def stage_replicate(rep: int) -> int:
    for fn in (lambda: stage_gen(rep), lambda: stage_verify(rep),
               lambda: stage_judge(rep)):
        rc = fn()
        if rc:
            return rc
    moved = check_candidates()
    if moved:
        print(f"[pr20] !! skill candidates changed during r{rep}: {moved}")
    return 0


def stage_status() -> int:
    print("ledger:", json.dumps(ledger.totals(), indent=1))
    for rep in REPLICATES:
        a, j = arm_dir(rep), judge_dir(rep)
        n_md = len(list(a.glob("pr*.md"))) if a.exists() else 0
        n_v = len(list(j.glob("*.r*.json"))) if j.exists() else 0
        print(f"  r{rep}: arm {n_md}/{len(campaign_prs())} items, "
              f"judge {n_v}/{len(campaign_prs()) * 3} verdicts")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    stage, rest = args[0], args[1:]
    if stage == "heads":
        return stage_heads()
    if stage == "snapshot":
        return stage_snapshot()
    if stage == "status":
        return stage_status()
    if stage in ("gen", "judge", "verify", "replicate"):
        rep = int(rest[0]) if rest else 1
        return {"gen": stage_gen, "judge": stage_judge,
                "verify": stage_verify, "replicate": stage_replicate}[stage](rep)
    if stage == "all":
        for rep in REPLICATES:
            print(f"\n===== replicate {rep}/{len(REPLICATES)} =====", flush=True)
            rc = stage_replicate(rep)
            if rc:
                print(f"[pr20] replicate {rep} failed (rc={rc}) — stopping")
                return rc
        print("[pr20] campaign complete |", json.dumps(ledger.totals()))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
