Good, the agent confirmed key context. Let me now compile the complete review.

---

## vLLM-Omni PR #4849 — Post-Merge Review

**PR:** `[image][bugfix] Fix HunyuanImage3 bridge request batching` by **Celeste-jq**  
**Status:** Merged into `main` | **Fixes:** #4832  
**Files:** 3 changed (+163 / −133)

### BLOCKER Scan

| Category | Result |
|----------|--------|
| Correctness | PASS |
| Reliability/Safety | PASS |
| Breaking Changes | PASS |
| Test Coverage | PASS |
| Documentation | PASS |
| Security | PASS |

### Summary

This PR fixes a `ValueError` in HunyuanImage3 image editing caused by request-level batching (#4079). The `ar2diffusion` bridge was returning `list[dict]` (one dict per source output, including CFG companions). The orchestrator fed this list to `StagePool`, which now rejects list-prompt batching. The fix is correct: return `dict | None` for a single parent request — matching the GLM-Image bridge pattern and the orchestrator's existing contract.

The orchestrator (`orchestrator.py:1264-1291`) already handles both list and dict returns, so compatibility is maintained. The `None` return path (empty source_outputs) is handled at `orchestrator.py:1239-1263`.

### Inline Comments

**`vllm_omni/model_executor/stage_input_processors/hunyuan_image3.py:165`** — Hardcoded request index in log message:

```python
logger.warning(
    "[ar2diffusion] Request 0: ratio_index=%d out of range [0,%d), keeping prompt size %dx%d",
```

The `"Request 0"` is hardcoded now that the loop is gone. This is technically accurate (always the first/only request) but will look odd in logs if someone debugs a multi-request session and sees every warning say "Request 0". Consider dropping the request index from the message entirely since the function now operates on exactly one request.

**`vllm_omni/model_executor/stage_input_processors/hunyuan_image3.py:97`** — `requires_multimodal_data` parameter is unused:

The parameter `requires_multimodal_data` is accepted in the signature but never read in the function body. The old code also didn't use it, so this is pre-existing, but it's dead weight. Either plumb it through (like GLM-Image's `streaming_context` parameter) or remove it.

### What Was Validated

- **Return type compatibility:** The orchestrator handles `dict | None` (new) and `list[dict]` (old/other bridges) through separate code paths — no regression risk.
- **CFG companion handling:** The fix correctly uses `source_outputs[0]` as the parent and ignores companions. Verified by new test `test_ar2diffusion_uses_parent_output_when_companions_are_present`.
- **Empty source_outputs:** Returns `None`, which the orchestrator routes to an error output. Verified by new test `test_ar2diffusion_returns_none_without_parent_output`.
- **Prompt normalization:** Handles list, dict, namedtuple, and `None` prompts — equivalent to the old loop-based normalization.
- **CI gates:** DCO, pre-commit, build (3.11/3.12), vllm-omni CI all green. ReadTheDocs green. AMD/NPU CI failures are pre-existing / infrastructure (unrelated to this change).
- **Pattern match with GLM-Image:** The new implementation mirrors `glm_image.py:ar2diffusion` (same return type, same `source_outputs[0]` pattern, same `None` guard).

### What's Not Covered

- **`mammoth_moda2.py` still returns `list`:** The `ar2dit` bridge for MammothModa2 still returns `list[OmniTokensPrompt]`. It doesn't share the same function name (`ar2diffusion`) so it's not directly affected, but it may have the same list-prompt batching issue under #4079. Separate follow-up.

### Recommended Verdict: **APPROVE** (post-merge — no action needed)

The fix is correct, well-tested, and matches the established pattern. The two inline notes above are non-blocking observations.