# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)

Judge: claude-sonnet-5 (blind, randomized order, 3 replicates x 10 items = 30 verdicts)

## Wins
- copilot_v2: 12
- opus_baseline: 16
- tie: 2

## Mean rubric scores

| arm | actionability | completeness | correctness | gap_hit | grounding | precision | recall |
|---|---|---|---|---|---|---|---|
| copilot_v2 | 0.84 | 0.66 | 0.65 | 0.38 | 0.58 | 0.81 | 0.48 |
| opus_baseline | 0.76 | 0.69 | 0.56 | 0.25 | 0.62 | 0.84 | 0.55 |

## Per-verdict detail

| item.rep | winner | margin | rationale (head) |
|---|---|---|---|
| issue4802.r1 | opus_baseline | clear | Both correctly capture the thread's actual resolution (LHXuuu's redundancy objection, author's concession that #3576 already covers stage/replica attribution, tail_waste/fragmentation being expected b |
| issue4802.r2 | opus_baseline | clear | Both reach the thread's actual conclusion (attribution already covered by #3576's {stage,replica} relabeling, tail_waste/fragmentation dropped as unactionable, diffusion deferred to Q3), but X asserts |
| issue4802.r3 | opus_baseline | clear | Both land on the same disposition maintainers reached (attribution already covered by #3576, tail_waste/fragmentation dropped as expected block-rounding overhead, diffusion deferred to Q3), but X lean |
| issue4815.r1 | copilot_v2 | clear | Both correctly land on the actual verdict (not reproducible, correctly closed) and cite real files/config (qwen3_tts_talker.py, deploy/qwen3_tts.yaml, gpu_model_runner.py). But the thread explicitly s |
| issue4815.r2 | opus_baseline | clear | Both correctly land on the actual resolution (closed as not-reproducible after 55/55 clean trials), but X engages the reporter's stated dilemma (not wanting to ship enforce_eager broadly) with a concr |
| issue4815.r3 | copilot_v2 | clear | Both land the right top-line verdict (closed as not-reproducible), but X goes on to construct a confident, unconfirmed mechanistic theory (EOS-logit depression from 'stale captured graph buffers,' a s |
| issue4826.r1 | copilot_v2 | clear | The thread never established a root cause — it simply stopped reproducing after an update and was closed as 'not occurred,' with the maintainer's diagnostic ask (paste text/audio output) left unanswer |
| issue4826.r2 | copilot_v2 | clear | The thread never established a root cause — it stayed genuinely unresolved (deterministic-output ask, reporter updates and can't reproduce, maintainer closes 'not occurred, reopen if needed'). X confi |
| issue4826.r3 | copilot_v2 | clear | The thread never identifies a root cause — the reporter just says it stopped reproducing after an update and the maintainer closes with 'can reopen if needed,' leaving the diagnosis genuinely open. X  |
| issue4957.r1 | copilot_v2 | clear | Both land on the correct conclusion (not-reproducible, talker temp=0.9 vs thinker temp=0 variance, no chunk drops), but X's submitted text is only an 'addendum' that references unseen earlier sections |
| issue4957.r2 | copilot_v2 | clear | Both correctly land on the ground truth (not reproducible; no chunk drops; gap is talker temp=0.9 vs request temp=0), but Y is a complete, standalone triage doc with concrete YAML/serving_chat.py cita |
| issue4957.r3 | copilot_v2 | clear | Both correctly land on the maintainer's actual resolution (no chunk drops; talker temp=0.9 vs request temp=0 explains the audio-length variance), and X's transport-path audit (shm_connector.py, chunk_ |
| issue4962.r1 | opus_baseline | clear | The only established ground truth is a maintainer tagging others for review ('PTAL') — neither candidate's confident 'fixed and merged, closing as resolved' narrative with fabricated file/line specifi |
| issue4962.r2 | opus_baseline | clear | The actual thread is just a maintainer tagging two colleagues for review ('PTAL') — nothing was established as fixed or merged. Both candidates instead confidently invent an elaborate 'already fixed o |
| issue4962.r3 | opus_baseline | slight | The actual thread resolution is just Gaohan123 pinging two other maintainers for review ("PTAL") — no fix is confirmed as merged. Both candidates instead confidently declare the bug already fixed on m |
| pr4762.r1 | opus_baseline | slight | X explicitly surfaces the two GT concerns most reviewers cared about (the trust_remote_code default flip, and the deploy-override-vs-auto-detected-pipeline precedence issue, noting the regression test |
| pr4762.r2 | opus_baseline | slight | Both candidates independently catch the trust_remote_code default flip (True→False), the one issue the PR author himself flagged as a real bug. But Y is the only one that surfaces and validates the ce |
| pr4762.r3 | opus_baseline | clear | Y is the only candidate that engages the PR's central, most-repeated reviewer concern (endpoint restrictions being resolved from the auto-detected pipeline instead of the post-deploy-override pipeline |
| pr4777.r1 | tie | slight | Both candidates independently converge on the same real, well-grounded defect — stale hardcoded '3'-boundary references in the two dfx reliability test files that the PR diff didn't touch — with concr |
| pr4777.r2 | opus_baseline | slight | Ground truth contains no substantive concerns (just two LGTM approvals plus a bot verification comment), so both candidates trivially achieve full recall by not missing anything real. Both independent |
| pr4777.r3 | opus_baseline | slight | Ground truth here is empty of substantive concerns (two LGTM approvals, no inline comments), so recall is vacuously satisfied by both. Both candidates independently surface the same real latent gap —  |
| pr4834.r1 | copilot_v2 | decisive | Y's blocker finding — that five pre-existing tests calling sleep(level=2) then wake_up() will now hit the new NotImplementedError guard — is a precise, evidence-cited hit on the latent gap (matching t |
| pr4834.r2 | copilot_v2 | clear | Both engage the ground-truth threads (regression tests, tag enum) and both flag the level-2 NotImplementedError guard as over-strict, hitting the latent gap. Y's version is far more concrete and verif |
| pr4834.r3 | opus_baseline | slight | Both candidates fully cover the two substantive ground-truth asks (regression tests, tag enum) and both surface the latent gap: X names five specific pre-existing tests that would now break under the  |
| pr4849.r1 | opus_baseline | slight | The ground-truth thread's substantive concern is Gaohan123 questioning whether source_outputs[0] is reliably the parent output, resolved by Celeste-jq explaining the orchestrator builds [output, *comp |
| pr4849.r2 | tie | slight | Neither candidate surfaces the two concrete human asks (fix precommit; run the diffusion benchmark script), so recall is low for both. Y engages more substantively with the actual GT concern (parent-f |
| pr4849.r3 | opus_baseline | slight | The one substantive human concern (Gaohan123 questioning whether source_outputs[0] is reliably the parent) is directly and thoroughly answered by Y, which traces the exact orchestrator construction si |
| pr4954.r1 | opus_baseline | clear | Y's flagged issue (the containment fallback now unconditionally loosens the gate for every caller, with a concrete failing example like expected 'hello' matching transcript 'hello world goodbye') dire |
| pr4954.r2 | copilot_v2 | slight | Both candidates correctly validate the core fix (codes.audio convention, backward compat) matching the reviewer's approval rationale, but neither precisely reproduces either non-blocking GT comment (d |
| pr4954.r3 | copilot_v2 | clear | GT's only concern still live in the final diff is whether the legacy top-level `audio` fallback in tts_preprocess still has a real producer given #4527 moved to codes.audio (the docstring-staleness co |
