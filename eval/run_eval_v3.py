#!/usr/bin/env python3
"""RQS v3 rerun — reliability-first metric over the cached arm reviews.

See METRIC_V3.md. New vs v2:
- validity: anchored rubric, 3 trials x 2 judge models (vote share), with
  self-consistency and cross-model kappa reported (arXiv 2606.13685);
- decision: verdict correctness vs the human outcome, regex-extracted with
  LLM fallback (Sphinx, arXiv 2601.04252);
- aggregate: weighted arithmetic mean — no harmonic zeroing of silent
  reviews (arXiv 2604.24525: components are weak signals, read jointly).

Reuses cached reviews/findings and the v2 coverage/actionability judgments;
new judgments cache as raw/v3_*.json.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
RAW = EVAL_DIR / "raw"
sys.path.insert(0, str(EVAL_DIR.parent / "src"))

from omni_copilot.config import Settings  # noqa: E402
from omni_copilot.llm import LLM, parse_json_reply  # noqa: E402

from run_eval import ARMS, GROUND_TRUTH, PRS  # noqa: E402
from run_eval_v2 import (  # noqa: E402
    GT_WEIGHTS,
    JUDGE_MODELS,
    _cached,
    cohens_kappa,
    judge_actionability,
    judge_coverage,
)

VALIDITY_TRIALS = 3
WEIGHTS = {"recall_w": 0.35, "precision": 0.25, "actionability": 0.20,
           "decision": 0.20}

# Cost model (Cost-of-Pass, arXiv 2504.13359): cost-of-quality = $/RQS3 point.
# DeepSeek arms: token counts at list rates ($/1M). The endpoint reports
# cache reads separately (excluded from input_tokens); when a run recorded
# them they are priced at the cache-hit rate — the same real-billing basis
# the Opus arm gets via the CLI's actual total_cost_usd.
DEEPSEEK_PRICE = {"input": 0.28, "output": 1.10, "cache_read": 0.028}

# Efficiency-adjusted headline: RQS3e = RQS3 * f($) * f(minutes), where
# f(x) = 1 / (1 + log10(1 + x/ref)) — a log-scale discount, since arm costs
# span orders of magnitude and a linear penalty would be dominated by the
# most expensive arm. References are explicit budget assumptions
# (env-overridable): $1/review and 10 min/review ~ the attention scale at
# which an automated review's cost starts to rival a maintainer's skim.
import math  # noqa: E402
import os  # noqa: E402

COST_REF_USD = float(os.environ.get("V3_COST_REF_USD", "1.0"))
TIME_REF_MIN = float(os.environ.get("V3_TIME_REF_MIN", "10.0"))


def efficiency_factor(x: float, ref: float) -> float:
    return 1.0 / (1.0 + math.log10(1.0 + max(x, 0.0) / ref))


def rqs3e(quality: float, usd: float, minutes: float) -> float:
    return (quality * efficiency_factor(usd, COST_REF_USD)
            * efficiency_factor(minutes, TIME_REF_MIN))


def review_cost_usd(cost: dict) -> float:
    if cost.get("cost_usd") is not None:
        return float(cost["cost_usd"])
    return (cost.get("input_tokens", 0) * DEEPSEEK_PRICE["input"]
            + cost.get("cache_read_tokens", 0) * DEEPSEEK_PRICE["cache_read"]
            + cost.get("output_tokens", 0) * DEEPSEEK_PRICE["output"]) / 1e6

# All three benchmark PRs drew substantive human change requests before merge
# (that is why they carry GT issues) — see METRIC_V3.md for the clean-approve
# extension this implies.
DECISION_GT = {4678: "request_changes", 4679: "request_changes",
               4849: "request_changes"}

_VALIDITY_RUBRIC = (
    "You verify code-review findings against a PR diff using this ANCHORED "
    "rubric.\n"
    "VALID requires BOTH: (a) what the finding says the change does is "
    "consistent with the diff; (b) the concern is technically plausible — "
    "including claims about repository context the change affects (in-repo "
    "consumers, docs, tests, callers) when the diff makes such impact "
    "plausible, even though that context is not itself in the diff.\n"
    "REQUESTED CHANGES: most review findings REQUEST something (add a test, "
    "update a docstring, add an assert, run a benchmark). Judge such a "
    "finding on whether the underlying issue it points at is real in the "
    "diff — the requested change being ABSENT from the diff is the "
    "finding's entire point and is NEVER a reason to vote invalid.\n"
    "INVALID: misreads the diff (wrong file/behavior/line), claims something "
    "the shown code already handles, or is too vague to check at all.\n"
    "Anchored examples:\n"
    "- 'The diff makes stream=True default to SSE; in-repo example clients "
    "still assume raw PCM and need stream_format=audio' -> VALID "
    "(diff-grounded claim, plausible repo impact).\n"
    "- 'Add a test for the widened rejection path', where the diff really "
    "does widen the rejection and adds no such test -> VALID (the absence "
    "of the requested test is the point, not a misread).\n"
    "- 'This function may be slow' with no location or mechanism -> INVALID "
    "(unverifiable).\n"
    "Judge substance, not style; never mark a finding invalid merely for "
    "being a nit or a documentation ask. Output ONLY: "
    '{"verdicts": [{"i": 0, "valid": true|false}]}'
)


def judge_validity_v3(llm: LLM, model: str, findings, diff) -> list[bool]:
    if not findings:
        return []
    numbered = "\n".join(f"{i}. [{f.get('file', '')}:{f.get('line', '')}] "
                         f"{f.get('summary', '')}"
                         for i, f in enumerate(findings))
    reply = llm.create(
        system=_VALIDITY_RUBRIC,
        messages=[{"role": "user", "content":
                   f"FINDINGS:\n{numbered}\n\n--- DIFF ---\n{diff[:60_000]}"}],
        model=model, max_tokens=3000)
    obj = parse_json_reply(reply.text) or {}
    v = {x.get("i"): bool(x.get("valid")) for x in obj.get("verdicts", [])}
    return [v.get(i, False) for i in range(len(findings))]


def extract_verdict(review: str, llm: LLM, cache: Path) -> str:
    """Deterministic first (c-CRAB's lesson), LLM fallback only if needed."""
    hits = re.findall(r"request[\s_-]*changes|approve", review, re.IGNORECASE)
    if hits:  # the LAST verdict token is the operative one in every arm format
        return ("request_changes" if "request" in hits[-1].lower()
                else "approve")

    def _ask():
        reply = llm.create(
            system=("Classify the final verdict of this code review. Output "
                    'ONLY: {"verdict": "approve"|"request_changes"|"none"}'),
            messages=[{"role": "user", "content": review[:20_000]}],
            max_tokens=200)
        return (parse_json_reply(reply.text) or {}).get("verdict", "none")

    return str(_cached(cache, _ask))


def decision_score(verdict: str, pr: int) -> float:
    if verdict == "none":
        return 0.5
    return 1.0 if verdict == DECISION_GT[pr] else 0.0


def main() -> int:
    settings = Settings()
    llm = LLM(settings)
    assert llm.available, "no API key"
    print(f"v3 jury: {JUDGE_MODELS} x {VALIDITY_TRIALS} trials", flush=True)

    rows: dict[int, dict[str, dict]] = {}
    self_pairs: list[tuple[list, list]] = []   # trial-vs-trial, same model
    cross_pairs: list[tuple[list, list]] = []  # model-vs-model, majority
    for pr in PRS:
        diff = (RAW / f"pr{pr}.diff").read_text()
        gt = GROUND_TRUTH[pr]
        weights = GT_WEIGHTS[pr]
        rows[pr] = {}
        for arm in ARMS:
            findings = json.loads(
                (RAW / f"pr{pr}_{arm}.findings.json").read_text())
            review = (RAW / f"pr{pr}_{arm}.md").read_text()
            n = len(findings)
            print(f"[v3] PR {pr} · {arm} ({n} findings)", flush=True)

            votes: dict[str, list[list[bool]]] = {}
            for model in JUDGE_MODELS:
                tag = model.replace("/", "_")
                votes[model] = [
                    _cached(RAW / f"v3_pr{pr}_{arm}.validity.{tag}.t{t}.json",
                            lambda m=model: judge_validity_v3(llm, m,
                                                              findings, diff))
                    for t in range(VALIDITY_TRIALS)]
            all_votes = [v for trials in votes.values() for v in trials]
            precision = (sum(sum(v) for v in all_votes)
                         / (n * len(all_votes))) if n else 0.0
            if n:
                for trials in votes.values():
                    self_pairs.append((trials[0], trials[1]))
                maj = []
                for trials in votes.values():
                    maj.append([sum(t[i] for t in trials) * 2
                                > len(trials) for i in range(n)])
                if len(maj) >= 2:
                    cross_pairs.append((maj[0], maj[1]))

            # coverage + actionability reuse the v2 jury caches
            cov_votes = [
                _cached(RAW / f"v2_pr{pr}_{arm}.coverage."
                        f"{m.replace('/', '_')}.json",
                        lambda m=m: judge_coverage(llm, m, findings, gt))
                for m in JUDGE_MODELS]
            act_votes = [
                _cached(RAW / f"v2_pr{pr}_{arm}.action."
                        f"{m.replace('/', '_')}.json",
                        lambda m=m: judge_actionability(llm, m, findings))
                for m in JUDGE_MODELS]
            cov = {g["id"]: sum(cv[g["id"]] for cv in cov_votes)
                   / len(cov_votes) for g in gt}
            recall_w = (sum(weights[g] * c for g, c in cov.items())
                        / sum(weights.values()))
            actionability = (sum(sum(v) for v in act_votes)
                             / (n * len(act_votes))) if n else 0.0

            verdict = extract_verdict(
                review, llm, RAW / f"v3_pr{pr}_{arm}.verdict.json")
            decision = decision_score(verdict, pr)

            comps = {"recall_w": recall_w, "precision": precision,
                     "actionability": actionability, "decision": decision}
            cost = json.loads((RAW / f"pr{pr}_{arm}.cost.json").read_text())
            rows[pr][arm] = {
                "findings": n, **comps, "verdict": verdict,
                "rqs3": sum(WEIGHTS[k] * v for k, v in comps.items()),
                "tokens": cost["input_tokens"] + cost["output_tokens"],
                "usd": review_cost_usd(cost),
                "minutes": cost.get("seconds", 0.0) / 60.0,
            }

    kappas = {
        "validity_self": cohens_kappa(
            [x for p in self_pairs for x in p[0]],
            [x for p in self_pairs for x in p[1]]),
        "validity_cross": cohens_kappa(
            [x for p in cross_pairs for x in p[0]],
            [x for p in cross_pairs for x in p[1]]),
    }
    write_results(rows, kappas)
    print(f"done -> {EVAL_DIR / 'RESULTS_V3.md'}")
    return 0


def write_results(rows: dict, kappas: dict) -> None:
    cols = ("findings", "recall_w", "precision", "actionability", "decision",
            "rqs3", "tokens", "usd", "minutes")
    lines = ["# RQS v3 results", "",
             "Metric: METRIC_V3.md (anchored-rubric multi-trial validity, "
             "decision correctness, arithmetic aggregate). "
             f"Jury: {JUDGE_MODELS} x {VALIDITY_TRIALS} validity trials.",
             "",
             "Validity reliability: "
             + ", ".join(f"{k} kappa={v:.2f}" if v is not None else f"{k} n/a"
                         for k, v in kappas.items()), ""]
    agg = {arm: dict.fromkeys(cols, 0.0) for arm in ARMS}
    for pr in PRS:
        lines += [f"## PR #{pr}", "",
                  "| arm | findings | recall_w | precision | actionability | "
                  "decision | **RQS3** | tokens |",
                  "|---|---|---|---|---|---|---|---|"]
        for arm in ARMS:
            r = rows[pr][arm]
            for c in cols:
                agg[arm][c] += r[c] / len(PRS)
            lines.append(
                f"| {arm} | {r['findings']} | {r['recall_w']:.2f} | "
                f"{r['precision']:.2f} | {r['actionability']:.2f} | "
                f"{r['decision']:.1f} ({r['verdict']}) | "
                f"**{r['rqs3']:.2f}** | {r['tokens']:,} |")
        lines.append("")
    lines += ["## Aggregate (mean over PRs)", "",
              "| arm | recall_w | precision | actionability | decision | "
              "**RQS3** | tokens |",
              "|---|---|---|---|---|---|---|"]
    for arm in ARMS:
        a = agg[arm]
        lines.append(
            f"| {arm} | {a['recall_w']:.2f} | {a['precision']:.2f} | "
            f"{a['actionability']:.2f} | {a['decision']:.2f} | "
            f"**{a['rqs3']:.2f}** | {a['tokens']:,.0f} |")

    # -- efficiency (Cost-of-Pass, arXiv 2504.13359) ---------------------------
    lines += ["", "## Efficiency — RQS3e headline (cost/time folded in)", "",
              "RQS3e = RQS3 x f($) x f(min), f(x) = 1/(1 + log10(1 + x/ref)); "
              f"refs: ${COST_REF_USD}/review, {TIME_REF_MIN} min/review "
              "(env-overridable). Cost model: Opus arm = actual CLI-billed "
              f"USD; DeepSeek arms = token estimate at "
              f"${DEEPSEEK_PRICE['input']}/M in, ${DEEPSEEK_PRICE['output']}/M "
              "out (cache-miss list rate — an upper bound). cost-of-quality = "
              "$/RQS3 point; frontier per Cost-of-Pass.", "",
              "| arm | RQS3 | $/review | min/review | **RQS3e** | "
              "$-of-quality | min-of-quality | Pareto ($,RQS3) |",
              "|---|---|---|---|---|---|---|---|"]
    effs = {arm: (agg[arm]["rqs3"], agg[arm]["usd"], agg[arm]["minutes"])
            for arm in ARMS}
    for arm in ARMS:
        q, usd, mins = effs[arm]
        dominated = any(q2 > q and u2 < usd
                        for a2, (q2, u2, _) in effs.items() if a2 != arm)
        lines.append(
            f"| {arm} | {q:.2f} | ${usd:.2f} | {mins:.1f} | "
            f"**{rqs3e(q, usd, mins):.2f}** | "
            f"{'$' + format(usd / q, '.2f') if q > 0 else 'inf'} | "
            f"{mins / q:.1f} | {'frontier' if not dominated else 'dominated'} |")
    (EVAL_DIR / "RESULTS_V3.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())
