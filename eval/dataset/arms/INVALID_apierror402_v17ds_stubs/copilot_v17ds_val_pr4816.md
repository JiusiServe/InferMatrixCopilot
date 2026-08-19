(no RUN_REPORT.md — rc=3)

## stdout
→ task: pr_review PR #4816 on vllm-omni (tier L2)
→ plan: reuse pr-review@6 (active) steps=['pr.fetch_diff', 'pr.gate_check', 'agent.review_diff', 'pr.post_review', 'report.final_summary']
  · recalled pr-review@6 (active)
→ path: eco · agent-model=deepseek-v4-pro @ api.deepseek.com
  metrics: usd≈0.00 0.1min S=1.00  (/data/zhoutaichang/copilot/InferMatrixCopilot/eval/dataset/arms/copilot_v17ds_val/runs/pr4816/run-20260817-104946-e1d77c/metrics.json)
  ✓ fetch: fetched PR #4816 diff (5330 chars, context 3985 chars); checkout: PR-TIME TREE (head e1dac23ac02c)
  ✓ gate: FAILING CHECKS (3): ['buildkite/vllm-omni-amd-ci', 'buildkite/vllm-omni-intel-ci', 'buildkite/vllm-omni-npu-ci'] — do no
  ✗ review: unhandled error: APIStatusError: Error code: 402 - {'error': {'message': 'Insufficient Balance', 'type': 'unknown_error', 'param': None, 'code': 'invalid_request_error'}}
run run-20260817-104946-e1d77c: blocked  (/data/zhoutaichang/copilot/InferMatrixCopilot/eval/dataset/arms/copilot_v17ds_val/runs/pr4816/run-20260817-104946-e1d77c)
  ⚠ step 'review' (agent.review_diff): unhandled error: APIStatusError: Error code: 402 - {'error': {'message': 'Insufficient Balance', 'type': 'unknown_error', 'param': None, 'code': 'invalid_request_error'}}
  see /data/zhoutaichang/copilot/InferMatrixCopilot/eval/dataset/arms/copilot_v17ds_val/runs/pr4816/run-20260817-104946-e1d77c/ESCALATION.md


## stderr
