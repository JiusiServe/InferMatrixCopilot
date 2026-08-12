# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)

Judge: claude-sonnet-5 (blind, randomized order, 3 replicates x 10 items = 60 verdicts)

## Wins
- copilot_v2: 4
- opus_baseline: 56
- tie: 0

## Mean rubric scores

| arm | actionability | gap_hit | precision | recall |
|---|---|---|---|---|
| copilot_v2 | 0.30 | 0.00 | 0.41 | 0.21 |
| opus_baseline | 0.83 | 0.17 | 0.82 | 0.57 |

## Per-verdict detail

| item.rep | winner | margin | rationale (head) |
|---|---|---|---|
| pr4762.r1 | opus_baseline | clear | X directly engages with the PR's most heavily-discussed ground-truth issue (deploy-override endpoint-restriction resolution ordering), correctly recognizing it's now resolved via the added regression  |
| pr4762.r2 | opus_baseline | clear | X misses the PR's central concern (endpoint restrictions resolved from the wrong pipeline) entirely and its one overlapping finding (trust_remote_code default) gets the direction backwards, recommendi |
| pr4762.r3 | opus_baseline | clear | Y explicitly addresses and verifies the single most important ground-truth finding (endpoint restrictions must resolve from the final, deploy-override pipeline, not the auto-detected one) plus the tru |
| pr4777.r1 | opus_baseline | decisive | X did substantive verification mirroring what the human validator actually did (confirmed the range/message consistency across image_api_utils.py and protocol/images.py, traced both API entrypoints, a |
| pr4777.r2 | opus_baseline | clear | Ground truth has no substantive reviewer concerns (just LGTM approvals and a verification comment confirming the shown 4-file diff works), so recall is trivially satisfied by both candidates. X correc |
| pr4777.r3 | opus_baseline | decisive | Ground truth contains no substantive concerns (two LGTM approvals, a bot verification comment confirming the boundary change works), so recall is trivially satisfied by both. Candidate X reports zero  |
| pr4804.r1 | opus_baseline | clear | X's 10 findings almost entirely miss the ground-truth concerns (slot-leak on abort, cumulative/delta rewind bug, ceil/floor length truncation, legacy-checkpoint v2 misinstantiation, WER PCM fallback r |
| pr4804.r2 | copilot_v2 | clear | Neither candidate surfaces the ground truth's core confirmed bugs (slot leak, cumulative/delta chunk re-slice, ceil/floor length bug, v2-tokenizer/legacy-checkpoint collision), so recall is low for bo |
| pr4804.r3 | copilot_v2 | clear | Neither candidate surfaces the ground truth's core findings (slot-leak on abort, cumulative/delta re-slice bug, ceil-division length bug, legacy-checkpoint v2-tokenizer ambiguity, missing vendored-hea |
| pr4810.r1 | opus_baseline | decisive | X delivers a substantive, evidence-grounded review that verifies the design against the actual upstream vLLM source, and its note 2 explicitly flags that the diffusion-loader file (hunyuan_image3_tran |
| pr4810.r2 | opus_baseline | decisive | X returned zero findings despite the PR having real, if non-blocking, discussion points—total miss on recall and actionability. Y independently verified the design against actual upstream vLLM source, |
| pr4810.r3 | opus_baseline | decisive | Y independently verifies the design against upstream vLLM source, echoes the ground-truth reviewer's core point (delegated loaders correctly rely on the outer AutoWeightsLoader mapper; the added test  |
| pr4816.r1 | opus_baseline | clear | Ground truth has no substantive concerns (Codex hit its limit, human reviewer just said 'lgtm'), so both candidates trivially satisfy recall by reaching the same approve conclusion. Candidate X earns  |
| pr4816.r2 | opus_baseline | decisive | Ground truth has no substantive concerns (just an 'lgtm' approval and a bot message about exhausted credits), so both candidates reach the correct verdict of no blockers. But X does real, grounded ver |
| pr4816.r3 | opus_baseline | clear | Ground truth has no substantive concerns (bot noise + a plain 'lgtm' approval, no inline comments), so both candidates trivially achieve full recall by approving. Candidate X does real verification wo |
| pr4817.r1 | opus_baseline | decisive | Ground truth has no substantive reviewer concerns to recall, so both trivially satisfy recall, but X does real, mostly-accurate work: it correctly verifies the >=10→==10 gate logic, checks the rename  |
| pr4817.r2 | opus_baseline | clear | Ground truth has no substantive concerns, so both trivially avoid missing anything, but X actually demonstrates grounded verification work: confirms the rename is applied consistently, checks truthy/f |
| pr4817.r3 | opus_baseline | clear | Ground truth has no substantive reviewer concerns, so recall is trivially satisfied by both. Candidate X returns zero findings with no analysis shown, so it makes no false claims (precision 1.0) but o |
| pr4825.r1 | opus_baseline | decisive | X engages substantively with the diff and surfaces a concern that closely mirrors dsocek's real ground-truth comment — the hardcoded component-name list is a maintenance/drift risk and could instead b |
| pr4825.r2 | opus_baseline | decisive | X delivers a substantive, diff-grounded review: it correctly validates the unet-scan change, flags a real design concern about hardcoded component lists (conceptually echoing dsocek's point about cent |
| pr4825.r3 | opus_baseline | decisive | X delivers a detailed, code-grounded review with specific file/line references, correctly validates the change's safety, and raises a design concern (hardcoded default_components list drifting across  |
| pr4834.r1 | opus_baseline | decisive | X delivers a thorough, line-grounded review that engages both ground-truth reviewer threads (test coverage, the CuMemTag enum) and, crucially, its finding #1 (default sleep(level=2) combined with the  |
| pr4834.r2 | opus_baseline | decisive | Candidate X delivers a substantive, well-grounded review that independently surfaces both ground-truth concerns (test coverage gap mirrors SamitHuang's regression-test ask; finding #5 echoes Gaohan123 |
| pr4834.r3 | opus_baseline | decisive | X reports zero findings and never engages with the two things human reviewers actually flagged (need for regression tests, need for a tags enum) despite both being visible as freshly-added code in the |
| pr4837.r1 | opus_baseline | decisive | X independently verifies both hunks against actual call sites (stage_pool.py submit_initial/submit_update both reject list prompts), arriving at the same conclusion as yJader's inline comment — that g |
| pr4837.r2 | opus_baseline | decisive | Ground truth here is thin (two LGTM approvals plus one inline comment from yJader explaining why the already_submitted-gated unwrap should be dropped since both submit_initial/submit_update reject lis |
| pr4837.r3 | opus_baseline | decisive | Candidate X independently verifies both diff hunks with concrete file/line references and reproduces the ground-truth reviewer's exact reasoning — that already_submitted doesn't semantically distingui |
| pr4849.r1 | opus_baseline | decisive | X performs a substantive investigation, directly engaging the parent-first-output assumption that Gaohan123 flagged (even if concluding no runtime check is needed rather than recommending one), and gr |
| pr4849.r2 | opus_baseline | decisive | Candidate X returned zero findings, missing the one substantive ground-truth concern (whether source_outputs[0] is reliably the parent AR output) entirely and offering nothing actionable. Candidate Y  |
| pr4849.r3 | opus_baseline | decisive | X reported zero findings, missing every ground-truth concern (the parent-first ordering assumption, the precommit fix request, the benchmark-run ask) and offering nothing actionable. Y independently i |
| pr4859.r1 | opus_baseline | decisive | X correctly surfaces and reasons through the two meatiest ground-truth threads (the audio_vae config mutation and the min_stop_step+1→+2 window change), independently arriving at the same 'intentional |
| pr4859.r2 | opus_baseline | decisive | X covers more of the ground-truth threads (config mutation, the intentional decode-window +2 change, the PCM-format refactor dedup, and the include_language removal with test verification) and correct |
| pr4859.r3 | opus_baseline | clear | Y independently surfaces and correctly calibrates the same audio_vae.py:141 config-mutation concern that amy-why-3459 raised (noting the encoder itself is unaffected since already constructed, matchin |
| pr4870.r1 | opus_baseline | decisive | X did real investigation: it confirmed the qwen3_tts scoping fix, independently rediscovered the ground truth's Low concern (async_chunk getattr defaulting to True, inconsistent with the rest of the f |
| pr4870.r2 | opus_baseline | decisive | X returned zero findings on a diff whose visible state actually still invites scrutiny, providing no recall, precision, or actionability. Y did substantive verification (confirmed the streaming-scope  |
| pr4870.r3 | opus_baseline | decisive | X (OCR) returned zero findings, missing every ground-truth concern and the latent gap entirely. Y independently verified the runner fix's correctness, confirmed the qwen3_tts streaming scoping and its |
| pr4893.r1 | opus_baseline | decisive | Ground truth is thin (mostly non-technical comments plus one inline note about verifying reduce_scatter in the test), so neither candidate hits that specific nuance. X returns zero findings with no ev |
| pr4893.r2 | opus_baseline | decisive | X returned zero findings, contributing nothing verifiable or actionable and missing the ground-truth's test-coverage concern entirely. Y performed genuine grounded verification of the diff (DPMetadata |
| pr4893.r3 | opus_baseline | decisive | X performs genuine code-level analysis (verifying DPMetadata construction, device_communicator semantics, group cleanup, and the CFG/DP gating change) and grounds its one non-blocking comment in a spe |
| pr4923.r1 | opus_baseline | decisive | X's sole finding (a duplicate assignment nit) doesn't overlap with any ground-truth reviewer concern, and its claim references a line outside the shown diff, making it hard to verify. Y independently  |
| pr4923.r2 | opus_baseline | clear | X engages with themes close to the real reviewer thread (the NPU cudagraph_mode fix, and the seed-reproducibility caveat baked into the TODO comment) and lands one clearly diff-grounded finding (the n |
| pr4923.r3 | opus_baseline | clear | X surfaces only one nit (likely real, since Y independently reports the identical duplicate-assignment at the same lines) but it matches none of the actual reviewer thread (cudagraph-in-modeling archi |
| pr4926.r1 | opus_baseline | slight | X's top-billed finding (integer version= silently no-ops) is directly contradicted by the author's own follow-up comment explaining version=1/2 are valid git-branch refs, hurting its precision, but X' |
| pr4926.r2 | copilot_v2 | slight | Both miss the bulk of ground-truth concerns, which center on the test file (markers, skipif, try/except-masks-CI-failures) and docs (kernel version requirements) — Y ignores the test file and docs ent |
| pr4926.r3 | opus_baseline | clear | X only reviewed platform.py/flash_attn_hub.py and missed every ground-truth theme (docs version question, test markers/skipif, test try/except masking failures, version=1/2 confusion) — its four findi |
| pr4950.r1 | opus_baseline | decisive | Ground truth has no substantive concerns (just LGTM/approvals), so recall is trivially satisfied by both. X performed no actual review — it was filtered out on file-extension grounds and produced zero |
| pr4950.r2 | opus_baseline | decisive | Candidate X delivers a substantive, evidence-based review that verifies each of the PR's technical claims against source (file:line citations for chat_template_kwargs handling, the two-choices behavio |
| pr4950.r3 | opus_baseline | decisive | Ground truth contains no substantive concerns (just LGTM/approval), so there is little to recall, but X still produced a thorough, source-grounded verification of every technical claim in the diff (cu |
| pr4954.r1 | opus_baseline | clear | Y independently reconstructs the reviewer's core insight (codes.audio write/read mismatch since #4527) and its first non-blocking comment substantively overlaps ground truth's concern about the contai |
| pr4954.r2 | opus_baseline | decisive | X correctly explains the core read/write mismatch fix (matching the GT reviewer's rationale) and independently surfaces a real, verifiable looseness in the new containment fallback (concrete counterex |
| pr4954.r3 | opus_baseline | decisive | X correctly verifies the core codes.audio/legacy-audio fix (matching GT's main point) and independently surfaces that the new containment fallback applies unconditionally to all callers of _assert_tra |
| pr4970.r1 | opus_baseline | clear | Ground truth has no substantive inline concerns (just LGTM/approve plus an unrelated VoxCPM2 note), so both candidates technically 'recall' everything relevant. X is a bare boilerplate '0 findings' wi |
| pr4970.r2 | opus_baseline | clear | Ground truth contains no substantive reviewer concerns (just LGTM/approve), so both candidates correctly land on 'no blockers.' X delivers only a bare zero-finding verdict with no visible verification |
| pr4970.r3 | opus_baseline | decisive | Ground truth is a trivial clean-approve PR (LGTM, no inline comments), so the bar is low, but X still does real work: it traces the seed-propagation mechanism through named files/lines, correctly reac |
| pr4977.r1 | opus_baseline | clear | Neither candidate reproduces the ground truth's actual concern (trust_remote_code kwarg incompatible with locked kernels<0.15.0 installs), but Y at least surfaces the trust_remote_code topic via a ver |
| pr4977.r2 | opus_baseline | clear | Neither candidate reproduces the ground-truth P2 concern (trust_remote_code compatibility with pinned kernels<0.15), but X at least surfaces the trust_remote_code discrepancy (noting it's promised in  |
| pr4977.r3 | copilot_v2 | clear | Neither candidate surfaces the ground-truth concern (trust_remote_code kwarg breaking on locked kernels<0.15.0), so recall is 0 for both. X's lock-contention finding is solid and grounded, with concre |
| pr5009.r1 | opus_baseline | decisive | X engages substantively with the diff, verifies the norm swap's signature-safety, and directly addresses the ground truth's central scope concern (global CUDA default vs. Qwen-only validation), even c |
| pr5009.r2 | opus_baseline | decisive | Candidate X returns zero findings and zero explanation of what was checked, so it contributes nothing comparable to the ground-truth concerns about override scope, test coverage of the inductor/oink b |
| pr5009.r3 | opus_baseline | decisive | X returned zero findings, missing every ground-truth concern (scope of the global default change, test coverage, perf/accuracy evidence) with no actionable content. Y correctly surfaces the central sc |
