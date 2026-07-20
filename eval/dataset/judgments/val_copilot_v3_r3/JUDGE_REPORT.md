# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)

Judge: claude-sonnet-5 (blind, randomized order, 3 replicates x 10 items = 30 verdicts)

## Wins
- copilot_v2: 10
- opus_baseline: 20
- tie: 0

## Mean rubric scores

| arm | actionability | completeness | correctness | gap_hit | grounding | precision | recall |
|---|---|---|---|---|---|---|---|
| copilot_v2 | 0.70 | 0.69 | 0.68 | 0.20 | 0.63 | 0.81 | 0.54 |
| opus_baseline | 0.74 | 0.80 | 0.79 | 0.20 | 0.78 | 0.84 | 0.62 |

## Per-verdict detail

| item.rep | winner | margin | rationale (head) |
|---|---|---|---|
| issue4793.r1 | opus_baseline | clear | Both correctly land on PR #4792 (null inter-stage payload starving the downstream stage) and correctly recommend closing with async_chunk:true as workaround, matching the thread. Y is more tightly gro |
| issue4793.r2 | opus_baseline | slight | Both correctly identify the same root cause (non-async-chunk branch shipping (None, payload) instead of the full payload, starving the downstream stage) and the same fix/PR #4792/0.24-rebase resolutio |
| issue4793.r3 | opus_baseline | slight | Both correctly identify PR #4792 as the fix for the non-async-chunk branch shipping (None, payload) instead of the full payload, matching the ground truth's diff and confirming it's already folded int |
| issue4827.r1 | opus_baseline | clear | Both correctly diagnose the None+1 TypeError from missing extended ratio tokens and give the same confirmed workaround, but X recommends 'keep-open' while the actual thread shows Gaohan123 directing t |
| issue4827.r2 | opus_baseline | slight | Both correctly diagnose the None+1 TypeError from the base tokenizer lacking extended ratio tokens, cite the same Tencent reference, and give the confirmed hunyuan_image3_dit.yaml workaround plus a se |
| issue4827.r3 | opus_baseline | clear | Both correctly diagnose the same root cause (missing extended ratio tokens in the base tokenizer, hunyuan_image3.py:1561-1563) and give the identical confirmed workaround, matching the thread closely. |
| issue4842.r1 | opus_baseline | clear | Both correctly diagnose the ground-truth root cause (default --run-level=core_model forces dummy weights via _add_dummy_load_format, unrelated to the full_model pytest marker) and prescribe the same f |
| issue4842.r2 | opus_baseline | slight | Both correctly diagnose the issue as user error (default --run-level=core_model patches all stages to load_format:dummy) rather than a real bug, matching the thread's 'invalid' resolution, and both ci |
| issue4842.r3 | opus_baseline | clear | Both correctly diagnose the same root cause as the thread (default core_model run-level forces load_format:dummy, extended to online serving by #4354; not a real bug, closed invalid) and give the corr |
| issue4891.r1 | opus_baseline | clear | Both correctly identify the missed diffusion-side call site and that #4810 only covered the AR loaders, matching the thread's 'duplicate of #4808' resolution. But X confidently asserts the fix 'is alr |
| issue4891.r2 | opus_baseline | clear | Both correctly diagnose the diffusion-side get_cache_scale call site as the missed 5th spot from #4810 and correctly recommend closing as duplicate, matching the thread's actual resolution. X confiden |
| issue4891.r3 | opus_baseline | clear | Both correctly land on the ground-truth disposition (duplicate of #4808/#4809) and give a grounded, correct technical fix. The key split: X notices #4808 is CLOSED with mergedAt null and honestly flag |
| issue4905.r1 | copilot_v2 | slight | The actual thread never confirms a fix — it's an open bisection to #4834 followed by a request to trigger a dedicated CI run, not a resolved test-parameter bug. Both candidates correctly tie the failu |
| issue4905.r2 | opus_baseline | slight | Both correctly identify the core established fact (PR #4834 intentionally made wake_up() raise after sleep(level=2), and the pre-existing test wasn't updated), matching yenuo26's thread comment. Both  |
| issue4905.r3 | copilot_v2 | slight | Both correctly flag PR #4834 as the likely trigger (matching yenuo26's comment) and propose a plausible level=2→level=1 test fix, but the actual thread shows the issue is unresolved — Flink-ddd (the a |
| pr4810.r1 | copilot_v2 | slight | Both candidates independently rediscover the latent gap (the unswept hunyuan_image3_transformer.py DiT caller), but Y treats it as a live blocker with concrete remediation options while X frames it as |
| pr4810.r2 | copilot_v2 | slight | Both candidates catch the key latent gap (the diffusion transformer's leftover get_cache_scale call), satisfying gap_hit for each. X frames it correctly as a blocker with a concrete grep-verified fix  |
| pr4810.r3 | opus_baseline | clear | Both correctly surface the missed diffusion-transformer caller of get_cache_scale, hitting the latent gap. Y grounds its analysis in actual upstream vLLM source (exact file:line citations in utils.py/ |
| pr4816.r1 | copilot_v2 | slight | Ground truth has no substantive concerns (just an approval), so both correctly reach APPROVE with no missed issues. Y is more rigorously grounded: its file:line citations for all 9 renamed occurrences |
| pr4816.r2 | copilot_v2 | slight | Ground truth has no substantive concerns (just LGTM), so both candidates correctly approve and 'recall' is vacuously satisfied. Both did diff-grounded grep verification, but Y's specific line-number c |
| pr4816.r3 | copilot_v2 | slight | Both reviews correctly approve, thoroughly verify the rename is complete via grep, and trace the call chain through _create_speech_error_json_response/base() to the upstream attribute name; ground tru |
| pr4825.r1 | opus_baseline | clear | X's suggestion to derive default_components from the pipeline's existing _dit_modules metadata closely mirrors dsocek's ground-truth concern about driving the mapping from _packed_modules_mapping inst |
| pr4825.r2 | opus_baseline | clear | The only substantive ground-truth concern (dsocek's point that the hardcoded default_components list is fragile and should instead be driven from existing per-model mapping data) is echoed by X's comm |
| pr4825.r3 | opus_baseline | clear | X's comment on reusing pipeline._dit_modules instead of a fourth hardcoded component list echoes the spirit of dsocek's ground-truth concern about driving matching from existing per-pipeline metadata  |
| pr4837.r1 | opus_baseline | slight | Both candidates independently verify the same core fact ground truth cares about (submit_initial and submit_update both reject list prompts, so dropping the already_submitted gate is correct) and both |
| pr4837.r2 | opus_baseline | slight | Both candidates converge on the same core conclusion the ground-truth inline comment makes (removing already_submitted is correct because both submit paths reject list prompts), but Y grounds it more  |
| pr4837.r3 | opus_baseline | clear | Both candidates independently reconstruct the one substantive ground-truth concern (already_submitted removal is safe because both submit_initial/submit_update reject list prompts for diffusion), so r |
| pr4893.r1 | copilot_v2 | slight | Neither candidate surfaces the one substantive ground-truth concern (yenuo26's question about verifying reduce_scatter behavior beyond hasattr) — X even explicitly marks that exact test code as 'valid |
| pr4893.r2 | copilot_v2 | slight | Neither candidate hits the one substantive ground-truth concern (whether hasattr-only checks for reduce_scatter are sufficient verification), so recall is low for both. X engages more with test-covera |
| pr4893.r3 | copilot_v2 | slight | Ground truth here is thin (mostly an LGTM/approval plus one inline nit asking whether reduce_scatter test coverage needs strengthening); neither candidate directly hits that specific ask, so recall is |
