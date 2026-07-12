# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4957, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

Thanks for the detailed report! This was investigated by @ZhengWG and @amy-why-3459 and the team's conclusion is that no chunks are actually being dropped.

**Root cause: talker temperature variance, not chunk loss.**

The Qwen3-Omni-MoE pipeline uses **per-stage sampling parameters** defined in the deploy YAML (`vllm_omni/deploy/qwen3_omni_moe.yaml`). Your benchmark's `--temperature 0` only applies to **Stage 0 (Thinker)** — that's why text output is deterministic and identical across runs. **Stage 1 (Talker)**, however, runs at its YAML default of `temperature: 0.9` (line 46 of the deploy YAML):

```yaml
  - stage_id: 1
    ...
    default_sampling_params:
      temperature: 0.9
      top_k: 50
      max_tokens: 4096
      repetition_penalty: 1.05
```

The talker's codec-code generation is therefore non-deterministic — temperature 0.9 means the length of the generated audio codec sequence can vary naturally between runs. At higher concurrency, request interleaving changes timing and the exact order in which talker decode steps execute, which can shift the codec-code count slightly even with identical text output.

**Async-chunk framing can also contribute.**

The talker→code2wav path (`talker2code2wav_async_chunk` in `vllm_omni/model_executor/stage_input_processors/qwen3_omni.py`) batches codec codes into chunks of `codec_chunk_frames: 25` (with an initial chunk of 4). Partial chunks at the boundary are held until the final `is_finished` signal. When concurrency changes the request completion order relative to the chunk-polling background thread, the *point at which the final flush happens* can shift by up to `chunk_size-1` rows, slightly altering the total audio frame count.

**Verification.**
Per-hop chunk accounting showed zero dropped chunks under load. The maintainer confirmed the audio-duration gap is **not** a chunk-loss regression.

**Workaround.**
If you need fully deterministic audio length for testing, you can override the talker temperature in your deploy YAML:

```yaml
  - stage_id: 1
    ...
    default_sampling_params:
      temperature: 0.0   # pin to 0 for deterministic codec generation
      ...
```

**Related.**
A refactoring of the stage-input-processor layer is underway (#4872, RFC) that will clean up the async-chunk producer path and make chunk-accounting easier to inspect. The original concern about coalesced decode chunks being dropped was a reasonable hypothesis, but the evidence ruled it out.

Closing as not reproducible — reopen with fresh logs if you can demonstrate a deterministic gap with all stages pinned to temperature=0.

**Disposition:** close

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
