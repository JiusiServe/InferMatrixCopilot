#!/bin/bash
# Clean-room frozen-test run: outputs/traces of BOTH arms are never shown to
# the operator and are deleted after aggregation. Only numeric aggregates
# survive, in judgments/TEST_CLEANROOM.md. All paths absolute.
set -u
DS=/rebase/vllm-omni-copilot/eval/dataset
cd "$DS"
TMP=$(mktemp -d /tmp/cleanroom.XXXXXX)
trap 'rm -rf "$TMP"' EXIT
for r in 1 2 3; do
  echo "[cleanroom] sweep replicate $r"
  ARM_OUT="$TMP/arm_r$r" /rebase/.venv/bin/python "$DS/run_copilot_arm.py" test \
    > /dev/null 2>&1 || true
  n=$(ls "$TMP/arm_r$r"/*.md 2>/dev/null | wc -l)
  echo "[cleanroom] replicate $r items: $n"
  [ "$n" -ge 10 ] || { echo "[cleanroom] ABORT: sweep produced $n items"; exit 1; }
done
for r in 1 2 3; do
  echo "[cleanroom] judging replicate $r"
  for attempt in 1 2 3; do
    SPLIT=test ARM_A_DIR="$TMP/arm_r$r" JUDGE_OUT="$TMP/judge_r$r" \
      /rebase/.venv/bin/python "$DS/judge_val.py" > /dev/null 2>&1 || true
    n=$(ls "$TMP/judge_r$r"/*.r*.json 2>/dev/null | wc -l)
    echo "[cleanroom] judge r$r verdicts: $n/30 (attempt $attempt)"
    [ "$n" -ge 30 ] && break
  done
done
/rebase/.venv/bin/python - "$TMP" <<'PYEOF'
import json, glob, sys
import statistics as st
from collections import defaultdict
TMP = sys.argv[1]

def load(d):
    dims = defaultdict(lambda: defaultdict(list)); wins = defaultdict(int); n = 0
    for f in glob.glob(f"{d}/*.r*.json"):
        v = json.load(open(f)); bl = v["_blinding"]; n += 1
        wins[bl.get(v.get("winner"), "tie")] += 1
        for side in ("x", "y"):
            arm = bl["X" if side == "x" else "Y"]
            for dim, val in (v.get(side) or {}).items():
                if isinstance(val, bool): val = float(val)
                if isinstance(val, (int, float)):
                    dims[arm][dim].append(float(val))
    return dims, wins, n

reps = [load(f"{TMP}/judge_r{r}") for r in (1, 2, 3)]
total = sum(n for _, _, n in reps)
L = ["# Frozen test — CLEAN-ROOM run (numeric aggregates only)", "",
     "Protocol: sweeps+judging entirely in a temp dir; outputs/traces of both",
     "arms never viewed by the operating agent; judge rationales discarded",
     "unread; all raw artifacts deleted after this aggregation. 3 arm",
     f"replicates, {total} blind verdicts (Sonnet 5).", "",
     "| dim | copilot (r1/r2/r3 -> mean) | baseline |", "|---|---|---|"]
dims_all = sorted({d for dd, _, _ in reps for a in dd.values() for d in a})
for d in dims_all:
    vals = [st.mean(dd["copilot_v2"][d]) for dd, _, _ in reps if dd["copilot_v2"].get(d)]
    base = st.mean([st.mean(dd["opus_baseline"][d]) for dd, _, _ in reps
                    if dd["opus_baseline"].get(d)])
    L.append(f"| {d} | " + "/".join(f"{v:.2f}" for v in vals)
             + f" -> **{st.mean(vals):.2f}** | {base:.2f} |")
L += ["", "Wins (copilot/baseline/tie): "
      + ", ".join(f"r{i+1} {w['copilot_v2']}/{w['opus_baseline']}/{w.get('tie', 0)}"
                  for i, (_, w, _) in enumerate(reps))]
open("/rebase/vllm-omni-copilot/eval/dataset/judgments/TEST_CLEANROOM.md",
     "w").write("\n".join(L) + "\n")
print("[cleanroom] aggregate written")
PYEOF
echo "[cleanroom] complete (temp dir purged on exit)"
