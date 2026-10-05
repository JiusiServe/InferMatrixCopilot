"""Offline chat isolation, explicit proposals and recoverable worker fences."""
import copy
import json
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

from infermatrix_copilot.rfc_service.application import RFCService
from infermatrix_copilot.rfc_service.chat import ZcodeChatAgent, apply_plan_changes, content_digest, prepare_candidate
from infermatrix_copilot.rfc_service.models import RFCError
from infermatrix_copilot.rfc_service.store import Store, encode

BODY = "# RFC\n\n## Goals\n\nDesign detail.\n\n### Engine\n\n#### F1. Implement\n\nImplement the service.\n\n## Acceptance criteria\n\n- Verify output.\n"


class Agent:
    model = "fake-offline"
    def __init__(self):
        self.value = {"answer": "Discussion only."}
        self.hook = None
        self.calls = []
        self.reads = []

    def run(self, **kwargs):
        self.calls.append(kwargs)
        for name, args in self.reads: kwargs["read_tool"](name, args)
        if self.hook: self.hook(kwargs)
        return copy.deepcopy(self.value)


@pytest.fixture
def workspace(tmp_path):
    agent = Agent()
    service = RFCService(tmp_path / "state", providers={"github": object()}, chat_agent=agent)
    issued = service.bootstrap_admin("Owner")
    admin = service.authenticate(issued["token"])
    repo = service.dispatch(admin, "repositories.create", {"name": "Repo", "provider": "github", "external_name": "owner/repo"})
    rfc = service.dispatch(admin, "rfcs.draft", {"repo_id": repo["id"], "title": "RFC", "body": BODY})
    return service, admin, repo, rfc, agent


def user(service, admin, repo, name, role="contributor"):
    account = service.dispatch(admin, "users.create", {"name": name})
    token = service.dispatch(admin, "tokens.create", {"user_id": account["id"]})
    service.dispatch(admin, "grants.set", {"repo_id": repo["id"], "user_id": account["id"], "role": role})
    return service.authenticate(token["token"]), token


def create(service, principal, rfc):
    return service.dispatch(principal, "chat.create", {"rfc_id": rfc["id"]})["thread_id"]


def send(service, principal, thread, **data):
    return service.dispatch(principal, "chat.send", {"thread_id": thread, "message": "Discuss the design", "idempotency_key": "one", **data})


def snapshot(service, principal, thread, **data):
    return service.dispatch(principal, "chat.get", {"thread_id": thread, **data})


def proposal(agent, **extra):
    agent.value = {"answer": "Review this proposal.", "proposal": {"edits": [{"before": "Design detail.", "after": "Clearer design detail."}], "plan_changes": [], "reason": "Clarify the design.", **extra}}


def generate(workspace, principal=None, **data):
    service, admin, repo, rfc, agent = workspace
    principal = principal or admin
    thread = create(service, principal, rfc)
    send(service, principal, thread, **data)
    assert service.chat.process()["status"] == "succeeded"
    current = snapshot(service, principal, thread)
    return thread, current["proposals"][0]["id"]


def preview(service, principal, thread, identity, **data):
    return service.dispatch(principal, "chat.proposals.preview", {"thread_id": thread, "proposal_id": identity, **data})


def apply(service, principal, thread, identity, reviewed, **data):
    return service.dispatch(principal, "chat.proposals.apply", {"thread_id": thread, "proposal_id": identity, "candidate_digest": reviewed["candidate_digest"], "draft_digest": reviewed["draft_digest"], "reason": "Reviewed the exact changes", **data})


def test_optional_backend_does_not_change_existing_service(tmp_path):
    service = RFCService(tmp_path)
    assert not service.chat.enabled and service.chat.process() == {"processed": 0}


def test_conversation_is_private_to_owner_even_for_another_admin(workspace):
    service, admin, repo, rfc, agent = workspace
    alice, _ = user(service, admin, repo, "Alice")
    thread = create(service, alice, rfc)
    send(service, alice, thread)
    for who in (admin, user(service, admin, repo, "Bob")[0]):
        for action in ("chat.get", "chat.events", "chat.send", "chat.delete"):
            with pytest.raises(RFCError) as exc:
                service.dispatch(who, action, {"thread_id": thread, "message": "read", "idempotency_key": "x"})
            assert exc.value.status == 403
        assert service.dispatch(who, "chat.list")["threads"] == []


def test_send_is_idempotent_and_key_does_not_bind_a_new_message(workspace):
    service, admin, repo, rfc, agent = workspace
    thread = create(service, admin, rfc)
    first = send(service, admin, thread)
    assert send(service, admin, thread)["job_id"] == first["job_id"]
    assert snapshot(service, admin, thread)["messages_total"] == 1
    with pytest.raises(RFCError) as exc: send(service, admin, thread, message="Another request")
    assert exc.value.code == "conflict"
    service.chat.process()
    assert send(service, admin, thread)["job_id"] == first["job_id"]
    assert len(agent.calls) == 1


def test_proposal_requires_exact_review_and_apply_is_idempotent(workspace):
    service, admin, repo, rfc, agent = workspace
    proposal(agent)
    thread, identity = generate(workspace)
    reviewed = preview(service, admin, thread, identity)
    assert "Clearer design detail." in reviewed["diff"]
    assert service.dispatch(admin, "rfcs.get", {"rfc_id": rfc["id"]})["body"] == BODY
    with pytest.raises(RFCError): apply(service, admin, thread, identity, reviewed, candidate_digest="wrong")
    result = apply(service, admin, thread, identity, reviewed)
    assert result["body"] == BODY.replace("Design detail.", "Clearer design detail.")
    assert apply(service, admin, thread, identity, reviewed)["revision"] == result["revision"]
    assert len([e for e in service.dispatch(admin, "audit.list")["events"] if e["action"] == "chat.proposals.apply"]) <= 1


def test_dirty_editor_snapshot_is_server_hashed_and_full_diff_is_reviewed(workspace):
    service, admin, repo, rfc, agent = workspace
    manual = BODY.replace("Design detail.", "Manual design detail.") + "\nManual note.\n"
    proposal(agent, edits=[{"before": "Manual design detail.", "after": "Manual and assistant detail."}])
    thread, identity = generate(workspace, draft={"body": manual, "title": "RFC"}, language="en")
    reviewed = preview(service, admin, thread, identity)
    assert reviewed["draft_digest"] == content_digest("RFC", manual)
    assert "Manual note." in reviewed["diff"]
    assert "Manual note." not in reviewed["agent_diff"]
    assert agent.calls[0]["context"]["language"] == "en"
    with pytest.raises(RFCError): apply(service, admin, thread, identity, reviewed, draft_digest="changed")
    saved = apply(service, admin, thread, identity, reviewed)
    assert "Manual note." in saved["body"] and "Manual and assistant detail." in saved["body"]


@pytest.mark.parametrize("invalid", [
    {"edits": [{"before": "missing", "after": "text"}]},
    {"edits": [{"before": "Design detail.", "after": "one"}, {"before": "detail.", "after": "two"}]},
    {"edits": [{"before": "Design detail.", "after": "<!-- feature-status --> **Status: complete**"}]},
    {"plan_changes": [{"op": "update", "feature_id": "F1", "fields": {"state": "implemented"}}]},
    {"plan_changes": [{"op": "criterion_update", "criterion_id": "C1", "fields": {"verdict": "passing"}}]},
    {"edits": [{"before": "#### F1. Implement", "after": "#### F1. Changed"}], "plan_changes": []},
    {"edits": [{"before": "#### F1. Implement", "after": "#### F1. Changed"}], "plan_changes": [{"op": "update", "feature_id": "F1", "fields": {"priority": "high"}}]},
    {"edits": [{"before": "#### F1. Implement", "after": "#### F1. Changed"}], "plan_changes": [{"op": "update", "feature_id": "F1", "fields": {"title": "Different title"}}]},
    {"edits": [{"before": "- Verify output.", "after": "- Verify latency."}], "plan_changes": []},
])
def test_unanchored_or_fact_inventing_proposals_never_save(workspace, invalid):
    service, admin, repo, rfc, agent = workspace
    proposal(agent, **invalid)
    thread = create(service, admin, rfc)
    send(service, admin, thread)
    assert service.chat.process()["status"] == "failed"
    assert snapshot(service, admin, thread)["proposals"] == []
    assert service.dispatch(admin, "rfcs.get", {"rfc_id": rfc["id"]})["body"] == BODY


def test_plan_definition_changes_preserve_stable_ids_history_and_evidence(workspace):
    service, admin, repo, rfc, agent = workspace
    criterion_id = rfc["criteria"][0]["id"]
    with service.store.transaction() as con:
        row = con.execute("SELECT model FROM rfcs WHERE id=?", (rfc["id"],)).fetchone()
        model = json.loads(row["model"])
        model["features"][0]["state"] = "implemented"
        model["criteria"][0].update(verdict="passing", evidence=[{"revision": "v1", "environment": "test", "stale": False}])
        con.execute("UPDATE rfcs SET model=? WHERE id=?", (encode(model), rfc["id"]))
    proposal(agent, edits=[{"before": "#### F1. Implement", "after": "#### F1. New definition"}, {"before": "- Verify output.", "after": "- Verify latency."}],
             plan_changes=[{"op": "update", "feature_id": "F1", "fields": {"title": "New definition"}}, {"op": "criterion_update", "criterion_id": criterion_id, "fields": {"title": "Verify latency."}}])
    thread, identity = generate(workspace)
    saved = apply(service, admin, thread, identity, preview(service, admin, thread, identity))
    assert saved["features"][0]["id"] == "F1" and saved["features"][0]["state"] == "implemented"
    assert saved["criteria"][0]["id"] == criterion_id and saved["criteria"][0]["verdict"] == "pending"
    assert saved["criteria"][0]["evidence"][0]["stale"]
    assert saved["criteria_history"][0]["verdict"] == "passing"


def test_explicit_restore_and_criterion_remove_keep_history(workspace):
    service, admin, repo, rfc, agent = workspace
    old = {"features": [{"id": "F1", "title": "Old", "track": "Engine", "links": [], "depends_on": [], "owner": "", "state": "planned", "dropped": True}], "criteria": [{"id": "C1", "title": "Check", "verdict": "passing", "evidence": [{"revision": "v1"}]}], "tombstones": ["F1"]}
    with pytest.raises(RFCError): apply_plan_changes(old, [{"op": "add", "feature_id": "F1", "fields": {"title": "New"}}])
    result = apply_plan_changes(old, [{"op": "restore", "feature_id": "F1", "fields": {}}, {"op": "criterion_remove", "criterion_id": "C1"}])
    assert not result["features"][0]["dropped"] and not result["tombstones"]
    assert result["criteria"] == [] and result["criteria_history"][0]["evidence"] == old["criteria"][0]["evidence"]


def test_revocation_before_model_call_and_after_model_call_discards_outputs(workspace):
    service, admin, repo, rfc, agent = workspace
    alice, token = user(service, admin, repo, "Alice")
    thread = create(service, alice, rfc)
    send(service, alice, thread)
    service.dispatch(admin, "tokens.revoke", {"token_id": token["token_id"]})
    assert service.chat.process()["status"] == "requires_reauthorization" and not agent.calls
    bob, token = user(service, admin, repo, "Bob")
    thread = create(service, bob, rfc)
    send(service, bob, thread)
    agent.hook = lambda _: service.dispatch(admin, "grants.set", {"repo_id": repo["id"], "user_id": bob.user_id, "role": ""})
    assert service.chat.process()["status"] == "requires_reauthorization"
    assert service.store.one("SELECT COUNT(*) n FROM chat_messages WHERE thread_id=? AND role='assistant'", (thread,))["n"] == 0


def test_linked_source_restriction_hides_old_history_and_allows_owner_deletion(workspace):
    service, admin, repo, rfc, agent = workspace
    alice, _ = user(service, admin, repo, "Alice")
    source = {"provider": "github", "repository": "owner/repo", "kind": "issue", "identifier": "99", "url": "https://github.com/owner/repo/issues/99"}
    secret = service.dispatch(admin, "rfcs.draft", {"repo_id": repo["id"], "title": "Private later", "body": "Source", "source": source})
    with service.store.transaction() as con:
        model = json.loads(con.execute("SELECT model FROM rfcs WHERE id=?", (rfc["id"],)).fetchone()["model"])
        model["features"].append({"id": "F2", "title": "Sensitive title", "auto_source": source, "track": "Engine", "owner": "", "state": "planned", "links": [], "depends_on": []})
        con.execute("UPDATE rfcs SET model=? WHERE id=?", (encode(model), rfc["id"]))
    thread = create(service, alice, rfc)
    send(service, alice, thread)
    service.chat.process()
    service.dispatch(admin, "rfcs.acl", {"rfc_id": secret["id"], "restricted": True, "grants": {}})
    for action in ("chat.get", "chat.events", "chat.proposals.preview"):
        with pytest.raises(RFCError) as exc: service.dispatch(alice, action, {"thread_id": thread})
        assert exc.value.code == "context_access_changed"
    assert service.dispatch(alice, "chat.list")["threads"] == []
    assert service.dispatch(alice, "chat.delete", {"thread_id": thread}) == {"ok": True}


def test_cancellation_and_deletion_fence_inflight_output(workspace):
    service, admin, repo, rfc, agent = workspace
    thread = create(service, admin, rfc)
    queued = send(service, admin, thread)
    agent.hook = lambda _: service.dispatch(admin, "chat.cancel", {"job_id": queued["job_id"]})
    assert service.chat.process()["status"] == "cancelled"
    assert snapshot(service, admin, thread)["messages_total"] == 1
    assert service.store.one("SELECT lease_until FROM chat_jobs WHERE id=?", (queued["job_id"],))["lease_until"] == 0
    service.dispatch(admin, "chat.retry", {"job_id": queued["job_id"]})
    agent.hook = lambda _: service.dispatch(admin, "chat.delete", {"thread_id": thread})
    assert service.chat.process()["status"] == "cancelled"
    assert service.store.one("SELECT COUNT(*) n FROM chat_jobs")["n"] == 0


def test_expired_worker_recovers_without_duplicate_reply(workspace):
    service, admin, repo, rfc, agent = workspace
    thread = create(service, admin, rfc)
    job = send(service, admin, thread)["job_id"]
    with service.store.transaction() as con:
        con.execute("UPDATE chat_jobs SET status='running',worker='lost',lease_until=? WHERE id=?", (service.clock() - 1, job))
    restarted = RFCService(service.store.root, providers={"github": object()}, chat_agent=agent)
    assert restarted.chat.process()["status"] == "succeeded"
    assert restarted.chat.process() == {"processed": 0}
    assert snapshot(restarted, admin, thread)["messages_total"] == 2


def test_stale_context_fails_then_retry_uses_current_revision(workspace):
    service, admin, repo, rfc, agent = workspace
    thread = create(service, admin, rfc)
    job = send(service, admin, thread)["job_id"]
    agent.hook = lambda _: service.dispatch(admin, "rfcs.update", {"rfc_id": rfc["id"], "expected_revision": rfc["revision"], "body": BODY + "\nNew context.\n"})
    assert service.chat.process()["status"] == "failed"
    assert snapshot(service, admin, thread)["messages_total"] == 1
    agent.hook = None
    service.dispatch(admin, "chat.retry", {"job_id": job})
    assert service.chat.process()["status"] == "succeeded"
    assert "New context." in agent.calls[-1]["context"]["selected_text"]


def test_physical_concurrency_cap_includes_cancelled_calls_until_they_finish(workspace):
    service, admin, repo, rfc, agent = workspace
    threads = [create(service, admin, rfc) for _ in range(3)]
    jobs = [send(service, admin, thread)["job_id"] for thread in threads]
    entered, release = threading.Event(), threading.Event()
    lock, count = threading.Lock(), [0]
    def blocking(_):
        with lock:
            count[0] += 1
            if count[0] == 2: entered.set()
        assert release.wait(5)
    agent.hook = blocking
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(service.chat.process) for _ in range(2)]
        assert entered.wait(5)
        assert service.chat.process() == {"processed": 0}
        running = service.store.one("SELECT id FROM chat_jobs WHERE status='running'")["id"]
        service.dispatch(admin, "chat.cancel", {"job_id": running})
        assert service.chat.process() == {"processed": 0}
        release.set()
        results = [future.result() for future in futures]
    assert sorted(r["status"] for r in results) == ["cancelled", "succeeded"]
    agent.hook = None
    assert service.chat.process()["status"] == "succeeded"


def test_event_cursor_pagination_and_recent_history_are_explicit(workspace):
    service, admin, repo, rfc, agent = workspace
    thread = create(service, admin, rfc)
    with service.store.transaction() as con:
        for n in range(110):
            con.execute("INSERT INTO chat_messages(thread_id,role,content,created) VALUES (?,?,?,?)", (thread, "user", str(n), service.clock()))
    page = snapshot(service, admin, thread, limit=100)
    assert page["has_more"] and page["messages_total"] == 110
    earlier = snapshot(service, admin, thread, limit=100, before=page["next_before"])
    assert len(earlier["messages"]) == 10 and not earlier["has_more"]
    send(service, admin, thread)
    service.chat.process()
    assert agent.calls[-1]["context"]["history_truncated"] and len(agent.calls[-1]["messages"]) == 20
    first = service.dispatch(admin, "chat.events", {"thread_id": thread, "cursor": 0, "limit": 1})
    second = service.dispatch(admin, "chat.events", {"thread_id": thread, "after": first["cursor"], "limit": 100})
    assert first["has_more"] and first["events"][0]["id"] < second["events"][0]["id"]


def test_controlled_reads_use_raw_selection_and_never_expose_credentials(workspace):
    service, admin, repo, rfc, agent = workspace
    thread = create(service, admin, rfc)
    agent.reads = [("read_rfc", {"offset": 0, "limit": 100}), ("read_feature", {"feature_id": "F1"}), ("read_criteria", {})]
    send(service, admin, thread, selection={"start_line": 3, "end_line": 5, "label": "Untrusted arbitrary label"}, language="en")
    assert service.chat.process()["status"] == "succeeded"
    context = agent.calls[0]["context"]
    assert context["selected_text"] == "## Goals\n\nDesign detail.\n"
    assert "Untrusted arbitrary label" not in encode(context) and admin.credential_id not in encode(context)
    assert agent.calls[0]["read_tool"]


def test_zcode_agent_runs_only_application_read_requests_and_times_out():
    agent = ZcodeChatAgent({"timeout_seconds": 10})
    calls, reads = [], []
    class Transport:
        settings = SimpleNamespace(strict_backend_timeout_s=10)
        def complete(self, **kwargs):
            calls.append(kwargs)
            value = {"answer": "", "tool_calls": [{"name": "read_rfc", "args": {"offset": 0, "limit": 10}}]} if len(calls) == 1 else {"answer": "Answer"}
            return SimpleNamespace(text=json.dumps(value), stop_reason="end_turn")
    agent.transport = Transport()
    assert agent.run(context={"language": "en"}, messages=[{"role": "user", "content": "Read"}], read_tool=lambda name, args: reads.append(name) or {"text": "Data"}, cancelled=lambda: False)["answer"] == "Answer"
    assert reads == ["read_rfc"] and all("tools" not in c for c in calls)
    class Timeout(Transport):
        def complete(self, **kwargs): return SimpleNamespace(text="", stop_reason="max_tokens")
    agent.transport = Timeout()
    with pytest.raises(RFCError) as exc: agent.run(context={}, messages=[], read_tool=lambda *_: None, cancelled=lambda: False)
    assert exc.value.code == "chat_timeout"


def test_existing_source_snapshot_schema_migrates_without_losing_data(tmp_path):
    tmp_path.mkdir(exist_ok=True)
    con = sqlite3.connect(tmp_path / "rfc.sqlite")
    con.execute("CREATE TABLE source_snapshots(id INTEGER PRIMARY KEY,rfc_id TEXT,revision TEXT,body TEXT,created REAL)")
    con.execute("INSERT INTO source_snapshots VALUES (1,'rfc','v1','body',1)")
    con.commit(); con.close()
    store = Store(tmp_path)
    assert store.one("SELECT * FROM source_snapshots WHERE id=1")["title"] == ""
    assert store.one("SELECT * FROM source_snapshots WHERE id=1")["body"] == "body"


def test_reader_can_discuss_sourced_rfc_without_a_source_write_baseline(workspace):
    service, admin, repo, rfc, agent = workspace
    reader, _ = user(service, admin, repo, "Reader", "reader")
    sourced = service.dispatch(admin, "rfcs.draft", {"repo_id": repo["id"], "title": "RFC", "body": BODY,
        "source": {"provider": "github", "repository": "owner/repo", "kind": "issue", "identifier": "7"}})
    service._chat_source_baseline = lambda *_: pytest.fail("Read-only discussion must not prepare an external write")
    thread = create(service, reader, sourced)
    send(service, reader, thread)
    assert service.chat.process()["status"] == "succeeded"


def test_reader_cannot_apply_and_new_revision_requires_a_new_preview(workspace):
    service, admin, repo, rfc, agent = workspace
    reader, _ = user(service, admin, repo, "Reader", "reader")
    proposal(agent)
    thread, identity = generate(workspace, reader)
    reviewed = preview(service, reader, thread, identity)
    with pytest.raises(RFCError) as denied: apply(service, reader, thread, identity, reviewed)
    assert denied.value.status == 403
    service.dispatch(admin, "rfcs.update", {"rfc_id": rfc["id"], "expected_revision": rfc["revision"], "body": BODY + "\nNew design.\n"})
    with pytest.raises(RFCError) as stale: preview(service, reader, thread, identity)
    assert stale.value.code == "stale_proposal"
    assert snapshot(service, reader, thread)["proposals"][0]["status"] == "stale"


def test_old_worker_losing_its_lease_cannot_commit_a_response(workspace):
    service, admin, repo, rfc, agent = workspace
    thread = create(service, admin, rfc)
    job = send(service, admin, thread)["job_id"]
    def steal(_):
        with service.store.transaction() as con:
            con.execute("UPDATE chat_jobs SET worker='replacement' WHERE id=?", (job,))
    agent.hook = steal
    assert service.chat.process()["status"] == "cancelled"
    assert snapshot(service, admin, thread)["messages_total"] == 1
    assert service.store.one("SELECT worker,status FROM chat_jobs WHERE id=?", (job,)) == {"worker": "replacement", "status": "running"}


def test_duplicate_acceptance_text_cannot_lose_an_occurrence_silently():
    body = BODY + "- Verify output.\n"
    model = {"features": [], "criteria": [{"id": "C1", "title": "Verify output."}, {"id": "C2", "title": "Verify output."}]}
    row = {"title": "RFC", "body": body, "revision": "v1", "model": encode(model)}
    with pytest.raises(RFCError) as denied:
        prepare_candidate(row, {"edits": [{"before": "- Verify output.\n- Verify output.\n", "after": "- Verify output.\n"}],
            "plan_changes": [{"op": "criterion_remove", "criterion_id": "C2"}], "reason": "Remove one duplicate"})
    assert "Repeated acceptance" in str(denied.value)
    result = apply_plan_changes(model, [{"op": "criterion_update", "criterion_id": "C1", "fields": {"required": False}}])
    assert len(result["criteria"]) == 2 and result["criteria"][1]["id"] == "C2"


def test_conversation_list_filters_before_paging_and_honors_private_titles(workspace):
    service, admin, repo, rfc, agent = workspace
    wanted = service.dispatch(admin, "chat.create", {"rfc_id": rfc["id"], "title": "Design alternatives"})
    other = service.dispatch(admin, "rfcs.draft", {"repo_id": repo["id"], "title": "Other", "body": BODY})
    create(service, admin, other)
    page = service.dispatch(admin, "chat.list", {"rfc_id": rfc["id"], "offset": 0, "limit": 1})
    assert page["threads"][0]["id"] == wanted["thread_id"]
    assert page["threads"][0]["title"] == "Design alternatives" and page["total"] == 1


def test_source_locks_serialize_aliases_across_repository_registrations(workspace):
    service, admin, repo, rfc, agent = workspace
    other = service.dispatch(admin, "repositories.create", {"name": "Alias", "provider": "github", "external_name": "owner/repo"})
    alias = service.dispatch(admin, "rfcs.draft", {"repo_id": other["id"], "title": "Alias", "body": BODY})
    with service.store.transaction() as con:
        service._enqueue(con, admin, "rfcs.update_source", repo["id"], rfc["id"], {"source_lock": "github:owner/repo:issue:1"})
        service._enqueue(con, admin, "rfcs.update_source", other["id"], alias["id"], {"source_lock": "github:owner/repo:issue:1"})
    first = service.store.claim("one", service.clock())
    assert first is not None and service.store.claim("two", service.clock()) is None


def test_untrusted_model_cannot_request_shell_or_exceed_context_read_budget():
    agent = ZcodeChatAgent({})
    class Transport:
        settings = SimpleNamespace(strict_backend_timeout_s=180)
        name = "run_shell"
        def complete(self, **kwargs):
            return SimpleNamespace(text=json.dumps({"answer": "", "tool_calls": [{"name": self.name, "args": {}}]}), stop_reason="end_turn")
    transport = Transport()
    agent.transport = transport
    with pytest.raises(RFCError): agent.run(context={}, messages=[], read_tool=lambda *_: pytest.fail("Shell must never dispatch"), cancelled=lambda: False)
    transport.name = "read_rfc"
    calls = []
    with pytest.raises(RFCError) as exhausted:
        agent.run(context={}, messages=[], read_tool=lambda *_: calls.append(1) or {"text": "x" * 50000}, cancelled=lambda: False)
    assert exhausted.value.code == "context_too_large" and len(calls) == 3


@pytest.mark.parametrize("slow_stage", ["agent", "read", "source", "validation"])
def test_total_round_deadline_fences_late_outputs_and_retries_without_duplicates(workspace, monkeypatch, slow_stage):
    from infermatrix_copilot.rfc_service import chat as chat_module
    service, admin, repo, rfc, agent = workspace
    clock = [100.0]
    monkeypatch.setattr(chat_module.time, "monotonic", lambda: clock[0])
    proposal(agent)
    if slow_stage == "source":
        with service.store.transaction() as con:
            con.execute("UPDATE rfcs SET source=? WHERE id=?", (encode({"provider": "github", "repository": "owner/repo", "kind": "issue", "identifier": "7"}), rfc["id"]))
        def delayed_source(*args, **kwargs):
            clock[0] += 181
            kwargs["check_deadline"]()
            return {"source_revision": "v1"}
        service._chat_source_baseline = delayed_source
    elif slow_stage == "validation":
        original = chat_module.prepare_candidate
        def delayed_validation(*args, **kwargs):
            value = original(*args, **kwargs)
            clock[0] += 181
            return value
        monkeypatch.setattr(chat_module, "prepare_candidate", delayed_validation)
    elif slow_stage == "read":
        def delayed_read(kwargs):
            clock[0] += 181
            kwargs["read_tool"]("read_rfc", {})
        agent.hook = delayed_read
    else:
        agent.hook = lambda _: clock.__setitem__(0, clock[0] + 181)
    thread = create(service, admin, rfc)
    job = send(service, admin, thread)["job_id"]
    result = service.chat.process()
    assert result["status"] == "failed" and result["code"] == "chat_timeout"
    assert snapshot(service, admin, thread)["jobs"][0]["error_code"] == "chat_timeout"
    assert snapshot(service, admin, thread)["messages_total"] == 1
    assert snapshot(service, admin, thread)["proposals"] == []
    assert "timed out" in service.store.one("SELECT error FROM chat_jobs WHERE id=?", (job,))["error"]
    assert service.store.one("SELECT COUNT(*) n FROM chat_events WHERE thread_id=? AND kind='completed'", (thread,))["n"] == 0
    assert service.chat.process() == {"processed": 0}
    # Explicit recovery retains the original user message; a successful retry adds one reply.
    agent.hook = None
    agent.value = {"answer": "Recovered discussion."}
    service.dispatch(admin, "chat.retry", {"job_id": job})
    assert service.chat.process()["status"] == "succeeded"
    assert snapshot(service, admin, thread)["messages_total"] == 2


def test_zcode_uses_whole_round_remaining_budget_and_hides_execution_deadline(monkeypatch):
    from infermatrix_copilot.rfc_service import chat as chat_module
    monkeypatch.setattr(chat_module.time, "monotonic", lambda: 175.0)
    agent = ZcodeChatAgent({"timeout_seconds": 180})
    captured = []
    class Transport:
        settings = SimpleNamespace(strict_backend_timeout_s=180)
        def complete(self, **kwargs):
            captured.append((self.settings.strict_backend_timeout_s, kwargs))
            return SimpleNamespace(text='{"answer":"Done"}', stop_reason="end_turn")
    agent.transport = Transport()
    agent.run(context={"language": "en", "_round_deadline": 180.0}, messages=[], read_tool=lambda *_: None, cancelled=lambda: False)
    assert captured[0][0] == 5.0
    assert "_round_deadline" not in encode(captured[0][1])


def test_changing_owner_label_clears_authenticated_claim_identity():
    model = {"features": [{"id": "F1", "title": "Work", "track": "Engine", "depends_on": [], "links": [], "owner": "Alice", "owner_user_id": "user-alice", "state": "planned"}], "criteria": [], "tombstones": []}
    same = apply_plan_changes(model, [{"op": "update", "feature_id": "F1", "fields": {"owner": "Alice"}}])
    changed = apply_plan_changes(model, [{"op": "update", "feature_id": "F1", "fields": {"owner": "Bob"}}])
    assert same["features"][0]["owner_user_id"] == "user-alice"
    assert changed["features"][0]["owner"] == "Bob" and "owner_user_id" not in changed["features"][0]


def test_suggestion_reads_filter_hidden_sources_before_paging_and_use_current_principal(workspace):
    service, admin, repo, rfc, agent = workspace
    alice, _ = user(service, admin, repo, "Alice", "maintainer")
    source = {"provider": "github", "repository": "owner/repo", "kind": "issue", "identifier": "99"}
    hidden = service.dispatch(admin, "rfcs.draft", {"repo_id": repo["id"], "title": "Private", "body": "Private", "source": source})
    service.dispatch(admin, "rfcs.acl", {"rfc_id": hidden["id"], "restricted": True, "grants": {}})
    with service.store.transaction() as con:
        model = json.loads(con.execute("SELECT model FROM rfcs WHERE id=?", (rfc["id"],)).fetchone()["model"])
        model["suggestions"] = [
            {"id": "hidden", "title": "CONFIDENTIAL", "status": "proposed", "evidence": {"source": source}},
            {"id": "one", "title": "Visible first", "status": "proposed", "evidence": {}},
            {"id": "two", "title": "Visible second", "status": "proposed", "evidence": {}},
            {"id": "three", "title": "Visible rejected", "status": "rejected", "evidence": {}},
        ]
        con.execute("UPDATE rfcs SET model=? WHERE id=?", (encode(model), rfc["id"]))
    thread = create(service, alice, rfc)
    job = send(service, alice, thread)["job_id"]
    pages = []
    def read_pages(kwargs):
        pages.append(kwargs["read_tool"]("read_suggestions", {"offset": 0, "limit": 1, "status": "proposed"}))
        pages.append(kwargs["read_tool"]("read_suggestions", {"offset": 1, "limit": 1, "status": "proposed"}))
        pages.append(kwargs["read_tool"]("read_suggestions", {"query": "rejected", "limit": 1}))
        with pytest.raises(RFCError): kwargs["read_tool"]("read_suggestions", {"rfc_id": hidden["id"], "limit": 1})
    agent.hook = read_pages
    assert service.chat.process()["status"] == "succeeded"
    assert [page["suggestions"][0]["id"] for page in pages] == ["one", "two", "three"]
    assert [page["total"] for page in pages] == [2, 2, 1]
    assert "CONFIDENTIAL" not in encode(pages)
    payload = json.loads(service.store.one("SELECT payload FROM chat_jobs WHERE id=?", (job,))["payload"])
    assert "suggestions" not in payload["context"] and "suggestions" not in json.loads(payload["base"]["model"])
    # An administrator demoted after the round starts must use the current identity on tool reads.
    with service.store.transaction() as con:
        con.execute("UPDATE users SET admin=1 WHERE id=?", (alice.user_id,))
        fresh = service._principal(con, alice.credential_id)
    other_thread = create(service, fresh, rfc)
    send(service, fresh, other_thread)
    def demote_and_read(kwargs):
        with service.store.transaction() as con: con.execute("UPDATE users SET admin=0 WHERE id=?", (alice.user_id,))
        page = kwargs["read_tool"]("read_suggestions", {"limit": 100})
        assert "CONFIDENTIAL" not in encode(page)
    agent.hook = demote_and_read
    # This thread initially saw the private source; narrowing hides the history before any read.
    assert service.chat.process()["status"] == "requires_reauthorization"
