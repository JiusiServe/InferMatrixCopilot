# Metrics Research for Agent Tasks

Literature-grounded metric design for the five copilot agent tasks
(`pr_review`, `pr_debug`, `pr_rebase`, `issue_answer`, `issue_filter`).
Extends the existing RQS3/RQS3e work (eval/METRIC_V3.md) into a unified
Quality × Safety / Cost family. References verified against arXiv/venue pages
2026-07-06; **per owner request, all cited papers/benchmarks are from 2025 or
later** (venue or arXiv v1 date ≥2025). Where a metric idea originates in
older work (F2P/P2P splits, duplicate recall-rate@k, usefulness taxonomies),
we cite the ≥2025 work that carries it forward. Components tagged **[lit]**
(directly literature-supported) or **[ext]** (our proposed extension).

## Executive Summary

Recommended metric family: **Cost-Adjusted Task Quality (CATQ)** per task —

```
CATQ_task = Q_task · S / C        (higher is better)
```

where `Q_task ∈ [0,1]` is a task-specific weighted-arithmetic quality score
(never harmonic/product — METRIC_V3 lesson #3), `S ∈ [0,1]` is a safety
multiplier that decays **geometrically per incident** (nonlinear in count) and
hard-zeros on catastrophic events, and `C ≥ 1` is the log-scale cost index
already validated in RQS3e (Cost-of-Pass framing). A linear **Task Utility
Score** `TUS = Q − λ_C·(1−1/C) − λ_R·(1−S)` is kept as a dashboard view in
"utility units", but CATQ is the headline because a multiplicative safety gate
cannot be bought back with volume.

The main quality–cost tradeoff, per the literature (Cost-of-Pass, AI Agents
That Matter/HAL, our own ensemble campaign): marginal quality from
inference-time spend (ensembles, retries, bigger evidence packs) usually does
not justify its cost, and any scalar that divides by cost degenerates toward
the cheapest arm. So: log-discount cost (a 10× cost increase costs a fixed
decrement), publish the (Q, $) Pareto frontier alongside every scalar, rank
configs on **replicate means (≥3 runs)** only, and never optimize CATQ without
its guardrails (recall floor, escalation-rate band, zero critical incidents,
judge-κ health).

---

## 1. PR Review: `pr_review`

### 1.1 Relevant Papers and Benchmarks

| # | Paper / Benchmark | Year | Relevance | Metric Ideas Borrowed |
|---|---|---|---|---|
| 1 | CRScore: Grounding Automated Evaluation of Code Review Comments in Code Claims and Smells — Naik et al., NAACL | 2025 | Reference-free metric paper for exactly this problem; 2,900 human judgments; 0.54 Spearman w/ humans | **Comprehensiveness** (recall of diff-derived claims) + **conciseness** (fraction of comment grounded in a claim) = P/R over verifiable claims |
| 2 | c-CRAB: Code Review Agent Benchmark — Zhang et al. (NUS), arXiv 2603.23448 | 2026 | Each expected human finding paired with an **executable test**; agents ~40% | Test-based recall of ground-truth findings — no LLM judge, no string match (already cited by METRIC_V3) |
| 3 | BitsAI-CR: Automated Code Review via LLM in Practice — Sun et al. (ByteDance), FSE Industry | 2025 | Production reviewer, 12k WAU, detect-then-verify pipeline, 75% precision target | **Outdated Rate** — fraction of commented lines later edited by the developer: automatic, reference-free adoption proxy |
| 4 | Towards Practical Defect-Focused Automated Code Review — Lu et al., ICML Spotlight | 2025 | Review as *defect detection with repo context*, not text generation | Defect detection recall/precision on real MRs with full-repo context |
| 5 | CodeReviewQA — H. Y. Lin et al., Findings of ACL (arXiv 2503.16167) | 2025 | Decomposes review comprehension into change-type recognition, localization, solution identification (900 curated examples, 9 languages) | Graded sub-skill accuracy — score file/line **localization** separately from prose quality |
| 6 | SWR-Bench — arXiv 2509.01494 | 2025 | PR-level (not hunk-level) review-comment generation benchmark with LLM-based evaluation | PR-level evaluation framing; judged match against human review sets |
| 7 | Sphinx (arXiv 2601.04252) | 2026 | Decision-level review scoring incl. true negatives (basis of RQS3's `decision`) | Score the APPROVE/REQUEST-CHANGES **verdict** itself; "correctly no comment" is scoreable, not auto-zero |
| 8 | Automated evaluators vs developer labels (arXiv 2604.24525) | 2026 | Automated usefulness evaluators agree with developers at only 0.44–0.62, near-zero MCC | Components are weak signals — **weighted arithmetic aggregation**, never harmonic/product (RQS3 lesson #3) |
| 9 | "The Coin Flip Judge?" (arXiv 2606.13685) | 2026 | Pointwise LLM judgments flip across identical trials | **Multi-trial majority voting + anchored rubrics** for every judged component; report self-consistency κ |
| 10 | Survey of Code Review Benchmarks & Evaluation Practices, Pre-LLM and LLM Era (arXiv 2602.13377) | 2026 | Catalogue of exactly this design space | Metric-taxonomy completeness checklist for the suite below |

### 1.2 Existing Evaluation Patterns

Text-overlap metrics (BLEU/ROUGE) are discredited for review (one-to-many
problem; CRScore shows poor human correlation). The 2025–26 literature
converged on: (a) **precision/recall vs ground-truth issues**, ideally with
executable verification (c-CRAB) or repo-context defect sets (Lu et al.);
(b) **grounded claim coverage** rather than raw comment counts (CRScore's
comprehensiveness/conciseness); (c) **behavioral adoption** in deployment —
BitsAI-CR's Outdated Rate (commented lines later edited) — automatic and hard
to game; (d) explicit **false-positive burden** via precision-gated filter
stages (BitsAI-CR's 75% precision bar); (e) verdict-level correctness incl.
true negatives (Sphinx, already RQS3's `decision`); (f) LLM-judge components
only with multi-trial anchored juries and reported κ, because automated
usefulness evaluators agree with developers at only 0.44–0.62 (arXiv
2604.24525) and pointwise judges flip across trials (Coin Flip Judge). Our
RQS3 already implements (a), (e), (f) offline; the gap is (c)/(d) online
adoption and burden signals.

### 1.3 Proposed Metric

**RUS — Review Utility Score** (v5 of the RQS family). Each emitted comment is
classified into: **TB** (true blocker — validated defect that would break or
must change in this PR), **UNB** (useful non-blocking — valid minor/doc/test
ask a maintainer acts on), **NIT** (valid but optional polish), **FP** (invalid,
misread, or ungrounded). Missed defects come from GT coverage offline and an
escaped-defect scan online. Quality is a weighted arithmetic mean over five
components (recall, value-weighted precision, usefulness/adoption, severity
calibration, decision correctness incl. merge-break prevention); safety and
cost are the shared multiplier/index. Comment classes come from the 6-vote
validity jury + severity audit offline **[lit: METRIC_V3 protocol]**, and from
maintainer behavior online (resolved/reacted/ignored/refuted) **[lit:
BitsAI-CR Outdated Rate]**.

### 1.4 Formula

```
Q_rev = 0.30·recall_w + 0.25·precision_v + 0.15·useful + 0.10·calib + 0.20·decision

precision_v = max(0, Σ_c value(c)) / N          value: TB=1.0, UNB=0.6, NIT=0.1, FP=−1.0
recall_w    = Σ_g w(g)·cover(g) / Σ_g w(g)      (unchanged from RQS3: severity×resolution
                                                 weighted GT coverage; online proxy:
                                                 1 − escaped_defects_norm)
useful      = resolved_or_reacted_comments / posted_comments      (online; offline: 6-vote
                                                                   validity share)
calib       = 1 − MAE(sev_agent, sev_human)/3   (ordinal blocker=3…nit=0, labeled subset)
decision    = 1.0 verdict matches human outcome (REQUEST-CHANGES↔substantive change
              requests / APPROVE↔merged w/o substantive change); 0.5 no verdict; 0 mismatch.
              A TB that flags a would-be merge-breaking defect (CI red on merge or revert
              ≤14d in the flagged hunk) also increments `prevented` (reported, not summed). [ext]

RUS = Q_rev · S / C
```

- `N` = number of emitted comments (post code-side cap of 5). All components ∈
  [0,1]; **higher is better**. `precision_v` clamps at 0 so FPs cannot push Q
  negative — but each FP also burns 1/N of the numerator, which is the
  verbosity/over-reporting penalty **[ext]**.
- `S`, `C`: shared definitions (Cross-Task Framework). Review-specific risk
  events: wrong APPROVE on a PR that breaks on merge = **severe** (×0.5);
  posting past the gate (no `post` intent or `ALLOW_POST=0`) = **catastrophic**
  (S=0).
- Offline (benchmark PRs): all five components computable now; `useful` falls
  back to jury validity. Online: `recall_w` proxied by escaped defects (fix
  commits ≤30d touching hunks of a reviewed PR that the review missed) **[ext,
  adapted from BitsAI Outdated Rate]**.

### 1.5 Required Instrumentation

Already exists: per-step tokens and tool calls (`agent_output` events), wall
clock (event timestamps), ensemble metadata (`agent_ensemble`), gate report,
verdict text, RQS3 GT + jury pipeline, dry-run/post flags in RunTrace.

To add: (1) **USD conversion at runtime** — price table in `config.py`, USD
per run emitted in a `run_metrics` event; (2) **posted-comment IDs** recorded
on `pr.post_review`; (3) a **feedback collector** (cron/gh): per comment —
resolved/outdated (commented line edited in a later commit), reactions,
maintainer replies; per PR — merge outcome, post-merge CI status, reverts ≤14d
(this also serves pr_debug); (4) **severity labels** on a sampled subset
(human audit queue, ~20 comments/week); (5) escaped-defect scanner (git blame
of fix commits vs reviewed hunks).

### 1.6 Failure Modes and Guardrails

- **Silence gaming**: emitting nothing yields precision_v undefined and
  recall 0 — define precision_v=0.5 (neutral) when N=0 so silence can't buy
  precision, and recall_w keeps the pressure on. Guardrail: recall floor
  (recall_w ≥ 0.35 on the benchmark) below which RUS is not ranked.
- **Nit farming / over-reporting**: FPs at −1.0, NITs at 0.1, and the hard cap
  of 5 comments make volume unprofitable; monitor comments/PR and the
  doc-ask share (≤2 rule already in the prompt).
- **Severity inflation** (calling everything blocker to win `decision`):
  `calib` directly penalizes it; audit any run with blocker-share > 40%.
- **Judge drift**: all judged components require position-swapped multi-trial
  juries with κ reported; κ < 0.4 marks the component "unscored," never zero
  (METRIC_V3 lesson).
- **What it misses**: praise/mentoring value of review, and cross-PR patterns;
  accepted as out of scope.
- Guardrail metrics (monitored, never optimized): prevented-incident count,
  escaped-defect count, PR latency delta attributable to the bot,
  escalation-rate band.

---

## 2. PR Debug: `pr_debug`

### 2.1 Relevant Papers and Benchmarks

| # | Paper / Benchmark | Year | Relevance | Metric Ideas Borrowed |
|---|---|---|---|---|
| 1 | SWE-bench-Live — L. Zhang et al. (Microsoft), NeurIPS D&B (arXiv 2505.23419) | 2025 | 1,890 live post-2024 issues, monthly refresh, per-task Docker envs — the contamination profile of a real CI failure arriving today | **Resolved rate on dated post-cutoff slices**; auto-provisioned reproducible env = the "reproduce failing check" gate; carries the F2P/P2P protocol forward |
| 2 | Demystifying LLM-Based SE Agents (Agentless) — Xia et al., FSE (Distinguished Paper) | 2025 | Localization → repair → validation with per-phase measurement; cheap scaffold beats agents ($0.68/task) | **Per-phase scoring** (localization accuracy vs fix rate); **$/task next to accuracy** as the low-cost baseline to beat |
| 3 | UTBoost: Rigorous Evaluation of Coding Agents on SWE-Bench — B. Yu et al., ACL (arXiv 2506.09289) | 2025 | 345 "passing" patches were wrong; weak oracles flipped up to 40.9% of rankings | **Two-tier oracle**: augmented/generated tests re-validate every "passing" patch before success is declared |
| 4 | RePaCA: Static Automated Patch Correctness Assessment — Fuster-Pena et al., arXiv 2507.22580 | 2025 | Reasoning-LLM judge separates root-cause fixes from test-overfitting patches (83% acc) | **Patch-correctness classification (correct vs overfitting)** layered on top of test results |
| 5 | OpenRCA: Can LLMs Locate the Root Cause of Software Failures? — J. Xu et al. (Microsoft), ICLR | 2025 | 335 real failures with logs/metrics/traces; scores root-cause identification in isolation | **All-or-nothing root-cause matching** (component + reason) as its own scored stage |
| 6 | SWE-PolyBench — Rashid et al. (Amazon), arXiv 2504.08703 | 2025 | 2,110 multi-language repo tasks; syntax-tree metrics check *where* the agent edited | **CST-node localization precision/recall** — "found the root cause" scored separately from "tests green" |
| 7 | SWE-smith: Scaling Data for SE Agents — J. Yang et al., NeurIPS D&B Spotlight | 2025 | Synthesizes known-root-cause bugs by breaking existing tests in *your own repo* | **Injected-bug eval set minting**: private, contamination-free CI-failure benchmark from vllm-omni itself |
| 8 | SWE-Effi — Z. Fan et al., arXiv 2509.09853 | 2025 | Re-scores agents on outcome *and* resources; flags token snowballing and expensive failures | **Resolve-rate-vs-budget AUC**; track **cost-of-failure** (tokens burned on unresolved groups), not just cost of success |
| 9 | Cost-of-Pass — Erol et al., arXiv 2504.13359 | 2025 | Expected $ per correct solution vs a human-expert baseline | **Cost per resolved failure group** as the go/no-go economic metric |
| 10 | SWE-Lancer — Miserendino et al. (OpenAI), arXiv 2502.12115 | 2025 | Real freelance tasks priced $50–$32k; grading by dollar value | **Value-weight fixes** by recovered engineer time / unblocked-merge cost instead of counting failures equally |

### 2.2 Existing Evaluation Patterns

The 2025 literature scores fixing as an execution-graded, **phase-decomposed**
ladder: resolved rate with the F2P/P2P protocol on live post-cutoff task
slices (SWE-bench-Live; SWE-bench Pro's held-out splits), root-cause
identification and localization scored separately from repair (OpenRCA;
SWE-PolyBench CST metrics; Agentless per-phase reporting), and a mandatory
patch-validity audit because weak test oracles let wrong patches "pass" —
UTBoost showed this flips up to 40.9% of rankings, and RePaCA classifies
correct-vs-overfitting patches statically. Cost reporting became structural:
$/task next to accuracy (Agentless), resolve-rate under token/time budgets
plus cost-of-failure (SWE-Effi), expected $ per correct solution vs a human
baseline (Cost-of-Pass), and dollar-value weighting of fixes (SWE-Lancer).
Explanation quality still has no canonical benchmark; practice is
multi-trial rubric judging cross-checked against objective proxies.

### 2.3 Proposed Metric

**DUS — Debug Utility Score**: a stage-weighted quality ladder over the eight
distinguishable outcomes (reproduced → root cause → compiles → original
failure fixed → no regressions → CI green → accepted → well-explained), where
execution-grounded stages carry most weight and judged stages least. CI usage
is priced into cost (each debug push triggers a Buildkite run). A pushed
regression is double-counted by design: it zeroes the P2P quality component
*and* fires a severe risk event — quality loss and safety are different
failures **[ext]**.

### 2.4 Formula

Per failure group g (the playbook's fan-out unit), then averaged over groups:

```
Q_dbg(g) = 0.10·repro + 0.10·rootcause + 0.05·builds + 0.30·F2P
         + 0.20·P2P + 0.15·accepted + 0.10·explain

repro     ∈ {0,1}  failing check reproduced locally before patching (tests_run
                    evidence in the output contract shows the failure)
                    [lit: SWE-bench-Live reproducible-env gate]
rootcause ∈ {0,1}  root_cause field names the true faulty file/component —
                    audited, or auto-credited if the fix touching exactly that
                    location made F2P=1 [lit: OpenRCA root-cause matching,
                    SWE-PolyBench localization; ext: auto-credit rule]
builds    ∈ {0,1}  patch compiles / imports / lints
F2P       ∈ [0,1]  fraction of the group's originally-failing checks now green
                    [lit: F2P/P2P protocol as carried by SWE-bench-Live]
P2P       ∈ {0,1}  no previously-green check newly red on the debug push [lit: same]
accepted  ∈ {0,1}  fix commit survives 14 days with no revert and no maintainer
                    rewrite of its hunks                                          [ext]
explain   ∈ [0,1]  anchored-rubric judged quality of root_cause/fix_summary/
                    verification contract fields (2 judges, position-swapped,
                    mean; κ reported) [lit: multi-trial judge protocol,
                    Coin Flip Judge]

Q_dbg = mean_g Q_dbg(g);   escalated group (honest failure, ESCALATION.md) → Q_dbg(g)=0.25 fixed [ext]

DUS = Q_dbg · S / C,   C's USD includes ci_minutes · ci_rate for every push-triggered build [ext]
```

All components higher-better. Ladder stages are cumulative in practice but
scored independently so partial credit is well-defined (e.g. correct diagnosis
+ failed fix = 0.20). Risk events: pushed regression = **severe**; force-push
attempt (playbook forbids it) or test-weakening patch shipped (see guardrail)
= **catastrophic** (S=0); out-of-scope edit shipped = **moderate**.

### 2.5 Required Instrumentation

Already exists: failure signatures and grouping (`pr.group_failures`),
tests_run/root_cause/fix_summary/verification in the output contract, tokens
and tool calls per agent step, patch-gate verdicts, push events, escalations.

To add: (1) **CI minutes** per triggered build (Buildkite REST — the stubbed
log-download client can also fetch build duration); (2) **check-state
snapshot** before/after the debug push to compute F2P/P2P deterministically
from `gh pr checks` (currently only failing checks are captured); (3)
**patch-suspicion flags** computed on the diff (test files edited, `skip`
markers added, assertions deleted, >200 deleted lines) → route to human audit,
F2P not credited until cleared — optionally backed by a RePaCA-style
correct-vs-overfitting LLM judge **[lit: UTBoost; RePaCA]**; (4) revert/rewrite
scanner (shared with pr_review's feedback collector); (5) explanation-judge
job over the run dir.

### 2.6 Failure Modes and Guardrails

- **Overfitting patches** (delete the test, skip the case, loosen the
  threshold): the single most documented failure — weak oracles let wrong
  patches "pass" (UTBoost). Guardrail: suspicion flags block F2P credit
  pending audit; test-weakening that ships = catastrophic.
- **Symptom-patching**: F2P passes but root cause remains. Mitigation:
  `accepted` (14-day survival) and recurrence tracking — same failure
  signature reappearing ≤30d retroactively zeroes that group's F2P in the
  dashboard trend **[ext]**.
- **Regression laundering**: pushing many small commits so a regression looks
  like a flake. P2P is computed against the pre-run snapshot, not
  per-commit; known-flaky signatures (debug memory) excluded from P2P both
  ways.
- **Explanation verbosity**: `explain` rubric is length-normalized and capped
  at 0.10 weight; execution stages dominate.
- **Escalation farming**: 0.25 for honest escalation is deliberately below any
  half-successful fix; escalation-rate band (2–15%) alarms both directions.
- **What it misses**: fix elegance/maintainability — partially proxied by
  patch minimality (report median diff size as a guardrail, don't score it).

---

## 3. PR Rebase: `pr_rebase`

### 3.1 Relevant Papers and Benchmarks

| # | Paper / Benchmark | Year | Relevance | Metric Ideas Borrowed |
|---|---|---|---|---|
| 1 | Merge-Bench: Resolve Merge Conflicts with LLMs — Schesch & Ernst, ICPR 2026 (arXiv 2605.25890) | 2026 | 7,938 real conflict hunks, 1,439 repos; GT = developer-committed resolution; best models <60% | **Test-free exact/normalized match vs the human resolution** (test-based reward is gameable); zero-label GT mining — same pipeline builds a vllm-omni set |
| 2 | GitGoodBench — Lindenbauer, Bogomolov, Zharov (JetBrains), arXiv 2505.22583 | 2025 | Only benchmark scoring *agents operating git itself*, incl. conflict scenarios; GPT-4o solves 21% | **Scenario-level solve rate**: the repo must end in a correct state, not just emit resolution text |
| 3 | Rover: Context-aware Conflict Resolution with LLM — Q. Zhang et al., arXiv 2605.17279 | 2026 | Cross-file dependency context fixes the hunk-local failure mode of large rebases | **Three-tier similarity** (character/lexical/semantic) vs GT instead of binary exact-match |
| 4 | LLM-based vs Search-based Merge Conflict Resolution — Campos Junior & Murta, EMSE (arXiv 2605.16646) | 2026 | LLMs win on imbalanced conflicts, degrade on large inputs; argues hybrid fallback | **Stratified accuracy by conflict characteristics** (size, balance, language); know when to fall back to deterministic strategies |
| 5 | AgenticFlict — Ogenrwot & Businge, AIware 2026 (arXiv 2604.03551) | 2026 | 142K agent-authored PRs; 27.67% conflict rate — base rates for agent-caused conflicts | **Merge-simulation conflict rate** of the agent's own pushes as a safe-push health metric |
| 6 | RefFilter: Refactoring-Aware Semantic Conflict Detection — Lira, Borba et al., arXiv 2510.01960 | 2025 | Detects *behavioral* interference in textually clean merges; −32% false positives | **Semantic-interference P/R** as a separate axis from textual resolution correctness |
| 7 | Example+Rule-Based Transformations for Build Conflicts — Towqir et al., arXiv 2507.19432 | 2025 | Conflicts that surface only at build time after a clean merge (import drift, signature changes) | **Build-success-after-merge** as its own pass/fail gate |

### 3.2 Existing Evaluation Patterns

2025–26 practice scores merges on three separate axes. (a) **Resolution
accuracy vs the developer's committed resolution** at hunk granularity, mined
from history with no manual labels (Merge-Bench) — explicitly *test-free*
because test-suite reward is gameable; graded similarity tiers (Rover) replace
binary exact-match; and accuracy is stratified by conflict size/balance/
language because aggregates hide the hard tail where LLMs degrade (EMSE 2026
study, which also motivates deterministic fallbacks). This GT is directly
mineable from vllm-omni's own `dev/vllm-align` regenerations. (b) **Process/
end-state correctness**: agentic benchmarks (GitGoodBench) score whether the
agent driving real git leaves the repo in a correct state — ~21% solve rates
for strong models justify treating abstention as a respectable outcome — and
AgenticFlict measures whether agent pushes *create* downstream conflicts.
(c) **Behavior preservation as its own axis**: semantic interference behind
textually clean merges (RefFilter) and build-only conflicts (Towqir et al.)
are scored as separate gates from textual resolution accuracy.

### 3.3 Proposed Metric

**RBUS — Rebase Utility Score**: layered quality (completed → conflicts
correct → tests pass → scope-pure) with an explicit **safe-abstain outcome**
scored at a fixed 0.35 — above any incorrect rebase, below any decent success —
so the agent is never pressured into a wrong merge **[lit: precision-first;
ext: the fixed abstain score]**. Push safety is binary and mostly a risk gate,
since the push guard already enforces it structurally.

### 3.4 Formula

```
Q_rb = 0.20·completed + 0.30·conflict + 0.25·tests + 0.15·purity + 0.10·push_safe

completed ∈ {0,1}   rebase replayed all PR commits onto latest base and pushed
conflict  ∈ [0,1]   offline: per-hunk match to the human resolution — exact, else graded
                    similarity tiers (character/lexical/semantic, Rover-style), reported
                    per size/balance stratum [lit: Merge-Bench; Rover; EMSE 2026]
                    online: 1 − (conflict hunks re-edited by a human ≤7d / conflict hunks) [ext]
tests     ∈ [0,1]   build success + per-module verification + CI pass on the rebased head
                    [lit: Towqir build gate; GitGoodBench end-state correctness]
purity    ∈ [0,1]   1 − unexpected_changed_lines / total_changed_lines, where expected =
                    three-dot replay delta (PR diff vs new base); lines outside conflict
                    regions and outside the PR's own diff are "unexpected" [ext]
push_safe ∈ {0,1}   --force-with-lease, PR head branch only, lease not stale

Safe abstain (conflict agent aborts, workspace restored, escalation filed): Q_rb = 0.35 fixed.
RBUS = Q_rb · S / C
```

Higher is better everywhere. Risk events: push to any non-PR-head or protected
branch, or lease violation losing commits = **catastrophic** (S=0; also
structurally prevented); semantic behavior change discovered after merge
(revert/bug traced to a resolved hunk) = **severe** **[lit: RefFilter's
semantic-interference axis]**; new-token resolution (code from neither side)
shipped unaudited = **moderate** **[lit: EditFusion, ASE 2025 — 94% of real
resolutions select existing edits rather than write new code]**.

### 3.5 Required Instrumentation

Already exists: `rebase_conflict` events, per-module verify results, patch
gate, push policy events, workspace-restore on abort, escalations.

To add: (1) **per-hunk conflict records** — file, region, ours/theirs/base,
agent resolution — written to the run dir (currently only the event is
traced); (2) the **expected-replay diff** (compute `git diff base...pr_head`
before rebase; after rebase, diff against it for `purity`); (3) **new-token
rate** per resolution (tokens absent from ours∪theirs∪base); (4) offline GT
miner: walk historical vllm-omni rebase commits, extract (conflict, human
resolution) pairs Merge-Bench-style; (5) post-merge tracker linking reverts to
resolved hunks (shared feedback collector).

### 3.6 Failure Modes and Guardrails

- **Abstain farming**: always escalating scores a safe 0.35 forever. Guardrail:
  completion-rate floor on the offline benchmark (agent must beat trivial
  "always abort") and the escalation band; the 0.35 is below the historical
  mean Q_rb of completed runs by construction — recalibrate if not.
- **Purity gaming by minimal-but-wrong resolutions** (e.g. always "take
  ours"): `conflict` correctness vs human GT catches it; report the
  keep-ours/keep-theirs/interleave/new-code mix (EditFusion-style edit-
  selection taxonomy) — a degenerate mix is visible even before scores move.
- **Tests as weak oracle**: vllm-omni's local pipeline tests cover modules
  unevenly; `tests` alone can pass a semantically wrong merge — exactly the
  class RefFilter targets. That is why `conflict` (0.30) outweighs `tests`
  (0.25), and the guardrail is the post-merge revert tracker. Merge-Bench's
  test-free stance is the same warning from the other direction.
- **Complexity masking**: aggregate accuracy dominated by trivial hunks —
  always publish per-stratum `conflict`, never just the mean.
- **What it misses**: performance regressions with green tests; covered only
  by the parent pipeline's benchmark phases, out of scope here.

---

## 4. Issue Answer: `issue_answer`

### 4.1 Relevant Papers and Benchmarks

| # | Paper / Benchmark | Year | Relevance | Metric Ideas Borrowed |
|---|---|---|---|---|
| 1 | SWE-QA: Can LLMs Answer Repository-level Code Questions? — Peng et al., arXiv 2509.14635 | 2025 | Closest task match: 720 QA pairs distilled from 77k GitHub issues, cross-file multi-hop repo reasoning | Two-level question taxonomy (what/why/how/where) for **stratified reporting**; long-form judging vs curated references |
| 2 | CodeRepoQA — Hu et al., SIGIR | 2025 | 585K multi-turn dialogues from real GitHub issues, 30 repos, 5 languages | **Multi-turn evaluation with issue-thread history**; medium context beats maximal — a retrieval-budget guideline |
| 3 | HalluLens: LLM Hallucination Benchmark — Bang et al. (Meta), ACL | 2025 | Extrinsic (invented repo facts) vs intrinsic (contradicts cited source) hallucination taxonomy | Dynamic test generation against leakage; score **hallucination rate and false-refusal rate as a pair** |
| 4 | FaithBench — Bao et al. (Vectara), NAACL | 2025 | Human-adjudicated *hard* hallucinations where detectors disagree (best ~50% acc) | 3-way label: Unwanted / Benign (world-knowledge) / Questionable — richer than binary faithful/unfaithful for answers mixing repo facts with general knowledge |
| 5 | Mu-SHROOM — Vázquez, Mickus et al., SemEval-2025 Task 3 | 2025 | Hallucination detection as **span labeling** inside the generated answer | Character-level span scoring against soft multi-annotator probabilities — highlight *which spans* of a draft are unsupported |
| 6 | FaithJudge: Benchmarking LLM Faithfulness in RAG with Evolving Leaderboards — Tamber et al. (Vectara), arXiv 2505.04847 | 2025 | Direct methodology for scoring RAG faithfulness of answers against retrieved context | **Few-shot judge anchored on human-annotated hallucination exemplars** instead of zero-shot judging |
| 7 | HealthBench — Arora et al. (OpenAI), arXiv 2505.08775 | 2025 | 48,562 expert-written, conversation-specific rubric criteria for open-ended answers | **Per-example weighted rubric** with named axes (accuracy, instruction-following, context-seeking) instead of one holistic judge score |
| 8 | StackRepoQA — Alebachew et al., arXiv 2603.26567 | 2026 | 1,318 real developer questions over 134 repos; separates memorized SO answers from repo-grounded reasoning | **Memorization-vs-reasoning ablation** (verbatim-reproduction check) as a contamination control |
| 9 | The Coin Flip Judge? — arXiv 2606.13685 | 2026 | Single-shot judging of drafts is unstable (~13.6% verdict flips) | Repeated trials + position swap; report **judge flip-rate** as the uncertainty bar |

### 4.2 Existing Evaluation Patterns

2025-era grounded-QA evaluation scores **claims, not answers**: hallucination
is located at span/claim level (Mu-SHROOM; FaithJudge entailment of each
statement against retrieved context), with severity tiers distinguishing
unwanted fabrications from benign world-knowledge additions (FaithBench) —
because one hallucinated API name in a copy-pasteable reply matters.
Hallucination rate is always reported *with* the abstention/false-refusal rate
(HalluLens): an agent that answers less hallucinates less, so both curves are
required. Open-ended answer quality moved to per-example weighted rubrics
(HealthBench pattern) over holistic 1–10 judging, and judge components need
multi-trial, position-swapped protocols with flip-rate reported (Coin Flip
Judge; Judging the Judges). Repo-QA benchmarks (SWE-QA, CodeRepoQA,
StackRepoQA) add two domain lessons: verify questions actually require the
repository (memorization ablation), and expect multi-turn issue-thread
context. A repo-specific pitfall: gold answers rot as the repo moves (an
answer correct at vLLM 0.19 is wrong at 0.24) — pin eval issues to commit
hashes.

### 4.3 Proposed Metric

**AUS — Answer Utility Score**: four quality components (correctness,
groundedness, completeness, helpfulness) with hallucination rate reported as
its own headline (`H = 1 − grounded`), a fixed calibrated-abstention score,
and posting risk in the safety multiplier. Groundedness is computable fully
automatically (FaithJudge-style exemplar-anchored entailment over atomic
claims vs the cited repo snippets) — the low-cost proxy — while correctness/
helpfulness need the maintainer-grounded or audited signals.

### 4.4 Formula

```
Q_ans = 0.35·correct + 0.30·grounded + 0.15·complete + 0.20·helpful

correct  ∈ [0,1]  offline: judged equivalence to the maintainer's actual reply on
                  resolved historical issues (2 judges, swap, κ) [lit]
                  online: 1 if no maintainer correction/contradiction follows the
                  posted answer, 0 if corrected [ext]
grounded ∈ [0,1]  fraction of atomic claims entailed by their cited repo evidence
                  (file:line, doc section), judged by an exemplar-anchored few-shot
                  entailment judge; claims with no citation count as unsupported
                  [lit: FaithJudge; Mu-SHROOM span framing]
                  H = 1 − grounded reported separately as hallucination rate,
                  always next to the abstention rate [lit: HalluLens]
complete ∈ [0,1]  fraction of distinct questions/asks in the issue addressed
                  (question extraction is deterministic-ish: LLM-extracted once,
                  cached with the eval item) [ext]
helpful  ∈ [0,1]  online: 1.0 issue closed/resolved by the answer or author thanks;
                  0.6 author engages constructively; 0.2 ignored; 0 negative reaction [ext]
                  offline: per-issue weighted rubric (root cause named, correct file
                  cited, workaround safe, no fabricated APIs) [lit: HealthBench pattern]

Calibrated abstention ("cannot verify in repo", escalate): Q_ans = 0.30 if audit agrees
evidence was genuinely insufficient, else 0.10.
[ext; HalluLens's paired hallucination/false-refusal axes are the rationale]

AUS = Q_ans · S / C
```

Higher is better. Risk events: posted answer with H > 0.3 (mostly ungrounded)
= **moderate**; posted factually wrong advice that a user follows into breakage
(maintainer flags it) = **severe**; wrong security-relevant advice or posting
past the gate = **catastrophic** (S=0).

### 4.5 Required Instrumentation

Already exists: draft text, evidence pack with the repo snippets the agent
actually retrieved, citations (the review-style contract can carry
`evidence`), gated post events, tokens/time.

To add: (1) **claim extractor + NLI entailment job** over drafts (one cheap
LLM pass; cache per run) producing `grounded`/H; (2) **posted-comment IDs** +
issue-thread watcher (close events, reactions, replies, maintainer
corrections); (3) an **atomic-claims audit sample** (~10 answers/week) to
calibrate the entailment judge against human groundedness labels — these
audited exemplars also become the judge's few-shot anchors (FaithJudge
pattern); (4) offline set of
resolved issues with maintainer answers, pinned to commit hashes.

### 4.6 Failure Modes and Guardrails

- **Evasion gaming**: maximally hedged answers score high `grounded` but low
  `complete`/`helpful`; the two-axis split is the countermeasure — monitor
  the abstention rate against its band.
- **Citation stuffing**: citing real files that don't support the claim —
  exactly what entailment checking (not link-resolution) catches; citation
  precision is inside `grounded`.
- **Verbosity bias in judged helpfulness**: length-normalized rubric,
  position-swapped pairs; online signals (issue closed, author reaction) are
  immune and preferred.
- **Entailment-judge drift**: the automated groundedness score is a proxy —
  FaithBench shows even the best detectors hit ~50% on hard cases; the weekly
  human calibration sample guards it, and proxy-vs-human κ is a dashboard
  health metric.
- **Stale ground truth**: eval issues pinned to commit hash; re-validate
  references when the set is reused after a rebase cycle.

---

## 5. Issue Filter / Triage: `issue_filter`

### 5.1 Relevant Papers and Benchmarks

| # | Paper / Benchmark | Year | Relevance | Metric Ideas Borrowed |
|---|---|---|---|---|
| 1 | Applying LLMs to Issue Classification: Revisiting with Extended Data and New Models — Aracena et al., arXiv 2506.00128 (SCP) | 2025 | Fine-tuned GPT-4o vs DeepSeek R1 on issue type labels (NLBSE data): F1 80.7% vs 59.3%; 10× more data didn't help; 4o-mini matched 4o at ~1/10 cost | Per-label + averaged **F1 on a frozen split, reported jointly with inference cost per issue** (accuracy-per-dollar) |
| 2 | Automated Duplicate Bug Report Detection in Large Open Bug Repositories — Laney et al., IEEE COMPSAC (arXiv 2504.14797) | 2025 | Six textual methods for duplicate detection; high-70s–low-90s accuracy | **Threshold-based duplicate decisions instead of top-k lists** — a confidence cutoff the agent can act on autonomously |
| 3 | GitBugs — Patil et al., arXiv 2504.09651 | 2025 | 150k+ bug reports, 9 projects, duplicate annotations, frozen train/test splits | **Recall-rate@k on frozen splits** with per-project duplicate-rate baselines for cross-repo comparability |
| 4 | Automated Bug Report Prioritization in Large Open-Source Projects — Pierson & Moin, arXiv 2504.15912 | 2025 | Priority prediction on 85,156 Eclipse reports at realistic class imbalance | **Per-priority-class P/R/F1 with macro-averaging** so rare high-priority classes aren't drowned out |
| 5 | Triangle: Empowering Incident Triage with Multi-Agent — Yu et al. (Microsoft), ASE | 2025 | Deployed multi-LLM-agent incident routing on real cloud incidents | Routing **accuracy paired with Time-to-Engage** (up to 97% / −91% TTE): score the operational latency of wrong routing, not just the label |
| 6 | Past, Present, and Future of Bug Tracking in the Generative AI Era — Torun et al., ACM TOSEM SI (arXiv 2510.08005) | 2025 | Roadmap for agent-driven bug tracking (refinement, reproduction, dedup, validation) | **Component-wise pipeline evaluation** rolled up to end-to-end maintainer-burden reduction |
| 7 | Evaluating LLMs for Security Bug Report Prediction — Soltaniani et al., arXiv 2601.22921 | 2026 | Cost-sensitive triage label where FN is expensive: prompted models recall 74%/precision 22%; fine-tuned precision 75%/recall 36% | **G-measure + explicit asymmetric error analysis**; report the recall–precision–latency trade-off per deployment mode |

### 5.2 Existing Evaluation Patterns

2025-era triage evaluation makes **cost a first-class metric**: the NLBSE-
lineage and security-bug studies rank models on F1 jointly with API cost and
latency, repeatedly finding small/fine-tuned models within a few F1 points of
frontier models at 10–50× lower cost. Duplicate detection moved from ranked
lists a human picks from to **confidence-threshold decisions** (Laney et
al.), which makes coverage × precision-at-threshold the operative agent
metric. Frozen public splits with per-project base rates are expected
(GitBugs), imbalanced tasks are reported with macro/per-class F1 or G-measure
rather than accuracy (Pierson & Moin; Soltaniani), and industrial deployments
grade **operational outcomes** — Time-to-Engage, reassignment cycles
(Triangle) — over classification scores. Cost asymmetry remains the loudest
warning: wrongly dup-marking or closing a real issue silently loses a defect
and alienates the reporter; missing a duplicate costs a maintainer a glance.
Settled (not initial) labels serve as ground truth because live triage is
itself noisy, and splits must be chronological because issue streams are
non-stationary — modules and label sets drift, especially mid-rebase.

### 5.3 Proposed Metric

**TQS — Triage Quality Score**: five components (label F1, routing, duplicate
detection precision-weighted, priority calibration with asymmetric cost,
maintainer acceptance as the burden-reduction proxy), evaluated at the
confidence-gated operating point, with FP-on-destructive-suggestions in the
safety multiplier. Everything is computable from GitHub metadata plus the
agent's triage table — no judges needed except for sampled audits — making
this the cheapest task to instrument end-to-end.

### 5.4 Formula

```
Q_tri = 0.30·label_F1 + 0.20·route + 0.20·dup + 0.15·prio + 0.15·accept

label_F1 ∈ [0,1]  macro-F1 of predicted type labels vs FINAL settled maintainer labels
                  (issues re-labeled ≤90d excluded from GT) [lit: Aracena F1-with-cost]
route    ∈ [0,1]  Top-1 module/owner accuracy (Top-3 reported alongside)
                  [lit: Triangle routing accuracy]
dup      ∈ [0,1]  F_0.5 over threshold-gated duplicate marks (precision-weighted: β=0.5),
                  with recall-rate@5 of the candidate list reported alongside
                  [lit: Laney threshold framing; GitBugs recall-rate@k;
                  ext: the F_0.5 choice encodes the FP≫FN cost asymmetry]
prio     ∈ [0,1]  1 − Σ cost(ŷ,y)/Σ cost_max, ordinal cost matrix where
                  under-prioritizing by k levels costs 3k and over-prioritizing costs k
                  (missing a critical bug ≫ crying wolf) [lit: Soltaniani asymmetric-error
                  analysis; Pierson & Moin macro per-class framing; ext: the 3:1 matrix]
accept   ∈ [0,1]  fraction of triage rows the maintainer applies without edits ≤7d
                  (burden-reduction proxy; Triangle's TTE/reassignment framing) [lit-adapted]

Confidence gating: rows below the confidence threshold are "suggestions" and are
excluded from label_F1/route/dup but capped at 60% of rows (coverage floor).
[lit: Laney's threshold-decision framing — coverage × precision at the operating point]

TQS = Q_tri · S / C
```

Higher is better. Risk events: duplicate-mark or close-recommendation on a
real unique issue that a maintainer follows = **severe**; any auto-close
action (if ever enabled) that is wrong = **catastrophic** (S=0); systematic
under-prioritization of a critical-labeled class = **moderate** per audit
window.

### 5.5 Required Instrumentation

Already exists: the triage-table output contract (type/module/priority/labels
per issue), read-only gh tools, tokens/time, gated posting.

To add: (1) **settled-label snapshotter**: for each triaged issue, capture the
label/assignee/duplicate state at +90d as GT; (2) per-row **confidence field**
in the triage contract; (3) **maintainer-diff job**: compare applied labels vs
suggested (accept/edit/ignore per row); (4) chronological benchmark split
builder over vllm-omni's issue history; (5) duplicate GT from GitHub's
"marked as duplicate" timeline events.

### 5.6 Failure Modes and Guardrails

- **Majority-class gaming** (label everything "bug"): macro-F1 (not accuracy)
  plus per-class F1 on the dashboard.
- **Confidence-gate abuse** (mark everything low-confidence to only answer
  easy rows): the 60% coverage floor, and report the full coverage/accuracy
  curve so the operating point is a choice, not a hiding place.
- **Duplicate over-marking**: F_0.5 plus the severe risk event for a followed
  wrong dup-mark; destructive suggestions require the highest confidence tier.
- **Priority inflation** (everything critical to dodge the 3× under-cost):
  the cost matrix charges over-prioritization too (1×), and the blocker-share
  audit from pr_review applies here as priority-share monitoring.
- **GT noise**: settled labels are themselves imperfect — live triage is
  noisy and reassignment-heavy (Triangle's motivating data) — so maintain a
  small re-labeled gold subset with inter-annotator agreement before trusting
  historical labels.

---

## Cross-Task Metric Framework

Anchor references (all ≥2025): Cost-of-Pass (Erol et al., arXiv 2504.13359,
2025) for the economic denominator; HAL — Holistic Agent Leaderboard (Kapoor,
Stroebl et al., arXiv 2510.11977, ICLR 2026) for cost-controlled Pareto
comparison; AI Agents That Matter (Kapoor et al., TMLR May 2025) for joint
cost+accuracy reporting; SWE-Effi (arXiv 2509.09853, 2025) for
resolve-under-budget AUC and cost-of-failure; τ²-bench (Barres et al., arXiv
2506.07982, 2025) for pass^k reliability; SHADE-Arena (Kutasov et al.,
Anthropic, arXiv 2506.15740, 2025) for incident-gated safety scoring;
Judging the Judges (arXiv 2604.23178, 2026) and The Coin Flip Judge (arXiv
2606.13685, 2026) for judge-reliability protocol; Terminal-Bench (arXiv
2601.11868, 2026) for leaderboards with per-run cost columns.

**Common quality dimensions** (each task's Q is a weighted arithmetic mean of
its instantiations): correctness of the primary artifact (comments/patch/
resolution/answer/labels) · coverage/recall of what should have been found ·
grounding/validity (precision) · calibration (severity/priority/confidence) ·
human adoption (resolution, acceptance, survival, reaction).

**Common cost dimensions**: model tokens → USD (price table) · tool calls and
wall-clock minutes · CI minutes triggered · human time consumed (review of
escalations, audits) — the first three metered, the last estimated.

**Common risk dimensions**: gate/scope violations (catastrophic) · shipped
regressions/wrong merges/wrong advice followed (severe) · out-of-scope edits,
unaudited new-code resolutions, mostly-ungrounded posts (moderate) · recorded
near-misses (minor; e.g. `tool_refused`, patch-gate `revise`).

**Generic formula** (all tasks):

```
Q_task ∈ [0,1]      weighted arithmetic mean of task components (weights above)
C      = (1 + log10(1 + usd/usd_ref)) · (1 + log10(1 + min/min_ref))      ≥ 1, lower better
         usd includes tokens, judge calls, and CI minutes · rate  [lit: Cost-of-Pass; RQS3e]
S      = 0 if any catastrophic event, else Π_c s_c^(n_c)                  ∈ [0,1], higher better
         s_severe=0.5, s_moderate=0.8, s_minor=0.95; geometric in count = nonlinear:
         two severe incidents cost 75%, not 2×25%
         [ext; incident-gated scoring per SHADE-Arena's success × no-sabotage pattern]

CATQ_task = Q_task · S / C          (headline, higher better)
TUS_task  = Q_task − 0.3·(1 − 1/C) − 0.7·(1 − S)     (dashboard utility view) [ext]
```

Normalization: per-task reference budgets `usd_ref`/`min_ref` are explicit,
env-overridable deployment assumptions (RQS3e precedent): review $1/10 min;
debug $3/30 min (CI-heavy); rebase $3/30 min; answer $0.30/5 min; triage
$0.10/2 min per issue. At the reference cost the discount is ~23%; an order of
magnitude over costs one further log step — cheap arms are compared on
quality, expensive arms must justify themselves (HAL's cost-controlled
principle). Scores aggregate as **replicate means (≥3)** offline and rolling
30-day means online; pass^k-style dispersion (τ²-bench) is reported next to
every mean.

**Task-specific adaptations**: safe-abstain fixed scores (rebase 0.35, answer
0.30, debug-escalation 0.25) implement "escalation beats confident error"
without making abstention profitable; pr_review has no abstain score (an empty
review is scored by its recall/decision); issue_filter adapts via the
confidence gate instead. Ensembles change only C (more tokens), never Q's
definition — so ensemble-vs-single is a fair CATQ comparison (this is exactly
the RQS3e ensemble question).

## Recommended Dashboard

One row per task, one column per field; sparklines for trends. Sourced from a
per-run `metrics.json` (emitted by a new `omni_copilot/metrics.py` collector
over RunTrace) plus the feedback-collector store.

- **Per-task score**: CATQ (headline) and TUS, 30-day rolling mean ± dispersion.
- **Quality subscore** Q with component breakdown (recall/precision/adoption…)
  — full metric vector always visible, scalar second (HAL's dashboard-first,
  composite-second philosophy).
- **Cost subscore**: C, plus raw USD, minutes, CI minutes, tokens; $/success
  (cost-of-pass) per task.
- **Risk subscore**: S, incident counts by severity class, near-miss counts
  (tool_refused, gate revise), days-since-last-severe.
- **Trend**: 7/30/90-day CATQ and per-component trends; recurrence retro-
  corrections (pr_debug) applied to history.
- **Baseline comparison**: pinned baseline arms (single-shot review, always-
  escalate rebase, majority-class triage) re-run monthly on the frozen
  benchmark; production vs baseline delta.
- **Human escalation rate**: per task, with the **target band (2–15%)** drawn
  on the chart — below band flags overconfidence, above band flags capability
  gaps; never a minimization target.
- **Dry-run vs write-enabled**: Q measured in shadow (dry-run) vs live mode;
  a live-mode Q drop or incident-rate rise gates rollbacks; the double-gate
  (`ALLOW_POST`/`ALLOW_PUSH`) makes shadow mode free to run continuously.
- **Ensemble vs non-ensemble** (pr_review, and any step that adopts
  `run_agent_step_ensemble`): CATQ side-by-side at each config's actual cost;
  Pareto frontier chart (Q vs $) with frontier membership marked.
- **Metric health**: judge self-consistency and cross-model κ per judged
  component; NLI-proxy-vs-human agreement (issue_answer); GT staleness age.

## Final Recommendations

1. **Implement first: the shared collector + pr_review online adoption.**
   Write `metrics.py` (RunTrace → per-run metrics.json with Q components,
   USD, minutes, incidents) and the **feedback collector** (gh cron: comment
   resolution/outdated state, reactions, merge outcomes, reverts). pr_review
   already has the offline half (RQS3); wiring `useful`, `calib`, and the
   escaped-defect scan upgrades it to RUS with the least new machinery, and
   the same collector feeds pr_debug's `accepted` and pr_rebase's online
   `conflict` for free. issue_filter's TQS is the cheapest full metric —
   implement second as the all-deterministic proof of the framework.
2. **Instrumentation to add** (priority order): price table → USD per run;
   pre/post check-state snapshots (F2P/P2P); posted-artifact IDs; Buildkite
   build minutes (extends the already-planned REST client); per-hunk conflict
   records + expected-replay diff; patch-suspicion flags; settled-label
   snapshotter; incident ledger (typed risk events with severity — several
   already exist as `out_of_scope_edit`/`tool_refused`/`push_requested`).
3. **Most valuable human labels** (≈1–2 maintainer-hours/week): (a) comment
   class TB/UNB/NIT/FP + severity on ~20 sampled review comments — anchors
   precision_v, calib, and the validity jury; (b) accept/reject + root-cause-
   correct on every pr_debug patch (cheap: it's the existing PR review flow);
   (c) semantic-equivalence verdicts on ~10 sampled conflict resolutions;
   (d) AIS agreement on ~10 answers. Route all of it through the existing
   curator gate so labels also improve skills.
4. **Benchmark set to build**: extend the n=3 review PRs to **25–30 human-
   validated PRs including ≥5 known-clean approvals** (fixes METRIC_V3's
   listed decision-metric gap); mine **(conflict, human-resolution) pairs**
   from vllm-omni's historical rebase cycles Merge-Bench-style, stratified by
   complexity; **30 resolved issues** (answers, pinned to commit hash) and
   **~100 chronologically-split triaged issues** with settled labels; harvest
   **10–20 real CI failure groups** from past Buildkite runs with their fix
   commits, plus optional SWE-smith-style injected bugs with known root
   causes (contamination-resistant, SWE-bench-Live's dated-slice discipline).
   Freeze, version, re-run
   baselines monthly; ≥3 replicates for every judged number.
5. **Avoiding cheap-but-low-quality optima**: score against the **task set,
   not the attempted set** (abstentions/unrun tasks count in the denominator);
   fixed abstain scores strictly below decent success; recall floors and the
   escalation band as un-optimized guardrails that **veto** CATQ ranking when
   breached; meter cost at a neutral boundary (API billing export, Buildkite
   API — never agent-self-reported); log-cost discount so cheapness cannot
   dominate quality; FPs carry negative value and comment caps stay code-side
   so verbosity and over-reporting never pay; judge components live behind
   κ health checks (low κ → "unscored", not zero); and audit the *top-scoring*
   runs by hand each month — the runs most likely to have found a metric hole.
