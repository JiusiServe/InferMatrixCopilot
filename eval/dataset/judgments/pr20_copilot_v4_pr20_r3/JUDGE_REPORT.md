# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)

Judge: claude-sonnet-5 (blind, randomized order, 3 replicates x 10 items = 60 verdicts)

## Wins
- copilot_v2: 26
- opus_baseline: 34
- tie: 0

## Mean rubric scores

| arm | actionability | gap_hit | precision | recall |
|---|---|---|---|---|
| copilot_v2 | 0.76 | 0.12 | 0.80 | 0.45 |
| opus_baseline | 0.74 | 0.17 | 0.81 | 0.52 |

## Per-verdict detail

| item.rep | winner | margin | rationale (head) |
|---|---|---|---|
| pr4762.r1 | copilot_v2 | slight | Both independently caught the single most important ground-truth issue (trust_remote_code default silently flipped True→False) and the same latent bug (api_server.py else-branch skipping the global UN |
| pr4762.r2 | opus_baseline | slight | Both candidates independently rediscovered the api_server.py hasattr-guard bug that silently skips the global UNSUPPORTED_ROUTES restriction, and both flagged the trust_remote_code default flip (True→ |
| pr4762.r3 | opus_baseline | clear | Y correctly identifies and credits the PR's central, most-discussed thread (endpoint restrictions must follow the final/deploy-overridden pipeline, not the auto-detected one), recognizing the regressi |
| pr4777.r1 | opus_baseline | clear | Ground truth has no substantive concerns (two LGTM approvals plus a manual verification comment confirming the fix works), so both candidates trivially satisfy recall and neither can score a gap_hit.  |
| pr4777.r2 | opus_baseline | clear | Ground truth here is essentially empty (two LGTMs and a manual verification comment, no inline concerns), so recall is trivially satisfied by both. X's single finding (missing positive unit test for l |
| pr4777.r3 | opus_baseline | slight | Ground truth here is thin (two LGTMs plus a QA walkthrough confirming boundary/unit-test/e2e behavior), so recall is mostly about matching that QA checklist — Y covers it more fully by also validating |
| pr4804.r1 | copilot_v2 | slight | Both candidates miss nearly all the ground-truth reviewers' core findings (the High-severity stream-slot-leak, the cumulative/delta rewind silent bug, the ceil-division latent bug, and most of the non |
| pr4804.r2 | opus_baseline | slight | Both candidates miss nearly all the confirmed ground-truth bugs (chunk re-slice rewind bug, ceil/floor length bug, legacy-checkpoint-routes-to-v2-tokenizer bug, WER raw-bytes fallback), so recall is l |
| pr4804.r3 | opus_baseline | slight | Both candidates miss the highest-value confirmed GT bugs (stream-slot leak on abort, cumulative/delta chunk_np resplice, ceil-division/input_lengths mismatch, v2-tokenizer-swallows-legacy-checkpoint)  |
| pr4810.r1 | copilot_v2 | slight | Both candidates independently verified the AutoWeightsLoader delegation logic and both caught the exact latent gap (the still-unmigrated hunyuan_image3_transformer.py diffusion loader, later #4891), c |
| pr4810.r2 | opus_baseline | slight | Both candidates correctly validate the core migration logic and both independently surface the exact latent gap (the unmigrated hunyuan_image3_transformer.py:2238 diffusion caller of get_cache_scale), |
| pr4810.r3 | opus_baseline | slight | Both candidates independently grep-discovered the exact latent gap (hunyuan_image3_transformer.py:2238 still calling the removed get_cache_scale), so gap_hit is true for both. Y goes further: it verif |
| pr4816.r1 | copilot_v2 | slight | Both correctly identify this as a clean, complete mechanical rename and approve, matching the ground truth's trivial 'lgtm.' However, X's specific verification claims are undermined by fabricated line |
| pr4816.r2 | copilot_v2 | slight | Ground truth has no substantive concerns (just an 'lgtm' approval), so both candidates correctly land on APPROVE with no fabricated blockers — recall/precision are both strong and roughly tied. Y is s |
| pr4816.r3 | copilot_v2 | slight | Ground truth has no substantive concerns (just a bot notice and an 'lgtm' approval), so both candidates correctly approve this trivial mechanical rename with full recall. Precision favors Y: its cited |
| pr4817.r1 | copilot_v2 | clear | Ground truth has no substantive concerns, so recall is trivial for both. Both correctly validate the core fix (== 10 gate, rename, env override, docs) and both raise the same speculative sm_110a point |
| pr4817.r2 | copilot_v2 | slight | Ground truth has no substantive reviewer concerns to recall, so both are roughly equal there. Both correctly validate the core `==10` fix and independently raise the same sm_110a edge-case concern (pl |
| pr4817.r3 | copilot_v2 | slight | Ground truth has no substantive concerns, so recall is vacuously satisfied by both. Both candidates correctly validate the core gate-logic fix and identify the same latent sm_110 ambiguity, with no fa |
| pr4825.r1 | opus_baseline | clear | The ground truth's substantive concern (dsocek questioning whether the hardcoded component list generalizes across PEFT naming conflicts, suggesting deriving from _packed_modules_mapping instead) is c |
| pr4825.r2 | opus_baseline | decisive | The one substantive ground-truth concern (dsocek's suggestion to derive component/naming discovery from existing mapping data like _packed_modules_mapping rather than hardcoded lists) is echoed in spi |
| pr4825.r3 | opus_baseline | clear | Ground truth's substantive concern (dsocek's suggestion to derive component/name mapping from `_packed_modules_mapping`/`stacked_params_mapping` rather than hardcoded lists) isn't hit precisely by eit |
| pr4834.r1 | copilot_v2 | slight | X better covers both ground-truth threads (test-coverage adequacy and the CuMemTag enum design), giving it stronger recall, and its default-level=2 finding gestures at the same over-strictness the LAT |
| pr4834.r2 | copilot_v2 | clear | Both cover the enum request; X also explicitly credits the added regression tests (SamitHuang's ask), giving it higher recall. But X's headline blocker rests on an apparently fabricated fact (claiming |
| pr4834.r3 | opus_baseline | slight | Both hit the latent gap (X very concretely, by naming five existing tests that call sleep(level=2)+wake_up() and would now break — closely mirroring the real #4905 CI break; Y frames it as the default |
| pr4837.r1 | opus_baseline | clear | The sole substantive ground-truth concern (yJader's comment) is that already_submitted shouldn't gate the unwrap because both submit_initial and submit_update reject list prompts identically. X explic |
| pr4837.r2 | opus_baseline | clear | Y independently verifies both submit_initial/submit_update reject list prompts (stage_pool.py:951-955, 1022-1026), reproducing almost exactly the reasoning in the ground-truth inline comment about why |
| pr4837.r3 | opus_baseline | clear | Both candidates correctly explain the core orchestrator.py:1290 fix, matching the substance of the single GT inline comment; X's framing (verifying that both submit_initial and submit_update reject li |
| pr4849.r1 | copilot_v2 | clear | Both candidates independently validate the parent-first ordering assumption that Gaohan123 questioned (already resolved by the docstring in this diff), but neither catches the ground-truth 'please fix |
| pr4849.r2 | copilot_v2 | clear | Both candidates independently confirm the parent-first ordering assumption that Gaohan123 flagged inline, but neither explicitly echoes the 'add a check or comment' ask verbatim (the diff already carr |
| pr4849.r3 | copilot_v2 | clear | X's minor findings substantively engage the same fragile-assumption territory the human reviewer flagged (indexing source_outputs[0]/outputs[0] without guards) and independently proposes concrete veri |
| pr4859.r1 | copilot_v2 | clear | Y independently surfaces nearly the same concerns the human reviewers actually raised — the audio_vae.py:141 config-mutation risk (near-verbatim match to amy-why-3459's inline comment) and the serving |
| pr4859.r2 | copilot_v2 | clear | Both correctly flag the audio_vae.py config-mutation issue and the patch_emission.py +2 window change, matching real GT threads. But X completely misses the serving_speech.py language/dialect-dropping |
| pr4859.r3 | copilot_v2 | decisive | X independently surfaces all three substantive concerns real reviewers raised (audio_vae.py config mutation, patch_emission.py +1→+2 window change, and the dropped include_language/方言 handling), each  |
| pr4870.r1 | opus_baseline | clear | Both candidates correctly validate the core runner fix and the qwen3_tts gating, and both raise a similar 'async_chunk default True vs False inconsistency' point that echoes the ground-truth Low conce |
| pr4870.r2 | opus_baseline | clear | Both candidates verify the already-resolved Med (qwen3_tts gating) and Nit (seq_len removal) concerns and both surface the live Low concern (async_chunk default fallback), but Y's version is more prec |
| pr4870.r3 | opus_baseline | clear | Y independently surfaces the async_chunk default-asymmetry (matching the GT Low finding almost exactly, with a concrete fix recommendation) and separately flags that the split now keys solely on total |
| pr4893.r1 | copilot_v2 | clear | The sole substantive ground-truth concern (yenuo26's inline comment) questions whether test verification is complete for the two simultaneous fixes (device_communicator + reduce_scatter). X's findings |
| pr4893.r2 | copilot_v2 | slight | Ground truth is thin (mostly social comments plus one inline nitpick about reduce_scatter test coverage, which the diff already addresses). X engages more with test-coverage completeness for the new v |
| pr4893.r3 | copilot_v2 | slight | The sole substantive ground-truth concern (whether the test should verify reduce_scatter behavior, not just device_communicator presence) is missed by both candidates, so recall is low for both. X mos |
| pr4923.r1 | opus_baseline | clear | Ground truth centers on two threads: (1) the seed-reproducibility regression for talker_mtp under full cudagraphs (gcanlin's 'mtp seed failed when decode batch > 1'), and (2) the NPU deploy config nee |
| pr4923.r2 | opus_baseline | clear | Both candidates independently catch the two stale YAML doc comments (prefix-caching rationale, max_num_batched_tokens header), but X also surfaces the seed-reproducibility tradeoff under full cudagrap |
| pr4923.r3 | opus_baseline | clear | Y engages the two threads that actually mattered post-hoc — it explicitly questions the NPU stage-1 PIECEWISE addition (the exact fix Wallbreazzz's crash report produced) and demands accuracy/perf evi |
| pr4926.r1 | opus_baseline | slight | X surfaces a genuine, actionable defect (masked/varlen path calling flash_attn_varlen_func when only flash_attn_func may be present, causing a TypeError) that Y actually reviewed and incorrectly clear |
| pr4926.r2 | opus_baseline | clear | Both reviews are well-grounded and cite concrete file/line evidence, but X's #1 finding (the version=1/2/default cascade silently swallowing failures and falling through to an unpinned kernel) closely |
| pr4926.r3 | opus_baseline | clear | Y independently surfaces the same class of bug RuixiangMa flagged and the author fixed: _forward_varlen_masked/_forward_varlen_dense call self.flash_attn_varlen_func unconditionally even though __init |
| pr4950.r1 | copilot_v2 | slight | Ground truth has zero substantive concerns (just LGTM/approve), so recall is trivially satisfied by both. Both candidates do solid diff-grounded verification of the PR's technical claims with specific |
| pr4950.r2 | copilot_v2 | slight | Ground truth has no substantive technical concerns (just LGTM approvals), so both candidates trivially satisfy recall by validating the PR's claims thoroughly with grounded code citations. Both are we |
| pr4950.r3 | copilot_v2 | slight | Ground truth is just LGTM approvals with zero substantive concerns, so recall is trivially satisfied by both. Both candidates build solid, well-cited verification tables confirming the PR's claims aga |
| pr4954.r1 | opus_baseline | clear | GT's one substantive non-blocking comment is that the docstring/module comment claiming 'original strict behaviour is preserved... other tests unaffected' is now false because the containment fallback |
| pr4954.r2 | copilot_v2 | slight | Neither candidate hits the two actual GT concerns precisely (docstring staleness and legacy-path ordering appear already resolved in the final diff, making them hard to rediscover); X's 'unconditional |
| pr4954.r3 | opus_baseline | slight | GT's two nits are (1) docs/module-comment don't clarify the containment fallback applies to ALL callers, not just opt-in escalation ones, and (2) a minor note about legacy-vs-nested check order and wh |
| pr4970.r1 | opus_baseline | clear | Both candidates independently verified the same mechanism (seed removal restores the batched-multinomial fast path) with grounded references to serving_speech.py and gpu_model_runner.py, and neither s |
| pr4970.r2 | opus_baseline | slight | Ground truth is nearly empty (LGTM + an unrelated request to spin off a VoxCPM2 fix into a separate PR, not inferable from this diff), so both candidates converge on the same correct outcome (APPROVE) |
| pr4970.r3 | opus_baseline | slight | Ground truth is essentially just an APPROVE/LGTM with an unrelated aside about splitting out a VoxCPM2 fix, which neither candidate's diff-scoped analysis touches, so recall is capped and equal for bo |
| pr4977.r1 | opus_baseline | slight | Neither candidate surfaces the actual ground-truth concern (trust_remote_code kwarg breaking on locked kernels<0.15.0 installs) — both instead flag that the PR description's trust_remote_code claim do |
| pr4977.r2 | copilot_v2 | slight | The one substantive ground-truth concern (trust_remote_code causing a regression on locked kernels<0.15.0 installs) was missed by both candidates, who instead flagged the inverse claim that trust_remo |
| pr4977.r3 | opus_baseline | slight | Both candidates independently surface the same tangential match to the ground-truth concern (PR description claims trust_remote_code=True was added but it's absent from the diff/file), so recall is eq |
| pr5009.r1 | opus_baseline | clear | Ground truth is dominated by reviewer asks for evidence (perf comparison, accuracy comparison, non-Qwen scope justification) and test coverage, most of which the author addressed via PR description da |
| pr5009.r2 | copilot_v2 | slight | Y engages more directly with the ground truth's two most-repeated concerns (the platform-wide scope of the default-priority change, and the requested P1+P2-vs-main perf comparison), even citing perf n |
| pr5009.r3 | opus_baseline | clear | Both largely miss the reviewers' central unresolved worry (only Qwen-Image/H200, and later FLUX, were validated among ~10 listed affected model families) and neither catches the pytest-mark completene |
