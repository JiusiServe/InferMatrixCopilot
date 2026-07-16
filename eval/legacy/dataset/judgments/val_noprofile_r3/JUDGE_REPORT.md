# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)

Judge: claude-sonnet-5 (blind, randomized order, 3 replicates x 10 items = 29 verdicts)

## Wins
- copilot_v2: 7
- opus_baseline: 21
- tie: 1

## Mean rubric scores

| arm | actionability | completeness | correctness | gap_hit | grounding | precision | recall |
|---|---|---|---|---|---|---|---|
| copilot_v2 | 0.82 | 0.53 | 0.57 | 0.20 | 0.54 | 0.74 | 0.58 |
| opus_baseline | 0.75 | 0.82 | 0.79 | 0.21 | 0.77 | 0.85 | 0.62 |

## Per-verdict detail

| item.rep | winner | margin | rationale (head) |
|---|---|---|---|
| issue4793.r1 | opus_baseline | clear | Both correctly land on the ground-truth resolution (PR #4792 fixed the None inter_stage_outputs regression from #4527, already folded into the 0.24 rebase commit a560ed1), matching the exact code snip |
| issue4793.r2 | opus_baseline | slight | Both candidates correctly identify the #4527 regression fixed by PR #4792 and already present in the 0.24 rebase commit a560ed18, matching the ground-truth thread. X reads as a clean, reporter-facing  |
| issue4793.r3 | opus_baseline | clear | Both correctly diagnose the #4527 regression fixed by #4792 and already folded into the 0.24 rebase (a560ed18), matching the thread's ground truth. X is delivered as a clean, self-contained maintainer |
| issue4827.r1 | opus_baseline | slight | Both correctly diagnose the base-tokenizer/None+int crash, cite the same hunyuan_image3.py:1561-1563 lines, and give the identical FayeSpica-confirmed DiT workaround plus a guard/docs fix matching aks |
| issue4827.r2 | opus_baseline | clear | Both correctly diagnose the base-tokenizer/config mismatch with the same code citation, and both surface the workaround and the guard/docs follow-up. X goes further in grounding (quotes YAML header li |
| issue4827.r3 | opus_baseline | slight | Both correctly diagnose the config/model mismatch, cite the same crashing lines in hunyuan_image3.py, confirm the DiT-config workaround, and propose the guard+docs fix while deferring to a tracking is |
| issue4842.r1 | copilot_v2 | slight | Both correctly land on the thread's actual resolution (invalid — default --run-level=core_model injects dummy weights via PR #4354, fix is --run-level=full_model), matching the maintainer/closer conse |
| issue4842.r2 | opus_baseline | slight | Both correctly reach the thread's actual resolution (invalid — wrong --run-level, load_format:dummy patched in via PR #4354), with plausible code-path grounding (run_args.py, stage_config.py, runtime. |
| issue4891.r1 | opus_baseline | decisive | Candidate X crashed before producing any answer (API 402 error, no RUN_REPORT), so it scores zero across the board. Candidate Y correctly reaches the same resolution as the thread — closing as a dupli |
| issue4891.r2 | opus_baseline | decisive | Candidate X produced no answer at all (API error, rc=1), so it cannot be credited on any dimension. Candidate Y correctly reaches the same disposition as the ground truth (duplicate of #4808, tied to  |
| issue4891.r3 | opus_baseline | decisive | Candidate Y produced no answer at all—only a stack trace from a failed API call (402 Insufficient Balance)—so it cannot be scored on merit. Candidate X correctly reaches the ground-truth conclusion (d |
| issue4905.r1 | opus_baseline | slight | Both correctly bisect the regression to PR #4834 and land on the same plausible test-vs-guard diagnosis, but both overreach by confidently declaring the issue already fixed and closeable — the actual  |
| issue4905.r2 | opus_baseline | slight | Both correctly identify PR #4834 as the cause (matching yenuo26's comment) and give nearly identical technical diagnoses (level=2 vs level=1, same file/line citations, same #4473 lineage), but both ov |
| issue4905.r3 | opus_baseline | slight | Both correctly latch onto the thread's one hard fact (yenuo26's attribution to #4834) and give the same plausible technical story (level-2 sleep intentionally has no wake path, test should use level=1 |
| pr4810.r1 | copilot_v2 | slight | Both candidates correctly validate the core loader-migration logic and both independently surface the exact latent gap: the unswept HunyuanImage3 diffusion loader (hunyuan_image3_transformer.py:2238)  |
| pr4810.r2 | opus_baseline | slight | Both candidates independently found the exact latent gap (hunyuan_image3_transformer.py:2238 still calling the removed get_cache_scale API, later issue #4891), which is the strongest signal of real in |
| pr4810.r3 | copilot_v2 | slight | Both candidates independently grep-discover the exact latent gap (hunyuan_image3_transformer.py:2238 still calling the removed get_cache_scale, matching the later #4891 issue) and both ground their fi |
| pr4816.r1 | copilot_v2 | slight | Ground truth has no substantive concerns (bot rate-limited, human said only 'lgtm'), so both correctly land on APPROVE with nothing to miss — recall ties at 1.0. Y is more rigorous and conservative: i |
| pr4816.r2 | copilot_v2 | slight | Both correctly land on APPROVE, matching the trivial ground truth (no substantive human concerns exist), so recall is saturated for both. Y grounds every claim in a specific diff hunk with file:line c |
| pr4816.r3 | opus_baseline | slight | Both correctly land on APPROVE matching the ground-truth 'lgtm', with no substantive concerns to recall since the PR is a clean, verified rename. Both perform grounded, diff-specific verification (ups |
| pr4825.r1 | opus_baseline | clear | The one substantive ground-truth concern (dsocek's point that hardcoding component names is fragile and a single source of truth like the packed-modules mapping should drive discovery instead) is clos |
| pr4825.r2 | opus_baseline | clear | The one substantive ground-truth concern (dsocek's point that the hardcoded default_components list duplicates logic and should instead be driven from a canonical per-model source, e.g. so naming vari |
| pr4825.r3 | opus_baseline | clear | The one substantive ground-truth concern (dsocek: hardcoded PEFT-name-to-module fixes should be driven from a single source of truth like stacked_params_mapping rather than ad hoc lists) is conceptual |
| pr4837.r1 | opus_baseline | clear | Both candidates correctly validate the two core fixes (DiffusionOutput access/return and the already_submitted removal) and independently arrive at the same reasoning as the sole ground-truth inline c |
| pr4837.r2 | opus_baseline | clear | The only substantive ground-truth concern is yJader's explanation that the already_submitted guard should be dropped because diffusion StagePool rejects list prompts in both submit_initial and submit_ |
| pr4837.r3 | opus_baseline | clear | X's core claim — that both submit_initial and submit_update reject list-shaped diffusion prompts, so gating the unwrap on already_submitted was unnecessary — is nearly verbatim the reasoning yJader ga |
| pr4893.r1 | copilot_v2 | slight | Ground truth's only substantive concern (yenuo26: test coverage gap around the new reduce_scatter/device_communicator plumbing) is closest matched by X's finding that init_vllm_model_parallel_group is |
| pr4893.r2 | tie | slight | X directly engages the one substantive GT concern (yenuo26's reduce_scatter/device_communicator assertions) by quoting and validating those exact lines, while Y never mentions it, only offering a gene |
| pr4893.r3 | copilot_v2 | clear | The single substantive ground-truth concern (yenuo26 questioning whether the reduce_scatter hasattr checks are sufficient verification) is essentially echoed by Candidate Y's finding that init_vllm_mo |
