"""Pinned semantic witnesses, separate from feature/file and rule coverage."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from urllib.parse import quote

from ..knowledge_service.lifecycle import Page
from .init_stages import neutral_headings
from .knowledge_coverage import _LEXICAL_NO_CODE, inventory

FACETS = ("flow", "api", "configuration", "dependencies", "failure_modes", "tradeoffs", "validation")
_BLOCK = re.compile(r"<!-- kb:depth feature=([a-z0-9-]+) facet=([a-z_]+) pin=([0-9a-f]{40}) "
                    r"sha256=([0-9a-f]{64}) -->\n(.*?)\n<!-- /kb:depth -->", re.S)
_PROOF = re.compile(r"\n<!-- kb:depth-proof (.*?) -->\s*$", re.S)
_PRIVATE_PATH = re.compile(r"/(?:home/(?!models(?:/|\b)|<)|data/(?!models?(?:/|\b)|<))[A-Za-z0-9_-]+")
_IP = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_path(path: object) -> bool:
    return isinstance(path, str) and bool(path) and not path.startswith("/") and "\\" not in path \
        and all(part not in ("", ".", "..") for part in path.split("/"))


def validate_draft(data: dict) -> None:
    sections = data.get("sections")
    if not isinstance(sections, list) or len(sections) > len(FACETS):
        raise ValueError("sections must list at most seven depth facets")
    seen = set()
    for section in sections:
        if not isinstance(section, dict) or section.get("facet") not in FACETS or section["facet"] in seen:
            raise ValueError("depth facets must be known and unique")
        seen.add(section["facet"])
        body = section.get("body")
        if not isinstance(body, str) or not body.strip() or len(body) > 1400 \
                or re.search(r"(?m)^\s*#", body) or "<!--" in body:
            raise ValueError("a depth section needs bounded prose without headings or metadata")
        if _PRIVATE_PATH.search(body) or any(not m.group().startswith("127.") for m in _IP.finditer(body)) \
                or "-----BEGIN PRIVATE KEY-----" in body:
            raise ValueError("depth prose contains machine-specific information")
        if section.get("interpretation") not in ("fact", "inference"):
            raise ValueError("depth interpretation must be fact or inference")
        evidence = section.get("evidence")
        if not isinstance(evidence, list) or not 1 <= len(evidence) <= 4:
            raise ValueError("each depth facet needs one to four evidence spans")
        for item in evidence:
            if not isinstance(item, dict) or not safe_path(item.get("path")) \
                    or type(item.get("start")) is not int or type(item.get("end")) is not int \
                    or not 1 <= item["start"] <= item["end"]:
                raise ValueError("depth evidence needs safe paths and inclusive integer line spans")
        if section["facet"] == "flow":
            trace = section.get("trace")
            if not isinstance(trace, list) or not 2 <= len(trace) <= 6:
                raise ValueError("flow needs two to six named, ordered call steps")
            for step in trace:
                if not isinstance(step, dict) or not isinstance(step.get("symbol"), str) \
                        or not re.fullmatch(r"[\w.$]+", step["symbol"]) \
                        or not safe_path(step.get("path")) or type(step.get("start")) is not int \
                        or type(step.get("end")) is not int or not 1 <= step["start"] <= step["end"]:
                    raise ValueError("flow steps need symbols and source spans")
                if not any(e["path"] == step["path"] and e["start"] <= step["start"] <= step["end"] <= e["end"]
                           for e in evidence):
                    raise ValueError("each flow step must be contained in the cited evidence")


def source_span(tree: Path, entry: dict) -> str:
    if not safe_path(entry.get("path")) or type(entry.get("start")) is not int \
            or type(entry.get("end")) is not int or not 1 <= entry["start"] <= entry["end"]:
        raise ValueError("invalid depth evidence")
    file = tree / entry["path"]
    if not file.is_file() or file.is_symlink() or not file.resolve().is_relative_to(tree.resolve()):
        raise ValueError("depth evidence escapes the pinned tree")
    lines = file.read_text(encoding="utf-8").splitlines(keepends=True)
    if entry["end"] > len(lines):
        raise ValueError("depth evidence exceeds the pinned file")
    return "".join(lines[entry["start"] - 1:entry["end"]])


def python_definitions(module: ast.AST) -> dict[str, ast.AST]:
    """Keep lexical owners so similarly named methods cannot impersonate one another."""
    found = {}

    def walk(node, prefix=""):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = prefix + child.name
                found[name] = child
                walk(child, name + ".")
            else:
                walk(child, prefix)

    walk(module)
    return found


def _scope_nodes(node):
    for child in ast.iter_child_nodes(node):
        if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            yield child
            yield from _scope_nodes(child)


def _module_matches(path: str, caller: str, node: ast.ImportFrom | ast.Import, name: str) -> bool:
    if isinstance(node, ast.ImportFrom) and node.level:
        package = caller.split("/")[:-1]
        if node.level > len(package):
            return False
        prefix = package[:len(package) - node.level + 1]
        base = "/".join(prefix + name.split("."))
        return path in (base + ".py", base + "/__init__.py")
    base = name.replace(".", "/")
    return any(path == suffix or path.endswith("/" + suffix)
               for suffix in (base + ".py", base + "/__init__.py"))


def _calls_next(module, definition, step, target):
    aliases = {}
    for node in list(_scope_nodes(module)) + list(_scope_nodes(definition)):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if _module_matches(target["path"], step["path"], node, node.module or ""):
                    aliases[alias.asname or alias.name] = alias.name
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if _module_matches(target["path"], step["path"], node, alias.name):
                    aliases[alias.asname or alias.name] = ""
    owner = step["symbol"].rsplit(".", 1)[0] if "." in step["symbol"] else ""
    for call in _scope_nodes(definition):
        if not isinstance(call, ast.Call) or not step["start"] <= call.lineno <= step["end"]:
            continue
        names, function = [], call.func
        while isinstance(function, ast.Attribute):
            names.insert(0, function.attr)
            function = function.value
        if not isinstance(function, ast.Name):
            continue  # object dispatch needs a runtime/type witness, not a name guess
        names.insert(0, function.id)
        root = names[0]
        if root in aliases:
            resolved = ".".join(([aliases[root]] if aliases[root] else []) + names[1:])
            if resolved == target["symbol"]:
                return True
        elif step["path"] == target["path"]:
            resolved = ".".join(names)
            if root in ("self", "cls") and owner:
                resolved = owner + "." + ".".join(names[1:])
            if resolved == target["symbol"]:
                return True
    return False


def verify_trace(tree: Path, trace: list[dict]) -> None:
    """Verify a representative static call chain; no runtime coverage claim."""
    identities = [(s["path"], s["symbol"], s["start"], s["end"]) for s in trace]
    if len(set(identities)) != len(identities) or len(trace) < 2:
        raise ValueError("flow steps must be distinct")
    for i, step in enumerate(trace):
        raw = (tree / step["path"]).read_text(encoding="utf-8")
        span = source_span(tree, step)
        name = step["symbol"].rsplit(".", 1)[-1]
        if step["path"].endswith(".py"):
            module = ast.parse(raw)
            definition = python_definitions(module).get(step["symbol"])
            if definition is None or not definition.lineno <= step["start"] <= step["end"] <= definition.end_lineno:
                raise ValueError("flow symbol/span is not a pinned definition")
            if i + 1 < len(trace):
                if not _calls_next(module, definition, step, trace[i + 1]):
                    raise ValueError("flow span does not call the next named step")
        else:
            # Conservative lexical witnesses for clients/build languages.
            span = _LEXICAL_NO_CODE.sub("", span)
            declared = re.search(r"(?:function|class|def|fun)\s+" + re.escape(name) + r"\b|\b"
                                 + re.escape(name) + r"\s*(?:=|\([^\n]*\)\s*\{)", span)
            if not declared:
                raise ValueError("flow symbol is not declared in the supplied span")
            if i + 1 < len(trace) and not re.search(
                    r"\b" + re.escape(trace[i + 1]["symbol"].rsplit(".", 1)[-1]) + r"\s*\(", span):
                raise ValueError("flow span does not show the next call")


def render_block(feature, section: dict, tree: Path, full_name: str, pin: str) -> str:
    proof = {"evidence": [{**e, "sha256": digest(source_span(tree, e))} for e in section["evidence"]],
             "trace": section.get("trace", [])}
    if section["facet"] == "flow":
        verify_trace(tree, proof["trace"])
    title = " ".join(str(section.get("title") or section["facet"]).replace("#", "").split())
    body = neutral_headings(f"## {title}\n\n")
    if section["interpretation"] == "inference":
        body += "设计推断（非作者历史意图）：\n\n"
    body += section["body"].strip() + "\n\n"
    if proof["trace"]:
        body += "调用路径：" + " → ".join(chr(96) + s["path"] + chr(96) + "（" + chr(96) + s["symbol"] + chr(96) + "）"
                                    for s in proof["trace"]) + "\n\n"
    body += "来源：" + ", ".join(
        f"[{e['path']}:L{e['start']}–L{e['end']}](https://github.com/{full_name}/blob/{pin}/"
        f"{quote(e['path'], safe='/')}#L{e['start']}-L{e['end']})" for e in section["evidence"]) + "\n"
    body += "\n<!-- kb:depth-proof " + json.dumps(proof, ensure_ascii=False, separators=(",", ":")) + " -->"
    return (f"<!-- kb:depth feature={feature.id} facet={section['facet']} pin={pin} sha256={digest(body)} -->\n"
            + body + "\n<!-- /kb:depth -->")


def verified_blocks(text: str, feature, tree: Path, pin: str) -> tuple[dict[str, str], list[str]]:
    blocks, problems, invalid = {}, [], set()
    try:
        page = Page.parse(text)
        if page.frontmatter_field("type") not in ("architecture", "guide") or page.rules():
            return {}, ["depth target must be explanatory, without rules"]
    except Exception as exc:
        return {}, [str(exc)]
    for fid, facet, sha, hashed, body in _BLOCK.findall(text):
        if fid != feature.id or facet not in FACETS:
            continue
        try:
            if facet in blocks or facet in invalid or sha != pin or digest(body) != hashed:
                raise ValueError("duplicate, stale or edited depth block")
            match = _PROOF.search(body)
            if not match:
                raise ValueError("depth block has no bound evidence proof")
            proof = json.loads(match.group(1))
            if not isinstance(proof.get("evidence"), list) or not 1 <= len(proof["evidence"]) <= 4:
                raise ValueError("invalid depth proof spans")
            for e in proof["evidence"]:
                if e.get("sha256") != digest(source_span(tree, e)):
                    raise ValueError("depth evidence changed at the pin")
            if facet == "flow":
                trace = proof.get("trace", [])
                if not 2 <= len(trace) <= 6 or any(not any(
                        e["path"] == s["path"] and e["start"] <= s["start"] <= s["end"] <= e["end"]
                        for e in proof["evidence"]) for s in trace):
                    raise ValueError("flow trace is not contained in its evidence")
                verify_trace(tree, trace)
            blocks[facet] = (f"<!-- kb:depth feature={fid} facet={facet} pin={sha} sha256={hashed} -->\n"
                             + body + "\n<!-- /kb:depth -->")
        except (ValueError, KeyError, TypeError, SyntaxError, OSError) as exc:
            problems.append(f"{feature.id}/{facet}: {exc}")
            invalid.add(facet)
            blocks.pop(facet, None)
    return blocks, problems


def depth_page(feature) -> str:
    return str(PurePosixPath(feature.page).with_name(f"feature-depth-{feature.id}.md"))


def audit_depth(head: dict[str, str], tree: Path, policy, pin: str) -> dict:
    production = set(inventory(tree, policy))
    witnessed, features, errors = set(), {}, []
    for feature in policy.features:
        page = depth_page(feature)
        blocks, problems = verified_blocks(head[page], feature, tree, pin) if page in head else ({}, [])
        if "flow" in blocks:
            proof = json.loads(_PROOF.search(_BLOCK.search(blocks["flow"]).group(5)).group(1))
            if any(s["path"] not in production for s in proof["trace"]):
                blocks.pop("flow")
                problems.append(f"{feature.id}/flow: trace must use production implementation")
        errors.extend(problems)
        for block in blocks.values():
            proof = json.loads(_PROOF.search(_BLOCK.search(block).group(5)).group(1))
            witnessed.update(e["path"] for e in proof["evidence"] if e["path"] in production)
        features[feature.id] = {"owner": feature.owner, "page": page, "facets": list(blocks),
                                "missing_facets": [f for f in FACETS if f not in blocks],
                                "complete": len(blocks) == len(FACETS)}
    slots = len(policy.features) * len(FACETS)
    covered = sum(len(x["facets"]) for x in features.values())
    return {"pin": pin, "features": features, "complete_features": sum(x["complete"] for x in features.values()),
            "total_features": len(features), "covered_facets": covered, "total_facets": slots,
            "facet_ratio": covered / slots if slots else 0.0,
            "production_files_with_semantic_evidence": sorted(witnessed), "production_files_total": len(production),
            "problems": errors, "complete": covered == slots and not errors,
            "interpretation": "Pinned representative call/contract witnesses; neither static interface cards "
                              "nor exhaustive behavior or executed-test coverage."}
