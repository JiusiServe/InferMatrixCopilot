# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4905, 'report_only': True, 'post': False, 'params': {}}

## fetch
- **state_updates**: {'issue_text': '{"body":"### Your current environment\\n\\n<details>\\n<summary>The output of <code>python collect_env.py</code></summary>\\n\\n```text\\nCI env\\n```\\n\\n</details>\\n\\n\\n### Your code version\\n\\n<details>\\n<summary>The commit id or version of vllm</summary>\\n\\n```text\\n0.24.0\\n```\\n</details>\\n<details>\\n<summary>The commit id or version of vllm-omni</summary>\\n\\n```text\\nddba6de2ab658a0fdb6f3f72cac9d2c3e2c19aea\\n```\\n</details>\\n\\n\\n### 🐛 Describe the bug\\n\\nhttps://buildkite.com/vllm/vllm-omni/builds/12074/canvas?sid=019f32cc-ec98-4269-8ec8-fbd915f2e962&tab=output\\n```\\n________________________________________________________________ test_multistage_sleep_h100[1] _________________________________________________________________\\n--\\n\xa0 | \xa0\\n\xa0 | tp_size = 1\\n\xa0 | \xa0\\n\xa0 | @pytest.mark.omni\\n\xa0 | @pytest.mark.advanced_model\\n\xa0 | @pytest.mark.parametrize(\\"tp_size\\", [1, 2])\\n\xa0 | @hardware_test(res={\\"cuda\\": \\"H100\\", \\"rocm\\": \\"MI325\\"}, num_cards=2)\\n\xa0 | @pytest.mark.asyncio\\n\xa0 | async def test_multistage_sleep_h100(tp_size: int):\\n\xa0 | \\"\\"\\"Explicit 2-stage (llm + diffusion) + connectors; sleep/wake both stages.\\"\\"\\"\\n\xa0 | if current_omni_platform.is_rocm():\\n\xa0 | clean_gpu_envs()\\n\xa0 | num_gpus = torch.accelerator.device_count()\\n\xa0 | if num_gpus < tp_size * 2:\\n\xa0 | pytest.skip(\\"Not enough GPUs\\")\\n\xa0 | \xa0\\n\xa0 | stages = []\\n\xa0 | for i in range(2):\\n\xa0 | devs = get_dynamic_devices(i, 2, tp_size)\\n\xa0 | stages.append(\\n\xa0 | {\\n\xa0 | \\"stage_id\\": i,\\n\xa0 | \\"stage_type\\": \\"llm\\" if i == 0 else \\"diffusion\\",\\n\xa0 | \\"runtime\\": {\\"process\\": True, \\"devices\\": devs},\\n\xa0 | \\"engine_args\\": {\\n\xa0 | \\"model\\": MODEL,\\n\xa0 | \\"model_stage\\": \\"thinker\\" if i == 0 else \\"base\\",\\n\xa0 | \\"tensor_parallel_size\\": tp_size,\\n\xa0 | \\"gpu_memory_utilization\\": 0.4,\\n\xa0 | \\"dtype\\": \

## draft
- **status**: success
- **summary**: This is not a bug in the production code — it's a test that wasn't updated when PR #4834 landed. PR #4834 intentionally added a NotImplementedError guard in AsyncOmni.wake_up() that rejects wake_up after sleep(level=2), because level-2 discards weights from GPU entirely and disk reload isn't implemented yet. The test test_multistage_sleep_h100 was still calling sleep(level=2) → wake_up() and was not adjusted. The fix is to use level=1 (which offloads to CPU RAM with DMA restore), and this appears already applied in the current repo.
- **findings**: ['PR #4834 (merged) added a safety guard at async_omni.py line ~943: wake_up() after sleep(level=2) now raises NotImplementedError — this was the fix for issue #4473 Repro A (silent corruption).', 'test_multistage_sleep_h100 was calling sleep(stage_ids=[0,1], level=2) followed by wake_up(), which now correctly triggers the new NotImplementedError.', 'The current file on disk already shows level=1 in test_multistage_sleep_h100, indicating the fix has been applied.', 'The dedicated regression test test_level2_sleep_wake_raises (added by PR #4834) correctly asserts NotImplementedError is raised for level-2 sleep → wake_up.', 'Other level=2 usages in the test file are safe: test_coordinated_cross_device uses level=2 but never calls wake_up; it only measures VRAM and shuts down.']
- **files_read**: ['/rebase/vllm-omni/tests/entrypoints/test_omni_sleep_mode.py', '/rebase/vllm-omni/vllm_omni/entrypoints/async_omni.py']
- **files_modified**: []
- **tests_requested**: ['pytest tests/entrypoints/test_omni_sleep_mode.py::test_multistage_sleep_h100 -v -x --timeout 600']
- **tests_run**: []
- **assumptions**: ['The fix (level=2 → level=1) appears already applied in the current working tree; assumed to be correct based on file read.', 'The CI failure at build 12074 reflects the pre-fix state where the test still used level=2.']
- **blockers**: []
- **confidence**: high
- **failure_kind**: None
- **next_action**: If the fix is not yet committed/merged, submit a one-line PR changing `sleep(stage_ids=[0, 1], level=2)` → `sleep(stage_ids=[0, 1], level=1)` in test_multistage_sleep_h100. Then re-run the CI sleep-mode suite as Flink-ddd requested.
- **answer_draft**: ## Root cause

This is **not a product bug** — it's a test that wasn't updated when #4834 landed.

PR #4834 intentionally added a `NotImplementedError` guard in `AsyncOmni.wake_up()` (`vllm_omni/entrypoints/async_omni.py`, line ~943):

```python
if getattr(self, "_level2_sleeping", False):
    raise NotImplementedError(
        "wake_up() after sleep(level=2) is not yet implemented: weights were "
        "discarded from GPU and reloading from disk is not yet supported. "
        "Use sleep(level=1) instead, which offloads weights to CPU RAM "
        "and supports fast DMA restore."
    )
```

This was the fix for **issue #4473 Repro A** (silent corruption after level-2 sleep/wake). Level-2 sleep discards weights from GPU entirely; reloading from disk is not yet implemented, so calling `wake_up()` after `sleep(level=2)` is now correctly rejected at the Python layer rather than silently producing corrupted output.

The test `test_multistage_sleep_h100` in `tests/entrypoints/test_omni_sleep_mode.py` was still using `sleep(level=2)` followed by `wake_up()`, which now triggers the intentional `NotImplementedError`.

## Fix

Change the sleep level in `test_multistage_sleep_h100` from `2` to `1`:

```diff
-        acks = await engine.sleep(stage_ids=[0, 1], level=2)
+        acks = await engine.sleep(stage_ids=[0, 1], level=1)
```

Level-1 sleep/wake is the fully supported path — it offloads weights to CPU RAM with fast DMA restore, and the rest of the test (wake, verify generation) works correctly at level 1.

This fix appears to already be applied in the current repo. The dedicated regression test `test_level2_sleep_wake_raises` (also added by #4834) correctly verifies that `wake_up()` after `sleep(level=2)` raises `NotImplementedError`, which is the expected behavior.

### Other level-2 usages are safe

- `test_coordinated_cross_device` uses `sleep(level=2)` but **never calls `wake_up()`** — it only measures VRAM drop and shuts down. That's fine.
- `test_level2_sleep_
- **draft_answer**: ## Root cause

This is **not a product bug** — it's a test that wasn't updated when #4834 landed.

PR #4834 intentionally added a `NotImplementedError` guard in `AsyncOmni.wake_up()` (`vllm_omni/entrypoints/async_omni.py`, line ~943):

```python
if getattr(self, "_level2_sleeping", False):
    raise NotImplementedError(
        "wake_up() after sleep(level=2) is not yet implemented: weights were "
        "discarded from GPU and reloading from disk is not yet supported. "
        "Use sleep(level=1) instead, which offloads weights to CPU RAM "
        "and supports fast DMA restore."
    )
```

This was the fix for **issue #4473 Repro A** (silent corruption after level-2 sleep/wake). Level-2 sleep discards weights from GPU entirely; reloading from disk is not yet implemented, so calling `wake_up()` after `sleep(level=2)` is now correctly rejected at the Python layer rather than silently producing corrupted output.

The test `test_multistage_sleep_h100` in `tests/entrypoints/test_omni_sleep_mode.py` was still using `sleep(level=2)` followed by `wake_up()`, which now triggers the intentional `NotImplementedError`.

## Fix

Change the sleep level in `test_multistage_sleep_h100` from `2` to `1`:

```diff
-        acks = await engine.sleep(stage_ids=[0, 1], level=2)
+        acks = await engine.sleep(stage_ids=[0, 1], level=1)
```

Level-1 sleep/wake is the fully supported path — it offloads weights to CPU RAM with fast DMA restore, and the rest of the test (wake, verify generation) works correctly at level 1.

This fix appears to already be applied in the current repo. The dedicated regression test `test_level2_sleep_wake_raises` (also added by #4834) correctly verifies that `wake_up()` after `sleep(level=2)` raises `NotImplementedError`, which is the expected behavior.

### Other level-2 usages are safe

- `test_coordinated_cross_device` uses `sleep(level=2)` but **never calls `wake_up()`** — it only measures VRAM drop and shuts down. That's fine.
- `test_level2_sleep_
- **state_updates**: {'draft_answer': '## Root cause\n\nThis is **not a product bug** — it\'s a test that wasn\'t updated when #4834 landed.\n\nPR #4834 intentionally added a `NotImplementedError` guard in `AsyncOmni.wake_up()` (`vllm_omni/entrypoints/async_omni.py`, line ~943):\n\n```python\nif getattr(self, "_level2_sleeping", False):\n    raise NotImplementedError(\n        "wake_up() after sleep(level=2) is not yet implemented: weights were "\n        "discarded from GPU and reloading from disk is not yet supported. "\n        "Use sleep(level=1) instead, which offloads weights to CPU RAM "\n        "and supports fast DMA restore."\n    )\n```\n\nThis was the fix for **issue #4473 Repro A** (silent corruption after level-2 sleep/wake). Level-2 sleep discards weights from GPU entirely; reloading from disk is not yet implemented, so calling `wake_up()` after `sleep(level=2)` is now correctly rejected at the Python layer rather than silently producing corrupted output.\n\nThe test `test_multistage_sleep_h100` in `tests/entrypoints/test_omni_sleep_mode.py` was still using `sleep(level=2)` followed by `wake_up()`, which now triggers the intentional `NotImplementedError`.\n\n## Fix\n\nChange the sleep level in `test_multistage_sleep_h100` from `2` to `1`:\n\n```diff\n-        acks = await engine.sleep(stage_ids=[0, 1], level=2)\n+        acks = await engine.sleep(stage_ids=[0, 1], level=1)\n```\n\nLevel-1 sleep/wake is the fully supported path — it offloads weights to CPU RAM with fast DMA restore, and the rest of the test (wake, verify generation) works correctly at level 1.\n\nThis fix appears to already be applied in the current repo. The dedicated regression test `test_level2_sleep_wake_raises` (also added by #4834) correctly verifies that `wake_up()` after `sleep(level=2)` raises `NotImplementedError`, which is the expected behavior.\n\n### Other level-2 usages are safe\n\n- `test_coordinated_cross_device` uses `sleep(level=2)` but **never calls `wake_up()`** — it only measures VRAM 
