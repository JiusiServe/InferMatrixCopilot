"""The public, read-only endpoint for the signed hold list.

The kb-gate verifier (a GitHub-hosted runner with no secrets) reads the
service's signed hold list over HTTPS and fails any knowledge segment it
cannot fetch, verify, or that is stale. This server exposes exactly one file,
``<state_dir>/public/holds.json``, at ``GET /holds.json``; everything else is
404. It never lists directories, follows paths, accepts writes, or serves
anything but that signed file, so running it exposes nothing the kb-gate does
not already publish. Put TLS in front of it (the bot host's reverse proxy) and
set that URL as ``holds_url`` in ``.github/kb-gate/config.json``.
"""

from __future__ import annotations

import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROUTE = "/holds.json"
MAX_BYTES = 1 << 20


def make_handler(holds_path: Path):
    class HoldsHandler(BaseHTTPRequestHandler):
        server_version = "kb-holds"
        sys_version = ""

        def _serve(self, with_body: bool) -> None:
            if self.path.split("?", 1)[0] != ROUTE:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            try:
                data = holds_path.read_bytes()[:MAX_BYTES]
            except OSError:
                # no hold list yet: the gate treats unreachable as held
                self.send_error(HTTPStatus.SERVICE_UNAVAILABLE)
                return
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if with_body:
                self.wfile.write(data)

        def do_GET(self) -> None:  # noqa: N802 - http.server API
            self._serve(True)

        def do_HEAD(self) -> None:  # noqa: N802
            self._serve(False)

        def log_message(self, format: str, *args) -> None:  # noqa: A002 - quiet by default
            return

    return HoldsHandler


def serve_holds(state_dir: str | Path, *, host: str = "127.0.0.1", port: int = 8765,
                stop: threading.Event | None = None) -> ThreadingHTTPServer:
    """Serve until ``stop`` is set (blocking); returns the server when stopped."""
    server = ThreadingHTTPServer((host, port), make_handler(Path(state_dir) / "public" / "holds.json"))
    server.daemon_threads = True
    if stop is None:
        try:
            server.serve_forever()
        finally:
            server.server_close()
        return server
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    stop.wait()
    server.shutdown()
    server.server_close()
    return server
