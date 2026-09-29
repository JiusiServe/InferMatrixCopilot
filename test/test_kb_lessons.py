"""Copilot run lessons (source 2): verified pr_debug fixes become knowledge events."""

from __future__ import annotations

import json
from dataclasses import replace
from urllib.parse import parse_qs, urlparse

from infermatrix_copilot.kb_service.runtime import collect_events
from test_kb_intake_gate import FakeGitHub, ScriptedGateway, _generator_then_judge, _runtime

MARKER = "<!-- infermatrix-copilot:bugfix-record:v2 -->"


def _record(repo="org/demo", run="run-20260929-000001-aaaaaa"):
    """The shape engine/steps/pr/debug.py drops and posts (schema v2)."""
    return {"schema_version": 2, "run_id": run, "repo": repo, "pr": 11, "kind": "bugfix_run",
            "title": "pr_debug fixes for PR #11",
            "groups": [{"signature": "test_queue_full", "jobs": ["unit"], "root_cause": "queue grew without bound",
                        "fix_summary": "reject when full", "verification": "unit test passes",
                        "files": ["demo/core/q.py"]}],
            "created_at": "2026-09-29T00:00:00+00:00",
            "event_id": f"bugfix_run:{repo.casefold()}:{run}", "repository": {"full_name": repo, "alias": "demo"}}


class MailboxGitHub(FakeGitHub):
    def __init__(self, comments):
        super().__init__()
        self.comments = comments

    def _answer(self, url):
        if "/issues/135/comments" in url:   # GitHub: created-time order, updated strictly after ``since``
            query = parse_qs(urlparse(url).query)
            since = query.get("since", [""])[0]
            page = int(query["page"][0])
            rows = [c for c in self.comments if c["updated_at"] > since]
            return rows[(page - 1) * 100:page * 100]
        return super()._answer(url)


def comment(cid, login, record, second=None):
    second = cid if second is None else second
    stamp = f"2026-09-29T{second // 3600:02d}:{second // 60 % 60:02d}:{second % 60:02d}Z"
    return {"id": cid, "created_at": stamp, "updated_at": stamp,
            "user": {"login": login}, "body": f"{MARKER}\n```json\n{json.dumps(record)}\n```\n"}


def _rt(tmp_path, monkeypatch, comments=()):
    rt, lifecycle = _runtime(tmp_path, ScriptedGateway(_generator_then_judge()))
    rt.github = MailboxGitHub(list(comments))
    monkeypatch.setenv("KB_BUGFIX_DIR", str(tmp_path / "drops"))
    return rt, lifecycle


def _events(rt):
    return [e for e in rt.ledger.events("demo", "pending", limit=100) if e["source"] == "copilot_run"]


def test_a_dropped_fix_record_becomes_one_event(tmp_path, monkeypatch):
    rt, lifecycle = _rt(tmp_path, monkeypatch)
    drops = tmp_path / "drops"
    drops.mkdir()
    (drops / "run-1.json").write_text(json.dumps(_record()))
    collect_events(rt, lifecycle)
    (event,) = _events(rt)
    assert "queue grew without bound" in event["payload"]["body"] and "reject when full" in event["payload"]["body"]
    assert (drops / "run-1.consumed").exists()
    (drops / "run-1.json").write_text(json.dumps(_record()))      # delivered twice: idempotent by event id
    collect_events(rt, lifecycle)
    assert len(_events(rt)) == 1


def test_records_for_other_or_ambiguous_repositories_are_not_taken(tmp_path, monkeypatch):
    rt, lifecycle = _rt(tmp_path, monkeypatch)
    rt.registry["org/demo"] = replace(lifecycle, repo="org/demo", full_name="other/x")   # alias collides
    drops = tmp_path / "drops"
    drops.mkdir()
    (drops / "mine.json").write_text(json.dumps(_record(repo="org/demo")))
    (drops / "theirs.json").write_text(json.dumps(_record(repo="someone/else")))
    (drops / "broken.json").write_text("{not json")
    collect_events(rt, lifecycle)
    assert _events(rt) == []
    assert (drops / "mine.quarantined").exists()                # ambiguous: never guessed
    assert (drops / "theirs.json").exists() and (drops / "broken.json").exists()


def test_the_mailbox_takes_only_allowed_authors_and_advances_its_cursor(tmp_path, monkeypatch):
    comments = [comment(1, "tzhouam", _record(run="run-a")), comment(2, "mallory", _record(run="run-b")),
                comment(3, "tzhouam", _record(repo="someone/else", run="run-c"))]
    rt, lifecycle = _rt(tmp_path, monkeypatch, comments)
    monkeypatch.setenv("KB_BUGFIX_MAILBOX", "org/infra#135")
    collect_events(rt, lifecycle)
    assert _events(rt) == []                                      # no author allowlist: mailbox ignored
    monkeypatch.setenv("KB_BUGFIX_AUTHORS", "TZhouAM")
    collect_events(rt, lifecycle)
    (event,) = _events(rt)
    assert event["external_id"] == "bugfix_run:org/demo:run-a"
    assert rt.ledger.get_cursor("demo", "bugfix_mailbox_after") == "3"
    rt.github.comments.append(comment(4, "tzhouam", _record(run="run-d")))
    collect_events(rt, lifecycle)
    assert len(_events(rt)) == 2


def test_the_mailbox_is_never_stuck_behind_a_page_window(tmp_path, monkeypatch):
    comments = [comment(i, "someone", {}) for i in range(1, 2001)] + [comment(2001, "tzhouam", _record(run="late"))]
    rt, lifecycle = _rt(tmp_path, monkeypatch, comments)
    monkeypatch.setenv("KB_BUGFIX_MAILBOX", "org/infra#135")
    monkeypatch.setenv("KB_BUGFIX_AUTHORS", "tzhouam")
    collect_events(rt, lifecycle)                                 # first poll reads the first 2,000
    collect_events(rt, lifecycle)                                 # the next continues past them
    (event,) = _events(rt)
    assert event["external_id"] == "bugfix_run:org/demo:late"


def test_a_code_fence_inside_the_record_and_malformed_files_are_handled(tmp_path, monkeypatch):
    fenced = _record(run="fenced")
    fenced["groups"][0]["root_cause"] = "the trace:\n```\nQueueFull\n```\n"
    bad = _record(run="bad")
    bad["groups"][0]["files"] = {"not": "a list"}
    rt, lifecycle = _rt(tmp_path, monkeypatch, [comment(1, "tzhouam", bad), comment(2, "tzhouam", fenced)])
    monkeypatch.setenv("KB_BUGFIX_MAILBOX", "org/infra#135")
    monkeypatch.setenv("KB_BUGFIX_AUTHORS", "tzhouam")
    drops = tmp_path / "drops"
    drops.mkdir()
    (drops / "a-bad.json").write_text(json.dumps(bad))
    (drops / "b-good.json").write_text(json.dumps(_record(run="good")))
    collect_events(rt, lifecycle)
    assert {e["external_id"] for e in _events(rt)} == {"bugfix_run:org/demo:fenced", "bugfix_run:org/demo:good"}
    assert "QueueFull" in next(e for e in _events(rt) if e["external_id"].endswith("fenced"))["payload"]["body"]
    assert (drops / "a-bad.json").exists()                        # malformed: left for inspection


def test_comments_sharing_the_last_seen_second_are_not_skipped(tmp_path, monkeypatch):
    # comments 2,000 and 2,001 share a second across the page window
    comments = [comment(i, "someone", {}) for i in range(1, 2001)] + [comment(2001, "tzhouam", _record(run="same"),
                                                                              second=2000)]
    rt, lifecycle = _rt(tmp_path, monkeypatch, comments)
    monkeypatch.setenv("KB_BUGFIX_MAILBOX", "org/infra#135")
    monkeypatch.setenv("KB_BUGFIX_AUTHORS", "tzhouam")
    collect_events(rt, lifecycle)
    collect_events(rt, lifecycle)
    (event,) = _events(rt)
    assert event["external_id"] == "bugfix_run:org/demo:same"
    collect_events(rt, lifecycle)                                 # the overlap is deduplicated by id
    assert len(_events(rt)) == 1
