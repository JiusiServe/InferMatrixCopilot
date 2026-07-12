# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4957, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Triage: not-reproducible / by-design — closed by maintainer

### Root cause

The audio-duration gap is **not** caused by dropped streaming chunks. It is explained by the talker (stage 1) running at `temperature: 0.9` in the deploy YAML, which is independent of the request-level `--temperature 0`.

**File:** `vllm_omni/deploy/qwen3_omni_moe.yaml`, lines 46–50:
```yaml
  - stage_id: 1          # ← the talker
    ...
    default_sampling_params:
      temperature: 0.9   # ← stochastic!
      top_k: 50
      max_tokens: 4096
```

Compare with stage 0 (the thinker) at line 34:
```yaml
  - stage_id: 0          # ← the thinker
    ...
    default_sampling_params:
      temperature: 0.0   # ← deterministic
```

### Mechanism

The request-level `--temperature 0` is applied **only to the comprehension stage** (stage 0, thinker). This is by design in `vllm_omni/entrypoints/openai/serving_chat.py`:

```python
def _build_sampling_params_list_from_request(self, request):
    ...
    for idx, default_params in enumerate(default_params_list):
        if idx == comprehension_idx:                         # ← only stage 0
            params = self._apply_request_overrides(default_params, request)
        else:
            params = default_params.clone()                  # ← talker gets YAML 0.9
```

So the talker always samples with temperature 0.9 regardless of the request temperature. At temperature 0.9 with top_k=50, different runs (and even same-prompt runs at different concurrency due to different scheduling order / random state) produce different-length codec token sequences, which the code2wav decoder maps to different audio durations.

Your data confirms the text side is deterministic: **total generated tokens = 2048** in both runs. But audio duration varies: 637 s (con 1) vs 580 s (con 4). The ~9% spread is consistent with temperature-0.9 variance.

### Verification by maintainer

> *"Per-hop chunk accounting shows no chunks are dropped under load; the original gap was likely stale environment state plus talker length variance (talker runs at YAML temp=0.9, not the request's temperature=0)."* — @ZhengWG, closing comment

Streaming continuity OK rate is **100%** in both your runs, independently confirming no chunk loss.

### Fix (for deterministic audio)

Create a modified deploy YAML (e.g. `qwen3_omni_moe_deterministic.yaml`) and set stage 1 temperature to 0.0:

```yaml
  - stage_id: 1
    default_sampling_params:
      temperature: 0.0   # changed from 0.9
      top_k: 50
      max_tokens: 4096
      repetition_penalty: 1.05
```

Then serve with:
```bash
vllm serve /home/admin/model --omni --async-chunk \
    --deploy-config path/to/qwen3_omni_moe_deterministic.yaml \
    --port 8090
```

Alternatively, pass per-stage sampling params via `extra_body.sampling_params_list` in the API request.

### Workaround (without changing YAML)

Use `sampling_params_list` in `extra_body` to override stage 1 temperature at request time:
```json
{
  "extra_body": {
    "sampling_params_list": [
      {},
      {"temperature": 0.0}
    ]
  }
}
```

### Verification command

Re-run your benchmark after the fix — audio duration should be identical between concurrency 1 and concurrency 4:
```bash
vllm bench serve --omni --host 127.0.0.1 --port 8090 \
    --backend openai-chat-omni --endpoint /v1/chat/completions \
    --dataset-name random --random-input-len 4000 --random-output-len 128 \
    --num-prompts 16 --max-concurrency ${con} --ignore-eos \
    --temperature 0 --extra-body '{}' \
    --percentile-metrics "ttft,e2el,audio_rtf,audio_ttfp" --metric-percentiles 99
```

### Cross-reference

- hsliuustc0106 linked this to refactoring PR #4872 (unresolved — may be internal or not yet public).
- If you can reproduce a systematic audio-shortening at concurrency 4 even with talker temperature 0.0, please re-open with those results and we'll investigate the chunk-coalescing path.

### Unrelated / red herrings

- The `numpy==2.3.5` in the environment is above the repo's `<2.5` pin but the issue is not numpy-related.
- The `--run-level` is not set, defaulting to `core_model` (DUMMY weights) — this is fine for benchmarking but would produce garbage audio for listening tests; unrelated to duration variance.

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
