### Review

- `vllm_omni/engine/orchestrator.py:1270-1273` **[unverified]** — When `diffusion_prompt` is a list with `len > 1`, the orchestrator falls through to submit without an explicit error, relying on StagePool to reject it. This is dead code for HunyuanImage3 (always returns a single dict) but `mammoth_moda2.ar2dit` might still hit it. Add an `else: raise ValueError(...)` branch to catch regressions early, or confirm that `mammoth_moda2.ar2dit` never returns multi‑element lists in practice.

- `vllm_omni/model_executor/stage_input_processors/hunyuan_image3.py:175` **[nit]** — The `logger.info` call unconditionally uses `len(generated_token_ids)`, but the helper `_extract_ratio_index` handles `None`. If `cumulative_token_ids` were ever `None`, this would raise `TypeError`. Change to `len(generated_token_ids or [])` for defensive safety.

- `vllm_omni/model_executor/stage_input_processors/hunyuan_image3.py:97` **[nit]** — The `prompt` parameter still carries `list` in its type annotation (`OmniTokensPrompt | TextPrompt | list | None`), yet the function now only ever uses `prompt[0]` when it’s a list. Update the docstring to explain the narrowing (e.g., “If `prompt` is a list, only the first element is used, matching the single-request contract.”) to avoid confusion.

- `tests/diffusion/models/hunyuan_image3/test_multi_resolution.py:559` **[nit]** — `_call_ar2diffusion` wraps the prompt in a list (`prompt=[prompt]`), which happens to work because the new code takes `prompt[0]`, but production always passes a single prompt object. Pass the fake prompt directly and drop the list wrapper to align the test with the real calling convention.

- `vllm_omni/model_executor/stage_input_processors/hunyuan_image3.py:116` **[nit]** — The fallback chain `getattr(output, "cumulative_text", None) or getattr(output, "text", "") or ""` treats an empty `cumulative_text` as falsy and lets the raw `text` leak through, which may unintentionally include untruncated tokens. Use `cumulative_text if cumulative_text is not None else ...` to truly “prefer” the accumulated field only when it exists.

- `vllm_omni/model_executor/stage_input_processors/hunyuan_image3.py:124-132` **[nit]** — The `prompt` normalization block (`isinstance(prompt, list)` → `prompt[0]`) is now structurally identical to the GLM‑Image bridge (`glm_image.py:229-234`). To prevent future drift, consider extracting this into a shared helper (e.g., `_first_prompt`) in a follow‑up.

**Verdict: APPROVE**