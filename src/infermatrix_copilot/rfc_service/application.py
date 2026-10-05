"""Shared RFC application: authorization, lifecycle, leases and deterministic tracking.

No host, repository, model, web framework or operating-system scheduler is required.
Every interactive adapter calls dispatch; workers reauthorize persisted operations.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import secrets
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from . import RFC_API_VERSION
from .drafts import digest, draft, parse, project, validate_features
from .models import SESSION_TTL_SECONDS, Principal, ProviderError, RFCError, SourceRef
from .store import Store, encode

ROLES = {"reader": 1, "contributor": 2, "maintainer": 3}


def identifier(prefix: str) -> str:
    return prefix + "-" + uuid.uuid4().hex


def content_digest(title, body):
    return digest(encode({"title": title, "body": body}))


class RFCService:
    def __init__(self, state_dir, providers=None, roots=None, clock=time.time):
        self.store = Store(state_dir)
        self.providers = dict(providers or {})
        self.roots = [Path(p).expanduser().resolve() for p in (roots or [])]
        self.managed_files = self.store.root / "files"
        self.managed_files.mkdir(mode=0o700, exist_ok=True)
        self.roots.append(self.managed_files)
        self.clock = clock
        with self.store.transaction() as con:
            con.execute("INSERT OR IGNORE INTO metadata VALUES ('writer_id',?)", (identifier("workspace"),))
        self.writer_id = self.store.one("SELECT value FROM metadata WHERE key='writer_id'")["value"]

    def capabilities(self):
        settings = self.settings()
        return {"version": RFC_API_VERSION, "rfc_api_version": RFC_API_VERSION, "providers": sorted(self.providers),
                "roles": list(ROLES), "multi_rfc": True, "knowledge_adapter_required": False,
                "drafting": "host-assisted", "default_sync_seconds": settings["sync_seconds"],
                "default_max_auto_additions": settings["default_max_auto_additions"], "writer_id": self.writer_id}

    def settings(self):
        row = self.store.one("SELECT value FROM metadata WHERE key='service_settings'")
        return {"sync_seconds": 3600, "default_max_auto_additions": 5,
                **(json.loads(row["value"]) if row else {}),
                "public_registration": False, "configured_providers": sorted(self.providers)}

    def _issue_token(self, con, user_id, expires_days=30):
        days = float(expires_days)
        if not 0 < days <= 365:
            raise RFCError("Token validity must be between 0 and 365 days")
        raw, key = "imrfc_" + secrets.token_urlsafe(36), identifier("token")
        expires = self.clock() + days * 86400
        con.execute("INSERT INTO tokens VALUES (?,?,?,?,0,?)", (key, user_id, digest(raw), expires, self.clock()))
        return {"token_id": key, "token": raw, "expires": expires, "user_id": user_id}

    def bootstrap_admin(self, name="Administrator"):
        with self.store.transaction() as con:
            if con.execute("SELECT 1 FROM users LIMIT 1").fetchone():
                raise RFCError("Administrator already initialized", 409, "already_initialized")
            user_id = identifier("user")
            con.execute("INSERT INTO users VALUES (?,?,1,1)", (user_id, self._text(name, "name")))
            result = self._issue_token(con, user_id)
            self.store.audit(con, user_id, "bootstrap_admin", self.clock())
            return result

    def _principal(self, con, token_id):
        row = con.execute("""SELECT u.*,t.id credential_id FROM users u JOIN tokens t ON t.user_id=u.id
            WHERE t.id=? AND t.revoked=0 AND t.expires>? AND u.enabled=1""", (token_id, self.clock())).fetchone()
        if not row:
            raise RFCError("Authentication required or credential expired", 401, "unauthorized")
        return Principal(row["id"], row["name"], bool(row["admin"]), row["credential_id"])

    def authenticate(self, token):
        if not token:
            raise RFCError("Authentication required", 401, "unauthorized")
        with self.store.transaction() as con:
            row = con.execute("SELECT id FROM tokens WHERE digest=?", (digest(token),)).fetchone()
            if not row:
                raise RFCError("Authentication required", 401, "unauthorized")
            return self._principal(con, row["id"])

    def create_session(self, token):
        principal = self.authenticate(token)
        secret = secrets.token_urlsafe(40)
        with self.store.transaction() as con:
            self._current(con, principal)
            con.execute("INSERT INTO sessions VALUES (?,?,?)", (digest(secret), principal.credential_id, self.clock() + SESSION_TTL_SECONDS))
        return secret, principal

    def authenticate_session(self, cookie):
        with self.store.transaction() as con:
            row = con.execute("SELECT token_id FROM sessions WHERE digest=? AND expires>?", (digest(cookie), self.clock())).fetchone()
            if not row:
                raise RFCError("Authentication required", 401, "unauthorized")
            return self._principal(con, row["token_id"])

    def revoke_session(self, cookie):
        with self.store.transaction() as con:
            con.execute("DELETE FROM sessions WHERE digest=?", (digest(cookie),))

    def _current(self, con, principal):
        current = self._principal(con, principal.credential_id)
        if current.user_id != principal.user_id:
            raise RFCError("Authentication required", 401, "unauthorized")
        return current

    @staticmethod
    def _text(value, name):
        if not isinstance(value, str) or not value.strip():
            raise RFCError(f"{name} is required")
        return value.strip()

    @staticmethod
    def _admin(principal):
        if not principal.admin:
            raise RFCError("Administrator role required", 403, "forbidden")

    def _role(self, con, principal, repo_id, rfc_id=""):
        if not con.execute("SELECT 1 FROM repositories WHERE id=?", (repo_id,)).fetchone():
            return ""
        if principal.admin:
            return "maintainer"
        row = con.execute("SELECT role FROM repository_grants WHERE repo_id=? AND user_id=?", (repo_id, principal.user_id)).fetchone()
        role = row["role"] if row else ""
        if rfc_id:
            rfc = con.execute("SELECT restricted FROM rfcs WHERE id=? AND repo_id=?", (rfc_id, repo_id)).fetchone()
            if not rfc:
                return ""
            if rfc["restricted"]:
                acl = con.execute("SELECT role FROM rfc_grants WHERE rfc_id=? AND user_id=?", (rfc_id, principal.user_id)).fetchone()
                allowed = acl["role"] if acl else ""
                return min((role, allowed), key=lambda x: ROLES.get(x, 0))
        return role

    def _require(self, con, principal, repo_id, role="reader", rfc_id=""):
        actual = self._role(con, principal, repo_id, rfc_id)
        if ROLES.get(actual, 0) < ROLES[role]:
            raise RFCError("Resource not found or access denied", 403, "forbidden")
        return actual

    def _rfc(self, con, principal, rfc_id, role="reader"):
        row = con.execute("SELECT * FROM rfcs WHERE id=?", (rfc_id,)).fetchone()
        if not row:
            raise RFCError("Resource not found or access denied", 403, "forbidden")
        self._require(con, principal, row["repo_id"], role, rfc_id)
        return dict(row)

    def _view(self, con, principal, row, parsed_model=None):
        model = dict(parsed_model) if parsed_model is not None else json.loads(row["model"])
        visible = self._view_visibility(con, principal, row["repo_id"])
        model["observations"] = {link: item for link, item in model.get("observations", {}).items()
                                 if visible(item.get("source"))}
        model["suggestions"] = [s for s in model.get("suggestions", []) if visible(s.get("evidence", {}).get("source"))]
        model["features"] = [dict(f) for f in model.get("features", []) if visible(f.get("auto_source"))]
        if "last_discovery" in model:
            model["last_discovery"] = {"proposed": sum(s.get("status") == "proposed" for s in model["suggestions"]),
                                       "applied": sum(s.get("status") == "applied" for s in model["suggestions"])}
        model = project(model)
        if row["enrolled"]:
            try:
                delegated = self._principal(con, model.get("enrollment", {}).get("credential_id", ""))
                self._require(con, delegated, row["repo_id"], "maintainer", row["id"])
                model["sync_status"] = "active" if model.get("writer_id") == self.writer_id else "different_writer"
            except RFCError:
                model["sync_status"] = "requires_reauthorization"
                model["next_actions"].append("维护者需要重新授权纳管，才能恢复后台同步")
        else:
            model["sync_status"] = "not_enrolled"
        # Enrollment credentials and private paths are execution state, never frontend data.
        model.pop("enrollment", None)
        model.pop("writer_id", None)
        source = json.loads(row["source"])
        if source.get("path", "").startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", source.get("path", "")):
            source.pop("path", None)
        role = self._role(con, principal, row["repo_id"], row["id"])
        if ROLES.get(role, 0) >= 3:
            model["grants"] = {r["user_id"]: r["role"] for r in con.execute("SELECT user_id,role FROM rfc_grants WHERE rfc_id=?", (row["id"],))}
        return {**model, "id": row["id"], "repo_id": row["repo_id"], "title": row["title"],
                "body": row["body"], "content_digest": content_digest(row["title"], row["body"]), "revision": row["revision"],
                "source": source, "enrolled": bool(row["enrolled"]), "restricted": bool(row["restricted"]),
                "updated": row["updated"], "role": role, "can_write": ROLES.get(role, 0) >= 2,
                "can_publish": ROLES.get(role, 0) >= 3}

    @staticmethod
    def _compact_view(view, mode):
        if mode not in ("detail", "summary"):
            return view
        counts = {}
        for suggestion in view.get("suggestions", []):
            state = suggestion.get("status", "proposed")
            counts[state] = counts.get(state, 0) + 1
        fields = {"id", "repo_id", "title", "revision", "content_digest", "source", "state",
                  "enrolled", "restricted", "updated", "role", "can_write", "can_publish",
                  "implementation", "acceptance", "complete", "sync_status", "freshness",
                  "next_actions", "last_discovery", "legacy_namespace", "namespace"}
        if mode == "detail":
            fields |= {"body", "features", "criteria", "scope", "auto_add", "max_auto_additions",
                       "grants", "historical_claims", "historical_priorities", "ambiguities"}
        return {**{key: value for key, value in view.items() if key in fields},
                "suggestion_counts": counts, "suggestions_total": sum(counts.values()),
                "feature_count": len(view.get("features", [])), "criterion_count": len(view.get("criteria", []))}

    def _save(self, con, principal, row, model, body=None, title=None):
        body = row["body"] if body is None else body
        title = row["title"] if title is None else title
        serialized = encode(model)
        # Same canonical revision, without encoding the large model twice.
        revision = digest('{"body":' + encode(body) + ',"model":' + serialized + ',"title":' + encode(title) + '}')
        updated = self.clock()
        con.execute("UPDATE rfcs SET title=?,body=?,model=?,revision=?,updated=? WHERE id=?",
                    (title, body, serialized, revision, updated, row["id"]))
        current = {**row, "title": title, "body": body, "model": serialized, "revision": revision, "updated": updated}
        return self._view(con, principal, current, parsed_model=model)

    def dispatch(self, principal, action, payload=None):
        payload = payload or {}
        if not isinstance(payload, dict):
            raise RFCError("Payload must be an object")
        if action == "sources.preview":
            with self.store.transaction() as con:
                principal = self._current(con, principal)
                rid = payload.get("repo_id", "")
                self._require(con, principal, rid, "contributor")
                ref = SourceRef.from_dict(self._source(con, rid, payload.get("source", {})))
                self._source_access(con, principal, rid, ref)
                repo = dict(con.execute("SELECT * FROM repositories WHERE id=?", (rid,)).fetchone())
            fetched = self._provider(repo).get_source(ref)
            with self.store.transaction() as con:
                principal = self._current(con, principal)
                self._require(con, principal, rid, "contributor")
                self._source_access(con, principal, rid, SourceRef.from_dict(fetched.get("source", ref.to_dict())))
            return {"source": ref.to_dict(), "title": fetched.get("title", "Imported RFC"), "body": fetched["body"], "revision": fetched.get("revision", ""), "content_digest": content_digest(fetched.get("title", "Imported RFC"), fetched["body"])}
        with self.store.transaction() as con:
            principal = self._current(con, principal)
            result = self._dispatch(con, principal, action, payload)
            if isinstance(result, dict) and "repo_id" in result and "features" in result:
                result = self._compact_view(result, payload.get("view"))
            return result

    def _dispatch(self, con, p, action, data):
        now = self.clock()
        if action in ("rfcs.update", "rfcs.work", "rfcs.decision") and data.get("rfc_id"):
            self._rfc(con, p, data["rfc_id"], "contributor")
            if con.execute("SELECT 1 FROM operations WHERE rfc_id=? AND kind IN ('rfcs.publish','rfcs.enroll') AND status IN ('running','uncertain')", (data["rfc_id"],)).fetchone():
                raise RFCError("Publication or import is in progress; recover its outcome before editing", 409, "write_in_progress")
        if action in ("rfcs.publish", "rfcs.enroll", "rfcs.sync") and data.get("idempotency_key"):
            old = con.execute("SELECT * FROM operations WHERE actor=? AND idempotency_key=?", (p.user_id, data["idempotency_key"])).fetchone()
            if old:
                self._require(con, p, old["repo_id"], "maintainer", old["rfc_id"])
                if old["request_digest"] != self._request_digest(action, old["repo_id"], old["rfc_id"], data):
                    raise RFCError("Idempotency key reused for a different operation", 409, "conflict")
                return {"operation_id": old["id"], "operation": self._operation(old)}
        if action == "capabilities":
            return self.capabilities()
        if action == "me":
            return p.to_dict()
        if action == "service.settings":
            self._admin(p)
            return self.settings()
        if action == "service.configure":
            self._admin(p)
            if set(data) - {"sync_seconds", "default_max_auto_additions"}:
                raise RFCError("Only refresh cadence and the new-RFC addition limit are configurable here")
            settings = self.settings()
            for key, minimum, maximum in (("sync_seconds", 60, 86400), ("default_max_auto_additions", 0, 100)):
                value = data.get(key, settings[key])
                if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
                    raise RFCError(f"{key} must be an integer between {minimum} and {maximum}")
                settings[key] = value
            saved = {key: settings[key] for key in ("sync_seconds", "default_max_auto_additions")}
            con.execute("INSERT OR REPLACE INTO metadata VALUES ('service_settings',?)", (encode(saved),))
            self.store.audit(con, p.user_id, action, now, detail=saved)
            return settings
        if action == "legacy.get":
            alias = con.execute("SELECT value FROM metadata WHERE key=?", ("legacy_alias:" + data.get("namespace", ""),)).fetchone()
            if not alias:
                raise RFCError("Resource not found or access denied", 403, "forbidden")
            return self._view(con, p, self._rfc(con, p, alias["value"]))
        if action == "users.list":
            self._admin(p)
            return {"users": [dict(r) for r in con.execute("SELECT * FROM users ORDER BY name")]}
        if action in ("users.create", "users.update"):
            self._admin(p)
            if action.endswith("create"):
                uid = identifier("user")
                name = self._text(data.get("name"), "name")
                if con.execute("SELECT 1 FROM users WHERE name=?", (name,)).fetchone():
                    raise RFCError("User name already exists", 409, "conflict")
                con.execute("INSERT INTO users VALUES (?,?,?,1)", (uid, name, int(bool(data.get("admin", False)))))
            else:
                uid = data.get("user_id", "")
                old = con.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
                if not old:
                    raise RFCError("User not found", 404, "not_found")
                enabled, admin = bool(data.get("enabled", old["enabled"])), bool(data.get("admin", old["admin"]))
                if old["admin"] and (not enabled or not admin) and con.execute("SELECT count(*) FROM users WHERE admin=1 AND enabled=1").fetchone()[0] == 1:
                    raise RFCError("The last active administrator cannot be disabled")
                con.execute("UPDATE users SET enabled=?,admin=? WHERE id=?", (int(enabled), int(admin), uid))
            self.store.audit(con, p.user_id, action, now, detail={"user_id": uid})
            return dict(con.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone())
        if action == "tokens.list":
            uid = data.get("user_id", p.user_id)
            if uid != p.user_id:
                self._admin(p)
            return {"tokens": [dict(r) for r in con.execute("SELECT id token_id,user_id,expires,revoked,created FROM tokens WHERE user_id=?", (uid,))]}
        if action == "tokens.create":
            uid = data.get("user_id", p.user_id)
            if uid != p.user_id:
                self._admin(p)
            if not con.execute("SELECT 1 FROM users WHERE id=? AND enabled=1", (uid,)).fetchone():
                raise RFCError("User not found", 404, "not_found")
            result = self._issue_token(con, uid, data.get("expires_days", 30))
            self.store.audit(con, p.user_id, action, now, detail={"token_id": result["token_id"], "user_id": uid})
            return result
        if action == "tokens.revoke":
            row = con.execute("SELECT * FROM tokens WHERE id=?", (data.get("token_id", ""),)).fetchone()
            if not row:
                raise RFCError("Token not found", 404, "not_found")
            if row["user_id"] != p.user_id:
                self._admin(p)
            con.execute("UPDATE tokens SET revoked=1 WHERE id=?", (row["id"],))
            self.store.audit(con, p.user_id, action, now, detail={"token_id": row["id"]})
            return {"revoked": True}
        if action == "repositories.list":
            result = []
            for row in con.execute("SELECT * FROM repositories ORDER BY name"):
                role = self._role(con, p, row["id"])
                if role:
                    result.append({k: row[k] for k in ("id", "name", "provider", "external_name")} | {"role": role})
            return {"repositories": result}
        if action == "repositories.create":
            self._admin(p)
            provider = data.get("provider", "local")
            if provider not in self.providers:
                raise RFCError("Provider is not configured")
            rid = identifier("repo")
            name = self._text(data.get("name"), "name")
            external = self._text(data.get("external_name", name), "external_name")
            root = ""
            if provider == "local":
                if not data.get("root"):
                    (self.managed_files / rid).mkdir(mode=0o700)
                path = Path(data.get("root") or self.managed_files / rid).expanduser().resolve()
                if not path.is_dir() or not any(path == allowed or path.is_relative_to(allowed) for allowed in self.roots):
                    raise RFCError("Local repository is outside configured workspace roots", 403, "forbidden")
                root = str(path)
            con.execute("INSERT INTO repositories VALUES (?,?,?,?,?,?)", (rid, name, provider, external, root, "{}"))
            con.execute("INSERT INTO repository_grants VALUES (?,?,?)", (rid, p.user_id, "maintainer"))
            self.store.audit(con, p.user_id, action, now, rid)
            return {"id": rid, "name": name, "provider": provider, "external_name": external}
        if action == "grants.set":
            self._admin(p)
            rid, uid, role = data.get("repo_id", ""), data.get("user_id", ""), data.get("role", "")
            if not con.execute("SELECT 1 FROM repositories WHERE id=?", (rid,)).fetchone() or not con.execute("SELECT 1 FROM users WHERE id=?", (uid,)).fetchone():
                raise RFCError("Repository or user not found", 404, "not_found")
            if role:
                if role not in ROLES:
                    raise RFCError("Invalid role")
                con.execute("INSERT OR REPLACE INTO repository_grants VALUES (?,?,?)", (rid, uid, role))
            else:
                con.execute("DELETE FROM repository_grants WHERE repo_id=? AND user_id=?", (rid, uid))
            self.store.audit(con, p.user_id, action, now, rid, detail={"user_id": uid, "role": role})
            return {"repo_id": rid, "user_id": uid, "role": role}
        if action == "rfcs.list":
            result = []
            for row in con.execute("SELECT * FROM rfcs ORDER BY updated DESC"):
                if data.get("repo_id") and data["repo_id"] != row["repo_id"]:
                    continue
                if self._role(con, p, row["repo_id"], row["id"]):
                    view = self._view(con, p, dict(row))
                    if data.get("query") and data["query"].casefold() not in (view["title"] + view["body"]).casefold():
                        continue
                    result.append(self._compact_view(view, data.get("view")))
            return {"rfcs": result}
        if action == "rfcs.draft":
            rid = data.get("repo_id", "")
            self._require(con, p, rid, "contributor")
            title = self._text(data.get("title"), "title")
            body = data.get("body", draft(title, data.get("goal", ""), data.get("scope", "")))
            if not isinstance(body, str) or len(body) > 2_000_000:
                raise RFCError("Invalid draft body")
            model = parse(body)
            model["max_auto_additions"] = self.settings()["default_max_auto_additions"]
            for key in ("scope", "auto_add", "max_auto_additions"):
                if key in data:
                    model[key] = data[key]
            if "features" in data:
                model["features"] = self._features(data["features"])
                for f in model["features"]:
                    f["sidecar"] = True
                    f["overrides"] = {k: f[k] for k in ("title", "track", "depends_on", "owner")}
            if "criteria" in data:
                model["criteria"] = self._criteria(data["criteria"])
                model["criteria_override"] = True
            self._policy(model)
            source = self._source(con, rid, data["source"]) if data.get("source") else {}
            key = identifier("rfc")
            con.execute("INSERT INTO rfcs VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (key, rid, title, body, digest(encode(model) + body), encode(source), encode(model), 0, 0, p.user_id, now))
            self.store.audit(con, p.user_id, action, now, rid, key)
            return self._view(con, p, dict(con.execute("SELECT * FROM rfcs WHERE id=?", (key,)).fetchone()))
        if action in ("rfcs.get", "rfcs.export", "rfcs.next", "rfcs.status", "rfcs.suggestions"):
            row = self._rfc(con, p, data.get("rfc_id", ""))
            view = self._view(con, p, row)
            if action == "rfcs.status":
                counts = {}
                for item in view.pop("suggestions", []):
                    state = item.get("status", "proposed")
                    counts[state] = counts.get(state, 0) + 1
                view.pop("body", None)
                return {**view, "suggestion_counts": counts, "suggestions_total": sum(counts.values())}
            if action == "rfcs.suggestions":
                offset, limit = data.get("offset", 0), data.get("limit", 50)
                if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 100:
                    raise RFCError("Suggestion offset must be nonnegative and limit between 1 and 100")
                items = view.get("suggestions", [])
                if data.get("status"):
                    items = [item for item in items if item.get("status", "proposed") == data["status"]]
                if data.get("query"):
                    query = str(data["query"]).casefold()
                    items = [item for item in items if query in encode(item).casefold()]
                return {"rfc_id": row["id"], "offset": offset, "limit": limit,
                        "total": len(items), "suggestions": items[offset:offset + limit]}
            if action == "rfcs.export":
                return {"rfc_id": row["id"], "markdown": row["body"], "content": row["body"], "tracking": view}
            return view
        if action == "rfcs.update":
            row = self._rfc(con, p, data.get("rfc_id", ""), "contributor")
            if data.get("expected_revision") != row["revision"]:
                raise RFCError("Draft changed; refresh and review before saving", 409, "conflict")
            old = json.loads(row["model"])
            body = data.get("body", row["body"])
            if not isinstance(body, str) or len(body) > 2_000_000:
                raise RFCError("Invalid draft body")
            if row["enrolled"] and (body != row["body"] or any(k in data for k in ("scope", "features", "criteria", "title", "auto_add", "max_auto_additions"))):
                self._require(con, p, row["repo_id"], "maintainer", row["id"])
                self._text(data.get("reason"), "Explicit decision reason")
            model = parse(body, old)
            removed = {f["id"] for f in old["features"]} - {f["id"] for f in model["features"]}
            model["tombstones"] = list(set(model["tombstones"]) | removed)
            for key in ("scope", "auto_add", "max_auto_additions"):
                if key in data:
                    model[key] = data[key]
            if "features" in data:
                model["features"] = self._features(data["features"])
                for f in model["features"]:
                    f["sidecar"] = True
                    f["overrides"] = {k: f[k] for k in ("title", "track", "depends_on", "owner")}
            if "criteria" in data:
                model["criteria"] = self._criteria(data["criteria"])
                model["criteria_override"] = True
            self._policy(model)
            if body != row["body"]:
                self._invalidate(model, "RFC design changed")
            self.store.audit(con, p.user_id, action, now, row["repo_id"], row["id"], {"reason": data.get("reason", "")})
            return self._save(con, p, row, model, body, data.get("title", row["title"]))
        if action == "rfcs.acl":
            row = self._rfc(con, p, data.get("rfc_id", ""), "maintainer")
            grants = data.get("grants", {})
            if not isinstance(grants, dict):
                raise RFCError("RFC grants must be a user-to-role object")
            for uid, role in grants.items():
                repo = con.execute("SELECT role FROM repository_grants WHERE repo_id=? AND user_id=?", (row["repo_id"], uid)).fetchone()
                if role not in ROLES or not repo or ROLES[role] > ROLES[repo["role"]]:
                    raise RFCError("RFC permissions can only narrow repository permissions", 403, "forbidden")
            con.execute("DELETE FROM rfc_grants WHERE rfc_id=?", (row["id"],))
            for uid, role in grants.items():
                con.execute("INSERT INTO rfc_grants VALUES (?,?,?)", (row["id"], uid, role))
            con.execute("UPDATE rfcs SET restricted=? WHERE id=?", (int(bool(data.get("restricted", True))), row["id"]))
            self.store.audit(con, p.user_id, action, now, row["repo_id"], row["id"])
            return {"rfc_id": row["id"], "restricted": bool(data.get("restricted", True))}
        if action == "rfcs.work":
            row = self._rfc(con, p, data.get("rfc_id", ""), "contributor")
            model = json.loads(row["model"])
            op, feature = data.get("op", "update"), dict(data.get("feature", {}))
            fid = data.get("feature_id", feature.get("id", ""))
            existing = next((f for f in model["features"] if f["id"] == fid), None)
            if op == "add":
                self._require(con, p, row["repo_id"], "maintainer", row["id"])
                if existing or fid in model["tombstones"]:
                    raise RFCError("Feature exists or was intentionally removed; restore explicitly", 409, "conflict")
                feature = self._features([feature], validate=False)[0]
                feature["sidecar"] = True
                model["features"].append(feature)
            elif op in ("drop", "restore"):
                self._require(con, p, row["repo_id"], "maintainer", row["id"])
                if not existing:
                    raise RFCError("Feature not found", 404, "not_found")
                existing["dropped"] = op == "drop"
                model["tombstones"] = sorted((set(model["tombstones"]) | {fid}) if op == "drop" else set(model["tombstones"]) - {fid})
            elif op == "claim" and existing:
                if existing.get("owner"):
                    raise RFCError("Work already has an owner; record a maintainer decision to reassign", 409, "conflict")
                self._text(data.get("reason"), "Claim reason")
                existing.update(owner=p.name, owner_user_id=p.user_id)
                existing.setdefault("overrides", {})["owner"] = p.name
            elif op == "update" and existing:
                if any(k in feature and feature[k] != existing.get(k) for k in ("title", "track", "depends_on", "owner")):
                    self._require(con, p, row["repo_id"], "maintainer", row["id"])
                    self._text(data.get("reason"), "Explicit decision reason")
                for key in ("title", "track", "depends_on", "owner", "links", "state", "priority"):
                    if key in feature:
                        existing[key] = feature[key]
                        if key in ("title", "track", "depends_on", "owner"):
                            existing.setdefault("overrides", {})[key] = feature[key]
                if existing.get("state") not in ("planned", "in_progress", "implemented", "dropped"):
                    raise RFCError("Invalid work state")
            else:
                raise RFCError("Feature or operation not found", 404, "not_found")
            validate_features(model["features"])
            self._invalidate(model, "Work plan changed")
            self.store.audit(con, p.user_id, action, now, row["repo_id"], row["id"], {"op": op, "feature_id": fid, "reason": data.get("reason", "")})
            return self._save(con, p, row, model)
        if action == "rfcs.decision":
            row = self._rfc(con, p, data.get("rfc_id", ""), "contributor")
            model = json.loads(row["model"])
            kind = data.get("kind", "criterion")
            if kind == "criterion":
                criterion = next((c for c in model["criteria"] if c["id"] == data.get("criterion_id")), None)
                if not criterion:
                    raise RFCError("Criterion not found", 404, "not_found")
                verdict = data.get("verdict", "pending")
                evidence = data.get("evidence")
                if evidence:
                    if not isinstance(evidence, dict) or not evidence.get("revision") or not evidence.get("environment"):
                        raise RFCError("Evidence requires verification revision and environment")
                    evidence = {**evidence, "actor": p.user_id, "recorded_at": now, "tracking_revision": row["revision"], "stale": False}
                    criterion.setdefault("evidence", []).append(evidence)
                    model["freshness"]["evidence"] = now
                if verdict not in ("pending", "passing", "failing", "waived"):
                    raise RFCError("Invalid acceptance verdict")
                if verdict in ("passing", "waived", "failing"):
                    self._require(con, p, row["repo_id"], "maintainer", row["id"])
                if verdict == "passing" and not any(not e.get("stale") for e in criterion.get("evidence", [])):
                    raise RFCError("Passing acceptance requires current evidence")
                if verdict == "waived":
                    self._text(data.get("reason"), "Waiver reason")
                criterion.update(verdict=verdict, reason=data.get("reason", ""), decided_by=p.user_id, decided_at=now)
            elif kind == "suggestion":
                self._require(con, p, row["repo_id"], "maintainer", row["id"])
                item = next((s for s in model["suggestions"] if s["id"] == data.get("suggestion_id")), None)
                if not item or item.get("status") != "proposed":
                    raise RFCError("Pending suggestion not found", 404, "not_found")
                verdict = data.get("verdict")
                if verdict == "rejected":
                    item["status"] = "rejected"
                    model["tombstones"] = sorted(set(model["tombstones"]) | {item["id"]})
                elif verdict in ("applied", "accepted"):
                    self._apply_candidate(model, item, explicit=True)
                    item["status"] = "applied"
                    self._invalidate(model, "Suggestion changed the work plan")
                else:
                    raise RFCError("Suggestion verdict must be applied or rejected")
            elif kind == "rfc":
                self._require(con, p, row["repo_id"], "maintainer", row["id"])
                self._text(data.get("reason"), "Decision reason")
                model["state"] = data.get("verdict", "proposed")
                model.setdefault("decisions", []).append({"actor": p.user_id, "verdict": model["state"], "reason": data["reason"], "at": now})
            else:
                raise RFCError("Invalid decision kind")
            self.store.audit(con, p.user_id, action, now, row["repo_id"], row["id"], {"kind": kind, "reason": data.get("reason", "")})
            return self._save(con, p, row, model)
        if action in ("rfcs.publish", "rfcs.enroll", "rfcs.sync"):
            if data.get("rfc_id"):
                row = self._rfc(con, p, data["rfc_id"], "maintainer")
                rid, rfc_id = row["repo_id"], row["id"]
                if action in ("rfcs.publish", "rfcs.enroll") and con.execute("SELECT 1 FROM operations WHERE rfc_id=? AND kind IN ('rfcs.publish','rfcs.enroll') AND status IN ('pending','running','uncertain')", (rfc_id,)).fetchone():
                    raise RFCError("An existing publication or import must finish or be recovered first", 409, "write_in_progress")
                model = json.loads(row["model"])
                if model.get("writer_id", self.writer_id) != self.writer_id:
                    raise RFCError("This workspace is not the designated RFC writer", 409, "writer_conflict")
                if action == "rfcs.publish":
                    if (data.get("post") is not True or data.get("content_digest") != content_digest(row["title"], row["body"])
                            or (data.get("expected_revision") and data["expected_revision"] != row["revision"])):
                        raise RFCError("Publication requires explicit intent and the exact preview digest", 409, "preview_mismatch")
                    if row["enrolled"] or json.loads(row["source"]):
                        raise RFCError("RFC already has a source; enroll or revise it explicitly", 409, "conflict")
                    data = {**data, "title": row["title"], "body": row["body"], "expected_revision": row["revision"]}
                if action == "rfcs.sync" and not row["enrolled"]:
                    raise RFCError("RFC is not enrolled")
                if action == "rfcs.enroll":
                    data = {**data, "expected_revision": row["revision"]}
            else:
                if action != "rfcs.enroll":
                    raise RFCError("rfc_id is required")
                rid, rfc_id = data.get("repo_id", ""), ""
                self._require(con, p, rid, "maintainer")
                data = {**data, "source": self._source(con, rid, data.get("source", {}))}
            return self._enqueue(con, p, action, rid, rfc_id, data)
        if action == "operations.retry":
            row = con.execute("SELECT * FROM operations WHERE id=?", (data.get("operation_id", ""),)).fetchone()
            if not row:
                raise RFCError("Resource not found or access denied", 403, "forbidden")
            self._require(con, p, row["repo_id"], "maintainer", row["rfc_id"])
            if row["actor"] != p.user_id and not p.admin:
                raise RFCError("Only the initiating user or administrator can recover this operation", 403, "forbidden")
            if row["status"] not in ("failed", "uncertain"):
                raise RFCError("Only failed or uncertain operations can be retried", 409, "conflict")
            con.execute("UPDATE operations SET status='pending',credential_id=?,error='',updated=? WHERE id=?", (p.credential_id, now, row["id"]))
            self.store.audit(con, p.user_id, action, now, row["repo_id"], row["rfc_id"], {"operation_id": row["id"]})
            return self._operation(con.execute("SELECT * FROM operations WHERE id=?", (row["id"],)).fetchone())
        if action in ("operations.get", "operations.list"):
            rows = con.execute("SELECT * FROM operations WHERE id=?", (data.get("operation_id", ""),)) if action.endswith("get") else con.execute("SELECT * FROM operations ORDER BY created DESC LIMIT 200")
            result = []
            for row in rows:
                if self._role(con, p, row["repo_id"], row["rfc_id"]):
                    result.append(self._operation(row))
            if action.endswith("get"):
                if not result:
                    raise RFCError("Resource not found or access denied", 403, "forbidden")
                return result[0]
            return {"operations": result}
        if action == "audit.list":
            result = []
            for row in con.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 500"):
                if p.admin or (row["repo_id"] and self._role(con, p, row["repo_id"], row["rfc_id"])):
                    result.append({**dict(row), "detail": json.loads(row["detail"])})
            return {"events": result}
        raise RFCError("Unknown RFC action", 404, "unknown_action")

    def _source(self, con, repo_id, data):
        ref = SourceRef.from_dict(data)
        repo = con.execute("SELECT * FROM repositories WHERE id=?", (repo_id,)).fetchone()
        if not repo or ref.provider != repo["provider"] or ref.repository not in ("", repo["external_name"]):
            raise RFCError("Source must belong to the authorized repository", 403, "forbidden")
        return SourceRef.from_dict({**ref.to_dict(), "repository": repo["external_name"]}).to_dict()

    @staticmethod
    def _same_source(a, b):
        aliases = {"pull_request": "pr", "pull": "pr"}
        same_repository = a.repository.casefold() == b.repository.casefold() if a.provider == "github" else a.repository == b.repository
        return (a.provider == b.provider and same_repository
                and aliases.get(a.kind, a.kind) == aliases.get(b.kind, b.kind)
                and (a.identifier or a.path) == (b.identifier or b.path))

    def _registered_sources(self, con, repo_id, ref):
        repo = con.execute("SELECT root FROM repositories WHERE id=?", (repo_id,)).fetchone()
        target = (Path(repo["root"]) / (ref.path or ref.identifier)).resolve() if ref.provider == "local" and repo else None
        matches = []
        for r in con.execute("SELECT f.id,f.repo_id,f.source,r.root FROM rfcs f JOIN repositories r ON r.id=f.repo_id WHERE f.source!='{}'"):
            registered = SourceRef.from_dict(json.loads(r["source"]))
            same = self._same_source(registered, ref)
            if target and registered.provider == "local":
                same = target == (Path(r["root"]) / (registered.path or registered.identifier)).resolve()
            if same:
                matches.append(dict(r))
        return matches

    def _source_access(self, con, principal, repo_id, ref):
        for r in self._registered_sources(con, repo_id, ref):
            self._require(con, principal, r["repo_id"], "reader", r["id"])

    def _visible_source(self, con, principal, repo_id, source):
        if not source:
            return True
        try:
            self._source_access(con, principal, repo_id, SourceRef.from_dict(source))
            return True
        except RFCError:
            return False

    def _view_visibility(self, con, principal, repo_id):
        """Build an ACL index for this transaction only; never cache user authority."""
        roots = {r["id"]: r["root"] for r in con.execute("SELECT id,root FROM repositories")}
        blocked, blocked_paths = set(), set()
        aliases = {"pull_request": "pr", "pull": "pr"}

        def identity(ref):
            repository = ref.repository.casefold() if ref.provider == "github" else ref.repository
            return ref.provider, repository, aliases.get(ref.kind, ref.kind), ref.identifier or ref.path

        for row in con.execute("SELECT id,repo_id,source FROM rfcs WHERE source!='{}'"):
            if ROLES.get(self._role(con, principal, row["repo_id"], row["id"]), 0) >= 1:
                continue
            ref = SourceRef.from_dict(json.loads(row["source"]))
            blocked.add(identity(ref))
            if ref.provider == "local":
                blocked_paths.add((Path(roots[row["repo_id"]]) / (ref.path or ref.identifier)).resolve())

        def visible(source):
            if not source:
                return True
            try:
                ref = SourceRef.from_dict(source)
                if ref.provider == "local" and repo_id in roots:
                    return (Path(roots[repo_id]) / (ref.path or ref.identifier)).resolve() not in blocked_paths
                return identity(ref) not in blocked
            except RFCError:
                return False
        return visible

    @staticmethod
    def _features(features, validate=True):
        if not isinstance(features, list):
            raise RFCError("Features must be a list")
        result = []
        for f in features:
            if not isinstance(f, dict) or not f.get("title"):
                raise RFCError("Each feature needs an identifier and title")
            if not isinstance(f.get("links", []), list) or any(not isinstance(link, str) for link in f.get("links", [])):
                raise RFCError("Feature links must be URL strings")
            result.append({"track": "实现", "depends_on": [], "links": [], "owner": "", "state": "planned", "dropped": False, **f})
        if validate:
            validate_features(result)
        return result

    @staticmethod
    def _criteria(criteria):
        if not isinstance(criteria, list):
            raise RFCError("Criteria must be a list")
        result = []
        for c in criteria:
            if not isinstance(c, dict) or not c.get("title"):
                raise RFCError("Each criterion needs a title")
            result.append({"id": c.get("id", "C-" + digest(c["title"])[:12]), "title": c["title"], "feature_ids": c.get("feature_ids", []), "verdict": "pending", "evidence": []})
        if len({c["id"] for c in result}) != len(result):
            raise RFCError("Duplicate criterion identifiers")
        return result

    @staticmethod
    def _policy(model):
        value = model.get("max_auto_additions", 5)
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
            raise RFCError("max_auto_additions must be between 0 and 100")
        if not isinstance(model.get("auto_add"), bool) or not isinstance(model.get("scope"), str):
            raise RFCError("Invalid enrollment policy")

    @staticmethod
    def _invalidate(model, reason):
        for c in model.get("criteria", []):
            if c.get("verdict") == "passing":
                c["verdict"] = "pending"
            for evidence in c.get("evidence", []):
                evidence["stale"] = True
                evidence["stale_reason"] = reason

    def _enqueue(self, con, p, kind, repo_id, rfc_id, data):
        key = data.get("idempotency_key") or identifier("request")
        request_digest = self._request_digest(kind, repo_id, rfc_id, data)
        old = con.execute("SELECT * FROM operations WHERE actor=? AND idempotency_key=?", (p.user_id, key)).fetchone()
        if old:
            if old["request_digest"] != request_digest:
                raise RFCError("Idempotency key reused for a different operation", 409, "conflict")
            return {"operation_id": old["id"], "operation": self._operation(old)}
        operation_id = identifier("op")
        now = self.clock()
        con.execute("""INSERT INTO operations(id,actor,credential_id,kind,repo_id,rfc_id,payload,idempotency_key,request_digest,created,updated)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""", (operation_id, p.user_id, p.credential_id, kind, repo_id, rfc_id, encode(data), key, request_digest, now, now))
        self.store.audit(con, p.user_id, kind + ".queued", now, repo_id, rfc_id, {"operation_id": operation_id})
        row = con.execute("SELECT * FROM operations WHERE id=?", (operation_id,)).fetchone()
        return {"operation_id": operation_id, "operation": self._operation(row)}

    @staticmethod
    def _request_digest(kind, repo_id, rfc_id, data):
        data = dict(data)
        if kind == "rfcs.publish":
            for key in ("title", "body", "expected_revision"):
                data.pop(key, None)
        if kind == "rfcs.enroll":
            data.pop("expected_revision", None)
        return digest(encode({"kind": kind, "repo_id": repo_id, "rfc_id": rfc_id, "data": data}))

    @staticmethod
    def _operation(row):
        return {k: row[k] for k in ("id", "kind", "repo_id", "rfc_id", "status", "error", "created", "updated")} | {"operation_id": row["id"], "result": json.loads(row["result"])}

    def _provider(self, repo):
        provider = self.providers.get(repo["provider"])
        if not provider:
            raise RFCError("Provider is not configured", 503, "provider_unavailable")
        if repo["provider"] == "local":
            from .providers import LocalProvider
            return LocalProvider({repo["external_name"]: repo["root"]})
        return provider

    def _authority(self, operation, worker):
        with self.store.transaction() as con:
            self._held(con, operation["id"], worker)
            p = self._principal(con, operation["credential_id"])
            self._require(con, p, operation["repo_id"], "maintainer", operation["rfc_id"])
            repo = dict(con.execute("SELECT * FROM repositories WHERE id=?", (operation["repo_id"],)).fetchone())
            row = self._rfc(con, p, operation["rfc_id"], "maintainer") if operation["rfc_id"] else None
            if row and json.loads(row["model"]).get("writer_id", self.writer_id) != self.writer_id:
                raise RFCError("This workspace is not the designated RFC writer", 409, "writer_conflict")
            return p, repo, row

    def _held(self, con, operation_id, worker):
        if not con.execute("SELECT 1 FROM operations WHERE id=? AND status='running' AND worker=? AND lease_until>?", (operation_id, worker, self.clock())).fetchone():
            raise RFCError("Write lease lost", 409, "lease_lost")

    def process_pending(self, limit=10):
        worker, results = identifier("worker"), []
        for _ in range(max(0, int(limit))):
            op = self.store.claim(worker, self.clock())
            if not op:
                break
            stop = threading.Event()
            def keep_lease():
                while not stop.wait(60):
                    if not self.store.renew(op["id"], worker, self.clock()):
                        return
            keeper = threading.Thread(target=keep_lease, daemon=True)
            keeper.start()
            status, result, error = "succeeded", {}, ""
            try:
                result = self._execute(op, worker)
            except ProviderError as exc:
                # Never blindly create again following an ambiguous external response.
                status = "uncertain" if exc.uncertain else "failed"
                error = str(exc)
            except RFCError as exc:
                status, error = "failed", str(exc)
            except Exception:
                status, error = "failed", "Operation failed; inspect server diagnostics"
            finally:
                stop.set()
                keeper.join(timeout=2)
            with self.store.transaction() as con:
                changed = con.execute("UPDATE operations SET status=?,result=?,error=?,updated=?,lease_until=0 WHERE id=? AND worker=? AND status='running'",
                                      (status, encode(result), error, self.clock(), op["id"], worker)).rowcount
                if changed:
                    executed = con.execute("SELECT user_id FROM tokens WHERE id=?", (op["credential_id"],)).fetchone()
                    self.store.audit(con, executed["user_id"] if executed else op["actor"], op["kind"] + "." + status, self.clock(), op["repo_id"], result.get("rfc_id", op["rfc_id"]), {"operation_id": op["id"], "initiated_by": op["actor"]})
            results.append({"operation_id": op["id"], "status": status, "error": error, "result": result})
        return results

    def _execute(self, op, worker):
        p, repo, row = self._authority(op, worker)
        data, kind = json.loads(op["payload"]), op["kind"]
        provider = self._provider(repo)
        if kind == "rfcs.publish":
            if row["enrolled"] and json.loads(row["source"]):
                recovered = provider.find_publication(repo["external_name"], op["id"])
                if recovered and recovered.identity() == SourceRef.from_dict(json.loads(row["source"])).identity():
                    return {"rfc_id": row["id"], "source": {k: v for k, v in recovered.to_dict().items() if k != "path"}}
            if row["revision"] != data["expected_revision"]:
                raise RFCError("Draft changed after preview; review again", 409, "preview_mismatch")
            # Reconcile before every create (also after restart with an expired lease).
            source = provider.find_publication(repo["external_name"], op["id"])
            if source is None:
                self._authority(op, worker)
                source = provider.publish(repo["external_name"], data["title"], data["body"], op["id"], path=data.get("path", ""))
            if isinstance(source, dict):
                source = SourceRef.from_dict(source)
            fetched = provider.get_source(source)
            if fetched.get("source"):
                source = SourceRef.from_dict(fetched["source"])
            self._authority(op, worker)
            with self.store.transaction() as con:
                self._held(con, op["id"], worker)
                p = self._current(con, p)
                current = self._rfc(con, p, row["id"], "maintainer")
                model = json.loads(current["model"])
                model.update(state="proposed", writer_id=self.writer_id,
                             enrollment={"actor": p.user_id, "credential_id": p.credential_id})
                model["freshness"]["publication"] = self.clock()
                con.execute("UPDATE rfcs SET source=?,enrolled=1 WHERE id=?", (encode(source.to_dict()), row["id"]))
                con.execute("INSERT INTO source_snapshots(rfc_id,revision,body,created) VALUES (?,?,?,?)", (row["id"], str(fetched.get("revision", "")), fetched.get("body", data["body"]), self.clock()))
                self._save(con, p, current, parse(fetched["body"], model), fetched["body"])
            return {"rfc_id": row["id"], "source": {k: v for k, v in source.to_dict().items() if k != "path"}}
        if kind == "rfcs.enroll":
            if row and data.get("expected_revision") != row["revision"]:
                raise RFCError("Imported draft changed after review", 409, "preview_mismatch")
            source_data = json.loads(row["source"]) if row else data["source"]
            if not source_data:
                raise RFCError("RFC has no published source; publish first")
            source = SourceRef.from_dict(source_data)
            with self.store.transaction() as con:
                self._source_access(con, p, repo["id"], source)
            fetched = provider.get_source(source)
            if fetched.get("source"):
                source = SourceRef.from_dict(fetched["source"])
            if row and not row["enrolled"] and row["body"] != fetched["body"]:
                raise RFCError("Source changed or draft differs from source; preview the current source before enrolling", 409, "preview_mismatch")
            self._authority(op, worker)
            with self.store.transaction() as con:
                self._held(con, op["id"], worker)
                p = self._current(con, p)
                self._require(con, p, repo["id"], "maintainer", row["id"] if row else "")
                self._source_access(con, p, repo["id"], source)
                # Stable identity prevents duplicate registration within a workspace.
                for existing in con.execute("SELECT * FROM rfcs WHERE repo_id=?", (repo["id"],)):
                    if json.loads(existing["source"]) and self._same_source(SourceRef.from_dict(json.loads(existing["source"])), source) and (not row or existing["id"] != row["id"]):
                        raise RFCError("Source is already registered", 409, "conflict")
                if not row:
                    rid = identifier("rfc")
                    body, title = fetched["body"], fetched.get("title", "Imported RFC")
                    model = parse(body)
                    model.update(scope=data.get("scope", ""), auto_add=data.get("auto_add", True),
                                 max_auto_additions=data.get("max_auto_additions", self.settings()["default_max_auto_additions"]))
                    con.execute("INSERT INTO rfcs VALUES (?,?,?,?,?,?,?,?,?,?,?)", (rid, repo["id"], title, body, digest(body), encode(source.to_dict()), encode(model), 0, 0, p.user_id, self.clock()))
                    row = dict(con.execute("SELECT * FROM rfcs WHERE id=?", (rid,)).fetchone())
                else:
                    row = self._rfc(con, p, row["id"], "maintainer")
                    model = parse(fetched["body"], json.loads(row["model"]))
                    if fetched["body"] != row["body"]:
                        self._invalidate(model, "Source changed during reauthorization")
                model.update(writer_id=self.writer_id, enrollment={"actor": p.user_id, "credential_id": p.credential_id}, state="proposed")
                self._policy(model)
                model["freshness"]["verification"] = self.clock()
                con.execute("UPDATE rfcs SET enrolled=1,source=? WHERE id=?", (encode(source.to_dict()), row["id"]))
                con.execute("INSERT INTO source_snapshots(rfc_id,revision,body,created) VALUES (?,?,?,?)", (row["id"], str(fetched.get("revision", "")), fetched["body"], self.clock()))
                self._save(con, p, row, model, fetched["body"])
                con.execute("UPDATE operations SET rfc_id=? WHERE id=?", (row["id"], op["id"]))
            return {"rfc_id": row["id"], "enrolled": True}
        if kind == "rfcs.sync":
            if not row["enrolled"]:
                raise RFCError("RFC is not enrolled")
            sync_started = self.clock()
            original = json.loads(row["model"])
            source = SourceRef.from_dict(json.loads(row["source"]))
            fetched = provider.get_source(source)
            model = parse(fetched["body"], original)
            removed = {f["id"] for f in original["features"] if not f.get("sidecar")} - {f["id"] for f in model["features"]}
            model["tombstones"] = sorted(set(model["tombstones"]) | removed)
            for f in model["features"]:
                if f["id"] in model["tombstones"]:
                    f["dropped"] = True
            observations = copy.deepcopy(original.get("observations", {}))
            verified = {}
            for feature in model["features"]:
                if feature.get("dropped"):
                    continue
                for link in feature.get("links", []):
                    ref = self._link_ref(link, repo, source)
                    if ref:
                        if ref.identity() not in verified:
                            verified[ref.identity()] = provider.get_item(ref)
                        observed = copy.deepcopy(verified[ref.identity()])
                        observed.pop("body", None)
                        # Only implementation PRs affect merge progress; issues remain associations.
                        observed["kind"] = ref.kind
                        prior = observations.get(link)
                        if prior and prior.get("revision") != observed.get("revision"):
                            self._invalidate(model, "Linked implementation revision changed")
                        observations[link] = observed
            model["observations"] = observations
            model["freshness"]["verification"] = self.clock()
            if fetched["body"] != row["body"]:
                self._invalidate(model, "Source RFC changed")
            cursor = original.get("discovery_cursor", 0)
            since = datetime.fromtimestamp(max(0, cursor - 60), timezone.utc).isoformat() if cursor else ""
            candidates = provider.discover(repo["external_name"], {"rfc_id": row["id"], "source": source.to_dict(), "scope": model.get("scope", ""), "features": model["features"]}, since=since)
            applied = 0
            known = {s["id"] for s in model["suggestions"]} | set(model["tombstones"])
            for candidate in candidates:
                candidate_source = candidate.get("source")
                if candidate_source:
                    candidate_ref = SourceRef.from_dict(candidate_source.to_dict() if isinstance(candidate_source, SourceRef) else candidate_source)
                    with self.store.transaction() as con:
                        registered_source = bool(self._registered_sources(con, repo["id"], candidate_ref))
                    if registered_source:
                        continue
                item = self._candidate(candidate, row, model)
                if item["id"] in known or self._candidate_exists(model, item):
                    continue
                if model["auto_add"] and applied < model["max_auto_additions"] and item.get("bounded"):
                    self._apply_candidate(model, item)
                    item["status"] = "applied"
                    applied += 1
                model["suggestions"].append(item)
                known.add(item["id"])
            if applied:
                self._invalidate(model, "Related work changed the work plan")
            model["freshness"]["discovery"] = self.clock()
            model["discovery_cursor"] = sync_started
            model["last_discovery"] = {"proposed": sum(s.get("status") == "proposed" for s in model["suggestions"]), "applied": applied}
            self._authority(op, worker)
            with self.store.transaction() as con:
                self._held(con, op["id"], worker)
                p = self._current(con, p)
                current = self._rfc(con, p, row["id"], "maintainer")
                if current["revision"] != row["revision"]:
                    raise RFCError("Tracking changed during synchronization; retry", 409, "conflict")
                con.execute("INSERT INTO source_snapshots(rfc_id,revision,body,created) VALUES (?,?,?,?)", (row["id"], str(fetched.get("revision", "")), fetched["body"], self.clock()))
                self._save(con, p, current, model, fetched["body"])
            return {"rfc_id": row["id"], "applied": applied, "proposed": model["last_discovery"]["proposed"]}
        raise RFCError("Unknown queued operation")

    @staticmethod
    def _link_ref(link, repo, source):
        if repo["provider"] == "local":
            commit = re.fullmatch(r"git:([0-9a-fA-F]{7,64})", link)
            return SourceRef("local", repo["external_name"], "commit", commit[1]) if commit else None
        parsed = urlparse(link)
        expected = urlparse(source.url).hostname
        if expected and parsed.hostname != expected:
            return None
        match = re.fullmatch(r"/([^/]+/[^/]+)/(issues|pulls?|merge_requests)/([^/]+?)/?", parsed.path)
        if not match or match[1].casefold() != repo["external_name"].casefold():
            return None
        return SourceRef(repo["provider"], repo["external_name"], "issue" if match[2] == "issues" else "pr", match[3], link, host=source.host)

    @staticmethod
    def _candidate(candidate, row, model):
        item = dict(candidate)
        source = item.get("source", {})
        if isinstance(source, SourceRef):
            source = source.to_dict()
        url = item.get("url") or source.get("url", "")
        if not url and source.get("provider") == "local":
            url = "local:" + (source.get("path") or source.get("identifier", ""))
        key = "suggestion-" + digest(encode(source) if source else url + item.get("title", ""))[:20]
        feature = dict(item.get("feature", {}))
        if not feature:
            feature = {"id": "F-" + digest(key)[:12], "title": item.get("title", "Related work"), "track": item.get("track", ""), "links": [url] if url else []}
        features = model["features"]
        ref = json.loads(row["source"])
        text = item.get("body", "") + " " + item.get("reason", "")
        references = [ref.get("url"), "imrfc:" + row["id"]]
        if ref.get("provider") == "local":
            references.append("RFC:" + (ref.get("path") or ref.get("identifier", "")))
        explicit = any(value and value in text for value in references)
        if ref.get("provider") == "local":
            path = ref.get("path") or ref.get("identifier", "")
            explicit = explicit or bool(path and re.search(
                r"(?im)^\s*(?:RFC|RFC source|RFC来源)\s*[:：]\s*`?" + re.escape(path) + r"`?\s*$", item.get("body", "")))
        track_ok = feature.get("track") in {f["track"] for f in features}
        feature_id = item.get("feature_id", "")
        attaches = feature_id in {f["id"] for f in features if not f.get("dropped")}
        # Conservative adapter evidence: references and exact existing work lanes are required.
        bounded = explicit and (attaches or (track_ok and bool(model.get("scope")) and item.get("within_scope") is True))
        return {"id": key, "feature": feature, "feature_id": feature_id, "url": url,
                "evidence": item.get("evidence", {"source": source, "reference": ref.get("url", "")}),
                "reason": item.get("reason", "Review relationship and scope"), "status": "proposed", "bounded": bounded}

    @staticmethod
    def _candidate_exists(model, item):
        return bool(item["url"] and any(item["url"] in f.get("links", []) for f in model["features"]))

    def _apply_candidate(self, model, item, explicit=False):
        if item["id"] in model["tombstones"]:
            raise RFCError("Suggestion was intentionally rejected", 409, "conflict")
        existing = next((f for f in model["features"] if f["id"] == item.get("feature_id")), None)
        if existing:
            if item["url"] and item["url"] not in existing["links"]:
                existing["links"].append(item["url"])
            return
        feature = dict(item["feature"])
        if feature.get("id") in model["tombstones"]:
            raise RFCError("Feature was intentionally removed", 409, "conflict")
        if any(f["id"] == feature.get("id") for f in model["features"]):
            raise RFCError("Feature identifier already exists", 409, "conflict")
        if not explicit and (feature.get("owner") or feature.get("depends_on") or feature.get("criteria")):
            raise RFCError("Automatic discovery cannot change ownership or acceptance")
        feature = self._features([feature], validate=False)[0]
        feature["sidecar"] = True
        feature["auto_source"] = item.get("evidence", {}).get("source", {})
        model["features"].append(feature)
        validate_features(model["features"])

    def sync_due(self):
        queued = []
        with self.store.transaction() as con:
            for row in con.execute("SELECT * FROM rfcs WHERE enrolled=1"):
                model = json.loads(row["model"])
                if model.get("writer_id") != self.writer_id:
                    continue
                if self.clock() - model.get("freshness", {}).get("verification", 0) < self.settings()["sync_seconds"]:
                    continue
                if con.execute("SELECT 1 FROM operations WHERE rfc_id=? AND status IN ('pending','running','uncertain')", (row["id"],)).fetchone():
                    continue
                enrollment = model.get("enrollment", {})
                try:
                    p = self._principal(con, enrollment.get("credential_id", ""))
                    self._require(con, p, row["repo_id"], "maintainer", row["id"])
                except RFCError:
                    continue
                queued.append(self._enqueue(con, p, "rfcs.sync", row["repo_id"], row["id"], {"rfc_id": row["id"]})["operation_id"])
        return {"queued": queued}


def build_service(state_dir, config_path=None):
    """Build providers from execution-host credentials; no fallback to another state."""
    from .providers import AtomGitProvider, GitHubProvider, LocalProvider
    config = json.loads(Path(config_path).expanduser().read_text(encoding="utf-8")) if config_path else {}
    roots = config.get("roots", [])
    providers = {"local": LocalProvider({})}
    classes = {"github": (GitHubProvider, "GITHUB_TOKEN"), "atomgit": (AtomGitProvider, "ATOMGIT_TOKEN")}
    for name, (cls, default_env) in classes.items():
        opts = config.get("providers", {}).get(name, {})
        kwargs = {"token": os.environ.get(opts.get("token_env", default_env), "")}
        if opts.get("api_url"):
            kwargs["api_url"] = opts["api_url"]
        providers[name] = cls(**kwargs)
    return RFCService(state_dir, providers=providers, roots=roots)
