I have enough to confirm the root cause directly in the code. Here's my maintainer answer.

---

## Answer to #4842

**This is not a bug in vllm-omni — the test was run at the wrong run-level, so it loaded random/dummy weights. `invalid` is the correct resolution.** The follow-up comments (@akshatvishu, @yenuo26) are right; here is the exact code path that explains why.

### What the output is telling you

The garbage is the classic signature of an uninitialized model:

- Text stage: `Joe\n Joe\n Joe…` repeated forever — a randomly-initialized LM collapsing onto one token.
- Audio stage: `Yn ymwneud yw'r llwyddiad…` — Welsh-flavored noise from a dummy code2wav/talker.

Both stages are running with **no real weights loaded**, so the semantic assertions (`"baby"`, `"book"`, and audio↔text cosine similarity) can never pass.

### Why it happened: `--run-level` defaults to `core_model`

The `--run-level` option defaults to `core_model` and is **completely independent of the `pytest.mark.full_model` marker** on the test:

- `tests/helpers/fixtures/run_args.py:4-11` — `--run-level` defaults to `"core_model"`.
- `tests/examples/online_serving/test_qwen3_omni.py:26` — the module is marked `pytest.mark.full_model`, but that marker is only a **selection/categorization** filter. It does *not* set the run-level. Selecting the test by node ID (as in your command) leaves `--run-level` at its default `core_model`.

At `core_model`, the `omni_server` fixture rewrites the deploy config to fake everything:

- `tests/helpers/runtime.py:2829-2832` — for `core_model` it swaps in a **tiny model** (`resolve_tiny_model_path`) *and* rewrites the stage config via `stage_config_path_for_run_level`.
- `tests/helpers/stage_config.py:713-717` → `_add_dummy_load_format` (`stage_config.py:670-681`) — for `core_model` it patches **every stage** in the deploy YAML to `load_format: dummy`.

That is exactly what @akshatvishu captured in the debug log: all three stages (thinker / talker / code2wav) show `'load_format': 'dummy'`. As noted, PR #4354 extended this dummy-weight behavior to the online-serving path, which is why the online test now also skips real weights at `core_model`.

So `core_model` is a **plumbing/smoke test** (does the 3-stage pipeline wire up, schedule, and stream?) — it deliberately does **not** load real weights and cannot produce meaningful text or audio. Only `advanced_model` / `full_model` strip the dummy `load_format` so real weights load (`stage_config.py:684-710`, and the assertion helpers only demand a real transcript at those levels — `tests/helpers/assertions.py:94, 480, 547, 727`).

### Fix / how to run it correctly

Run this test with the full-model run-level so real weights are loaded:

```bash
pytest -s -v \
  "tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0]" \
  --run-level=full_model
```

Requirements for a meaningful pass:
- Real `Qwen/Qwen3-Omni-30B-A3B-Instruct` weights available/cached.
- Enough GPU memory for all three stages (the config splits gpu_mem_util 0.55 / 0.3 / 0.1 across thinker/talker/code2wav). The `@hardware_test` decorator declares H100×2 / MI325; an A100 works for local runs if it has the capacity, but the resource declaration is why CI schedules it on H100.
- The video path in the test body (`--video-path /rebase/vllm-omni/sample_demo_1.mp4`) must actually exist on your machine.

### Summary
Keep it closed as **invalid**. There's no code defect here — running a `full_model`-marked accuracy test at the default `core_model` run-level loads dummy weights by design, which produces the `"Joe Joe Joe"` / Welsh-noise output and the `AssertionError`. Re-run with `--run-level=full_model` (plus real weights) and the semantic + similarity assertions will be exercised properly.

One genuine ergonomics gap worth a separate tracking issue (not a bug in this test): a test hard-marked `full_model` that is silently downgraded to dummy weights at the default run-level is a footgun. A small guard — e.g. having the `omni_server` fixture emit a loud warning (or `skip`) when a `full_model`-marked test is collected at `core_model` — would have turned this into an obvious "you're at the wrong run-level" message instead of a confusing accuracy failure.