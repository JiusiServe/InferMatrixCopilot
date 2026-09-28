"""Read-only inputs of the knowledge service: the knowledge repository clone and
GitHub. Nothing here writes to GitHub; the service holds no write credential.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

KNOWLEDGE_SUFFIXES = (".md", ".yaml")
EXTERNAL_REF_DIRS = ("skills/", "plugins/", "adapters/", "doc/", "playbooks/")
MAX_BODY_CHARS = 3000
MAX_CHANGED_PATHS = 50
MAX_DIFF_BYTES = 8 * 1024


class SourceError(RuntimeError):
    """A read of git or GitHub failed; the caller retries on a later tick."""


class KnowledgeRepo:
    """A local clone of the knowledge repository (InferMatrixCopilot)."""

    def __init__(self, path: str | Path, *, remote: str = "origin", branch: str = "main"):
        self.path = Path(path)
        self.remote = remote
        self.branch = branch

    def _git(self, *args: str, input: bytes | None = None) -> bytes:
        proc = subprocess.run(["git", "-C", str(self.path), *args], input=input,
                              capture_output=True, check=False)
        if proc.returncode != 0:
            raise SourceError(f"git {' '.join(args)} failed: {proc.stderr.decode(errors='replace')[:500]}")
        return proc.stdout

    def fetch(self) -> str:
        self._git("fetch", "--quiet", self.remote, self.branch)
        return self.main_sha()

    def main_sha(self) -> str:
        return self._git("rev-parse", f"{self.remote}/{self.branch}").decode().strip()

    def _texts(self, rev: str, prefixes: tuple[str, ...], suffixes: tuple[str, ...] | None) -> dict[str, str]:
        listing = self._git("ls-tree", "-r", "-z", "--full-tree", rev).split(b"\0")
        wanted: list[tuple[str, str]] = []
        for entry in listing:
            if not entry:
                continue
            meta, _, path = entry.partition(b"\t")
            mode, kind, oid = meta.decode().split()
            name = path.decode("utf-8", "replace")
            if kind != "blob" or mode != "100644":
                continue
            if not name.startswith(prefixes) or (suffixes and not name.endswith(suffixes)):
                continue
            wanted.append((name, oid))
        if not wanted:
            return {}
        out = self._git("cat-file", "--batch", input="".join(f"{oid}\n" for _, oid in wanted).encode())
        texts: dict[str, str] = {}
        cursor = 0
        for name, _oid in wanted:
            header_end = out.index(b"\n", cursor)
            size = int(out[cursor:header_end].split()[2])
            body = out[header_end + 1: header_end + 1 + size]
            cursor = header_end + 1 + size + 1
            try:
                texts[name] = body.decode("utf-8")
            except UnicodeDecodeError:
                continue
        return texts

    def fetch_pull(self, number: int) -> str:
        """Fetch a pull request's head as data (never checked out); its SHA."""
        self._git("fetch", "--quiet", self.remote, f"+refs/pull/{int(number)}/head:refs/kb/pull/{int(number)}")
        return self._git("rev-parse", f"refs/kb/pull/{int(number)}").decode().strip()

    def merge_base(self, a: str, b: str) -> str:
        return self._git("merge-base", a, b).decode().strip()

    def show(self, rev: str, path: str) -> str | None:
        try:
            return self._git("show", f"{rev}:{path}").decode("utf-8", "replace")
        except SourceError:
            return None

    def export(self, rev: str, dest: str | Path) -> Path:
        """Materialize the tree at ``rev`` under ``dest`` (no checkout involved)."""
        import io
        import tarfile

        dest = Path(dest)
        dest.mkdir(parents=True, exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(self._git("archive", "--format=tar", rev))) as tar:
            tar.extractall(dest, filter="data")
        return dest

    def raw_manifest(self, old: str, new: str) -> list[dict]:
        """Every changed path as a kb-gate manifest entry (renames are D + A),
        the exact form the verifier recomputes."""
        out = self._git("diff", "--raw", "-z", "--no-renames", "--no-abbrev", old, new).split(b"\0")
        entries, zero = [], "0" * 40
        for index in range(0, len(out) - 1, 2):
            old_mode, new_mode, old_blob, new_blob, status = out[index].decode()[1:].split()
            entries.append({
                "path": out[index + 1].decode("utf-8", "replace"), "status": status[0],
                "old_blob": "" if old_blob == zero else old_blob, "new_blob": "" if new_blob == zero else new_blob,
                "old_mode": "" if old_mode == "000000" else old_mode,
                "new_mode": "" if new_mode == "000000" else new_mode,
            })
        return entries

    def first_parent_commits(self, old: str, new: str) -> list[tuple[str, list[str], float, str]]:
        """(sha, parents, commit time, message) on new's first-parent chain
        after old, oldest first."""
        out = self._git("log", "--first-parent", "--reverse", "-z", "--format=%H %P%n%ct%n%B",
                        f"{old}..{new}").decode("utf-8", "replace")
        commits = []
        for record in out.split("\0"):
            if not record.strip():
                continue
            head, _, rest = record.lstrip("\n").partition("\n")
            stamp, _, message = rest.partition("\n")
            shas = head.split()
            commits.append((shas[0], shas[1:], float(stamp or 0), message))
        return commits

    def blob_ids(self, rev: str, paths: list[str]) -> dict[str, str]:
        """path -> "<mode> <type> <blob id>" at ``rev`` ("" for an absent path):
        the mode is part of the identity (an executable bit is a change)."""
        if not paths:
            return {}
        out = self._git("ls-tree", "-z", "--full-tree", rev, "--", *paths).split(b"\0")
        found = {}
        for entry in out:
            if entry:
                meta, _, name = entry.partition(b"\t")
                found[name.decode("utf-8", "replace")] = meta.decode()
        return {path: found.get(path, "") for path in paths}

    def changed_names(self, old: str, new: str) -> list[str]:
        if not old:  # a root commit
            out = self._git("ls-tree", "-r", "-z", "--name-only", new)
        else:
            out = self._git("diff", "--name-only", "-z", "--no-renames", old, new)
        return [name.decode("utf-8", "replace") for name in out.split(b"\0") if name]

    def knowledge_files(self, rev: str) -> dict[str, str]:
        """Knowledge-relative path -> text for the governed tree at ``rev``."""
        files = self._texts(rev, ("knowledge/repos/", "knowledge/general/"), KNOWLEDGE_SUFFIXES)
        return {name.removeprefix("knowledge/"): text for name, text in files.items()}

    def top_level_knowledge(self, rev: str) -> dict[str, str]:
        """knowledge/*.md at the top of the tree (AGENTS.md, README.md, ...):
        not governed by the gate, but served with every snapshot."""
        files = self._texts(rev, ("knowledge/",), (".md",))
        return {name.removeprefix("knowledge/"): text for name, text in files.items()
                if "/" not in name.removeprefix("knowledge/")}

    def external_texts(self, rev: str) -> dict[str, str]:
        """Text files outside knowledge/ that may cite rule IDs (companion PRs)."""
        return self._texts(rev, EXTERNAL_REF_DIRS, (".md", ".yaml", ".yml", ".json", ".txt"))


@dataclass(frozen=True)
class PullRequest:
    number: int
    title: str
    body: str
    merged_at: str
    merge_commit_sha: str
    author: str
    changed_files: tuple[str, ...]
    diff_excerpt: str

    def evidence(self) -> dict:
        return {
            "source_reference": f"PR #{self.number}",
            "title": self.title,
            "body": self.body[:MAX_BODY_CHARS],
            "merged_at": self.merged_at,
            "changed_files": list(self.changed_files[:MAX_CHANGED_PATHS]),
            "diff_excerpt": self.diff_excerpt,
        }


class GitHubReader:
    """Minimal read-only REST client. ``fetch(url) -> (status, json)`` is
    injectable for tests; by default it uses urllib with an optional read-only
    token from ``KB_GITHUB_READ_TOKEN`` (anonymous for public repositories)."""

    API = "https://api.github.com"

    def __init__(self, *, fetch: Callable[[str], Any] | None = None, token: str | None = None):
        self._fetch = fetch or self._urllib_fetch
        self._token = token if token is not None else os.environ.get("KB_GITHUB_READ_TOKEN", "")

    def _urllib_fetch(self, url: str) -> Any:
        request = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
            **({"Authorization": f"Bearer {self._token}"} if self._token else {}),
        })
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, ValueError, TimeoutError) as exc:
            raise SourceError(f"GitHub read failed: {url}: {exc}") from exc

    def get(self, path: str, **params: Any) -> Any:
        query = ("?" + urllib.parse.urlencode(params)) if params else ""
        return self._fetch(f"{self.API}{path}{query}")

    def merged_prs_since(self, full_name: str, since_iso: str, *, after_number: int = 0,
                         limit: int = 50, max_pages: int = 10) -> list[tuple[int, str]]:
        """``(number, merged_at)`` of PRs merged at or after ``since_iso``, in
        merge-time order, bounded to ``limit``. Every page of the interval is
        read before sorting (search order is not merge order), so a caller that
        advances its cursor to the last RETURNED merge time never skips a PR:
        anything not returned merged at or after that time and is found again
        (events are idempotent). The cursor is the pair (merge time, PR number):
        PRs at exactly ``since_iso`` with a number <= ``after_number`` are
        already consumed, so many PRs sharing one merge second cannot stall it."""
        query = f"repo:{full_name} is:pr is:merged merged:>={since_iso}"
        found: dict[int, str] = {}
        for page in range(1, max_pages + 1):
            data = self.get("/search/issues", q=query, sort="updated", order="asc",
                            per_page=100, page=page)
            items = data.get("items", [])
            for item in items:
                merged_at = str((item.get("pull_request") or {}).get("merged_at") or "")
                if merged_at:
                    found[int(item["number"])] = merged_at
            if len(items) < 100:
                break
        ordered = sorted(
            (pair for pair in found.items()
             if (pair[1], pair[0]) > (since_iso, after_number)),
            key=lambda pair: (pair[1], pair[0]))
        return ordered[:limit]

    def pull_request(self, full_name: str, number: int) -> PullRequest:
        pr = self.get(f"/repos/{full_name}/pulls/{number}")
        files = self.get(f"/repos/{full_name}/pulls/{number}/files", per_page=100)
        paths, excerpt, used = [], [], 0
        for item in files:
            paths.append(str(item.get("filename", "")))
            patch = str(item.get("patch") or "")
            if patch and used < MAX_DIFF_BYTES:
                chunk = f"--- {item.get('filename')}\n{patch}\n"
                room = MAX_DIFF_BYTES - used
                chunk = chunk.encode("utf-8")[:room].decode("utf-8", "ignore")
                excerpt.append(chunk)
                used += len(chunk.encode("utf-8"))
        return PullRequest(
            number=int(pr["number"]), title=str(pr.get("title") or ""),
            body=str(pr.get("body") or ""), merged_at=str(pr.get("merged_at") or ""),
            merge_commit_sha=str(pr.get("merge_commit_sha") or ""),
            author=str((pr.get("user") or {}).get("login") or ""),
            changed_files=tuple(paths), diff_excerpt="".join(excerpt),
        )

    def latest_release(self, full_name: str) -> dict | None:
        releases = self.get(f"/repos/{full_name}/releases", per_page=5)
        for release in releases:
            if not release.get("draft") and not release.get("prerelease"):
                return {"tag": str(release["tag_name"]), "published_at": str(release.get("published_at") or "")}
        return None

    def tags(self, full_name: str, pattern: str) -> list[str]:
        regex = re.compile(_glob_to_regex(pattern))
        return [str(t["name"]) for t in self.get(f"/repos/{full_name}/tags", per_page=100)
                if regex.fullmatch(str(t["name"]))]


def _glob_to_regex(pattern: str) -> str:
    return "".join(".*" if ch == "*" else re.escape(ch) for ch in pattern)


def load_lessons(inbox: str | Path, repo: str) -> list[dict]:
    """Copilot run lessons dropped by runs on this host (``inbox/lessons/<repo>/``).
    Each file: {event_id, repo, run_ref, summary, diff_excerpt?}. Malformed files
    are skipped (and left for inspection), never guessed at."""
    directory = Path(inbox) / "lessons" / repo
    lessons = []
    if not directory.is_dir():
        return lessons
    for path in sorted(directory.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict) or data.get("repo") != repo or not data.get("event_id") \
                or not data.get("summary"):
            continue
        lessons.append({
            "event_id": str(data["event_id"]), "run_ref": str(data.get("run_ref") or ""),
            "summary": str(data["summary"])[:MAX_BODY_CHARS],
            "diff_excerpt": str(data.get("diff_excerpt") or "")[:MAX_DIFF_BYTES],
            "path": str(path),
        })
    return lessons
