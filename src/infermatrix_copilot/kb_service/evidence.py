"""What the L2 judge sees for ONE rule: the upstream PRs it cites, with full diffs.

An intake event stores a merged PR with an 8 KB diff excerpt (enough to draft
from), and a change set judges every rule against the evidence of its whole
batch. The judge then reads ten PRs' worth of excerpts and still misses the
code a rule describes: "the supplied diff ends before ..." was the most common
reason for an unsure or failed verdict in the first live run.

``for_rule`` narrows the evidence to the PRs the rule cites (``^[PR #N]``, and
the PRs its lifecycle footer names as evidence; all of them when it cites none
we hold) and replaces each excerpt with the full
per-file diffs of the PR as GitHub shows it (its head against its merge
base with main), read from the service's own upstream
mirror: files the rule names first, then source, tests, docs and configuration, within ``PER_FILE`` and
``PER_RULE`` bytes. Only upstream merged-PR evidence is expanded; anything the
mirror cannot answer keeps its excerpt (the judge says "unsure" rather than
guessing), so expansion never makes a verdict easier than today.
"""

from __future__ import annotations

import re

from ..knowledge_service.facts import CODE_SPAN, EVIDENCE_PR, PR_CITATION, FactsError
from ..knowledge_service.lifecycle import FOOTER

PER_FILE = 24 * 1024
PER_RULE = 48 * 1024
NOTE = ("full per-file diffs of the merged commit (files the rule names first); "
        "a file cut at the byte limit says so")


def _named(text: str) -> list[str]:
    out = []
    for m in CODE_SPAN.finditer(text):
        token = m.group("tok").strip().partition("::")[0].strip("/")
        if "/" in token or re.search(r"\.[A-Za-z0-9]{1,5}$", token):
            out.append(token)
    return out


def _rank(path: str) -> int:
    """Source before tests before docs and configuration (the code a rule describes first)."""
    parts = path.lower().split("/")
    if any(p in ("docs", "doc", "recipes", "examples") for p in parts[:-1]) or \
            parts[-1].endswith((".md", ".rst", ".txt", ".yaml", ".yml", ".json", ".toml")):
        return 2
    if any(p in ("tests", "test") for p in parts[:-1]) or parts[-1].startswith("test_"):
        return 1
    return 0


def _matches(path: str, names: list[str]) -> bool:
    return any(path == n or path.endswith("/" + n) or n.endswith("/" + path) for n in names)


def _cut(text: str, limit: int) -> str:
    data = text.encode("utf-8")
    if len(data) <= limit:
        return text
    return data[:limit].decode("utf-8", "ignore") + f"\n[... cut at {limit} bytes of {len(data)}]\n"


def for_rule(text: str, evidence: list[dict], observer) -> list[dict]:
    """The evidence for one rule (``text``: the rule as proposed, or as it was)."""
    cited = {f"PR #{m.group('n')}" for m in PR_CITATION.finditer(text)}
    # a retirement's justification lives in its footer (evidence="PR #N"), not in a citation
    for line in text.splitlines():
        footer = FOOTER.match(line.strip())
        if footer:
            cited |= {f"PR #{m.group('n')}" for m in EVIDENCE_PR.finditer(footer.group("attrs"))}
    items = [e for e in evidence if e.get("source_reference") in cited] or list(evidence)
    if observer is None:
        return items
    names, budget, out = _named(text), PER_RULE, []
    for item in items:
        number = re.fullmatch(r"PR #(\d+)", str(item.get("source_reference") or ""))
        if not number or "merged_at" not in item or budget <= 0:
            out.append(item)  # not an upstream merged PR (or no room left): as recorded
            continue
        try:
            sha = str(item.get("merge_commit_sha") or observer.pull(int(number.group(1))).get("merge_commit_sha") or "")
            if not sha:
                raise FactsError("no merge commit")
            files = list(item.get("changed_files") or [])
            ordered = sorted(files, key=lambda f: (not _matches(f, names), _rank(f)))
            diffs: dict[str, str] = {}
            for path in ordered:
                if budget <= 0:
                    break
                diff = _cut(observer.pr_diff(int(number.group(1)), sha, path), min(PER_FILE, budget))
                if diff:
                    diffs[path] = diff
                    budget -= len(diff.encode("utf-8"))
        except FactsError:
            out.append(item)
            continue
        if not diffs:
            out.append(item)
            continue
        expanded = {k: v for k, v in item.items() if k != "diff_excerpt"}
        out.append({**expanded, "diffs": diffs, "diffs_note": NOTE,
                    "diffs_omitted": [f for f in ordered if f not in diffs]})
    return out
