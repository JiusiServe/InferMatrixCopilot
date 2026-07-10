"""RepoPlugin — repo structure knowledge at the edge (DESIGN_REPO_PLUGINS).

Declarative plugin.yaml; high-risk sections (push, repo) are human-only —
agent-side updates to them are rejected at this layer. Unknown repos get a
deterministic fingerprint + a DRAFT plugin that stops for human review.
"""

from __future__ import annotations

import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

import yaml

HIGH_RISK_SECTIONS = ("push", "repo", "upstream")
REQUIRED_SECTIONS = ("name", "repo")


class PluginError(Exception):
    pass


@dataclass
class RepoPlugin:
    name: str
    root: Path
    manifest: dict

    @property
    def status(self) -> str:
        return self.manifest.get("status", "draft")

    @property
    def repo_path(self) -> str:
        return self.manifest.get("repo", {}).get("path", "")

    @property
    def protected_branches(self) -> list[str]:
        return list(self.manifest.get("push", {}).get("protected_branches", ["main"]))

    @property
    def modules(self) -> dict:
        return self.manifest.get("modules", {}) or {}

    def module_for_path(self, path: str) -> str | None:
        for module, spec in self.modules.items():
            for pattern in (spec or {}).get("local_paths", []):
                if path.startswith(pattern.rstrip("*").rstrip("/")):
                    return module
        return None

    @property
    def high_risk_modules(self) -> list[str]:
        """Modules declared `risk: high` — feeds the patch-review trigger."""
        return [m for m, spec in self.modules.items()
                if str((spec or {}).get("risk", "")).lower() == "high"]

    @property
    def skills_dir(self) -> Path:
        return self.root / "skills"

    @property
    def debug_memory_db(self) -> Path:
        return self.root / "store" / "debug_memory.db"

    @property
    def profile_dir(self) -> Path:
        return self.root / "profile"

    @property
    def capabilities(self) -> set[str]:
        """What this repo's profile provides — matched against playbook
        `requires:` (design §V2.2.3). Derived facts plus the manifest's
        explicit `capabilities:` list."""
        caps: set[str] = set(self.manifest.get("capabilities") or [])
        repo = self.manifest.get("repo", {}) or {}
        if repo.get("path"):
            caps.add("repo.path")
        if repo.get("language"):
            caps.add(f"language.{repo['language']}")
        if (self.manifest.get("ci") or {}).get("provider"):
            caps.add("ci.provider")
        if (self.manifest.get("upstream") or {}).get("kind"):
            caps.add(f"upstream.{self.manifest['upstream']['kind']}")
        if self.modules:
            caps.add("modules")
        return caps

    def briefing(self) -> str:
        """The repo's always-on prompt slice (empty when no profile exists)."""
        if not (self.profile_dir / "profile.yaml").exists():
            return ""
        from ..profiles.store import ProfileStore

        return ProfileStore(self.profile_dir).render_briefing()


def load_plugin(plugin_dir: str | Path) -> RepoPlugin:
    root = Path(plugin_dir)
    manifest_path = root / "plugin.yaml"
    if not manifest_path.exists():
        raise PluginError(f"no plugin.yaml in {root}")
    manifest = yaml.safe_load(manifest_path.read_text()) or {}
    for section in REQUIRED_SECTIONS:
        if section not in manifest:
            raise PluginError(f"plugin {root.name}: missing required section '{section}'")
    return RepoPlugin(name=manifest["name"], root=root, manifest=manifest)


def update_manifest(plugin: RepoPlugin, section: str, value: dict, *, actor: str = "agent") -> None:
    """Agent-proposed plugin updates. High-risk sections are human-only."""
    if actor != "human" and section in HIGH_RISK_SECTIONS:
        raise PluginError(
            f"section '{section}' is high-risk (human-only); propose a candidate instead"
        )
    plugin.manifest[section] = value
    (plugin.root / "plugin.yaml").write_text(
        yaml.safe_dump(plugin.manifest, sort_keys=False, allow_unicode=True)
    )


class PluginRegistry:
    def __init__(self, plugins_dir: str | Path):
        self.plugins_dir = Path(plugins_dir)

    def all(self) -> list[RepoPlugin]:
        out = []
        if self.plugins_dir.exists():
            for d in sorted(self.plugins_dir.iterdir()):
                if (d / "plugin.yaml").exists():
                    out.append(load_plugin(d))
        return out

    def resolve(self, *, name: str | None = None, repo_path: str | None = None) -> RepoPlugin | None:
        """--plugin name wins; then repo-path match; None -> caller bootstraps."""
        plugins = self.all()
        if name:
            for p in plugins:
                if p.name == name:
                    return p
            raise PluginError(f"no plugin named {name!r}")
        if repo_path:
            resolved = str(Path(repo_path).resolve())
            for p in plugins:
                if p.repo_path and str(Path(p.repo_path).resolve()) == resolved:
                    return p
        return None


# -- Phase 0 bootstrap (read-only wrt the target repo) ------------------------

def _git(repo: Path, *args: str) -> str:
    out = subprocess.run(["git", *args], cwd=str(repo), capture_output=True,
                         text=True, timeout=30)
    return out.stdout.strip()


def fingerprint_repo(repo_path: str | Path) -> dict:
    """Deterministic, no-LLM repo fingerprint. Never modifies the target repo."""
    repo = Path(repo_path)
    suffix_counts: dict[str, int] = {}
    for p in list(repo.rglob("*"))[:5000]:
        if p.is_file() and not any(part.startswith(".") for part in p.parts):
            suffix_counts[p.suffix] = suffix_counts.get(p.suffix, 0) + 1
    language = max(
        (("python", suffix_counts.get(".py", 0)),
         ("rust", suffix_counts.get(".rs", 0)),
         ("go", suffix_counts.get(".go", 0)),
         ("javascript", suffix_counts.get(".ts", 0) + suffix_counts.get(".js", 0))),
        key=lambda kv: kv[1],
    )[0]
    return {
        "path": str(repo.resolve()),
        "remotes": _git(repo, "remote", "-v").splitlines()[:4],
        "default_branch": _git(repo, "rev-parse", "--abbrev-ref", "HEAD") or "main",
        "language": language,
        "has_buildkite": (repo / ".buildkite").exists(),
        "has_github_actions": (repo / ".github" / "workflows").exists(),
        "has_tests": any((repo / d).exists() for d in ("tests", "test")),
        "top_level": sorted(p.name for p in repo.iterdir() if p.is_dir()
                            and not p.name.startswith("."))[:20],
    }


def draft_plugin(fingerprint: dict, plugins_dir: str | Path) -> Path:
    """Persist a DRAFT plugin + bootstrap report, then STOP (human review gate)."""
    name = re.sub(r"[^a-z0-9_]+", "_", Path(fingerprint["path"]).name.lower())
    root = Path(plugins_dir) / name
    root.mkdir(parents=True, exist_ok=True)
    manifest = {
        "name": name,
        "status": "draft",  # human flips to active
        "created_by": "bootstrap",
        "created_at": time.strftime("%Y-%m-%d"),
        "repo": {
            "path": fingerprint["path"],
            "default_branch": fingerprint["default_branch"],
            "language": fingerprint["language"],
        },
        "modules": {},
        "validation": {"has_tests": fingerprint["has_tests"]},
        "ci": {
            "buildkite": fingerprint["has_buildkite"],
            "github_actions": fingerprint["has_github_actions"],
        },
        "push": {"default_remote": "origin", "protected_branches": ["main"],
                 "allowed": False},
    }
    (root / "plugin.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True)
    )
    (root / "BOOTSTRAP_REPORT.md").write_text(
        f"# Bootstrap report — {name}\n\n"
        "Draft plugin generated from a deterministic fingerprint. Review and set\n"
        "`status: active` (and fill `modules:`) before code-modifying runs.\n\n"
        "```yaml\n" + yaml.safe_dump(fingerprint, sort_keys=False) + "```\n"
    )
    return root
