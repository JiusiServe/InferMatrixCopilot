# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)

Judge: claude-sonnet-5 (blind, randomized order, 3 replicates x 10 items = 60 verdicts)

## Wins
- copilot_v2: 22
- opus_baseline: 36
- tie: 2

## Mean rubric scores

| arm | actionability | gap_hit | precision | recall |
|---|---|---|---|---|
| copilot_v2 | 0.75 | 0.09 | 0.78 | 0.42 |
| opus_baseline | 0.76 | 0.15 | 0.80 | 0.51 |

## Per-verdict detail

| item.rep | winner | margin | rationale (head) |
|---|---|---|---|
| pr4762.r1 | opus_baseline | slight | Both candidates independently rediscover the two GT threads visible in the diff (the trust_remote_code default flip True→False, and the deploy-config-override pipeline precedence fix), and both explic |
| pr4762.r2 | opus_baseline | clear | Y recalls the two most significant author-confirmed bugs from the human thread — the trust_remote_code default flip and the endpoint-restrictions-resolved-from-wrong-pipeline issue (correctly noting t |
| pr4762.r3 | opus_baseline | clear | X makes a factual error claiming no CPU-level test exists for endpoint restrictions and asking to add one to tests/config/test_endpoint_policy.py, when that exact file with exactly those CPU tests is  |
| pr4777.r1 | copilot_v2 | clear | Ground truth shows a clean, unanimous approval with no substantive concerns, so recall is vacuously satisfied by both. X's central 'blocking' findings (three stale reliability tests in files entirely  |
| pr4777.r2 | copilot_v2 | clear | Both correctly validate the core range-boundary change (dynamic error message, consistent 2-10 across protocol/util/tests). X stays grounded strictly in the diff, offering one defensible, low-risk nit |
| pr4777.r3 | opus_baseline | clear | Ground truth is essentially content-free (LGTM approvals plus a bot verification comment), so neither candidate had real concerns to recall. X's only finding is a valid but trivial nit (missing ge/le  |
| pr4804.r1 | opus_baseline | clear | Y independently investigated and refuted X's headline 'major' finding (put_req_chunk never incremented), citing a framework-managed counter pattern shared with sibling processors — a strong signal X's |
| pr4804.r2 | copilot_v2 | clear | Y's findings are concrete, line-anchored, and evidence-backed (e.g. the serving_speech.py:3714 finding that the qwen3_tts guard was removed making tts_local_seed apply unconditionally is independently |
| pr4804.r3 | copilot_v2 | clear | X confidently asserts two things that ground truth directly contradicts: it claims the stream-slot leak on abort is 'handled' when linyueqian's confirmed High-severity finding (fixed by the author) sa |
| pr4810.r1 | copilot_v2 | slight | Both candidates independently rediscover the exact latent gap (hunyuan_image3_transformer.py:2238 still calling the removed get_cache_scale API), and both confirm the core design correctness the human |
| pr4810.r2 | opus_baseline | slight | Both candidates independently surfaced the key latent gap — the unswept get_cache_scale call in hunyuan_image3_transformer.py — with concrete file/line evidence, matching the LATENT GAP CHECK. Y goes  |
| pr4810.r3 | opus_baseline | clear | Both correctly validate the direct-vs-delegated loader design and both flag the same latent gap (the still-unfixed diffusion-stage hunyuan_image3_transformer.py caller of the removed API), so gap_hit  |
| pr4816.r1 | copilot_v2 | clear | Ground truth offers no substantive concerns (just an 'lgtm' approval), so both candidates correctly reach APPROVE and recall is near-full for both. Precision separates them: cross-checking cited line  |
| pr4816.r2 | copilot_v2 | clear | Ground truth has no substantive concerns (just an approve), so both candidates correctly land on APPROVE with equal recall. But X cites specific test-file line numbers (2638, 2651, 2720) that don't ma |
| pr4816.r3 | copilot_v2 | clear | Both correctly approve with no blockers, matching the ground truth 'lgtm' with no substantive concerns, so recall is trivially satisfied for both. However, X cites specific line numbers for the update |
| pr4817.r1 | copilot_v2 | slight | Ground truth has no substantive reviewer concerns (bot noise + 'thanks'), so both candidates are judged on diff-grounded quality alone. Both correctly verify the core fix (>=10 → ==10 excludes sm_120/ |
| pr4817.r2 | copilot_v2 | slight | Ground truth has no substantive reviewer concerns (just a 'thanks' comment and bot spam), so both candidates trivially achieve full recall. Both give accurate, diff-grounded technical assessments and  |
| pr4817.r3 | tie | slight | Ground truth has no substantive concerns to recall, so both trivially satisfy recall by correctly finding no blockers. Both independently converge on the same legitimate nit (the ==10 gate excluding h |
| pr4825.r1 | opus_baseline | clear | Neither candidate hits the ground truth's actual substantive concern (dsocek's naming-conflict/_packed_modules_mapping comment, which appears tied to a part of the PR later removed per tthakkal's repl |
| pr4825.r2 | opus_baseline | clear | X's suggestion to derive the component list from a single source of truth (echoing dsocek's actual review comment about generalizing the PEFT-name mapping instead of hardcoding) gives it meaningful re |
| pr4825.r3 | opus_baseline | clear | The one substantive reviewer concern in the ground truth (dsocek's suggestion to derive the component/naming list from an existing declarative source like _packed_modules_mapping rather than hand-main |
| pr4834.r1 | opus_baseline | clear | Both candidates independently surface the latent gap (X via the default level=2 + hardware-gated-tests-never-run-in-CI angle, Y via the docs example that would now fail), so gap_hit is true for both,  |
| pr4834.r2 | opus_baseline | clear | Both reviews are well-grounded with specific file:line evidence, but X's Major finding (default sleep(level=2) plus the new hard NotImplementedError permanently bricks wake_up/generate) directly fores |
| pr4834.r3 | opus_baseline | clear | Both reviews are grounded and actionable with concrete file/line suggestions, but Y engages more directly with the GT's own concerns (critiques the half-used CuMemTag enum, flags that the new hardware |
| pr4837.r1 | opus_baseline | clear | X's core analysis of orchestrator.py:1290 independently verifies (via stage_pool.py:951/1022) that both submit_initial and submit_update reject list prompts, which is almost exactly the crux of yJader |
| pr4837.r2 | opus_baseline | clear | The only substantive ground-truth signal is yJader's inline comment explaining that already_submitted-gating is unnecessary because both submit_initial and submit_update reject list prompts identicall |
| pr4837.r3 | opus_baseline | clear | The only substantive ground-truth concern (yJader's note that already_submitted shouldn't gate the diffusion singleton-list unwrap since both submit paths funnel into the same DiffusionEngine call) is |
| pr4849.r1 | opus_baseline | slight | Both candidates independently verify the parent-first ordering assumption that Gaohan123 flagged inline, but neither raises Bounty-hunter's specific ask to re-run the diffusion benchmark script. X add |
| pr4849.r2 | opus_baseline | slight | Both candidates independently verified the exact question the human reviewer raised (is source_outputs[0] really the parent?) but neither recommended the actual requested action (add a check/comment), |
| pr4849.r3 | tie | slight | Both largely miss the GT's actual concerns (the parent-prompt-ordering question was already resolved in-diff via the docstring both candidates independently re-verify, and neither flags the requested  |
| pr4859.r1 | copilot_v2 | clear | Both correctly flag the audio_vae.py config-mutation issue (GT's amy-why-3459/LHXuuu thread) and the patch_emission.py +1→+2 window-validation change (GT's LHXuuu thread), with solid grounding and con |
| pr4859.r2 | copilot_v2 | clear | Both candidates independently caught the audio_vae.py:141 shared-config mutation bug, which matches GT's most substantive inline finding (amy-why-3459), with Y giving a slightly more precise fix (copy |
| pr4859.r3 | copilot_v2 | clear | Both candidates independently flag the audio_vae.py:141 config-mutation issue that reviewer amy-why-3459 raised, but only X also flags the dropped-language-field concern in serving_speech.py:2655 (ask |
| pr4870.r1 | opus_baseline | slight | Both candidates correctly verified the runner fix's root cause and the streaming FINAL_ONLY scoping (matching the reviewer's main validated points), and both independently flagged the same async_chunk |
| pr4870.r2 | opus_baseline | slight | Both candidates independently find the same valid async_chunk default (True vs False) inconsistency and correctly validate that the seq_len nit was already fixed and the streaming scoping was already  |
| pr4870.r3 | opus_baseline | clear | Both candidates correctly validate the already-fixed qwen3_tts scoping and independently rediscover the same async_chunk default-value inconsistency (True vs False) that echoes the ground-truth Low co |
| pr4893.r1 | copilot_v2 | clear | The one substantive GT concern (yenuo26 questioning whether reduce_scatter verification was added to the test) is explicitly engaged by X, which calls out those exact assertions (lines 121-126) in its |
| pr4893.r2 | copilot_v2 | slight | Ground truth is thin (mostly non-technical thread plus one inline comment about verifying the reduce_scatter assertions in the layout test, which the diff already addresses). X explicitly calls out an |
| pr4893.r3 | copilot_v2 | slight | Ground truth is thin and mostly social (blurred-image question, LGTM, a startup-success confirmation) plus one inline ask about whether the test's reduce_scatter hasattr checks are sufficient; neither |
| pr4923.r1 | opus_baseline | clear | Ground truth centers on three real reviewer concerns: the design debate over reading cudagraph_mode in modeling vs. the runner (gcanlin/R2-Y), the TODO documenting that mtp seed reproducibility breaks |
| pr4923.r2 | opus_baseline | slight | Ground-truth concerns center on: whether the model should read cudagraph_mode (architecture placement), the TODO needing to flag mtp-seed non-reproducibility under batch>1, an NPU compilation_config f |
| pr4923.r3 | opus_baseline | clear | Y identifies the seeding-reproducibility tradeoff under full cudagraphs (mirroring gcanlin's central inline concern about mtp seed failing at decode batch>1) and questions the NPU stage-1 PIECEWISE sc |
| pr4926.r1 | opus_baseline | clear | X independently surfaces the same crash-risk theme the human reviewer (RuixiangMa) raised about `flash_attn_varlen_func`/`flash_attn_func` being allowed to be None while downstream paths call one unco |
| pr4926.r2 | opus_baseline | slight | X caught the one substantive bug ground truth reviewers flagged and got fixed — the piecewise_attn/None-attn_func crash when only one of flash_attn_func/flash_attn_varlen_func is present (RuixiangMa's |
| pr4926.r3 | copilot_v2 | slight | Both largely miss the ground-truth's core threads because most GT comments (SM90 gating, try/except-swallowing tests, hardware markers) were already fixed by the time of this diff; Y partially compens |
| pr4950.r1 | opus_baseline | slight | Ground truth shows no substantive reviewer concerns (just LGTM approvals), so both candidates trivially satisfy recall. Y did more rigorous, precisely-cited code verification (exact line ranges like s |
| pr4950.r2 | copilot_v2 | slight | Ground truth has no substantive concerns (just LGTM/approvals), so both trivially cover it and neither fabricates anything obviously wrong — both verify the PR's core claims against source with specif |
| pr4950.r3 | copilot_v2 | slight | Both candidates thoroughly verify the diff's technical claims against source with specific file:line citations and reach the same correct 'no blockers, approve/comment' conclusion consistent with the  |
| pr4954.r1 | opus_baseline | slight | Neither candidate recovers GT's two actual concerns (stale docstring wording, confirming a live producer for the legacy `audio` key) with any precision, but Y's finding that the containment fallback i |
| pr4954.r2 | opus_baseline | clear | GT's core concern is that the containment-fallback docstring/comment at L644-657 now misdescribes behavior since the fallback applies to all callers, not just opt-in escalation tests. X independently  |
| pr4954.r3 | opus_baseline | clear | Both candidates correctly validate the core codes.audio fix and produce grounded, non-fabricated findings, but X's top non-blocking comment ('containment fallback now applies to all speech tests, not  |
| pr4970.r1 | opus_baseline | clear | Ground truth is sparse (LGTM approval plus an unrelated aside about a separate VoxCPM2 regression PR); neither candidate addresses that aside, so recall is low and tied. Both correctly trace the seed→ |
| pr4970.r2 | opus_baseline | clear | Both candidates did genuine, grounded mechanism tracing (serving_speech.py propagation → gpu_model_runner.py consumption) and neither surfaces the one real GT concern (spinning off the VoxCPM2 regress |
| pr4970.r3 | opus_baseline | clear | Neither candidate surfaces the one real GT concern (the VoxCPM2 regression follow-up), so recall is essentially zero for both against this sparse GT. X's technical diagnosis is specific and well-groun |
| pr4977.r1 | copilot_v2 | slight | Both candidates spot the same core discrepancy the ground-truth reviewer flagged (trust_remote_code mentioned in the PR description but not reflected in the code), though neither reproduces the ground |
| pr4977.r2 | copilot_v2 | slight | Both candidates independently caught the same discrepancy underlying the ground-truth concern — the PR description's trust_remote_code=True claim doesn't appear in the diff — but neither surfaced the  |
| pr4977.r3 | copilot_v2 | clear | Neither candidate surfaces the GT's actual concern (kernels<0.15 lacking a lower bound so trust_remote_code would break on 0.13.x), but both notice the adjacent description/diff mismatch around trust_ |
| pr5009.r1 | opus_baseline | clear | Both candidates verify the Cosmos3 override argument for the scope concern, but X goes further and cites the FLUX.1-dev -14.1% latency figure that matches the GT resolution almost exactly, showing it  |
| pr5009.r2 | opus_baseline | clear | Y engages the two substantive GT threads that X misses entirely: the global-scope risk of making vllm_c default for every CUDA diffusion model (GT's line-252 concern), and it cites perf/accuracy numbe |
| pr5009.r3 | opus_baseline | decisive | The dominant ground-truth concern (raised twice by hsliuustc0106 and answered by the author with FLUX.1-dev A/B numbers) is that the platform-wide default change was validated only on Qwen-Image but a |
