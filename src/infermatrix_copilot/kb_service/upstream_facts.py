"""Upstream facts for the gate (service) and the local gate (publisher).

``MirrorObserver`` reads one public upstream through a bare mirror (paths,
symbols) and a PR lookup (the service's read-only GitHub reader, or the
publisher's own ``gh api``): the two sides never share a data source, so the
publisher's re-check is independent of what the service saw.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable

from ..knowledge_service.facts import Claim, FactsError, claims_in
from ..knowledge_service.lifecycle import LifecycleError, Page


class MirrorObserver:
    def __init__(self, git_dir: Path, repository: str, pull: Callable[[int], dict], *,
                 url: str | None = None):
        self.git_dir = Path(git_dir)
        self.repository = repository
        self._pull = pull
        self._url = url or f"https://github.com/{repository}.git"
        self._synced = False

    def _git(self, *args: str, ok: tuple[int, ...] = (0,)) -> subprocess.CompletedProcess:
        try:
            proc = subprocess.run(["git", "--git-dir", str(self.git_dir), *args], capture_output=True,
                                  text=True, check=False, timeout=600)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise FactsError(f"git {args[0]}: {exc}") from exc
        if proc.returncode not in ok:
            raise FactsError(f"git {' '.join(args[:2])}: {proc.stderr.strip()[:300]}")
        return proc

    def sync(self) -> None:
        """Fetch the upstream's branches once per observer."""
        if self._synced:
            return
        if not self.git_dir.exists():
            self.git_dir.parent.mkdir(parents=True, exist_ok=True)
            try:
                proc = subprocess.run(["git", "clone", "--bare", "--quiet", self._url, str(self.git_dir)],
                                      capture_output=True, text=True, check=False, timeout=1800)
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise FactsError(f"cannot clone {self.repository}: {exc}") from exc
            if proc.returncode != 0:
                raise FactsError(f"cannot clone {self.repository}: {proc.stderr.strip()[:300]}")
        self._git("fetch", "--quiet", "origin", "+refs/heads/*:refs/heads/*")
        self._synced = True

    def head(self) -> str:
        self.sync()
        return self._git("rev-parse", "HEAD^{commit}").stdout.strip()

    def _commit(self, sha: str) -> None:
        self.sync()
        if self._git("cat-file", "-e", f"{sha}^{{commit}}", ok=(0, 1, 128)).returncode != 0:
            raise FactsError(f"{self.repository} has no commit {sha[:12]}")

    def top_level(self, sha: str) -> set[str]:
        self._commit(sha)
        return set(self._git("ls-tree", "--name-only", sha).stdout.split())

    def path_exists(self, sha: str, path: str) -> bool:
        self._commit(sha)
        return self._git("cat-file", "-e", f"{sha}:{path}", ok=(0, 1, 128)).returncode == 0

    def file_text(self, sha: str, path: str) -> str | None:
        self._commit(sha)
        proc = self._git("cat-file", "blob", f"{sha}:{path}", ok=(0, 1, 128))
        return proc.stdout if proc.returncode == 0 else None

    def pr_diff(self, number: int, merge_sha: str, path: str) -> str:
        """What PR ``number`` changed in ``path``, as GitHub shows it: from the
        merge base of its head with main before it landed (``merge_sha^1``) to
        its head. Right for squash, merge-commit and rebase merges alike (for a
        rebase merge ``merge_sha`` is only the LAST rebased commit)."""
        base, head = self._pr_range(number, merge_sha)
        return self._git("diff", "--no-color", "-U3", base, head, "--", path).stdout

    def _pr_range(self, number: int, merge_sha: str) -> tuple[str, str]:
        cache = self.__dict__.setdefault("_ranges", {})
        if number not in cache:
            self._commit(merge_sha)
            ref = f"refs/kb-pr/{number}"
            self._git("fetch", "--quiet", "origin", f"+refs/pull/{number}/head:{ref}")
            head = self._git("rev-parse", f"{ref}^{{commit}}").stdout.strip()
            base = self._git("merge-base", f"{merge_sha}^1", head).stdout.strip()
            cache[number] = (base, head)
        return cache[number]

    def pull(self, number: int) -> dict:
        try:
            data = self._pull(number)
        except FactsError:
            raise
        except Exception as exc:  # noqa: BLE001 - the API is down or rate-limited
            raise FactsError(f"{self.repository} PR #{number}: {exc}") from exc
        if not isinstance(data, dict):
            raise FactsError(f"{self.repository} PR #{number}: unexpected answer")
        return data


def change_claims(head: dict[str, str], blocks, top_level: set[str]) -> list[Claim]:
    """The claims of every rule the change adds, edits or retires (prose and
    purged rules carry none)."""
    claims: list[Claim] = []
    for block in blocks:
        if block.kind != "rule" or block.op == "purge" or block.path not in head:
            continue
        try:
            section = Page.parse(head[block.path]).rule(block.rule_id)
            footer = section.footer
        except (LifecycleError, KeyError):
            continue  # L1 already refused anything unparsable
        claims += claims_in(section.body_without_footer, top_level, active=footer.status == "active",
                            evidence=footer.evidence)
    return claims
