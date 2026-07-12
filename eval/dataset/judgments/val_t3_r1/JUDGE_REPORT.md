# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)

Judge: claude-sonnet-5 (blind, randomized order, 3 replicates x 10 items = 30 verdicts)

## Wins
- copilot_v2: 3
- opus_baseline: 27
- tie: 0

## Mean rubric scores

| arm | actionability | completeness | correctness | gap_hit | grounding | precision | recall |
|---|---|---|---|---|---|---|---|
| copilot_v2 | 0.62 | 0.45 | 0.54 | 0.20 | 0.51 | 0.52 | 0.46 |
| opus_baseline | 0.75 | 0.82 | 0.80 | 0.20 | 0.80 | 0.90 | 0.61 |

## Per-verdict detail

| item.rep | winner | margin | rationale (head) |
|---|---|---|---|
| issue4793.r1 | opus_baseline | clear | Both candidates correctly identify PR #4792 as the fix for the #4527 regression and cite the same file/line/code snippet, matching the ground truth's diagnosis. X's answer is technically correct but i |
| issue4793.r2 | opus_baseline | clear | Both correctly identify the #4527 regression, the #4792 fix, and that it's already folded into the 0.24 rebase commit a560ed18 matching the thread. X is delivered as a clean, well-organized maintainer |
| issue4793.r3 | opus_baseline | clear | Both reach the same correct diagnosis matching the ground truth (regression from #4527, fix in #4792, already folded into the 0.24 rebase commit a560ed18) and cite the same real files/lines/snippet ve |
| issue4827.r1 | opus_baseline | clear | Both correctly diagnose the Base-vs-Instruct tokenizer/config mismatch and reach the same workaround, matching the thread. Y is more grounded, citing specific surrounding code (start/end ratio ids) an |
| issue4827.r2 | opus_baseline | clear | Both correctly diagnose the base/Instruct config mismatch and the None+1 TypeError, and both propose the same guard fix plus docs clarification, matching the thread's resolution. X is better grounded  |
| issue4827.r3 | opus_baseline | clear | Both reach the same correct core diagnosis (base checkpoint + Instruct-only MoE config → missing extended ratio tokens → TypeError) and the same workaround/fix direction, matching the thread's resolut |
| issue4842.r1 | opus_baseline | decisive | X correctly diagnoses the issue as a run-level mismatch (core_model defaulting to dummy weights despite the full_model marker), matching the actual thread resolution (akshatvishu/yenuo26, closed inval |
| issue4842.r2 | opus_baseline | decisive | Candidate X produced no answer at all (agent hit max iterations and escalated), so it scores zero on all axes. Candidate Y correctly diagnoses the root cause exactly as the thread resolved it: the tes |
| issue4842.r3 | opus_baseline | decisive | X produced no actual answer at all — it hit max iterations and escalated with zero diagnosis, so it cannot match the thread resolution on any axis. Y correctly concludes 'invalid' due to running at th |
| issue4891.r1 | opus_baseline | decisive | Both correctly land on 'duplicate of #4808' matching the ground-truth comment, but X confidently asserts 'Both PRs have been merged' and 'main contains zero calls to the removed API' based solely on t |
| issue4891.r2 | opus_baseline | clear | Ground truth is narrowly 'duplicate of #4808, see #4809 comment for details' — Y matches this precisely, correctly separating #4810 (AR-side, 4/5 sites) from #4808 (the specific DiT site this issue re |
| issue4891.r3 | opus_baseline | clear | Both reach the right disposition (duplicate/close, mirroring #4810's fix pattern), but X actually checks PR #4808's merge state and finds mergedAt is null — flagging a real risk that Y's confident 'Bo |
| issue4905.r1 | copilot_v2 | clear | Both correctly identify PR #4834 as the trigger for the guard (matching yenuo26's comment) and propose the same level=2→level=1 test fix, but the actual thread shows the issue was NOT resolved simply  |
| issue4905.r2 | copilot_v2 | slight | Both candidates converge on the same technically plausible diagnosis (PR #4834's wake_up guard vs. a stale level=2 test), matching yenuo26's bisection to #4834, and cite the same code/line evidence. X |
| issue4905.r3 | copilot_v2 | slight | Both correctly trace the failure to PR #4834's new wake_up() guard, matching yenuo26's causal claim in the thread, and both quote the guard code plausibly. But the actual thread shows the issue still  |
| pr4810.r1 | opus_baseline | clear | Both candidates independently catch the latent diffusion-transformer gap (hunyuan_image3_transformer.py:2238), so gap_hit is true for both. X additionally reproduces the ground truth's own critique al |
| pr4810.r2 | opus_baseline | clear | Both catch the latent gap (diffusion-side hunyuan_image3_transformer.py still calling the removed get_cache_scale API), but X undermines itself with a fabricated 'major' claim that HunyuanModel.load_w |
| pr4810.r3 | opus_baseline | clear | Both independently catch the latent gap (stale get_cache_scale call in the diffusion-side hunyuan_image3_transformer.py), so gap_hit is true for both, but Y frames it accurately as a non-blocking scop |
| pr4816.r1 | opus_baseline | clear | Ground truth has no substantive concerns (bot rate-limit message + a bare 'lgtm' approval), so both trivially achieve full recall. X thoroughly verifies the rename against upstream and confirms zero m |
| pr4816.r2 | opus_baseline | clear | Ground truth shows no real concerns (Codex quota-exhausted, human reviewer just said 'lgtm'/APPROVED), so the correct call is a clean approve. Candidate X verifies the rename exhaustively against both |
| pr4816.r3 | opus_baseline | clear | Ground truth is a trivial 'lgtm' approve with zero substantive concerns, which matches Candidate X's clean, well-verified APPROVE (grep + upstream cross-check, no fabricated issues). Candidate Y inste |
| pr4825.r1 | opus_baseline | clear | Both candidates independently converge on the ground-truth's core theme (dsocek's suggestion to derive default_components from existing declarative metadata rather than hardcoding), but X also credits |
| pr4825.r2 | opus_baseline | clear | Neither candidate surfaces the one substantive ground-truth concern (dsocek's note about driving naming-conflict handling from _packed_modules_mapping), which likely referenced a hunk removed before t |
| pr4825.r3 | opus_baseline | clear | Both candidates independently arrive at a variant of the ground-truth's core theme (dsocek's 'derive from existing metadata instead of hardcoding'), though neither cites the actual _packed_modules_map |
| pr4837.r1 | opus_baseline | decisive | X directly reconstructs the ground-truth reviewer's actual reasoning (both submit_initial and submit_update reject list prompts regardless of already_submitted, so the fix is correct and consistent),  |
| pr4837.r2 | opus_baseline | decisive | The one substantive ground-truth concern (yJader's point that already_submitted is irrelevant since both submit paths reject list prompts regardless) is directly and correctly reproduced by Y, which v |
| pr4837.r3 | opus_baseline | decisive | X's core claim — both submit_initial and submit_update reject list prompts regardless of already_submitted — directly matches the ground-truth reviewer's rationale for why the gate removal is correct, |
| pr4893.r1 | opus_baseline | slight | X's two findings (untested guard branches in _set_forward_context_dp_metadata, and the fake-group mock masking real GroupCoordinator behavior near the reduce_scatter assertions) are valid and grounded |
| pr4893.r2 | opus_baseline | slight | Ground truth's only substantive concern is yenuo26's inline question about verifying reduce_scatter in the test; X's second finding (mocked device_communicator/reduce_scatter validates fakes, not real |
| pr4893.r3 | opus_baseline | clear | Ground truth's only substantive concern (yenuo26's inline note on verifying reduce_scatter in the test) is largely already satisfied in the diff shown, so neither candidate scores much recall; Y's nit |
