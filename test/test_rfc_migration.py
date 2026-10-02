"""Legacy migration preserves prose, permissions, uncertainty and rollback state."""
import json
import os
from pathlib import Path
import sqlite3

import pytest

from infermatrix_copilot.rfc_service.application import RFCService
from infermatrix_copilot.rfc_service.models import RFCError, SourceRef
from infermatrix_copilot.rfc_service.migration import migrate
from infermatrix_copilot.rfc_service import migration


BODY = ("# Existing RFC\r\n\r\n### Engine\r\n\r\n#### E7. Benchmark and harness\r\n"
        "https://github.com/legacy-owner/legacy-repo/pull/1\r\n"
        "https://github.com/legacy-owner/legacy-repo/pull/2\r\n\r\n"
        "### Model\r\n\r\n#### L6. Optional kernels\r\n\r\n"
        "## Acceptance criteria\r\n\r\n### Hardware\r\n\r\n- Validate latency.\r\n")


def workspace(tmp_path):
    service = RFCService(tmp_path / "state", {"github": object()})
    admin = service.authenticate(service.bootstrap_admin("Owner")["token"])
    repo = service.dispatch(admin, "repositories.create", {"name": "Legacy repository", "provider": "github", "external_name": "legacy-owner/legacy-repo"})
    source = SourceRef("github", "legacy-owner/legacy-repo", "issue", "7074",
        "https://github.com/legacy-owner/legacy-repo/issues/7074", host="github.com")
    rfc = service.dispatch(admin, "rfcs.draft", {"repo_id": repo["id"], "title": "Existing RFC", "body": BODY, "source": source.to_dict()})
    return service, admin, repo, rfc


def legacy(tmp_path):
    root = tmp_path / "legacy"
    root.mkdir()
    (root / "roadmap.json").write_text(json.dumps({"body": BODY}), encoding="utf-8")
    (root / "roadmap-work").mkdir()
    prs = {}
    for number, state in ((1, "open"), (2, "closed")):
        prs[str(number)] = {"number": number, "title": "Implementation", "body": "PR body", "state": state,
            "draft": number == 1, "merged_at": "2026-10-02T08:00:00Z" if number == 2 else None,
            "updated_at": "2026-10-02T08:00:00Z", "head": {"sha": ("a" if number == 1 else "b") * 40},
            "html_url": f"https://github.com/legacy-owner/legacy-repo/pull/{number}", "user": {"login": "historical-author"}}
    (root / "roadmap-work" / "prs.json").write_text(json.dumps(prs), encoding="utf-8")
    con = sqlite3.connect(root / "campaign.sqlite")
    con.executescript("""
        CREATE TABLE feature_claims(id INTEGER,feature TEXT,login TEXT,note TEXT,token_hash TEXT,ip TEXT,created_at TEXT);
        CREATE TABLE feature_priority(feature TEXT,priority TEXT,token_hash TEXT,ip TEXT,updated_at TEXT);
        CREATE TABLE roadmap_tasks(id INTEGER,roadmap TEXT,op TEXT,feature TEXT,group_prefix TEXT,title TEXT,
            depends_on TEXT,number INTEGER,login TEXT,note TEXT,token_hash TEXT,ip TEXT,created_at TEXT,applied_at TEXT,reverted_at TEXT,error TEXT);
        CREATE TABLE roadmap_auto_items(roadmap TEXT,number INTEGER,kind TEXT,title TEXT,state TEXT,author TEXT,
            url TEXT,decision TEXT,target TEXT,group_prefix TEXT,new_title TEXT,depends_on TEXT,rationale TEXT,
            applied_at TEXT,tombstoned_at TEXT);
        CREATE TABLE roadmap_auto_runs(id INTEGER,roadmap TEXT,at TEXT,mode TEXT,discovered INTEGER,judged INTEGER,applied INTEGER,tombstoned INTEGER,error TEXT);
        INSERT INTO feature_claims VALUES(1,'E7','unverified-login','Anonymous browser claim','SECRET-HASH','SECRET-IP','2026-09-01');
        INSERT INTO feature_priority VALUES('E7','optional','SECRET-HASH','SECRET-IP','2026-09-01');
        INSERT INTO roadmap_tasks(id,roadmap,op,feature,login,created_at,applied_at) VALUES(1,'wm-7074','drop','L6','anonymous','2026-09-01','2026-09-02');
        INSERT INTO roadmap_tasks(id,roadmap,op,feature,login,created_at) VALUES(2,'wm-7074','drop','E7','anonymous','2026-09-03');
        INSERT INTO roadmap_auto_items VALUES('wm-7074',1,'pr','Draft harness','draft','author','unused','attach','E7',NULL,NULL,NULL,'Explicit E7 relationship',NULL,NULL);
        INSERT INTO roadmap_auto_items VALUES('wm-7074',2,'pr','Unrelated work','merged','author','unused','ignore',NULL,NULL,NULL,NULL,'Out of scope',NULL,NULL);
        INSERT INTO roadmap_auto_items VALUES('wm-7074',3,'pr','Applied kernel','open','author','unused','attach','L6',NULL,NULL,NULL,'Applied association','2026-09-02',NULL);
        INSERT INTO roadmap_auto_items VALUES('wm-7074',4,'pr','Deleted addition','open','author','unused','new','M3','M','New work',NULL,'Intentionally deleted','2026-09-02','2026-09-03');
        INSERT INTO roadmap_auto_items VALUES('other-rfc',99,'pr','Other campaign','open','author','unused','ignore',NULL,NULL,NULL,NULL,'Other namespace',NULL,NULL);
        INSERT INTO roadmap_auto_runs VALUES(1,'wm-7074','2026-09-02','dry-run',4,4,0,0,NULL);
    """)
    con.commit()
    con.close()
    (root / "evidence-ledger.json").write_text(json.dumps({"entries": [{"id": "legacy-run", "verdict": "passing",
        "revision": "old-head", "environment": "H200", "result": "latency passed", "token": "SECRET-TOKEN"}]}), encoding="utf-8")
    return root


def run(service, actor, repo, rfc, root, apply=False):
    return migrate(service, actor, root, repo["id"], rfc["id"], apply=apply)


def test_dry_run_is_read_only_and_compares_exact_prose_ids_and_counts(tmp_path):
    service, admin, repo, rfc = workspace(tmp_path)
    root = legacy(tmp_path)
    old_target = service.store.one("SELECT * FROM rfcs WHERE id=?", (rfc["id"],))
    old_source = (root / "campaign.sqlite").read_bytes()
    (root / "campaign.sqlite").chmod(0o444)
    result = run(service, admin, repo, rfc, root)
    assert result["eligible"] and result["body_matches"] and result["feature_ids_match"]
    assert result["counts"] == {"claims": 1, "priorities": 1, "tasks": 2, "auto_items": 4,
        "auto_runs": 1, "prs": 2, "historical_evidence": 1, "features": 2}
    assert not result["applied"] and result["backup_path"] == ""
    assert old_source == (root / "campaign.sqlite").read_bytes()
    assert old_target == service.store.one("SELECT * FROM rfcs WHERE id=?", (rfc["id"],))
    assert not (service.store.root / "backups").exists()


def test_apply_preserves_owners_prose_ids_and_keeps_partial_delivery_unaccepted(tmp_path):
    service, admin, repo, rfc = workspace(tmp_path)
    root = legacy(tmp_path)
    service.dispatch(admin, "rfcs.work", {"rfc_id": rfc["id"], "op": "claim", "feature_id": "E7", "reason": "I own this work"})
    result = run(service, admin, repo, rfc, root, True)
    view = service.dispatch(admin, "rfcs.get", {"rfc_id": rfc["id"]})
    assert result["applied"] and Path(result["backup_path"]).is_file()
    if os.name != "nt":
        assert Path(result["backup_path"]).stat().st_mode & 0o777 == 0o600
    assert view["body"].encode("utf-8") == BODY.encode("utf-8")
    assert [f["id"] for f in view["features"]] == ["E7", "L6"]
    e7, l6 = view["features"]
    assert e7["owner"] == "Owner" and e7["owner_user_id"] == admin.user_id
    assert e7["priority"] == "optional" and e7["implementation"] == "partial"
    assert l6["dropped"] and "L6" in view["tombstones"]
    assert view["legacy_namespace"] == "wm-7074"
    assert view["historical_claims"][0]["authenticated"] is False
    assert view["historical_claims"][0]["id"] == "wm-7074:claim:1"
    assert {s["status"] for s in view["suggestions"]} == {"proposed", "rejected", "applied"}
    assert "Out of scope" in {s["reason"] for s in view["suggestions"]}
    assert view["historical_evidence"][0]["stale"] and not view["historical_evidence"][0]["accepted"]
    assert view["acceptance"] == "pending" and not view["complete"]
    observation = view["observations"]["https://github.com/legacy-owner/legacy-repo/pull/1"]
    assert observation["head_sha"] == "a" * 40 and observation["kind"] == "pr" and observation["state"] == "draft"
    assert "SECRET" not in json.dumps(view)
    assert "backup_path" not in view["legacy_migration"]
    assert service.store.one("SELECT value FROM metadata WHERE key='legacy_alias:wm-7074'")["value"] == rfc["id"]


def test_repeated_migration_creates_no_extra_backup_or_audit_and_does_not_reset_edits(tmp_path):
    service, admin, repo, rfc = workspace(tmp_path)
    root = legacy(tmp_path)
    first = run(service, admin, repo, rfc, root, True)
    service.dispatch(admin, "rfcs.work", {"rfc_id": rfc["id"], "op": "update", "feature_id": "E7", "feature": {"priority": "normal"}})
    before = service.store.one("SELECT * FROM rfcs WHERE id=?", (rfc["id"],))
    second = run(service, admin, repo, rfc, root, True)
    assert second["already_applied"] and not second["applied"] and second["backup_path"] == first["backup_path"]
    assert before == service.store.one("SELECT * FROM rfcs WHERE id=?", (rfc["id"],))
    assert len(list((service.store.root / "backups").iterdir())) == 1
    assert len(service.store.all("SELECT * FROM audit WHERE action='legacy.migrate'")) == 1


@pytest.mark.parametrize("mismatch", ["body", "features", "source"])
def test_comparison_mismatch_blocks_apply_before_backup(tmp_path, mismatch):
    service, admin, repo, rfc = workspace(tmp_path)
    root = legacy(tmp_path)
    with service.store.transaction() as con:
        row = service._rfc(con, admin, rfc["id"])
        if mismatch == "body":
            con.execute("UPDATE rfcs SET body=? WHERE id=?", (BODY.replace("Existing RFC", "Changed RFC"), rfc["id"]))
        elif mismatch == "features":
            model = json.loads(row["model"])
            model["features"].pop()
            con.execute("UPDATE rfcs SET model=? WHERE id=?", (json.dumps(model), rfc["id"]))
        else:
            source = json.loads(row["source"])
            source["identifier"] = "999"
            con.execute("UPDATE rfcs SET source=? WHERE id=?", (json.dumps(source), rfc["id"]))
    assert not run(service, admin, repo, rfc, root)["eligible"]
    with pytest.raises(RFCError) as error:
        run(service, admin, repo, rfc, root, True)
    assert error.value.status == 409
    assert not (service.store.root / "backups").exists()


def test_migration_requires_fresh_maintainer_rfc_permission_before_reading_source(tmp_path):
    service, admin, repo, rfc = workspace(tmp_path)
    created = service.dispatch(admin, "users.create", {"name": "Contributor"})
    token = service.dispatch(admin, "tokens.create", {"user_id": created["id"]})
    contributor = service.authenticate(token["token"])
    service.dispatch(admin, "grants.set", {"repo_id": repo["id"], "user_id": created["id"], "role": "contributor"})
    with pytest.raises(RFCError) as error:
        run(service, contributor, repo, rfc, tmp_path / "does-not-exist")
    assert error.value.status == 403
    service.dispatch(admin, "grants.set", {"repo_id": repo["id"], "user_id": created["id"], "role": "maintainer"})
    service.dispatch(admin, "rfcs.acl", {"rfc_id": rfc["id"], "restricted": True, "grants": {}})
    with pytest.raises(RFCError) as error:
        run(service, contributor, repo, rfc, tmp_path / "does-not-exist")
    assert error.value.status == 403


def test_revocation_during_legacy_read_prevents_backup_and_apply(tmp_path, monkeypatch):
    service, admin, repo, rfc = workspace(tmp_path)
    root = legacy(tmp_path)
    real_read = migration._read_legacy
    def read_then_revoke(path):
        value = real_read(path)
        service.dispatch(admin, "tokens.revoke", {"token_id": admin.credential_id})
        return value
    monkeypatch.setattr(migration, "_read_legacy", read_then_revoke)
    with pytest.raises(RFCError) as error:
        run(service, admin, repo, rfc, root, True)
    assert error.value.status == 401
    assert not (service.store.root / "backups").exists()


def test_failed_apply_rolls_back_and_backup_restores_pre_migration_database(tmp_path, monkeypatch):
    service, admin, repo, rfc = workspace(tmp_path)
    root = legacy(tmp_path)
    original = service.store.one("SELECT * FROM rfcs WHERE id=?", (rfc["id"],))
    real_audit = service.store.audit
    def failed_audit(*args, **kwargs):
        if args[2] == "legacy.migrate":
            raise RuntimeError("simulated commit failure")
        return real_audit(*args, **kwargs)
    monkeypatch.setattr(service.store, "audit", failed_audit)
    with pytest.raises(RuntimeError):
        run(service, admin, repo, rfc, root, True)
    assert original == service.store.one("SELECT * FROM rfcs WHERE id=?", (rfc["id"],))
    assert not service.store.one("SELECT * FROM metadata WHERE key='legacy_alias:wm-7074'")
    backup = next((service.store.root / "backups").iterdir())
    with sqlite3.connect(backup) as con:
        assert con.execute("SELECT body FROM rfcs WHERE id=?", (rfc["id"],)).fetchone()[0] == BODY
    monkeypatch.setattr(service.store, "audit", real_audit)
    result = run(service, admin, repo, rfc, root, True)
    source = sqlite3.connect(result["backup_path"])
    target = service.store.connect()
    source.backup(target)
    target.close()
    source.close()
    assert original == service.store.one("SELECT * FROM rfcs WHERE id=?", (rfc["id"],))
    assert not service.store.one("SELECT * FROM metadata WHERE key='legacy_alias:wm-7074'")


def test_live_observations_are_not_overwritten_by_older_snapshot(tmp_path):
    service, admin, repo, rfc = workspace(tmp_path)
    root = legacy(tmp_path)
    with service.store.transaction() as con:
        row = service._rfc(con, admin, rfc["id"])
        model = json.loads(row["model"])
        model["observations"] = {"https://github.com/legacy-owner/legacy-repo/pull/1": {"kind": "pr", "state": "open", "head_sha": "new-head", "revision": "fresh"}}
        service._save(con, admin, row, model)
    run(service, admin, repo, rfc, root, True)
    view = service.dispatch(admin, "rfcs.get", {"rfc_id": rfc["id"]})
    assert view["observations"]["https://github.com/legacy-owner/legacy-repo/pull/1"]["head_sha"] == "new-head"


def test_pr_snapshot_origin_must_match_selected_repository_before_backup(tmp_path):
    service, admin, repo, rfc = workspace(tmp_path)
    root = legacy(tmp_path)
    path = root / "roadmap-work" / "prs.json"
    prs = json.loads(path.read_text(encoding="utf-8"))
    prs["1"]["html_url"] = "https://github.com/another-owner/another-repo/pull/1"
    path.write_text(json.dumps(prs), encoding="utf-8")
    with pytest.raises(RFCError, match="different repository"):
        run(service, admin, repo, rfc, root, True)
    assert not (service.store.root / "backups").exists()
