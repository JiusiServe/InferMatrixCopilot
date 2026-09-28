"""The publisher: performs the knowledge service's signed outbox items on GitHub.

It runs on the GPU box as the repository owner, through that user's existing
``gh`` login, which never leaves the box and never enters a model environment.
The knowledge service holds no GitHub write credential; this is the only place
knowledge PRs are opened, commented on, queued, paused or closed.

One round (``kb publish --once``; without it, a round per interval):

1. read the service's signed control record over SSH (or a local directory);
   a stale one means the service may be down, and the round does nothing;
2. for every outbox item: verify it with ``outbox.check_item`` (signature,
   expiry, generation, pause, the repository's publication mode in BOTH the
   control record and the publisher's own adapter configuration), perform it,
   record the result locally, then write a signed ack (``kb-ack``) back;
3. an item already performed only has its ack re-sent (the service deletes an
   item once it collected the ack), so a crash between the two never performs
   an item twice. ``open_pr`` also reuses an open PR on its branch.

Writes are double-gated like every outward write in the copilot: GitHub is
only written when ``ALLOW_POST=1`` (and, for anything that pushes a branch,
``ALLOW_PUSH=1``); otherwise the round only records what it would do.

``open_pr`` never trusts a working tree: it rebuilds the change from the
signed file contents on top of the signed ``base_sha`` in a scratch index,
checks every path is a governed knowledge page, pushes the commit to the
item's branch and opens the PR.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

from ..knowledge_service.signing import sign
from .outbox import CONTROL_MAX_AGE, OutboxError, OutboxItem, check_item

ITEM_ID = re.compile(r"[0-9]+-[0-9a-f]{12}")
GOVERNED_PATH = re.compile(r"knowledge/(?:repos/[A-Za-z0-9._-]+|general)/(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+\.(?:md|yaml)")
BRANCH = re.compile(r"kb/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+")
HOLD_LABEL = "kb:hold"
PUSHING = frozenset({"open_pr", "open_companion_pr"})
# retried until done, never acked as failed: stops (pause, close) and reports
# (open_issue: a transient GitHub error must not lose a sweep report)
RETRIED = frozenset({"pause", "close", "open_issue"})


class PublishError(RuntimeError):
    """An item could not be performed; it is acked as failed with this reason."""


# -- where the outbox lives ----------------------------------------------------

class Transport(Protocol):
    def list_items(self) -> list[str]: ...
    def read(self, rel: str) -> bytes: ...
    def write_ack(self, item_id: str, data: bytes) -> None: ...


@dataclass
class LocalTransport:
    """The service state directory on this machine (tests, co-located setups)."""

    root: Path

    def list_items(self) -> list[str]:
        folder = self.root / "outbox"
        return sorted(p.stem for p in folder.glob("*.json") if ITEM_ID.fullmatch(p.stem)) \
            if folder.is_dir() else []

    def read(self, rel: str) -> bytes:
        return (self.root / rel).read_bytes()

    def write_ack(self, item_id: str, data: bytes) -> None:
        folder = self.root / "inbox" / "acks"
        folder.mkdir(parents=True, exist_ok=True)
        tmp = folder / f".{item_id}.tmp"
        tmp.write_bytes(data)
        tmp.replace(folder / f"{item_id}.json")


@dataclass
class SshTransport:
    """``host:/path/to/state_dir`` on the bot host, through the box's ssh config."""

    host: str
    root: str
    run: Callable[..., subprocess.CompletedProcess] = subprocess.run

    @classmethod
    def parse(cls, remote: str) -> "SshTransport":
        host, sep, root = remote.partition(":")
        if not sep or not host or not root.startswith("/"):
            raise SystemExit(f"--remote must be host:/absolute/state_dir, not {remote!r}")
        return cls(host, root.rstrip("/"))

    def _ssh(self, command: str, data: bytes | None = None) -> bytes:
        proc = self.run(["ssh", "-o", "BatchMode=yes", self.host, command], input=data,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if proc.returncode != 0:
            raise OutboxError(f"ssh {self.host}: {proc.stderr.decode(errors='replace')[:300]}")
        return proc.stdout

    def list_items(self) -> list[str]:
        out = self._ssh(f"ls -1 {shlex.quote(self.root + '/outbox')} 2>/dev/null || true").decode()
        return sorted(name[:-5] for name in out.split() if name.endswith(".json") and ITEM_ID.fullmatch(name[:-5]))

    def read(self, rel: str) -> bytes:
        return self._ssh(f"cat {shlex.quote(self.root + '/' + rel)}")

    def write_ack(self, item_id: str, data: bytes) -> None:
        folder = shlex.quote(self.root + "/inbox/acks")
        tmp, final = shlex.quote(f"{self.root}/inbox/acks/.{item_id}.tmp"), \
            shlex.quote(f"{self.root}/inbox/acks/{item_id}.json")
        self._ssh(f"mkdir -p {folder} && cat > {tmp} && mv {tmp} {final}", data)


# -- GitHub through the owner's gh login ------------------------------------------

@dataclass
class Gh:
    """``gh`` and ``git`` as the box owner. ``cwd`` must be inside the owner's
    directory: the machine's gh wrapper picks the login from it."""

    repository: str
    cwd: Path
    run: Callable[..., subprocess.CompletedProcess] = subprocess.run

    def gh(self, *args: str, input: str | None = None, ok_fail: bool = False) -> str:
        proc = self.run(["gh", *args], cwd=self.cwd, input=None if input is None else input.encode(),
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if proc.returncode != 0 and not ok_fail:
            raise PublishError(f"gh {' '.join(args[:3])} failed: {proc.stderr.decode(errors='replace')[:300]}")
        return proc.stdout.decode(errors="replace")

    def pr(self, number: int) -> dict:
        return json.loads(self.gh("pr", "view", str(number), "--repo", self.repository,
                                  "--json", "number,state,isDraft,headRefOid,headRefName,id,labels"))


# -- the publisher -------------------------------------------------------------------

@dataclass
class Publisher:
    transport: Transport
    service_public_key: Any
    publisher_key: Any
    github: Gh
    state_dir: Path
    repo_flags: Mapping[str, tuple[bool, bool]]  # repo -> (publishes, auto_merge), from OUR adapter config
    allow_post: bool = False
    allow_push: bool = False
    author: tuple[str, str] = ("", "")          # (name, email) of the commits, the gh login's owner
    git_remote: str = ""                         # default https://github.com/<repository>.git
    clock: Callable[[], float] = time.time
    log: list[dict] = field(default_factory=list)

    # local records -------------------------------------------------------------
    def _done_path(self, item_id: str) -> Path:
        return self.state_dir / "done" / f"{item_id}.json"

    def _trace(self, **entry) -> None:
        entry = {"at": self.clock(), **entry}
        self.log.append(entry)
        path = self.state_dir / "traces" / "publisher.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")

    def _send_ack(self, ack: dict) -> bool:
        """False when the ack could not be delivered; the completion record
        stays, so the next round re-sends it without repeating the action."""
        envelope = sign("kb-ack", ack, self.publisher_key)
        try:
            self.transport.write_ack(ack["item_id"], json.dumps(envelope, ensure_ascii=False).encode())
            return True
        except (OutboxError, OSError) as exc:
            self._trace(event="ack_undelivered", item=ack["item_id"], error=str(exc))
            return False

    # one round -----------------------------------------------------------------
    def run_once(self) -> dict:
        summary = {"performed": 0, "failed": 0, "resent": 0, "undelivered": 0, "dry_run": 0, "skipped": 0}
        try:
            control = json.loads(self.transport.read("outbox/control.json"))
            # a quick look before verifying (check_item verifies it for real)
            control_issued = float(control["payload"]["issued_at"])
        except (OutboxError, OSError, ValueError, KeyError, TypeError) as exc:
            self._trace(event="no_control", error=str(exc))
            return summary
        if self.clock() - control_issued > CONTROL_MAX_AGE:
            self._trace(event="stale_control", issued_at=control_issued)
            return summary  # the service may be down: act on nothing
        try:
            item_ids = self.transport.list_items()
        except (OutboxError, OSError) as exc:
            self._trace(event="outbox_unreachable", error=str(exc))
            return summary
        for item_id in item_ids:
            done = self._done_path(item_id)
            if done.is_file():
                try:
                    record = json.loads(done.read_text(encoding="utf-8"))
                except ValueError:
                    # never guess whether it was performed: set it aside for people
                    done.replace(done.with_suffix(".corrupt"))
                    self._trace(event="corrupt_record", item=item_id)
                    summary["skipped"] += 1
                    continue
                summary["resent" if self._send_ack(record) else "undelivered"] += 1
                continue
            if done.with_suffix(".corrupt").exists():
                summary["skipped"] += 1  # waits for a person to decide (see the trace)
                continue
            summary[self._handle(item_id, control)] += 1
        return summary

    def _record_done(self, item_id: str, ack: dict) -> None:
        """Atomically: a crash leaves either no record or a complete one."""
        path = self._done_path(item_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=f".{item_id}.", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(ack, ensure_ascii=False, sort_keys=True))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, path)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise

    def _handle(self, item_id: str, control: Any) -> str:
        try:
            envelope = json.loads(self.transport.read(f"outbox/{item_id}.json"))
            payload = envelope.get("payload") if isinstance(envelope, dict) else None
            claimed = str(payload.get("repo", "")) if isinstance(payload, dict) else ""
            publishes, auto_merge = self.repo_flags.get(claimed, (False, False))
            item = check_item(envelope, control, self.service_public_key, now=self.clock(),
                              repo_publishes=publishes, repo_auto_merge=auto_merge)
        except (OutboxError, OSError, ValueError, KeyError, TypeError) as exc:
            # not performed and not acked: an unverifiable item is never
            # answered, and a stale one is superseded by the service itself
            self._trace(event="refused", item=item_id, error=str(exc))
            return "skipped"
        if not self.allow_post or (item.kind in PUSHING and not self.allow_push):
            self._trace(event="dry_run", item=item.id, kind=item.kind, repo=item.repo,
                        body={k: v for k, v in item.body.items() if k not in ("files", "comment", "body")})
            return "dry_run"
        ack = {"item_id": item.id, "kind": item.kind, "changeset_id": str(item.body.get("changeset_id", "")),
               "ok": True, "pr": None, "head_sha": "", "branch": "", "error": ""}
        try:
            ack.update(getattr(self, f"_do_{item.kind}")(item))
        except (PublishError, OSError, ValueError, KeyError, TypeError) as exc:
            ack.update(ok=False, error=str(exc)[:500])
        if not ack["ok"] and item.kind in RETRIED:
            # a stop that did not happen must not be answered as done: the item
            # stays in the outbox and is retried every round until it succeeds
            self._trace(event="retry", item=item.id, kind=item.kind, repo=item.repo, error=ack["error"])
            return "failed"
        self._record_done(item.id, ack)
        self._trace(event="performed" if ack["ok"] else "failed", item=item.id, kind=item.kind,
                    repo=item.repo, ack=ack)
        self._send_ack(ack)
        return "performed" if ack["ok"] else "failed"

    # the actions ---------------------------------------------------------------
    def _checked_head(self, item: OutboxItem) -> dict:
        pr = self.github.pr(int(item.body["pr"]))
        if pr.get("state") != "OPEN":
            raise PublishError(f"PR #{item.body['pr']} is {pr.get('state')}")
        if pr.get("headRefOid") != item.body["head_sha"]:
            raise PublishError(f"PR #{item.body['pr']} head moved to {str(pr.get('headRefOid'))[:12]}")
        return pr

    def _do_open_pr(self, item: OutboxItem, *, draft: bool = False) -> dict:
        body = item.body
        branch = str(body["branch"])
        if not BRANCH.fullmatch(branch):
            raise PublishError(f"refusing branch name {branch!r}")
        files: dict[str, str] = dict(body.get("files") or {})
        deleted = [str(p) for p in body.get("deleted") or []]
        for path in [*files, *deleted]:
            if not GOVERNED_PATH.fullmatch(path) or ".." in path.split("/"):
                raise PublishError(f"refusing to write outside governed knowledge pages: {path}")
        commit = self._build_commit(str(body["base_sha"]), files, deleted, str(body["title"]),
                                    when=item.issued_at)
        existing = json.loads(self.github.gh("pr", "list", "--repo", self.github.repository, "--head", branch,
                                             "--state", "open", "--json", "number,headRefOid,isDraft"))
        if existing:  # performed before a crash: reuse it only if it is exactly this change
            pr = existing[0]
            if len(existing) != 1 or pr["headRefOid"] != commit:
                raise PublishError(f"an open PR on {branch} does not carry the signed change")
            if draft and not pr.get("isDraft"):
                raise PublishError(f"the PR on {branch} must be a draft")
            return {"pr": int(pr["number"]), "head_sha": commit, "branch": branch}
        remote = self.git_remote or f"https://github.com/{self.github.repository}.git"
        listed = self._git("ls-remote", remote, f"refs/heads/{branch}", auth=True).split()
        if not listed:  # expect the branch to be absent: never overwrite anything
            self._git("push", "--quiet", remote, f"{commit}:refs/heads/{branch}",
                      f"--force-with-lease=refs/heads/{branch}:", auth=True)
        elif listed[0] != commit:
            raise PublishError(f"branch {branch} already exists with other content")
        args = ["pr", "create", "--repo", self.github.repository, "--base", "main", "--head", branch,
                "--title", str(body["title"]), "--body-file", "-"]
        self.github.gh(*args, *(["--draft"] if draft else []), input=str(body.get("body") or ""))
        opened = json.loads(self.github.gh("pr", "list", "--repo", self.github.repository, "--head", branch,
                                           "--state", "open", "--json", "number,headRefOid"))
        if len(opened) != 1 or opened[0]["headRefOid"] != commit:
            raise PublishError(f"the PR for {branch} could not be confirmed after creation")
        return {"pr": int(opened[0]["number"]), "head_sha": commit, "branch": branch}

    def _do_open_companion_pr(self, item: OutboxItem) -> dict:
        return self._do_open_pr(item, draft=True)  # companions are always drafts for people

    def _do_post_verdict(self, item: OutboxItem) -> dict:
        """A verdict is only issued for an unpaused repository, under its current
        generation, so posting one also lifts an earlier pause's kb:hold label
        (first, so the precheck the comment triggers no longer sees it)."""
        self._checked_head(item)
        number = str(item.body["pr"])
        self.github.gh("pr", "edit", number, "--repo", self.github.repository, "--remove-label", HOLD_LABEL,
                       ok_fail=True)  # fails when the label is absent; what matters is checked next
        if HOLD_LABEL in {str(label.get("name")) for label in self.github.pr(int(number)).get("labels") or []}:
            raise PublishError(f"PR #{number} still carries {HOLD_LABEL}; the gate would reject it")
        self.github.gh("pr", "comment", number, "--repo", self.github.repository,
                       "--body-file", "-", input=str(item.body["comment"]))
        return {"pr": int(item.body["pr"]), "head_sha": item.body["head_sha"]}

    def _do_enqueue(self, item: OutboxItem) -> dict:
        pr = self._checked_head(item)
        number = str(item.body["pr"])
        if pr.get("isDraft"):  # a resumed PR was turned into a draft by its pause
            self.github.gh("pr", "ready", number, "--repo", self.github.repository)
        self.github.gh("pr", "merge", number, "--repo", self.github.repository, "--merge", "--auto",
                       "--match-head-commit", str(item.body["head_sha"]))
        return {"pr": int(number), "head_sha": item.body["head_sha"]}

    def _do_pause(self, item: OutboxItem) -> dict:
        """Procedure P: out of the merge queue, then draft (the guarantee), then
        the kb:hold label (a record only)."""
        number = str(item.body["pr"])
        pr = self.github.pr(int(number))
        if pr.get("state") != "OPEN":
            return {"pr": int(number)}  # merged or closed already: nothing to stop
        self.github.gh("api", "graphql", "-f", "query=mutation($id:ID!){dequeuePullRequest(input:{id:$id})"
                       "{clientMutationId}}", "-f", f"id={pr['id']}", ok_fail=True)
        self.github.gh("pr", "merge", number, "--repo", self.github.repository, "--disable-auto", ok_fail=True)
        if not pr.get("isDraft"):
            self.github.gh("pr", "ready", number, "--repo", self.github.repository, "--undo")
        if not self.github.pr(int(number)).get("isDraft"):
            raise PublishError(f"PR #{number} is still not a draft")
        self.github.gh("pr", "edit", number, "--repo", self.github.repository, "--add-label", HOLD_LABEL,
                       ok_fail=True)
        return {"pr": int(number)}

    def _do_update_branch(self, item: OutboxItem) -> dict:
        self._checked_head(item)
        self.github.gh("api", "-X", "PUT", f"repos/{self.github.repository}/pulls/{item.body['pr']}/update-branch",
                       "-f", f"expected_head_sha={item.body['head_sha']}")
        return {"pr": int(item.body["pr"])}

    def _do_open_issue(self, item: OutboxItem) -> dict:
        """One issue per title (a sweep report): an existing one is reused."""
        title = str(item.body["title"])
        found = json.loads(self.github.gh("issue", "list", "--repo", self.github.repository, "--state", "all",
                                          "--search", f'in:title "{title}"', "--json", "number,title"))
        for issue in found:
            if issue.get("title") == title:
                return {"pr": int(issue["number"])}
        args = ["issue", "create", "--repo", self.github.repository, "--title", title, "--body-file", "-"]
        for label in item.body.get("labels") or []:
            args += ["--label", str(label)]
        out = self.github.gh(*args, input=str(item.body.get("body") or ""), ok_fail=True)
        if not out.strip():  # a missing label must not lose the report
            out = self.github.gh("issue", "create", "--repo", self.github.repository, "--title", title,
                                 "--body-file", "-", input=str(item.body.get("body") or ""))
        number = out.strip().rsplit("/", 1)[-1]
        return {"pr": int(number) if number.isdigit() else None}

    def _do_close(self, item: OutboxItem) -> dict:
        number = str(item.body["pr"])
        if self.github.pr(int(number)).get("state") == "OPEN":
            self.github.gh("pr", "close", number, "--repo", self.github.repository,
                           "--comment", str(item.body.get("reason") or "closed by the knowledge service"))
        return {"pr": int(number)}

    # git ------------------------------------------------------------------------
    @property
    def clone(self) -> Path:
        return self.state_dir / "clones" / self.github.repository.replace("/", "__")

    def _git(self, *args: str, env: Mapping[str, str] | None = None, input: bytes | None = None,
             auth: bool = False) -> str:
        prefix = ["-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential"] if auth else []
        proc = subprocess.run(["git", "-C", str(self.clone), *prefix, *args], input=input,
                              env={**os.environ, **(env or {})}, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, check=False, cwd=self.github.cwd)
        if proc.returncode != 0:
            raise PublishError(f"git {args[0]} failed: {proc.stderr.decode(errors='replace')[:300]}")
        return proc.stdout.decode().strip()

    def _build_commit(self, base_sha: str, files: Mapping[str, str], deleted: list[str], title: str,
                      *, when: float) -> str:
        """The change as ONE commit on ``base_sha``, built in a scratch index.
        Deterministic (dates from the item), so a retry rebuilds the same SHA."""
        remote = self.git_remote or f"https://github.com/{self.github.repository}.git"
        if not (self.clone / ".git").exists() and not (self.clone / "HEAD").exists():
            self.clone.parent.mkdir(parents=True, exist_ok=True)
            proc = subprocess.run(["git", "clone", "--quiet", "--bare", remote, str(self.clone)],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, cwd=self.github.cwd)
            if proc.returncode != 0:
                raise PublishError(f"git clone failed: {proc.stderr.decode(errors='replace')[:300]}")
        self._git("fetch", "--quiet", remote, "+refs/heads/main:refs/remotes/origin/main")
        if self._git("cat-file", "-t", base_sha) != "commit":
            raise PublishError(f"base {base_sha[:12]} is not a commit")
        with tempfile.TemporaryDirectory() as scratch:
            env = {"GIT_INDEX_FILE": str(Path(scratch) / "index")}
            self._git("read-tree", base_sha, env=env)
            for path, text in sorted(files.items()):
                oid = self._git("hash-object", "-w", "--stdin", input=text.encode("utf-8"))
                self._git("update-index", "--add", "--cacheinfo", f"100644,{oid},{path}", env=env)
            for path in deleted:
                self._git("update-index", "--force-remove", path, env=env)
            tree = self._git("write-tree", env=env)
        name, email = self.author
        if not name or not email:
            raise PublishError("no commit author configured (KB_PUBLISHER_GIT_AUTHOR='Name <email>')")
        date = f"{int(when)} +0000"
        return self._git("commit-tree", tree, "-p", base_sha, "-m", title, env={
            "GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email, "GIT_AUTHOR_DATE": date,
            "GIT_COMMITTER_NAME": name, "GIT_COMMITTER_EMAIL": email, "GIT_COMMITTER_DATE": date})

    def serve(self, *, interval: float, stop=None) -> None:
        import threading

        stop = stop or threading.Event()
        while not stop.is_set():
            self._trace(event="round", **self.run_once())
            stop.wait(interval)
