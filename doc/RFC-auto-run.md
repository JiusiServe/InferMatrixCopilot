# RFC: Auto-run InferMatrixCopilot on GitHub events (PR review first)

- **Status**: draft v3, for team discussion (two gpt-5.6 review rounds folded)
- **Author**: tzhouam (+ copilot analysis)
- **Date**: 2026-07-23
- **Discussion**: https://github.com/JiusiServe/InferMatrixCopilot/issues/3

## Summary

Give the copilot a trigger layer so it runs unattended against our GitHub repos — starting with automatic PR review, later issue answering/triage. Today every run is manually invoked. The headless building blocks exist; this RFC covers the trigger, the idempotency/trigger-ownership rules, the security hardening that must land first, and the rollout gates for letting it post.

## Motivation

- The copilot is now used beyond vllm-omni (AgentInfer, afd-plugin); issues #1/#2 came from that adoption and are fixed. Manual invocation is the remaining friction.
- Measured envelope (20-PR campaign, 3 generation replicates over the same 20 PRs — not 60 independent items): ~$0.19 and 6–13 min per review on the eco path; precision 0.777 ± 0.026, recall 0.430 ± 0.018, with documented context asymmetry vs the recorded baseline. Read: comments are usually right but coverage is partial — an *additional* reviewer, cheap enough to run on every PR; never a replacement for human review.
- Reviews that arrive minutes after a PR opens change author behavior; reviews that must be requested mostly don't happen.

## What already exists

- Headless one-shot: `-p "review <pr-url> and post the review" --yes`; URL/bare-ref routing is deterministic (no LLM intent call) and explicit post intent survives it (issue #1 fix).
- Double-gated outward writes: command must carry post intent AND `ALLOW_POST=1`; anything less is a dry run. Push safety (force-with-lease only, protected `main`) is unchanged and out of scope here.
- `pr.gate_check` reports draft/merge-state/failing CI — as review *context*, deliberately non-blocking. The trigger layer must do its own eligibility filtering (draft/closed/merged); it cannot lean on this step.
- Unattended failure path: `ESCALATION.md`, exit 3, escalation email.

## Prerequisite hardening (blockers before ANY auto-run)

Auto-run turns hostile PR/issue content from a theoretical input into a routine one, and the current posture has real gaps. These land first:

- **H1 — repo-bounded reads.** Today the agent's read tools resolve relative paths against the run's repo root but pass absolute paths through untouched, and `PathScope` bounds only writes. A prompt-injected review agent could read arbitrary host files (keys, `.env`) and quote them into its output. Fix: refuse absolute paths outside the run's root/worktree for `read_file`/`list_dir`/`grep`/`run_shell` cwd, and refuse `.env*`/key-material patterns (the jail chat's `repo_read` already has, applied to the step runtime).
- **H2 — outbound scrubber.** Before `pr.post_review` publishes, scan the body for credential-shaped strings (key prefixes, PEM headers, high-entropy tokens) and refuse/redact with an escalation. Defense in depth for exfiltration-via-comment; note `<untrusted_data>` fencing is prompt guidance, not an enforcement boundary — H1/H2 are the boundary.
- **H3 — least-privilege identity & isolation.** The poller must not use ambient `gh` auth (which may hold broad rights). Dedicated machine account + fine-grained PAT: selected repos only, PR read/write, nothing else — and the poller runs as a dedicated OS user whose environment holds only that PAT and its own LLM key, not the host's other credentials. This also puts a bot name on every posted comment.
- **H4 — no agent-controlled persistent writes in auto-run.** Review agents normally may propose skill candidates (`skill_update_candidate`); under auto-run that is an injection-to-persistent-state path, so knowledge-write tools are disabled for auto-triggered runs. Auto-runs are pure read + report; knowledge accrual stays a human-invoked flow.

## Design options

### A. GitHub Actions workflow in each target repo

`pull_request` (opened / ready_for_review) → install copilot → one-shot → post via repo token.

- Pros: event-driven, visible/re-runnable by the team, per-repo opt-in.
- Cons: fork PRs get no secrets and a read-only token on `pull_request`; `pull_request_target` would hand secrets to untrusted-PR-triggered runs — not acceptable before H1/H2 have soaked. Ephemeral runners reset the knowledge plane (debug memory, skill priors); only the committed profile briefing persists. LLM keys spread into each repo's Actions secrets.

### B. Poller on the copilot host (recommended start)

A `copilot-watch` script on a systemd timer on the machine already running the nightly rebase: per managed repo, list open PRs → eligibility filter → dedupe (below) → run one-shot → record + post (Phase 1+).

- Pros: inherits the full setup (checkouts, worktree cache) and the persistent knowledge plane; no LLM secrets exported to GitHub; ~100–200 lines; same operational pattern as the nightly rebase.
- Cons: trigger is invisible to the team (results aren't); single host; polling latency (below).

### C. GitHub App / webhook service — explicit non-goal

The productized form; real hosting + auth surface. Not at our scale.

## Proposal

**Phase 0 — report-only shadow (≥1 week).** Option B on team-nominated repos, H1–H4 landed. Shadow runs carry **no post intent at all** (a genuinely read-only TaskSpec — `ALLOW_POST=0` is the belt, not the mechanism). Reviews accumulate in run dirs; escalations email the operator. Humans adjudicate outputs (gate below).

**Phase 1 — posting.** Flip `ALLOW_POST=1` per repo that passes the gate. Posted via `gh pr comment` under the bot identity with a signature footer (`copilot-review: <repo> #<pr> @ <head-sha> / <config-digest>`). Known limitation, deliberate: a *comment*, not a GitHub review submission — no APPROVE/REQUEST_CHANGES state, no inline threads. Upgrading to `gh pr review` (and whether a bot may ever set blocking state) is a separate later proposal.

**Phase 2 — optional Actions front-end (sketch only).** For repos wanting team-visible triggers: same-repo PRs only (no `pull_request_target`), `/copilot review` comment command for re-runs with actor-permission validation before any secret use. **One trigger owner per repo**: a repo is served by the poller OR Actions, never both; migration moves ownership. Phase 2 is deliberately underspecified here — it gets its own RFC (trigger security, permission checks, workflow provenance) before any implementation; nothing in Phase 0/1 depends on it.

### Trigger & idempotency spec (Phase 0/1)

- **Eligibility**: open, non-draft, not merged/closed, opened after the repo's enablement timestamp (no historical backlog sweep).
- **Dedupe key**: `(repo, pr_number)` — a PR is auto-reviewed **once**, at first eligibility. New pushes (`synchronize`, force-push) do NOT re-trigger; re-review is on-demand only (`/copilot review`, keyed to the new head SHA, commenters with write permission only). This keeps cost and comment noise linear in PRs, not pushes.
- **Ledger is a cache; GitHub is the source of truth.** Transactional order: record `started` → run → re-resolve head SHA and PR state immediately before posting (advanced/closed ⇒ mark `stale`, don't post) → post → record `posted` + comment URL. On startup and on any crash-uncertainty, reconcile by querying the bot's signature comments — a crash between post and record therefore cannot double-post, and a `started`-but-dead entry retries instead of being suppressed. Record the reviewed SHA in the footer so humans can see review-vs-head drift.
- **Run states & limits**: ledger entries move `started → reviewed → posted | stale | failed | post_unknown`. `failed` retries at most twice with backoff, then escalates —  a crashing PR cannot burn budget every cycle; `post_unknown` (posted but unrecorded) is resolved only by the signature-comment query. Hard per-run timeout (kill at 30 min), daily cost circuit breaker (configurable, e.g. $10/day across repos), run-dir retention cap.
- **Queueing honesty**: reviews take 6–13 min; one worker, ≤4 new reviews per cycle, FIFO across repos. Latency is "~15 min under light load" and grows linearly in bursts — a queue-age alert (not just email) is part of the health story, alongside the existing `/status` and a weekly human glance at the ledger. API/rate-limit failures skip the cycle; ≥3 consecutive failures escalate by email.
- **Loop prevention**: the trigger ignores PRs and comments authored by the bot account or any `[bot]` actor — the copilot never triggers on its own (or another bot's) output.

### Phase-1 promotion gate (per repo)

Report-only output is adjudicated by the repo owner + one other reviewer (disagreements resolve toward the stricter label): each finding labeled useful / neutral / wrong. Promote when, over ≥15 PRs AND ≥30 findings: useful-rate ≥ 0.75, ≥50% of PRs got at least one useful finding (a mostly silent reviewer must not pass), zero critical-wrong findings (a "wrong blocker" that would have misdirected a merge), and no unresolved injection/exfiltration incident. Recall is tracked but not gated — the copilot is additive. Sign-off: repo owner. This is a judgment gate, not a significance test — the floors exist to make the rate meaningful, and the owner can hold a repo in shadow longer on any doubt.

### Policy defaults (debatable)

- Review depth `auto`; eco model path.
- Issue auto-answering: off in Phase 0/1; separate proposal with its own gate — wrong PR comments waste reviewer minutes, wrong issue answers mislead users.
- Write-capable kinds (pr_debug fixes, rebase pushes): permanently out of scope for auto-run.

## Security considerations

- Posting stays double-gated; auto-run changes *when* reviews run, not what they may do.
- Injection worst case (post-H1/H2): a wrong or hostile *comment* — which can itself trigger other repos' comment-bots; the bot identity (H3) lets other automation filter it, and the scrubber bounds exfiltration.
- Fork PRs: poller-only (H3 identity holds comment rights only); `pull_request_target` stays banned until explicitly revisited.
- Secrets: Phase 0/1 keep all LLM keys on the copilot host; Phase 2 adds them only to participating repos' Actions secrets.

## Rollback

- `systemctl stop` the timer **and** the service unit (terminating any active worker/run), then revoke the bot PAT ⇒ no new runs and no in-flight posts.
- Posted comments are NOT auto-retracted: rollback procedure includes bulk-minimizing the bot's comments (GraphQL `minimizeComment`) when the reason is quality/incident, and disabling `/copilot review` handling in config.
- Phase 2: delete the workflow file; trigger ownership reverts per repo.

## Open questions for the team

1. Which repos are in scope for Phase 0?
2. Is the promotion gate (useful ≥0.75 over ≥10 PRs / ≥20 findings, zero critical-wrong) right, and who besides the repo owner adjudicates?
3. Once-per-PR + on-command re-review: acceptable, or does anyone want re-review on every push despite the cost/noise?
4. Should `/copilot review` land in Phase 1 (poller reads comments) rather than waiting for Phase 2?
5. Who operates the poller host and owns the escalation inbox?
6. Comment vs GitHub-review submission: is the no-status limitation fine for Phase 1, or is inline/review-state support a requirement before anyone relies on it?

## Review record

Drafted with the copilot's analysis, then run twice through our external plan-review hook (gpt-5.6). Round 1 (verdict REVISE) surfaced, verified against source, and got folded: the absolute-path read gap (→ H1), the gate_check non-blocking misstatement, comment-vs-review-submission, the synchronize/ledger contradiction (→ once-per-PR keying), eval-caveat honesty, and the transactional posting order. Round 2 (verdict REVISE) added: skill-candidate writes as an injection path (→ H4), post-intent-free shadow runs, retry/timeout/cost limits, loop prevention, gate floors, and kill-active-workers rollback — all folded. Not adopted (logged for discussion, judged disproportionate at our scale): full container isolation with restricted egress, and blocking Phase 1 on GitHub-review- state posting. The reviewer's position on both is available on request.
