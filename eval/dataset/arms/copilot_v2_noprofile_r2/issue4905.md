# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4905, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root cause

**`vllm_omni/entrypoints/async_omni.py` line ~945** — the `wake_up()` method has a guard:

```python
if getattr(self, "_level2_sleeping", False):
    raise NotImplementedError(
        "wake_up() after sleep(level=2) is not yet implemented: weights were "
        "discarded from GPU and reloading from disk is not yet supported. "
        "Use sleep(level=1) instead, which offloads weights to CPU RAM "
        "and supports fast DMA restore."
    )
```

This guard was added by **PR #4834** ([Bugfix][sleep mode]) to fix issue #4473 (silent corruption after level-2 sleep). However, the existing test `test_multistage_sleep_h100` was calling `sleep(stage_ids=[0,1], level=2)` followed by `wake_up()` — the test was not updated to match the new behavior.

## Mechanism

1. `sleep(level=2)` sets `self._level2_sleeping = True` (async_omni.py `sleep()` method, `if level == 2:` block)
2. `wake_up()` checks `_level2_sleeping` first thing and raises `NotImplementedError`
3. The test was exercising a path that PR #4834 intentionally blocked

## Fix

Change `level=2` to `level=1` in `test_multistage_sleep_h100`. Level 1 offloads weights to CPU RAM and supports `wake_up()` via DMA restore. This fix is already in the current `main` tip.

**Before (broken):**
```python
acks = await engine.sleep(stage_ids=[0, 1], level=2)
```

**After (fixed):**
```python
acks = await engine.sleep(stage_ids=[0, 1], level=1)
```

## Verification

```bash
pytest tests/entrypoints/test_omni_sleep_mode.py::test_multistage_sleep_h100 -k '1' -v
```

## Related

- PR #4834 — introduced the guard (merged, correct behavior)
- Issue #4473 — the original bug that PR #4834 fixed
- `test_level2_sleep_wake_raises` — correctly validates `NotImplementedError` is raised after `sleep(level=2)`

**Disposition:** close

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
