"""Skills — procedural knowledge, governed more strictly than debug memory.

Agents may only PROPOSE skills (candidates file); promotion to a real SKILL.md
is a curator/human action. Facts recorded freely, knowledge promoted via gates.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Skill:
    """One parsed SKILL.md: its frontmatter metadata (`name`, `description`,
    `trigger`, `modules`, `status`, `run_count`) plus the markdown `body`.
    `modules` is the join key for module-scoped retrieval; `run_count` is the
    usage prior that breaks ranking ties toward proven skills."""

    name: str
    description: str = ""
    trigger: str = ""
    modules: list[str] = field(default_factory=list)
    status: str = "active"
    run_count: int = 0
    body: str = ""


def _parse_skill(path: Path) -> Skill | None:
    """Parse a `SKILL.md` at `path` into a `Skill`, or None when the file lacks
    the leading `---` frontmatter fence or the YAML is malformed. Missing scalar
    fields fall back to defaults (name defaults to the containing dir name), so a
    partial-but-valid file still loads rather than being dropped."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    try:
        _, fm, body = text.split("---", 2)
        meta = yaml.safe_load(fm) or {}
    except (ValueError, yaml.YAMLError):
        return None
    return Skill(
        name=meta.get("name", path.parent.name),
        description=str(meta.get("description", "")),
        trigger=str(meta.get("trigger", "")),
        modules=list(meta.get("modules", []) or []),
        status=str(meta.get("status", "active")),
        run_count=int(meta.get("run_count", 0) or 0),
        body=body.strip(),
    )


class SkillStore:
    """Directory of promoted `<name>/SKILL.md` skills plus a `_candidates.json`
    holding agent-proposed but not-yet-promoted skills. Enforces the governance
    split: agents may only `propose`; `promote` (writing a real SKILL.md) is a
    curator/human action."""

    def __init__(self, directory: str | Path):
        """Bind to the skills `directory`; candidates live in `_candidates.json`
        under it. Neither path is required to exist yet."""
        self.directory = Path(directory)
        self.candidates_file = self.directory / "_candidates.json"

    def load_all(self) -> list[Skill]:
        """Parse and return every active promoted skill under the directory
        (sorted by path). Non-active or unparseable `SKILL.md` files are skipped;
        an absent directory yields an empty list."""
        skills = []
        if self.directory.exists():
            for p in sorted(self.directory.glob("*/SKILL.md")):
                s = _parse_skill(p)
                if s and s.status == "active":
                    skills.append(s)
        return skills

    def find(self, query: str = "", module: str = "", k: int = 3) -> list[Skill]:
        """Return up to `k` active skills ranked for the given `query`/`module`.
        Ranking key (descending): module match first, then count of query words
        found in description+trigger, then `run_count` as the usage tie-breaker.
        With a query or module supplied, zero-relevance skills are dropped; with
        neither, the top `k` by run_count are returned as a default surface."""

        def score(s: Skill) -> tuple:
            """Rank tuple for `s`: (module_hit, query-word overlap, run_count),
            compared lexicographically so a module match dominates text overlap."""
            module_hit = 1 if module and module in s.modules else 0
            text_hit = sum(
                1 for w in query.lower().split()
                if w in (s.description + " " + s.trigger).lower()
            )
            return (module_hit, text_hit, s.run_count)

        ranked = sorted(self.load_all(), key=score, reverse=True)
        return [s for s in ranked[:k] if score(s) != (0, 0, 0) or not (query or module)]

    # -- write gate: propose -> candidate; promote is curator/human ----------
    def propose(self, *, name: str, description: str, body: str,
                modules: list[str] | None = None) -> None:
        """Record a proposed skill (keyed by `name`) into `_candidates.json` with
        a `proposed_at` timestamp — the only write agents are permitted. Re-using
        a name overwrites its candidate. No SKILL.md is created until `promote`."""
        candidates = self._load_candidates()
        candidates[name] = {
            "name": name, "description": description, "body": body,
            "modules": modules or [], "proposed_at": time.time(),
        }
        self.directory.mkdir(parents=True, exist_ok=True)
        self.candidates_file.write_text(json.dumps(candidates, indent=2, ensure_ascii=False))

    def promote(self, name: str) -> Path:
        """Curator action: turn the candidate `name` into a real `<name>/SKILL.md`
        (frontmatter + body), remove it from the candidates file, and return the
        written path. Raises `KeyError` if no such candidate exists. The new skill
        starts `status: active`, `run_count: 0`, dated today."""
        candidates = self._load_candidates()
        if name not in candidates:
            raise KeyError(f"no skill candidate named {name!r}")
        c = candidates.pop(name)
        skill_dir = self.directory / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        path = skill_dir / "SKILL.md"
        fm = {
            "name": name, "description": c["description"], "trigger": "",
            "modules": c["modules"], "status": "active",
            "created_at": time.strftime("%Y-%m-%d"), "run_count": 0,
        }
        path.write_text(
            "---\n" + yaml.safe_dump(fm, sort_keys=False, allow_unicode=True)
            + "---\n\n" + c["body"] + "\n",
            encoding="utf-8",
        )
        self.candidates_file.write_text(json.dumps(candidates, indent=2, ensure_ascii=False))
        return path

    def touch(self, name: str) -> bool:
        """Record one use of the promoted skill `name`: bump `run_count` and
        stamp `last_used_at` in its frontmatter (the body is preserved
        byte-for-byte). Returns False when no such skill file exists or the
        frontmatter cannot be parsed — usage tracking never raises."""
        path = self.directory / name / "SKILL.md"
        try:
            text = path.read_text(encoding="utf-8")
            _, fm, body = text.split("---", 2)
            meta = yaml.safe_load(fm) or {}
            meta["run_count"] = int(meta.get("run_count", 0) or 0) + 1
            meta["last_used_at"] = time.strftime("%Y-%m-%d")
            path.write_text(
                "---\n" + yaml.safe_dump(meta, sort_keys=False,
                                          allow_unicode=True) + "---" + body,
                encoding="utf-8")
            return True
        except (OSError, ValueError, yaml.YAMLError):
            return False

    def candidates(self) -> dict:
        """The current proposed-but-unpromoted skills, keyed by name."""
        return self._load_candidates()

    def _load_candidates(self) -> dict:
        """Read and return the candidates map from `_candidates.json`, or an empty
        dict when the file does not exist yet."""
        if self.candidates_file.exists():
            return json.loads(self.candidates_file.read_text())
        return {}

    def render_for_prompt(self, skills: list[Skill]) -> str:
        """Format the given `skills` into a markdown block for prompt injection —
        a heading plus each skill's name, description, and body truncated to 1500
        chars (bounds prompt cost). Returns "" for an empty list so the caller can
        omit the section entirely."""
        if not skills:
            return ""
        parts = ["## Relevant skills (distilled past lessons)"]
        for s in skills:
            parts.append(f"### {s.name}\n{s.description}\n{s.body[:1_500]}")
        return "\n\n".join(parts)
