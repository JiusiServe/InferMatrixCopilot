# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4905, 'report_only': True, 'post': False, 'params': {}}

## fetch
- **state_updates**: {'issue_text': '{"body":"### Your current environment\\n\\n<details>\\n<summary>The output of <code>python collect_env.py</code></summary>\\n\\n```text\\nCI env\\n```\\n\\n</details>\\n\\n\\n### Your code version\\n\\n<details>\\n<summary>The commit id or version of vllm</summary>\\n\\n```text\\n0.24.0\\n```\\n</details>\\n<details>\\n<summary>The commit id or version of vllm-omni</summary>\\n\\n```text\\nddba6de2ab658a0fdb6f3f72cac9d2c3e2c19aea\\n```\\n</details>\\n\\n\\n### 🐛 Describe the bug\\n\\nhttps://buildkite.com/vllm/vllm-omni/builds/12074/canvas?sid=019f32cc-ec98-4269-8ec8-fbd915f2e962&tab=output\\n```\\n________________________________________________________________ test_multistage_sleep_h100[1] _________________________________________________________________\\n--\\n\xa0 | \xa0\\n\xa0 | tp_size = 1\\n\xa0 | \xa0\\n\xa0 | @pytest.mark.omni\\n\xa0 | @pytest.mark.advanced_model\\n\xa0 | @pytest.mark.parametrize(\\"tp_size\\", [1, 2])\\n\xa0 | @hardware_test(res={\\"cuda\\": \\"H100\\", \\"rocm\\": \\"MI325\\"}, num_cards=2)\\n\xa0 | @pytest.mark.asyncio\\n\xa0 | async def test_multistage_sleep_h100(tp_size: int):\\n\xa0 | \\"\\"\\"Explicit 2-stage (llm + diffusion) + connectors; sleep/wake both stages.\\"\\"\\"\\n\xa0 | if current_omni_platform.is_rocm():\\n\xa0 | clean_gpu_envs()\\n\xa0 | num_gpus = torch.accelerator.device_count()\\n\xa0 | if num_gpus < tp_size * 2:\\n\xa0 | pytest.skip(\\"Not enough GPUs\\")\\n\xa0 | \xa0\\n\xa0 | stages = []\\n\xa0 | for i in range(2):\\n\xa0 | devs = get_dynamic_devices(i, 2, tp_size)\\n\xa0 | stages.append(\\n\xa0 | {\\n\xa0 | \\"stage_id\\": i,\\n\xa0 | \\"stage_type\\": \\"llm\\" if i == 0 else \\"diffusion\\",\\n\xa0 | \\"runtime\\": {\\"process\\": True, \\"devices\\": devs},\\n\xa0 | \\"engine_args\\": {\\n\xa0 | \\"model\\": MODEL,\\n\xa0 | \\"model_stage\\": \\"thinker\\" if i == 0 else \\"base\\",\\n\xa0 | \\"tensor_parallel_size\\": tp_size,\\n\xa0 | \\"gpu_memory_utilization\\": 0.4,\\n\xa0 | \\"dtype\\": \

## draft
- **status**: success
- **summary**: PR #4834 intentionally added a `NotImplementedError` guard in `AsyncOmni.wake_up()` (vllm_omni/entrypoints/async_omni.py:945) that rejects wake_up after sleep(level=2) because level-2 discards weights from GPU and reload from disk is not yet implemented. The pre-existing test `test_multistage_sleep_h100` was still calling `sleep(stage_ids=[0,1], level=2)` followed by `wake_up()`, which now correctly triggers the guard. The fix is to change the test to use `level=1` (which offloads to CPU RAM and supports DMA restore) — this has already been applied in the current repo tree at tests/entrypoints/test_omni_sleep_mode.py:540. The fix should be committed as a follow-up PR (or was already committed) and the CI re-run to confirm.
- **findings**: ['Root cause: PR #4834 (merged) added the NotImplementedError guard at vllm_omni/entrypoints/async_omni.py line ~945: `if getattr(self, "_level2_sleeping", False): raise NotImplementedError(...)`. This guard is correct and intentional — it prevents silent corruption from #4473 Repro A.', 'The guard is triggered because sleep() sets `self._level2_sleeping = True` when `level == 2` (async_omni.py, end of sleep method).', 'The test `test_multistage_sleep_h100` was not updated in PR #4834 (the PR only added 3 new regression tests: test_level2_sleep_wake_raises, test_partial_wake_blocks_generate, test_duplicate_wake_is_idempotent).', 'The current repo tree already has the fix: the sleep call at tests/entrypoints/test_omni_sleep_mode.py:540 now passes `level=1` instead of `level=2`.', 'The dedicated regression test `test_level2_sleep_wake_raises` (line 413-419) correctly expects NotImplementedError for level-2 sleep → wake_up path.', "The skipped test `test_coordinated_cross_device` (line 323-325) still uses level=2 but only for sleep; it never calls wake_up after, so it won't hit the guard when re-enabled."]
- **files_read**: ['/rebase/vllm-omni/tests/entrypoints/test_omni_sleep_mode.py', '/rebase/vllm-omni/vllm_omni/entrypoints/async_omni.py', '/rebase/vllm-omni/tests/entrypoints/openai_api/test_omni_sleep_wakeup.py']
- **files_modified**: []
- **tests_requested**: ['pytest tests/entrypoints/test_omni_sleep_mode.py::test_multistage_sleep_h100 -v']
- **tests_run**: []
- **assumptions**: ['The fix (level=2 → level=1) in the current repo tree was committed after the CI failure at commit ddba6de2ab658a0fdb6f3f72cac9d2c3e2c19aea and before this investigation — the issue may already be resolved on main but the issue ticket is still open.', 'The buildkite CI URL in the issue (build 12074) ran against the merge commit of PR #4834, which did not yet include the test fix.']
- **blockers**: []
- **confidence**: high
- **failure_kind**: test_failure
- **next_action**: Close the issue if the level=1 fix is already committed and CI passes; otherwise submit a one-line PR changing level=2 to level=1 in test_multistage_sleep_h100 and request CI re-run.
- **answer_draft**: ## Diagnosis

This is **not a bug in the engine** — it's a test that wasn't updated when PR #4834 landed.

### Root cause

PR [#4834](https://github.com/vllm-project/vllm-omni/pull/4834) (merged) added an intentional `NotImplementedError` guard in `AsyncOmni.wake_up()`:

**`vllm_omni/entrypoints/async_omni.py` (~line 945):**
```python
if getattr(self, "_level2_sleeping", False):
    raise NotImplementedError(
        "wake_up() after sleep(level=2) is not yet implemented: weights were "
        "discarded from GPU and reloading from disk is not yet supported. "
        "Use sleep(level=1) instead, which offloads weights to CPU RAM "
        "and supports fast DMA restore."
    )
```

This guard is **correct and intentional**: it prevents the silent corruption / CUDA illegal-memory-access crash that was reported in [#4473](https://github.com/vllm-project/vllm-omni/issues/4473) (Repro A). Level-2 sleep discards weights from GPU entirely, and reloading from disk is not yet implemented.

The pre-existing test `test_multistage_sleep_h100` was calling `sleep(stage_ids=[0, 1], level=2)` followed by `wake_up(stage_ids=[0, 1])`. PR #4834 added the guard but did not update this test, so it started failing.

### Fix (one-line change)

In `tests/entrypoints/test_omni_sleep_mode.py`, change `level=2` to `level=1`:

```diff
-        acks = await engine.sleep(stage_ids=[0, 1], level=2)
+        acks = await engine.sleep(stage_ids=[0, 1], level=1)
```

Level-1 sleep offloads weights to CPU RAM and supports fast DMA restore via `wake_up()` — which is exactly what this test intends to exercise (sleep → wake → verify generation).

### Status

This fix appears to already be present in the current repository tree (the test now reads `level=1` at line 540). If the CI hasn't been re-run yet, please trigger `tests/entrypoints/test_omni_sleep_mode.py` to confirm.

### Related tests (already correct)

- `test_level2_sleep_wake_raises` — explicitly validates that `wake_up()` after `sleep(leve
- **draft_answer**: ## Diagnosis

This is **not a bug in the engine** — it's a test that wasn't updated when PR #4834 landed.

### Root cause

PR [#4834](https://github.com/vllm-project/vllm-omni/pull/4834) (merged) added an intentional `NotImplementedError` guard in `AsyncOmni.wake_up()`:

**`vllm_omni/entrypoints/async_omni.py` (~line 945):**
```python
if getattr(self, "_level2_sleeping", False):
    raise NotImplementedError(
        "wake_up() after sleep(level=2) is not yet implemented: weights were "
        "discarded from GPU and reloading from disk is not yet supported. "
        "Use sleep(level=1) instead, which offloads weights to CPU RAM "
        "and supports fast DMA restore."
    )
```

This guard is **correct and intentional**: it prevents the silent corruption / CUDA illegal-memory-access crash that was reported in [#4473](https://github.com/vllm-project/vllm-omni/issues/4473) (Repro A). Level-2 sleep discards weights from GPU entirely, and reloading from disk is not yet implemented.

The pre-existing test `test_multistage_sleep_h100` was calling `sleep(stage_ids=[0, 1], level=2)` followed by `wake_up(stage_ids=[0, 1])`. PR #4834 added the guard but did not update this test, so it started failing.

### Fix (one-line change)

In `tests/entrypoints/test_omni_sleep_mode.py`, change `level=2` to `level=1`:

```diff
-        acks = await engine.sleep(stage_ids=[0, 1], level=2)
+        acks = await engine.sleep(stage_ids=[0, 1], level=1)
```

Level-1 sleep offloads weights to CPU RAM and supports fast DMA restore via `wake_up()` — which is exactly what this test intends to exercise (sleep → wake → verify generation).

### Status

This fix appears to already be present in the current repository tree (the test now reads `level=1` at line 540). If the CI hasn't been re-run yet, please trigger `tests/entrypoints/test_omni_sleep_mode.py` to confirm.

### Related tests (already correct)

- `test_level2_sleep_wake_raises` — explicitly validates that `wake_up()` after `sleep(leve
- **state_updates**: {'draft_answer': '## Diagnosis\n\nThis is **not a bug in the engine** — it\'s a test that wasn\'t updated when PR #4834 landed.\n\n### Root cause\n\nPR [#4834](https://github.com/vllm-project/vllm-omni/pull/4834) (merged) added an intentional `NotImplementedError` guard in `AsyncOmni.wake_up()`:\n\n**`vllm_omni/entrypoints/async_omni.py` (~line 945):**\n```python\nif getattr(self, "_level2_sleeping", False):\n    raise NotImplementedError(\n        "wake_up() after sleep(level=2) is not yet implemented: weights were "\n        "discarded from GPU and reloading from disk is not yet supported. "\n        "Use sleep(level=1) instead, which offloads weights to CPU RAM "\n        "and supports fast DMA restore."\n    )\n```\n\nThis guard is **correct and intentional**: it prevents the silent corruption / CUDA illegal-memory-access crash that was reported in [#4473](https://github.com/vllm-project/vllm-omni/issues/4473) (Repro A). Level-2 sleep discards weights from GPU entirely, and reloading from disk is not yet implemented.\n\nThe pre-existing test `test_multistage_sleep_h100` was calling `sleep(stage_ids=[0, 1], level=2)` followed by `wake_up(stage_ids=[0, 1])`. PR #4834 added the guard but did not update this test, so it started failing.\n\n### Fix (one-line change)\n\nIn `tests/entrypoints/test_omni_sleep_mode.py`, change `level=2` to `level=1`:\n\n```diff\n-        acks = await engine.sleep(stage_ids=[0, 1], level=2)\n+        acks = await engine.sleep(stage_ids=[0, 1], level=1)\n```\n\nLevel-1 sleep offloads weights to CPU RAM and supports fast DMA restore via `wake_up()` — which is exactly what this test intends to exercise (sleep → wake → verify generation).\n\n### Status\n\nThis fix appears to already be present in the current repository tree (the test now reads `level=1` at line 540). If the CI hasn\'t been re-run yet, please trigger `tests/entrypoints/test_omni_sleep_mode.py` to confirm.\n\n### Related tests (already correct)\n\n- `test_level2_sleep_wake_rais
