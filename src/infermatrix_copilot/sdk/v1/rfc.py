"""Portable RFC client; local application and HTTP are loaded only on use."""
from __future__ import annotations

import ipaddress
import json
import os
from pathlib import Path
from typing import Any
from urllib import error, parse, request

from ...rfc_service import RFC_API_VERSION
from ...rfc_service.models import Principal, RFCError, SourceRef
from .models import SDKError


class RFCClientError(SDKError):
    """Stable transport/domain failure without credentials in its message."""

    def __init__(self, message: str, *, code: str = "rfc_error", status: int = 400):
        super().__init__(message)
        self.code = code
        self.status = status


class _NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # never forward a bearer credential to another endpoint


class RFCClient:
    """Use one explicit local state directory or a configured RFC service.

    A remote failure is an error; it never initializes unrelated local state.
    Construction and public SDK imports do not load Copilot configuration,
    application services, model providers, or either MCP server.
    """

    def __init__(self, *, state_dir: str | Path | None = None,
                 service_url: str = "", token: str = "",
                 config_path: str | Path | None = None, timeout: float = 30):
        self.service_url = str(service_url).rstrip("/")
        if self.service_url:
            try:
                parsed = parse.urlsplit(self.service_url)
                parsed.port
            except ValueError:
                raise RFCClientError("Invalid RFC service endpoint") from None
            if (parsed.scheme not in {"http", "https"} or not parsed.hostname
                    or parsed.username or parsed.password or parsed.query or parsed.fragment):
                raise RFCClientError("RFC service URL must be an HTTP(S) endpoint")
            if parsed.scheme == "http":
                try:
                    loopback = ipaddress.ip_address(parsed.hostname).is_loopback
                except ValueError:
                    loopback = parsed.hostname.lower() == "localhost"
                if not loopback:
                    raise RFCClientError("An external RFC service requires HTTPS", code="insecure_endpoint")
        if timeout <= 0:
            raise RFCClientError("timeout must be positive")
        if not isinstance(token, str) or any(ch.isspace() for ch in token):
            raise RFCClientError("Invalid RFC user token", code="unauthenticated", status=401)
        self.state_dir = Path(state_dir).expanduser() if state_dir else None
        self.config_path = Path(config_path).expanduser() if config_path else None
        self._token = token
        self.timeout = timeout
        self._service = None
        self._version_checked = False

    @classmethod
    def from_env(cls) -> RFCClient:
        return cls(state_dir=os.environ.get("RFC_STATE_DIR"),
                   service_url=os.environ.get("RFC_SERVICE_URL", ""),
                   token=os.environ.get("RFC_TOKEN", ""),
                   config_path=os.environ.get("RFC_CONFIG"))

    def _local(self):
        if self._service is None:
            from ...rfc_service.application import build_service

            state = self.state_dir or Path.home() / ".infermatrix-copilot" / "rfc"
            self._service = build_service(state, config_path=self.config_path)
        return self._service

    def _http(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {"Accept": "application/json"}
        if self._token:
            headers["Authorization"] = "Bearer " + self._token
        body = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(self.service_url + path, data=body, headers=headers)
        opener = request.build_opener(_NoRedirect())
        try:
            with opener.open(req, timeout=self.timeout) as response:
                raw = response.read(4 * 1024 * 1024 + 1)
        except error.HTTPError as exc:
            # Only propagate structured application errors, not proxy HTML or
            # redirects that could echo private request headers.
            try:
                value = json.loads(exc.read(65536))
                detail = value.get("error", {})
            except (ValueError, AttributeError):
                detail = {}
            if not isinstance(detail, dict):
                detail = {}
            raise RFCClientError(str(detail.get("message") or "RFC service request refused"),
                                 code=str(detail.get("code") or "http_error"),
                                 status=exc.code) from None
        except (error.URLError, TimeoutError, OSError):
            raise RFCClientError("RFC service unavailable", code="transport_error", status=503) from None
        if len(raw) > 4 * 1024 * 1024:
            raise RFCClientError("RFC service response exceeds the client limit", code="invalid_response")
        try:
            value = json.loads(raw)
        except (ValueError, UnicodeError):
            raise RFCClientError("RFC service returned invalid JSON", code="invalid_response") from None
        if not isinstance(value, dict):
            raise RFCClientError("RFC service response must be an object", code="invalid_response")
        return value

    def capabilities(self) -> dict[str, Any]:
        if not self._token:
            raise RFCClientError("An RFC user token is required", code="unauthenticated", status=401)
        if self.service_url:
            result = self._http("/api/v1/capabilities")
        else:
            try:
                service = self._local()
                result = service.dispatch(service.authenticate(self._token), "capabilities", {})
            except RFCError as exc:
                raise RFCClientError(str(exc), code=exc.code, status=exc.status) from None
        version = result.get("rfc_api_version", result.get("api_version"))
        if not isinstance(version, str) or not version:
            raise RFCClientError("RFC service did not declare its API version", code="invalid_response")
        if version.split(".")[0] != RFC_API_VERSION.split(".")[0]:
            raise RFCClientError("Unsupported RFC service API version", code="incompatible_version")
        self._version_checked = True
        return result

    def dispatch(self, action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not isinstance(action, str) or not action or not all(
                part and part.replace("_", "").isalnum() for part in action.split(".")):
            raise RFCClientError("Invalid RFC action")
        if payload is not None and not isinstance(payload, dict):
            raise RFCClientError("RFC payload must be an object")
        if action == "capabilities":
            return self.capabilities()
        if not self._version_checked:
            self.capabilities()
        if self.service_url:
            return self._http("/api/v1/actions/" + parse.quote(action, safe="."), payload or {})
        try:
            service = self._local()
            return service.dispatch(service.authenticate(self._token), action, payload or {})
        except RFCError as exc:
            raise RFCClientError(str(exc), code=exc.code, status=exc.status) from None

    def list_rfcs(self, repo_id: str = "") -> dict[str, Any]:
        return self.dispatch("rfcs.list", {"repo_id": repo_id} if repo_id else {})

    def get(self, rfc_id: str) -> dict[str, Any]:
        return self.dispatch("rfcs.get", {"rfc_id": rfc_id})

    def draft(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.dispatch("rfcs.draft", payload)

    def enroll(self, rfc_id: str, **settings: Any) -> dict[str, Any]:
        return self.dispatch("rfcs.enroll", {**settings, "rfc_id": rfc_id})

    def sync(self, rfc_id: str) -> dict[str, Any]:
        return self.dispatch("rfcs.sync", {"rfc_id": rfc_id})

    def publish(self, rfc_id: str, *, content_digest: str, idempotency_key: str,
                post: bool = False, expected_revision: str | None = None,
                path: str | None = None) -> dict[str, Any]:
        payload = {"rfc_id": rfc_id, "content_digest": content_digest,
                   "idempotency_key": idempotency_key, "post": post}
        if expected_revision is not None:
            payload["expected_revision"] = expected_revision
        if path is not None:
            payload["path"] = path
        return self.dispatch("rfcs.publish", payload)

    def decision(self, rfc_id: str, **decision: Any) -> dict[str, Any]:
        return self.dispatch("rfcs.decision", {**decision, "rfc_id": rfc_id})

    def operation(self, operation_id: str) -> dict[str, Any]:
        return self.dispatch("operations.get", {"operation_id": operation_id})

    def export(self, rfc_id: str, format: str = "json") -> dict[str, Any]:
        return self.dispatch("rfcs.export", {"rfc_id": rfc_id, "format": format})
