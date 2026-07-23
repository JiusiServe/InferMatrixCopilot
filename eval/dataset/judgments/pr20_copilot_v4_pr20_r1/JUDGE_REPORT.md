# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)

Judge: claude-sonnet-5 (blind, randomized order, 3 replicates x 10 items = 60 verdicts)

## Wins
- copilot_v2: 26
- opus_baseline: 33
- tie: 1

## Mean rubric scores

| arm | actionability | gap_hit | precision | recall |
|---|---|---|---|---|
| copilot_v2 | 0.79 | 0.12 | 0.75 | 0.42 |
| opus_baseline | 0.73 | 0.14 | 0.81 | 0.52 |

## Per-verdict detail

| item.rep | winner | margin | rationale (head) |
|---|---|---|---|
| pr4762.r1 | opus_baseline | slight | X engages more directly with the ground-truth threads: it explicitly discusses the trust_remote_code default flip (matches alex-jw-brooks's own bug note), confirms the deploy-override endpoint-restric |
| pr4762.r2 | opus_baseline | clear | Y catches the two concerns human reviewers emphasized most — the trust_remote_code default flip (near-verbatim match to alex-jw-brooks's inline comment) and the endpoint-restriction/deploy-override re |
| pr4762.r3 | opus_baseline | clear | Y correctly recognizes that the major reviewer concern (endpoint restrictions resolved from the wrong/auto-detected pipeline) was already fixed via get_pipeline_config's deploy-override-first ordering |
| pr4777.r1 | opus_baseline | slight | Ground truth found zero issues (two LGTMs plus a manual verification that everything, including the L2 e2e test, passed), so recall is vacuously full for both. X's four touched files analysis is accur |
| pr4777.r2 | opus_baseline | clear | Ground truth is essentially empty (approvals plus an informal manual-QA comment, no inline concerns), so recall is low-value for both. X is careful and diff-grounded (verified via grep that the range  |
| pr4777.r3 | opus_baseline | clear | Ground truth is thin (LGTM approvals plus an informal QA comment confirming boundary/unit/e2e checks), so neither candidate has much substantive human feedback to recall against. X correctly validates |
| pr4804.r1 | opus_baseline | slight | Both candidates miss the two sharpest GT bugs (the abort slot-leak and the cumulative/delta chunk_np re-slice bug) and the latent ceil-division bug; neither is a strong recall performer. Y independent |
| pr4804.r2 | copilot_v2 | clear | Both candidates miss the four substantive bugs the human reviewers actually flagged (slot leak on abort, cumulative/delta re-slice bug, ceil-division length bug, legacy-tokenizer/v2 config collision), |
| pr4804.r3 | copilot_v2 | slight | Both candidates miss all four core confirmed bugs (slot leak on abort, cumulative/delta re-slice, ceil-division length bug, legacy-checkpoint v2 dispatch), so recall is near-zero for both, with X gett |
| pr4810.r1 | copilot_v2 | slight | Both independently rediscover the exact latent gap (the unswept hunyuan_image3_transformer.py diffusion caller of get_cache_scale), which the human reviewers never mentioned. Y additionally reproduces |
| pr4810.r2 | opus_baseline | clear | Both candidates correctly validate the core migration logic and both independently surface the latent gap (the unswept diffusion-transformer caller of get_cache_scale), satisfying gap_hit. Y is more r |
| pr4810.r3 | opus_baseline | clear | Both candidates independently find the exact latent gap (the unswept get_cache_scale call in hunyuan_image3_transformer.py), but Y verifies it more rigorously by checking the actual upstream vLLM sour |
| pr4816.r1 | copilot_v2 | slight | Ground truth is essentially empty (just an 'lgtm' approval), so both candidates trivially achieve full recall. Both correctly approve and verify the rename is complete and consistent, but Y's cited fi |
| pr4816.r2 | copilot_v2 | clear | Ground truth contains no substantive concerns (just an 'lgtm' approval), so both candidates correctly reach APPROVE and recall is moot for both. X reads well but its specific citations don't hold up:  |
| pr4816.r3 | copilot_v2 | clear | Ground truth has no substantive concerns (just an 'lgtm' approval), so both candidates correctly reach APPROVE and recall is trivially satisfied. Y's cited line numbers (754, 1017, 1157, 1248, 1286, 1 |
| pr4817.r1 | copilot_v2 | slight | Ground truth has no substantive reviewer concerns (bot credit-limit messages and a 'thanks' comment), so both candidates trivially achieve full recall. Both reviews are well-grounded in the diff, corr |
| pr4817.r2 | copilot_v2 | slight | Ground truth has no substantive reviewer concerns, so both trivially satisfy recall. Both candidates independently raise the same grounded, low-severity nit about sm_110a/cc 11.x being excluded by the |
| pr4817.r3 | copilot_v2 | slight | Ground truth has no substantive reviewer concerns (just thanks/codex-limit noise), so recall is trivially satisfied by both. Both candidates independently surface the same legitimate edge case (sm_110 |
| pr4825.r1 | opus_baseline | clear | Both miss dsocek's specific packed_modules_mapping/naming-conflict point (likely tied to a since-removed part of the PR not visible in the truncated diff), but X's suggestion to derive default_compone |
| pr4825.r2 | opus_baseline | clear | The one substantive ground-truth concern (dsocek's point that the hardcoded component list is fragile and should instead be derived from an existing declarative source like the packed-modules mapping) |
| pr4825.r3 | opus_baseline | clear | X's suggestion to derive the component list from the pipeline's declarative _dit_modules instead of hardcoding echoes the actual reviewer concern (dsocek's comment about generalizing PEFT-naming fixes |
| pr4834.r1 | copilot_v2 | clear | Both candidates engage with the two ground-truth concerns (regression tests added, CuMemTag enum introduced) to similar depth. The decisive difference is the latent gap: Y pinpoints five pre-existing  |
| pr4834.r2 | copilot_v2 | clear | Y directly hits the latent gap: it greps the full PR-time tree and names five pre-existing tests (test_diffusion_sleep_handshake, test_diffusion_integrity_bit_level, test_diffusion_vram_lifecycle_audi |
| pr4834.r3 | opus_baseline | slight | Both candidates surface real, diff-grounded issues and both effectively hit the latent gap: X pinpoints five concrete pre-existing tests that will now break under the new level=2 wake guard (precisely |
| pr4837.r1 | opus_baseline | clear | GT's sole substantive point (yJader's inline comment) explains that removing `already_submitted` is safe because both submit_initial and submit_update reject list prompts identically for diffusion — X |
| pr4837.r2 | opus_baseline | decisive | The one substantive GT insight (yJader's inline comment) is that removing `already_submitted` is correct because StagePool rejects list prompts in both submit_initial and submit_update, so unwrapping  |
| pr4837.r3 | opus_baseline | clear | The one substantive ground-truth point is yJader's inline comment explaining that dropping the `already_submitted` gate is safe because both submit_initial and submit_update reject list prompts identi |
| pr4849.r1 | copilot_v2 | clear | The GT's headline concern (Gaohan123: is source_outputs[0] really the parent? add a check/comment) is exactly what Y flags at hunyuan_image3.py:118 with a concrete fix suggestion (add an assertion/gua |
| pr4849.r2 | copilot_v2 | slight | X directly surfaces the reviewers' central concern (source_outputs[0] as parent is an unenforced assumption) and, matching Gaohan123's actual ask, recommends adding an assertion/guard — the single mos |
| pr4849.r3 | copilot_v2 | clear | The GT's central concern (Gaohan123's line-118 comment questioning whether source_outputs[0] is reliably the parent) is directly hit by X, which flags the same unenforced assumption with a concrete fi |
| pr4859.r1 | copilot_v2 | slight | Both correctly flag the audio_vae.py:141 config-mutation issue that matches the GT thread, but X's phrasing is more precise (it notes the encoder's actual layer count is unaffected since it's built be |
| pr4859.r2 | opus_baseline | slight | Both catch the key GT-aligned issue (shared-config mutation in audio_vae.py:141) with grounded, actionable fixes, and neither surfaces the dialect-removal question that GT reviewers actually debated.  |
| pr4859.r3 | copilot_v2 | clear | Both candidates independently converge on the two real hotspots human reviewers debated (audio_vae.py config mutation, patch_emission.py +1→+2 gating), but X also raises the stale README documentation |
| pr4870.r1 | opus_baseline | clear | Both candidates independently catch the one still-live GT concern (the async_chunk getattr default inconsistency, True vs False) and correctly confirm the qwen3_tts scoping and seq_len cleanup already |
| pr4870.r2 | opus_baseline | clear | Both candidates independently surface a real async_chunk getattr default-inconsistency (True vs False) that echoes the ground-truth 'Low' robustness concern, and both validate the qwen3_tts scoping fi |
| pr4870.r3 | opus_baseline | clear | Both candidates independently rediscover the async_chunk default-inconsistency issue (echoing the GT Low comment), but Y's version is sharper — it cites the exact sibling default (line 3823) and the r |
| pr4893.r1 | copilot_v2 | clear | Neither candidate surfaces the one substantive ground-truth concern (whether the test should more deeply verify the reduce_scatter wiring beyond hasattr), so recall is near-zero for both. X delivers t |
| pr4893.r2 | copilot_v2 | slight | Ground truth is thin (mostly approval/off-topic comments) with one substantive inline ask about deepening reduce_scatter test verification; neither candidate directly surfaces that gap, though X's swe |
| pr4893.r3 | copilot_v2 | clear | Neither candidate captures the sole substantive ground-truth concern (test coverage for reduce_scatter, already resolved in the shown diff), so recall is near-zero for both. X's review is largely a co |
| pr4923.r1 | opus_baseline | clear | Y directly engages the three real GT threads: it validates/explains the exact cudagraph_mode-in-modeling question gcanlin raised and the TODO resolving it, explains the seed-reproducibility tradeoff g |
| pr4923.r2 | copilot_v2 | slight | Both catch the mtp-seed reproducibility loss under full cudagraphs and the redundant omni_pooler_payload_include_hidden assignment, and both flag the stale prefix-caching comment vs. new false value — |
| pr4923.r3 | opus_baseline | clear | Y's review converges with the actual reviewer thread: it flags the same seed-reproducibility/full-cudagraph consequence the inline comments dwell on, explicitly questions the NPU stage-1 PIECEWISE add |
| pr4926.r1 | copilot_v2 | slight | Both candidates independently found the strongest real bug in the diff — the varlen_func-may-be-None crash in the masked/piecewise path — matching RuixiangMa's GT comment almost exactly, and both flag |
| pr4926.r2 | copilot_v2 | slight | Both candidates miss most of the actual ground-truth concerns (doc clarification on kernels versions, test-mark/skipif process nits, and the confirmed FA3 SM90+ gating bug), and both independently cat |
| pr4926.r3 | opus_baseline | slight | Y independently surfaces the version=1/2 integer-vs-string kernel loading defect, which closely tracks (and actually resolves) wtomin's exact ground-truth question that even the PR author had to clari |
| pr4950.r1 | copilot_v2 | slight | Ground truth has no substantive concerns (just LGTM/approval), so both candidates trivially satisfy recall. X delivers three concrete, grounded findings with exact file/line and suggested rewrites, in |
| pr4950.r2 | copilot_v2 | slight | Ground truth is essentially empty (just LGTM/approvals), so both candidates trivially satisfy recall; the real differentiator is depth and usefulness of extra findings. X's source-code verification is |
| pr4950.r3 | copilot_v2 | slight | Ground truth contains no substantive concerns (only LGTM/approval), so recall is trivially maxed for both. X performs deeper source-level verification (tracing actual code paths in serving_chat.py and |
| pr4954.r1 | opus_baseline | clear | GT's substance is: (1) approve, core fix correctly restores codes.audio feedback matching #4527; (2) the new containment fallback silently drops the 'strict behavior preserved' guarantee for all calle |
| pr4954.r2 | opus_baseline | slight | Both candidates correctly validate the core codes.audio fix but miss GT's two specific non-blocking asks (update the stale docstring/module comment, and question whether the legacy top-level-audio pro |
| pr4954.r3 | opus_baseline | clear | Both candidates correctly confirm the core fix (codes.audio vs legacy audio) matching the GT's main point. X also independently surfaces the GT's key non-blocking concern — that the new containment fa |
| pr4970.r1 | opus_baseline | slight | Ground truth offers almost no substantive concerns (just an LGTM/approve and an unrelated ask to file a separate VoxCPM2 PR), which neither candidate addresses, so recall is low and tied. Both candida |
| pr4970.r2 | opus_baseline | slight | Both candidates independently traced the same seed→tts_local_seed→sampling-path mechanism correctly and landed on the same non-blocking nit (add a comment explaining the intentional omission), which i |
| pr4970.r3 | tie | slight | Ground truth offers almost nothing to recall against (just an unrelated 'split out VoxCPM2 regression' ask and an LGTM), which neither candidate addresses, so recall is low and equal for both. Both ca |
| pr4977.r1 | opus_baseline | slight | Both candidates independently surfaced the same PR-description/code mismatch around trust_remote_code that underlies the ground-truth codex comment, giving them roughly equal partial recall of the sol |
| pr4977.r2 | copilot_v2 | slight | Neither candidate catches the ground truth's actual concern (trust_remote_code kwarg breaking compatibility with locked kernels<0.15.0 installs) — both only note that the PR description mentions trust |
| pr4977.r3 | opus_baseline | slight | Both candidates converge on the same discrepancy the ground-truth comment orbits (the description's trust_remote_code claim vs. the visible code), but neither reproduces the ground truth's precise con |
| pr5009.r1 | opus_baseline | clear | The ground truth's most substantive concern (hsliuustc0106's line-252 comment: the platform default now applies to ALL CUDA diffusion models but was only validated on Qwen-Image, requiring non-Qwen A/ |
| pr5009.r2 | opus_baseline | clear | Both are grounded and free of fabrication, but Y engages the actual review threads: it explicitly discusses the performance/accuracy A/B evidence (matching Gaohan123's perf-comparison ask) and cites t |
| pr5009.r3 | opus_baseline | clear | The GT's dominant concern (hsliuustc0106 + NumberWan thread) is that the platform default was globalized to all CUDA diffusion models but validated only on Qwen-Image, later justified with FLUX.1-dev  |
