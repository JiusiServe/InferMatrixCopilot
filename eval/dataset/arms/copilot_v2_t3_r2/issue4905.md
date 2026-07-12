# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4905, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root Cause

This is **not a regression bug** — it's the **intended behavior** introduced by PR #4834 (merged). That PR added a safety guard that prevents `wake_up()` after `sleep(level=2)` because level-2 sleep discards model weights from GPU entirely, and reloading from disk is not yet implemented. Before #4834, calling `wake_up()` after `sleep(level=2)` would silently produce corrupted output (e.g., garbage tokens).

### Mechanism (code references)

- **`vllm_omni/entrypoints/async_omni.py:145`**: `self._level2_sleeping: bool = False` is initialized in `__init__`.
- **Line 947**: `sleep()` sets `self._level2_sleeping = True` when `level == 2`.
- **Line 953**: `wake_up()` checks `getattr(self, "_level2_sleeping", False)` and raises `NotImplementedError` **before** dispatching any RPCs to workers — this is the intentional guard.

### Why the test failed

`test_multistage_sleep_h100` was calling `sleep(level=2)` followed by `wake_up()`. PR #4834 added a dedicated regression test (`test_level2_sleep_wake_raises` at line 413) that correctly asserts the `NotImplementedError`, but the author forgot to update this existing test to use `level=1`.

## Fix

Change the sleep level from 2 to 1 in `test_multistage_sleep_h100`:

```diff
-        acks = await engine.sleep(stage_ids=[0, 1], level=2)
+        acks = await engine.sleep(stage_ids=[0, 1], level=1)
```

**Location**: `tests/entrypoints/test_omni_sleep_mode.py` line 547.

This fix is **already applied** on the current HEAD of the repository. The CI failure occurred on commit `ddba6de2` which predates the fix.

### Why level=1 works

- **Level 1**: Offloads weights to CPU RAM and supports fast DMA restore via `wake_up()`.
- **Level 2**: Discards weights from GPU entirely; `wake_up()` is intentionally blocked because reloading from disk is not yet implemented.

## Workaround

If you need to test sleep/wake cycles, always use `sleep(level=1)` — it provides the same VRAM reclamation benefit while supporting `wake_up()`.

## Verification

```bash
pytest tests/entrypoints/test_omni_sleep_mode.py::test_multistage_sleep_h100 -v -x
```

The test should pass on the current HEAD (where `level=1` is already applied).

## Related

- PR #4834: Added the `_level2_sleeping` guard and regression tests for #4473
- `test_level2_sleep_wake_raises` (line 413): the regression test that intentionally verifies the `NotImplementedError`
- `test_coordinated_cross_device` (line 323): also uses `level=2` but is `@pytest.mark.skip`-ped, so it won't cause CI failures

## draft_answer

## Root Cause

This is **not a regression bug** — it's the **intended behavior** introduced by PR #4834 (merged). That PR added a safety guard that prevents `wake_up()` after `sleep(level=2)` because level-2 sleep discards model weights from GPU entirely, and reloading from disk is not yet implemented. Before #4834, calling `wake_up()` after `sleep(level=2)` would silently produce corrupted output (e.g., garbage tokens).

### Mechanism (code references)

- **`vllm_omni/entrypoints/async_omni.py:145`**: `self._level2_sleeping: bool = False` is initialized in `__init__`.
- **Line 947**: `sleep()` sets `self._level2_sleeping = True` when `level == 2`.
- **Line 953**: `wake_up()` checks `getattr(self, "_level2_sleeping", False)` and raises `NotImplementedError` **before** dispatching any RPCs to workers — this is the intentional guard.

### Why the test failed

`test_multistage_sleep_h100` was calling `sleep(level=2)` followed by `wake_up()`. PR #4834 added a dedicated regression test (`test_level2_sleep_wake_raises` at line 413) that correctly asserts the `NotImplementedError`, but the author forgot to update this existing test to use `level=1`.

## Fix

Change the sleep level from 2 to 1 in `test_multistage_sleep_h100`:

```diff
-        acks = await engine.sleep(stage_ids=[0, 1], level=2)
+        acks = await engine.sleep(stage_ids=[0, 1], level=1)
```

**Location**: `tests/entrypoints/test_omni_sleep_mode.py` line 547.

This fix is **already applied** on the current HEAD of the repository. The CI failure occurred on commit `ddba6de2` which predates the fix.

### Why level=1 works

- **Level 1**: Offloads weights to CPU RAM and supports fast DMA restore via `wake_up()`.
- **Level 2**: Discards weights from GPU entirely; `wake_up()` is intentionally blocked because reloading from disk is not yet implemented.

## Workaround

If you need to test sleep/wake cycles, always use `sleep(level=1)` — it provides the same VRAM reclamation benefit while supporting `wake_up()`.

## Verification

```bash
pytest tests/entrypoints/test_omni_sleep_mode.py::test_multistage_sleep_h100 -v -x
```

The test should pass on the current HEAD (where `level=1` is already applied).

## Related

- PR #4834: Added the `_level2_sleeping` guard and regression tests for #4473
- `test_level2_sleep_wake_raises` (line 413): the regression test that intentionally verifies the `NotImplementedError`
- `test_coordinated_cross_device` (line 323): also uses `level=2` but is `@pytest.mark.skip`-ped, so it won't cause CI failures

---

## Step diagnostics

### fetch

### draft
- **status**: success
- **summary**: This is not a bug — it's the intended behavior of PR #4834, which added a safety guard in `AsyncOmni.wake_up()` that raises `NotImplementedError` after `sleep(level=2)`. The test `test_multistage_sleep_h100` was not updated when #4834 landed and was still calling `sleep(level=2)` followed by `wake_up()`. The fix is a one-line change in the test: use `sleep(level=1)` instead of `sleep(level=2)`. This fix is already applied on the current HEAD of the repo.
- **findings**: ['PR #4834 introduced `_level2_sleeping` flag tracking in `AsyncOmni.__init__` (vllm_omni/entrypoints/async_omni.py:145) and sets it to True in `sleep()` when `level == 2` (line 947).', '`wake_up()` (line 953) checks `_level2_sleeping` and raises `NotImplementedError` before any RPCs are dispatched, preventing silent corruption when weights were discarded from GPU.', 'The existing test `test_multistage_sleep_h100` was not updated: it called `sleep(level=2)` then `wake_up()`, which now correctly triggers the NotImplementedError guard.', 'A proper regression test `test_level2_sleep_wake_raises` (line 413) was added by PR #4834 and correctly asserts the error with `pytest.raises(NotImplementedError)`.', 'The current HEAD already has the fix: `sleep(stage_ids=[0, 1], level=1)` at tests/entrypoints/test_omni_sleep_mode.py line 547.', "The skipped test `test_coordinated_cross_device` (line 323,325) still uses `level=2` but is already disabled with `@pytest.mark.skip`, so it won't cause CI failures."]
- **files_read**: ['vllm_omni/entrypoints/async_omni.py', 'tests/entrypoints/test_omni_sleep_mode.py']
- **files_modified**: []
- **tests_requested**: ['pytest tests/entrypoints/test_omni_sleep_mode.py::test_multistage_sleep_h100 -v -x']
- **tests_run**: []
- **assumptions**: ['The issue was filed from commit ddba6de2 which predates the test fix; the current HEAD already has `level=1` applied.', 'The CI build (Buildkite #12074) ran the unfixed version of the test at that commit.']
- **blockers**: []
- **confidence**: high
- **failure_kind**: None
- **next_action**: The fix is already applied on HEAD (level=1). If the CI failure is still occurring on the latest commit, re-run the CI; otherwise this can be closed. The skipped test `test_coordinated_cross_device` also uses `level=2` in its sleep calls but is already disabled — if it's ever re-enabled, those `level=2` calls will need updating too.
- **answer_draft**: ## Root Cause

This is **not a regression bug** — it's the **intended behavior** introduced by PR #4834 (merged). That PR added a safety guard that prevents `wake_up()` after `sleep(level=2)` because level-2 sleep discards model weights from GPU entirely, and reloading from disk is not yet implemented. Before #4834, calling `wake_up()` after `sleep(level=2)` would silently produce corrupted output (e.g., garbage tokens).

### Mechanism (code references)

- **`vllm_omni/entrypoints/async_omni.py:145`**: `self._level2_sleeping: bool = False` is initialized in `__init__`.
- **Line 947**: `sleep()` sets `self._level2_sleeping = True` when `level == 2`.
- **Line 953**: `wake_up()` checks `getattr(self, "_level2_sleeping", False)` and raises `NotImplementedError` **before** dispatching any RPCs to workers — this is the intentional guard.

### Why the test failed

`test_multistage_sleep_h100` was calling `sleep(level=2)` followed by `wake_up()`. PR #4834 added a dedicated regression test (`test_level2_sleep_wake_raises` at line 413) that correctly asserts the `NotImplementedError`, but the author forgot to update this existing test to use `level=1`.

## Fix

Change the sleep level from 2 to 1 in `test_multistage_sleep_h100`:

```diff
-        acks = await engine.sleep(stage_ids=[0, 1], level=2)
+        acks = await engine.sleep(stage_ids=[0, 1], level=1)
```

**Location**: `tests/entrypoints/test_omni_sleep_mode.py` line 547.

This fix is **already applied** on the current HEAD of the repository. The CI failure occurred on commit `ddba6de2` which predates the fix.

### Why level=1 works

- **Level 1**: Offloads weights to CPU RAM and supports fast DMA restore via `wake_up()`.
- **Level 2**: Discards weights from GPU entirely; `wake_up()` is intentionally blocked because reloading from disk is not yet implemented.

## Workaround

If you need to test sleep/wake cycles, always use `sleep(level=1)` — it provides the same VRAM reclamation benefit while supporting `wake_up()`.

