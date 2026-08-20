#!/usr/bin/env python3
"""compare_validation — the §8 PR6 Phase-5 comparison over ARTIFACTS.

Fail-closed by construction (design D9): every gate precondition is
verified from artifact-carried evidence — never recomputed from mutable
current trees — and any missing or mismatched piece stamps the report
**GATE-ELIGIBLE: NO** with the reasons. Cells the artifacts cannot decide
are marked HUMAN JUDGMENT PENDING, which is distinct from eligibility:
a gate-eligible report may still carry pending human judgments (the owner
signs COMPARISON.md, this tool only assembles the evidence).

Inputs (all artifact paths; see doc/RUNBOOK-rebase.md Phase 5):
  --ext-state       the ext world's terminal state.json (phase must be done)
  --ext-manifest    the ext world's built test manifest (its OWN slug set)
  --nat-run         the nat (v3) run directory
  --frozen-target   frozen target start SHA (values-file freeze table)
  --frozen-upstream frozen upstream SHA (values-file freeze table)
  --snapshot-digest the Phase-1 knowledge snapshot's logical digest
  --routing-golden  shell_golden.json (DRIFT #7 module-name mapping), optional
  --ext-wallclock-sec / --nat-wallclock-sec  optional recorded durations
  --out             output COMPARISON.md path (default: stdout)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _load_json(path: str, problems: list, label: str) -> dict:
    p = Path(path)
    if not p.is_file():
        problems.append(f"{label}: missing artifact {path}")
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except ValueError as exc:
        problems.append(f"{label}: unreadable ({exc})")
        return {}


def _nat_substate(run_dir: Path, problems: list) -> dict:
    sub = run_dir / "substate.json"
    if not sub.is_file():
        problems.append(f"nat run: no substate.json under {run_dir}")
        return {}
    try:
        return json.loads(sub.read_text(encoding="utf-8"))
    except ValueError as exc:
        problems.append(f"nat substate unreadable: {exc}")
        return {}


def _slug_set(manifest: dict) -> set[str]:
    jobs = manifest.get("jobs") or manifest.get("tests") or []
    if isinstance(jobs, dict):
        return set(jobs)
    return {str(j.get("slug", j)) if isinstance(j, dict) else str(j)
            for j in jobs}


def _routing_map(golden_path: str, problems: list) -> dict[str, str]:
    """slug -> module through the golden's recorded `assignment_routing`
    flavor (DRIFT #7; the REAL golden at
    adapters/<repo>/rebase/shell_golden.json — provenance keys starting
    with '_' are metadata, not routes)."""
    if not golden_path:
        return {}
    golden = _load_json(golden_path, problems, "routing golden")
    routing = {k: str(v) for k, v in
               (golden.get("assignment_routing") or {}).items()
               if not str(k).startswith("_")}
    if golden and not routing:
        problems.append("routing golden carries no assignment_routing "
                        "map — wrong artifact?")
    return routing


def build_report(args) -> tuple[str, bool]:
    problems: list[str] = []
    pending: list[str] = []

    ext_state = _load_json(args.ext_state, problems, "ext state")
    ext_manifest = _load_json(args.ext_manifest, problems, "ext manifest")
    nat_run = Path(args.nat_run)
    substate = _nat_substate(nat_run, problems)
    nat_manifest = _load_json(str(nat_run / "test_manifest.json"),
                              problems, "nat manifest")

    # ── gate preconditions, artifact-carried, ALL fail-closed ───────────
    # (missing evidence is a BLOCKER, never "pending" — pending is
    # reserved for judgments artifacts cannot carry by nature)
    if ext_state and str(ext_state.get("phase")) != "done":
        problems.append(
            f"ext world did not finish: phase={ext_state.get('phase')!r} "
            "(the comparison needs a completed baseline)")
    nat_phase = str(substate.get("phase") or "")
    if substate and nat_phase != "done":
        problems.append(
            f"nat run did not reach phase=done (phase={nat_phase!r}) — "
            "a needs-human/aborted run is not gate evidence without an "
            "owner-recorded waiver")
    knowledge = (substate.get("knowledge") or {})
    if knowledge.get("drift"):
        problems.append("nat run recorded parent-layer knowledge DRIFT "
                        "(open→close) — outside interference; owner waiver "
                        "required")
    required_evidence = (
        ("--snapshot-digest", args.snapshot_digest),
        ("--snapshot-skills-digest", args.snapshot_skills_digest),
        ("--ext-open-digest", args.ext_open_digest),
        ("--ext-open-skills-digest", args.ext_open_skills_digest),
        ("--frozen-target", args.frozen_target),
        ("--frozen-upstream", args.frozen_upstream),
        ("--ext-start-head", args.ext_start_head),
        ("--nat-start-head", args.nat_start_head),
        ("--ext-head", args.ext_head),
        ("--nat-head", args.nat_head),
        ("--routing-golden", args.routing_golden),
    )
    for flag, value in required_evidence:
        if not value:
            problems.append(f"{flag} not supplied — freeze-table/"
                            "attestation evidence is a gate requirement")
    import math
    if not all(isinstance(v, (int, float)) and math.isfinite(v) and v > 0
               for v in (args.ext_wallclock_sec, args.nat_wallclock_sec)):
        problems.append("wall-clock durations missing or invalid (must "
                        "be finite and > 0) — the 1.25x bound is a gate "
                        "requirement")
    # knowledge evidence must be COMPLETE (PR-boundary F16): drift is an
    # explicit False, never an absence; the close block must exist and
    # equal the open block per declared layer; both opening digests are
    # required
    if knowledge.get("drift") is not False:
        problems.append("nat run does not record knowledge drift == "
                        "False explicitly (absent/ambiguous evidence "
                        "never passes)")
    open_block = knowledge.get("open") or {}
    close_block = knowledge.get("close") or {}
    if open_block and not close_block:
        problems.append("nat run carries no CLOSING knowledge "
                        "attestation (compare step did not record it)")
    for layer, rec in open_block.items():
        open_digest = (rec or {}).get("digest", "")
        close_digest = (close_block.get(layer) or {}).get("digest", "")
        if open_digest and close_digest != open_digest:
            problems.append(
                f"knowledge layer {layer}: close digest != open digest "
                "(or missing from the close block)")
    nat_open_db = (open_block.get("parent_debug_db") or {}).get(
        "digest", "")
    nat_open_skills = (open_block.get("parent_skills_dir") or {}).get(
        "digest", "")
    if not nat_open_db:
        problems.append("nat run carries no opening knowledge "
                        "attestation (prelude provenance block absent)")
    if not nat_open_skills:
        problems.append("nat run carries no opening SKILLS attestation "
                        "— the skills layer's fairness is unproven")
    checks = (
        ("nat opening debug digest", nat_open_db, args.snapshot_digest),
        ("nat opening skills digest", nat_open_skills,
         args.snapshot_skills_digest),
        ("ext opening debug digest", args.ext_open_digest,
         args.snapshot_digest),
        ("ext opening skills digest", args.ext_open_skills_digest,
         args.snapshot_skills_digest),
    )
    for label, got, want in checks:
        if got and want and got != want:
            problems.append(
                f"{label} != Phase-1 snapshot ({got[:12]}… vs "
                f"{want[:12]}…) — that world did not open from the "
                "restored snapshot")
    def _sha_matches(got: str, want: str) -> bool:
        """Exact where lengths agree; otherwise the shorter must be a
        ≥12-char prefix of the longer (values files may record short
        SHAs) — never a lax 12-char default."""
        got, want = got.strip(), want.strip()
        if not got or not want or min(len(got), len(want)) < 12:
            return False
        shorter, longer = sorted((got, want), key=len)
        return longer.startswith(shorter)

    if args.frozen_upstream:
        nat_up = str(substate.get("upstream_commit") or "")
        if not nat_up:
            problems.append("nat substate carries no upstream_commit — "
                            "the frozen-upstream check cannot pass")
        elif not _sha_matches(nat_up, args.frozen_upstream):
            problems.append(
                f"nat upstream commit {nat_up[:12]} != frozen "
                f"{args.frozen_upstream[:12]}")
        ext_up = str(ext_state.get("vllm_commit")
                     or ext_state.get("upstream_commit") or "")
        if not ext_up:
            problems.append("ext state carries no upstream commit — "
                            "the frozen-upstream check cannot pass for "
                            "the baseline world")
        elif not _sha_matches(ext_up, args.frozen_upstream):
            problems.append(
                f"ext upstream commit {ext_up[:12]} != frozen "
                f"{args.frozen_upstream[:12]}")
    # frozen TARGET provenance is DECIDABLE from the recorded START heads
    # (each phase records `git rev-parse` before its run; post-run heads
    # move by design and are evidence only)
    if args.frozen_target:
        for label, start in (("ext", args.ext_start_head),
                             ("nat", args.nat_start_head)):
            if start and not _sha_matches(start, args.frozen_target):
                problems.append(
                    f"{label} start head {start[:12]} != frozen target "
                    f"{args.frozen_target[:12]} — that world did not "
                    "start from the frozen SHA")

    # ── slug sets (each world's OWN built manifest) ─────────────────────
    ext_slugs = _slug_set(ext_manifest)
    nat_slugs = _slug_set(nat_manifest)
    slug_equal = ext_slugs == nat_slugs and bool(ext_slugs)
    for label, slugs, manifest in (("ext", ext_slugs, ext_manifest),
                                   ("nat", nat_slugs, nat_manifest)):
        if manifest and not slugs:
            problems.append(f"{label} manifest is valid but EMPTY — zero "
                            "jobs is not comparable evidence")
    if ext_manifest and nat_manifest and not slug_equal:
        problems.append(
            f"slug sets differ: only-ext={sorted(ext_slugs - nat_slugs)[:10]} "
            f"only-nat={sorted(nat_slugs - ext_slugs)[:10]}")

    # ── per-module outcomes (module names are shared vocabulary) ────────
    ext_modules = {k: (v or {}).get("status", v)
                   for k, v in (ext_state.get("modules") or {}).items()}
    nat_modules = {k: (v or {}).get("status", "?")
                   for k, v in (substate.get("modules") or {}).items()}

    # ── PER-SLUG outcomes, equal-or-better (PR-boundary F17) ────────────
    # ext per-slug results are REQUIRED artifact evidence (--ext-results:
    # {slug: "passed"|"failed"}); nat failures come from substate; a slug
    # the ext world passed and the nat world failed is a hard blocker.
    route = _routing_map(args.routing_golden, problems)
    slug_rows: list[str] = []
    if not args.ext_results:
        problems.append("--ext-results not supplied — per-slug "
                        "equal-or-better cannot be judged")
        ext_results: dict = {}
    else:
        ext_results = {k: str(v) for k, v in _load_json(
            args.ext_results, problems, "ext results").items()}
    nat_failed = {str(t) for t in
                  ((substate.get("tests") or {}).get("pipeline") or {})
                  .get("failed_tests") or []}
    for slug in sorted(set(ext_results) | nat_failed):
        ext_out = ext_results.get(slug, "(absent)")
        nat_out = "failed" if slug in nat_failed else \
            ("passed" if slug in nat_slugs else "(absent)")
        module = route.get(slug, "(unmapped)")
        slug_rows.append(f"- {slug} [{module}]: ext={ext_out} "
                         f"nat={nat_out}")
        if ext_out == "passed" and nat_out == "failed":
            problems.append(f"per-slug regression: {slug} passed in ext "
                            "but FAILED in nat (equal-or-better "
                            "violated)")

    # ── wall-clock ──────────────────────────────────────────────────────
    import math as _math
    wall_line = "durations missing/invalid — recorded as a gate blocker"
    if all(isinstance(v, (int, float)) and _math.isfinite(v) and v > 0
           for v in (args.ext_wallclock_sec, args.nat_wallclock_sec)):
        ratio = args.nat_wallclock_sec / args.ext_wallclock_sec
        wall_line = (f"nat {args.nat_wallclock_sec:.0f}s / ext "
                     f"{args.ext_wallclock_sec:.0f}s = {ratio:.2f}x "
                     f"(bound 1.25x) — "
                     + ("WITHIN BOUND" if ratio <= 1.25 else "EXCEEDED"))
        if ratio > 1.25:
            problems.append(f"wall-clock ratio {ratio:.2f}x exceeds the "
                            "1.25x bound")

    eligible = not problems
    lines = ["# COMPARISON — repo-rebase v3 (nat) vs external baseline "
             "(ext)", "",
             f"**GATE-ELIGIBLE: {'YES' if eligible else 'NO'}**", ""]
    if problems:
        lines.append("## Gate blockers (fail-closed)")
        lines += [f"- {p}" for p in problems]
        lines.append("")
    if pending:
        lines.append("## Human judgment pending")
        lines += [f"- {p}" for p in pending]
        lines.append("")
    lines += ["## Evidence",
              f"- frozen target SHA: {args.frozen_target or '(missing)'}",
              f"- frozen upstream SHA: {args.frozen_upstream or '(missing)'}",
              f"- snapshot digests (db / skills): "
              f"{args.snapshot_digest or '(missing)'} / "
              f"{args.snapshot_skills_digest or '(missing)'}",
              f"- ext opening attestation (db / skills): "
              f"{args.ext_open_digest or '(missing)'} / "
              f"{args.ext_open_skills_digest or '(missing)'}",
              f"- start heads (ext / nat, vs frozen target): "
              f"{args.ext_start_head or '(missing)'} / "
              f"{args.nat_start_head or '(missing)'}",
              f"- post-run heads (ext / nat): "
              f"{args.ext_head or '(missing)'} / "
              f"{args.nat_head or '(missing)'}",
              f"- nat knowledge drift: {knowledge.get('drift', '(none recorded)')}",
              f"- terminal phases (ext / nat): "
              f"{ext_state.get('phase', '(missing)')} / "
              f"{nat_phase or '(missing)'}",
              "",
              "## Slug set (each world's OWN built manifest)",
              f"- ext: {len(ext_slugs)} jobs; nat: {len(nat_slugs)} jobs; "
              f"identical: {slug_equal}",
              "", "## Per-module outcomes"]
    for module in sorted(set(ext_modules) | set(nat_modules)):
        e = ext_modules.get(module, "(absent)")
        n = nat_modules.get(module, "(absent)")
        verdict = "equal" if e == n else "HUMAN JUDGMENT PENDING " \
            "(one rerun allowed per flaky divergence; investigate via v1)"
        lines.append(f"- {module}: ext={e} nat={n} — {verdict}")
    if not (ext_modules or nat_modules):
        lines.append("- (no module records on either side)")
    lines += ["", "## Per-slug outcomes (modules via the golden's "
              "assignment_routing; ext-pass/nat-fail blocks)"]
    lines += slug_rows or ["- (no per-slug records)"]
    lines += ["", "## CI (equal-or-better obligation)"]
    ci = substate.get("ci") or {}
    if ci:
        lines.append(f"- nat remote CI: {ci.get('result', '?')}"
                     + (f" ({ci.get('reason')})" if ci.get("reason") else ""))
    else:
        lines.append("- nat run carries no CI substate")
    lines.append("- ext CI verdict: HUMAN JUDGMENT PENDING (read from the "
                 "provider records for the ext run's builds)")
    lines += ["", "## Wall-clock", f"- {wall_line}", "",
              "## Flaky-rerun ledger (human-recorded)",
              "- (record each allowed single rerun here: module/slug, "
              "divergence, rerun outcome)", "",
              "## Sign-off",
              "- [ ] owner name + date (gate requires GATE-ELIGIBLE: YES "
              "and every pending judgment resolved)"]
    return "\n".join(lines) + "\n", eligible


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ext-state", required=True)
    parser.add_argument("--ext-manifest", required=True)
    parser.add_argument("--nat-run", required=True)
    parser.add_argument("--frozen-target", default="")
    parser.add_argument("--frozen-upstream", default="")
    parser.add_argument("--snapshot-digest", default="",
                        help="Phase-1 snapshot: debug-db logical digest")
    parser.add_argument("--snapshot-skills-digest", default="",
                        help="Phase-1 snapshot: skills catalog digest")
    parser.add_argument("--ext-open-digest", default="",
                        help="ext world's OPENING db attestation (Phase 3)")
    parser.add_argument("--ext-open-skills-digest", default="",
                        help="ext world's OPENING skills attestation")
    parser.add_argument("--ext-start-head", default="",
                        help="ext world's recorded PRE-run target HEAD "
                             "(must equal the frozen target SHA)")
    parser.add_argument("--nat-start-head", default="",
                        help="nat world's recorded PRE-run target HEAD "
                             "(must equal the frozen target SHA)")
    parser.add_argument("--ext-head", default="",
                        help="ext world's recorded post-run target HEAD")
    parser.add_argument("--nat-head", default="",
                        help="nat world's recorded post-run target HEAD")
    parser.add_argument("--routing-golden", default="",
                        help="the adapter's shell_golden.json "
                             "(assignment_routing slug→module map)")
    parser.add_argument("--ext-results", default="",
                        help="ext world's per-slug outcomes json "
                             "({slug: passed|failed}) — required")
    parser.add_argument("--ext-wallclock-sec", type=float, default=0.0)
    parser.add_argument("--nat-wallclock-sec", type=float, default=0.0)
    parser.add_argument("--out", default="")
    args = parser.parse_args(argv)
    report, eligible = build_report(args)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"wrote {args.out} (GATE-ELIGIBLE: "
              f"{'YES' if eligible else 'NO'})")
    else:
        print(report, end="")
    return 0 if eligible else 2


if __name__ == "__main__":
    sys.exit(main())
