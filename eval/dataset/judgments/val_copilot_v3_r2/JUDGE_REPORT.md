# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)

Judge: claude-sonnet-5 (blind, randomized order, 3 replicates x 10 items = 30 verdicts)

## Wins
- copilot_v2: 12
- opus_baseline: 18
- tie: 0

## Mean rubric scores

| arm | actionability | completeness | correctness | gap_hit | grounding | precision | recall |
|---|---|---|---|---|---|---|---|
| copilot_v2 | 0.69 | 0.68 | 0.66 | 0.21 | 0.64 | 0.83 | 0.51 |
| opus_baseline | 0.66 | 0.79 | 0.75 | 0.21 | 0.70 | 0.85 | 0.60 |

## Per-verdict detail

| item.rep | winner | margin | rationale (head) |
|---|---|---|---|
| issue4793.r1 | opus_baseline | slight | Both correctly land on the actual resolution: the hang is the #4527 regression fixed by PR #4792, already absorbed into main via the 0.24 rebase (a560ed18), and both correctly cite the exact gpu_gener |
| issue4793.r2 | opus_baseline | slight | Both correctly identify the #4527 regression (non-async-chunk branch shipping (None, payload) instead of (payload, payload)) and correctly conclude 'close — fixed by PR #4792, already absorbed into th |
| issue4793.r3 | opus_baseline | slight | Both land on the correct, thread-matching conclusion (real regression, fixed by #4792, already absorbed into the vLLM 0.24 rebase, close with reopen condition) and both cite the exact code diff quoted |
| issue4827.r1 | opus_baseline | slight | Both correctly diagnose the same root cause (missing extended ratio tokens on the Base tokenizer, regression from #2713 forcing two-stage topology) and give the same confirmed workaround, matching the |
| issue4827.r2 | opus_baseline | clear | Both correctly diagnose the base-tokenizer/extended-ratio-token crash, cite the same file/lines, and confirm the same DiT-config workaround FayeSpica validated. X is cleaner: it gives a concrete guard |
| issue4827.r3 | opus_baseline | clear | Both correctly diagnose the base-tokenizer/instruct-config mismatch at the same code lines and cite the same Tencent reference and FayeSpica workaround, so grounding on the core diagnosis is comparabl |
| issue4842.r1 | copilot_v2 | slight | Both correctly diagnose the core_model→dummy-weight run-level issue and correctly land on 'invalid' matching the actual thread resolution, with matching fix commands. X fabricates specific evidence no |
| issue4842.r2 | copilot_v2 | slight | Both correctly land on the actual resolution: default --run-level=core_model forces dummy weights via #4354, fix is --run-level=full_model, correctly closed as invalid, matching akshatvishu/yenuo26's  |
| issue4842.r3 | opus_baseline | slight | Both correctly identify the actual thread resolution: this is a run-level misconfiguration (core_model dummy weights) not a real bug, and the fix is --run-level=full_model, matching akshatvishu/yenuo2 |
| issue4891.r1 | opus_baseline | clear | Ground truth is a simple duplicate-closure pointing to #4808/#4809. Y explicitly reaches that same disposition, backs it with concrete PR metadata (enumerates the 5 call sites from #4809, confirms #48 |
| issue4891.r2 | opus_baseline | decisive | Ground truth closes #4891 as a duplicate of #4808, pointing to #4809 for the full triage; Y reaches exactly this conclusion, cites the #4809 tracking issue, and correctly hedges the one unverifiable c |
| issue4891.r3 | opus_baseline | clear | Both correctly diagnose the removed get_cache_scale call and correctly identify the fix (drop the branch, rely on maybe_remap_kv_scale_name), matching the ground truth's disposition of closing as a du |
| issue4905.r1 | copilot_v2 | slight | Both correctly identify PR #4834 as the trigger (matching yenuo26's bisection), but both then confidently invent an unconfirmed resolution — a specific 'already fixed on main' commit, precise diffs tu |
| issue4905.r2 | copilot_v2 | slight | Both correctly identify PR #4834's intentional NotImplementedError guard as the trigger, matching yenuo26's bisection — but both overclaim a confirmed 'already fixed on main, close it' resolution that |
| issue4905.r3 | copilot_v2 | slight | The actual thread shows an unresolved escalation: Flink-ddd is asking yenuo26 to trigger a full CI sleep-mode run to investigate, not confirming any fix — yet both candidates confidently declare the b |
| pr4810.r1 | opus_baseline | clear | Both candidates independently surface the exact latent gap (hunyuan_image3_transformer.py still calling the removed get_cache_scale API), and both cover the core ground-truth point that delegated vs.  |
| pr4810.r2 | opus_baseline | clear | Both correctly validate the direct-vs-delegated loader distinction and both independently surface the real latent gap (hunyuan_image3_transformer.py:2238 still calling removed get_cache_scale) with fi |
| pr4810.r3 | opus_baseline | slight | Both correctly validate why the direct vs. delegated loader migration is sound, and both independently rediscover the real latent gap (the diffusion-loader caller of the removed get_cache_scale API, l |
| pr4816.r1 | copilot_v2 | clear | Ground truth has no substantive concerns (bot noise + 'lgtm'), so both candidates land on the right overall verdict and neither misses anything real. X's evidence includes a suspiciously specific unve |
| pr4816.r2 | copilot_v2 | clear | Ground truth has no substantive concerns (just an 'lgtm' approval), so both candidates trivially achieve full recall. X's review is solid but purely confirmatory (grep + claimed upstream cross-check)  |
| pr4816.r3 | copilot_v2 | clear | Ground truth has no real concerns (Codex hit its limit, human just said 'lgtm'), so both reviews correctly land on approve/no-blocker verdicts and neither misses anything. But Y's cited line numbers ( |
| pr4825.r1 | opus_baseline | clear | The one substantive ground-truth concern (dsocek's push to generalize the fix, e.g. drive it from _packed_modules_mapping, instead of hardcoding another component name) is echoed by X's comment #1 urg |
| pr4825.r2 | opus_baseline | decisive | X surfaces two grounded, actionable design notes (derive the component list from each pipeline's already-declared `_dit_modules` instead of a fourth hardcoded list, and flags that text-encoder LoRA is |
| pr4825.r3 | opus_baseline | clear | X's core suggestion (drive component discovery from already-computed manager state like `_dit_modules` instead of a fourth hardcoded list) is thematically close to dsocek's real ask (drive naming from |
| pr4837.r1 | opus_baseline | slight | Both candidates independently verify the same core fact the ground-truth reviewer (yJader) explains inline — that both submit_initial and submit_update reject list-shaped diffusion prompts, so gating  |
| pr4837.r2 | opus_baseline | clear | The sole ground-truth concern (yJader's comment) explains that removing the `already_submitted` gate is safe because both `submit_initial` and `submit_update` reject list prompts identically for diffu |
| pr4837.r3 | copilot_v2 | slight | Both candidates independently arrive at the same core grounding as the human reviewer (submit_initial and submit_update both reject list prompts for diffusion, so dropping the already_submitted gate i |
| pr4893.r1 | copilot_v2 | slight | Neither candidate surfaces the one substantive ground-truth concern (yenuo26's question about verifying the reduce_scatter parameter in the test); X at least discusses the reduce_scatter mock logic in |
| pr4893.r2 | copilot_v2 | slight | Neither candidate caught the actual ground-truth concern (yenuo26's question about verifying the reduce_scatter parameter in test_expert_parallel_layout.py), so recall is low for both. X is thematical |
| pr4893.r3 | copilot_v2 | clear | Neither candidate directly surfaces the ground-truth ask (whether the reduce_scatter hasattr checks need deeper verification), but Y's broader test-coverage focus (untested world_size==1/None branches |
