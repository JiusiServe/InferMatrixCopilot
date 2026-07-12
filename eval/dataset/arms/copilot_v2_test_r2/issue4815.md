# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4815, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

Thanks for the thorough investigation and for closing the loop, @linyueqian. To summarize the outcome for anyone who finds this thread:

**Verdict: not reproducible.** After your initial report (intermittent EOS failure on Qwen3-TTS Base ICL voice-clone, running to `max_tokens` with garbled/looping output), you re-verified from scratch on a clean environment and got **55/55 clean trials** (35 on main @ `e4a2d367`, 20 on #4559 head @ `289107b1`). The most likely cause was a contaminated test session — hours of repeated code patches, dependency version changes, and at one point shared GPU usage.

**Key findings from your isolation work (still useful if this recurs):**

1. **Root cause pointer:** The bug was specific to the CUDA-graph/torch.compile compiled forward path on stage-0. Setting `--stage-overrides '{"0": {"enforce_eager": true}}'` reliably prevented the runaway, while disabling chunked prefill alone did nothing. This points at a vLLM 0.24 compilation/CUDAGraph interaction, not vllm-omni's prompt-construction code.

2. **Ruled out:** PR #4559's resume-replay path (never exercised for single-request, no-concurrency repro), codec EOS token (2150, in-range), logit mask, transformers version (reproduced on both 5.5.3 and 5.12.1), and the known transformers 5.9 `create_causal_mask`/`cache_position` shim.

3. **Workaround if it recurs:** Use `x_vector_only_mode: true` (skips ICL conditioning, uses per-step streaming signal) or `--stage-overrides '{"0": {"enforce_eager": true}}'` (disables CUDA graph on stage-0 at the cost of the graph/compile speedup).

**Environment note for future reference:** Ubuntu 22.04.5, Python 3.12.13, torch 2.11.0+cu129, vLLM 0.24.0, transformers 5.12.1. GPU reported as NVIDIA L20X but CUDA runtime shows H200-class Hopper (compute capability 9.0).

Closing as not reproducible per your self-closure. Happy to reopen if it recurs with a clean repro.

**Disposition:** close

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
