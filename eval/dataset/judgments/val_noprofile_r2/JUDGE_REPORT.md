# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)

Judge: claude-sonnet-5 (blind, randomized order, 3 replicates x 10 items = 29 verdicts)

## Wins
- copilot_v2: 6
- opus_baseline: 23
- tie: 0

## Mean rubric scores

| arm | actionability | completeness | correctness | gap_hit | grounding | precision | recall |
|---|---|---|---|---|---|---|---|
| copilot_v2 | 0.74 | 0.66 | 0.70 | 0.33 | 0.66 | 0.65 | 0.59 |
| opus_baseline | 0.71 | 0.83 | 0.81 | 0.33 | 0.79 | 0.84 | 0.56 |

## Per-verdict detail

| item.rep | winner | margin | rationale (head) |
|---|---|---|---|
| issue4793.r1 | opus_baseline | slight | Both correctly identify the #4527 regression (None sentinel skipping accumulate_full_payload_output) fixed by #4792, already folded into the 0.24 rebase — matching the ground truth exactly, including  |
| issue4793.r2 | opus_baseline | slight | Both candidates correctly identify PR #4527 as the regression source and PR #4792 as the fix already folded into the 0.24 rebase commit a560ed18, matching the ground truth exactly (both even quote the |
| issue4793.r3 | opus_baseline | slight | Both candidates converge on the same correct diagnosis (PR #4527 regression fixed by #4792, already folded into the 0.24 rebase) and both quote the exact ground-truth code comment verbatim, so correct |
| issue4827.r1 | opus_baseline | slight | Both correctly diagnose the base-tokenizer/extended-ratio-token crash and the config mismatch (moe.yaml=Instruct two-stage vs dit.yaml=base single-stage), matching the thread's resolution and FayeSpic |
| issue4827.r2 | opus_baseline | slight | Both correctly diagnose the missing-extended-ratio-token crash and the base-vs-Instruct config mismatch, matching the thread; both cite the confirmed DiT workaround and defer the hardening work to a f |
| issue4827.r3 | opus_baseline | slight | Both candidates correctly diagnose the None+1 crash from missing extended ratio tokens in the base tokenizer, cite the same code path and Tencent reference guard, and give the exact workaround FayeSpi |
| issue4842.r1 | opus_baseline | slight | Both correctly diagnose the run-level mismatch (default core_model → dummy weights) matching the actual 'invalid' resolution, and both cite the same core files (run_args.py, stage_config.py's _add_dum |
| issue4842.r2 | opus_baseline | slight | Both candidates correctly diagnose the issue as a run-level mismatch (default core_model → dummy weights) rather than a real bug, matching the thread's 'invalid' resolution and citing the same core ev |
| issue4891.r1 | opus_baseline | decisive | Both reach the correct top-level 'duplicate' verdict, but X asserts with false confidence that the diffusion-loader fix 'has since landed on main' and shows a fabricated-looking file comment, seemingl |
| issue4891.r2 | opus_baseline | decisive | Ground truth resolves this as 'duplicate of #4808'; Y explicitly reaches and justifies that same duplicate-closure conclusion, correctly notes its own checkout is the rebase branch (not upstream main) |
| issue4891.r3 | opus_baseline | clear | Ground truth closes #4891 as a duplicate of #4808 (see #4809 for details); X reaches exactly this verdict, ties it to the #4809 triage tracking issue, and flags a legitimate real risk (that #4808 show |
| issue4905.r1 | opus_baseline | slight | Both correctly identify PR #4834 as the trigger (matching yenuo26's comment) but both overclaim a resolved state — asserting the level=1 fix is 'already in main' and recommending closure — when the ac |
| issue4905.r2 | opus_baseline | slight | Both correctly tie the failure to PR #4834's new wake_up() guard, matching yenuo26's thread comment that the error appeared after that merge — a plausible, grounded root cause. But both overreach by a |
| issue4905.r3 | copilot_v2 | slight | Both correctly identify PR #4834 as the source of the new NotImplementedError guard, matching yenuo26's comment, but both then confidently assert the issue is 'already fixed on main' and should be 'cl |
| pr4810.r1 | opus_baseline | slight | Both correctly validate the delegated-vs-direct loader design and both independently find the uncovered hunyuan_image3_transformer.py caller of the removed get_cache_scale API, satisfying the latent g |
| pr4810.r2 | opus_baseline | clear | Both candidates independently found the key latent gap (the unswept get_cache_scale caller in hunyuan_image3_transformer.py), satisfying gap_hit, but Y ties it directly to the PR's own listed affected |
| pr4810.r3 | opus_baseline | clear | Both independently surfaced the exact latent gap (hunyuan_image3_transformer.py:2238 still calling the removed get_cache_scale), so gap_hit is true for both. Y's review is more rigorous: it traces the |
| pr4816.r1 | opus_baseline | clear | X correctly identifies the root cause (upstream's shared `base()` helper hardcodes `state.serving_tokenization`), verifies against the actual upstream checkout including the exact traceback line, and  |
| pr4816.r2 | opus_baseline | clear | Ground truth shows zero substantive concerns (a plain 'lgtm' approval), so both candidates correctly find no blockers via accurate hunk-by-hunk verification. X stops there, cross-checks against the ac |
| pr4816.r3 | opus_baseline | clear | Ground truth is a trivial clean rename PR (lgtm, no comments). X correctly approves with well-grounded verification (checked upstream matches, confirmed no missed occurrences, noted test coverage) and |
| pr4825.r1 | copilot_v2 | clear | Both hit similar recall on the loosely-related ground-truth theme (dsocek's 'derive from existing per-model mapping instead of hardcoding'), neither nailing the specific PEFT-naming-conflict angle. X' |
| pr4825.r2 | opus_baseline | slight | Neither candidate recovers the ground-truth reviewer's core ask (dsocek's suggestion to derive naming from `_packed_modules_mapping`, which referred to code apparently removed before merge per tthakka |
| pr4825.r3 | copilot_v2 | slight | Ground truth is sparse (two LGTM approvals, one thread about a change later removed from the PR), so neither candidate has much to recall, but both independently converge on the same underlying theme  |
| pr4837.r1 | opus_baseline | decisive | X directly verifies the exact question the ground-truth reviewer (yJader) answers — checking that both submit_initial and submit_update reject list prompts for diffusion, confirming the already_submit |
| pr4837.r2 | opus_baseline | decisive | The one substantive ground-truth signal (yJader's inline comment) explains that dropping the already_submitted gate is correct and intentional, since both submit_initial and submit_update reject list  |
| pr4837.r3 | opus_baseline | decisive | The ground-truth inline comment explains why dropping `already_submitted` is safe: both submit_initial and submit_update reject list prompts identically for diffusion, so unconditional unwrapping is c |
| pr4893.r1 | copilot_v2 | decisive | X's top finding (test_expert_parallel_layout.py:121 — TP missing device_communicator/reduce_scatter assertions despite now using init_vllm_model_parallel_group) is essentially the same concern the hum |
| pr4893.r2 | copilot_v2 | decisive | The one substantive ground-truth concern (reviewer questioning why the test's device_communicator/reduce_scatter assertions don't cover _TP, which was also converted to init_vllm_model_parallel_group) |
| pr4893.r3 | copilot_v2 | decisive | The sole ground-truth inline concern (reviewer yenuo26 asking whether reduce_scatter/device_communicator assertions should also cover _TP) is exactly what Candidate Y flags as its top finding, with pr |
