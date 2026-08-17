(no RUN_REPORT.md — rc=3)

## stdout
→ task: pr_review PR #4926 on vllm-omni (tier L2)
→ plan: reuse pr-review@6 (active) steps=['pr.fetch_diff', 'pr.gate_check', 'agent.review_diff', 'pr.post_review', 'report.final_summary']
  · recalled pr-review@6 (active)
→ path: eco · agent-model=deepseek-v4-pro @ api.deepseek.com
  metrics: usd≈0.00 0.1min S=1.00  (/data/zhoutaichang/copilot/InferMatrixCopilot/eval/dataset/arms/copilot_v17ds_train/runs/pr4926/run-20260817-105011-b1bdc1/metrics.json)
  ✓ fetch: fetched PR #4926 diff (27969 chars, context 3985 chars); checkout: PR-TIME TREE (head 35aa741e1962)
  ✓ gate: FAILING CHECKS (2): ['buildkite/vllm-omni-amd-ci', 'buildkite/vllm-omni-npu-ci'] — do not re-argue what CI already repor
  ✗ review: unhandled error: APIStatusError: Error code: 402 - {'error': {'message': 'Insufficient Balance', 'type': 'unknown_error', 'param': None, 'code': 'invalid_request_error'}}
run run-20260817-105011-b1bdc1: blocked  (/data/zhoutaichang/copilot/InferMatrixCopilot/eval/dataset/arms/copilot_v17ds_train/runs/pr4926/run-20260817-105011-b1bdc1)
  ⚠ step 'review' (agent.review_diff): unhandled error: APIStatusError: Error code: 402 - {'error': {'message': 'Insufficient Balance', 'type': 'unknown_error', 'param': None, 'code': 'invalid_request_error'}}
  see /data/zhoutaichang/copilot/InferMatrixCopilot/eval/dataset/arms/copilot_v17ds_train/runs/pr4926/run-20260817-105011-b1bdc1/ESCALATION.md


## stderr
