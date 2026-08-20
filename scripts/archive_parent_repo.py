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


def _acquire_checkout_lock(target_checkout: Path, lock_name: str):
    """The SHARED hardened checkout lock (PR-boundary F20): the same
    `CheckoutLock` every v3/v1/EXT1 participant takes — it validates the
    checkout is a real git worktree with canonical, symlink-safe lock
    components, so a typo'd/fake target cannot 'succeed' while the real
    lock is held elsewhere."""
    repo_src = Path(__file__).resolve().parents[1] / "src"
    if str(repo_src) not in sys.path:
        sys.path.insert(0, str(repo_src))
    from infermatrix_copilot.rebase_engine.runctx import CheckoutLock

    probe = subprocess.run(
        ["git", "-C", str(target_checkout), "rev-parse",
         "--show-toplevel"], capture_output=True, text=True)
    toplevel = probe.stdout.strip()
    if probe.returncode != 0 or not toplevel or \
            Path(toplevel).resolve() != Path(target_checkout).resolve():
        raise SystemExit(
            f"--target-checkout {target_checkout} is not a git "
            "worktree's TOPLEVEL — a nested or fake directory would lock "
            "a different inode than the real checkout's participants "
            "(round-2 F11; hook: --is-inside-work-tree accepted "
            "subdirectories)")
    lock = CheckoutLock(Path(target_checkout), lock_name)
    if lock.acquire(blocking=False) is False:
        if "contention" == lock.last_failure.split(":")[0]:
            raise SystemExit(
                f"checkout lock {lock_name!r} in {target_checkout} is "
                "HELD — an external or v1 run is active; archive later")
        raise SystemExit(
            f"checkout lock REFUSED (not contention): {lock.last_failure}"
            " — a typo'd/fake/symlinked target must never let the "
            "archive proceed while the real lock is elsewhere")
    return lock


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
    parser.add_argument("--allow-missing-db", action="store_true",
                        help="owner waiver: archive without the debug DB")
    parser.add_argument("--allow-missing-logs", action="store_true",
                        help="owner waiver: archive without the logs dir")
    parser.add_argument("--accept-db-content", action="store_true",
                        help="owner reviewed the debug DB's token-like "
                             "content (debug rows may quote error text)")
    parser.add_argument("--skip-copilot-check", action="store_true",
                        help="owner waiver: archive without verifying "
                             "the copilot pre-pr7-retirement tag")
    args = parser.parse_args(argv)

    # PREFLIGHT (round-3 F3): every owner-input refusal fires BEFORE any
    # parent/archive mutation — a refused invocation must leave the live
    # parent untouched
    if not args.copilot_repo and not args.skip_copilot_check:
        print("ABORT — the combined restore requires the copilot "
              "pre-pr7-retirement tag: pass --copilot-repo to verify it, "
              "or --skip-copilot-check to record the owner's waiver",
              file=sys.stderr)
        return 7
    if args.copilot_repo:
        tag_probe = subprocess.run(
            ["git", "-C", args.copilot_repo, "tag", "-l",
             "pre-pr7-retirement"], capture_output=True, text=True)
        if tag_probe.returncode != 0 or not tag_probe.stdout.strip():
            print("ABORT — --copilot-repo supplied but the "
                  "pre-pr7-retirement tag does not exist; create it at "
                  "the PR7 deletion commit first", file=sys.stderr)
            return 7

    repo = Path(args.parent_repo).resolve()
    archive = Path(args.archive_dir).resolve()
    archive.mkdir(parents=True, exist_ok=True)
    import uuid

    # unique per invocation: same-second reruns (a refused first attempt,
    # then a corrected one) must not collide on branch/tag names
    ts = time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    allowlist = {p.strip() for p in args.secret_allowlist.split(",")
                 if p.strip()}
    lock = _acquire_checkout_lock(Path(args.target_checkout),
                                  args.lock_name)  # WHOLE capture
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

        # 1b. the ARCHIVE'S OWN final surfaces obey the secret policy too
        # (PR-boundary F19): the archival branch's HEAD TREE is scanned
        # blob by blob — a CLEAN COMMITTED secret aborts unless
        # allowlisted (it cannot be excluded without rewriting history;
        # allowlisting records the owner's acceptance). Full HISTORY
        # (the bundle) is deliberately NOT scanned — recorded owner
        # position: history predates archival and is governed by the
        # repo's own hygiene; the NAME inventory covers env files.
        # CONTENT decides for committed blobs: the aggressive *key*/*token*
        # path globs exist for working-state env files; on a whole tree
        # they would flag benign names (keyboard.py) whose content is
        # right there to scan.
        committed_hits: list[str] = []
        name_flagged_tree: list[str] = []
        tree_raw = subprocess.run(
            ["git", "ls-tree", "-r", "-z", "--name-only", "HEAD"],
            cwd=repo, capture_output=True, check=True).stdout
        for rel_b in tree_raw.split(b"\0"):
            if not rel_b:  # only the terminal empty NUL field — an
                continue   # all-whitespace FILENAME is a real tracked path
            rel = rel_b.decode("utf-8", "surrogateescape")
            blob = subprocess.run(
                ["git", "cat-file", "blob", f"HEAD:{rel}"], cwd=repo,
                capture_output=True, check=True).stdout
            if _is_secret_path(rel):
                # a committed env-NAMED file is inventoried even when its
                # content scans clean (round-2 F13) — the restore
                # procedure must know it exists
                name_flagged_tree.append(rel)
            if SECRET_CONTENT_RX.search(blob):
                if rel in allowlist:
                    if rel not in allowlisted:
                        allowlisted.append(rel)
                else:
                    committed_hits.append(rel)
        if committed_hits:
            print("ABORT — secret-bearing files in the archival branch's "
                  "COMMITTED tree outside the allowlist:", file=sys.stderr)
            for rel in committed_hits:
                print(f"  {rel}", file=sys.stderr)
            return 5

        # 2. independent copies
        clone_dir = archive / f"parent-clone-{ts}"
        run(["git", "clone", "--no-local", str(repo), str(clone_dir)],
            archive)
        run(["git", "bundle", "create",
             str(archive / f"parent-{ts}.bundle"), "--all"], repo)

        # 3. consistent debug-DB copy — REQUIRED unless the owner
        # explicitly waives it (PR-boundary F21: archive success must
        # guarantee a self-contained restore), and the CONSISTENT COPY's
        # bytes obey the secret policy (WAL-only secrets consolidate into
        # the backup — F19) unless --accept-db-content records the
        # owner's review (debug rows legitimately QUOTE error text that
        # can look token-like).
        db = repo / args.debug_db
        db_copy = archive / f"debug_memory-{ts}.db"
        if db.is_file():
            src = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            dst = sqlite3.connect(db_copy)
            src.backup(dst)
            dst.close()
            src.close()
            if not args.accept_db_content and _content_scan(db_copy):
                db_copy.unlink()
                print("ABORT — the debug-DB copy contains token-like "
                      "content; review the store and re-run with "
                      "--accept-db-content to record acceptance",
                      file=sys.stderr)
                return 6
        elif not args.allow_missing_db:
            print(f"ABORT — debug DB {db} is missing; a restore without "
                  "it is not self-contained (pass --allow-missing-db to "
                  "record the waiver)", file=sys.stderr)
            return 6

        # 4. logs tarball — the SAME secret policy applies to tar inputs
        # (an ignored/untracked token-bearing log must not ride into the
        # archive through the tarball after classification excluded it
        # from the commit)
        excluded_logs: list[str] = []
        logs = repo / args.logs_dir
        if not logs.is_dir() and not args.allow_missing_logs:
            print(f"ABORT — logs dir {logs} is missing; pass "
                  "--allow-missing-logs to record the waiver",
                  file=sys.stderr)
            return 6
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
        env_like = sorted({str(q.relative_to(repo)) for q in
                           list(repo.glob(".env*"))
                           + list(repo.glob("*/.env*"))
                           if q.is_file()}
                          | set(name_flagged_tree))
        for env_name in env_like:
            env_file = repo / env_name
            if not env_file.is_file():
                continue
            keys = [ln.split("=", 1)[0].strip() for ln in
                    env_file.read_text(encoding="utf-8",
                                       errors="replace").splitlines()
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

        # 6-7. restore script + docs. The copilot tag is FAIL-CLOSED
        # when the copilot side is in scope (PR-boundary F21): restore
        # instructions that reference a tag that does not exist are not
        # a restore path.
        # (tag/waiver already validated in the pre-mutation preflight)
        copilot_tag_state = "present" if args.copilot_repo \
            else "owner-waived (--skip-copilot-check)"
        restore_sh = archive / "restore.sh"
        db_rel = db_copy.name if db_copy.exists() else ""
        restore_sh.write_text(f"""#!/usr/bin/env bash
# Self-contained parent-side restore (generated by archive_parent_repo).
# Every artifact is addressed RELATIVE to this script, so the archive
# directory can be moved/copied whole. Usage: restore.sh <destination>
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DEST="${{1:?usage: restore.sh <destination-path>}}"
git clone "$HERE/parent-clone-{ts}" "$DEST"
git -C "$DEST" checkout "{branch}"
TARBALL="$HERE/rebase_logs-{ts}.tar.gz"
if [ -f "$TARBALL" ]; then
  tar -xzf "$TARBALL" -C "$DEST"
elif [ "{1 if args.allow_missing_logs else 0}" != "1" ]; then
  echo "ERROR: required logs tarball missing from the archive" >&2
  exit 1
fi
if [ -n "{db_rel}" ]; then
  if [ ! -f "$HERE/{db_rel}" ]; then
    echo "ERROR: required debug-DB copy missing from the archive" >&2
    exit 1
  fi
  mkdir -p "$DEST/$(dirname "{args.debug_db}")"
  cp "$HERE/{db_rel}" "$DEST/{args.debug_db}"
elif [ "{1 if args.allow_missing_db else 0}" != "1" ]; then
  echo "ERROR: archive carries no debug-DB copy and no waiver" >&2
  exit 1
fi
echo "parent restored to $DEST at branch {branch} (tag {tag})."
echo "NEXT (manual): recreate the files in ENV_INVENTORY.md from the"
echo "owner's secret store, and deploy the copilot pre-pr7-retirement tag."
""", encoding="utf-8")
        restore_sh.chmod(0o755)
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
        lock.release()


if __name__ == "__main__":
    sys.exit(main())
