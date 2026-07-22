#!/bin/bash
# Final evaluation: frozen test split (3 replicates) + no-briefing ablation on
# val (3 replicates). Run ONLY after T4 val validation passes.
set -u
PY=${PYTHON:-python3}          # honour an active venv; override with PYTHON=
for r in 1 2 3; do
  echo "[final] test replicate $r starting $(date +%H:%M:%S)"
  ARM_OUT=copilot_v2_test_r$r "$PY" run_copilot_arm.py test
  echo "[final] test replicate $r done"
done
for r in 1 2 3; do
  echo "[final] ablation (no-briefing) val replicate $r starting $(date +%H:%M:%S)"
  PROFILE_BRIEFING_ENABLED=0 ARM_OUT=copilot_v2_noprofile_r$r \
    "$PY" run_copilot_arm.py val
  echo "[final] ablation replicate $r done"
done
echo "[final] all sweeps complete"
