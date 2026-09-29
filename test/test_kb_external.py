"""Knowledge PRs the service did not open: the auto gate, findings, people."""

from __future__ import annotations

import subprocess
import uuid

from infermatrix_copilot.kb_service import merge
from infermatrix_copilot.kb_service.external import poll_external
from infermatrix_copilot.knowledge_service.signing import load_public_key, public_key_text, verify
from infermatrix_copilot.knowledge_service.ops import KnowledgeOperation as Op, apply_operations
from test_kb_flow import KnowledgeGitHub, _flow_runtime, _items
from test_kb_intake_gate import PAGE, _rule, _tree

REPO = "JiusiServe/InferMatrixCopilot"


def _git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout.strip()


class PullsGitHub(KnowledgeGitHub):
    def __init__(self):
        super().__init__()
        self.open: dict[int, dict] = {}

    def _answer(self, url):
        path = url.split("?", 1)[0]
        if path.endswith(f"/repos/{REPO}/pulls"):
            return list(self.open.values()) if "page=1" in url else []
        return super()._answer(url)


def _setup(tmp_path):
    rt, lifecycle = _flow_runtime(tmp_path)
    github = PullsGitHub()
    github.prs = rt.github.prs
    rt.github = github
    rt.lease_owner = rt.ledger.acquire_lease("scheduler")
    return rt, lifecycle, tmp_path / "origin"


def _open_human_pr(rt, origin, number, files: dict[str, str | None], *, labels=(), draft=False):
    _git(origin, "checkout", "-q", "-B", f"human-{number}", "main")
    for rel, text in files.items():
        target = origin / rel
        if text is None:
            target.unlink()
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
    _git(origin, "add", "-A")
    _git(origin, "-c", "user.name=h", "-c", "user.email=h@e", "commit", "-q", "--allow-empty",
         "-m", f"pr {number} {uuid.uuid4().hex}")      # a distinct head even for an identical tree
    head = _git(origin, "rev-parse", "HEAD")
    _git(origin, "update-ref", f"refs/pull/{number}/head", head)
    _git(origin, "checkout", "-q", "main")
    rt.github.open[number] = {"number": number, "draft": draft, "head": {"sha": head}, "title": "Add a rule",
                              "body": "from a person", "user": {"login": "dev"},
                              "labels": [{"name": name} for name in labels]}
    rt.github.prs[number] = {"state": "open", "merged": False, "head": {"sha": head}}
    return head


def _add_rule_files():
    base = _tree()
    return {f"knowledge/{rel}": text for rel, text in apply_operations(
        base, [Op("add", PAGE, "DEMO-2a", _rule("DEMO-2a", "PR #11"))], release="v1", today="2026-09-28").files.items()}


def _daily(rt):
    """One daily pass (forced: in real time a day passes between two)."""
    return poll_external(rt, force=True)


def _findings(tmp_path, number):
    return [item["body"]["comment"] for item in _items(tmp_path, "post_findings") if item["body"]["pr"] == number]


def _verdict(tmp_path, rt):
    envelope = _items(tmp_path, "merge")[-1]["body"]["verdict"]
    return verify("kb-gate-verdict", envelope, load_public_key(public_key_text(rt.outbox._key.public_key())))


def test_a_human_knowledge_pr_passes_the_auto_gate_and_gets_a_verdict(tmp_path):
    rt, lifecycle, origin = _setup(tmp_path)
    head = _open_human_pr(rt, origin, 7, _add_rule_files())
    (event,) = _daily(rt)
    assert "auto pr_open" in event
    (changeset,) = [cs for cs in rt.ledger.changesets("demo", ("pr_open",)) if cs["kind"] == "external"]
    assert changeset["pr_number"] == 7 and changeset["head_sha"] == head
    assert _daily(rt) == []                       # judged once per head
    assert merge.advance(rt, lifecycle) == [f"merge issued {changeset['id']}"]
    verdict = _verdict(tmp_path, rt)
    merge_base = _git(origin, "merge-base", "main", head)
    assert verdict["source"] == "auto" and verdict["pr"] == 7 and verdict["head_sha"] == head
    assert verdict["manifest"] == rt.knowledge.raw_manifest(merge_base, head)
    assert verdict["blocks"] and all(b["verdict"] == "pass" for b in verdict["blocks"])


def test_paths_outside_the_governed_pages_are_never_merged(tmp_path):
    rt, lifecycle, origin = _setup(tmp_path)
    _open_human_pr(rt, origin, 8, {"knowledge/tools/check.md": "tool notes\n"})
    (event,) = _daily(rt)
    assert event.endswith("to people")
    assert rt.ledger.human_queue("demo") == []            # the author is told, not people's queue
    findings = _findings(tmp_path, 8)[-1]
    assert "not passed" in findings and "knowledge/tools/check.md" in findings and "split" in findings
    assert "human-approved" not in findings
    rt.github.open[8]["labels"] = [{"name": "kb:human-approved"}]  # a label changes nothing any more
    (event,) = _daily(rt)                                 # not passed: checked again the next day
    assert event.endswith("to people")
    merge.advance(rt, lifecycle)
    assert not _items(tmp_path, "merge")
def test_a_pr_branched_before_main_changed_the_same_page_must_be_rebased(tmp_path):
    rt, lifecycle, origin = _setup(tmp_path)
    _open_human_pr(rt, origin, 10, _add_rule_files())
    page = origin / "knowledge" / PAGE
    page.write_text(page.read_text() + "\n<!-- main moved -->\n")
    _git(origin, "add", "-A")
    _git(origin, "-c", "user.name=t", "-c", "user.email=t@e", "commit", "-q", "-m", "main moves")
    (event,) = _daily(rt)
    assert event.endswith("to people") and "rebased" in _findings(tmp_path, 10)[-1]


def test_a_new_head_is_judged_again_and_drafts_and_our_own_prs_are_skipped(tmp_path):
    rt, lifecycle, origin = _setup(tmp_path)
    _open_human_pr(rt, origin, 11, _add_rule_files(), draft=True)
    assert _daily(rt) == []
    rt.github.open[11]["draft"] = False
    assert len(_daily(rt)) == 1
    (first,) = [cs for cs in rt.ledger.changesets("demo", ("pr_open",)) if cs["kind"] == "external"]
    head2 = _open_human_pr(rt, origin, 11, {**_add_rule_files(), "knowledge/repos/demo/core/_index.md":
                                            "# core\n\n- [rules](rules.md)\n"})
    assert merge.advance(rt, lifecycle) == [f"head_changed {first['id']}"]
    assert rt.ledger.human_queue("demo") == []           # an author pushing is not an incident
    (event,) = _daily(rt)
    assert "PR #11" in event
    assert rt.ledger.changesets("demo", ("pr_open",))[-1]["head_sha"] == head2
    # a PR the service opened itself is never judged as external
    ours = rt.ledger.new_changeset_id("demo", "intake")
    rt.ledger.stage_intake(rt.lease_owner, "demo", ours, detail={}, status="pr_open", verdicts=[],
                           human_reason="", drafted_events=[])
    rt.ledger.update_changeset(ours, pr_number=12)
    _open_human_pr(rt, origin, 12, _add_rule_files())
    assert all("PR #12" not in event for event in _daily(rt))


def _local_gate(tmp_path, rt, number):
    """Run the publisher's local gate on the verdict this service handed over."""
    import time

    from infermatrix_copilot.kb_service import local_gate

    (body,) = [item["body"] for item in _items(tmp_path, "merge") if item["body"]["pr"] == number]
    key = rt.outbox._key.public_key()
    verdict = local_gate.check_verdict(body["verdict"], key, repository=REPO, pr=number,
                                       head_sha=body["head_sha"], now=time.time())
    clone = rt.knowledge.path
    _git(clone, "fetch", "-q", "origin", "+refs/heads/main:refs/remotes/origin/main",
         f"+refs/pull/{number}/head:refs/kb/pr-{number}")
    pr = {"number": number, "state": "open", "head": {"sha": body["head_sha"]}, "labels": []}
    return local_gate.gate(clone, repository=REPO, repo="demo", pr=pr, head_sha=body["head_sha"],
                           main_sha=_git(clone, "rev-parse", "refs/remotes/origin/main"), verdict=verdict,
                           public_key=key, now=time.time())


def test_verdicts_for_external_prs_pass_the_publishers_local_gate(tmp_path):
    rt, lifecycle, origin = _setup(tmp_path)
    rt.clock = __import__("time").time          # verdict windows are checked against the real clock
    _open_human_pr(rt, origin, 7, _add_rule_files())
    _daily(rt)
    merge.advance(rt, lifecycle)
    assert _local_gate(tmp_path, rt, 7) == []
    assert [e for e in _daily(rt) if "PR #7" in e and "findings" not in e] == []   # not judged again


def test_an_auto_verdict_needs_a_current_judge_calibration(tmp_path):
    from dataclasses import replace

    from test_kb_intake_gate import _calibrate

    rt, lifecycle, origin = _setup(tmp_path)
    rt.registry["demo"] = replace(rt.registry["demo"], calibration_set="missing")
    _open_human_pr(rt, origin, 21, _add_rule_files())
    (event,) = _daily(rt)
    assert event.endswith("calibration_required")
    assert _daily(rt) == []                       # not re-judged (no paid judge calls) until calibrated
    _calibrate(tmp_path, rt, rt.registry["demo"])
    (event,) = _daily(rt)
    assert event.endswith("auto pr_open")


def test_rules_an_external_pr_retires_enter_the_retirement_ledger(tmp_path):
    rt, lifecycle, origin = _setup(tmp_path)
    (origin / "skills" / "x.md").write_text("no citations here\n")   # else it needs a companion PR
    _git(origin, "add", "-A")
    _git(origin, "-c", "user.name=t", "-c", "user.email=t@e", "commit", "-q", "-m", "drop citation")
    retired = apply_operations(_tree(), [Op("retire", PAGE, "DEMO-1a", reason="upstream-removed",
                                            evidence="PR #13")], release="v1", today="2026-09-28").files
    _open_human_pr(rt, origin, 41, {f"knowledge/{rel}": text for rel, text in retired.items()})
    rt.registry["demo"] = __import__("dataclasses").replace(rt.registry["demo"], retire_ratio=1.0)
    events = _daily(rt)
    assert "auto pr_open" in events[0], (events, rt.ledger.human_queue("demo"))
    (changeset,) = [cs for cs in rt.ledger.changesets("demo", ("pr_open",)) if cs["kind"] == "external"]
    assert changeset["detail"]["retirements"] == [{"rule_id": "DEMO-1a", "page": PAGE}]
    rt.ledger.update_changeset(changeset["id"], status="merge_requested")
    rt.github.prs[41] = {"state": "closed", "merged": True, "merge_commit_sha": "f" * 40,
                         "head": {"sha": changeset["head_sha"]}}
    merge.advance(rt, lifecycle)
    row = rt.ledger._conn.execute("SELECT rule_id, page FROM retirements WHERE repo='demo'").fetchall()
    assert [tuple(r) for r in row] == [("DEMO-1a", PAGE)]


def test_our_own_prs_are_never_judged_as_external_in_any_status(tmp_path):
    rt, lifecycle, origin = _setup(tmp_path)
    for number, status in ((31, "refine_needed"), (32, "refine_exhausted"), (33, "superseding")):
        ours = rt.ledger.new_changeset_id("demo", "intake")
        rt.ledger.stage_intake(rt.lease_owner, "demo", ours, detail={}, status=status, verdicts=[],
                               human_reason="", drafted_events=[])
        rt.ledger.update_changeset(ours, pr_number=number)
        _open_human_pr(rt, origin, number, _add_rule_files())
    assert _daily(rt) == []
    assert not _items(tmp_path, "merge")


def test_other_peoples_prs_are_checked_once_a_day_not_on_every_push(tmp_path):
    rt, lifecycle, origin = _setup(tmp_path)
    _open_human_pr(rt, origin, 40, {"knowledge/tools/z.md": "z\n"})
    judged = lambda: [e for e in poll_external(rt) if e.startswith("external ")]  # noqa: E731
    assert len(judged()) == 1                             # the first pass of the day
    _open_human_pr(rt, origin, 40, {"knowledge/tools/z.md": "z2\n"})   # the author pushes
    assert judged() == []                                 # not until the next day
    start = rt.clock()
    rt.clock = lambda: start + 24 * 3600
    assert len(judged()) == 1


def test_one_findings_comment_says_why_a_pr_is_not_merged(tmp_path):
    rt, lifecycle, origin = _setup(tmp_path)
    _open_human_pr(rt, origin, 41, _add_rule_files())
    (event,) = _daily(rt)
    assert "auto pr_open" in event
    (comment,) = _findings(tmp_path, 41)
    assert comment.startswith("<!-- kb-findings:v1 -->") and "**passed**" in comment
    assert not _items(tmp_path, "post_verdict")


def test_a_pass_that_fails_half_way_never_checks_a_pr_twice_that_day(tmp_path):
    import pytest

    from infermatrix_copilot.kb_service import external

    rt, lifecycle, origin = _setup(tmp_path)
    _open_human_pr(rt, origin, 50, {"knowledge/tools/a.md": "a\n"})
    _open_human_pr(rt, origin, 51, _add_rule_files())
    real = external.run_gate
    external.run_gate = lambda **kw: (_ for _ in ()).throw(RuntimeError("judge crashed"))
    try:
        with pytest.raises(RuntimeError):
            poll_external(rt)                       # PR 50 was checked, then PR 51 crashed
    finally:
        external.run_gate = real
    events = poll_external(rt)                      # the scheduler's next tick, same day
    assert [e for e in events if "PR #50" in e] == [] and any("PR #51" in e for e in events)


def test_a_pr_spanning_repositories_is_told_through_one_that_publishes(tmp_path):
    from dataclasses import replace

    rt, lifecycle, origin = _setup(tmp_path)
    rt.registry["other"] = replace(lifecycle, repo="other", full_name="org/other", knowledge_dir="repos/other")
    rt.ledger.ensure_repo("other", "auto_merge")
    files = {**_add_rule_files(), "knowledge/repos/other/x.md": "# x\n"}
    _open_human_pr(rt, origin, 60, files)
    (event,) = _daily(rt)
    assert event.endswith("to people")
    (comment,) = _findings(tmp_path, 60)
    assert "spans several repositories" in comment
    # with a private upstream among its scopes nothing public may be written
    rt.registry["other"] = replace(rt.registry["other"], upstream_visibility="private", mode="shadow")
    _open_human_pr(rt, origin, 61, files)
    _daily(rt)
    assert _findings(tmp_path, 61) == []
