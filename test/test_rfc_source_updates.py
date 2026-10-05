"""Approved chat candidates survive guarded, durable source writeback."""
import copy
import json

import pytest

from infermatrix_copilot.rfc_service.application import RFCService, content_digest
from infermatrix_copilot.rfc_service.models import ProviderError, RFCError, SourceRef


BODY = "# Source RFC\n\n### Engine\n\n#### F1. Implement\n\n## Acceptance criteria\n\n- Verify output.\n"


class SourceProvider:
    def __init__(self):
        self.ref = SourceRef("github", "owner/repo", "issue", "1", "https://github.com/owner/repo/issues/1", host="github.com")
        self.source = {"source": self.ref.to_dict(), "title": "Source RFC", "body": BODY, "revision": "s1"}
        self.writes = 0
        self.timeout = False
        self.failure = False
        self.on_write = None
        self.items = {}

    def get_source(self, ref):
        return copy.deepcopy(self.source)

    def get_item(self, ref):
        return copy.deepcopy(self.items[ref.identifier])

    def discover(self, repository, scope, since=""):
        return []

    def update_source(self, ref, body, expected_revision, *, title=None):
        assert self.source["revision"] == expected_revision
        self.writes += 1
        if self.failure:
            raise ProviderError("Provider returned HTTP 403")
        self.source.update(title=title, body=body, revision="s" + str(self.writes + 1))
        if self.on_write:
            self.on_write()
        if self.timeout:
            self.timeout = False
            raise ProviderError("Provider request could not be completed", uncertain=True)
        return copy.deepcopy(self.source)


def setup(tmp_path, provider=None):
    provider = provider or SourceProvider()
    service = RFCService(tmp_path / "state", {"github": provider})
    token = service.bootstrap_admin("Owner")
    admin = service.authenticate(token["token"])
    repo = service.dispatch(admin, "repositories.create", {"name": "Source", "provider": "github", "external_name": "owner/repo"})
    queued = service.dispatch(admin, "rfcs.enroll", {"repo_id": repo["id"], "source": provider.ref.to_dict(), "scope": "Engine"})
    service.process_pending()
    rfc_id = service.dispatch(admin, "operations.get", {"operation_id": queued["operation_id"]})["result"]["rfc_id"]
    return service, admin, repo, provider, rfc_id


def apply(service, actor, rfc_id, *, body=None, changes=None, proposal_id="reviewed-proposal"):
    baseline = service.dispatch(actor, "rfcs.get", {"rfc_id": rfc_id})
    source_baseline = service._chat_source_baseline(actor, rfc_id, baseline["revision"])
    candidate = {"title": baseline["title"], "body": body or baseline["body"] + "\nReviewed design.\n",
                 "plan_changes": changes or [], "base_revision": baseline["revision"],
                 "content_digest": baseline["content_digest"], "draft_digest": "", **source_baseline}
    with service.store.transaction() as con:
        row = service._rfc(con, actor, rfc_id)
        return service._apply_chat_proposal(con, actor, row, candidate, proposal_id, "Approve reviewed design")


def test_source_candidate_saved_then_written_and_status_is_compact(tmp_path):
    service, admin, _, provider, rfc_id = setup(tmp_path)
    reviewed = apply(service, admin, rfc_id)
    assert reviewed["body"].endswith("Reviewed design.\n")
    assert provider.source["body"] == BODY
    assert reviewed["source_update"]["status"] == "pending"
    assert reviewed["operation"]["kind"] == "rfcs.update_source"
    assert service.process_pending()[0]["status"] == "succeeded"
    detail = service.dispatch(admin, "rfcs.get", {"rfc_id": rfc_id, "view": "detail"})
    assert detail["source_update"]["status"] == "synced"
    assert provider.source["body"] == reviewed["body"]
    assert provider.writes == 1
    for exposed in (detail["source_update"], reviewed["operation"]):
        assert not {"payload", "credential_id", "write_started"} & exposed.keys()
    assert service.store.one("SELECT body FROM source_snapshots WHERE rfc_id=? ORDER BY id DESC", (rfc_id,))["body"] == reviewed["body"]


def test_conflict_retains_reviewed_content_and_sync_observes_prs(tmp_path):
    service, admin, _, provider, rfc_id = setup(tmp_path)
    link = "https://github.com/owner/repo/pull/7"
    service.dispatch(admin, "rfcs.work", {"rfc_id": rfc_id, "op": "update", "feature_id": "F1", "feature": {"links": [link]}, "reason": "Track implementation"})
    provider.items["7"] = {"source": SourceRef("github", "owner/repo", "pr", "7", link, host="github.com").to_dict(), "revision": "pr-v2", "state": "merged"}
    reviewed = apply(service, admin, rfc_id)
    provider.source.update(body=BODY + "\nConcurrent source edit.\n", revision="upstream-new")
    assert service.process_pending()[0]["status"] == "failed"
    view = service.dispatch(admin, "rfcs.get", {"rfc_id": rfc_id})
    assert view["source_update"]["status"] == "conflict"
    assert view["source_update"]["can_retry"] is False
    with pytest.raises(RFCError, match="fresh proposal"):
        service.dispatch(admin, "operations.retry", {"operation_id": reviewed["operation_id"]})
    service.dispatch(admin, "rfcs.sync", {"rfc_id": rfc_id})
    assert service.process_pending()[0]["status"] == "succeeded"
    observed = service.dispatch(admin, "rfcs.get", {"rfc_id": rfc_id})
    assert observed["body"] == reviewed["body"]
    assert observed["observations"][link]["state"] == "merged"
    assert observed["features"][0]["implementation"] == "implemented"
    assert provider.writes == 0
    baseline = service._chat_source_baseline(admin, rfc_id, observed["revision"])
    assert baseline["source_conflict"] is True
    assert baseline["source_body"] == provider.source["body"]
    reconciled = apply(service, admin, rfc_id, body=reviewed["body"] + "\nReconciled after full source review.\n", proposal_id="fresh-reviewed-reconciliation")
    assert service.process_pending()[0]["status"] == "succeeded"
    assert provider.source["body"] == reconciled["body"]
    assert provider.writes == 1


def test_ambiguous_write_is_recovered_after_restart_without_duplicate(tmp_path):
    service, admin, _, provider, rfc_id = setup(tmp_path)
    reviewed = apply(service, admin, rfc_id)
    provider.timeout = True
    assert service.process_pending()[0]["status"] == "uncertain"
    restarted = RFCService(tmp_path / "state", {"github": provider})
    restarted.dispatch(admin, "operations.retry", {"operation_id": reviewed["operation_id"]})
    result = restarted.process_pending()[0]
    assert result["status"] == "succeeded" and result["result"]["recovered"] is True
    assert provider.writes == 1
    assert restarted.dispatch(admin, "rfcs.get", {"rfc_id": rfc_id})["body"] == reviewed["body"]


def test_expired_source_write_lease_recovers_readback(tmp_path):
    service, admin, _, provider, rfc_id = setup(tmp_path)
    reviewed = apply(service, admin, rfc_id)
    operation = service.store.one("SELECT * FROM operations WHERE id=?", (reviewed["operation_id"],))
    payload = json.loads(operation["payload"])
    payload["write_started"] = True
    provider.source.update(body=reviewed["body"], title=reviewed["title"], revision="applied-before-crash")
    with service.store.transaction() as con:
        con.execute("UPDATE operations SET status='running',worker='dead-worker',lease_until=0,payload=? WHERE id=?", (json.dumps(payload), operation["id"]))
    assert service.process_pending()[0]["status"] == "succeeded"
    assert provider.writes == 0


def test_uncertain_unapplied_write_only_reads_and_never_repeats_mutation(tmp_path):
    service, admin, _, provider, rfc_id = setup(tmp_path)
    reviewed = apply(service, admin, rfc_id)
    with service.store.transaction() as con:
        row = con.execute("SELECT payload FROM operations WHERE id=?", (reviewed["operation_id"],)).fetchone()
        payload = json.loads(row["payload"])
        payload["write_started"] = True
        con.execute("UPDATE operations SET status='uncertain',payload=? WHERE id=?", (json.dumps(payload), reviewed["operation_id"]))
    service.dispatch(admin, "operations.retry", {"operation_id": reviewed["operation_id"]})
    assert service.process_pending()[0]["status"] == "uncertain"
    assert provider.writes == 0 and provider.source["body"] == BODY
    assert service.dispatch(admin, "rfcs.get", {"rfc_id": rfc_id})["body"] == reviewed["body"]


def test_authorization_revoked_after_approval_prevents_source_write(tmp_path):
    service, admin, repo, provider, rfc_id = setup(tmp_path)
    user = service.dispatch(admin, "users.create", {"name": "Maintainer"})
    issued = service.dispatch(admin, "tokens.create", {"user_id": user["id"]})
    service.dispatch(admin, "grants.set", {"repo_id": repo["id"], "user_id": user["id"], "role": "maintainer"})
    actor = service.authenticate(issued["token"])
    reviewed = apply(service, actor, rfc_id)
    service.dispatch(admin, "tokens.revoke", {"token_id": issued["token_id"]})
    assert service.process_pending()[0]["status"] == "failed"
    assert provider.writes == 0
    assert service.dispatch(admin, "rfcs.get", {"rfc_id": rfc_id})["body"] == reviewed["body"]


def test_draft_source_alias_cannot_bypass_registered_rfc_write_acl(tmp_path):
    service, admin, repo, provider, rfc_id = setup(tmp_path)
    user = service.dispatch(admin, "users.create", {"name": "Maintainer"})
    issued = service.dispatch(admin, "tokens.create", {"user_id": user["id"]})
    service.dispatch(admin, "grants.set", {"repo_id": repo["id"], "user_id": user["id"], "role": "maintainer"})
    service.dispatch(admin, "rfcs.acl", {"rfc_id": rfc_id, "restricted": True, "grants": {user["id"]: "reader"}})
    actor = service.authenticate(issued["token"])
    alias = service.dispatch(actor, "rfcs.draft", {"repo_id": repo["id"], "title": "Source RFC", "body": BODY, "source": provider.ref.to_dict()})
    with pytest.raises(RFCError) as denied:
        apply(service, actor, alias["id"])
    assert denied.value.status == 403
    assert provider.writes == 0
    assert service.dispatch(actor, "rfcs.get", {"rfc_id": alias["id"]})["body"] == BODY


def test_rfc_view_hides_acceptance_evidence_from_inaccessible_source(tmp_path):
    service, admin, repo, _, rfc_id = setup(tmp_path)
    user = service.dispatch(admin, "users.create", {"name": "Reader"})
    issued = service.dispatch(admin, "tokens.create", {"user_id": user["id"]})
    service.dispatch(admin, "grants.set", {"repo_id": repo["id"], "user_id": user["id"], "role": "reader"})
    private_ref = SourceRef("github", "owner/repo", "issue", "2", "https://github.com/owner/repo/issues/2", host="github.com")
    private = service.dispatch(admin, "rfcs.draft", {"repo_id": repo["id"], "title": "Private evidence", "body": BODY, "source": private_ref.to_dict()})
    service.dispatch(admin, "rfcs.acl", {"rfc_id": private["id"], "restricted": True, "grants": {}})
    criterion = service.dispatch(admin, "rfcs.get", {"rfc_id": rfc_id})["criteria"][0]
    service.dispatch(admin, "rfcs.decision", {"rfc_id": rfc_id, "criterion_id": criterion["id"], "verdict": "passing", "evidence": {
        "revision": "private-v1", "environment": "private environment", "result": "private result", "source": private_ref.to_dict()}})
    reader = service.authenticate(issued["token"])
    view = service.dispatch(reader, "rfcs.get", {"rfc_id": rfc_id})
    assert view["criteria"][0]["evidence"] == []
    assert "private result" not in json.dumps(view)
    assert service.dispatch(admin, "rfcs.get", {"rfc_id": rfc_id})["criteria"][0]["evidence"][0]["result"] == "private result"


def test_source_completion_merges_live_tracking_metadata(tmp_path):
    service, admin, _, provider, rfc_id = setup(tmp_path)
    reviewed = apply(service, admin, rfc_id)
    provider.on_write = lambda: service.dispatch(admin, "rfcs.work", {"rfc_id": rfc_id, "op": "claim", "feature_id": "F1", "owner": "Maintainer", "reason": "Confirmed owner"})
    assert service.process_pending()[0]["status"] == "succeeded"
    current = service.dispatch(admin, "rfcs.get", {"rfc_id": rfc_id})
    assert current["features"][0]["owner"] == "Owner"
    assert current["body"] == reviewed["body"]


def test_due_sync_queues_while_reviewed_source_update_pending(tmp_path):
    service, admin, _, _, rfc_id = setup(tmp_path)
    apply(service, admin, rfc_id)
    with service.store.transaction() as con:
        row = service._rfc(con, admin, rfc_id)
        model = json.loads(row["model"])
        model["freshness"]["verification"] = 0
        service._save(con, admin, row, model)
    assert len(service.sync_due()["queued"]) == 1
    assert service.sync_due()["queued"] == []


def test_pending_source_update_survives_earlier_sync_and_restart(tmp_path):
    service, admin, _, provider, rfc_id = setup(tmp_path)
    service.dispatch(admin, "rfcs.sync", {"rfc_id": rfc_id})
    reviewed = apply(service, admin, rfc_id)
    restarted = RFCService(tmp_path / "state", {"github": provider})
    first = restarted.process_pending(limit=1)[0]
    assert first["status"] == "succeeded"
    assert restarted.dispatch(admin, "rfcs.get", {"rfc_id": rfc_id})["body"] == reviewed["body"]
    assert provider.source["body"] == BODY
    assert restarted.process_pending(limit=1)[0]["status"] == "succeeded"
    assert provider.source["body"] == reviewed["body"]


def test_reviewed_prose_preserves_stable_plan_and_acceptance_history(tmp_path):
    service, admin, _, _, rfc_id = setup(tmp_path)
    with service.store.transaction() as con:
        row = service._rfc(con, admin, rfc_id)
        model = json.loads(row["model"])
        model["features"][0].update(state="in_progress", priority="high", decisions=[{"reason": "Keep the original decision"}])
        model["criteria"][0].update(verdict="passing", reason="Verified before edit", evidence=[{"version": "v1", "result": "passed"}])
        model["tombstones"] = ["F_removed"]
        model["decisions"] = [{"reason": "Historical acceptance decision"}]
        model["archived_criteria"] = [{"id": "old-criterion", "evidence": [{"result": "waived"}]}]
        before = service._save(con, admin, row, model)
    after = apply(service, admin, rfc_id)
    assert after["features"][0]["id"] == before["features"][0]["id"]
    assert after["features"][0]["state"] == "in_progress"
    assert after["features"][0]["priority"] == "high"
    assert after["features"][0]["decisions"] == before["features"][0]["decisions"]
    assert after["criteria"][0]["verdict"] == "pending"
    assert after["criteria"][0]["reason"] == "Verified before edit"
    assert after["criteria"][0]["evidence"][0]["version"] == "v1"
    assert after["criteria"][0]["evidence"][0]["stale"] is True
    assert after["tombstones"] == ["F_removed"]
    assert after["decisions"] == before["decisions"]
    assert after["archived_criteria"] == before["archived_criteria"]


def test_missing_snapshot_baseline_fetches_and_returns_conflict_review(tmp_path):
    service, admin, _, provider, rfc_id = setup(tmp_path)
    before = service.dispatch(admin, "rfcs.get", {"rfc_id": rfc_id})
    with service.store.transaction() as con:
        con.execute("DELETE FROM source_snapshots WHERE rfc_id=?", (rfc_id,))
    assert service._chat_source_baseline(admin, rfc_id, before["revision"]) == {
        "source_revision": "s1", "source_body": BODY, "source_title": "Source RFC", "source_conflict": False}
    with service.store.transaction() as con:
        con.execute("DELETE FROM source_snapshots WHERE rfc_id=?", (rfc_id,))
    provider.source.update(body=BODY + "External edit", revision="s2")
    conflict = service._chat_source_baseline(admin, rfc_id, before["revision"])
    assert conflict == {"source_revision": "s2", "source_body": BODY + "External edit", "source_title": "Source RFC", "source_conflict": True}


def test_known_provider_failure_allows_safe_guarded_retry(tmp_path):
    service, admin, _, provider, rfc_id = setup(tmp_path)
    reviewed = apply(service, admin, rfc_id)
    provider.failure = True
    assert service.process_pending()[0]["status"] == "failed"
    provider.failure = False
    service.dispatch(admin, "operations.retry", {"operation_id": reviewed["operation_id"]})
    assert service.process_pending()[0]["status"] == "succeeded"
    assert provider.source["body"] == reviewed["body"]


def test_conflicted_plan_only_update_fetches_fresh_source_without_sync(tmp_path):
    service, admin, _, provider, rfc_id = setup(tmp_path)
    reviewed = apply(service, admin, rfc_id, body=BODY, changes=[{"op": "update", "feature_id": "F1", "fields": {"priority": "high"}}])
    provider.source.update(title="Upstream changed title", revision="upstream-title")
    assert service.process_pending()[0]["status"] == "failed"
    current = service.dispatch(admin, "rfcs.get", {"rfc_id": rfc_id})
    baseline = service._chat_source_baseline(admin, rfc_id, current["revision"])
    assert baseline["source_revision"] == "upstream-title"
    assert baseline["source_title"] == "Upstream changed title"
    assert baseline["source_conflict"] is True
    assert current["body"] == reviewed["body"]


def test_draft_chat_save_has_no_external_operation(tmp_path):
    service, admin, repo, provider, _ = setup(tmp_path)
    draft = service.dispatch(admin, "rfcs.draft", {"repo_id": repo["id"], "title": "Draft", "body": BODY})
    saved = apply(service, admin, draft["id"])
    assert "operation_id" not in saved and "source_update" not in saved
    assert not service.store.all("SELECT id FROM operations WHERE rfc_id=?", (draft["id"],))
    assert provider.writes == 0


def test_local_source_title_and_body_match_exact_review(tmp_path):
    root = tmp_path / "documents"
    root.mkdir()
    path = root / "rfc.md"
    path.write_text(BODY)
    from infermatrix_copilot.rfc_service.providers import LocalProvider
    provider = LocalProvider({"docs": root})
    ref = SourceRef("local", "docs", "markdown", "rfc.md", path="rfc.md")
    before = provider.get_source(ref)
    changed = BODY.replace("# Source RFC", "# Updated RFC")
    result = provider.update_source(ref, changed, before["revision"], title="Updated RFC")
    assert result["body"] == changed and result["title"] == "Updated RFC"
    with pytest.raises(RFCError, match="Markdown heading"):
        provider.update_source(ref, changed, result["revision"], title="Unreviewed heading")
    assert path.read_text() == changed


@pytest.mark.parametrize("provider_name,kind", [("github", "issue"), ("github", "pr"), ("atomgit", "issue"), ("atomgit", "pr")])
def test_remote_source_updates_reviewed_title_and_body(provider_name, kind):
    from infermatrix_copilot.rfc_service.providers import AtomGitProvider, GitHubProvider
    host = provider_name + ".com"
    raw = {"number": "7", "title": "Before", "body": "Before body", "state": "open",
           "updated_at": "2026-10-05T00:00:00Z", "html_url": f"https://{host}/owner/repo/{'pull' if kind == 'pr' else 'issues'}/7"}
    after = {**raw, "title": "Reviewed title", "body": "Reviewed body", "updated_at": "2026-10-05T00:01:00Z"}
    responses, calls = [raw, raw, after, after], []
    def transport(method, url, headers, payload):
        calls.append((method, url, payload))
        return 200, {}, copy.deepcopy(responses.pop(0))
    provider = (GitHubProvider if provider_name == "github" else AtomGitProvider)(transport=transport)
    ref = SourceRef(provider_name, "owner/repo", kind, "7")
    revision = provider.get_source(ref)["revision"]
    result = provider.update_source(ref, "Reviewed body", revision, title="Reviewed title")
    assert result["body"] == "Reviewed body" and result["title"] == "Reviewed title"
    assert calls[2][0] == "PATCH" and calls[2][2]["title"] == "Reviewed title"
    assert calls[2][2]["body"] == "Reviewed body"
    if kind == "pr":
        assert "/pulls/7" in calls[2][1]


def test_successful_patch_with_failed_readback_has_uncertain_outcome():
    from infermatrix_copilot.rfc_service.providers import GitHubProvider
    raw = {"number": "7", "title": "RFC", "body": "Before", "state": "open", "html_url": "https://github.com/owner/repo/issues/7"}
    responses = [raw, raw, raw, (503, {}, None)]
    def transport(method, url, headers, payload):
        response = responses.pop(0)
        return response if isinstance(response, tuple) else (200, {}, response)
    provider = GitHubProvider(transport=transport)
    ref = SourceRef("github", "owner/repo", "issue", "7")
    revision = provider.get_source(ref)["revision"]
    with pytest.raises(ProviderError) as unknown:
        provider.update_source(ref, "Reviewed", revision, title="RFC")
    assert unknown.value.uncertain is True
