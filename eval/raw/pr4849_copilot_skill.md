The change fixes a request-level batching contract mismatch by returning a single diffusion payload (or `None`) instead of a list, matching the GLM-Image bridge pattern. The updated tests cover the new return type and edge cases. No blocking issues.

**Findings**

- `vllm_omni/model_executor/stage_input_processors/hunyuan_image3.py:195`  
  Log message now hardcodes `Request 0` instead of the previous dynamic index. While correct for single-request processing, the fixed index may be less informative if the function is ever reused in a multi-request context. Non-blocking.

- The caller (orchestrator) must handle the `None` return. The PR description indicates this matches the existing GLM-Image bridge pattern, so the orchestrator should already expect `dict | None`. No risk of a breaking change at the orchestration layer.

- The new tests (`test_ar2diffusion_returns_one_request_payload_for_request_level_batching`, `test_ar2diffusion_uses_parent_output_when_companions_are_present`, `test_ar2diffusion_returns_none_without_parent_output`) are well-structured and cover the three key return scenarios.

**Verdict**: APPROVE