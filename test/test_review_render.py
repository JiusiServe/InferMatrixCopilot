

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


# -- v19 signal-density defects (measured on the v17 Composer/DeepSeek arms) --
# Every judge rationale on the losing items named the same three faults:
# near-duplicate restatements, a ledger that buries the real finding, and
# broken `?:NN` locations. Each test below pins one of them.

_TRC = [
    "[resolved] trust_remote_code kwarg - dropped at head for kernels 0.13.x "
    "compat per commit message; residual checked: PR description not updated",
    "[resolved] trust_remote_code claim - commit 9947f414 dropped kwargs; "
    "flash_attn_hub.py:34-35 calls get_kernel(repo_id, version=version)",
    "[resolved] PR-body trust_remote_code claim - dropped at 9947f414; head "
    "calls get_kernel(repo_id, version=version) with no trust_remote_code",
    "[resolved] trust_remote_code kwarg concern - removed at 9947f414 for "
    "kernels 0.13.x compat; residual: PR description still advertises it",
]


def test_ledger_collapses_restatements_that_cite_different_evidence():
    """The shipped 90-char prefix key was inert: replayed over twenty measured
    artifacts it removed 0 of 138 and 0 of 136 entries, because each lens
    opens its restatement with whichever evidence it happened to cite."""
    from infermatrix_copilot.engine.steps.review.utils import _render_review_md
    md = _render_review_md({"review_comments": [], "findings": list(_TRC)})
    assert md.count("[resolved]") == 1


def test_ledger_is_capped_below_the_quota_it_used_to_fill():
    """14 saturated on 9 of 10 items in both arms - a cap always hit is a
    quota being filled, not a ceiling protecting the reader."""
    from infermatrix_copilot.engine.steps.review.utils import _render_review_md
    findings = [f"[claim-verified] symbol_{i}_check in mod_{i}.py holds "
                f"under the new branch_{i}_path" for i in range(20)]
    md = _render_review_md({"review_comments": [], "findings": findings})
    assert md.count("[claim-verified]") == 6


def test_duplicate_findings_merge_across_differing_anchors():
    """The commonest duplicate class anchored the SAME fact differently, so a
    within-a-file rule never compared them: `?:34` and `flash_attn_hub.py:34`
    landed in different buckets. Replaying the shipped rule over ten measured
    artifacts removed 0 of 68 comments."""
    from infermatrix_copilot.engine.steps.review.utils import _render_review_md
    md = _render_review_md({"review_comments": [
        {"file": "", "line": 34, "severity": "minor",
         "comment": "PR Purpose still claims this adds trust_remote_code=True "
                    "for hub kernel loading, but head 9947f414 dropped it"},
        {"file": "flash_attn_hub.py", "line": 34, "severity": "minor",
         "comment": "PR description mismatch: body claims adding "
                    "trust_remote_code=True, but head 9947f414 dropped it "
                    "from _load_hub_module and calls get_kernel plainly"},
    ]})
    assert md.count("[minor]") == 1


def test_distinct_findings_about_one_file_are_not_merged():
    """The conjunctive rule exists for this case: identifiers alone merged
    pr4977's `:~81` ("add a cache test") into `:~58` ("that test sits on no CI
    path"), and the judge credited `:~58` by name. A false merge costs recall,
    so subject agreement alone must not be enough."""
    from infermatrix_copilot.engine.steps.review.utils import _render_review_md
    md = _render_review_md({"review_comments": [
        {"file": "tests/test_kernels_hub.py", "line": 81, "severity": "minor",
         "comment": "This diff caches hub kernels in _get_hub_module so each "
                    "repo loads once per process; existing tests construct "
                    "one FlashAttentionHubImpl and would miss a reload "
                    "regression. Add a core_model cpu test asserting one call."},
        {"file": "tests/test_kernels_hub.py", "line": 58, "severity": "minor",
         "comment": "test_kernels_hub_execution is the only test constructing "
                    "FlashAttentionHubImpl and it is on no Buildkite pytest "
                    "path: the cuda glob excludes the attention subdirectory "
                    "and the cpu lane deselects it for want of a marker."},
    ]})
    assert md.count("[minor]") == 2


def test_findings_with_no_file_do_not_invent_a_broken_reference():
    """"two of its findings cite broken locations ('?:102', '?:33') instead of
    real file paths, hurting both precision and actionability" - and those
    findings were about the PR's own prose, which has no file:line at all."""
    from infermatrix_copilot.engine.steps.review.utils import _render_review_md
    md = _render_review_md({"review_comments": [
        {"file": "", "line": 34, "severity": "minor",
         "comment": "The PR description still claims trust_remote_code=True"},
        {"file": None, "line": 7, "severity": "minor",
         "comment": "A concern the lens could not anchor to any file"},
    ]})
    assert "?:" not in md
    assert "`PR description`" in md and "`general`" in md


def test_promoted_residuals_are_deduped_against_each_other():
    """`covered` only held the pre-existing comments, so N resolved lines
    about one residual promoted N times - pr4977 shipped four near-identical
    PR-description-staleness comments, saturating the cap of 4."""
    import asyncio
    from types import SimpleNamespace
    from infermatrix_copilot.engine.steps.review.steps import (
        _promote_resolved_residuals)
    ctx = SimpleNamespace(trace=SimpleNamespace(record=lambda *a, **k: None))
    out = _promote_resolved_residuals(ctx, {"findings": list(_TRC),
                                            "review_comments": []})
    assert len(out["review_comments"]) == 1
    assert asyncio is not None  # keep the import honest for the linter


def test_skill_curation_queue_stays_out_of_the_deliverable():
    """Operator state about the copilot, not review of the PR - the same leak
    class the T3 forensics removed once, ~1000 chars on every measured item."""
    import inspect
    from infermatrix_copilot.engine.steps import report
    src = inspect.getsource(report)
    body = src.split("diag = [")[0]
    assert "skill candidates awaiting curation" not in body.split("cand_lines")[-1] \
        or "cand_lines" in body
    assert 'lines += [f"- task: {spec}"' not in src


def test_one_subject_named_by_path_and_by_basename_is_one_subject():
    """One lens writes `orchestrator.py`, another writes the full
    `vllm_omni/engine/orchestrator.py`. As raw strings those share nothing, so
    two comments on one subject scored zero topic overlap and both shipped --
    measured on the v19 val run, where the same CI-red question was asked
    twice at `orchestrator.py:1290`."""
    from infermatrix_copilot.engine.steps.review.utils import _render_review_md
    md = _render_review_md({"review_comments": [
        {"file": "vllm_omni/engine/orchestrator.py", "line": 1290,
         "severity": "nit",
         "comment": "Head shows buildkite vllm-omni-amd-ci and "
                    "vllm-omni-npu-ci failing; this diff only touches shared "
                    "orchestrator.py code with no amd or npu platform worker "
                    "changes. Can you confirm those reds are pre-existing?"},
        {"file": "vllm_omni/engine/orchestrator.py", "line": None,
         "_declared_line": 1290, "severity": "nit",
         "comment": "buildkite vllm-omni-amd-ci and vllm-omni-npu-ci are "
                    "failing at PR head per the gate report. This diff only "
                    "touches vllm_omni/engine/orchestrator.py with no amd or "
                    "npu platform changes, so are those reds pre-existing?"},
    ]})
    assert md.count("[nit]") == 1


def test_duplicate_findings_merge_to_the_richest_statement():
    """Dropping the tail of a duplicate cluster cost recall on both measured
    splits (train -.052 -> -.092, val -.003 -> -.122) while precision rose.
    Restatements differ in how precisely they state the causal mechanism, and
    that is what earns recall credit -- so the survivor is the richest one,
    not whichever arrived first."""
    from infermatrix_copilot.engine.steps.review.utils import _render_review_md
    thin = {"file": "hub.py", "line": 34, "severity": "minor",
            "comment": "The get_kernel call in flash_attn_hub.py dropped "
                       "trust_remote_code, so the PR description is stale."}
    rich = {"file": "hub.py", "line": 34, "severity": "minor",
            "comment": "The get_kernel call in flash_attn_hub.py dropped "
                       "trust_remote_code because kernels 0.13.x rejects the "
                       "kwarg, which would have made every version fallback "
                       "attempt fail on older installs; the PR description "
                       "still advertises it as added."}
    for order in ([thin, rich], [rich, thin]):
        md = _render_review_md({"review_comments": list(order)})
        assert md.count("[minor]") == 1, "duplicates must still collapse"
        assert "every version fallback" in md, "the richest survivor is kept"


def test_merging_never_demotes_a_blocker_to_its_chattier_twin():
    """Severity outranks richness: a wordier minor must not displace the
    blocker it restates."""
    from infermatrix_copilot.engine.steps.review.utils import _render_review_md
    md = _render_review_md({"review_comments": [
        {"file": "m.py", "line": 5, "severity": "blocker",
         "comment": "The cfg_parallel_size guard was removed so ranks diverge"},
        {"file": "m.py", "line": 5, "severity": "nit",
         "comment": "The cfg_parallel_size guard was removed so ranks diverge "
                    "and this is worth a longer look at some point later on"},
    ]})
    assert "[blocker]" in md and "[nit]" not in md


def test_finding_leads_with_the_concern_not_the_change():
    """The reducer contract puts the change the diff makes in the FIRST
    sentence, so a headline taken from it says nothing ("This diff adds a
    cache"). The concern is what a reader scans for -- and a finding they
    cannot pick out earns no credit for being present."""
    from infermatrix_copilot.engine.steps.review.utils import _split_claim
    head, rest = _split_claim(
        "This diff centralizes Hub loading into _get_hub_module so each "
        "repo_id loads once per process. No test exercises that path, so a "
        "per-layer reload regression would ship unnoticed. Add a cpu test.")
    assert head.startswith("No test exercises")
    assert "centralizes Hub loading" in rest


def test_evidence_renders_as_a_quote_not_a_parenthetical_tail():
    """Evidence ran past 500 chars appended inside `(evidence: ...)`, which is
    the measured "hard to find" complaint. It becomes a quote block."""
    from infermatrix_copilot.engine.steps.review.utils import _render_review_md
    md = _render_review_md({"review_comments": [
        {"file": "t.py", "line": 3, "severity": "major",
         "comment": "The guard was dropped. Ranks now diverge under DP>1.",
         "evidence": "t.py:3 `if dp > 1:`"}]})
    assert "(evidence:" not in md
    assert "> t.py:3" in md
    assert md.startswith("**Scan:**")
