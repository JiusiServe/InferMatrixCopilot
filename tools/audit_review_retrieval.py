#!/usr/bin/env python3
"""Offline acceptance for bounded review retrieval, separate from KB coverage."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import yaml

from infermatrix_copilot.direct_routing import direct_review_plan
from infermatrix_copilot.kb_service.knowledge_coverage import load_policy, policy_path
from infermatrix_copilot.kb_service.knowledge_depth import depth_page
from infermatrix_copilot.knowledge_service.lifecycle import depth_sections
from infermatrix_copilot.knowledge_view import KnowledgeView


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    knowledge = root / "knowledge"
    if args.report and args.report.resolve().is_relative_to(knowledge):
        parser.error("acceptance reports belong outside product knowledge")
    manifest = yaml.safe_load((root / f"adapters/{args.repo}/manifest.yaml").read_text())
    policy_file = root / policy_path(args.repo)
    policy = load_policy(policy_file.read_text(), manifest["knowledge"]["repo_subdir"])
    files = {p.relative_to(knowledge).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in knowledge.rglob("*") if p.is_file() and p.suffix in (".md", ".yaml", ".yml")}
    view = KnowledgeView(root=knowledge, snapshot="audit", files=files)
    cases, problems = [], []
    for feature in policy.features:
        path = knowledge / depth_page(feature)
        expected_depth = bool(path.exists() and depth_sections(path.read_text()))
        for probe in ("description_and_paths", "paths_only"):
            started = time.perf_counter()
            plan = direct_review_plan(args.repo, title=f"{feature.title} {feature.id}" if probe == "description_and_paths" else "",
                                      changed_files=list(feature.entry_points), view=view)
            related = plan["related_knowledge"]
            documents = related["documents"]
            hit = next((d for d in documents if d["feature"] == feature.id), None)
            passed = bool(hit and (not expected_depth or hit["included_facets"]))
            if probe == "description_and_paths" and not passed:
                problems.append(f"{feature.id}: expected feature explanation absent from Direct context")
            if len(documents) > 2 or related["content_chars"] > 6000:
                problems.append(f"{feature.id}: context bound exceeded")
            cases.append({"feature": feature.id, "probe": probe, "changed_files": list(feature.entry_points),
                          "expected_depth": expected_depth, "feature_hit": bool(hit),
                          "depth_hit": bool(hit and hit["included_facets"]),
                          "content_chars": related["content_chars"],
                          "elapsed_ms": round((time.perf_counter() - started) * 1000),
                          "extra_read_paths": plan["navigation_policy"]["related_document_read_paths"],
                          "documents": [{k: d[k] for k in ("path", "feature", "match_reason", "source_pins",
                                                               "included_facets", "available_facets", "missing_facets")}
                                        for d in documents]})
    summary = {probe: {"cases": len(rows), "feature_hits": sum(c["feature_hit"] for c in rows),
                       "depth_hits": sum(c["depth_hit"] for c in rows),
                       "expected_depth": sum(c["expected_depth"] for c in rows),
                       "max_content_chars": max((c["content_chars"] for c in rows), default=0),
                       "median_elapsed_ms": sorted(c["elapsed_ms"] for c in rows)[len(rows) // 2] if rows else 0}
               for probe in ("description_and_paths", "paths_only")
               if (rows := [c for c in cases if c["probe"] == probe])}
    report = {"summary": summary, "problems": problems, "cases": cases,
              "provenance": {"knowledge_tree_sha256": view.tree_sha256,
                             "policy_sha256": hashlib.sha256(policy_file.read_bytes()).hexdigest()},
              "limits": "Catalog probes test context delivery, not real PR bug recall or review quality. "
                        "Paths-only probes are diagnostic when multiple features share entry points. "
                        "Intact depth prose does not revalidate upstream source or the PR head."}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"summary": summary, "problems": problems}, ensure_ascii=False, indent=2))
    return int(bool(problems))


if __name__ == "__main__":
    raise SystemExit(main())
