"""Workflow declarations: how a playbook step or agent loop enrolls.

A declaration (``improve/workflows/<name>.yaml``, plus any directory named in
``IMPROVE_WORKFLOWS_DIRS``) says what a unit of work is, how its item is
keyed for pairing, what the configuration fingerprint covers, what the
capture level is, and (Tier 2 only) which outcome adapter scores it. A
workflow that writes traces but has no declaration is Tier 1 only: the
executor still records its units, with no fingerprint and no item key.

Declarations are repo-neutral by construction: they may name only the
copilot's own playbooks, steps, roles, settings keys and package files.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import yaml

KINDS = ("static", "dynamic")
UNITS = ("step_call", "agent_loop")
CAPTURE = ("full", "decisions_only")
BUILTIN_DIR = Path(__file__).resolve().parent / "workflows"


class DeclarationError(ValueError):
    """A declaration file is malformed; the engine refuses it loudly."""


@dataclass(frozen=True)
class WorkflowDeclaration:
    workflow: str                       # "<playbook>.<step or role>"
    kind: str                           # static | dynamic
    unit: str                           # step_call | agent_loop
    item_key: str                       # e.g. "{repo}#{pr}@{head_sha}"
    fingerprint_covers: tuple[Any, ...] # entries of fingerprint.covers, in order
    capture: str = "full"               # full | decisions_only
    outcome_adapter: str = ""           # "module:Class" or "" (Tier 1 only)
    tier2_min_items: int = 8
    shadow_tools: tuple[str, ...] = ()
    shadow_executables: tuple[str, ...] = ("python3", "git", "grep")
    source: str = ""
    raw: dict = field(default_factory=dict, compare=False, hash=False)
    evolution: dict = field(default_factory=dict, compare=False, hash=False)
    experiment_driver: str = ""

    @property
    def playbook(self) -> str:
        return self.workflow.split(".", 1)[0]

    @property
    def target(self) -> str:
        """The step name or agent role after the playbook prefix."""
        return self.workflow.split(".", 1)[1] if "." in self.workflow else ""

    @property
    def tier2(self) -> bool:
        return bool(self.outcome_adapter)


def _require(doc: dict, key: str, source: str) -> Any:
    if key not in doc:
        raise DeclarationError(f"{source}: missing required key {key!r}")
    return doc[key]


def parse_declaration(doc: dict, source: str = "<memory>") -> WorkflowDeclaration:
    if not isinstance(doc, dict):
        raise DeclarationError(f"{source}: a declaration is a mapping")
    workflow = str(_require(doc, "workflow", source)).strip()
    if "." not in workflow:
        raise DeclarationError(f"{source}: workflow must be '<playbook>.<step or role>', got {workflow!r}")
    kind = str(_require(doc, "kind", source))
    if kind not in KINDS:
        raise DeclarationError(f"{source}: kind must be one of {KINDS}, got {kind!r}")
    unit = str(_require(doc, "unit", source))
    if unit not in UNITS:
        raise DeclarationError(f"{source}: unit must be one of {UNITS}, got {unit!r}")
    capture = str(doc.get("capture", "full"))
    if capture not in CAPTURE:
        raise DeclarationError(f"{source}: capture must be one of {CAPTURE}, got {capture!r}")
    fp = _require(doc, "fingerprint", source)
    covers = fp.get("covers") if isinstance(fp, dict) else None
    if not isinstance(covers, list) or not covers:
        raise DeclarationError(f"{source}: fingerprint.covers must be a non-empty list")
    for entry in covers:
        if isinstance(entry, str):
            continue
        if isinstance(entry, dict) and len(entry) == 1 and all(
                isinstance(v, list) for v in entry.values()):
            continue
        raise DeclarationError(f"{source}: bad fingerprint.covers entry {entry!r}")
    min_items = int(doc.get("tier2_min_items", 8))
    if min_items < 1:
        raise DeclarationError(f"{source}: tier2_min_items must be >= 1")
    evolution = doc.get("evolution") or {}
    if not isinstance(evolution, dict):
        raise DeclarationError(f"{source}: evolution must be a mapping")
    if evolution:
        for key in ("paths", "settings", "tests"):
            if not isinstance(evolution.get(key, []), list) or not all(isinstance(v, str) for v in evolution.get(key, [])):
                raise DeclarationError(f"{source}: evolution.{key} must be a string list")
        from .artifacts import validate_policy
        validate_policy(evolution)
    return WorkflowDeclaration(
        workflow=workflow, kind=kind, unit=unit, item_key=str(_require(doc, "item_key", source)),
        fingerprint_covers=tuple(covers), capture=capture,
        outcome_adapter=str(doc.get("outcome_adapter") or ""), tier2_min_items=min_items,
        shadow_tools=tuple(str(t) for t in doc.get("shadow_tools") or ()),
        shadow_executables=tuple(str(t) for t in doc.get("shadow_executables") or ("python3", "git", "grep")),
        source=source, raw=dict(doc), evolution=evolution,
        experiment_driver=str(doc.get("experiment_driver") or ""))


def declaration_dirs(extra: Iterable[str | Path] | None = None, environ: dict | None = None) -> list[Path]:
    """The builtin directory first, then ``IMPROVE_WORKFLOWS_DIRS`` (os.pathsep
    separated) and any ``extra`` directories."""
    env = os.environ if environ is None else environ
    dirs = [BUILTIN_DIR]
    for raw in (env.get("IMPROVE_WORKFLOWS_DIRS") or "").split(os.pathsep):
        if raw.strip():
            dirs.append(Path(raw).expanduser())
    for d in extra or ():
        dirs.append(Path(d))
    return dirs


def load_declarations(extra: Iterable[str | Path] | None = None,
                      environ: dict | None = None) -> dict[str, WorkflowDeclaration]:
    """Every declaration keyed by workflow name; a later directory overrides an
    earlier one for the same workflow, and a malformed file raises."""
    found: dict[str, WorkflowDeclaration] = {}
    for directory in declaration_dirs(extra, environ):
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.yaml")):
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
            decl = parse_declaration(doc, str(path))
            found[decl.workflow] = decl
    return found


def lookup(declarations: dict[str, WorkflowDeclaration], playbook: str, target: str) -> WorkflowDeclaration | None:
    """The declaration for ``<playbook>.<target>`` or None (undeclared = Tier 1)."""
    return declarations.get(f"{playbook}.{target}")


class _Blank(dict):
    def __missing__(self, key: str) -> str:
        return ""


def item_for(decl: WorkflowDeclaration, state: dict) -> str:
    """Format the declaration's ``item_key`` from run state (TaskSpec fields and
    published state keys); a missing field renders blank rather than raising."""
    spec = state.get("task_spec") or {}
    values = _Blank({**{k: v for k, v in state.items() if isinstance(v, (str, int))},
                     **{k: v for k, v in spec.items() if isinstance(v, (str, int))}})
    values.setdefault("head_sha", state.get("pr_head_sha") or "")
    try:
        return decl.item_key.format_map(values)
    except (KeyError, IndexError, ValueError):
        return ""


def declarations_for(settings: Any, environ: dict | None = None) -> dict[str, WorkflowDeclaration]:
    """The declarations every part of the engine must agree on: the builtin
    directory, ``IMPROVE_WORKFLOWS_DIRS`` and ``settings.improve_workflows_dirs``
    (os.pathsep separated). The executor, the shadow hardening, the cycle and
    the forensics step all go through here."""
    extra = [d for d in str(getattr(settings, "improve_workflows_dirs", "") or "").split(os.pathsep) if d.strip()]
    return load_declarations(extra, environ=environ)
