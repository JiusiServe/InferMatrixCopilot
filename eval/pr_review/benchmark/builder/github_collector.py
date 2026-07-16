"""GitHub REST collector used only while constructing benchmark artifacts.

Evaluation runs never import or call this module, so the frozen benchmark can run
without network access.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Iterator


class GitHubCollectorError(RuntimeError):
    pass


@dataclass(frozen=True)
class GitHubCollector:
    token: str = ""
    api_base: str = "https://api.github.com"
    timeout_seconds: int = 30
    max_retries: int = 3

    def _request(self, path: str, *, params: dict[str, Any] | None = None) -> tuple[Any, dict[str, str]]:
        url = f"{self.api_base.rstrip('/')}/{path.lstrip('/')}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "vllm-omni-copilot-pr-review-benchmark",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                with urllib.request.urlopen(
                    urllib.request.Request(url, headers=headers),
                    timeout=self.timeout_seconds,
                ) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                    return payload, dict(response.headers.items())
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
                last_error = exc
                if isinstance(exc, urllib.error.HTTPError) and exc.code not in {429, 500, 502, 503, 504}:
                    break
                time.sleep(2 ** attempt)
        raise GitHubCollectorError(f"GitHub request failed for {url}: {last_error}")

    def paginate(self, path: str, *, params: dict[str, Any] | None = None, max_pages: int = 20) -> Iterator[dict[str, Any]]:
        query = dict(params or {})
        query["per_page"] = 100
        for page in range(1, max_pages + 1):
            query["page"] = page
            payload, _ = self._request(path, params=query)
            if not isinstance(payload, list):
                raise GitHubCollectorError(f"expected a list from {path}")
            for value in payload:
                if isinstance(value, dict):
                    yield value
            if len(payload) < 100:
                return
        raise GitHubCollectorError(f"pagination cap reached for {path}")

    def collect_pr(self, repository: str, pr_number: int) -> dict[str, Any]:
        prefix = f"repos/{repository}"
        pr, _ = self._request(f"{prefix}/pulls/{pr_number}")
        return {
            "repository": repository,
            "pr": pr,
            "commits": list(self.paginate(f"{prefix}/pulls/{pr_number}/commits")),
            "files": list(self.paginate(f"{prefix}/pulls/{pr_number}/files")),
            "reviews": list(self.paginate(f"{prefix}/pulls/{pr_number}/reviews")),
            "review_comments": list(self.paginate(f"{prefix}/pulls/{pr_number}/comments")),
            "issue_comments": list(self.paginate(f"{prefix}/issues/{pr_number}/comments")),
        }

    def list_closed_pull_requests(self, repository: str, *, max_pages: int = 10) -> list[dict[str, Any]]:
        return list(self.paginate(
            f"repos/{repository}/pulls",
            params={"state": "closed", "sort": "updated", "direction": "desc"},
            max_pages=max_pages,
        ))
