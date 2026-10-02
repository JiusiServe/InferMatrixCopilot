#!/usr/bin/env python3
"""Recompute semantic depth and breadth independently at a clean upstream pin."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import yaml

from infermatrix_copilot.kb_service.knowledge_coverage import audit_coverage, load_policy, policy_path
from infermatrix_copilot.kb_service.knowledge_depth import audit_depth


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--pin", required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
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
    head = {p.relative_to(knowledge).as_posix(): p.read_text() for p in (knowledge / repo_dir).rglob("*.md")}
    report = {"semantic_depth": audit_depth(head, args.upstream, policy, args.pin),
              "breadth": audit_coverage(head, args.upstream, policy, full_name=manifest["repo"]["full_name"], pin=args.pin),
              "provenance": {
                  "policy_sha256": hashlib.sha256(policy_file.read_bytes()).hexdigest(),
                  "knowledge_sha256": hashlib.sha256(json.dumps(head, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
                  "upstream_tracked_files_clean": True,
                  "reproduce": f"PYTHONPATH=src python tools/audit_knowledge_depth.py --repo {args.repo} "
                               f"--upstream /path/to/pinned/{args.repo} --pin {args.pin}"}}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    depth = report["semantic_depth"]
    print(json.dumps({"depth": {k: depth[k] for k in ("complete_features", "total_features", "covered_facets", "total_facets")},
                      "production_files_with_semantic_evidence": len(depth["production_files_with_semantic_evidence"]),
                      "breadth_targets_met": report["breadth"]["met"], "problems": depth["problems"]}, indent=2))
    return 1 if depth["problems"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
