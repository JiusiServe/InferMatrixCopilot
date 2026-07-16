"""Load and validate immutable benchmark manifests and items."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from .schema import BenchmarkItem, BenchmarkManifest


class BenchmarkIntegrityError(ValueError):
    pass


def _load_mapping(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text) if path.suffix.lower() in {".yaml", ".yml"} else json.loads(text)
    if not isinstance(data, dict):
        raise BenchmarkIntegrityError(f"expected an object in {path}")
    return data


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: str | Path) -> BenchmarkManifest:
    path = Path(path)
    return BenchmarkManifest.model_validate(_load_mapping(path))


def load_item(path: str | Path) -> BenchmarkItem:
    path = Path(path)
    return BenchmarkItem.model_validate(_load_mapping(path))


def load_benchmark(manifest_path: str | Path, *, verify_hashes: bool = True) -> tuple[BenchmarkManifest, list[BenchmarkItem]]:
    manifest_path = Path(manifest_path)
    manifest = load_manifest(manifest_path)
    items: list[BenchmarkItem] = []
    for entry in manifest.entries:
        item_path = (manifest_path.parent / entry.item).resolve()
        if not item_path.is_file():
            raise BenchmarkIntegrityError(f"missing benchmark item: {item_path}")
        if verify_hashes and entry.sha256 and sha256_file(item_path) != entry.sha256:
            raise BenchmarkIntegrityError(f"SHA-256 mismatch for {entry.item}")
        item = load_item(item_path)
        if item.benchmark_id != entry.benchmark_id:
            raise BenchmarkIntegrityError(
                f"manifest ID {entry.benchmark_id!r} does not match item ID {item.benchmark_id!r}"
            )
        items.append(item)
    return manifest, items
