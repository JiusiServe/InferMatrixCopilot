"""Knowledge migration — the PR4d deployment-time cutover tool (design D6).

Moves the parent rebase agent's knowledge and the copilot's legacy store
locations into the per-repo runtime state dir, once, explicitly, under
every exclusion lock. EXECUTION is a post-PR6-validation owner action
(Rev 8 Decision 6); this module only ships the machinery.

Guarantees, each pinned by test:
- **Locks held for the full duration**: the adapter's checkout flock, the
  state lock, and the knowledge run-lock EXCLUSIVE (every copilot run for
  the repo holds it shared, so no store writer can be alive or start).
- **Per-store journaled transaction**: the target debug DB is rebuilt as
  a WAL-safe sqlite-backup COPY of the existing target (ids preserved —
  lineage stays stable) plus the newly ingested source rows, at a `.migrate-tmp`
  path, then atomically replaces the target after a versioned backup;
  candidates merge is backup + tmp+rename; seed-skill adds are per-file
  tmp+rename, digest-journaled, skip-on-exact-digest-match (redo
  converges, rollback deletes only exact matches). Existing runtime state
  (`skills_runtime` promoted skills, overlay, decisions, harvest
  checkpoints) is neither source nor target.
- **Self-contained source identity** `<store-tag>#<rowid>@<row-digest-12>`
  per migrated row: identical frozen inputs ⇒ strict no-op; a changed
  source row versions-and-retires exactly its own target row.
- **Complete field mapping** for both input schema families (parent,
  copilot-legacy), verification synthesized so the write contract holds.
- **MIGRATION_COMPLETE.json** (schema + per-store digests) is written
  durably as the LAST act — the activation flag refuses to resolve
  without it.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path

from ..memory.debug_memory import ADDITIVE_COLUMNS, DebugMemory
from ..memory.paths import KnowledgePaths, KnowledgeRunLock
from . import knowledge_attest as ka

_PARENT_STATUS_MAP = {"active": "active", "stale": "stale",
                      "inactive": "stale"}


@dataclass
class MigrationReport:
    sources: dict = field(default_factory=dict)
    ingested: int = 0
    skipped_unchanged: int = 0
    reversioned: int = 0
    retired_by_dedup: int = 0
    skills_added: list = field(default_factory=list)
    skills_collisions: list = field(default_factory=list)
    candidates_merged: int = 0
    notes: list = field(default_factory=list)

    def render(self) -> str:
        lines = ["# MIGRATION_REPORT", "",
                 f"- ingested rows: {self.ingested}",
                 f"- skipped (identical source identity): "
                 f"{self.skipped_unchanged}",
                 f"- re-versioned (changed source rows): "
                 f"{self.reversioned}",
                 f"- retired by dedup: {self.retired_by_dedup}",
                 f"- seed skills added: {len(self.skills_added)}",
                 f"- seed collisions (existing adapter skill wins): "
                 f"{len(self.skills_collisions)}",
                 f"- candidates merged: {self.candidates_merged}", "",
                 "## Sources"]
        for tag, meta in self.sources.items():
            lines.append(f"- {tag}: {meta['path']} "
                         f"digest={meta['digest'][:12]} "
                         f"rows={meta.get('rows', '?')}")
        if self.skills_added:
            lines.append("")
            lines.append("## Seed skills added (git-visible; owner "
                         "reviews/commits the adapter diff)")
            lines += [f"- {name}" for name in self.skills_added]
        if self.skills_collisions:
            lines.append("")
            lines.append("## Seed collisions (parent copy NOT installed)")
            lines += [f"- {name}" for name in self.skills_collisions]
        if self.notes:
            lines.append("")
            lines.append("## Per-row notes")
            lines += [f"- {n}" for n in self.notes[:200]]
        return "\n".join(lines) + "\n"


def _row_digest(row: dict) -> str:
    return hashlib.sha256(json.dumps(
        row, sort_keys=True, ensure_ascii=False,
        default=str).encode("utf-8")).hexdigest()[:12]


def _durable_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp-{os.getpid()}")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def _parent_rows(db_path: Path) -> list[dict]:
    conn = sqlite3.connect(
        f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM debug_entries ORDER BY id")]
    finally:
        conn.close()


def _legacy_rows(db_path: Path, repo: str) -> list[dict]:
    """Rows FOR THIS REPO only — the legacy global/adapter-tree stores
    are shared across repos, and migrating one repo must never copy
    another's knowledge into its repo-scoped state DB."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM entries WHERE repo = ? ORDER BY id", (repo,))]
    finally:
        conn.close()


def _synthesize_key(symptom: str) -> str:
    import re
    tokens = re.findall(r"[a-z0-9]+", (symptom or "").lower())
    return "-".join(tokens)[:64] or "unkeyed"


def _map_parent_row(row: dict, repo: str, report: MigrationReport) -> dict:
    created = time.time()
    ts = str(row.get("timestamp") or "")
    if ts:
        try:
            created = time.mktime(time.strptime(ts[:19],
                                                "%Y-%m-%dT%H:%M:%S"))
        except ValueError:
            try:
                created = time.mktime(time.strptime(ts[:19],
                                                    "%Y-%m-%d %H:%M:%S"))
            except ValueError:
                report.notes.append(
                    f"parent#{row.get('id')}: unparseable timestamp "
                    f"{ts!r} -> migration time")
    status = _PARENT_STATUS_MAP.get(str(row.get("status") or "active"))
    if status is None:
        report.notes.append(f"parent#{row.get('id')}: unknown status "
                            f"{row.get('status')!r} -> stale")
        status = "stale"
    elif str(row.get("status")) == "inactive":
        report.notes.append(f"parent#{row.get('id')}: status inactive -> "
                            "stale (copilot has no inactive)")
    # the copilot write contract requires non-empty run_id/files — parent
    # rows may lack both; truthful placeholders preserve the knowledge
    # without faking provenance (the verification string already names
    # the real origin)
    files = [f for f in str(row.get("files") or "").split(",") if f]
    if not files:
        files = ["(parent store recorded no files)"]
    return dict(
        repo=repo, module=str(row.get("module") or ""),
        run_id=str(row.get("run_id") or "parent-store"),
        symptom=str(row.get("symptom") or ""),
        root_cause=str(row.get("root_cause") or ""),
        fix_summary=str(row.get("fix") or ""),
        files=files,
        verification=(f"migrated from parent store: status="
                      f"{row.get('status') or 'active'}, run_count="
                      f"{row.get('run_count') or 1}, run="
                      f"{row.get('run_id') or '?'}"),
        status=status, created_at=created,
        key=str(row.get("key") or "") or _synthesize_key(
            str(row.get("symptom") or "")),
        tags=str(row.get("tags") or ""),
        watch_outs=str(row.get("watch_outs") or ""),
        upstream_commit=str(row.get("vllm_commit") or ""),
        last_seen_run=str(row.get("last_seen_run") or ""),
        run_count=int(row.get("run_count") or 1),
    )


def _map_legacy_row(row: dict, report: MigrationReport) -> dict:
    files = row.get("files")
    if isinstance(files, str):
        try:
            files = json.loads(files)
        except ValueError:
            files = [files]
    out = {k: row.get(k) for k in (
        "repo", "module", "run_id", "symptom", "root_cause", "fix_summary",
        "verification", "status", "created_at") if row.get(k) is not None}
    for k in ADDITIVE_COLUMNS:
        if row.get(k) not in (None, ""):
            out[k] = row[k]
    out["files"] = files or []
    if not out.get("key"):
        out["key"] = _synthesize_key(str(row.get("symptom") or ""))
    return out


def _fill_required(mapped: dict, origin: str) -> dict:
    """The copilot write contract rejects empty required fields, but
    legacy/parent rows may legitimately lack any of them — preserve the
    knowledge with TRUTHFUL placeholders naming the gap (never fabricated
    content; the `source` column carries the real provenance)."""
    for field_name in ("symptom", "root_cause", "fix_summary"):
        if not mapped.get(field_name):
            mapped[field_name] = f"(not recorded in {origin})"
    if not mapped.get("files"):
        mapped["files"] = [f"(no files recorded in {origin})"]
    if not mapped.get("run_id"):
        mapped["run_id"] = origin
    if not mapped.get("verification"):
        mapped["verification"] = f"migrated from {origin}"
    if not mapped.get("module"):
        mapped["module"] = "(unassigned)"
    return mapped


class MigrationError(RuntimeError):
    pass


def migrate_knowledge(settings, repo: str, *, dry_run: bool = False,
                      now: float | None = None) -> MigrationReport:
    """The whole PR4d data migration for `repo`. Raises `MigrationError`
    on any refused precondition; returns the report (also written to the
    state dir — report-only under `--dry-run`)."""
    from ..adapters.base import AdapterRegistry, expand_path
    from .runctx import CheckoutLock

    report = MigrationReport()
    adapter = AdapterRegistry(settings.adapters_dir).resolve(
        name=repo.replace("-", "_"))
    if adapter is None:
        raise MigrationError(f"no adapter for repo {repo!r}")
    kp = KnowledgePaths.resolve(settings, repo, adapter_root=adapter.root)
    # NOTE deliberately resolved with the flag OFF semantics for targets:
    # migration RUNS before activation. The target state db is the
    # state-dir path regardless of the flag.
    state_db = kp.state_dir / "debug_memory.db"
    manifest = adapter.manifest
    kn_cfg = (manifest.get("rebase") or {}).get("knowledge") or {}
    lock_name = str((manifest.get("rebase") or {}).get("lock_name") or "")
    repo_path = expand_path(str((manifest.get("repo") or {})
                                .get("path") or ""))

    # ── locks: checkout flock + state lock + knowledge EXCLUSIVE ────────
    locks: list = []
    try:
        if repo_path and lock_name and Path(repo_path).is_dir():
            checkout = CheckoutLock(Path(repo_path), lock_name)
            if checkout.acquire(blocking=False) is False:
                raise MigrationError(
                    "checkout flock is HELD — a rebase run (v3/v1/"
                    "external) is active")
            locks.append(checkout)
        know = KnowledgeRunLock(kp.knowledge_run_lock)
        know.acquire_exclusive()  # raises KnowledgeLockHeld when runs live
        locks.append(know)
        state_lock = KnowledgeRunLock(kp.state_lock)
        state_lock.acquire_exclusive()
        locks.append(state_lock)
        return _migrate_locked(settings, repo, adapter, kp, state_db,
                               kn_cfg, report, dry_run=dry_run)
    finally:
        for lock in reversed(locks):
            lock.release()


def _migrate_locked(settings, repo, adapter, kp: KnowledgePaths,
                    state_db: Path, kn_cfg: dict,
                    report: MigrationReport, *, dry_run: bool
                    ) -> MigrationReport:
    from ..adapters.base import expand_path
    from ..memory.skills import SkillStore

    ts = time.strftime("%Y%m%d-%H%M%S")
    journal_path = kp.state_dir / ".migration-journal.json"
    # crash-redo contract (round-3 F6): a PRIOR journal's planned seed
    # adds are enforced BY DIGEST before anything else — a file that
    # appeared at a planned path since the crash is either our own
    # partial work (exact match ⇒ fine) or someone else's (fail closed);
    # re-planning would silently misread it as a benign collision.
    prior_planned: dict[str, str] = {}
    if journal_path.is_file():
        try:
            prior = json.loads(journal_path.read_text(encoding="utf-8"))
            prior_planned = {p["relpath"]: p["sha256"]
                             for p in prior.get("planned_seed_adds", [])}
        except (ValueError, KeyError, TypeError):
            report.notes.append("prior migration journal unreadable — "
                                "treated as absent")
    for relpath, expected in prior_planned.items():
        dest = adapter.root / "skills" / relpath
        if dest.exists():
            have = hashlib.sha256(dest.read_bytes()).hexdigest()
            if have != expected:
                raise MigrationError(
                    f"planned seed add {relpath} exists with DIFFERENT "
                    "content than the journaled plan — refusing to adopt "
                    "or overwrite (round-3 F6); resolve by hand, then "
                    "delete the stale .migration-journal.json")

    # ── sources, realpath-deduped, digest-bound ─────────────────────────
    candidates: list[tuple[str, Path, str]] = []  # (tag, path, family)
    _extra = settings.expansion_env()
    parent_db = expand_path(str(kn_cfg.get("parent_debug_db") or ""),
                            extra=_extra)
    if parent_db and Path(parent_db).is_file():
        candidates.append(("parent-db", Path(parent_db), "parent"))
    legacy_global = Path(settings.memory_db)
    if legacy_global.is_file():
        candidates.append(("copilot-global", legacy_global, "legacy"))
    adapter_tree_db = adapter.root / "store" / "debug_memory.db"
    if adapter_tree_db.is_file():
        candidates.append(("adapter-tree", adapter_tree_db, "legacy"))
    seen_real: set[str] = set()
    sources = []
    for tag, path, family in candidates:
        real = str(Path(path).resolve())
        if real in seen_real:
            report.notes.append(f"{tag}: duplicate physical path {real} — "
                                "skipped")
            continue
        seen_real.add(real)
        sources.append((tag, Path(path), family,
                        ka.debug_db_digest(path)))

    parent_skills = expand_path(str(kn_cfg.get("parent_skills_dir") or ""),
                                extra=settings.expansion_env())
    planned_skills: list[dict] = []
    if parent_skills and Path(parent_skills).is_dir():
        existing = {p.parent.name for p in
                    (adapter.root / "skills").glob("*/SKILL.md")}
        for skill_md in sorted(Path(parent_skills).glob("*/SKILL.md")):
            name = skill_md.parent.name
            if name in existing and f"{name}/SKILL.md" not in prior_planned:
                report.skills_collisions.append(name)
                continue
            planned_skills.append({
                "name": name,
                "relpath": f"{name}/SKILL.md",
                "sha256": hashlib.sha256(
                    skill_md.read_bytes()).hexdigest(),
                "source": str(skill_md)})

    for tag, path, family, digest in sources:
        rows = _parent_rows(path) if family == "parent" \
            else _legacy_rows(path, repo)
        report.sources[tag] = {"path": str(path), "digest": digest,
                               "rows": len(rows)}

    if dry_run:
        _plan_ingest(settings, repo, kp, state_db, sources, report,
                     apply_to=None)
        report.notes.append("DRY RUN — nothing written but this report")
        _durable_write(kp.state_dir / "MIGRATION_REPORT.md",
                       report.render())
        return report

    # ── journal FIRST (crash-redo contract) ─────────────────────────────
    _durable_write(journal_path, json.dumps({
        "ts": ts,
        "sources": {t: {"path": str(p), "digest": d}
                    for t, p, _f, d in sources},
        "target": str(state_db),
        "planned_seed_adds": planned_skills}, indent=1))
    # marker-last also means marker-INVALID-first on a rerun: a previous
    # MIGRATION_COMPLETE must not let activated runtimes start against a
    # partially re-migrated world if this pass crashes mid-mutation
    # (hook iteration-3 finding); it is recreated as the final act
    (kp.state_dir / KnowledgePaths.MIGRATION_MARKER).unlink(
        missing_ok=True)

    # ── target debug DB: backup, rebuild at tmp, atomic replace ─────────
    kp.backups_dir.mkdir(parents=True, exist_ok=True)
    if state_db.is_file():
        ka.snapshot_debug_db(state_db,
                             kp.backups_dir / f"{ts}-debug_memory.db")
    tmp_db = state_db.with_name(state_db.name + ".migrate-tmp")
    if tmp_db.exists():
        tmp_db.unlink()
    if state_db.is_file():
        # ids preserved: the tmp starts as a consistent COPY of the target
        ka.snapshot_debug_db(state_db, tmp_db)
    target = DebugMemory(tmp_db)
    target.ensure_schema_v2()
    _plan_ingest(settings, repo, kp, state_db, sources, report,
                 apply_to=target)
    _dedup_pass(target, repo, report)
    target._conn.commit()
    target._conn.close()
    # install via the hardened restore path (stages + integrity-checks
    # the built DB, CHECKPOINTS the old target before touching its
    # sidecars, rolls preserved sidecars back on a failed replace) — a
    # crash anywhere in the swap leaves the old target fully readable
    # and the journal drives a clean redo
    ka.restore_debug_db(tmp_db, state_db)
    tmp_db.unlink(missing_ok=True)

    # ── seed skills: per-file tmp+rename, digest-journaled ──────────────
    seed_dir = adapter.root / "skills"
    for planned in planned_skills:
        dest = seed_dir / planned["relpath"]
        if dest.exists():
            have = hashlib.sha256(dest.read_bytes()).hexdigest()
            if have == planned["sha256"]:
                continue  # redo after crash: already installed, verified
            raise MigrationError(
                f"planned seed add {planned['relpath']} exists with "
                "DIFFERENT content — refusing to overwrite (round-3 F6)")
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = Path(planned["source"]).read_bytes()
        tmp = dest.with_name(dest.name + ".tmp")
        tmp.write_bytes(data)
        os.replace(tmp, dest)
        report.skills_added.append(planned["name"])

    # ── parent candidates → runtime candidates (merge) ──────────────────
    if parent_skills:
        parent_cands = Path(parent_skills) / "_candidates.json"
        if parent_cands.is_file():
            runtime_store = SkillStore(kp.skills_runtime_dir)
            try:
                incoming = json.loads(
                    parent_cands.read_text(encoding="utf-8"))
            except ValueError:
                incoming = {}
                report.notes.append("parent _candidates.json unreadable — "
                                    "skipped")
            existing_c = runtime_store.candidates()
            for name, cand in incoming.items():
                if name not in existing_c and isinstance(cand, dict):
                    runtime_store.propose(
                        name=name,
                        description=str(cand.get("description", "")
                                        or cand.get("trigger", "")),
                        body=str(cand.get("body", "") or ""),
                        modules=list(cand.get("modules") or []))
                    report.candidates_merged += 1

    # ── report + marker (LAST act) ──────────────────────────────────────
    _durable_write(kp.state_dir / "MIGRATION_REPORT.md", report.render())
    _durable_write(kp.state_dir / KnowledgePaths.MIGRATION_MARKER,
                   json.dumps({
                       "schema": "v2", "ts": ts, "repo": repo,
                       "digests": {
                           "target_db": ka.debug_db_digest(state_db),
                           **{t: m["digest"]
                              for t, m in report.sources.items()}},
                   }, indent=1))
    journal_path.unlink(missing_ok=True)
    return report


def _plan_ingest(settings, repo, kp, state_db, sources, report,
                 *, apply_to: DebugMemory | None) -> None:
    """Ingest source rows (or, with `apply_to=None`, only count what WOULD
    ingest — the dry-run path). Skip rule per row (round-3 F4): same
    source key + same row digest ⇒ skip; same `<tag>#<rowid>` prefix with
    a DIFFERENT digest ⇒ ingest the new version and retire the old target
    row with lineage."""
    existing: dict[str, tuple[int, str]] = {}
    probe = apply_to
    if probe is None and state_db.is_file():
        probe = DebugMemory.open_readonly(state_db)
    if probe is not None and "source" in probe._columns:
        for row in probe._conn.execute(
                "SELECT id, source FROM entries WHERE source != ''"):
            src = str(row["source"])
            prefix = src.split("@", 1)[0]
            existing[prefix] = (int(row["id"]), src)
    for tag, path, family, digest in sources:
        rows = _parent_rows(path) if family == "parent" \
            else _legacy_rows(path, repo)
        for raw in rows:
            prefix = f"{tag}#{raw.get('id')}"
            row_digest = _row_digest(raw)
            source_key = f"{prefix}@{row_digest}"
            if prefix in existing:
                old_id, old_key = existing[prefix]
                if old_key == source_key:
                    report.skipped_unchanged += 1
                    continue
                # changed source row: version-and-retire
                report.reversioned += 1
                if apply_to is not None:
                    mapped = _fill_required(
                        _map_parent_row(raw, repo, report)
                        if family == "parent"
                        else _map_legacy_row(raw, report), tag)
                    mapped["source"] = source_key
                    new_id = apply_to.record(**mapped)
                    apply_to.apply_curation(
                        {old_id: {"status": "retired",
                                  "derived_from": str(new_id)}})
                continue
            report.ingested += 1
            if apply_to is not None:
                mapped = _fill_required(
                    _map_parent_row(raw, repo, report)
                    if family == "parent"
                    else _map_legacy_row(raw, report), tag)
                mapped["source"] = source_key
                apply_to.record(**mapped)


def _dedup_pass(target: DebugMemory, repo: str,
                report: MigrationReport) -> None:
    """Exact (module,key) first, then the curator's clustering at
    Jaccard ≥ 0.8 over a TOTAL ORDER (source precedence, then id) —
    merged-away rows retire with lineage, never delete."""
    from ..memory.curator import DebugMemoryCurator

    precedence = {"": 0, "v3-agent": 0, "copilot-global": 1,
                  "adapter-tree": 2, "parent-db": 3}

    def rank(row: dict) -> tuple:
        tag = str(row.get("source") or "").split("#", 1)[0]
        return (precedence.get(tag, 4), -int(row["id"]))

    updates: dict[int, dict] = {}
    by_key: dict[tuple, list[dict]] = {}
    for row in target.entries(repo=repo):
        by_key.setdefault((row.get("module"), row.get("key")),
                          []).append(row)
    for (_, _), rows in sorted(by_key.items(),
                               key=lambda kv: str(kv[0])):
        if len(rows) < 2:
            continue
        rows.sort(key=rank)
        survivor, rest = rows[0], rows[1:]
        run_count = int(survivor.get("run_count") or 1)
        for r in rest:
            run_count += int(r.get("run_count") or 1)
            updates[r["id"]] = {"status": "retired",
                                "derived_from": str(survivor["id"])}
            report.retired_by_dedup += 1
        updates[survivor["id"]] = {"run_count": run_count}
    target.apply_curation(updates)
    # near-dup consolidation rides the shared curator (same thresholds)
    curator = DebugMemoryCurator(target, repo=repo, sim_threshold=0.8)
    merge_report = curator.curate()
    report.retired_by_dedup += merge_report.merged
