"""Snippet-derived anchoring: the position is computed, never taken on trust.

The rule that shapes almost every case here: a snippet we cannot resolve to exactly one
changed line does NOT fall back to the model's declared line. Having looked for
corroboration and failed is weaker evidence than never having looked, and an
API-addressable line is not the same thing as the intended anchor.
"""

from infermatrix_copilot.engine.steps.pr.publish import _partition_comments
from infermatrix_copilot.engine.steps.review.anchor import (
    AMBIGUOUS,
    INVALID,
    RESOLVED,
    UNMATCHED,
    diff_index,
    resolve_review_comments,
    resolve_snippet,
)

DIFF = (
    "diff --git a/m.py b/m.py\n--- a/m.py\n+++ b/m.py\n"
    "@@ -1,2 +1,4 @@\n"
    " import os\n"          # 1 context
    "+first = items[0]\n"   # 2 added
    "+second = rows[1]\n"   # 3 added
    " done = True\n"        # 4 context
)


def _index(diff=DIFF, path="m.py"):
    return diff_index(diff)[path]


# -- resolution ----------------------------------------------------------------


def test_exact_single_line_resolves():
    assert resolve_snippet("first = items[0]", _index()) == (RESOLVED, 2)


def test_multi_line_snippet_resolves_to_its_first_line():
    snippet = "first = items[0]\nsecond = rows[1]"
    assert resolve_snippet(snippet, _index()) == (RESOLVED, 2)


def test_trailing_whitespace_is_tolerated():
    assert resolve_snippet("first = items[0]   \n", _index()) == (RESOLVED, 2)


def test_indentation_is_significant():
    """Leading whitespace is structure, not noise. Stripping it would make an
    indentation-only change normalize its removed and added lines identically, so a
    perfectly valid added snippet would be classified as quoting removed code."""
    assert resolve_snippet("    first = items[0]", _index()) == (UNMATCHED, None)

    indent_only = (
        "diff --git a/h.py b/h.py\n--- a/h.py\n+++ b/h.py\n"
        "@@ -1,1 +1,1 @@\n-  val = 1\n+    val = 1\n"
    )
    idx = diff_index(indent_only)["h.py"]
    assert resolve_snippet("    val = 1", idx) == (RESOLVED, 1)   # the added form
    assert resolve_snippet("  val = 1", idx) == (AMBIGUOUS, None)  # the removed form


def test_snippet_still_carrying_its_diff_marker_resolves():
    """A model copying out of a diff often brings the +/- with it."""
    assert resolve_snippet("+first = items[0]", _index()) == (RESOLVED, 2)


def test_context_line_anchors_normally():
    """Context lines are addressable on the RIGHT and must not be treated as
    old-side content just because they also appear there."""
    assert resolve_snippet("import os", _index()) == (RESOLVED, 1)


def test_unmatched_snippet_reports_unmatched():
    assert resolve_snippet("nothing like this", _index()) == (UNMATCHED, None)


# -- refusals ------------------------------------------------------------------


def test_duplicate_snippet_is_ambiguous_not_first_match():
    """OCR takes the first match (resolver.go:148) — precisely its mis-anchor source."""
    dup = (
        "diff --git a/d.py b/d.py\n--- a/d.py\n+++ b/d.py\n"
        "@@ -1,1 +1,3 @@\n keep\n+x = 1\n+x = 1\n"
    )
    assert resolve_snippet("x = 1", diff_index(dup)["d.py"]) == (AMBIGUOUS, None)


def test_multi_line_snippet_cannot_span_two_hunks():
    """Adjacent in a flat list, hundreds of lines apart in the file. Segmenting per
    hunk is what stops this from fabricating an anchor."""
    # hunk B must OPEN with the target line: if a context line preceded it, the two
    # targets would not be adjacent even in a flattened list and the test would pass
    # against the very bug it is meant to catch.
    two = (
        "diff --git a/t.py b/t.py\n--- a/t.py\n+++ b/t.py\n"
        "@@ -1,1 +1,2 @@\n head\n+tail_of_hunk_a\n"
        "@@ -50,0 +51,1 @@\n+head_of_hunk_b\n"
    )
    idx = diff_index(two)["t.py"]
    assert resolve_snippet("tail_of_hunk_a", idx)[0] == RESOLVED
    assert resolve_snippet("head_of_hunk_b", idx)[0] == RESOLVED
    assert resolve_snippet("tail_of_hunk_a\nhead_of_hunk_b", idx) == (UNMATCHED, None)


def test_snippet_quoting_removed_code_is_ambiguous():
    removed = (
        "diff --git a/r.py b/r.py\n--- a/r.py\n+++ b/r.py\n"
        "@@ -1,2 +1,1 @@\n keep\n-gone = 1\n"
    )
    assert resolve_snippet("gone = 1", diff_index(removed)["r.py"]) == (AMBIGUOUS, None)


def test_removed_code_is_not_relocated_to_an_identical_right_side_line():
    """The dangerous case: the quoted line is being deleted here AND happens to exist
    elsewhere on the right. Anchoring there points at unrelated code."""
    moved = (
        "diff --git a/v.py b/v.py\n--- a/v.py\n+++ b/v.py\n"
        "@@ -1,2 +1,1 @@\n keep\n-dup = 1\n"
        "@@ -40,1 +40,2 @@\n other\n+dup = 1\n"
    )
    assert resolve_snippet("dup = 1", diff_index(moved)["v.py"]) == (AMBIGUOUS, None)


def test_deletions_separated_by_context_cannot_fabricate_a_match():
    """Indexing only `-` lines would make these two adjacent, so a two-line snippet
    would falsely read as removed code. The old side keeps its context to stay
    contiguous."""
    spaced = (
        "diff --git a/s.py b/s.py\n--- a/s.py\n+++ b/s.py\n"
        "@@ -1,4 +1,2 @@\n-alpha\n between\n-beta\n tail\n"
    )
    idx = diff_index(spaced)["s.py"]
    assert resolve_snippet("alpha\nbeta", idx) == (UNMATCHED, None)
    assert resolve_snippet("alpha", idx) == (AMBIGUOUS, None)   # genuinely removed


def test_blank_and_non_string_snippets_are_invalid():
    idx = _index()
    for bad in ("", "   ", "\n\n", ["first = items[0]"], {"a": 1}, 5, True):
        assert resolve_snippet(bad, idx) == (INVALID, None), bad


# -- comment-level wiring ------------------------------------------------------


def test_resolution_overrides_a_wrong_declared_line_and_counts_it():
    out, stats = resolve_review_comments(
        [{"file": "m.py", "line": 99, "anchor_snippet": "second = rows[1]",
          "comment": "x"}], DIFF)
    assert out[0]["line"] == 3
    assert stats[RESOLVED] == 1 and stats["disagreed"] == 1
    assert "_anchor_unverified" not in out[0]


def test_agreeing_declared_line_is_not_counted_as_disagreement():
    out, stats = resolve_review_comments(
        [{"file": "m.py", "line": 2, "anchor_snippet": "first = items[0]",
          "comment": "x"}], DIFF)
    assert out[0]["line"] == 2 and stats["disagreed"] == 0


def test_no_snippet_is_left_exactly_as_it_was():
    original = {"file": "m.py", "line": 2, "comment": "x", "severity": "nit"}
    out, stats = resolve_review_comments([dict(original)], DIFF)
    assert out[0] == original
    assert stats["no_snippet"] == 1 and stats[RESOLVED] == 0


def test_unresolvable_snippet_marks_the_comment_unverified():
    out, stats = resolve_review_comments(
        [{"file": "m.py", "line": 2, "anchor_snippet": "not in the diff",
          "comment": "x"}], DIFF)
    assert out[0]["_anchor_unverified"] is True
    # the declared line is moved OUT of `line`: the run report renders `file:line`, and
    # showing an uncorroborated position as authoritative is what resolving before
    # rendering exists to prevent. Kept under a private key for diagnostics.
    assert "line" not in out[0] and out[0]["_declared_line"] == 2
    assert stats[UNMATCHED] == 1


def test_snippet_for_a_file_outside_the_diff_is_unverified():
    out, stats = resolve_review_comments(
        [{"file": "elsewhere.py", "line": 1, "anchor_snippet": "x", "comment": "c"}],
        DIFF)
    assert out[0]["_anchor_unverified"] is True and stats[UNMATCHED] == 1


# -- the fail-closed boundary --------------------------------------------------


def test_unverified_comment_is_demoted_even_when_its_line_is_addressable():
    """The case the whole rule exists for, and the one a resolver-only test cannot
    reach: line 2 IS addressable, so without the flag this would publish an anchor we
    had just failed to corroborate."""
    resolved, _ = resolve_review_comments(
        [{"file": "m.py", "line": 2, "anchor_snippet": "quotes nothing real",
          "severity": "major", "comment": "x"}], DIFF)
    inline, downgraded = _partition_comments(resolved, DIFF)
    assert inline == [] and len(downgraded) == 1
    assert "could not be corroborated" in downgraded[0]["_why"]


def test_resolved_comment_reaches_the_inline_path():
    resolved, _ = resolve_review_comments(
        [{"file": "m.py", "line": 99, "anchor_snippet": "second = rows[1]",
          "severity": "major", "comment": "x"}], DIFF)
    inline, downgraded = _partition_comments(resolved, DIFF)
    assert downgraded == [] and len(inline) == 1
    assert inline[0]["line"] == 3 and inline[0]["side"] == "RIGHT"


def test_the_internal_flag_never_leaks_into_a_published_payload():
    resolved, _ = resolve_review_comments(
        [{"file": "m.py", "line": 2, "anchor_snippet": "bogus", "comment": "x"}], DIFF)
    _, downgraded = _partition_comments(resolved, DIFF)
    assert "_anchor_unverified" not in downgraded[0]


def test_deletions_separated_by_a_blank_context_line_stay_apart():
    """Dropping blank lines when matching would make these adjacent and fabricate a
    multi-line 'removed' match. Interior blanks are kept for exactly this reason."""
    spaced = (
        "diff --git a/i.py b/i.py\n--- a/i.py\n+++ b/i.py\n"
        "@@ -1,4 +1,2 @@\n-alpha\n \n-beta\n tail\n"
    )
    assert resolve_snippet("alpha\nbeta", diff_index(spaced)["i.py"]) == (UNMATCHED, None)


def test_a_minus_marked_snippet_is_not_relocated_onto_added_code():
    """Stripping `-` alongside `+` looked symmetric and was a hole: `-x = 1` would
    strip to `x = 1` and resolve onto an ADDED line, turning a quote of removed code
    into a verified right-side anchor."""
    d = ("diff --git a/f.py b/f.py\n--- a/f.py\n+++ b/f.py\n"
         "@@ -1,1 +1,2 @@\n keep\n+x = 1\n")
    assert resolve_snippet("-x = 1", diff_index(d)["f.py"]) == (UNMATCHED, None)
    assert resolve_snippet("+x = 1", diff_index(d)["f.py"]) == (RESOLVED, 2)


def test_a_source_line_that_really_starts_with_a_dash_still_matches():
    """A YAML item or negative literal must not be mistaken for a diff marker."""
    d = ("diff --git a/c.yaml b/c.yaml\n--- a/c.yaml\n+++ b/c.yaml\n"
         "@@ -1,1 +1,2 @@\n items:\n+- alpha\n")
    assert resolve_snippet("- alpha", diff_index(d)["c.yaml"]) == (RESOLVED, 2)


def test_a_clipped_file_refuses_snippet_resolution_entirely():
    """Detecting a clipped file is worth nothing if we then derive from it: the
    deletion guard can only report what the old side CONTAINS, so on a short index its
    silence proves nothing. Here the missing deletion is identical to the surviving
    context line, which is exactly how a fabricated anchor would slip through."""
    clipped = ("diff --git a/g.py b/g.py\n--- a/g.py\n+++ b/g.py\n"
               "@@ -1,3 +1,1 @@\n dup = 1\n")     # old declares 3, one line arrives
    idx = diff_index(clipped)["g.py"]
    assert idx.state == "incomplete"
    assert resolve_snippet("dup = 1", idx) == (AMBIGUOUS, None)

    resolved, _ = resolve_review_comments(
        [{"file": "g.py", "line": 1, "anchor_snippet": "dup = 1",
          "severity": "major", "comment": "x"}], clipped)
    inline, downgraded = _partition_comments(resolved, clipped)
    assert inline == [] and len(downgraded) == 1


def test_absent_file_also_clears_the_uncorroborated_line():
    """Every unresolved path goes through the same exit; this branch used to return
    early and leave `elsewhere.py:1` rendering as though it were authoritative."""
    out, _ = resolve_review_comments(
        [{"file": "elsewhere.py", "line": 1, "anchor_snippet": "x", "comment": "c"}],
        DIFF)
    assert "line" not in out[0] and out[0]["_declared_line"] == 1


def test_trailing_whitespace_only_edit_resolves_the_added_form():
    """`-value = 1` / `+value = 1  ` differ ONLY in trailing space. Normalizing before
    trying the literal text makes both sides identical, so the verbatim added snippet
    reads as quoting removed code. The exact pass runs first and wins outright — later,
    looser passes are never consulted once one resolves."""
    d = ("diff --git a/w.py b/w.py\n--- a/w.py\n+++ b/w.py\n"
         "@@ -1,1 +1,1 @@\n-value = 1\n+value = 1  \n")
    idx = diff_index(d)["w.py"]
    assert resolve_snippet("value = 1  ", idx) == (RESOLVED, 1)
    assert resolve_snippet("value = 1", idx) == (AMBIGUOUS, None)   # the removed form


def test_marker_plus_trailing_whitespace_still_resolves_the_added_line():
    """Both corrections at once. The snippet carries its `+` AND the edit is
    trailing-whitespace-only, so the exact pass cannot match while the marker is
    present. Sending the unmarked form straight to the loose pass reopened the hole one
    level down — it matched the deletion. Each form now tries exact before loose."""
    d = ("diff --git a/w.py b/w.py\n--- a/w.py\n+++ b/w.py\n"
         "@@ -1,1 +1,1 @@\n-value = 1\n+value = 1  \n")
    idx = diff_index(d)["w.py"]
    assert resolve_snippet("+value = 1  ", idx) == (RESOLVED, 1)


def test_rival_readings_of_a_marked_snippet_are_ambiguous_not_first_wins():
    """`+value = 1` has two honest readings: the literal text (a source line that
    really does start with `+`) and the marker-stripped one. Both exist here, so
    picking either would be a guess."""
    d = ("diff --git a/p.py b/p.py\n--- a/p.py\n+++ b/p.py\n"
         "@@ -1,1 +1,3 @@\n"
         " +value = 1\n"      # 1: CONTEXT whose source literally begins with '+'
         "+value = 1\n"       # 2: an ADDED line reading `value = 1`
         "+tail\n")           # 3
    assert resolve_snippet("+value = 1", diff_index(d)["p.py"]) == (AMBIGUOUS, None)
