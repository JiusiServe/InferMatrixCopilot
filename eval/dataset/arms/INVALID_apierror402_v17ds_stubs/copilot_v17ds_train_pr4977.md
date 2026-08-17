(no RUN_REPORT.md — rc=3)

## stdout
→ task: pr_review PR #4977 on vllm-omni (tier L2)
→ plan: reuse pr-review@6 (active) steps=['pr.fetch_diff', 'pr.gate_check', 'agent.review_diff', 'pr.post_review', 'report.final_summary']
  · recalled pr-review@6 (active)
→ path: eco · agent-model=deepseek-v4-pro @ api.deepseek.com
  metrics: usd≈0.00 0.1min S=1.00  (/data/zhoutaichang/copilot/InferMatrixCopilot/eval/dataset/arms/copilot_v17ds_train/runs/pr4977/run-20260817-104946-ed83da/metrics.json)
  ✓ fetch: fetched PR #4977 diff (4140 chars, context 1866 chars); checkout: PR-TIME TREE (head 9947f41430aa)
  ✓ gate: FAILING CHECKS (1): ['buildkite/vllm-omni-npu-ci'] — do not re-argue what CI already reports; point at the gate.
  ✗ review: unhandled error: APIStatusError: Error code: 402 - {'error': {'message': 'Insufficient Balance', 'type': 'unknown_error', 'param': None, 'code': 'invalid_request_error'}}
run run-20260817-104946-ed83da: blocked  (/data/zhoutaichang/copilot/InferMatrixCopilot/eval/dataset/arms/copilot_v17ds_train/runs/pr4977/run-20260817-104946-ed83da)
  ⚠ step 'review' (agent.review_diff): unhandled error: APIStatusError: Error code: 402 - {'error': {'message': 'Insufficient Balance', 'type': 'unknown_error', 'param': None, 'code': 'invalid_request_error'}}
  see /data/zhoutaichang/copilot/InferMatrixCopilot/eval/dataset/arms/copilot_v17ds_train/runs/pr4977/run-20260817-104946-ed83da/ESCALATION.md


## stderr
