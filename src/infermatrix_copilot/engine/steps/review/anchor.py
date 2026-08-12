"""Derive a review comment's line from a verbatim code snippet.

A model that is asked for a line number gets it wrong often enough that we demote the
finding at publish time. The fix is not a better validator but a different question:
have the model quote the code it is talking about, and compute the position ourselves.
That is OCR's design (`internal/diff/resolver.go:82` — its comment tool accepts no line
number at all), and the arithmetic is exactly what a program should own.

Our validator still runs last, so the "never post a wrong anchor" guarantee is unchanged.
What changes is that a finding whose *only* defect was the number keeps its inline
position instead of being demoted into the review body.

This module owns the diff walk and the path normalizer for the whole engine. It cannot
import from `..pr.publish` — that module already imports from this package
(`publish.py:17`), so the dependency runs pr → review and the reverse would cycle.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# BOTH declared counts are captured. The new side alone is not enough: a diff clipped
# after the last right-side line but before trailing deletions still balances on the new
# side, so the file would read as intact while its removed-code index is short — and a
# snippet quoting one of those lost deletions could then resolve onto an identical
# earlier right-side line and be published as a verified anchor.
_HUNK = re.compile(r"^@@ -\d+(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

RESOLVED = "resolved"
AMBIGUOUS = "ambiguous"
UNMATCHED = "unmatched"
INVALID = "invalid"


def normalize_path(path: object) -> str:
    """Canonical form of a diff path. Lives here rather than in publish.py because the
    walk below keys on it and both sides must agree; two normalizers would drift."""
    value = str(path or "").strip().replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return value[2:] if value.startswith("b/") else value


@dataclass
class FileIndex:
    """One file's diff, indexed per hunk.

    `right` is every RIGHT-side line (added *and* context) as `(lineno, raw_content)`,
    unfiltered — a bare `+` added line and a bare ` ` context line are both addressable
    by GitHub's API, so dropping blank lines here would silently shrink the set publish
    validates against and start demoting findings that are inline today. Blanks are
    skipped when *matching*, which is a different concern.

    `old` is the OLD side as `(content, is_deletion)` — context *and* deletions together,
    contiguous, in old-side order. Both obvious alternatives are wrong: indexing only
    deletions makes two deletions separated by context falsely adjacent, and indexing
    everything without the flag would demote context-only snippets, which anchor
    perfectly well on the right. It carries no line numbers because it is used only to
    detect that a snippet quotes removed code, never to anchor anything.

    Segments are per hunk so a multi-line snippet cannot match the tail of one hunk plus
    the head of the next — adjacent in a flat list, far apart in the file.
    """

    right: list[list[tuple[int, str]]] = field(default_factory=list)
    old: list[list[tuple[str, bool]]] = field(default_factory=list)
    state: str = "no_clipping_detected"


def diff_index(diff: str) -> dict[str, FileIndex]:
    """Walk a unified diff into per-file, per-hunk segments for both sides."""
    files: dict[str, FileIndex] = {}
    path = ""
    new_line: int | None = None
    hunk_path = ""
    declared_new = seen_new = declared_old = seen_old = 0
    seg_right: list[tuple[int, str]] = []
    seg_old: list[tuple[str, bool]] = []

    def close_hunk() -> None:
        nonlocal hunk_path, declared_new, seen_new, declared_old, seen_old
        nonlocal seg_right, seg_old
        if hunk_path:
            entry = files.setdefault(hunk_path, FileIndex())
            entry.right.append(seg_right)
            entry.old.append(seg_old)
            if seen_new < declared_new or seen_old < declared_old:
                entry.state = "incomplete"
        hunk_path = ""
        declared_new = seen_new = declared_old = seen_old = 0
        seg_right, seg_old = [], []

    for raw in str(diff or "").splitlines():
        if raw.startswith("diff --git "):
            close_hunk()
            path, new_line = "", None
        elif new_line is None and raw.startswith("+++ "):
            candidate = raw[4:].strip()
            path = "" if candidate == "/dev/null" else normalize_path(candidate)
            if path:
                files.setdefault(path, FileIndex())
            new_line = None
        elif raw.startswith("@@"):
            close_hunk()
            match = _HUNK.match(raw)
            if match and path:
                new_line = int(match.group(2))
                # an absent count means 1 line, per the unified-diff grammar
                declared_old = int(match.group(1)) if match.group(1) is not None else 1
                declared_new = int(match.group(3)) if match.group(3) is not None else 1
                hunk_path, seen_new, seen_old = path, 0, 0
            else:
                new_line = None
        elif path and new_line is not None:
            if raw.startswith("\\"):        # "\ No newline at end of file"
                continue
            marker, content = raw[:1], raw[1:]
            if marker == "-":
                # INSIDE a hunk every "-" is a deletion, with no exception for "---":
                # a deleted source line reading `--option` renders as `---option`, and
                # treating it as a file header would invent a right-side line number
                # for content that does not exist there. Headers cannot reach this
                # branch — they precede the first @@, while new_line is still None.
                seg_old.append((content, True))
                seen_old += 1
            else:
                seg_right.append((new_line, content))
                new_line += 1
                seen_new += 1
                if marker != "+":           # context exists on both sides
                    seg_old.append((content, False))
                    seen_old += 1
    close_hunk()
    return files


def _block(text: str) -> list[str]:
    """Snippet lines with whole blank lines trimmed off each END of the block only.

    Interior blanks are structure and are kept; a model's quote just often carries a
    stray leading or trailing newline.
    """
    lines = text.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def _tiers(snippet: str) -> list[tuple[list[list[str]], bool]]:
    """Match attempts grouped into precision TIERS: `(competing_forms, loose)`.

    Two axes, and they compose differently:

    * PRECISION is ordered — exact before rstrip. Normalizing first loses
      trailing-whitespace-only edits: given `-value = 1` / `+value = 1  `, both sides
      rstrip to the same text, so the verbatim ADDED snippet reads as removed code.
    * INTERPRETATION is not ordered — the raw text and the `+`-stripped text are rival
      readings of the same snippet, so they are evaluated TOGETHER and disagreement is
      ambiguity. Trying them in sequence and taking the first hit silently picks a
      winner: with a context line whose source literally begins `+value = 1` and an
      added line `value = 1` in the same hunk, the raw reading would anchor the context
      line before the unmarked reading ever saw the intended addition.

    `-` is never stripped: that turns a quote of removed code into a right-side anchor.
    """
    raw = _block(snippet)
    if not raw:
        return []
    unmarked = [line[1:] if line[:1] == "+" else line for line in raw]
    forms = [raw] if unmarked == raw else [raw, unmarked]

    loose: list[list[str]] = []
    for form in forms:
        rstripped = [line.rstrip() for line in form]
        if rstripped not in loose:
            loose.append(rstripped)

    tiers = [(forms, False)]
    if loose != forms:
        tiers.append((loose, True))
    return tiers


def _normalized(text: str) -> list[str]:
    """Trailing whitespace only. Indentation and interior blank lines are structure.

    OCR strips both ends and drops blanks (`normalizeLine`, resolver.go:232). Copying
    that here was wrong in three ways, because unlike OCR we also consult the old side:

    * an indentation-only change makes the removed and added lines normalize to the
      SAME text, so a perfectly valid added snippet is classified as quoting removed
      code and demoted;
    * dropping blank lines makes two deletions separated by a blank context line
      adjacent, fabricating a multi-line "removed" match;
    * likewise on the right, a snippet could match across omitted blanks.

    So: `rstrip` each line, keep interior blanks, and trim only whole blank lines from
    the ends of the block (a model's quote often carries a stray leading newline).
    """
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return lines


def _without_marker(text: str) -> str:
    """Drop exactly one leading `+` per line — never a `-`.

    A model copying an ADDED line out of a diff often brings its `+`. Stripping `-` as
    well looked symmetric and was a hole: given a diff adding `x = 1`, the snippet
    `-x = 1` would strip to `x = 1` and resolve onto that added line, turning a quote of
    removed code into a verified right-side anchor. Left unstripped, such a snippet
    simply fails to match right-side content — which is the safe outcome. A genuine
    source line beginning with `-` (a YAML item, a negative literal) still matches on the
    unstripped first attempt.
    """
    return "\n".join(
        line[1:] if line[:1] == "+" else line
        for line in text.splitlines()
    )


def _right_hits(target: list[str], index: FileIndex, loose: bool) -> list[int]:
    """Every right-side line number where `target` matches consecutively."""
    hits: list[int] = []
    for segment in index.right:
        rows = [(num, text.rstrip() if loose else text) for num, text in segment]
        for start in range(len(rows) - len(target) + 1):
            if all(rows[start + i][1] == target[i] for i in range(len(target))):
                hits.append(rows[start][0])
    return hits


def _quotes_removed_code(target: list[str], index: FileIndex, loose: bool) -> bool:
    """True when `target` matches an old-side window containing a real deletion.

    A pure-context window does not count: context anchors fine on the right, and
    demoting on it would regress behaviour that works today.
    """
    for segment in index.old:
        rows = [(text.rstrip() if loose else text, gone) for text, gone in segment]
        for start in range(len(rows) - len(target) + 1):
            window = rows[start:start + len(target)]
            if all(window[i][0] == target[i] for i in range(len(target))):
                if any(gone for _, gone in window):
                    return True
    return False


def resolve_snippet(snippet: object, index: FileIndex) -> tuple[str, int | None]:
    """Derive the right-side line a snippet refers to.

    Returns a status rather than an optional int so callers can tell `ambiguous` from
    `unmatched` without re-running the match. Every non-`resolved` status means the
    caller must NOT trust the model's declared line either — we looked and could not
    corroborate it, which is strictly worse evidence than never having looked.
    """
    if not isinstance(snippet, str):
        return INVALID, None       # never stringify: str(["x"]) could false-match
    # KNOWN RESIDUAL LIMIT: this refuses only *detected* incompleteness. Hunk counts
    # cannot see an omitted whole hunk, an omitted file, or a clip exactly on a hunk
    # boundary — such a diff still reads as intact, and a snippet quoting a deletion
    # that never arrived could match a surviving identical context line. Closing that
    # needs completeness established by the FETCH layer, not inferred from the text:
    # `pr/fetch.py` builds diff_text either from `gh pr diff` (API, truncatable) or a
    # local `git diff base..head` (complete by construction), and only it knows which.
    # Plumbing that provenance through state is its own change; recorded, not smuggled.
    if index.state == "incomplete":
        # Detecting a clipped file is worth nothing if we then derive from it. The
        # deletion guard below can only report what the old side CONTAINS, and on a
        # short index its silence proves nothing — a snippet quoting a deletion that
        # never arrived would sail past it and match a surviving identical context
        # line. Refuse the whole file rather than trust a check we know is blind.
        return AMBIGUOUS, None
    tiers = _tiers(snippet)
    if not tiers:
        return INVALID, None       # empty or whitespace-only

    # Within a tier the rival readings must AGREE; across tiers the first that resolves
    # wins, so a looser pass never overturns a precise one.
    for forms, loose in tiers:
        found: set[int] = set()
        for target in forms:
            if _quotes_removed_code(target, index, loose):
                return AMBIGUOUS, None
            hits = _right_hits(target, index, loose)
            if len(hits) > 1:
                return AMBIGUOUS, None
            found.update(hits)
        if len(found) > 1:         # the readings disagree — do not pick one
            return AMBIGUOUS, None
        if found:
            return RESOLVED, found.pop()
    return UNMATCHED, None


def resolve_review_comments(
    comments: list[dict], diff: str,
) -> tuple[list[dict], dict[str, int]]:
    """Replace each finding's line with the one derived from its snippet.

    A finding that supplied no snippet is untouched and keeps today's behaviour. A
    finding that supplied one we could not resolve is marked `_anchor_unverified`, and
    publish demotes it regardless of whether its declared line happens to be
    addressable — see `resolve_snippet`.
    """
    index = diff_index(diff)
    stats = {RESOLVED: 0, AMBIGUOUS: 0, UNMATCHED: 0, INVALID: 0,
             "disagreed": 0, "no_snippet": 0}

    def reject(comment: dict) -> dict:
        """One exit for every unresolved outcome, so no branch can forget to clear the
        uncorroborated line — the absent-file path did exactly that."""
        comment["_anchor_unverified"] = True
        if comment.get("line") is not None:
            comment["_declared_line"] = comment.pop("line")
        return comment

    out: list[dict] = []
    for raw in comments:
        comment = dict(raw) if isinstance(raw, dict) else {"comment": str(raw)}
        if comment.get("anchor_snippet") is None:
            stats["no_snippet"] += 1
            out.append(comment)
            continue
        file_index = index.get(normalize_path(comment.get("file")))
        if file_index is None:
            stats[UNMATCHED] += 1
            out.append(reject(comment))
            continue
        status, line = resolve_snippet(comment["anchor_snippet"], file_index)
        stats[status] += 1
        if status == RESOLVED:
            declared = comment.get("line")
            if isinstance(declared, bool) or not isinstance(declared, int) \
                    or declared != line:
                stats["disagreed"] += 1
            comment["line"] = line
        else:
            # `_render_review_md` prints `file:line` into the run report, so leaving an
            # uncorroborated position there would show it as authoritative — the exact
            # confusion that resolving before rendering exists to avoid.
            reject(comment)
        out.append(comment)
    return out, stats
