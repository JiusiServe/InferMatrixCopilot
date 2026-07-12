# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4905, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Diagnosis

**Root cause:** PR #4834 ([Bugfix][sleep mode]: guard generation on partial wake and ensure wake idempotency) added a deliberate `NotImplementedError` guard in `AsyncOmni.wake_up()` when called after `sleep(level=2)`. The pre-existing test `test_multistage_sleep_h100` was not updated and still called `sleep(level=2)` → `wake_up()`, triggering the new guard.

### Code path

1. `sleep(level=2)` at `vllm_omni/entrypoints/async_omni.py:947` sets `self._level2_sleeping = True`
2. `wake_up()` at line 953 checks this flag and raises:
   ```python
   if getattr(self, "_level2_sleeping", False):
       raise NotImplementedError(
           "wake_up() after sleep(level=2) is not yet implemented: weights were "
           "discarded from GPU and reloading from disk is not yet supported. "
           "Use sleep(level=1) instead, which offloads weights to CPU RAM "
           "and supports fast DMA restore."
       )
   ```

### Why this is correct behavior

Level-2 sleep **discards** weights from GPU entirely. Reloading them from disk is not yet implemented (it's a follow-up item noted in PR #4834). The `NotImplementedError` is intentional — it replaces the previous silent corruption (garbage output like `!!!!!!!!!!`) reported in issue #4473.

### The actual bug

The test `test_multistage_sleep_h100` at `tests/entrypoints/test_omni_sleep_mode.py:506` should use `level=1` (CPU-RAM offload with DMA restore), not `level=2`. PR #4834 correctly added a regression test `test_level2_sleep_wake_raises` that expects the `NotImplementedError`, but missed updating this older test.

## Fix

**Already applied in the current tree:** `test_multistage_sleep_h100` now uses `sleep(stage_ids=[0, 1], level=1)` — verified against the live checkout.

If you're still seeing the failure, ensure your CI is running against a tree where `tests/entrypoints/test_omni_sleep_mode.py` line ~540 reads:
```python
acks = await engine.sleep(stage_ids=[0, 1], level=1)
```
not `level=2`.

## Workaround (for users)

If you need `wake_up()` to work, use `sleep(level=1)`:
```python
await engine.sleep(stage_ids=[0, 1], level=1)   # offload to CPU RAM
await engine.wake_up(stage_ids=[0, 1])           # DMA restore — supported
```

## Verification

```bash
pytest tests/entrypoints/test_omni_sleep_mode.py::test_multistage_sleep_h100 -v -x
```

## Related

- PR #4834 — the change that added the guard
- Issue #4473 — the original sleep/wake corruption bug fixed by #4834
- `test_level2_sleep_wake_raises` — regression test that correctly expects this `NotImplementedError`

**Disposition:** close

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
