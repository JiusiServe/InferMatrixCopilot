import subprocess

from infermatrix_copilot.llm import Block, Reply
from infermatrix_copilot.review.diff_summary import DiffSummary, build_diff_summary
from infermatrix_copilot.review.reviewer import run_patch_review
from infermatrix_copilot.review.triggers import evaluate_triggers


class FakeLLM:
    def __init__(self, text):
        self._text = text
        self.available = True

    def create(self, **kwargs):
        return Reply(blocks=[Block(type="text", text=self._text)])


def test_diff_summary_from_real_repo(git_repo, trace):
    (git_repo / "mod_a.py").write_text("A = 2\nAA = 3\n")
    (git_repo / "mod_b.py").write_text("B = 2\n")
    summary = build_diff_summary(git_repo, primary_files=("mod_a*",), trace=trace)
    assert sorted(summary.changed_files) == ["mod_a.py", "mod_b.py"]
    assert summary.out_of_scope_files == ["mod_b.py"]
    assert summary.total_lines > 0


def test_trigger_matrix(settings):
    clean = DiffSummary(changed_files=["a.py"], insertions=5, deletions=1,
                        tests_run=["pytest ok"])
    assert evaluate_triggers(clean, settings) == []

    risky = DiffSummary(
        changed_files=[f"f{i}.py" for i in range(12)],
        insertions=500, deletions=100,
        out_of_scope_files=["other.py"], full_file_writes=["f1.py"],
    )
    fired = evaluate_triggers(risky, settings, touched_modules=("scheduler",),
                              pre_push=True, knowledge_edit=True)
    assert set(fired) == {
        "out_of_scope_edits", "high_risk_modules", "large_diff",
        "tests_unavailable", "full_file_fallback", "before_push", "knowledge_edit",
    }


def test_reviewer_fail_closed_without_llm():
    v = run_patch_review(None, diff_text="d", summary=DiffSummary(), fired_rules=["before_push"])
    assert v.verdict == "unavailable" and not v.passing


def test_reviewer_parses_verdict():
    llm = FakeLLM('{"verdict": "block", "critiques": ["touches scheduler w/o tests"]}')
    v = run_patch_review(llm, diff_text="d", summary=DiffSummary(), fired_rules=["large_diff"])
    assert v.verdict == "block" and "scheduler" in v.critiques[0]

    llm = FakeLLM("garbage not json")
    v = run_patch_review(llm, diff_text="d", summary=DiffSummary(), fired_rules=[])
    assert v.verdict == "revise"  # unparseable -> conservative
