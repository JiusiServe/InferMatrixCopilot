"""CI log providers (design §V2.1(c)) — selected by the repo profile's
`ci.provider`, never hardcoded. Each provider enriches the failing-check list
(in place) with real logs so pr-debug groups by root-cause signature instead
of by check name. Enrichment is best-effort: a provider error leaves the
check's log empty and pr-debug degrades to name grouping, recorded — never a
crash.
"""

from __future__ import annotations

import json
import re
import urllib.request
from typing import Callable


def _http_get_json(url: str, token: str) -> dict | list:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


class BuildkiteLogs:
    """Buildkite REST: check link -> build -> failed jobs -> job logs."""

    _BUILD_URL = re.compile(r"buildkite\.com/([^/]+)/([^/]+)/builds/(\d+)")
    _API = "https://api.buildkite.com/v2/organizations/{org}/pipelines/{pipe}/builds/{num}"

    def __init__(self, token: str, http_get: Callable | None = None):
        self.token = token
        self._get = http_get or (lambda url: _http_get_json(url, self.token))

    def enrich(self, failures: list[dict], log_cap: int = 100_000) -> int:
        enriched = 0
        builds: dict[str, dict] = {}
        for failure in failures:
            if failure.get("log"):
                continue
            m = self._BUILD_URL.search(str(failure.get("link", "")))
            if not m:
                continue
            api_url = self._API.format(org=m.group(1), pipe=m.group(2),
                                       num=m.group(3))
            try:
                build = builds.get(api_url)
                if build is None:
                    build = builds[api_url] = self._get(api_url)
                failed_jobs = [j for j in build.get("jobs", [])
                               if j.get("state") in ("failed", "broken",
                                                     "timed_out")]
                name = str(failure.get("name", ""))
                jobs = [j for j in failed_jobs
                        if name and (name in str(j.get("name", ""))
                                     or str(j.get("name", "")) in name)] \
                    or failed_jobs
                logs = []
                for job in jobs[:3]:
                    log = self._get(f"{api_url}/jobs/{job['id']}/log")
                    content = str((log or {}).get("content", ""))
                    if content:
                        logs.append(content)
                if logs:
                    failure["log"] = "\n".join(logs)[-log_cap:]
                    enriched += 1
            except Exception:
                continue  # this check stays name-grouped
        return enriched


class GithubActionsLogs:
    """GitHub Actions via gh: check link -> run id -> `gh run view --log-failed`."""

    _RUN_URL = re.compile(r"github\.com/[^/]+/[^/]+/actions/runs/(\d+)")

    def __init__(self, runner: Callable[..., tuple[int, str]], repo=None):
        self._gh = runner   # (args, cwd) -> (exit_code, output)
        self.repo = repo

    def enrich(self, failures: list[dict], log_cap: int = 100_000) -> int:
        enriched = 0
        run_logs: dict[str, str] = {}
        for failure in failures:
            if failure.get("log"):
                continue
            m = self._RUN_URL.search(str(failure.get("link", "")))
            if not m:
                continue
            run_id = m.group(1)
            try:
                if run_id not in run_logs:
                    code, out = self._gh(["run", "view", run_id, "--log-failed"],
                                         cwd=self.repo)
                    run_logs[run_id] = out if code == 0 else ""
                if run_logs[run_id]:
                    failure["log"] = run_logs[run_id][-log_cap:]
                    enriched += 1
            except Exception:
                continue
        return enriched


def provider_for(plugin, settings, gh_runner: Callable | None = None):
    """The repo's CI log provider, or (None, gap-reason). The gap reason is
    escalation material for a `capability_gap` trace event."""
    name = ""
    if plugin is not None:
        name = str((plugin.manifest.get("ci") or {}).get("provider") or "")
    if not name:
        return None, "no ci.provider in the repo profile"
    if name == "buildkite":
        if not settings.buildkite_api_token:
            return None, "ci.provider=buildkite but BUILDKITE_API_TOKEN unset"
        return BuildkiteLogs(settings.buildkite_api_token), ""
    if name in ("github_actions", "github-actions", "github"):
        if gh_runner is None:
            return None, "no gh runner available"
        return GithubActionsLogs(gh_runner), ""
    return None, f"unknown ci.provider '{name}'"
