"""Preserving Markdown import, stable tracking sidecars, and deterministic views."""
from __future__ import annotations

import hashlib
import re
from typing import Any

from .models import RFCError


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def draft(title: str, goal: str, scope: str = "") -> str:
    return (f"# RFC: {title}\n\n## 问题与目标\n\n{goal}\n\n## 范围\n\n{scope or '待明确：包含与排除的范围。'}\n\n"
            "## 事实与依据\n\n- 待补充：仓库路径、issue、PR 与测量证据。\n\n"
            "## 备选方案\n\n- 待比较：方案、成本与取舍。\n\n## 提议设计\n\n待补充设计与接口边界。\n\n"
            "## 工作计划\n\n### 实现\n\n#### F1. 核心实现\n\n负责人：待确认\n\n"
            "#### F2. 集成与验证\n\n依赖：F1\n\n## 验收标准\n\n"
            "- 用户目标得到验证，并记录验证版本与环境。\n- 必需测试通过，负责人确认验收。\n\n"
            "## 风险与未决问题\n\n- 待明确：兼容性、回滚和未决设计。\n")


def parse(body: str, previous: dict | None = None) -> dict[str, Any]:
    previous = previous or {}
    old = {f["id"]: f for f in previous.get("features", [])}
    features: list[dict] = []
    track, current = "实现", None
    outside = re.sub(r"```[\s\S]*?```", "", body)
    seen: set[str] = set()
    criteria: list[dict] = []
    criterion_section = False
    criterion_depth = 0
    for line in outside.splitlines():
        heading = re.match(r"^(#{2,6})\s+(.+)$", line)
        if heading:
            level, text = len(heading[1]), heading[2].strip()
            if any(x in text.casefold() for x in ("验收", "acceptance criteria")):
                criterion_section, criterion_depth = True, level
            elif criterion_section and level <= criterion_depth:
                criterion_section = False
            if level == 3:
                track = text
            feature = re.match(r"([A-Za-z][A-Za-z0-9_-]*)[.、:]\s*(.+)", text) if level >= 3 else None
            if feature:
                key, title = feature.groups()
                if key in seen:
                    raise RFCError("Duplicate feature identifier")
                seen.add(key)
                prior = old.get(key, {})
                current = {**prior, "id": key, "title": title, "track": track,
                           "depends_on": [], "links": prior.get("links", []),
                           "owner": prior.get("owner", ""), "state": prior.get("state", "planned"),
                           "source_quote": line, "dropped": prior.get("dropped", False)}
                features.append(current)
            elif level <= 3:
                current = None
        if current:
            if re.search(r"<!--\s*feature-status\s*-->\s*\*\*Status:\s*complete\*\*", line, re.I):
                current["state"] = "implemented"
                current["implementation_claim"] = {"source_quote": line.strip(), "source_revision": digest(body),
                                                   "provenance": "imported_explicit_milestone"}
            dep = re.search(r"(?:依赖|depends\s+on|requires)\s*[：:]?\s*(.+)", line, re.I)
            if dep:
                current["depends_on"] += re.findall(r"\b[A-Za-z][A-Za-z0-9_-]*\d[A-Za-z0-9_-]*\b", dep[1])
            owner = re.search(r"(?:负责人|owner)\s*[：:]\s*(.+)", line, re.I)
            if owner and "待" not in owner[1]:
                current["owner"] = owner[1].strip()
            for url in re.findall(r"https?://[^\s)<>]+", line):
                if url not in current["links"]:
                    current["links"].append(url)
        if criterion_section:
            item = re.match(r"\s*[-*]\s+(?:\[[ xX]\]\s*)?(.+)", line)
            if item:
                key = "C-" + digest(item[1])[:12]
                prior = next((c for c in previous.get("criteria", []) if c["id"] == key), {})
                criteria.append({"id": key, "title": item[1], "verdict": prior.get("verdict", "unverified"),
                                 "evidence": prior.get("evidence", []), "reason": prior.get("reason", "")})
    if not features:
        for text in re.findall(r"^\s*[-*]\s+\[[ xX]\]\s+(.+)$", outside, re.M):
            key = "F-" + digest(text)[:12]
            if key in seen:
                continue
            seen.add(key)
            features.append({"id": key, "title": text, "track": "工作", "depends_on": [], "links": [],
                             "owner": "", "state": "planned", "source_quote": text, "dropped": False})
    # Resolve bare PR references through canonical links elsewhere in the RFC,
    # including live-status tables. An issue or documentation URL is no PR fact.
    pr_links = {number: url for url, number in re.findall(
        r"(https?://[^\s)<>]+/(?:pull|pulls)/([1-9][0-9]*))", body)}
    sections = re.split(r"(?=^#{3,6}\s+[A-Za-z][A-Za-z0-9_-]*[.、:]\s)", outside, flags=re.M)
    for section in sections:
        match = re.match(r"^#{3,6}\s+([A-Za-z][A-Za-z0-9_-]*)[.、:]", section)
        target = next((f for f in features if match and f["id"] == match[1]), None)
        if target:
            for number in re.findall(r"(?<![\w/])#([1-9][0-9]*)\b", section):
                if number in pr_links and pr_links[number] not in target["links"]:
                    target["links"].append(pr_links[number])
    available = {f["id"] for f in features}
    for graph in re.findall(r"```mermaid\s*\n([\s\S]*?)```", body):
        for left, right in re.findall(r"\b([A-Za-z][A-Za-z0-9_-]*)\s*(?:-->|-\.->|==>)\s*([A-Za-z][A-Za-z0-9_-]*)\b", graph):
            if left in available and right in available:
                next(f for f in features if f["id"] == right)["depends_on"].append(left)
    for feature in features:
        feature.update(feature.get("overrides", {}))
        feature["depends_on"] = list(dict.fromkeys(feature["depends_on"]))
    # Existing sidecar additions survive unrelated human prose edits.
    for prior in old.values():
        if prior.get("sidecar") and prior["id"] not in seen:
            features.append(prior)
    ambiguities = []
    available = {f["id"] for f in features}
    for feature in features:
        unresolved = [d for d in feature["depends_on"] if d not in available]
        if unresolved:
            ambiguities.append({"feature_id": feature["id"], "unknown_dependencies": unresolved})
            feature["unresolved_dependencies"] = unresolved
            feature["depends_on"] = [d for d in feature["depends_on"] if d in available]
    validate_features(features)
    return {**previous, "features": features, "criteria": previous.get("criteria", []) if previous.get("criteria_override") else criteria or previous.get("criteria", []),
            "source_digest": digest(body), "state": previous.get("state", "draft"),
            "suggestions": previous.get("suggestions", []), "tombstones": previous.get("tombstones", []),
            "freshness": previous.get("freshness", {}), "scope": previous.get("scope", ""),
            "auto_add": previous.get("auto_add", True), "max_auto_additions": previous.get("max_auto_additions", 5),
            "ambiguities": ambiguities}


def validate_features(features: list[dict]) -> None:
    ids = [f.get("id", "") for f in features]
    if any(not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,79}", key) for key in ids) or len(set(ids)) != len(ids):
        raise RFCError("Feature identifiers must be unique and portable")
    graph = {f["id"]: f.get("depends_on", []) for f in features}
    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(key: str) -> None:
        if key not in graph:
            raise RFCError("Unknown feature dependency")
        if key in visiting:
            raise RFCError("Dependency cycle")
        if key in visited:
            return
        visiting.add(key)
        for dep in graph[key]:
            visit(dep)
        visiting.remove(key)
        visited.add(key)
    for key in graph:
        visit(key)


def project(model: dict) -> dict:
    features = [f for f in model.get("features", []) if not f.get("dropped")]
    observations = model.get("observations", {})
    for feature in features:
        states = [observations.get(link, {}).get("state", "unknown") for link in feature.get("links", [])
                  if observations.get(link, {}).get("kind") in ("pr", "pull", "pull_request")]
        if states:
            feature["implementation"] = ("implemented" if all(s == "merged" for s in states)
                                          else "partial" if "merged" in states else "in_progress")
        else:
            feature["implementation"] = feature.get("state", "planned")
    criteria = model.get("criteria", [])
    acceptance = ("accepted" if criteria and all(c.get("verdict") in ("passing", "waived") for c in criteria)
                  else "failing" if any(c.get("verdict") == "failing" for c in criteria) else "pending")
    implemented = bool(features) and all(f.get("implementation") == "implemented" for f in features)
    next_actions = [f"验证：{c['title']}" for c in criteria if c.get("verdict") not in ("passing", "waived")]
    for feature in features:
        unresolved = [dep for dep in feature.get("depends_on", [])
                      if next((f.get("implementation") for f in features if f["id"] == dep), None) != "implemented"]
        unresolved += feature.get("unresolved_dependencies", [])
        feature["blockers"] = unresolved
        applicable = [c for c in criteria if not c.get("feature_ids") or feature["id"] in c["feature_ids"]]
        feature["acceptance"] = "accepted" if applicable and all(c.get("verdict") in ("passing", "waived") for c in applicable) else "pending"
        feature["complete"] = feature["implementation"] == "implemented" and feature["acceptance"] == "accepted"
        if unresolved:
            next_actions.append(f"{feature['id']} 等待：{', '.join(unresolved)}")
        elif feature["implementation"] != "implemented":
            next_actions.append(f"推进 {feature['id']}：{feature['title']}")
    for ambiguity in model.get("ambiguities", []):
        next_actions.append(f"审阅 {ambiguity['feature_id']} 的未解析依赖")
    if not features:
        next_actions.append("补充可跟踪的工作拆分")
    return {**model, "implementation": "implemented" if implemented else "partial" if any(
        f.get("implementation") in ("implemented", "partial") for f in features) else "planned",
        "acceptance": acceptance, "next_actions": next_actions,
        "complete": implemented and acceptance == "accepted"}
