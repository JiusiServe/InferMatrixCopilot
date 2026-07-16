"""Deterministic output-format repair with no repository or model access."""

from __future__ import annotations

import json
import re
from typing import Any


_FIELD_ALIASES = {
    "finding": "findings",
    "issues": "findings",
    "issue": "findings",
    "file_path": "file",
    "path": "file",
    "line_start": "start_line",
    "start": "start_line",
    "line_end": "end_line",
    "end": "end_line",
}

_SEVERITY = {
    "critical": "Critical",
    "blocker": "Blocker",
    "major": "Major",
    "minor": "Minor",
    "nit": "Nit",
}

_CATEGORIES = {
    "correctness",
    "compatibility_api",
    "concurrency",
    "performance_resource",
    "security_safety",
    "test",
    "documentation",
    "maintainability",
}


def _extract_json(text: str) -> str | None:
    stripped = text.strip()
    fence = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", stripped, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        stripped = fence.group(1).strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end <= start:
        return None
    return stripped[start : end + 1]


def _normalize(obj: Any) -> Any:
    if isinstance(obj, list):
        return [_normalize(value) for value in obj]
    if not isinstance(obj, dict):
        return obj

    result: dict[str, Any] = {}
    for raw_key, value in obj.items():
        key = _FIELD_ALIASES.get(str(raw_key).strip().lower(), str(raw_key).strip())
        result[key] = _normalize(value)

    if "verdict" in result and isinstance(result["verdict"], str):
        result["verdict"] = result["verdict"].strip().upper().replace(" ", "_")
    if "severity" in result and isinstance(result["severity"], str):
        result["severity"] = _SEVERITY.get(result["severity"].strip().lower(), result["severity"])
    if "category" in result and isinstance(result["category"], str):
        category = result["category"].strip().lower().replace("-", "_").replace(" ", "_")
        if category in _CATEGORIES:
            result["category"] = category
    return result


def repair_json_text(raw: str) -> str | None:
    candidate = _extract_json(raw)
    if candidate is None:
        return None
    try:
        obj = json.loads(candidate)
    except json.JSONDecodeError:
        # Only syntax-level repairs: trailing commas and single quotes around keys/strings.
        candidate = re.sub(r",\s*([}\]])", r"\1", candidate)
        candidate = re.sub(r"'([^'\\]*(?:\\.[^'\\]*)*)'", lambda m: json.dumps(m.group(1)), candidate)
        try:
            obj = json.loads(candidate)
        except json.JSONDecodeError:
            return None
    return json.dumps(_normalize(obj), ensure_ascii=False)
