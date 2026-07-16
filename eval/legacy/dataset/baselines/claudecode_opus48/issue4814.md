I now have a complete, precise picture of the root cause. Here is my answer as a maintainer.

---

## Answer to issue #4814

Thanks for the detailed log — the traceback points straight at the culprit.

### TL;DR

This is a **known incompatibility between the `cache_dit` block cache and Ulysses sequence parallelism** (`--ulysses-degree 2`) that existed around the `0.20.0` line. It has since been fixed. As @FayeSpica already verified, the exact command runs fine on **`v0.23.0rc1`**, so the fix is: **upgrade to `>= 0.23.0`**. If you must stay on `0.20.0`, the reliable workaround is to **drop `--cache-backend cache_dit`** (or drop the sequence-parallel degree) — details below.

### Root cause

The fatal line is inside `cache_dit`, not vllm-omni:

```
cache_dit/.../pattern_base.py", line 217, in _get_Fn_residual
    Fn_hidden_states_residual = hidden_states - original_hidden_states.to(...)
RuntimeError: The size of tensor a (512) must match the size of tensor b (1024) at non-singleton dimension 1
```

`512` vs `1024` is the giveaway: `1024` is the **full** video-token sequence and `512` is **half** of it, i.e. the per-rank Ulysses shard with `sp_size = 2`. So one tensor got sequence-parallel-split and the other didn't, and `cache_dit` then tried to subtract them.

Why does that happen? `cache_dit` wraps the whole transformer block stack. At the top of the cached region it snapshots `original_hidden_states = hidden_states`, runs the "Fn" blocks, and computes `residual = hidden_states - original_hidden_states` (`_get_Fn_residual`). For that subtraction to be valid, the snapshot and the block output must have the **same** sequence length.

In the `0.20.0`-era code, the hidden-state sequence-parallel **split was applied at the first transformer block's input** — i.e. entangled with the very blocks that `cache_dit` had already wrapped and whose input `cache_dit` had already snapshotted at full length (`1024`). The block then executed on the sharded slice (`512`), so `residual = 512 − 1024` → the size mismatch. The earlier warning in your log is the same mechanism misfiring:

```
WARNING [sequence_parallel.py:316] Expected tensor with 4 dims, got 3. Skipping split.
```

That "Skipping split" is the SP hook declining to shard a tensor whose rank didn't match what the plan expected, which is exactly how you end up with some tensors at `1024` and others at `512` in the same forward.

### How it was fixed

Current `main` shards the hidden states **once, up front, at a dedicated shard point placed *before* the `cache_dit`-wrapped blocks**, so every downstream `cache_dit` block wrapper sees a consistent *local* (`512`) tensor for both the snapshot and the output. You can see it in `vllm_omni/diffusion/models/wan2_2/wan2_2_transformer.py`:

- A dedicated `nn.Identity` shard point is created (`self._sp_shard_point = nn.Identity()`, line 940) and the `_sp_plan` shards on it (`"_sp_shard_point": {0: SequenceParallelInput(split_dim=1, expected_dims=3, ...)}`, lines 827–829).
- In `forward`, the split happens **before** the block loop (lines 983–988):
  ```python
  hidden_states = self.patch_embedding(hidden_states)
  hidden_states = hidden_states.flatten(2).transpose(1, 2)
  hidden_states = self._sp_shard_point(hidden_states)   # SP split here, up front
  ...
  for block in self.blocks[self.start_layer:self.end_layer]:
      hidden_states = block(...)                          # cache_dit sees local (512) tensors
  ```
  The code comment states the intent directly: *"Shard hidden_states before entering transformer blocks. This keeps CacheDiT block wrappers aligned with the local SP shard."* (lines 825–826). The VACE variant has the same treatment (`wan2_2_vace_transformer.py:215`, "Shard hidden_states via _sp_plan hook (before VACE, not at blocks.0)").

Because the shard is now cleanly separated from the cached blocks, `cache_dit`'s residual subtraction always operates on same-length tensors and the crash is gone — consistent with the successful `v0.23.0rc1` run in the thread.

### What to do

1. **Recommended:** upgrade to **`>= 0.23.0`** (e.g. the `quay.nju.edu.cn/ascend/vllm-omni:v0.23.0rc1` image @FayeSpica used) and re-run your command unchanged. Also make sure your `vllm` / `vllm-ascend` versions match the vllm-omni release — see the version-matching note in vllm-project/vllm-omni#2223.

2. **If you must stay on `0.20.0`,** either:
   - **Drop `--cache-backend cache_dit`** and keep `--ulysses-degree 2 --cfg-parallel-size 2`. The error lives entirely inside the `cache_dit` residual path; without it, the sharded blocks run normally. You lose caching speedup but SP still works. **This is the simplest workaround.**
   - **Or** keep `cache_dit` but set `--ulysses-degree 1` (drop sequence parallelism), so there's no shard/no-shard mismatch. You can still use `--cfg-parallel-size 2` for parallelism across the CFG branches.

Note this is not Ascend-specific — it's a generic `cache_dit` + Ulysses-SP ordering bug — so the fix and workarounds apply regardless of the backend.

I'll mark this as fixed-in-`>=0.23.0`. Please reopen if you can still reproduce the mismatch on a current release with `cache_dit` + `--ulysses-degree 2`.