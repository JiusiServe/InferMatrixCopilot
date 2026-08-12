#!/usr/bin/env bash
# Judge all three arms against the Opus 5 reference with the gpt-5.6 judge, then compare.
#
# One run per PR per arm, one judgment per review: 3 arms x 20 PRs x 1 replicate =
# 60 verdicts. That is the user's scoping decision, and it costs every error bar in the
# campaign — see the completeness gate below and the note the comparison prints.
#
# These numbers SUPERSEDE and are NOT comparable to the sonnet-5 / Opus 4.8 campaign:
# both the judge and the reference changed. The comparison refuses to mix them.
set -euo pipefail
cd "$(dirname "$0")"

BASE=baselines/claudecode_opus5
export JUDGE_BACKEND=cursor
export JUDGE_MODEL=gpt-5.6-sol-high
export REPLICATES=1
export SPLIT=all_pr
export ARM_B_DIR="$BASE"

declare -A ARMS=(
  [g56_ocr_r1]=arms/ocr_v1810_r1
  [g56_copilot_r1]=arms/copilot_v4_pr20_r1
  [g56_direct_r1]=arms/direct_opus5_r1
)

for out in "${!ARMS[@]}"; do
  echo "=== judging ${ARMS[$out]} -> judgments/$out ==="
  # judge_val.py is resumable (existing verdict files are skipped) and returns
  # non-zero if any call failed, so a transient failure is retried, not averaged over.
  for attempt in 1 2 3; do
    if ARM_A_DIR="${ARMS[$out]}" JUDGE_OUT="judgments/$out" python3 judge_val.py; then
      break
    fi
    echo "  attempt $attempt had failures; retrying the missing verdicts"
    [ "$attempt" = 3 ] && { echo "GIVING UP on $out"; exit 1; }
  done
done

echo
echo "=== comparison (fails closed on completeness) ==="
EXPECT_ITEMS=20 EXPECT_VERDICTS=60 python3 compare_ocr_vs_copilot.py \
  judgments/g56_ocr_r1 judgments/g56_copilot_r1 judgments/g56_direct_r1
