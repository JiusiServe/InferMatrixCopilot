"""Knowledge-layer attestation — canonical LOGICAL digests for §8 fairness.

A bare file hash of a SQLite store is meaningless under WAL (committed rows
may live only in the `-wal` sidecar), so the digest here is over a canonical
row dump read through a read-only connection's snapshot: every row of the
store's entry table, ordered by id, serialized deterministically. Skills
directories digest as a per-file relpath→sha256 catalog of `*/SKILL.md`.

Consumers: the v3 prelude records the OPENING provenance block (fail-closed
on declared-but-broken layers); the compare step records the CLOSING block
and the parent-layer `knowledge_drift` verdict; `scripts/knowledge_digest.py`
gives the RUNBOOK the same functions standalone (ext-world attestations,
WAL-safe snapshot/restore). Digesting never writes: connections are
`mode=ro` URIs.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path

from ..memory.debug_memory import readonly_uri


def _rows_digest(conn: sqlite3.Connection, table: str) -> str:
    """sha256 over the canonical serialization of every row of `table`,
    ordered by id — WAL-consistent because it reads through the connection's
    own snapshot."""
    h = hashlib.sha256()
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
    for row in conn.execute(
            f"SELECT {','.join(cols)} FROM {table} ORDER BY id"):
        h.update(json.dumps(list(row), ensure_ascii=False,
                            default=str).encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


def debug_db_digest(db_path: str | Path) -> str:
    """Logical digest of a debug store (parent `debug_entries` or copilot
    `entries` schema — detected). Raises on a missing/corrupt store."""
    path = Path(db_path)
    if not path.is_file():
        raise FileNotFoundError(f"no debug store at {path}")
    conn = sqlite3.connect(readonly_uri(path), uri=True)
    try:
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        for table in ("debug_entries", "entries"):
            if table in tables:
                return _rows_digest(conn, table)
        raise sqlite3.DatabaseError(
            f"{path}: neither a parent nor a copilot debug store "
            f"(tables: {sorted(tables)[:6]})")
    finally:
        conn.close()


def skills_catalog(skills_dir: str | Path, *,
                   validate: bool = False) -> dict[str, str]:
    """{relative SKILL.md path: sha256} for every skill under `skills_dir`,
    sorted; an absent directory is an empty catalog (a DECLARED-but-missing
    dir is the prelude's fail-closed check, not this function's).
    `validate=True` additionally requires every file to PARSE as a skill —
    hashing bytes that `SkillStore` would silently skip at retrieval time
    would attest knowledge the run can never actually read (PR-boundary
    F2)."""
    root = Path(skills_dir)
    if not root.is_dir():
        return {}
    out: dict[str, str] = {}
    for p in sorted(root.glob("*/SKILL.md")):
        if validate:
            from ..memory.skills import _parse_skill

            if _parse_skill(p) is None:
                raise ValueError(
                    f"{p} does not parse as a skill — retrieval would "
                    "silently skip it; fix or remove it before attesting")
        out[str(p.relative_to(root))] = hashlib.sha256(
            p.read_bytes()).hexdigest()
    return out


def skills_catalog_digest(catalog: dict[str, str]) -> str:
    """Stable digest of a `skills_catalog()` result."""
    h = hashlib.sha256()
    for rel, digest in sorted(catalog.items()):
        h.update(f"{rel}\0{digest}\n".encode("utf-8"))
    return h.hexdigest()


def attest_layers(*, parent_debug_db: str = "",
                  parent_skills_dir: str = "",
                  parent_upstream_column: str = "") -> dict:
    """The provenance block for the DECLARED parent layers: per-layer logical
    digests. Raises on a declared-but-unreadable layer (the prelude turns
    that into BLOCKED); an undeclared ("") layer is simply absent from the
    block. The debug layer is validated against the EXACT parent retrieval
    schema (tables, columns, FTS answers a probe) — a copilot-schema or
    half-broken store must fail HERE, at the gate, not degrade silently
    mid-run after a green attestation."""
    block: dict = {}
    if parent_debug_db:
        from .parent_compat import ParentDebugMemory

        probe = ParentDebugMemory(  # schema-validating open (exact shape)
            parent_debug_db, upstream_column=parent_upstream_column)
        # index/content consistency via FTS5's OWN external-content
        # integrity check — the complete verification (hand-rolled
        # phrase/token probes kept failing review for a reason: phrase
        # matching accepts subsequences, so a SHORTENED content field
        # with stale postings still matched). `integrity-check` with
        # rank=1 compares the full indexed token stream against the
        # content table, catching missing rows, per-column staleness,
        # and shortened/extended content alike. It is a write-flavored
        # command, so it runs on a PRIVATE snapshot copy (sqlite backup
        # API) — the parent store itself stays strictly unwritten.
        import tempfile

        fd, tmp_copy = tempfile.mkstemp(suffix=".attest.db")
        os.close(fd)
        try:
            snap = sqlite3.connect(tmp_copy)
            try:
                probe._conn.backup(snap)
                snap.execute(
                    "INSERT INTO debug_entries_fts(debug_entries_fts, "
                    "rank) VALUES('integrity-check', 1)")
            except sqlite3.DatabaseError as exc:
                raise sqlite3.DatabaseError(
                    f"{parent_debug_db}: FTS index does not match the "
                    f"content table ({exc}) — rebuild the parent index "
                    "before attesting this layer") from exc
            finally:
                snap.close()
        finally:
            os.unlink(tmp_copy)
        block["parent_debug_db"] = {
            "path": parent_debug_db,
            "digest": debug_db_digest(parent_debug_db),
        }
    if parent_skills_dir:
        skills_root = Path(parent_skills_dir)
        if not skills_root.is_dir():
            raise FileNotFoundError(
                f"declared parent skills dir missing: {parent_skills_dir}")
        catalog = skills_catalog(skills_root, validate=True)
        block["parent_skills_dir"] = {
            "path": parent_skills_dir,
            "digest": skills_catalog_digest(catalog),
            "skills": len(catalog),
        }
    return block


def snapshot_debug_db(db_path: str | Path, dest: str | Path) -> str:
    """WAL-safe consistent copy of a SQLite debug store via the sqlite
    backup API (captures committed WAL content; never mutates the source).
    Returns the logical digest of the RESULTING snapshot — record it in the
    freeze table."""
    src = sqlite3.connect(readonly_uri(db_path), uri=True)
    try:
        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        dst = sqlite3.connect(str(dest))
        try:
            src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()
    return debug_db_digest(dest)


def restore_debug_db(snapshot: str | Path, target: str | Path) -> str:
    """Restore a snapshot over `target`, removing stale `-wal`/`-shm`
    sidecars FIRST so the restored file can never have a previous run's WAL
    attached, and normalizing the restored file out of WAL mode so it is
    fully self-contained (a WAL-marked header would make the next open
    recreate sidecars; the store's owner re-enables WAL on its own next
    open). Caller must hold the world's exclusion lock (RUNBOOK: the
    checkout flock) across the whole call. Returns the restored digest.

    Crash-safety (PR-boundary F15): before an uncheckpointable target's
    sidecars are touched, a DURABLE consistent copy of the live target
    (sqlite backup API — WAL rows included) lands at
    `<target>.pre-restore-guard.db`; a SIGKILL anywhere later leaves that
    guard on disk, and the next restore call SELF-HEALS an unreadable
    target from it before proceeding. The guard is removed only after a
    fully successful restore. Staging uses a unique O_EXCL temp file
    (PR-boundary F14) — a pre-planted symlink at a predictable name can
    neither redirect the staged write nor be installed as the target."""
    import os
    import tempfile

    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    guard = target.with_name(target.name + ".pre-restore-guard.db")
    # SELF-HEAL a previous crash: a leftover guard plus an unreadable
    # target means the crash hit between sidecar-aside and replace —
    # the guard IS the pre-restore world
    if guard.exists() and target.exists():
        try:
            conn = sqlite3.connect(readonly_uri(target), uri=True)
            try:
                ok = conn.execute(
                    "PRAGMA integrity_check").fetchone()[0] == "ok"
            finally:
                conn.close()
        except sqlite3.Error:
            ok = False
        if not ok:
            os.replace(guard, target)
            for suffix in ("-wal", "-shm"):
                stale = Path(str(target) + suffix)
                stale.unlink(missing_ok=True)
                Path(str(target) + suffix + ".pre-restore").unlink(
                    missing_ok=True)
    # STAGE AND VALIDATE FIRST: only after the staged copy proves readable
    # may the target's committed WAL data be touched — a missing/corrupt
    # snapshot must fail the restore with the target fully intact
    fd, tmp_name = tempfile.mkstemp(dir=target.parent,
                                    prefix=target.name + ".restore-",
                                    suffix=".tmp")
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        tmp.write_bytes(Path(snapshot).read_bytes())
        conn = sqlite3.connect(tmp)
        try:
            conn.execute("PRAGMA journal_mode=DELETE")
            if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise sqlite3.DatabaseError(
                    f"snapshot {snapshot} fails integrity_check")
            conn.commit()
        finally:
            conn.close()
        staged_digest = debug_db_digest(tmp)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    # Consolidate the target BEFORE touching its sidecars: a VERIFIED
    # checkpoint folds WAL-resident committed rows into the main file, so
    # a failed replace can no longer lose them (the caller holds the
    # exclusion lock — no writers). `wal_checkpoint` reports busy=1
    # without raising, so its result row is checked, not assumed. A
    # target that cannot checkpoint keeps its sidecars PRESERVED ASIDE,
    # and a failure at the final replace rolls them back — every failure
    # path leaves the original target fully readable.
    preserved: list[tuple] = []
    if target.exists():
        checkpointed = False
        try:
            conn = sqlite3.connect(target)
            try:
                row = conn.execute(
                    "PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
                conn.execute("PRAGMA journal_mode=DELETE")
                conn.commit()
                # a MISSING result row is unproven, not success
                checkpointed = row is not None and int(row[0]) == 0
            finally:
                conn.close()
        except sqlite3.Error:
            checkpointed = False
        if not checkpointed:
            # DURABLE guard BEFORE any sidecar move (F15): a consistent
            # backup-API copy of the live target, WAL rows included —
            # the self-heal source if the process dies mid-swap. A main
            # file so corrupt the backup API itself refuses cannot be
            # guarded (there is no consistent state to copy) — the
            # exception-handler rollback still restores its sidecars.
            try:
                src = sqlite3.connect(readonly_uri(target), uri=True)
                try:
                    gconn = sqlite3.connect(guard)
                    try:
                        src.backup(gconn)
                    finally:
                        gconn.close()
                finally:
                    src.close()
            except sqlite3.Error:
                guard.unlink(missing_ok=True)
            try:
                for suffix in ("-wal", "-shm"):
                    side = Path(str(target) + suffix)
                    if side.exists():
                        aside = Path(str(side) + ".pre-restore")
                        os.replace(side, aside)
                        preserved.append((side, aside))
            except BaseException:
                # a PARTIAL preserve (wal moved, shm move failed) must not
                # strand the wal aside — roll back what moved, then fail
                for side, aside in preserved:
                    if aside.exists():
                        os.replace(aside, side)
                guard.unlink(missing_ok=True)
                raise
    try:
        for suffix in ("-wal", "-shm"):
            side = Path(str(target) + suffix)
            if side.exists():
                side.unlink()
        os.replace(tmp, target)
    except BaseException:
        for side, aside in preserved:
            if aside.exists():
                os.replace(aside, side)  # the old target is whole again
        raise
    for _side, aside in preserved:
        aside.unlink(missing_ok=True)
    guard.unlink(missing_ok=True)
    return staged_digest
