#!/bin/bash
# T4: 3 sequential val replicates on the punch-list config.
set -u
for r in 1 2 3; do
  echo "[t4] replicate $r starting $(date +%H:%M:%S)"
  ARM_OUT=copilot_v2_t4_r$r /rebase/.venv/bin/python run_copilot_arm.py val
  echo "[t4] replicate $r done"
done
echo "[t4] all replicates complete"
