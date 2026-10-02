"""Index finalized A/B raw evidence outside Git; never inline evidence contents.

Usage: python eval/jiuwenswarm_ab_archive.py --state STATE --output STATE/raw-trace-index.json
The index is deterministic and excludes caches, temporary locks and derived
reports. All72 review slots and all12 scorer records must be terminal first.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


SCHEMA = "jiuwenswarm-pr-ab-raw-index-v1"
PREFIXES = ("mapping", "snapshots", "evaluation-v2")
SUPPLEMENTAL = ("campaign.json", "extraction-timing.json", "upstream-freshness.json",
                "freshness-branch-develop.json", "final-validation.json", "baseline-pr290.json", "ci-code-checks.json")
EXCLUDED_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules"}
EXCLUDED_FILES = {"index.db"}


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _external(path):
    path = Path(path).absolute()
    for ancestor in (path, *path.parents):
        if ancestor.is_symlink():
            raise ValueError("symlink paths are not supported")
        if ancestor.is_dir() and (ancestor / ".git").exists():
            raise ValueError("archive inputs/output must remain outside Git")
    return path.resolve()


def _within(path, root):
    path = Path(path)
    if not path.is_absolute() or not path.resolve().is_relative_to(root):
        raise ValueError("artifact path escapes external run root")
    relative = path.relative_to(root)
    if any((root.joinpath(*relative.parts[:end])).is_symlink() for end in range(1, len(relative.parts) + 1)):
        raise ValueError("symlink artifact is not supported")
    return path


def _read(path, guards):
    path = _external(path)
    data = path.read_bytes()
    guards[path] = _sha(data)
    obj = json.loads(data)
    if not isinstance(obj, dict):
        raise ValueError("expected JSON object")
    return obj


def _finalized(state):
    """Bind terminal records before walking any raw model output directories."""
    run = state / "evaluation-v2"
    guards = {}
    campaign = _read(run / "campaign.json", guards)
    campaign_sha = guards[run / "campaign.json"]
    if campaign.get("schema") != "jiuwenswarm-pr-review-ab-v1" or Path(campaign.get("run_root", "")).resolve() != run:
        raise ValueError("invalid finalized campaign root/schema")
    cases = campaign.get("cases", [])
    prs = {c.get("number") for c in cases}
    if len(cases) != 12 or len(prs) != 12 or any(type(pr) is not int or pr <= 0 for pr in prs):
        raise ValueError("campaign must contain exactly12 PRs")
    identity = _read(run / "identity.json", guards)
    calculated_identity = _sha(json.dumps({k: v for k, v in identity.items() if k != "identity_sha256"}, sort_keys=True).encode())
    if identity.get("schema") != campaign["schema"] or identity.get("campaign_sha256") != campaign_sha or identity.get("identity_sha256") != calculated_identity:
        raise ValueError("campaign identity differs")
    manifest = _read(run / "reviews-manifest.json", guards)
    if manifest.get("schema") != "jiuwenswarm-pr-reviews-v1" or manifest.get("campaign_sha256") != campaign_sha or manifest.get("identity_sha256") != identity.get("identity_sha256"):
        raise ValueError("reviews manifest identity differs")
    expected = {(pr, arm, repeat) for pr in prs for arm in ("A", "B") for repeat in range(3)}
    rows = {}
    for row in manifest.get("reviews", []):
        key = row.get("pr"), row.get("arm"), row.get("repeat")
        if key not in expected or key in rows or type(key[0]) is not int or type(key[2]) is not int or row.get("status") not in ("complete", "failed"):
            raise ValueError("live/incomplete or duplicate review slot")
        item = run / "items" / f"review-pr{key[0]}-{key[1]}-r{key[2] + 1}"
        result_path = _within(Path(row.get("run_result_path", "")), run)
        if result_path != item / "result.json":
            raise ValueError("review result path/slot differs")
        result = _read(result_path, guards)
        output_path = _within(Path(row.get("output_path", "")), item)
        output = output_path.read_bytes()
        guards[output_path] = _sha(output)
        native_status = result.get("status")
        if native_status not in ("valid", "invalid_run", "transport_failed", "interrupted") or row.get("native_status") != native_status or row.get("status") != ("complete" if native_status == "valid" else "failed"):
            raise ValueError("native review is not terminal")
        if result.get("preflight") is not False or (result.get("number"), result.get("arm"), result.get("repetition")) != (key[0], key[1], key[2] + 1):
            raise ValueError("native result slot differs")
        if row.get("run_result_sha256") != guards[result_path] or row.get("normalized_output_sha256") != guards[output_path] or result.get("normalized_output_sha256") != guards[output_path]:
            raise ValueError("final review output/result hash differs")
        if any(obj.get("campaign_sha256") != campaign_sha or obj.get("identity_sha256") != identity.get("identity_sha256") for obj in (row, result)):
            raise ValueError("review campaign binding differs")
        attempts = result.get("attempts", [])
        if not attempts:
            raise ValueError("terminal review has no native attempt record")
        expected_attempts = {item / f"attempt-{ordinal}" for ordinal in range(1, len(attempts) + 1)}
        if set(item.glob("attempt-*")) != expected_attempts:
            raise ValueError("unaccounted live/incomplete native attempt directory")
        for ordinal, attempt in enumerate(attempts, 1):
            if attempt.get("status") not in ("valid", "invalid_run", "transport_failed", "interrupted") or _within(Path(attempt.get("attempt_root", "")), run) != item / f"attempt-{ordinal}":
                raise ValueError("native attempt is not terminal or slot-bound")
        rows[key] = row
    if set(rows) != expected:
        raise ValueError("all72 formal reviews must be terminal before indexing")
    expected_dirs = {f"review-pr{pr}-{arm}-r{repeat + 1}" for pr, arm, repeat in expected}
    if {p.name for p in (run / "items").glob("review-*")} != expected_dirs:
        raise ValueError("unexpected live formal review directory")
    private = run / "private-codex"
    truth = _read(private / "truth-manifest.json", guards)
    if truth.get("frozen") is not True or truth.get("campaign_sha256") != campaign_sha:
        raise ValueError("truth must be frozen before raw indexing")
    score_paths = set((private / "scores").glob("pr-*.json"))
    expected_scores = {private / "scores" / f"pr-{pr}.json" for pr in prs}
    if score_paths != expected_scores:
        raise ValueError("all12 scorer records must be terminal before indexing")
    for path in sorted(score_paths):
        record = _read(_within(path, run), guards)
        pr = int(path.stem.removeprefix("pr-"))
        if record.get("schema") != "jiuwenswarm-pr-blind-score-v1" or record.get("pr") != pr or record.get("status") not in ("complete", "failed") or record.get("truth_manifest_sha256") != guards[private / "truth-manifest.json"]:
            raise ValueError("live/incomplete scorer or truth binding differs")
        mapping = record.get("blind_mapping", {})
        mapped = {(r.get("pr"), r.get("arm"), r.get("repeat")) for r in mapping.values()}
        if len(mapping) != 6 or mapped != {key for key in expected if key[0] == pr}:
            raise ValueError("scorer must account for all six review slots")
        for row in mapping.values():
            original = rows[row["pr"], row["arm"], row["repeat"]]
            if any(row.get(key) != original.get(key) for key in ("run_result_sha256", "normalized_output_sha256")):
                raise ValueError("scorer review binding differs")
    return guards


def _excluded(path, prefix):
    name = path.name
    relative = path.relative_to(prefix).as_posix()
    # Frozen documents/source inputs are data, including files whose names
    # resemble runtime caches or generated reports. Never filter those by name.
    if prefix.name == "snapshots" or relative.startswith(("inputs/", "private-codex/source-inputs/", "private-codex/score-source-inputs/")):
        return False
    runtime = (prefix.name == "mapping" and relative.startswith(("traces/", "runtime/"))) or \
        (prefix.name == "evaluation-v2" and (relative.startswith(("items/", "preflight-v2-archive/items/", "private-codex/preflight-attempts/", "private-codex/preflight-traces/", "private-codex/truth-traces/", "private-codex/score-traces/")) or "/" not in relative or relative.count("/") == 1 and relative.startswith("private-codex/")))
    if runtime and (name in EXCLUDED_DIRS or name in EXCLUDED_FILES or name.endswith((".lock", ".tmp", ".pyc", ".db-wal", ".db-shm"))):
        return True
    if prefix.name != "evaluation-v2":
        return prefix.name == "mapping" and relative == "original-content-cn.md"
    return relative in {"collection.json", "private-codex/results.json", "diagnostics.json", "raw-trace-index.json", "report-draft"} or \
        bool(re.fullmatch(r"report(?:[-_].*)?\.(?:json|md|html)", relative)) or \
        bool(re.fullmatch(r"(?:preflight-v2-archive/)?items/[^/]+/attempt-\d+/storage", relative)) or \
        bool(re.fullmatch(r"preflight-v2-archive/(?:collection|reviews-manifest)\.json", relative))


def _walk(path, prefix):
    if _excluded(path, prefix):
        return
    if path.is_symlink():
        raise ValueError("symlink raw artifact is not supported")
    if path.is_dir():
        for child in sorted(path.iterdir()):
            yield from _walk(child, prefix)
    elif path.is_file():
        yield path
    else:
        raise ValueError("raw archive contains a non-regular artifact")


def build_index(state):
    """Build a deterministic digest inventory; no filesystem mutation or models."""
    state = _external(state)
    guards = _finalized(state)
    files = []
    for name in PREFIXES:
        prefix = state / name
        if not prefix.is_dir():
            raise ValueError("missing raw archive directory:" + name)
        for path in _walk(prefix, prefix):
            before = path.stat()
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for block in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(block)
            after = path.stat()
            if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
                raise ValueError("raw artifact changed while indexing")
            files.append({"path": path.relative_to(state).as_posix(), "bytes": after.st_size, "sha256": digest.hexdigest()})
    for name in SUPPLEMENTAL:
        path = state / name
        if path.exists() or path.is_symlink():
            _within(path, state)
            data = path.read_bytes()
            files.append({"path": name, "bytes": len(data), "sha256": _sha(data)})
    for path, digest in guards.items():
        if _sha(path.read_bytes()) != digest:
            raise ValueError("terminal campaign/scorer record changed while indexing")
    files.sort(key=lambda row: row["path"])
    canonical = json.dumps(files, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return {"schema": SCHEMA, "files": files, "file_count": len(files),
            "total_bytes": sum(row["bytes"] for row in files), "files_sha256": _sha(canonical)}


def write_index(state, output):
    state, output = _external(state), _external(output)
    if any(output.is_relative_to(state / name) for name in PREFIXES) or output in {state / name for name in SUPPLEMENTAL}:
        raise ValueError("index output must not overwrite indexed raw evidence")
    manifest = build_index(state)
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".raw-index-", suffix=".tmp", dir=output.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    manifest = write_index(args.state, args.output)
    print(json.dumps({key: manifest[key] for key in ("schema", "file_count", "total_bytes", "files_sha256")}, sort_keys=True))


if __name__ == "__main__":
    main()
