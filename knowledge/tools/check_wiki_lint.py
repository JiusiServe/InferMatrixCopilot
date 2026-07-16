#!/usr/bin/env python3
"""检查沉淀层页面的 frontmatter、标签分类法、孤页与陈旧度（SCHEMA.md 机制）。

范围：general/ 与 repos/ 下的沉淀层页面。证据层（incidents/、history/、
results/）、repos/jianghan-roleplay-data-pipeline/ 与 _archive/ 不检查。
结构/索引/链接/错题校验属于 check_knowledge_tree.py，这里不重复。
"""

from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "SCHEMA.md"
SYNTH_ROOTS = (ROOT / "general", ROOT / "repos")
RAW_PARTS = {"incidents", "history", "results"}
SKIP_PARTS = {"_archive"}
SKIP_SUBTREES = (ROOT / "repos" / "jianghan-roleplay-data-pipeline",)
TYPES = {"rule", "guide", "architecture", "index"}
CONFIDENCE = {"high", "medium", "low"}
REQUIRED = ("title", "created", "updated", "type", "tags")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
STALE_DAYS = 365

errors: list[str] = []
warnings: list[str] = []


def display(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def taxonomy() -> set[str]:
    """SCHEMA.md 标签分类法：分类法小节里所有反引号 token。"""
    text = SCHEMA.read_text(encoding="utf-8")
    m = re.search(r"## 标签分类法(.*?)\n## ", text, re.DOTALL)
    if not m:
        errors.append("SCHEMA.md 缺少 ## 标签分类法 小节")
        return set()
    return set(re.findall(r"`([^`]+)`", m.group(1)))


def synthesized_pages() -> list[Path]:
    pages = []
    for root in SYNTH_ROOTS:
        for p in sorted(root.rglob("*.md")):
            parts = set(p.relative_to(ROOT).parts)
            if parts & RAW_PARTS or parts & SKIP_PARTS:
                continue
            if any(p.is_relative_to(s) for s in SKIP_SUBTREES):
                continue
            pages.append(p)
    return pages


def frontmatter(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8-sig")
    if not text.startswith("---"):
        return None
    try:
        _, fm, _ = text.split("---", 2)
        meta = yaml.safe_load(fm)
    except (ValueError, yaml.YAMLError):
        return None
    return meta if isinstance(meta, dict) else None


def check_page(path: Path, tags_allowed: set[str]) -> dict | None:
    meta = frontmatter(path)
    if meta is None:
        errors.append(f"沉淀层页面缺少 frontmatter：{display(path)}")
        return None
    for field in REQUIRED:
        if field not in meta:
            errors.append(f"frontmatter 缺少字段 {field}：{display(path)}")
    if meta.get("type") not in TYPES:
        errors.append(f"type 不合法（{meta.get('type')}）：{display(path)}")
    for d in ("created", "updated"):
        v = str(meta.get(d, ""))
        if not DATE.match(v):
            errors.append(f"{d} 不是 YYYY-MM-DD（{v}）：{display(path)}")
    tags = meta.get("tags") or []
    if not isinstance(tags, list) or not tags:
        errors.append(f"tags 缺失或为空：{display(path)}")
    else:
        for t in tags:
            if t not in tags_allowed:
                errors.append(f"标签不在 SCHEMA 分类法中（{t}）：{display(path)}")
    if "confidence" in meta and meta["confidence"] not in CONFIDENCE:
        errors.append(f"confidence 不合法（{meta['confidence']}）：{display(path)}")
    if meta.get("confidence") == "low" or meta.get("contested"):
        warnings.append(f"待复核（confidence: low / contested）：{display(path)}")
    return meta


def inbound_links() -> set[Path]:
    """全树（含证据层）Markdown 链接指向的目标集合。"""
    targets: set[Path] = set()
    for p in ROOT.rglob("*.md"):
        if ".git" in p.parts:
            continue
        in_fence = False
        for line in p.read_text(encoding="utf-8-sig").splitlines():
            s = line.lstrip()
            if s.startswith(("```", "~~~")):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for m in MARKDOWN_LINK.finditer(line):
                t = m.group(1).split("#", 1)[0].strip()
                if t and not t.startswith(("http://", "https://", "mailto:")):
                    targets.add((p.parent / t).resolve())
    return targets


def main() -> int:
    tags_allowed = taxonomy()
    pages = synthesized_pages()
    today = datetime.date.today()
    linked = inbound_links()
    for p in pages:
        meta = check_page(p, tags_allowed)
        if meta is None:
            continue
        updated = str(meta.get("updated", ""))
        if DATE.match(updated):
            age = (today - datetime.date.fromisoformat(updated)).days
            if age > STALE_DAYS:
                warnings.append(f"超过 {STALE_DAYS} 天未更新：{display(p)}")
        if p.name != "_index.md" and p.resolve() not in linked:
            warnings.append(f"孤页（没有任何入链）：{display(p)}")

    for message in warnings:
        print(f"提醒：{message}")
    for message in errors:
        print(f"错误：{message}")
    if errors:
        print(f"wiki lint 失败：{len(errors)} 个错误，{len(warnings)} 个提醒")
        return 1
    print(f"wiki lint 通过：0 个错误，{len(warnings)} 个提醒（共 {len(pages)} 页）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
