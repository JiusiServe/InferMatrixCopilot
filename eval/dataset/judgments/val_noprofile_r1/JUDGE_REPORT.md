# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)

Judge: claude-sonnet-5 (blind, randomized order, 3 replicates x 10 items = 30 verdicts)

## Wins
- copilot_v2: 12
- opus_baseline: 17
- tie: 1

## Mean rubric scores

| arm | actionability | completeness | correctness | gap_hit | grounding | precision | recall |
|---|---|---|---|---|---|---|---|
| copilot_v2 | 0.78 | 0.68 | 0.72 | 0.25 | 0.71 | 0.60 | 0.42 |
| opus_baseline | 0.72 | 0.80 | 0.76 | 0.23 | 0.76 | 0.86 | 0.61 |

## Per-verdict detail

| item.rep | winner | margin | rationale (head) |
|---|---|---|---|
| issue4793.r1 | copilot_v2 | slight | Both correctly diagnose the #4527 regression fixed by #4792, already folded into the 0.24 rebase, matching the thread exactly. X's fix snippet is a verbatim, character-for-character match to the groun |
| issue4793.r2 | opus_baseline | slight | Both correctly diagnose the #4527 regression and confirm the #4792 fix already lives in the 0.24 rebase commit cited by the maintainers, matching the thread's actual resolution. X grounds slightly bet |
| issue4793.r3 | tie | slight | Both candidates correctly identify PR #4527 as the regression (None inter-stage payload starving the downstream stage) and PR #4792 as the fix already folded into the 0.24 rebase commit a560ed18, matc |
| issue4827.r1 | copilot_v2 | slight | Both correctly diagnose the None+1 crash from missing extended ratio tokens and give the same confirmed workaround, but X explicitly cites PR #2713 and the old `modes`-filtering regression that akshat |
| issue4827.r2 | opus_baseline | slight | Both candidates correctly diagnose the base/Instruct tokenizer mismatch, cite the same crash site, explain the PR #2713 config regression, confirm the DiT-config workaround, and correctly note the gua |
| issue4827.r3 | copilot_v2 | slight | Both correctly diagnose the None+1 crash at hunyuan_image3.py:1561-1563 as a base-tokenizer-vs-Instruct-config mismatch and cite the same confirmed workaround and follow-up-issue disposition, matching |
| issue4842.r1 | opus_baseline | clear | Both correctly diagnose the dummy-weight/run-level mismatch and cite the same core evidence (run_args.py default, _add_dummy_load_format in stage_config.py, PR #4354), matching the thread's actual 'in |
| issue4842.r2 | opus_baseline | slight | Both correctly identify the actual resolution (invalid, wrong --run-level defaulting to core_model which forces dummy weights), cite the same core mechanism (_add_dummy_load_format in stage_config.py) |
| issue4842.r3 | opus_baseline | clear | Both correctly reach the ground-truth verdict (run-level mismatch causing dummy weights, closed as invalid) and cite the same PR #4354 / dummy load_format mechanism that akshatvishu identified. Y is m |
| issue4891.r1 | copilot_v2 | clear | Both correctly land on the ground-truth verdict (duplicate of #4808, per #4809), but X states it simply and directly, matching the terse actual resolution and giving the reporter concrete next steps ( |
| issue4891.r2 | opus_baseline | clear | Ground truth says the issue is a duplicate of #4808 (fix PR) with details in #4809; X inverts this, labeling it 'duplicate-of-4809' and asserting the fix is 'already merged' and the reporter has a 'st |
| issue4891.r3 | opus_baseline | clear | Both correctly land on the duplicate-of-#4808 disposition and the get_cache_scale root cause, matching the ground truth. X is far more grounded, citing specific file:line evidence (including a real re |
| issue4905.r1 | opus_baseline | slight | Both correctly identify PR #4834 as the cause and correctly explain the NotImplementedError guard's intent, matching yenuo26's bisection — but both overclaim resolution ('already fixed on main', recom |
| issue4905.r2 | copilot_v2 | slight | Both correctly bisect the failure to PR #4834's intentional NotImplementedError guard, matching yenuo26's thread comment, and both cite the same async_omni.py guard code and propose the same level=1 t |
| issue4905.r3 | copilot_v2 | slight | The actual thread never confirms a fix — it's just yenuo26 bisecting to #4834 and Flink-ddd asking to trigger a full CI run, i.e. the issue is still open/unresolved, not closed. Both candidates invent |
| pr4810.r1 | copilot_v2 | slight | Both candidates independently discover the unswept get_cache_scale caller in the diffusion transformer, correctly hitting the latent gap the human reviewers missed. Y frames it as a severity-tagged bl |
| pr4810.r2 | copilot_v2 | slight | Both candidates independently found the latent gap — the leftover get_cache_scale call in hunyuan_image3_transformer.py:2238 — and both raised the same substantive test-coverage critique (delegated-lo |
| pr4810.r3 | copilot_v2 | slight | Both independently rediscover the latent gap (the diffusion-transformer hunyuan_image3_transformer.py still calling the removed get_cache_scale), but X grounds it purely in verified PR-time-tree evide |
| pr4816.r1 | opus_baseline | clear | Ground truth shows this is a trivial, fully-consistent rename that was simply approved ('lgtm'), and X correctly reaches that conclusion with grounded verification (exhaustive grep, cross-check agains |
| pr4816.r2 | opus_baseline | clear | Ground truth shows this PR is a trivial, correctly-scoped rename with zero substantive reviewer concerns (just 'lgtm' approval), so there's nothing for either candidate to miss. X's approve verdict is |
| pr4816.r3 | opus_baseline | clear | Ground truth is a trivial 'lgtm' approval with no substantive concerns, which X matches — it verifies the rename against the actual upstream `base()` consumer and confirms completeness, all grounded i |
| pr4825.r1 | opus_baseline | clear | X's comment about deriving default_components from the pipeline's own declarative source (_dit_modules) instead of a fourth hardcoded list closely mirrors the actual reviewer dsocek's concern about dr |
| pr4825.r2 | opus_baseline | clear | The one substantive ground-truth concern (dsocek: hardcoded default_components list should be derived from existing per-model mapping rather than manually appended) is directly hit by Candidate X's co |
| pr4825.r3 | opus_baseline | clear | X's top comment (reuse pipeline._dit_modules instead of growing a hardcoded default_components tuple) closely echoes the actual reviewer concern (dsocek: derive the mapping from existing per-model met |
| pr4837.r1 | opus_baseline | decisive | The sole substantive ground-truth concern (yJader's inline comment) explains that dropping the already_submitted gate is correct because diffusion StagePool rejects list prompts in both submit_initial |
| pr4837.r2 | opus_baseline | decisive | Ground truth is a unanimous APPROVE where the one inline comment explains that removing `already_submitted` is correct because both submit paths converge on the same DiffusionEngine code and StagePool |
| pr4837.r3 | opus_baseline | decisive | X directly verified the exact concern the human reviewer raised (whether already_submitted-gated unwrapping is safe to drop) by reading stage_pool.py and confirming both submit_initial and submit_upda |
| pr4893.r1 | copilot_v2 | slight | Neither candidate surfaces the one substantive ground-truth concern (yenuo26's question about verifying reduce_scatter behavior, not just hasattr, in the test), so recall is near-zero for both. X does |
| pr4893.r2 | copilot_v2 | clear | Neither candidate reproduces the one substantive ground-truth concern (yenuo26's nitpick that the new hasattr(reduce_scatter) checks don't actually verify reduce_scatter's behavior), so recall is low  |
| pr4893.r3 | copilot_v2 | slight | Neither candidate surfaces the one substantive ground-truth ask (verifying device_communicator/reduce_scatter for _TP too, not just PCP/DP/EP), so recall is low for both. X is tighter and more precise |
