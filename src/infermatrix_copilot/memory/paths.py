"""KnowledgePaths — the ONE resolver for every mutable-knowledge location.

Until the PR4d cutover activates, every member resolves to exactly the
location its consumer used before this module existed (byte-identity is
pinned by test) — the resolver is a pure refactor that gives the runtime-dir
cutover a single switch to act on later, instead of five scattered
path expressions. The per-repo runtime state home is
`<memory_db dir>/state/<repo>/` (the location `skills_runtime` already
used); the flag-on branch that redirects the LEGACY locations there lands
with the migration machinery (PR4d code), not here.

Debug-memory members deliberately mirror the historical PER-CONSUMER wiring
(they differ today and must keep differing until cutover):
`rebase_backend_db` (v3 agent tools), `shared_write_db`
(`_common.record_debug_memory`), `debug_read_layers`
(`agent_runtime` retrieval, adapter store first).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:  # POSIX-only, same guard as run_status.py / watchdog_learn.py
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None  # type: ignore


@dataclass(frozen=True)
class KnowledgePaths:
    """Resolved knowledge locations for one repo. Build via `resolve()`."""

    repo: str
    state_dir: Path            # per-repo runtime state home
    rebase_backend_db: Path    # v3 agent-tool debug memory
    shared_write_db: Path      # shared record_debug_memory target
    debug_read_layers: tuple   # retrieval order (first = highest priority)
    skills_seed_dir: Path      # adapter-tree seed skills (read-only at run time)
    skills_runtime_dir: Path   # runtime candidates/promoted skills
    skills_usage_journal: Path # append-only seed-skill usage journal
    repo_map_cache_dir: Path | None  # adapter repo_map cache (None: no adapter)
    watchdog_overlay: Path     # learned noise-pattern overlay YAML
    watchdog_decisions: Path   # harvested Tier-2 decision log (curator-owned)
    watchdog_harvest_checkpoint: Path
    backups_dir: Path          # versioned non-destructive knowledge backups
    state_lock: Path           # flock wrapping state-dir writes
    knowledge_run_lock: Path   # LOCK_SH per run / LOCK_EX for migration

    @classmethod
    def resolve(cls, settings, repo: str,
                adapter_root: Path | None = None) -> "KnowledgePaths":
        """Resolve for `repo`. `adapter_root` is the repo adapter's directory
        when one is registered (callers already resolve the adapter; passing
        None reproduces every no-adapter fallback exactly)."""
        memory_db = Path(settings.memory_db)
        state = memory_db.parent / "state" / repo
        adapter_db = (adapter_root / "store" / "debug_memory.db"
                      if adapter_root is not None else None)
        if adapter_root is not None:
            seed_skills = adapter_root / "skills"
            read_layers: tuple = (adapter_db, memory_db)
            repo_map_cache = adapter_root / "repo_map"
        else:
            seed_skills = Path(settings.skills_dir)
            read_layers = (memory_db,)
            repo_map_cache = None
        return cls(
            repo=repo,
            state_dir=state,
            rebase_backend_db=memory_db,
            shared_write_db=adapter_db if adapter_db is not None else memory_db,
            debug_read_layers=read_layers,
            skills_seed_dir=seed_skills,
            skills_runtime_dir=state / "skills_runtime",
            skills_usage_journal=state / "skills_usage.jsonl",
            repo_map_cache_dir=repo_map_cache,
            watchdog_overlay=state / "watchdog_overlay.yaml",
            watchdog_decisions=state / "watchdog_decisions.jsonl",
            watchdog_harvest_checkpoint=state / "watchdog_harvested.json",
            backups_dir=state / "backups",
            state_lock=state / "locks" / "state.lock",
            knowledge_run_lock=state / "locks" / "knowledge.lock",
        )


class KnowledgeLockHeld(RuntimeError):
    """The per-repo knowledge lock is exclusively held (a knowledge
    migration is in progress) — runs must not start mid-migration."""


class KnowledgeRunLock:
    """Shared/exclusive flock on `state/<repo>/locks/knowledge.lock`.

    Every copilot RUN for a repo holds it SHARED for its whole lifetime;
    the knowledge-migration tool takes it EXCLUSIVE. Shared holders never
    contend with each other, so runs are unaffected day-to-day — but a
    migration cannot start while any potential store writer is alive, and
    no run can start mid-migration (the lock-census TOCTOU the design
    review closed). POSIX-only; on platforms without flock both sides
    degrade together to no enforcement."""

    def __init__(self, lock_path: Path):
        self.lock_path = Path(lock_path)
        self._fd: int | None = None

    def _open(self) -> int:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        return os.open(self.lock_path, os.O_RDWR | os.O_CREAT, 0o644)

    def _acquire(self, mode: int) -> "KnowledgeRunLock":
        if fcntl is None:  # pragma: no cover - Windows
            return self
        fd = self._open()
        try:
            fcntl.flock(fd, mode | fcntl.LOCK_NB)
        except OSError:
            os.close(fd)
            if mode == fcntl.LOCK_SH:
                raise KnowledgeLockHeld(
                    f"knowledge lock {self.lock_path} refused (shared "
                    "acquire): held exclusively — a knowledge migration is "
                    "in progress; retry after it completes")
            raise KnowledgeLockHeld(
                f"knowledge lock {self.lock_path} refused (exclusive "
                "acquire): a run for this repo is active")
        self._fd = fd
        return self

    def acquire_shared(self) -> "KnowledgeRunLock":
        """Run-side: non-blocking shared acquire (fails only against a
        migration's exclusive hold)."""
        return self._acquire(fcntl.LOCK_SH if fcntl else 0)

    def acquire_exclusive(self) -> "KnowledgeRunLock":
        """Migration-side: non-blocking exclusive acquire (fails while any
        run holds shared)."""
        return self._acquire(fcntl.LOCK_EX if fcntl else 0)

    def release(self) -> None:
        if self._fd is not None:
            if fcntl is not None:
                fcntl.flock(self._fd, fcntl.LOCK_UN)
            os.close(self._fd)
            self._fd = None
