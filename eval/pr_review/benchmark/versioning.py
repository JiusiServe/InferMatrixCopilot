"""Helpers for benchmark artifact versioning and immutable writes."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from .io import sha256_file
from .schema import BenchmarkItem, BenchmarkManifest, BenchmarkManifestEntry


def write_item(item: BenchmarkItem, path: str | Path, *, overwrite: bool = False) -> Path:
    path = Path(path)
    if path.exists() and not overwrite:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = item.model_dump(mode="json", exclude_none=True)
    if path.suffix.lower() in {".yaml", ".yml"}:
        path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    else:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def freeze_manifest(manifest: BenchmarkManifest, root: str | Path) -> BenchmarkManifest:
    root = Path(root)
    entries: list[BenchmarkManifestEntry] = []
    for entry in manifest.entries:
        item_path = root / entry.item
        entries.append(entry.model_copy(update={"sha256": sha256_file(item_path)}))
    return manifest.model_copy(update={"entries": entries})
