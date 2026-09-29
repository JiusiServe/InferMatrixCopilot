"""Repo-neutral release-audit plugin contract for the knowledge service.

A repository whose releases can invalidate knowledge ships an audit plugin in
its adapter directory (packaged runtime data, so it loads from an installed
wheel). The plugin is a Python file exposing::

    def audit_for_knowledge(*, upstream_repo, from_ref, to_ref,
                            knowledge_root, project_root) -> dict

returning at least ``issues`` (knowledge-document problems, enforced),
``reconciliation`` (adapter/baseline maintenance, reported only),
``generated_baseline`` and ``upstream.from/to.sha``. The audit runs against a
baseline generated for exactly the audited SHA pair, so a knowledge change never
waits for the committed adapter baseline to be advanced; the reconciliation list
is what the adapter-baseline companion PR must fix.

Repositories without a plugin fall back to the generic reference-existence
checks in L1; nothing here names a repository.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Callable

ENTRY_POINT = "audit_for_knowledge"


class ReleaseAuditPluginError(RuntimeError):
    """The configured plugin is missing, escapes its adapter, or misbehaves."""


@dataclass(frozen=True)
class ReleaseAuditResult:
    from_sha: str
    to_sha: str
    issues: tuple[dict, ...]
    reconciliation: tuple[dict, ...]
    generated_baseline: dict = field(default_factory=dict)
    data: dict = field(default_factory=dict, compare=False)

    @property
    def enforced_clean(self) -> bool:
        return not self.issues


def load_release_auditor(adapter_dir: str | Path, module: str) -> Callable[..., dict]:
    """Load ``module`` (a path relative to ``adapter_dir``) and return its entry."""
    adapter_dir = Path(adapter_dir).resolve()
    pure = PurePosixPath(str(module).replace("\\", "/"))
    if not str(module) or pure.is_absolute() or ".." in pure.parts or pure.suffix != ".py":
        raise ReleaseAuditPluginError(f"audit plugin must be a .py path inside the adapter: {module!r}")
    path = (adapter_dir / pure).resolve()
    try:
        path.relative_to(adapter_dir)
    except ValueError as exc:
        raise ReleaseAuditPluginError(f"audit plugin escapes its adapter: {module!r}") from exc
    if not path.is_file():
        raise ReleaseAuditPluginError(f"audit plugin is missing: {path}")
    name = f"infermatrix_release_audit_{abs(hash(str(path)))}"
    loaded = sys.modules.get(name)
    if loaded is None:
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise ReleaseAuditPluginError(f"audit plugin cannot be loaded: {path}")
        loaded = importlib.util.module_from_spec(spec)
        sys.modules[name] = loaded
        try:
            spec.loader.exec_module(loaded)
        except Exception:
            sys.modules.pop(name, None)
            raise
    entry = getattr(loaded, ENTRY_POINT, None)
    if not callable(entry):
        raise ReleaseAuditPluginError(f"audit plugin has no {ENTRY_POINT}(): {path}")
    return entry


def run_release_audit(
    adapter_dir: str | Path,
    module: str,
    *,
    upstream_repo: str | Path,
    from_ref: str,
    to_ref: str,
    knowledge_root: str | Path,
    project_root: str | Path,
) -> ReleaseAuditResult:
    entry = load_release_auditor(adapter_dir, module)
    data: dict[str, Any] = entry(
        upstream_repo=upstream_repo,
        from_ref=from_ref,
        to_ref=to_ref,
        knowledge_root=knowledge_root,
        project_root=project_root,
    )
    return _result(data)


_SHA = re.compile(r"[0-9a-f]{40}")


def _result(data: object) -> ReleaseAuditResult:
    """Validate the plugin's report strictly: a malformed report must never
    read as a clean audit."""
    def bad(reason: str) -> ReleaseAuditPluginError:
        return ReleaseAuditPluginError(f"audit plugin returned a malformed report: {reason}")

    if not isinstance(data, dict):
        raise bad("report must be a mapping")
    upstream = data.get("upstream")
    if not isinstance(upstream, dict):
        raise bad("upstream must be a mapping")
    shas = []
    for end in ("from", "to"):
        item = upstream.get(end)
        sha = item.get("sha") if isinstance(item, dict) else None
        if not isinstance(sha, str) or not _SHA.fullmatch(sha):
            raise bad(f"upstream.{end}.sha must be a 40-character hex SHA")
        shas.append(sha)
    lists = {}
    for key in ("issues", "reconciliation"):
        value = data.get(key)
        if not isinstance(value, list) or any(
            not isinstance(item, dict) or not isinstance(item.get("kind"), str) or not item["kind"]
            for item in value
        ):
            raise bad(f"{key} must be a list of {{kind, ...}} mappings")
        lists[key] = tuple(value)
    baseline = data.get("generated_baseline")
    if not isinstance(baseline, dict) or not isinstance(baseline.get("upstream"), dict) \
            or baseline["upstream"].get("audited_sha") != shas[1]:
        raise bad("generated_baseline.upstream.audited_sha must equal upstream.to.sha")
    return ReleaseAuditResult(
        from_sha=shas[0],
        to_sha=shas[1],
        issues=lists["issues"],
        reconciliation=lists["reconciliation"],
        generated_baseline=dict(baseline),
        data=data,
    )
