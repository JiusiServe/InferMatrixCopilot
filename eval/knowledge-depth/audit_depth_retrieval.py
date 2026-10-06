#!/usr/bin/env python3
"""Audit actual bounded Direct context for every feature in one frozen KB tree.

Facet status here describes intact served metadata. Source verification and
native approval are separate audits; these probes do not measure PR bug recall.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import yaml

from infermatrix_copilot.direct_routing import direct_review_plan
from infermatrix_copilot.kb_service.knowledge_coverage import load_policy, policy_path
from infermatrix_copilot.kb_service.knowledge_depth import FACETS, depth_page
from infermatrix_copilot.knowledge_service.lifecycle import depth_sections
from infermatrix_copilot.knowledge_view import KnowledgeView, build_manifest

PROBES = ("description_and_paths", "query_only", "paths_only")
REPORT_FORMAT = "depth-retrieval-deduplicated-v1"


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _object_hash(value) -> str:
    return _hash(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def pack_report(report: dict) -> dict:
    """Store repeated actual context and budgets once, without losing evidence."""
    if "storage" in report:
        raise ValueError("retrieval report is already packed")
    packed = {**report, "cases": [], "documents": {}, "content_blobs": {}, "execution_budgets": {}}
    for case in report["cases"]:
        row = {k: v for k, v in case.items() if k not in ("documents", "execution_budget")}
        row["document_refs"] = []
        for document in case["documents"]:
            content = document["content"]
            content_hash = _hash(content)
            if document.get("content_sha256") != content_hash:
                raise ValueError("actual retrieval content hash differs from the document")
            packed["content_blobs"][content_hash] = content
            metadata = {k: v for k, v in document.items() if k != "content"}
            reference = _object_hash(metadata)
            packed["documents"][reference] = metadata
            row["document_refs"].append(reference)
        budget_hash = _object_hash(case["execution_budget"])
        packed["execution_budgets"][budget_hash] = case["execution_budget"]
        row["execution_budget_ref"] = budget_hash
        packed["cases"].append(row)
    packed["storage"] = {"format": REPORT_FORMAT, "expanded_report_sha256": _object_hash(report)}
    return packed


def expand_report(report: dict) -> dict:
    """Replay hash-bound records into the exact original audit result."""
    storage = report.get("storage", {})
    if storage.get("format") != REPORT_FORMAT:
        raise ValueError("unsupported retrieval evidence storage format")
    expanded = {k: v for k, v in report.items()
                if k not in ("storage", "documents", "content_blobs", "execution_budgets", "cases")}
    expanded["cases"] = []
    try:
        for reference, content in report["content_blobs"].items():
            if _hash(content) != reference:
                raise ValueError("retrieval content blob hash mismatch")
        for reference, document in report["documents"].items():
            if _object_hash(document) != reference:
                raise ValueError("retrieval document metadata hash mismatch")
        for reference, budget in report["execution_budgets"].items():
            if _object_hash(budget) != reference:
                raise ValueError("retrieval execution budget hash mismatch")
        for case in report["cases"]:
            row = {k: v for k, v in case.items() if k not in ("document_refs", "execution_budget_ref")}
            row["documents"] = []
            for reference in case["document_refs"]:
                metadata = report["documents"][reference]
                row["documents"].append({**metadata, "content": report["content_blobs"][metadata["content_sha256"]]})
            row["execution_budget"] = report["execution_budgets"][case["execution_budget_ref"]]
            expanded["cases"].append(row)
    except (KeyError, TypeError) as exc:
        raise ValueError("missing or malformed retrieval evidence reference") from exc
    if _object_hash(expanded) != storage.get("expanded_report_sha256"):
        raise ValueError("expanded retrieval evidence differs from the original audit")
    return expanded


def serialize_report(report: dict) -> str:
    """Readable summaries and one record per line for large evidence tables."""
    packed = pack_report(report)
    compact = lambda value: json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    fields = []
    for key, value in packed.items():
        if key == "cases":
            rendered = "[\n" + ",\n".join("    " + compact(row) for row in value) + "\n  ]"
        elif key in ("features", "documents", "content_blobs", "execution_budgets"):
            rendered = "{\n" + ",\n".join("    " + compact(k) + ": " + compact(v)
                                          for k, v in value.items()) + "\n  }"
        else:
            rendered = json.dumps(value, ensure_ascii=False, indent=2).replace("\n", "\n  ")
        fields.append("  " + compact(key) + ": " + rendered)
    return "{\n" + ",\n".join(fields) + "\n}\n"


def _document(document: dict, view: KnowledgeView, pin: str, problems: list[str], label: str) -> dict:
    raw = view.read_text(document["path"])
    sections = {row["facet"]: row for row in depth_sections(raw)}
    content = document["content"]
    included = document["included_facets"]
    available = document["available_facets"]
    expected = set(sections)
    if set(available) != expected or len(available) != len(expected) or len(set(included)) != len(included):
        problems.append(f"{label}: delivered facet metadata differs from the intact page")
    if not set(included) <= expected:
        problems.append(f"{label}: included facets are not available")
    if document.get("facet_basis") != {facet: row["basis"] for facet, row in sections.items()}:
        problems.append(f"{label}: delivered basis differs from the intact page")
    if document.get("included_facet_basis") != {facet: sections[facet]["basis"] for facet in included if facet in sections}:
        problems.append(f"{label}: delivered injected basis differs from the actual included facets")
    if document.get("verified_gaps") != {facet: row["gap_label"] for facet, row in sections.items() if row["gap_label"]}:
        problems.append(f"{label}: delivered gap labels differ from the intact page")
    modes = {facet: row["acceptance_mode"] for facet, row in sections.items()}
    kinds = {facet: row["validation_kind"] for facet, row in sections.items() if row["validation_kind"]}
    if "facet_acceptance_modes" in document or "lightweight" in modes.values():
        if document.get("facet_acceptance_modes") != modes or document.get("included_facet_acceptance_modes") != {
                facet: modes[facet] for facet in included if facet in modes}:
            problems.append(f"{label}: acceptance modes differ from available or injected facets")
    if "validation_kinds" in document or kinds:
        if document.get("validation_kinds") != kinds or document.get("included_validation_kinds") != {
                facet: kinds[facet] for facet in included if facet in kinds}:
            problems.append(f"{label}: validation types differ from available or injected facets")
    if document.get("not_injected_facets") != [facet for facet in available if facet not in included]:
        problems.append(f"{label}: uninjected facet metadata differs from selection")
    missing = [facet for facet in FACETS if facet not in expected] if document["feature"] else []
    if document["missing_facets"] != missing:
        problems.append(f"{label}: missing facet metadata differs from the intact page")
    if len(content) > 3000:
        problems.append(f"{label}: document exceeds 3000 characters")
    if any(row["pin"] != pin for row in sections.values()):
        problems.append(f"{label}: served depth has another source pin")
    # A clipped snippet truthfully advertises no *intact* included facet. Bind
    # its actual prose to one frozen section instead of inferring absence from
    # included_facets=[] or accepting the partial flag without reading content.
    fragment = content.rstrip()
    partial_candidates = [facet for facet, section in sections.items()
                          if document.get("partial") is True and fragment.strip()
                          and len(fragment) < len(section["content"].strip())
                          and section["content"].strip().startswith(fragment)]
    partial_facet = partial_candidates[0] if len(partial_candidates) == 1 else None
    if len(partial_candidates) > 1:
        problems.append(f"{label}: partial context cannot be attributed to one intact facet")
    facet_states = {}
    for facet in FACETS:
        section = sections.get(facet)
        injection = "not_injected"
        if facet in included and section:
            if section["content"].strip() in content:
                injection = "full"
            elif content.strip() and len(included) == 1 and section["content"].strip().startswith(content.rstrip()):
                injection = "partial"
            else:
                problems.append(f"{label}: declared injected facet {facet} is absent from actual content")
        elif facet == partial_facet:
            injection = "partial"
        facet_states[facet] = {"status": section["basis"] if section else "unknown", "injection": injection,
                               "gap_label": section["gap_label"] if section else None}
    return {**document, "content_sha256": _hash(content), "page_sha256": _hash(raw),
            "content_chars": len(content), "facet_states": facet_states}


def audit_retrieval(root: Path, repo: str, pin: str, *, require_depth: bool = False) -> dict:
    if not re.fullmatch(r"[0-9a-f]{40}", pin):
        raise ValueError("retrieval audit requires a full pinned source SHA")
    root = root.resolve()
    knowledge = root / "knowledge"
    manifest = yaml.safe_load((root / f"adapters/{repo}/manifest.yaml").read_text())
    repo_dir = manifest["knowledge"]["repo_subdir"]
    policy_file = root / policy_path(repo)
    policy_text = policy_file.read_text()
    policy = load_policy(policy_text, repo_dir)
    frozen = build_manifest(knowledge, "depth-retrieval-audit")
    view = KnowledgeView(root=knowledge, snapshot=f"depth-retrieval-audit-{frozen['tree_sha256']}", files=frozen["files"])
    cases, problems, feature_status = [], [], {}
    for feature in policy.features:
        page = depth_page(feature)
        rows = depth_sections(view.read_text(page)) if page in view.files else []
        rows = [row for row in rows if row["feature"] == feature.id]
        available = {row["facet"]: row["basis"] for row in rows}
        feature_status[feature.id] = {"page": page, "entry_points": list(feature.entry_points),
                                     "facets": {facet: available.get(facet, "unknown") for facet in FACETS}}
        if require_depth and not available:
            problems.append(f"{feature.id}: no intact depth available")
        for probe in PROBES:
            changed = list(feature.entry_points) if probe != "query_only" else []
            title = f"{feature.title} {feature.id}" if probe != "paths_only" else ""
            plan = direct_review_plan(repo_dir.removeprefix("repos/"), title=title, changed_files=changed, view=view)
            related = plan["related_knowledge"]
            label = f"{feature.id}/{probe}"
            documents = [_document(d, view, pin, problems, label) for d in related["documents"]]
            if any(not d["path"].startswith(repo_dir + "/") for d in documents):
                problems.append(f"{label}: automatic context escaped the selected repository")
            actual_chars = sum(len(d["content"]) for d in documents)
            if len(documents) > 2 or actual_chars > 6000 or actual_chars != related["content_chars"]:
                problems.append(f"{label}: actual context violates the two-page/6000-character contract")
            if len({d["feature"] or d["path"] for d in documents}) != len(documents):
                problems.append(f"{label}: duplicate feature selected")
            hit = next((d for d in documents if d["feature"] == feature.id), None)
            delivered_depth = bool(hit and any(s["injection"] != "not_injected" for s in hit["facet_states"].values()))
            if probe != "paths_only" and (not hit or (available and (hit["path"] != page or not delivered_depth))):
                problems.append(f"{label}: feature depth absent from actual Direct context")
            followups = plan["navigation_policy"]["related_document_read_paths"]
            if followups != [d["path"] for d in documents if d["more_available"]]:
                problems.append(f"{label}: followup paths differ from the selected incomplete documents")
            cases.append({"feature": feature.id, "probe": probe, "changed_files": changed, "query": title,
                          "feature_hit": bool(hit), "depth_hit": delivered_depth,
                          "content_chars": actual_chars, "documents": documents,
                          "followup_read_paths": followups, "execution_budget": plan["execution_budget"],
                          "facet_injection": {facet: hit["facet_states"][facet]["injection"] if hit else "not_injected"
                                              for facet in FACETS}})
    if build_manifest(knowledge, frozen["snapshot"])["files"] != frozen["files"] or policy_file.read_text() != policy_text:
        problems.append("knowledge or policy changed during the frozen retrieval audit")
    statuses = ("supported", "verified_absent", "unknown")
    summary = {"total_features": len(policy.features), "total_facets": len(policy.features) * len(FACETS),
               "features_with_intact_depth": sum(any(s != "unknown" for s in f["facets"].values()) for f in feature_status.values()),
               "available_facet_status": {s: sum(status == s for f in feature_status.values() for status in f["facets"].values())
                                          for s in statuses}, "probes": {}}
    for probe in PROBES:
        selected = [case for case in cases if case["probe"] == probe]
        summary["probes"][probe] = {"cases": len(selected), "feature_hits": sum(c["feature_hit"] for c in selected),
            "depth_hits": sum(c["depth_hit"] for c in selected),
            "max_documents": max((len(c["documents"]) for c in selected), default=0),
            "max_content_chars": max((c["content_chars"] for c in selected), default=0),
            "target_feature_injection": {s: sum(state == s for c in selected for state in c["facet_injection"].values())
                                         for s in ("full", "partial", "not_injected")}}
    return {"summary": summary, "problems": problems, "features": feature_status, "cases": cases,
            "provenance": {"source_pin": pin, "policy_sha256": _hash(policy_text),
                           "knowledge_tree_sha256": view.tree_sha256, "snapshot_files": len(view.files)},
            "limits": "Statuses describe intact served metadata, not independent source/native approval. "
                      "Full and partial injection are counted separately from available knowledge. "
                      "Paths-only misses are diagnostic when entry points overlap. Catalog delivery does not "
                      "establish PR bug recall, review quality, verified behavior or passing tests."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pin", required=True)
    parser.add_argument("--snapshot-commit", help="Full commit SHA identifying the caller's read-only Git export")
    parser.add_argument("--require-depth", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.snapshot_commit and not re.fullmatch(r"[0-9a-f]{40}", args.snapshot_commit):
        parser.error("snapshot commit must be a full SHA")
    if args.report and args.report.resolve().is_relative_to((args.root / "knowledge").resolve()):
        parser.error("retrieval evidence belongs outside product knowledge")
    report = audit_retrieval(args.root, args.repo, args.pin, require_depth=args.require_depth)
    if args.snapshot_commit:
        report["provenance"]["declared_snapshot_commit"] = args.snapshot_commit
        report["notes"] = ["The caller identifies this read-only Git export with declared_snapshot_commit; "
                           "the audit independently binds its actual files with knowledge_tree_sha256."]
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(serialize_report(report))
    print(json.dumps({"summary": report["summary"], "problems": report["problems"]}, ensure_ascii=False, indent=2))
    return int(bool(report["problems"]))


if __name__ == "__main__":
    raise SystemExit(main())
