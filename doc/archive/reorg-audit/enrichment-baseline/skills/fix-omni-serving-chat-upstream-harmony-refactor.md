---
name: fix-omni-serving-chat-upstream-harmony-refactor
description: When upstream vLLM refactors OpenAIServingChat methods that OmniOpenAIServingChat overrides independently, restore removed methods locally.
trigger: AttributeError on OmniOpenAIServingChat for use_harmony, _should_stream_with_auto_tool_parsing, _should_check_for_unstreamed_tool_arg_tokens, parse_chat_output, or similar methods that upstream removed during Harmony/tool-parser refactoring. Often surfaces in chat_completion_stream_generator (e.g. ~line 1535) and fails the test_stream_finish_reason cases.
modules: [scheduler]
status: active
created_at: 2026-06-15
last_used_at: 2026-07-11
run_count: 20
---

## Diagnose
1. The failing test shows `'OmniOpenAIServingChat' object has no attribute 'X'`.
2. Check the upstream vLLM baseline (git log on vllm/entrypoints/openai/chat_completion/serving.py).
3. The method may have existed in upstream baseline commit but was removed during refactoring.
4. Omni's `chat_completion_stream_generator` is independently maintained (modality streaming) — it calls methods that were removed.

## Fix
1. Add `use_harmony: bool = False` as a class attribute.
2. Restore any removed methods as local copies on OmniOpenAIServingChat.
3. Check imports from `vllm.entrypoints.openai.parser.harmony_utils` — if `parse_chat_output` was removed, inline it.
4. Run the failing tests:
   - `tests/entrypoints/test_stream_finish_reason.py`
   - `tests/comfyui/test_comfyui_integration.py::test_understanding_node`

## Verification
- All tests pass after the fix.
- Pre-commit hooks pass (ruff format may inline removed imports).
