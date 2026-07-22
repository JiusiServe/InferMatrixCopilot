#!/usr/bin/env bash
# Re-judge ARCHIVED copilot_v2 runs under the current (v3.1) metric: restore
# each run's generated reviews into raw/, clear only copilot_v2 judge caches,
# re-run v2+v3 judging (no generation), snapshot RESULTS_V3.md back into the
# archive as RESULTS_V3_rejudged.md. Pure re-measurement of fixed artifacts.
set -euo pipefail
PY=${PYTHON:-python3}          # honour an active venv; override with PYTHON=
cd "$(dirname "$0")"
# activate your venv first, or set PYTHON=/path/to/venv/bin/python
for tag in "$@"; do
    src="raw/copilot_v2_samples/${tag}"
    [ -d "$src" ] || { echo "missing $src"; exit 1; }
    echo "=== re-judging $tag ==="
    rm -f raw/pr4678_copilot_v2.* raw/pr4679_copilot_v2.* raw/pr4849_copilot_v2.* \
          raw/v2_pr*_copilot_v2.* raw/v3_pr*_copilot_v2.*
    cp "$src"/pr*_copilot_v2.md "$src"/pr*_copilot_v2.cost.json raw/
    ls "$src"/pr*_copilot_v2.findings.json >/dev/null 2>&1 \
        && cp "$src"/pr*_copilot_v2.findings.json raw/
    "$PY" run_eval.py --skill-dir "${OMNI_SKILL_DIR:?set OMNI_SKILL_DIR=/path/to/vllm-omni-skills/skills/vllm-omni-review}"
    python run_eval_v2.py
    python run_eval_v3.py
    cp RESULTS_V3.md "$src/RESULTS_V3_rejudged.md"
    echo "=== $tag re-judged ==="
done
