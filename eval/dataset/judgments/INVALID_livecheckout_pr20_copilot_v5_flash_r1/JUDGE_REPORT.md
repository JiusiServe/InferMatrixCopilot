# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)

Judge: claude-sonnet-5 (blind, randomized order, 3 replicates x 10 items = 60 verdicts)

## Wins
- copilot_v2: 31
- opus_baseline: 29
- tie: 0

## Mean rubric scores

| arm | actionability | gap_hit | precision | recall |
|---|---|---|---|---|
| copilot_v2 | 0.81 | 0.14 | 0.65 | 0.52 |
| opus_baseline | 0.69 | 0.19 | 0.78 | 0.49 |

## Per-verdict detail

| item.rep | winner | margin | rationale (head) |
|---|---|---|---|
| pr4762.r1 | copilot_v2 | slight | Y independently rediscovers and extends the single most significant ground-truth-confirmed bug (endpoint restrictions resolved from a pipeline that may not match the final deploy-overridden pipeline), |
| pr4762.r2 | copilot_v2 | clear | X independently rediscovers both of the GT's heaviest-weighted concerns — the trust_remote_code default flip (author: 'this looks like a bug') and the endpoint-restrictions-resolved-from-wrong-pipelin |
| pr4762.r3 | copilot_v2 | slight | X hits the two dominant GT threads (trust_remote_code default flip and endpoint-restrictions-resolved-from-wrong-pipeline) and even extends the latter with a well-grounded, specific claim that the fix |
| pr4777.r1 | copilot_v2 | clear | Both candidates correctly validated the core boundary-value change and explored beyond the diff into pipeline/API call sites, and both exceed the (essentially empty, LGTM-only) ground truth in depth.  |
| pr4777.r2 | opus_baseline | slight | Ground truth contains no substantive reviewer concerns (just approvals and bot noise), so recall is trivially satisfied by both. Both candidates go beyond the diff with well-evidenced, file/line-groun |
| pr4777.r3 | copilot_v2 | clear | Ground truth is thin (two LGTMs plus a verification comment confirming boundary/unit/L4 tests pass), so neither candidate has much to 'recall' and both correctly validate the core range-consistency lo |
| pr4804.r1 | opus_baseline | slight | Both miss most ground-truth concerns (slot-leak on abort, ceil-division bug in audio_tokenizer_v2.py:949, v2-tokenizer/legacy-checkpoint mismatch, docstring/provenance issues, WER-fallback raw-bytes s |
| pr4804.r2 | copilot_v2 | slight | Both miss the two most significant confirmed bugs (High-severity slot leak, Medium-latent ceil-division bug), and neither surfaces the hsliuustc0106 legacy-checkpoint model_type collision cleanly. X a |
| pr4804.r3 | copilot_v2 | slight | Both miss nearly all confirmed ground-truth bugs (slot leak, cumulative/delta flip, ceil-division, legacy-checkpoint v2 routing); X even asserts the slot-leak area is 'handled' and vendor headers are  |
| pr4810.r1 | opus_baseline | clear | Both explicitly flag the unswept hunyuan_image3_transformer.py diffusion loader (the latent gap) and both touch the ground truth's 'fake-param test doesn't prove real resolution' concern, but X ground |
| pr4810.r2 | opus_baseline | clear | Both correctly reconstruct why delegated vs. direct loaders differ and both explicitly flag the diffusion-transformer loader dropped from _STALE_API_FILES, hitting the latent gap. X's headline 'major' |
| pr4810.r3 | opus_baseline | slight | Both candidates independently surface the same latent gap (hunyuan_image3_transformer.py's un-swept get_cache_scale caller) and both echo the ground truth's core concern that the new test verifies the |
| pr4816.r1 | opus_baseline | clear | The PR is a mechanical attribute rename across 2 files, matched by real reviewers with a plain 'lgtm' — nothing substantive to recall for either candidate. X correctly scopes its review to the diff, v |
| pr4816.r2 | opus_baseline | slight | Ground truth shows this is a trivial, clean rename PR (human reviewer: 'lgtm', no inline comments), and X's concise approve-with-verification (confirmed rename completeness and upstream alignment) mat |
| pr4816.r3 | copilot_v2 | slight | Ground truth has no substantive concerns (bot hit rate limits, human just said 'lgtm'), so recall is vacuous for both. X delivers a clean, well-grounded approve that correctly verifies the rename is c |
| pr4817.r1 | copilot_v2 | slight | Ground truth has no substantive concerns (bot noise + 'thanks'), so both reviews are essentially graded on grounded thoroughness rather than recall. X is a competent, accurate pass/fail table with one |
| pr4817.r2 | copilot_v2 | clear | Ground truth has no substantive concerns (just Codex quota noise and 'thanks'), so recall is vacuous for both. X offers a mostly PASS scan plus one speculative, hedged nit (sm_110a) that isn't grounde |
| pr4817.r3 | opus_baseline | slight | Ground truth has no substantive concerns to recall, so both score fully there. X is thorough (greps, reads) and gives concrete file:line/edit suggestions, but several findings (hardware-table wording, |
| pr4825.r1 | copilot_v2 | slight | Neither candidate surfaces dsocek's actual concern (driving the component/mapper list from _packed_modules_mapping to auto-cover fused-projection renames like to_q/k/v→to_qkv), so recall is low for bo |
| pr4825.r2 | copilot_v2 | clear | Both candidates converge on a similar theme to the one substantive ground-truth design concern (dsocek's push to avoid duplicated hardcoded component lists), with X proposing to read pipeline._dit_mod |
| pr4825.r3 | copilot_v2 | slight | Both candidates converge on the closest analog to the real reviewer concern (dsocek's point about a hardcoded/duplicated component list, echoed via the three enumerations in registry.py/offloader/mana |
| pr4834.r1 | opus_baseline | slight | X covers both substantive ground-truth threads (the regression-test ask and the enum suggestion, both visible in the inline comments) and its top finding — default sleep() level=2 permanently bricking |
| pr4834.r2 | opus_baseline | slight | X covers more of the thin ground truth (explicitly critiques the CuMemTag enum usage per Gaohan123's ask, notes a CI lane issue, and engages with test coverage), while Y omits the enum entirely and do |
| pr4834.r3 | opus_baseline | clear | Y's finding #1 (default sleep() level=2 permanently bricks the engine after wake_up, since the NotImplementedError guard fires on the common bare-sleep() path) is a precise, high-value hit on the late |
| pr4837.r1 | opus_baseline | slight | Both candidates independently verify the same core fact set as the ground truth's sole inline comment (already_submitted is redundant since both submit paths reject list prompts), and both correctly d |
| pr4837.r2 | opus_baseline | slight | Both candidates independently arrive at the same core technical justification as the ground-truth inline comment (both submit_initial/submit_update reject list prompts identically, so gating the unwra |
| pr4837.r3 | opus_baseline | slight | Both candidates correctly reconstruct the ground-truth reviewer's core point — that dropping `already_submitted` is safe because both submit_initial and submit_update reject list prompts identically — |
| pr4849.r1 | copilot_v2 | clear | Y independently surfaces both substantive ground-truth concerns — the parent-is-first assumption (matching Gaohan123's exact question, going further to propose a concrete assert) and a request to vali |
| pr4849.r2 | copilot_v2 | clear | The ground truth's central concern (Gaohan123: is source_outputs[0] reliably the parent, and should there be a check/comment) is exactly what X surfaces as an actionable finding, complete with a concr |
| pr4849.r3 | copilot_v2 | slight | The ground truth's central concern is Gaohan123's question about whether source_outputs[0] is reliably the parent and whether a check/comment is needed. X hits this directly and even proposes a concre |
| pr4859.r1 | copilot_v2 | clear | Y independently surfaces the serving_speech.py language/方言 removal concern that amy-why-3459 and LHXuuu discussed at length in ground truth, plus the audio_vae.py config-mutation issue also raised the |
| pr4859.r2 | copilot_v2 | slight | Y independently surfaces both real reviewer debates — the serving_speech.py language/方言 removal (matching amy-why-3459's actual comment almost exactly) and the audio_vae.py config mutation (matching a |
| pr4859.r3 | copilot_v2 | slight | X catches the serving_speech.py language/dialect removal — a substantial ground-truth thread with real reviewer debate — and correctly flags the audio_vae.py config-mutation hazard, both with concrete |
| pr4870.r1 | opus_baseline | slight | Both candidates correctly verify the seq_len removal and the qwen3 scoping fix, and both independently flag the async_chunk default (True vs the codebase's established False) as an inconsistency, echo |
| pr4870.r2 | opus_baseline | slight | Both candidates independently rediscover the Low/default-inconsistency concern (async_chunk defaulting True vs False elsewhere), but neither surfaces the Med blast-radius discussion or amy's architect |
| pr4870.r3 | opus_baseline | clear | Both catch the residual async_chunk default-value inconsistency (matching the ground-truth Low comment), and neither surfaces the amy-why design question, so recall is comparable. X's precision is und |
| pr4893.r1 | copilot_v2 | clear | The only substantive ground-truth concern (yenuo26's inline note about verifying reduce_scatter in the test) is touched on tangentially by X's minor comment on the test-fake scaffolding, while Y never |
| pr4893.r2 | copilot_v2 | clear | The only substantive ground-truth concern (yenuo26's inline comment questioning whether the test adequately verifies the reduce_scatter fix) is touched by X's finding on the same line/topic but entire |
| pr4893.r3 | copilot_v2 | slight | The lone concrete ground-truth concern (reduce_scatter verification adequacy in the fake-group test) is untouched by X, which reads as a confident approval with confirmatory checks but no findings res |
| pr4923.r1 | opus_baseline | clear | Both candidates surface the two real reviewer threads (cudagraph_mode belonging in the runner not the model, and the mtp-seed-under-full-cudagraphs consequence), and Y additionally echoes the benchmar |
| pr4923.r2 | opus_baseline | clear | Both candidates independently surface the duplicate omni_pooler_payload_include_hidden assignment, the stale YAML doc comments, and engage with the seed-reproducibility/full-cudagraph tradeoff that mi |
| pr4923.r3 | opus_baseline | clear | Y stays grounded in the shown diff (stale header comments, duplicate `omni_pooler_payload_include_hidden`, NPU PIECEWISE question) and directly echoes the actual reviewer thread's biggest ask — a full |
| pr4926.r1 | opus_baseline | clear | X's finding #3 (varlen_func possibly None causing a crash in piecewise/masked paths) is a precise, fully-elaborated match to RuixiangMa's confirmed real bug, and X's broad-except critique echoes Ruixi |
| pr4926.r2 | opus_baseline | clear | X independently surfaces both the confirmed varlen_func-None crash (RuixiangMa's actual finding, albeit mirrored to the masked path) and the swallowed-exception version-cascade issue that echoes the r |
| pr4926.r3 | opus_baseline | slight | Y independently surfaces the piecewise_attn crash-on-None-varlen-func bug (flash_attn_hub.py masked/varlen paths), which matches RuixiangMa's confirmed ground-truth finding that was actually fixed by  |
| pr4950.r1 | copilot_v2 | slight | Ground truth has no substantive concerns (just LGTM approvals), so both trivially achieve full recall. X's findings are well-grounded and concrete — notably catching that examples/online_serving/minic |
| pr4950.r2 | copilot_v2 | slight | Ground truth has no substantive reviewer concerns (just LGTM/approve), so both trivially achieve full recall. X gives a tight, well-evidenced verification of the diff's three claims with specific file |
| pr4950.r3 | copilot_v2 | slight | Ground truth has no substantive reviewer concerns (just an LGTM approval), so both trivially achieve full recall. X is tightly scoped and safely grounded, verifying diff claims against source with spe |
| pr4954.r1 | opus_baseline | slight | Both candidates catch the core ground-truth concern (the new containment fallback silently weakens/bypasses the opt-in escalation guarantee, contradicting the docstring) with concrete evidence and fix |
| pr4954.r2 | copilot_v2 | clear | Both candidates correctly validate the core codes.audio fix, but Y more precisely reproduces the ground-truth reviewer's central non-blocking concern — that the containment fallback silently weakens t |
| pr4954.r3 | copilot_v2 | slight | Both correctly validate the core codes.audio fix, but neither flags the human reviewer's stale-docstring point. Y goes further by tracing the containment-fallback-vs-escalation interaction with a conc |
| pr4970.r1 | opus_baseline | clear | Ground truth here is essentially trivial (a maintainer asked for a separate PR on an unrelated VoxCPM2 regression and approved) — neither candidate covers that, so recall is near-zero for both. Candid |
| pr4970.r2 | opus_baseline | clear | The PR is a trivial 2-line seed removal that was approved with a plain 'LGTM' and no inline concerns, so there's little to recall for either side. X manufactures four hedged 'minor' findings (test-cla |
| pr4970.r3 | opus_baseline | clear | Ground truth shows this was a trivial, uncontroversial LGTM/approve with no substantive concerns, so recall is a wash for both. X correctly diagnoses the mechanism, reaches the matching APPROVE verdic |
| pr4977.r1 | copilot_v2 | clear | Neither candidate surfaces the ground-truth concern (trust_remote_code causing regressions against unpinned kernels<0.15.0); both instead claim trust_remote_code is absent from the diff, which is like |
| pr4977.r2 | copilot_v2 | slight | Both candidates independently noticed the same core discrepancy relevant to the ground-truth concern (PR description claims trust_remote_code=True but it's absent from the diff), giving each partial,  |
| pr4977.r3 | copilot_v2 | slight | Neither candidate reproduces the ground-truth codex concern (trust_remote_code kwarg breaking on locked kernels<0.15.0) since the diff they saw shows no such kwarg being added; both instead independen |
| pr5009.r1 | opus_baseline | clear | X directly engages the ground-truth's central concern (global-default scope risk vs. limited validation) and correctly notes the FLUX.1-dev A/B evidence that answers it, while also flagging the now-va |
| pr5009.r2 | copilot_v2 | clear | Both candidates converge on similar defensible verdicts and touch the scope-of-change and test-coverage themes from the ground truth, but neither explicitly reproduces the reviewers' core asks (scope  |
| pr5009.r3 | opus_baseline | clear | Y directly engages the ground truth's central concern (scope risk requiring non-Qwen validation) by verifying and citing the FLUX.1-dev A/B numbers that actually resolved it, and its 'vacuous parametr |
