"""Manual implementation facts and reversible roadmap view groups."""
import copy
import json

import pytest

from infermatrix_copilot.rfc_service.application import RFCService
from infermatrix_copilot.rfc_service.chat import apply_plan_changes, prepare_candidate
from infermatrix_copilot.rfc_service.drafts import parse
from infermatrix_copilot.rfc_service.models import RFCError, SourceRef
from infermatrix_copilot.rfc_service.store import encode


BODY = ("# RFC\n\n## Goals\n\nImprove the service.\n\n### Engine\n\n#### F1. Same name\n\n"
        "https://github.com/owner/repo/pull/9\n\n#### F2. Same name\n\nDepends on: F1\n\n"
        "### Models\n\n#### F3. Model support\n\nDepends on: F2\n\n"
        "## Acceptance criteria\n\n- Verify the output.\n")


class Provider:
    def __init__(self):
        self.source = {"title": "RFC", "body": BODY, "revision": "source-1"}
        self.item = {"state": "open", "revision": "pr-1"}

    def get_source(self, ref):
        return copy.deepcopy(self.source)

    def get_item(self, ref):
        return copy.deepcopy(self.item)

    def discover(self, repository, scope, since=""):
        return []


@pytest.fixture
def workspace(tmp_path):
    provider = Provider()
    service = RFCService(tmp_path / "state", {"github": provider})
    token = service.bootstrap_admin("Owner")
    admin = service.authenticate(token["token"])
    repo = service.dispatch(admin, "repositories.create", {"name": "Repo", "provider": "github", "external_name": "owner/repo"})
    rfc = service.dispatch(admin, "rfcs.draft", {"repo_id": repo["id"], "title": "RFC", "body": BODY})
    return service, admin, repo, rfc, provider


def member(service, admin, repo, role="contributor"):
    user = service.dispatch(admin, "users.create", {"name": "User " + role})
    token = service.dispatch(admin, "tokens.create", {"user_id": user["id"]})
    service.dispatch(admin, "grants.set", {"repo_id": repo["id"], "user_id": user["id"], "role": role})
    return service.authenticate(token["token"]), token


def work(service, actor, rfc, **extra):
    return service.dispatch(actor, "rfcs.work", {"rfc_id": rfc["id"], "feature_id": "F1", "reason": "Verified manually", **extra})


def merge(service, actor, rfc, **extra):
    return service.dispatch(actor, "rfcs.graph", {"rfc_id": rfc["id"], "op": "merge", "feature_ids": ["F1", "F2"], "title": "Engine delivery", **extra})


def feature(rfc, identity="F1"):
    return next(f for f in rfc["features"] if f["id"] == identity)


def put_model(service, rfc, change):
    with service.store.transaction() as con:
        row = con.execute("SELECT model FROM rfcs WHERE id=?", (rfc["id"],)).fetchone()
        model = json.loads(row["model"])
        change(model)
        con.execute("UPDATE rfcs SET model=? WHERE id=?", (encode(model), rfc["id"]))


def test_manual_done_wins_open_pr_and_never_accepts_goal(workspace):
    service, admin, repo, rfc, _ = workspace
    contributor, _ = member(service, admin, repo)
    link = feature(rfc)["links"][0]
    put_model(service, rfc, lambda m: m.update(observations={link: {"kind": "pr", "state": "open"}}))
    result = work(service, contributor, rfc, op="mark_done", expected_revision=rfc["revision"])
    assert feature(result)["implementation"] == "implemented"
    assert feature(result)["implementation_override"]["actor"] == contributor.user_id
    assert feature(result)["implementation_override"]["reason"] == "Verified manually"
    assert feature(result)["acceptance"] == "pending" and not feature(result)["complete"]
    assert result["acceptance"] == "pending" and result["complete"] is False
    assert feature(result, "F2")["implementation"] == "planned"
    assert result["body"] == BODY
    assert service.store.one("SELECT COUNT(*) count FROM operations")["count"] == 0
    result = work(service, contributor, result, op="clear_done", expected_revision=result["revision"])
    assert "implementation_override" not in feature(result)
    assert feature(result)["state"] == "planned" and feature(result)["implementation"] == "in_progress"
    assert [entry["op"] for entry in feature(result)["implementation_history"]] == ["mark_done", "clear_done"]


def test_manual_state_and_groups_preserve_acceptance_evidence(workspace):
    service, admin, _, rfc, _ = workspace
    rfc = service.dispatch(admin, "rfcs.decision", {"rfc_id": rfc["id"], "criterion_id": rfc["criteria"][0]["id"], "verdict": "passing",
        "evidence": {"revision": "v1", "environment": "Linux"}})
    rfc = work(service, admin, rfc, op="update", feature={"state": "in_progress"})
    assert feature(rfc)["implementation_override"]["previous_state"] == "planned"
    rfc = work(service, admin, rfc, op="mark_done")
    rfc = merge(service, admin, rfc)
    assert rfc["criteria"][0]["verdict"] == "passing"
    assert rfc["criteria"][0]["evidence"][0]["stale"] is False
    cleared = work(service, admin, rfc, op="clear_done")
    assert feature(cleared)["state"] == "planned"
    assert len(feature(cleared)["implementation_history"]) == 3


def test_state_dropdown_uses_explicit_override_and_restores_initial_state(workspace):
    service, admin, _, rfc, _ = workspace
    put_model(service, rfc, lambda m: m.update(observations={feature(rfc)["links"][0]: {"kind": "pr", "state": "merged"}}))
    result = work(service, admin, rfc, op="update", feature={"state": "in_progress"})
    assert feature(result)["implementation"] == "in_progress"
    result = work(service, admin, result, op="clear_done")
    assert feature(result)["state"] == "planned" and feature(result)["implementation"] == "implemented"
    assert result["acceptance"] == "pending"


def test_manual_done_and_groups_survive_sync_editor_and_restart(workspace):
    service, admin, _, rfc, provider = workspace
    source = SourceRef("github", "owner/repo", "issue", "1").to_dict()
    with service.store.transaction() as con:
        con.execute("UPDATE rfcs SET source=?,enrolled=1 WHERE id=?", (encode(source), rfc["id"]))
    result = work(service, admin, rfc, op="mark_done")
    result = merge(service, admin, result)
    original_override = copy.deepcopy(feature(result)["implementation_override"])
    original_group = copy.deepcopy(result["node_groups"])
    provider.source["body"] += "\nUnrelated source note.\n"
    service.dispatch(admin, "rfcs.sync", {"rfc_id": rfc["id"]})
    assert service.process_pending()[0]["status"] == "succeeded"
    result = service.dispatch(admin, "rfcs.get", {"rfc_id": rfc["id"]})
    assert feature(result)["implementation"] == "implemented"
    assert feature(result)["implementation_override"] == original_override
    assert result["node_groups"] == original_group
    forged = copy.deepcopy(result["features"])
    forged[0]["implementation_override"] = {"state": "planned", "actor": "forged"}
    result = service.dispatch(admin, "rfcs.update", {"rfc_id": rfc["id"], "expected_revision": result["revision"],
        "body": result["body"] + "\nEditor note.\n", "features": forged, "reason": "Edit design only"})
    assert feature(result)["implementation_override"] == original_override
    resumed = RFCService(service.store.root, {"github": provider})
    result = resumed.dispatch(admin, "rfcs.get", {"rfc_id": rfc["id"], "view": "detail"})
    assert feature(result)["implementation_override"] == original_override
    assert result["node_groups"] == original_group


def test_graph_groups_are_view_only_reversible_and_rfc_local(workspace):
    service, admin, repo, rfc, _ = workspace
    contributor, _ = member(service, admin, repo)
    before = copy.deepcopy(rfc)
    result = merge(service, contributor, rfc, feature_ids=["F1", "F3"], expected_revision=rfc["revision"], view="detail")
    assert result["features"] == before["features"] and result["criteria"] == before["criteria"]
    assert result["body"] == before["body"] and result["revision"] != before["revision"]
    group = result["node_groups"][0]
    assert group["created_by"] == contributor.user_id and group["id"] not in {f["id"] for f in rfc["features"]}
    assert len(result["features"]) == 3
    result = service.dispatch(contributor, "rfcs.graph", {"rfc_id": rfc["id"], "op": "rename", "group_id": group["id"], "title": "Cross-track delivery", "expected_revision": result["revision"]})
    assert result["node_groups"][0]["title"] == "Cross-track delivery"
    other = service.dispatch(admin, "rfcs.draft", {"repo_id": repo["id"], "title": "Other", "body": BODY})
    assert other["node_groups"] == []
    with pytest.raises(RFCError):
        service.dispatch(contributor, "rfcs.graph", {"rfc_id": other["id"], "op": "unmerge", "group_id": group["id"]})
    result = service.dispatch(contributor, "rfcs.graph", {"rfc_id": rfc["id"], "op": "unmerge", "group_id": group["id"], "expected_revision": result["revision"]})
    assert result["node_groups"] == [] and result["features"] == before["features"]
    assert [e["detail"]["op"] for e in reversed(service.dispatch(admin, "audit.list")["events"]) if e["action"] == "rfcs.graph"] == ["merge", "rename", "unmerge"]


@pytest.mark.parametrize("members", [["F1"], ["F1", "F1"], ["F1", "missing"], "F1,F2", ["F1", 2]])
def test_invalid_group_members_are_rejected(workspace, members):
    service, admin, _, rfc, _ = workspace
    with pytest.raises(RFCError): merge(service, admin, rfc, feature_ids=members)
    assert service.dispatch(admin, "rfcs.get", {"rfc_id": rfc["id"]})["revision"] == rfc["revision"]


def test_overlapping_and_dropped_members_are_rejected_without_task_loss(workspace):
    service, admin, _, rfc, _ = workspace
    result = merge(service, admin, rfc)
    with pytest.raises(RFCError) as conflict: merge(service, admin, result, feature_ids=["F2", "F3"])
    assert conflict.value.status == 409
    result = work(service, admin, result, op="drop", feature_id="F3")
    with pytest.raises(RFCError): merge(service, admin, result, feature_ids=["F1", "F3"])
    assert len(result["node_groups"]) == 1 and len(result["features"]) == 3


def test_dropped_group_member_releases_remaining_tasks_and_restoration_keeps_new_group(workspace):
    service, admin, _, rfc, _ = workspace
    rfc = merge(service, admin, rfc)
    old_id = rfc["node_groups"][0]["id"]
    rfc = work(service, admin, rfc, op="drop", feature_id="F2")
    assert rfc["node_groups"] == []
    rfc = merge(service, admin, rfc, feature_ids=["F1", "F3"])
    new_id = rfc["node_groups"][0]["id"]
    assert new_id != old_id
    rfc = work(service, admin, rfc, op="restore", feature_id="F2")
    assert [group["id"] for group in rfc["node_groups"]] == [new_id]
    assert rfc["node_group_history"][0]["id"] == old_id
    assert rfc["node_group_history"][0]["end_reason"] == "member_removed"


def test_source_removed_group_member_releases_view_group_on_next_save(workspace):
    service, admin, _, rfc, _ = workspace
    rfc = merge(service, admin, rfc)
    rfc = service.dispatch(admin, "rfcs.update", {"rfc_id": rfc["id"], "expected_revision": rfc["revision"],
        "body": BODY.replace("#### F2. Same name\n\nDepends on: F1\n\n", "").replace("Depends on: F2", "Depends on: F1")})
    assert rfc["node_groups"] == []
    assert merge(service, admin, rfc, feature_ids=["F1", "F3"])["node_groups"]


@pytest.mark.parametrize("action,payload", [
    ("rfcs.work", {"op": "mark_done", "feature_id": "F1", "reason": "Done"}),
    ("rfcs.graph", {"op": "merge", "feature_ids": ["F1", "F2"], "title": "Group"}),
])
def test_permissions_revocation_and_revision_guard(workspace, action, payload):
    service, admin, repo, rfc, _ = workspace
    reader, _ = member(service, admin, repo, "reader")
    with pytest.raises(RFCError) as denied: service.dispatch(reader, action, {"rfc_id": rfc["id"], **payload})
    assert denied.value.status == 403
    contributor, token = member(service, admin, repo)
    work(service, admin, rfc, op="mark_done")
    with pytest.raises(RFCError) as stale:
        service.dispatch(contributor, action, {"rfc_id": rfc["id"], "expected_revision": rfc["revision"], **payload})
    assert stale.value.status == 409
    service.dispatch(admin, "tokens.revoke", {"token_id": token["token_id"]})
    with pytest.raises(RFCError) as revoked: service.dispatch(contributor, action, {"rfc_id": rfc["id"], **payload})
    assert revoked.value.status == 401
    restricted = service.dispatch(admin, "rfcs.draft", {"repo_id": repo["id"], "title": "Restricted", "body": BODY})
    service.dispatch(admin, "rfcs.acl", {"rfc_id": restricted["id"], "restricted": True, "grants": {}})
    with pytest.raises(RFCError): service.dispatch(reader, action, {"rfc_id": restricted["id"], **payload})


@pytest.mark.parametrize("revocation", ["grant", "rfc", "user"])
def test_current_authority_is_required_for_manual_marks_and_groups(workspace, revocation):
    service, admin, repo, rfc, _ = workspace
    contributor, _ = member(service, admin, repo)
    if revocation == "grant":
        service.dispatch(admin, "grants.set", {"repo_id": repo["id"], "user_id": contributor.user_id, "role": "reader"})
    elif revocation == "rfc":
        service.dispatch(admin, "rfcs.acl", {"rfc_id": rfc["id"], "restricted": True, "grants": {}})
    else:
        service.dispatch(admin, "users.update", {"user_id": contributor.user_id, "enabled": False})
    for action, payload in (("rfcs.work", {"op": "mark_done", "feature_id": "F1", "reason": "Done"}),
                            ("rfcs.graph", {"feature_ids": ["F1", "F2"], "title": "Group"})):
        with pytest.raises(RFCError): service.dispatch(contributor, action, {"rfc_id": rfc["id"], **payload})
    assert service.dispatch(admin, "rfcs.get", {"rfc_id": rfc["id"]})["revision"] == rfc["revision"]


def test_group_and_manual_operations_cannot_cross_repository_grants(workspace):
    service, admin, repo, _, _ = workspace
    contributor, _ = member(service, admin, repo)
    other_repo = service.dispatch(admin, "repositories.create", {"name": "Private", "provider": "github", "external_name": "owner/private"})
    other_rfc = service.dispatch(admin, "rfcs.draft", {"repo_id": other_repo["id"], "title": "Private", "body": BODY})
    with pytest.raises(RFCError): work(service, contributor, other_rfc, op="mark_done")
    with pytest.raises(RFCError): merge(service, contributor, other_rfc)


def test_inaccessible_group_and_manual_task_do_not_leak_source(workspace):
    service, admin, repo, rfc, _ = workspace
    contributor, _ = member(service, admin, repo)
    hidden_source = SourceRef("github", "owner/repo", "issue", "2").to_dict()
    hidden = service.dispatch(admin, "rfcs.draft", {"repo_id": repo["id"], "title": "Secret", "body": BODY, "source": hidden_source})
    service.dispatch(admin, "rfcs.acl", {"rfc_id": hidden["id"], "restricted": True, "grants": {}})
    put_model(service, rfc, lambda model: next(f for f in model["features"] if f["id"] == "F2").update(auto_source=hidden_source))
    result = merge(service, admin, rfc, title="Secret group title")
    group_id = result["node_groups"][0]["id"]
    for action in ("rfcs.get", "rfcs.status", "rfcs.export"):
        result = service.dispatch(contributor, action, {"rfc_id": rfc["id"], "view": "detail"})
        assert group_id not in json.dumps(result) and "Secret group title" not in json.dumps(result)
    for payload in ({"op": "unmerge", "group_id": group_id}, {"op": "merge", "feature_ids": ["F1", "F2"], "title": "Forbidden"}):
        with pytest.raises(RFCError): service.dispatch(contributor, "rfcs.graph", {"rfc_id": rfc["id"], **payload})
    with pytest.raises(RFCError) as denied: work(service, contributor, rfc, op="mark_done", feature_id="F2")
    assert denied.value.status == 403


def test_manual_fact_proposals_are_rejected_and_design_proposals_preserve_history(workspace):
    service, admin, _, rfc, _ = workspace
    rfc = work(service, admin, rfc, op="mark_done")
    prior = feature(rfc)["implementation_override"]
    model = json.loads(service.store.one("SELECT model FROM rfcs WHERE id=?", (rfc["id"],))["model"])
    changed = apply_plan_changes(parse(BODY, model), [{"op": "update", "feature_id": "F1", "fields": {"owner": "Reviewer"}}], previous=model)
    assert changed["features"][0]["implementation_override"] == prior
    assert changed["features"][0]["implementation_history"] == feature(rfc)["implementation_history"]
    row = dict(service.store.one("SELECT * FROM rfcs WHERE id=?", (rfc["id"],)))
    for field in ("state", "implementation_override", "implementation_history"):
        with pytest.raises(RFCError):
            prepare_candidate(row, {"plan_changes": [{"op": "update", "feature_id": "F1", "fields": {field: "implemented"}}]})
    candidate = prepare_candidate(row, {"edits": [{"before": "Improve the service.", "after": "Improve its responsiveness."}], "plan_changes": [], "reason": "Clarify"})
    with service.store.transaction() as con:
        saved = service._apply_chat_proposal(con, admin, row, candidate, "proposal-test", "Reviewed design")
    assert feature(saved)["implementation_override"] == prior
    assert feature(saved)["implementation_history"] == feature(rfc)["implementation_history"]


def test_checkbox_parse_preserves_manual_implementation():
    body = "# RFC\n\n- [ ] Work item\n"
    previous = parse(body)
    previous["features"][0].update(state="implemented", implementation_override={"state": "implemented", "actor": "user", "reason": "Manual", "at": 1})
    assert parse(body + "\nMore context.\n", previous)["features"][0]["implementation_override"]["actor"] == "user"


def test_manual_reason_is_required_and_dropped_features_cannot_be_marked(workspace):
    service, admin, _, rfc, _ = workspace
    for op in ("mark_done", "update"):
        with pytest.raises(RFCError): work(service, admin, rfc, op=op, reason="", feature={"state": "implemented"})
    rfc = work(service, admin, rfc, op="drop")
    with pytest.raises(RFCError): work(service, admin, rfc, op="mark_done")
    with pytest.raises(RFCError): work(service, admin, rfc, op="clear_done")
    with pytest.raises(RFCError): work(service, admin, rfc, op="update", feature={"state": "implemented"})


def test_untrusted_feature_dictionaries_cannot_fabricate_manual_facts(workspace):
    service, admin, repo, rfc, _ = workspace
    forged = {"id": "Fake", "title": "Fake", "implementation_override": {"state": "implemented", "actor": "forged"},
              "implementation_history": [{"actor": "forged"}],
              "overrides": {"implementation_override": {"state": "implemented", "actor": "nested"}}}
    draft = service.dispatch(admin, "rfcs.draft", {"repo_id": repo["id"], "title": "Untrusted", "body": "# Empty", "features": [forged]})
    added = work(service, admin, rfc, op="add", feature_id="Fake", feature=forged)
    for result in (draft, added):
        f = feature(result, "Fake")
        assert "implementation_override" not in f and "implementation_history" not in f
        assert f["overrides"].get("implementation_override") is None
        assert parse(result["body"], result)["features"][-1].get("implementation_override") is None


def test_sdk_work_and_graph_share_application_permissions(workspace):
    from infermatrix_copilot.sdk.v1.rfc import RFCClient
    service, admin, repo, rfc, _ = workspace
    token = service.dispatch(admin, "tokens.create", {})
    client = RFCClient(state_dir=service.store.root, token=token["token"])
    client._service = service
    marked = client.work(rfc["id"], op="mark_done", feature_id="F1", reason="Confirmed by SDK", expected_revision=rfc["revision"])
    assert feature(marked)["implementation"] == "implemented"
    grouped = client.graph(rfc["id"], op="merge", feature_ids=["F1", "F2"], title="SDK group", expected_revision=marked["revision"])
    assert grouped["node_groups"][0]["title"] == "SDK group"
