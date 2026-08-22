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
    _seen_names: dict[str, str] = {}
    for p in sorted(root.glob("*/SKILL.md")):
        if validate:
            from ..memory.skills import _parse_skill

            skill = _parse_skill(p)
            if skill is None:
                raise ValueError(
                    f"{p} does not parse as a skill — retrieval would "
                    "silently skip it; fix or remove it before attesting")
            # operational schema over the RAW frontmatter (round-3
            # F6): every field SkillStore.find consumes must carry its
            # retrieval type — parse-time str() coercion would otherwise
            # attest `description: [x]` as the literal string "['x']",
            # and a list-typed name is unhashable at retrieval
            import yaml as _yaml

            meta = _yaml.safe_load(
                p.read_text(encoding="utf-8").split("---", 2)[1])
            # STRICT raw types (round-4 F3 / round-5 F2): no falsey or
            # null laundering at the GATE — empty/null frontmatter is a
            # malformed seed; `status: false` would load, stringify to
            # "False" and be silently dropped by SkillStore.load_all
            if meta is None or not isinstance(meta, dict):
                raise ValueError(
                    f"{p}: skill frontmatter must be a non-empty "
                    "mapping")
            name = meta.get("name", p.parent.name)
            if not isinstance(name, str) or not name.strip():
                raise ValueError(f"{p}: skill name must be a non-empty "
                                 "string")
            for fld in ("description", "trigger", "status"):
                if fld in meta and not isinstance(meta[fld], str):
                    raise ValueError(
                        f"{p}: skill {fld} must be a scalar string")
            # ABSENT modules is fine ([]); a PRESENT non-list —
            # explicit null included — is not (round-5 F2)
            mods = meta["modules"] if "modules" in meta else []
            if not isinstance(mods, list) or \
                    not all(isinstance(m, str) for m in mods):
                raise ValueError(
                    f"{p}: skill modules must be a list of strings")
            if name in _seen_names:
                raise ValueError(
                    f"{p}: duplicate effective skill name "
                    f"{name!r} (also {_seen_names[name]}) — "
                    "retrieval collisions are silent")
            _seen_names[name] = str(p)
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
    # SELF-HEAL a previous crash: guard removal is the SUCCESSFUL
    # restore's last act, so any leftover guard means the previous
    # attempt died mid-swap and the target's state is UNKNOWN — a
    # structurally valid main file can still be missing committed
    # WAL-resident rows (round-2 F9), so the heal is UNCONDITIONAL, not
    # integrity-gated. A guard that is not a regular file (a planted
    # symlink — round-2 F10) is hostile: refuse to consume it.
    if guard.exists():
        if guard.is_symlink() or not guard.is_file():
            raise OSError(
                f"pre-restore guard {guard} is not a regular file — "
                "refusing to self-heal from a planted path")
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
    # From here the staged tmp must NEVER outlive the attempt: a
    # guard abort, preserve failure, or failed final replace all
    # leave a snapshot-sized .restore-*.tmp behind otherwise, and
    # retries would accumulate full DB copies (round-5 F3)
    try:
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
                # the self-heal source if the process dies mid-swap. Built
                # at a UNIQUE temp path and atomically renamed onto the
                # guard name, so a planted symlink at the predictable name
                # is replaced, never followed (round-2 F10). A guard
                # failure on a READABLE target ABORTS (proceeding without
                # crash protection was the round-2 F9 fail-open); only a
                # main file so corrupt the backup API itself refuses —
                # where no consistent copy can exist — proceeds guardless,
                # protected by the exception-handler sidecar rollback.
                import tempfile as _tf

                gfd, gtmp = _tf.mkstemp(dir=target.parent,
                                        prefix=guard.name + ".",
                                        suffix=".tmp")
                os.close(gfd)
                try:
                    src = sqlite3.connect(readonly_uri(target), uri=True)
                    try:
                        gconn = sqlite3.connect(gtmp)
                        try:
                            src.backup(gconn)
                        finally:
                            gconn.close()
                    finally:
                        src.close()
                    guard.unlink(missing_ok=True)  # replace even a symlink
                    os.replace(gtmp, guard)
                except sqlite3.Error as backup_exc:
                    Path(gtmp).unlink(missing_ok=True)
                    try:
                        probe = sqlite3.connect(readonly_uri(target),
                                                uri=True)
                        try:
                            readable = probe.execute(
                                "PRAGMA integrity_check").fetchone()[0] == "ok"
                        finally:
                            probe.close()
                    except sqlite3.Error as probe_exc:
                        # UNKNOWN is not corrupt (round-3 F8): only a
                        # DEFINITIVE corruption verdict (NOTADB/CORRUPT —
                        # restore's remedy case) may proceed guardless. A
                        # transient/environmental error (locked, disk IO →
                        # OperationalError/InterfaceError) leaves the
                        # target's state unknown and must abort BEFORE any
                        # sidecar move, never strip crash protection.
                        code = getattr(probe_exc, "sqlite_errorcode",
                                       None)
                        definitive = code is not None and (code & 0xff) in (
                            sqlite3.SQLITE_CORRUPT, sqlite3.SQLITE_NOTADB)
                        if not definitive:
                            raise sqlite3.DatabaseError(
                                "pre-restore guard failed and the target's "
                                f"state is UNKNOWN ({probe_exc}) — refusing "
                                "to touch its sidecars") from probe_exc
                        readable = False
                    if readable:
                        raise sqlite3.DatabaseError(
                            "could not create the pre-restore guard for a "
                            f"READABLE target ({backup_exc}) — refusing to "
                            "swap without crash protection")
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
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
