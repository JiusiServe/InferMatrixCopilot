"""Stable audit units and deterministic selection over served knowledge.

An unchanged snapshot is still eligible. Content/pin identity, rather than a
page's edit date, determines whether an earlier semantic review is fresh.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import PurePosixPath
import re
import time
from types import SimpleNamespace

from ..knowledge_service.lifecycle import DEPTH_BLOCK, LifecycleError, Page

_KNOWLEDGE = re.compile(r"<!-- kb:knowledge owner=([a-z0-9-]+) facet=([a-z_]+) "
                        r"pin=([0-9a-f]{40}|[0-9a-f]{64})(?: verdict=\w+)? -->")
_PIN = re.compile(r"(?:/blob/|@)([0-9a-f]{64}|[0-9a-f]{40})(?=[:/])")
_LINK = re.compile(r"https?://[^\s)<>]+")


def _digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _uncovered_prose(text, occupied, frontmatter_length):
    """Ignore presentation/routing lines, retain any unstructured assertion."""
    end, parts = frontmatter_length, []
    for start, stop in sorted(occupied):
        if start > end:
            parts.append(text[end:start])
        end = max(end, stop)
    parts.append(text[end:])
    remaining = re.sub(r"<!--.*?-->", "", "\n".join(parts), flags=re.S)
    for line in remaining.splitlines():
        line = line.strip()
        if not line or re.fullmatch(r"#{1,6}\s+.*|[-*_]{3,}", line):
            continue
        if re.fullmatch(r"(?:[-*+]\s+)?\[[^]]+\]\([^)]*\)", line):
            continue
        if re.fullmatch(r"(?:(?:Source|Sources|来源):\s*)?(?:https?://\S+\s*)+", line, re.I):
            continue
        return True
    return False


def enumerate_units(files, lifecycle, snapshot):
    """Return rules, generated prose blocks, and otherwise legacy whole pages.

    ``unit_id`` is stable across snapshots; ``content_sha256`` and
    ``upstream_pin`` must also match before reusing an audit outcome.
    Malformed/duplicate rule identities remain visible and protected.
    """
    root = lifecycle.knowledge_dir.rstrip("/")
    units = []
    for path, text in sorted(files.items()):
        if not path.startswith(root + "/") or not path.endswith(".md"):
            continue
        parsed = Page.parse(text)
        try:
            metadata = parsed.frontmatter_data()
            page_sources = metadata.get("sources") or []
            if not isinstance(page_sources, list):
                page_sources = []
        except (LifecycleError, ValueError, TypeError):
            metadata = {}
            page_sources = []
        owner = str(PurePosixPath(path).parent)
        occupied, blocks = [], []
        offset = len(parsed.frontmatter) + len(parsed.head)
        counts = {}
        for section in parsed.sections:
            end = offset + len(section.text)
            if section.is_rule:
                counts[section.rule_id] = counts.get(section.rule_id, 0) + 1
                try:
                    footer = section.footer
                    active, protected = footer.status == "active", footer.protected
                    malformed = False
                except LifecycleError:
                    active, protected, malformed = True, True, True
                if active:
                    blocks.append((section.rule_id, "rule", section.text, protected, malformed))
                occupied.append((offset, end))
            offset = end
        for match in DEPTH_BLOCK.finditer(text):
            if not any(a <= match.start() < b for a, b in occupied):
                blocks.append((f"depth:{match[1]}:{match[2]}", "depth", match[0], False, False))
                occupied.append(match.span())
        markers = list(_KNOWLEDGE.finditer(text))
        for index, match in enumerate(markers):
            end = markers[index + 1].start() if index + 1 < len(markers) else len(text)
            # Foundation blocks end before a later generated depth block.
            end = min([end, *[a for a, _ in occupied if a > match.start()]])
            if not any(a <= match.start() < b for a, b in occupied):
                blocks.append((f"knowledge:{match[1]}:{match[2]}", "knowledge",
                               text[match.start():end], False, False))
                occupied.append((match.start(), end))
        if not blocks and not parsed.rules():
            blocks.append(("legacy:page", "legacy", text, False, False))
        elif _uncovered_prose(text, occupied, len(parsed.frontmatter)):
            # A factual introduction/non-rule section must remain auditable.
            # Whole-page correction on a structured owner page is human-only.
            blocks.append(("legacy:page", "legacy", text, True, False))
        seen = {}
        for block_id, kind, body, protected, malformed in blocks:
            seen[block_id] = seen.get(block_id, 0) + 1
            duplicate = seen[block_id] > 1 or (kind == "rule" and counts.get(block_id, 0) > 1)
            identity = block_id if seen[block_id] == 1 else f"{block_id}:duplicate:{seen[block_id]}"
            marker = re.search(r"<!-- kb:(?:depth|knowledge|file) [^>]*?\bpin=([0-9a-f]{64}|[0-9a-f]{40})(?=\s|\s*-->)", body)
            proof_sources = []
            proof = re.search(r"<!-- kb:depth-proof (.*?) -->", body, re.S)
            if proof and marker and getattr(lifecycle, "full_name", ""):
                try:
                    for span in json.loads(proof[1]).get("evidence", []):
                        proof_sources.append({"repository": lifecycle.full_name, "sha": marker[1],
                            "path": span["path"], "start": span["start"], "end": span["end"],
                            "content_sha256": span["sha256"]})
                except (ValueError, TypeError, KeyError, AttributeError):
                    proof_sources = []
            primary_keys = {json.dumps(source, sort_keys=True) for source in [*proof_sources, *_LINK.findall(body)]}
            page_keys = {json.dumps(source, sort_keys=True) for source in page_sources if isinstance(source, (str, dict))}
            sources, source_keys = [], set()
            for source in [*proof_sources, *_LINK.findall(body), *page_sources]:
                if not isinstance(source, (str, dict)):
                    continue
                path_hint = source if isinstance(source, str) else source.get("path", "")
                if str(path_hint).startswith(("repos/", "general/", "incidents/", "history/", "results/", "knowledge/")):
                    continue
                key = json.dumps(source, sort_keys=True)
                if key not in source_keys:
                    sources.append(source)
                    source_keys.add(key)
            primary_sources = [source for source in sources if json.dumps(source, sort_keys=True) in primary_keys]
            fallback_sources = [source for source in sources if json.dumps(source, sort_keys=True) in page_keys]
            applicability_sources = sources if kind == "legacy" else primary_sources or fallback_sources
            marker_pins = re.findall(r"<!-- kb:(?:depth|knowledge|file) [^>]*?\bpin=([0-9a-f]{64}|[0-9a-f]{40})(?=\s|\s*-->)", body)
            pins = [marker[1]] if marker and kind != "legacy" else sorted(set(marker_pins +
                _PIN.findall("\n".join(source for source in applicability_sources if isinstance(source, str)))
                + [source["sha"] for source in applicability_sources if isinstance(source, dict)
                   and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", str(source.get("sha", "")))]))
            # Risk is a selection hint, never an admission verdict. Structured
            # executable constraints precede unreviewed prose at equal age;
            # audit-only whole-page protection grants no severity by itself.
            risk = {"rule": 20, "depth": 10, "knowledge": 10}.get(kind, 0)
            risk_reasons = ["unit_kind_" + kind]
            if kind == "rule" and (protected or block_id in lifecycle.protected_rules):
                risk = max(risk, 40)
                risk_reasons.append("protected_constraint")
            impact = str(metadata.get("impact", "")).casefold()
            if impact in {"critical", "high", "medium", "low"}:
                risk += {"critical": 100, "high": 60, "medium": 20, "low": 0}[impact]
                risk_reasons.append("page_impact_" + impact)
            units.append({
                "unit_id": _digest("\0".join((lifecycle.repo, path, identity, kind))),
                "repo": lifecycle.repo, "owner": owner, "page": path,
                "block_id": identity, "kind": kind, "text": body,
                "content_sha256": _digest(body), "sources": sources[:64], "sources_truncated": len(sources) > 64,
                "primary_sources": primary_sources[:64], "page_sources": fallback_sources[:64],
                "upstream_pin": pins[0] if len(pins) == 1 else "", "upstream_pins": pins,
                "protected": bool(protected or duplicate or malformed or block_id in lifecycle.protected_rules),
                "snapshot": snapshot,
                "risk_score": risk, "risk_reasons": risk_reasons,
                "structural_issues": (["duplicate_block_id"] if duplicate else [])
                                     + (["malformed_rule_footer"] if malformed else []),
            })
    return sorted(units, key=lambda unit: unit["unit_id"])


def page_units(path, text, repo, snapshot="", protected_rules=()):
    """The same extraction for consumers checking one packaged/snapshot page."""
    lifecycle = SimpleNamespace(repo=repo, knowledge_dir="general" if repo == "general" else f"repos/{repo}",
                                protected_rules=protected_rules)
    return enumerate_units({path: text}, lifecycle, snapshot)


def fresh_history(unit, row):
    """A historical verdict never transfers to different content or source pin."""
    return bool(row and row.get("content_sha256") == unit["content_sha256"]
                and row.get("upstream_pin", "") == unit.get("upstream_pin", ""))


def select_units(units, history, limit, cycle_key, usage=None, *, fair_fraction=0.2, now=None):
    """Fair owner/repository rotation, followed by risk/usage/age priority.

    Returned copies carry a budget ``lane`` and explainable selection reason.
    Usage is a map of unit ID to distinct retrieved/injected counters. Injected
    content receives more weight, but the fair lane prevents cold starvation.
    """
    if type(limit) is not int or limit < 0 or not 0 <= fair_fraction <= 1:
        raise ValueError("invalid maintenance selection limit/fair fraction")
    now = time.time() if now is None else float(now)
    usage = usage or {}
    available = {unit["unit_id"]: unit for unit in units}
    if len(available) != len(units):
        raise ValueError("duplicate maintenance unit identity")
    limit = min(limit, len(available))

    def age(unit):
        row = history.get(unit["unit_id"], {})
        if not fresh_history(unit, row):
            return float("inf")
        return max(0.0, now - float(row.get("finished_at") or 0))

    def stable(unit):
        return _digest(str(cycle_key) + "\0" + unit["unit_id"])

    def priority(unit):
        row = history.get(unit["unit_id"], {})
        signals = usage.get(unit["unit_id"], {})
        risk = float(unit.get("risk_score", 0))
        risk += 100 if unit.get("structural_issues") else 0
        risk += 80 if row.get("outcome") == "contradicted" else 0
        risk += 30 if row.get("outcome") in ("unknown", "execution_error") else 0
        risk += 50 if row and not fresh_history(unit, row) else 0
        used = 2 * math.log1p(max(0, signals.get("injected", 0))) \
            + math.log1p(max(0, signals.get("retrieved", 0)))
        return (-risk, -age(unit), -used, stable(unit))

    fair_count = min(limit, max(1, math.ceil(limit * fair_fraction))) if limit and fair_fraction else 0
    # One owner per repository each round, then the next owner, prevents a
    # repository with many owners taking the entire fair reserve.
    groups = {}
    for unit in units:
        groups.setdefault(unit["repo"], {}).setdefault(unit["owner"], []).append(unit)
    if fair_fraction and limit >= len(groups):
        fair_count = max(fair_count, len(groups))
    for owners in groups.values():
        for values in owners.values():
            values.sort(key=lambda unit: (-age(unit), stable(unit)))
    repos = sorted(groups, key=lambda repo: _digest(str(cycle_key) + repo))
    owner_order = {repo: sorted(groups[repo], key=lambda owner: _digest(str(cycle_key) + owner))
                   for repo in repos}
    selected = []
    while len(selected) < fair_count:
        progressed = False
        for repo in repos:
            owners = owner_order[repo]
            if not owners:
                continue
            owner = owners.pop(0)
            values = groups[repo][owner]
            unit = values.pop(0)
            selected.append({**unit, "lane": "fair", "selection_reason": "fair_repo_owner_oldest"})
            available.pop(unit["unit_id"])
            if values:
                owners.append(owner)
            progressed = True
            if len(selected) == fair_count:
                break
        if not progressed:
            break
    for unit in sorted(available.values(), key=priority)[:limit - len(selected)]:
        selected.append({**unit, "lane": "priority", "selection_reason": "risk_age_usage"})
    return [{**unit, "selection_rank": rank} for rank, unit in enumerate(selected)]
