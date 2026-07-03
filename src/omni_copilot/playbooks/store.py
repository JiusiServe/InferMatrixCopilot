"""Playbook registry — orchestration-level reusable assets (design §3.2).

Versioned, with provenance and status (candidate/active/locked/retired).
High-risk (code-modifying / pushing) playbooks are locked: reuse verbatim,
never improvised. Status promotion is curator + human, mirroring skills.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..engine.registry import StepRegistry

STATUSES = ("candidate", "active", "locked", "retired")


@dataclass
class PlaybookStep:
    id: str
    step: str
    params: dict = field(default_factory=dict)
    foreach: str | None = None  # state key holding a list to fan out over
    when: str | None = None     # TaskSpec condition: "post" / "not report_only"


@dataclass
class Playbook:
    name: str
    version: int
    status: str
    task_kinds: list[str]
    repos: list[str]
    steps: list[PlaybookStep]
    params: dict = field(default_factory=dict)  # declared adaptation surface
    provenance: dict = field(default_factory=dict)
    success: str = ""

    @property
    def locked(self) -> bool:
        return self.status == "locked"


def playbook_to_doc(pb: Playbook) -> dict:
    return {
        "name": pb.name, "version": pb.version, "status": pb.status,
        "task_kinds": pb.task_kinds, "repos": pb.repos, "params": pb.params,
        "provenance": pb.provenance, "success": pb.success,
        "steps": [
            {"id": s.id, "step": s.step,
             **({"params": s.params} if s.params else {}),
             **({"foreach": s.foreach} if s.foreach else {}),
             **({"when": s.when} if s.when else {})}
            for s in pb.steps
        ],
    }


def parse_playbook(doc: dict, source: str = "<inline>") -> Playbook:
    return _parse(doc, source)


def _parse(doc: dict, source: str) -> Playbook:
    for key in ("name", "status", "task_kinds", "steps"):
        if key not in doc:
            raise ValueError(f"playbook {source}: missing '{key}'")
    if doc["status"] not in STATUSES:
        raise ValueError(f"playbook {source}: bad status {doc['status']!r}")
    steps = [
        PlaybookStep(
            id=s["id"], step=s["step"], params=s.get("params", {}) or {},
            foreach=s.get("foreach"), when=s.get("when"),
        )
        for s in doc["steps"]
    ]
    ids = [s.id for s in steps]
    if len(ids) != len(set(ids)):
        raise ValueError(f"playbook {source}: duplicate step ids")
    return Playbook(
        name=doc["name"], version=int(doc.get("version", 1)), status=doc["status"],
        task_kinds=list(doc["task_kinds"]), repos=list(doc.get("repos", [])),
        steps=steps, params=doc.get("params", {}) or {},
        provenance=doc.get("provenance", {}) or {}, success=doc.get("success", ""),
    )


class PlaybookStore:
    def __init__(self, directory: Path, registry: StepRegistry):
        self.directory = Path(directory)
        self.registry = registry
        self._playbooks: dict[str, Playbook] = {}
        self.load()

    def load(self) -> None:
        self._playbooks.clear()
        if not self.directory.exists():
            return
        for path in sorted(self.directory.glob("*.yaml")):
            doc = yaml.safe_load(path.read_text())
            pb = _parse(doc, str(path))
            self.validate(pb)
            self._playbooks[pb.name] = pb

    def validate(self, pb: Playbook) -> None:
        for s in pb.steps:
            if s.step not in self.registry:
                raise ValueError(
                    f"playbook '{pb.name}' references unregistered step '{s.step}'"
                )

    def get(self, name: str) -> Playbook | None:
        return self._playbooks.get(name)

    def all(self) -> list[Playbook]:
        return list(self._playbooks.values())

    def find(self, task_kind: str, repo: str | None = None) -> Playbook | None:
        """Recall: exact task-kind match, preferring repo match, locked > active."""
        candidates = [
            p for p in self._playbooks.values()
            if task_kind in p.task_kinds and p.status in ("active", "locked")
        ]
        if repo:
            scoped = [p for p in candidates if repo in p.repos]
            candidates = scoped or [p for p in candidates if not p.repos]
        candidates.sort(key=lambda p: (p.status != "locked", -p.version))
        return candidates[0] if candidates else None

    def save_candidate(self, pb: Playbook) -> Path:
        """Successful generated/adapted plans enter the registry as candidates
        only — promotion to active/locked is curator + human."""
        pb.status = "candidate"
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / f"{pb.name}.yaml"
        path.write_text(yaml.safe_dump(playbook_to_doc(pb), sort_keys=False,
                                       allow_unicode=True))
        self._playbooks[pb.name] = pb
        return path
