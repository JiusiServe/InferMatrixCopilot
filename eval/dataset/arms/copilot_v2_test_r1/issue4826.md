# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4826, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Verdict: not reproducible — closing

@yenuo26 confirmed on 2026-07-03 that after updating vllm-omni to the latest commit the issue no longer reproduces. Closing per @Gaohan123's suggestion.

### What we know

All six failing tests hit the same assertion at `tests/examples/online_serving/test_qwen2_5_omni.py`:

```python
assert all(keyword in text_content for keyword in ["baby", "book"]), (
    "The output does not contain any of the keywords in video description."
)
```

The **single passing test** (`test_send_multimodal_request_002`) differs only in the prompt — it uses `--prompt "Analyze all the media content and provide a comprehensive summary."` instead of the default question `"What is recited in the audio? What is the content of this image? Why is this video funny?"` (from `get_mixed_modalities_query()` at `examples/online_serving/openai_chat_completion_client_for_multimodal_generation.py`).

This suggests the default prompt may not always elicit responses that contain the expected video-description keywords. Without the actual text/audio output from the failing runs, we cannot confirm whether video features were dropped entirely or the model described the video with wording that missed the keyword check.

### Fix / workaround

- **Proper fix**: Update to the latest commit. The reporter's version (`efc6b391`) predates a fix that landed between that commit and current HEAD (`ae2c25dc` on `dev/vllm-align`).
- **Workaround** (if the failure reappears): Use an explicit prompt that asks for a description (as `test_002` does) rather than relying on the default `"Why is this video funny?"`.

### Verification

```bash
pytest -sv tests/examples/online_serving/test_qwen2_5_omni.py --run-level full_model
```

### Reopen condition

Re-open if the failure reproduces on the latest commit **with the printed `text content is:` and `audio content is:` output attached**. This will let us determine whether the model is (a) dropping video features entirely, (b) describing the video with different wording, or (c) producing garbled output due to a whisper-small ASR mishearing in the audio-to-text conversion (`tests/helpers/media.py:convert_audio_file_to_text` defaults to `model_size="small"`).

### Caveat: whisper-small ASR

Note that `convert_audio_file_to_text` uses whisper-small by default. Per the repo maintainer guidance, audio/TTS similarity below 0.9 is often a whisper-small mishearing of short/quiet clips rather than a model regression — if the `cosine_similarity_text > 0.9` assertion ever fails alone (without the keyword assertion), re-check with whisper-large-v3 before flagging.

**Disposition:** close

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
