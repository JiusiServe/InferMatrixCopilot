"""Module path-map sync — the deterministic core of `35_sync_module_paths.sh`.

After the merge, module file/test path lists drift (files move or vanish).
The sync pass drops entries that no longer exist, applies adapter-curated
candidate overlays, and retargets the ADAPTER MANIFEST's module map (the
single source of truth here — the parent rewrote config.sh assoc arrays).
The L2 final-decision *application* (validated, deterministic) also lives
here; producing the decision is an agent step wired in the assembly PR.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

import yaml

PathMap = dict[str, list[str]]


class PathSyncError(RuntimeError):
    """The mapping/decision cannot be applied safely."""


def keep_existing(root: Path, candidates: Sequence[str]) -> list[str]:
    root = Path(root)
    return [p for p in candidates if (root / p.rstrip("/")).exists()]


def ensure_non_empty(paths: list[str], fallback: str) -> list[str]:
    """A module's path list must never go empty — an empty list silently
    matches nothing downstream (no commits assigned, no tests selected)."""
    return paths if paths else [fallback]


@dataclass(frozen=True)
class CuratedEntry:
    """Adapter-curated candidate list for one module key: the candidates are
    filtered against the tree; `fallback` is the entry to keep when none
    survive (chosen by the adapter author, not necessarily the first)."""

    candidates: tuple[str, ...]
    fallback: str

    @classmethod
    def from_data(cls, data: Mapping) -> "CuratedEntry":
        candidates = tuple(data["candidates"])
        return cls(candidates=candidates,
                   fallback=data.get("fallback", candidates[0]))


def sync_path_map(root: Path, current: Mapping[str, Sequence[str]],
                  curated: Mapping[str, CuratedEntry] | None = None) -> PathMap:
    """Filter every module's list to paths that still exist (first current
    entry as fallback), then MERGE the curated candidate lists in (their own
    fallback when nothing at all survives). Curated entries add coverage —
    they never replace the surviving coarse prefixes, which review scoping
    and module rebases rely on (the parent replaced outright, but its config
    held only file lists; our manifest is a union by design). Key set is
    preserved exactly — curated keys unknown to `current` are rejected loudly
    rather than silently added."""
    curated = curated or {}
    unknown = sorted(set(curated) - set(current))
    if unknown:
        raise PathSyncError(f"curated overlay names unknown module(s): {unknown}")
    out: PathMap = {}
    surviving: dict[str, list[str]] = {}
    for key, value in current.items():
        candidates = list(value)
        fallback = candidates[0] if candidates else ""
        surviving[key] = keep_existing(root, candidates)
        out[key] = (ensure_non_empty(surviving[key], fallback)
                    if fallback else surviving[key])
    for key, entry in curated.items():
        kept = keep_existing(root, list(entry.candidates))
        # merge real survivors only — a fallback placeholder for a vanished
        # current path must not ride along once curated coverage exists
        merged = list(dict.fromkeys([*surviving[key], *kept]))
        out[key] = ensure_non_empty(merged, entry.fallback)
    return out


# -- L2 final decision (same JSON shape as the parent, lists or space-joined) --

def normalize_paths(value) -> list[str]:
    if isinstance(value, str):
        return value.split()
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value]
    raise PathSyncError(f"path list must be string or list, got {type(value).__name__}")


def apply_decision(root: Path, current: Mapping[str, Sequence[str]],
                   decision_block: Mapping) -> PathMap:
    """Validated application of an agent's final mapping for ONE block:
    - a key the agent omitted keeps its existing value (a newly-added module
      the prompt doesn't know about must not break the run);
    - a key the agent invented is an error (parent parity: a typo'd module
      name must not make the run "succeed" without the requested change);
    - an empty value is an error;
    - every path must exist under `root` (fail-closed: an agent typo must not
      silently unmap a module)."""
    unknown = sorted(set(decision_block) - set(current))
    if unknown:
        raise PathSyncError(f"unknown module key(s) in decision: {unknown}")
    out: PathMap = {}
    for key, existing in current.items():
        value = decision_block.get(key)
        if value is None:
            out[key] = list(existing)
            continue
        paths = normalize_paths(value)
        if not paths:
            raise PathSyncError(f"missing or empty value for {key}")
        for rel in paths:
            if not (Path(root) / rel.rstrip("/")).exists():
                raise PathSyncError(f"non-existent path in decision: {rel}")
        out[key] = paths
    return out


# -- manifest retarget ---------------------------------------------------------

_MODULE_LIST_FIELDS = ("local_paths", "upstream_paths", "test_paths")


def _emit_modules_block(modules: Mapping[str, Mapping]) -> str:
    """Deterministic re-emission of the manifest `modules:` section: key order
    preserved, path lists in flow style (the manifest's existing idiom),
    scalar fields verbatim."""
    lines = ["modules:"]
    for name, spec in modules.items():
        lines.append(f"  {name}:")
        for field, value in spec.items():
            if field in _MODULE_LIST_FIELDS:
                items = ", ".join(str(v) for v in value)
                lines.append(f"    {field}: [{items}]")
            else:
                # dump as a one-key mapping to get a clean scalar rendering
                # (a bare-scalar dump appends a `...` document-end marker)
                dumped = yaml.safe_dump({"k": value},
                                        default_flow_style=True).strip()
                lines.append(f"    {field}: {dumped[len('{k: '):-1]}")
        if not spec:
            lines[-1] += " {}"
    return "\n".join(lines) + "\n"


def _modules_section_span(text: str) -> tuple[int, int]:
    """(start, end) line indices of the top-level `modules:` section. The end
    excludes trailing blank/comment lines that belong to the NEXT section."""
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if re.match(r"^modules:\s*$", ln)),
                 -1)
    if start < 0:
        raise PathSyncError("manifest has no top-level `modules:` section")
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if re.match(r"^[A-Za-z_]", lines[i]):
            end = i
            break
    while end > start + 1 and (not lines[end - 1].strip()
                               or lines[end - 1].lstrip().startswith("#")):
        end -= 1
    return start, end


def rewrite_manifest_modules(manifest_path: Path,
                             updates: Mapping[str, Mapping[str, list[str]]]
                             ) -> bool:
    """Retarget path-list fields inside the manifest's `modules:` section,
    leaving every byte outside that section untouched. `updates` maps module →
    {field: paths}; unknown modules/fields are an error (an agent must not be
    able to invent manifest structure). Returns True when the file changed.

    Comments *inside* the modules section are not preserved — the section is
    re-emitted deterministically (pinned by test)."""
    manifest_path = Path(manifest_path)
    text = manifest_path.read_text(encoding="utf-8")
    data = yaml.safe_load(text) or {}
    modules = data.get("modules")
    if not isinstance(modules, dict) or not modules:
        raise PathSyncError("manifest has no parseable `modules:` mapping")

    for module, fields in updates.items():
        if module not in modules:
            raise PathSyncError(f"unknown module in updates: {module}")
        for field, paths in fields.items():
            if field not in _MODULE_LIST_FIELDS:
                raise PathSyncError(
                    f"refusing to rewrite non-path field: {module}.{field}")
            modules[module] = dict(modules[module] or {})
            modules[module][field] = list(paths)

    lines = text.splitlines()
    start, end = _modules_section_span(text)
    new_block = _emit_modules_block(modules).splitlines()
    new_lines = lines[:start] + new_block + lines[end:]
    new_text = "\n".join(new_lines) + ("\n" if text.endswith("\n") else "")
    if new_text == text:
        return False
    reparsed = yaml.safe_load(new_text)
    if not isinstance(reparsed, dict) or "modules" not in reparsed:
        raise PathSyncError("manifest rewrite produced unparseable YAML; aborted")
    manifest_path.write_text(new_text, encoding="utf-8")
    return True


def render_sync_report(root: Path, updated: Mapping[str, Mapping[str, list[str]]],
                       *, source: str = "") -> str:
    lines = ["# Module Path Sync Report", ""]
    if source:
        lines.append(f"- Source of truth: {source}")
    lines += [f"- Repo root: `{root}`", "", "## Updated Entries"]
    for block_name, entries in updated.items():
        lines += ["", f"### {block_name}"]
        for key in sorted(entries):
            joined = " ".join(entries[key])
            lines.append(f'- `["{key}"]="{joined}"`')
    return "\n".join(lines) + "\n"
