"""Pinned knowledge references locate new inputs; they never approve new prose."""
from __future__ import annotations

import re

from ..knowledge_service.lifecycle import Page
from .evidence_bundle import bounded_spans
from .init_support import InitError


def context_version(rt):
    raw = str(rt.environ.get("KB_KNOWLEDGE_CONTEXT_VERSION", "4"))
    if raw not in {"4", "5"}:
        raise InitError("KB_KNOWLEDGE_CONTEXT_VERSION must be 4 or 5")
    return int(raw)


def feature_context(stage, feature, sources, docs, *, source_limit, doc_limit):
    """Put fixed-version citations and their implementation context before prefixes.

    Only the shared declared inventory is read. A citation with another pin,
    an unreadable file or an invalid range is not evidence. Existing explanations
    remain unchanged, and both models still receive the same actual source text.
    """
    from .knowledge_depth import depth_page

    index = stage.source_index
    if index.identity["pin"] != stage.record.pin:
        raise InitError("foundation context index source pin differs")
    prefix = re.escape(stage.lifecycle.full_name + "@" + stage.record.pin + ":")
    pattern = re.compile(r"^" + prefix + r"(.+):L(\d+)-L(\d+)$")
    references = []
    for page in (feature.page, depth_page(feature)):
        text = stage.head.get(page, "")
        if not text:
            continue
        for source in Page.parse(text).sources():
            match = pattern.fullmatch(source)
            if match:
                references.append((match[1], int(match[2]), int(match[3])))
    located, seen = [], set()
    for path, start, end in references:
        entry = index.entries.get(path)
        if not entry or entry.get("status") != "ready" or not 1 <= start <= end <= len(entry["lines"]):
            stage.record.unfinished.append(f"feature {feature.id}: existing source locator unavailable: {path}")
            continue
        lines = entry["lines"]
        # Python symbols have actual parsed bodies. Other languages retain
        # representative neighboring text, without claiming a runtime relation.
        enclosing = [s for s in entry.get("symbols", [])
                     if s["start"] <= start <= end <= s["end"]]
        symbol = min(enclosing, key=lambda s: s["end"] - s["start"], default=None)
        left, right = max(1, start - 80), min(len(lines), end + 80)
        if symbol and entry.get("language") == "python":
            left, right = max(1, symbol["start"] - 2), symbol["end"]
        # Put the cited anchor first even when a large enclosing implementation
        # cannot fit; a prefix cap must not hide the very location being reused.
        for left, right in ((start, end), (left, right)):
            key = (path, left, right)
            if key in seen:
                continue
            seen.add(key)
            located.append({"path": path, "start": left, "end": right,
                            "total_lines": len(lines), "language": entry["language"],
                            "sha256": entry["sha256"], "kind": entry["kind"],
                            "localization": "existing pinned citation; new claims require independent review",
                            "text": "\n".join(f"{n}: {lines[n - 1]}" for n in range(left, right + 1))})
    # The caller already reserved related-test bytes. Do not let newly located
    # implementation bodies crowd those assertions out of the final packet.
    def is_test(item):
        return bool(item.get("test_context")) or index.entries.get(item["path"], {}).get("kind") == "test"
    tests = [item for item in sources if is_test(item)]
    source = bounded_spans(tests + [s for s in located if s["kind"] == "test"]
                           + [s for s in located if s["kind"] == "source"]
                           + [item for item in sources if not is_test(item)], source_limit)
    documents = bounded_spans([s for s in located if s["kind"] == "doc"] + docs, doc_limit)
    return source, documents
