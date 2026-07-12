# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4826, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Verdict: Closed — cannot reproduce on latest

@yenuo26 confirmed on 2026-07-03 that after updating vllm-omni to the latest commit, all six failing tests pass. This was likely a transient regression on commit `efc6b391e` that was resolved by a subsequent update.

### What was happening

All failing tests (`test_send_multimodal_request_001/002/003`, `test_modality_control_001/002/003`, `test_stream_001`) use `--query-type use_mixed_modalities` with the default sample video (`sample_demo_1.mp4`). The tests assert the model's text output contains the keywords `"baby"` and `"book"` — expected content in a description of that video. On your old checkout, the model's output was missing those keywords.

### Root cause

Not determined — the actual text output was never shared, so we can't say whether video features were being dropped entirely or the model simply described the video with different wording. Since updating resolved it, the most likely explanation is a bug on that specific commit that was fixed shortly after.

### If it happens again

Please capture and share the **exact printed output** from pytest:

```
text content is: <...>
audio content is: <...>
```

These `print()` lines are already in the test (e.g. `test_qwen2_5_omni.py:63-64`). With that output we can tell whether:
- The model sees the video at all (video features being dropped)
- The model describes the video but uses different words (keyword fragility)

### Related note

The `"cherry blossom"` image-description assertion is already **commented out** in the test file with the note: *"There is currently an issue with incorrect image descriptions."* That is a separate, known limitation and not related to your report.

Closing as **not reproducible**. Reopen with the text/audio output if it recurs.

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
