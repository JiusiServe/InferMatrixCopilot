# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)

Judge: claude-sonnet-5 (blind, randomized order, 3 replicates x 10 items = 30 verdicts)

## Wins
- copilot_v2: 9
- opus_baseline: 21
- tie: 0

## Mean rubric scores

| arm | actionability | completeness | correctness | gap_hit | grounding | precision | recall |
|---|---|---|---|---|---|---|---|
| copilot_v2 | 0.74 | 0.67 | 0.69 | 0.23 | 0.66 | 0.75 | 0.52 |
| opus_baseline | 0.71 | 0.81 | 0.76 | 0.23 | 0.73 | 0.81 | 0.59 |

## Per-verdict detail

| item.rep | winner | margin | rationale (head) |
|---|---|---|---|
| issue4793.r1 | copilot_v2 | slight | Both correctly identify the actual resolution: PR #4527 set inter_stage_outputs=None in the non-async-chunk path, PR #4792 fixed it by using per_req_payloads for both, already merged into main via the |
| issue4793.r2 | opus_baseline | slight | Both correctly identify the root cause (PR #4527's None inter-stage payload starving the downstream stage) and the fix (PR #4792, already in the 0.24 rebase commit a560ed18), matching the ground truth |
| issue4793.r3 | copilot_v2 | slight | Both correctly identify PR #4527 as the regression, PR #4792 as the fix, and confirm it's folded into the 0.24 rebase (a560ed18), matching the thread resolution and offering the same async_chunk:true  |
| issue4827.r1 | opus_baseline | clear | Both correctly diagnose the None+1 TypeError from missing extended ratio tokens and correctly prescribe the hunyuan_image3_dit.yaml workaround confirmed in-thread. Y is better grounded (cites specific |
| issue4827.r2 | opus_baseline | slight | Both correctly diagnose the config/tokenizer mismatch and give the same verified workaround, matching the thread's core resolution. X is more grounded, citing specific line ranges and pulling explicit |
| issue4827.r3 | opus_baseline | slight | Both correctly diagnose the tokenizer-missing-extended-ratio-token crash and give the same fix (serve Base with hunyuan_image3_dit.yaml), matching the thread resolution. X is more grounded, citing spe |
| issue4842.r1 | opus_baseline | slight | Both correctly reproduce the thread's actual resolution: default --run-level=core_model forces load_format=dummy via _add_dummy_load_format (extended to online serving by #4354), so the semantic asser |
| issue4842.r2 | opus_baseline | slight | Both correctly diagnose the invalid/wrong-run-level root cause and match the thread's actual resolution, both citing run_args.py/stage_config.py for the dummy-load-format mechanism and both proposing  |
| issue4842.r3 | opus_baseline | clear | Both correctly diagnose the same root cause (default --run-level=core_model forces dummy weights) and land on the same 'closed as invalid, rerun with --run-level=full_model' disposition matching the t |
| issue4891.r1 | opus_baseline | slight | Both correctly land on the ground-truth disposition (duplicate of #4808/#4809), but X asserts as fact that the fix is 'already applied on main' and 'verified against current main checkout' plus an unv |
| issue4891.r2 | opus_baseline | clear | The thread closed #4891 as a duplicate of PR #4808 with pointer to #4809 for detail — Y mirrors that structure exactly (cites #4808 as the fix PR, #4809 as the tracking issue with more context) while  |
| issue4891.r3 | opus_baseline | clear | Ground truth resolves this as 'duplicate of #4808' with #4809 for extra detail — X mirrors that framing exactly and additionally catches that #4808 is closed-not-merged, correctly hedging with a reque |
| issue4905.r1 | copilot_v2 | slight | Both correctly tie the failure to PR #4834's intentional wake_up() guard (matching yenuo26's comment) and both propose the same level=1 fix, but both overstate resolution status: the actual thread sho |
| issue4905.r2 | opus_baseline | slight | Both candidates converge on the same plausible diagnosis (PR #4834 added an intentional wake-after-level-2-sleep guard; the pre-existing test wasn't updated) but both overclaim a confident 'already fi |
| issue4905.r3 | opus_baseline | slight | Both correctly tie the failure to PR #4834's intentional NotImplementedError guard (matching yenuo26's comment), but both confidently declare the issue 'already fixed on main' and recommend closing —  |
| pr4810.r1 | opus_baseline | clear | Both candidates correctly validate the direct/delegated loader split and both independently flag the exact latent gap (hunyuan_image3_transformer.py diffusion loader still calling the removed API), ma |
| pr4810.r2 | opus_baseline | slight | Both candidates independently surface the exact latent gap (hunyuan_image3_transformer.py:2238 still calling the removed get_cache_scale), so gap_hit is true for both, but neither recovers the human r |
| pr4810.r3 | opus_baseline | slight | Both candidates independently found the diffusion-loader (hunyuan_image3_transformer.py:2238) still calling the removed get_cache_scale API, matching the latent gap check and effectively the '#4808 co |
| pr4816.r1 | copilot_v2 | slight | Both correctly conclude this is a clean, complete mechanical rename with no blockers, matching the ground truth's trivial 'lgtm' approval — recall is tied since there's nothing substantive to miss. Y' |
| pr4816.r2 | copilot_v2 | slight | Ground truth has no substantive concerns (plain 'lgtm' approve), so both candidates correctly reach APPROVE and recall is trivially satisfied for each. Both give the same accurate high-level narrative |
| pr4816.r3 | copilot_v2 | clear | Ground truth has no substantive concerns (bot notice + plain 'lgtm'), so both APPROVE verdicts trivially match and recall is vacuously full for each. Precision favors Y: every line number Y cites (754 |
| pr4825.r1 | opus_baseline | clear | Both correctly validate that adding 'unet' is safe and scoped, matching the ground truth's LGTM consensus, but neither candidate surfaces dsocek's specific inline suggestion about driving naming/compo |
| pr4825.r2 | opus_baseline | clear | X's top comment (reuse pipeline._dit_modules instead of a fourth hardcoded component list) echoes the spirit of dsocek's real concern about the hardcoded default_components list drifting and wanting a |
| pr4825.r3 | opus_baseline | clear | The one substantive ground-truth concern (dsocek's point that hardcoding component names is fragile and the manager should instead derive from a single source of truth to handle naming/fusion conflict |
| pr4837.r1 | opus_baseline | clear | Both candidates correctly identify and verify the core fix (already_submitted removal is safe because both submit_initial and submit_update reject list prompts), matching the sole ground-truth inline  |
| pr4837.r2 | opus_baseline | clear | The sole ground-truth substantive concern (yJader's point that already_submitted shouldn't gate the unwrap because both submit_initial and submit_update reject list prompts) is nailed precisely by Y,  |
| pr4837.r3 | opus_baseline | clear | Both candidates independently reconstruct the sole ground-truth insight (both submit_initial/submit_update reject list prompts regardless of already_submitted, so the gate removal is correct) and both |
| pr4893.r1 | copilot_v2 | clear | X surfaces several concrete, line-cited findings grounded in the diff (untested early-return branch in the new DP-metadata helper, a plausible unnecessary all_gather on non-MoE paths, and the intent b |
| pr4893.r2 | copilot_v2 | clear | Ground truth here is thin (mostly social comments plus one inline concern about reduce_scatter test coverage that the diff already resolves), so recall is low for both, but X explicitly engages with t |
| pr4893.r3 | copilot_v2 | clear | Neither candidate surfaces the ground-truth reviewer's actual concern (hasattr checks not verifying reduce_scatter behaves correctly), so recall is near-zero for both. X mostly confirms the PR is corr |
