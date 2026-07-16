(no RUN_REPORT.md — rc=3)

## stdout
→ task: issue_answer issue #4842 on vllm-omni (tier L2) [report-only]
→ plan: reuse issue-answer@2 (active) steps=['issue.fetch', 'agent.draft_issue_answer', 'issue.post_answer', 'report.final_summary']
  · recalled issue-answer@2 (active)
  metrics: usd≈0.05 3.2min S=1.00 CATQ=0.232  (/rebase/vllm-omni-copilot/eval/dataset/arms/copilot_v2_t3_r3/runs/issue4842/run-20260712-032812-55f2a7/metrics.json)
  ✓ fetch: fetched issue #4842
  ✗ draft: [low] The agent exceeded the maximum number of allowed iterations and was unable to complete the requested task.
run run-20260712-032812-55f2a7: blocked  (/rebase/vllm-omni-copilot/eval/dataset/arms/copilot_v2_t3_r3/runs/issue4842/run-20260712-032812-55f2a7)
  ⚠ step 'draft' (agent.draft_issue_answer): [low] The agent exceeded the maximum number of allowed iterations and was unable to complete the requested task.
  see /rebase/vllm-omni-copilot/eval/dataset/arms/copilot_v2_t3_r3/runs/issue4842/run-20260712-032812-55f2a7/ESCALATION.md


## stderr
