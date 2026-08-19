"""Read-only compat reader over the PARENT rebase agent's knowledge stores.

Rev 8 §9 PR4c promised "the engine reads the parent's existing stores
read-compatibly (migration deferred)"; this module delivers it. The parent's
debug store is a different SQLite schema (`debug_entries` +
`debug_entries_fts`: module/key/tags/symptom/root_cause/fix/watch_outs,
`vllm_commit`, run_count) — queries map it onto the copilot's summary shape
at read time (`fix`→`fix_summary`, `vllm_commit`→`upstream_commit`). Opens
are strictly `mode=ro` URIs: the parent stores are NEVER written, and after
the PR4d migration executes the adapter drops its `rebase.knowledge` keys
and this layer dies with them (no permanent dual-store world).

Failure contract: constructors raise (the v3 prelude fails CLOSED on a
declared-but-broken layer); `search()` after a successful open degrades to
an explicit error dict so a mid-run hiccup can be traced without killing a
run (the design's two-tier semantics).
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from ..memory.debug_memory import readonly_uri

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


class ParentDebugMemory:
    """Read-only view of a parent-schema debug store."""

    def __init__(self, db_path: str | Path):
        """Open `db_path` read-only and probe it. Raises `FileNotFoundError`
        for a missing file, `sqlite3.DatabaseError` for a corrupt one or a
        file that is not a parent-schema store."""
        path = Path(db_path)
        if not path.is_file():
            raise FileNotFoundError(f"no parent debug store at {path}")
        self.db_path = path
        self._conn = sqlite3.connect(readonly_uri(path), uri=True)
        self._conn.row_factory = sqlite3.Row
        try:
            self._conn.execute("SELECT count(*) FROM debug_entries").fetchone()
        except sqlite3.Error as exc:
            raise sqlite3.DatabaseError(
                f"{path} is not a parent-schema debug store: {exc}") from exc

    def search(self, query: str, k: int = 5) -> list[dict]:
        """Top-k summaries in the copilot's summary shape (`fix_summary`
        carries the parent's `fix`). Only active-status rows, like the
        copilot store's own search."""
        tokens = _TOKEN_RE.findall(query)
        if not tokens:
            return []
        match = " OR ".join(f'"{t}"' for t in tokens)
        rows = self._conn.execute(
            """SELECT e.id, e.module, e.key, e.symptom, e.fix AS fix_summary
               FROM debug_entries_fts f JOIN debug_entries e ON e.id = f.rowid
               WHERE debug_entries_fts MATCH ? AND e.status = 'active'
               ORDER BY rank LIMIT ?""",
            (match, k),
        ).fetchall()
        return [dict(r) for r in rows]

    def get(self, entry_id: int) -> dict | None:
        """Full parent row mapped to copilot field names (`fix_summary`,
        `upstream_commit`); parent-only fields ride along unchanged."""
        row = self._conn.execute(
            "SELECT * FROM debug_entries WHERE id=?", (entry_id,)).fetchone()
        if row is None:
            return None
        d = dict(row)
        d["fix_summary"] = d.pop("fix", "")
        d["upstream_commit"] = d.pop("vllm_commit", "")
        return d

    def count(self) -> int:
        return self._conn.execute(
            "SELECT count(*) FROM debug_entries").fetchone()[0]
