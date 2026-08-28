#!/usr/bin/env python3
"""Verify and report a reviewbot judgment campaign.

`--verify` runs the exact-denominator audit (judge_val.py skips existing
verdict files unconditionally and succeeds on an empty job set, so its
exit code proves nothing about completeness):

  per replicate dir, verdict files are exactly {arm-manifest stems} x
  {judge reps}; every file parses; `_roles` names this arm and the pinned
  baseline; the recorded judge backend/model equal the pinned
  claude/claude-sonnet-5; and each verdict's arm_a/arm_b sha256 matches
  the sha256 of the CURRENT candidate texts (first 24k, exactly as the
  judge read them) — a stale verdict left over from a changed artifact or
  baseline fails here, not in the statistics.

Without `--verify` it builds the report: paired-within-verdict deltas
(the ONLY honest comparison — raw side means drift +-.08 across judge
batches), clustered by item (replicates of one item are not independent
observations), pooled over generation replicates. Output is written
atomically; a `reviewbot_<YYYY-MM>` tag also upserts one row in
results/reviewbot/INDEX.md (rerunning a month replaces its row; any
other tag, e.g. a smoke run, never touches INDEX).

These numbers are a MONITORING PROBE of the live bot configuration,
never a promotion gate, and never comparable with the generator
ablation tables in results/model_comparison.md (the bot is loop+model).

Usage: build_reviewbot_report.py [--verify] --tag reviewbot_<month>
       [--gen-reps 3] [--judge-reps 3]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import statistics as st
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

DS = Path(os.environ.get("REVIEWBOT_EVAL_ROOT") or Path(__file__).parent)
BASELINE = "claudecode_opus5"
JUDGE_BACKEND = "claude"
JUDGE_MODEL = "claude-sonnet-5"
CAP = 24_000
DIMS = ("recall", "precision", "actionability")
# GOLD latent-gap items (one per split; train+val scope carries two).
GOLD_STEMS = {"pr4870", "pr4810", "pr4834"}
MONTH_TAG = re.compile(r"^reviewbot_(\d{4}-\d{2})$")

# Two-sided t .975 critical values, df 1..30 (as in paired_analysis.py).
_T95 = [12.71, 4.30, 3.18, 2.78, 2.57, 2.45, 2.36, 2.31, 2.26, 2.23,
        2.20, 2.18, 2.16, 2.14, 2.13, 2.12, 2.11, 2.10, 2.09, 2.09,
        2.08, 2.07, 2.07, 2.06, 2.06, 2.06, 2.05, 2.05, 2.05, 2.04]


def t95(df: int) -> float:
    if df < 1:
        return float("nan")
    return _T95[df - 1] if df <= 30 else 1.96


def _sha(path: Path) -> str:
    return hashlib.sha256(
        path.read_text()[:CAP].encode()
    ).hexdigest()


class CampaignError(RuntimeError):
    pass


def load_campaign(tag: str, gen_reps: int, judge_reps: int):
    """Verify everything, return (verdicts, stems, config).

    verdicts: list of (stem, gen_rep, judge_rep, verdict_dict, arm_side)
    where arm_side is "x" or "y" — the slot holding the reviewbot text.
    """
    problems: list[str] = []
    verdicts = []
    stems: list[str] | None = None
    config = None
    for rep in range(1, gen_reps + 1):
        arm_dir = DS / "arms" / f"{tag}_r{rep}"
        judge_dir = DS / "judgments" / f"{tag}_r{rep}"
        manifest_path = arm_dir / "manifest.json"
        if not manifest_path.is_file():
            problems.append(f"{manifest_path} missing")
            continue
        manifest = json.loads(manifest_path.read_text())
        if stems is None:
            stems = list(manifest["stems"])
        elif manifest["stems"] != stems:
            problems.append(f"r{rep}: stems differ from r1 — mixed campaign")
        if config is None:
            config = manifest.get("config")
        elif manifest.get("config") != config:
            problems.append(f"r{rep}: config differs from r1 — mixed campaign")
        expected = {f"{s}.r{k}.json" for s in stems for k in
                    range(1, judge_reps + 1)}
        actual = {p.name for p in judge_dir.glob("*.r*.json")}
        for name in sorted(expected - actual):
            problems.append(f"{judge_dir.name}: MISSING {name}")
        for name in sorted(actual - expected):
            problems.append(f"{judge_dir.name}: EXTRA {name}")
        for stem in stems:
            arm_file = arm_dir / f"{stem}.md"
            base_file = DS / "baselines" / BASELINE / f"{stem}.md"
            for k in range(1, judge_reps + 1):
                vf = judge_dir / f"{stem}.r{k}.json"
                if not vf.is_file():
                    continue
                try:
                    v = json.loads(vf.read_text())
                except json.JSONDecodeError as exc:
                    problems.append(f"{vf.name}: unparseable ({exc})")
                    continue
                roles = v.get("_roles") or {}
                if roles.get("arm") != f"{tag}_r{rep}" or (
                    roles.get("baseline") != BASELINE
                ):
                    problems.append(f"{vf.name}: roles {roles} != "
                                    f"({tag}_r{rep}, {BASELINE})")
                    continue
                meta = v.get("_arm_meta") or {}
                if meta.get("judge_backend") != JUDGE_BACKEND or (
                    meta.get("judge_model") != JUDGE_MODEL
                ):
                    problems.append(
                        f"{vf.name}: judge {meta.get('judge_backend')}/"
                        f"{meta.get('judge_model')} is not the pinned "
                        f"{JUDGE_BACKEND}/{JUDGE_MODEL}"
                    )
                    continue
                if meta.get("arm_a_sha256") != _sha(arm_file):
                    problems.append(f"{vf.name}: STALE — arm text changed "
                                    "since this verdict")
                    continue
                if meta.get("arm_b_sha256") != _sha(base_file):
                    problems.append(f"{vf.name}: STALE — baseline text "
                                    "changed since this verdict")
                    continue
                # Schema, fail-closed: a malformed verdict must abort the
                # campaign, never silently shrink a denominator or default
                # the arm onto side Y.
                blinding = v.get("_blinding") or {}
                labels = {blinding.get("X"), blinding.get("Y")}
                if labels != {f"{tag}_r{rep}", BASELINE}:
                    problems.append(
                        f"{vf.name}: blinding {blinding} does not map X/Y "
                        f"onto ({tag}_r{rep}, {BASELINE})"
                    )
                    continue
                schema_bad = False
                for side in ("x", "y"):
                    scores = v.get(side)
                    if not isinstance(scores, dict):
                        problems.append(f"{vf.name}: side {side} missing")
                        schema_bad = True
                        continue
                    for dim in DIMS:
                        value = scores.get(dim)
                        if not isinstance(value, (int, float)) or not (
                            0.0 <= float(value) <= 1.0
                        ):
                            problems.append(
                                f"{vf.name}: {side}.{dim}={value!r} is not "
                                "a score in [0,1]"
                            )
                            schema_bad = True
                    if not isinstance(scores.get("gap_hit"), bool):
                        problems.append(
                            f"{vf.name}: {side}.gap_hit missing or not a "
                            "bool"
                        )
                        schema_bad = True
                if v.get("winner") not in {"X", "Y", "tie"}:
                    problems.append(
                        f"{vf.name}: winner={v.get('winner')!r} invalid"
                    )
                    schema_bad = True
                if schema_bad:
                    continue
                arm_side = (
                    "x" if blinding.get("X") == f"{tag}_r{rep}" else "y"
                )
                verdicts.append((stem, rep, k, v, arm_side))
    if problems:
        raise CampaignError(
            "campaign verification FAILED — do not report:\n  "
            + "\n  ".join(problems)
        )
    if not verdicts or stems is None:
        raise CampaignError("no verdicts found")
    return verdicts, stems, config or {}


def analyze(verdicts, stems):
    """Paired within verdict, clustered by item."""
    per_item: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    wins = {"arm": 0, "baseline": 0, "tie": 0}
    gap = defaultdict(lambda: {"arm": 0, "baseline": 0, "n": 0})
    for stem, _rep, _k, v, arm_side in verdicts:
        base_side = "y" if arm_side == "x" else "x"
        arm_scores, base_scores = v.get(arm_side) or {}, v.get(base_side) or {}
        for dim in DIMS:
            if dim in arm_scores and dim in base_scores:
                per_item[stem][dim].append(
                    float(arm_scores[dim]) - float(base_scores[dim])
                )
        winner = v.get("winner")
        slot = {"X": "x", "Y": "y"}.get(winner)
        if slot is None:
            wins["tie"] += 1
        else:
            wins["arm" if slot == arm_side else "baseline"] += 1
        if stem in GOLD_STEMS:
            entry = gap[stem]
            entry["n"] += 1
            entry["arm"] += bool(arm_scores.get("gap_hit"))
            entry["baseline"] += bool(base_scores.get("gap_hit"))
    aggregate = {}
    item_rows = {}
    for dim in DIMS:
        means = [
            st.mean(per_item[stem][dim])
            for stem in stems
            if per_item[stem][dim]
        ]
        n = len(means)
        mean = st.mean(means) if means else float("nan")
        if n >= 2:
            half = t95(n - 1) * st.stdev(means) / math.sqrt(n)
        else:
            half = float("nan")
        aggregate[dim] = {"delta": mean, "ci": half, "n": n,
                          "pos": sum(1 for m in means if m > 0),
                          "neg": sum(1 for m in means if m < 0)}
    for stem in stems:
        item_rows[stem] = {
            dim: (st.mean(per_item[stem][dim])
                  if per_item[stem][dim] else None)
            for dim in DIMS
        } | {"n": len(per_item[stem][DIMS[0]])}
    # Every judged GOLD item is reported, a 0/n double miss included —
    # hiding it would overstate latent-gap coverage.
    gap_rows = {stem: entry for stem, entry in gap.items() if entry["n"]}
    return aggregate, item_rows, wins, gap_rows


def render(tag, aggregate, item_rows, wins, gap_rows, config,
           gen_reps, judge_reps):
    stems = list(item_rows)
    lines = [
        f"# Reviewbot review-quality probe — `{tag}`",
        "",
        "> **Monitoring probe, not a gate.** n="
        f"{aggregate[DIMS[0]]['n']} items resolves ≈.06 at the measured "
        "item sd; months are comparable only under the same judge model "
        "and the same pinned baseline; these numbers are loop+model and "
        "are NEVER merged into `results/model_comparison.md`.",
        "",
        f"- Arm: omni-reviewbot Direct pipeline, bot `"
        f"{config.get('bot_sha', 'unknown')[:12]}`, infermatrix `"
        f"{config.get('infermatrix_sha', 'unknown')[:12]}`, provider "
        f"`{(config.get('env') or {}).get('AGENT_PROVIDER', 'codex')}`, "
        f"`REVIEW_CONTEXT_MODE={config.get('review_context_mode')}`",
        f"- Baseline: pinned `{BASELINE}` · Judge: pinned "
        f"`{JUDGE_BACKEND}/{JUDGE_MODEL}` · {gen_reps} generation × "
        f"{judge_reps} judge replicates",
        "",
        "## Paired deltas (arm − baseline, clustered by item)",
        "",
        "| dim | Δ | 95% CI | items +/− | n |",
        "|---|---|---|---|---|",
    ]
    for dim in DIMS:
        a = aggregate[dim]
        lines.append(
            f"| {dim} | {a['delta']:+.3f} | ±{a['ci']:.3f} | "
            f"{a['pos']}/{a['neg']} | {a['n']} |"
        )
    total = sum(wins.values())
    lines += [
        "",
        f"**Verdict wins** (least informative statistic — margin is "
        f"discarded): arm {wins['arm']} · baseline {wins['baseline']} · "
        f"tie {wins['tie']} (of {total})",
        "",
        "## Per item (mean paired delta)",
        "",
        "| item | Δrecall | Δprecision | Δactionability | verdicts |",
        "|---|---|---|---|---|",
    ]
    for stem in stems:
        row = item_rows[stem]

        def fmt(value):
            return f"{value:+.3f}" if value is not None else "—"

        lines.append(
            f"| {stem} | {fmt(row['recall'])} | {fmt(row['precision'])} | "
            f"{fmt(row['actionability'])} | {row['n']} |"
        )
    if gap_rows:
        lines += ["", "## GOLD latent-gap items", ""]
        for stem, entry in sorted(gap_rows.items()):
            lines.append(
                f"- {stem}: arm hit {entry['arm']}/{entry['n']}, "
                f"baseline {entry['baseline']}/{entry['n']} (1-item "
                "measurement — a direction, not a number)"
            )
    return "\n".join(lines) + "\n"


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as handle:
        handle.write(text)
    os.replace(tmp, path)


def upsert_index(month: str, aggregate, wins, config) -> None:
    index = DS / "results" / "reviewbot" / "INDEX.md"
    header = [
        "# Reviewbot monthly probe series",
        "",
        "One row per month; rerunning a month replaces its row. "
        "Loop+model numbers — never merge into model_comparison.md.",
        "",
        "| month | Δrecall | Δprecision | Δactionability | W-T-L | "
        "bot | judge |",
        "|---|---|---|---|---|---|---|",
    ]
    row = (
        f"| {month} | {aggregate['recall']['delta']:+.3f} "
        f"±{aggregate['recall']['ci']:.3f} "
        f"| {aggregate['precision']['delta']:+.3f} "
        f"| {aggregate['actionability']['delta']:+.3f} "
        f"| {wins['arm']}-{wins['tie']}-{wins['baseline']} "
        f"| {config.get('bot_sha', 'unknown')[:12]} | {JUDGE_MODEL} |"
    )
    rows: dict[str, str] = {}
    if index.is_file():
        for line in index.read_text().splitlines():
            matched = re.match(r"^\| (\d{4}-\d{2}) \|", line)
            if matched:
                rows[matched.group(1)] = line
    rows[month] = row
    body = header + [rows[key] for key in sorted(rows)]
    write_atomic(index, "\n".join(body) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--gen-reps", type=int, default=3)
    parser.add_argument("--judge-reps", type=int, default=3)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    verdicts, stems, config = load_campaign(
        args.tag, args.gen_reps, args.judge_reps
    )
    if args.verify:
        print(
            f"[verify] ok: {len(verdicts)} verdicts = {len(stems)} items × "
            f"{args.gen_reps} gen × {args.judge_reps} judge replicates, "
            "roles/judge/sha all pinned"
        )
        return 0
    aggregate, item_rows, wins, gap_rows = analyze(verdicts, stems)
    report = render(args.tag, aggregate, item_rows, wins, gap_rows,
                    config, args.gen_reps, args.judge_reps)
    matched = MONTH_TAG.match(args.tag)
    name = matched.group(1) if matched else args.tag
    out = DS / "results" / "reviewbot" / f"REVIEWBOT_{name}.md"
    write_atomic(out, report)
    print(f"[report] {out}")
    if matched:
        upsert_index(matched.group(1), aggregate, wins, config)
        print(f"[report] INDEX.md upserted for {matched.group(1)}")
    else:
        print("[report] non-month tag — INDEX.md untouched")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CampaignError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(2) from exc
