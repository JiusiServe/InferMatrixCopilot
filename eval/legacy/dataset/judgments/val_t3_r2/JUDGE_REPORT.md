# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)

Judge: claude-sonnet-5 (blind, randomized order, 3 replicates x 10 items = 29 verdicts)

## Wins
- copilot_v2: 3
- opus_baseline: 26
- tie: 0

## Mean rubric scores

| arm | actionability | completeness | correctness | gap_hit | grounding | precision | recall |
|---|---|---|---|---|---|---|---|
| copilot_v2 | 0.72 | 0.64 | 0.69 | 0.20 | 0.70 | 0.69 | 0.36 |
| opus_baseline | 0.74 | 0.81 | 0.78 | 0.20 | 0.76 | 0.88 | 0.60 |

## Per-verdict detail

| item.rep | winner | margin | rationale (head) |
|---|---|---|---|
| issue4793.r1 | opus_baseline | clear | Both correctly pin the bug to PR #4792 and reproduce the exact code/comment from the real fix commit, matching the thread's core resolution. Y goes further, independently corroborating the actual main |
| issue4793.r2 | opus_baseline | clear | Both correctly identify PR #4792 as the fix for the async_chunk:false None-payload starvation bug, and both quote the exact fix snippet that matches akshatvishu's ground-truth comment almost verbatim. |
| issue4793.r3 | opus_baseline | slight | Both candidates correctly identify PR #4792 as the fix (None vs per_req_payloads starving the downstream stage) and both quote the exact code/comment that appears in the ground-truth thread, so core c |
| issue4827.r1 | copilot_v2 | slight | Both correctly diagnose the tokenizer/config mismatch and cite the confirmed workaround, but X faithfully reproduces the thread's actual root-cause framing (PR #2713 regression removing the `modes` fi |
| issue4827.r2 | opus_baseline | slight | Both candidates correctly reproduce the thread's diagnosis (base tokenizer lacks extended ratio tokens, config mismatch between moe.yaml and dit.yaml, confirmed workaround, defer hardening to a new is |
| issue4827.r3 | opus_baseline | clear | Both correctly diagnose the config/tokenizer mismatch, cite the same crash line, and reproduce the confirmed workaround and Gaohan123's follow-up-issue instruction. X goes further with a concrete prop |
| issue4842.r1 | opus_baseline | clear | Both correctly diagnose the issue as a run-level misconfiguration (default core_model → dummy weights) rather than a real bug, matching the actual 'invalid' resolution and the fix of using --run-level |
| issue4842.r3 | opus_baseline | clear | Both correctly diagnose the run-level misconfiguration (default core_model → dummy weights) matching the confirmed thread resolution, and both cite specific file:line evidence for the dummy-load-forma |
| issue4891.r1 | opus_baseline | clear | Ground truth closed #4891 as a duplicate of #4808, pointing to #4809 for details. Y reaches exactly that resolution, explains the #4809 triage of all 5 call sites, correctly flags that #4808 closed wi |
| issue4891.r2 | opus_baseline | clear | The thread resolution was a duplicate closure pointing to PR #4808 and issue #4809 — Y explicitly reaches and argues for that same disposition, citing #4809's role as the tracking issue and #4808 as t |
| issue4891.r3 | opus_baseline | clear | The actual resolution was a terse duplicate-closure pointing to #4808/#4809, and X is the only candidate that explicitly reaches and recommends that exact conclusion ('closing as duplicate is the righ |
| issue4905.r1 | copilot_v2 | clear | Both candidates correctly identify PR #4834 as the causal trigger (matching yenuo26's comment), but both overclaim that the fix is already merged/verified and that the issue can be closed — the actual |
| issue4905.r2 | opus_baseline | slight | Both candidates converge on the same (plausible but unverified) theory — PR #4834 added an intentional guard and the stale test needs a level=1 fix already on HEAD — which overstates the actual thread |
| issue4905.r3 | copilot_v2 | slight | The actual thread shows an unresolved escalation: yenuo26 suspects #4834 caused the regression and asks Flink-ddd to check, and Flink-ddd in turn asks yenuo26 to trigger a full CI sleep-mode test — no |
| pr4810.r1 | opus_baseline | slight | Both candidates independently catch the latent gap (the surviving get_cache_scale caller in hunyuan_image3_transformer.py that later became issue #4891), so gap_hit is true for both, and both are conc |
| pr4810.r2 | opus_baseline | clear | Both candidates independently surface the real latent gap (hunyuan_image3_transformer.py:2238 still calling the removed get_cache_scale, later fixed by #4891), so gap_hit is true for both. But the gro |
| pr4810.r3 | opus_baseline | slight | Both candidates independently surface the real latent gap (hunyuan_image3_transformer.py:2238 still calling the removed get_cache_scale API), so gap_hit is true for both, with X framing it more forcef |
| pr4816.r1 | opus_baseline | slight | Ground truth is a trivial 'lgtm' approval on a mechanical rename PR with zero substantive concerns; X matches this exactly, with grounded verification (confirms no missed occurrences, matches upstream |
| pr4816.r2 | opus_baseline | clear | Ground truth is a trivial approve ('lgtm', no inline comments), so recall is vacuously satisfied by both. X's review is fully grounded — it verifies the rename against upstream and existing tests and  |
| pr4816.r3 | opus_baseline | clear | Ground truth has no real concerns (just an lgtm approve), so both trivially satisfy recall. X correctly matches the actual outcome with rigorous, grounded verification (cross-checked upstream vLLM nam |
| pr4825.r1 | opus_baseline | clear | X covers both real reviewer threads (the validation-results request, which it explicitly notes was already satisfied, and dsocek's hardcoded-list/naming-conflict concern, matched via a similar _dit_mo |
| pr4825.r2 | opus_baseline | slight | Both candidates converge on the same core structural point the ground truth hints at (dsocek's suggestion to derive component names from an existing mapping rather than hardcoding a list), though neit |
| pr4825.r3 | opus_baseline | slight | Neither candidate found the actual substantive ground-truth concern (dsocek's suggestion to derive PEFT naming from `_packed_modules_mapping`/`stacked_params_mapping` for fused-projection renames), th |
| pr4837.r1 | opus_baseline | decisive | X independently verifies the exact reasoning the ground-truth reviewer gave (both submit_initial and submit_update reject list prompts regardless of already_submitted, confirming the guard removal is  |
| pr4837.r2 | opus_baseline | decisive | The one substantive ground-truth concern (yJader's inline comment) argues that dropping `already_submitted` is safe because diffusion's StagePool rejects list prompts identically in both submit_initia |
| pr4837.r3 | opus_baseline | decisive | X independently verified the exact reasoning the human reviewer gave (both submit_initial/submit_update reject list prompts identically, so gating unwrap on already_submitted was the actual bug) and c |
| pr4893.r1 | opus_baseline | clear | The one substantive ground-truth concern (yenuo26 asking about verifying the reduce_scatter fix alongside device_communicator) is only echoed by Y, which explicitly notes the new coordinators own both |
| pr4893.r2 | opus_baseline | clear | Neither candidate surfaces the one substantive ground-truth concern (yenuo26's question about whether the test should also verify reduce_scatter), so recall is near-zero for both. X's deliverable is a |
| pr4893.r3 | opus_baseline | clear | Neither candidate surfaces the ground truth's one substantive concern (yenuo26's question about verifying reduce_scatter alongside device_communicator in the test), so recall is low and roughly tied.  |
