"""RepoAdapter — repo structure knowledge at the edge (DESIGN §V2.3.0 two-tier repo knowledge).

Declarative manifest.yaml; high-risk sections (push, repo) are human-only —
agent-side updates to them are rejected at this layer. Unknown repos get a
deterministic fingerprint + a DRAFT adapter that stops for human review.
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

# Always-on briefing byte cap. The curated hard-gate + navigation pages are
# high-signal and injected into the static (cached) prompt prefix, so a generous
# cap is fine; deeper guides/incidents are pulled on demand via the doc tools.
_BRIEFING_CAP = 8000


class AdapterError(Exception):
    """Raised for any adapter-layer violation: a missing/invalid manifest, an
    unknown adapter name, or an agent-side write to a high-risk section."""


@dataclass
class RepoAdapter:
    """A loaded repo adapter: its `name`, on-disk `root`, and parsed `manifest`
    (manifest.yaml). Exposes the manifest as typed views and locates the repo's
    store/skills/profile dirs — the single edge object steps consult for a
    target repo's structure and policy."""

    name: str
    root: Path
    manifest: dict

    @property
    def status(self) -> str:
        """Lifecycle status from the manifest (`draft` until a human activates)."""
        return self.manifest.get("status", "draft")

    @property
    def repo_path(self) -> str:
        """Filesystem path of the target repo, or "" if the manifest omits it."""
        return self.manifest.get("repo", {}).get("path", "")

    @property
    def protected_branches(self) -> list[str]:
        """Branches a push may never target (defaults to `["main"]`) — read by the
        push authorization gate."""
        return list(self.manifest.get("push", {}).get("protected_branches", ["main"]))

    @property
    def modules(self) -> dict:
        """The manifest's module map (name → spec), or {} when undeclared."""
        return self.manifest.get("modules", {}) or {}

    def module_for_path(self, path: str) -> str | None:
        """Return the module owning `path` — the first module whose declared
        `local_paths` prefix (trailing glob/slash stripped) matches — or None when
        no module claims it."""
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
        """Directory holding this repo's promoted `SKILL.md` runbooks."""
        return self.root / "skills"

    @property
    def debug_memory_db(self) -> Path:
        """Path to this repo's `DebugMemory` SQLite database."""
        return self.root / "store" / "debug_memory.db"

    @property
    def profile_dir(self) -> Path:
        """Directory holding this repo's `ProfileStore` (profile.yaml + logs)."""
        return self.root / "profile"

    @property
    def knowledge_dir(self) -> Path:
        """Root of the referenced knowledge base (a git submodule) when the
        manifest declares a `knowledge:` section, else the conventional
        `knowledge/` dir. The curated community docs live under here."""
        rel = (self.manifest.get("knowledge") or {}).get("dir", "knowledge")
        return self.root / rel

    @property
    def knowledge_repo_dir(self) -> Path:
        """The repo-specific subtree of the knowledge base (e.g.
        `knowledge/repos/<repo>`), where this repo's docs + `_index.md` live.
        Falls back to `knowledge_dir` when no `repo_subdir` is declared."""
        sub = (self.manifest.get("knowledge") or {}).get("repo_subdir", "")
        return (self.knowledge_dir / sub) if sub else self.knowledge_dir

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
        """The repo's always-on prompt slice. Prefers the curated knowledge base
        — the `knowledge.briefing_docs` (hard-gate rules + navigation index) from
        the referenced community submodule, concatenated and capped. Deeper
        guides/incidents are NOT injected here; they are pulled on demand via the
        doc tools (nothing is lost, just not dumped wholesale). Falls back to a
        legacy AI `profile.yaml` when one exists, else empty."""
        kn = self.manifest.get("knowledge") or {}
        docs = kn.get("briefing_docs") or []
        kdir = self.knowledge_dir
        if docs and kdir.exists():
            parts = []
            for rel in docs:
                p = kdir / rel
                if p.exists():
                    parts.append(p.read_text(encoding="utf-8", errors="replace").strip())
            if parts:
                header = (f"Curated repo knowledge (source: {kn.get('source', '')}; "
                          "read the linked deeper docs with the doc_read / doc_search "
                          "tools — paths are relative to the knowledge base):\n\n")
                body = header + "\n\n---\n\n".join(parts)
                if len(body) > _BRIEFING_CAP:
                    body = (body[:_BRIEFING_CAP]
                            + f"\n\n...[briefing capped at {_BRIEFING_CAP} chars — "
                              "use doc_read for the full pages]")
                return body
        if (self.profile_dir / "profile.yaml").exists():  # legacy AI profile
            from ..profiles.store import ProfileStore

            return ProfileStore(self.profile_dir).render_briefing()
        return ""


def load_adapter(adapter_dir: str | Path) -> RepoAdapter:
    """Load and validate the adapter at `adapter_dir`, returning a `RepoAdapter`.
    Raises `AdapterError` if `manifest.yaml` is absent or any `REQUIRED_SECTIONS`
    (name, repo) is missing — the fail-closed check before a adapter is trusted."""
    root = Path(adapter_dir)
    manifest_path = root / "manifest.yaml"
    if not manifest_path.exists():
        raise AdapterError(f"no manifest.yaml in {root}")
    manifest = yaml.safe_load(manifest_path.read_text()) or {}
    for section in REQUIRED_SECTIONS:
        if section not in manifest:
            raise AdapterError(f"adapter {root.name}: missing required section '{section}'")
    return RepoAdapter(name=manifest["name"], root=root, manifest=manifest)


def update_manifest(adapter: RepoAdapter, section: str, value: dict, *, actor: str = "agent") -> None:
    """Agent-proposed adapter updates. High-risk sections are human-only."""
    if actor != "human" and section in HIGH_RISK_SECTIONS:
        raise AdapterError(
            f"section '{section}' is high-risk (human-only); propose a candidate instead"
        )
    adapter.manifest[section] = value
    (adapter.root / "manifest.yaml").write_text(
        yaml.safe_dump(adapter.manifest, sort_keys=False, allow_unicode=True)
    )


class AdapterRegistry:
    """Directory of installed adapters. Enumerates and resolves them (by explicit
    name or by target repo path) for a run's bootstrap."""

    def __init__(self, adapters_dir: str | Path):
        """Bind to `adapters_dir`, the directory whose immediate subdirs each hold
        a `manifest.yaml`. Not required to exist yet."""
        self.adapters_dir = Path(adapters_dir)

    def all(self) -> list[RepoAdapter]:
        """Load every adapter under the dir (each subdir with a `manifest.yaml`),
        sorted by path; empty list when the dir is absent."""
        out = []
        if self.adapters_dir.exists():
            for d in sorted(self.adapters_dir.iterdir()):
                if (d / "manifest.yaml").exists():
                    out.append(load_adapter(d))
        return out

    def resolve(self, *, name: str | None = None, repo_path: str | None = None) -> RepoAdapter | None:
        """--adapter name wins; then repo-path match; None -> caller bootstraps."""
        adapters = self.all()
        if name:
            for p in adapters:
                if p.name == name:
                    return p
            raise AdapterError(f"no adapter named {name!r}")
        if repo_path:
            resolved = str(Path(repo_path).resolve())
            for p in adapters:
                if p.repo_path and str(Path(p.repo_path).resolve()) == resolved:
                    return p
        return None


# -- Phase 0 bootstrap (read-only wrt the target repo) ------------------------

def _git(repo: Path, *args: str) -> str:
    """Run `git <args>` in `repo` and return its stripped stdout — the read-only
    git helper the deterministic fingerprint uses."""
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


def draft_adapter(fingerprint: dict, adapters_dir: str | Path) -> Path:
    """Persist a DRAFT adapter + bootstrap report, then STOP (human review gate)."""
    name = re.sub(r"[^a-z0-9_]+", "_", Path(fingerprint["path"]).name.lower())
    root = Path(adapters_dir) / name
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
    (root / "manifest.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True)
    )
    (root / "BOOTSTRAP_REPORT.md").write_text(
        f"# Bootstrap report — {name}\n\n"
        "Draft adapter generated from a deterministic fingerprint. Review and set\n"
        "`status: active` (and fill `modules:`) before code-modifying runs.\n\n"
        "```yaml\n" + yaml.safe_dump(fingerprint, sort_keys=False) + "```\n"
    )
    return root
