# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4905, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root Cause

The test `test_multistage_sleep_h100` (`tests/entrypoints/test_omni_sleep_mode.py`, line ~540) calls:

```python
acks = await engine.sleep(stage_ids=[0, 1], level=2)
```

followed by:

```python
await engine.wake_up(stage_ids=[0, 1])
```

PR [#4834](https://github.com/vllm-project/vllm-omni/pull/4834) intentionally made `wake_up()` raise `NotImplementedError` after `sleep(level=2)`. Here's the mechanism:

- `sleep(level=2)` sets `self._level2_sleeping = True` (`vllm_omni/entrypoints/async_omni.py:947`)
- `wake_up()` checks this flag at line 953 and raises:
  ```python
  if getattr(self, "_level2_sleeping", False):
      raise NotImplementedError(
          "wake_up() after sleep(level=2) is not yet implemented: weights were "
          "discarded from GPU and reloading from disk is not yet supported. "
          "Use sleep(level=1) instead, which offloads weights to CPU RAM "
          "and supports fast DMA restore."
      )
  ```

This guard was added to prevent **silent corruption** (issue [#4473](https://github.com/vllm-project/vllm-omni/issues/4473) Repro A) where `sleep(level=2)` + `wake_up()` would appear to succeed but produce garbage output.

The test uses the wrong sleep level for its lifecycle test. It should use `level=1` (offload to CPU RAM, supports DMA restore via `wake_up`), not `level=2` (discard weights entirely, reload not yet implemented).

## Fix

Change one line in `test_multistage_sleep_h100`:

```diff
-        acks = await engine.sleep(stage_ids=[0, 1], level=2)
+        acks = await engine.sleep(stage_ids=[0, 1], level=1)
```

**Note:** The current `main` checkout already shows `level=1` at this location. If your CI ran against an older commit or a merge-queue branch that still had `level=2`, re-running against the latest `main` should pass.

## Workaround

No user workaround needed — this is a test bug, not a product bug. The API correctly rejects `wake_up()` after `sleep(level=2)`.

## Verification

```bash
# Confirm the only level=2 uses are in the intentional regression test and the skipped test
grep -n 'level=2' tests/entrypoints/test_omni_sleep_mode.py
# Expected output (3 occurrences):
# 323: (skipped test_coordinated_cross_device, no wake_up call)
# 325: (skipped test_coordinated_cross_device, no wake_up call)
# 416: (test_level2_sleep_wake_raises, correctly expects NotImplementedError)

# Run the fixed test
pytest tests/entrypoints/test_omni_sleep_mode.py::test_multistage_sleep_h100 -v
```

## Related

- [#4473](https://github.com/vllm-project/vllm-omni/issues/4473) — original sleep/wake corruption bug that PR #4834 fixed
- [#4834](https://github.com/vllm-project/vllm-omni/pull/4834) — the PR that added the `_level2_sleeping` guard (merged)

@Flink-ddd @yenuo26 @Gaohan123 — the current tree already has `level=1`; please confirm the CI was on the right commit and re-trigger if needed.

**Disposition:** close

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
