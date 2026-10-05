"""Cross-platform SQLite persistence and transactionally claimed operations."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

SCHEMA = """
CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, name TEXT UNIQUE NOT NULL, admin INTEGER NOT NULL DEFAULT 0, enabled INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS tokens(id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), digest TEXT UNIQUE NOT NULL, expires REAL NOT NULL, revoked INTEGER NOT NULL DEFAULT 0, created REAL NOT NULL);
CREATE TABLE IF NOT EXISTS sessions(digest TEXT PRIMARY KEY, token_id TEXT NOT NULL REFERENCES tokens(id), expires REAL NOT NULL);
CREATE TABLE IF NOT EXISTS repositories(id TEXT PRIMARY KEY, name TEXT NOT NULL, provider TEXT NOT NULL, external_name TEXT NOT NULL, root TEXT NOT NULL DEFAULT '', config TEXT NOT NULL DEFAULT '{}');
CREATE TABLE IF NOT EXISTS repository_grants(repo_id TEXT NOT NULL REFERENCES repositories(id), user_id TEXT NOT NULL REFERENCES users(id), role TEXT NOT NULL, PRIMARY KEY(repo_id,user_id));
CREATE TABLE IF NOT EXISTS rfcs(id TEXT PRIMARY KEY, repo_id TEXT NOT NULL REFERENCES repositories(id), title TEXT NOT NULL, body TEXT NOT NULL, revision TEXT NOT NULL, source TEXT NOT NULL DEFAULT '{}', model TEXT NOT NULL, enrolled INTEGER NOT NULL DEFAULT 0, restricted INTEGER NOT NULL DEFAULT 0, created_by TEXT NOT NULL REFERENCES users(id), updated REAL NOT NULL);
CREATE TABLE IF NOT EXISTS rfc_grants(rfc_id TEXT NOT NULL REFERENCES rfcs(id), user_id TEXT NOT NULL REFERENCES users(id), role TEXT NOT NULL, PRIMARY KEY(rfc_id,user_id));
CREATE TABLE IF NOT EXISTS source_snapshots(id INTEGER PRIMARY KEY, rfc_id TEXT NOT NULL REFERENCES rfcs(id), revision TEXT NOT NULL, body TEXT NOT NULL, created REAL NOT NULL, title TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS operations(id TEXT PRIMARY KEY, actor TEXT NOT NULL REFERENCES users(id), credential_id TEXT NOT NULL DEFAULT '', kind TEXT NOT NULL, repo_id TEXT NOT NULL, rfc_id TEXT NOT NULL DEFAULT '', payload TEXT NOT NULL, idempotency_key TEXT NOT NULL, request_digest TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', result TEXT NOT NULL DEFAULT '{}', error TEXT NOT NULL DEFAULT '', created REAL NOT NULL, updated REAL NOT NULL, worker TEXT NOT NULL DEFAULT '', lease_until REAL NOT NULL DEFAULT 0, UNIQUE(actor,idempotency_key));
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, actor TEXT NOT NULL, action TEXT NOT NULL, repo_id TEXT NOT NULL DEFAULT '', rfc_id TEXT NOT NULL DEFAULT '', detail TEXT NOT NULL DEFAULT '{}', created REAL NOT NULL);
CREATE INDEX IF NOT EXISTS operations_pending ON operations(status,lease_until,created);
CREATE TABLE IF NOT EXISTS translations(scope TEXT NOT NULL, segment TEXT NOT NULL, language TEXT NOT NULL, source TEXT NOT NULL, translated TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'pending', credential_id TEXT NOT NULL DEFAULT '', model TEXT NOT NULL DEFAULT '', attempts INTEGER NOT NULL DEFAULT 0, retry_at REAL NOT NULL DEFAULT 0, lease_until REAL NOT NULL DEFAULT 0, worker TEXT NOT NULL DEFAULT '', updated REAL NOT NULL, PRIMARY KEY(scope,segment,language));
CREATE INDEX IF NOT EXISTS translations_pending ON translations(status,retry_at,lease_until,updated);
CREATE TABLE IF NOT EXISTS chat_threads(id TEXT PRIMARY KEY, actor TEXT NOT NULL REFERENCES users(id), repo_id TEXT NOT NULL REFERENCES repositories(id), rfc_id TEXT NOT NULL REFERENCES rfcs(id), title TEXT NOT NULL DEFAULT '', visibility TEXT NOT NULL, created REAL NOT NULL, updated REAL NOT NULL);
CREATE TABLE IF NOT EXISTS chat_messages(id INTEGER PRIMARY KEY, thread_id TEXT NOT NULL REFERENCES chat_threads(id) ON DELETE CASCADE, job_id TEXT NOT NULL DEFAULT '', role TEXT NOT NULL, content TEXT NOT NULL, created REAL NOT NULL);
CREATE TABLE IF NOT EXISTS chat_jobs(id TEXT PRIMARY KEY, thread_id TEXT NOT NULL REFERENCES chat_threads(id) ON DELETE CASCADE, credential_id TEXT NOT NULL REFERENCES tokens(id), payload TEXT NOT NULL, idempotency_key TEXT NOT NULL, request_digest TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', result TEXT NOT NULL DEFAULT '{}', error TEXT NOT NULL DEFAULT '', worker TEXT NOT NULL DEFAULT '', lease_until REAL NOT NULL DEFAULT 0, attempts INTEGER NOT NULL DEFAULT 0, created REAL NOT NULL, updated REAL NOT NULL, UNIQUE(thread_id,idempotency_key));
CREATE INDEX IF NOT EXISTS chat_jobs_pending ON chat_jobs(status,lease_until,created);
CREATE TABLE IF NOT EXISTS chat_leases(worker TEXT PRIMARY KEY, job_id TEXT NOT NULL, thread_id TEXT NOT NULL, lease_until REAL NOT NULL);
CREATE TABLE IF NOT EXISTS chat_events(id INTEGER PRIMARY KEY, thread_id TEXT NOT NULL REFERENCES chat_threads(id) ON DELETE CASCADE, job_id TEXT NOT NULL DEFAULT '', kind TEXT NOT NULL, data TEXT NOT NULL DEFAULT '{}', created REAL NOT NULL);
CREATE INDEX IF NOT EXISTS chat_events_thread ON chat_events(thread_id,id);
CREATE TABLE IF NOT EXISTS chat_proposals(id TEXT PRIMARY KEY, thread_id TEXT NOT NULL REFERENCES chat_threads(id) ON DELETE CASCADE, job_id TEXT NOT NULL REFERENCES chat_jobs(id) ON DELETE CASCADE, status TEXT NOT NULL DEFAULT 'proposed', proposal TEXT NOT NULL, candidate TEXT NOT NULL, candidate_digest TEXT NOT NULL, reason TEXT NOT NULL, result TEXT NOT NULL DEFAULT '{}', created REAL NOT NULL, updated REAL NOT NULL);
"""


def encode(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class Store:
    def __init__(self, state_dir: str | Path):
        self.root = Path(state_dir).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = self.root / "rfc.sqlite"
        con = self.connect()
        try:
            con.execute("PRAGMA journal_mode=WAL")
            con.executescript(SCHEMA)
            con.execute("BEGIN IMMEDIATE")
            if "title" not in {row[1] for row in con.execute("PRAGMA table_info(source_snapshots)")}:
                con.execute("ALTER TABLE source_snapshots ADD COLUMN title TEXT NOT NULL DEFAULT ''")
            con.execute("INSERT OR IGNORE INTO metadata VALUES ('schema_version','1')")
            con.commit()
        finally:
            con.close()
        try:
            self.path.chmod(0o600)
        except OSError:
            pass

    def connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA busy_timeout=15000")
        return con

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        con = self.connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            yield con
            con.commit()
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()

    def one(self, sql: str, params: tuple = ()) -> dict | None:
        con = self.connect()
        try:
            row = con.execute(sql, params).fetchone()
            return dict(row) if row else None
        finally:
            con.close()

    def all(self, sql: str, params: tuple = ()) -> list[dict]:
        con = self.connect()
        try:
            return [dict(row) for row in con.execute(sql, params).fetchall()]
        finally:
            con.close()

    def audit(self, con: sqlite3.Connection, actor: str, action: str, now: float,
              repo_id: str = "", rfc_id: str = "", detail: dict | None = None) -> None:
        con.execute("INSERT INTO audit(actor,action,repo_id,rfc_id,detail,created) VALUES (?,?,?,?,?,?)",
                    (actor, action, repo_id, rfc_id, encode(detail or {}), now))

    def claim(self, worker: str, now: float, lease_seconds: float = 900) -> dict | None:
        with self.transaction() as con:
            # Serialize operations per RFC/repository even across independent processes.
            row = con.execute("""SELECT o.* FROM operations o
                WHERE (o.status='pending' OR (o.status='running' AND o.lease_until<?))
                AND NOT EXISTS (SELECT 1 FROM operations x WHERE x.id!=o.id
                    AND x.status='running' AND x.lease_until>=?
                    AND ((o.rfc_id!='' AND x.rfc_id=o.rfc_id) OR (o.rfc_id='' AND x.repo_id=o.repo_id)
                        OR (o.kind='rfcs.update_source' AND x.kind='rfcs.update_source'
                            AND (o.repo_id=x.repo_id OR (COALESCE(json_extract(o.payload,'$.source_lock'),'')!=''
                                AND json_extract(o.payload,'$.source_lock')=json_extract(x.payload,'$.source_lock'))))))
                ORDER BY o.created,o.id LIMIT 1""", (now, now)).fetchone()
            if not row:
                return None
            result = dict(row)
            con.execute("UPDATE operations SET status='running',worker=?,lease_until=?,updated=? WHERE id=?",
                        (worker, now + lease_seconds, now, row["id"]))
            return result

    def renew(self, operation_id: str, worker: str, now: float) -> bool:
        with self.transaction() as con:
            return bool(con.execute("UPDATE operations SET lease_until=? WHERE id=? AND worker=? AND status='running'",
                                    (now + 900, operation_id, worker)).rowcount)
