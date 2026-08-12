# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)

Judge: claude-sonnet-5 (blind, randomized order, 3 replicates x 10 items = 60 verdicts)

## Wins
- copilot_v2: 4
- opus_baseline: 56
- tie: 0

## Mean rubric scores

| arm | actionability | gap_hit | precision | recall |
|---|---|---|---|---|
| copilot_v2 | 0.35 | 0.00 | 0.48 | 0.19 |
| opus_baseline | 0.81 | 0.19 | 0.84 | 0.58 |

## Per-verdict detail

| item.rep | winner | margin | rationale (head) |
|---|---|---|---|
| pr4762.r1 | opus_baseline | slight | X catches the one concrete, author-confirmed bug in the diff (trust_remote_code default flip from True to False in the config_factory refactor), which directly matches the inline GT comment on that ex |
| pr4762.r2 | opus_baseline | clear | Y independently surfaces the trust_remote_code default-flip (near-verbatim match to the ground-truth inline comment) and correctly validates that the deploy-override pipeline-resolution bug was fixed  |
| pr4762.r3 | opus_baseline | clear | Y surfaces the two concerns that actually mattered most to human reviewers — the trust_remote_code default flip (flagged as 'looks like a bug' inline) and the endpoint-restrictions-must-follow-final-p |
| pr4777.r1 | opus_baseline | decisive | Ground truth is essentially two LGTM approvals plus a manual verification comment confirming boundary validation, unit tests, and L4 regression passed — no substantive defects exist to recall. Candida |
| pr4777.r2 | opus_baseline | clear | Ground truth has no substantive concerns (just approvals plus a manual verification confirming layers=2 works end-to-end), so both candidates trivially achieve full recall and X's zero findings are te |
| pr4777.r3 | opus_baseline | clear | Ground truth has no substantive concerns (two LGTMs and a verification comment confirming the change works), so X's zero-finding review technically doesn't contradict it but adds no analytical value o |
| pr4804.r1 | copilot_v2 | clear | X independently reproduces the exact latent ceil/floor division bug ground truth flagged as 'Medium, latent' (audio_tokenizer_v2.py:947-949) plus the docstring default mismatches, both grounded with c |
| pr4804.r2 | copilot_v2 | clear | Y independently reproduces two confirmed ground-truth bugs with exact line matches (the audio_tokenizer_v2.py:949 ceil/floor division bug, and the configuration docstring defaults mismatch), each with |
| pr4804.r3 | copilot_v2 | clear | Y independently reproduces two confirmed ground-truth findings almost verbatim (the ceil/floor division bug at audio_tokenizer_v2.py:949, and the stale docstring defaults in configuration_moss_audio_t |
| pr4810.r1 | opus_baseline | decisive | X independently verifies the design against upstream vLLM source, echoes the ground truth's core assessment (mapper placement correct, qwen2_old getattr removal is cleanup not regression), raises a gr |
| pr4810.r2 | opus_baseline | decisive | Y verifies the fix against actual upstream vLLM source, echoes the ground truth's direct-vs-delegated-loader reasoning and its concern about the test only proving the mapper is 'called' rather than fu |
| pr4810.r3 | opus_baseline | decisive | Y independently verifies the design against the real upstream vLLM source (matching the human reviewer's core assessment about delegated vs direct loaders) and raises a sharper version of the human's  |
| pr4816.r1 | opus_baseline | decisive | Both candidates reach the same 'no blockers' conclusion that matches the ground truth's lgtm approval, but X substantiates it with concrete, diff-grounded verification (enumerates all 9 renamed sites, |
| pr4816.r2 | opus_baseline | decisive | Ground truth has no substantive concerns (empty inline comments, single 'lgtm' approval), so both trivially achieve full recall. Candidate X still delivers real value: it verifies the rename is applie |
| pr4816.r3 | opus_baseline | decisive | Ground truth has no substantive concerns (bot rate-limit notice + plain 'lgtm' approval), so both candidates trivially avoid missing anything. Candidate X actually engages with the diff: it correctly  |
| pr4817.r1 | opus_baseline | decisive | Ground truth has no substantive concerns (empty inline comments, only 'thanks'/Codex-limit noise), so recall is trivially satisfied by both. X does real, verifiable work grounded in the diff: it corre |
| pr4817.r2 | opus_baseline | decisive | Ground truth contains no substantive reviewer concerns to recall, so neither candidate misses anything. Candidate X does real verification work (confirms the >=10→==10 gate logic, checks rename consis |
| pr4817.r3 | opus_baseline | clear | Ground truth has no substantive reviewer concerns, so both trivially achieve full recall and X's zero-finding output is not 'wrong.' But X provides essentially no review substance (a bare 'no issues f |
| pr4825.r1 | opus_baseline | decisive | X delivers a substantive, line-grounded review that echoes the one real ground-truth concern (dsocek's point that this is a narrow hardcoded-list patch that should instead derive from a single source  |
| pr4825.r2 | opus_baseline | decisive | Ground truth is thin (mostly LGTM approvals, a validation-post request, and a partially-superseded suggestion about avoiding hardcoded naming/component lists). Candidate X delivers a substantive, diff |
| pr4825.r3 | opus_baseline | decisive | Candidate X's top comment (drive component discovery from a single source of truth instead of a hardcoded list) closely mirrors the one substantive ground-truth concern (dsocek's note about deriving f |
| pr4834.r1 | opus_baseline | decisive | X delivers a thorough, diff-grounded review that touches both ground-truth threads (the enum suggestion in finding #5, and test-coverage concerns in finding #2 responding to the regression-test ask) a |
| pr4834.r2 | opus_baseline | decisive | X substantively engages both real reviewer threads (test-coverage adequacy and the enum-for-tags request) by critiquing the quality of the fixes rather than just noting they exist, and independently s |
| pr4834.r3 | opus_baseline | decisive | X surfaces one accurate but trivial logging nitpick and misses both substantive ground-truth threads (the regression-test ask and the enum-extraction ask), while Y explicitly engages both (finding #2  |
| pr4837.r1 | opus_baseline | decisive | X independently re-derives the exact reasoning behind the ground-truth inline comment (both submit_initial and submit_update reject list prompts for diffusion, so already_submitted is redundant), veri |
| pr4837.r2 | opus_baseline | decisive | The only substantive ground-truth concern is yJader's inline comment explaining why the already_submitted gate should be dropped since both submit_initial and submit_update reject list prompts identic |
| pr4837.r3 | opus_baseline | decisive | The lone ground-truth inline comment explains why removing the `already_submitted` gate is safe (both submit_initial and submit_update reject list prompts for diffusion), and Candidate X independently |
| pr4849.r1 | opus_baseline | clear | The ground-truth's substantive concern is Gaohan123's question about whether source_outputs[0] is reliably the parent output and whether a check/comment is warranted. Candidate X explicitly investigat |
| pr4849.r2 | opus_baseline | clear | The central substantive ground-truth concern (whether source_outputs[0] is reliably the parent request) is directly investigated and resolved by Y via concrete orchestrator code references, while X ne |
| pr4849.r3 | copilot_v2 | slight | X finds two minor but genuinely grounded issues (unchecked ar_output.outputs[0] indexing, hardcoded 'Request 0' log) with concrete file/line suggested-diff fixes, but misses the reviewers' central con |
| pr4859.r1 | opus_baseline | decisive | X independently surfaces two of the three substantive concerns ground-truth reviewers raised (the audio_vae.py num_hidden_layers config-mutation issue, and the patch_emission.py min_stop_step+2 window |
| pr4859.r2 | opus_baseline | decisive | X independently surfaces the same core concern the ground-truth reviewer raised about audio_vae.py:141 (config.num_hidden_layers mutation affecting introspection), with nearly identical reasoning abou |
| pr4859.r3 | opus_baseline | clear | Y independently surfaces the audio_vae.py:141 config-mutation issue almost identically to amy-why-3459's real ground-truth comment, and separately flags the patch_emission.py stop-step tightening and  |
| pr4870.r1 | opus_baseline | decisive | X does real investigation grounded in the diff: confirms the qwen3_tts scoping fix and seq_len cleanup are correct, flags a genuine residual inconsistency in the getattr default (True vs the file's ow |
| pr4870.r2 | opus_baseline | decisive | Candidate X returned zero findings despite the diff containing verifiable, non-trivial content to check (already-applied qwen3_tts scoping, async_chunk default handling, seq_len removal), so it earns  |
| pr4870.r3 | opus_baseline | decisive | X returned zero findings, missing everything including the subtleties still live in the diff. Y did substantive grounded analysis: correctly traced is_streaming_request's scope, verified the seq_len r |
| pr4893.r1 | opus_baseline | decisive | X returned zero findings and thus contributes no recall, precision, or actionable content — it's a no-op review. Y engages substantively with the diff, correctly verifies several technical claims grou |
| pr4893.r2 | opus_baseline | clear | Ground truth is thin (one inline question about missing reduce_scatter test coverage, which the diff already added; otherwise just approvals/procedural chat), so neither candidate scores high recall.  |
| pr4893.r3 | opus_baseline | decisive | X performs genuine code-level analysis grounded in the diff (DPMetadata construction, init_vllm_model_parallel_group semantics, group separation, cleanup, the _DP condition change) and gives one concr |
| pr4923.r1 | opus_baseline | clear | X surfaces only one minor, unverifiable duplicate-assignment nit and misses every substantive theme from the human thread (the cudagraph_mode/modeling-boundary TODO, the seed-reproducibility consequen |
| pr4923.r2 | opus_baseline | decisive | X substantively engages the PR's core technical change: it validates the cudagraph_mode gating logic, explicitly flags the seed-reproducibility consequence for decode batch>1 (matching gcanlin's groun |
| pr4923.r3 | opus_baseline | decisive | Y engages the actual substantive review thread — it validates the TODO addressing gcanlin's/R2-Y's cudagraph_mode-in-modeling concern, explicitly flags the seed-reproducibility loss for decode batch>1 |
| pr4926.r1 | opus_baseline | decisive | X independently surfaces the same conceptual bug RuixiangMa flagged (varlen_func/attn_func may be None despite __init__ only requiring one, crashing piecewise/masked paths) and engages with the versio |
| pr4926.r2 | opus_baseline | decisive | X finds a real, still-present bug (masked/varlen paths call flash_attn_varlen_func unconditionally when only one of the two funcs is guaranteed non-None) that matches the same root-cause category Ruix |
| pr4926.r3 | opus_baseline | decisive | Y independently rediscovers RuixiangMa's confirmed real bug (varlen_func being None when only flash_attn_func is provided crashes masked/piecewise paths) almost verbatim, plus flags genuine, diff-grou |
| pr4950.r1 | opus_baseline | decisive | Ground truth contains no substantive concerns (just LGTM/approval), so the bar is whether a candidate produces grounded, useful analysis without fabricating issues. X performed no review at all (markd |
| pr4950.r2 | opus_baseline | decisive | Ground truth is trivial (all approvals, no substantive concerns), so the bar is really 'engage credibly and don't invent problems.' X does real work: it verifies every technical claim in the docs diff |
| pr4950.r3 | opus_baseline | decisive | Ground truth shows a trivial, uncontested docs PR (LGTM/approve, no inline concerns), so the bar is mainly 'did the reviewer verify correctness without fabricating issues.' X actually read the code, v |
| pr4954.r1 | opus_baseline | decisive | Y verifies the actual core fix (producer/consumer key match, no prefill regression) and raises a non-blocking point that substantively overlaps the human reviewer's key concern — that the new containm |
| pr4954.r2 | opus_baseline | slight | Neither candidate hits the two specific ground-truth nitpicks (stale docstring wording, legacy-vs-nested check order), so recall is 0 for both. Both candidates' findings are valid and diff-grounded (p |
| pr4954.r3 | opus_baseline | clear | X's non-blocking comment about the containment fallback applying unconditionally to all callers substantively overlaps with the reviewer's actual concern (that the docstring's old 'strict behaviour pr |
| pr4970.r1 | opus_baseline | clear | Ground truth for this trivial seed-removal PR is essentially 'LGTM' with no substantive concerns, so neither candidate missed real issues (recall is near-vacuous for both). X returns a bare zero-findi |
| pr4970.r2 | opus_baseline | decisive | Ground truth has essentially no substantive concerns (just an LGTM approval and an unrelated request to split off a VoxCPM2 fix), so neither candidate misses much, but Y earns its 'approve' conclusion |
| pr4970.r3 | opus_baseline | decisive | Ground truth has no substantive concerns (just an unrelated VoxCPM2 ask and an LGTM approval), so there's little to recall for either candidate. X does a genuine, code-grounded investigation confirmin |
| pr4977.r1 | opus_baseline | decisive | X returned zero findings, missing the sole ground-truth concern (trust_remote_code/kernels-version compatibility) entirely and offering nothing actionable. Y produced a diff-grounded review that corre |
| pr4977.r2 | opus_baseline | decisive | Candidate X performed a substantive, grounded review: it correctly verified the fallback-order and cache-safety semantics, flagged a real (if minor) lock-contention point, and independently surfaced a |
| pr4977.r3 | opus_baseline | decisive | X returned zero findings, missing the only ground-truth concern (trust_remote_code/kernels version compatibility) entirely and offering nothing actionable. Y actually engaged with that exact area of t |
| pr5009.r1 | opus_baseline | decisive | X delivers a deeply grounded review with accurate line references and even reproduces exact PR metrics (26.9%/14.1% latency figures) matching the real discussion, substantively covering the UT-added,  |
| pr5009.r2 | opus_baseline | decisive | X returned zero findings, missing every ground-truth concern (scope of the global default change, missing regression coverage for the #4964 inductor case, incomplete pytest mark, perf/accuracy compari |
| pr5009.r3 | opus_baseline | decisive | X is a zero-finding OCR pass that surfaces nothing from the ground truth (missing the scope concern, test-coverage gaps, and regression-test rationale entirely), so it offers no recall or actionable v |
