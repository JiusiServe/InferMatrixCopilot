#!/usr/bin/env bash
# Monthly review-quality probe of omni-reviewbot against the pinned
# CC+Opus 5 baseline. One command: run_reviewbot_monthly.sh 2026-09
# (a non-month tag, e.g. "smoke", writes a report but never touches the
# month-over-month INDEX). See REVIEWBOT_EVAL.md for the runbook.
set -euo pipefail
MONTH="${1:?usage: run_reviewbot_monthly.sh <YYYY-MM | smoke-tag>}"
TAG="reviewbot_${MONTH}"
GEN="${GEN_REPLICATES:-3}"
cd "$(dirname "$0")"
PY=${PYTHON:-python3}

echo "=== preflight ==="
command -v claude >/dev/null || {
  echo "judge CLI missing: install/login the claude CLI first" >&2; exit 1; }
ARM_TAG="$TAG" GEN_REPLICATES="$GEN" "$PY" run_reviewbot_arm.py --preflight

echo "=== generate ($GEN replicates) ==="
ARM_TAG="$TAG" GEN_REPLICATES="$GEN" "$PY" run_reviewbot_arm.py

echo "=== judge (pinned claude/claude-sonnet-5, 3 reps, vs claudecode_opus5) ==="
# Judge targets are derived from the arm manifest, so generation and
# judging can never disagree about the item set (smoke runs included).
ONLY=$("$PY" -c "
import json,sys
m = json.load(open('arms/${TAG}_r1/manifest.json'))
print(','.join(s[2:] for s in m['stems']))
")
for i in $(seq 1 "$GEN"); do
  JUDGE_BACKEND=claude JUDGE_MODEL=claude-sonnet-5 \
  SPLIT=all_pr ONLY_ITEMS="$ONLY" REPLICATES=3 \
  ARM_A_DIR="arms/${TAG}_r${i}" ARM_B_DIR="baselines/claudecode_opus5" \
  JUDGE_OUT="judgments/${TAG}_r${i}" "$PY" judge_val.py
done

echo "=== verify (exact denominators, pinned judge, fresh sha256s) ==="
"$PY" build_reviewbot_report.py --verify --tag "$TAG" --gen-reps "$GEN"

echo "=== report ==="
"$PY" build_reviewbot_report.py --tag "$TAG" --gen-reps "$GEN"
