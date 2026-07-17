---
name: resolve-moss-tts-nano-load-weights-conflict
description: How to resolve rebase conflicts in moss_tts_nano load_weights() where upstream drain-only collides with omni's eager-init pattern
trigger: Rebase conflict in vllm_omni/model_executor/models/moss_tts_nano/modeling_moss_tts_nano.py load_weights method between upstream drain-only and omni full from_pretrained loading
modules: [model_executor]
status: active
created_at: 2026-06-10
last_used_at: 2026-07-11
run_count: 24
---

## Diagnose

1. Open the conflicting file and find `<<<<<<< HEAD` ... `>>>>>>>` markers in `load_weights()`
2. HEAD side: simple drain-only (just `for _ in weights: pass`)
3. Omni side: full `from_pretrained` loading with `_transformers_keys_to_ignore_compat()` wrapper
4. Check if `__init__` already eagerly loads models via `from_pretrained`

## Fix

1. **Take HEAD side for load_weights** — weights are already loaded eagerly in `__init__`, so `load_weights` just needs to drain the iterator:
   ```python
   def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]) -> set[str]:
       # Weights are populated in __init__ via from_pretrained; drain the
       # iterator and report all params as loaded. Not called under
       # load_format=dummy (DummyModelLoader randomises params in place).
       for _ in weights:
           pass
       return {name for name, _ in self.named_parameters()}
   ```

2. **Move `_transformers_keys_to_ignore_compat()` wrapper to `__init__`** — wrap both `from_pretrained` calls:
   - `AutoModelForCausalLM.from_pretrained(...)` — LM loading
   - `AutoModel.from_pretrained(...)` — audio tokenizer loading

3. Verify: no conflict markers, syntax valid, imports work
