# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)

Judge: claude-sonnet-5 (blind, randomized order, 3 replicates x 10 items = 30 verdicts)

## Wins
- copilot_v2: 7
- opus_baseline: 23
- tie: 0

## Mean rubric scores

| arm | actionability | completeness | correctness | gap_hit | grounding | precision | recall |
|---|---|---|---|---|---|---|---|
| copilot_v2 | 0.75 | 0.70 | 0.73 | 0.20 | 0.65 | 0.68 | 0.51 |
| opus_baseline | 0.68 | 0.82 | 0.78 | 0.20 | 0.77 | 0.88 | 0.59 |

## Per-verdict detail

| item.rep | winner | margin | rationale (head) |
|---|---|---|---|
| issue4793.r1 | opus_baseline | clear | Both correctly land on the ground-truth resolution (PR #4792 fixing the non-async-chunk None-payload starvation, already folded into the v0.24 rebase) and quote the same code snippet from akshatvishu' |
| issue4793.r2 | opus_baseline | slight | Both correctly identify PR #4792 as the fix for the non-async-chunk (None, payload) starvation bug already folded into the 0.24 rebase (a560ed18), matching the thread's resolution exactly, and both gi |
| issue4793.r3 | opus_baseline | slight | Both correctly identify PR #4792 as the fix for the #4527 regression and note it's already folded into the 0.24 rebase commit, matching the ground truth almost exactly, including reproducing the same  |
| issue4827.r1 | copilot_v2 | slight | Both correctly pinpoint the None+1 crash on the missing <img_ratio_33..36> tokens in hunyuan_image3.py and confirm the same dit.yaml workaround and close-with-follow-up disposition, closely tracking t |
| issue4827.r2 | opus_baseline | slight | Both candidates correctly reproduce the thread's diagnosis (base tokenizer lacks extended ratio tokens, moe.yaml wrongly forces the AR stage post-#2713, DiT config workaround confirmed by FayeSpica) a |
| issue4827.r3 | copilot_v2 | slight | Both correctly diagnose the base-vs-Instruct tokenizer/config mismatch, cite the same crash site, and land on the same workaround and disposition (close, track hardening separately per Gaohan123). Y m |
| issue4842.r1 | opus_baseline | slight | Both correctly diagnose the run-level/dummy-weight issue and land on the same 'invalid' disposition as the thread, matching akshatvishu's and yenuo26's findings. X is better grounded: it cites more sp |
| issue4842.r2 | opus_baseline | slight | Both correctly diagnose the issue as a run-level misconfiguration (default core_model loads dummy weights) rather than a real bug, and both give the same correct fix (--run-level=full_model) and dispo |
| issue4842.r3 | opus_baseline | slight | Both correctly diagnose the run-level/dummy-weight issue and reach the same 'closed as invalid' disposition matching the thread, with the same fix (--run-level=full_model). Y is more thoroughly ground |
| issue4891.r1 | opus_baseline | clear | Both land on the correct disposition (duplicate of #4808), matching the thread's actual resolution. But X confidently asserts the fix is 'already on main,' fabricates a specific code snippet and a nam |
| issue4891.r2 | opus_baseline | clear | Both reach the correct disposition (duplicate of #4808/#4809) and correctly diagnose the missing-migration root cause, but X asserts with unwarranted confidence that the fix is 'fixed on main' and fab |
| issue4891.r3 | opus_baseline | clear | Both reach the ground-truth disposition (duplicate of #4808, per #4809), but Y asserts as settled fact that the fix is 'on main' and even reproduces fabricated-looking code/comment snippets and exact  |
| issue4905.r1 | opus_baseline | slight | Both candidates correctly bisect the failure to PR #4834's intentional level-2 wake guard, matching yenuo26's comment, but both overclaim a settled resolution ('already fixed on main', 'close as resol |
| issue4905.r2 | opus_baseline | slight | Both correctly trace the failure to PR #4834's level-2 wake guard (matching yenuo26's bisection), but both overreach by confidently declaring the issue resolved/closeable, when the actual thread shows |
| issue4905.r3 | opus_baseline | slight | Both candidates converge on the same diagnosis (PR #4834's level-2 wake guard is intentional, test used the wrong sleep level) and both overreach by confidently declaring the issue already fixed on ma |
| pr4810.r1 | opus_baseline | clear | Both candidates independently surface the same latent gap (unswept get_cache_scale caller in hunyuan_image3_transformer.py:2238), so gap_hit is true for both, and both correctly validate the core mapp |
| pr4810.r2 | opus_baseline | clear | Both candidates independently surface the latent gap (the unswept hunyuan_image3_transformer.py caller of get_cache_scale), so gap_hit is true for both. But X's precision is hurt by two/three near-dup |
| pr4810.r3 | opus_baseline | slight | Both correctly validate the 4 loader changes and both independently surface the exact latent gap (the unswept hunyuan_image3_transformer.py caller of get_cache_scale), so gap_hit=true for both. X pads |
| pr4816.r1 | copilot_v2 | slight | Ground truth for this trivial rename PR is essentially empty (bot noise + a plain 'lgtm' approve), so both candidates trivially achieve full recall with nothing to miss. X thoroughly re-verifies the m |
| pr4816.r2 | opus_baseline | clear | Ground truth is a trivial, correct rename with a plain 'lgtm' approval and no requested changes. X verifies the rename exhaustively (grep for stragglers, cross-check against upstream vllm) and correct |
| pr4816.r3 | opus_baseline | slight | Ground truth has no substantive concerns (approve/lgtm), so both correctly find no real defects and neither fabricates anything grounded outside the diff. X's verification (upstream grep, no leftover  |
| pr4825.r1 | copilot_v2 | slight | Neither candidate recovers the ground truth's actual substantive suggestion (dsocek's packed_modules_mapping-driven naming-conflict idea, likely tied to a hunk removed before merge per tthakkal's repl |
| pr4825.r2 | opus_baseline | slight | Both candidates independently converge on the same core structural nit (derive component list from _dit_modules instead of a hardcoded tuple), which echoes the spirit of dsocek's ground-truth question |
| pr4825.r3 | copilot_v2 | slight | Neither candidate surfaces the ground truth's core concern (dsocek's point about deriving the PEFT-to-vllm-omni naming mapper from `_packed_modules_mapping` to cover fused-projection renames like to_q |
| pr4837.r1 | opus_baseline | decisive | X's core analysis of orchestrator.py:1290 mirrors yJader's actual reasoning almost exactly (both submit paths reject lists, so gating the unwrap on already_submitted was the bug) and correctly reaches |
| pr4837.r2 | opus_baseline | clear | Y independently verifies the exact reasoning behind the ground-truth inline comment (both submit_initial and submit_update reject list prompts, stage_pool.py:951/1022), matching its conclusion and the |
| pr4837.r3 | opus_baseline | clear | Both candidates independently reach the same core insight as the ground-truth comment (submit_initial and submit_update both reject list prompts for diffusion, so dropping already_submitted is safe/co |
| pr4893.r1 | opus_baseline | slight | Neither candidate surfaces the one substantive ground-truth concern (yenuo26's question about whether reduce_scatter behavior, not just hasattr, needs test verification), so recall is 0 for both. X pa |
| pr4893.r2 | copilot_v2 | slight | Neither candidate hits the one substantive ground-truth concern (yenuo26's question about whether hasattr(reduce_scatter) checks are sufficient verification), so recall is low for both. X supplies mor |
| pr4893.r3 | copilot_v2 | slight | Ground truth is thin (one inline comment about verifying reduce_scatter, already satisfied by the diff, plus non-technical PR chatter), so neither candidate scores well on recall and both are largely  |
