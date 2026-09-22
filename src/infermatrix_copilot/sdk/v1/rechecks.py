"""Validate explicit rechecks without deriving resolution from omission."""
from __future__ import annotations

import re
from .models import InvalidRequestError


def validate_carried(rows):
    ids = set()
    if not isinstance(rows, (list, tuple)) or not all(isinstance(row, dict) for row in rows):
        raise InvalidRequestError("carried findings must be a list of objects")
    if len(rows) > 200:
        raise InvalidRequestError("at most 200 carried findings per review")
    for row in rows:
        identity = row.get("finding_id")
        if not isinstance(identity, str) or not identity.strip() or identity in ids:
            raise InvalidRequestError("carried findings require unique nonempty identities")
        if not re.fullmatch(r"[0-9a-fA-F]{40}", str(row.get("source_head_sha") or "")):
            raise InvalidRequestError("carried finding source_head_sha must be a full SHA")
        if not str(row.get("title") or "").strip():
            raise InvalidRequestError("carried finding title must not be empty")
        ids.add(identity)
    return ids


def checked_rechecks(carried, records, head_sha):
    """Return only safe records and explicit gaps; duplicates never resolve."""
    expected = {row["finding_id"] for row in carried}
    missing = []
    safe = []
    seen = set()
    duplicates = set()
    if not isinstance(records, (list, tuple)):
        records = ()
    for row in records:
        if not isinstance(row, dict):
            missing.append("invalid finding recheck")
            continue
        identity = row.get("finding_id")
        if not isinstance(identity, str) or identity not in expected:
            missing.append("recheck names an unknown carried finding")
            continue
        if identity in seen:
            duplicates.add(identity)
            missing.append("duplicate finding recheck: " + identity)
        seen.add(identity)
        if (row.get("head_sha") != head_sha
            or not isinstance(row.get("outcome"), str)
            or row.get("outcome") not in {"fixed", "still_affected", "unverified"}
            or not isinstance(row.get("evidence"), str) or not row["evidence"].strip()):
            missing.append("invalid or wrong-head finding recheck: " + identity)
            continue
        safe.append({key: row[key] for key in ("finding_id", "head_sha", "outcome", "evidence")})
    safe = [row for row in safe if row["finding_id"] not in duplicates]
    answered = {row["finding_id"] for row in safe}
    missing.extend("missing finding recheck: " + identity for identity in sorted(expected - answered))
    return safe, missing
