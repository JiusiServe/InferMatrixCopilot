I've completed my investigation. The subagent confirmed the tag-handling change is safe for both LLM and diffusion workers (the extra `"kv_cache"` tag is a silent no-op for diffusion; no crash). Here is my complete review.

---

# Review: PR #4834 — `[Bugfix][sleep mode]: guard generation on partial wake and ensure wake idempotency`

**Author:** Flink-ddd · **Base:** `main` · **State:** MERGED · +92/−6 across 3 files
**CI gates:** GitHub Actions (build 3.11/3.12, pre-commit, DCO) ✅, buildkite/vllm-omni ✅, intel/npu ✅; buildkite-amd ❌ (AMD lane failing — unrelated to inspect, but worth confirming it's not this change).

## Summary

The fix is well-motivated and the core control-plane logic is sound. Replacing the boolean `_is_sleeping` with a `_sleeping_tags` set correctly distinguishes "weights-only warm" from "fully warm," the `generate()` admission guard correctly rejects partial-wake requests before they reach CUDA (Repro B), the `_level2_sleeping` gate turns silent corruption into a clear error (Repro A), and the tag-filtering makes duplicate `wake_up()` a safe no-op (Repro C). I verified end-to-end that passing an explicit `["weights","kv_cache"]` list to the workers is semantically equivalent to the previous `tags=None` for both LLM and diffusion paths — no regression, no crash on the nonexistent diffusion `kv_cache` pool.

## Blocker scan

| Category | Result |
|---|---|
| Correctness | PASS (guard logic verified end-to-end through worker → vLLM allocator) |
| Reliability/Safety | ISSUE: default `sleep()` level bricks the engine (see #1) |
| Breaking Changes | Behavior change: default `sleep()`→`wake_up()` now hard-fails (was silent-corrupt) |
| Test Coverage | Regression tests exist but are hardware-gated; core logic never runs in CI (see #2) |
| Documentation | PASS (clear error messages; PR body thorough) |
| Security | PASS |

## Findings

### 1. (Major / footgun) Default `sleep()` level is `2`, and level-2 wake now permanently bricks the engine — `vllm_omni/entrypoints/async_omni.py:914`

`sleep(self, stage_ids=None, level: int = 2, ...)` defaults to **level 2**. After a bare `sleep()` (no explicit level), `_level2_sleeping=True` is set (`:946-947`), which makes **every** subsequent `wake_up()` raise `NotImplementedError` (`:953-959`) and **every** `generate()` raise `RuntimeError` (`:319-324`) — permanently, with no recovery path. So the out-of-the-box `sleep()` → `wake_up()` cycle is now unusable.

This PR is right to hard-fail level-2 wake (silent corruption is worse), but leaving `level=2` as the *default* means the common path breaks. The worker-side `sleep()` defaults to `level=1` (`worker/base.py:191`, `diffusion_worker.py:522`) and vLLM's convention is level 1. Recommend changing the orchestrator default to `level=1` (or making `level` required). This is the one change I'd want before merge.

### 2. (Test coverage) The three regression tests are gated behind `num_cards=2` H100/MI325 — the pure-Python guard logic never runs in standard CI — `tests/entrypoints/test_omni_sleep_mode.py:421,435,449`

All three new tests carry `@hardware_test(res={"cuda": "H100", "rocm": "MI325"}, num_cards=2)`, so they only execute on a 2-GPU box (confirmed by the PR body: manual 4×A100 run). But the logic they protect — the `generate()` rejection, the `NotImplementedError` on level-2, and the tag-filtering/idempotency in `wake_up()` — is pure control-plane Python that needs no GPU. A lightweight unit test that constructs the orchestrator with a stubbed `engine`/`collective_rpc` would exercise all three guards and actually run on every PR. As-is, these regressions are unprotected in the CI that gates merges.

### 3. (Minor) `tags=None` → explicit `["weights","kv_cache"]` silently drops any other-tagged allocations from a full wake — `vllm_omni/entrypoints/async_omni.py:961-964,982`

The vLLM allocator's `wake_up(None)` remaps **all** allocations, whereas `wake_up(["weights","kv_cache"])` only remaps those two tags. Any allocation under the allocator's `default` tag would be woken by the old `None` path but skipped now. No persistent state uses the `default` pool today, so there's no impact — but the "wake everything" intent is now silently coupled to `_sleeping_tags` containing exactly the full tag set. A short comment noting this assumption (or deriving the full-wake set from the allocator rather than a hardcoded pair) would prevent a future footgun.

### 4. (Minor / style) Dead defensive `getattr`/`hasattr` guards for always-initialized attributes — `async_omni.py:319,943,960,995,999,1010`

`_sleeping_tags` and `_level2_sleeping` are initialized unconditionally in `__init__` (`:144-145`), so `getattr(self, "_sleeping_tags", None)`, `if not hasattr(self, "_sleeping_tags")`, etc., can never take the fallback branch. They add noise and imply an initialization uncertainty that doesn't exist. Direct attribute access (`self._sleeping_tags`) reads cleaner.

### 5. (Nit) `CuMemTag` enum is only half-used — `vllm_omni/diffusion/data.py:1492`

The new enum populates `_sleeping_tags` in `sleep()`, but the user-facing `tags` argument and the `wake_up()` filtering compare raw strings (`t in _current_tags`). Either validate incoming `tags` against `CuMemTag` (catching typos like `"kvcache"`) or the enum buys little over string constants. Placement in `diffusion/data.py` is defensible since `OmniSleepTask`/`OmniWakeTask` live there, though a CuMem concept is broader than diffusion.

### 6. (Low, pre-existing) State can desync from reality

`_sleeping_tags` is marked fully-asleep (`:945`) and cleared on wake (`:994-996`) unconditionally, regardless of whether the sleep/wake RPCs actually succeeded on all workers. If a wake RPC partially fails, the orchestrator still records the tag as warm and `generate()` will then dispatch into a half-woken engine. The old code had the same unconditional-toggle behavior, and `is_sleeping()`'s docstring already concedes it "track[s] the requested state locally," so this isn't a regression — just worth a follow-up to reconcile against actual worker ACKs.

## Recommended verdict

**REQUEST_CHANGES** — for finding #1 only (change the default `sleep()` level to `1`, or require it explicitly; otherwise the default sleep/wake path bricks the engine). The fix itself is correct and a real safety improvement; #2 is a strong follow-up (add a no-GPU unit test so the guards run in CI), and #3–#6 are minor/optional. If you consider the level-2 default an intentional, separately-tracked API decision, this downgrades to **COMMENT**.

Note: the PR is already **MERGED**, so these are best delivered as a follow-up issue/PR rather than blocking this one. Per your instruction, I have **not** posted anything to GitHub.