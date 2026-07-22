"""Deterministic helpers for the review step: the diff sweep-target extractor
and the review-markdown renderer (with its verdict-coherence rule).

Both are pure functions over a diff / an output dict — no LLM, no state — so
they live apart from the agent handlers in `steps.py`. `_sweep_targets` feeds
the ensemble the ENUMERABLE classes (index assumptions, new branches, untested
files) so lens coverage never depends on a model re-enumerating the diff.
"""

from __future__ import annotations

_SEVERITY_ORDER = {"critical": 0, "blocker": 1, "major": 2, "minor": 3, "nit": 4}


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


def _render_review_md(output: dict) -> str:
    """Render the review output dict as Markdown: comments sorted by severity,
    each as `file:line [severity] — comment` with optional evidence, followed
    by a verdict line. The verdict enforces coherence — any comment at blocker,
    blocker/major (and only when not self-declared-uncertain) means the PR
    must change -> REQUEST CHANGES; other comments -> COMMENT; none ->
    APPROVE. Positive [validated]/[upstream-verify]/[sweep] findings render
    as a 'Validated' section. Falls back to the summary without comments."""
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
    blocking = any(str(c.get("severity", "")).lower() in ("critical", "blocker", "major")
                   and not _uncertain(c) for c in comments)
    if blocking:
        verdict = "REQUEST CHANGES"
    elif comments:
        verdict = "COMMENT"  # non-blocking asks; mergeable as-is
    else:
        verdict = "APPROVE"
    parts = []
    if validated:
        parts.append("**Validated:**\n" + "\n".join(f"- {v}" for v in validated))
    parts.append("\n\n".join(lines) if lines else output.get("summary", "No findings."))
    body = "\n\n".join(parts)
    return f"{body}\n\n**Verdict:** {verdict}"
