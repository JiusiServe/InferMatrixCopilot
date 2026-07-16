---
name: fix-test-parser_cls-missing
description: When a test creates OmniOpenAIServingChat via object.__new__() (bypassing __init__), the parser_cls attribute set by upstream's OpenAIServingChat.__init__ is missing. Add parser_cls=None to the test setup.
trigger: AttributeError: 'OmniOpenAIServingChat' object has no attribute 'parser_cls
modules: [scheduler, entrypoints]
status: active
created_at: 2026-06-16
last_used_at: 2026-07-11
run_count: 16
---

## Diagnose
1. Test creates `OmniOpenAIServingChat` via `object.__new__(OmniOpenAIServingChat)` which bypasses `__init__`.
2. Upstream `OpenAIServingChat.__init__()` sets `self.parser_cls = ParserManager.get_parser(...)`.
3. During rebase, `_create_chat_completion` was updated to use `self.parser_cls` instead of old `self.reasoning_parser_cls`.
4. Error: `AttributeError: 'OmniOpenAIServingChat' object has no attribute 'parser_cls'`

## Fix
Add `serving_chat.parser_cls = None` in the test function before the code path that accesses `self.parser_cls`. This is safe because the product code checks `if self.parser_cls is not None` before using it.

## Verification
```bash
python -m pytest tests/entrypoints/openai_api/test_serving_chat_speaker.py -xvs
```
