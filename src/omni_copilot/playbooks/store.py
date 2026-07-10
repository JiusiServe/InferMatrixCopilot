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
    """One step in a playbook: a unique `id`, the registered `step` name to run,
    its `params`, and optional control — `foreach` (a state key holding a list
    to fan out over) and `when` (a TaskSpec condition gating execution)."""

    id: str
    step: str
    params: dict = field(default_factory=dict)
    foreach: str | None = None  # state key holding a list to fan out over
    when: str | None = None     # TaskSpec condition: "post" / "not report_only"


@dataclass
class Playbook:
    """A versioned, reusable orchestration plan: its `steps` plus the matching
    keys (`task_kinds`, `repos`), declared adaptation `params`, profile
    `requires`, `provenance`, and `success` criterion. `status` drives reuse
    (candidate/active/locked/retired)."""

    name: str
    version: int
    status: str
    task_kinds: list[str]
    repos: list[str]                 # explicit repos win; [] = repo-neutral
    steps: list[PlaybookStep]
    params: dict = field(default_factory=dict)  # declared adaptation surface
    requires: list[str] = field(default_factory=list)  # profile capabilities
    provenance: dict = field(default_factory=dict)
    success: str = ""

    @property
    def locked(self) -> bool:
        """True for locked playbooks — high-risk plans reused verbatim."""
        return self.status == "locked"


def playbook_to_doc(pb: Playbook) -> dict:
    """Serialize a Playbook back to its YAML-ready dict, the inverse of
    `_parse`. Empty optional fields are omitted so the round-trip stays clean."""
    return {
        "name": pb.name, "version": pb.version, "status": pb.status,
        "task_kinds": pb.task_kinds, "repos": pb.repos, "params": pb.params,
        **({"requires": pb.requires} if pb.requires else {}),
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
    """Parse and validate a playbook `doc` into a Playbook; `source` labels it in
    error messages. The public entry point over `_parse`."""
    return _parse(doc, source)


def _parse(doc: dict, source: str) -> Playbook:
    """Build a Playbook from a raw `doc`, validating required keys, the `status`
    enum, and step-id uniqueness; raises ValueError (naming `source`) on any
    violation. Returns the constructed Playbook."""
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
        requires=list(doc.get("requires", []) or []),
        provenance=doc.get("provenance", {}) or {}, success=doc.get("success", ""),
    )


class PlaybookStore:
    """In-memory registry of the playbooks under `directory`, validated against a
    `StepRegistry` so a plan can never name an unregistered step. Provides recall
    (`find`), lookup (`get`/`all`), and candidate persistence."""

    def __init__(self, directory: Path, registry: StepRegistry):
        """Bind the store to its `directory` and step `registry`, then load all
        playbooks eagerly."""
        self.directory = Path(directory)
        self.registry = registry
        self._playbooks: dict[str, Playbook] = {}
        self.load()

    def load(self) -> None:
        """(Re)load every `*.yaml` in the directory, parsing and validating each;
        replaces the in-memory set. A missing directory leaves it empty."""
        self._playbooks.clear()
        if not self.directory.exists():
            return
        for path in sorted(self.directory.glob("*.yaml")):
            doc = yaml.safe_load(path.read_text())
            pb = _parse(doc, str(path))
            self.validate(pb)
            self._playbooks[pb.name] = pb

    def validate(self, pb: Playbook) -> None:
        """Raise ValueError if any of `pb`'s steps names a step not in the
        registry — the guard that keeps plans executable."""
        for s in pb.steps:
            if s.step not in self.registry:
                raise ValueError(
                    f"playbook '{pb.name}' references unregistered step '{s.step}'"
                )

    def get(self, name: str) -> Playbook | None:
        """The playbook registered under `name`, or None."""
        return self._playbooks.get(name)

    def all(self) -> list[Playbook]:
        """All loaded playbooks."""
        return list(self._playbooks.values())

    def find(self, task_kind: str, repo: str | None = None,
             capabilities: set[str] | None = None) -> Playbook | None:
        """Recall: exact task-kind match, preferring repo match, locked > active.

        Repo-neutral playbooks (`repos: []`) additionally declare `requires:` —
        the profile capabilities they need (design §V2.2.3). With a known
        capability set they only match when satisfied; `capabilities=None`
        means "unknown" and skips the filter (v1-compatible)."""
        candidates = [
            p for p in self._playbooks.values()
            if task_kind in p.task_kinds and p.status in ("active", "locked")
        ]
        if repo:
            scoped = [p for p in candidates if repo in p.repos]
            if not scoped:
                scoped = [p for p in candidates if not p.repos]
                if capabilities is not None:
                    scoped = [p for p in scoped
                              if set(p.requires) <= capabilities]
            candidates = scoped
        candidates.sort(key=lambda p: (p.status != "locked", -p.version))
        return candidates[0] if candidates else None

    def missing_capabilities(self, task_kind: str,
                             capabilities: set[str]) -> dict[str, list[str]]:
        """Per repo-neutral playbook of this kind: the unmet requirements
        (escalation material for capability_gap reporting)."""
        return {
            p.name: sorted(set(p.requires) - capabilities)
            for p in self._playbooks.values()
            if task_kind in p.task_kinds and not p.repos
            and p.status in ("active", "locked")
            and not set(p.requires) <= capabilities
        }

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
