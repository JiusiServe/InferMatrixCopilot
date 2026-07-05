Code inspection is sufficient here and the test run needs approval I'll skip — the contract is fully verifiable statically. My investigation is complete. Here's the review.

---

## Review: PR #4849 — `[image][bugfix] Fix HunyuanImage3 bridge request batching`

**Recommended verdict: APPROVE** (no blocking issues)

### Summary of what was validated

This is a clean, well-scoped bugfix. `ar2diffusion` in `vllm_omni/model_executor/stage_input_processors/hunyuan_image3.py` changed its contract from `list[dict]` (one payload per source output) to `dict | None` (one payload for the parent AR request). I verified the change is correct end-to-end:

**BLOCKER scan**

| Category | Result |
|---|---|
| Correctness | PASS |
| Reliability/Safety | PASS |
| Breaking Changes | PASS (internal bridge contract; sole caller updated) |
| Test Coverage | PASS (3 new unit tests + updated existing) |
| Documentation | PASS (docstring updated to match) |
| Security | PASS |

**Contract handling by the sole caller is correct.** The only non-test caller is `orchestrator.py:1224` (`_fn(diffusion_source_outputs, ...)`). It already handles the new return shape robustly:
- `None` → routes a terminal error output and cleans up (`orchestrator.py:1239-1263`) — matches the new "no parent output" return.
- `dict` → passed straight to `submit_initial/submit_update`.
- It still tolerates a `list` (`orchestrator.py:1264-1291`) for other bridges, so nothing else breaks.

**The single-output semantics are correct.** At `orchestrator.py:1211`, `diffusion_source_outputs = [output, *companion_outputs]` where `output` is the parent AR output — so `source_outputs[0]` is always the parent, and the CFG companions are correctly ignored here. Critically, CFG conditioning is wired through `cfg_kv_request_ids` on the diffusion sampling params (`_maybe_attach_cfg_companions`, `orchestrator.py:860-873`), **not** through extra bridge payloads. That confirms dropping the companion payloads is the right fix, not data loss.

**Mirrors the GLM-Image pattern accurately.** `glm_image.py:ar2diffusion` has the identical `dict[str, Any] | None` signature and `if not source_outputs: return None` guard, and `tests/.../test_glm_image.py:374` (`test_multiple_source_outputs_uses_first_payload_only`) is the exact same contract the PR now applies to HunyuanImage3.

**Tests updated consistently.** All `result[0]` / `len(result) == 1` assertions in the two touched test files were converted to the single-payload form, and the new tests cover the three relevant cases (single payload, parent-preferred-over-companion, empty→`None`). The `test_multi_resolution.py:370 len(result) == 2` I checked is unrelated (`Resolution.match()` returning a `(w,h)` tuple), not a stale reference.

### Non-blocking notes (optional, no comment needed)
- `hunyuan_image3.py` — log lines are now hardcoded to `"Request 0"`. Fine given one request per call, but slightly less useful than including `req_id`; the orchestrator already logs `req_id` alongside, so no action needed.
- The `requires_multimodal_data` parameter remains accepted-but-unused (pre-existing, not introduced here).

### What still lacks independent evidence
- I did not execute the test suite (bash approval was declined in this session). The change is fully verifiable by inspection, and the PR reports the two CPU unit files plus the online e2e (`test_image_to_image_alignment_online`) passing on the NPU stack with #4079/#4344 backported. If you want a local gate, run:
  `pytest tests/model_executor/stage_input_processors/test_hunyuan_image3_bridge.py tests/diffusion/models/hunyuan_image3/test_multi_resolution.py`

No comments to post — this is an approve.