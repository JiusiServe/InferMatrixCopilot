# Reference-agent research — mechanisms for PR review & issue answering

Goal-phase-3 deliverable (hook-approved research plan, 2026-07-17). Evidence classes: **source-backed** (clone file:line), **documented** (official doc URL), **inferred** (labeled; never grounds an "adopt"). Every entry cross-checks what the copilot already has (adaptive depth `review/planner.py`, single-model lens ensemble `agent_runtime/ensemble.py`, on-demand `gh_pr_view`/`gh_issue_view`/`gh_ci_read` `_common.py:133-173`, knowledge briefing + doc tools).

## A. Baseline behavior autopsy (output-level; no turn traces exist — `cost.json` has aggregate `calls` only, so tool-usage claims are inference)

Items compared: PR #4810 (GOLD latent-gap, val), PR #4837 (clean bugfix, val), issue #4842 (invalid/run-level, val), issue #4793 — baseline `eval/dataset/baselines/claudecode_opus48/*.md` vs our `arms/copilot_v2_t4_r1/*.md`.

Output-level deltas (baseline has, ours lacks):
1. **Test-efficacy critique** (pr4810): baseline's top non-blocking finding is that the added regression test *doesn't exercise the behavior it names* (feeds pre-mapped names, bypassing `AutoWeightsLoader`) — a test-coverage-quality finding class our lenses never produced on this item. Maps to **PR recall** (GT reviewer concerns include test adequacy).
2. **Systematic category scan rendered as a table** (pr4810, pr4837): a 6-category BLOCKER scan (Correctness / Reliability / Breaking / Test Coverage / Documentation / Security) with explicit PASS marks. Coverage-forcing device; also signals the swept-but-clean categories to the judge. Maps to **PR recall** (+judge-visible coverage).
3. **Verdict calibration on merged PRs** (pr4810): baseline says APPROVE + non-blocking notes where ours says REQUEST CHANGES with the same core finding as [blocker]. Judged against "human comments + merged diff", the merged outcome favors approve-with-notes. Maps to **PR precision/recall** (finding kept, verdict aligned).
4. **Duplicate finding leaked** (ours, pr4810): `mimo_audio_llm.py:1158` dead-guard comment appears TWICE in our output — reducer dedup miss. Maps to **PR precision**.
5. **Prevention/ergonomics follow-up** (issue4842): baseline ends with a forward-looking recommendation (guard/warn when a `full_model`-marked test collects at `core_model`; suggests a tracking issue). Ours stops at disposition. Maps to **issue completeness** (end-to-end service incl. recurrence prevention).
6. **"Requirements for a meaningful pass" checklist** (issue4842): baseline enumerates concrete preconditions (weights cached, VRAM split 0.55/0.3/0.1 per stage, sample video path exists). Maps to **issue completeness**.
7. **Full mechanism chain** (issue4842): baseline traces every layer (`run_args.py` default → `runtime.py:2829` tiny-model swap → `stage_config.py:713/670` dummy load_format → assertion helpers per level) where ours cites 3 anchors. Maps to **issue grounding/completeness**.
8. Baseline cost (real-billed): pr4810 = 38 calls / 1.57M in / $3.21 / 682s — our eco run ≈ $0.26. The quality levers above are output-shape levers, not spend levers: adoptable without approaching baseline cost.

## B. Mechanism entries — context assembly & recall (OpenHands / SWE-agent / aider sweep)

**B1. Issue-bundle + "re-read all requirements" final checklist** (OpenHands) — source-backed: `resolver.py:19,37,191,225` (paginated comments, chronological, last-10 cap) + `issue_conversation_instructions.j2` (body + comments + Guidelines + Final Checklist "re-read title/body/comments, confirm every requirement addressed"). Cross-check: we already fetch title/body/labels/comments (`issue.py:49-50`); the deltas are the completeness **final-checklist prompt** and last-N comment budgeting. Benefit: issue completeness. Cost S. **Verdict: adopt** (checklist + slot contract), reject the fetch part (already present).

**B2. PR body + linked-issue as first-class review evidence** (OpenHands) — source-backed: `pr_update_conversation_instructions.j2` ("Retrieve the diff… Fetch the PR body and the linked issue"); full review-thread reconstruction via GraphQL `resolver.py:73`. Cross-check: we fetch diff+gate only; PR body reachable only by agent choice; discussion comments unreachable. Benefit: PR recall (acceptance criteria + maintainer concerns live there). Cost S (REST `gh pr view --json title,body,comments,reviews` + linked-issue fetch; skip GraphQL threads initially). **Verdict: adopt.**

**B3. Structured per-finding format + pre-review triage gate + repo flag-lists** (OpenHands skills) — source-backed: `skills/code-review.md`, `.agents/skills/custom-codereview-guide.md`. Cross-check: we already have {file,line,severity,comment,evidence} contract + per-repo `review.md` checklist injection (`review/steps.py:95-100`) — those parts are present. Delta worth taking: the **category-PASS scan** (matches autopsy #2) as an output-shape element. **Verdict: adapt** (render swept-categories table + verdict calibration); reject checklist part (already present).

**B4. Capped search + windowed viewer + tree-sitter filemap for usage enumeration** (SWE-agent) — source-backed: `tools/search/bin/search_dir` (>100 files ⇒ "narrow"), `tools/windowed/config.yaml`, `tools/filemap/bin/filemap`. Cross-check: our agent runtime already has scoped `grep`/`read_file` (windowed) — present; the delta is a **prompted usage-enumeration sweep** ("for each changed public symbol, grep all usages; name every stale caller") which our behavior lens asks for narrowly. Benefit: PR recall. Cost S (prompt-level; tools exist). **Verdict: adapt.**

**B5. History processors (elision, cache-control pinning)** (SWE-agent) — source-backed: `agent/history_processors.py:85,215,261`. Cross-check: our runtime already uses windowed reads, evidence caps, and cache stagger; ensemble evidence lives in a shared cached prefix. **Verdict: reject (already present in equivalent form)**; revisit only if traces show context blowups.

**B6. Review-on-submit self-check sweep** (SWE-agent) — source-backed: `tools/review_on_submit_m/bin/submit` + `SUBMIT_REVIEW_MESSAGES`. Cross-check: ensemble paths get verify-and-merge; the **light path has no verification stage at all**. Benefit: PR precision on light-tier reviews + issue completeness re-check. Cost S (one extra staged message in the light/issue steps). **Verdict: adapt** (light-tier self-check against diff+contract before finalizing).

**B7. Timeline-event mining for related PRs/commits** (SWE-agent) — source-backed: `utils/github.py:111` (`issues.list_events` → `referenced` events → commit "fixes #N" matching). Cross-check: absent in our pipeline. Benefit: issue grounding/completeness (related artifacts), duplicate-answer avoidance. Cost S (one `gh api` tool). **Verdict: adopt.**

**B8. Issue-seeded repo-map (tree-sitter tags + personalized PageRank, token-budgeted)** (aider) — source-backed: `repomap.py:279,365,525,629` + `context_coder.py` stabilization loop. Cross-check: our `profiles/repo_map.py` is an index/cache map, not request-seeded ranking; agent has grep tools that partially substitute. Benefit: PR recall (impacted-but-not-in-diff code) + issue completeness (fix-site location). Cost M-L (tree-sitter + networkx + cache). **Verdict: experiment** — high ceiling, but measure grep-sweep (B4) first; only invest if recall still lags.

**Incidental UX conventions** (aider `/commands`, `commands.py:445,657,1182+`): explicit mode switches, `/tokens` context inspection — feeds the design's chat-surface polish; no verdict needed here.

## C. Mechanism entries — install/routing UX & orchestration (cline / openclaw / hermes sweep)

**C1. One-command bootstrap + preflight that prints the exact fix** (hermes) — source-backed: `hermes-agent/README.md:34-65`, `setup-hermes.sh:66-127` (per-dep probe; on failure capture installer output and print the real error + manual fix URL; two-stage `curl -o` then `sh`). Cross-check: we have nothing (manual pip + hand-filled .env; gh auth undocumented). Benefit: UX. Cost M. **Verdict: adapt** — an `install.sh` + `omni-copilot doctor` that validates venv, .env keys (names only), `gh auth status`, repo paths, and prints the fix command per miss.

**C2. `doctor` / `doctor fix` diagnose-then-remediate** (cline) — source-backed: `cline/apps/cli/src/commands/doctor.ts:408-462,464-550` (+`--json`). Also documented for Claude Code: `claude doctor` prints read-only install/settings diagnostics with suggested fixes (code.claude.com/docs/en/setup, "Verify your installation"); install one-liner `curl -fsSL https://claude.ai/install.sh | bash`. Cross-check: absent. **Verdict: adopt** (read-only doctor; auto-fix only for safe items like creating .env from template).

**C3. Typed mention/URL extraction that preserves the raw reference** (cline) — source-backed: `context-mentions.ts:52-66` (URL/commit-hash/path regexes with trailing-punctuation lookahead), `mentions/index.ts:59-120` (keep raw + attach expansion). Cross-check: our intent layer discards org/repo (`intent.py:140`). Benefit: routing accuracy; kills the late "no PR number" failure. Cost S. **Verdict: adopt** — deterministic GitHub URL/`#N` parser BEFORE the LLM intent call; extracted {host, org/repo, kind, number} override/augment the LLM parse; unknown repo → upfront typed error, not default-repo silent misroute.

**C4. Deterministic-first command routing; LLM only for free-form** (openclaw) — source-backed: `command-detection.ts:14-54,78-100`, `commands-text-routing.ts:16-48`; typed errors instead of guessing (`directive-handling.model-selection.ts:110-160`). Cross-check: our every-input LLM parse is the flake source (single call, no retry, `intent.py:124-129`). Benefit: routing accuracy + cost + latency (skip LLM on unambiguous refs). Cost S-M. **Verdict: adopt** — regex/registry fast-path for "review <url|pr N> [depth]", "answer issue N", fall through to LLM with ONE retry.

**C5. Structured clarify-vs-guess + headless fallback** (cline) — source-backed: `PlanModeRespondHandler.ts:36-59,49-54`, `AskFollowupQuestionToolHandler.ts:43-54` (ask with options only when material; in non-interactive mode self-serve via tools instead of hanging). Cross-check: we fail late at fetch on missing PR. Benefit: UX mandate ("clarify only when ambiguity materially affects result"). Cost S. **Verdict: adopt** — validate spec completeness at parse time; interactive → one concrete question; `--yes`/MCP → typed BLOCKED with the fix phrase.

**C6. Provider fallback chain with unhealthy-provider TTL cache** (hermes) — source-backed: `auxiliary_client.py:36-39,2246-2306,2353-2423` (402/429-classified fallback; recently-failed providers hidden by TTL). Cross-check: copilot LLM has none; personal-agent MoA breaker is our in-house analog. Benefit: reliability of intent + MoA members. Cost M. **Verdict: adapt** (fold into the MoA member/breaker design; single-model path gets one retry, not a chain).

**C7. Background verification fork + graded effort dial** (hermes) — source-backed: `background_review.py:1-18`, `hermes_constants.py:408-425` (VALID_REASONING_EFFORTS enum + capability guards; no auto complexity→effort inference found). Cross-check: we already have depth tiers (planner) = our effort dial; background forks conflict with our synchronous run model. **Verdict: reject** (effort dial already present as review_depth; background fork out of scope).

**C8. Cursor BugBot review controls** — documented (cursor.com/docs/bugbot): analyzes PR diffs **and uses existing PR comments as context** to avoid duplication; severity-tagged findings with fix suggestions; repo rules via `.cursor/BUGBOT.md`; effort levels; incremental re-review ("only changes since previous review"); dry-run mode. Cross-check: we have severity+rules(review.md)+depth(planner); missing = **existing-PR-comments as context** (dedup against what maintainers already said) and incremental re-review. Benefit: PR precision (no duplicating maintainer comments) + recall (comment threads carry concerns). Cost S (part of B2 fetch). **Verdict: adopt** (fetch comments; prompt "do not repeat concerns already raised; build on them").

**Claude Code documented UX bar** — documented (code.claude.com/docs/en/setup): single-command install (`curl … install.sh | bash`), `claude --version` verify, `claude doctor` diagnostics. This is the install UX bar C1/C2 implement for our CLI.

## D. Mechanism entries — MoA / ensembles / cost control (cross-clone sweep)

**D1. Best-of-N + LLM judge/chooser with partial-failure floors** (swe-agent) — source-backed: `reviewer.py:329-372,416-449,524-546,617-658` (Chooser aggregator w/ Preselector; Reviewer judge with n_sample averaging − std penalty; fallback to `selected_indices[0]` on chooser failure; unparseable judge samples skipped, all-invalid → −100 not crash; cheapest-trajectory tie-break; `min_budget_for_new_attempt` pre-call gate). Cross-check: our verify-and-merge reducer already merges perspectives; what we lack is the **judge/chooser layer over heterogeneous-model proposals + budget gating**. **Verdict: adapt** — this is the arbitration template for MoA (below).

**D2. Architect/editor two-model split** (aider) — source-backed: `architect_coder.py:11-48`, `models.py:625-645`. Cross-check: our reducer already rides the tier model; the analog slot is heterogeneous proposers + tier-model aggregator. **Verdict: adapt** (shape informs MoA roles; no direct port).

**D3. Ordered `[cheap, strong]` role fallback** (aider) — source-backed: `models.py:603-623`. Cross-check: intent already falls back INTENT_MODEL→agent_model at config level, but calls have no runtime fallback. **Verdict: adopt** for the intent-parse retry (one retry, then typed clarify).

**D4. Plan/act hard capability gating per mode** (cline) — source-backed: `ToolExecutor.ts:291`. Cross-check: we already enforce read-only scopes in code (ToolScope). **Verdict: reject (already present).**

**D5. Model-fallback candidate chain + error classification + attempts summary** (openclaw) — source-backed: `model-fallback.ts:137-152,584,604-629`, `run-fallback-policy.ts:13-75`. Cross-check: absent in copilot; personal-agent breaker is the in-house analog. **Verdict: adapt** into MoA member handling (classify rate-limit/auth/context-overflow; drop member, record attempts, never crash the step).

**D6. Per-role cheap-model routing + per-model compression thresholds** (hermes) — source-backed: `auxiliary_client.py:1-33,255-300`. Cross-check: we have role models (intent/reviewer/planner) — present; per-model thresholds not needed yet. **Verdict: reject (mostly present).**

**D7. Centralized cost/call caps with typed exceptions** (swe-agent) — source-backed: `models.py:372-382,667-670,73-78`, `exceptions.py:31-43` (`0 < limit < cost` sentinel; per-instance + total + call caps at ONE choke point; post-hoc — pair with D1's pre-call budget gate). Cross-check: we have budget refs in metrics but NO runtime enforcement. **Verdict: adopt** — cap MoA spend (`moa_max_usd` per run + per-proposer timeout) and expose planner/MoA overhead to metrics.

**D8. Cache-aware context layering** (aider `chat_chunks.py:28-61`; cline `ContextManager.ts:249-317,628-634`; swe-agent `history_processors.py:134-176`) — Cross-check: we already order evidence in a shared cached prefix + stagger lenses. **Verdict: reject (already present)**; keep the file-read-dedup idea in reserve.

Cross-clone negative results (load-bearing): no clone runs a same-model multi-perspective committee with deterministic verify-and-merge (we already have that — it is a differentiator, keep it); none has a concurrent heterogeneous-proposer primitive with per-proposer timeout + partial drop + single-model fallback (our MoA must compose D1+D5+D7 with the personal-agent `_mixture` breaker design); none does up-front complexity→tier classification (our `review/planner.py` is already ahead — extend the same idea to issues).

## E. Verdict summary → design-plan inputs (priority order)

| Priority | Change | Research basis | Targets |
|---|---|---|---|
| 1 | PR evidence bundle: title/body + PR comments/reviews + linked issue auto-fetched (budgeted) + "don't repeat maintainer comments, build on them" | B2, C8, autopsy #1-2 | PR recall, precision |
| 2 | Output shape: category-PASS scan table; verdict calibration (approve-with-notes vs REQUEST CHANGES); reducer exact-dup guard | autopsy #2-#4, B3 | PR recall (judge-visible), precision |
| 3 | Issue completeness contract: explicit slots (root cause/fix/workaround/verification/disposition/prevention) + final re-read checklist + preconditions list | B1, B6, autopsy #5-#7 | issue completeness |
| 4 | Related-artifact mining: timeline events → linked PRs/commits tool | B7 | issue grounding/completeness |
| 5 | Deterministic-first routing: URL/PR-ref parser (keeps org/repo, typed errors), registry fast-path, LLM fallback w/ one retry, upfront clarify, params from NL | C3, C4, C5, D3 | UX, routing accuracy, latency |
| 6 | One-click setup: `install.sh` + `omni-copilot doctor` (gh auth, .env, repo paths; prints exact fixes) | C1, C2, Claude Code bar | UX |
| 7 | Selective MoA: heterogeneous lens proposers from `LLM_MIXTURE` on full-depth/hard tasks; tier-model aggregator (existing reducer); breaker + timeout + cost cap + single-model fallback | D1, D5, D7, personal-agent `_mixture` | PR recall / issue completeness at bounded cost |
| 8 | Usage-enumeration sweep prompt (changed-symbol callers) | B4 | PR recall |
| — | Experiment-only: issue-seeded PageRank repo-map (B8) — revisit if recall still lags after 1-8 | B8 | PR recall ceiling |
