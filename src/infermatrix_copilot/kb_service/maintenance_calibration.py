"""Additional calibration and human-confirmed cases; never part of served knowledge."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from ..knowledge_service.signing import sign, verify
from .maintenance_audit import AUDIT_SYSTEM, BudgetGateway, audit_unit, digest
from .outbox import atomic_write_json


def cases_directory():
    return Path(os.environ.get("KB_MAINTENANCE_CASES_DIR") or
                Path(__file__).resolve().parents[3] / "eval" / "knowledge-maintenance")


def load_cases(rt):
    result = []
    directory = cases_directory()
    if rt.outbox is None:
        return result
    for path in sorted(directory.glob("*/cases/*.json")):
        envelope = json.loads(path.read_text())
        case = verify("kb-maintenance-human-case", envelope, rt.outbox._key.public_key())
        if not case.get("actor") or case.get("expected") not in {"verified", "contradicted", "unknown"}:
            raise ValueError("maintenance calibration case lacks a human oracle")
        if case.get("unit", {}).get("repo") not in rt.registry:
            raise ValueError("maintenance case names an unknown repository")
        kind = case.get("calibration_kind", "audit")
        if kind not in {"audit", "correction"}:
            raise ValueError("unknown maintenance calibration kind")
        if kind == "correction":
            oracle = case.get("correction_oracle", {})
            if oracle.get("expected_gate") not in {"pass", "fail", "human"}:
                raise ValueError("correction case needs an explicit human gate oracle")
            if oracle["expected_gate"] == "pass" and not oracle.get("expected_page_sha256"):
                raise ValueError("passing correction case needs a human-confirmed content digest")
        result.append(case)
    return result


def cases_digest(rt):
    cases = load_cases(rt)
    return digest(json.dumps(cases, ensure_ascii=False, sort_keys=True))


def current(rt, policy_sha256, *, observed_model=None, observed_generator=None):
    if rt.outbox is None:
        return False
    path = rt.state_dir / "maintenance" / "calibration.json"
    if not path.exists():
        return False
    try:
        record = verify("kb-maintenance-calibration", json.loads(path.read_text()), rt.outbox._key.public_key())
        return record.get("passed") is True and record.get("policy_sha256") == policy_sha256 \
            and record.get("case_digest") == cases_digest(rt) and record.get("judge") == rt.judge.label() \
            and record.get("generator") == rt.generator.label() and record.get("correction_passed") is True \
            and (observed_model is None or observed_model in record.get("observed_models", [])) \
            and (observed_generator is None or observed_generator in record.get("observed_generators", []))
    except (ValueError, OSError, KeyError):
        return False


def calibrate(rt, store, config, *, run_id, policy_sha256):
    cases = load_cases(rt)
    details, observed_models, observed_generators, corrections = [], set(), set(), []
    for case in cases:
        unit = {**case["unit"], "lane": "priority"}
        gateway = BudgetGateway(rt, store, config, run_id=run_id, unit=unit, phase="calibration:" + case["id"])
        result = audit_unit(rt, rt.registry[unit["repo"]], unit, gateway)
        observed_models.add(result["reviewer"])
        if case.get("calibration_kind", "audit") == "audit":
            details.append({"id": case["id"], "expected": case["expected"], "outcome": result["outcome"]})
        else:
            from .maintenance_correction import propose_correction
            from ..knowledge_service.lifecycle import Page
            from .models import ModelUnavailable
            from .maintenance_store import BudgetExceeded
            oracle = case["correction_oracle"]
            entry = {"id": case["id"], "expected_gate": oracle["expected_gate"], "gate": "unknown", "content_matches": False}
            try:
                if result["outcome"] != "contradicted":
                    raise ValueError("correction calibration did not find its confirmed defect")
                base = rt.knowledge.knowledge_files(unit["snapshot"])
                if unit["text"] not in base.get(unit["page"], ""):
                    raise ValueError("correction calibration original snapshot does not match its oracle")
                proposal = propose_correction(rt, rt.registry[unit["repo"]], store, config,
                    run_id=run_id, unit=unit, finding=result, base=base, base_sha=unit["snapshot"],
                    publish_result=False, phase="correction-calibration:" + case["id"])
                changeset = rt.ledger.changeset(proposal["changeset_id"])
                observed_generators.add(changeset["detail"].get("served_generator"))
                entry["gate"] = changeset["detail"]["decision"]["status"]
                files = rt.load_changeset_files(proposal["changeset_id"])["files"]
                corrected = Page.parse(files[unit["page"]])
                old_updated = Page.parse(base[unit["page"]]).frontmatter_data().get("updated")
                normalized = corrected.with_frontmatter_field("updated", str(old_updated)).render()
                entry["content_matches"] = digest(normalized) == oracle.get("expected_page_sha256")
                entry["changeset_id"] = proposal["changeset_id"]
            except BudgetExceeded:
                raise
            except ModelUnavailable as exc:
                entry["gate"], entry["reason"] = "execution_error", str(exc)
            except ValueError as exc:
                entry["gate"], entry["reason"] = "human", str(exc)
            entry["passed"] = entry["gate"] == oracle["expected_gate"] and (entry["gate"] != "pass" or entry["content_matches"])
            corrections.append(entry)
    good = [case for case in details if case["expected"] == "verified"]
    bad = [case for case in details if case["expected"] != "verified"]
    correction_good = [c for c in corrections if c["expected_gate"] == "pass"]
    correction_bad = [c for c in corrections if c["expected_gate"] != "pass"]
    correction_passed = bool(correction_good and correction_bad) and all(c["passed"] for c in correction_bad) \
        and sum(not c["passed"] for c in correction_good) / len(correction_good) <= .2
    # An ambiguous owner oracle must stay unknown: a false contradiction can
    # authorize correction just as a false verification can retain bad advice.
    unsafe = [case for case in bad if case["expected"] == "unknown" and case["outcome"] != "unknown"]
    unsafe += [case for case in bad if case["expected"] == "contradicted" and case["outcome"] == "verified"]
    passed = correction_passed and bool(good and bad) and not unsafe \
        and sum(case["outcome"] != "verified" for case in good) / len(good) <= 0.2
    record = {"passed": passed, "policy_sha256": policy_sha256, "case_digest": cases_digest(rt),
              "judge": rt.judge.label(), "generator": rt.generator.label(), "correction_passed": correction_passed,
              "corrections": corrections, "observed_models": sorted(v for v in observed_models if v),
              "observed_generators": sorted(v for v in observed_generators if v),
              "at": rt.clock(), "details": details, "false_accepts": len(unsafe)}
    if rt.outbox is not None:
        atomic_write_json(rt.state_dir / "maintenance" / "calibration.json",
                          sign("kb-maintenance-calibration", record, rt.outbox._key))
    return record


def candidate(rt, unit, finding):
    """Prepare unlabeled evidence. Only an explicit owner action creates an oracle."""
    identity = digest(json.dumps({"unit": unit["unit_id"], "hash": unit["content_sha256"],
                                  "finding": finding}, ensure_ascii=False, sort_keys=True))
    path = rt.state_dir / "maintenance" / "regression-candidates" / f"{identity}.json"
    if not path.exists():
        atomic_write_json(path, {"id": identity, "unit": unit, "finding": finding,
                                 "status": "awaiting_human_confirmation", "expected": None})
        path.chmod(0o600)
    return path
