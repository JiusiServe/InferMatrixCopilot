# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)

Judge: claude-sonnet-5 (blind, randomized order, 3 replicates x 10 items = 30 verdicts)

## Wins
- copilot_v2: 11
- opus_baseline: 18
- tie: 1

## Mean rubric scores

| arm | actionability | completeness | correctness | gap_hit | grounding | precision | recall |
|---|---|---|---|---|---|---|---|
| copilot_v2 | 0.80 | 0.68 | 0.69 | 0.21 | 0.63 | 0.76 | 0.52 |
| opus_baseline | 0.65 | 0.82 | 0.79 | 0.21 | 0.75 | 0.85 | 0.54 |

## Per-verdict detail

| item.rep | winner | margin | rationale (head) |
|---|---|---|---|
| issue4793.r1 | opus_baseline | clear | Both correctly identify PR #4792 as the fix already folded into the 0.24 rebase and point to the same non-async-chunk full-payload code path, matching the thread's resolution. Y is more precise: it ex |
| issue4793.r2 | opus_baseline | slight | Both candidates correctly identify PR #4792 as the fix and the #4527 regression as root cause (non-async-chunk shipping (None, payload) instead of full payload), matching the ground-truth thread exact |
| issue4793.r3 | opus_baseline | clear | Both candidates correctly converge on the ground-truth resolution: the regression traces to #4527's (None, payload) split starving the non-async-chunk downstream stage, fixed by #4792, and already fol |
| issue4827.r1 | opus_baseline | slight | Both correctly diagnose the crash as `<img_ratio_33..36>` lookups returning None on the base tokenizer, correctly attribute it to the two-stage MoE config forcing AR init, and cite the same working Di |
| issue4827.r2 | opus_baseline | slight | Both correctly diagnose the config/tokenizer mismatch, cite the same crash line, confirm the DiT workaround, and note the request to track hardening in a new issue — matching the thread closely. X gro |
| issue4827.r3 | opus_baseline | clear | Both correctly diagnose the config/tokenizer mismatch (base tokenizer lacks <img_ratio_33..36>, moe.yaml forces the AR stage) and reproduce FayeSpica's confirmed DiT-config workaround. X grounds more  |
| issue4842.r1 | copilot_v2 | slight | Both correctly diagnose the issue as a run-level misconfiguration (default core_model → dummy weights) rather than a real bug, matching the thread's 'invalid' resolution and citing PR #4354/full_model |
| issue4842.r2 | opus_baseline | clear | Both correctly land on the actual resolution (invalid — core_model run-level silently injects dummy weights; fix is --run-level=full_model), matching the thread's close. X cites the same _add_dummy_lo |
| issue4842.r3 | opus_baseline | slight | Both candidates correctly identify the actual thread resolution: the test was run at the default core_model run-level, which forces dummy weights, and the correct fix is --run-level=full_model with th |
| issue4891.r1 | opus_baseline | clear | The thread closed this as a duplicate of #4808 (not a merged fix), but X confidently asserts the bug is 'already fixed on main' with fabricated line-by-line quotes of a specific comment and a claim th |
| issue4891.r2 | opus_baseline | clear | Ground truth closes this as a duplicate of #4808 with details in #4809; Y's answer converges on exactly that outcome and correctly reconstructs the #4809/#4810/#4808 relationship (4 of 5 loaders fixed |
| issue4891.r3 | opus_baseline | clear | The actual resolution was a terse duplicate-closure pointing to #4808/#4809, and X's final recommendation ('keep closed as duplicate') matches that outcome while appropriately hedging on what it could |
| issue4905.r1 | copilot_v2 | slight | Both correctly latch onto the thread's one confirmed fact (yenuo26 blaming PR #4834) and build a plausible, well-cited narrative around the NotImplementedError guard and a level=1 fix, but the actual  |
| issue4905.r2 | opus_baseline | slight | Both candidates give nearly identical, highly confident diagnoses (intended NotImplementedError from #4834, stale test using level=2, one-line fix to level=1, recommend closing) that go well beyond wh |
| issue4905.r3 | copilot_v2 | slight | The actual thread shows only a bisection to #4834 and a request from Flink-ddd for a full sleep-mode CI run — it is not resolved, so confident 'close' dispositions from both candidates outrun what the |
| pr4810.r1 | copilot_v2 | clear | Both flag the diffusion loader (hunyuan_image3_transformer.py) still calling the removed get_cache_scale API, hitting the latent gap, but Y treats it as a grep-verified blocker with concrete file:line |
| pr4810.r2 | opus_baseline | clear | Both are well-grounded, code-verified reviews that independently surface the latent gap (the unswept HunyuanImage3 diffusion loader). But Y also captures several ground-truth-specific nuances X misses |
| pr4810.r3 | copilot_v2 | slight | Both candidates independently found the same latent gap (the unswept HunyuanImage3 diffusion-transformer caller of get_cache_scale), which the ground-truth human reviewers missed — a strong catch for  |
| pr4816.r1 | copilot_v2 | slight | Ground truth is trivial (an 'lgtm' approval, no substantive comments), so recall ties. X is more precise and disciplined: it explicitly cross-checks the rename against the upstream vllm checkout, pinp |
| pr4816.r2 | copilot_v2 | slight | Ground truth has no substantive concerns (just an 'lgtm' approval), so recall is trivially satisfied by both. Both candidates correctly validate the core rename across all hunks with accurate file/lin |
| pr4816.r3 | opus_baseline | slight | Ground truth has no substantive concerns (just an approve), so both reviews' verification-heavy approach is appropriate and both correctly conclude the rename is complete and consistent. X's approve i |
| pr4825.r1 | opus_baseline | slight | Both candidates converge on the same well-grounded core finding (default_components duplicates the pipeline's own _dit_modules metadata, citing matching file:line evidence in pipeline_sdxl.py/registry |
| pr4825.r2 | tie | slight | Neither candidate surfaces the ground truth's actual substantive concern (dsocek's suggestion to derive LoRA naming from `_packed_modules_mapping`/`stacked_params_mapping` for fused-projection renames |
| pr4825.r3 | copilot_v2 | slight | Ground truth's substantive concern (dsocek's note about PEFT naming-conflict workarounds and driving the mapper from _packed_modules_mapping) appears to reference code removed before the final diff (p |
| pr4837.r1 | opus_baseline | decisive | X's core analysis directly reproduces the sole ground-truth concern — that both submit_initial and submit_update reject list prompts identically, so gating the unwrap on already_submitted was unnecess |
| pr4837.r2 | opus_baseline | decisive | The only substantive ground-truth concern (yJader's inline comment explaining that submit_initial and submit_update both reject list prompts, so gating the unwrap on already_submitted was wrong) is re |
| pr4837.r3 | opus_baseline | clear | X directly reproduces the substance of the sole ground-truth inline comment by verifying that both submit_initial and submit_update reject list prompts, correctly explaining why the already_submitted  |
| pr4893.r1 | copilot_v2 | clear | The one substantive ground-truth concern (yenuo26 asking whether reduce_scatter verification in the test is adequate given two issues were fixed together) is only loosely echoed by X, which flags that |
| pr4893.r2 | copilot_v2 | clear | The only substantive ground-truth concern is yenuo26's inline question about whether reduce_scatter also needs test verification alongside device_communicator; X independently flags that the same test |
| pr4893.r3 | copilot_v2 | decisive | The sole substantive ground-truth concern (yenuo26's question about whether reduce_scatter verification should be added given two issues fixed at once) is completely missed by X, which instead validat |
