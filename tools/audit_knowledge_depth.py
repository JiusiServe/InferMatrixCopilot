#!/usr/bin/env python3
"""Recompute semantic depth and breadth independently at a clean upstream pin."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import yaml

from infermatrix_copilot.kb_service.knowledge_coverage import audit_coverage, coverage_targets_met, load_policy, policy_path
from infermatrix_copilot.kb_service.knowledge_depth import audit_depth


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--pin", required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--report", type=Path)
    parser.add_argument("--approval-report", type=Path, action="append",
                        help="Repeatable native all-yes block binding report, outside product knowledge")
    parser.add_argument("--require-approvals", action="store_true",
                        help="Fail unless every recognized block has a matching native all-yes approval")
    parser.add_argument("--foundation-mode", choices=("strict", "partial"), default="strict")
    parser.add_argument("--foundation-record", type=Path)
    args = parser.parse_args()
    if args.foundation_mode == "partial" and (not args.foundation_record or not args.require_approvals):
        parser.error("partial foundation requires --foundation-record and --require-approvals")
    if args.foundation_mode == "strict" and args.foundation_record:
        parser.error("--foundation-record requires --foundation-mode partial")
    current = subprocess.check_output(["git", "-C", str(args.upstream), "rev-parse", "HEAD"], text=True).strip()
    if current != args.pin or len(args.pin) != 40:
        parser.error("upstream HEAD must equal the full requested pin")
    if subprocess.check_output(["git", "-C", str(args.upstream), "status", "--porcelain", "--untracked-files=no"], text=True):
        parser.error("upstream tracked files must be clean at the pin")
    knowledge = args.root / "knowledge"
    if args.report and args.report.resolve().is_relative_to(knowledge.resolve()):
        parser.error("reports belong in eval or local state, outside product knowledge")
    manifest = yaml.safe_load((args.root / f"adapters/{args.repo}/manifest.yaml").read_text())
    repo_dir = manifest["knowledge"]["repo_subdir"]
    policy_file = args.root / policy_path(args.repo)
    policy = load_policy(policy_file.read_text(), repo_dir)
    if args.require_approvals and not args.approval_report:
        parser.error("--require-approvals requires at least one --approval-report")
    approvals = [] if args.approval_report else None
    for path in args.approval_report or []:
        data = json.loads(path.read_text())
        rows = data.get("approvals", data.get("native_execution", {}).get("approvals")) if isinstance(data, dict) else None
        if not isinstance(rows, list):
            parser.error("each approval report must contain an approvals list")
        approvals.extend(rows)
    head = {p.relative_to(knowledge).as_posix(): p.read_text() for p in (knowledge / repo_dir).rglob("*.md")}
    report = {"semantic_depth": audit_depth(head, args.upstream, policy, args.pin, approvals=approvals),
              "breadth": audit_coverage(head, args.upstream, policy, full_name=manifest["repo"]["full_name"], pin=args.pin),
              "provenance": {
                  "policy_sha256": hashlib.sha256(policy_file.read_bytes()).hexdigest(),
                  "knowledge_sha256": hashlib.sha256(json.dumps(head, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
                  "upstream_tracked_files_clean": True,
                  "native_approval_reports": [{"name": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                                              for p in args.approval_report or []],
                  "reproduce": f"PYTHONPATH=src python tools/audit_knowledge_depth.py --repo {args.repo} "
                               f"--upstream /path/to/pinned/{args.repo} --pin {args.pin}"}}
    if args.foundation_mode == "partial":
        from infermatrix_copilot.kb_service.foundation_publication import foundation_handoff
        from infermatrix_copilot.kb_service.sources import KnowledgeRepo
        knowledge_repo = KnowledgeRepo(args.root)
        baseline = knowledge_repo._git("rev-parse", "HEAD").decode().strip()
        report["foundation_mode"] = "partial"
        report["foundation"] = foundation_handoff(args.foundation_record, knowledge=knowledge_repo,
                    baseline=baseline, repo=args.repo, pin=args.pin)
        report["init_complete"] = False  # Final init includes its separate publication and retrieval gates.
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    depth = report["semantic_depth"]
    print(json.dumps({"depth": {k: depth[k] for k in ("complete_features", "total_features", "covered_facets", "total_facets")},
                      "recognized_facets": depth["recognized_facets"], "facet_counts": depth["facet_counts"],
                      "semantic_depth_target_met": depth["target_met"],
                      "approval_bindings_checked": depth["approval_bindings_checked"],
                      "approval_binding_problems": depth["approval_binding_problems"],
                      "production_files_with_semantic_evidence": len(depth["production_files_with_semantic_evidence"]),
                      "breadth_targets_met": report["breadth"]["met"],
                      "structural_targets_met": report["breadth"]["structural"]["met"], "problems": depth["problems"]}, indent=2))
    return 1 if depth["problems"] or depth["approval_binding_problems"] or not depth["target_met"] \
        or not coverage_targets_met(report["breadth"], args.foundation_mode) else 0


if __name__ == "__main__":
    raise SystemExit(main())
