(no RUN_REPORT.md — rc=3)

## stdout
→ task: issue_answer issue #5003 on vllm-omni (tier L2) [report-only]
→ plan: reuse issue-answer@2 (active) steps=['issue.fetch', 'agent.draft_issue_answer', 'issue.post_answer', 'report.final_summary']
  · recalled issue-answer@2 (active)
  metrics: usd≈0.06 3.1min S=1.00 CATQ=0.229  (/rebase/vllm-omni-copilot/eval/dataset/arms/copilot_v2/runs/issue5003/run-20260711-232305/metrics.json)
  ✓ fetch: fetched issue #5003
  ✗ draft: [medium] The root cause is a device-assignment mismatch between the deploy YAML and the user's hardware. The default `qwen3_omni_moe.yaml` assigns `devices: "0"` to stage 0 (thinker), but `--tensor-parallel-size 4` requires 4 GPUs. `setup_stage_devices` narrows `CUDA_VISIBLE_DEVICES` to just GPU 0, so TP workers with adjusted local_ranks 1–3 crash because `torch.accelerator.device_count()` returns
run run-20260711-232305: blocked  (/rebase/vllm-omni-copilot/eval/dataset/arms/copilot_v2/runs/issue5003/run-20260711-232305)
  ⚠ step 'draft' (agent.draft_issue_answer): [medium] The root cause is a device-assignment mismatch between the deploy YAML and the user's hardware. The default `qwen3_omni_moe.yaml` assigns `devices: "0"` to stage 0 (thinker), but `--tensor-parallel-size 4` requires 4 GPUs. `setup_stage_devices` narrows `CUDA_VISIBLE_DEVICES` to just GPU 0, so TP workers with adjusted local_ranks 1–3 crash because `torch.accelerator.device_count()` returns
  see /rebase/vllm-omni-copilot/eval/dataset/arms/copilot_v2/runs/issue5003/run-20260711-232305/ESCALATION.md


## stderr
