"""Authenticated same-origin browser and HTTP transport for the RFC service.

The application owns every permission decision. This adapter never reads RFC
storage directly and does not trust proxy headers to establish its origin.
"""
from __future__ import annotations

import ipaddress
import json
import gzip
import hashlib
from functools import lru_cache
from http.cookies import CookieError, SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit

from .models import SESSION_TTL_SECONDS, RFCError

COOKIE_NAME = "imrfc_session"
MAX_BODY_BYTES = 1024 * 1024
_STATIC = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/roadmap": ("index.html", "text/html; charset=utf-8"),
    "/roadmap.html": ("index.html", "text/html; charset=utf-8"),
    "/roadmap-500ms-cn.html": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/roadmap-markdown.js": ("markdown-it.min.js", "text/javascript; charset=utf-8"),
    "/roadmap-graph.mjs": ("roadmap-graph.mjs", "text/javascript; charset=utf-8"),
    "/roadmap-markdown-display.mjs": ("roadmap-markdown-display.mjs", "text/javascript; charset=utf-8"),
    "/roadmap-components.mjs": ("roadmap-components.mjs", "text/javascript; charset=utf-8"),
    "/roadmap-locale.mjs": ("roadmap-locale.mjs", "text/javascript; charset=utf-8"),
    "/roadmap-mermaid.js": ("roadmap-mermaid.js", "text/javascript; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
}
_COLLECTIONS = {
    "repositories": "repositories.list", "rfcs": "rfcs.list",
    "users": "users.list", "tokens": "tokens.list",
    "operations": "operations.list", "audit": "audit.list",
}
_CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self'; "
    "connect-src 'self'; img-src 'self' data:; object-src 'none'; "
    "base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
)


@lru_cache(maxsize=16)
def _asset(name):
    body = files(__package__).joinpath("web", name).read_bytes()
    return body, gzip.compress(body, compresslevel=5, mtime=0), 'W/"' + hashlib.sha256(body).hexdigest() + '"'


def _accepts_gzip(value):
    preferences = {}
    for part in value.lower().split(","):
        name, *parameters = part.strip().split(";")
        quality = 1.0
        for parameter in parameters:
            if parameter.strip().startswith("q="):
                try:
                    quality = float(parameter.strip()[2:])
                except ValueError:
                    quality = 0.0
        preferences[name] = quality
    return preferences.get("gzip", preferences.get("*", 0.0)) > 0


def _loopback(host: str) -> bool:
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _origin(value: str) -> str:
    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError as exc:
        raise ValueError("Invalid public URL") from exc
    if (parts.scheme not in {"http", "https"} or not parts.hostname
            or parts.username or parts.password or parts.query or parts.fragment
            or parts.path not in {"", "/"}):
        raise ValueError("Public URL must be an HTTP(S) origin without a path")
    host = parts.hostname.lower()
    hostname = f"[{host}]" if ":" in host else host
    default_port = 443 if parts.scheme == "https" else 80
    return f"{parts.scheme}://{hostname}" + (f":{port}" if port and port != default_port else "")


class RFCRequestHandler(BaseHTTPRequestHandler):
    """No credentials, request bodies or private source URLs enter access logs."""

    server_version = "InferMatrixRFC/1"
    sys_version = ""

    def setup(self) -> None:
        self.request.settimeout(30)
        super().setup()

    def log_message(self, format: str, *args: Any) -> None:
        # Applications can audit actions through the domain event log instead.
        pass

    def _send(self, status: int, body: bytes = b"", *, content_type: str = "application/json; charset=utf-8",
              headers: dict[str, str] | None = None) -> None:
        headers = dict(headers or {})
        if status == 200 and len(body) >= 1024 and "Content-Encoding" not in headers and _accepts_gzip(self.headers.get("Accept-Encoding", "")):
            body = gzip.compress(body, compresslevel=5, mtime=0)
            headers["Content-Encoding"] = "gzip"
        headers.setdefault("Vary", "Accept-Encoding")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        if status not in (204, 304):
            self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", headers.pop("Cache-Control", "no-store"))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", _CSP)
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD" and body:
            self.wfile.write(body)

    def _json(self, result: Any, status: int = 200, headers: dict[str, str] | None = None) -> None:
        body = json.dumps(result, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self._send(status, body, headers=headers)

    def _error(self, error: RFCError) -> None:
        status = error.status if 400 <= error.status <= 599 else 500
        self._json({"error": {"code": error.code, "message": str(error)}}, status)

    def _run(self, callback: Any) -> None:
        try:
            callback()
        except RFCError as exc:
            self._error(exc)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            # Unexpected exceptions may contain credentials or private content.
            self._json({"error": {"code": "internal_error", "message": "The request could not be completed"}}, 500)

    def _path(self) -> tuple[str, dict[str, str]]:
        parts = urlsplit(self.path)
        if parts.scheme or parts.netloc:
            raise RFCError("Absolute request targets are not supported")
        path = parts.path
        query = {key: values[-1] for key, values in parse_qs(parts.query, keep_blank_values=True).items()}
        return path, query

    def _body(self) -> dict[str, Any]:
        if self.headers.get("Transfer-Encoding"):
            raise RFCError("Transfer encoding is not supported")
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError as exc:
            raise RFCError("Invalid content length") from exc
        if length < 0:
            raise RFCError("Content length is required", 411, "length_required")
        if length > MAX_BODY_BYTES:
            raise RFCError("Request body is too large", 413, "body_too_large")
        if self.headers.get_content_type() != "application/json":
            raise RFCError("Send an application/json request body", 415, "unsupported_media_type")
        try:
            data = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeError) as exc:
            raise RFCError("Invalid JSON request body") from exc
        if not isinstance(data, dict):
            raise RFCError("Request body must be a JSON object")
        return data

    def _cookie(self) -> str:
        raw = self.headers.get("Cookie", "")
        if len(raw) > 8192:
            raise RFCError("Invalid session", 401, "unauthenticated")
        cookies = SimpleCookie()
        try:
            cookies.load(raw)
        except CookieError as exc:
            raise RFCError("Invalid session", 401, "unauthenticated") from exc
        cookie = cookies.get(COOKIE_NAME)
        return cookie.value if cookie else ""

    def _check_origin(self) -> None:
        # Compare against explicit deployment configuration, never Host or X-Forwarded-*.
        request_origin = self.headers.get("Origin", "")
        try:
            matches = bool(request_origin) and _origin(request_origin) == self.server.public_origin
        except ValueError:
            matches = False
        if not matches:
            raise RFCError("This action requires the configured service origin", 403, "invalid_origin")

    def _principal(self, *, mutation: bool = False) -> Any:
        authorization = self.headers.get("Authorization")
        if authorization is not None:
            scheme, separator, token = authorization.partition(" ")
            if scheme.lower() != "bearer" or not separator or not token or len(token) > 4096:
                raise RFCError("A valid bearer token is required", 401, "unauthenticated")
            # Bearer requests are for CLI/SDK; browser cookie actions require Origin.
            return self.server.service.authenticate(token)
        session = self._cookie()
        if not session:
            raise RFCError("Sign in to access this service", 401, "unauthenticated")
        if mutation:
            self._check_origin()
        return self.server.service.authenticate_session(session)

    def _session_cookie(self, secret: str, *, revoke: bool = False) -> str:
        cookies = SimpleCookie()
        cookies[COOKIE_NAME] = "" if revoke else secret
        morsel = cookies[COOKIE_NAME]
        morsel["path"] = "/"
        morsel["httponly"] = True
        morsel["samesite"] = "Strict"
        if self.server.public_origin.startswith("https://"):
            morsel["secure"] = True
        morsel["max-age"] = "0" if revoke else str(SESSION_TTL_SECONDS)
        return morsel.OutputString()

    def _get(self) -> None:
        path, query = self._path()
        if path == "/roadmap-languages.json":
            self._json(self.server.service.translations.public_ui(query.get("language", "en")))
            return
        if path in _STATIC:
            name, mime = _STATIC[path]
            body, compressed, etag = _asset(name)
            headers = {}
            if name != "index.html":
                headers = {"ETag": etag, "Cache-Control": "public, max-age=0, must-revalidate"}
                if etag in [value.strip() for value in self.headers.get("If-None-Match", "").split(",")]:
                    self._send(304, content_type=mime, headers=headers)
                    return
            if _accepts_gzip(self.headers.get("Accept-Encoding", "")):
                body = compressed
                headers["Content-Encoding"] = "gzip"
            self._send(200, body, content_type=mime, headers=headers)
            return
        # Authenticate before selecting a data route, including legacy aliases.
        principal = self._principal()
        action = ""
        payload = dict(query)
        if path in {"/api/v1/me", "/api/v1/capabilities"}:
            action = path.rsplit("/", 1)[-1]
        elif path.startswith("/api/v1/"):
            segments = path[len("/api/v1/"):].split("/")
            if len(segments) == 1 and segments[0] in _COLLECTIONS:
                action = _COLLECTIONS[segments[0]]
            elif len(segments) in {2, 3} and segments[0] == "rfcs" and segments[1]:
                action = "rfcs.get" if len(segments) == 2 else "rfcs.export" if segments[2] == "export" else ""
                payload["rfc_id"] = unquote(segments[1])
            elif len(segments) == 2 and segments[0] == "operations" and segments[1]:
                action = "operations.get"
                payload["operation_id"] = unquote(segments[1])
        elif path in {"/roadmap-snapshot.json", "/roadmap-500ms-cn.json", "/roadmap-500ms-cn.md",
                      "/api/roadmap/claims", "/api/roadmap/priority", "/api/roadmap/tasks", "/api/roadmap/auto"}:
            action = "rfcs.get" if payload.get("rfc_id") else "legacy.get"
            if action == "legacy.get":
                payload = {"namespace": "wm-7074"}
        if not action:
            raise RFCError("Route not found", 404, "not_found")
        result = self.server.service.dispatch(principal, action, payload)
        if path == "/roadmap-500ms-cn.md":
            markdown = result.get("body", result.get("markdown", result.get("tracking", {}).get("body", "")))
            if not isinstance(markdown, str):
                raise RFCError("Markdown is unavailable", 404, "not_found")
            self._send(200, markdown.encode("utf-8"), content_type="text/markdown; charset=utf-8",
                       headers={"Content-Disposition": 'attachment; filename="rfc-roadmap.md"'})
            return
        extra = {"Content-Disposition": 'attachment; filename="rfc-export.json"'} if action == "rfcs.export" else None
        self._json(result, headers=extra)

    def _post(self) -> None:
        path, _ = self._path()
        if path == "/api/v1/session":
            self._check_origin()
            payload = self._body()
            token = payload.get("token")
            if not isinstance(token, str) or not token or len(token) > 4096:
                raise RFCError("A personal token is required", 401, "unauthenticated")
            secret, principal = self.server.service.create_session(token)
            # Only the browser cookie receives the secret; responses contain identity.
            identity = principal.to_dict() if hasattr(principal, "to_dict") else dict(principal)
            self._json({"principal": identity}, headers={"Set-Cookie": self._session_cookie(secret)})
            return
        principal = self._principal(mutation=True)
        if not path.startswith("/api/v1/actions/"):
            raise RFCError("Route not found", 404, "not_found")
        action = path[len("/api/v1/actions/"):]
        if not action or "/" in action or unquote(action) != action:
            raise RFCError("Invalid action")
        payload = self._body()
        result = self.server.service.dispatch(principal, action, payload)
        self._json(result)

    def _delete(self) -> None:
        path, _ = self._path()
        self._principal(mutation=True)
        if path != "/api/v1/session":
            raise RFCError("Route not found", 404, "not_found")
        self._check_origin()
        secret = self._cookie()
        if secret:
            self.server.service.revoke_session(secret)
        self._json({"ok": True}, headers={"Set-Cookie": self._session_cookie("", revoke=True)})

    def do_GET(self) -> None:
        self._run(self._get)

    def do_HEAD(self) -> None:
        self._run(self._get)

    def do_POST(self) -> None:
        self._run(self._post)

    def do_DELETE(self) -> None:
        self._run(self._delete)

    def do_OPTIONS(self) -> None:
        self._error(RFCError("Cross-origin requests are not supported", 405, "method_not_allowed"))


def create_server(service: Any, host: str = "127.0.0.1", port: int = 0,
                  public_url: str | None = None) -> ThreadingHTTPServer:
    """Construct a server. HTTP is limited to loopback development.

    For a production reverse proxy set ``public_url`` to its HTTPS origin.
    The server does not infer TLS or allowed origins from forwarded headers.
    """
    if public_url is not None:
        origin = _origin(public_url)
        if origin.startswith("http://") and (not _loopback(urlsplit(origin).hostname or "") or not _loopback(host)):
            raise ValueError("HTTP is only permitted on loopback; configure an HTTPS public URL")
    elif not _loopback(host):
        raise ValueError("A non-loopback listener requires an HTTPS public URL")
    else:
        origin = ""
    if ":" in host:
        import socket

        class IPv6Server(ThreadingHTTPServer):
            address_family = socket.AF_INET6

        server_class = IPv6Server
    else:
        server_class = ThreadingHTTPServer
    server = server_class((host, port), RFCRequestHandler)
    server.daemon_threads = True
    server.service = service
    if not origin:
        hostname = f"[{host}]" if ":" in host else host
        origin = _origin(f"http://{hostname}:{server.server_address[1]}")
    server.public_origin = origin
    server.public_url = origin
    return server


def serve(service: Any, host: str = "127.0.0.1", port: int = 8765,
          public_url: str | None = None) -> None:
    """Serve until interrupted; no scheduler or deployment daemon is required."""
    server = create_server(service, host=host, port=port, public_url=public_url)
    try:
        server.serve_forever(poll_interval=0.25)
    finally:
        server.server_close()
