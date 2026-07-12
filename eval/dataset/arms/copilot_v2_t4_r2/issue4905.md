# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4905, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root Cause

This is **not a bug in `wake_up()`** — the `NotImplementedError` is the **correct, intended behavior** introduced by PR [#4834](https://github.com/vllm-project/vllm-omni/pull/4834) to fix issue [#4473](https://github.com/vllm-project/vllm-omni/issues/4473) (silent corruption after level-2 sleep).

**What happened:** PR #4834 added a guard in `AsyncOmni.wake_up()` at:
- **`vllm_omni/entrypoints/async_omni.py:953`** — if `self._level2_sleeping` is `True` (set by `sleep(level=2)` at line 947), `wake_up()` raises `NotImplementedError`.

This was the fix for #4473 Repro A: previously, `sleep(level=2)` followed by `wake_up()` would silently produce corrupted output (e.g., `"!!!!!!!!!!"`). Now it correctly errors out.

However, the pre-existing test `test_multistage_sleep_h100` at:
- **`tests/entrypoints/test_omni_sleep_mode.py:~544`**

was written before this guard existed and calls:
```python
acks = await engine.sleep(stage_ids=[0, 1], level=2)  # ← this line
assert len(acks) == 2
await engine.wake_up(stage_ids=[0, 1])               # ← hits the new guard
```

PR #4834 added 3 new regression tests (`test_level2_sleep_wake_raises`, `test_partial_wake_blocks_generate`, `test_duplicate_wake_is_idempotent`) but did not update the existing `test_multistage_sleep_h100`.

## Fix

**One-line change** — use `level=1` instead of `level=2`:

```diff
-        acks = await engine.sleep(stage_ids=[0, 1], level=2)
+        acks = await engine.sleep(stage_ids=[0, 1], level=1)
```

`level=1` offloads weights to CPU RAM and supports fast DMA restore via `wake_up()`. This is the appropriate level for a sleep/wake lifecycle test — `level=2` (discard weights from GPU entirely, requiring disk reload) is intentionally unsupported for wake-up.

## Workaround

None needed — this is purely a CI test issue, not a user-facing bug. The `NotImplementedError` is the correct runtime behavior.

## Verification

```bash
pytest tests/entrypoints/test_omni_sleep_mode.py::test_multistage_sleep_h100 -v -s
```

## Thread Grounding

- @yenuo26 correctly identified that this appeared when #4834 merged
- @Flink-ddd requested a full sleep mode test CI run
- The `test_level2_sleep_wake_raises` regression test (same file, line 413) already validates that `sleep(level=2)` + `wake_up()` raises `NotImplementedError` — that test passes

## Additional Note

`test_coordinated_cross_device` (line 323/325) also uses `level=2` but is currently `@pytest.mark.skip`-ped, so it doesn't cause CI failures. It should receive the same fix before being un-skipped.

**Disposition:** close
