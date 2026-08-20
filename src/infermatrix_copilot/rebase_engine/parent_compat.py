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


def _fts5_unindexed_columns(create_sql: str) -> set[str]:
    """Column names declared UNINDEXED in an FTS5 CREATE VIRTUAL TABLE
    statement, parsed from the argument list itself (comments stripped,
    args split at top-level commas) — a substring scan is formatting-
    dependent and misses `col   UNINDEXED` or comment-separated forms.
    Non-FTS5 SQL yields the empty set (the FTS5-ness check is separate)."""
    s = re.sub(r"/\*.*?\*/", " ", create_sql, flags=re.S)
    s = re.sub(r"--[^\n]*", " ", s)
    m = re.search(r"using\s+fts5\s*\(", s, flags=re.I)
    if not m:
        return set()
    args, depth, start, i = [], 1, m.end(), m.end()
    while i < len(s) and depth:
        ch = s[i]
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
            if depth == 0:
                break
        elif ch == "," and depth == 1:
            args.append(s[start:i])
            start = i + 1
        i += 1
    args.append(s[start:i])
    out: set[str] = set()
    for arg in args:
        arg = arg.strip()
        if not arg or "=" in arg:
            continue  # an option (content=, tokenize=…), not a column
        toks = re.findall(
            r"'[^']*'|\"[^\"]*\"|`[^`]*`|\[[^\]]*\]|[A-Za-z_][A-Za-z0-9_]*",
            arg)
        if not toks:
            continue
        name = toks[0].strip("'\"`[]").casefold()
        if any(tk.lower() == "unindexed" for tk in toks[1:]):
            out.add(name)
    return out


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
            # the index must BE fts5 with every required column INDEXED —
            # column names alone can hide fts4 tables or UNINDEXED
            # declarations whose searches silently miss (round-3 F4)
            fts_sql = (self._conn.execute(
                "SELECT sql FROM sqlite_master WHERE name = "
                "'debug_entries_fts'").fetchone() or ("",))[0] or ""
            if not re.search(r"using\s+fts5\s*\(", fts_sql,
                             flags=re.I):
                raise sqlite3.DatabaseError(
                    "debug_entries_fts is not an FTS5 table")
            bad = _fts5_unindexed_columns(fts_sql) & {
                "module", "key", "tags", "symptom", "root_cause",
                "fix", "watch_outs"}
            if bad:
                raise sqlite3.DatabaseError(
                    f"FTS columns {sorted(bad)} are UNINDEXED — "
                    "searches would silently miss them")
            # the exact search() join + every mapped column, incl. the
            # adapter-declared upstream column when present
            self._conn.execute(
                "SELECT e.id, e.module, e.key, e.symptom, "
                "e.root_cause, e.fix, e.status "
                "FROM debug_entries_fts f "
                "JOIN debug_entries e ON e.id = f.rowid "
                "WHERE debug_entries_fts MATCH '\"probe\"' LIMIT 1"
            ).fetchone()
            # every INDEXED column search relies on must exist in the FTS
            # table itself — a symptom-only index would answer the join
            # probe yet silently miss key/tag/root-cause/fix/watch-out
            # terms (PR-boundary round-2 F4); a column-filtered MATCH
            # errors on a missing column
            for col in ("module", "key", "tags", "symptom", "root_cause",
                        "fix", "watch_outs"):
                self._conn.execute(
                    "SELECT rowid FROM debug_entries_fts WHERE "
                    f"debug_entries_fts MATCH '{col}: \"probe\"' LIMIT 1"
                ).fetchone()
            self._conn.execute("SELECT count(*) FROM debug_entries"
                               ).fetchone()
            if upstream_column:
                # EXACT declared-column membership (round-3): a bare
                # SELECT accepts case variants of the name and
                # rowid/oid/NULL-ish identifiers, but `get()`'s dict
                # lookup is exact — every upstream commit would
                # silently map to ""
                cols = {r[1] for r in self._conn.execute(
                    "PRAGMA table_xinfo(debug_entries)")}
                if upstream_column not in cols:
                    raise sqlite3.DatabaseError(
                        f"declared upstream column {upstream_column!r} "
                        "is not an exact column of debug_entries "
                        f"({sorted(cols)[:8]})")
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
