#!/usr/bin/env python3
"""archive_parent_repo — the PR7 retirement archive (plan §8), scripted.

Runs ENTIRELY while holding the shared checkout flock (`locks/<name>.lock`
inside the TARGET checkout — the same lock EXT1's guard, the v1 backend,
and every v3 run take), so holding it across the capture proves no
external and no v1 run is active. Produces, under --archive-dir:

  1. `archival-branch` commit in the parent repo capturing ALL dirty and
     untracked runtime state EXCEPT secret-bearing files (fail-closed
     secrets pass; see below), then a clean-tree proof.
  2. An independent tagged FULL CLONE (`git clone --no-local`) tagged
     `pr7-archive-<ts>` plus a `git bundle --all` file.
  3. A SQLite-consistent copy of the gitignored debug DB (backup API).
  4. A tarball of `rebase_logs/`.
  5. `ENV_INVENTORY.md`: env-key NAMES ONLY from every parent env source
     that exists (values never leave the machine).
  6. `RESTORE.md` + `restore.sh`: the both-sides restore (parent re-clone
     + state unpack + env recreation from the owner's secret store, AND
     the copilot side's `pre-pr7-retirement` tag deployment — that tag is
     created by the PR7 RUNBOOK step at the deletion commit; this script
     checks for it when --copilot-repo is supplied and records its
     presence or absence in the archive).
  7. `REHEARSAL.md`: the timed restore-rehearsal checklist (PR7
     acceptance requires one timed combined restore).

Secrets, fail-closed (design round-2 F10): path patterns (.env*, *token*,
*key*, *secret*, *credential*) plus a content scan over candidate files.
An UNTRACKED match is excluded from the commit and inventoried by
NAME+sha256. A TRACKED-and-dirty match ABORTS the archive with a
remediation list, UNLESS listed in --secret-allowlist (the values-file
`archival_secret_allowlist`): then it is excluded, inventoried, and the
clean-tree proof asserts "clean except exactly the inventoried allowlist
paths". A failed scan aborts — never archives blind.

EXECUTION is a PR7 action (post-soak). Shipping now, running later.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import os
import re
import sqlite3
import subprocess
import sys
import tarfile
import time
from pathlib import Path

SECRET_PATH_GLOBS = (".env*", "*token*", "*key*", "*secret*", "*credential*")
SECRET_CONTENT_RX = re.compile(
    rb"(api[_-]?key|secret|token|password)\s*[=:]\s*\S{8,}", re.I)


def run(cmd, cwd, **kw):
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True,
                          text=True, **kw)


def _flock(lock_path: Path):
    import fcntl

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        raise SystemExit(f"checkout lock {lock_path} is HELD — an external "
                         "or v1 run is active; archive later")
    return fd


def _is_secret_path(rel: str) -> bool:
    name = Path(rel).name.lower()
    return any(fnmatch.fnmatch(name, g) for g in SECRET_PATH_GLOBS)


def _content_scan(path: Path) -> bool:
    """Scan the WHOLE file incrementally (a credential deep inside a log
    must not slip past a head-only scan); chunks overlap so a match
    straddling a boundary is still seen."""
    overlap = 256
    tail = b""
    try:
        with open(path, "rb") as fh:
            while True:
                chunk = fh.read(1 << 20)
                if not chunk:
                    return False
                if SECRET_CONTENT_RX.search(tail + chunk):
                    return True
                tail = chunk[-overlap:]
    except OSError as exc:
        raise SystemExit(f"secrets scan could not read {path}: {exc} — "
                         "aborting (never archive blind)")


def classify_files(repo: Path, allowlist: set[str]):
    """(to_commit, excluded_untracked, allowlisted_tracked, aborts)"""
    out = run(["git", "status", "--porcelain", "-uall"], repo).stdout
    to_commit, excluded, allowlisted, aborts = [], [], [], []
    for line in out.splitlines():
        status, rel = line[:2], line[3:].strip()
        if not rel or rel.endswith("/"):
            continue
        path = repo / rel
        if not path.is_file():
            continue
        secret = _is_secret_path(rel) or _content_scan(path)
        tracked = "?" not in status
        if not secret:
            to_commit.append(rel)
        elif not tracked:
            excluded.append(rel)
        elif rel in allowlist:
            allowlisted.append(rel)
        else:
            aborts.append(rel)
    return to_commit, excluded, allowlisted, aborts


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent-repo", required=True,
                        help="canonical external checkout (git repo)")
    parser.add_argument("--target-checkout", required=True,
                        help="the target repo holding locks/<name>.lock")
    parser.add_argument("--lock-name", required=True)
    parser.add_argument("--archive-dir", required=True)
    parser.add_argument("--copilot-repo", default="",
                        help="copilot checkout — records the "
                             "pre-pr7-retirement tag's presence")
    parser.add_argument("--secret-allowlist", default="",
                        help="comma-separated repo-relative paths (the "
                             "values-file archival_secret_allowlist)")
    parser.add_argument("--debug-db", default="agent/store/debug_memory.db")
    parser.add_argument("--logs-dir", default="rebase_logs")
    args = parser.parse_args(argv)

    repo = Path(args.parent_repo).resolve()
    archive = Path(args.archive_dir).resolve()
    archive.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    allowlist = {p.strip() for p in args.secret_allowlist.split(",")
                 if p.strip()}
    lock_path = Path(args.target_checkout) / "locks" / \
        f"{args.lock_name}.lock"
    lock_fd = _flock(lock_path)  # held for the WHOLE capture
    try:
        # 1. archival branch: everything except secrets
        to_commit, excluded, allowlisted, aborts = classify_files(
            repo, allowlist)
        if aborts:
            print("ABORT — tracked-and-dirty secret-bearing files outside "
                  "the allowlist:", file=sys.stderr)
            for rel in aborts:
                print(f"  {rel}  (move the secret out, restore the file, "
                      "or add to archival_secret_allowlist)",
                      file=sys.stderr)
            return 3
        branch = f"pr7-archival-{ts}"
        run(["git", "checkout", "-b", branch], repo)
        # a PRE-STAGED secret (added to the index before this script ran)
        # would survive classification and ride into the pathspec-free
        # commit, clone, and bundle — reset the index so the commit
        # contains EXACTLY the classified set (working tree untouched)
        run(["git", "reset", "-q"], repo)
        if to_commit:
            run(["git", "add", "--"] + to_commit, repo)
            run(["git", "-c", "user.name=pr7-archive",
                 "-c", "user.email=pr7-archive@localhost",
                 "commit", "-m",
                 f"PR7 archival: runtime state snapshot {ts}"], repo)
        # clean-tree proof: clean except exactly the inventoried paths
        residue = [ln[3:].strip() for ln in
                   run(["git", "status", "--porcelain", "-uall"],
                       repo).stdout.splitlines()]
        expected = set(excluded) | set(allowlisted)
        unexpected = [r for r in residue if r not in expected]
        if unexpected:
            print(f"ABORT — clean-tree proof failed; unexpected residue: "
                  f"{unexpected[:10]}", file=sys.stderr)
            return 4
        tag = f"pr7-archive-{ts}"
        run(["git", "tag", tag], repo)

        # 2. independent copies
        clone_dir = archive / f"parent-clone-{ts}"
        run(["git", "clone", "--no-local", str(repo), str(clone_dir)],
            archive)
        run(["git", "bundle", "create",
             str(archive / f"parent-{ts}.bundle"), "--all"], repo)

        # 3. consistent debug-DB copy
        db = repo / args.debug_db
        if db.is_file():
            src = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            dst = sqlite3.connect(archive / f"debug_memory-{ts}.db")
            src.backup(dst)
            dst.close()
            src.close()

        # 4. logs tarball — the SAME secret policy applies to tar inputs
        # (an ignored/untracked token-bearing log must not ride into the
        # archive through the tarball after classification excluded it
        # from the commit)
        excluded_logs: list[str] = []
        logs = repo / args.logs_dir
        if logs.is_dir():
            with tarfile.open(archive / f"rebase_logs-{ts}.tar.gz",
                              "w:gz") as tar:
                for path in sorted(logs.rglob("*")):
                    if not path.is_file():
                        continue
                    rel = path.relative_to(repo).as_posix()
                    if _is_secret_path(rel) or _content_scan(path):
                        excluded_logs.append(rel)
                        continue
                    tar.add(path, arcname=rel)

        # 5. env-key NAME inventory + excluded-secret inventory
        inventory = ["# ENV/SECRET inventory (NAMES ONLY — values live in "
                     "the owner's secret store)", ""]
        for env_name in ("agent/.env", ".env"):
            env_file = repo / env_name
            if env_file.is_file():
                keys = [ln.split("=", 1)[0].strip() for ln in
                        env_file.read_text(encoding="utf-8").splitlines()
                        if "=" in ln and not ln.lstrip().startswith("#")]
                inventory.append(f"## {env_name}")
                inventory += [f"- {k}" for k in keys] + [""]
        if excluded or allowlisted or excluded_logs:
            inventory.append("## excluded secret-bearing files "
                             "(recreate from the secret store on restore)")
            for rel in excluded + allowlisted + excluded_logs:
                inventory.append(f"- {rel}  sha256={sha256(repo / rel)}")
        (archive / "ENV_INVENTORY.md").write_text(
            "\n".join(inventory) + "\n", encoding="utf-8")

        # 6-7. restore + rehearsal docs
        copilot_tag_state = "not checked (--copilot-repo not supplied)"
        if args.copilot_repo:
            tags = run(["git", "tag", "-l", "pre-pr7-retirement"],
                       Path(args.copilot_repo)).stdout.strip()
            copilot_tag_state = ("present" if tags else
                                 "ABSENT — create it at the PR7 deletion "
                                 "commit before retiring")
        (archive / "RESTORE.md").write_text(f"""# Combined restore (both sides)

1. Parent: `git clone {archive / f'parent-clone-{ts}'} <canonical-path>`
   (or `git clone parent-{ts}.bundle`), checkout tag `{tag}` /
   branch `{branch}`.
2. Unpack `rebase_logs-{ts}.tar.gz` into the checkout; place
   `debug_memory-{ts}.db` at `{args.debug_db}`.
3. Recreate every file in ENV_INVENTORY.md from the owner's secret store
   (same paths; verify sha256 where recorded).
4. Copilot: deploy the `pre-pr7-retirement` tag (state at archive time:
   {copilot_tag_state}) or revert the PR7 deletion commit; re-add the
   copilot .env orchestrator block from its timestamped backup.
5. Verify: parent `--dry-run` exits 0; copilot doctor green;
   `repo-rebase-native-v1` resolves via --plan-only.
""", encoding="utf-8")
        (archive / "REHEARSAL.md").write_text(
            "# Timed restore rehearsal (PR7 acceptance)\n\n"
            "- [ ] stopwatch start\n"
            "- [ ] RESTORE.md steps 1-4 executed to a scratch path\n"
            "- [ ] step 5 verifications green\n"
            "- [ ] stopwatch stop — record duration in the values file\n",
            encoding="utf-8")
        print(f"archive complete under {archive} (branch {branch}, "
              f"tag {tag}); excluded secrets: {len(excluded)} untracked, "
              f"{len(allowlisted)} allowlisted")
        return 0
    finally:
        import fcntl
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)


if __name__ == "__main__":
    sys.exit(main())
