"""Operator requests for the single-writer maintenance scheduler.

The CLI only enqueues immutable requests. Owner resolution requests are signed
after authenticating the actual gh user; only the scheduler can append a
resolution or sign a labeled regression case. Original audit rows stay intact.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess

from ..knowledge_service.signing import canonical_json, sign, verify
from .maintenance_audit import source_evidence
from .maintenance_calibration import cases_directory
from .maintenance_store import MaintenanceStore
from .outbox import atomic_write_json

RESOLUTION_PURPOSE = "kb-maintenance-resolution-request"
OUTCOMES = {"verified", "contradicted", "unknown"}
PROOF_FIELDS = ("repository", "sha", "path", "start_line", "end_line", "content_sha256")


def _digest(value):
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _owners():
    owners = {name.casefold() for name in re.split(r"[,\s]+", os.environ.get("KB_MAINTENANCE_OWNERS", "")) if name}
    if not owners:
        raise ValueError("KB_MAINTENANCE_OWNERS must explicitly allow the authenticated owner")
    return owners


def authenticated_owner():
    result = subprocess.run(["gh", "api", "user", "--jq", ".login"],
                            check=True, capture_output=True, text=True, timeout=30)
    actor = result.stdout.strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}", actor) or actor.casefold() not in _owners():
        raise ValueError("authenticated gh user is not an allowed maintenance owner")
    return actor


def _evidence(value):
    text = Path(value[1:]).read_text() if value.startswith("@") else value
    evidence = json.loads(text)
    if not isinstance(evidence, dict) or not isinstance(evidence.get("reason"), str) or not evidence["reason"].strip():
        raise ValueError("resolution evidence must be a JSON object with a nonempty reason")
    # Canonical encoding also rejects non-finite numbers before signing.
    json.dumps(evidence, allow_nan=False)
    return evidence


def _oracle(evidence):
    kind = evidence.get("calibration_kind", "audit")
    if kind not in {"audit", "correction"}:
        raise ValueError("calibration_kind must be audit or correction")
    oracle = evidence.get("correction_oracle")
    if kind == "correction":
        if not isinstance(oracle, dict) or oracle.get("expected_gate") not in {"pass", "fail", "human"}:
            raise ValueError("a correction case requires an explicit correction_oracle.expected_gate")
        if oracle["expected_gate"] == "pass" and not re.fullmatch(r"[a-f0-9]{64}", str(oracle.get("expected_page_sha256", ""))):
            raise ValueError("a passing correction oracle requires the normalized corrected page SHA-256")
    elif oracle is not None:
        raise ValueError("correction_oracle requires calibration_kind=correction")
    return kind, oracle


def _confirmation(evidence):
    if evidence.get("expected") not in OUTCOMES:
        raise ValueError("confirm requires explicit expected=verified|contradicted|unknown")
    witnesses = evidence.get("witnesses")
    if not isinstance(witnesses, list) or not witnesses or any(
        not isinstance(row, dict) or any(field not in row for field in PROOF_FIELDS) for row in witnesses
    ):
        raise ValueError("confirm requires immutable original-source witnesses with repository, SHA, path, span and SHA-256")
    if len(witnesses) > 64:
        raise ValueError("confirm requires a bounded original-source witness packet")
    for row in witnesses:
        path = row["path"]
        if (not isinstance(row["repository"], str) or not row["repository"]
                or not isinstance(path, str) or not path or PurePosixPath(path).is_absolute()
                or ".." in PurePosixPath(path).parts or "\\" in path
                or not isinstance(row["sha"], str) or not re.fullmatch(r"[a-f0-9]{40}(?:[a-f0-9]{24})?", row["sha"])
                or not isinstance(row["content_sha256"], str) or not re.fullmatch(r"[a-f0-9]{64}", row["content_sha256"])
                or type(row["start_line"]) is not int or type(row["end_line"]) is not int
                or not 1 <= row["start_line"] <= row["end_line"]
                or ("quote" in row and (not isinstance(row["quote"], str) or not row["quote"].strip()))):
            raise ValueError("original-source witness identity, span or hash is malformed")
    _oracle(evidence)


def _selected(rt, args):
    if getattr(args, "all", False):
        return None
    repo = args.repo
    if repo not in rt.registry:
        raise ValueError(f"unknown maintenance repository: {repo}")
    if not rt.registry[repo].enabled:
        raise ValueError(f"maintenance repository is disabled: {repo}")
    return [repo]


def command(args, state_dir):
    from ..config import Settings
    from . import maintenance
    from .runtime import KbRuntime

    rt = KbRuntime.from_env(Settings(), state_dir=state_dir, sync_repos=False)
    try:
        store = MaintenanceStore(rt.ledger, lease_owner=rt.lease_owner)
        if args.command == "maintain":
            repos = _selected(rt, args)
            if args.maintenance_action in {"plan", "status"}:
                result = maintenance.plan(rt, repos=repos)
                if args.maintenance_action == "status":
                    snapshot = result.get("snapshot")
                    _, units = maintenance._units(rt, snapshot, repos) if snapshot else ({}, [])
                    operational = maintenance.operational_status(rt, store, units)
                    findings = [{"id": row["id"], "run_id": row["run_id"], "unit_id": row["unit_id"],
                                 "repo": row["unit"]["repo"], "outcome": row["outcome"], "created_at": row["created_at"],
                                 "reason": row["detail"].get("reason", "")}
                                for row in store.findings() if repos is None or row["unit"]["repo"] in repos]
                    result = {**result, "requests": [r for r in store.pending_requests()
                                                     if repos is None or r["repo"] in {*repos, "*"}],
                              "runs": store.runs(), "findings": findings, "operational": operational}
            else:
                detail = {"kind": "maintenance", "calibrate": args.calibrate, "drill": args.drill}
                result = store.enqueue_request(args.request_id, repos[0] if repos else "*", detail, now=rt.clock())
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
            return 0
        actor = authenticated_owner()
        finding = store.finding(args.id)
        if finding is None:
            raise ValueError("unknown maintenance finding ID")
        if rt.outbox is None:
            raise ValueError("owner resolution requires the existing KB_SIGNING_KEY")
        evidence = _evidence(args.evidence)
        if args.decision == "confirm":
            _confirmation(evidence)
        payload = {"schema_version": 1, "finding_id": args.id,
                   "finding_sha256": _digest(finding), "decision": args.decision,
                   "actor": actor, "evidence": evidence}
        request_id = args.request_id or "resolution-" + _digest(payload)
        payload["request_id"] = request_id
        envelope = sign(RESOLUTION_PURPOSE, payload, rt.outbox._key)
        result = store.enqueue_request(request_id, finding["unit"]["repo"],
                                       {"resolution": envelope}, now=rt.clock())
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    finally:
        rt.ledger.close()


def apply_resolution(rt, store, request):
    """Revalidate an owner request under the scheduler lease; no model calls."""
    if not rt.lease_owner or store.lease_owner != rt.lease_owner:
        raise ValueError("owner resolution requires the live scheduler lease")
    if rt.outbox is None:
        raise ValueError("owner resolution requires the service signing key")
    payload = verify(RESOLUTION_PURPOSE, request["detail"]["resolution"], rt.outbox._key.public_key())
    if payload.get("schema_version") != 1 or payload.get("request_id") != request["id"]:
        raise ValueError("resolution request identity mismatch")
    actor, decision = payload.get("actor"), payload.get("decision")
    if not isinstance(actor, str) or actor.casefold() not in _owners() or decision not in {"confirm", "dismiss"}:
        raise ValueError("resolution is not authorized by a current maintenance owner")
    finding = store.finding(payload["finding_id"])
    if finding is None or payload.get("finding_sha256") != _digest(finding) or request["repo"] != finding["unit"]["repo"]:
        raise ValueError("resolution does not bind the immutable original finding")
    evidence = payload["evidence"]
    if not isinstance(evidence, dict) or not str(evidence.get("reason", "")).strip():
        raise ValueError("resolution evidence requires a reason")
    recorded = dict(evidence)
    case_path = None
    if decision == "confirm":
        _confirmation(evidence)
        unit = finding["unit"]
        witnesses = source_evidence(rt, rt.registry[unit["repo"]], unit)
        available = {tuple(row[field] for field in PROOF_FIELDS): row for row in witnesses}
        verified = []
        for row in evidence["witnesses"]:
            proof = available.get(tuple(row[field] for field in PROOF_FIELDS))
            if proof is None or (row.get("quote") and row["quote"] not in proof["excerpt"]):
                raise ValueError("owner witness does not match the immutable original source")
            verified.append(proof)
        kind, oracle = _oracle(evidence)
        case_id = _digest({"request": request["id"], "finding": finding["id"]})
        case = {"id": case_id, "actor": actor, "expected": evidence["expected"],
                "calibration_kind": kind, "unit": unit, "finding_id": finding["id"],
                "original_outcome": finding["outcome"], "reason": evidence["reason"],
                "source_evidence": verified}
        if oracle is not None:
            case["correction_oracle"] = oracle
        # Repo adapter IDs are path components, never caller-supplied paths.
        repo = str(unit["repo"])
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", repo) or repo in {".", ".."}:
            raise ValueError("repository ID is not safe for a calibration case directory")
        case_path = cases_directory() / repo / "cases" / f"{case_id}.json"
        if case_path.exists():
            existing = verify("kb-maintenance-human-case", json.loads(case_path.read_text()), rt.outbox._key.public_key())
            if existing != case:
                raise ValueError("human calibration case identity changed")
        else:
            # No unlabeled candidate is promoted implicitly; every label and
            # correction oracle above came from this signed owner request.
            with rt.ledger.fenced(rt.lease_owner):
                atomic_write_json(case_path, sign("kb-maintenance-human-case", case, rt.outbox._key))
                case_path.chmod(0o600)
        recorded["verified_original_sources"] = verified
        recorded["calibration_case"] = str(case_path)
    result = store.record_resolution(finding["id"], decision, actor, recorded,
                                     resolution_id=request["id"], now=rt.clock())
    return {**result, "calibration_case": str(case_path) if case_path else None}
