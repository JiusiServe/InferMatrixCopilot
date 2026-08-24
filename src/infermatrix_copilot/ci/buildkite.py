"""Buildkite provider client — the injected `CIClient` for the rebase
engine's guarded build lifecycle (Rev 8 §3.2).

Repo-neutral: org, pipeline, and the trigger env come from the ADAPTER
(`ci.org` + `rebase.ci.*`); nothing here names a repo, pipeline, or queue.

Build dicts are NORMALIZED at this boundary: `id` is the build NUMBER as a
string (Buildkite's REST API addresses builds by number — the UUID `id`
field is not routable), `web_url` is the human link, and the raw fields
(state / commit / branch / source / jobs / meta_data / number) pass
through. The op ledger in `ci_loop` therefore stores ids that stay
resolvable across process restarts.

Error contract, chosen per call site:
- mutating calls and identity lookups (`create_build`, `cancel_build`,
  `find_builds_by_meta`, `retry_job` non-400, `builds_for_commit`,
  `latest_builds`) RAISE `BuildkiteError` on an unexpected response —
  `create_build_guarded` must see the failure before an op is marked
  created, and recovery/adoption must escalate rather than guess;
- polling reads degrade instead of aborting a monitor mid-build:
  `get_build` returns {} and `get_job_log` returns "" on error (the poll
  loop re-tries on its own cadence, and the final reconciliation pass is
  what rules).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Mapping, Sequence

# (method, url, body|None, raw) -> (status, parsed_json_or_text)
RequestFn = Callable[[str, str, dict | None, bool], tuple[int, Any]]

_API = "https://api.buildkite.com/v2"


class BuildkiteError(RuntimeError):
    """An unexpected Buildkite API response on a call that must not guess."""


def _urllib_request(token: str, method: str, url: str,
                    body: dict | None = None,
                    raw: bool = False) -> tuple[int, Any]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Authorization": f"Bearer {token}",
                 **({"Content-Type": "application/json"} if data else {})})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = resp.read().decode("utf-8", errors="replace")
            status = resp.status
    except urllib.error.HTTPError as e:  # non-2xx still carries a body
        payload = (e.read() or b"").decode("utf-8", errors="replace")
        status = e.code
    except OSError as e:
        raise BuildkiteError(f"Buildkite API unreachable: {e}") from e
    if raw:
        return status, payload
    try:
        return status, json.loads(payload) if payload else {}
    except ValueError:
        return status, {}


class BuildkiteCI:
    """`CIClient` over the Buildkite REST API, scoped to one pipeline."""

    def __init__(self, token: str, org: str, pipeline: str,
                 build_env: Mapping[str, str] | None = None,
                 request: RequestFn | None = None, *,
                 ignore_branch_filters: bool = False):
        self.org = org
        self.pipeline = pipeline
        self.build_env = dict(build_env or {})
        # Adapter opt-in (rebase.ci.ignore_branch_filters): send the
        # documented `ignore_pipeline_branch_filters` override on create.
        # Buildkite couples provider build_branches=false to ordinary API
        # creation ("Branches have been disabled for this pipeline", 422);
        # this override is the staff-documented remedy and needs only the
        # write_builds scope. Step-level branch filters still apply.
        self.ignore_branch_filters = bool(ignore_branch_filters)
        self._request: RequestFn = request or (
            lambda method, url, body=None, raw=False:
            _urllib_request(token, method, url, body, raw))

    # ── url helpers ─────────────────────────────────────────────────────────

    @property
    def base(self) -> str:
        return (f"{_API}/organizations/{urllib.parse.quote(self.org, safe='')}"
                f"/pipelines/{urllib.parse.quote(self.pipeline, safe='')}")

    def _build_path(self, build_id: str) -> str:
        return f"{self.base}/builds/{urllib.parse.quote(str(build_id), safe='')}"

    def _norm(self, build: dict) -> dict:
        out = dict(build)
        number = build.get("number")
        out["id"] = str(number) if number is not None \
            else str(build.get("id", ""))
        out["web_url"] = build.get("web_url") or (
            f"https://buildkite.com/{self.org}/{self.pipeline}"
            f"/builds/{number}" if number is not None else "")
        return out

    # ── CIClient protocol ───────────────────────────────────────────────────

    def create_build(self, *, branch: str, commit: str, message: str,
                     meta_data: Mapping[str, str]) -> dict:
        body: dict = {"commit": commit, "branch": branch,
                      "message": message, "meta_data": dict(meta_data)}
        if self.ignore_branch_filters:
            body["ignore_pipeline_branch_filters"] = True
        if self.build_env:
            body["env"] = dict(self.build_env)
        status, data = self._request("POST", f"{self.base}/builds", body,
                                     False)
        if status != 201 or not isinstance(data, dict):
            # ONLY the specific branch-builds-disabled policy response is
            # the typed refusal (422 + "disabled" in the message) - the
            # round loop then reports the schedule-only guidance. Every
            # other 4xx (401 auth, 403 authz, 404 pipeline, 400/422
            # validation) is an operational error where that guidance
            # would mislead, and stays BuildkiteError.
            message = str((data or {}).get("message", "")) \
                if isinstance(data, dict) else str(data)
            if status == 422 and \
                    "branches have been disabled" in message.lower():
                from ..rebase_engine.ci_loop import BuildCreationRefused
                raise BuildCreationRefused(
                    f"create_build refused: HTTP {status} "
                    f"{str(data)[:200]}")
            raise BuildkiteError(
                f"create_build failed: HTTP {status} "
                f"{str(data)[:200]}")
        return self._norm(data)

    def get_build(self, build_id: str) -> dict:
        try:
            status, data = self._request("GET", self._build_path(build_id),
                                         None, False)
        except BuildkiteError:
            # polling read: transport errors degrade too — the poll loop
            # re-tries on its own cadence (round-1 review)
            return {}
        if status != 200 or not isinstance(data, dict):
            return {}
        return self._norm(data)

    def find_builds_by_meta(self, key: str, value: str) -> list[dict]:
        q = urllib.parse.urlencode({f"meta_data[{key}]": value,
                                    "per_page": 30})
        status, data = self._request("GET", f"{self.base}/builds?{q}",
                                     None, False)
        if status != 200 or not isinstance(data, list):
            raise BuildkiteError(
                f"find_builds_by_meta failed: HTTP {status} — refusing to "
                "treat an API error as 'no matches'")
        return [self._norm(b) for b in data if isinstance(b, dict)]

    def cancel_build(self, build_id: str) -> dict:
        status, data = self._request(
            "PUT", self._build_path(build_id) + "/cancel", None, False)
        if status not in (200, 201) or not isinstance(data, dict):
            raise BuildkiteError(f"cancel_build failed: HTTP {status}")
        return self._norm(data)

    def get_job_log(self, build_id: str, job_id: str) -> str:
        try:
            status, text = self._request(
                "GET",
                self._build_path(build_id)
                + f"/jobs/{urllib.parse.quote(str(job_id), safe='')}"
                  "/log.txt",
                None, True)
        except BuildkiteError:
            return ""
        return text if status == 200 and isinstance(text, str) else ""

    def list_jobs(self, build_id: str) -> list[dict]:
        """Authoritative job list: the dedicated /jobs endpoint when it
        behaves, embedded jobs from a fresh build fetch otherwise (some
        builds 404 the endpoint; it can also answer with the build object
        itself — parent-documented). RAISES when neither source is
        readable: retrieval failure must stay distinguishable from a
        genuinely empty job list, or a reconciliation during an API
        outage would silently pass (round-2 review)."""
        try:
            status, data = self._request(
                "GET", self._build_path(build_id) + "/jobs?per_page=100",
                None, False)
            if status == 200:
                if isinstance(data, list):
                    return [j for j in data if isinstance(j, dict)]
                if isinstance(data, dict) and \
                        isinstance(data.get("jobs"), list):
                    return [j for j in data["jobs"] if isinstance(j, dict)]
        except BuildkiteError:
            pass
        build = self.get_build(build_id)
        if not build:
            raise BuildkiteError(
                "list_jobs failed: the jobs endpoint was unusable and the "
                "build itself is unreadable")
        return [j for j in (build.get("jobs") or []) if isinstance(j, dict)]

    def retry_job(self, build_id: str,
                  job_id: str) -> tuple[str | None, bool]:
        """(new_job_id | None, retryable). HTTP 400 means this job TYPE
        cannot be retried (pipeline-upload / trigger steps) — the caller
        classifies it ignorable instead of actionable. Any OTHER failure
        RAISES (mutating-call policy): an API outage must never be
        mistaken for a code failure — the monitor records the job
        structurally incomplete instead of dispatching a mutation agent
        (round-1 review)."""
        status, data = self._request(
            "PUT",
            self._build_path(build_id)
            + f"/jobs/{urllib.parse.quote(str(job_id), safe='')}/retry",
            None, False)
        if status in (200, 201) and isinstance(data, dict):
            return str(data.get("id", "")), True
        if status == 400:
            return None, False
        raise BuildkiteError(f"retry_job failed: HTTP {status}")

    # ── adoption / baseline lookups (beyond the core protocol) ─────────────

    def builds_for_commit(self, branch: str, commit: str) -> list[dict]:
        q = urllib.parse.urlencode({"branch": branch, "commit": commit,
                                    "per_page": 30})
        status, data = self._request("GET", f"{self.base}/builds?{q}",
                                     None, False)
        if status != 200 or not isinstance(data, list):
            raise BuildkiteError(
                f"builds_for_commit failed: HTTP {status} — refusing to "
                "treat an API error as 'no sibling builds'")
        return [self._norm(b) for b in data if isinstance(b, dict)]

    def latest_builds(self, branch: str, states: Sequence[str] = (),
                      per_page: int = 30) -> list[dict]:
        params = [("branch", branch), ("per_page", str(per_page))]
        params.extend(("state[]", s) for s in states)
        q = urllib.parse.urlencode(params)
        status, data = self._request("GET", f"{self.base}/builds?{q}",
                                     None, False)
        if status != 200 or not isinstance(data, list):
            raise BuildkiteError(f"latest_builds failed: HTTP {status}")
        return [self._norm(b) for b in data if isinstance(b, dict)]
