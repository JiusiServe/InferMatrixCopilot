# DRIFT_TRIAGE — dual-source divergences surfaced by the migration

Plan §9 risk 1: the parent orchestrator carried the same facts in multiple
places, and they drifted. Each entry here must receive a pre-cutover DECISION
(which side is truth for v3) recorded in place; unresolved entries block PR6.

## 1. Prompt builder maps vs config.sh maps (found in PR4b)

The parent's `prompts/builder.py` inlined its own copies of the module maps,
and they DIVERGED from `config.sh` (the operational source the shell tasks
used):

| Field | builder.py (prompt flavor) | config.sh (operational flavor) |
|---|---|---|
| `module_import_check` | prints `'OK'`, e.g. model_config imports 2 symbols | prints `'Model Config imports OK'`-style messages |
| `module_test_map.scheduler` | `["tests/distributed/"]` | adds `tests/diffusion/distributed/test_ulysses_uaa_perf.py` |
| `module_test_map.input_output` | 3 entries incl. `tests/engine/` | 4 entries incl. `test_async_omni_engine_input.py` |
| `module_test_map.worker_runner` | 3 entries | 5 entries incl. sleep-mode + qwen3 tts |
| `module_test_map.online_serving` | `tests/entrypoints/` (broad) | 4 explicit entries incl. `openai_api/` |
| `module_test_map.model_executor` / others | equal | equal |

Where each lives now:
- builder flavor → `adapters/vllm_omni/rebase/prompt_data.yaml` (prompt-render
  byte-parity; the goldens pin it against the parent builder's output).
- config.sh flavor → the manifest's `modules.*.{upstream_paths,test_paths}`
  (operational: commit assignment, path-sync, test selection).

**Decision needed before PR6:** whether v3 prompts should keep the builder's
(narrower) test lists for cache parity through validation and adopt the
operational lists at cutover, or unify immediately after the validation run.
Default recommendation: keep both flavors frozen through the §8 validation
comparison (byte-parity evidence), unify to the operational flavor in the
first post-cutover soak stage.

## 2. `local_paths` granularity (PR2/PR4b audit — DECIDED)

Rev 8 called for "the parent's authoritative module paths copied in". Audit
result: `local_paths` is consumed by prefix-matching scoping (review
attribution, `module_for_path`); replacing the coarse directory prefixes with
the parent's file lists would NARROW attribution and regress review coverage.
Decision (recorded in the manifest comment): `local_paths` = UNION of the
coarse prefixes and every parent `MODULE_OMNI_FILES` entry not covered by
them — a strict superset of the parent's rebase scope, no consumer loses
coverage. Pinned by `test_manifest_local_paths_cover_parent_module_map`.

## 3. `[[:space:]]` vs `[ \t]` in wheel-pin regexes (PR2 — accepted)

The shell's character class also matched `\r` (CRLF Dockerfiles). The port
uses `[ \t]`; unobservable on LF-normalized repos. Accepted; revisit only if
a CRLF `docker/Dockerfile.ci` ever appears.

## 4. config.sh §10 false-pass (pre-existing, from Rev 8)

Manifest slug missing from config.sh §10 → empty command → rc=0 "pass" in
the parent. The v3 substrate fails closed on empty commands; the
shell-golden comparison in PR5 will enumerate any slugs affected so the
cutover comparison isn't polluted by the parent's false passes. Decision at
PR5.
