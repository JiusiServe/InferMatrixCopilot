"""The release-sweep summary: always recorded, published only where allowed."""

from __future__ import annotations

import json
import subprocess
from dataclasses import replace

from infermatrix_copilot.kb_service.report import MARKER, publish_summary, summary
from test_kb_flow import _flow_runtime, _items


def _report(rt, changeset_ids):
    return {"sweep": {"tag": "v0.30.0", "from_sha": "a" * 40, "to_sha": "b" * 40, "reason": "release"},
            "t1": {"issues": [{"code": "x"}], "duplicates": {}, "over_capacity": {}, "unlisted": ["p.md"]},
            "changesets": changeset_ids, "skipped_pages": ["k.md", "l.md"], "failed_pages": ["f.md", "f.md"],
            "breaker": "", "complete": True}


def _staged(rt, status, ops):
    changeset_id = rt.ledger.new_changeset_id("demo", "sweep")
    rt.ledger.stage_intake(rt.ledger.acquire_lease("t"), "demo", changeset_id, kind="sweep",
                           detail={"operations": ops}, status=status, verdicts=[], human_reason="",
                           drafted_events=[])
    return changeset_id


def test_the_summary_counts_findings_fixes_people_and_cost(tmp_path):
    from infermatrix_copilot.trace_store import TraceStore, trace_context

    rt, lifecycle = _flow_runtime(tmp_path)
    rt.traces = TraceStore(tmp_path / "traces", environ={})
    with trace_context(run_id="sweep-demo-v0.30.0-1790000000", playbook="kb-sweep"):
        rt.traces.append("model_call", inputs={"prompt": "p"}, outputs={"reply": "r"},
                         model={"role": "generator"}, usage={"input_tokens": 100, "output_tokens": 7}, seconds=3)
    ids = [_staged(rt, "gated", [{"kind": "retire", "page": "x", "rule_id": "A"}]),
           _staged(rt, "human", [{"kind": "edit_same_meaning", "page": "x", "rule_id": "B"}])]
    title, body = summary(rt, lifecycle, {**_report(rt, ids), "run_id": "sweep-demo-v0.30.0-1790000000"})
    assert title == "Knowledge sweep report: demo v0.30.0" and body.startswith(MARKER)
    for expected in ("| structural issues (T1) | 1 |", "| pages missing from an index (fixed) | 1 |",
                     "| pages kept as they are | 2 |", "| pages that failed an evaluation | 1 (0 failed attempts) |",
                     "| change sets | 2 (gated: 1, human: 1) |", "edit_same_meaning: 1, retire: 1",
                     "| model calls | 1 (100 in / 7 out tokens, 3s) |"):
        assert expected in body, expected


def test_auto_merge_publishes_the_summary_as_an_issue(tmp_path):
    rt, lifecycle = _flow_runtime(tmp_path)
    assert publish_summary(rt, lifecycle, _report(rt, [])) == "issued"
    (item,) = _items(tmp_path, "open_issue")
    assert item["body"]["title"] == "Knowledge sweep report: demo v0.30.0"
    assert (tmp_path / "state" / "reports" / "sweep-demo-v0.30.0.md").exists()


def test_shadow_and_private_repositories_only_record_it(tmp_path):
    rt, lifecycle = _flow_runtime(tmp_path)
    for variant in (replace(lifecycle, mode="shadow"), replace(lifecycle, upstream_visibility="private")):
        assert publish_summary(rt, variant, _report(rt, [])) == "recorded"
    assert _items(tmp_path, "open_issue") == []
    assert (tmp_path / "state" / "reports" / "sweep-demo-v0.30.0.md").exists()


def test_the_publisher_opens_one_issue_per_report(tmp_path):
    from test_kb_publisher import FakeGh, _setup

    rt, lifecycle, _changeset_id, pub, gh = _setup(tmp_path)
    issues: list[dict] = []

    def run(argv, **kw):
        args = argv[1:]
        if args[:2] == ["issue", "list"]:
            return subprocess.CompletedProcess(argv, 0, json.dumps(issues).encode(), b"")
        if args[:2] == ["issue", "create"]:
            if "--label" in args:
                return subprocess.CompletedProcess(argv, 1, b"", b"label not found")
            issues.append({"number": 7, "title": args[args.index("--title") + 1]})
            return subprocess.CompletedProcess(argv, 0, b"https://github.com/o/r/issues/7\n", b"")
        return FakeGh.__call__(gh, argv, **kw)

    pub.github.run = run
    publish_summary(rt, lifecycle, _report(rt, []))
    pub.run_once()
    publish_summary(rt, lifecycle, _report(rt, []))       # the same report again
    pub.run_once()
    assert len(issues) == 1                                 # reused by title
    acks = [json.loads(p.read_text())["payload"] for p in (tmp_path / "state" / "inbox" / "acks").glob("*.json")]
    assert all(a["ok"] and a["pr"] == 7 for a in acks if a["kind"] == "open_issue")


def test_fallback_sweeps_of_the_same_tag_get_their_own_report(tmp_path):
    from infermatrix_copilot.kb_service.report import report_id

    rt, lifecycle = _flow_runtime(tmp_path)
    first = {**_report(rt, []), "sweep": {"tag": "v0.30.0", "reason": "fallback"}, "started_at": 1790000000.0}
    later = {**first, "started_at": 1790000000.0 + 31 * 86400}
    assert report_id(rt, first) != report_id(rt, later)
    assert report_id(rt, first) == report_id(rt, dict(first))            # stable across retries
    assert report_id(rt, _report(rt, [])) == "v0.30.0"
    publish_summary(rt, lifecycle, first)
    publish_summary(rt, lifecycle, later)
    titles = {item["body"]["title"] for item in _items(tmp_path, "open_issue")}
    assert len(titles) == 2


def test_a_resumed_sweep_reports_every_attempt(tmp_path):
    from infermatrix_copilot.kb_service.sweep import _progress

    rt, lifecycle = _flow_runtime(tmp_path)
    sweep = {"tag": "v1", "from_sha": "a" * 40, "to_sha": "b" * 40, "reason": "release"}
    progress = _progress(rt, lifecycle, sweep)
    progress["kept"] = ["repos/demo/core/a.md"]            # kept in an earlier attempt
    progress["attempts"] = {"repos/demo/core/b.md": 1}      # failed once, settled later
    report = {**_report(rt, []), "sweep": sweep, "kept_pages": progress["kept"],
              "failed_attempts": progress["attempts"], "skipped_pages": [], "failed_pages": []}
    _title, body = summary(rt, lifecycle, report)
    assert "| pages kept as they are | 1 |" in body
    assert "| pages that failed an evaluation | 1 (1 failed attempts) |" in body


def test_a_fallback_sweep_never_reports_the_release_sweeps_model_calls(tmp_path):
    from infermatrix_copilot.trace_store import TraceStore, trace_context

    rt, lifecycle = _flow_runtime(tmp_path)
    rt.traces = TraceStore(tmp_path / "traces", environ={})
    with trace_context(run_id="sweep-demo-v0.30.0-1", playbook="kb-sweep"):
        rt.traces.append("model_call", inputs={"prompt": "p"}, outputs={"reply": "r"},
                         model={"role": "generator"}, usage={"input_tokens": 9, "output_tokens": 9})
    fallback = {**_report(rt, []), "sweep": {"tag": "v0.30.0", "reason": "fallback"}, "run_id": "sweep-demo-v0.30.0-2"}
    assert "| model calls | 0 (0 in / 0 out tokens, 0s) |" in summary(rt, lifecycle, fallback)[1]


def test_a_queued_report_survives_a_failure_and_is_flushed_later(tmp_path, monkeypatch):
    from infermatrix_copilot.kb_service import report as report_module

    rt, lifecycle = _flow_runtime(tmp_path)
    report_module.queue_report(rt.ledger, "demo", {**_report(rt, []), "run_id": "sweep-demo-v0.30.0-5"})
    report_module.queue_report(rt.ledger, "demo", {**_report(rt, []), "run_id": "sweep-demo-v0.30.0-5"})  # once

    def broken(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(report_module, "publish_summary", broken)
    import pytest
    with pytest.raises(OSError):
        report_module.flush_reports(rt, lifecycle)
    monkeypatch.undo()
    assert report_module.flush_reports(rt, lifecycle) == ["sweep-demo-v0.30.0-5"]
    assert report_module.flush_reports(rt, lifecycle) == []
    assert len(_items(tmp_path, "open_issue")) == 1


def test_a_report_issue_survives_a_transient_github_failure(tmp_path):
    from test_kb_publisher import FakeGh, _setup

    rt, lifecycle, _changeset_id, pub, gh = _setup(tmp_path)
    issues: list[dict] = []
    state = {"down": True}

    def run(argv, **kw):
        args = argv[1:]
        if args[:2] == ["issue", "list"]:
            if state["down"]:
                return subprocess.CompletedProcess(argv, 1, b"", b"HTTP 502")
            return subprocess.CompletedProcess(argv, 0, json.dumps(issues).encode(), b"")
        if args[:2] == ["issue", "create"]:
            issues.append({"number": 8, "title": args[args.index("--title") + 1]})
            return subprocess.CompletedProcess(argv, 0, b"https://github.com/o/r/issues/8\n", b"")
        return FakeGh.__call__(gh, argv, **kw)

    pub.github.run = run
    publish_summary(rt, lifecycle, _report(rt, []))
    pub.run_once()
    assert issues == [] and not [p for p in (tmp_path / "state" / "inbox" / "acks").glob("*.json")
                                 if json.loads(p.read_text())["payload"]["kind"] == "open_issue"]
    state["down"] = False
    pub.run_once()                                          # retried, not lost
    assert len(issues) == 1
