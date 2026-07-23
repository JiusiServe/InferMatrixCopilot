"""RepoAdapter — repo structure knowledge at the edge (DESIGN §V2.3.0 two-tier repo knowledge).

Declarative manifest.yaml; high-risk sections (push, repo) are human-only —
agent-side updates to them are rejected at this layer. Unknown repos get a
deterministic fingerprint + a DRAFT adapter that stops for human review.
"""

from __future__ import annotations

import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

import yaml

HIGH_RISK_SECTIONS = ("push", "repo", "upstream")


def expand_path(value: str) -> str:
    """Expand `~` and `${VAR}` in a manifest path so committed adapters stay
    machine-independent. An unset variable yields "" (treated as "not declared",
    which degrades through the normal capability-gap path) rather than a bogus
    literal path containing `${...}`."""
    if not value:
        return ""
    expanded = os.path.expanduser(os.path.expandvars(value))
    return "" if "$" in expanded else expanded
REQUIRED_SECTIONS = ("name", "repo")

# Always-on briefing byte cap. The curated hard-gate + navigation pages are
# high-signal and injected into the static (cached) prompt prefix, so a generous
# cap is fine; deeper guides/incidents are pulled on demand via the doc tools.
_BRIEFING_CAP = 8000


def _without_frontmatter(text: str) -> str:
    """Drop a leading YAML frontmatter block — page metadata (SCHEMA.md), not
    briefing content the agent should spend prompt budget on."""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            return parts[2]
    return text


def render_briefing_docs(root: Path | str, docs: list[str], *, header: str = "",
                         cap: int = _BRIEFING_CAP,
                         warnings: list[str] | None = None) -> str:
    """Concatenate the `docs` (paths relative to `root`) into one capped briefing
    slice, prefixed by `header`. Missing docs are skipped (never fatal); page
    frontmatter is stripped. Returns "" when none exist. Shared by the general
    and repo-specific briefing layers so both render identically."""
    root = Path(root).resolve()
    parts: list[str] = []
    for rel in docs:
        p = (root / rel).resolve()
        try:
            p.relative_to(root)
        except ValueError:
            if warnings is not None:
                warnings.append(f"briefing path escapes knowledge root: {rel}")
            continue
        if not p.is_file() or p.suffix.casefold() != ".md":
            if warnings is not None:
                warnings.append(f"briefing document missing or not Markdown: {rel}")
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        parts.append(_without_frontmatter(text).strip())
    if not parts:
        return ""
    body = ((header + "\n\n") if header else "") + "\n\n---\n\n".join(parts)
    if len(body) > cap:
        body = (body[:cap]
                + f"\n\n...[briefing capped at {cap} chars — use doc_read for the "
                  "full pages]")
    return body


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
        """Filesystem path of the target repo, or "" if the manifest omits it.

        Expanded through `expand_path`, so a committed manifest can stay portable
        (`${VAR}` / `~`) instead of hardcoding one machine's absolute layout."""
        return expand_path(self.manifest.get("repo", {}).get("path", ""))

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

    def briefing(self, knowledge_root: Path | None = None,
                 warnings: list[str] | None = None,
                 mode: str = "eco") -> str:
        """The repo's always-on prompt slice — the REPO-SPECIFIC part only. Reads
        this adapter's `knowledge.briefing_docs` (its `repos/<repo>/` hard-gate
        rules + navigation index) from the SHARED `knowledge_root` (the vendored
        community docs; `general/` knowledge is injected separately by the
        caller). Deeper guides/incidents are pulled on demand via the doc tools,
        not dumped here. Falls back to a legacy AI `profile.yaml` when one exists,
        else empty."""
        kn = self.manifest.get("knowledge") or {}
        docs = list(kn.get("briefing_docs") or [])
        # Extra briefing docs are TIER-INDEPENDENT (plan v2): the eco/performance
        # boundary is the model backend and nothing else, so any eco-vs-perf
        # difference is attributable to the model. `performance_briefing_docs`
        # is the deprecated tier-coupled name for the same list.
        extra_docs = list(kn.get("briefing_docs_extra") or [])
        legacy = list(kn.get("performance_briefing_docs") or [])
        if legacy:
            if warnings is not None:
                warnings.append(
                    "manifest key performance_briefing_docs is deprecated — "
                    "rename it to briefing_docs_extra (now injected for ALL "
                    "tiers; the tier boundary is model-only)")
            extra_docs = extra_docs or legacy
        repo_subdir = str(kn.get("repo_subdir") or "").rstrip("/")
        if repo_subdir:
            def scoped(items: list[str]) -> list[str]:
                out = []
                for rel in items:
                    rel_posix = Path(rel).as_posix()
                    if (rel_posix == repo_subdir
                            or rel_posix.startswith(repo_subdir + "/")):
                        out.append(rel)
                    elif warnings is not None:
                        warnings.append(
                            f"repo briefing path outside {repo_subdir}: {rel}")
                return out

            docs = scoped(docs)
            extra_docs = scoped(extra_docs)
        if knowledge_root is not None and (docs or extra_docs):
            parts = []
            if docs:
                parts.append(render_briefing_docs(
                    knowledge_root, docs,
                    header=(f"Repo-specific knowledge (source: {kn.get('source', '')}; "
                            "open the linked deeper docs with doc_read / doc_search):"),
                    warnings=warnings))
            if extra_docs:
                parts.append(render_briefing_docs(
                    knowledge_root, extra_docs,
                    header="Extended review knowledge router:",
                    warnings=warnings))
            body = "\n\n".join(part for part in parts if part)
            if body:
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
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
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
                         text=True, encoding="utf-8", errors="replace", timeout=30)
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
