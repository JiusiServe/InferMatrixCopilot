# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4957, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root Cause: Talker stage uses YAML temperature, not request temperature

This is **not a bug** — it's the expected behavior of the Qwen3-Omni-MoE multi-stage sampling-parameter flow.

The pipeline has three stages, each with its own `default_sampling_params` in `qwen3_omni_moe.yaml`:

| Stage | Role | YAML `temperature` |
|-------|------|--------------------|
| 0     | thinker (text) | **0.0** |
| 1     | talker (audio codes) | **0.9** |
| 2     | code2wav (waveform) | 0.0 |

When you pass `--temperature 0` to `vllm bench serve`, that request-level parameter only overrides the **comprehension stage** (stage 0, the thinker). This is by design in [`serving_chat.py:_build_sampling_params_list_from_request`](https://github.com/vllm-project/vllm-omni/blob/main/vllm_omni/entrypoints/openai/serving_chat.py#L1139) which calls `_apply_request_overrides` only on the stage where `is_comprehension=True`. The talker stage (stage 1) always uses its YAML-configured `temperature: 0.9`.

### Why this explains your observations

1. **Text output is identical** (2048 tokens in both runs) because the thinker runs at temp=0.0 — deterministic.
2. **Audio duration varies** (637s vs 580s) because the talker at temp=0.9 samples audio codes non-deterministically via its CFM (Conditional Flow Matching) decoder. Different code sequences → different audio lengths.
3. **100% streaming continuity OK rate** in both runs confirms no chunks were dropped.
4. The apparent correlation with concurrency is coincidental — the variance comes from the talker's random seed differing between runs, not from load-induced chunk loss.

### Workaround: deterministic audio

If you need deterministic audio output, modify the deploy YAML:

```yaml
# In qwen3_omni_moe.yaml, under stage 1:
default_sampling_params:
  temperature: 0.0   # was 0.9
  top_k: 50
  max_tokens: 4096
  repetition_penalty: 1.05
```

Or pass per-stage sampling params via `extra_body`:

```json
{
  "sampling_params_list": [
    {"temperature": 0.0},
    {"temperature": 0.0},
    {"temperature": 0.0}
  ]
}
```

### Related

- This sampling-param propagation behavior is being addressed in the refactoring tracked by #4872.
- Closing comment from @ZhengWG: per-hop chunk accounting confirmed no drops; the gap was "likely stale environment state plus talker length variance."

**Disposition:** close

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
