"""Public RFC clients and entry points exercise one application contract."""
from __future__ import annotations

import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from infermatrix_copilot.sdk.v1 import RFCClient, RFCClientError, SourceRef


def test_rfc_sdk_import_has_no_application_or_server_side_effects():
    script = """
import sys
from infermatrix_copilot.sdk.v1 import RFCClient, SourceRef, RFC_API_VERSION
client = RFCClient(service_url='http://127.0.0.1:12345', token='example')
assert RFC_API_VERSION == '1.0.0'
assert SourceRef('local', path='RFC.md').identity()
assert not any(x in sys.modules for x in (
 'infermatrix_copilot.config', 'infermatrix_copilot.rfc_service.application',
 'infermatrix_copilot.rfc_service.http', 'infermatrix_copilot.mcp_server',
 'infermatrix_copilot.thin_mcp_server'))
"""
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_unavailable_remote_never_creates_local_state(tmp_path):
    # Reserve a local port, then close it to produce a reliable refused connection.
    server = ThreadingHTTPServer(("127.0.0.1", 0), BaseHTTPRequestHandler)
    port = server.server_port
    server.server_close()
    state = tmp_path / "unused"
    client = RFCClient(state_dir=state, service_url=f"http://127.0.0.1:{port}", token="secret", timeout=1)
    with pytest.raises(RFCClientError) as exc:
        client.list_rfcs()
    assert exc.value.code == "transport_error"
    assert "secret" not in str(exc.value)
    assert not state.exists()


@pytest.mark.parametrize("endpoint", ["http://service.example", "http://10.0.0.2:8765", "http://[2001:db8::1]"])
def test_client_refuses_cleartext_external_credentials(endpoint, monkeypatch):
    from urllib import request

    calls = []
    monkeypatch.setattr(request, "build_opener", lambda *args: calls.append(args))
    with pytest.raises(RFCClientError) as exc:
        RFCClient(service_url=endpoint, token="private")
    assert exc.value.code == "insecure_endpoint"
    assert "private" not in str(exc.value)
    assert calls == []


def test_incompatible_service_version_prevents_actions(monkeypatch):
    client = RFCClient(service_url="http://127.0.0.1:12345", token="example")
    calls = []
    def transport(path, payload=None):
        calls.append(path)
        return {"rfc_api_version": "2.0.0"}
    monkeypatch.setattr(client, "_http", transport)
    with pytest.raises(RFCClientError) as exc:
        client.draft({"repo_id": "repo", "title": "example"})
    assert exc.value.code == "incompatible_version"
    assert calls == ["/api/v1/capabilities"]


def test_http_client_does_not_forward_bearer_on_redirect():
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            requests.append((self.path, self.headers.get("Authorization")))
            self.send_response(302)
            self.send_header("Location", "/unexpected")
            self.end_headers()

        def do_GET(self):
            requests.append((self.path, self.headers.get("Authorization")))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"rfc_api_version":"1.0.0"}')

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = RFCClient(service_url=f"http://127.0.0.1:{server.server_port}", token="private")
        with pytest.raises(RFCClientError) as exc:
            client.list_rfcs()
        assert exc.value.status == 302
        assert requests == [("/api/v1/capabilities", "Bearer private"),
                            ("/api/v1/actions/rfcs.list", "Bearer private")]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def _workspace(tmp_path):
    from infermatrix_copilot.rfc_service.application import build_service

    service = build_service(tmp_path / "state")
    bootstrap = service.bootstrap_admin("Owner")
    client = RFCClient(state_dir=tmp_path / "state", token=bootstrap["token"])
    return service, bootstrap, client


def test_local_sdk_and_authenticated_http_return_the_same_rfc(tmp_path):
    from infermatrix_copilot.rfc_service.http import create_server

    service, bootstrap, local = _workspace(tmp_path)
    repo = local.dispatch("repositories.create", {"name": "Any repository", "provider": "local"})
    draft = local.draft({"repo_id": repo["id"], "title": "Portable RFC",
        "body": "# Portable RFC\n\n#### F1. Implementation\n\n## Acceptance criteria\n\n- Validate on Windows and Linux.\n"})
    server = create_server(service)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        remote = RFCClient(service_url=server.public_url, token=bootstrap["token"])
        assert remote.capabilities() == local.capabilities()
        assert remote.get(draft["id"]) == local.get(draft["id"])
        assert remote.get(draft["id"])["acceptance"] == "pending"
        with pytest.raises(RFCClientError) as exc:
            RFCClient(service_url=server.public_url, token="invalid").get(draft["id"])
        assert exc.value.status == 401
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_cli_bootstrap_and_private_import_need_no_model_credentials(tmp_path, monkeypatch, capsys):
    from infermatrix_copilot.rfc_service.cli import main

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("RFC_SERVICE_URL", raising=False)
    state = tmp_path / "state"
    assert main(["--state-dir", str(state), "bootstrap-admin", "--name", "Owner"]) == 0
    bootstrap = json.loads(capsys.readouterr().out)
    monkeypatch.setenv("RFC_TOKEN", bootstrap["token"])
    client = RFCClient(state_dir=state, token=bootstrap["token"])
    repo = client.dispatch("repositories.create", {"name": "Local RFCs", "provider": "local"})
    path = tmp_path / "RFC.md"
    path.write_text("# Existing RFC\n\n- [ ] Implement the change.\n", encoding="utf-8")
    assert main(["--state-dir", str(state), "import", "--repo", repo["id"], "--file", str(path)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["title"] == "Existing RFC"
    assert result["body"] == path.read_text(encoding="utf-8")
    assert result["state"] == "draft"
    assert main(["--state-dir", str(state), "publish", result["id"], "--content-digest",
                 result["content_digest"], "--idempotency-key", "example"]) == 2
    assert "requires --post" in capsys.readouterr().err
    assert client.dispatch("operations.list")["operations"] == []
    exported = tmp_path / "export.json"
    assert main(["--state-dir", str(state), "export", result["id"], "--format", "json", "--out", str(exported)]) == 0
    assert json.loads(exported.read_text(encoding="utf-8"))["markdown"] == result["body"]
    markdown = tmp_path / "export.md"
    assert main(["--state-dir", str(state), "export", result["id"], "--format", "markdown", "--out", str(markdown)]) == 0
    assert markdown.read_text(encoding="utf-8") == result["body"]


def test_local_cli_worker_completes_sdk_publication(tmp_path, monkeypatch, capsys):
    from infermatrix_copilot.rfc_service.cli import main

    service, bootstrap, client = _workspace(tmp_path)
    monkeypatch.setenv("RFC_TOKEN", bootstrap["token"])
    monkeypatch.delenv("RFC_SERVICE_URL", raising=False)
    repo = client.dispatch("repositories.create", {"name": "Publication", "provider": "local"})
    draft = client.draft({"repo_id": repo["id"], "title": "Local publication", "body": "# RFC\n\n- [ ] Implement a portable feature.\n"})
    operation = client.publish(draft["id"], content_digest=draft["content_digest"],
                               idempotency_key="publish-once", post=True)
    assert client.operation(operation["operation_id"])["status"] == "pending"
    assert main(["--state-dir", str(tmp_path / "state"), "--local", "sync", "--once"]) == 0
    capsys.readouterr()
    completed = client.operation(operation["operation_id"])
    assert completed["status"] == "succeeded", completed
    published = client.get(draft["id"])
    assert published["source"]["provider"] == "local"
    assert published["source"]["identifier"].endswith(".md")
    # Retrying the same intent identifies its durable operation, not another file.
    retried = client.publish(draft["id"], content_digest=draft["content_digest"],
                            idempotency_key="publish-once", post=True)
    assert retried["operation_id"] == operation["operation_id"]


def test_cli_crlf_source_import_enrollment_and_markdown_export_preserve_bytes(tmp_path, monkeypatch, capsys):
    from infermatrix_copilot.rfc_service.cli import main

    service, bootstrap, client = _workspace(tmp_path)
    monkeypatch.setenv("RFC_TOKEN", bootstrap["token"])
    monkeypatch.delenv("RFC_SERVICE_URL", raising=False)
    repo = client.dispatch("repositories.create", {"name": "Windows source", "provider": "local"})
    path = service.store.root / "files" / repo["id"] / "rfcs" / "windows.md"
    path.parent.mkdir()
    original = b"# Windows RFC\r\n\r\n#### F1. Portable implementation\r\n\r\n## Acceptance criteria\r\n\r\n- Preserve source line endings.\r\n"
    path.write_bytes(original)
    source_file = tmp_path / "source.json"
    source_file.write_text(json.dumps(SourceRef("local", repo["external_name"], "markdown",
        "rfcs/windows.md", path="rfcs/windows.md").to_dict()), encoding="utf-8")
    base = ["--state-dir", str(tmp_path / "state")]
    assert main([*base, "import", "--repo", repo["id"], "--file", str(path), "--source", str(source_file)]) == 0
    imported = json.loads(capsys.readouterr().out)
    assert imported["body"].encode("utf-8") == original
    assert main([*base, "enroll", imported["id"]]) == 0
    queued = json.loads(capsys.readouterr().out)
    assert main([*base, "sync", "--once"]) == 0
    capsys.readouterr()
    assert client.operation(queued["operation_id"])["status"] == "succeeded"
    output = tmp_path / "export.md"
    assert main([*base, "export", imported["id"], "--format", "markdown", "--out", str(output)]) == 0
    assert output.read_bytes() == original


def test_copilot_rfc_command_forwards_to_service_cli(monkeypatch):
    from infermatrix_copilot.cli.entry import main
    from infermatrix_copilot.rfc_service import cli

    calls = []
    monkeypatch.setattr(cli, "main", lambda argv: calls.append(argv) or 0)
    assert main(["rfc", "status", "rfc-example"]) == 0
    assert calls == [["status", "rfc-example"]]


def test_mcp_rfc_tools_use_host_identity_without_endpoint_parameters(monkeypatch):
    # Existing fixture supplies a lightweight transport; no MCP installation,
    # model backend or live source provider is involved.
    from test_thin_mcp_server import _fake_mcp

    calls = []
    class FakeClient:
        def dispatch(self, action, payload=None):
            calls.append((action, payload))
            return {"accepted": True}

    monkeypatch.setattr(RFCClient, "from_env", lambda: FakeClient())
    mcp, _ = _fake_mcp(monkeypatch)
    assert mcp.tools["rfc_status"]("rfc-1") == {"accepted": True}
    assert calls == [("rfcs.get", {"rfc_id": "rfc-1"})]
    import inspect

    assert list(inspect.signature(mcp.tools["rfc_request"]).parameters) == ["action", "payload"]
    assert mcp.tool_annotations["rfc_request"].readOnlyHint is False
