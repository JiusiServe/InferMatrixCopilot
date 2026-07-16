I've now verified agent 2's flagged paths directly. Its findings are real *latent* fragilities but do **not** fire in this issue's scenario, and they don't change the root cause. Here's my refined final position, incorporating that check:

---

## Addendum (after auditing the send/transport path)

I audited the streaming send path (`chunk_transfer_adapter.py`) for the "chunks dropped under load" hypothesis. To be fair to the title, there **are** two latent robustness gaps there — but neither is triggered by the reported run, and the observed audio-length difference is fully explained by talker sampling (section 1–3 above). Details:

**The transport does not drop or backpressure in the normal path.** `SharedMemoryConnector.put/get` (`shm_connector.py:42-169`) is key-addressed with per-key file locks — no bounded queue, no ring buffer, no drop-on-full; unconsumed segments just accumulate in `/dev/shm` until read in strict `chunk_id` order. The pending deques are unbounded (`base.py`).

**The two latent gaps (not fired here):**
- `chunk_transfer_adapter.py:331-339` — if `connector.put()` returns `success=False`, `put_req_chunk` is not incremented and the task is dropped with no retry/requeue. But `put()` returns `False` only when it *raises* (`shm_connector.py:83-85`): `/dev/shm` or fd exhaustion, or `flock` failure. At the reported scale — con=4, 16 prompts — none of that happens.
- `save_async` watermark guard `chunk_transfer_adapter.py:170-184` — I read this closely: it uses `_confirmed_num_computed_tokens = num_computed_tokens − num_output_placeholders` and skips only when the confirmed count goes **backwards** (`confirmed < already_sent`), i.e. a preemption/rollback. That is a **re-send dedup**, not a new-content drop — it skips only tokens already sent before the rollback. It does not lose forward progress.
- `stage_utils.py:189-197` overwrite-on-`FileExistsError` requires a `put_key` (`{req_id}_{stage}_{chunk_id}`) collision, i.e. external-req-id reuse — not present in a benchmark run.

**Why these definitively aren't the cause of #4957:**
1. **`Streaming continuity OK rate: 100.00%` at *both* con=1 and con=4.** Dropped/truncated mid-stream chunks would break continuity; they didn't.
2. The reporter's own per-hop chunk accounting found no drops.
3. The signature is textbook sampling non-determinism, not transport loss: greedy thinker text is bit-identical (2048 tokens), while the temp-0.9 talker's frame count — and thus audio duration — drifts, amplified by batch-invariance at con=4.

**Net:** closing as not-reproducible is correct; the audio-length gap is the temp-0.9 talker (decoupled from the request's `temperature 0` and `--ignore-eos`), not dropped chunks. Separately, the failed-`put`-without-retry and the strict, gap-intolerant `chunk_id` handshake at `chunk_transfer_adapter.py:331-339` are worth hardening (retry/requeue on `put` failure, or gap-tolerant chunk ids) so that genuine `/dev/shm`/fd pressure can't silently truncate audio — a good item to fold into the #4872 refactor, but a separate concern from this bug.