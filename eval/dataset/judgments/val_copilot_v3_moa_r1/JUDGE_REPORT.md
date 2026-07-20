# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)

Judge: claude-sonnet-5 (blind, randomized order, 3 replicates x 10 items = 30 verdicts)

## Wins
- copilot_v2: 10
- opus_baseline: 20
- tie: 0

## Mean rubric scores

| arm | actionability | completeness | correctness | gap_hit | grounding | precision | recall |
|---|---|---|---|---|---|---|---|
| copilot_v2 | 0.67 | 0.70 | 0.73 | 0.20 | 0.64 | 0.76 | 0.60 |
| opus_baseline | 0.65 | 0.81 | 0.76 | 0.20 | 0.74 | 0.83 | 0.60 |

## Per-verdict detail

| item.rep | winner | margin | rationale (head) |
|---|---|---|---|
| issue4793.r1 | opus_baseline | clear | Both correctly identify the #4527 regression (None instead of per_req_payloads in the non-async-chunk branch) and #4792 as the fix, matching the ground truth thread. Y is far more grounded, tracing th |
| issue4793.r2 | opus_baseline | slight | Both correctly identify the same root cause (PR #4527 broke the non-async-chunk payload split to None, starving accumulate_full_payload_output) and the same resolution (already fixed by merged PR #479 |
| issue4793.r3 | opus_baseline | clear | Both candidates land the same core diagnosis and disposition as the thread (regression from #4527's `(None, per_req_payloads)` split fixed by #4792, already in the 0.24/a560ed18 rebase, workaround via |
| issue4827.r1 | opus_baseline | slight | Both correctly diagnose the config mismatch (base tokenizer missing <img_ratio_36>) and land on the same workaround/fix already confirmed in the thread, matching the ground truth well. Y goes further  |
| issue4827.r2 | opus_baseline | slight | Both correctly diagnose the None+1 crash from the base tokenizer lacking <img_ratio_33..36>, cite the same hunyuan_image3.py:1561-1563 snippet, give the same dit.yaml workaround, and correctly land on |
| issue4827.r3 | opus_baseline | slight | Both correctly diagnose the base-tokenizer/config mismatch and recommend the same dit.yaml workaround the thread confirmed (FayeSpica), and both propose the same guard+docs follow-up matching Gaohan12 |
| issue4842.r1 | opus_baseline | slight | Both correctly land on the ground-truth resolution (wrong --run-level, dummy weights, close as invalid) with matching file/line citations for stage_config.py and run_args.py. X grounds more tightly to |
| issue4842.r2 | opus_baseline | clear | Both candidates correctly reach the thread's actual resolution (default --run-level=core_model forces dummy weights via #4354, fix is --run-level=full_model, closed invalid), so correctness is close.  |
| issue4842.r3 | copilot_v2 | slight | Both correctly reproduce the thread's actual resolution: default --run-level=core_model forces dummy weights via stage_config.py's load-format patching, the fix is --run-level=full_model, and the issu |
| issue4891.r1 | opus_baseline | clear | Both correctly identify the duplicate-of-#4808 disposition, but X asserts unverified specifics as fact (PR 'merged', fabricated grep/comment output, fabricated 'Verified end-to-end' claim in the repro |
| issue4891.r2 | opus_baseline | clear | Both correctly land on 'duplicate of #4808,' matching the thread resolution, but Y also cites #4809 as the tracking issue exactly as the ground-truth comment does, while X never mentions #4809 at all. |
| issue4891.r3 | opus_baseline | slight | Both correctly land on the ground-truth disposition (duplicate of #4808, pointer to #4809) and give the same technical root-cause narrative. X is better grounded: it cites the specific gh API field (' |
| issue4905.r1 | copilot_v2 | slight | Both correctly identify PR #4834's NotImplementedError guard as the root cause, matching yenuo26's comment that the error appeared after that PR merged. But both then confidently assert the issue is ' |
| issue4905.r2 | copilot_v2 | slight | The actual thread shows the issue is still unresolved: yenuo26 links it to #4834 but Flink-ddd is still asking to trigger a full CI run to investigate, with no confirmation that a fix already landed.  |
| issue4905.r3 | copilot_v2 | slight | Both correctly trace the guard to #4834 (matching yenuo26's comment) but then confidently assert the test was 'already fixed on main' with specific line numbers, diffs, and test names (e.g. test_level |
| pr4810.r1 | copilot_v2 | slight | Both candidates independently verify the delegated-vs-direct loader distinction, confirm qwen2_old's guard removal is safe, and—crucially—both surface the unswept hunyuan_image3_transformer.py caller  |
| pr4810.r2 | opus_baseline | clear | Both candidates independently surface the real latent gap (hunyuan_image3_transformer.py still calling the removed get_cache_scale), which neither ground-truth reviewer caught. X frames it as an unres |
| pr4810.r3 | opus_baseline | slight | Both independently verified the delegated-vs-direct loader distinction (matching lishunyang12's core review) and both surfaced the exact latent gap — the still-broken get_cache_scale call in hunyuan_i |
| pr4816.r1 | copilot_v2 | slight | Ground truth has no substantive concerns (just an 'lgtm' approve), so both candidates trivially achieve full recall and neither fabricates findings — both did real verification (greps, upstream compar |
| pr4816.r2 | copilot_v2 | slight | Ground truth has no substantive concerns (bot rate-limit notice + bare 'lgtm'), so both candidates trivially achieve full recall on a genuinely trivial rename PR. Both did solid diligence (grep verifi |
| pr4816.r3 | opus_baseline | slight | Ground truth has no substantive concerns (just an 'lgtm' approval), so both candidates correctly find no blockers and their verification claims (grep for stale references, cross-check against upstream |
| pr4825.r1 | opus_baseline | clear | The one substantive ground-truth concern (dsocek's point that hardcoded/scattered naming lists should instead be derived from a single per-model source of truth) is echoed almost exactly by X's commen |
| pr4825.r2 | opus_baseline | decisive | X independently surfaces the same core concern dsocek raised in the ground truth (the hardcoded per-manager component list should instead be derived from existing per-pipeline metadata, here _dit_modu |
| pr4825.r3 | opus_baseline | clear | X's comment about deriving denoiser/component discovery from existing per-pipeline data (_dit_modules) instead of a fourth hardcoded list echoes the spirit of dsocek's actual ground-truth concern abou |
| pr4837.r1 | opus_baseline | clear | Both candidates correctly explain the core fix (unconditional singleton-list unwrap is safe because both submit_initial/submit_update reject list prompts identically), matching yJader's inline reasoni |
| pr4837.r2 | opus_baseline | clear | Y's verification that both submit_initial and submit_update reject list prompts (making already_submitted an irrelevant distinction) closely mirrors yJader's actual inline comment, the one substantive |
| pr4837.r3 | opus_baseline | clear | X's key claim — that both submit_initial and submit_update reject list prompts identically, so the already_submitted gate was superfluous — mirrors the ground-truth inline comment's exact reasoning al |
| pr4893.r1 | copilot_v2 | decisive | The only substantive ground-truth concern (yenuo26's inline comment on test_expert_parallel_layout.py:121 noting that TP, built via the same init_vllm_model_parallel_group path, lacks the same device_ |
| pr4893.r2 | copilot_v2 | clear | The sole substantive ground-truth concern (yenuo26's ask about verifying device_communicator/reduce_scatter coverage in the new test) is directly echoed by X's finding that TP lacks the same hasattr a |
| pr4893.r3 | copilot_v2 | clear | The one substantive ground-truth concern (yenuo26's inline comment) points out that the test verifies device_communicator/reduce_scatter for PCP/DP/EP but not TP, even though TP now goes through the s |
