# Val-split judgment: copilot_v2 (DeepSeek) vs claudecode_opus48 (Opus 4.8)

Judge: claude-sonnet-5 (blind, randomized order, 3 replicates x 10 items = 30 verdicts)

## Wins
- copilot_v2: 13
- opus_baseline: 17
- tie: 0

## Mean rubric scores

| arm | actionability | completeness | correctness | gap_hit | grounding | precision | recall |
|---|---|---|---|---|---|---|---|
| copilot_v2 | 0.80 | 0.66 | 0.69 | 0.23 | 0.63 | 0.77 | 0.39 |
| opus_baseline | 0.80 | 0.72 | 0.57 | 0.08 | 0.66 | 0.76 | 0.46 |

## Per-verdict detail

| item.rep | winner | margin | rationale (head) |
|---|---|---|---|
| issue4802.r1 | opus_baseline | slight | Both correctly capture the two things the thread actually settled — stage/replica attribution already covered by the relabeling work, and tail_waste/fragmentation dropped as expected block-rounding ov |
| issue4802.r2 | opus_baseline | slight | Both correctly capture the two core resolved points (attribution already covered by #3576's {stage,replica} labels; tail_waste/fragmentation dropped per LHXuuu's pushback), but X omits the explicit sc |
| issue4802.r3 | opus_baseline | clear | The thread actually closes with Ronnie-Rui explicitly conceding 'I won't push these as default Prometheus metrics for now' — a full withdrawal, not a partial one. Y matches this with a 'won't-implemen |
| issue4815.r1 | copilot_v2 | slight | Both correctly endorse closing as not-reproducible, but the thread explicitly states the maintainer had no confirmed explanation and suspected a contaminated session (hot patches, shared GPU) — X stay |
| issue4815.r2 | opus_baseline | clear | Both correctly endorse the actual resolution (close, not reproducible, likely a runtime/environment fluke) rather than inventing a false root cause. X is cleanly formatted as a real maintainer comment |
| issue4815.r3 | opus_baseline | slight | Both correctly endorse the not-reproducible closure and correctly avoid recommending a shipped enforce_eager fix, matching the thread's actual (uncertain) resolution. X grounds its analysis with more  |
| issue4826.r1 | copilot_v2 | decisive | The thread shows no root cause was ever identified: the maintainer asked for diagnostic text/audio output, the reporter never captured it, and the issue closed as 'not occurred' after an unrelated upd |
| issue4826.r2 | copilot_v2 | decisive | The thread shows no root cause was ever found — the reporter simply couldn't reproduce after updating, admitted no diagnostic was captured, and the issue was closed as 'not occurred' with a reopen off |
| issue4826.r3 | copilot_v2 | decisive | The thread never identified a root cause — the reporter simply could no longer reproduce after updating, and the maintainer closed it as 'not occurred.' Y mirrors this exactly: closes as not-reproduci |
| issue4957.r1 | opus_baseline | slight | Both correctly land on the true root cause (talker YAML temperature=0.9 vs request temperature=0) and correctly endorse closing as not-reproducible, matching the actual thread. X goes further by audit |
| issue4957.r2 | opus_baseline | clear | Both correctly land on the ground truth's core finding (no dropped chunks; audio-length variance from talker temp=0.9 vs request temp=0), but X directly audits the transport/chunk-accounting path (shm |
| issue4957.r3 | opus_baseline | clear | Both land on the same core conclusion as the thread (not reproducible; talker temp=0.9 vs request temp=0 explains audio-length variance, no dropped chunks), but X does the harder work of actually audi |
| issue4962.r1 | opus_baseline | slight | Both accurately restate the reporter's own root-cause analysis (text EOS folded into all_stop_token_ids, index_put_ overrun on the narrow codec vocab) and both cite an identical, suspiciously specific |
| issue4962.r2 | copilot_v2 | slight | Both give the same technically sound root-cause diagnosis (text-tokenizer EOS folded into all_stop_token_ids overruns the talker's narrow codec vocab) and cite matching file/line evidence for an alleg |
| issue4962.r3 | copilot_v2 | slight | The actual thread shows only a maintainer tagging colleagues for review ("PTAL"), i.e. an escalation with no confirmed resolution — yet both candidates confidently assert a merged fix with near-identi |
| pr4762.r1 | opus_baseline | slight | Both candidates catch the trust_remote_code True→False default flip (matches the acknowledged inline bug), but X also explicitly validates that endpoint-restriction resolution now follows the post-dep |
| pr4762.r2 | opus_baseline | clear | Both catch the trust_remote_code default flip (matches the author's own flagged concern), but Y also explicitly surfaces and confirms the PR's central reviewer concern — that endpoint restrictions mus |
| pr4762.r3 | opus_baseline | clear | Both candidates independently flag the trust_remote_code default flip (True→False), matching the author's self-acknowledged bug. Y goes further: it explicitly verifies and confirms the ground truth's  |
| pr4777.r1 | copilot_v2 | clear | Both candidates correctly validate the core range/message-consistency change and match the ground truth's implicit 'this works as intended' sentiment (GT is thin: two LGTMs plus a manual QA confirmati |
| pr4777.r2 | opus_baseline | slight | Ground truth here is thin (two LGTM approvals plus a manual verification comment confirming boundary/unit-test/e2e behavior); both candidates correctly validate the core range/message/test changes X d |
| pr4777.r3 | copilot_v2 | clear | Ground truth shows a clean, low-risk change verified by a human (boundary check, unit tests, L4 regression all passed) and merged with two LGTMs — no real defects existed. X stays disciplined, validat |
| pr4834.r1 | copilot_v2 | clear | Y's blocker finding pinpoints exactly the over-strictness that later broke merge CI (issue #4905): it names 5 existing tests that call sleep(level=2)→wake_up() and will now hit the new NotImplementedE |
| pr4834.r2 | copilot_v2 | clear | Y directly hits the latent gap: it names 5 existing tests (with file/line) that call sleep(level=2) then wake_up and will now hit the new NotImplementedError guard, precisely matching the real-world # |
| pr4834.r3 | opus_baseline | slight | Both hit the latent gap directly and concretely: X pinpoints 5 existing tests that call sleep(level=2)+wake_up() and will now raise (exact reproduction of the #4905 break), while Y independently diagn |
| pr4849.r1 | copilot_v2 | slight | Both candidates investigate the exact same code path the human reviewer questioned (source_outputs[0] as parent, hunyuan_image3.py:118) and confirm it via the orchestrator's [output, *companions] cons |
| pr4849.r2 | opus_baseline | slight | Y independently confirms the PR's central disputed point (is source_outputs[0] really the parent?) by tracing orchestrator.py's construction of [output, *companions], mirroring the actual thread's res |
| pr4849.r3 | opus_baseline | clear | Y directly investigates and confirms the core reviewer question (is source_outputs[0] really the parent?) by tracing orchestrator.py's construction of [output, *companion_outputs], matching the actual |
| pr4954.r1 | opus_baseline | clear | Both candidates correctly validate the core fix (codes.audio read/write match), but the ground truth's real substance is the reviewer's note that the containment fallback now applies unconditionally t |
| pr4954.r2 | copilot_v2 | slight | Both correctly validate the core fix (codes.audio read now matches tts_postprocess's write, with backward-compat for legacy top-level audio) and both raise legitimate, grounded concerns about the new  |
| pr4954.r3 | copilot_v2 | slight | Both confirm the core codes.audio/tts_postprocess fix is correct and surface valid, well-grounded non-blocking issues (X: unconditional containment fallback loosening all callers, and the near-useless |
