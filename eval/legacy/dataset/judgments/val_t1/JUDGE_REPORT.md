# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)

Judge: claude-sonnet-5 (blind, randomized order, 3 replicates x 10 items = 30 verdicts)

## Wins
- copilot_v2: 3
- opus_baseline: 27
- tie: 0

## Mean rubric scores

| arm | actionability | completeness | correctness | gap_hit | grounding | precision | recall |
|---|---|---|---|---|---|---|---|
| copilot_v2 | 0.63 | 0.48 | 0.60 | 0.00 | 0.58 | 0.61 | 0.45 |
| opus_baseline | 0.77 | 0.84 | 0.82 | 0.25 | 0.79 | 0.87 | 0.61 |

## Per-verdict detail

| item.rep | winner | margin | rationale (head) |
|---|---|---|---|
| issue4793.r1 | opus_baseline | clear | Both correctly land on PR #4792 fixing the #4527 regression that nulled inter_stage_outputs in the async_chunk:false path, matching the ground truth resolution. Y is far better grounded: it cites spec |
| issue4793.r2 | opus_baseline | clear | Both candidates converge on the same correct diagnosis matching the thread (regression from #4527 nulled the inter-stage payload in the non-async-chunk branch, fixed by merged PR #4792, already folded |
| issue4793.r3 | opus_baseline | clear | Both correctly identify the #4527 regression (non-async-chunk branch nulling the inter-stage payload) and that PR #4792 already fixes it in the 0.24 rebase, matching the thread resolution. X is ground |
| issue4827.r1 | opus_baseline | decisive | Candidate X's output is entirely unrelated to the issue (references a 'Mission Control'/cron-runs feature request), indicating a broken or mismatched run — it fails to engage with the HunyuanImage-3.0 |
| issue4827.r2 | opus_baseline | decisive | X correctly diagnoses the base-tokenizer/Instruct-config mismatch, cites the exact crash site and matches the thread's confirmed workaround (hunyuan_image3_dit.yaml) plus the proposed guard/docs fix a |
| issue4827.r3 | opus_baseline | decisive | X correctly diagnoses the root cause (base tokenizer missing extended <img_ratio_33..36> tokens vs. the MoE/Instruct config forcing AR init), matches the thread's identified fix path (base checkpoint  |
| issue4842.r1 | copilot_v2 | slight | Both land on the same correct resolution as the thread: the test loaded dummy weights because it ran at the default --run-level=core_model instead of full_model, and the fix is --run-level=full_model  |
| issue4842.r2 | opus_baseline | clear | Both correctly diagnose the run-level/dummy-weight root cause matching the thread's 'invalid' resolution and cite specific test-helper files/functions. Y goes further: it explains the crucial nuance t |
| issue4842.r3 | opus_baseline | clear | Both correctly identify the ground truth root cause (default --run-level=core_model forcing dummy weights) and reach the same 'invalid' conclusion, citing akshatvishu/yenuo26. Y digs deeper with preci |
| issue4891.r1 | opus_baseline | clear | Both correctly land on 'duplicate of #4808,' matching the thread, but Y also surfaces the #4809 triage-issue reference that the maintainer explicitly pointed to, while X omits it entirely. X asserts ' |
| issue4891.r2 | opus_baseline | clear | Both agree with the actual 'duplicate of #4808' closure, but X's own findings note PR #4808 is CLOSED (not merged) yet it still confidently declares the bug 'already fixed on main' — an unresolved int |
| issue4891.r3 | copilot_v2 | slight | Both correctly land on the maintainer's actual resolution (duplicate of #4808, per #4809). Y is more grounded — it shows an actual file read and grep confirming the get_cache_scale call is already gon |
| issue4905.r1 | opus_baseline | clear | Both correctly bisect the failure to PR #4834's intentional NotImplementedError guard, matching the thread's '#4834 was merged, this error appeared' clue, and both cite real file/line evidence from as |
| issue4905.r2 | opus_baseline | clear | Both candidates converge on the same plausible root cause (PR #4834's wake_up() guard vs. a stale test still using level=2), which partially aligns with yenuo26's thread comment pinpointing #4834 as t |
| issue4905.r3 | copilot_v2 | slight | Both correctly identify PR #4834's NotImplementedError guard as the proximate cause, matching yenuo26's attribution, and both ground claims in real file/line citations from async_omni.py and the test  |
| pr4810.r1 | opus_baseline | decisive | X matches the ground-truth reviewer's core technical points (outer AutoWeightsLoader auto-applies the mapper, qwen2_old's getattr guard made removal a clean-up not a regression) and independently catc |
| pr4810.r2 | opus_baseline | decisive | Y grounds every claim in specific upstream file/line evidence, correctly identifies that the diffusion loader (hunyuan_image3_transformer.py) was dropped from this PR's sweep despite being listed as a |
| pr4810.r3 | opus_baseline | decisive | Y independently re-derives the same delegated-vs-direct-loader analysis the human reviewer gave, then adds a legitimate new finding (the delegated-loader test doesn't actually exercise AutoWeightsLoad |
| pr4816.r1 | opus_baseline | clear | Both correctly verify the mechanical rename is complete and consistent with upstream, and ground truth (a bare 'lgtm' approval) has no substantive concerns to recall. X reaches an accurate APPROVE ver |
| pr4816.r2 | opus_baseline | clear | Ground truth is a trivial 'lgtm' approve on a pure mechanical rename with no substantive concerns, so recall is vacuous for both. X reaches the same correctly-grounded APPROVE verdict, verifying the r |
| pr4816.r3 | opus_baseline | clear | Ground truth is a trivial merged rename PR with an 'lgtm' approval and no real concerns; X correctly matches this, verifying the rename against upstream and test updates without fabricating issues, an |
| pr4825.r1 | opus_baseline | slight | Both candidates independently surface the one substantive reviewer concern visible in the diff — that default_components is a hardcoded, drift-prone list that should instead be derived from each pipel |
| pr4825.r2 | opus_baseline | clear | Both candidates independently converge on the same core latent concern the ground-truth reviewer raised (dsocek's point that hardcoding pipeline component names is fragile and should derive from an ex |
| pr4825.r3 | opus_baseline | clear | Both candidates converge on the same core design critique (derive default_components from existing declared metadata like _dit_modules rather than hardcoding), which is grounded but only tangentially  |
| pr4837.r1 | opus_baseline | clear | The one substantive ground-truth point (removing the already_submitted gate is safe because both submit_initial and submit_update reject list prompts identically) is almost verbatim reproduced by X (' |
| pr4837.r2 | opus_baseline | clear | The one substantive ground-truth signal (yJader's inline comment) explains that the already_submitted guard removal is correct because both submit_initial and submit_update reject list prompts for dif |
| pr4837.r3 | opus_baseline | clear | X's review directly reconstructs the ground-truth reviewer's core insight — that submit_initial and submit_update both reject list prompts for diffusion, so gating the unwrap on already_submitted was  |
| pr4893.r1 | opus_baseline | clear | Neither candidate surfaces the one substantive ground-truth concern (whether the new reduce_scatter hasattr assertions are sufficient verification), so recall is low for both. X finds some plausibly-r |
| pr4893.r2 | opus_baseline | slight | Neither candidate surfaces the one substantive ground-truth concern (yenuo26's ask to also verify the reduce_scatter parameter, not just hasattr); X even inspects that exact test code and dismisses it |
| pr4893.r3 | opus_baseline | slight | Neither candidate caught the one substantive ground-truth ask (whether the test should verify the reduce_scatter param, not just device_communicator/hasattr), so recall is low for both, with Y getting |
