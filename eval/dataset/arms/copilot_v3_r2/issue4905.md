# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4905, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

### Root cause
PR #4834 added intentional `NotImplementedError` at `vllm_omni/entrypoints/async_omni.py:953-958` to block `wake_up()` after `sleep(level=2)` (fix for #4473). The test `test_multistage_sleep_h100` at `tests/entrypoints/test_omni_sleep_mode.py:547` (commit `ddba6de2`) was calling `engine.sleep(level=2)` then `wake_up()` without being updated, so it hits the intentional guard.

### Fix
Change `level=2` to `level=1` in `test_multistage_sleep_h100` at `tests/entrypoints/test_omni_sleep_mode.py`. This is already applied on current main (`238fc0a6`). The test line now reads: `acks = await engine.sleep(stage_ids=[0, 1], level=1)`.

### Workaround
If you cannot rebase to current main, manually change the one line in your checkout: `s/level=2/level=1/` on the `engine.sleep(...)` call inside `test_multistage_sleep_h100`.

### Preconditions
None beyond having a checkout at or past the fix commit on main.

### Verification
pytest tests/entrypoints/test_omni_sleep_mode.py::test_multistage_sleep_h100 -v -x --timeout=600

### Prevention
When adding a guard/NotImplementedError/assertion that changes API contract, grep all in-repo callers before merge. In this case: `grep -n 'level=2' tests/entrypoints/test_omni_sleep_mode.py` would have flagged the existing caller before the PR landed. Consider adding a pre-merge CI lint check or PR template checklist item for 'swept all callers of changed API paths'.

### Disposition
close — the fix is already on main; reopen condition: if `test_multistage_sleep_h100` still fails with `level=1` on current main (indicating a different root cause beyond the sleep-level mismatch)

### Additional context
## Diagnosis

**Root cause**: This is a **test-only bug** — the production code is behaving correctly. PR [#4834](https://github.com/vllm-project/vllm-omni/pull/4834) intentionally added a guard in `wake_up()` that raises `NotImplementedError` after `sleep(level=2)`. This was the fix for [#4473](https://github.com/vllm-project/vllm-omni/issues/4473) Reproduction A (silent data corruption when waking from level-2 sleep before disk reload was implemented).

**What broke**: The test `test_multistage_sleep_h100` was calling `engine.sleep(stage_ids=[0, 1], level=2)` and then `engine.wake_up()` — this hit the new guard. The test was not updated when #4834 merged.

### Evidence

- **Guard (intentional)**: `vllm_omni/entrypoints/async_omni.py:953-958`:
  ```python
  if getattr(self, "_level2_sleeping", False):
      raise NotImplementedError(
          "wake_up() after sleep(level=2) is not yet implemented: weights were "
          "discarded from GPU and reloading from disk is not yet supported. "
          "Use sleep(level=1) instead, which offloads weights to CPU RAM "
          "and supports fast DMA restore."
      )
  ```

- **Test at CI commit** `ddba6de2`, `tests/entrypoints/test_omni_sleep_mode.py:547`:
  ```python
  acks = await engine.sleep(stage_ids=[0, 1], level=2)   # ← hits the guard on wake_up
  await engine.wake_up(stage_ids=[0, 1])
  ```

- **Fixed test on current main** (`238fc0a6`):
  ```python
  acks = await engine.sleep(stage_ids=[0, 1], level=1)   # ← level=1 allows wake_up
  await engine.wake_up(stage_ids=[0, 1])
  ```

- **Dedicated regression test** `test_level2_sleep_wake_raises` (line 413-418) already validates the `NotImplementedError` for level-2:
  ```python
  await llm_engine.sleep(stage_ids=[0], level=2)
  with pytest.raises(NotImplementedError, match="sleep\\(level=2\\)"):
      await llm_engine.wake_up(stage_ids=[0])
  ```

## Sleep level semantics

| Level | Behavior | `wake_up()` supported? |
|-------|----------|------------------------|
| 1 | Offload weights to CPU RAM (fast DMA restore) | ✅ Yes |
| 2 | Discard weights from GPU entirely (requires disk reload) | ❌ No (NotImplementedError) |

## Fix

The fix is already on main: change `level=2` → `level=1` in `test_multistage_sleep_h100`. This test exercises the multi-stage sleep/wake lifecycle and should use level-1 (the working path). Level-2 is separately covered by `test_level2_sleep_wake_raises`.

## Verification

```bash
# Run the failing test against current main — should pass:
pytest tests/entrypoints/test_omni_sleep_mode.py::test_multistage_sleep_h100 -v -x --timeout=600

# Verify the level-2 regression test still passes:
pytest tests/entrypoints/test_omni_sleep_mode.py::TestOmniSleepMode::test_level2_sleep_wake_raises -v -x --timeout=600
```

## Prevention

When adding a new guard/`NotImplementedError`/assertion that changes API contract, sweep all existing callers — especially tests — that exercise the guarded path. PR #4834 added the guard and a new regression test but missed the existing `test_multistage_sleep_h100` caller. A `grep 'level=2' tests/` before merge would have caught this.

---

Thanks @yenuo26 for flagging this and @Flink-ddd for the quick triage. The fix is already on main — no further code changes are needed. Closing.
