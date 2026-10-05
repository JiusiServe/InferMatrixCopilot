"""Provider adapters for portable RFCs; network access stays on configured API hosts.

An injected transport is ``(method, url, headers, payload) ->
(status, response_headers, decoded_json)``. No provider retries a creation request:
callers recover its operation marker before deciding whether to publish again.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import secrets
from typing import Any, Callable, Iterator, Mapping
from urllib.error import HTTPError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .models import ProviderError, RFCError, SourceRef

Transport = Callable[[str, str, dict[str, str], dict[str, Any] | None], tuple[int, Mapping[str, str], Any]]
MAX_PAGES = 100
PAGE_SIZE = 100
MAX_DOCUMENT_BYTES = 4 * 1024 * 1024
_OPERATION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_COMPONENT = re.compile(r"^[A-Za-z0-9_.-]+$")


def _marker(operation_id: str) -> str:
    if not isinstance(operation_id, str) or not _OPERATION.fullmatch(operation_id):
        raise RFCError("Invalid publication operation identifier")
    return f"<!-- imrfc-operation:{operation_id} -->"


def _publication_body(body: str, operation_id: str) -> str:
    if not isinstance(body, str) or len(body.encode("utf-8")) > MAX_DOCUMENT_BYTES:
        raise RFCError("RFC body must be text within the document size limit")
    marker = _marker(operation_id)
    return body if marker in body else body.rstrip() + "\n\n" + marker + "\n"


def _title(title: str) -> str:
    if not isinstance(title, str) or not title.strip() or len(title) > 256 or "\n" in title:
        raise RFCError("RFC title must be a single nonempty line of at most 256 characters")
    return title.strip()


def _digest(value: str | bytes) -> str:
    return hashlib.sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()


def _revision(item: Mapping[str, Any]) -> str:
    relevant = {key: item.get(key) for key in ("title", "body", "updated_at", "state", "draft", "merged_at")}
    head = item.get("head")
    relevant["head_sha"] = head.get("sha", "") if isinstance(head, dict) else ""
    return _digest(json.dumps(relevant, sort_keys=True, ensure_ascii=False, separators=(",", ":")))


def _logins(values: Any) -> list[str]:
    if not isinstance(values, list):
        values = [values] if values else []
    result = []
    for value in values:
        login = value if isinstance(value, str) else (value.get("login") or value.get("username") or "") if isinstance(value, dict) else ""
        if isinstance(login, str) and login and login not in result:
            result.append(login)
    return result


def _state(item: Mapping[str, Any]) -> str:
    native = str(item.get("state") or "").lower()
    merge_time = item.get("merged_at")
    try:
        has_merge_time = isinstance(merge_time, str) and bool(datetime.fromisoformat(merge_time.replace("Z", "+00:00")))
    except ValueError:
        has_merge_time = False
    if native == "merged" or item.get("merged") is True or has_merge_time:
        return "merged"
    if native in ("closed", "close"):
        return "closed"
    if native in ("open", "opened", "reopen", "reopened"):
        return "draft" if item.get("draft") is True else "open"
    return "unknown"


def _scope_matches(title: str, body: str, labels: Any, scope: Any) -> list[str]:
    if isinstance(scope, dict):
        terms = scope.get("keywords") or []
        wanted_labels = scope.get("labels") or []
        if not terms:
            terms = re.findall(r"[\w-]{3,}", str(scope.get("scope") or scope.get("text") or scope.get("description") or ""))
    elif isinstance(scope, str):
        terms = re.findall(r"[\w-]{3,}", scope)
        wanted_labels = []
    else:
        raise RFCError("Discovery scope must be text or a scope object")
    if isinstance(terms, str):
        terms = [terms]
    if isinstance(wanted_labels, str):
        wanted_labels = [wanted_labels]
    stopwords = {"the", "and", "for", "with", "from", "this", "that", "into", "are", "only", "scope", "within", "related", "repository"}
    terms = [str(term).lower() for term in terms if str(term).lower() not in stopwords]
    text = (title + "\n" + body).lower()
    matched = [term for term in terms if term in text]
    names = {str(label.get("name", "") if isinstance(label, dict) else label).lower() for label in labels or []}
    matched += ["label:" + str(label) for label in wanted_labels if str(label).lower() in names]
    return list(dict.fromkeys(matched)) if terms or wanted_labels else ["enrolled repository"]


def _discovery_reference(scope: Any, text: str) -> str:
    """An exact backlink establishes a relationship; keywords only retrieve work."""
    if not isinstance(scope, dict) or not isinstance(scope.get("source"), dict):
        return ""
    source = scope["source"]
    url = source.get("url", "")
    if url:
        return url if re.search(re.escape(url) + r"(?=$|[\s<>)\]#?,.!;:])", text) else ""
    path = source.get("path") or source.get("identifier") or ""
    # Local relationships require a field, rather than an incidental path mention.
    references = re.findall(r"(?im)^\s*(?:RFC|RFC source|RFC来源)\s*[:：]\s*`?([^`\n]+?)`?\s*$", text)
    return path if path and path in references else ""


def _same_discovery_source(item: dict[str, Any], scope: Any) -> bool:
    if not isinstance(scope, dict) or not isinstance(scope.get("source"), dict):
        return False
    source, candidate = scope["source"], item.get("source", {})
    def kind(value):
        return "pr" if value in ("pr", "pull", "pull_request") else value
    return (source.get("provider") == candidate.get("provider")
            and source.get("repository") == candidate.get("repository")
            and kind(source.get("kind")) == kind(candidate.get("kind"))
            and (source.get("identifier") or source.get("path")) == (candidate.get("identifier") or candidate.get("path")))


def _annotate_discovery(item: dict[str, Any], scope: Any, matches: list[str]) -> dict[str, Any]:
    text = item["title"] + "\n" + item["body"]
    reference = _discovery_reference(scope, text)
    reason = "Matched enrolled scope: " + ", ".join(matches) if matches else "Explicit RFC reference"
    item.update(rationale=reason, reason=reason, evidence={"source": item["source"], "revision": item["revision"],
                "reference": reference, "scope_matches": matches}, within_scope=False)
    if not reference or not isinstance(scope, dict):
        return item
    features = [feature for feature in scope.get("features", []) if isinstance(feature, dict) and not feature.get("dropped")]
    named = [feature for feature in features if feature.get("id") and re.search(
        r"(?<![\w-])" + re.escape(feature["id"]) + r"(?![\w-])", text)]
    if len(named) == 1:
        item.update(feature_id=named[0]["id"], track=named[0].get("track", ""))
        item["evidence"]["feature_reference"] = named[0]["id"]
    elif not named:
        # New work requires declared lane and exact enrolled scope. A fuzzy keyword
        # overlap or a PR author cannot authorize scope, ownership or acceptance.
        tracks = re.findall(r"(?im)^\s*(?:Track|轨道)\s*[:：]\s*(.+?)\s*$", text)
        scopes = re.findall(r"(?im)^\s*(?:Scope|范围)\s*[:：]\s*(.+?)\s*$", text)
        allowed_tracks = {feature.get("track", "") for feature in features}
        declared = set(tracks) & allowed_tracks - {""}
        if len(declared) == 1:
            item["track"] = declared.pop()
            item["evidence"]["track_reference"] = item["track"]
            enrolled_scope = scope.get("scope", "")
            if enrolled_scope and scopes == [enrolled_scope]:
                item["within_scope"] = True
                item["evidence"]["scope_reference"] = enrolled_scope
    return item


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Authentication must never follow a redirect to an unconfigured host.
        return None


def _urllib_transport(method: str, url: str, headers: dict[str, str], payload: dict[str, Any] | None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with build_opener(_NoRedirect()).open(request, timeout=30) as response:
            raw = response.read(MAX_DOCUMENT_BYTES * 4 + 1)
            if len(raw) > MAX_DOCUMENT_BYTES * 4:
                raise ValueError("response too large")
            return response.status, dict(response.headers), json.loads(raw) if raw else None
    except HTTPError as error:
        # Never expose upstream messages, URLs or response bodies containing secrets.
        return error.code, dict(error.headers), None


class _HTTPProvider:
    name = ""
    default_api_url = ""
    default_web_hosts: tuple[str, ...] = ()

    def __init__(self, token: str = "", api_url: str = "", transport: Transport | None = None):
        parsed = urlsplit(api_url or self.default_api_url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise RFCError("Provider API URL must be a configured HTTPS origin and optional API path")
        self.api_url = (api_url or self.default_api_url).rstrip("/")
        self.api_host = parsed.hostname.lower()
        self.web_hosts = set(self.default_web_hosts) if self.api_host == urlsplit(self.default_api_url).hostname else {self.api_host}
        self.web_host = next(iter(self.default_web_hosts), self.api_host) if self.api_host == urlsplit(self.default_api_url).hostname else self.api_host
        self._token = token
        self._transport = transport or _urllib_transport

    def _repo(self, repository: str) -> tuple[str, str]:
        parts = repository.split("/") if isinstance(repository, str) else []
        if len(parts) != 2 or any(part in ("", ".", "..") or not _COMPONENT.fullmatch(part) for part in parts):
            raise RFCError("Provider repository must be an owner/repository path")
        return parts[0], parts[1]

    def _number(self, value: str, kind: str) -> str:
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", value):
            raise RFCError("Invalid source identifier")
        return quote(value, safe="")

    def _validate_ref(self, ref: SourceRef) -> None:
        if ref.provider != self.name or ref.kind not in ("issue", "pr", "pull_request"):
            raise RFCError("Unsupported provider source")
        self._repo(ref.repository)
        self._number(ref.identifier, ref.kind)
        if ref.host and ref.host.lower() not in self.web_hosts | {self.api_host}:
            raise RFCError("Source host is outside the configured provider", 403, "source_host_forbidden")
        if ref.url:
            try:
                parsed = urlsplit(ref.url)
                allowed = parsed.scheme == "https" and parsed.hostname in self.web_hosts and not parsed.username and not parsed.password and not parsed.query and parsed.port in (None, 443)
            except ValueError:
                allowed = False
            if not allowed:
                raise RFCError("Source URL is outside the configured provider", 403, "source_host_forbidden")

    def _json(self, method: str, route: str, query: Mapping[str, Any] | None = None, payload: dict[str, Any] | None = None):
        url = self.api_url + route
        if query:
            url += "?" + urlencode({key: value for key, value in query.items() if value is not None and value != ""})
        headers = {"Accept": "application/json", "User-Agent": "InferMatrixCopilot-RFC/1"}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        if self._token:
            headers["Authorization"] = "Bearer " + self._token
        if self.name == "github":
            headers["X-GitHub-Api-Version"] = "2022-11-28"
        try:
            status_code, response_headers, result = self._transport(method, url, headers, payload)
        except Exception:
            raise ProviderError("Provider request could not be completed", uncertain=method != "GET") from None
        if not isinstance(status_code, int) or not 200 <= status_code < 300:
            known_status = status_code if isinstance(status_code, int) else "invalid"
            raise ProviderError(f"Provider returned HTTP {known_status}", uncertain=method != "GET" and (not isinstance(status_code, int) or status_code >= 500))
        if not isinstance(response_headers, Mapping):
            raise ProviderError("Provider returned invalid response headers", uncertain=method != "GET")
        return result, {str(key).lower(): str(value) for key, value in response_headers.items()}

    def _pages(self, route: str, query: Mapping[str, Any] | None = None, *, size: int = PAGE_SIZE) -> Iterator[dict[str, Any]]:
        for page in range(1, MAX_PAGES + 1):
            result, headers = self._json("GET", route, dict(query or {}, page=page, per_page=size))
            if not isinstance(result, list) or any(not isinstance(row, dict) for row in result):
                raise ProviderError("Provider returned an invalid listing")
            yield from result
            next_page = headers.get("x-next-page", "").strip()
            has_next = bool(re.search(r'rel\s*=\s*"?next\b', headers.get("link", ""))) or next_page not in ("", "0")
            if len(result) < size and not has_next:
                return
        raise ProviderError("Provider listing is incomplete; pagination limit reached", uncertain=True)

    def _source(self, repository: str, item: Mapping[str, Any], kind: str = "issue") -> SourceRef:
        identifier = str(item.get("number") or "")
        self._number(identifier, kind)
        owner, repo = self._repo(repository)
        fallback = f"https://{self.web_host}/{owner}/{repo}/{'issues' if kind == 'issue' else 'pull'}/{identifier}"
        url = str(item.get("html_url") or item.get("web_url") or fallback)
        ref = SourceRef(self.name, repository, kind, identifier, url, host=urlsplit(url).hostname or self.web_host)
        self._validate_ref(ref)
        return ref

    def _item(self, ref: SourceRef, raw: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(raw, dict) or any(raw.get(key) is not None and not isinstance(raw.get(key), str) for key in ("title", "body")):
            raise ProviderError("Provider returned an invalid source")
        try:
            actual = self._source(ref.repository, raw, "pr" if ref.kind in ("pr", "pull_request") else "issue")
        except RFCError:
            raise ProviderError("Provider returned an invalid source identity") from None
        if actual.identifier != ref.identifier:
            raise ProviderError("Provider returned a different source identifier")
        author = _logins(raw.get("user") or raw.get("author"))
        owners = _logins(raw.get("assignees") or raw.get("assignee"))
        reviewers = _logins(raw.get("requested_reviewers"))
        if self.name == "atomgit" and actual.kind == "pr":
            reviewers = list(dict.fromkeys(_logins(raw.get("assignees")) + _logins(raw.get("approval_reviewers"))))
            owners = []
        head = raw.get("head")
        return {"source": actual.to_dict(), "title": str(raw.get("title") or ""), "body": str(raw.get("body") or ""),
                "url": actual.url, "revision": _revision(raw), "state": _state(raw), "native_state": str(raw.get("state") or ""),
                "head_sha": str(head.get("sha") or "") if isinstance(head, dict) else "", "author": author[0] if author else "",
                "owner": owners[0] if owners else "", "owners": owners, "reviewers": reviewers,
                "updated_at": str(raw.get("updated_at") or ""), "labels": raw.get("labels") or []}

    def _get_raw(self, ref: SourceRef) -> dict[str, Any]:
        self._validate_ref(ref)
        owner, repo = self._repo(ref.repository)
        resource = "pulls" if ref.kind in ("pr", "pull_request") else "issues"
        result, _ = self._json("GET", f"/repos/{quote(owner)}/{quote(repo)}/{resource}/{self._number(ref.identifier, ref.kind)}")
        if not isinstance(result, dict):
            raise ProviderError("Provider returned an invalid source")
        return result

    def get_source(self, ref: SourceRef) -> dict[str, Any]:
        return self._item(ref, self._get_raw(ref))

    def get_item(self, ref: SourceRef) -> dict[str, Any]:
        return self.get_source(ref)

    def publish(self, repository: str, title: str, body: str, operation_id: str, *, path: str = "") -> SourceRef:
        if path:
            raise RFCError("Remote issue publication does not accept a file path")
        owner, repo = self._repo(repository)
        payload = {"title": _title(title), "body": _publication_body(body, operation_id)}
        route = f"/repos/{quote(owner)}/{quote(repo)}/issues"
        if self.name == "atomgit":
            route = f"/repos/{quote(owner)}/issues"
            payload["repo"] = repo
        raw, _ = self._json("POST", route, payload=payload)
        try:
            if not isinstance(raw, dict):
                raise ValueError("invalid publication response")
            return self._source(repository, raw)
        except (RFCError, ValueError, TypeError):
            raise ProviderError("Publication response could not establish the created source", uncertain=True) from None

    def find_publication(self, repository: str, operation_id: str) -> SourceRef | None:
        owner, repo = self._repo(repository)
        marker = _marker(operation_id)
        found = []
        try:
            for item in self._pages(f"/repos/{quote(owner)}/{quote(repo)}/issues", {"state": "all", "sort": "created", "direction": "desc"}):
                if "pull_request" not in item and marker in str(item.get("body") or ""):
                    found.append(self._source(repository, item))
        except (ProviderError, RFCError):
            raise ProviderError("Publication recovery could not complete the repository scan", uncertain=True) from None
        if len(found) > 1:
            raise ProviderError("Multiple publications carry the operation marker", uncertain=True)
        return found[0] if found else None

    def update_source(self, ref: SourceRef, body: str, expected_revision: str, *, title: str | None = None) -> dict[str, Any]:
        if ref.kind not in ("issue", "pr", "pull_request"):
            raise RFCError("Managed RFC updates require an issue or pull request source")
        current = self.get_source(ref)
        if current["revision"] != expected_revision:
            raise RFCError("RFC changed before the update", 409, "source_conflict")
        if not isinstance(body, str) or len(body.encode("utf-8")) > MAX_DOCUMENT_BYTES:
            raise RFCError("RFC body exceeds the document size limit")
        owner, repo = self._repo(ref.repository)
        desired_title = current["title"] if title is None else _title(title)
        resource = "pulls" if ref.kind in ("pr", "pull_request") else "issues"
        route = f"/repos/{quote(owner)}/{quote(repo)}/{resource}/{self._number(ref.identifier, ref.kind)}"
        payload = {"body": body}
        if title is not None:
            payload["title"] = desired_title
        if self.name == "atomgit" and ref.kind == "issue":
            route = f"/repos/{quote(owner)}/issues/{self._number(ref.identifier, ref.kind)}"
            payload.update(repo=repo, title=desired_title)
        # This is a read/check/write guard, not a claim of provider-side atomic CAS.
        self._json("PATCH", route, payload=payload)
        try:
            result = self.get_source(ref)
        except RFCError:
            raise ProviderError("RFC update readback could not confirm the source", uncertain=True) from None
        if result["body"] != body or result["title"] != desired_title:
            raise RFCError("RFC update readback differs; reconcile the source", 409, "source_conflict")
        return result

    def discover(self, repository: str, scope: Any, since: str = "") -> list[dict[str, Any]]:
        owner, repo = self._repo(repository)
        prefix = f"/repos/{quote(owner)}/{quote(repo)}"
        query = {"state": "all", "sort": "updated", "direction": "desc", "since": since}
        result = []
        resources = [("issue", prefix + "/issues")]
        if self.name == "atomgit":
            resources.append(("pr", prefix + "/pulls"))
        for kind, route in resources:
            for raw in self._pages(route, query):
                matched = _scope_matches(str(raw.get("title") or ""), str(raw.get("body") or ""), raw.get("labels"), scope)
                text = str(raw.get("title") or "") + "\n" + str(raw.get("body") or "")
                if not matched and not _discovery_reference(scope, text):
                    continue
                actual_kind = "pr" if "pull_request" in raw else kind
                ref = self._source(repository, raw, actual_kind)
                # Discovery retrieves references, not delivery verification. Avoid
                # one detail request per candidate; attached links are verified by
                # the application through get_item. GitHub issue listings carry
                # an explicit merge timestamp inside their pull_request field.
                native = raw
                pull = raw.get("pull_request")
                if actual_kind == "pr" and isinstance(pull, dict) and pull.get("merged_at") and not raw.get("merged_at"):
                    native = {**raw, "merged_at": pull["merged_at"]}
                item = self._item(ref, native)
                if not _same_discovery_source(item, scope):
                    result.append(_annotate_discovery(item, scope, matched))
        return result


class GitHubProvider(_HTTPProvider):
    name = "github"
    default_api_url = "https://api.github.com"
    default_web_hosts = ("github.com",)

    def __init__(self, token: str = "", api_url: str = "https://api.github.com", transport: Transport | None = None):
        super().__init__(token, api_url, transport)

    def _number(self, value: str, kind: str) -> str:
        if not isinstance(value, str) or not re.fullmatch(r"[1-9][0-9]*", value):
            raise RFCError("GitHub issue and PR identifiers must be positive integers")
        return value


class AtomGitProvider(_HTTPProvider):
    name = "atomgit"
    default_api_url = "https://api.atomgit.com/api/v5"
    default_web_hosts = ("atomgit.com", "gitcode.com")

    def __init__(self, token: str = "", api_url: str = "https://api.atomgit.com/api/v5", transport: Transport | None = None):
        if not urlsplit(api_url).path.strip("/"):
            api_url = api_url.rstrip("/") + "/api/v5"
        super().__init__(token, api_url, transport)

    def _number(self, value: str, kind: str) -> str:
        if kind in ("pr", "pull_request") and (not isinstance(value, str) or not re.fullmatch(r"[1-9][0-9]*", value)):
            raise RFCError("AtomGit PR identifiers must be positive integers")
        return super()._number(value, kind)


class LocalProvider:
    """Markdown RFCs and observed Git commits inside explicitly registered roots."""
    name = "local"

    def __init__(self, roots: Mapping[str, str | Path]):
        self.roots: dict[str, Path] = {}
        self._root_inodes: dict[str, tuple[int, int]] = {}
        for repository, value in roots.items():
            path = Path(value)
            if not repository or not path.is_absolute() or not path.is_dir():
                raise RFCError("Local repositories require existing absolute directory roots")
            self.roots[repository] = path.resolve(strict=True)
            metadata = self.roots[repository].stat()
            self._root_inodes[repository] = (metadata.st_dev, metadata.st_ino)

    def _root(self, repository: str) -> Path:
        if repository not in self.roots:
            raise RFCError("Local repository is outside the configured roots", 403, "source_root_forbidden")
        return self.roots[repository]

    def _parts(self, path: str) -> tuple[str, ...]:
        if not isinstance(path, str) or not path or "\\" in path or "\x00" in path or ":" in path:
            raise RFCError("Local source requires a repository-relative Markdown path")
        value = PurePosixPath(path)
        if value.is_absolute() or any(part in ("..", ".git", ".hg", ".svn") for part in value.parts) or value.suffix.lower() not in (".md", ".markdown"):
            raise RFCError("Local source path is outside the permitted Markdown tree", 403, "source_path_forbidden")
        return value.parts

    @contextmanager
    def _parent(self, repository: str, path: str, *, create: bool = False):
        root = self._root(repository)
        parts = self._parts(path)
        # POSIX walks directories by descriptor, so replacing a parent with a
        # symlink cannot redirect a read/create/replace outside the registered root.
        if os.open in os.supports_dir_fd and hasattr(os, "O_NOFOLLOW"):
            try:
                fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            except OSError:
                raise RFCError("Local repository root cannot be accessed safely", 403, "source_root_forbidden") from None
            try:
                metadata = os.fstat(fd)
                if (metadata.st_dev, metadata.st_ino) != self._root_inodes[repository]:
                    raise RFCError("Local repository root changed after registration", 403, "source_root_forbidden")
                for part in parts[:-1]:
                    try:
                        child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                    except FileNotFoundError:
                        if not create:
                            raise
                        try:
                            os.mkdir(part, mode=0o700, dir_fd=fd)
                        except FileExistsError:
                            pass
                        child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                    os.close(fd)
                    fd = child
                yield fd, parts[-1], root.joinpath(*parts)
            except OSError as error:
                if isinstance(error, FileNotFoundError):
                    raise RFCError("Local RFC source does not exist", 404, "source_not_found") from None
                raise RFCError("Local RFC path cannot be accessed safely", 403, "source_path_forbidden") from None
            finally:
                os.close(fd)
        else:
            target = root
            for part in parts[:-1]:
                target = target / part
                if target.is_symlink():
                    raise RFCError("Symlinks are not permitted in local RFC paths", 403, "source_path_forbidden")
                if create:
                    target.mkdir(exist_ok=True)
                if not target.is_dir():
                    raise RFCError("Local RFC source does not exist", 404, "source_not_found")
            target = target / parts[-1]
            if target.is_symlink() or not target.resolve(strict=False).is_relative_to(root):
                raise RFCError("Local RFC path escapes the configured root", 403, "source_path_forbidden")
            yield None, parts[-1], target

    def _read_info(self, repository: str, path: str) -> tuple[bytes, float]:
        with self._parent(repository, path) as (parent, leaf, target):
            try:
                fd = os.open(leaf if parent is not None else target, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0), **({"dir_fd": parent} if parent is not None else {}))
                with os.fdopen(fd, "rb") as stream:
                    metadata = os.fstat(stream.fileno())
                    if not stat.S_ISREG(metadata.st_mode):
                        raise RFCError("Local RFC source must be a regular file")
                    raw = stream.read(MAX_DOCUMENT_BYTES + 1)
            except FileNotFoundError:
                raise RFCError("Local RFC source does not exist", 404, "source_not_found") from None
            if len(raw) > MAX_DOCUMENT_BYTES:
                raise RFCError("Local RFC source exceeds the document size limit")
            return raw, metadata.st_mtime

    def _read(self, repository: str, path: str) -> bytes:
        return self._read_info(repository, path)[0]

    def _ref(self, repository: str, path: str) -> SourceRef:
        return SourceRef("local", repository, "markdown", path, path=path)

    def get_source(self, ref: SourceRef) -> dict[str, Any]:
        if ref.provider not in ("local", "local_git", "markdown") or ref.host or ref.url:
            raise RFCError("Local sources must use an allowlisted repository and relative path")
        if ref.kind in ("commit", "git_commit"):
            return self._commit(ref)
        raw, modified = self._read_info(ref.repository, ref.path or ref.identifier)
        try:
            body = raw.decode("utf-8")
        except UnicodeDecodeError:
            raise RFCError("Local RFC sources must be UTF-8 Markdown") from None
        path = str(PurePosixPath(ref.path or ref.identifier))
        source = self._ref(ref.repository, path)
        title = re.search(r"^#\s+(.+)$", body, re.M)
        return {"source": source.to_dict(), "title": title[1] if title else PurePosixPath(path).stem, "body": body,
                "revision": _digest(raw), "url": "", "state": "unknown", "native_state": "markdown",
                "head_sha": "", "author": "", "owner": "", "owners": [], "reviewers": [],
                "updated_at": datetime.fromtimestamp(modified, timezone.utc).isoformat()}

    def get_item(self, ref: SourceRef) -> dict[str, Any]:
        return self.get_source(ref)

    def _commit(self, ref: SourceRef) -> dict[str, Any]:
        root = self._root(ref.repository)
        if not re.fullmatch(r"[0-9a-fA-F]{7,64}", ref.identifier):
            raise RFCError("Local commit references require a hexadecimal Git object identifier")
        try:
            result = subprocess.run(["git", "-C", str(root), "show", "--no-ext-diff", "--no-patch", "--format=%H%n%an%n%cI%n%s%n%b", ref.identifier, "--"], capture_output=True, text=True, timeout=15, check=True)
        except (OSError, subprocess.SubprocessError):
            raise ProviderError("Local Git commit could not be read") from None
        fields = result.stdout.split("\n", 4)
        if len(fields) < 4 or not re.fullmatch(r"[0-9a-fA-F]{40,64}", fields[0]):
            raise ProviderError("Local Git returned an invalid commit")
        source = SourceRef("local", ref.repository, "commit", fields[0])
        return {"source": source.to_dict(), "title": fields[3], "body": fields[4] if len(fields) > 4 else "", "revision": fields[0],
                "url": "", "state": "unknown", "native_state": "commit", "head_sha": fields[0], "author": fields[1],
                "owner": "", "owners": [], "reviewers": [], "updated_at": fields[2]}

    def publish(self, repository: str, title: str, body: str, operation_id: str, *, path: str = "") -> SourceRef:
        marker = _marker(operation_id)
        title = _title(title)
        path = path or "rfcs/" + re.sub(r"[^A-Za-z0-9._-]", "_", operation_id) + ".md"
        content = _publication_body(body, operation_id)
        if not re.search(r"^#\s", content, re.M):
            content = "# " + title + "\n\n" + content
        with self._parent(repository, path, create=True) as (parent, leaf, target):
            try:
                fd = os.open(leaf if parent is not None else target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600, **({"dir_fd": parent} if parent is not None else {}))
            except FileExistsError:
                existing = self.get_source(self._ref(repository, path))
                if marker in existing["body"]:
                    return self._ref(repository, path)
                raise RFCError("Local RFC publication path already exists", 409, "publication_conflict") from None
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(content.encode("utf-8"))
                    stream.flush()
                    os.fsync(stream.fileno())
            except OSError:
                raise ProviderError("Local RFC publication may be incomplete", uncertain=True) from None
        return self._ref(repository, str(PurePosixPath(path)))

    def _files(self, repository: str) -> Iterator[str]:
        root = self._root(repository)
        def onerror(error):
            raise ProviderError("Local RFC tree could not be completely scanned", uncertain=True) from None
        for base, dirs, files in os.walk(root, followlinks=False, onerror=onerror):
            dirs[:] = [name for name in dirs if name not in (".git", ".hg", ".svn") and not (Path(base) / name).is_symlink()]
            for name in files:
                file = Path(base) / name
                if file.suffix.lower() in (".md", ".markdown") and not file.is_symlink():
                    yield file.relative_to(root).as_posix()

    def find_publication(self, repository: str, operation_id: str) -> SourceRef | None:
        marker = _marker(operation_id)
        found = []
        try:
            for path in self._files(repository):
                if marker.encode("utf-8") in self._read(repository, path):
                    found.append(self._ref(repository, path))
        except (RFCError, ProviderError, OSError):
            raise ProviderError("Local publication recovery could not complete the repository scan", uncertain=True) from None
        if len(found) > 1:
            raise ProviderError("Multiple local publications carry the operation marker", uncertain=True)
        return found[0] if found else None

    def update_source(self, ref: SourceRef, body: str, expected_revision: str, *, title: str | None = None) -> dict[str, Any]:
        current = self.get_source(ref)
        if ref.kind in ("commit", "git_commit"):
            raise RFCError("Git commits cannot be rewritten by the RFC provider")
        if current["revision"] != expected_revision:
            raise RFCError("Local RFC changed before the update", 409, "source_conflict")
        if not isinstance(body, str) or len(body.encode("utf-8")) > MAX_DOCUMENT_BYTES:
            raise RFCError("RFC body exceeds the document size limit")
        path = ref.path or ref.identifier
        if title is not None:
            heading = re.search(r"^#\s+(.+)$", body, re.M)
            body_title = heading[1] if heading else PurePosixPath(path).stem
            if body_title != _title(title):
                raise RFCError("The reviewed local RFC title must match its Markdown heading", 409, "preview_mismatch")
        with self._parent(ref.repository, path) as (parent, leaf, target):
            temporary = ".imrfc-" + secrets.token_hex(16) + ".tmp"
            kwargs = {"dir_fd": parent} if parent is not None else {}
            temp_path = temporary if parent is not None else target.parent / temporary
            try:
                fd = os.open(temp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600, **kwargs)
                with os.fdopen(fd, "wb") as stream:
                    stream.write(body.encode("utf-8"))
                    stream.flush()
                    os.fsync(stream.fileno())
                if self.get_source(ref)["revision"] != expected_revision:
                    raise RFCError("Local RFC changed before replacement", 409, "source_conflict")
                if parent is not None:
                    os.replace(temporary, leaf, src_dir_fd=parent, dst_dir_fd=parent)
                else:
                    os.replace(temp_path, target)
            finally:
                try:
                    os.unlink(temp_path, **kwargs)
                except FileNotFoundError:
                    pass
        try:
            result = self.get_source(ref)
        except RFCError:
            raise ProviderError("Local RFC update readback could not confirm the source", uncertain=True) from None
        if result["body"] != body or (title is not None and result["title"] != title):
            raise RFCError("Local RFC update readback differs", 409, "source_conflict")
        return result

    def discover(self, repository: str, scope: Any, since: str = "") -> list[dict[str, Any]]:
        try:
            since_time = datetime.fromisoformat(since.replace("Z", "+00:00")) if since else None
            if since_time and since_time.tzinfo is None:
                since_time = since_time.replace(tzinfo=timezone.utc)
        except ValueError:
            raise RFCError("Discovery since must be an ISO 8601 timestamp") from None
        result = []
        for path in self._files(repository):
            item = self.get_source(self._ref(repository, path))
            if since_time and datetime.fromisoformat(item["updated_at"]) < since_time:
                continue
            matches = _scope_matches(item["title"], item["body"], [], scope)
            if not _same_discovery_source(item, scope) and (matches or _discovery_reference(scope, item["title"] + "\n" + item["body"])):
                result.append(_annotate_discovery(item, scope, matches))
        return result
