Here is my complete answer to issue #4891.

---

## Answer (as maintainer)

**tl;dr:** The bug report and root-cause analysis are correct. Closing this as a **duplicate is the right call** — it's the 5th and last call site tracked in #4809, and the fix belongs in #4808 (the DiT-loader PR), not in a new one. But #4808 was **closed without merging**, and the regression test #4810 added has a **coverage hole exactly at this call site**, so I want to flag two follow-ups so this doesn't silently regress.

### 1. The diagnosis is accurate

vLLM removed `QuantizationConfig.get_cache_scale` in v0.23.0, and the diffusion-side HunyuanImage3 loader (`HunyuanImage3Transformer2DModel.load_weights`) was still calling it. That method is reached through the outer `AutoWeightsLoader` set up in `pipeline_hunyuan_image3.py:458-462`, which delegates weight loading to the transformer's own `load_weights` (`hunyuan_image3_transformer.py:2125`). On any quantized (ModelOpt mixed FP8/NVFP4) checkpoint, the KV-cache scale tensors hit the removed API and the DiT worker crashes with the `AttributeError` you pasted — so the reproduction and the sm_120 / ModelOpt setup are entirely plausible.

### 2. Why the "duplicate" closure is correct

The five `get_cache_scale` call sites were enumerated and triaged in **#4809**:

- **#4810** (merged 2026-07-03) fixed **4 of 5**: the AR loader `hunyuan_image3.py` plus `mammoth_moda2`, `mimo_audio`, `qwen2_old` — with regression tests.
- **#4808** was scoped to the **5th** site — this exact file, `diffusion/.../hunyuan_image3_transformer.py` ("HunyuanImage3 DiT: drop redundant manual KV-cache scale loading", fixing #4806).

So #4891 describes precisely the gap #4808 exists to close. Routing it there rather than opening a parallel fix is correct.

### 3. The fix (what you proposed, and it's right)

Drop the dead branch — there is nothing to replace it with, because KV-cache scale names are already remapped on the fall-through path by `maybe_remap_kv_scale_name(name, params_dict)` (`hunyuan_image3_transformer.py:2343`), and the outer `AutoWeightsLoader` handles the `.output_scale` → `.attn.{k,v}_scale` renaming. This mirrors #4810's approach for the AR loaders. In our rebase branch the change is already in place — see `hunyuan_image3_transformer.py:2238-2239`, where the old call is gone and replaced with a comment pointing at the remap path.

### 4. Two things I'd ask before we consider this fully done

**(a) #4808 is `CLOSED` and `mergedAt` is null — it never merged.** If the DiT fix didn't land on `main` under a different PR, then main (at your `86bdcaf3d`) still carries the bug and closing #4891 as "duplicate of #4808" leaves users with no merged fix. Please confirm the DiT loader change is actually on `main` (either a re-opened/superseding #4808, or folded into #4597's trim). If not, this should be re-opened or a replacement PR filed.

**(b) The regression guard added by #4810 does not cover this file.** In `tests/model_executor/models/test_kv_cache_scale_mapper.py`, the `_STALE_API_FILES` list (lines 15-20) checks the AR `hunyuan_image3.py`, `mammoth_moda2`, `mimo_audio`, and `qwen2_old` — but **not** `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py`. That's the one file this whole issue is about, and it's exactly the one the test doesn't watch, which is likely how it slipped through in the first place. The DiT-loader fix should add that path to `_STALE_API_FILES` so `test_model_loaders_do_not_call_removed_get_cache_scale` fails if the call is ever reintroduced.

### Recommendation
Keep #4891 closed as a duplicate, but treat it as a signal that (a) the DiT fix must be confirmed merged to `main`, and (b) the diffusion transformer path must be added to the `_STALE_API_FILES` regression list. Both are one-line changes and close the loop on #4809 permanently.

---

Note on scope: my read-only checkout is the rebase branch `dev/vllm-align`, where the DiT fix is already applied — so I could verify the intended end state and the test gap, but I could **not** verify upstream `main`'s current state directly; that's why point 4(a) is phrased as a request to confirm rather than an assertion.