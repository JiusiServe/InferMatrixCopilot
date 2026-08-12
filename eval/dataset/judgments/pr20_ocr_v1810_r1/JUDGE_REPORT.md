# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)

Judge: claude-sonnet-5 (blind, randomized order, 3 replicates x 10 items = 60 verdicts)

## Wins
- copilot_v2: 3
- opus_baseline: 57
- tie: 0

## Mean rubric scores

| arm | actionability | gap_hit | precision | recall |
|---|---|---|---|---|
| copilot_v2 | 0.27 | 0.00 | 0.42 | 0.24 |
| opus_baseline | 0.82 | 0.18 | 0.83 | 0.60 |

## Per-verdict detail

| item.rep | winner | margin | rationale (head) |
|---|---|---|---|
| pr4762.r1 | opus_baseline | decisive | X delivers a substantive, code-grounded review that catches the trust_remote_code default-flip bug (matching the author's own inline admission), correctly confirms the deploy-override pipeline resolut |
| pr4762.r2 | opus_baseline | decisive | X reported zero findings despite a diff with real, discussed issues (trust_remote_code default flip, hf_config caching risk, pipeline-resolution ordering), so it contributes nothing. Y did substantive |
| pr4762.r3 | opus_baseline | decisive | X returned zero findings, contributing no recall, precision, or actionable content whatsoever. Y engaged substantively with the diff, correctly flagged the intentional trust_remote_code default flip ( |
| pr4777.r1 | opus_baseline | decisive | Ground truth for this PR contains no substantive concerns (just LGTM approvals and a verification comment confirming the change works), so recall is trivially satisfied by both. Candidate X does thoro |
| pr4777.r2 | opus_baseline | decisive | Ground truth is essentially an unqualified LGTM with a verification comment confirming boundary validation, unit tests, and L4 regression all passed — X's zero-finding output trivially matches that su |
| pr4777.r3 | opus_baseline | clear | Ground truth shows no substantive reviewer concerns (just LGTM approvals and a bot verification confirming the fix works), so both candidates trivially achieve full recall. Candidate X reports zero fi |
| pr4804.r1 | copilot_v2 | clear | X independently found the exact latent bug a human reviewer flagged (ceil-vs-floor division at audio_tokenizer_v2.py:949, matching file/line/reasoning) plus the docstring-defaults mismatch also raised |
| pr4804.r2 | copilot_v2 | clear | Y independently rediscovers two of the ground truth's most specific findings almost verbatim: the ceil-vs-floor division latent bug at audio_tokenizer_v2.py:949 (linyueqian's exact line and fix) and t |
| pr4804.r3 | copilot_v2 | clear | Y independently reproduces two of the ground truth's most substantive findings almost verbatim: the audio_tokenizer_v2.py:949 ceil-vs-floor division latent bug (linyueqian's exact concern, same fix) a |
| pr4810.r1 | opus_baseline | decisive | X independently re-derives nearly every point the human reviewer made (design correctness of the split between delegated/direct loaders, the weakness of the fake-param test not proving real checkpoint |
| pr4810.r2 | opus_baseline | decisive | Y independently re-derives the ground truth's core technical claim (delegated vs. direct loaders and why removing the manual branch is safe), verifies it against the actual upstream vLLM source with f |
| pr4810.r3 | opus_baseline | decisive | Y independently verifies the fix against the actual upstream vLLM source, echoes the human reviewers' core correctness assessment, raises a test-coverage critique that overlaps with the human's 'fake  |
| pr4816.r1 | opus_baseline | clear | Ground truth has no substantive concerns (empty inline comments, just an 'lgtm' approval), so both candidates trivially achieve full recall by reaching the correct APPROVE verdict. Candidate X gives a |
| pr4816.r2 | opus_baseline | decisive | Ground truth has no substantive concerns (just an LGTM), so both candidates correctly land on approve, but X demonstrates real grounded verification — greping for leftover occurrences, cross-checking  |
| pr4816.r3 | opus_baseline | clear | Ground truth has no substantive concerns (Codex hit usage limits, human reviewer just said 'lgtm'), so both trivially achieve full recall with nothing to miss. Candidate X does real, grounded verifica |
| pr4817.r1 | opus_baseline | decisive | Ground truth contains no substantive reviewer concerns, so recall is trivially satisfied by both. Candidate X gives a thorough, technically accurate walkthrough grounded in the diff (correctly explain |
| pr4817.r2 | opus_baseline | decisive | Ground truth has no substantive reviewer concerns, so recall is trivially satisfied by both. Candidate X delivers a grounded, accurate review (correctly explains the >=10→==10 fix, verifies the rename |
| pr4817.r3 | opus_baseline | clear | Ground truth has no substantive reviewer concerns (just 'thanks'/'.' and bot noise), so neither candidate misses anything real, giving both full recall. X returns zero findings with no evidence of ver |
| pr4825.r1 | opus_baseline | decisive | X independently surfaces essentially the same substantive concern as the ground-truth inline comment (dsocek's point about hardcoded component lists vs. driving discovery from existing mapping/declara |
| pr4825.r2 | opus_baseline | decisive | Candidate X engages substantively with the diff, correctly validates the change's safety, and its comment #1 (reuse pipeline's declared denoiser/`_dit_modules` instead of a fourth hardcoded component  |
| pr4825.r3 | opus_baseline | decisive | Candidate X delivers a substantive, well-grounded review: its top comment (reuse the pipeline's declared denoiser like _dit_modules instead of a hardcoded list, noting drift risk) closely mirrors the  |
| pr4834.r1 | opus_baseline | decisive | X delivers a deeply grounded review with specific file:line findings, correctly flags that the new hardware-gated tests never run in standard CI and that the default sleep(level=2) makes the new NotIm |
| pr4834.r2 | opus_baseline | decisive | Candidate X engages substantively with both threads the human reviewers raised (regression-test adequacy and the enum suggestion), and independently surfaces the exact latent gap: it flags that sleep( |
| pr4834.r3 | opus_baseline | decisive | X returned zero findings, missing both threads the human reviewers actually raised (tests, tag enum) and the latent over-strictness gap entirely. Y engages substantively with both review threads (test |
| pr4837.r1 | opus_baseline | decisive | X independently arrives at the same core insight as the ground-truth inline comment — that both submit_initial and submit_update reject list prompts for diffusion stages, confirming the already_submit |
| pr4837.r2 | opus_baseline | decisive | X reported zero findings and outright failed to review one of the two changed files due to budget exhaustion, missing the substantive point entirely. Y independently verified the fix by tracing submit |
| pr4837.r3 | opus_baseline | decisive | X delivers a grounded, verified analysis that independently confirms the exact reasoning behind the human inline comment (both submit_initial and submit_update reject list prompts in diffusion StagePo |
| pr4849.r1 | opus_baseline | clear | The central human-reviewer concern (Gaohan123 questioning whether source_outputs[0] is reliably the parent request) is directly investigated and resolved by X, which traces the orchestrator's [output, |
| pr4849.r2 | opus_baseline | clear | The core human concern was whether source_outputs[0] is reliably the parent (Gaohan123's inline comment); Y directly investigates and verifies this exact assumption against the orchestrator's construc |
| pr4849.r3 | opus_baseline | slight | Y directly investigates and substantiates the ground-truth reviewer's central question (whether source_outputs[0] is reliably the parent), citing orchestrator.py construction of [output, *companion_ou |
| pr4859.r1 | opus_baseline | slight | X catches the shared-config mutation bug in audio_vae.py (matching the ground-truth amy-why-3459 comment) and adds a legitimate, diff-grounded bonus observation about the encode_latent path becoming s |
| pr4859.r2 | opus_baseline | clear | Both candidates correctly flag the audio_vae.py:141 config.num_hidden_layers mutation, the standout ground-truth concern (amy-why-3459), with grounded, actionable fixes. X goes further: it explicitly  |
| pr4859.r3 | opus_baseline | clear | Both correctly flag the audio_vae.py config.num_hidden_layers mutation (the PR's main substantive review thread), but Y's treatment is more calibrated (notes the encoder is already constructed before  |
| pr4870.r1 | opus_baseline | decisive | X does real diff-grounded investigation: verifies the qwen3_tts scoping fix and its guarding test (matching the ground-truth Med concern's resolution), flags the async_chunk default inconsistency echo |
| pr4870.r2 | opus_baseline | decisive | X's OCR run terminated partial with zero findings, surfacing none of the ground-truth concerns and providing nothing actionable. Y independently verified the already-fixed qwen3 scoping, caught a real |
| pr4870.r3 | opus_baseline | decisive | X's OCR run terminated early with zero findings and an unreviewed file, so it covers none of the ground-truth threads (Med gating, Low flag-source, Nit seq_len) and offers nothing actionable. Y indepe |
| pr4893.r1 | opus_baseline | decisive | X returned zero findings and provides no grounded engagement with the diff, missing even the thin ground-truth signal (reduce_scatter/device_communicator verification). Y does substantive code-level v |
| pr4893.r2 | opus_baseline | decisive | X returned zero findings on a PR that touches nontrivial distributed-parallel-state semantics, providing no recall, no actionable content, and no verifiable claims. Y engaged substantively with the di |
| pr4893.r3 | opus_baseline | decisive | Neither candidate surfaces the sole ground-truth concern (yenuo26's suggestion to more rigorously verify reduce_scatter behavior beyond hasattr), so recall is 0 for both. Candidate X performs substant |
| pr4923.r1 | opus_baseline | decisive | X surfaces only a single trivial redundant-assignment nit that overlaps with none of the ground-truth reviewer threads (layering concern, seed-reproducibility caveat, NPU compilation_config fix, bench |
| pr4923.r2 | opus_baseline | decisive | X substantively engages with the two dominant threads of the real review — the talker_mtp cudagraph gating correctness and the seed-reproducibility consequence under full cudagraphs (near-verbatim ove |
| pr4923.r3 | opus_baseline | decisive | Y independently surfaces two threads that map directly onto the real reviewer discussion: the NPU 'cudagraph_mode: PIECEWISE' addition tied to the exact startup-crash fix Wallbreazzz requested, and th |
| pr4926.r1 | opus_baseline | clear | X independently found the same root-cause bug RuixiangMa flagged (only one of flash_attn_func/flash_attn_varlen_func is guaranteed non-None, yet code paths assume both), a genuinely confirmed issue th |
| pr4926.r2 | opus_baseline | clear | X independently rediscovers a variant of RuixiangMa's core bug (varlen_func being None crashes the masked path), touches the same version=1/2/default ambiguity wtomin flagged, and raises a legitimate  |
| pr4926.r3 | opus_baseline | clear | Y independently rediscovers RuixiangMa's confirmed 'flash_attn_varlen_func may be None → crash' bug almost exactly, plus flags real duplication and a plausible test-coverage gap, giving it meaningful  |
| pr4950.r1 | opus_baseline | decisive | Ground truth has no substantive reviewer concerns (just approvals/admin chatter), so recall is vacuously satisfied by both. X never actually reviewed the diff — it was filtered out for being Markdown, |
| pr4950.r2 | opus_baseline | decisive | Ground truth shows a docs-only PR that was simply approved with no substantive concerns; Candidate X actually engaged with the diff, cross-verified every technical claim against source (serving_chat.p |
| pr4950.r3 | opus_baseline | decisive | Ground truth has no substantive concerns (just LGTM/approvals), so neither candidate misses anything material. Candidate X performs an actual, diff-grounded review, cross-checking each doc claim (root |
| pr4954.r1 | opus_baseline | decisive | X returned zero findings, missing the core-fix confirmation and both reviewer comments entirely — no recall, no actionable content, nothing to assess for precision beyond vacuous. Y correctly confirms |
| pr4954.r2 | opus_baseline | decisive | X correctly confirms the core fix (codes.audio vs legacy audio, matching tts_postprocess and repo convention) and raises two grounded, actionable non-blocking issues with file:line references, though  |
| pr4954.r3 | opus_baseline | decisive | X correctly validates the core fix with precise line references and independently surfaces the substance of the ground truth's main non-blocking point (the containment fallback silently loosens all ca |
| pr4970.r1 | opus_baseline | clear | Ground truth has no substantive inline concerns (just an approval and an unrelated ask for a separate VoxCPM2 PR), so neither candidate misses anything material — recall is trivially satisfied by both |
| pr4970.r2 | opus_baseline | clear | Ground truth is essentially a rubber-stamp LGTM with an unrelated request (separate PR for VoxCPM2) not reflected in the visible diff, so neither candidate had much to recall. X's zero-finding output  |
| pr4970.r3 | opus_baseline | clear | Ground truth has no substantive concerns (just LGTM plus an unrelated ask), so both candidates trivially match the correct 'no blocker' outcome, but X actually demonstrates the reasoning: it traces th |
| pr4977.r1 | opus_baseline | decisive | X returned zero findings, missing the ground truth's sole substantive concern (trust_remote_code/kernels version compatibility) entirely and offering nothing actionable. Y did real diff-grounded analy |
| pr4977.r2 | opus_baseline | decisive | Y is a null review reporting zero findings, so it earns no recall, precision, or actionability credit. X performs genuine grounded analysis (verifies fallback-order equivalence, non-caching of failure |
| pr4977.r3 | opus_baseline | decisive | The only substantive ground-truth concern is Codex's P2 flag about a trust_remote_code kwarg breaking on locked kernels<0.15.0; Candidate X reports zero findings and misses it entirely, providing no v |
| pr5009.r1 | opus_baseline | decisive | Candidate X performs genuine code verification, correctly surfaces the global-scope risk of the platform default change and cross-checks it against the actual FLUX.1-dev evidence and override hooks me |
| pr5009.r2 | opus_baseline | decisive | X reported zero findings, missing every ground-truth concern (scope of the global default change, test adequacy, pytest mark, performance comparison). Y substantively engages with the scope question ( |
| pr5009.r3 | opus_baseline | decisive | X returned zero findings, so it misses every ground-truth thread (blast-radius scope of the platform-wide default change, the P1+P2/non-Qwen perf-accuracy justification, UT adequacy) and offers nothin |
