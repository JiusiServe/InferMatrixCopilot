"""Real HTTP requests verify authentication boundaries and browser sessions."""
from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from http.client import HTTPConnection
from typing import Any

import pytest

from infermatrix_copilot.rfc_service.http import MAX_BODY_BYTES, create_server
from infermatrix_copilot.rfc_service.models import Principal, RFCError


class FakeService:
    def __init__(self) -> None:
        self.principal = Principal("alice", "Alice", False, "credential-id")
        self.sessions: dict[str, Principal] = {}
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def authenticate(self, token: str) -> Principal:
        if token != "personal-test-token":
            raise RFCError("Invalid token", 401, "unauthenticated")
        return self.principal

    def create_session(self, token: str) -> tuple[str, Principal]:
        principal = self.authenticate(token)
        self.sessions["opaque-session-secret"] = principal
        return "opaque-session-secret", principal

    def authenticate_session(self, cookie: str) -> Principal:
        if cookie not in self.sessions:
            raise RFCError("Invalid session", 401, "unauthenticated")
        return self.sessions[cookie]

    def revoke_session(self, cookie: str) -> None:
        self.sessions.pop(cookie, None)

    def dispatch(self, principal: Principal, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        assert principal == self.principal
        self.calls.append((action, payload))
        if action == "me":
            return principal.to_dict()
        if action == "capabilities":
            return {"api_version": "1.0.0"}
        if action == "rfcs.list":
            return {"rfcs": [{"id": "one", "title": "Private project"}]}
        if action == "legacy.get":
            return {"id": "legacy-one", "body": "# Private legacy RFC", "features": []}
        if action in {"rfcs.get", "rfcs.export"}:
            if payload.get("rfc_id") == "denied":
                raise RFCError("RFC access denied", 403, "forbidden")
            return {"id": payload["rfc_id"], "body": "Private design"}
        if action == "unsafe.failure":
            raise RuntimeError("sensitive-token-do-not-disclose")
        if action == "operations.get":
            return {"id": payload["operation_id"]}
        return {"ok": True, "action": action}


@contextmanager
def running(service: FakeService | None = None, *, public_url: str | None = None):
    service = service or FakeService()
    server = create_server(service, public_url=public_url)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    try:
        yield server, service
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def request(server: Any, method: str, path: str, payload: Any = None, *, headers: dict[str, str] | None = None,
            raw_body: bytes | None = None):
    connection = HTTPConnection("127.0.0.1", server.server_address[1], timeout=3)
    request_headers = dict(headers or {})
    body = raw_body
    if payload is not None:
        body = json.dumps(payload).encode()
        request_headers.setdefault("Content-Type", "application/json")
    connection.request(method, path, body=body, headers=request_headers)
    response = connection.getresponse()
    result = response.read()
    response_headers = {key.lower(): value for key, value in response.getheaders()}
    connection.close()
    return response.status, response_headers, result


def login(server: Any):
    status, headers, raw = request(server, "POST", "/api/v1/session", {"token": "personal-test-token"},
                                   headers={"Origin": server.public_origin})
    assert status == 200
    return headers["set-cookie"].split(";", 1)[0], headers, json.loads(raw)


@pytest.mark.parametrize("path", [
    "/api/v1/capabilities", "/api/v1/rfcs", "/api/v1/rfcs/one", "/api/v1/rfcs/one/export",
    "/api/v1/operations", "/api/v1/audit", "/roadmap-snapshot.json", "/api/roadmap/tasks",
    "/api/roadmap/claims", "/api/roadmap/priority", "/api/roadmap/auto", "/roadmap-500ms-cn.json",
    "/roadmap-500ms-cn.md", "/roadmap-backup.json", "/web/../../application.py",
])
def test_all_data_routes_require_authentication(path: str):
    with running() as (server, service):
        status, headers, raw = request(server, "GET", path)
        assert status == 401
        assert "private" not in raw.decode().lower()
        assert headers["cache-control"] == "no-store"
        assert not service.calls


def test_login_shell_contains_no_rfc_data_and_assets_are_allowlisted():
    with running() as (server, _):
        status, headers, raw = request(server, "GET", "/")
        assert status == 200
        assert "登录工作空间" in raw.decode()
        assert b"Private project" not in raw
        assert "frame-ancestors 'none'" in headers["content-security-policy"]
        assert request(server, "GET", "/app.js")[0] == 200
        assert request(server, "GET", "/style.css")[0] == 200
        assert request(server, "GET", "/models.py")[0] == 401


@pytest.mark.parametrize("path", ["/roadmap.html", "/roadmap-500ms-cn.html"])
def test_legacy_html_is_only_the_login_shell(path):
    with running() as (server, service):
        status, _, raw = request(server, "GET", path)
        assert status == 200
        assert "登录工作空间" in raw.decode()
        assert b"Private legacy" not in raw
        assert not service.calls


@pytest.mark.parametrize("path", ["/roadmap-snapshot.json", "/roadmap-500ms-cn.json", "/api/roadmap/claims", "/api/roadmap/priority", "/api/roadmap/tasks", "/api/roadmap/auto"])
def test_legacy_data_resolves_one_authorized_namespace_or_explicit_rfc(path):
    with running() as (server, service):
        bearer = {"Authorization": "Bearer personal-test-token"}
        status, _, raw = request(server, "GET", path, headers=bearer)
        assert status == 200
        assert json.loads(raw)["id"] == "legacy-one"
        assert service.calls[-1] == ("legacy.get", {"namespace": "wm-7074"})
        status, _, raw = request(server, "GET", path + "?rfc_id=string%3Aid", headers=bearer)
        assert status == 200
        assert json.loads(raw)["id"] == "string:id"
        assert service.calls[-1] == ("rfcs.get", {"rfc_id": "string:id"})


def test_legacy_markdown_is_authenticated_attachment_and_backups_are_not_served():
    with running() as (server, service):
        bearer = {"Authorization": "Bearer personal-test-token"}
        status, headers, raw = request(server, "GET", "/roadmap-500ms-cn.md", headers=bearer)
        assert status == 200
        assert headers["content-type"].startswith("text/markdown")
        assert "attachment" in headers["content-disposition"]
        assert raw == b"# Private legacy RFC"
        assert service.calls[-1] == ("legacy.get", {"namespace": "wm-7074"})
        for path in ("/roadmap-backup.json", "/roadmap-500ms-cn.md.bak", "/roadmap-old.html"):
            assert request(server, "GET", path)[0] == 401
            assert request(server, "GET", path, headers=bearer)[0] == 404


def test_bearer_transport_reads_and_mutates_without_browser_origin():
    with running() as (server, service):
        bearer = {"Authorization": "Bearer personal-test-token"}
        assert request(server, "GET", "/api/v1/capabilities", headers=bearer)[0] == 200
        status, _, raw = request(server, "POST", "/api/v1/actions/rfcs.draft", {"repo_id": "local"}, headers=bearer)
        assert status == 200
        assert json.loads(raw)["ok"] is True
        assert service.calls[-1] == ("rfcs.draft", {"repo_id": "local"})


def test_session_is_http_only_and_neither_credential_is_in_json():
    with running() as (server, _):
        cookie, headers, value = login(server)
        assert "HttpOnly" in headers["set-cookie"]
        assert "SameSite=Strict" in headers["set-cookie"]
        assert "Secure" not in headers["set-cookie"]
        assert value["principal"]["user_id"] == "alice"
        assert "personal-test-token" not in json.dumps(value)
        assert "opaque-session-secret" not in json.dumps(value)
        assert request(server, "GET", "/api/v1/rfcs", headers={"Cookie": cookie})[0] == 200


def test_https_cookie_uses_configured_origin_not_forwarded_host():
    with running(public_url="https://rfc.example.test") as (server, _):
        _, headers, _ = login(server)
        assert "Secure" in headers["set-cookie"]
        status, _, raw = request(server, "POST", "/api/v1/session", {"token": "personal-test-token"},
                                 headers={"Origin": "https://attacker.example", "X-Forwarded-Host": "attacker.example", "Host": "attacker.example"})
        assert status == 403
        assert json.loads(raw)["error"]["code"] == "invalid_origin"


@pytest.mark.parametrize("origin", [None, "https://attacker.example", "null"])
def test_cookie_mutations_require_the_same_origin(origin: str | None):
    with running() as (server, service):
        cookie, _, _ = login(server)
        headers = {"Cookie": cookie}
        if origin:
            headers["Origin"] = origin
        status, _, _ = request(server, "POST", "/api/v1/actions/rfcs.update", {"rfc_id": "one"}, headers=headers)
        assert status == 403
        assert not service.calls


def test_logout_revokes_cookie_and_clears_browser_state():
    with running() as (server, _):
        cookie, _, _ = login(server)
        headers = {"Cookie": cookie, "Origin": server.public_origin}
        assert request(server, "POST", "/api/v1/actions/rfcs.update", {"rfc_id": "one"}, headers=headers)[0] == 200
        status, response_headers, _ = request(server, "DELETE", "/api/v1/session", headers=headers)
        assert status == 200
        assert "Max-Age=0" in response_headers["set-cookie"]
        assert request(server, "GET", "/api/v1/rfcs", headers={"Cookie": cookie})[0] == 401


def test_core_permissions_are_enforced_for_reads_and_exports():
    with running() as (server, _):
        bearer = {"Authorization": "Bearer personal-test-token"}
        for path in ("/api/v1/rfcs/denied", "/api/v1/rfcs/denied/export"):
            status, _, raw = request(server, "GET", path, headers=bearer)
            assert status == 403
            assert json.loads(raw)["error"]["code"] == "forbidden"
            assert b"Private design" not in raw


def test_unexpected_errors_hide_secrets_and_request_logging_is_silent(capsys):
    with running() as (server, _):
        status, _, raw = request(server, "POST", "/api/v1/actions/unsafe.failure", {}, headers={"Authorization": "Bearer personal-test-token"})
        assert status == 500
        assert b"sensitive-token" not in raw
        assert json.loads(raw)["error"]["code"] == "internal_error"
    output = capsys.readouterr()
    assert not output.out
    assert not output.err


def test_malformed_and_oversized_bodies_never_reach_the_application():
    with running() as (server, service):
        headers = {"Authorization": "Bearer personal-test-token", "Content-Type": "application/json"}
        status, _, _ = request(server, "POST", "/api/v1/actions/rfcs.draft", raw_body=b"invalid-json", headers=headers)
        assert status == 400
        # The server rejects the advertised length before consuming an upload.
        # Sending a full oversized body can race its early connection close.
        status, _, _ = request(server, "POST", "/api/v1/actions/rfcs.draft", raw_body=b"",
                               headers={**headers, "Content-Length": str(MAX_BODY_BYTES + 1)})
        assert status == 413
        assert not service.calls


def test_http_deployments_are_limited_to_loopback():
    with pytest.raises(ValueError, match="HTTPS"):
        create_server(FakeService(), host="0.0.0.0")
    with pytest.raises(ValueError, match="HTTPS"):
        create_server(FakeService(), public_url="http://rfc.example.test")
    with pytest.raises(ValueError, match="HTTPS"):
        create_server(FakeService(), host="0.0.0.0", public_url="http://127.0.0.1")
    with pytest.raises(ValueError, match="origin"):
        create_server(FakeService(), public_url="https://rfc.example.test/subpath")


def test_opaque_ids_survive_routing_and_unknown_routes_fail_closed():
    with running() as (server, service):
        bearer = {"Authorization": "Bearer personal-test-token"}
        status, _, raw = request(server, "GET", "/api/v1/rfcs/string%3Aid/export", headers=bearer)
        assert status == 200
        assert json.loads(raw)["id"] == "string:id"
        assert service.calls[-1] == ("rfcs.export", {"rfc_id": "string:id"})
        status, _, raw = request(server, "GET", "/api/v1/operations/op%3Aone", headers=bearer)
        assert status == 200
        assert json.loads(raw)["id"] == "op:one"
        assert request(server, "GET", "/not-a-route", headers=bearer)[0] == 404


def test_real_service_session_obeys_changed_rfc_permissions_and_token_revocation(tmp_path):
    from infermatrix_copilot.rfc_service.application import build_service

    service = build_service(tmp_path)
    administrator = service.bootstrap_admin("Admin")
    admin = service.authenticate(administrator["token"])
    repository = service.dispatch(admin, "repositories.create", {"name": "Pilot", "provider": "local"})
    rfc = service.dispatch(admin, "rfcs.draft", {"repo_id": repository["id"], "title": "Restricted pilot"})
    user = service.dispatch(admin, "users.create", {"name": "Reader"})
    token = service.dispatch(admin, "tokens.create", {"user_id": user["id"]})
    service.dispatch(admin, "grants.set", {"repo_id": repository["id"], "user_id": user["id"], "role": "reader"})
    with running(service) as (server, _):
        status, headers, raw = request(server, "POST", "/api/v1/session", {"token": token["token"]},
                                       headers={"Origin": server.public_origin})
        assert status == 200
        assert token["token"].encode() not in raw
        browser = {"Cookie": headers["set-cookie"].split(";", 1)[0]}
        mutation = {**browser, "Origin": server.public_origin}
        status, _, raw = request(server, "GET", f"/api/v1/tokens?user_id={user['id']}", headers=browser)
        assert status == 200
        assert {record["user_id"] for record in json.loads(raw)["tokens"]} == {user["id"]}
        assert request(server, "GET", "/api/v1/users", headers=browser)[0] == 403
        assert request(server, "POST", "/api/v1/actions/service.settings", {}, headers=mutation)[0] == 403
        assert request(server, "POST", "/api/v1/actions/service.configure", {"sync_seconds": 60}, headers=mutation)[0] == 403
        assert request(server, "GET", f"/api/v1/tokens?user_id={admin.user_id}", headers=browser)[0] == 403
        assert request(server, "POST", "/api/v1/actions/tokens.create", {"user_id": admin.user_id}, headers=mutation)[0] == 403
        status, _, raw = request(server, "POST", "/api/v1/actions/tokens.create", {"user_id": user["id"], "expires_days": 7}, headers=mutation)
        assert status == 200
        own_token = json.loads(raw)
        assert service.authenticate(own_token["token"]).user_id == user["id"]
        assert request(server, "POST", "/api/v1/actions/tokens.revoke", {"token_id": administrator["token_id"]}, headers=mutation)[0] == 403
        assert request(server, "POST", "/api/v1/actions/tokens.revoke", {"token_id": own_token["token_id"]}, headers=mutation)[0] == 200
        with pytest.raises(RFCError, match="Authentication"):
            service.authenticate(own_token["token"])
        assert request(server, "GET", f"/api/v1/rfcs/{rfc['id']}", headers=browser)[0] == 200
        status, _, _ = request(server, "POST", "/api/v1/actions/rfcs.work", {"rfc_id": rfc["id"], "op": "claim", "feature_id": "F1"},
                               headers={**browser, "Origin": server.public_origin})
        assert status == 403
        service.dispatch(admin, "rfcs.acl", {"rfc_id": rfc["id"], "restricted": True, "grants": {}})
        assert request(server, "GET", f"/api/v1/rfcs/{rfc['id']}/export", headers=browser)[0] == 403
        status, _, raw = request(server, "GET", "/api/v1/rfcs", headers=browser)
        assert status == 200
        assert json.loads(raw)["rfcs"] == []
        service.dispatch(admin, "tokens.revoke", {"token_id": token["token_id"]})
        assert request(server, "GET", "/api/v1/capabilities", headers=browser)[0] == 401
