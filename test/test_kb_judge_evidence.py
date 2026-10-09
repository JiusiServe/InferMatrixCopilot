"""The L2 judge's evidence per rule: only the PRs it cites, with full upstream diffs."""

from __future__ import annotations

import json

from infermatrix_copilot.kb_service import evidence as ev
from infermatrix_copilot.kb_service.gate import changes_between, run_gate
from infermatrix_copilot.knowledge_service.facts import FactsError
from infermatrix_copilot.knowledge_service.ops import KnowledgeOperation as Op, apply_operations
from test_kb_intake_gate import JUDGE, PAGE, ScriptedGateway, _judge_all, _rule, _tree


def _pr(n, files, sha="m" * 40):
    return {"source_reference": f"PR #{n}", "title": f"pr {n}", "merged_at": "2026-09-29T00:00:00Z",
            "merge_commit_sha": sha, "changed_files": files, "diff_excerpt": "--- cut short"}


class Mirror:
    def __init__(self, diffs, *, down=False):
        self.diffs, self.down, self.asked = diffs, down, []

    def pr_diff(self, number, sha, path):
        if self.down:
            raise FactsError("mirror unreadable")
        self.asked.append(path)
        return self.diffs.get(path, "")

    def pull(self, number):
        return {"merged": True, "merge_commit_sha": "p" * 40}


EVIDENCE = [_pr(10, ["docs/a.md", "pkg/serving_speech.py", "tests/test_x.py"]), _pr(11, ["pkg/other.py"]),
            {"source_reference": "run r1", "title": "a lesson"}]


def test_only_the_cited_prs_are_shown_or_everything_when_none_is_held():
    assert [e["source_reference"] for e in ev.for_rule("x ^[PR #11]", EVIDENCE, None)] == ["PR #11"]
    assert ev.for_rule("x ^[PR #99]", EVIDENCE, None) == EVIDENCE


def test_full_diffs_replace_the_excerpt_named_files_first():
    mirror = Mirror({"docs/a.md": "+doc\n", "pkg/serving_speech.py": "+handler\n", "tests/test_x.py": "+test\n"})
    (item,) = ev.for_rule("见 `serving_speech.py::delete_voice` ^[PR #10]", EVIDENCE, mirror)
    assert "diff_excerpt" not in item and list(item["diffs"]) == ["pkg/serving_speech.py", "tests/test_x.py",
                                                                  "docs/a.md"]
    assert item["diffs"]["pkg/serving_speech.py"] == "+handler\n" and item["diffs_omitted"] == []


def test_the_byte_limits_hold_and_say_so(monkeypatch):
    monkeypatch.setattr(ev, "PER_FILE", 10)
    monkeypatch.setattr(ev, "PER_RULE", 15)
    mirror = Mirror({"docs/a.md": "x" * 50, "pkg/serving_speech.py": "y" * 5, "tests/test_x.py": "z" * 50})
    (item,) = ev.for_rule("`pkg/serving_speech.py` ^[PR #10]", EVIDENCE, mirror)
    assert item["diffs"]["pkg/serving_speech.py"] == "y" * 5
    assert item["diffs"]["tests/test_x.py"].startswith("z" * 10) and "cut at 10 bytes of 50" in item["diffs"]["tests/test_x.py"]
    assert item["diffs_omitted"] == ["docs/a.md"]


def test_source_comes_before_tests_and_docs_when_the_rule_names_no_file():
    files = ["docs/guide.md", "tests/test_a.py", "pkg/deploy/x.yaml", "pkg/adapter.py"]
    mirror = Mirror({f: "+\n" for f in files})
    (item,) = ev.for_rule("^[PR #10]", [_pr(10, files)], mirror)
    assert list(item["diffs"]) == ["pkg/adapter.py", "tests/test_a.py", "docs/guide.md", "pkg/deploy/x.yaml"]


def test_an_unreadable_mirror_keeps_the_recorded_excerpt():
    (item,) = ev.for_rule("^[PR #10]", EVIDENCE, Mirror({}, down=True))
    assert item == EVIDENCE[0]
    (item,) = ev.for_rule("^[PR #10]", EVIDENCE, Mirror({}))                 # nothing to show: as recorded
    assert item == EVIDENCE[0]


def test_older_evidence_without_a_merge_sha_asks_for_it_and_lessons_are_untouched():
    old = {k: v for k, v in EVIDENCE[0].items() if k != "merge_commit_sha"}
    mirror = Mirror({"docs/a.md": "+doc\n"})
    (item,) = ev.for_rule("^[PR #10]", [old], mirror)
    assert item["diffs"] == {"docs/a.md": "+doc\n"}
    assert ev.for_rule("no citation", [EVIDENCE[2]], mirror) == [EVIDENCE[2]]


def test_each_rule_is_judged_on_its_own_evidence():
    base = _tree()
    head = {**base, **apply_operations(base, [Op("add", PAGE, "DEMO-2a", _rule("DEMO-2a", "PR #11"))],
                                       release="v1", today="2026-09-29").files}
    gateway = ScriptedGateway(_judge_all("yes"))
    decision = run_gate(base=base, head=head, changes=changes_between(base, head), external_texts={},
                        evidence=EVIDENCE, gateway=gateway, judge=JUDGE, release="v1", repo_dir="repos/demo",
                        evidence_for=lambda text, items: ev.for_rule(text, items, Mirror({"pkg/other.py": "+o\n"})))
    assert decision.status == "pass"
    prompts = [p for _r, p in gateway.calls if '"dimensions_to_answer"' in p]
    payload = json.loads(prompts[0].split("<untrusted_data>\n", 1)[1].rsplit("\n</untrusted_data>", 1)[0])
    assert [e["source_reference"] for e in payload["evidence"]] == ["PR #11"]
    assert payload["evidence"][0]["diffs"] == {"pkg/other.py": "+o\n"}


def test_recorded_pr_evidence_carries_its_merge_commit():
    from infermatrix_copilot.kb_service.sources import PullRequest

    pr = PullRequest(7, "t", "b", "2026-09-29", "c" * 40, "dev", ("a.py",), "diff")
    assert pr.evidence()["merge_commit_sha"] == "c" * 40



def test_feature_branch_merge_identity_survives_source_collection_and_drafting():
    from infermatrix_copilot.kb_service.intake import draft_prompt
    from infermatrix_copilot.kb_service.sources import GitHubReader

    def fetch(url):
        if "/files?" in url:
            return [{"filename": "pkg/feature.py", "patch": "+feature()"}]
        return {"number": 6926, "merge_commit_sha": "c" * 40,
                "base": {"ref": "xiaoyi_0.2.4.beta3"},
                "head": {"ref": "wiretrace", "sha": "d" * 40}}

    evidence = GitHubReader(fetch=fetch, token="").pull_request("org/demo", 6926).evidence()
    assert evidence["base_ref"] == "xiaoyi_0.2.4.beta3"
    assert evidence["head_ref"] == "wiretrace" and evidence["head_sha"] == "d" * 40
    prompt = draft_prompt("demo", evidence, _tree(), "repos/demo")
    recorded = json.loads(prompt.split("<untrusted_data>\n", 1)[1].split("\n</untrusted_data>", 1)[0])
    assert recorded == evidence


def _git(cwd, *args):
    import subprocess

    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout.strip()


def _commit(repo, path, text, message):
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@e", "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def test_a_rebase_merged_pr_shows_every_commit_not_only_the_last(tmp_path):
    from infermatrix_copilot.kb_service.upstream_facts import MirrorObserver

    up = tmp_path / "up"
    up.mkdir()
    _git(up, "init", "-q", "-b", "main")
    _commit(up, "README.md", "x\n", "base")
    _git(up, "checkout", "-q", "-b", "feature")
    _commit(up, "pkg/feature.py", "def feature():\n    return 1\n", "A: the behaviour")
    head = _commit(up, "tests/test_feature.py", "def test_feature():\n    pass\n", "B: its test")
    _git(up, "update-ref", "refs/pull/7/head", head)
    _git(up, "checkout", "-q", "main")
    _commit(up, "other.py", "y\n", "main moves on")
    _git(up, "-c", "user.name=t", "-c", "user.email=t@e", "cherry-pick", "feature~1", "feature")
    merged = _git(up, "rev-parse", "HEAD")                                   # the LAST rebased commit only
    observer = MirrorObserver(tmp_path / "mirror.git", "org/up", lambda n: {}, url=str(up))
    assert "def feature" in observer.pr_diff(7, merged, "pkg/feature.py")    # from commit A
    assert "def test_feature" in observer.pr_diff(7, merged, "tests/test_feature.py")
    assert observer.pr_diff(7, merged, "other.py") == ""                     # main's own change is not the PR's
    (item,) = ev.for_rule("^[PR #7]", [_pr(7, ["pkg/feature.py", "tests/test_feature.py"], sha=merged)], observer)
    assert list(item["diffs"]) == ["pkg/feature.py", "tests/test_feature.py"]


def test_a_pr_head_that_cannot_be_fetched_keeps_the_excerpt(tmp_path):
    from infermatrix_copilot.kb_service.upstream_facts import MirrorObserver

    up = tmp_path / "up"
    up.mkdir()
    _git(up, "init", "-q", "-b", "main")
    merged = _commit(up, "pkg/a.py", "a\n", "squashed (#8)")
    observer = MirrorObserver(tmp_path / "mirror.git", "org/up", lambda n: {}, url=str(up))
    (item,) = ev.for_rule("^[PR #8]", [_pr(8, ["pkg/a.py"], sha=merged)], observer)   # no refs/pull/8/head
    assert item["diff_excerpt"] == "--- cut short" and "diffs" not in item



def test_a_retirement_keeps_the_pr_that_justifies_it():
    retired = ("## DEMO-1a — old\n\n- 强制：旧规则。 ^[PR #10]\n\n"
               '<!-- kb:rule status=retired since=v0 retired_at=v1 reason=upstream-removed evidence="PR #11" -->\n')
    shown = [e["source_reference"] for e in ev.for_rule(retired, EVIDENCE, None)]
    assert shown == ["PR #10", "PR #11"]



def test_a_renamed_and_edited_file_keeps_its_removed_lines(tmp_path):
    from infermatrix_copilot.kb_service.upstream_facts import MirrorObserver

    up = tmp_path / "up"
    up.mkdir()
    _git(up, "init", "-q", "-b", "main")
    body = "".join(f"line {i}\n" for i in range(40))
    _commit(up, "pkg/old_name.py", body + "def removed_behaviour():\n    pass\n", "base")
    _git(up, "checkout", "-q", "-b", "feature")
    _git(up, "mv", "pkg/old_name.py", "pkg/new_name.py")
    head = _commit(up, "pkg/new_name.py", body, "rename, drop removed_behaviour")
    _git(up, "update-ref", "refs/pull/9/head", head)
    _git(up, "checkout", "-q", "main")
    _git(up, "-c", "user.name=t", "-c", "user.email=t@e", "merge", "-q", "--squash", "feature")
    merged = _commit(up, "pkg/new_name.py", body, "squash (#9)")
    observer = MirrorObserver(tmp_path / "mirror.git", "org/up", lambda n: {}, url=str(up))
    patch = observer.pr_diff(9, merged, "pkg/new_name.py")
    assert "rename from pkg/old_name.py" in patch and "-def removed_behaviour():" in patch
    assert "+line 0" not in patch                                            # not shown as all-new
    assert observer.pr_diff(9, merged, "pkg/old_name.py") == patch



def test_paths_with_spaces_and_non_ascii_names_are_found(tmp_path):
    from infermatrix_copilot.kb_service.upstream_facts import MirrorObserver

    up = tmp_path / "up"
    up.mkdir()
    _git(up, "init", "-q", "-b", "main")
    _commit(up, "README.md", "x\n", "base")
    _git(up, "checkout", "-q", "-b", "feature")
    _commit(up, "docs/my guide.md", "spaced\n", "a spaced name")
    head = _commit(up, "docs/说明.md", "非 ASCII\n", "a non-ASCII name")
    _git(up, "update-ref", "refs/pull/5/head", head)
    _git(up, "checkout", "-q", "main")
    _git(up, "-c", "user.name=t", "-c", "user.email=t@e", "merge", "-q", "--squash", "feature")
    _git(up, "-c", "user.name=t", "-c", "user.email=t@e", "commit", "-q", "-m", "squash (#5)")
    merged = _git(up, "rev-parse", "HEAD")
    observer = MirrorObserver(tmp_path / "mirror.git", "org/up", lambda n: {}, url=str(up))
    assert "+spaced" in observer.pr_diff(5, merged, "docs/my guide.md")
    assert "+非 ASCII" in observer.pr_diff(5, merged, "docs/说明.md")
    assert observer.pr_diff(5, merged, "README.md") == ""                   # not the PR's
