"""Private chat travels through SDK, CLI and MCP without a separate identity."""
import json
import threading

import pytest

from infermatrix_copilot.rfc_service.application import build_service
from infermatrix_copilot.rfc_service.http import create_server
from infermatrix_copilot.sdk.v1 import RFCClient, RFCClientError


def test_chat_round_is_durable_across_http_cli_and_mcp(tmp_path, monkeypatch, capsys):
    from infermatrix_copilot.rfc_service.cli import main
    from test_thin_mcp_server import _fake_mcp

    service = build_service(tmp_path / "state")
    service.chat.agent = object()  # Creating/reading a thread never invokes a model.
    issued = service.bootstrap_admin("Owner")
    owner = service.authenticate(issued["token"])
    repo = service.dispatch(owner, "repositories.create", {"name": "Chat integration", "provider": "local"})
    rfc = service.dispatch(owner, "rfcs.draft", {"repo_id": repo["id"], "title": "Discussion",
        "body": "# Discussion\n\n## Goals\n\nDiscuss a portable service.\n"})
    server = create_server(service)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        client = RFCClient(service_url=server.public_url, token=issued["token"])
        thread = client.chat_create(rfc["id"])["thread"]
        assert client.chat_list(rfc["id"])["threads"][0]["id"] == thread["id"]
        monkeypatch.setenv("RFC_SERVICE_URL", server.public_url)
        monkeypatch.setenv("RFC_TOKEN", issued["token"])
        payload = tmp_path / "get.json"
        payload.write_text(json.dumps({"thread_id": thread["id"]}), encoding="utf-8")
        assert main(["request", "chat.get", "--data", str(payload)]) == 0
        cli_view = json.loads(capsys.readouterr().out)
        assert cli_view["thread"]["id"] == thread["id"]
        mcp, _ = _fake_mcp(monkeypatch)
        assert mcp.tools["rfc_request"]("chat.get", {"thread_id": thread["id"]})["thread"]["id"] == thread["id"]

        # Another current repository reader cannot read the owner's conversation.
        other = service.dispatch(owner, "users.create", {"name": "Other reader"})
        other_token = service.dispatch(owner, "tokens.create", {"user_id": other["id"]})
        service.dispatch(owner, "grants.set", {"repo_id": repo["id"], "user_id": other["id"], "role": "reader"})
        with pytest.raises(RFCClientError) as denied:
            RFCClient(service_url=server.public_url, token=other_token["token"]).chat_get(thread["id"])
        assert denied.value.status in (403, 404)
        with pytest.raises(RFCClientError) as anonymous:
            RFCClient(service_url=server.public_url, token="invalid").chat_list(rfc["id"])
        assert anonymous.value.status == 401
        client.chat_delete(thread["id"])
        assert client.chat_list(rfc["id"])["threads"] == []
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)
