# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)

Judge: claude-sonnet-5 (blind, randomized order, 3 replicates x 10 items = 30 verdicts)

## Wins
- copilot_v2: 9
- opus_baseline: 20
- tie: 1

## Mean rubric scores

| arm | actionability | completeness | correctness | gap_hit | grounding | precision | recall |
|---|---|---|---|---|---|---|---|
| copilot_v2 | 0.73 | 0.70 | 0.71 | 0.20 | 0.67 | 0.63 | 0.49 |
| opus_baseline | 0.72 | 0.81 | 0.79 | 0.20 | 0.77 | 0.87 | 0.57 |

## Per-verdict detail

| item.rep | winner | margin | rationale (head) |
|---|---|---|---|
| issue4793.r1 | copilot_v2 | slight | Both correctly identify the exact ground-truth resolution (regression from #4527, fixed by PR #4792, already folded into the v0.24 rebase commit) and both reproduce the akshatvishu code snippet verbat |
| issue4793.r2 | opus_baseline | slight | Both correctly identify PR #4792 as the fix and correctly note it's already folded into the vLLM 0.24 rebase commit, matching the ground truth exactly. X provides more extensive file:line grounding (s |
| issue4793.r3 | opus_baseline | slight | Both correctly identify PR #4792/#4527 as the fix, matching the thread's ground truth almost verbatim in code citations. X is slightly more conservative and grounded — it flags potential red herrings  |
| issue4827.r1 | copilot_v2 | slight | Both correctly diagnose the None+1 TypeError from missing extended ratio tokens and confirm the hunyuan_image3_dit.yaml workaround, matching the thread. X more faithfully captures the thread's actual  |
| issue4827.r2 | copilot_v2 | slight | Both candidates correctly diagnose the None+1 TypeError as a base-vs-Instruct tokenizer mismatch triggered by the two-stage MoE config, cite the same hunyuan_image3.py lines, confirm the DiT-config wo |
| issue4827.r3 | copilot_v2 | slight | Both correctly diagnose the None+1 crash on extended ratio tokens and confirm the same dit.yaml workaround credited to FayeSpica, matching the thread. Y more precisely mirrors the thread's actual caus |
| issue4842.r1 | opus_baseline | slight | Both correctly diagnose the run-level/dummy-weight issue and land on the thread's 'invalid' resolution, with similar code-path reasoning. X grounds more tightly to the actual thread by explicitly citi |
| issue4842.r2 | opus_baseline | slight | Both correctly diagnose the issue as a run-level misconfiguration (core_model dummy weights) rather than a bug, matching the thread's 'invalid' resolution and both prescribe --run-level=full_model. Y  |
| issue4842.r3 | opus_baseline | clear | Both correctly diagnose the failure as a run-level misconfiguration (core_model dummy weights) matching the thread's 'invalid' resolution and --run-level=full_model fix. Y is more accurate and thoroug |
| issue4891.r1 | opus_baseline | clear | Both correctly land on the ground-truth disposition ('duplicate of #4808'), but X fabricates unverifiable specifics (a '9 tests pass on main' claim, a grep 'should return nothing', a full regression-t |
| issue4891.r2 | opus_baseline | clear | Both correctly land on 'duplicate of #4808/#4809,' matching the ground truth, but X asserts with unqualified confidence that the fix is 'already on main' and cites suspiciously specific artifacts (a c |
| issue4891.r3 | opus_baseline | clear | Both correctly identify the duplicate-of-#4808 disposition, but X hedges appropriately on the one point it couldn't verify (whether #4808 actually merged to main) and flags a specific, internally-cons |
| issue4905.r1 | opus_baseline | slight | Both correctly bisect the failure to PR #4834's intentional level-2 wake guard (matching yenuo26's thread comment) and propose the same level=1 test fix, but both overreach by confidently declaring th |
| issue4905.r2 | copilot_v2 | slight | Both candidates converge on the same core diagnosis (test hits the intentional NotImplementedError guard added by #4834 when sleep(level=2) is followed by wake_up(), which matches the traceback in the |
| issue4905.r3 | opus_baseline | slight | Both candidates converge on the same diagnosis (PR #4834 intentionally hard-stops wake_up() after level=2 sleep, test needs level=1) and both overreach by confidently declaring the issue already fixed |
| pr4810.r1 | copilot_v2 | slight | Both candidates independently sweep the repo and correctly identify the exact missed caller (hunyuan_image3_transformer.py's stale get_cache_scale call) that later became issue #4891, so gap_hit is tr |
| pr4810.r2 | opus_baseline | clear | Both candidates independently surface the latent gap (the hunyuan_image3 diffusion transformer still calling the removed get_cache_scale), so gap_hit is true for both, but Y grounds it more rigorously |
| pr4810.r3 | opus_baseline | clear | Both independently catch the real latent gap (hunyuan_image3_transformer.py:2238 still calling the removed get_cache_scale API), so gap_hit is true for both. X's catch is framed as a stronger 'blocker |
| pr4816.r1 | opus_baseline | slight | Ground truth has zero substantive findings (just an 'lgtm' approve), so both candidates score full recall since nothing was missed. X delivers a clean, fully-grounded approve that verifies the rename  |
| pr4816.r2 | opus_baseline | slight | Ground truth shows a trivial, cleanly-approved rename PR with zero substantive concerns, so recall is trivially satisfied by both. X's verification-heavy APPROVE (grep for leftovers, upstream cross-ch |
| pr4816.r3 | opus_baseline | slight | Ground truth is a clean 'lgtm' approve with zero substantive concerns, and X reaches the same conclusion with grounded verification (upstream match, no leftover references, existing tests updated) wit |
| pr4825.r1 | copilot_v2 | slight | Both candidates converge on the same substantive theme echoed by dsocek's ground-truth comment (stop hardcoding component names, derive from an existing single source of truth), but Y backs this with  |
| pr4825.r2 | copilot_v2 | slight | Neither candidate surfaces the actual ground-truth concern (dsocek's PEFT-naming/packed_modules_mapping point, tied to a since-removed WA not visible in the truncated diff), so recall is low for both. |
| pr4825.r3 | tie | slight | Both candidates correctly validate the unet addition as safe and independently rediscover the same underlying theme as dsocek's ground-truth comment (hardcoded component lists should derive from a sin |
| pr4837.r1 | opus_baseline | decisive | The single ground-truth concern (yJader's inline comment) is actually a defense of the fix: both submit_initial and submit_update reject list prompts, so dropping the already_submitted gate is correct |
| pr4837.r2 | opus_baseline | clear | Y directly verifies the exact rationale the ground-truth inline comment gives (both submit_initial and submit_update reject list prompts for diffusion, so already_submitted was never load-bearing) and |
| pr4837.r3 | opus_baseline | clear | Both candidates independently rediscover the ground-truth insight (yJader's inline comment) that both submit_initial and submit_update reject list prompts, so removing the already_submitted gate is co |
| pr4893.r1 | opus_baseline | decisive | Candidate X produced no review at all (crashed with an API error before generating output), so it contributes nothing on any axis. Candidate Y delivered a grounded, technically verified review (checke |
| pr4893.r2 | opus_baseline | slight | Neither candidate surfaces the one substantive ground-truth concern (verifying reduce_scatter in the test alongside device_communicator). X pads its review with five 'minor' findings that are largely  |
| pr4893.r3 | copilot_v2 | clear | Neither candidate surfaces the one substantive ground-truth concern (reduce_scatter verification gap in test_expert_parallel_layout.py), so recall is low for both, but Y at least raises an analogous t |
