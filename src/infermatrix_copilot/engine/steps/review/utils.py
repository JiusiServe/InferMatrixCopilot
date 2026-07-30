"""Deterministic helpers for the review step: the diff sweep-target extractor
and the review-markdown renderer (with its verdict-coherence rule).

Both are pure functions over a diff / an output dict — no LLM, no state — so
they live apart from the agent handlers in `steps.py`. `_sweep_targets` feeds
the ensemble the ENUMERABLE classes (index assumptions, new branches, untested
files) so lens coverage never depends on a model re-enumerating the diff.
"""

from __future__ import annotations

_SEVERITY_ORDER = {"blocker": 0, "major": 1, "minor": 2, "nit": 3}


def _sweep_targets(diff: str, language: str = "python") -> str:
    """Deterministic sweep targets extracted from the diff's added lines.

    Injected as evidence so lens coverage of the ENUMERABLE classes (index
    assumptions, new branches, untested files) never depends on the model
    enumerating the diff itself — stochastic self-enumeration was the
    highest-variance link in review recall (whole classes silently skipped
    on some runs).

    The line-level extractors are language-keyed (from the repo profile);
    an unknown language degrades to the file-level sections only — recorded
    honestly instead of running Python heuristics on foreign syntax."""
    import re

    from ....profiles.languages import sweep_re
    rules = sweep_re(language)
    current: str | None = None
    new_line = 0
    subs: list[str] = []
    branches: list[str] = []
    files: set[str] = set()
    test_files: set[str] = set()
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
            files.add(current)
            if current.startswith("tests/") or "/tests/" in current:
                test_files.add(current)
        elif line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            new_line = int(m.group(1)) if m else 0
        elif current and line.startswith("+") and not line.startswith("+++"):
            code = line[1:]
            stripped = code.strip()
            if rules is not None:
                if rules[0].search(code):
                    subs.append(f"{current}:{new_line} `{stripped[:90]}`")
                if rules[1].match(stripped):
                    branches.append(f"{current}:{new_line} `{stripped[:90]}`")
            new_line += 1
        elif current and not line.startswith("-"):
            new_line += 1
    non_test = sorted(f for f in files if f not in test_files)
    out: list[str] = []
    if subs:
        out.append("INDEXED/FIRST-ELEMENT ACCESSES ADDED — contracts lens "
                   "must state the assumption + what guarantees it for EACH:")
        out += [f"- {s}" for s in subs[:20]]
    if branches:
        out.append("NEW/CHANGED BRANCHES — logic lens must answer for EACH: "
                   "can all arms occur? dead/redundant?")
        out += [f"- {b}" for b in branches[:25]]
    if non_test:
        out.append("NON-TEST FILES TOUCHED — verification lens must name the "
                   "test/benchmark covering each changed path:")
        out += [f"- {f}" for f in non_test[:20]]
    out.append("TEST FILES TOUCHED IN THIS DIFF: "
               + (", ".join(sorted(test_files)) or "NONE"))
    return "\n".join(out)


_CATEGORY_RULES = (
    # deterministic finding→category keyword map (W2: no PASS inference — a
    # row without findings renders "no finding reported", an honest coverage
    # display, never a claimed verification)
    ("Tests / verification", ("test", "coverage", "assert", "regression",
                              "benchmark", "fixture")),
    ("Security", ("security", "inject", "secret", "credential", "unsafe",
                  "traversal", "sanitiz")),
    ("Docs / comments", ("docstring", "comment", "doc", "readme", "stale")),
    ("Behavior / compatibility", ("break", "consumer", "default", "api",
                                  "compat", "regress", "behavior", "caller")),
    ("Correctness", ()),  # catch-all
)


def _category_of(c: dict) -> str:
    hay = (str(c.get("comment", "")) + " " + str(c.get("evidence", ""))).lower()
    for name, keys in _CATEGORY_RULES:
        if any(k in hay for k in keys):
            return name
    return "Correctness"


def _render_review_md(output: dict, pr_state: str = "") -> str:
    """Render the review output dict as Markdown: a category scan table
    (finding counts per category; empty rows say `no finding reported`),
    comments sorted by severity as `file:line [severity] — comment`, then a
    verdict line. The verdict enforces coherence — blocker/major (not
    self-declared-uncertain) -> REQUEST CHANGES, softened to
    `FOLLOW-UP REQUIRED (post-merge)` when `pr_state` is MERGED (a merged PR
    cannot coherently be blocked; the finding ships as a follow-up); other
    comments -> COMMENT; none -> APPROVE. Positive [validated]/[sweep]
    findings render as a 'Validated' section."""
    comments = sorted(output.get("review_comments") or [],
                      key=lambda c: _SEVERITY_ORDER.get(
                          str(c.get("severity", "minor")).lower(), 2))
    lines = []
    for c in comments:
        loc = f"`{c.get('file', '?')}:{c.get('line', '?')}`"
        ev = f" (evidence: {c['evidence']})" if c.get("evidence") else ""
        lines.append(f"{loc} [{c.get('severity', 'minor')}] — "
                     f"{c.get('comment', '')}{ev}")
    # "What I validated": lenses record positive verifications as findings
    # ([validated]/[upstream-verify]/[sweep] prefixes). On approved PRs the
    # human reviewers' "concerns" are mostly validation reasoning — a
    # comments-only review structurally caps recall (T3 forensics #4).
    validated = [str(f).strip() for f in (output.get("findings") or [])
                 if str(f).lstrip().lower().startswith(
                     ("[validated]", "[upstream-verify]", "[sweep]"))][:8]
    # Verdict calibration (T3 forensics #2): only blocker/major block — a
    # `minor` is an in-PR ask but not merge-blocking (14/15 human-approved
    # PRs got REQUEST CHANGES under the old rule). A comment whose own text
    # or evidence declares uncertainty can never block.
    def _uncertain(c: dict) -> bool:
        hay = (str(c.get("comment", "")) + " " + str(c.get("evidence", ""))).lower()
        return any(m in hay for m in ("uncertain", "unverified", "could not verify",
                                      "cannot verify", "budget exhaust",
                                      "not able to confirm"))
    blocking = any(str(c.get("severity", "")).lower() in ("blocker", "major")
                   and not _uncertain(c) for c in comments)
    if blocking:
        verdict = "FOLLOW-UP REQUIRED (post-merge)" \
            if str(pr_state).upper() == "MERGED" else "REQUEST CHANGES"
    elif comments:
        verdict = "COMMENT"  # non-blocking asks; mergeable as-is
    else:
        verdict = "APPROVE"
    parts = []
    # category scan: judge-visible coverage without claiming verification
    counts: dict[str, int] = {}
    for c in comments:
        counts[_category_of(c)] = counts.get(_category_of(c), 0) + 1
    scan = ["| Category | Result |", "|---|---|"]
    for name, _ in _CATEGORY_RULES:
        n = counts.get(name, 0)
        scan.append(f"| {name} | {f'{n} finding(s) below' if n else 'no finding reported'} |")
    parts.append("**Scan:**\n" + "\n".join(scan))
    if validated:
        parts.append("**Validated:**\n" + "\n".join(f"- {v}" for v in validated))
    parts.append("\n\n".join(lines) if lines else output.get("summary", "No findings."))
    body = "\n\n".join(parts)
    return f"{body}\n\n**Verdict:** {verdict}"
