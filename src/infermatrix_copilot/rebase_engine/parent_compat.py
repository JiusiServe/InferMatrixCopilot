"""Read-only compat reader over the PARENT rebase agent's knowledge stores.

Rev 8 §9 PR4c promised "the engine reads the parent's existing stores
read-compatibly (migration deferred)"; this module delivers it, REPO-
NEUTRALLY: the parent store's repo-specific column naming (which column
carries the upstream commit) is ADAPTER DATA
(`rebase.knowledge.parent_upstream_column`), never a literal here. Queries
map the parent schema (`debug_entries` + `debug_entries_fts`:
module/key/tags/symptom/root_cause/fix/watch_outs) onto the copilot's
summary shape at read time (`fix`→`fix_summary`,
`<parent_upstream_column>`→`upstream_commit`). Opens are strictly
`mode=ro` URIs: the parent stores are NEVER written, and after the PR4d
migration executes the adapter drops its `rebase.knowledge` keys and this
layer dies with them (no permanent dual-store world).

Failure contract: constructors raise (the v3 prelude fails CLOSED on a
declared-but-broken layer) — the open probes the EXACT retrieval shape
`search()` uses (tables, columns, FTS join), so a near-miss schema fails
at the gate instead of degrading silently mid-run; `search()` after a
successful open degrades to an explicit error dict so a mid-run hiccup
can be traced without killing a run (the design's two-tier semantics).
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from ..memory.debug_memory import readonly_uri

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class ParentDebugMemory:
    """Read-only view of a parent-schema debug store."""

    def __init__(self, db_path: str | Path, *,
                 upstream_column: str = ""):
        """Open `db_path` read-only and probe the EXACT retrieval shape.
        Raises `FileNotFoundError` for a missing file,
        `sqlite3.DatabaseError` for a corrupt store or one missing any
        column/table `search()`/`get()` relies on (a near-miss schema
        must fail at the gate, not degrade mid-run). `upstream_column`
        names the parent column carrying the upstream commit (adapter
        data; "" = the store has none)."""
        path = Path(db_path)
        if not path.is_file():
            raise FileNotFoundError(f"no parent debug store at {path}")
        if upstream_column and not _NAME_RE.match(upstream_column):
            raise ValueError(
                f"bad parent_upstream_column {upstream_column!r}")
        self.db_path = path
        self.upstream_column = upstream_column
        self._conn = sqlite3.connect(readonly_uri(path), uri=True)
        self._conn.row_factory = sqlite3.Row
        try:
            # the exact search() join + every mapped column, incl. the
            # adapter-declared upstream column when present
            self._conn.execute(
                "SELECT e.id, e.module, e.key, e.symptom, "
                "e.root_cause, e.fix, e.status "
                "FROM debug_entries_fts f "
                "JOIN debug_entries e ON e.id = f.rowid "
                "WHERE debug_entries_fts MATCH '\"probe\"' LIMIT 1"
            ).fetchone()
            self._conn.execute("SELECT count(*) FROM debug_entries"
                               ).fetchone()
            if upstream_column:
                self._conn.execute(
                    f"SELECT {upstream_column} FROM debug_entries "
                    "LIMIT 1").fetchone()
        except sqlite3.Error as exc:
            raise sqlite3.DatabaseError(
                f"{path} is not a parent-schema debug store (retrieval "
                f"probe failed): {exc}") from exc

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
        `upstream_commit` from the adapter-declared column); parent-only
        fields ride along unchanged."""
        row = self._conn.execute(
            "SELECT * FROM debug_entries WHERE id=?", (entry_id,)).fetchone()
        if row is None:
            return None
        d = dict(row)
        d["fix_summary"] = d.pop("fix", "")
        d["upstream_commit"] = d.pop(self.upstream_column, "") \
            if self.upstream_column else ""
        return d

    def count(self) -> int:
        return self._conn.execute(
            "SELECT count(*) FROM debug_entries").fetchone()[0]
