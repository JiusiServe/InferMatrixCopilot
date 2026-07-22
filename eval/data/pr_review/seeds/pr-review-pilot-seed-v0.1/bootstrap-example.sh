#!/usr/bin/env bash
set -euo pipefail

# Run in an environment with outbound GitHub access, a repository cache,
# read-only GITHUB_TOKEN (recommended), and three configured JudgeBackend plugins.
python -m eval.tasks.pr_review benchmark build \
  --repo vllm-project/vllm-omni \
  --repository-cache /path/to/git-cache \
  --token-env GITHUB_TOKEN \
  --judge judges.family_a:backend \
  --judge judges.family_b:backend \
  --judge judges.family_c:backend \
  --output /path/to/pr-review-pilot-v0.1

python -m eval.tasks.pr_review benchmark validate \
  --benchmark /path/to/pr-review-pilot-v0.1
