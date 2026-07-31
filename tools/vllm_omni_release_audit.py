"""Deterministic, read-only drift audit for vLLM-Omni releases."""

from __future__ import annotations

import argparse
import ast
import fnmatch
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml


_REPO_ROOT = Path(__file__).resolve().parents[1]
_REGISTRIES = {
    "autoregressive": (
        "vllm_omni/model_executor/models/registry.py",
        "_OMNI_MODELS",
        True,
    ),
    "diffusion": (
        "vllm_omni/diffusion/registry.py",
        "_DIFFUSION_MODELS",
        True,
    ),
    "pipelines": (
        "vllm_omni/config/pipeline_registry.py",
        "OMNI_PIPELINES",
        False,
    ),
}
_UPSTREAM_SOURCE_PREFIXES = (
    ".buildkite/",
    "benchmarks/",
    "docs/",
    "tests/",
    "vllm_omni/",
)
_SOURCE_EXCLUDED_PARTS = {"_archive", "history", "incidents", "results"}
_PIN_RE = re.compile(
    r"\b(?:main|v\d[0-9A-Za-z.-]*)\s*@\s*`?([0-9a-f]{8,40})",
    re.IGNORECASE,
)


class ReleaseAuditError(RuntimeError):
    """The audit could not read or understand one of its declared inputs."""


@dataclass(frozen=True)
class ChangedPath:
    status: str
    path: str
    old_path: str | None = None

    def as_dict(self) -> dict[str, str]:
        item = {"status": self.status, "path": self.path}
        if self.old_path:
            item["old_path"] = self.old_path
        return item


@dataclass(frozen=True)
class ReleaseAuditReport:
    data: dict[str, Any]

    @property
    def has_drift(self) -> bool:
        return bool(self.data["issues"])

    def to_json(self) -> str:
        return (
            json.dumps(
                self.data,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )


class GitSnapshotReader:
    """Read immutable Git objects without checking out or importing upstream."""

    def __init__(self, repo: Path | str):
        self.repo = Path(repo).resolve()
        if not self.repo.is_dir():
            raise ReleaseAuditError(f"upstream checkout does not exist: {self.repo}")
        self._run_text("rev-parse", "--git-dir")

    def _run(
        self,
        *args: str,
        text: bool,
        check: bool = True,
    ) -> subprocess.CompletedProcess:
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repo), *args],
                capture_output=True,
                text=text,
                encoding="utf-8" if text else None,
                errors="replace" if text else None,
                timeout=60,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise ReleaseAuditError(f"git {' '.join(args)} failed: {exc}") from exc
        if check and result.returncode:
            stderr = (
                result.stderr.strip()
                if text
                else result.stderr.decode("utf-8", errors="replace").strip()
            )
            raise ReleaseAuditError(
                f"git {' '.join(args)} failed ({result.returncode}): {stderr}"
            )
        return result

    def _run_text(self, *args: str, check: bool = True) -> str:
        return self._run(*args, text=True, check=check).stdout.strip()

    def resolve(self, ref: str) -> str:
        sha = self._run_text("rev-parse", "--verify", f"{ref}^{{commit}}")
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise ReleaseAuditError(f"ref did not resolve to a commit: {ref}")
        return sha

    def read_text(self, commit: str, path: str) -> str:
        return self._run_text("show", f"{commit}:{path}")

    def tree_files(self, commit: str) -> list[str]:
        raw = self._run(
            "ls-tree",
            "-r",
            "--name-only",
            "-z",
            commit,
            text=False,
        ).stdout
        return sorted(
            part.decode("utf-8", errors="surrogateescape")
            for part in raw.split(b"\0")
            if part
        )

    def changed_paths(self, old: str, new: str) -> list[ChangedPath]:
        raw = self._run(
            "diff",
            "--name-status",
            "-z",
            "-M",
            old,
            new,
            "--",
            text=False,
        ).stdout
        fields = [
            part.decode("utf-8", errors="surrogateescape")
            for part in raw.split(b"\0")
            if part
        ]
        changed: list[ChangedPath] = []
        index = 0
        while index < len(fields):
            status = fields[index]
            index += 1
            kind = status[:1]
            if kind in {"R", "C"}:
                if index + 1 >= len(fields):
                    raise ReleaseAuditError("unexpected truncated git rename output")
                old_path, new_path = fields[index], fields[index + 1]
                index += 2
                changed.append(
                    ChangedPath(status=status, path=new_path, old_path=old_path)
                )
            else:
                if index >= len(fields):
                    raise ReleaseAuditError("unexpected truncated git diff output")
                changed.append(ChangedPath(status=status, path=fields[index]))
                index += 1
        return sorted(changed, key=lambda item: (item.path, item.old_path or ""))


def _assigned_dict(source: str, variable: str, path: str) -> ast.Dict:
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        raise ReleaseAuditError(f"cannot parse {path}: {exc}") from exc
    for node in tree.body:
        value: ast.AST | None = None
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == variable
            for target in node.targets
        ):
            value = node.value
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == variable
        ):
            value = node.value
        if value is not None:
            if not isinstance(value, ast.Dict):
                raise ReleaseAuditError(f"{path}:{variable} is not a dict literal")
            return value
    raise ReleaseAuditError(f"{path} does not define {variable}")


def _registry_entries(
    source: str,
    variable: str,
    path: str,
    include_targets: bool,
) -> dict[str, list[str]] | list[str]:
    dictionary = _assigned_dict(source, variable, path)
    entries: dict[str, list[str]] = {}
    keys: list[str] = []
    for key_node, value_node in zip(dictionary.keys, dictionary.values):
        if not isinstance(key_node, ast.Constant) or not isinstance(
            key_node.value, str
        ):
            raise ReleaseAuditError(f"{path}:{variable} has a non-string key")
        key = key_node.value
        if key in keys:
            raise ReleaseAuditError(f"{path}:{variable} has duplicate key {key!r}")
        keys.append(key)
        if include_targets:
            try:
                value = ast.literal_eval(value_node)
            except (ValueError, TypeError, SyntaxError) as exc:
                raise ReleaseAuditError(
                    f"{path}:{variable}[{key!r}] is not a literal target tuple"
                ) from exc
            if (
                not isinstance(value, tuple)
                or len(value) != 3
                or not all(isinstance(part, str) for part in value)
            ):
                raise ReleaseAuditError(
                    f"{path}:{variable}[{key!r}] is not a 3-string target tuple"
                )
            entries[key] = list(value)
    return dict(sorted(entries.items())) if include_targets else sorted(keys)


def _fingerprint(value: Any) -> dict[str, int | str]:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "count": len(value),
        "sha256": hashlib.sha256(encoded).hexdigest(),
    }


def snapshot_inventory(reader: GitSnapshotReader, commit: str) -> dict[str, Any]:
    inventories: dict[str, Any] = {}
    for name, (path, variable, include_targets) in _REGISTRIES.items():
        inventories[name] = _registry_entries(
            reader.read_text(commit, path),
            variable,
            path,
            include_targets,
        )
    inventories["deploy_yamls"] = sorted(
        path
        for path in reader.tree_files(commit)
        if path.startswith("vllm_omni/deploy/")
        and path.casefold().endswith((".yaml", ".yml"))
    )
    return inventories


def _inventory_delta(old: Any, new: Any) -> dict[str, Any]:
    if isinstance(old, dict) and isinstance(new, dict):
        old_keys, new_keys = set(old), set(new)
        return {
            "added": sorted(new_keys - old_keys),
            "removed": sorted(old_keys - new_keys),
            "changed": sorted(
                key for key in old_keys & new_keys if old[key] != new[key]
            ),
        }
    old_set, new_set = set(old), set(new)
    return {
        "added": sorted(new_set - old_set),
        "removed": sorted(old_set - new_set),
        "changed": [],
    }


def _load_yaml_mapping(path: Path, label: str) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise ReleaseAuditError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReleaseAuditError(f"{label} must be a YAML mapping: {path}")
    return value


def _matches(path: str, pattern: str) -> bool:
    normalized = pattern.replace("\\", "/")
    if normalized.endswith("/"):
        return path.startswith(normalized)
    return fnmatch.fnmatchcase(path, normalized)


def _route_path(path: str, baseline: dict[str, Any]) -> tuple[list[str], list[str]]:
    owners = sorted(
        owner
        for owner, patterns in (baseline.get("path_owners") or {}).items()
        if any(_matches(path, str(pattern)) for pattern in patterns or [])
    )
    ignored = sorted(
        str(item.get("reason") or "no reason supplied")
        for item in baseline.get("ignored_paths") or []
        if isinstance(item, dict) and _matches(path, str(item.get("pattern") or ""))
    )
    return owners, ignored


def _adapter_modules(path: str, manifest: dict[str, Any]) -> list[str]:
    modules: list[str] = []
    for module, spec in (manifest.get("modules") or {}).items():
        for pattern in (spec or {}).get("local_paths") or []:
            prefix = str(pattern).replace("\\", "/").rstrip("*").rstrip("/")
            if path.startswith(prefix):
                modules.append(str(module))
                break
    return sorted(modules)


def _source_path(value: str) -> str | None:
    candidate = value.strip().strip("`")
    if not candidate.startswith(_UPSTREAM_SOURCE_PREFIXES):
        return None
    candidate = candidate.split("::", 1)[0]
    candidate = re.sub(r":\d+(?:-\d+)?$", "", candidate)
    return candidate


def _path_exists(files: Iterable[str], source_path: str) -> bool:
    file_list = files if isinstance(files, list) else list(files)
    if any(char in source_path for char in "*?["):
        return any(fnmatch.fnmatchcase(path, source_path) for path in file_list)
    if source_path.endswith("/"):
        return any(path.startswith(source_path) for path in file_list)
    return source_path in file_list or any(
        path.startswith(source_path.rstrip("/") + "/") for path in file_list
    )


def _knowledge_source_issues(
    knowledge_root: Path,
    old_files: list[str],
    new_files: list[str],
    changes: list[ChangedPath],
) -> list[dict[str, str]]:
    repo_root = knowledge_root / "repos" / "vllm-omni"
    if not repo_root.is_dir():
        raise ReleaseAuditError(f"vLLM-Omni knowledge root is missing: {repo_root}")
    rename_map = {
        item.old_path: item.path
        for item in changes
        if item.old_path and item.status.startswith("R")
    }
    issues: list[dict[str, str]] = []
    for page in sorted(repo_root.rglob("*.md")):
        if any(
            part in _SOURCE_EXCLUDED_PARTS for part in page.relative_to(repo_root).parts
        ):
            continue
        text = page.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        parts = text.split("---", 2)
        if len(parts) != 3:
            continue
        try:
            metadata = yaml.safe_load(parts[1]) or {}
        except yaml.YAMLError as exc:
            issues.append(
                {
                    "kind": "knowledge_metadata_error",
                    "document": page.relative_to(knowledge_root.parent).as_posix(),
                    "detail": str(exc).splitlines()[0],
                }
            )
            continue
        sources = metadata.get("sources") or []
        if not isinstance(sources, list):
            issues.append(
                {
                    "kind": "knowledge_metadata_error",
                    "document": page.relative_to(knowledge_root.parent).as_posix(),
                    "detail": "sources must be a list",
                }
            )
            continue
        for raw_source in sources:
            if not isinstance(raw_source, str):
                continue
            source_path = _source_path(raw_source)
            if not source_path:
                continue
            if _path_exists(old_files, source_path) and not _path_exists(
                new_files, source_path
            ):
                issue = {
                    "kind": "stale_knowledge_source",
                    "document": page.relative_to(knowledge_root.parent).as_posix(),
                    "source": source_path,
                }
                if source_path in rename_map:
                    issue["renamed_to"] = rename_map[source_path]
                issues.append(issue)
    return sorted(
        issues,
        key=lambda item: (
            item["kind"],
            item.get("document", ""),
            item.get("source", ""),
        ),
    )


def _pin_issues(
    project_root: Path,
    baseline: dict[str, Any],
    audited_sha: str,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for rel in baseline.get("pin_documents") or []:
        document = project_root / str(rel)
        if not document.is_file():
            issues.append(
                {
                    "kind": "pin_document_missing",
                    "document": str(rel),
                }
            )
            continue
        pins = sorted(set(_PIN_RE.findall(document.read_text(encoding="utf-8"))))
        if not pins:
            issues.append(
                {
                    "kind": "pin_marker_missing",
                    "document": str(rel),
                }
            )
            continue
        for pin in pins:
            if not audited_sha.startswith(pin):
                issues.append(
                    {
                        "kind": "stale_pin",
                        "document": str(rel),
                        "actual": pin,
                        "expected": audited_sha,
                    }
                )
    return issues


def _policy_issues(
    project_root: Path,
    baseline: dict[str, Any],
    target_files: list[str],
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    owner_documents = baseline.get("owner_documents") or {}
    for owner, patterns in sorted((baseline.get("path_owners") or {}).items()):
        documents = owner_documents.get(owner) or []
        if not documents:
            issues.append({"kind": "owner_document_missing", "owner": str(owner)})
        for document in documents:
            if not (project_root / str(document)).is_file():
                issues.append(
                    {
                        "kind": "owner_document_missing",
                        "owner": str(owner),
                        "document": str(document),
                    }
                )
        for pattern in patterns or []:
            if not _path_exists(target_files, str(pattern)):
                issues.append(
                    {
                        "kind": "stale_source_map_path",
                        "owner": str(owner),
                        "path": str(pattern),
                    }
                )
    return issues


def audit_release(
    *,
    upstream_repo: Path | str,
    from_ref: str,
    to_ref: str,
    baseline_path: Path | str,
    adapter_manifest_path: Path | str,
    knowledge_root: Path | str,
    project_root: Path | str = _REPO_ROOT,
) -> ReleaseAuditReport:
    reader = GitSnapshotReader(upstream_repo)
    old_sha, new_sha = reader.resolve(from_ref), reader.resolve(to_ref)
    baseline_path = Path(baseline_path)
    baseline = _load_yaml_mapping(baseline_path, "release baseline")
    manifest = _load_yaml_mapping(Path(adapter_manifest_path), "adapter manifest")
    if baseline.get("schema_version") != 1:
        raise ReleaseAuditError("release baseline schema_version must be 1")

    old_inventory = snapshot_inventory(reader, old_sha)
    new_inventory = snapshot_inventory(reader, new_sha)
    changes = reader.changed_paths(old_sha, new_sha)
    old_files, new_files = reader.tree_files(old_sha), reader.tree_files(new_sha)

    issues: list[dict[str, Any]] = []
    expected_sha = str((baseline.get("upstream") or {}).get("audited_sha") or "")
    if expected_sha != new_sha:
        issues.append(
            {
                "kind": "baseline_pin_mismatch",
                "baseline": expected_sha,
                "target": new_sha,
            }
        )
    expected_old_sha = str(
        (baseline.get("upstream") or {}).get("previous_audited_sha") or ""
    )
    if expected_sha == new_sha and expected_old_sha != old_sha:
        issues.append(
            {
                "kind": "baseline_from_mismatch",
                "baseline": expected_old_sha,
                "target": old_sha,
            }
        )

    actual_fingerprints = {
        name: _fingerprint(value) for name, value in new_inventory.items()
    }
    expected_fingerprints = baseline.get("inventories") or {}
    for name in sorted(actual_fingerprints):
        if expected_fingerprints.get(name) != actual_fingerprints[name]:
            issues.append(
                {
                    "kind": "inventory_mismatch",
                    "inventory": name,
                    "baseline": expected_fingerprints.get(name),
                    "target": actual_fingerprints[name],
                }
            )

    routing: list[dict[str, Any]] = []
    adapter_uncovered: list[str] = []
    for change in changes:
        owners, ignored = _route_path(change.path, baseline)
        adapter_modules = _adapter_modules(change.path, manifest)
        route = {
            **change.as_dict(),
            "owners": owners,
            "ignored": ignored,
            "adapter_modules": adapter_modules,
            "knowledge_documents": sorted(
                {
                    str(document)
                    for owner in owners
                    for document in (baseline.get("owner_documents") or {}).get(
                        owner, []
                    )
                }
            ),
        }
        routing.append(route)
        if change.path.startswith("vllm_omni/") and not adapter_modules:
            adapter_uncovered.append(change.path)
        if not owners and not ignored:
            issues.append({"kind": "unmatched_path", "path": change.path})
        elif len(owners) > 1 or (owners and ignored):
            issues.append(
                {
                    "kind": "suspicious_path_route",
                    "path": change.path,
                    "owners": owners,
                    "ignored": ignored,
                }
            )

    issues.extend(
        _knowledge_source_issues(
            Path(knowledge_root),
            old_files,
            new_files,
            changes,
        )
    )
    issues.extend(_pin_issues(Path(project_root), baseline, new_sha))
    issues.extend(
        _policy_issues(
            Path(project_root),
            baseline,
            new_files,
        )
    )
    issues = sorted(
        issues,
        key=lambda item: (
            str(item.get("kind", "")),
            str(item.get("path", "")),
            str(item.get("document", "")),
            str(item.get("inventory", "")),
        ),
    )

    deltas = {
        name: _inventory_delta(old_inventory[name], new_inventory[name])
        for name in sorted(new_inventory)
    }
    status_counts: dict[str, int] = {}
    for change in changes:
        kind = change.status[:1]
        status_counts[kind] = status_counts.get(kind, 0) + 1

    data = {
        "schema_version": 1,
        "upstream": {
            "repository": str((baseline.get("upstream") or {}).get("repository") or ""),
            "from": {"ref": from_ref, "sha": old_sha},
            "to": {"ref": to_ref, "sha": new_sha},
        },
        "inventory": {
            "deltas": deltas,
            "target_fingerprints": actual_fingerprints,
        },
        "paths": {
            "counts": dict(sorted(status_counts.items())),
            "changes": [item.as_dict() for item in changes],
            "routing": routing,
            "adapter_uncovered": sorted(set(adapter_uncovered)),
        },
        "issues": issues,
        "result": "drift" if issues else "clean",
    }
    return ReleaseAuditReport(data)


def render_summary(report: ReleaseAuditReport) -> str:
    data = report.data
    old = data["upstream"]["from"]["sha"][:8]
    new = data["upstream"]["to"]["sha"][:8]
    deltas = data["inventory"]["deltas"]
    lines = [f"vLLM-Omni release audit: {old} -> {new}"]
    for name in ("autoregressive", "diffusion", "pipelines", "deploy_yamls"):
        delta = deltas[name]
        lines.append(
            f"  {name}: +{len(delta['added'])} -{len(delta['removed'])} "
            f"~{len(delta['changed'])}"
        )
    lines.append(
        f"  changed paths: {len(data['paths']['changes'])}; "
        "runtime-manifest gaps (reported separately): "
        f"{len(data['paths']['adapter_uncovered'])}"
    )
    lines.append(f"  issues: {len(data['issues'])}")
    for issue in data["issues"][:10]:
        subject = (
            issue.get("path") or issue.get("document") or issue.get("inventory") or ""
        )
        lines.append(f"    - {issue['kind']}: {subject}".rstrip())
    if len(data["issues"]) > 10:
        lines.append(f"    ... {len(data['issues']) - 10} more in JSON report")
    lines.append(f"RESULT: {data['result'].upper()}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit vLLM-Omni release drift without modifying either repo."
    )
    parser.add_argument("--from", dest="from_ref", required=True)
    parser.add_argument("--to", dest="to_ref", required=True)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument(
        "--baseline",
        type=Path,
        default=_REPO_ROOT / "adapters" / "vllm_omni" / "release_baseline.yaml",
    )
    parser.add_argument(
        "--adapter-manifest",
        type=Path,
        default=_REPO_ROOT / "adapters" / "vllm_omni" / "manifest.yaml",
    )
    parser.add_argument(
        "--knowledge-root",
        type=Path,
        default=_REPO_ROOT / "knowledge",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=_REPO_ROOT,
        help="root used to resolve pin_documents from the baseline",
    )
    parser.add_argument("--json-output", type=Path)
    parser.add_argument(
        "--mode",
        choices=("enforce", "report-only"),
        default="enforce",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = audit_release(
            upstream_repo=args.repo,
            from_ref=args.from_ref,
            to_ref=args.to_ref,
            baseline_path=args.baseline,
            adapter_manifest_path=args.adapter_manifest,
            knowledge_root=args.knowledge_root,
            project_root=args.project_root,
        )
    except ReleaseAuditError as exc:
        print(f"release audit error: {exc}")
        return 2
    print(render_summary(report))
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(report.to_json(), encoding="utf-8")
        print(f"JSON report: {args.json_output}")
    return 1 if report.has_drift and args.mode == "enforce" else 0


if __name__ == "__main__":
    raise SystemExit(main())
