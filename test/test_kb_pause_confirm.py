"""A pause counts once GitHub shows it; unconfirmed pauses go to people."""

from __future__ import annotations

from infermatrix_copilot.kb_service import merge
from test_kb_flow import _ack, _flow_runtime, _items, _open_pr

HEAD = "d" * 40


def _paused_repo(tmp_path):
    rt, lifecycle = _flow_runtime(tmp_path)
    changeset_id, publisher = _open_pr(tmp_path, rt, lifecycle)
    _ack(tmp_path, rt, publisher, kind="open_pr", changeset_id=changeset_id, ok=True, pr=42, head_sha=HEAD)
    rt.github.prs[42] = {"state": "open", "merged": False, "draft": False, "head": {"sha": HEAD}}
    rt.outbox.transition(lambda: rt.ledger.bump_generation(lifecycle.repo, pause=True, reason="drill"),
                         public_repos={lifecycle.repo})
    assert merge.pause_open_prs(rt.ledger, rt.outbox, lifecycle.repo, "drill") == 1
    return rt, lifecycle, changeset_id, publisher


def _later(rt, seconds):
    start = rt.clock()
    rt.clock = lambda: start + seconds


def test_an_unacked_pause_goes_to_people_once_after_five_minutes(tmp_path):
    rt, lifecycle, changeset_id, _ = _paused_repo(tmp_path)
    assert merge.advance(rt, lifecycle) == []
    assert merge.pause_unconfirmed(rt.ledger, "demo") == 1
    _later(rt, merge.PAUSE_CONFIRM + 1)
    assert merge.advance(rt, lifecycle) == [f"pause_unconfirmed {changeset_id}"]
    (alert,) = [item for item in rt.ledger.human_queue("demo") if "not confirmed" in item["reason"]]
    assert "gh pr ready 42 --undo" in alert["reason"] and "drill" in alert["reason"]
    assert merge.advance(rt, lifecycle) == []            # once


def test_an_acked_pause_is_confirmed_only_when_github_shows_a_draft(tmp_path):
    rt, lifecycle, changeset_id, publisher = _paused_repo(tmp_path)
    _ack(tmp_path, rt, publisher, kind="pause", changeset_id=changeset_id, ok=True)
    assert rt.ledger.changeset(changeset_id)["status"] == "paused"
    pauses = len(_items(tmp_path, "pause"))
    assert merge.advance(rt, lifecycle) == []            # not a draft on GitHub: pause again
    assert len(_items(tmp_path, "pause")) == pauses + 1
    assert merge.pause_unconfirmed(rt.ledger, "demo") == 1
    _later(rt, merge.PAUSE_CONFIRM + 1)
    assert merge.advance(rt, lifecycle) == [f"pause_unconfirmed {changeset_id}"]
    rt.github.prs[42]["draft"] = True
    assert merge.advance(rt, lifecycle) == [f"pause_confirmed {changeset_id}"]
    assert merge.pause_unconfirmed(rt.ledger, "demo") == 0
    assert merge.advance(rt, lifecycle) == []


def test_resume_clears_the_pause_bookkeeping(tmp_path):
    rt, lifecycle, changeset_id, publisher = _paused_repo(tmp_path)
    _ack(tmp_path, rt, publisher, kind="pause", changeset_id=changeset_id, ok=True)
    rt.github.prs[42]["draft"] = True
    merge.advance(rt, lifecycle)
    rt.ledger.resume("demo")
    merge.resume_paused_prs(rt.ledger, "demo")
    detail = rt.ledger.changeset(changeset_id)["detail"]
    assert not {"pause_requested_at", "pause_alerted", "pause_confirmed"} & set(detail)
    assert merge.pause_unconfirmed(rt.ledger, "demo") == 0


def test_kb_status_reports_unconfirmed_pauses(tmp_path, monkeypatch, capsys):
    import json

    from infermatrix_copilot.kb_service import cli

    rt, lifecycle, changeset_id, _ = _paused_repo(tmp_path)
    monkeypatch.setattr(cli, "_registry", lambda: rt.registry)
    monkeypatch.delenv("KB_SIGNING_KEY", raising=False)
    assert cli.main(["--state-dir", str(tmp_path / "state"), "status"]) == 0
    report = json.loads(capsys.readouterr().out)
    (demo,) = [row for row in report["repos"] if row["repo"] == "demo"]
    assert demo["pause_unconfirmed"] == 1


def test_a_confirmed_pause_that_is_undone_counts_as_unconfirmed_again(tmp_path):
    rt, lifecycle, changeset_id, publisher = _paused_repo(tmp_path)
    _ack(tmp_path, rt, publisher, kind="pause", changeset_id=changeset_id, ok=True)
    rt.github.prs[42]["draft"] = True
    merge.advance(rt, lifecycle)
    assert merge.pause_unconfirmed(rt.ledger, "demo") == 0
    rt.github.prs[42]["draft"] = False                   # someone marked it ready again
    merge.advance(rt, lifecycle)
    assert merge.pause_unconfirmed(rt.ledger, "demo") == 1
    _later(rt, merge.PAUSE_CONFIRM + 1)
    assert merge.advance(rt, lifecycle) == [f"pause_unconfirmed {changeset_id}"]


def test_resume_before_the_ack_clears_the_request(tmp_path):
    rt, lifecycle, changeset_id, _ = _paused_repo(tmp_path)
    rt.ledger.resume("demo")
    merge.resume_paused_prs(rt.ledger, "demo")
    assert merge.pause_unconfirmed(rt.ledger, "demo") == 0
    assert "pause_requested_at" not in rt.ledger.changeset(changeset_id)["detail"]


def test_a_paused_pr_whose_head_moves_stays_watched(tmp_path):
    rt, lifecycle, changeset_id, publisher = _paused_repo(tmp_path)
    rt.github.prs[42]["head"]["sha"] = "e" * 40
    _later(rt, merge.PAUSE_CONFIRM + 1)
    assert merge.advance(rt, lifecycle) == [f"pause_unconfirmed {changeset_id}"]
    _ack(tmp_path, rt, publisher, kind="pause", changeset_id=changeset_id, ok=True)
    assert merge.pause_unconfirmed(rt.ledger, "demo") == 1
    rt.github.prs[42]["draft"] = True
    assert merge.advance(rt, lifecycle) == [f"pause_confirmed {changeset_id}"]


def test_a_completed_retry_never_blocks_the_next_re_pause(tmp_path):
    rt, lifecycle, changeset_id, publisher = _paused_repo(tmp_path)
    _ack(tmp_path, rt, publisher, kind="pause", changeset_id=changeset_id, ok=True)
    merge.advance(rt, lifecycle)                          # not a draft: a retry is issued
    _ack(tmp_path, rt, publisher, kind="pause", changeset_id=changeset_id, ok=True)   # the retry ran
    assert rt.ledger.changeset(changeset_id)["pending_item"] is None
    rt.github.prs[42]["draft"] = True
    merge.advance(rt, lifecycle)                          # confirmed
    rt.github.prs[42]["draft"] = False                    # ready again
    before = len(_items(tmp_path, "pause"))
    merge.advance(rt, lifecycle)
    assert len(_items(tmp_path, "pause")) == before + 1   # a fresh pause at once


def test_overdue_pauses_escalate_even_when_github_cannot_be_read(tmp_path):
    rt, lifecycle, changeset_id, publisher = _paused_repo(tmp_path)

    def down(url):
        raise RuntimeError("GitHub 503")

    rt.github._fetch = down
    _later(rt, merge.PAUSE_CONFIRM + 1)
    events = merge.advance(rt, lifecycle)                 # unacked pause, GitHub down
    assert f"pause_unconfirmed {changeset_id}" in events and f"observe_failed {changeset_id}" in events

    rt2, lifecycle2, changeset2, publisher2 = _paused_repo(tmp_path / "acked")
    _ack(tmp_path / "acked", rt2, publisher2, kind="pause", changeset_id=changeset2, ok=True)
    rt2.github._fetch = down
    _later(rt2, merge.PAUSE_CONFIRM + 1)
    assert f"pause_unconfirmed {changeset2}" in merge.advance(rt2, lifecycle2)   # acked, never confirmed
