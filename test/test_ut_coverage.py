"""#164: unit-test coverage candidates for new public functions.

The deterministic half only nominates; the reviewer judges. These tests pin
what gets nominated, what the reviewer is shown in each mode, and the
three-comment cap."""

import asyncio
import json
import subprocess

from infermatrix_copilot.ut_coverage import (
    MAX_COMMENTS,
    CoverageReport,
    PublicDef,
    UTCoverageRules,
    analyze,
    cap_gap_comments,
    new_public_defs,
    render,
)

RULES = UTCoverageRules(source_roots=("pkg/",), exclude=("*/__init__.py",))

DIFF = """\
diff --git a/pkg/sched.py b/pkg/sched.py
--- a/pkg/sched.py
+++ b/pkg/sched.py
@@ -10,3 +10,22 @@ class Scheduler:
     def existing(self):
         return 1

+    def admit(self, req):
+        def _inner():
+            return req
+        return _inner()
+
+    def _private(self):
+        return 0
+
+    def __repr__(self):
+        return "S"
+
+
+def plan_batch(items):
+    def helper(x):
+        return x
+    return [helper(i) for i in items]
+
+@overload
+def plan_batch_typed(items): ...
diff --git a/pkg/moved.py b/pkg/moved.py
--- a/pkg/moved.py
+++ b/pkg/moved.py
@@ -1,2 +1,2 @@
-def relocate(x):
+def relocate(x, y=0):
     return x
diff --git a/pkg/__init__.py b/pkg/__init__.py
--- a/pkg/__init__.py
+++ b/pkg/__init__.py
@@ -1 +1,3 @@
 import os
+def exported():
+    return os
diff --git a/tests/test_sched.py b/tests/test_sched.py
--- /dev/null
+++ b/tests/test_sched.py
@@ -0,0 +1,3 @@
+from pkg.sched import plan_batch
+def test_plan_batch():
+    assert plan_batch([1]) == [1]
"""


def test_only_new_public_source_defs_are_nominated():
    defs = {(d.qualname, d.line) for d in new_public_defs(DIFF, RULES)}
    # admit is a method (class named in the hunk header); plan_batch is a
    # module function. Skipped: the nested defs, private and dunder names,
    # the @overload stub, a def edited in place, __init__.py, and tests.
    assert defs == {("Scheduler.admit", 13), ("plan_batch", 25)}


def test_an_edit_to_one_class_does_not_hide_a_new_method_of_another():
    """Removal matching is by qualified name: changing Existing.forward's
    signature is an edit, but NewModel.forward in another file is new API."""
    diff = """\
diff --git a/pkg/old.py b/pkg/old.py
--- a/pkg/old.py
+++ b/pkg/old.py
@@ -3,2 +3,2 @@ class Existing:
-    def forward(self, x):
+    def forward(self, x, y=None):
         return x
diff --git a/pkg/new.py b/pkg/new.py
--- /dev/null
+++ b/pkg/new.py
@@ -0,0 +1,3 @@
+class NewModel:
+    def forward(self, x):
+        return x
"""
    defs = [(d.qualname, d.path, d.line) for d in new_public_defs(diff, RULES)]
    assert defs == [("NewModel.forward", "pkg/new.py", 2)]


def test_a_sibling_of_the_hunk_header_method_is_not_nested():
    """The hunk header keeps its source indentation: under a header naming
    an existing method, a new method at the same indentation is a sibling."""
    diff = """\
diff --git a/pkg/svc.py b/pkg/svc.py
--- a/pkg/svc.py
+++ b/pkg/svc.py
@@ -20,2 +20,5 @@     def existing(self):
         return 1
+
+    def added(self):
+        return 2
"""
    assert [(d.name, d.line) for d in new_public_defs(diff, RULES)] == [
        ("added", 22)]


def test_a_function_moved_out_of_a_deleted_module_is_not_new():
    """A deleted file's removed defs count for move detection, so moving
    `move()` out of a module the PR deletes nominates nothing."""
    diff = """\
diff --git a/pkg/old.py b/pkg/old.py
deleted file mode 100644
--- a/pkg/old.py
+++ /dev/null
@@ -1,2 +0,0 @@
-def move(x):
-    return x
diff --git a/pkg/new.py b/pkg/new.py
--- a/pkg/new.py
+++ b/pkg/new.py
@@ -1 +1,4 @@
 import os
+
+def move(x):
+    return x
"""
    assert new_public_defs(diff, RULES) == []


def test_a_test_in_the_diff_covers_its_function():
    report = analyze(DIFF, RULES)
    assert [d.qualname for d in report.candidates] == ["Scheduler.admit"]
    assert report.referenced == {"plan_batch": ["tests/test_sched.py"]}
    assert report.searched_tree is False


def test_a_test_already_in_the_tree_covers_its_function(tmp_path):
    repo = tmp_path / "repo"
    (repo / "tests").mkdir(parents=True)
    (repo / "tests" / "test_admit.py").write_text("s.admit(r)\n")
    (repo / "pkg").mkdir()
    (repo / "pkg" / "sched.py").write_text("def admit(): pass\n")
    for cmd in (["git", "init", "-q"], ["git", "add", "-A"]):
        subprocess.run(cmd, cwd=repo, check=True)
    report = analyze(DIFF, RULES, str(repo))
    assert report.candidates == []
    # the defining source file never counts as a test reference
    assert report.referenced["Scheduler.admit"] == ["tests/test_admit.py"]


def test_rules_come_from_the_adapter_and_can_switch_the_check_off():
    assert UTCoverageRules.from_manifest(None) == UTCoverageRules()
    assert UTCoverageRules.from_manifest(
        {"ut_coverage": {"enabled": False}}) is None
    assert UTCoverageRules.from_manifest(
        {"repo": {"language": "rust"}}) is None
    rules = UTCoverageRules.from_manifest(
        {"ut_coverage": {"source_roots": ["src/"], "test_globs": ["t/*"]}})
    assert rules.is_source("src/a.py") and not rules.is_source("lib/a.py")
    assert rules.is_test("t/a.py") and not rules.is_source("t/a.py")


def test_render_lists_candidates_with_the_judgement_rules():
    assert render(CoverageReport()) == ""
    text = render(analyze(DIFF, RULES))
    assert "pkg/sched.py:13 `Scheduler.admit`" in text
    assert "indirectly" in text and "trivial" in text
    assert f"At most {MAX_COMMENTS}" in text


def test_only_three_gap_comments_publish_and_the_rest_are_named():
    report = CoverageReport(candidates=[
        PublicDef("pkg/m.py", n, f"f{n}") for n in range(1, 6)])
    other = {"file": "pkg/m.py", "line": 99, "comment": "real bug"}
    gaps = [{"file": "m.py" if n == 1 else "pkg/m.py", "line": n,
             "kind": "untested_api", "comment": f"test f{n}"}
            for n in range(1, 6)]
    kept, dropped = cap_gap_comments([other, *gaps], report)
    assert [c["comment"] for c in kept] == ["real bug", "test f1", "test f2",
                                            "test f3"]
    assert dropped == ["f4", "f5"]
    assert all("kind" not in c for c in kept)
    assert cap_gap_comments([other], None) == ([other], [])


def test_a_correctness_finding_on_a_candidate_def_is_never_capped():
    """Only the explicit `untested_api` classification is capped: a blocker
    anchored on the same def line survives three gap comments before it."""
    report = CoverageReport(candidates=[
        PublicDef("pkg/m.py", n, f"f{n}") for n in range(1, 5)])
    gaps = [{"file": "pkg/m.py", "line": n, "kind": "untested_api",
             "severity": "minor", "comment": f"test f{n}"} for n in range(1, 4)]
    blocker = {"file": "pkg/m.py", "line": 4, "severity": "blocker",
               "comment": "mutable default argument is shared across calls"}
    kept, dropped = cap_gap_comments([*gaps, blocker], report)
    assert blocker in kept and dropped == []


def test_direct_plan_carries_candidates_only_when_given_a_diff():
    from infermatrix_copilot.direct_routing import direct_review_plan

    diff = DIFF.replace("pkg/", "vllm_omni/")
    plan = direct_review_plan("vllm-omni", changed_files=["vllm_omni/sched.py"],
                              diff=diff)
    block = plan["untested_public_api"]
    assert block["status"] == "ok"
    assert [c["name"] for c in block["candidates"]] == ["Scheduler.admit"]
    assert block["searched_tree"] is False and block["instructions"]
    assert any("untested_public_api" in item
               for item in plan["first_review_checklist"])
    assert direct_review_plan("vllm-omni")["untested_public_api"] == {
        "status": "no_diff"}


def test_sdk_request_diff_reaches_the_typed_plan():
    from infermatrix_copilot.sdk.v1 import (
        ChangedPath, DirectClient, DirectReviewRequest, RepositoryRef)

    request = DirectReviewRequest(
        review_id="attempt-1", repository=RepositoryRef(alias="vllm-omni"),
        pr_number=7, expected_head_sha="a" * 40, title="t", body="b",
        changed_paths=(ChangedPath("vllm_omni/sched.py", "modified"),),
        diff=DIFF.replace("pkg/", "vllm_omni/"))
    plan = DirectClient().plan(request)
    assert plan.untested_public_api["candidates"][0]["name"] == "Scheduler.admit"
    assert plan.to_dict()["untested_public_api"]["status"] == "ok"


def test_strict_reviewer_sees_candidates_and_the_cap_holds(settings, trace,
                                                            tmp_path, git_repo):
    from infermatrix_copilot.engine.registry import StepRegistry
    from infermatrix_copilot.engine.step import StepContext
    from infermatrix_copilot.engine.steps import register_builtin_steps
    from infermatrix_copilot.llm import Block, Reply

    diff = "".join(
        f"diff --git a/pkg/m{n}.py b/pkg/m{n}.py\n--- a/pkg/m{n}.py\n"
        f"+++ b/pkg/m{n}.py\n@@ -0,0 +1,2 @@\n+def build_{n}(x):\n+    return x\n"
        for n in range(5))
    comments = [{"file": f"pkg/m{n}.py", "line": 1, "severity": "minor",
                 "comment": f"build_{n} has no unit test", "evidence": "e",
                 "disposition": "publish", "kind": "untested_api"}
                for n in range(5)]

    class LLM:
        available = True

        def __init__(self):
            self.calls = []

        def create(self, *, system, messages, **_kw):
            self.calls.append(messages[0]["content"])
            return Reply(blocks=[Block(type="text", text=json.dumps({
                "status": "success", "summary": "reviewed", "findings": [],
                "files_read": [], "files_modified": [], "tests_requested": [],
                "tests_run": [], "assumptions": [], "blockers": [],
                "confidence": "high", "failure_kind": None,
                "next_action": "post", "review_comments": comments}))])

    settings.review_ensemble = False
    llm = LLM()
    state = {"diff_text": diff, "task_spec": {"pr": 9},
             "repo_path": str(git_repo)}
    handler = register_builtin_steps(StepRegistry()).get("agent.review_diff")
    result = asyncio.run(handler.handler(StepContext(
        settings=settings, state=state, params={}, run_dir=tmp_path / "run",
        trace=trace, llm=llm)))
    assert result.ok, result.summary
    assert "NEW PUBLIC FUNCTIONS WITH NO TEST REFERENCE" in llm.calls[0]
    assert "pkg/m0.py:1 `build_0`" in llm.calls[0]
    published = result.outputs["state_updates"]["review_comments"]
    assert len([c for c in published if "no unit test" in c["comment"]]) == 3
    assert all("kind" not in c for c in published)
    assert "Also without a unit test: `build_3`, `build_4`." in \
        result.outputs["state_updates"]["review_summary"]
