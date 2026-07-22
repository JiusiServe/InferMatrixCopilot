# PR-review quality evaluation

Compares three review configurations on the **same model** (DeepSeek v4 pro via
the Anthropic-compatible endpoint) over real, merged vLLM-Omni PRs whose human
review threads provide ground truth.

## Arms

| Arm | What runs |
|---|---|
| **pure skill** | A tool-using agent (read_file/list_dir/grep over the repo + the skill's references) whose instructions are the [vllm-omni-review skill](https://github.com/hsliuustc0106/vllm-omni-skills) SKILL.md — i.e. the "Claude Code + skill" configuration, on DeepSeek. |
| **pure copilot** | infermatrix-copilot's `pr-review` playbook step exactly as shipped: `agent.review_diff`, single structured pass over the fetched diff with the generic reviewer prompt. No skill, no repo tools. |
| **copilot + skill** | The copilot's structured review step with the skill injected as guidance (SKILL.md + the references its routing table selects for this diff) — how the copilot's skill store would feed `adaptive_guidance`. |

## Benchmark set

Merged PRs with ≥2 substantive human inline review issues (bots excluded):

- **#4678** [Cosmos3] Pad sound latents under SP — 2 ground-truth issues
- **#4679** Make speech streaming default to SSE — 4 ground-truth issues (incl. 2 blocking)
- **#4849** Fix HunyuanImage3 bridge request batching — 2 ground-truth issues

Ground truth = distinct issues raised by human reviewers (curated from the
inline threads, embedded in `run_eval.py` with source attribution).

## Metric — RQS (Review Quality Score)

Per PR per arm, findings are first normalized to JSON (`{file, line, summary}`)
by an extraction call, then judged **blind** (no arm labels, fixed-seed order):

- **Recall_GT** — over ground-truth issues: full hit = 1, partial = 0.5, miss = 0;
  averaged. *Does the review find what human maintainers found?*
- **Precision** — fraction of the arm's findings judged valid (grounded in the
  actual diff, technically correct; hallucinated/misread findings fail).
  *Is what it says true?* Zero findings ⇒ precision 0.
- **F1** — harmonic mean of Recall_GT and Precision. **Primary ranking metric.**
- **Specificity** — fraction of findings carrying a concrete file reference.
- **Cost** — total tokens (in+out) and wall-clock seconds per review.

Aggregate = mean over the three PRs.

### Known limitations (stated up front)

- The judge is the same DeepSeek model (only endpoint available) → possible
  self-style preference; mitigated by blind labels, normalized findings, and a
  validity rubric tied to the diff text rather than prose quality.
- Ground truth is what humans *happened to* comment on; a valid finding humans
  missed scores in Precision but not Recall — so F1 rewards finding the human
  issues without hallucinating, which matches the skill's own "high-signal,
  low-noise" goal.
- The repo checkout is post-merge `main`, so tool-using arms inspect slightly
  newer code than the reviewers saw.
- n=3 PRs: directional, not statistically tight.

## Run

```bash
python eval/run_eval.py --skill-dir /path/to/vllm-omni-skills/skills/vllm-omni-review
# artifacts land in eval/raw/, scores in eval/RESULTS.md
```

Requires: `.env` with the DeepSeek key, `gh` authenticated, and a local vllm-omni checkout (set `OMNI_REPO`).
All stages cache into `eval/raw/` — reruns only redo missing pieces.

Metric v2 (literature-grounded redesign): see [METRIC_V2.md](./METRIC_V2.md).
