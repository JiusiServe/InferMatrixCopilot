# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)

Judge: claude-sonnet-5 (blind, randomized order, 3 replicates x 10 items = 60 verdicts)

## Wins
- copilot_v2: 28
- opus_baseline: 32
- tie: 0

## Mean rubric scores

| arm | actionability | gap_hit | precision | recall |
|---|---|---|---|---|
| copilot_v2 | 0.74 | 0.11 | 0.75 | 0.41 |
| opus_baseline | 0.73 | 0.15 | 0.81 | 0.48 |

## Per-verdict detail

| item.rep | winner | margin | rationale (head) |
|---|---|---|---|
| pr4762.r1 | copilot_v2 | clear | Both candidates catch the trust_remote_code default-flip concern that the ground truth flags. Y additionally matches yuanheng-zhao's exact concern about positional-arg binding risk in the changed crea |
| pr4762.r2 | opus_baseline | clear | Y correctly identifies and reasons through the PR's central controversy (endpoint restrictions resolving from the correct post-override pipeline) and the trust_remote_code default flip, judging the la |
| pr4762.r3 | opus_baseline | clear | Y demonstrates deeper grounding: it explicitly recognizes the deploy-override pipeline-restriction fix (the reviewers' top concern) via the new regression test, engages accurately with the trust_remot |
| pr4777.r1 | copilot_v2 | clear | Ground truth shows this was a trivial, well-tested bound change with unanimous LGTM and no real concerns, so neither review had much to 'recall.' X's review hinges almost entirely on three 'blocking'  |
| pr4777.r2 | opus_baseline | clear | Ground truth is essentially a rubber-stamp approval with a manual verification comment confirming layers=2 now works and the L2/L4 regression passed, so there's little to 'recall' beyond confirming th |
| pr4777.r3 | opus_baseline | clear | Ground truth has no substantive concerns (just LGTM/approval plus a manual verification comment), so both candidates are graded mostly on precision/actionability of self-found issues. X's two findings |
| pr4804.r1 | opus_baseline | slight | Both candidates miss nearly all ground-truth concerns (slot-leak on abort, cumulative/delta rewind bug, floor/ceil latent bug, WER PCM fallback, docstring drift, missing vendor header, amy-why's clean |
| pr4804.r2 | copilot_v2 | clear | Neither candidate surfaced the ground-truth's substantive bugs (stream-slot leak on abort, cumulative/delta chunk_np rewind, floor/ceil division in audio_tokenizer_v2, legacy MOSS-Audio-Tokenizer mode |
| pr4804.r3 | copilot_v2 | slight | Both candidates miss nearly all of the ground-truth's real findings — the confirmed High-severity slot-leak-on-abort bug, the High-severity legacy-tokenizer-misload bug, the cumulative/delta chunk fli |
| pr4810.r1 | opus_baseline | clear | Both candidates independently catch the latent gap (the untouched hunyuan_image3_transformer.py diffusion loader still calling get_cache_scale), so gap_hit is true for both. X's other finding is tight |
| pr4810.r2 | opus_baseline | slight | Both candidates independently catch the latent gap — the still-live get_cache_scale call in hunyuan_image3_transformer.py — with X framing it more forcefully as a blocking 'major/FOLLOW-UP REQUIRED' i |
| pr4810.r3 | opus_baseline | clear | Both candidates independently surface the latent gap (the diffusion hunyuan_image3_transformer.py caller of the removed API), but Y grounds it more thoroughly by citing the PR's own file list and conf |
| pr4816.r1 | copilot_v2 | clear | Ground truth has no substantive concerns (just an approval), so both correctly land on no-blockers; recall is trivially satisfied by both. X's verification claims specific external upstream PR/line nu |
| pr4816.r2 | copilot_v2 | slight | Both correctly verify the rename is complete/consistent and tests updated appropriately; ground truth offers nothing substantive to miss, so recall is near-full for both. X leans on unverifiable exter |
| pr4816.r3 | copilot_v2 | clear | Both correctly confirm the rename is exhaustive and matches upstream, and ground truth has no substantive concerns to recall, so both score well on recall. Y is more precisely grounded (its cited line |
| pr4817.r1 | copilot_v2 | slight | Ground truth carries no substantive concerns, so recall is trivially satisfied by both. Both reviews correctly validate the core `== 10` fix and the rename cleanup; X raises one soft, hedged point abo |
| pr4817.r2 | copilot_v2 | slight | Ground truth has no substantive concerns, so recall is trivially satisfied by both. X offers one hedged, ultimately dismissed nit (sm_110a exclusion) and a clean approve. Y surfaces three concrete, fi |
| pr4817.r3 | copilot_v2 | slight | Ground truth has no substantive reviewer concerns, so both trivially achieve full recall. Both candidates correctly validate the core fix and tests without fabricating blockers, converging on the same |
| pr4825.r1 | opus_baseline | decisive | X's core finding — that hardcoding 'unet' grows a drifting set of denoiser-component lists and should instead be driven from the pipeline's own declared components (_dit_modules) — closely mirrors dso |
| pr4825.r2 | opus_baseline | decisive | X's design comment about deriving denoiser components from existing per-pipeline declarations (_dit_modules) instead of a growing hardcoded list closely parallels dsocek's ground-truth concern about d |
| pr4825.r3 | opus_baseline | decisive | X's top comment (reuse _dit_modules/_packed_modules_mapping instead of a hardcoded component list) closely mirrors dsocek's actual ground-truth concern about driving the mapper from existing per-model |
| pr4834.r1 | copilot_v2 | clear | Both candidates surface the ground-truth themes (regression tests already added, CuMemTag enum underused/half-utilized), so recall is similar and modest since the human thread was thin and already res |
| pr4834.r2 | copilot_v2 | slight | Both cover similar ground (enum underutilization, dead getattr guards, generate() guard correctness) and both hit the latent gap by questioning whether the new NotImplementedError guard is exercised/t |
| pr4834.r3 | copilot_v2 | slight | Both reviews are solid and both substantively hit the latent gap (guard-too-strict theme): X finds that the _level2_sleeping flag can never be cleared once set (wake_up always raises before reaching t |
| pr4837.r1 | opus_baseline | slight | Both candidates correctly reconstruct the core regression story and explicitly verify that removing the `already_submitted` gate is safe because both submit_initial and submit_update reject list promp |
| pr4837.r2 | opus_baseline | clear | The sole substantive ground-truth concern (yJader's inline comment explaining why the already_submitted gate should be dropped because both submit paths converge to identical diffusion semantics) is d |
| pr4837.r3 | opus_baseline | slight | Both candidates correctly reconstruct the core mechanism (already_submitted removal is safe because both submit_initial/submit_update reject list prompts uniformly), mirroring the ground-truth inline  |
| pr4849.r1 | opus_baseline | slight | Neither candidate surfaces the ground-truth procedural asks (precommit fix, benchmark run request), and both independently validate the parent-first ordering question that Gaohan123 raised (already re |
| pr4849.r2 | copilot_v2 | slight | Both candidates correctly validate the parent-first-ordering assumption that Gaohan123 flagged inline, with Y giving crisper line-cited evidence. But X better tracks the human thread's actual asks: it |
| pr4849.r3 | copilot_v2 | slight | Neither candidate surfaces the ground-truth reviewer's core concern (whether source_outputs[0] is reliably the parent, and whether a check/comment should guard that) as an actionable ask — both instea |
| pr4859.r1 | copilot_v2 | clear | Both correctly flag the audio_vae.py:141 config-mutation issue that GT reviewer amy-why-3459 raised, and both correctly treat the patch_emission.py stop-step change and refactor-consolidation as non-i |
| pr4859.r2 | copilot_v2 | clear | Both correctly flag the audio_vae.py config.num_hidden_layers mutation, the PR's central review thread. Y additionally catches the serving_speech.py language/dialect removal — a major concern amy-why- |
| pr4859.r3 | copilot_v2 | clear | X surfaces both real open questions from the GT thread (the audio_vae config.num_hidden_layers mutation and the serving_speech.py dropped language/方言 field, the latter mirroring amy-why-3459's exact a |
| pr4870.r1 | opus_baseline | clear | X correctly validates that the Med (scoping) and Nit (seq_len) ground-truth items are already fixed in this diff rather than re-flagging them, actually verifies the self.model_config aliasing claim in |
| pr4870.r2 | opus_baseline | clear | Both candidates validate the seq_len removal and the qwen3_tts scoping correctly, but X's 'new' findings are mostly three redundant restatements of the same async_chunk-default concern plus a trivial  |
| pr4870.r3 | opus_baseline | clear | Y correctly identifies that this diff already resolves the Med/Nit ground-truth items, then raises the residual default-value inconsistency (async_chunk getattr default True vs. the sibling code's Fal |
| pr4893.r1 | copilot_v2 | slight | Neither candidate surfaces the one substantive ground-truth concern (reduce_scatter test coverage), which appears already resolved in this diff anyway, so recall is weak for both. X offers several con |
| pr4893.r2 | copilot_v2 | slight | Ground truth is thin (mostly non-technical banter plus one inline nit about the reduce_scatter hasattr checks, which the diff already added), so recall is low for both. X engages more with the reduce_ |
| pr4893.r3 | copilot_v2 | slight | Ground truth is thin (mostly an approval and a tangential reduce_scatter test-coverage suggestion already incorporated into the diff), so neither candidate scores high recall. X is a careful, high-pre |
| pr4923.r1 | opus_baseline | clear | Y independently surfaces the two threads that dominate the actual PR discussion — the mtp-seed-reproducibility tradeoff under full cudagraphs (matching gcanlin's inline comment) and the demand for ful |
| pr4923.r2 | opus_baseline | clear | X explicitly surfaces the two things real reviewers actually cared about beyond the already-fixed TODO/NPU items: the silent loss of per-request seed reproducibility under full cudagraphs (gcanlin's e |
| pr4923.r3 | opus_baseline | clear | Ground truth centers on three threads: reviewers questioning why the model reads cudagraph_mode (a runner concern), demands for full before/after benchmark evidence, and the NPU PIECEWISE yaml fix plu |
| pr4926.r1 | copilot_v2 | slight | Both candidates catch the one clearly-confirmed ground-truth bug (varlen_func=None crash), but neither touches the docs-version question, test-marker requests, SM90 gating, or the try/except-masks-tes |
| pr4926.r2 | copilot_v2 | slight | Both catch the single confirmed major bug (varlen_func=None crash on masked path, matching RuixiangMa's comment) with good detail, but neither surfaces the doc/version-requirements question, test-mark |
| pr4926.r3 | opus_baseline | slight | Both candidates independently found the single most important confirmed-and-fixed ground-truth bug (varlen_func-None crash on masked path, matching RuixiangMa's comment) and the FA2/FA3 code-duplicati |
| pr4950.r1 | copilot_v2 | slight | Ground truth has no substantive concerns (just LGTM/approvals), so both trivially satisfy recall. Both did thorough diff verification against source, but X surfaced one concrete, grounded, actionable  |
| pr4950.r2 | copilot_v2 | slight | Ground truth has no substantive concerns (just LGTM approvals), so both candidates trivially achieve full recall and both correctly verify every diff claim against source with no fabrication, landing  |
| pr4950.r3 | copilot_v2 | slight | Ground truth has no substantive reviewer concerns (just LGTM/approve), so recall is trivially satisfied by both. Both candidates do solid diff-verification with specific source citations, but X's only |
| pr4954.r1 | opus_baseline | clear | Both candidates correctly validate the core codes.audio fix, but Y's non-blocking comments are more substantive: it identifies the real behavioral consequence GT's docstring-staleness comment was gest |
| pr4954.r2 | opus_baseline | clear | GT's core ask is that the docstring's 'strict behaviour preserved when escalation_model is None' claim is now false because containment fallback runs for all callers; X's comment #1 captures exactly t |
| pr4954.r3 | copilot_v2 | slight | Both correctly validate the core fix and flag doc/comment gaps around the new containment fallback and the legacy-vs-nested audio read at similar locations, with no fabricated findings. Y more directl |
| pr4970.r1 | opus_baseline | slight | Ground truth for this PR is essentially just an LGTM plus an unrelated scope-split request (VoxCPM2) that isn't derivable from the shown diff, so recall is capped similarly for both since neither surf |
| pr4970.r2 | opus_baseline | slight | Ground truth is essentially empty (an LGTM approval plus an unrelated request to spin off a VoxCPM2 fix into a separate PR, which neither candidate mentions), so recall is low and near-identical for b |
| pr4970.r3 | opus_baseline | slight | Both candidates correctly and accurately trace the seed→tts_local_seed→batched-multinomial mechanism with grounded file/line citations and reach the same APPROVE verdict as the human reviewer (LGTM);  |
| pr4977.r1 | opus_baseline | slight | Both candidates surfaced the same PR-description/trust_remote_code discrepancy but neither caught the actual ground-truth concern (kernels version incompatibility with the trust_remote_code kwarg), so |
| pr4977.r2 | copilot_v2 | slight | Neither candidate identifies the ground truth's actual concern (kernels<0.15.0 lacking a lower bound means 0.13.x installs can't accept trust_remote_code), but both independently flag the same trust_r |
| pr4977.r3 | opus_baseline | slight | Both candidates independently caught the same tangential issue to the ground truth (PR description claims trust_remote_code=True but it's absent from the diff/code), giving them equal partial recall o |
| pr5009.r1 | opus_baseline | clear | X substantively engages the two dominant ground-truth threads — the global-scope-vs-Qwen-only validation concern (citing the FLUX A/B evidence that resolved it) and the perf/accuracy comparison ask —  |
| pr5009.r2 | opus_baseline | clear | Y engages with the central, most-discussed ground-truth concern (global scope of the platform-default change, validated only on Qwen-Image, and whether FLUX/perf/accuracy evidence justifies it) and ex |
| pr5009.r3 | opus_baseline | clear | The dominant ground-truth thread is the scoping risk of making vllm_c the global CUDA default when only validated on Qwen-Image/H200 (hsliuustc0106's main comment, plus NumberWan's FLUX.1-dev justific |
