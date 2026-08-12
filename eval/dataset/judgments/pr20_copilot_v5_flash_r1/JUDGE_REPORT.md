# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)

Judge: claude-sonnet-5 (blind, randomized order, 3 replicates x 10 items = 60 verdicts)

## Wins
- copilot_v2: 31
- opus_baseline: 29
- tie: 0

## Mean rubric scores

| arm | actionability | gap_hit | precision | recall |
|---|---|---|---|---|
| copilot_v2 | 0.82 | 0.13 | 0.69 | 0.49 |
| opus_baseline | 0.71 | 0.13 | 0.82 | 0.48 |

## Per-verdict detail

| item.rep | winner | margin | rationale (head) |
|---|---|---|---|
| pr4762.r1 | opus_baseline | clear | Both candidates independently flag the trust_remote_code True→False default flip in config_factory.py, which maps to the one clearly-confirmed GT concern (author's own 'this looks like a bug' comment) |
| pr4762.r2 | opus_baseline | slight | Both candidates independently surface the trust_remote_code default flip (True→False), which matches the ground-truth's confirmed bug (author: 'this looks like a bug'). X repeats this single finding f |
| pr4762.r3 | opus_baseline | clear | Both candidates catch the trust_remote_code default-flip issue (matching the ground-truth inline comment where the author admits 'this looks like a bug'), but X repeats this single finding four times  |
| pr4777.r1 | copilot_v2 | slight | Ground truth has no substantive reviewer concerns (two LGTMs plus a bot comment confirming validation passed), so recall is vacuously satisfied by both. Both independently surface the same real gap —  |
| pr4777.r2 | copilot_v2 | slight | Both candidates independently surface the same real, high-value finding missed by the human reviewers (LGTM-only): the two hardware-gated reliability test files under tests/dfx/reliability/invalid_par |
| pr4777.r3 | opus_baseline | slight | Both candidates converge on the same real, high-value gap the human reviewers (who only said LGTM) missed: two reliability test files (test_invalid_image_generation.py, test_invalid_image_editing.py)  |
| pr4804.r1 | copilot_v2 | slight | Neither candidate surfaced the actual headline findings from the ground-truth reviewers (the High-severity stream-slot leak on abort, the cumulative/delta silent-rewind bug, the ceil-division/input_le |
| pr4804.r2 | copilot_v2 | clear | Neither candidate surfaces the ground truth's confirmed high-severity bugs (stream-slot leak on abort, cumulative/delta chunk flip, ceil-division length bug, v2-tokenizer model_type collision), so bot |
| pr4804.r3 | copilot_v2 | slight | Neither candidate surfaces the ground truth's core technical bugs (stream-slot leak on abort, cumulative/delta rewind, ceil-division length bug, legacy-checkpoint v2-tokenizer mismatch), so recall is  |
| pr4810.r1 | opus_baseline | slight | Both candidates independently rediscover the exact latent gap (hunyuan_image3_transformer.py:2238 still calling the removed get_cache_scale API, excluded from _STALE_API_FILES) with solid, grounded ev |
| pr4810.r2 | opus_baseline | clear | Both candidates independently discover the same latent gap (the diffusion-stage HunyuanImage3 loader still calling the removed get_cache_scale API) via repo-wide grep, and both raise a legitimate test |
| pr4810.r3 | opus_baseline | clear | Both catch the real latent gap (hunyuan_image3_transformer.py still calling the removed API), but X repeats the identical finding five times near-verbatim as separate 'comments', which reads as a malf |
| pr4816.r1 | opus_baseline | slight | Ground truth shows this PR had no real concerns (human reviewer just said 'lgtm'), so a clean, verified approve like X's is the accurate call — X grounds every claim in actual greps and an upstream ch |
| pr4816.r2 | copilot_v2 | slight | Ground truth carries no substantive concerns (plain LGTM approve), so recall is trivially satisfied by both. X delivers a clean, well-grounded verification (grep for stale names, consistency check) bu |
| pr4816.r3 | opus_baseline | slight | Ground truth shows this PR was a trivial, uncontroversial rename with an outright 'lgtm' approval — nothing substantive to recall, so both score full recall. X's approval is tightly grounded (grep ver |
| pr4817.r1 | copilot_v2 | clear | Ground truth has no substantive reviewer concerns, so recall is trivially satisfied by both. X delivers a clean, accurate review with one valid but softly-stated nit (sm_110a exclusion), verified via  |
| pr4817.r2 | copilot_v2 | slight | Ground truth has no substantive reviewer concerns, so recall is trivially satisfied by both. Both candidates independently surface the same real latent gap (cc 11.x/sm_110a excluded by the `==10` gate |
| pr4817.r3 | copilot_v2 | clear | Ground truth has no substantive concerns to recall, so both score full recall trivially. X's findings are more thorough and grounded in specific file:line evidence (docstring/heading/test overclaims,  |
| pr4825.r1 | opus_baseline | clear | Ground truth's only substantive technical concern is dsocek's point that the hardcoded component list should instead be driven from the model's existing packed/stacked-params mapping so fused-projecti |
| pr4825.r2 | opus_baseline | slight | The only substantive ground-truth concern (dsocek's suggestion to stop hardcoding the component list and instead derive it from an existing structured source like stacked_params_mapping/_packed_module |
| pr4825.r3 | opus_baseline | clear | X's top finding (hardcoded default_components list drifts from per-pipeline _dit_modules/registry declarations, so other denoisers like soulx still won't be covered) closely mirrors the actual human c |
| pr4834.r1 | copilot_v2 | clear | Both reviews are grounded and actionable, covering the enum/test-coverage themes from the human thread and adding solid original findings (X's default-level footgun, Y's concurrency race and tag-valid |
| pr4834.r2 | copilot_v2 | clear | Both candidates cover the two substantive ground-truth points (regression tests added, CuMemTag enum added per Gaohan123's request) with grounded, actionable findings. Y is the only one to hit the lat |
| pr4834.r3 | copilot_v2 | clear | Both reviews are grounded and well-evidenced, cover the enum/test-coverage points implicit in the ground truth, and add plausible unique findings (concurrency race in X, default-level footgun in Y). X |
| pr4837.r1 | opus_baseline | clear | Both candidates correctly explain the core fix (already_submitted gate removal now unwraps singleton lists on both submit paths, matching the ground-truth inline comment's reasoning) and both verify t |
| pr4837.r2 | opus_baseline | clear | The one substantive ground-truth concern (yJader's inline comment) is that removing `already_submitted` is correct because both `submit_initial` and `submit_update` already reject list prompts in Stag |
| pr4837.r3 | opus_baseline | slight | Both candidates independently verify the same core ground-truth point (that both submit_initial and submit_update reject list prompts, justifying removal of the already_submitted gate), so recall is c |
| pr4849.r1 | copilot_v2 | slight | Both candidates independently verify the parent-first ordering contract (matching the Gaohan123/Celeste-jq exchange) and both surface the amd-ci/npu-ci CI failures, but neither flags the 'please fix p |
| pr4849.r2 | opus_baseline | clear | Both miss the ground-truth reviewer's actual asks (explicit comment/check on parent-first ordering, running the specific benchmark test, fixing precommit), so recall is low and roughly tied. X piles o |
| pr4849.r3 | copilot_v2 | slight | X's finding at hunyuan_image3.py:125 (recommend a comment/assert about extras being intentionally ignored near the parent-index access) partially overlaps the ground-truth reviewer's core concern abou |
| pr4859.r1 | opus_baseline | clear | Both candidates independently converge on the two real discussion points from the PR (audio_vae.py config mutation and the dialect/language drop in serving_speech.py), but X frames them as calibrated  |
| pr4859.r2 | opus_baseline | slight | X correctly frames the config-mutation and stop-step changes as intentional/benign (matching the actual PR resolution where LHXuuu confirms both align with vendor code), staying well-calibrated even t |
| pr4859.r3 | opus_baseline | slight | Both catch roughly half of the real reviewer threads (X gets the language/dialect drop and the config-mutation question; Y gets the config-mutation question and the min_stop_step+2 tightening), but X  |
| pr4870.r1 | opus_baseline | clear | Most ground-truth concerns (scoping, dead seq_len param) are already resolved in the diff shown, so recall is inherently low for both; X's note that the split now keys solely on total_num_scheduled_to |
| pr4870.r2 | opus_baseline | clear | Both catch the async_chunk default-value inconsistency (matching the ground-truth Low note), but X's verdict (FOLLOW-UP REQUIRED, multiple 'major' tags) is poorly calibrated: it raises a 'major' test- |
| pr4870.r3 | opus_baseline | clear | Both candidates independently rediscover the ground-truth [Low] async_chunk default inconsistency (True vs False) with correct file/line grounding. X piles on extra 'major' findings — a claimed test/p |
| pr4893.r1 | copilot_v2 | slight | X is the only candidate that touches the sole substantive human concern (verifying the reduce_scatter test parameter), flagging the dead conditional in the fake-group constructor, and it surfaces a pl |
| pr4893.r2 | copilot_v2 | clear | Ground truth is sparse (mostly procedural comments plus one inline nit questioning whether the test's reduce_scatter kwarg needs explicit verification); X's dead-code finding on the same test fake's ` |
| pr4893.r3 | copilot_v2 | clear | The one substantive ground-truth concern (yenuo26's question about verifying the reduce_scatter kwarg in the fake-group test) is caught precisely by Y, which flags the exact dead-code conditional at t |
| pr4923.r1 | opus_baseline | clear | Y directly hits several ground-truth threads: the exact NPU PIECEWISE fix Wallbreazzz requested, the seed-reproducibility caveat gcanlin flagged, and the benchmark/accuracy evidence gap Sy0307 pushed  |
| pr4923.r2 | opus_baseline | clear | X's findings (stale yaml header comments, redundant field assignment, missing accuracy/benchmark evidence, seeding-reproducibility gap) are grounded in the actual diff and echo real ground-truth threa |
| pr4923.r3 | opus_baseline | clear | Y catches two genuinely valid, verifiable doc-staleness issues (stale max_num_batched_tokens/prefix-caching comments), the duplicate omni_pooler_payload_include_hidden assignment, and explicitly surfa |
| pr4926.r1 | copilot_v2 | clear | Both miss most GT concerns since the shown diff already incorporates the reviewers' fixes (shared _run_varlen_dense helper, FA3 major>=9 gate), so neither can 'recall' issues that no longer exist; bot |
| pr4926.r2 | opus_baseline | slight | X correctly reproduces the RuixiangMa-confirmed varlen_func-None crash and hedges its riskiest claim (the get_kernel version=int semantics), which ground truth reveals is actually intentional (git-bra |
| pr4926.r3 | opus_baseline | clear | Y independently surfaces the varlen/flash_attn_func None-crash bug that RuixiangMa flagged and SamitHuang confirmed fixing ('added a shared _run_varlen_dense() helper'), while X's sweep explicitly inv |
| pr4950.r1 | copilot_v2 | slight | Ground truth shows no substantive reviewer concerns (just LGTM/approve), so both candidates correctly find no blockers and both verify the PR's technical claims against source with plausible, specific |
| pr4950.r2 | copilot_v2 | clear | Both correctly verify the diff's core technical claims (root-level chat_template_kwargs, SDK flattening, two-choices response, silent-vs-text-only) with plausible code citations, and ground truth offe |
| pr4950.r3 | copilot_v2 | slight | Both candidates verify the PR's technical claims against the code with specific file:line citations and reach consistent, plausible conclusions; since the ground-truth review contains no substantive c |
| pr4954.r1 | copilot_v2 | slight | Both candidates touch the ground-truth's core doc/behavior-contract concern (containment fallback silently loosening the 'strict unless opt-in' promise). X goes further, independently investigating th |
| pr4954.r2 | copilot_v2 | clear | Both correctly validate the core codes.audio fix and both flag the containment-fallback interacting with the opt-in escalation contract, mirroring GT's approval-with-caveats stance. Y goes further and |
| pr4954.r3 | copilot_v2 | clear | Both correctly validate the core codes.audio fix and add valid, grounded non-blocking findings (X: unconditional containment fallback loosening, misleading min() short_text guard). Y goes further: it  |
| pr4970.r1 | opus_baseline | slight | Ground truth is essentially an LGTM approval with no substantive inline concerns (plus an unrelated ask to split out a VoxCPM2 fix, which neither candidate addresses). Both candidates did solid, well- |
| pr4970.r2 | opus_baseline | slight | Neither candidate surfaces the one real reviewer concern (the VoxCPM2 regression follow-up ask), so recall is ~0 for both; both did solid, well-grounded tracing of the seed→tts_local_seed→per-row-gene |
| pr4970.r3 | copilot_v2 | slight | Ground truth has essentially no substantive findings (LGTM plus an unrelated request to split out a VoxCPM2 fix into a separate PR); neither candidate explicitly addresses that scope request, so recal |
| pr4977.r1 | copilot_v2 | slight | Both candidates independently flag the trust_remote_code/description mismatch, which is the closest overlap with the ground-truth Codex comment (though neither reproduces its actual technical concern  |
| pr4977.r2 | copilot_v2 | slight | Neither candidate surfaces the ground truth's actual concern (trust_remote_code causing a regression on kernels<0.15.0 installs) — both instead note trust_remote_code is absent from the diff/descripti |
| pr4977.r3 | copilot_v2 | slight | Neither candidate surfaces the ground-truth concern (trust_remote_code kwarg incompatible with locked kernels<0.15.0 installs) since the visible diff doesn't contain that kwarg, so recall is low and r |
| pr5009.r1 | copilot_v2 | slight | Both correctly recognize that the PR's stated concerns (UT coverage, perf/accuracy comparison, non-Qwen scope justification) were already resolved via FLUX.1-dev A/B and the new test file. X is cleane |
| pr5009.r2 | copilot_v2 | clear | X's major finding (global CUDA default now unconditionally vllm_c-preferring, validated only on Qwen-Image/FLUX diffusion, with a concrete fix suggestion to scope via the per-pipeline ir_op_priority_f |
| pr5009.r3 | copilot_v2 | clear | X's major finding (platform-wide default extrapolated from single-model evidence) closely mirrors hsliuustc0106's core scoping concern and gives concrete actionable remediation (scope via ir_op_priori |
