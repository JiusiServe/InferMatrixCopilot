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
    name: str
    description: str = ""
    trigger: str = ""
    modules: list[str] = field(default_factory=list)
    status: str = "active"
    run_count: int = 0
    body: str = ""


def _parse_skill(path: Path) -> Skill | None:
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
    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self.candidates_file = self.directory / "_candidates.json"

    def load_all(self) -> list[Skill]:
        skills = []
        if self.directory.exists():
            for p in sorted(self.directory.glob("*/SKILL.md")):
                s = _parse_skill(p)
                if s and s.status == "active":
                    skills.append(s)
        return skills

    def find(self, query: str = "", module: str = "", k: int = 3) -> list[Skill]:
        def score(s: Skill) -> tuple:
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
        candidates = self._load_candidates()
        candidates[name] = {
            "name": name, "description": description, "body": body,
            "modules": modules or [], "proposed_at": time.time(),
        }
        self.directory.mkdir(parents=True, exist_ok=True)
        self.candidates_file.write_text(json.dumps(candidates, indent=2, ensure_ascii=False))

    def promote(self, name: str) -> Path:
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

    def candidates(self) -> dict:
        return self._load_candidates()

    def _load_candidates(self) -> dict:
        if self.candidates_file.exists():
            return json.loads(self.candidates_file.read_text())
        return {}

    def render_for_prompt(self, skills: list[Skill]) -> str:
        if not skills:
            return ""
        parts = ["## Relevant skills (distilled past lessons)"]
        for s in skills:
            parts.append(f"### {s.name}\n{s.description}\n{s.body[:1_500]}")
        return "\n\n".join(parts)
