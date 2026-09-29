"""Unknown knowledge changes: revert PRs, exact disposal, blocked activation, the publisher's check."""

from __future__ import annotations

import json

from infermatrix_copilot.kb_service import merge
from infermatrix_copilot.kb_service.audit import (
    DISPOSED, TRUSTED, UNKNOWN, audit_main, open_unknown,
)
from test_kb_audit import _git, _land, _setup
from test_kb_flow import _items
from test_kb_intake_gate import PAGE


def _sneak(origin, text="\n<!-- pushed around the gate -->\n"):
    page = origin / "knowledge" / PAGE
    before = page.read_text()
    sha = _land(origin, f"knowledge/{PAGE}", before + text, "hotfix knowledge directly")
    return sha, before


def _open_revert(rt, origin, sha, before, *, extra=None):
    """What the publisher does for open_revert_pr, then its ack."""
    (item,) = _items(origin.parent, "open_revert_pr")
    body = item["body"]
    assert body["files"] == {f"knowledge/{PAGE}": before} and body["deleted"] == []
    _git(origin, "checkout", "-q", "-b", body["branch"])
    head = _land(origin, f"knowledge/{PAGE}", before, "revert")
    if extra:
        head = _land(origin, extra[0], extra[1], "and something else")
    _git(origin, "checkout", "-q", "main")
    merge.apply_acks(rt, [{"item_id": item["id"], "kind": "open_revert_pr", "changeset_id": body["changeset_id"],
                           "ok": True, "pr": 90, "head_sha": head, "branch": body["branch"]}])
    return body["changeset_id"], head


def _merge_revert(rt, origin, head, *, chmod=False):
    """People merge the revert PR on GitHub (the service's clone has not seen it yet)."""
    _git(origin, "-c", "user.name=h", "-c", "user.email=h@e", "merge", "-q", "--no-ff", "--no-commit", head)
    if chmod:
        _git(origin, "update-index", "--chmod=+x", f"knowledge/{PAGE}")
    _git(origin, "-c", "user.name=h", "-c", "user.email=h@e", "commit", "-q", "-m", "merge revert")
    merged = _git(origin, "rev-parse", "HEAD")
    rt.github.prs[90] = {"state": "closed", "merged": True, "merge_commit_sha": merged, "head": {"sha": head}}
    return merged


def test_an_unknown_change_is_paused_blocked_reverted_and_sent_back_to_intake(tmp_path):
    rt, lifecycle, scheduler, origin = _setup(tmp_path)
    sha, before = _sneak(origin)
    (finding,) = audit_main(rt, scheduler._pause)
    assert sha[:12] in finding and rt.ledger.repo_state("demo")["paused"]
    assert open_unknown(rt) == [sha]
    record = json.loads(rt.ledger.get_cursor("*", UNKNOWN + sha))
    assert record["state"] == "reverting"
    (revert,) = rt.ledger.changesets_of_kind("demo", "revert")
    assert revert["status"] == "pr_requested" and revert["detail"]["reverts"] == sha
    (item,) = _items(tmp_path, "open_revert_pr")
    assert item["body"]["files"] == {f"knowledge/{PAGE}": before}
    (event,) = rt.ledger.events("demo", "pending")
    assert event["payload"]["source_reference"] == f"commit {sha}"
    assert "+<!-- pushed around the gate -->" in event["payload"]["diff_excerpt"]   # the content, not a name
    assert audit_main(rt, scheduler._pause) == []        # handled once


def test_an_exact_revert_disposes_of_the_change_and_both_become_trusted(tmp_path):
    rt, lifecycle, scheduler, origin = _setup(tmp_path)
    sha, before = _sneak(origin)
    audit_main(rt, scheduler._pause)
    changeset_id, head = _open_revert(rt, origin, sha, before)
    assert rt.ledger.changeset(changeset_id)["status"] == "revert_open"
    merged = _merge_revert(rt, origin, head)
    assert f"revert_merged {changeset_id} exact=True" in merge.advance(rt, lifecycle)
    assert rt.ledger.get_cursor("*", DISPOSED + sha) == merged
    assert open_unknown(rt) == []
    assert audit_main(rt, scheduler._pause) == []        # the revert merge is trusted too
    assert {sha, merged} <= set(json.loads(rt.ledger.get_cursor("*", TRUSTED)))


def test_a_revert_merged_with_other_changes_disposes_of_nothing(tmp_path):
    rt, lifecycle, scheduler, origin = _setup(tmp_path)
    sha, before = _sneak(origin)
    audit_main(rt, scheduler._pause)
    changeset_id, head = _open_revert(rt, origin, sha, before,
                                      extra=("knowledge/repos/demo/core/_index.md", "# core\n\nsmuggled\n"))
    merged = _merge_revert(rt, origin, head)
    assert f"revert_merged {changeset_id} exact=False" in merge.advance(rt, lifecycle)
    assert open_unknown(rt) == [sha]
    assert any("not the exact revert" in row["reason"] for row in rt.ledger.human_queue("demo"))
    (finding,) = audit_main(rt, scheduler._pause)       # and the inexact merge is itself unknown
    assert merged[:12] in finding


def test_a_revert_that_would_conflict_goes_to_people(tmp_path):
    rt, lifecycle, scheduler, origin = _setup(tmp_path)
    page = origin / "knowledge" / PAGE
    sha, _before = _sneak(origin)
    _land(origin, f"knowledge/{PAGE}", page.read_text() + "\n<!-- and again -->\n", "a second direct push")
    audit_main(rt, scheduler._pause)
    record = json.loads(rt.ledger.get_cursor("*", UNKNOWN + sha))
    assert record["state"] == "conflict"
    assert all(sha not in item["body"]["title"] for item in _items(tmp_path, "open_revert_pr"))
    assert any("would conflict" in row["reason"] for row in rt.ledger.human_queue("demo"))


def test_nothing_is_activated_while_an_unknown_change_is_open(tmp_path):
    from infermatrix_copilot.kb_service.activate import activate
    from test_kb_flow import _add_agents

    rt, lifecycle, scheduler, origin = _setup(tmp_path)
    from infermatrix_copilot.kb_service.audit import AUDIT_CURSOR

    _add_agents(rt)
    activate(rt, rt.knowledge.fetch())
    rt.ledger.set_cursor("*", AUDIT_CURSOR, rt.knowledge.main_sha())   # the fixture's own setup commit
    active = rt.ledger.active_snapshot()
    sha, before = _sneak(origin)
    scheduler._last = {f"intake:{lifecycle.repo}": rt.clock(), f"release:{lifecycle.repo}": rt.clock(),
                       "external": rt.clock(), "archive": rt.clock()}
    scheduler.tick()
    assert rt.ledger.active_snapshot() == active
    assert any(e["event"] == "activation_blocked" for e in scheduler.log)
    changeset_id, head = _open_revert(rt, origin, sha, before)
    _merge_revert(rt, origin, head)
    rt.ledger.resume("demo")
    scheduler.tick()
    assert rt.ledger.active_snapshot() == rt.knowledge.main_sha() != active


def test_the_publisher_refuses_to_merge_on_top_of_an_unknown_change(tmp_path):
    from infermatrix_copilot.kb_service.activate import activate
    from test_kb_flow import _add_agents
    from test_kb_publisher import _collect, _merge_ready

    rt, lifecycle, changeset_id, pub, gh, head = _merge_ready(tmp_path)
    _add_agents(rt)
    activate(rt, rt.knowledge.fetch())
    rt.outbox.refresh_control()                             # carries the active snapshot + trusted list
    origin = tmp_path / "origin"
    _git(origin, "checkout", "-q", "main")
    sneaky, _ = _sneak(origin)
    summary = pub.run_once()
    assert summary["failed"] == 1 and gh.prs[42]["state"] == "OPEN"
    _collect(rt)
    assert rt.ledger.changeset(changeset_id)["status"] == "pr_open"   # transient: the service pauses next


def test_a_revert_merged_with_a_mode_change_is_not_exact(tmp_path):
    rt, lifecycle, scheduler, origin = _setup(tmp_path)
    sha, before = _sneak(origin)
    audit_main(rt, scheduler._pause)
    changeset_id, head = _open_revert(rt, origin, sha, before)
    _merge_revert(rt, origin, head, chmod=True)
    assert f"revert_merged {changeset_id} exact=False" in merge.advance(rt, lifecycle)
    assert open_unknown(rt) == [sha]


def test_a_revert_made_by_hand_disposes_of_what_it_undoes(tmp_path):
    rt, lifecycle, scheduler, origin = _setup(tmp_path)
    page = origin / "knowledge" / PAGE
    first, before = _sneak(origin)
    second = _land(origin, f"knowledge/{PAGE}", page.read_text() + "\n<!-- and again -->\n", "second push")
    audit_main(rt, scheduler._pause)
    assert open_unknown(rt) == sorted([first, second])
    manual = _land(origin, f"knowledge/{PAGE}", before, "revert both by hand")
    assert audit_main(rt, scheduler._pause) == []          # recognised as their exact revert
    assert open_unknown(rt) == []
    assert rt.ledger.get_cursor("*", DISPOSED + first) == manual == rt.ledger.get_cursor("*", DISPOSED + second)


def test_activation_itself_refuses_a_commit_that_passed_no_gate(tmp_path):
    import pytest

    from infermatrix_copilot.kb_service.activate import ActivationError, activate
    from test_kb_flow import _add_agents

    rt, lifecycle, scheduler, origin = _setup(tmp_path)
    _add_agents(rt)
    activate(rt, rt.knowledge.fetch())
    _sneak(origin)                                          # not even audited yet
    with pytest.raises(ActivationError, match="provenance"):
        activate(rt, rt.knowledge.fetch())                  # what `kb activate` runs


def test_a_revert_must_restore_every_knowledge_path_not_just_governed_ones(tmp_path):
    rt, lifecycle, scheduler, origin = _setup(tmp_path)
    page = origin / "knowledge" / PAGE
    before = page.read_text()
    page.write_text(before + "\n<!-- page -->\n")
    (origin / "knowledge" / "AGENTS.md").write_text("# agents, rewritten around the gate\n")
    _git(origin, "add", "-A")
    _git(origin, "-c", "user.name=t", "-c", "user.email=t@e", "commit", "-q", "-m", "page + AGENTS")
    both = _git(origin, "rev-parse", "HEAD")
    audit_main(rt, scheduler._pause)
    assert _items(tmp_path, "open_revert_pr") == []           # not all governed: people revert it
    _land(origin, f"knowledge/{PAGE}", before, "revert only the page")
    audit_main(rt, scheduler._pause)
    assert both in open_unknown(rt)                           # AGENTS.md is still unreviewed
    (origin / "knowledge" / "AGENTS.md").unlink()
    _git(origin, "add", "-A")
    _git(origin, "-c", "user.name=t", "-c", "user.email=t@e", "commit", "-q", "-m", "revert AGENTS too")
    audit_main(rt, scheduler._pause)
    assert both not in open_unknown(rt)                       # the second revert completed it


def test_a_revert_by_hand_of_a_non_governed_change_clears_the_block(tmp_path):
    rt, lifecycle, scheduler, origin = _setup(tmp_path)
    agents = _land(origin, "knowledge/AGENTS.md", "# agents around the gate\n", "AGENTS only")
    audit_main(rt, scheduler._pause)
    assert open_unknown(rt) == [agents]
    (origin / "knowledge" / "AGENTS.md").unlink()
    _git(origin, "add", "-A")
    _git(origin, "-c", "user.name=t", "-c", "user.email=t@e", "commit", "-q", "-m", "revert it")
    assert audit_main(rt, scheduler._pause) == []
    assert open_unknown(rt) == []


def test_a_later_edit_to_any_path_of_a_large_change_makes_the_revert_conflict(tmp_path):
    rt, lifecycle, scheduler, origin = _setup(tmp_path)
    core = origin / "knowledge" / "repos" / "demo" / "core"
    for n in range(55):
        (core / f"p{n:02d}.md").write_text(f"# p{n}\n")
    _git(origin, "add", "-A")
    _git(origin, "-c", "user.name=t", "-c", "user.email=t@e", "commit", "-q", "-m", "55 pages around the gate")
    big = _git(origin, "rev-parse", "HEAD")
    later = _land(origin, "knowledge/repos/demo/core/p53.md", "# p53, edited through the gate\n", "gated edit")
    merged = rt.ledger.new_changeset_id("demo", "intake")
    rt.ledger.stage_intake(rt.lease_owner, "demo", merged, detail={}, status="merged",
                           verdicts=[], human_reason="", drafted_events=[])
    rt.ledger.update_changeset(merged, merge_sha=later)
    audit_main(rt, scheduler._pause)
    record = json.loads(rt.ledger.get_cursor("*", UNKNOWN + big))
    assert len(record["paths"]) == 55
    assert record["state"] == "conflict" and "knowledge/repos/demo/core/p53.md" in record["moved"]
    assert _items(tmp_path, "open_revert_pr") == []


def test_rewinding_main_past_a_revert_brings_the_unknown_change_back(tmp_path):
    import pytest

    from infermatrix_copilot.kb_service.activate import ActivationError, activate
    from infermatrix_copilot.kb_service.audit import AUDIT_CURSOR
    from test_kb_flow import _add_agents

    rt, lifecycle, scheduler, origin = _setup(tmp_path)
    _add_agents(rt)
    activate(rt, rt.knowledge.fetch())
    rt.ledger.set_cursor("*", AUDIT_CURSOR, rt.knowledge.main_sha())
    sha, before = _sneak(origin)
    audit_main(rt, scheduler._pause)
    _land(origin, f"knowledge/{PAGE}", before, "revert by hand")
    audit_main(rt, scheduler._pause)
    assert open_unknown(rt) == []                            # disposed of by the revert
    _git(origin, "reset", "-q", "--hard", sha)               # main rewound past the revert
    with pytest.raises(ActivationError, match="provenance"):
        activate(rt, rt.knowledge.fetch())


def test_a_change_touching_a_private_scope_is_never_reverted_in_public(tmp_path):
    from dataclasses import replace

    rt, lifecycle, scheduler, origin = _setup(tmp_path)
    rt.registry["secret"] = replace(lifecycle, repo="secret", full_name="org/secret", knowledge_dir="repos/secret",
                                    upstream_visibility="private", mode="shadow")
    rt.ledger.ensure_repo("secret", "shadow")
    page = origin / "knowledge" / PAGE
    page.write_text(page.read_text() + "\n<!-- public part -->\n")
    private = origin / "knowledge" / "repos" / "secret" / "notes.md"
    private.parent.mkdir(parents=True, exist_ok=True)
    private.write_text("# private upstream notes\n")
    _git(origin, "add", "-A")
    _git(origin, "-c", "user.name=t", "-c", "user.email=t@e", "commit", "-q", "-m", "mixed scopes")
    mixed = _git(origin, "rev-parse", "HEAD")
    audit_main(rt, scheduler._pause)
    assert _items(tmp_path, "open_revert_pr") == []           # nothing public about the private scope
    assert rt.ledger.events("demo", "pending") == []
    assert json.loads(rt.ledger.get_cursor("*", UNKNOWN + mixed))["state"] == "people"
    assert rt.ledger.repo_state("demo")["paused"]            # still stopped until people revert it
