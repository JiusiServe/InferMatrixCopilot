# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4814, 'report_only': True, 'post': False, 'params': {}}

## fetch
- **state_updates**: {'issue_text': '{"body":"### Your current environment\\n\\n<details>\\n<summary>The output of <code>python collect_env.py</code></summary>\\n\\n```text\\nYour output of `python collect_env.py` here\\n```\\n\\n</details>\\n\\n\\n### Your code version\\n\\n<details>\\n<summary>The commit id or version of vllm</summary>\\n\\n```text\\n\\n```\\n</details>\\n<details>\\n<summary>The commit id or version of vllm-omni</summary>\\n\\n```text\\n0.20.0\\n```\\n</details>\\n\\n\\n### 🐛 Describe the bug\\n\\n运行命令如下：\\n```bash\\nexport ASCEND_RT_VISIBLE_DEVICES=0,1,2,3\\nmodel_base=\\"/data/Wan2.2-T2V-A14B-Diffusers\\"\\npython text_to_video.py \\\\\\n  --prompt \\"Two anthropomorphic cats in comfy boxing gear and bright gloves fight intensely on a spotlighted stage.\\" \\\\\\n  --negative-prompt \\"<optional quality filter>\\" \\\\\\n  --height 480 \\\\\\n  --width 832 \\\\\\n  --num-frames 33 \\\\\\n  --guidance-scale 4.0 \\\\\\n  --guidance-scale-high 3.0 \\\\\\n  --flow-shift 12.0 \\\\\\n  --num-inference-steps 40 \\\\\\n  --fps 16 \\\\\\n  --output t2v_out.mp4 \\\\\\n  --cache-backend \\"cache_dit\\" \\\\\\n  --model ${model_base} \\\\\\n  --ulysses-degree 2 \\\\\\n  --cfg-parallel-size 2 \\\\\\n  --enable-cpu-offload\\n```\\n报错如下：\\n```bash\\nWARNING 07-01 02:48:30 [pipeline_wan2_2.py:553] boundary_ratio is required for T2V generation. using default value 0.875\\nWARNING 07-01 02:48:30 [pipeline_wan2_2.py:553] boundary_ratio is required for T2V generation. using default value 0.875\\nWARNING 07-01 02:48:30 [pipeline_wan2_2.py:553] boundary_ratio is required for T2V generation. using default value 0.875\\nWARNING 07-01 02:48:30 [pipeline_wan2_2.py:553] boundary_ratio is required for T2V generation. using default value 0.875\\n  0%|                                                                                                                                                                                       | 0/1 [00:00<?, ?it/s]WARNING 07-01 02:48:47 [sequence_parallel.

## draft
- **status**: success
- **summary**: The reported incompatibility between ulysses parallelism and cache_dit on Wan2.2/Ascend NPU was reproducible in v0.20.0 but has been verified as fixed in v0.23.0rc1 (commit 724f5d132deb55dfd73591c83494eca15c95d179). The contributor @FayeSpica successfully ran the exact same command with ulysses-degree=2, cfg-parallel-size=2, and --cache-backend cache_dit on 8 NPUs and completed generation. A collaborator (@Gaohan123) confirmed the fix and offered to reopen if issues persist.
- **findings**: ["Root cause in v0.20.0: cache_dit's pattern_base.py _get_Fn_residual compared tensor shapes where dimension 1 had size 512 (ulysses-sharded) vs 1024 (full), causing RuntimeError. The sequence_parallel hook also issued 'Expected tensor with 4 dims, got 3. Skipping split' warnings, indicating the SP hooks were not handling cache_dit-wrapped transformer layers correctly.", '@FayeSpica verified the same command works on v0.23.0rc1 (commit 724f5d132deb55dfd73591c83494eca15c95d179), producing valid output at 100% | 40/40 on 8 Ascend NPUs.', 'Collaborator @Gaohan123 acknowledged the fix and stated they can reopen if the user still encounters issues after upgrading.']
- **files_read**: ['/rebase/vllm-omni-copilot/eval/dataset/arms/copilot_v2/runs/issue4814/run-20260711-231601/evidence/issue_text.txt', '/rebase/vllm-omni/vllm_omni/diffusion/hooks/sequence_parallel.py', '/rebase/vllm-omni/vllm_omni/diffusion/distributed/cfg_parallel.py', '/rebase/vllm-omni/vllm_omni/diffusion/models/wan2_2/pipeline_wan2_2.py']
- **files_modified**: []
- **tests_requested**: []
- **tests_run**: []
- **assumptions**: ['The fix landed between v0.20.0 and v0.23.0rc1 (commit 724f5d13...). The exact commit that resolved the cache_dit+ulysses interaction is not identified, but the verification evidence is conclusive.', "The user's environment (4x Ascend NPU, CANN version) is compatible with v0.23.0; the successful verification used 8 NPUs but ulysses-degree=2 should work on 4 as well."]
- **blockers**: []
- **confidence**: high
- **failure_kind**: None
- **next_action**: Close the issue as resolved; user should upgrade to v0.23.0 or later. If the problem persists after upgrading, reopen for further investigation.
- **answer_draft**: ## Summary

This issue (Wan2.2 + ulysses + cache_dit crash on Ascend NPU in v0.20.0) has been **verified as fixed in v0.23.0rc1** (commit `724f5d132deb55dfd73591c83494eca15c95d179`).

## Root Cause (v0.20.0)

The crash occurred because `cache_dit`'s caching layer stored hidden states at the full sequence length, but ulysses sequence parallelism had already sharded the sequence dimension. When comparing original vs. current hidden states in `_get_Fn_residual`, the sizes didn't match (512 vs 1024 on dim 1), causing a `RuntimeError`. Additionally, the sequence parallel split hook emitted warnings about receiving tensors with unexpected dimensions, indicating cache_dit-wrapped layers weren't properly handled by the SP hook system at that time.

## Verification

@FayeSpica tested the **exact same command** with all parallel features enabled (`--ulysses-degree 2 --cfg-parallel-size 2 --cache-backend cache_dit --enable-cpu-offload`) on v0.23.0rc1 (commit `724f5d13`) and it completed successfully:

```
100%|████████████████████████████████████████| 40/40 [00:43<00:00,  1.08s/it]
Processed prompts: 100%|████████████████████| 1/1 [01:30<00:00, 90.27s/it]
Total generation time: 90.2696 seconds (90269.60 ms)
Saved generated video to t2v_out.mp4
```

## Recommended Action

Please **upgrade to v0.23.0 or later**. An Ascend Docker image is available at `quay.io/ascend/vllm-omni:v0.24.0` (or `quay.io/ascend/vllm-omni:v0.23.0` for the verified version). The version compatibility reference is maintained in [Issue #2223](https://github.com/vllm-project/vllm-omni/issues/2223#issuecomment-4705062827).

If the issue persists after upgrading, please comment and we will reopen for further investigation.
- **draft_answer**: ## Summary

This issue (Wan2.2 + ulysses + cache_dit crash on Ascend NPU in v0.20.0) has been **verified as fixed in v0.23.0rc1** (commit `724f5d132deb55dfd73591c83494eca15c95d179`).

## Root Cause (v0.20.0)

The crash occurred because `cache_dit`'s caching layer stored hidden states at the full sequence length, but ulysses sequence parallelism had already sharded the sequence dimension. When comparing original vs. current hidden states in `_get_Fn_residual`, the sizes didn't match (512 vs 1024 on dim 1), causing a `RuntimeError`. Additionally, the sequence parallel split hook emitted warnings about receiving tensors with unexpected dimensions, indicating cache_dit-wrapped layers weren't properly handled by the SP hook system at that time.

## Verification

@FayeSpica tested the **exact same command** with all parallel features enabled (`--ulysses-degree 2 --cfg-parallel-size 2 --cache-backend cache_dit --enable-cpu-offload`) on v0.23.0rc1 (commit `724f5d13`) and it completed successfully:

```
100%|████████████████████████████████████████| 40/40 [00:43<00:00,  1.08s/it]
Processed prompts: 100%|████████████████████| 1/1 [01:30<00:00, 90.27s/it]
Total generation time: 90.2696 seconds (90269.60 ms)
Saved generated video to t2v_out.mp4
```

## Recommended Action

Please **upgrade to v0.23.0 or later**. An Ascend Docker image is available at `quay.io/ascend/vllm-omni:v0.24.0` (or `quay.io/ascend/vllm-omni:v0.23.0` for the verified version). The version compatibility reference is maintained in [Issue #2223](https://github.com/vllm-project/vllm-omni/issues/2223#issuecomment-4705062827).

If the issue persists after upgrading, please comment and we will reopen for further investigation.
- **state_updates**: {'draft_answer': "## Summary\n\nThis issue (Wan2.2 + ulysses + cache_dit crash on Ascend NPU in v0.20.0) has been **verified as fixed in v0.23.0rc1** (commit `724f5d132deb55dfd73591c83494eca15c95d179`).\n\n## Root Cause (v0.20.0)\n\nThe crash occurred because `cache_dit`'s caching layer stored hidden states at the full sequence length, but ulysses sequence parallelism had already sharded the sequence dimension. When comparing original vs. current hidden states in `_get_Fn_residual`, the sizes didn't match (512 vs 1024 on dim 1), causing a `RuntimeError`. Additionally, the sequence parallel split hook emitted warnings about receiving tensors with unexpected dimensions, indicating cache_dit-wrapped layers weren't properly handled by the SP hook system at that time.\n\n## Verification\n\n@FayeSpica tested the **exact same command** with all parallel features enabled (`--ulysses-degree 2 --cfg-parallel-size 2 --cache-backend cache_dit --enable-cpu-offload`) on v0.23.0rc1 (commit `724f5d13`) and it completed successfully:\n\n```\n100%|████████████████████████████████████████| 40/40 [00:43<00:00,  1.08s/it]\nProcessed prompts: 100%|████████████████████| 1/1 [01:30<00:00, 90.27s/it]\nTotal generation time: 90.2696 seconds (90269.60 ms)\nSaved generated video to t2v_out.mp4\n```\n\n## Recommended Action\n\nPlease **upgrade to v0.23.0 or later**. An Ascend Docker image is available at `quay.io/ascend/vllm-omni:v0.24.0` (or `quay.io/ascend/vllm-omni:v0.23.0` for the verified version). The version compatibility reference is maintained in [Issue #2223](https://github.com/vllm-project/vllm-omni/issues/2223#issuecomment-4705062827).\n\nIf the issue persists after upgrading, please comment and we will reopen for further investigation."}
