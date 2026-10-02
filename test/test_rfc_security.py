"""Adversarial authorization and recovery checks across RFC/source boundaries."""
from __future__ import annotations

import copy
import json

import pytest

from infermatrix_copilot.rfc_service.application import RFCService
from infermatrix_copilot.rfc_service.models import Principal, ProviderError, RFCError, SourceRef


SECRET = "confidential-rfc-detail-do-not-export"
PUBLIC = "# Public RFC\n\n### Engine\n\n#### F1. Public implementation\n\n## Acceptance criteria\n\n- Validate the public output.\n"


class Sources:
    def __init__(self):
        self.records = {}
        self.publications = {}
        self.reads = 0
        self.writes = 0
        self.before_read = None
        self.candidates = []
        self.fail_before_publish = False

    def publish(self, repository, title, body, operation_id, **kwargs):
        if self.fail_before_publish:
            raise ProviderError("Temporary provider failure")
        self.writes += 1
        key = str(len(self.records) + 1)
        source = SourceRef("github", repository, "issue", key,
                           f"https://github.com/{repository}/issues/{key}", host="github.com")
        self.records[key] = {"source": source.to_dict(), "title": title, "body": body,
                             "revision": "revision-" + key, "state": "open"}
        self.publications[operation_id] = source
        return source

    def find_publication(self, repository, operation_id):
        return self.publications.get(operation_id)

    def get_source(self, ref):
        self.reads += 1
        callback, self.before_read = self.before_read, None
        if callback:
            callback()
        return copy.deepcopy(self.records[ref.identifier])

    get_item = get_source

    def discover(self, repository, scope, since=""):
        return copy.deepcopy(self.candidates)


def workspace(tmp_path):
    provider = Sources()
    service = RFCService(tmp_path / "state", providers={"github": provider})
    admin = service.authenticate(service.bootstrap_admin("Administrator")["token"])
    repo = service.dispatch(admin, "repositories.create", {"name": "Repository", "provider": "github", "external_name": "owner/repo"})
    return service, admin, repo, provider


def test_service_settings_require_admin_and_cannot_expose_or_redirect_credentials(tmp_path):
    service, admin, repo, provider = workspace(tmp_path)
    contributor, _ = member(service, admin, repo)
    for action in ("service.settings", "service.configure"):
        with pytest.raises(RFCError) as denied:
            service.dispatch(contributor, action, {"sync_seconds": 300})
        assert denied.value.status == 403
    settings = service.dispatch(admin, "service.configure", {"sync_seconds": 300, "default_max_auto_additions": 2})
    assert settings["public_registration"] is False
    assert service.capabilities()["default_sync_seconds"] == 300
    fresh = service.dispatch(admin, "rfcs.draft", {"repo_id": repo["id"], "title": "Configured draft", "body": PUBLIC})
    assert fresh["max_auto_additions"] == 2
    provider.records["9"] = {"title": "Imported source", "body": PUBLIC, "revision": "source-9"}
    service.dispatch(admin, "rfcs.enroll", {"repo_id": repo["id"], "source": {
        "provider": "github", "repository": repo["external_name"], "kind": "issue", "identifier": "9"}})
    result = service.process_pending()[0]
    assert result["status"] == "succeeded"
    assert service.dispatch(admin, "rfcs.get", {"rfc_id": result["result"]["rfc_id"]})["max_auto_additions"] == 2
    for payload in ({"api_url": "https://attacker.test"}, {"token": "secret"}, {"public_registration": True}, {"sync_seconds": 1}):
        with pytest.raises(RFCError):
            service.dispatch(admin, "service.configure", payload)
    resumed = RFCService(service.store.root, providers={"github": provider})
    assert resumed.capabilities()["default_max_auto_additions"] == 2


def member(service, admin, repo, name="Contributor", role="contributor"):
    created = service.dispatch(admin, "users.create", {"name": name})
    token = service.dispatch(admin, "tokens.create", {"user_id": created["id"]})
    service.dispatch(admin, "grants.set", {"repo_id": repo["id"], "user_id": created["id"], "role": role})
    return service.authenticate(token["token"]), token


def make_rfc(service, actor, repo, title, body, key):
    draft = service.dispatch(actor, "rfcs.draft", {"repo_id": repo["id"], "title": title, "body": body, "scope": "Engine"})
    queued = service.dispatch(actor, "rfcs.publish", {"rfc_id": draft["id"], "content_digest": draft["content_digest"], "post": True, "idempotency_key": key})
    result = service.process_pending()
    assert result[0]["status"] == "succeeded", result
    return service.dispatch(actor, "rfcs.get", {"rfc_id": draft["id"]}), queued


def restricted_pair(tmp_path):
    service, admin, repo, provider = workspace(tmp_path)
    actor, token = member(service, admin, repo)
    hidden, _ = make_rfc(service, admin, repo, SECRET, PUBLIC + SECRET, "hidden-publication")
    visible, _ = make_rfc(service, admin, repo, "Public RFC", PUBLIC, "visible-publication")
    service.dispatch(admin, "rfcs.acl", {"rfc_id": hidden["id"], "restricted": True, "grants": {}})
    return service, admin, repo, provider, actor, hidden, visible


@pytest.mark.parametrize("minimal", [False, True])
def test_source_preview_cannot_bypass_registered_restricted_rfc(tmp_path, minimal):
    service, admin, repo, provider, actor, hidden, visible = restricted_pair(tmp_path)
    source = hidden["source"] if not minimal else {
        "provider": "github", "kind": "issue", "identifier": hidden["source"]["identifier"]}
    before = provider.reads
    with pytest.raises(RFCError) as exc:
        service.dispatch(actor, "sources.preview", {"repo_id": repo["id"], "source": source})
    assert exc.value.status == 403
    assert SECRET not in str(exc.value)
    assert provider.reads == before  # the bot must not read on the user's behalf


def test_preview_rechecks_rfc_acl_after_provider_io(tmp_path):
    service, admin, repo, provider, actor, hidden, visible = restricted_pair(tmp_path)
    service.dispatch(admin, "rfcs.acl", {"rfc_id": hidden["id"], "restricted": False})
    provider.before_read = lambda: service.dispatch(admin, "rfcs.acl", {
        "rfc_id": hidden["id"], "restricted": True, "grants": {}})
    with pytest.raises(RFCError) as exc:
        service.dispatch(actor, "sources.preview", {"repo_id": repo["id"], "source": hidden["source"]})
    assert exc.value.status == 403
    assert SECRET not in str(exc.value)


def test_source_preview_cannot_use_second_repository_alias_to_escape_acl(tmp_path):
    service, admin, repo, provider, actor, hidden, visible = restricted_pair(tmp_path)
    try:
        alias = service.dispatch(admin, "repositories.create", {
            "name": "Another configured alias", "provider": "github", "external_name": "owner/repo"})
    except RFCError as exc:
        assert exc.status == 409  # rejecting duplicate upstream identity is also safe
        return
    service.dispatch(admin, "grants.set", {"repo_id": alias["id"], "user_id": actor.user_id, "role": "contributor"})
    with pytest.raises(RFCError) as exc:
        service.dispatch(actor, "sources.preview", {"repo_id": alias["id"], "source": hidden["source"]})
    assert exc.value.status == 403


def test_queued_enrollment_cannot_extract_restricted_source_using_an_alias(tmp_path):
    service, admin, repo, provider, actor, hidden, visible = restricted_pair(tmp_path)
    alias = service.dispatch(admin, "repositories.create", {
        "name": "Enrollment alias", "provider": "github", "external_name": "owner/repo"})
    service.dispatch(admin, "grants.set", {"repo_id": alias["id"], "user_id": actor.user_id, "role": "maintainer"})
    before = provider.reads
    queued = service.dispatch(actor, "rfcs.enroll", {"repo_id": alias["id"], "source": hidden["source"]})
    result = service.process_pending()
    assert result[0]["status"] == "failed"
    assert provider.reads == before
    assert SECRET not in json.dumps(service.dispatch(actor, "operations.get", {"operation_id": queued["operation_id"]}))
    assert service.dispatch(actor, "rfcs.list", {"repo_id": alias["id"]})["rfcs"] == []


def test_related_observations_do_not_export_another_rfcs_restricted_body(tmp_path):
    service, admin, repo, provider, actor, hidden, visible = restricted_pair(tmp_path)
    service.dispatch(admin, "rfcs.work", {"rfc_id": visible["id"], "feature_id": "F1",
                                         "feature": {"links": [hidden["source"]["url"]]}})
    service.dispatch(admin, "rfcs.sync", {"rfc_id": visible["id"]})
    result = service.process_pending()
    assert result[0]["status"] == "succeeded", result
    for action in ("rfcs.get", "rfcs.export", "rfcs.list"):
        result = service.dispatch(actor, action, {"rfc_id": visible["id"]})
        assert SECRET not in json.dumps(result), action


def test_compact_status_and_suggestion_pages_filter_before_counting_and_search(tmp_path):
    service, admin, repo, provider, actor, hidden, visible = restricted_pair(tmp_path)
    model = json.loads(service.store.one("SELECT model FROM rfcs WHERE id=?", (visible["id"],))["model"])
    # Imported history can retain a reference whose RFC access was narrowed later.
    model["suggestions"] = [{"id": "hidden", "status": "proposed", "feature": {"title": SECRET},
        "evidence": {"source": hidden["source"]}},
        {"id": "allowed-one", "status": "proposed", "feature": {"title": "Allowed first work"}},
        {"id": "allowed-two", "status": "proposed", "feature": {"title": "Allowed second work"}}]
    with service.store.transaction() as con:
        con.execute("UPDATE rfcs SET model=? WHERE id=?", (json.dumps(model), visible["id"]))
    compact = service.dispatch(actor, "rfcs.status", {"rfc_id": visible["id"]})
    assert "body" not in compact and "suggestions" not in compact
    assert compact["suggestion_counts"] == {"proposed": 2} and compact["suggestions_total"] == 2
    assert SECRET not in json.dumps(compact)
    first = service.dispatch(actor, "rfcs.suggestions", {"rfc_id": visible["id"], "limit": 1})
    second = service.dispatch(actor, "rfcs.suggestions", {"rfc_id": visible["id"], "limit": 1, "offset": 1})
    assert first["total"] == second["total"] == 2
    assert first["suggestions"][0]["id"] == "allowed-one" and second["suggestions"][0]["id"] == "allowed-two"
    assert service.dispatch(actor, "rfcs.suggestions", {"rfc_id": visible["id"], "query": SECRET})["total"] == 0
    for action in ("rfcs.status", "rfcs.suggestions"):
        with pytest.raises(RFCError) as denied:
            service.dispatch(actor, action, {"rfc_id": hidden["id"]})
        assert denied.value.status == 403
    for options in ({"limit": 0}, {"limit": 101}, {"offset": -1}, {"offset": True}):
        with pytest.raises(RFCError):
            service.dispatch(actor, "rfcs.suggestions", {"rfc_id": visible["id"], **options})


@pytest.mark.parametrize("auto_add", [False, True])
def test_related_discovery_does_not_copy_a_restricted_rfcs_title(tmp_path, auto_add):
    service, admin, repo, provider, actor, hidden, visible = restricted_pair(tmp_path)
    visible = service.dispatch(admin, "rfcs.update", {"rfc_id": visible["id"],
        "expected_revision": visible["revision"], "auto_add": auto_add, "reason": "Select discovery policy"})
    provider.candidates = [{"source": hidden["source"], "url": hidden["source"]["url"],
        "title": SECRET, "body": visible["source"]["url"], "track": "Engine", "within_scope": True}]
    service.dispatch(admin, "rfcs.sync", {"rfc_id": visible["id"]})
    result = service.process_pending()
    assert result[0]["status"] == "succeeded", result
    assert SECRET not in json.dumps(service.dispatch(actor, "rfcs.get", {"rfc_id": visible["id"]}))


def test_discovery_cannot_copy_a_restricted_rfc_through_another_repository_alias(tmp_path):
    service, admin, repo, provider, actor, hidden, visible = restricted_pair(tmp_path)
    alias = service.dispatch(admin, "repositories.create", {
        "name": "Discovery alias", "provider": "github", "external_name": "owner/repo"})
    service.dispatch(admin, "grants.set", {"repo_id": alias["id"], "user_id": actor.user_id, "role": "contributor"})
    public_alias, _ = make_rfc(service, admin, alias, "Public alias RFC", PUBLIC, "alias-publication")
    provider.candidates = [{"source": hidden["source"], "url": hidden["source"]["url"],
        "title": SECRET, "body": public_alias["source"]["url"], "track": "Engine", "within_scope": True}]
    service.dispatch(admin, "rfcs.sync", {"rfc_id": public_alias["id"]})
    assert service.process_pending()[0]["status"] == "succeeded"
    assert SECRET not in json.dumps(service.dispatch(actor, "rfcs.get", {"rfc_id": public_alias["id"]}))


def test_discovery_does_not_leave_copied_rfc_details_after_its_acl_is_narrowed(tmp_path):
    service, admin, repo, provider, actor, hidden, visible = restricted_pair(tmp_path)
    service.dispatch(admin, "rfcs.acl", {"rfc_id": hidden["id"], "restricted": False})
    provider.candidates = [{"source": hidden["source"], "url": hidden["source"]["url"],
        "title": SECRET, "body": visible["source"]["url"], "track": "Engine", "within_scope": True}]
    service.dispatch(admin, "rfcs.sync", {"rfc_id": visible["id"]})
    assert service.process_pending()[0]["status"] == "succeeded"
    service.dispatch(admin, "rfcs.acl", {"rfc_id": hidden["id"], "restricted": True, "grants": {}})
    assert SECRET not in json.dumps(service.dispatch(actor, "rfcs.get", {"rfc_id": visible["id"]}))


def test_local_discovery_obeys_physical_source_acl_across_distinct_alias_names(tmp_path):
    from infermatrix_copilot.rfc_service.providers import LocalProvider

    checkout = tmp_path / "checkout"
    checkout.mkdir()
    service = RFCService(tmp_path / "state", providers={"local": LocalProvider({})}, roots=[checkout])
    admin = service.authenticate(service.bootstrap_admin("Administrator")["token"])
    repos = [service.dispatch(admin, "repositories.create", {
        "name": name, "external_name": name, "provider": "local", "root": str(checkout)})
        for name in ("private-alias", "public-alias")]
    body = "# " + SECRET + "\n\nRFC:rfcs/public.md\nScope: Engine\nTrack: Engine\n"
    records = []
    for repo, title, text, path in ((repos[0], SECRET, body, "rfcs/secret.md"),
                                  (repos[1], "Public RFC", PUBLIC, "rfcs/public.md")):
        draft = service.dispatch(admin, "rfcs.draft", {"repo_id": repo["id"], "title": title, "body": text, "scope": "Engine"})
        service.dispatch(admin, "rfcs.publish", {"rfc_id": draft["id"], "content_digest": draft["content_digest"],
            "post": True, "idempotency_key": path, "path": path})
        assert service.process_pending()[0]["status"] == "succeeded"
        records.append(service.dispatch(admin, "rfcs.get", {"rfc_id": draft["id"]}))
    service.dispatch(admin, "rfcs.acl", {"rfc_id": records[0]["id"], "restricted": True, "grants": {}})
    actor, token = member(service, admin, repos[1])
    service.dispatch(admin, "rfcs.sync", {"rfc_id": records[1]["id"]})
    assert service.process_pending()[0]["status"] == "succeeded"
    assert SECRET not in json.dumps(service.dispatch(actor, "rfcs.get", {"rfc_id": records[1]["id"]}))


def test_forged_admin_flag_does_not_widen_a_persisted_identity(tmp_path):
    service, admin, repo, provider = workspace(tmp_path)
    actor, token = member(service, admin, repo)
    forged = Principal(actor.user_id, "Administrator", admin=True, credential_id=actor.credential_id)
    with pytest.raises(RFCError) as exc:
        service.dispatch(forged, "users.create", {"name": "Injected administrator", "admin": True})
    assert exc.value.status == 403
    assert service.dispatch(actor, "me")["admin"] is False


def test_admin_recovery_preserves_original_idempotency_namespace(tmp_path):
    service, admin, repo, provider = workspace(tmp_path)
    actor, token = member(service, admin, repo, role="maintainer")
    provider.fail_before_publish = True
    draft = service.dispatch(actor, "rfcs.draft", {"repo_id": repo["id"], "title": "Recoverable", "body": PUBLIC})
    payload = {"rfc_id": draft["id"], "content_digest": draft["content_digest"], "post": True, "idempotency_key": "stable-intent"}
    queued = service.dispatch(actor, "rfcs.publish", payload)
    assert service.process_pending()[0]["status"] == "failed"
    service.dispatch(admin, "operations.retry", {"operation_id": queued["operation_id"]})
    retried = service.dispatch(actor, "rfcs.publish", payload)
    assert retried["operation_id"] == queued["operation_id"]
    assert len(service.dispatch(admin, "operations.list")["operations"]) == 1


def test_admin_recovery_does_not_collide_with_its_own_request_key(tmp_path):
    service, admin, repo, provider = workspace(tmp_path)
    actor, token = member(service, admin, repo, role="maintainer")
    provider.fail_before_publish = True
    queued = []
    for who, title in ((actor, "User intent"), (admin, "Admin intent")):
        draft = service.dispatch(who, "rfcs.draft", {"repo_id": repo["id"], "title": title, "body": PUBLIC})
        queued.append(service.dispatch(who, "rfcs.publish", {"rfc_id": draft["id"], "content_digest": draft["content_digest"], "post": True, "idempotency_key": "same-opaque-key"}))
    assert all(item["status"] == "failed" for item in service.process_pending())
    recovered = service.dispatch(admin, "operations.retry", {"operation_id": queued[0]["operation_id"]})
    assert recovered["operation_id"] == queued[0]["operation_id"]


def test_admin_can_reauthorize_failed_operation_after_original_token_revocation(tmp_path):
    service, admin, repo, provider = workspace(tmp_path)
    actor, token = member(service, admin, repo, role="maintainer")
    provider.fail_before_publish = True
    draft = service.dispatch(actor, "rfcs.draft", {"repo_id": repo["id"], "title": "Recover after revocation", "body": PUBLIC})
    queued = service.dispatch(actor, "rfcs.publish", {"rfc_id": draft["id"],
        "content_digest": draft["content_digest"], "post": True, "idempotency_key": "authorized-recovery"})
    assert service.process_pending()[0]["status"] == "failed"
    service.dispatch(admin, "tokens.revoke", {"token_id": token["token_id"]})
    service.dispatch(admin, "operations.retry", {"operation_id": queued["operation_id"]})
    provider.fail_before_publish = False
    assert service.process_pending()[0]["status"] == "succeeded"
    operation = service.store.one("SELECT actor,credential_id FROM operations WHERE id=?", (queued["operation_id"],))
    assert operation["actor"] == actor.user_id
    assert operation["credential_id"] == admin.credential_id


@pytest.mark.parametrize("change", [{"title": "A newly reviewed title"}, {"scope": "A newly reviewed scope"}])
def test_publication_binds_title_and_tracking_revision_to_its_preview(tmp_path, change):
    service, admin, repo, provider = workspace(tmp_path)
    preview = service.dispatch(admin, "rfcs.draft", {"repo_id": repo["id"], "title": "Original title", "body": PUBLIC})
    current = service.dispatch(admin, "rfcs.update", {
        "rfc_id": preview["id"], "expected_revision": preview["revision"], **change})
    assert current["revision"] != preview["revision"]
    with pytest.raises(RFCError) as exc:
        service.dispatch(admin, "rfcs.publish", {"rfc_id": preview["id"],
            "content_digest": preview["content_digest"], "expected_revision": preview["revision"],
            "post": True, "idempotency_key": "stale-preview"})
    assert exc.value.code == "preview_mismatch"
    assert provider.writes == 0


def test_expired_delegated_tracking_is_visible_and_requires_fresh_enrollment(tmp_path):
    service, admin, repo, provider = workspace(tmp_path)
    renewable = service.dispatch(admin, "tokens.create", {"expires_days": 365})
    admin = service.authenticate(renewable["token"])
    actor, token = member(service, admin, repo, role="maintainer")
    rfc, queued = make_rfc(service, actor, repo, "Delegated tracking", PUBLIC, "delegate-publication")
    # Real providers append a recovery marker; it must not block reauthorization.
    provider.records[rfc["source"]["identifier"]]["body"] += "\n<!-- imrfc-operation:" + queued["operation_id"] + " -->\n"
    assert rfc["sync_status"] == "active"
    now = service.clock()
    service.clock = lambda: now + 31 * 86400
    status = service.dispatch(admin, "rfcs.get", {"rfc_id": rfc["id"]})
    assert status["sync_status"] == "requires_reauthorization"
    assert status["next_actions"]
    assert "enrollment" not in status
    assert service.sync_due() == {"queued": []}
    service.dispatch(admin, "rfcs.enroll", {"rfc_id": rfc["id"]})
    assert service.process_pending()[0]["status"] == "succeeded"
    assert service.dispatch(admin, "rfcs.get", {"rfc_id": rfc["id"]})["sync_status"] == "active"


def test_reenrollment_invalidates_acceptance_after_upstream_rfc_changes(tmp_path):
    service, admin, repo, provider = workspace(tmp_path)
    rfc, _ = make_rfc(service, admin, repo, "Reauthorized source", PUBLIC, "acceptance-publication")
    criterion_id = rfc["criteria"][0]["id"]
    rfc = service.dispatch(admin, "rfcs.decision", {"rfc_id": rfc["id"],
        "criterion_id": criterion_id, "verdict": "passing",
        "evidence": {"revision": "accepted-source-revision", "environment": "Linux test workload"}})
    assert rfc["criteria"][0]["verdict"] == "passing"
    provider.records[rfc["source"]["identifier"]]["body"] += "\n## Revised scope\n\nThe workload now requires a different delivery guarantee.\n"
    service.dispatch(admin, "rfcs.enroll", {"rfc_id": rfc["id"]})
    assert service.process_pending()[0]["status"] == "succeeded"
    current = service.dispatch(admin, "rfcs.get", {"rfc_id": rfc["id"]})
    assert current["criteria"][0]["verdict"] == "pending"
    assert current["criteria"][0]["evidence"][0]["stale"] is True
