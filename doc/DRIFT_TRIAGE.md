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

**DECISION (PR5, recorded; owner may veto at the PR6 gate):** keep both
flavors frozen through the §8 validation comparison — the prompt flavor is
byte-parity EVIDENCE (goldens pin it against the parent builder's own
output) and changing it mid-validation would invalidate the cache-parity
claim. Operational truth is the manifest (now pinned byte-for-byte against
the parent's LIVE §11 arrays by `test_shell_golden.py`). Unify: regenerate
`prompt_data.yaml`'s maps from the manifest in the first post-cutover soak
stage (PR7 cleanup), retiring the dual source.

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

## 4. config.sh §10 false-pass (pre-existing, from Rev 8) — DECIDED (PR5)

Manifest slug missing from config.sh §10 → empty command → rc=0 "pass" in
the parent. The PR5 shell-golden enumeration (live `.buildkite/cuda`
pipelines vs the captured §10 arrays, 2026-08-01) quantified it:

- live yaml builds **54** jobs; the parent's §10 defines **49**;
- **25 live slugs are ABSENT from §10** — every one FALSE-PASSES in the
  parent today (diffusion_batch/cache/cosmos3/distributed/gguf_plugin/
  model/offloader tests, entrypoints_test, 10 `full_moon_*` suites,
  tiny-model tests, tts_higgs-audio-v3/soulx-singer/voxcpm2, …);
- **20 §10 entries are stale** (no longer in the live yaml);
- 7 of the 29 intersecting slugs differ in command text (quoting churn
  plus real drift: e.g. `distributed_test` gained an `and L4` marker
  upstream; two multi-GPU X2I suites split their file lists).

**DECISION:** the live-yaml manifest builder is the ONLY operational
command source for v3 (the §10 static map is demonstrably ~46% stale).
The false-pass mechanism is structurally dead here — the builder DROPS
labeled steps with no runnable command and the run side classifies an
empty command as an infrastructure failure (`test_empty_command_never_
passes`). PR6 consequence: the §8 outcome-equivalence comparison must be
run over the MANIFEST-BUILT slug set; the parent's "pass" on the 25
missing slugs is vacuous and must not count as a baseline outcome.


## 5. Buildkite pipeline location: `.buildkite/cuda/` vs `.buildkite/` (PR4c)

The live vllm-omni tree nests its per-accelerator pipelines under
`.buildkite/cuda/` (siblings: `amd/`, `intel/`, `npu/`, `release/`); the
parent's `test_manifest.py` hardcodes `yaml_dir = omni / ".buildkite"` and
would find ZERO jobs against today's tree — every manifest it built there
would be empty. Our `yaml_dir` is adapter DATA
(`rebase.test_manifest.yaml_dir: .buildkite/cuda`), pinned to the live
layout; fixtures reproduce the nested layout. If the PR5 shell-golden
capture runs the parent against the live tree, expect its manifest step to
produce an empty set — compare against the parent's recorded run instead.

## 6. PR5 golden-capture sweep corrections (DECIDED in place)

The one-time capture surfaced adapter-data drifts, all fixed in the PR5
commits and pinned by `test_shell_golden.py`:

- `watchdog_patterns.yaml` was missing the parent's post-PR1 noise entry
  `"Released CuMem memory pool during shutdown"` (inventory bijection now
  enforced per tier, with the documented POSIX-class/escape translation).
- `modules.*.import_check` (parent MODULE_IMPORT_CHECK per-module smoke
  snippets) was absent from the manifest — added parent-verbatim.
- **THE ROUTING FLAVOR IS ITS OWN MAP.** `test_paths` carried two entries
  beyond §11 (`tests/engine/`, `tests/e2e/online_serving/`); a first
  attempt to trim them to §11-verbatim broke job→module ROUTING — the
  parent's `_assign_modules` scores against its OWN inline map (a third
  flavor whose broad prefixes are load-bearing: without
  `tests/e2e/online_serving/`, `platform`'s `tests/` swallowed 37/54 live
  jobs). Final resolution (reverses PR4c's "third copy unified onto the
  operational flavor"): the assignment map lives as its own adapter datum,
  `rebase.test_manifest.assignment_paths` (parent test_manifest.py inline
  map VERBATIM); `modules.*.test_paths` is §11-verbatim for shell test
  selection; the two flavors are never merged — merging in either
  direction changes scores. Pinned three ways: `assignment_paths` ==
  golden `assignment_map` (bytes); routing over a golden-derived fixture
  == the recorded behavioral replay (verified identical to the parent's
  own `_assign_modules` output at capture time); and a histogram guard
  that fails if `platform` ever swallows the set again.

## 7. §10 `CI_TEST_MODULE` declared vs computed routing (parent-internal)

The parent holds job→module in TWO places: §10's hand-maintained
`CI_TEST_MODULE` (consumed by the shell's failure routing) and the
computed `_assign_modules` output (consumed by module test plans). At
capture time they DISAGREE on 13 of 28 comparable slugs (e.g. the
`full_moon_*` doc/function suites: declared `online_serving`, computed
`platform`; `tts_qwen3-tts_base_test`: declared `worker_runner`, computed
`online_serving`). v3 reproduces the COMPUTED side (that is what fed
module plans and prompts). PR6 consequence: when comparing per-module
outcomes against parent artifacts that used the declared labels, map
through the golden's `assignment_routing`, not `CI_TEST_MODULE`.
