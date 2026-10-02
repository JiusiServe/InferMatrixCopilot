"""Application invariants through authenticated, concurrent lifecycle operations."""
import copy
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import pytest

from infermatrix_copilot.rfc_service.application import RFCService, build_service
from infermatrix_copilot.rfc_service.drafts import parse
from infermatrix_copilot.rfc_service.models import ProviderError, RFCError, SourceRef

BODY = "# RFC\n\n### Engine\n\n#### F1. Implement\n\n## Acceptance criteria\n\n### Service\n\n- Verify the output.\n"


class Provider:
    def __init__(self):
        self.sources = {}
        self.calls = 0
        self.candidates = []
        self.items = {}
        self.uncertain_once = False
        self.lock = threading.Lock()

    def publish(self, repository, title, body, operation_id, **kwargs):
        with self.lock:
            self.calls += 1
            ref = SourceRef("github", repository, "issue", "1", f"https://github.com/{repository}/issues/1", host="github.com")
            self.sources[operation_id] = {"source": ref.to_dict(), "title": title, "body": body, "revision": "source-v1"}
            if self.uncertain_once:
                self.uncertain_once = False
                raise ProviderError("Timed out after publication", uncertain=True)
            return ref

    def find_publication(self, repository, operation_id):
        return SourceRef.from_dict(self.sources[operation_id]["source"]) if operation_id in self.sources else None

    def get_source(self, ref):
        return copy.deepcopy(next(s for s in self.sources.values() if s["source"]["identifier"] == ref.identifier))

    def get_item(self, ref):
        return copy.deepcopy(self.items[ref.identifier])

    def discover(self, repository, scope, since=""):
        return copy.deepcopy(self.candidates)


def setup(tmp_path, provider=None):
    provider = provider or Provider()
    service = RFCService(tmp_path / "state", {"github": provider})
    issued = service.bootstrap_admin("Owner")
    admin = service.authenticate(issued["token"])
    repo = service.dispatch(admin, "repositories.create", {"name": "Any repo", "provider": "github", "external_name": "owner/repo"})
    return service, admin, repo, provider


def user(service, admin, repo, name, role):
    u = service.dispatch(admin, "users.create", {"name": name})
    issued = service.dispatch(admin, "tokens.create", {"user_id": u["id"]})
    service.dispatch(admin, "grants.set", {"repo_id": repo["id"], "user_id": u["id"], "role": role})
    return service.authenticate(issued["token"]), issued


def drafted(service, actor, repo):
    return service.dispatch(actor, "rfcs.draft", {"repo_id": repo["id"], "title": "Portable", "body": BODY})


def publish(service, actor, rfc, key="publication"):
    return service.dispatch(actor, "rfcs.publish", {"rfc_id": rfc["id"], "content_digest": rfc["content_digest"], "post": True, "idempotency_key": key})


def test_named_tokens_hashes_expiry_and_revoked_sessions(tmp_path):
    service, admin, repo, _ = setup(tmp_path)
    with pytest.raises(RFCError):
        service.bootstrap_admin("Second")
    reader, issued = user(service, admin, repo, "Alice", "reader")
    cookie, _ = service.create_session(issued["token"])
    stored = service.store.one("SELECT digest FROM tokens WHERE id=?", (issued["token_id"],))["digest"]
    assert stored != issued["token"] and issued["token"] not in service.store.path.read_bytes().decode("latin1")
    assert service.authenticate_session(cookie).user_id == reader.user_id
    service.dispatch(admin, "tokens.revoke", {"token_id": issued["token_id"]})
    with pytest.raises(RFCError) as denied:
        service.authenticate_session(cookie)
    assert denied.value.status == 401
    with pytest.raises(RFCError):
        service.dispatch(reader, "rfcs.list")


def test_all_projections_obey_repository_and_narrowed_rfc_acl(tmp_path):
    service, admin, repo, _ = setup(tmp_path)
    reader, _ = user(service, admin, repo, "Alice", "reader")
    another = service.dispatch(admin, "repositories.create", {"name": "Secret", "provider": "github", "external_name": "owner/secret"})
    visible, hidden = drafted(service, admin, repo), drafted(service, admin, another)
    restricted = drafted(service, admin, repo)
    service.dispatch(admin, "rfcs.acl", {"rfc_id": restricted["id"], "restricted": True, "grants": {}})
    assert visible["features"][0]["id"] == hidden["features"][0]["id"] == "F1"
    assert [r["id"] for r in service.dispatch(reader, "rfcs.list")["rfcs"]] == [visible["id"]]
    assert [r["id"] for r in service.dispatch(reader, "repositories.list")["repositories"]] == [repo["id"]]
    for action in ("rfcs.get", "rfcs.export", "rfcs.next"):
        for denied in (hidden, restricted):
            with pytest.raises(RFCError) as exc:
                service.dispatch(reader, action, {"rfc_id": denied["id"]})
            assert exc.value.status == 403
    with pytest.raises(RFCError):
        service.dispatch(reader, "rfcs.work", {"rfc_id": visible["id"], "op": "claim", "feature_id": "F1", "reason": "Claim"})
    with pytest.raises(RFCError):
        service.dispatch(admin, "rfcs.acl", {"rfc_id": visible["id"], "grants": {reader.user_id: "maintainer"}})
    queued = publish(service, admin, restricted)
    with pytest.raises(RFCError):
        service.dispatch(reader, "operations.get", {"operation_id": queued["operation_id"]})
    assert all(e["rfc_id"] != restricted["id"] for e in service.dispatch(reader, "audit.list")["events"])


@pytest.mark.parametrize("revoke", ["grant", "token", "user", "rfc"])
def test_queued_external_write_rechecks_current_authority(tmp_path, revoke):
    service, admin, repo, provider = setup(tmp_path)
    maintainer, issued = user(service, admin, repo, "Publisher", "maintainer")
    rfc = drafted(service, maintainer, repo)
    operation = publish(service, maintainer, rfc)
    if revoke == "grant":
        service.dispatch(admin, "grants.set", {"repo_id": repo["id"], "user_id": maintainer.user_id, "role": ""})
    elif revoke == "token":
        service.dispatch(admin, "tokens.revoke", {"token_id": issued["token_id"]})
    elif revoke == "user":
        service.dispatch(admin, "users.update", {"user_id": maintainer.user_id, "enabled": False})
    else:
        service.dispatch(admin, "rfcs.acl", {"rfc_id": rfc["id"], "grants": {}, "restricted": True})
    result = service.process_pending()
    assert result[0]["status"] == "failed" and provider.calls == 0
    assert service.dispatch(admin, "operations.get", {"operation_id": operation["operation_id"]})["status"] == "failed"


def test_preview_binding_concurrent_workers_restart_and_uncertain_recovery(tmp_path):
    service, admin, repo, provider = setup(tmp_path)
    rfc = drafted(service, admin, repo)
    with pytest.raises(RFCError):
        service.dispatch(admin, "rfcs.publish", {"rfc_id": rfc["id"], "post": True, "content_digest": "wrong"})
    queued = publish(service, admin, rfc)
    assert publish(service, admin, rfc)["operation_id"] == queued["operation_id"]
    provider.uncertain_once = True
    with ThreadPoolExecutor(max_workers=2) as executor:
        result = list(executor.map(lambda _: service.process_pending(), range(2)))
    assert provider.calls == 1
    assert service.dispatch(admin, "operations.get", {"operation_id": queued["operation_id"]})["status"] == "uncertain"
    restarted = RFCService(tmp_path / "state", {"github": provider})
    assert restarted.writer_id == service.writer_id
    restarted.dispatch(admin, "operations.retry", {"operation_id": queued["operation_id"]})
    assert restarted.process_pending()[0]["status"] == "succeeded"
    assert provider.calls == 1
    assert publish(restarted, admin, rfc)["operation_id"] == queued["operation_id"]
    assert restarted.dispatch(admin, "rfcs.get", {"rfc_id": rfc["id"]})["enrolled"] is True


def test_draft_change_after_queue_prevents_publication(tmp_path):
    service, admin, repo, provider = setup(tmp_path)
    rfc = drafted(service, admin, repo)
    publish(service, admin, rfc)
    service.dispatch(admin, "rfcs.update", {"rfc_id": rfc["id"], "expected_revision": rfc["revision"], "body": BODY + "new design"})
    assert service.process_pending()[0]["status"] == "failed"
    assert provider.calls == 0


def test_sync_deduplicates_delivery_reads_and_advances_only_successful_discovery_cursor(tmp_path):
    service, admin, repo, provider = setup(tmp_path)
    now = service.clock()
    service.clock = lambda: now
    rfc = drafted(service, admin, repo)
    link = "https://github.com/owner/repo/pull/2"
    for feature_id in ("F1", "F2"):
        service.dispatch(admin, "rfcs.work", {"rfc_id": rfc["id"], "op": "update" if feature_id == "F1" else "add",
            "reason": "Both work items share this implementation PR",
            "feature_id": feature_id, "feature": {"id": feature_id, "title": feature_id, "track": "Engine", "links": [link]}})
    rfc = service.dispatch(admin, "rfcs.get", {"rfc_id": rfc["id"]})
    publish(service, admin, rfc)
    assert service.process_pending()[0]["status"] == "succeeded"
    reads, cursors = [], []
    def get_item(ref):
        reads.append(ref.identifier)
        return {"state": "merged", "revision": "sha2"}
    def discover(repository, scope, since=""):
        cursors.append(since)
        return []
    provider.get_item, provider.discover = get_item, discover
    service.dispatch(admin, "rfcs.sync", {"rfc_id": rfc["id"]})
    assert service.process_pending()[0]["status"] == "succeeded"
    assert reads == ["2"] and cursors == [""]
    now += 3600
    def unavailable(repository, scope, since=""):
        cursors.append(since)
        raise ProviderError("Discovery unavailable")
    provider.discover = unavailable
    service.dispatch(admin, "rfcs.sync", {"rfc_id": rfc["id"]})
    assert service.process_pending()[0]["status"] == "failed"
    provider.discover = discover
    resumed = RFCService(service.store.root, {"github": provider}, clock=lambda: now)
    resumed.dispatch(admin, "rfcs.sync", {"rfc_id": rfc["id"]})
    assert resumed.process_pending()[0]["status"] == "succeeded"
    assert cursors[1] == cursors[2] == datetime.fromtimestamp(now - 3660, timezone.utc).isoformat()
    assert reads == ["2", "2", "2"]


def test_local_explicit_discovery_records_an_actual_relative_association(tmp_path):
    service = build_service(tmp_path / "local-state")
    admin = service.authenticate(service.bootstrap_admin("Owner")["token"])
    repo = service.dispatch(admin, "repositories.create", {"name": "Unconfigured repository", "provider": "local"})
    rfc = drafted(service, admin, repo)
    publish(service, admin, rfc)
    assert service.process_pending()[0]["status"] == "succeeded"
    rfc = service.dispatch(admin, "rfcs.get", {"rfc_id": rfc["id"]})
    root = Path(service.store.one("SELECT root FROM repositories WHERE id=?", (repo["id"],))["root"])
    (root / "implementation.md").write_text("# Implementation work\n\nRFC: " + rfc["source"]["path"] + "\nFeature: F1\n", encoding="utf-8")
    service.dispatch(admin, "rfcs.sync", {"rfc_id": rfc["id"]})
    result = service.process_pending()[0]
    assert result["status"] == "succeeded" and result["result"]["applied"] == 1
    current = service.dispatch(admin, "rfcs.get", {"rfc_id": rfc["id"]})
    assert "local:implementation.md" in current["features"][0]["links"]
    assert current["features"][0]["implementation"] != "implemented"
    service.dispatch(admin, "rfcs.sync", {"rfc_id": rfc["id"]})
    assert service.process_pending()[0]["result"]["applied"] == 0


def test_automatically_attached_work_requires_fresh_acceptance_evidence(tmp_path):
    service, admin, repo, provider = setup(tmp_path)
    rfc = drafted(service, admin, repo)
    publish(service, admin, rfc)
    assert service.process_pending()[0]["status"] == "succeeded"
    rfc = service.dispatch(admin, "rfcs.get", {"rfc_id": rfc["id"]})
    rfc = service.dispatch(admin, "rfcs.decision", {"rfc_id": rfc["id"], "criterion_id": rfc["criteria"][0]["id"],
        "verdict": "passing", "evidence": {"revision": "verified-initial-plan", "environment": "Linux"}})
    provider.candidates = [{"title": "Implementation PR", "body": rfc["source"]["url"],
        "url": "https://github.com/owner/repo/pull/2", "feature_id": "F1"}]
    provider.items["2"] = {"state": "merged", "revision": "new-implementation"}
    for _ in range(2):
        service.dispatch(admin, "rfcs.sync", {"rfc_id": rfc["id"]})
        assert service.process_pending()[0]["status"] == "succeeded"
    current = service.dispatch(admin, "rfcs.get", {"rfc_id": rfc["id"]})
    assert current["implementation"] == "implemented" and current["acceptance"] == "pending"
    assert current["criteria"][0]["evidence"][0]["stale"] is True


def test_merged_delivery_still_requires_evidence_and_revision_revalidation(tmp_path):
    service, admin, repo, provider = setup(tmp_path)
    rfc = drafted(service, admin, repo)
    links = ["https://github.com/owner/repo/pull/2", "https://github.com/owner/repo/pull/3"]
    rfc = service.dispatch(admin, "rfcs.work", {"rfc_id": rfc["id"], "feature_id": "F1", "feature": {"links": links}})
    publish(service, admin, rfc)
    assert service.process_pending()[0]["status"] == "succeeded"
    provider.items = {"2": {"state": "merged", "revision": "sha2"}, "3": {"state": "draft", "revision": "sha3"}}
    def sync():
        service.dispatch(admin, "rfcs.sync", {"rfc_id": rfc["id"]})
        assert service.process_pending()[0]["status"] == "succeeded"
        return service.dispatch(admin, "rfcs.get", {"rfc_id": rfc["id"]})
    status = sync()
    assert status["implementation"] == "partial" and not status["complete"]
    provider.items["3"]["state"] = "merged"
    status = sync()
    assert status["implementation"] == "implemented" and status["acceptance"] == "pending"
    criterion_id = status["criteria"][0]["id"]
    with pytest.raises(RFCError):
        service.dispatch(admin, "rfcs.decision", {"rfc_id": rfc["id"], "criterion_id": criterion_id, "verdict": "passing"})
    status = service.dispatch(admin, "rfcs.decision", {"rfc_id": rfc["id"], "criterion_id": criterion_id,
        "verdict": "passing", "evidence": {"revision": "sha3", "environment": "Linux/H100", "url": "https://example.test/report"}})
    assert status["complete"] is True
    provider.items["3"]["revision"] = "sha4"
    status = sync()
    assert status["acceptance"] == "pending" and status["criteria"][0]["evidence"][0]["stale"]


def test_bounded_discovery_cap_rejections_and_human_removals_survive_sync(tmp_path):
    service, admin, repo, provider = setup(tmp_path)
    rfc = drafted(service, admin, repo)
    rfc = service.dispatch(admin, "rfcs.update", {"rfc_id": rfc["id"], "expected_revision": rfc["revision"], "scope": "test scope"})
    publish(service, admin, rfc)
    service.process_pending()
    source_url = f"https://github.com/owner/repo/issues/1"
    provider.candidates = [{"title": f"Work {n}", "url": f"https://github.com/owner/repo/pull/{n}",
        "body": source_url, "track": "Engine", "within_scope": True} for n in range(10, 17)]
    def sync():
        service.dispatch(admin, "rfcs.sync", {"rfc_id": rfc["id"]})
        return service.process_pending()[0]
    assert sync()["result"]["applied"] == 5
    status = service.dispatch(admin, "rfcs.get", {"rfc_id": rfc["id"]})
    assert len(status["features"]) == 6
    pending = next(s for s in status["suggestions"] if s["status"] == "proposed")
    service.dispatch(admin, "rfcs.decision", {"rfc_id": rfc["id"], "kind": "suggestion", "suggestion_id": pending["id"], "verdict": "rejected"})
    drop = status["features"][1]["id"]
    service.dispatch(admin, "rfcs.work", {"rfc_id": rfc["id"], "op": "drop", "feature_id": drop})
    for n in range(10, 17):
        provider.items[str(n)] = {"state": "open", "revision": "sha"}
    assert sync()["result"]["applied"] == 0
    status = service.dispatch(admin, "rfcs.get", {"rfc_id": rfc["id"]})
    assert next(f for f in status["features"] if f["id"] == drop)["dropped"]
    assert next(s for s in status["suggestions"] if s["id"] == pending["id"])["status"] == "rejected"


def test_local_end_to_end_uses_any_repo_without_knowledge_adapter(tmp_path):
    service = build_service(tmp_path / "state")
    admin = service.authenticate(service.bootstrap_admin("Owner")["token"])
    repo = service.dispatch(admin, "repositories.create", {"name": "Arbitrary", "provider": "local"})
    rfc = drafted(service, admin, repo)
    queued = service.dispatch(admin, "rfcs.publish", {"rfc_id": rfc["id"], "post": True, "content_digest": rfc["content_digest"], "path": "rfcs/example.md"})
    assert service.process_pending()[0]["status"] == "succeeded"
    root = service.store.one("SELECT root FROM repositories WHERE id=?", (repo["id"],))["root"]
    from pathlib import Path
    assert BODY in (Path(root) / "rfcs/example.md").read_text()
    assert service.dispatch(admin, "operations.get", {"operation_id": queued["operation_id"]})["status"] == "succeeded"
    with pytest.raises(RFCError):
        service.dispatch(admin, "sources.preview", {"repo_id": repo["id"], "source": {"provider": "local", "path": "../outside.md"}})


def test_nested_acceptance_and_arbitrary_dependency_graph_import_preserves_prose():
    body = BODY + "\n#### Other_2. Integrate\n\nDepends on: F1, Missing3\n\n```mermaid\nF1 --> Other_2\n```\n"
    model = parse(body)
    assert model["criteria"] and model["features"][1]["depends_on"] == ["F1"]
    assert model["ambiguities"][0]["unknown_dependencies"] == ["Missing3"]
    assert body.startswith("# RFC")  # parse works on a sidecar; the caller retains prose.


def test_imported_explicit_milestone_is_delivery_fact_without_acceptance():
    from infermatrix_copilot.rfc_service.drafts import project
    body = BODY.replace("#### F1. Implement", "#### F1. Implement\n\n<!-- feature-status --> **Status: complete** — Suite selected; confirmed 2026-09-22")
    model = project(parse(body))
    assert model["implementation"] == "implemented"
    assert model["features"][0]["implementation_claim"]["provenance"] == "imported_explicit_milestone"
    assert model["acceptance"] == "pending" and not model["complete"]
