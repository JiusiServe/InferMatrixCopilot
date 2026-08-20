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
from urllib.parse import quote


def readonly_uri(path: str | Path) -> str:
    """`file:` URI opening `path` read-only, with the path percent-escaped so
    filenames containing `?`, `#`, or `%` cannot be misparsed into URI
    machinery (and silently open the wrong database)."""
    return f"file:{quote(str(path), safe='/')}?mode=ro"

REQUIRED_FIELDS = (
    "repo", "module", "run_id", "symptom", "root_cause",
    "fix_summary", "files", "verification",
)
STATUSES = ("candidate", "active", "stale", "retired")

# Schema v2 (Rev 8 §5 additive columns + curation provenance). New DBs are
# created with them; an EXISTING DB is upgraded ONLY through the explicit
# `ensure_schema_v2()` maintenance routine — never as a side effect of
# opening the store (report-only paths must be able to prove no-write).
ADDITIVE_COLUMNS: dict[str, str] = {
    "key": "TEXT DEFAULT ''",
    "tags": "TEXT DEFAULT ''",
    "watch_outs": "TEXT DEFAULT ''",
    "upstream_commit": "TEXT DEFAULT ''",
    "last_seen_run": "TEXT DEFAULT ''",
    "source": "TEXT DEFAULT ''",
    "run_count": "INTEGER DEFAULT 1",
    "derived_from": "TEXT DEFAULT ''",
}
_FTS_V2_EXTRA = ("key", "tags", "watch_outs")


def strip_sql_comments(sql: str) -> str:
    """`sql` with /* */ and -- comments blanked, QUOTE-AWARE. sqlite_master
    stores CREATE statements verbatim, so any check that regex-matches the
    DDL text must strip comments first — `/* USING fts5( */ USING
    fts4(...)` is valid SQL whose raw text passes a naive FTS5 test. And
    the stripper itself must honor quoting: a column named `"a /*"` must
    not open a comment, or the blanked span could swallow a real
    UNINDEXED declaration (round-4 F1)."""
    out, i, n = [], 0, len(sql)
    while i < n:
        ch = sql[i]
        if ch in "'\"`[":
            close = "]" if ch == "[" else ch
            j = i + 1
            while j < n:
                if sql[j] == close:
                    if close != "]" and j + 1 < n and sql[j + 1] == close:
                        j += 2  # doubled quote stays inside the literal
                        continue
                    break
                j += 1
            out.append(sql[i:min(j + 1, n)])
            i = j + 1
        elif sql.startswith("/*", i):
            j = sql.find("*/", i + 2)
            i = n if j == -1 else j + 2
            out.append(" ")
        elif sql.startswith("--", i):
            j = sql.find("\n", i)
            i = n if j == -1 else j
            out.append(" ")
        else:
            out.append(ch)
            i += 1
    return "".join(out)


_SQL_TOKEN_RE = re.compile(
    r"'(?:[^']|'')*'|\"(?:[^\"]|\"\")*\"|`(?:[^`]|``)*`|\[[^\]]*\]"
    r"|[A-Za-z_][A-Za-z0-9_]*|.", re.S)


def _fts5_arg_tokens(sql_no_comments: str) -> list[str] | None:
    """Tokens of the FTS5 argument list (everything after the table-
    level `USING fts5 (`), or None when the statement does not declare
    one. TOKENIZED, never scanned: quoted identifiers are single atomic
    tokens, so a column literally named `[USING fts5(]` in FTS4 DDL
    cannot stand in for the module clause, and a quoted `")"` cannot
    terminate the argument list early. The FIRST bare `USING` token is
    the table-level one — nothing precedes it but CREATE VIRTUAL TABLE
    and the (possibly quoted) table name."""
    toks = [m.group(0) for m in _SQL_TOKEN_RE.finditer(sql_no_comments)
            if not m.group(0).isspace()]
    for i, tok in enumerate(toks):
        if tok.lower() == "using":
            if (i + 2 < len(toks) and toks[i + 1].lower() == "fts5"
                    and toks[i + 2] == "("):
                return toks[i + 3:]
            return None
    return None


def is_fts5_table(create_sql: str) -> bool:
    """True when `create_sql` declares an FTS5 virtual table — comment-
    stripped and tokenized (see _fts5_arg_tokens): neither a comment nor
    a quoted identifier carrying `USING fts5(` can spoof it."""
    return _fts5_arg_tokens(strip_sql_comments(create_sql)) is not None


def fts5_unindexed_columns(create_sql: str) -> set[str]:
    """LOWERCASED names of columns declared UNINDEXED in an FTS5 CREATE
    VIRTUAL TABLE statement, parsed from the tokenized argument list —
    args split at top-level bare commas, nesting tracked on bare parens
    only, so quoted identifiers containing `)`/`,` can neither hide a
    later UNINDEXED declaration nor invent one. SQLite resolves FTS
    column names case-insensitively, hence lowercase. Non-FTS5 SQL
    yields the empty set (FTS5-ness is is_fts5_table's job)."""
    toks = _fts5_arg_tokens(strip_sql_comments(create_sql))
    if toks is None:
        return set()
    out: set[str] = set()

    def flush(arg: list[str]) -> None:
        if not arg or "=" in arg:
            return  # empty, or an option (content=, tokenize=…)
        name = arg[0].strip("'\"`[]").lower()
        # SQLite DEQUOTES option tokens too: `module "UNINDEXED"` (any
        # quote style) is a real UNINDEXED declaration (round-5 F1)
        if name and any(tk.strip("'\"`[]").lower() == "unindexed"
                        for tk in arg[1:]):
            out.add(name)

    depth, arg = 1, []
    for tok in toks:
        if tok == "(":
            depth += 1
            arg.append(tok)
        elif tok == ")":
            depth -= 1
            if depth == 0:
                break
            arg.append(tok)
        elif tok == "," and depth == 1:
            flush(arg)
            arg = []
        else:
            arg.append(tok)
    flush(arg)
    return out



class DebugMemory:
    """SQLite-backed store of failure/fix experiences with an FTS5 mirror for
    retrieval. Every entry must carry the full `REQUIRED_FIELDS` set (a fix with
    no verification or root cause is not reusable), and search returns summaries
    only — the full entry is a deliberate second `get` call to keep context lean."""

    def __init__(self, db_path: str | Path):
        """Open (creating parent dirs and the schema if absent) the SQLite db at
        `db_path`. Rows are returned as `sqlite3.Row` so callers get dict access.
        An EXISTING database is opened as-is — no DDL of any kind runs against
        it (schema upgrades are the explicit `ensure_schema_v2()` action)."""
        self.db_path = Path(db_path)
        self.readonly = False
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        if not self._table_exists("entries"):
            # an existing file that already holds OTHER tables is not a
            # debug store — refuse instead of installing our schema into it
            if self._conn.execute(
                    "SELECT 1 FROM sqlite_master LIMIT 1").fetchone():
                raise sqlite3.DatabaseError(
                    f"{self.db_path} is an existing database without an "
                    "'entries' table — not a debug memory store")
            self._create_schema()
        elif not self._table_exists("entries_fts"):
            # crash window repair: entries landed, mirror did not
            self._create_schema()
        self._introspect()

    @classmethod
    def open_readonly(cls, db_path: str | Path) -> "DebugMemory":
        """Open an EXISTING db strictly read-only (sqlite URI `mode=ro`,
        path percent-escaped): no mkdir, no DDL, no content writes. Copilot
        stores are rollback-journal databases, so the open leaves the file
        byte-identical (pinned by test); a WAL-mode store with live sidecars
        reads through them without creating anything new. Raises
        `FileNotFoundError` for a missing file and `sqlite3.DatabaseError`
        for a corrupt one (probed eagerly) — the fail-closed open the
        report-only prelude relies on."""
        path = Path(db_path)
        if not path.is_file():
            raise FileNotFoundError(f"no debug memory db at {path}")
        self = cls.__new__(cls)
        self.db_path = path
        self.readonly = True
        self._conn = sqlite3.connect(readonly_uri(path), uri=True)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("SELECT count(*) FROM entries").fetchone()
        self._introspect()
        return self

    def _table_exists(self, name: str) -> bool:
        """True when table `name` exists — the new-vs-existing DB probe that
        keeps `__init__` DDL-free for existing databases."""
        return self._conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') "
            "AND name=?", (name,)).fetchone() is not None

    def _create_schema(self) -> None:
        """Install the current (v2) schema, atomically and race-safely: both
        tables inside ONE immediate transaction with IF NOT EXISTS — two
        concurrent first opens serialize on the write lock and the loser's
        creates no-op; a crash can never leave `entries` without its mirror
        visible as "initialized". When repairing a half-created legacy db
        (entries present, mirror missing) the mirror's columns follow the
        EXISTING entries table, so a legacy store never gains a mirror that
        indexes columns it does not have."""
        cols = ",\n                ".join(
            f"{name} {decl}" for name, decl in ADDITIVE_COLUMNS.items())
        old_isolation = self._conn.isolation_level
        self._conn.isolation_level = None  # manage the txn explicitly
        try:
            self._conn.execute("BEGIN IMMEDIATE")
            self._conn.execute(
                f"""CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo TEXT, module TEXT, run_id TEXT,
                    symptom TEXT, root_cause TEXT, fix_summary TEXT,
                    files TEXT, verification TEXT,
                    status TEXT DEFAULT 'active',
                    created_at REAL,
                    {cols})"""
            )
            have = {r[1] for r in
                    self._conn.execute("PRAGMA table_info(entries)")}
            extra = [c for c in _FTS_V2_EXTRA if c in have]
            base_cols = ["symptom", "root_cause", "fix_summary", "module",
                         "repo"] + extra
            self._conn.execute(
                f"""CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
                    {', '.join(base_cols)},
                    content='entries', content_rowid='id')"""
            )
            # backfill via FTS5's own 'rebuild': a mirror created NEXT TO
            # existing rows must index them or every pre-repair memory goes
            # invisible to search. Rebuild re-derives the index from the
            # content table, so it is idempotent — safe on the fresh path
            # (empty), the repair path (backfills), and the concurrent-
            # creator path (no duplicate index entries).
            self._conn.execute(
                "INSERT INTO entries_fts(entries_fts) VALUES('rebuild')")
            self._conn.execute("COMMIT")
        except BaseException:
            try:
                self._conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            self._conn.isolation_level = old_isolation

    def _introspect(self) -> None:
        """Record which columns this database actually has — `record()` writes
        the additive fields only where they exist, so a not-yet-upgraded
        legacy DB keeps working (fields dropped, never an SQL error)."""
        self._columns = {r["name"] for r in
                         self._conn.execute("PRAGMA table_info(entries)")}
        self._fts_columns = {r["name"] for r in
                             self._conn.execute("PRAGMA table_info(entries_fts)")}

    @property
    def schema_v2(self) -> bool:
        """True when every `ADDITIVE_COLUMNS` column exists."""
        return set(ADDITIVE_COLUMNS) <= self._columns

    def ensure_schema_v2(self) -> bool:
        """Explicit, writable schema upgrade to v2 — the ONLY way an existing
        database gains the additive columns. Sanctioned call sites (pinned by
        test): the knowledge-migration CLI, `rebase.v3_knowledge_prep`, and
        `rebase.v3_curate`. Adds the missing columns and rebuilds the FTS
        mirror to index key/tags/watch_outs, all in one transaction. Returns
        True when it changed anything; no-op (False) on an already-v2 db."""
        if self.readonly:
            raise sqlite3.OperationalError("read-only debug memory store")
        old_isolation = self._conn.isolation_level
        self._conn.isolation_level = None
        try:
            # take the write lock FIRST, then decide: two concurrent
            # upgraders (runs share the knowledge lock only SHARED) must
            # serialize here, and the loser must re-observe the schema the
            # winner installed instead of failing on duplicate ALTERs
            self._conn.execute("BEGIN IMMEDIATE")
            self._introspect()
            missing = [c for c in ADDITIVE_COLUMNS if c not in self._columns]
            fts_missing = [c for c in _FTS_V2_EXTRA
                           if c not in self._fts_columns]
            if not missing and not fts_missing:
                self._conn.execute("COMMIT")
                return False
            for col in missing:
                self._conn.execute(
                    f"ALTER TABLE entries ADD COLUMN {col} "
                    f"{ADDITIVE_COLUMNS[col]}")
            self._conn.execute("DROP TABLE IF EXISTS entries_fts")
            self._conn.execute(
                """CREATE VIRTUAL TABLE entries_fts USING fts5(
                    symptom, root_cause, fix_summary, module, repo,
                    key, tags, watch_outs,
                    content='entries', content_rowid='id')""")
            self._conn.execute(
                "INSERT INTO entries_fts(entries_fts) VALUES('rebuild')")
            self._conn.execute("COMMIT")
        except BaseException:
            try:
                self._conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            self._conn.isolation_level = old_isolation
        self._introspect()
        return True

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
        cols = ["repo", "module", "run_id", "symptom", "root_cause",
                "fix_summary", "files", "verification", "status", "created_at"]
        vals: list = [fields["repo"], fields["module"], fields["run_id"],
                      fields["symptom"], fields["root_cause"],
                      fields["fix_summary"], files_json,
                      fields["verification"], status,
                      fields.get("created_at") or time.time()]
        # additive v2 fields: written only where the column exists — a legacy
        # (not-yet-upgraded) db drops them instead of erroring
        for name in ADDITIVE_COLUMNS:
            if name in self._columns and name in fields:
                v = fields[name]
                if name in ("tags", "watch_outs") and isinstance(v, list):
                    v = ",".join(str(t) for t in v)
                cols.append(name)
                vals.append(v)
        cur = self._conn.execute(
            f"INSERT INTO entries ({','.join(cols)}) "
            f"VALUES ({','.join('?' * len(cols))})", vals)
        rowid = cur.lastrowid
        fts_cols = ["rowid", "symptom", "root_cause", "fix_summary",
                    "module", "repo"]
        fts_vals: list = [rowid, fields["symptom"], fields["root_cause"],
                          fields["fix_summary"], fields["module"],
                          fields["repo"]]
        for name in _FTS_V2_EXTRA:
            if name in self._fts_columns:
                v = fields.get(name, "")
                if isinstance(v, list):
                    v = ",".join(str(t) for t in v)
                fts_cols.append(name)
                fts_vals.append(v)
        self._conn.execute(
            f"INSERT INTO entries_fts ({','.join(fts_cols)}) "
            f"VALUES ({','.join('?' * len(fts_cols))})", fts_vals)
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

    # -- curator surface (design D5) ----------------------------------------
    def entries(self, *, repo: str | None = None,
                statuses: tuple = ("active", "candidate")) -> list[dict]:
        """Full rows filtered by repo/status — the curator's read surface.
        The default status set excludes `stale` AND `retired`: retired rows
        are terminal lineage records and must never re-enter clustering."""
        sql = "SELECT * FROM entries WHERE status IN (%s)" % \
            ",".join("?" * len(statuses))
        args: list = list(statuses)
        if repo is not None:
            sql += " AND repo=?"
            args.append(repo)
        out = []
        for row in self._conn.execute(sql + " ORDER BY id", args):
            d = dict(row)
            try:
                d["files"] = json.loads(d.get("files") or "[]")
            except ValueError:
                d["files"] = []
            out.append(d)
        return out

    def apply_curation(self, updates: dict[int, dict]) -> None:
        """Apply the curator's decided field updates ({id: {col: value}}),
        one transaction, then rebuild the FTS mirror once (tags are
        indexed; per-row external-content sync is not worth the fragility).
        Only existing columns are written; `files` lists are re-encoded."""
        if self.readonly:
            raise sqlite3.OperationalError("read-only debug memory store")
        if not updates:
            return
        with self._conn:
            for rowid, fields in updates.items():
                cols, vals = [], []
                for name, value in fields.items():
                    if name not in self._columns:
                        continue
                    if name == "files" and isinstance(value, list):
                        value = json.dumps(value)
                    cols.append(f"{name}=?")
                    vals.append(value)
                if cols:
                    self._conn.execute(
                        f"UPDATE entries SET {', '.join(cols)} WHERE id=?",
                        (*vals, rowid))
            self._conn.execute(
                "INSERT INTO entries_fts(entries_fts) VALUES('rebuild')")
