#!/bin/bash
# T3: 3 sequential val replicates on the final config (knowledge + delivery
# fixes + cache optimization + PR-time checkout). Sequential so replicates
# don't contend for provider cache or rate limits.
set -u
for r in 1 2 3; do
  echo "[t3] replicate $r starting $(date +%H:%M:%S)"
  ARM_OUT=copilot_v2_t3_r$r /rebase/.venv/bin/python run_copilot_arm.py val
  echo "[t3] replicate $r done"
done
echo "[t3] all replicates complete"
