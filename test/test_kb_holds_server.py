"""The hold-list endpoint serves exactly one signed file, read-only."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from infermatrix_copilot.kb_service.holds_server import make_handler
from infermatrix_copilot.knowledge_service import gate_verifier as gv
from infermatrix_copilot.knowledge_service.signing import sign


@pytest.fixture
def server(tmp_path):
    from http.server import ThreadingHTTPServer

    holds = tmp_path / "public" / "holds.json"
    srv = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(holds))
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield srv, holds, f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


def _status(url, method="GET"):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method=method), timeout=5) as response:
            return response.status, response.read(), response.headers
    except urllib.error.HTTPError as exc:
        return exc.code, b"", exc.headers


def test_the_signed_hold_list_is_served_and_verifies_through_the_gate(server):
    import time

    srv, holds, base = server
    key = Ed25519PrivateKey.generate()
    holds.parent.mkdir(parents=True)
    payload = {"issued_at": time.time(), "sequence": 3, "global": False, "repos": ["demo"], "prs": [7]}
    holds.write_text(json.dumps(sign("kb-holds", payload, key)))
    status, body, headers = _status(base + "/holds.json")
    assert status == 200 and headers["Cache-Control"] == "no-store"
    # exactly what the kb-gate verifier does with it
    envelope = gv.fetch_holds(base + "/holds.json")
    assert gv.verify_holds(envelope, key.public_key(), now=time.time())["prs"] == [7]


def test_nothing_else_is_served(server, tmp_path):
    srv, holds, base = server
    holds.parent.mkdir(parents=True)
    holds.write_text("{}")
    (tmp_path / "kb.db").write_text("secret ledger")
    for path in ("/", "/kb.db", "/../kb.db", "/public/", "/public/holds.json", "/holds.json/../kb.db"):
        assert _status(base + path)[0] == 404, path
    assert _status(base + "/holds.json", method="POST")[0] in (404, 405, 501)


def test_a_missing_hold_list_is_unavailable_not_empty(server):
    assert _status(server[2] + "/holds.json")[0] == 503
