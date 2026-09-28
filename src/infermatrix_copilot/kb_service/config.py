"""Per-repository knowledge-lifecycle configuration and the repository registry.

Every difference between repositories lives in each adapter's human-reviewed
``knowledge_lifecycle`` manifest section; the service code never names a
repository. ``general`` (the cross-repository slice) is configured by the
service itself because it has no adapter.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from ..adapters import AdapterError, AdapterRegistry, RepoAdapter

MODES = ("shadow", "auto_merge")
TRIGGERS = ("github_release", "tag_pattern", "branch_cut", "none")
VISIBILITIES = ("public", "private")
GENERAL = "general"
_NAME = re.compile(r"[a-z0-9][a-z0-9._-]*")
_FULL_NAME = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
_KEYS = {
    "enabled", "mode", "knowledge_dir", "intake", "release", "sweep",
    "upstream_visibility", "circuit_breaker", "protected_rules",
    "calibration_set", "model_dir",
}


class LifecycleConfigError(ValueError):
    """An adapter's knowledge_lifecycle section is invalid."""


@dataclass(frozen=True)
class IntakeConfig:
    merged_prs: bool = True
    copilot_runs: bool = True
    human_prs: bool = True
    daily_model_budget_usd: float = 0.0


@dataclass(frozen=True)
class ReleaseConfig:
    trigger: str = "none"
    tag_pattern: str = ""
    auditor: str = ""  # plugin path relative to the adapter directory


@dataclass(frozen=True)
class RepoLifecycle:
    repo: str                      # knowledge repo name, or "general"
    full_name: str                 # upstream owner/name ("" for general)
    enabled: bool
    mode: str
    knowledge_dir: str             # "repos/<repo>" or "general"
    intake: IntakeConfig = field(default_factory=IntakeConfig)
    release: ReleaseConfig = field(default_factory=ReleaseConfig)
    fallback_interval_days: int = 30
    upstream_visibility: str = "public"
    retire_ratio: float = 0.10
    max_files: int = 50
    protected_rules: tuple[str, ...] = ()
    calibration_set: str = ""      # directory relative to the adapter (ships in the wheel)
    model_dir: str = ""
    adapter_dir: Path | None = None

    @property
    def auto_merge(self) -> bool:
        return self.enabled and self.mode == "auto_merge"

    @property
    def publishes(self) -> bool:
        """Whether anything about this repository may appear in the PUBLIC
        knowledge repository (PRs, verdict comments, reports)."""
        return self.upstream_visibility == "public"


def _bool(value: object, where: str) -> bool:
    if not isinstance(value, bool):
        raise LifecycleConfigError(f"{where} must be true or false")
    return value


def _mapping(value: object, where: str, allowed: set[str]) -> dict:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise LifecycleConfigError(f"{where} must be a mapping")
    unknown = set(value) - allowed
    if unknown:
        raise LifecycleConfigError(f"{where} has unknown keys {sorted(unknown)}")
    return value


def parse_lifecycle(adapter: RepoAdapter) -> RepoLifecycle | None:
    """The adapter's lifecycle, or None when it has no knowledge_lifecycle."""
    section = adapter.manifest.get("knowledge_lifecycle")
    if section is None:
        return None
    where = f"adapters/{adapter.name}/manifest.yaml knowledge_lifecycle"
    data = _mapping(section, where, _KEYS)
    repo_meta = adapter.manifest.get("repo") or {}
    knowledge = adapter.manifest.get("knowledge") or {}
    repo_subdir = str(knowledge.get("repo_subdir") or "").strip("/")
    if not repo_subdir.startswith("repos/"):
        raise LifecycleConfigError(f"{where}: adapter knowledge.repo_subdir must be repos/<repo>")
    repo = repo_subdir.removeprefix("repos/")
    if not _NAME.fullmatch(repo):
        raise LifecycleConfigError(f"{where}: invalid repo name {repo!r}")
    full_name = str(repo_meta.get("full_name") or "")
    if not _FULL_NAME.fullmatch(full_name):
        raise LifecycleConfigError(f"{where}: adapter repo.full_name must be owner/name")
    enabled = _bool(data.get("enabled", False), f"{where}.enabled")
    mode = str(data.get("mode", "shadow"))
    if mode not in MODES:
        raise LifecycleConfigError(f"{where}.mode must be one of {MODES}")
    knowledge_dir = str(data.get("knowledge_dir", repo_subdir)).strip("/")
    if knowledge_dir != repo_subdir:
        raise LifecycleConfigError(f"{where}.knowledge_dir must equal the adapter repo_subdir {repo_subdir}")
    intake = _mapping(data.get("intake"), f"{where}.intake",
                      {"merged_prs", "copilot_runs", "human_prs", "daily_model_budget_usd"})
    release = _mapping(data.get("release"), f"{where}.release", {"trigger", "tag_pattern", "auditor"})
    sweep = _mapping(data.get("sweep"), f"{where}.sweep", {"fallback_interval_days"})
    breaker = _mapping(data.get("circuit_breaker"), f"{where}.circuit_breaker",
                       {"retire_ratio", "max_files"})
    trigger = str(release.get("trigger", "none"))
    if trigger not in TRIGGERS:
        raise LifecycleConfigError(f"{where}.release.trigger must be one of {TRIGGERS}")
    if trigger == "tag_pattern" and not release.get("tag_pattern"):
        raise LifecycleConfigError(f"{where}.release.tag_pattern is required for tag_pattern")
    auditor = str(release.get("auditor") or "")
    if auditor and not (Path(adapter.root) / auditor).is_file():
        raise LifecycleConfigError(f"{where}.release.auditor does not exist: {auditor}")
    visibility = str(data.get("upstream_visibility", "public"))
    if visibility not in VISIBILITIES:
        raise LifecycleConfigError(f"{where}.upstream_visibility must be one of {VISIBILITIES}")
    if visibility == "private" and mode == "auto_merge":
        # the knowledge repository is public: a private upstream may never publish
        raise LifecycleConfigError(f"{where}: a private upstream can only run in shadow mode")
    retire_ratio = float(breaker.get("retire_ratio", 0.10))
    max_files = int(breaker.get("max_files", 50))
    if not 0 < retire_ratio <= 1 or max_files < 1:
        raise LifecycleConfigError(f"{where}.circuit_breaker values are out of range")
    budget = float(intake.get("daily_model_budget_usd", 0.0))
    if budget < 0:
        raise LifecycleConfigError(f"{where}.intake.daily_model_budget_usd must be >= 0")
    protected = data.get("protected_rules") or []
    if not isinstance(protected, list) or any(not isinstance(item, str) for item in protected):
        raise LifecycleConfigError(f"{where}.protected_rules must be a list of rule IDs")
    if mode == "auto_merge" and not data.get("calibration_set"):
        raise LifecycleConfigError(f"{where}: auto_merge requires a calibration_set")
    return RepoLifecycle(
        repo=repo,
        full_name=full_name,
        enabled=enabled,
        mode=mode,
        knowledge_dir=knowledge_dir,
        intake=IntakeConfig(
            merged_prs=_bool(intake.get("merged_prs", True), f"{where}.intake.merged_prs"),
            copilot_runs=_bool(intake.get("copilot_runs", True), f"{where}.intake.copilot_runs"),
            human_prs=_bool(intake.get("human_prs", True), f"{where}.intake.human_prs"),
            daily_model_budget_usd=budget,
        ),
        release=ReleaseConfig(trigger=trigger, tag_pattern=str(release.get("tag_pattern") or ""),
                              auditor=auditor),
        fallback_interval_days=int(sweep.get("fallback_interval_days", 30)),
        upstream_visibility=visibility,
        retire_ratio=retire_ratio,
        max_files=max_files,
        protected_rules=tuple(protected),
        calibration_set=str(data.get("calibration_set") or ""),
        model_dir=str(data.get("model_dir") or ""),
        adapter_dir=Path(adapter.root),
    )


def general_lifecycle(*, enabled: bool, mode: str = "shadow") -> RepoLifecycle:
    """The cross-repository slice: sources are Copilot runs and human PRs only,
    no release events, monthly full sweep."""
    if mode not in MODES:
        raise LifecycleConfigError(f"general mode must be one of {MODES}")
    return RepoLifecycle(
        repo=GENERAL, full_name="", enabled=enabled, mode=mode, knowledge_dir=GENERAL,
        intake=IntakeConfig(merged_prs=False),
        release=ReleaseConfig(trigger="none"),
    )


def load_registry(adapters_dir: str | Path, *, general: RepoLifecycle | None = None
                  ) -> dict[str, RepoLifecycle]:
    """Every adapter with a knowledge_lifecycle section, keyed by repo name.

    An invalid section raises: a misconfigured repository must never run with
    guessed settings. Adapters without the section are simply not served.
    """
    registry: dict[str, RepoLifecycle] = {}
    try:
        adapters = AdapterRegistry(adapters_dir).all()
    except AdapterError as exc:
        raise LifecycleConfigError(f"adapters cannot be loaded: {exc}") from exc
    for adapter in adapters:
        lifecycle = parse_lifecycle(adapter)
        if lifecycle is None:
            continue
        if lifecycle.repo in registry:
            raise LifecycleConfigError(f"two adapters claim knowledge repo {lifecycle.repo}")
        registry[lifecycle.repo] = lifecycle
    if general is not None:
        registry[GENERAL] = general
    return registry
