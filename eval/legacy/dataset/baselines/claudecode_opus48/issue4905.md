I have everything I need. Here's my answer as a maintainer.

---

## Answer to #4905

**TL;DR:** This is not a product bug — it's a stale test that was left asserting the *old* (buggy) contract. PR #4834 deliberately made `wake_up()` raise `NotImplementedError` after `sleep(level=2)`, but the pre-existing `test_multistage_sleep_h100` still called `sleep(level=2)` → `wake_up()`, so on merge CI it now (correctly) hits that guard and fails. The fix is a one-line test change: use `level=1`. This is already in `main`, so the issue can stay **closed**.

### Root cause

`@yenuo26` correctly bisected it to **#4834** (`[Bugfix][sleep mode]: guard generation on partial wake and ensure wake idempotency`, merged 2026-07-05). That PR fixed the silent-corruption / CUDA-illegal-access failure modes from #4473. As part of it, level-2 sleep was made a control-plane hard stop:

`vllm_omni/entrypoints/async_omni.py:946-947` — `sleep()` sets the flag when level 2 is requested:
```python
if level == 2:
    self._level2_sleeping = True
```

`vllm_omni/entrypoints/async_omni.py:953-959` — `wake_up()` refuses to proceed while that flag is set:
```python
if getattr(self, "_level2_sleeping", False):
    raise NotImplementedError(
        "wake_up() after sleep(level=2) is not yet implemented: weights were "
        "discarded from GPU and reloading from disk is not yet supported. ..."
    )
```

This is **intended behavior**. Level-2 sleep frees the weight allocation entirely (not just offloading to CPU RAM like level 1), so there is nothing to DMA back — reloading from disk is a documented follow-up. Raising early prevents the exact silent-corruption path (Repro A in #4834: post-wake generation emitting `!!!!!!!...`).

The problem is that #4834 added new regression tests for this contract but did **not** update the older `test_multistage_sleep_h100`, which still drove the now-forbidden sequence. Before #4834 the test happened to pass (with corrupt-but-non-crashing wake); after the merge, the same call path deterministically raises `NotImplementedError`. Hence "Merge CI" is red — a test/behavior mismatch, not a regression in the engine.

### The fix (already applied on `main`)

`test_multistage_sleep_h100` was switched to level-1 sleep, which offloads weights to CPU RAM and supports fast DMA restore — so the sleep → wake → generate round-trip is actually valid:

`tests/entrypoints/test_omni_sleep_mode.py:544`
```python
acks = await engine.sleep(stage_ids=[0, 1], level=1)   # was: level=2
assert len(acks) == 2
await engine.wake_up(stage_ids=[0, 1])
async for _ in engine.generate("verify", ...):
    pass
```

The level-2 contract is now covered by a dedicated, correctly-asserting regression test instead:

`tests/entrypoints/test_omni_sleep_mode.py:410-420` — `test_level2_sleep_wake_raises` does `sleep(level=2)` and asserts `pytest.raises(NotImplementedError, match="sleep\\(level=2\\)")`, alongside `test_partial_wake_blocks_generate` (Repro B) and `test_duplicate_wake_is_idempotent` (Repro C).

### Guidance for users hitting this at runtime (not just CI)

If your workload needs to sleep and later resume the *same* weights, use **`sleep(level=1)`**. Level 1 keeps weights in CPU RAM and wakes fast. Reserve `level=2` for cases where you will tear the engine down (or where reloading from disk lands as a future feature) — calling `wake_up()` after it is intentionally unsupported today and will raise. Note also the companion admission guard added in the same PR: `generate()` is now rejected with a `RuntimeError` if any tag is still asleep (`async_omni.py:319-324`), so partial wakes fail loudly at the Python layer instead of crashing the CUDA context.

**Recommendation:** keep #4905 **closed** as resolved by the test fix. No engine code change is warranted; full level-2 wake (disk reload) remains a tracked follow-up from #4834/#4473.