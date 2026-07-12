# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4815, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Verdict: Not reproducible (self-closed)

@linyueqian has re-verified from scratch on a clean environment and found **zero reproductions across 55 trials** on current `main` (e4a2d367) and PR #4559 head (289107b1). All requests completed correctly in 3.4–4.9 seconds. The issue was self-closed as not reproducible.

---

## Summary of the original investigation

This was a methodical, well-instrumented report. The key isolation findings:

| What was ruled out | Why |
|---|---|
| PR #4559 preemption path | Single request never triggers preemption; resume-replay code is never exercised |
| codec_eos_token_id config/mask | Loads correctly as 2150, in-range, and the logit mask allows it to be sampled (`qwen3_tts_talker.py` `__init__`, `_codec_disallowed_mask`) |
| transformers version | Reproduced identically on 5.5.3 (vLLM 0.24 floor) and 5.12.1 |
| Codec tokenizer `create_causal_mask`/`cache_position` shim | Reference-audio encoder output codes were healthy (full codebook range, no degeneracy) |

**What isolated it:**
1. `x_vector_only_mode: true` → always completes correctly (bypasses the ICL prefill path)
2. `enforce_eager: true` on stage-0 → always completes correctly (bypasses CUDA graph/torch.compile)
3. Disabling chunked prefill alone → *did not* fix it (prefill was under `max_num_batched_tokens`)

This pointed at the vLLM 0.24 CUDA-graph/torch.compile forward path for this stage (`gpu_model_runner.py` line ~1172: `speculative_config.enforce_eager` gates graph usage), not at vllm-omni's prompt-construction code.

---

## Workaround (if the symptom recurs)

Pass `enforce_eager: true` on stage-0 via `--stage-overrides`:

```bash
vllm-omni serve Qwen/Qwen3-TTS-12Hz-1.7B-Base \
  --deploy-config vllm_omni/deploy/qwen3_tts.yaml \
  --trust-remote-code --omni \
  --host 127.0.0.1 --port 8902 \
  --stage-overrides '{"0": {"enforce_eager": true}}'
```

**Caveat:** This disables the CUDA graph/torch.compile speedup for *every* voice-clone request, not just the affected case. The default deploy config (`vllm_omni/deploy/qwen3_tts.yaml` line 11) intentionally keeps Stage 0 `enforce_eager` unset (defaults to `false`) so the talker runs cudagraph by default. Only use this workaround if the symptom is confirmed on a clean environment.

---

## Environmental note

The reporter's GPU (`nvidia-smi` reports "NVIDIA L20X") actually presents as compute capability 9.0 / 132 SMs / ~150GB — consistent with H200-class Hopper silicon. This GPU identity mismatch is unusual and could be a confound. If anyone attempts to reproduce on actual L20 hardware (compute capability 8.9), be aware the CUDA graph capture characteristics may differ.

---

## Reopen conditions

If the symptom recurs, please reopen with:
1. **Exact git commit** (`git rev-parse HEAD`)
2. **Clean environment** — fresh venv, fresh editable install, no prior runs
3. **`nvidia-smi` output** confirming the actual GPU identity
4. **The repro script** from the issue (already documented above)
5. **Number of trials and successes/failures**

## Linked

- PR #4709: vLLM 0.24 rebase (merged) — the rebase that introduced the v0.24 CUDA-graph/compile path
- PR #4559: Qwen3-TTS talker multi-token replay fix (merged) — ruled out as unrelated
- Issue #4559: original preemption crash this PR fixed

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
