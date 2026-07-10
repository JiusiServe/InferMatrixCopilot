"""DebugMemory — failure/fix experience, SQLite + FTS5 (design task 3).

Write contract: entries missing the required fields are rejected with an
instructive error. Retrieval returns top-k SUMMARIES; the full entry is an
explicit second call (context noise control).
"""

from __future__ import annotations

import json
import re
import sqlite3
import time
from pathlib import Path

REQUIRED_FIELDS = (
    "repo", "module", "run_id", "symptom", "root_cause",
    "fix_summary", "files", "verification",
)
STATUSES = ("candidate", "active", "stale", "retired")


class DebugMemory:
    """SQLite-backed store of failure/fix experiences with an FTS5 mirror for
    retrieval. Every entry must carry the full `REQUIRED_FIELDS` set (a fix with
    no verification or root cause is not reusable), and search returns summaries
    only — the full entry is a deliberate second `get` call to keep context lean."""

    def __init__(self, db_path: str | Path):
        """Open (creating parent dirs and the schema if absent) the SQLite db at
        `db_path`. Rows are returned as `sqlite3.Row` so callers get dict access."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        """Create the `entries` table and its `entries_fts` FTS5 mirror if they
        do not yet exist. The mirror is `content='entries'` external-content so
        the searchable columns stay in sync with the base row on insert."""
        c = self._conn
        c.execute(
            """CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo TEXT, module TEXT, run_id TEXT,
                symptom TEXT, root_cause TEXT, fix_summary TEXT,
                files TEXT, verification TEXT,
                status TEXT DEFAULT 'active',
                created_at REAL)"""
        )
        c.execute(
            """CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
                symptom, root_cause, fix_summary, module, repo,
                content='entries', content_rowid='id')"""
        )
        c.commit()

    def record(self, **fields) -> int:
        """Insert one failure/fix entry and return its new row id. Rejects (with
        an instructive `ValueError`) any call missing a `REQUIRED_FIELDS` value or
        naming a `status` outside `STATUSES` — the write contract that keeps the
        store reusable. `files` is normalized to a JSON list; the searchable text
        columns are mirrored into `entries_fts`."""
        missing = [f for f in REQUIRED_FIELDS if not fields.get(f)]
        if missing:
            raise ValueError(
                f"debug memory rejected — missing required fields: {missing}. "
                f"Required: {list(REQUIRED_FIELDS)}"
            )
        status = fields.get("status", "active")
        if status not in STATUSES:
            raise ValueError(f"bad status {status!r}; one of {STATUSES}")
        files = fields["files"]
        files_json = json.dumps(files if isinstance(files, list) else [str(files)])
        cur = self._conn.execute(
            """INSERT INTO entries
               (repo, module, run_id, symptom, root_cause, fix_summary, files,
                verification, status, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (fields["repo"], fields["module"], fields["run_id"], fields["symptom"],
             fields["root_cause"], fields["fix_summary"], files_json,
             fields["verification"], status, time.time()),
        )
        rowid = cur.lastrowid
        self._conn.execute(
            """INSERT INTO entries_fts (rowid, symptom, root_cause, fix_summary,
                                        module, repo)
               VALUES (?,?,?,?,?,?)""",
            (rowid, fields["symptom"], fields["root_cause"], fields["fix_summary"],
             fields["module"], fields["repo"]),
        )
        self._conn.commit()
        return int(rowid)

    def search(self, query: str, k: int = 5, repo: str | None = None) -> list[dict]:
        """Top-k summaries (id, module, symptom, fix_summary) — never full entries."""
        tokens = re.findall(r"[A-Za-z0-9_]+", query)
        if not tokens:
            return []
        match = " OR ".join(f'"{t}"' for t in tokens)
        rows = self._conn.execute(
            """SELECT e.id, e.repo, e.module, e.symptom, e.fix_summary
               FROM entries_fts f JOIN entries e ON e.id = f.rowid
               WHERE entries_fts MATCH ? AND e.status IN ('active','candidate')
               ORDER BY rank LIMIT ?""",
            (match, k * 3),
        ).fetchall()
        out = [dict(r) for r in rows if repo is None or r["repo"] == repo]
        return out[:k]

    def get(self, entry_id: int) -> dict | None:
        """Return the full entry for `entry_id` as a dict (with `files` decoded
        back to a list), or None if no such row — the explicit second call that
        `search` summaries lead to."""
        row = self._conn.execute("SELECT * FROM entries WHERE id=?", (entry_id,)).fetchone()
        if row is None:
            return None
        d = dict(row)
        d["files"] = json.loads(d["files"])
        return d

    def count(self) -> int:
        """Total number of stored entries, regardless of status."""
        return self._conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
