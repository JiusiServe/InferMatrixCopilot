"""One repository context for planning capabilities and execution policy."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..adapters.base import AdapterError, AdapterNotFound, AdapterRegistry, RepoAdapter
from ..config import Settings
from ..task_spec import TaskSpec


@dataclass(frozen=True)
class RepositoryContext:
    repo_path: str
    capabilities: frozenset[str] | None
    protected_branches: tuple[str, ...]
    high_risk_modules: tuple[str, ...]


class RepositoryContextResolver:
    """Resolve one run's checkout and adapter policy without hiding bad adapters."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def adapter_for(self, repo: str) -> RepoAdapter | None:
        name = repo.replace("-", "_")
        try:
            return AdapterRegistry(self.settings.adapters_dir).resolve(name=name)
        except AdapterNotFound:
            # A directory with a missing or mismatched manifest is a broken
            # known adapter, not the compatibility path for an unknown repo.
            if (Path(self.settings.adapters_dir) / name).exists():
                raise AdapterError(
                    f"adapter directory {name!r} exists but did not "
                    "load/resolve (missing manifest.yaml or mismatched "
                    "name:) — refusing to use unknown repository policy"
                )
            return None
        except (OSError, UnicodeError) as exc:
            raise AdapterError(
                f"cannot inspect repository adapters for {repo!r}: {exc}"
            ) from exc

    def ambient_repo_path(self, repo: str) -> str:
        return self.for_spec(TaskSpec(kind="repo_rebase", repo=repo)).repo_path

    def repo_path_for(self, spec: TaskSpec) -> str:
        return self.for_spec(spec).repo_path

    def for_spec(self, spec: TaskSpec) -> RepositoryContext:
        adapter = self.adapter_for(spec.repo)
        configured = self.settings.repo_path(spec.repo)
        repo_path = spec.repo_path or (str(configured) if configured else "")
        if adapter is None:
            # No adapter means capabilities are unknown if a checkout exists;
            # the planner's v1 compatibility behavior deliberately uses None.
            capabilities = None if repo_path else frozenset()
            protected = tuple(self.settings.protected_branches)
            high_risk = ()
        else:
            try:
                manifest = adapter.manifest
                raw_path = manifest["repo"].get("path", "")
                raw_capabilities = manifest.get("capabilities")
                raw_modules = manifest.get("modules")
                raw_push = manifest.get("push")
                if "path" in manifest["repo"] and not isinstance(raw_path, str):
                    raise TypeError("repo.path must be text")
                if raw_capabilities is None:
                    raw_capabilities = []
                if (not isinstance(raw_capabilities, list)
                        or not all(isinstance(item, str) for item in raw_capabilities)):
                    raise TypeError("capabilities must be a list of text")
                if raw_modules is None:
                    raw_modules = {}
                if not isinstance(raw_modules, dict):
                    raise TypeError("modules must be a mapping")
                if raw_push is None:
                    raw_push = {}
                if not isinstance(raw_push, dict):
                    raise TypeError("push must be a mapping")
                raw_branches = raw_push.get("protected_branches", ["main"])
                if (not isinstance(raw_branches, list)
                        or not all(isinstance(item, str) for item in raw_branches)):
                    raise TypeError("push.protected_branches must be a list of text")
                if not repo_path:
                    repo_path = adapter.repo_path
                if not isinstance(repo_path, str):
                    raise TypeError("repo.path must be text")
                known = set(adapter.capabilities)
                protected = tuple(adapter.protected_branches)
                high_risk = tuple(adapter.high_risk_modules)
                if not all(isinstance(item, str) for item in (*known, *protected, *high_risk)):
                    raise TypeError("capabilities and policy entries must be text")
            except (AttributeError, TypeError, ValueError) as exc:
                raise AdapterError(
                    f"adapter {adapter.name!r} has invalid repository policy: {exc}"
                ) from exc
            known.discard("repo.path")
            if repo_path:
                known.add("repo.path")
            capabilities = frozenset(known)
        return RepositoryContext(
            repo_path=repo_path,
            capabilities=capabilities,
            protected_branches=protected,
            high_risk_modules=high_risk,
        )
