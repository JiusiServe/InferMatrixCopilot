# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4815, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

Thanks for the thorough investigation and the clean re-verification, @linyueqian. Closing as not reproducible is the right call given 55/55 clean trials on a fresh environment.

## Summary of what was found (for anyone hitting similar symptoms)

**Symptom:** Qwen3-TTS Base ICL voice-clone (`task_type=Base` + `ref_audio`, no `x_vector_only_mode`) intermittently runs to `max_tokens` (4096) producing ~319 s of garbled/stuttering audio with no EOS.

**Isolation (credits to @linyueqian):**
- Not the #4559 resume path (single request, no preemption).
- Not config/logit-mask: `codec_eos_token_id` = 2150, mask allows it (`qwen3_tts_talker.py` `compute_logits()`).
- Not a transformers regression (reproduced on 5.5.3 and 5.12.1).
- Not the codec tokenizer `create_causal_mask` shim (ref-audio codes healthy).
- **Workaround 1:** `x_vector_only_mode: true` — skips ICL, uses explicit `trailing_text`/`talker_text_offset` streaming signal.
- **Workaround 2:** `--stage-overrides '{"0": {"enforce_eager": true}}'` — disables CUDA-graph/torch.compile for stage-0, pointing at vLLM 0.24's compiled forward path as the trigger.

**Resolution:** Could not be reproduced on a clean checkout + fresh venv. 55/55 trials all completed correctly (3.4–4.9 s). Most likely a one-off environment artifact.

**If it recurs:** please reopen with a clean repro including git commit, `pip freeze`, and GPU details. The `enforce_eager` workaround is available but not recommended as a permanent fix since it costs the graph/compile speedup.

**Related areas to watch:** The `talker_mtp_graph_safe = True` flag in `qwen3_tts_talker.py:327` and the `cudagraph_mode` gating TODO at line 340 (#4923) — if the issue is a CUDA-graph capture nondeterminism, refactoring that gating into the runner may surface it more cleanly.

**Disposition:** close

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
