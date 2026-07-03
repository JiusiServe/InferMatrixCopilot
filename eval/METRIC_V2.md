# RQS v2 — a literature-grounded review-quality metric

Survey of the relevant research and the redesign it implies for our eval
(current metric: [README.md](./README.md); v1 results: [RESULTS.md](./RESULTS.md)).

## What the literature says

1. **Reference-based similarity (BLEU vs. a human comment) is discredited.**
   Code review is one-to-many — many valid reviews exist per diff — so
   comparing against the single human comment underestimates quality.
   CRScore (NAACL 2025, arXiv 2409.19801) replaces references with
   **pseudo-references**: an LLM generates claims/implications about the diff,
   static analyzers add code smells, and review sentences are aligned to them
   by embedding similarity (mxbai-embed-large, τ≈0.73). From the alignment:
   *Conciseness* = fraction of review sentences matching some pseudo-reference
   (precision-like), *Comprehensiveness* = fraction of pseudo-references
   covered (recall-like), *Relevance* = their harmonic mean. Best open-metric
   correlation with human judgment (Spearman 0.54 comment-level, 0.95
   system-ranking); ships 2.9k human-annotated scores for calibration.

2. **Usefulness ≈ does the author act on it.** The classic Microsoft study
   (Bosu et al., MSR 2015) defines useful comments as ones that trigger
   change; Atlassian's RovoDev online eval (arXiv 2601.01129) uses
   **resolution rate** (38.7% of posted comments trigger a code change) as its
   production KPI; arXiv 2510.05450 shows bug/readability/maintainability
   comments resolve most. EvaCRC and Google's "AI-Assisted Assessment"
   (arXiv 2405.13565) both score **actionability** explicitly.

3. **Same-model judging is biased.** Self-preference bias is measurable and
   directional (arXiv 2604.22891; "Justice or Prejudice?" catalogs 12 judge
   biases). Mitigations with evidence: cross-family judges, multi-judge
   juries, blind/randomized presentation, and structured rubrics
   (~31% bias reduction) — never a single same-family judge scoring prose.

4. **Report dimensions, not one scalar.** The 2026 survey of 99 code-review
   papers (arXiv 2602.13377) finds evaluation practices fragmented and
   recommends task-aware, multi-dimensional reporting.

## RQS v2 design

Per review, report five sub-scores plus cost; headline = **Usefulness-weighted F1**.

| Sub-score | How | Grounding |
|---|---|---|
| **Comprehensiveness** | CRScore-style: pseudo-references = LLM claims about the diff (cross-family model) ∪ ruff/pylint findings on changed files; fraction covered by the review (embedding alignment, τ calibrated on CRScore's released annotations) | CRScore |
| **Conciseness** | fraction of review sentences aligned to ≥1 pseudo-reference (penalizes padding/"coverage theater") | CRScore |
| **Human-issue recall** (when GT exists) | as v1, but **severity-weighted**: issues marked `[blocking]` ×2, nits ×1; issues whose threads show a code change ("resolved") ×1.5 | Bosu 2015; resolution-rate studies |
| **Actionability** | per finding, rubric judge: does it say *what to change and where*? (binary) | EvaCRC; RovoDev; Google 2405.13565 |
| **Precision/validity** | as v1 (grounded-in-diff check) — kept, it worked | v1 |
| **Cost** | tokens + seconds | — |

**Judge protocol changes** (the biggest v1 weakness):
- **Cross-family jury**: 2–3 judges from different model families (e.g.
  Claude + DeepSeek + one OSS model), majority vote per judgment; report
  inter-judge agreement (Cohen's κ) so we know when the metric is trustworthy.
- Keep v1's blind, normalized-findings, seeded-shuffle presentation.
- **Human anchor**: hand-label ~30 findings once; report each judge's
  agreement with the anchor set (CRScore's calibration pattern).

**Scale unlock**: pseudo-reference scores need no human comments, so the
benchmark can grow from 3 GT-rich PRs to 20–30 arbitrary merged PRs, with
human-issue recall computed on the GT-rich subset only.

**Online metric (post-deployment)**: once `ALLOW_POST` is enabled, track
**resolution rate** of posted comments (did the author change the flagged
code?) — the only metric the literature ties directly to real-world value,
and it's free to collect from the PR timeline.

## Implementation sketch (incremental on `run_eval.py`)

1. `pseudo_refs(pr)` — claims via a cross-family LLM + `ruff check --diff`
   on changed files; cache per PR.
2. `align(review_sentences, refs)` — embedding model (or judge-LLM matching
   as fallback if no embedding endpoint); τ from CRScore's public data.
3. `jury(judge_fn, models=[...])` — majority vote wrapper around the v1
   validity/coverage/actionability judges; κ computed across judges.
4. Severity weights parsed from GT annotations (already tagged in
   `GROUND_TRUTH` sources).
5. RESULTS v2 table: 5 sub-scores + κ + cost; headline = harmonic mean of
   (severity-weighted recall, precision, actionability).

## Sources

- CRScore — arXiv [2409.19801](https://arxiv.org/abs/2409.19801) / [NAACL 2025](https://aclanthology.org/2025.naacl-long.457/)
- Survey of code-review benchmarks 2015–2025 — arXiv [2602.13377](https://arxiv.org/abs/2602.13377)
- RovoDev online eval @ Atlassian (resolution rate) — arXiv [2601.01129](https://arxiv.org/html/2601.01129v1)
- Which comments do developers resolve — arXiv [2510.05450](https://arxiv.org/html/2510.05450v1)
- Bosu et al., *Characteristics of Useful Code Reviews*, MSR 2015 — [Microsoft Research](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/bosu2015useful.pdf)
- AI-Assisted Assessment of Coding Practices (Google) — arXiv [2405.13565](https://arxiv.org/abs/2405.13565)
- Useful-comment identification survey — arXiv [2307.00692](https://arxiv.org/pdf/2307.00692)
- Self-preference bias of LLM judges — arXiv [2604.22891](https://arxiv.org/html/2604.22891v2); *Justice or Prejudice?* — [llm-judge-bias.github.io](https://llm-judge-bias.github.io/)
