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


def _render_review_md(output: dict) -> str:
    comments = sorted(output.get("review_comments") or [],
                      key=lambda c: _SEVERITY_ORDER.get(
                          str(c.get("severity", "minor")).lower(), 2))
    lines = []
    for c in comments:
        loc = f"`{c.get('file', '?')}:{c.get('line', '?')}`"
        ev = f" (evidence: {c['evidence']})" if c.get("evidence") else ""
        lines.append(f"{loc} [{c.get('severity', 'minor')}] — "
                     f"{c.get('comment', '')}{ev}")
    # verdict coherence: severities above nit mean "belongs in THIS PR", and
    # asking for in-PR changes while approving is incoherent (the eval's
    # decision metric caught exactly that: all-minor reviews said APPROVE on
    # PRs whose human maintainers requested changes)
    blocking = any(str(c.get("severity", "")).lower()
                   in ("blocker", "major", "minor") for c in comments)
    verdict = "REQUEST CHANGES" if blocking else "APPROVE"
    body = "\n\n".join(lines) if lines else output.get("summary", "No findings.")
    return f"{body}\n\n**Verdict:** {verdict}"
