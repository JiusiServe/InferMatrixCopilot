#!/usr/bin/env python3
"""Audit (and optionally add source contracts to) a pinned knowledge slice."""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import subprocess
from pathlib import Path, PurePosixPath

from infermatrix_copilot.kb_service.init_coverage import owner_table
from infermatrix_copilot.kb_service.init_stages import _page_frontmatter
from infermatrix_copilot.kb_service.knowledge_coverage import add_contract_pages, audit_coverage, load_policy, policy_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--pin", required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--report", type=Path)
    parser.add_argument("--write-contracts", action="store_true")
    args = parser.parse_args()
    current = subprocess.check_output(["git", "-C", str(args.upstream), "rev-parse", "HEAD"], text=True).strip()
    if current != args.pin or len(args.pin) != 40:
        parser.error("upstream HEAD must equal the full requested pin")
    if subprocess.check_output(["git", "-C", str(args.upstream), "status", "--porcelain", "--untracked-files=no"], text=True):
        parser.error("upstream tracked files must be clean at the pin")
    import yaml

    manifest = yaml.safe_load((args.root / f"adapters/{args.repo}/manifest.yaml").read_text())
    repo_dir = manifest["knowledge"]["repo_subdir"]
    policy = load_policy((args.root / policy_path(args.repo)).read_text(), repo_dir)
    knowledge = args.root / "knowledge"
    head = {p.relative_to(knowledge).as_posix(): p.read_text() for p in (knowledge / repo_dir).rglob("*.md")}
    before = dict(head)
    routes = knowledge / repo_dir / "_routes.yaml"
    _, owners = owner_table(routes.read_text() if routes.exists() else None, manifest)

    def link_page(page: str, title: str) -> None:
        directory = PurePosixPath(page).parent
        while str(directory).startswith(repo_dir):
            index = str(directory / "_index.md")
            if index not in head:
                head[index] = (_page_frontmatter(directory.name, kind="index", today=today, tags=[args.repo])
                               + "理解本 owner 的源码职责、接口和集成边界时查这里。源码接口记录是静态契约；功能语义、配置和取舍沿功能页查证。通用审查方法不放在这里。\n")
            relative = posixpath.relpath(page, str(directory))
            if f"]({relative})" not in head[index]:
                head[index] = head[index].rstrip() + f"\n- [{title}]({relative})\n"
            if str(directory) == repo_dir:
                break
            page, title = index, directory.name
            directory = directory.parent

    full_name = manifest["repo"]["full_name"]
    from datetime import date

    today = date.today().isoformat()
    if args.write_contracts:
        add_contract_pages(head, args.upstream, policy, owners, repo_dir=repo_dir, full_name=full_name,
                           pin=args.pin, today=today, tags=[args.repo], link_page=link_page)
        for path, text in head.items():
            if before.get(path) != text:
                target = knowledge / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text)
    report = audit_coverage(head, args.upstream, policy, full_name=full_name, pin=args.pin)
    report["provenance"] = {
        "policy_sha256": hashlib.sha256((args.root / policy_path(args.repo)).read_bytes()).hexdigest(),
        "knowledge_sha256": hashlib.sha256(json.dumps(head, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
        "upstream_tracked_files_clean": True,
        "reproduce": f"PYTHONPATH=src python tools/audit_knowledge_coverage.py --repo {args.repo} "
                     f"--upstream /path/to/pinned/{args.repo} --pin {args.pin}",
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"targets_met": report["met"], "features": {k: report["features"][k] for k in ("covered", "total")},
                      "core": {k: report["core"][k] for k in ("covered", "total", "ratio", "target", "contract_files")}}, indent=2))
    return 0 if report["met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
