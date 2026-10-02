"""Per-rule proof stays pinned, bounded, and distinguishable from test runs."""

import hashlib

from infermatrix_copilot.kb_service import evidence as ev
from infermatrix_copilot.knowledge_service.facts import FactsError
from test_kb_judge_evidence import _pr

SHA = "a" * 40


class Source:
    def __init__(self, files):
        self.files, self.reads = files, []

    def file_text(self, sha, path):
        assert sha == SHA
        self.reads.append((sha, path))
        value = self.files.get(path)
        if isinstance(value, Exception):
            raise value
        return value

    def pr_diff(self, *args):
        raise AssertionError("prepared owner diffs must not be fetched again")

    def head(self):
        raise AssertionError("source fragments must not read branch HEAD")


def _prepared(paths):
    return {**_pr(10, paths, sha=SHA), "diffs": {p: "+ truncated upstream definition\n" for p in paths}}


def test_named_definition_beyond_diff_limit_comes_from_exact_merged_source():
    path = "pkg/browser.py"
    prefix = "# context omitted from the per-file diff\n" * 1000
    definition = "def update_decision(config):\n    config['mode'] = 'llm'\n    return config\n"
    source = Source({path: prefix + definition})
    item = _prepared([path])
    item["diffs"][path] = prefix + "+def update_decision(config):\n"
    (shown,) = ev.for_rule(f"`{path}::update_decision` ^[PR #10]", [item], source)
    assert "cut at" in shown["diffs"][path]
    (fragment,) = shown["source_fragments"]
    assert fragment["content"] == definition and fragment["status"] == "complete"
    assert fragment["sha"] == SHA and fragment["start_line"] == 1001 and fragment["end_line"] == 1003
    assert fragment["content_sha256"] == hashlib.sha256(definition.encode()).hexdigest()
    assert source.reads == [(SHA, path)]


def test_named_tests_and_constants_are_definitions_without_claiming_test_execution():
    paths = ["pkg/worker.py", "tests/test_worker.py"]
    source = Source({paths[0]: "DEFAULT_LIMIT = 9000\nclass Worker:\n    def finish(self):\n        return DEFAULT_LIMIT\n",
                     paths[1]: "def test_finish():\n    assert Worker().finish() == 9000\n"})
    text = (f"`{paths[0]}::Worker.finish`、`DEFAULT_LIMIT`，验收时执行 "
            f"`{paths[1]}::test_finish`。 ^[PR #10]")
    (shown,) = ev.for_rule(text, [_prepared(paths)], source)
    fragments = shown["source_fragments"]
    assert any("DEFAULT_LIMIT = 9000" in f.get("content", "") for f in fragments)
    assert any("def finish" in f.get("content", "") for f in fragments)
    assert any("def test_finish" in f.get("content", "") for f in fragments)
    assert "not test executions" in shown["source_fragments_note"]
    assert all(f["sha"] == SHA for f in fragments)


def test_prepared_diffs_obey_cited_filter_and_byte_limit_without_an_observer(monkeypatch):
    monkeypatch.setattr(ev, "PER_FILE", 20)
    monkeypatch.setattr(ev, "PER_RULE", 4096)
    one, two = _prepared(["pkg/one.py"]), {**_pr(11, ["pkg/two.py"], sha=SHA),
                                         "diffs": {"pkg/two.py": "x" * 100}, "diff": "raw whole PR"}
    (shown,) = ev.for_rule("`pkg/two.py` ^[PR #11]", [one, two], None)
    assert shown["source_reference"] == "PR #11" and "diff" not in shown
    assert shown["diffs"]["pkg/two.py"].startswith("x" * 20)
    assert "cut at 20 bytes of 100" in shown["diffs"]["pkg/two.py"]


def test_missing_unavailable_and_truncated_source_are_explicit(monkeypatch):
    monkeypatch.setattr(ev, "PER_RULE", 4096)
    paths = ["pkg/missing.py", "pkg/down.py", "pkg/large.py"]
    source = Source({paths[1]: FactsError("pinned merge unavailable"),
                     paths[2]: "def finish():\n" + "    value = 'a long source line'\n" * 400})
    text = "、".join(f"`{p}::finish`" for p in paths) + " ^[PR #10]"
    (shown,) = ev.for_rule(text, [_prepared(paths)], source)
    fragments = shown["source_fragments"]
    assert [f["status"] for f in fragments] == ["missing", "unavailable", "truncated"]
    assert fragments[-1]["requested_end_line"] > fragments[-1]["end_line"]
    assert len(fragments[-1]["content"].encode()) <= ev.PER_RULE // 2
    assert all(sha == SHA for sha, _ in source.reads)


def test_source_definition_inside_a_string_is_not_proof():
    path = "pkg/removed.py"
    source = Source({path: 'DOC = """\ndef removed():\n    pass\n"""\n'})
    (shown,) = ev.for_rule(f"`{path}::removed` ^[PR #10]", [_prepared([path])], source)
    assert shown["source_fragments"] == [{"path": path, "sha": SHA, "status": "symbol_missing"}]


def test_nondeclarative_language_fragments_are_labelled_as_source_windows():
    path = "tests/settings.mjs"
    source = Source({path: "// setup\nconst DEFAULT_MODE = 'llm';\nassert.equal(DEFAULT_MODE, 'llm');\n"})
    (shown,) = ev.for_rule(f"`{path}`、`DEFAULT_MODE` ^[PR #10]", [_prepared([path])], source)
    assert shown["source_fragments"][0]["kind"] == "source_window"
    assert "assert.equal" in shown["source_fragments"][0]["content"]


def test_exhausted_budget_never_reinjects_the_next_complete_pr(monkeypatch):
    monkeypatch.setattr(ev, "PER_RULE", 4096)
    monkeypatch.setattr(ev, "PER_FILE", 4096)
    first, second = _prepared(["pkg/a.py"]), {**_pr(11, ["pkg/b.py"], sha=SHA),
                                            "diffs": {"pkg/b.py": "b" * 20000}}
    first["diffs"]["pkg/a.py"] = "a" * 20000
    shown = ev.for_rule("^[PR #10] ^[PR #11]", [first, second], None)
    assert shown[1]["diffs"] == {} and shown[1]["diffs_omitted"] == ["pkg/b.py"]
