# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4826, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Summary

Thanks for the report @yenuo26. Since you confirmed on 2026-07-03 that updating to the latest vllm-omni commit resolved the issue and you can no longer reproduce it, we'll close this as **not reproducible**.

## What happened

All six failing tests in `tests/examples/online_serving/test_qwen2_5_omni.py` failed on the same assertion: the text output from the thinker stage did not contain the keywords `"baby"` or `"book"` (expected video description of `sample_demo_1.mp4`). Notably, the `"lamb"` keyword check (audio description) appears to have passed in every test — the traceback only shows the video-keyword assertion failing. This suggests video feature processing was affected specifically, not a general model regression.

## Resolution

The failure resolved itself after pulling the latest commits. No root-cause commit was identified because the diagnostic output (`text content is:` / `audio content is:`) was not captured while the failure was reproducible.

## If it recurs

Please capture and post:
1. The printed `text content is:` and `audio content is:` lines from the test output
2. The exact vllm-omni commit SHA (`git rev-parse HEAD`)
3. The full pytest output

This will let us distinguish between:
- **Video features dropped entirely** — the model generates text unrelated to the video
- **Keyword mismatch** — the model describes the video correctly but uses wording that doesn't contain "baby" or "book"

## Verification

```bash
# Re-run with current main:
pytest -sv tests/examples/online_serving/test_qwen2_5_omni.py --run-level full_model -k 'test_send_multimodal_request_001'
```

---

> Closing per @Gaohan123's suggestion. Please reopen if you encounter this again with the diagnostic output captured.

_Verified against vllm-omni tree at commit efc6b391 (reporter's) and current main; test file at `tests/examples/online_serving/test_qwen2_5_omni.py`._

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
