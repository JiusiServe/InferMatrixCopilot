# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)

Judge: claude-sonnet-5 (blind, randomized order, 3 replicates x 10 items = 30 verdicts)

## Wins
- copilot_v2: 11
- opus_baseline: 19
- tie: 0

## Mean rubric scores

| arm | actionability | completeness | correctness | gap_hit | grounding | precision | recall |
|---|---|---|---|---|---|---|---|
| copilot_v2 | 0.69 | 0.62 | 0.66 | 0.21 | 0.57 | 0.82 | 0.54 |
| opus_baseline | 0.71 | 0.78 | 0.73 | 0.21 | 0.69 | 0.82 | 0.57 |

## Per-verdict detail

| item.rep | winner | margin | rationale (head) |
|---|---|---|---|
| issue4793.r1 | opus_baseline | clear | Both correctly land on PR #4792 as the fix and note it's already in the vLLM 0.24 rebase (a560ed18), matching the thread. X mostly parrots the exact ground-truth comment text but attaches it to an unv |
| issue4793.r2 | copilot_v2 | clear | Both land on the right final answer (PR #4792 fixes the #4527 regression, already in the 0.24 rebase). But X's primary root-cause narrative invents an entire mechanism in gpu_ar_model_runner.py (poole |
| issue4793.r3 | opus_baseline | clear | Both correctly land on the ground-truth resolution (regression from #4527, fixed by #4792, already present via the 0.24 rebase commit a560ed18, close-as-fixed). X's file structure — primary fix commen |
| issue4827.r1 | opus_baseline | slight | Both correctly diagnose the base/instruct config mismatch, cite the same crashing lines in hunyuan_image3.py, give the working DiT-config workaround, and correctly note the maintainer's ask to track t |
| issue4827.r2 | opus_baseline | clear | Both correctly diagnose the None+1 TypeError from missing extended ratio tokens on the Base tokenizer and both give the maintainer-confirmed workaround (hunyuan_image3_dit.yaml) plus the correct dispo |
| issue4827.r3 | opus_baseline | clear | Both correctly diagnose the None+1 TypeError from missing extended ratio tokens in the base tokenizer and give the same working workaround (hunyuan_image3_dit.yaml), matching the thread's actual resol |
| issue4842.r1 | copilot_v2 | slight | Both correctly diagnose the run-level mismatch (core_model → dummy weights) matching the actual 'invalid'/closed resolution, cite stage_config.py's dummy-load-format patching, and recommend --run-leve |
| issue4842.r2 | opus_baseline | clear | Both correctly diagnose the run-level/dummy-weight issue and recommend --run-level=full_model, matching the thread's actual resolution. Y is more tightly grounded: it explicitly ties in PR #4354 (mirr |
| issue4842.r3 | opus_baseline | slight | Both correctly diagnose the run-level/dummy-weight mismatch and recommend --run-level=full_model, matching the thread's 'invalid' resolution. Y grounds the explanation more thoroughly, tracing the ful |
| issue4891.r1 | opus_baseline | clear | The actual resolution cites two things: duplicate of #4808 AND refer to #4809 for details; X addresses only the former and never mentions #4809, while Y explicitly reconstructs the #4809 triage (5 cal |
| issue4891.r2 | opus_baseline | clear | Both reach the correct 'duplicate of #4808' disposition, but the actual thread explicitly points to #4809's comment for 'additional details' — Y correctly surfaces #4809 as the tracking issue coordina |
| issue4891.r3 | opus_baseline | clear | Both correctly land on the 'duplicate of #4808' disposition, but the ground truth explicitly points to issue #4809's comment for context, and only X engages with #4809 (framing it as the tracking issu |
| issue4905.r1 | copilot_v2 | slight | The actual thread shows this is still unresolved — Flink-ddd is asking yenuo26 to trigger a full sleep-mode CI run, implying active investigation, not a closed/merged fix. Both candidates instead conf |
| issue4905.r2 | copilot_v2 | slight | The actual thread shows this issue still under active investigation (yenuo26 flags #4834 as the likely trigger and asks for a CI rerun; no fix or closure is confirmed), yet both candidates confidently |
| issue4905.r3 | copilot_v2 | slight | Both correctly trace the guard to PR #4834 (matches yenuo26's comment) but then both confidently fabricate a specific closing fix (PR #4912, level=1 change) and declare the issue resolved/closed — whi |
| pr4810.r1 | copilot_v2 | clear | Both independently surface the exact latent gap — the unswept hunyuan_image3_transformer.py:2238 caller of the removed get_cache_scale API — with concrete file/line evidence and fix suggestions, which |
| pr4810.r2 | opus_baseline | clear | Both candidates independently surface the latent gap (hunyuan_image3_transformer.py:2238 still calling removed get_cache_scale, unswept by this PR), satisfying gap_hit for both. Y goes further by actu |
| pr4810.r3 | opus_baseline | slight | Both candidates independently catch the exact latent gap (the still-unfixed get_cache_scale call in hunyuan_image3_transformer.py), and both give concrete, actionable file/line feedback. Y is slightly |
| pr4816.r1 | copilot_v2 | slight | Ground truth has no substantive concerns (codex hit a rate limit, human just said 'lgtm'), so both correctly land on APPROVE with no missed issues—recall is trivially satisfied for both. Y's hunk-by-h |
| pr4816.r2 | opus_baseline | slight | Ground truth has no substantive concerns (just an 'lgtm' approval), and both candidates correctly reach APPROVE with grounded, diff-consistent verification of the rename's completeness (repo-wide grep |
| pr4816.r3 | copilot_v2 | slight | Ground truth has no substantive concerns (just an approving 'lgtm' and a bot notice), so both candidates correctly recall everything by recommending APPROVE with grounded, diff-matching analysis of th |
| pr4825.r1 | opus_baseline | clear | The GT's substantive concern (dsocek) is that hardcoding component names is fragile and should instead be driven by structured per-model data (packed_modules_mapping/stacked_params_mapping) to handle  |
| pr4825.r2 | opus_baseline | clear | X's suggestion to derive default_components from each pipeline's existing _dit_modules declaration mirrors the substance of dsocek's ground-truth concern (avoid ad-hoc naming lists, drive from structu |
| pr4825.r3 | opus_baseline | slight | Neither candidate surfaces dsocek's actual substantive concern (fused-projection naming conflicts, driving the mapper from _packed_modules_mapping), so recall is low for both, though X's push toward a |
| pr4837.r1 | opus_baseline | slight | Both candidates correctly zero in on the same line (orchestrator.py:1290) that the human reviewer flagged, and both give a grounded, code-cited explanation of why removing the `already_submitted` gate |
| pr4837.r2 | opus_baseline | clear | Both candidates correctly validate the orchestrator.py:1290 already_submitted removal as safe, but Y's justification (submit_initial and submit_update both raise ValueError on list prompts, cited with |
| pr4837.r3 | opus_baseline | slight | Both candidates correctly zero in on the only substantive ground-truth point (the already_submitted gate removal is safe because both submit paths reject list prompts identically) and both flag the mi |
| pr4893.r1 | copilot_v2 | clear | The one substantive ground-truth concern (yenuo26 questioning whether the reduce_scatter hasattr checks in test_expert_parallel_layout.py are sufficient verification) falls in territory X explicitly e |
| pr4893.r2 | copilot_v2 | clear | Neither candidate reproduces the ground-truth reviewer's concern about whether hasattr-only verification of reduce_scatter is sufficient, but X at least directly discusses that exact test line (valida |
| pr4893.r3 | copilot_v2 | clear | The one substantive ground-truth concern (yenuo26's question about verifying reduce_scatter in the test) is directly addressed by Y, which validates that exact test line with a specific citation; X ne |
