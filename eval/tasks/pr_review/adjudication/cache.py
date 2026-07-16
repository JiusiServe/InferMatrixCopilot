"""Content-addressed JSON cache for expensive judge calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class AdjudicationCache:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def key(namespace: str, payload: dict[str, Any]) -> str:
        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(f"{namespace}\n{canonical}".encode()).hexdigest()

    def get(self, key: str) -> dict[str, Any] | None:
        path = self.root / f"{key}.json"
        if not path.is_file():
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None

    def put(self, key: str, value: dict[str, Any]) -> Path:
        path = self.root / f"{key}.json"
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        temp.replace(path)
        return path
