"""Operator-only, read-only comparison and backed-up legacy roadmap migration.

Legacy browser login claims and agent decisions are historical provenance. They
never grant service permissions, assign authenticated owners or accept an RFC.
"""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import re
import sqlite3
import uuid

from .drafts import digest, parse
from .models import RFCError, SourceRef
from .providers import GitHubProvider
from .store import encode

NAMESPACE = "wm-7074"
MAX_INPUT_BYTES = 32 * 1024 * 1024
TABLE_FIELDS = {
    "feature_claims": ("id", "feature", "login", "note", "created_at"),
    "feature_priority": ("feature", "priority", "updated_at"),
    "roadmap_tasks": ("id", "roadmap", "op", "feature", "group_prefix", "title", "depends_on", "number", "login", "note", "created_at", "applied_at", "reverted_at", "error"),
    "roadmap_auto_items": ("roadmap", "number", "kind", "title", "state", "author", "url", "decision", "target", "group_prefix", "new_title", "depends_on", "rationale", "judged_at", "judge_model", "applied_at", "tombstoned_at", "error", "first_seen", "last_seen", "matched", "refs"),
    "roadmap_auto_runs": ("id", "roadmap", "at", "mode", "discovered", "judged", "applied", "tombstoned", "error"),
}
EVIDENCE_FIELDS = {"id", "criterion_id", "feature_id", "title", "status", "verdict", "revision", "head_sha", "environment", "url", "reason", "recorded_at", "created_at", "result", "command"}


def _read_json(path: Path, *, optional=False):
    if optional and not path.exists():
        return None
    try:
        raw = path.read_bytes()
        if len(raw) > MAX_INPUT_BYTES:
            raise ValueError("size")
        return json.loads(raw)
    except (OSError, ValueError, UnicodeError):
        raise RFCError("Legacy JSON input is unavailable or invalid") from None


def _read_legacy(root: Path):
    snapshot = _read_json(root / "roadmap.json")
    prs = _read_json(root / "roadmap-work" / "prs.json", optional=True) or {}
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("body"), str) or not isinstance(prs, dict):
        raise RFCError("Legacy snapshot must contain body text and a PR mapping")
    path = root / "campaign.sqlite"
    if not path.is_file():
        raise RFCError("Legacy campaign database is required")
    rows = {}
    try:
        con = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        try:
            con.execute("PRAGMA query_only=ON")
            con.execute("BEGIN")
            tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            for table, allowed in TABLE_FIELDS.items():
                if table not in tables:
                    rows[table] = []
                    continue
                columns = {row[1] for row in con.execute(f'PRAGMA table_info("{table}")')}
                fields = [name for name in allowed if name in columns]
                if not fields:
                    raise RFCError("Legacy table has no recognized fields")
                query = f'SELECT {",".join(fields)} FROM "{table}"'
                params = ()
                if "roadmap" in columns:
                    query += " WHERE roadmap=?"
                    params = (NAMESPACE,)
                rows[table] = [dict(row) for row in con.execute(query, params)]
            con.rollback()
        finally:
            con.close()
    except sqlite3.Error:
        raise RFCError("Legacy database could not be read") from None
    evidence = []
    for relative in ("evidence-ledger.json", "evidence_ledger.json", "evidence/ledger.json"):
        value = _read_json(root / relative, optional=True)
        if value is None:
            continue
        if isinstance(value, dict):
            value = value.get("entries", value.get("evidence", value.get("items", [])))
        if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
            raise RFCError("Legacy evidence ledger must contain entry objects")
        evidence.extend({key: item[key] for key in EVIDENCE_FIELDS if key in item} for item in value)
    return {"body": snapshot["body"], "prs": prs, "rows": rows, "evidence": evidence}


def _compare(row, legacy, repository):
    model = json.loads(row["model"])
    legacy_ids = [item["id"] for item in parse(legacy["body"])["features"]]
    target_ids = [item["id"] for item in model["features"]]
    missing = sorted(set(legacy_ids) - set(target_ids))
    extra = sorted({item["id"] for item in model["features"] if not item.get("sidecar")} - set(legacy_ids))
    source = json.loads(row["source"])
    source_matches = repository["provider"] == "github" and (not source or (source.get("provider") == repository["provider"]
        and source.get("repository", "").casefold() == repository["external_name"].casefold()
        and source.get("kind", "issue") == "issue" and source.get("identifier") == "7074"))
    body_matches = row["body"].encode("utf-8") == legacy["body"].encode("utf-8")
    counts = {"claims": len(legacy["rows"]["feature_claims"]), "priorities": len(legacy["rows"]["feature_priority"]),
        "tasks": len(legacy["rows"]["roadmap_tasks"]), "auto_items": len(legacy["rows"]["roadmap_auto_items"]),
        "auto_runs": len(legacy["rows"]["roadmap_auto_runs"]), "prs": len(legacy["prs"]),
        "historical_evidence": len(legacy["evidence"]), "features": len(legacy_ids)}
    return {"namespace": NAMESPACE, "body_matches": body_matches, "feature_ids_match": not missing and not extra,
        "source_matches": source_matches, "legacy_feature_ids": legacy_ids, "target_feature_ids": target_ids,
        "missing_feature_ids": missing, "extra_feature_ids": extra, "counts": counts,
        "eligible": body_matches and not missing and not extra and source_matches}


def _backup(service):
    directory = service.store.root / "backups"
    directory.mkdir(mode=0o700, exist_ok=True)
    directory.chmod(0o700)
    path = directory / ("before-" + NAMESPACE + "-" + uuid.uuid4().hex + ".sqlite")
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    source, target = None, None
    try:
        source = service.store.connect()
        target = sqlite3.connect(path)
        source.backup(target)
        target.close()
        target = None
        path.chmod(0o600)
        return path
    except (OSError, sqlite3.Error):
        if target is not None:
            target.close()
            target = None
        path.unlink(missing_ok=True)
        raise RFCError("Target database backup failed; migration was not applied") from None
    finally:
        if target is not None:
            target.close()
        if source is not None:
            source.close()


def _merge(model, legacy, repository):
    model = deepcopy(model)
    features = {feature["id"]: feature for feature in model["features"]}
    rows = legacy["rows"]
    model["legacy_namespace"] = NAMESPACE
    model["historical_claims"] = [{**row, "id": f"{NAMESPACE}:claim:{row.get('id', index)}",
        "provenance": "legacy_anonymous_login", "authenticated": False}
        for index, row in enumerate(rows["feature_claims"])]
    model["historical_priorities"] = rows["feature_priority"]
    for row in rows["feature_priority"]:
        if row.get("feature") in features and row.get("priority") in ("normal", "low", "optional"):
            features[row["feature"]]["priority"] = row["priority"]
    model["historical_tasks"] = rows["roadmap_tasks"]
    tombstones = set(model.get("tombstones", []))
    for row in sorted(rows["roadmap_tasks"], key=lambda item: (item.get("created_at") or "", item.get("id") or 0)):
        if not row.get("applied_at") or row.get("reverted_at"):
            continue
        feature_id = row.get("feature")
        if row.get("op") == "drop" and feature_id:
            tombstones.add(feature_id)
            if feature_id in features:
                features[feature_id]["dropped"] = True
        elif row.get("op") == "undrop" and feature_id:
            tombstones.discard(feature_id)
            if feature_id in features:
                features[feature_id]["dropped"] = False
    suggestions = {item["id"]: item for item in model.get("suggestions", [])}
    for row in rows["roadmap_auto_items"]:
        number = str(row.get("number") or "")
        if not re.fullmatch(r"[1-9][0-9]*", number):
            raise RFCError("Legacy discovery contains an invalid item identifier")
        kind = "pr" if row.get("kind") in ("pr", "pull", "pull_request") else "issue"
        url = f"https://github.com/{repository['external_name']}/{'pull' if kind == 'pr' else 'issues'}/{number}"
        ref = SourceRef(repository["provider"], repository["external_name"], kind, number, url, host="github.com")
        key = "suggestion-" + digest(encode(ref.to_dict()))[:20]
        rejected = bool(row.get("tombstoned_at")) or row.get("decision") in ("ignore", "reject", "rejected")
        status = "rejected" if rejected else "applied" if row.get("applied_at") else "proposed"
        target = row.get("target") or ""
        feature = {"id": target if re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,79}", target) else "F-" + digest(key)[:12],
            "title": row.get("new_title") or row.get("title") or "Legacy related work",
            "track": features.get(target, {}).get("track", ""), "links": [url], "depends_on": []}
        suggestions.setdefault(key, {"id": key, "feature_id": target if row.get("decision") == "attach" else "",
            "feature": feature, "url": url, "status": status, "bounded": False,
            "reason": row.get("rationale") or "Legacy discovery; review its relationship and scope",
            "evidence": {"source": ref.to_dict(), "provenance": "legacy_agent_decision", "historical": True},
            "legacy": {**row, "namespace": NAMESPACE}})
        if rejected:
            tombstones.add(key)
        elif status == "applied" and row.get("decision") == "attach" and target in features:
            if url not in features[target]["links"]:
                features[target]["links"].append(url)
    model["suggestions"] = list(suggestions.values())
    model["tombstones"] = sorted(tombstones)
    model["historical_discovery_runs"] = rows["roadmap_auto_runs"]
    model["historical_evidence"] = [{**row, "provenance": "legacy_evidence_ledger", "historical": True,
        "accepted": False, "stale": True} for row in legacy["evidence"]]
    observations = model.setdefault("observations", {})
    adapter = GitHubProvider()
    for number, raw in legacy["prs"].items():
        if not isinstance(raw, dict) or str(raw.get("number") or "") != str(number):
            raise RFCError("Legacy PR snapshot contains an invalid identity")
        ref = SourceRef(repository["provider"], repository["external_name"], "pr", str(number))
        item = adapter._item(ref, raw)
        if item["url"] != f"https://github.com/{repository['external_name']}/pull/{number}":
            raise RFCError("Legacy PR snapshot belongs to a different repository")
        item.update(kind="pr", legacy_snapshot=True, observed_at=raw.get("updated_at", ""))
        observations.setdefault(item["url"], item)
    return model


def migrate(service, principal, source_dir, repo_id, rfc_id, apply=False):
    """Compare first; explicit apply changes only RFC sidecars after a full backup.

    Restore the returned backup with SQLite's backup API while the service and
    worker are stopped. A failed apply rolls back its entire target transaction.
    Absolute backup paths are returned to this local operator entry point only.
    """
    with service.store.transaction() as con:
        current = service._current(con, principal)
        row = service._rfc(con, current, rfc_id, "maintainer")
        if row["repo_id"] != repo_id:
            raise RFCError("Resource not found or access denied", 403, "forbidden")
        repository = dict(con.execute("SELECT * FROM repositories WHERE id=?", (repo_id,)).fetchone())
    try:
        root = Path(source_dir).expanduser().resolve(strict=True)
    except OSError:
        raise RFCError("Legacy source directory is unavailable") from None
    if not root.is_dir():
        raise RFCError("Legacy source directory is required")
    legacy = _read_legacy(root)
    input_digest = digest(encode(legacy))
    comparison = _compare(row, legacy, repository)
    result = {**comparison, "repo_id": repo_id, "rfc_id": rfc_id, "applied": False,
        "input_digest": input_digest, "already_applied": False, "backup_path": ""}
    # Build and validate everything before creating a backup or changing state.
    merged = _merge(json.loads(row["model"]), legacy, repository) if comparison["source_matches"] else None
    with service.store.transaction() as con:
        current = service._current(con, principal)
        latest = service._rfc(con, current, rfc_id, "maintainer")
        if latest["repo_id"] != repo_id:
            raise RFCError("Resource not found or access denied", 403, "forbidden")
        old = con.execute("SELECT value FROM metadata WHERE key=?", (f"legacy_migration:{NAMESPACE}:{rfc_id}",)).fetchone()
        if old:
            record = json.loads(old["value"])
            if record["input_digest"] != input_digest:
                if not apply:
                    return {**result, "requires_review": True, "previous_input_digest": record["input_digest"]}
                raise RFCError("Legacy input changed after migration; review a new migration explicitly", 409, "conflict")
            return {**result, "already_applied": True, "backup_path": record["backup_path"] if apply else ""}
        if not apply:
            return result
        if not comparison["eligible"]:
            raise RFCError("Legacy RFC prose, feature identifiers or source differ; import the exact RFC before applying", 409, "migration_mismatch")
        if latest["revision"] != row["revision"]:
            raise RFCError("Target RFC changed during comparison; rerun migration", 409, "conflict")
        alias = con.execute("SELECT value FROM metadata WHERE key=?", ("legacy_alias:" + NAMESPACE,)).fetchone()
        if alias and alias["value"] != rfc_id:
            raise RFCError("Legacy roadmap alias already targets another RFC", 409, "conflict")
        namespace = json.loads(row["model"]).get("legacy_namespace", NAMESPACE)
        if namespace != NAMESPACE:
            raise RFCError("Target RFC already belongs to another legacy namespace", 409, "conflict")
        if con.execute("SELECT 1 FROM operations WHERE rfc_id=? AND status IN ('pending','running','uncertain')", (rfc_id,)).fetchone():
            raise RFCError("Finish or recover queued RFC operations before migration", 409, "conflict")
        backup = _backup(service)
        merged["legacy_migration"] = {"namespace": NAMESPACE, "input_digest": input_digest,
            "imported_at": service.clock(), "counts": comparison["counts"]}
        service._save(con, current, latest, merged)
        if not alias:
            con.execute("INSERT INTO metadata VALUES (?,?)", ("legacy_alias:" + NAMESPACE, rfc_id))
        con.execute("INSERT INTO metadata VALUES (?,?)", (f"legacy_migration:{NAMESPACE}:{rfc_id}",
            encode({"input_digest": input_digest, "backup_path": str(backup), "counts": comparison["counts"]})))
        service.store.audit(con, current.user_id, "legacy.migrate", service.clock(), repo_id, rfc_id,
            {"namespace": NAMESPACE, "input_digest": input_digest, "counts": comparison["counts"]})
        return {**result, "applied": True, "backup_path": str(backup)}
