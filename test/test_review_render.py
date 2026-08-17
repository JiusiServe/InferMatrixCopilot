

# -- render defects measured on the v17 arms (pr4893 forensics) --------------

def test_overflow_anchor_uses_the_declared_line_fallback():
    """`c.get('line', default)` returns None when the key EXISTS and holds
    None -- which is exactly what anchor resolution does when the diff index
    cannot corroborate a position. 25 of 26 measured artifacts carried a
    `?:NNN`-shaped anchor from that path."""
    from infermatrix_copilot.engine.steps.review.utils import _render_review_md
    out = {"review_comments": [],
           "_review_overflow": [{"file": "a/b.py", "line": None,
                                 "_declared_line": 882, "severity": "minor",
                                 "comment": "residual concern"}]}
    md = _render_review_md(out)
    assert "`a/b.py:~882`" in md
    assert "?:882" not in md and "None" not in md


def test_overflow_is_not_cut_mid_sentence():
    """The appendix is where ground-truth matches land once the budget is
    full; a half-sentence was scored as a non-finding on pr4893."""
    from infermatrix_copilot.engine.steps.review.utils import _render_review_md
    body = ("The assertions only validate the fake rather than production. "
            "A spy on init_vllm_model_parallel_group would prove the real "
            "wiring instead. " + "Filler detail. " * 60)
    md = _render_review_md({"review_comments": [],
                            "_review_overflow": [{"file": "t.py", "line": 3,
                                                  "severity": "minor",
                                                  "comment": body}]})
    kept = md.split("`t.py:3` [minor] ")[1]
    assert "only validate the fake rather than production." in kept
    assert not kept.strip().endswith("Filler")
    assert len(kept) > 320   # the old ceiling truncated the claim itself


def test_near_duplicate_findings_are_dropped():
    from infermatrix_copilot.engine.steps.review.utils import _render_review_md
    c = lambda t: {"file": "m.py", "line": 5, "severity": "major", "comment": t}
    md = _render_review_md({"review_comments": [
        c("The cfg_parallel_size>1 guard was removed, so ranks diverge"),
        c("The cfg_parallel_size>1 guard was removed, so ranks diverge here"),
        c("A completely different concern about weight loading order"),
    ]})
    assert md.count("cfg_parallel_size>1 guard was removed") == 1
    assert "weight loading order" in md


def test_unparseable_python_suggestion_is_not_shipped_as_a_patch():
    """A wrong claim welded to an applyable diff is refutable in a way a
    hedged one is not -- judges refuted two of ours on pr4893."""
    from infermatrix_copilot.engine.steps.review.utils import _render_review_md
    bad = _render_review_md({"review_comments": [
        {"file": "t.py", "line": 1, "severity": "major", "comment": "fix",
         "suggestion": "mocker.patch.object(x) as dp_md"}]})
    assert "```suggestion" not in bad
    assert "not a ready patch" in bad
    good = _render_review_md({"review_comments": [
        {"file": "t.py", "line": 1, "severity": "major", "comment": "fix",
         "suggestion": "if base is None:\n    return None"}]})
    assert "```suggestion" in good
    # an indented fragment is still a real patch, not a syntax error
    frag = _render_review_md({"review_comments": [
        {"file": "t.py", "line": 1, "severity": "major", "comment": "fix",
         "suggestion": "    return _error_response(err, status_code=404)"}]})
    assert "```suggestion" in frag
