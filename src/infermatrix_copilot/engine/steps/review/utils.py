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


def _review_verdict(comments: list[dict], pr_state: str = "") -> str:
    """Map structured findings to the product verdict used by GitHub reviews."""
    def uncertain(comment: dict) -> bool:
        hay = (
            str(comment.get("comment", ""))
            + " "
            + str(comment.get("evidence", ""))
        ).lower()
        return any(marker in hay for marker in (
            "uncertain", "unverified", "could not verify", "cannot verify",
            "budget exhaust", "not able to confirm",
        ))

    blocking = any(
        str(comment.get("severity", "")).lower() in ("blocker", "major")
        and not uncertain(comment)
        for comment in comments
    )
    if blocking:
        return (
            "FOLLOW-UP REQUIRED (post-merge)"
            if str(pr_state).upper() == "MERGED"
            else "REQUEST CHANGES"
        )
    return "COMMENT" if comments else "APPROVE"


def _review_summary_parts(output: dict) -> list[str]:
    """Render the scan and positive validation sections shared by both views."""
    comments = output.get("review_comments") or []
    validated = [
        str(finding).strip()
        for finding in (output.get("findings") or [])
        if str(finding).lstrip().lower().startswith(
            ("[validated]", "[upstream-verify]", "[sweep]")
        )
    ][:8]
    counts: dict[str, int] = {}
    for comment in comments:
        category = _category_of(comment)
        counts[category] = counts.get(category, 0) + 1
    scan = ["| Category | Result |", "|---|---|"]
    for name, _ in _CATEGORY_RULES:
        count = counts.get(name, 0)
        scan.append(
            f"| {name} | "
            f"{f'{count} finding(s) below' if count else 'no finding reported'} |"
        )
    parts = ["**Scan:**\n" + "\n".join(scan)]
    if validated:
        parts.append(
            "**Validated:**\n"
            + "\n".join(f"- {finding}" for finding in validated)
        )
    return parts


def _render_review_summary(output: dict, pr_state: str = "") -> str:
    """Render a concise review body; individual findings are posted inline."""
    comments = output.get("review_comments") or []
    parts = _review_summary_parts(output)
    summary = str(output.get("summary") or "").strip()
    if summary:
        parts.append(summary)
    elif comments:
        parts.append(f"{len(comments)} actionable finding(s).")
    else:
        parts.append("No actionable findings.")
    parts.append(f"**Verdict:** {_review_verdict(comments, pr_state)}")
    return "\n\n".join(parts)


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
    parts = _review_summary_parts(output)
    parts.append("\n\n".join(lines) if lines else output.get("summary", "No findings."))
    body = "\n\n".join(parts)
    return f"{body}\n\n**Verdict:** {_review_verdict(comments, pr_state)}"
