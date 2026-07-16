(no RUN_REPORT.md — rc=3)

## stdout
→ task: issue_answer issue #4842 on vllm-omni (tier L2) [report-only]
→ plan: reuse issue-answer@2 (active) steps=['issue.fetch', 'agent.draft_issue_answer', 'issue.post_answer', 'report.final_summary']
  · recalled issue-answer@2 (active)
  metrics: usd≈0.02 1.7min S=1.00 CATQ=0.260  (/rebase/vllm-omni-copilot/eval/dataset/arms/copilot_v2_t3_r1/runs/issue4842/run-20260712-024932-d10fff/metrics.json)
  ✓ fetch: fetched issue #4842
  ✗ draft: [low] The agent exceeded the maximum number of iterations (max_iterations) without completing the task.
run run-20260712-024932-d10fff: blocked  (/rebase/vllm-omni-copilot/eval/dataset/arms/copilot_v2_t3_r1/runs/issue4842/run-20260712-024932-d10fff)
  ⚠ step 'draft' (agent.draft_issue_answer): [low] The agent exceeded the maximum number of iterations (max_iterations) without completing the task.
  see /rebase/vllm-omni-copilot/eval/dataset/arms/copilot_v2_t3_r1/runs/issue4842/run-20260712-024932-d10fff/ESCALATION.md


## stderr
