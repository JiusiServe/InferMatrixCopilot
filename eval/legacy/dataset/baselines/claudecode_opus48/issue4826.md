I have enough to write a thorough maintainer response. Here is my complete answer to issue #4826.

---

## Answer to #4826 — [Bug]: H800 local CI fail, Qwen2.5-Omni, returned text missing video description ("baby"/"book")

Thanks for the report, and thanks @IneshReddy249 for jumping on it. Closing as **not-a-standing-bug was the right call** — but since this touched CI I want to leave a post-mortem so we (and the next person who hits it) understand *why* updating to a newer commit made it disappear, rather than chalking it up to flakiness.

### What the test actually checks

All six failing cases (`test_send_multimodal_request_001/003`, `test_modality_control_001/002/003`, `test_stream_001`) drive the same `use_mixed_modalities` request and then assert keywords from each modality appear in the thinker's text/audio output:

- `tests/examples/online_serving/test_qwen2_5_omni.py:66` → `["baby", "book"]` come from the **video** (`sample_demo_1.mp4`, the baby-with-a-book demo clip, default URL at `examples/online_serving/openai_chat_completion_client_for_multimodal_generation.py:55`).
- `:71` → `"lamb"` comes from the **audio** (`mary_had_lamb`).
- `:69-70` → the image keyword (`cherry blossom`) is already **commented out** because image descriptions are known-unreliable here.

The request packs all three modalities in a fixed order — audio, image, video, then the text question (`...client_for_multimodal_generation.py:311-319`), and the prompt asks the model to answer them in that same order ("What is recited in the audio? What is the content of this image? Why is this video funny?"). So the model narrates **audio first, video last**.

That ordering is the tell. Your run failed the `baby`/`book` (video, last) check specifically. Since the thinker samples greedily (`temperature=0, seed=42`), this is deterministic — not a sampling wobble — which is exactly why the failure was reproducible for you and then vanished on a clean bump. A genuine phrasing mismatch ("infant" instead of "baby") wouldn't reliably fix itself on an update; a config/code change would.

### Likely root cause: the video embedding was being split by chunked prefill

Look at the setup log in your report:

```
INFO vllm.config.scheduler:scheduler.py:252 Chunked prefill is enabled with max_num_batched_tokens=2048.
```

At your commit (`efc6b391`) the qwen2.5-omni CI deploy overlay ran the **thinker (stage 0) with `max_num_batched_tokens=2048`**. `sample_demo_1.mp4` sampled at the default fps expands to *far* more than 2048 vision tokens, so the video's contiguous multimodal placeholder block was guaranteed to straddle several prefill chunks. Splitting a single multimodal item's placeholders across chunk boundaries is a fragile path in the encoder-cache / mm-embedding merge — the tail frames of the video effectively don't get attended to, so the thinker "sees" the audio and image but the video content drops out. Result: the description contains `lamb` but never reaches `baby`/`book`. That matches your symptom precisely.

The current tree has already changed exactly this knob. In `tests/helpers/stage_config.py:264-296`, the `qwen2_5_omni` CI overlay now runs the thinker with:

```python
"stage_id": 0,
"max_model_len": 16384,
"max_num_batched_tokens": 16384,   # was 2048 at efc6b391
```

16384 is sized to prefill the whole audio+image+video+text prompt in a **single** pass, so the video embedding is no longer split and its features survive. That is the change that made it un-reproducible for you after updating — not luck.

(Corroborating evidence that the team knows 2048 is only safe when outputs don't matter: the `qwen2_5_omni_thinker_only` overlay still uses `max_num_batched_tokens: 2048` and explicitly notes at `tests/helpers/stage_config.py:581-585` that it's fine there *because that test only checks the engine inits, not the generated text*.)

### Recommendation / status

- **Keep it closed.** The fix (16384-token single-chunk prefill for the thinker) is already in `_CI_OVERLAYS` and you've confirmed it no longer reproduces.
- **If it recurs**, the one thing that would nail it down is the diagnostic @IneshReddy249 asked for: paste the printed `text content is:` / `audio content is:` lines. If the text describes the video but phrases it differently → it's the assertion; if the video is simply absent from an otherwise-complete answer → it's a prefill/mm regression again, and the first thing to check is whether `max_num_batched_tokens` on the thinker got lowered below the total multimodal prompt length (or set `async_chunk`/chunked-prefill off for stage 0 as a workaround).
- **Hardening worth doing (separate low-pri task):** the `assert all(keyword in text ...)` checks are inherently brittle against free-form generation — the image keyword was already disabled for this reason (`:69-70`). We should move the video/audio checks to the same `cosine_similarity_text` semantic comparison the test already imports and uses for text-vs-audio parity (`:73`), so a correct-but-reworded description ("child"/"reading material") doesn't red the build. That would remove the residual flakiness class independent of the prefill fix.

**Workaround for anyone on an older checkout who still hits this:** raise the thinker stage's `max_num_batched_tokens` (and `max_model_len`) so the full multimodal prompt fits in one prefill chunk — e.g. `16384` as in the current CI overlay — or update past the commit that changed the qwen2.5-omni CI overlay.