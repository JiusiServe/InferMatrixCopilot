# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4905, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Diagnosis

This is a **test-only regression** introduced by **PR #4834** ([Bugfix][sleep mode]: guard generation on partial wake and ensure wake idempotency).

### Root cause

**`vllm_omni/entrypoints/async_omni.py`**, `wake_up()` method (line ~945):

```python
if getattr(self, "_level2_sleeping", False):
    raise NotImplementedError(
        "wake_up() after sleep(level=2) is not yet implemented: weights were "
        "discarded from GPU and reloading from disk is not yet supported. "
        "Use sleep(level=1) instead, which offloads weights to CPU RAM "
        "and supports fast DMA restore."
    )
```

This guard is **correct and intentional** — `sleep(level=2)` discards weights from GPU, and reload from disk is not implemented. PR #4834 added this to prevent silent corruption (issue #4473).

However, the PR missed updating the existing test **`test_multistage_sleep_h100`** (`tests/entrypoints/test_omni_sleep_mode.py`, line ~545 at the failing commit) which called:

```python
acks = await engine.sleep(stage_ids=[0, 1], level=2)   # ← should be level=1
assert len(acks) == 2
await engine.wake_up(stage_ids=[0, 1])                  # ← raises NotImplementedError
```

### Fix

Change `level=2` → `level=1` in `test_multistage_sleep_h100`. Level-1 offloads weights to CPU RAM and supports `wake_up()` via fast DMA restore — which is the intended workflow for this test.

**This fix is already applied in the current tree** — the live checkout shows `level=1`.

A dedicated regression test **`test_level2_sleep_wake_raises`** (line 413) already exists and correctly asserts that `sleep(level=2)` + `wake_up()` raises `NotImplementedError`.

### Workaround (for the old commit)

```python
# In test_multistage_sleep_h100, change:
acks = await engine.sleep(stage_ids=[0, 1], level=2)
# to:
acks = await engine.sleep(stage_ids=[0, 1], level=1)
```

### Verification

```bash
# Run the fixed test
pytest tests/entrypoints/test_omni_sleep_mode.py::test_multistage_sleep_h100 -v -x

# Confirm the level-2 regression test still passes
pytest tests/entrypoints/test_omni_sleep_mode.py::test_level2_sleep_wake_raises -v -x

# Full sleep-mode suite
pytest tests/entrypoints/test_omni_sleep_mode.py -v --timeout=600
```

### Related

- **PR #4834** — the fix that introduced the guard (merged, confirmed)
- **Issue #4473** — the original silent-corruption bug that #4834 fixed
- **`test_level2_sleep_wake_raises`** — the dedicated regression test for level-2 behavior added by #4834

**Disposition:** close

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
