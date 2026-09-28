"""Trace schema v1: durable records of model calls, decisions and outcomes.

Shared by the copilot and the review bot, so the expensive models' work can be
replayed and turned into datasets for cheaper models plus workflows. Layout
under a trace root::

    records/<YYYY-MM-DD>.jsonl   one JSON record per line (append-only)
    blobs/<aa>/<sha256>.gz       content-addressed payloads (prompts, replies)
    index.db                     SQLite index: id, kind, run, repo, PR, rule
                                 IDs, model, outcome -> the record itself

A record (``schema: trace/1``)::

    {"schema", "id", "kind", "at",
     "context":  {run_id, playbook, step, repo, changeset_id, pr, rule_ids, ...},
     "model":    {role, provider, model, effort, served_model},   # model_call
     "usage", "seconds",
     "inputs":   {name: "sha256:<hex>"},      # blobs, never inline text
     "outputs":  {name: "sha256:<hex>"},
     "result":   {...},                       # decision / outcome / replay
     "error":    "",
     "env":      {copilot_version, copilot_sha, ...}}

``kind`` is ``model_call``, ``decision`` (a gate/review verdict), ``outcome``
(what happened later: merged, closed, retired, accepted...) or ``replay``.
Outcomes are the gold labels for evaluating a cheaper model.

Everything is redacted before it is hashed or written: known token shapes
(GitHub, Anthropic, OpenAI, AWS, bearer headers, private keys) and the value
of every environment variable whose name marks it as a secret.

Standard library only; importing it loads nothing else from the package.
"""

from __future__ import annotations

import contextvars
import datetime as dt
import gzip
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import threading
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping

SCHEMA = "trace/1"
KINDS = ("model_call", "decision", "outcome", "replay")
_CONTEXT: contextvars.ContextVar[dict] = contextvars.ContextVar("trace_context", default={})

_SECRET_SHAPES = re.compile(
    r"gh[pousr]_[A-Za-z0-9]{20,}"
    r"|github_pat_[A-Za-z0-9_]{20,}"
    r"|sk-ant-[A-Za-z0-9_-]{16,}"
    r"|sk-(?:proj-)?[A-Za-z0-9_-]{20,}"
    r"|(?:AKIA|ASIA)[A-Z0-9]{16}"
    r"|xox[abpr]-[A-Za-z0-9-]{10,}"
    r"|(?i:bearer)\s+[A-Za-z0-9._~+/=-]{16,}"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"
)
_SECRET_NAME = re.compile(r"(TOKEN|SECRET|PASSWORD|PASSWD|API_KEY|_KEY|_PAT|CREDENTIALS?)$", re.I)
REDACTED = "[REDACTED]"


def _secret_values(environ: Mapping[str, str]) -> list[str]:
    values = {v for k, v in environ.items() if _SECRET_NAME.search(k) and len(v) >= 8
              and not v.startswith(("/", "~", "."))}  # paths to key files are not secrets
    return sorted(values, key=len, reverse=True)


def redact(text: str, environ: Mapping[str, str] | None = None) -> str:
    """``text`` with secrets replaced by ``[REDACTED]``."""
    for value in _secret_values(os.environ if environ is None else environ):
        text = text.replace(value, REDACTED)
    return _SECRET_SHAPES.sub(REDACTED, text)


def _redact_obj(value: Any, environ: Mapping[str, str] | None = None) -> Any:
    if isinstance(value, str):
        return redact(value, environ)
    if isinstance(value, dict):
        return {(redact(k, environ) if isinstance(k, str) else k): _redact_obj(v, environ)
                for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact_obj(v, environ) for v in value]
    return value


# -- context -----------------------------------------------------------------------

@contextmanager
def trace_context(**fields: Any) -> Iterator[dict]:
    """Bind context fields (run_id, playbook, repo, changeset_id, ...) to every
    record written inside the block, nested blocks adding to outer ones."""
    merged = {**_CONTEXT.get(), **{k: v for k, v in fields.items() if v is not None}}
    token = _CONTEXT.set(merged)
    try:
        yield merged
    finally:
        _CONTEXT.reset(token)


def current_context() -> dict:
    """The bound context as recorded (private ``_`` fields are not recorded)."""
    return {k: v for k, v in _CONTEXT.get().items() if not k.startswith("_")}


def accept_attempt(attempt: int) -> None:
    """Mark which attempt of the current draft was accepted. The caller binds a
    holder as ``_accepted={}``; the accepted call is then identified by its
    ``draft_key`` and ``attempt``, and only that call inherits the decision."""
    holder = _CONTEXT.get().get("_accepted")
    if isinstance(holder, dict):
        holder["attempt"] = int(attempt)


def accepted_key(draft_key: str, holder: Mapping[str, Any]) -> str | None:
    return f"{draft_key}#{holder['attempt']}" if "attempt" in holder else None


_ENV: dict | None = None


def environment_fingerprint() -> dict:
    """Which code produced a record (computed once per process)."""
    global _ENV
    if _ENV is None:
        from . import __version__

        sha = ""
        try:
            proc = subprocess.run(["git", "-C", str(Path(__file__).resolve().parent), "rev-parse", "HEAD"],
                                  capture_output=True, text=True, timeout=5, check=False)
            sha = proc.stdout.strip() if proc.returncode == 0 else ""
        except (OSError, subprocess.SubprocessError):
            pass
        _ENV = {"copilot_version": __version__, "copilot_sha": sha}
    return dict(_ENV)


# -- the store ------------------------------------------------------------------------

class TraceStore:
    def __init__(self, root: str | Path, *, clock=time.time, environ: Mapping[str, str] | None = None):
        self.root = Path(root)
        self._clock = clock
        self._environ = environ
        self._lock = threading.Lock()

    # blobs -----------------------------------------------------------------------
    def put_blob(self, content: str | bytes) -> str:
        """Store redacted text; bytes must be UTF-8 text (redaction needs text)."""
        if isinstance(content, bytes):
            try:
                content = content.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise TypeError("trace blobs are text: binary payloads cannot be redacted") from exc
        data = redact(content, self._environ).encode("utf-8")
        digest = hashlib.sha256(data).hexdigest()
        path = self.root / "blobs" / digest[:2] / f"{digest}.gz"
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(f".{uuid.uuid4().hex}.tmp")
            tmp.write_bytes(gzip.compress(data, mtime=0))
            os.replace(tmp, path)
        return f"sha256:{digest}"

    def blob(self, ref: str) -> str:
        digest = ref.removeprefix("sha256:")
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise KeyError(ref)
        data = gzip.decompress((self.root / "blobs" / digest[:2] / f"{digest}.gz").read_bytes())
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError(f"blob {ref} is corrupt")
        return data.decode("utf-8")

    # records ---------------------------------------------------------------------
    def _db(self) -> sqlite3.Connection:
        self.root.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.root / "index.db", timeout=30)
        conn.execute("""CREATE TABLE IF NOT EXISTS records (
            id TEXT PRIMARY KEY, kind TEXT, at REAL, run_id TEXT, playbook TEXT, repo TEXT,
            changeset_id TEXT, pr INTEGER, rule_ids TEXT, role TEXT, model TEXT, outcome TEXT,
            record TEXT)""")
        for column in ("kind", "run_id", "repo", "changeset_id", "pr", "model", "outcome"):
            conn.execute(f"CREATE INDEX IF NOT EXISTS records_{column} ON records({column})")
        return conn

    def append(self, kind: str, *, inputs: Mapping[str, str] | None = None,
               outputs: Mapping[str, str] | None = None, model: Mapping[str, Any] | None = None,
               result: Mapping[str, Any] | None = None, usage: Mapping[str, Any] | None = None,
               seconds: float | None = None, error: str = "", context: Mapping[str, Any] | None = None,
               ) -> dict:
        """Write one record; text in ``inputs``/``outputs`` goes to blobs."""
        if kind not in KINDS:
            raise ValueError(f"unknown trace record kind: {kind}")
        now = self._clock()
        record = {
            "schema": SCHEMA, "id": f"{int(now * 1000)}-{uuid.uuid4().hex[:12]}", "kind": kind, "at": now,
            "context": {**current_context(), **(context or {})},
            "model": dict(model or {}), "usage": dict(usage or {}),
            "seconds": seconds,
            "inputs": {k: self.put_blob(v) for k, v in (inputs or {}).items()},
            "outputs": {k: self.put_blob(v) for k, v in (outputs or {}).items()},
            "result": dict(result or {}),
            "error": error or "",
            "env": environment_fingerprint(),
        }
        # every string of the record, keys included, before it is serialized or indexed
        record = _redact_obj(record, self._environ)
        line = json.dumps(record, ensure_ascii=False, sort_keys=True)
        day = dt.datetime.fromtimestamp(now, dt.timezone.utc).date().isoformat()
        with self._lock:
            path = self.root / "records" / f"{day}.jsonl"
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
            with self._db() as conn:
                conn.execute("INSERT INTO records VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", _row(record, line))
        return record

    def get(self, record_id: str) -> dict:
        with self._db() as conn:
            row = conn.execute("SELECT record FROM records WHERE id=?", (record_id,)).fetchone()
        if row is None:
            raise KeyError(record_id)
        return json.loads(row[0])

    def query(self, *, kind: str | None = None, run_id: str | None = None, repo: str | None = None,
              changeset_id: str | None = None, pr: int | None = None, rule_id: str | None = None,
              role: str | None = None, model: str | None = None, playbook: str | None = None,
              limit: int = 1000) -> list[dict]:
        clauses, args = [], []
        for column, value in (("kind", kind), ("run_id", run_id), ("repo", repo),
                              ("changeset_id", changeset_id), ("pr", pr), ("role", role),
                              ("model", model), ("playbook", playbook)):
            if value is not None:
                clauses.append(f"{column}=?")
                args.append(value)
        if rule_id is not None:
            clauses.append("rule_ids LIKE ?")
            args.append(f"%,{rule_id},%")
        sql = "SELECT record FROM records" + (" WHERE " + " AND ".join(clauses) if clauses else "") \
            + " ORDER BY at, id LIMIT ?"
        with self._db() as conn:
            return [json.loads(row[0]) for row in conn.execute(sql, (*args, int(limit)))]

    def rebuild_index(self) -> int:
        """Re-create index.db from the JSONL records (the source of truth)."""
        (self.root / "index.db").unlink(missing_ok=True)
        count = 0
        with self._db() as conn:
            for path in sorted((self.root / "records").glob("*.jsonl")):
                for line in path.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    conn.execute("INSERT OR REPLACE INTO records VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                 _row(json.loads(line), line))
                    count += 1
        return count


def _row(record: dict, line: str) -> tuple:
    ctx = record.get("context") or {}
    model = record.get("model") or {}
    result = record.get("result") or {}
    rule_ids = ctx.get("rule_ids") or []
    pr = str(ctx.get("pr") or "")
    return (record["id"], record["kind"], record["at"], str(ctx.get("run_id") or ""),
            str(ctx.get("playbook") or ""), str(ctx.get("repo") or ""), str(ctx.get("changeset_id") or ""),
            int(pr) if pr.isdigit() else None,
            "," + ",".join(map(str, rule_ids)) + "," if rule_ids else "",
            str(model.get("role") or ""), str(model.get("model") or ""),
            str(result.get("outcome") or result.get("status") or ""), line)
