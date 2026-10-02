"""The judge's budget includes discussion and metadata, with atomic threads."""

import copy
import hashlib

import pytest

from infermatrix_copilot.kb_service import evidence as ev
from infermatrix_copilot.knowledge_service.facts import FactsError
from test_kb_rule_source_fragments import Source, _prepared


def test_large_metadata_is_hashed_and_late_withdrawal_survives_as_complete_thread(monkeypatch):
    monkeypatch.setattr(ev, "PER_RULE", 4096)
    path = "pkg/browser.py"
    item = _prepared([path])
    item["body"] = "unrelated summary <details> " * 50000
    item["commits"] = [{"sha": str(n), "commit": {"message": "unrelated build metadata " * 100}}
                       for n in range(1000)]
    item["threads"] = [{"id": n, "path": "pkg/other.py", "body": "unrelated concern " * 100,
                        "created_at": "2026-09-01"} for n in range(1000)]
    item["threads"] += [
        {"id": 2001, "path": path, "body": "update_decision loses configuration", "created_at": "2026-09-30"},
        {"id": 2002, "in_reply_to_id": 2001, "body": "Fixed and verified", "created_at": "2026-10-01"},
        {"id": 2003, "in_reply_to_id": 2002, "body": "Withdrawn; the original concern was incorrect.",
         "created_at": "2026-10-02"},
    ]
    item["reviews"] = [{"id": 3, "body": "unrelated formatting observation " * 10000}]
    item["replies"] = [{"id": 4, "body": "unrelated summary " * 10000}]
    before = copy.deepcopy(item)
    source = Source({path: "def update_decision(config):\n    return config\n"})
    (shown,) = ev.for_rule(f"`{path}::update_decision` ^[PR #10]", [item], source)
    assert len(ev._encoded([shown])) <= ev.PER_RULE
    assert [row["id"] for row in shown["threads"]] == [2001, 2002, 2003]
    assert shown["threads"][-1]["body"].startswith("Withdrawn")
    omissions = {record["field"]: record for record in shown["evidence_omissions"]}
    assert {"body", "commits", "threads", "reviews", "replies"} <= omissions.keys()
    assert omissions["body"]["sha256"] == hashlib.sha256(ev._encoded(item["body"])).hexdigest()
    assert omissions["threads"]["status"] == "selected_complete_reply_chains"
    assert "body" not in shown and "commits" not in shown
    assert any("def update_decision" in f.get("content", "") for f in shown["source_fragments"])
    assert item == before, "narrowing a judge packet must preserve canonical source evidence"


def test_relevant_thread_too_large_is_refused_whole_with_size_and_hash(monkeypatch):
    monkeypatch.setattr(ev, "PER_RULE", 4096)
    item = _prepared(["pkg/browser.py"])
    item["threads"] = [
        {"id": 1, "path": "pkg/browser.py", "body": "update_decision " + "x" * 3000},
        {"id": 2, "in_reply_to_id": 1, "body": "Withdrawn " + "y" * 3000},
    ]
    with pytest.raises(FactsError, match=r"chronology exceeds evidence budget: \d+ bytes sha256=[0-9a-f]{64}"):
        ev.for_rule("`pkg/browser.py::update_decision` ^[PR #10]", [item], None)


def test_small_sources_retain_all_discussion_and_commit_metadata():
    item = _prepared(["pkg/browser.py"])
    item.update(body="Purpose", commits=[{"sha": "a", "commit": {"message": "change"}}],
                threads=[{"id": 1, "path": "pkg/other.py", "body": "Unrelated but small"}],
                reviews=[{"id": 2, "body": "Review"}], replies=[{"id": 3, "body": "Reply"}])
    (shown,) = ev.for_rule("`pkg/browser.py` ^[PR #10]", [item], None)
    for field in ("body", "commits", "threads", "reviews", "replies"):
        assert shown[field] == item[field]
    assert "evidence_omissions" not in shown


def test_unprepared_lesson_metadata_cannot_bypass_the_same_budget(monkeypatch):
    monkeypatch.setattr(ev, "PER_RULE", 4096)
    item = {"source_reference": "run lesson", "summary": "huge lesson data " * 100000}
    (shown,) = ev.for_rule("Any rule", [item], None)
    assert len(ev._encoded([shown])) <= ev.PER_RULE
    assert shown["source_reference"] == "run lesson"
    assert shown["evidence_omissions"][0]["field"] == "summary"
