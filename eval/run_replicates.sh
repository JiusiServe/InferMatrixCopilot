#!/usr/bin/env bash
# Replicate driver: N full copilot_v2 eval runs (fresh generation + judging),
# each snapshotted under raw/copilot_v2_samples/<tag>_run<i>/ with its
# RESULTS_V3.md. Single-run scores are judge+generation noise (±0.1 RQS3 at
# n=3 PRs) — configs are ranked on the replicate mean, never a single roll.
set -euo pipefail
PY=${PYTHON:-python3}          # honour an active venv; override with PYTHON=
N="${1:-3}"
TAG="${2:-replicate}"
cd "$(dirname "$0")"
# activate your venv first, or set PYTHON=/path/to/venv/bin/python
for i in $(seq 1 "$N"); do
    echo "=== replicate $i/$N ($TAG) ==="
    rm -f raw/pr4678_copilot_v2.* raw/pr4679_copilot_v2.* raw/pr4849_copilot_v2.* \
          raw/v2_pr*_copilot_v2.* raw/v3_pr*_copilot_v2.*
    rm -rf raw/copilot_v2_work
    "$PY" run_eval.py --skill-dir "${OMNI_SKILL_DIR:?set OMNI_SKILL_DIR=/path/to/vllm-omni-skills/skills/vllm-omni-review}"
    python run_eval_v2.py
    python run_eval_v3.py
    dst="raw/copilot_v2_samples/${TAG}_run${i}"
    mkdir -p "$dst"
    cp raw/pr*_copilot_v2.md raw/pr*_copilot_v2.cost.json \
       raw/pr*_copilot_v2.findings.json "$dst"/
    cp RESULTS_V3.md "$dst/RESULTS_V3.md"
    echo "=== replicate $i done -> $dst ==="
done
echo "=== all $N replicates done ==="
