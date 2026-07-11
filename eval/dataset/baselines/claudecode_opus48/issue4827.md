I have everything I need. The root cause is confirmed at `hunyuan_image3.py:1561-1563` in the checkout, and the config topology difference is clear from the two deploy YAMLs. Here's my maintainer response.

---

## Answer to issue #4827

**tl;dr — this is a config/model mismatch, not a model-support gap. The base `tencent/HunyuanImage-3.0` checkpoint must be served with the single-stage DiT config, not the two-stage Instruct/MoE config. There's also a real robustness bug we should fix: the AR init hard-codes the extended ratio tokens that only exist in the Instruct tokenizer.**

### Root cause

The crash is exactly where the traceback points, in `HunyuanImage3ForCausalLM.__init__` — `vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py:1561-1563`:

```python
self._start_ratio_id = tokenizer.convert_tokens_to_ids("<img_ratio_0>")
self._end_ratio_id   = tokenizer.convert_tokens_to_ids("<img_ratio_32>")
ratio_33 = tokenizer.convert_tokens_to_ids("<img_ratio_33>")
ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")
self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]   # <-- None + 1
```

The **base** `HunyuanImage-3.0` tokenizer only defines the standard aspect-ratio tokens `<img_ratio_0>` … `<img_ratio_32>`. The **extended** ratios `<img_ratio_33>` … `<img_ratio_36>` exist only in the `-Instruct` tokenizer. For the base checkpoint, `convert_tokens_to_ids("<img_ratio_36>")` returns `None`, so `ratio_36 + 1` raises `TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'`, and every worker dies during `load_model`.

@akshatvishu's analysis in the thread is correct, including the pointer to Tencent's reference, which guards this branch on `model_version == "HunyuanImage-3.0"` (the base/instruct split): the base version simply has no extended-ratio slice.

### Why the config matters

`hunyuan_image_3_moe.yaml` (`pipeline: hunyuan_image_3_moe`) is the **two-stage Instruct topology**: stage 0 = AR (tokenizer-owning, emits the CoT + `<img_size_*>`/`<img_ratio_*>` token stream), stage 1 = DiT, with AR→DiT KV reuse. Its own header says "HunyuanImage-3.0-Instruct deploy" (`hunyuan_image_3_moe.yaml:1`). Bringing up stage 0 instantiates the AR model that runs the ratio-token lookup above — which the base tokenizer can't satisfy.

`hunyuan_image3_dit.yaml` (`pipeline: hunyuan_image3_dit`) is the **single-stage DiT** path (`hunyuan_image3_dit.yaml:1-5`); it never constructs the AR stage, so it never touches the extended ratio tokens.

### Workaround (works today)

Serve the base checkpoint with the DiT config, as @FayeSpica already confirmed:

```bash
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml --trust-remote-code
```

Use `hunyuan_image_3_moe.yaml` only with `tencent/HunyuanImage-3.0-Instruct`, which needs the AR stage and ships the extended ratio tokens.

### Concrete fix we should land

Two parts, matching the proposal in the thread:

1. **Make the ratio-token init tolerant of a base tokenizer** (`hunyuan_image3.py:1561-1567`). Don't assume the extended ratios exist:

   ```python
   ratio_33 = tokenizer.convert_tokens_to_ids("<img_ratio_33>")
   ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")
   if ratio_33 is not None and ratio_36 is not None:
       self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]
   else:
       self._ratio_other_slices = []   # base checkpoint: no extended ratios
   ```

   The downstream `_all_ratio_ids` builder already iterates `_ratio_other_slices` (`hunyuan_image3.py:1566-1567`), so an empty list degrades cleanly. (`<img_ratio_0>`/`<img_ratio_32>` are present in the base tokenizer, so the `range()` on line 1565 is safe — only the 33–36 slice is Instruct-only.)

2. **Fail fast with a clear message** when the base checkpoint is loaded under the AR/MoE pipeline, rather than crashing deep in init — e.g. detect the missing `<img_ratio_36>` (or the model version) and raise something like *"HunyuanImage-3.0 (base) requires `hunyuan_image3_dit.yaml`; `hunyuan_image_3_moe.yaml` is for the -Instruct checkpoint."*

3. **Docs:** the deploy files should state which checkpoint each targets (base → `hunyuan_image3_dit.yaml`, Instruct → `hunyuan_image_3_moe.yaml`); right now both MoE and DiT headers say "Instruct," which is misleading for the DiT case.

### Status

The behavior is understood and there's a working path, so this specific bug report can be considered resolved/closed. Per @Gaohan123's request, the code hardening + docs clarification (items 1–3 above) should be tracked in a dedicated follow-up issue/PR — I don't have HunyuanImage-3.0-class hardware to run the base model end-to-end after the guard, so a maintainer with access should confirm generation quality on the DiT path once the guard lands.