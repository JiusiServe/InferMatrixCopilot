"""The diff inventory must not blame findings for gaps in our own input.

`_right_side_diff_lines` used to discard each hunk's declared new-side count, so a
diff clipped mid-hunk produced a short addressable set and every finding past the cut
was demoted with "their file/line could not be mapped" — a statement about our input
dressed up as a statement about the reviewer's work.

(Lives in its own file rather than in `test_pr_steps.py` because these cover one
coherent behaviour; the publish tests there stay as the regression pin for demotion.)
"""

from infermatrix_copilot.engine.steps.pr.publish import (
    _fallback_section,
    _partition_comments,
    _right_side_diff_lines,
)

# declares 6 new-side lines, delivers 3 — clipped mid-hunk
CLIPPED_DIFF = (
    "diff --git a/m.py b/m.py\n"
    "--- a/m.py\n+++ b/m.py\n"
    "@@ -1,3 +1,6 @@\n"
    " ctx\n+one\n+two\n"
)
WHOLE_DIFF = (
    "diff --git a/w.py b/w.py\n"
    "--- a/w.py\n+++ b/w.py\n"
    "@@ -1,1 +1,2 @@\n"
    " ctx\n+added\n"
)


def test_inventory_flags_a_clipped_hunk():
    assert _right_side_diff_lines(CLIPPED_DIFF)["m.py"][1] == "incomplete"
    assert _right_side_diff_lines(WHOLE_DIFF)["w.py"][1] == "no_clipping_detected"


def test_absent_path_is_unknown_not_complete():
    """A missing key must never read as "this file was fine" — the over-claim a
    boolean would have forced."""
    assert "nowhere.py" not in _right_side_diff_lines(WHOLE_DIFF)


def test_hunk_without_an_explicit_count_is_one_line():
    """An omitted count means 1, per the unified-diff grammar — here on the old side.

    (The original fixture was `@@ -1 +1 @@` with a lone `+only`, which declares one
    old-side line that never arrives. It passed only because the parser checked the new
    side alone; once the old side is validated too, that fixture is correctly flagged
    incomplete. Rewritten well-formed so it still tests what it was written to test.)
    """
    diff = ("diff --git a/s.py b/s.py\n--- a/s.py\n+++ b/s.py\n"
            "@@ -1 +1,2 @@\n ctx\n+only\n")
    lines, state = _right_side_diff_lines(diff)["s.py"]
    assert sorted(lines) == [1, 2] and state == "no_clipping_detected"


def test_clipping_that_balances_on_the_new_side_is_still_caught():
    """A diff cut after the last right-side line but before trailing deletions balances
    on the new side. Checking only that side would report it intact while the
    removed-code index is short — and a snippet quoting one of the lost deletions could
    then resolve onto an identical earlier right-side line."""
    diff = ("diff --git a/g.py b/g.py\n--- a/g.py\n+++ b/g.py\n"
            "@@ -1,3 +1,1 @@\n dup = 1\n")   # old declares 3, one line arrives
    assert _right_side_diff_lines(diff)["g.py"][1] == "incomplete"


def test_clipped_diff_blames_the_diff_not_the_finding():
    inline, down = _partition_comments(
        [{"file": "m.py", "line": 99, "severity": "major", "comment": "boom"}],
        CLIPPED_DIFF)
    assert inline == [] and len(down) == 1
    body = _fallback_section(down)
    assert "clipped mid-hunk" in body
    assert "could not be mapped" not in body


def test_each_demotion_carries_its_own_reason():
    """One review, all three demotion classes at once — a single global reason
    string would misattribute two of them."""
    _, down = _partition_comments([
        {"file": "m.py", "line": 99, "severity": "major", "comment": "clipped file"},
        {"file": "gone.py", "line": 5, "severity": "minor", "comment": "absent file"},
        {"file": "w.py", "line": 500, "severity": "nit", "comment": "outside range"},
    ], CLIPPED_DIFF + WHOLE_DIFF)
    assert len(down) == 3
    body = _fallback_section(down)
    assert "clipped mid-hunk" in body
    assert "does not appear in the diff we fetched" in body
    assert "outside the changed lines" in body
    for text in ("clipped file", "absent file", "outside range"):
        assert text in body


def test_addressable_line_on_a_whole_diff_still_goes_inline():
    """The demotion guarantee is unchanged; only the reasons are new."""
    inline, down = _partition_comments(
        [{"file": "w.py", "line": 2, "severity": "major", "comment": "ok"}],
        WHOLE_DIFF)
    assert len(inline) == 1 and down == []
    assert inline[0]["line"] == 2 and inline[0]["side"] == "RIGHT"


def test_stale_head_still_uses_one_global_reason():
    """The head-changed case is the one where a single reason genuinely covers every
    finding; grouping must not regress it into three near-identical paragraphs."""
    body = _fallback_section(
        [{"file": "a.py", "line": 1, "comment": "x"},
         {"file": "b.py", "line": 2, "comment": "y"}],
        reason="The PR head changed after review (aaa → bbb).")
    assert body.count("The PR head changed") == 1
    assert "x" in body and "y" in body


def test_deleted_line_starting_with_dashes_is_not_a_right_side_line():
    """A deleted source line reading `--option` renders as `---option`. Treating that
    as a file header invents a RIGHT-side line number for content that does not exist
    there — an anchor GitHub rejects, taking the whole review submission with it —
    and inflates the observed count, masking real clipping."""
    diff = ("diff --git a/f.py b/f.py\n--- a/f.py\n+++ b/f.py\n"
            "@@ -1,2 +1,1 @@\n ctx\n---option\n")
    lines, state = _right_side_diff_lines(diff)["f.py"]
    assert sorted(lines) == [1], f"invented a right-side line: {sorted(lines)}"
    assert state == "no_clipping_detected"


def test_finding_without_a_usable_location_says_so():
    """Blaming a clipped diff for a finding that named no line is the opposite of
    the truth, so the malformed case is classified before the file-state cases."""
    _, down = _partition_comments(
        [{"file": "m.py", "line": None, "severity": "major", "comment": "no line"}],
        CLIPPED_DIFF)
    body = _fallback_section(down)
    assert "did not carry a usable file and line" in body
    assert "clipped mid-hunk" not in body


def test_fractional_and_boolean_lines_are_malformed_not_line_one():
    """int(1.9) and int(True) are both 1. Coercing them would post the finding at
    line 1 whenever line 1 is addressable — a wrong anchor, not a demotion."""
    for bad in (1.9, True, "1.9", "abc", None, [2]):
        _, down = _partition_comments(
            [{"file": "w.py", "line": bad, "severity": "major", "comment": "x"}],
            WHOLE_DIFF)
        assert len(down) == 1, f"{bad!r} was accepted as a location"
        assert "did not carry a usable file and line" in _fallback_section(down), bad


def test_a_genuine_integer_line_still_anchors():
    """The stricter check must not reject the normal case, including a digit string."""
    for good in (2, "2"):
        inline, down = _partition_comments(
            [{"file": "w.py", "line": good, "severity": "major", "comment": "x"}],
            WHOLE_DIFF)
        assert len(inline) == 1 and down == [], f"{good!r} was rejected"
        assert inline[0]["line"] == 2


def test_unicode_digit_line_does_not_crash_payload_construction():
    """`"²".isdigit()` is True but `int("²")` raises — an isdigit()-only guard would
    take down the whole review payload rather than demote one finding."""
    _, down = _partition_comments(
        [{"file": "w.py", "line": "²", "severity": "major", "comment": "x"}],
        WHOLE_DIFF)
    assert len(down) == 1
    assert "did not carry a usable file and line" in _fallback_section(down)


def test_absurdly_long_digit_string_does_not_abort_the_payload():
    """CPython caps int(str) at sys.get_int_max_str_digits() (4300), so an all-ASCII
    digit string can still refuse to convert — letting that escape would abort the
    whole review over one nonsense finding."""
    _, down = _partition_comments(
        [{"file": "w.py", "line": "1" * 5000, "severity": "major", "comment": "x"}],
        WHOLE_DIFF)
    assert len(down) == 1
    assert "did not carry a usable file and line" in _fallback_section(down)


# -- characterization: pins the CURRENT parser before it is refactored ---------
# The fixtures above are all single-hunk and only one uses two files, so on their
# own they do not pin enough of `_right_side_diff_lines` to prove a rewrite is
# behaviour-preserving. These do. They must keep passing UNTOUCHED afterwards.

MULTI_HUNK_DIFF = (
    "diff --git a/multi.py b/multi.py\n"
    "--- a/multi.py\n+++ b/multi.py\n"
    "@@ -1,2 +1,3 @@\n"
    " head\n+added_one\n ctx_one\n"          # right: 1,2,3
    "@@ -20,2 +21,3 @@\n"
    " tail\n+added_two\n ctx_two\n"          # right: 21,22,23
)
TWO_FILE_DIFF = MULTI_HUNK_DIFF + (
    "diff --git a/other.py b/other.py\n"
    "--- a/other.py\n+++ b/other.py\n"
    "@@ -5,1 +5,2 @@\n"
    " keep\n+fresh\n"                        # right: 5,6
)
BLANK_LINE_DIFF = (
    "diff --git a/blank.py b/blank.py\n"
    "--- a/blank.py\n+++ b/blank.py\n"
    "@@ -1,2 +1,4 @@\n"
    " a = 1\n"      # 1  context
    "+\n"           # 2  BLANK added
    " \n"           # 3  BLANK context
    "+b = 2\n"      # 4
)


def test_char_multi_hunk_line_numbers_restart_per_hunk():
    lines, state = _right_side_diff_lines(MULTI_HUNK_DIFF)["multi.py"]
    assert sorted(lines) == [1, 2, 3, 21, 22, 23]
    assert state == "no_clipping_detected"


def test_char_two_files_are_indexed_independently():
    idx = _right_side_diff_lines(TWO_FILE_DIFF)
    assert set(idx) == {"multi.py", "other.py"}
    assert sorted(idx["multi.py"][0]) == [1, 2, 3, 21, 22, 23]
    assert sorted(idx["other.py"][0]) == [5, 6]


def test_char_blank_added_and_context_lines_are_addressable():
    """Bare `+` and bare ` ` lines are real right-side lines; a parser that filters
    normalized blanks would silently shrink the addressable set and start demoting
    findings that are inline today."""
    lines, _ = _right_side_diff_lines(BLANK_LINE_DIFF)["blank.py"]
    assert sorted(lines) == [1, 2, 3, 4]


def test_char_finding_on_a_blank_added_line_goes_inline():
    inline, down = _partition_comments(
        [{"file": "blank.py", "line": 2, "severity": "nit", "comment": "trailing blank"}],
        BLANK_LINE_DIFF)
    assert len(inline) == 1 and down == []


def test_char_one_clipped_hunk_marks_the_whole_file():
    clipped = (
        "diff --git a/m.py b/m.py\n--- a/m.py\n+++ b/m.py\n"
        "@@ -1,1 +1,2 @@\n ok\n+fine\n"       # balanced
        "@@ -9,1 +9,4 @@\n short\n"            # declares 4, delivers 1
    )
    lines, state = _right_side_diff_lines(clipped)["m.py"]
    assert sorted(lines) == [1, 2, 9]
    assert state == "incomplete"
