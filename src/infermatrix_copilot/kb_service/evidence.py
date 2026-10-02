"""Per-rule evidence: cited PRs, bounded patches, and pinned source definitions.

Prepared owner packets supply complete patches. Older records are expanded
through the upstream mirror. Named definitions from the exact merged commit
can recover relevant code beyond a patch's byte limit. Cuts and unavailable
source remain explicit; test definitions never imply passing test executions.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re

from ..knowledge_service.facts import CODE_SPAN, EVIDENCE_PR, PR_CITATION, FactsError
from ..knowledge_service.lifecycle import FOOTER

PER_FILE = 24 * 1024
PER_RULE = 48 * 1024
NOTE = ("full per-file diffs of the merged commit (files the rule names first); "
        "a file cut at the byte limit says so")


def _named(text: str) -> list[str]:
    out = []
    for m in CODE_SPAN.finditer(text):
        token = m.group("tok").strip().partition("::")[0].strip("/")
        if "/" in token or re.search(r"\.[A-Za-z0-9]{1,5}$", token):
            out.append(token)
    return out


def _rank(path: str) -> int:
    """Source before tests before docs and configuration (the code a rule describes first)."""
    parts = path.lower().split("/")
    if any(p in ("docs", "doc", "recipes", "examples") for p in parts[:-1]) or \
            parts[-1].endswith((".md", ".rst", ".txt", ".yaml", ".yml", ".json", ".toml")):
        return 2
    if any(p in ("tests", "test") for p in parts[:-1]) or parts[-1].startswith("test_"):
        return 1
    return 0


def _matches(path: str, names: list[str]) -> bool:
    return any(path == n or path.endswith("/" + n) or n.endswith("/" + path) for n in names)


def _cut(text: str, limit: int) -> str:
    data = text.encode("utf-8")
    if len(data) <= limit:
        return text
    digest = hashlib.sha256(data).hexdigest()
    return data[:limit].decode("utf-8", "ignore") + f"\n[... cut at {limit} bytes of {len(data)}; sha256={digest}]\n"


def _encoded(value) -> bytes:
    # Match the judge's JSON indentation and untrusted-data escaping, including
    # the evidence field's depth, rather than counting only patch characters.
    return json.dumps({"evidence": value}, ensure_ascii=False, indent=1).replace("<", "\\u003c").encode()


def _discussion(rows: list[dict], text: str, names: list[str]) -> list[dict]:
    """Select whole reply chains, including later withdrawals and corrections."""
    terms = set(re.findall(r"[A-Za-z_][A-Za-z0-9_.]{3,}|[\u4e00-\u9fff]{2,}", text.lower()))
    terms -= {"with", "when", "must", "should", "that", "this", "from", "then", "rule", "test"}
    by_id = {r.get("id"): r for r in rows if r.get("id") is not None}
    groups = {}
    for index, row in enumerate(rows):
        root, seen = row.get("id", f"row:{index}"), set()
        while root in by_id and (parent := by_id[root].get("in_reply_to_id")) is not None and root not in seen:
            seen.add(root)
            root = parent
        groups.setdefault(root, []).append(row)
    chosen = []
    for group in groups.values():
        if any(_matches(str(r.get("path") or ""), names) or
               any(term in str(r.get("body") or "").lower() for term in terms) for r in group):
            chosen.extend(group)
    return sorted(chosen, key=lambda r: (str(r.get("created_at") or r.get("submitted_at") or ""),
                                         r.get("id") if isinstance(r.get("id"), int) else 0))


def _bounded(items: list[dict], text: str) -> list[dict]:
    """One overall budget; omitted metadata and incomplete patches stay visible."""
    if len(_encoded(items)) <= PER_RULE:
        return items
    out, discussion_bytes = [], 0
    def omission(item, field, original, status="omitted"):
        data = _encoded(original)
        item.setdefault("evidence_omissions", []).append({"field": field, "status": status,
            "bytes_total": len(data), "sha256": hashlib.sha256(data).hexdigest()})

    for original in items:
        item = {}
        for field, value in original.items():
            if field in ("threads", "reviews", "replies") and isinstance(value, list):
                selected = _discussion(value, text, _named(text))
                size = len(_encoded(selected)) if selected else 0
                if discussion_bytes + size > PER_RULE // 2:
                    data = _encoded(selected)
                    raise FactsError(f"relevant {field} chronology exceeds evidence budget: "
                                     f"{len(data)} bytes sha256={hashlib.sha256(data).hexdigest()}")
                discussion_bytes += size
                item[field] = selected
                if len(selected) != len(value):
                    omission(item, field, value, "selected_complete_reply_chains")
            elif field not in ("diffs", "source_fragments") and len(_encoded(value)) > PER_RULE // 8:
                omission(item, field, value)
            else:
                item[field] = dict(value) if field == "diffs" and isinstance(value, dict) else (
                    list(value) if isinstance(value, list) else value)
        out.append(item)
    while len(_encoded(out)) > PER_RULE:
        excess = len(_encoded(out)) - PER_RULE
        patches = [(item, path, patch) for item in out for path, patch in item.get("diffs", {}).items()]
        if patches:
            item, path, patch = max(patches, key=lambda p: len(p[2].encode()))
            size = len(patch.encode())
            if size > excess + 256:
                item["diffs"][path] = _cut(patch, size - excess - 256)
            else:
                del item["diffs"][path]
                omission(item, "diffs:" + path, patch)
            continue
        fragments = [item for item in out if item.get("source_fragments")]
        if fragments:
            item = fragments[-1]
            removed = item["source_fragments"].pop()
            omission(item, "source_fragments:" + str(removed.get("path")), removed)
            continue
        fields = [(item, field, value) for item in out for field, value in item.items()
                  if field not in ("source_reference", "merge_commit_sha", "source_scope", "threads",
                                   "reviews", "replies", "evidence_omissions")]
        if not fields:
            raise FactsError("evidence identity and complete relevant discussion exceed the overall budget")
        item, field, value = max(fields, key=lambda f: len(_encoded(f[2])))
        del item[field]
        omission(item, field, value)
    return out


def _definitions(source: str, path: str, symbols: set[str]) -> list[tuple[int, int, str]]:
    """Exact Python definition ranges; bounded line windows for other languages."""
    ranges = []
    if path.endswith((".py", ".pyi")):
        try:
            tree = ast.parse(source)
        except (SyntaxError, ValueError, RecursionError):
            tree = None
        if tree is not None:
            def visit(node, prefix=""):
                for child in ast.iter_child_nodes(node):
                    definition = isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                    targets = child.targets if isinstance(child, ast.Assign) else (
                        [child.target] if isinstance(child, ast.AnnAssign) else [])
                    names = [child.name] if definition else [t.id for t in targets
                                                            if isinstance(t, ast.Name) and t.id.isupper()]
                    if any(name in symbols or prefix + name in symbols for name in names):
                        first = min([child.lineno] + [d.lineno for d in getattr(child, "decorator_list", [])])
                        ranges.append((first, child.end_lineno, "source_definition"))
                    visit(child, prefix + child.name + "." if definition else prefix)
            visit(tree)
            return sorted(set(ranges))
    lines = source.splitlines()
    for index, line in enumerate(lines):
        if any(re.search(rf"\b{re.escape(s.rsplit('.', 1)[-1])}\b", line) for s in symbols):
            ranges.append((max(1, index - 4), min(len(lines), index + 61), "source_window"))
            if len(ranges) == 4:
                break
    return ranges


def _fragments(text: str, names: list[str], files: list[str], sha: str, observer,
               budget: int) -> tuple[list[dict], int]:
    """Read named definitions at the merged SHA, never another branch or commit."""
    if not callable(getattr(observer, "file_text", None)):
        return [], budget
    symbols = set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*\b", text)) - {"PR"}
    explicit = {m.group("tok").partition("::")[2].strip() for m in CODE_SPAN.finditer(text)
                if "::" in m.group("tok")}
    symbols |= explicit
    if not names and not symbols:
        return [], budget
    paths = [p for p in files if _matches(p, names)]
    paths += [p for p in names if "/" in p and "." in p.rsplit("/", 1)[-1]
              and ".." not in p.split("/") and p not in paths]
    if not paths and symbols:
        paths = [p for p in files if _rank(p) < 2][:4]
    fragments = []
    for path in list(dict.fromkeys(paths))[:8]:
        record = {"path": path, "sha": sha}
        try:
            source = observer.file_text(sha, path)
        except FactsError as exc:
            fragments.append({**record, "status": "unavailable", "reason": str(exc)})
            continue
        if source is None:
            fragments.append({**record, "status": "missing"})
            continue
        lines = source.splitlines(keepends=True)
        ranges = _definitions(source, path, symbols)
        if not ranges:
            fragments.append({**record, "status": "symbol_missing" if explicit else "no_named_definition"})
            continue
        for first, last, kind in ranges[:4]:
            if budget <= 0:
                fragments.append({**record, "kind": kind, "status": "budget_exhausted",
                                  "requested_start_line": first, "requested_end_line": last})
                continue
            raw = "".join(lines[first - 1:last]).encode("utf-8")
            content = raw[:min(8 * 1024, max(0, budget))].decode("utf-8", "ignore")
            size = len(content.encode("utf-8"))
            status = "complete" if size == len(raw) else "truncated" if size else "budget_exhausted"
            fragments.append({**record, "kind": kind, "status": status,
                              "start_line": first, "end_line": first + max(0, len(content.splitlines()) - 1),
                              "requested_end_line": last, "bytes_total": len(raw), "content": content,
                              "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest()})
            budget -= size
    return fragments, budget


def for_rule(text: str, evidence: list[dict], observer) -> list[dict]:
    """The evidence for one rule (``text``: the rule as proposed, or as it was)."""
    cited = {f"PR #{m.group('n')}" for m in PR_CITATION.finditer(text)}
    # a retirement's justification lives in its footer (evidence="PR #N"), not in a citation
    for line in text.splitlines():
        footer = FOOTER.match(line.strip())
        if footer:
            cited |= {f"PR #{m.group('n')}" for m in EVIDENCE_PR.finditer(footer.group("attrs"))}
    items = [e for e in evidence if e.get("source_reference") in cited] or list(evidence)
    if observer is None and not any("diffs" in item for item in items):
        return _bounded(items, text)
    names, budget, out = _named(text), PER_RULE, []
    for item in items:
        number = re.fullmatch(r"PR #(\d+)", str(item.get("source_reference") or ""))
        if not number or "merged_at" not in item:
            out.append(item)  # not an upstream merged PR (or no room left): as recorded
            continue
        prepared = item.get("diffs") if isinstance(item.get("diffs"), dict) else None
        files = list(dict.fromkeys([*(item.get("changed_files") or []), *(prepared or {})]))
        ordered = sorted(files, key=lambda f: (not _matches(f, names), _rank(f)))
        fragments, diffs, error = [], {}, ""
        try:
            sha = str(item.get("merge_commit_sha") or (
                observer.pull(int(number.group(1))).get("merge_commit_sha") if observer else "") or "")
            if not sha:
                raise FactsError("no merge commit")
            allowance = min(24 * 1024, max(0, budget // 2))
            fragments, remaining = _fragments(text, names, files, sha, observer, allowance)
            budget -= allowance - remaining
            for path in ordered:
                if budget <= 0:
                    break
                full = prepared.get(path, "") if prepared is not None else (
                    observer.pr_diff(int(number.group(1)), sha, path) if observer else "")
                diff = _cut(full, min(PER_FILE, budget))
                if diff:
                    diffs[path] = diff
                    budget -= len(diff.encode("utf-8"))
        except FactsError as exc:
            if not fragments and prepared is None:
                out.append(item)
                continue
            error = str(exc)
        if not diffs and not fragments and prepared is None:
            out.append(item)
            continue
        expanded = {k: v for k, v in item.items() if k not in ("diff_excerpt", "diff", "diffs")}
        out.append({**expanded, "diffs": diffs, "diffs_note": NOTE,
                    "diffs_omitted": [f for f in ordered if f not in diffs],
                    **({"diffs_status": "unavailable", "diffs_error": error} if error else {}),
                    **({"source_fragments": fragments,
                        "source_fragments_note": "Exact merged-commit source; test definitions are not test executions."}
                       if fragments else {})})
    return _bounded(out, text)
