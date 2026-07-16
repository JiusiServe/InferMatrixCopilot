# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)

Judge: claude-sonnet-5 (blind, randomized order, 3 replicates x 10 items = 30 verdicts)

## Wins
- copilot_v2: 9
- opus_baseline: 21
- tie: 0

## Mean rubric scores

| arm | actionability | completeness | correctness | gap_hit | grounding | precision | recall |
|---|---|---|---|---|---|---|---|
| copilot_v2 | 0.81 | 0.64 | 0.66 | 0.20 | 0.62 | 0.72 | 0.60 |
| opus_baseline | 0.70 | 0.81 | 0.79 | 0.20 | 0.77 | 0.87 | 0.60 |

## Per-verdict detail

| item.rep | winner | margin | rationale (head) |
|---|---|---|---|
| issue4793.r1 | opus_baseline | clear | Both correctly identify PR #4792 (the non-async-chunk (None, payload) starvation from #4527) as the fix already folded into the 0.24 rebase commit a560ed18, matching the ground truth's core resolution |
| issue4793.r2 | opus_baseline | slight | Both correctly identify the #4527 regression (non-async-chunk branch shipping (None, payload) starving the downstream stage) and the #4792 fix, matching the ground-truth thread's code snippet and file |
| issue4793.r3 | opus_baseline | clear | Both correctly diagnose the (None, payload) vs (payload, payload) starvation bug fixed by PR #4792 and correctly note it's already folded into the 0.24 rebase commit a560ed18, matching the ground-trut |
| issue4827.r1 | opus_baseline | slight | Both correctly diagnose the None+1 crash from missing extended ratio tokens and the moe.yaml vs dit.yaml topology mismatch, matching the thread's resolution and workaround. Y goes further with a concr |
| issue4827.r2 | opus_baseline | slight | Both correctly diagnose the None+1 crash from missing extended ratio tokens in the base tokenizer, cite the same file/lines, provide the identical FayeSpica-confirmed DiT workaround, and propose the s |
| issue4827.r3 | opus_baseline | clear | Both correctly diagnose the config/tokenizer mismatch and cite the same crash site (hunyuan_image3.py:1561-1563), matching the thread's root cause and workaround. X goes further with grounded detail ( |
| issue4842.r1 | opus_baseline | slight | Both correctly identify the ground truth's actual resolution (run-level misconfiguration causing dummy weights, closed invalid) and cite the same core evidence (stage_config.py's dummy load_format pat |
| issue4842.r2 | opus_baseline | slight | Both correctly diagnose the issue as invalid/run-level misconfiguration (dummy weights at core_model, extended to online serving by #4354) matching the thread's actual resolution, and both give the co |
| issue4842.r3 | opus_baseline | slight | Both correctly diagnose the issue as a run-level misconfiguration (core_model → dummy weights) rather than a real bug, matching the thread's 'invalid' resolution and citing the same _add_dummy_load_fo |
| issue4891.r1 | opus_baseline | clear | Ground truth closes #4891 as a duplicate of #4808 (not #4810), pointing to #4809 for the full call-site inventory. Y matches this exactly — it explains #4810 covered 4/5 AR-side sites while #4808 is t |
| issue4891.r2 | opus_baseline | decisive | Ground truth closed #4891 as a duplicate of #4808, not as already-fixed-by-#4810. X confidently asserts the bug is 'already fixed on main' via #4810 and fabricates verified line-numbered code/comments |
| issue4891.r3 | opus_baseline | clear | Both reach the correct top-level verdict (close as duplicate of #4808, tracked in #4809), but X is honest about what it could verify — it explicitly flags that #4808 shows closed/unmerged and asks for |
| issue4905.r1 | copilot_v2 | slight | Both correctly identify PR #4834 as the culprit (matching yenuo26's bisection) and propose the same plausible fix (use level=1 instead of level=2 in the test), which is reasonable but unconfirmed spec |
| issue4905.r2 | copilot_v2 | slight | Both reach the same core diagnosis (bisected to #4834's intentional level-2-sleep guard, propose switching the test to level=1) and both overreach by asserting a 'close' disposition the thread never c |
| issue4905.r3 | copilot_v2 | slight | Both correctly bisect the failure to PR #4834's new wake_up() guard and propose the same level=1 test fix, matching yenuo26's thread comment that #4834 introduced the error — reasonable diagnoses give |
| pr4810.r1 | opus_baseline | slight | Both correctly validate the direct-vs-delegated loader migration and both hit the latent gap by naming the unswept hunyuan_image3_transformer.py diffusion loader still calling the removed get_cache_sc |
| pr4810.r2 | copilot_v2 | slight | Both candidates independently catch the latent gap (the unmigrated get_cache_scale caller in hunyuan_image3_transformer.py), but X treats it as a blocker with precise file/line evidence and a concrete |
| pr4810.r3 | opus_baseline | clear | Both catch the real latent gap (unswept get_cache_scale caller in the diffusion transformer), satisfying gap_hit for each. X pads its findings with two speculative 'dead code' nitpicks and a trivial m |
| pr4816.r1 | opus_baseline | slight | Ground truth is trivial (bot rate-limit notice + a bare 'lgtm' approval), so recall is moot for both; the real differentiator is precision and groundedness. X correctly identifies the core rationale ( |
| pr4816.r2 | copilot_v2 | slight | Ground truth has zero substantive concerns (bot notice + plain 'lgtm'), so both candidates trivially achieve full recall and both correctly conclude the PR is sound. X gives a clean, accurate, well-ve |
| pr4816.r3 | opus_baseline | slight | Ground truth shows no substantive concerns (bot rate-limited, human said 'lgtm'), so both candidates correctly find nothing blocking and both verify every hunk against upstream/tests with accurate, gr |
| pr4825.r1 | copilot_v2 | slight | Both candidates identify the one substantive ground-truth concern (dsocek's point that the hardcoded default_components list is fragile and should be derived from existing per-pipeline structure), and |
| pr4825.r2 | opus_baseline | slight | Both candidates converge on the same latent theme the ground truth reviewer raised (manager.py hardcodes a component list that duplicates existing per-pipeline metadata like _dit_modules), though neit |
| pr4825.r3 | opus_baseline | slight | Both reviews independently converge on a legitimate, well-grounded finding (default_components duplicates the pipeline's own _dit_modules declaration, citing matching pipeline_sdxl.py/registry.py loca |
| pr4837.r1 | opus_baseline | clear | The sole substantive ground-truth concern (yJader's inline comment) explains that already_submitted is irrelevant because both submit_initial and submit_update reject list prompts identically — X repr |
| pr4837.r2 | opus_baseline | clear | Y's review closely reconstructs the ground-truth reviewer's actual reasoning (already_submitted is safe to drop because both submit_initial/submit_update reject list prompts identically), backing it w |
| pr4837.r3 | opus_baseline | decisive | X's core finding — that both submit_initial and submit_update reject list prompts for diffusion, so unwrapping shouldn't be gated on already_submitted — almost exactly reproduces the ground-truth inli |
| pr4893.r1 | copilot_v2 | decisive | The one substantive ground-truth concern (yenuo26's inline comment questioning whether reduce_scatter/device_communicator verification is missing for a group in the test) maps almost exactly onto Cand |
| pr4893.r2 | copilot_v2 | clear | The one substantive ground-truth concern (yenuo26's inline comment questioning whether the new device_communicator/reduce_scatter test assertions are complete) is directly echoed by Candidate X's find |
| pr4893.r3 | copilot_v2 | clear | The only substantive ground-truth concern (yenuo26's inline comment questioning whether reduce_scatter verification is complete in the new test assertions) is missed entirely by X, which mostly issues |
