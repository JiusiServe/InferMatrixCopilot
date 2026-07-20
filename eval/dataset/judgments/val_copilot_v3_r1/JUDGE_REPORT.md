# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)

Judge: claude-sonnet-5 (blind, randomized order, 3 replicates x 10 items = 30 verdicts)

## Wins
- copilot_v2: 11
- opus_baseline: 19
- tie: 0

## Mean rubric scores

| arm | actionability | completeness | correctness | gap_hit | grounding | precision | recall |
|---|---|---|---|---|---|---|---|
| copilot_v2 | 0.80 | 0.72 | 0.73 | 0.21 | 0.68 | 0.76 | 0.51 |
| opus_baseline | 0.73 | 0.81 | 0.77 | 0.21 | 0.71 | 0.83 | 0.54 |

## Per-verdict detail

| item.rep | winner | margin | rationale (head) |
|---|---|---|---|
| issue4793.r1 | opus_baseline | clear | Both correctly identify the root cause (PR #4527's None,payload split starving the downstream stage) and the fix (PR #4792, already folded into the 0.24 rebase commit a560ed18), matching the thread's  |
| issue4793.r2 | opus_baseline | slight | Both correctly diagnose the #4527 regression (None inter-stage payload starving the full-payload consumer) and correctly identify PR #4792 as the merged fix already folded into the 0.24 rebase commit, |
| issue4793.r3 | opus_baseline | slight | Both candidates correctly identify the same root cause (PR #4527 regression), the same fix (PR #4792, already folded into the 0.24 rebase commit a560ed18), and the same async_chunk:true workaround, ma |
| issue4827.r1 | opus_baseline | slight | Both correctly diagnose the config/topology mismatch (base tokenizer lacking <img_ratio_33..36>) and recommend the same confirmed workaround (hunyuan_image3_dit.yaml), matching the thread exactly. Y g |
| issue4827.r2 | opus_baseline | clear | Both correctly diagnose the None+1 TypeError from the base tokenizer lacking extended ratio tokens and recommend the same dit.yaml workaround the thread confirms, but X goes further to explain *why* t |
| issue4827.r3 | opus_baseline | slight | Both candidates correctly diagnose the None+1 TypeError from the base tokenizer lacking extended ratio tokens and give the exact workaround (hunyuan_image3_dit.yaml) that FayeSpica confirmed in the th |
| issue4842.r1 | copilot_v2 | slight | Both correctly diagnose the root cause (default --run-level=core_model injects load_format:dummy via #4354, producing garbage output on a full_model-only assertion) and give the correct fix (--run-lev |
| issue4842.r2 | opus_baseline | slight | Both correctly identify the root cause (default --run-level=core_model injecting load_format: dummy per #4354, fixed by --run-level=full_model) matching the thread's resolution. Y aligns more precisel |
| issue4842.r3 | opus_baseline | slight | Both correctly diagnose the root cause as a run-level mismatch (core_model dummy-weight injection via _add_dummy_load_format, extended to online serving by PR #4354) and give the identical fix (--run- |
| issue4891.r1 | opus_baseline | clear | Both correctly diagnose the missed get_cache_scale call and land on the right disposition (duplicate of #4808), matching the ground truth. But X asserts as fact that '#4808's fix is already in the cod |
| issue4891.r2 | opus_baseline | clear | Both land on the correct disposition (duplicate of #4808) and diagnose the same root cause, but Y's narrative about #4809 tracking 5 call sites with #4810 fixing 4 and #4808 covering the 5th is a much |
| issue4891.r3 | copilot_v2 | slight | Both correctly land on the actual disposition (duplicate of #4808) and cite the same plausible code anchors (line 2238 crash, maybe_remap_kv_scale_name at 2343). X adds an unverified, unhedged-enough  |
| issue4905.r1 | copilot_v2 | slight | The actual thread shows the issue still in triage (yenuo26 pointing at #4834, Flink-ddd asking for a full CI sleep-mode run) — no confirmed fix or closure. Both candidates overreach by confidently dec |
| issue4905.r2 | copilot_v2 | slight | Both reach the same plausible technical diagnosis (PR #4834's intentional NotImplementedError guard vs. a stale test still calling sleep(level=2)+wake_up), but the actual thread shows this is unresolv |
| issue4905.r3 | copilot_v2 | slight | Both candidates correctly tie the failure to PR #4834's new NotImplementedError guard (matching yenuo26's thread comment), but both then confidently assert the issue is already fixed on main and shoul |
| pr4810.r1 | copilot_v2 | slight | Both correctly validate the core delegated-vs-direct loader design split and independently surface the key latent gap — the untouched hunyuan_image3_transformer.py diffusion loader still calling the r |
| pr4810.r2 | copilot_v2 | clear | Both candidates independently surface the latent gap (the untouched hunyuan_image3_transformer.py diffusion loader still calling the removed get_cache_scale API), but X classifies it correctly as a ma |
| pr4810.r3 | opus_baseline | slight | Both correctly validate the core loader changes (direct loaders apply the mapper, delegated loaders correctly rely on the outer AutoWeightsLoader) and both independently catch the latent gap — hunyuan |
| pr4816.r1 | opus_baseline | slight | Ground truth has no substantive concerns (just an 'lgtm' approval), so both candidates correctly approve with no blockers and both achieve full recall vacuously. Both are well-grounded, citing accurat |
| pr4816.r2 | opus_baseline | slight | Ground truth offers nothing substantive (just an 'lgtm' approve, no inline comments), and both candidates correctly reach APPROVE with well-grounded, diff-consistent explanations of the rename and its |
| pr4816.r3 | copilot_v2 | slight | Ground truth has no substantive concerns (just an 'lgtm' approval), so both candidates trivially achieve full recall and correctly reach APPROVE. Both correctly diagnose the rename's purpose (matching |
| pr4825.r1 | opus_baseline | slight | Neither candidate surfaces dsocek's core ground-truth concern (unify naming-conflict handling with _packed_modules_mapping/stacked_params_mapping), but X's suggestion to derive default_components from |
| pr4825.r2 | opus_baseline | slight | Ground truth's only substantive concern (dsocek's suggestion to derive naming/component matching from existing declarative data like _packed_modules_mapping rather than hardcoded lists) is echoed more |
| pr4825.r3 | opus_baseline | slight | Neither candidate hits the ground truth's core substantive point (dsocek's suggestion to derive LoRA target discovery from `_packed_modules_mapping`/`stacked_params_mapping` to handle PEFT fused-proje |
| pr4837.r1 | opus_baseline | clear | X's key claim ('both submit_initial and submit_update raise ValueError on a list for diffusion stages') is essentially the exact reasoning yJader gave for why gating the unwrap on already_submitted wa |
| pr4837.r2 | opus_baseline | clear | Y independently verifies the exact mechanism the ground-truth inline comment relies on (both submit_initial and submit_update reject list prompts in StagePool), correctly concludes the fix is safe/com |
| pr4837.r3 | opus_baseline | clear | X's core claim — that both submit_initial and submit_update reject list prompts identically, so gating the unwrap on already_submitted was never semantically justified — is essentially the exact reaso |
| pr4893.r1 | copilot_v2 | slight | Neither candidate surfaces the one substantive ground-truth concern (yenuo26's point that the reduce_scatter test only checks hasattr, not real parameter behavior), so recall is near-zero for both, th |
| pr4893.r2 | copilot_v2 | slight | Neither candidate surfaces the one substantive ground-truth concern (yenuo26's question about whether reduce_scatter test verification at test_expert_parallel_layout.py:121 is sufficient), so recall i |
| pr4893.r3 | copilot_v2 | slight | Ground truth is thin (mostly LGTM/approve plus one narrow inline ask about verifying reduce_scatter behavior in test_expert_parallel_layout.py, unrelated to hunyuan_fused_moe.py); neither candidate hi |
