"""Check that an adapter manifest edit changes only named lifecycle keys.

``kb init`` touches one file outside ``knowledge/``: the adapter manifest, and
only to switch the repository's knowledge service on (``enabled`` + ``mode``)
or to name its calibration set. The knowledge L1 never sees that file (its
whitelist is ``knowledge/``), so this check validates it on its own: both
documents are parsed, the allowed key paths are removed from both, and what is
left must be equal. Formatting and comments are free to stay as they are; the
comparison is on parsed values.

The caller additionally runs ``config.parse_lifecycle`` on the head adapter
(it needs an adapter object, not text) so the new values are also valid.
"""

from __future__ import annotations

from typing import Any, Iterable

import yaml

LIFECYCLE = "knowledge_lifecycle"
FLIP_KEYS: frozenset[tuple[str, ...]] = frozenset({(LIFECYCLE, "enabled"), (LIFECYCLE, "mode")})
CALIBRATION_KEYS: frozenset[tuple[str, ...]] = frozenset({(LIFECYCLE, "calibration_set")})


def _load(text: str, which: str) -> tuple[Any, list[str]]:
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return None, [f"{which} manifest is not valid YAML: {exc}"]
    if not isinstance(data, dict):
        return None, [f"{which} manifest is not a mapping"]
    return data, []


def _copy(value: Any, active: frozenset[int] = frozenset()) -> Any:
    """A tree copy with YAML aliases UNshared: ``deepcopy`` keeps ``*alias``
    nodes shared, so removing an allowed key through one path would also hide
    a change made through another. A recursive alias is refused."""
    if isinstance(value, (dict, list)):
        if id(value) in active:
            raise ValueError("manifest contains a recursive alias")
        active = active | {id(value)}
        if isinstance(value, dict):
            return {key: _copy(item, active) for key, item in value.items()}
        return [_copy(item, active) for item in value]
    return value


def _without(data: dict, paths: Iterable[tuple[str, ...]]) -> dict:
    out = _copy(data)
    for path in paths:
        node: Any = out
        for key in path[:-1]:
            node = node.get(key) if isinstance(node, dict) else None
            if node is None:
                break
        if isinstance(node, dict):
            node.pop(path[-1], None)
    return out


def _typed(mapping: dict) -> dict[tuple[str, Any], Any]:
    # 1, 1.0 and True are equal (and collide) as Python dict keys; YAML keeps them apart
    return {(type(key).__name__, key): value for key, value in mapping.items()}


def _diff_keys(base: Any, head: Any, prefix: str = "") -> list[str]:
    """Paths where ``base`` and ``head`` differ, type-sensitively: YAML ``1``,
    ``1.0`` and ``true`` are different values even though Python compares
    them equal (and ``parse_lifecycle`` would stringify them differently)."""
    where = prefix or "<root>"
    if isinstance(base, dict) and isinstance(head, dict):
        typed_base, typed_head = _typed(base), _typed(head)
        out = []
        for key in sorted(set(typed_base) | set(typed_head), key=str):
            child = f"{prefix}.{key[1]}" if prefix else str(key[1])
            if key not in typed_base or key not in typed_head:
                out.append(child)
            else:
                out.extend(_diff_keys(typed_base[key], typed_head[key], child))
        return out
    if isinstance(base, list) and isinstance(head, list):
        if len(base) != len(head):
            return [where]
        out = []
        for index, (left, right) in enumerate(zip(base, head)):
            out.extend(_diff_keys(left, right, f"{where}[{index}]"))
        return out
    same = type(base) is type(head) and (base == head or (base != base and head != head))  # .nan
    return [] if same else [where]


def check_lifecycle_flip(base_yaml: str, head_yaml: str, *,
                         allowed: Iterable[tuple[str, ...]]) -> list[str]:
    """Problems when the manifest changed anything besides the ``allowed``
    key paths (empty list: the edit is confined to them)."""
    allowed = list(allowed)
    base, problems = _load(base_yaml, "base")
    head, more = _load(head_yaml, "head")
    problems += more
    if problems:
        return problems
    try:
        changed = _diff_keys(_without(base, allowed), _without(head, allowed))
    except ValueError as exc:
        return [str(exc)]
    return [f"manifest key {key} changed; only "
            f"{', '.join('.'.join(p) for p in sorted(allowed))} may change" for key in changed]


def check_flip_to_shadow(base_yaml: str, head_yaml: str) -> list[str]:
    """The init lifecycle flip: only ``enabled``/``mode`` change, and the head
    turns the service on in shadow mode."""
    problems = check_lifecycle_flip(base_yaml, head_yaml, allowed=FLIP_KEYS)
    if problems:
        return problems
    section = (yaml.safe_load(head_yaml) or {}).get(LIFECYCLE)
    if not isinstance(section, dict):
        return [f"head manifest has no {LIFECYCLE} mapping"]
    if section.get("enabled") is not True:
        problems.append(f"{LIFECYCLE}.enabled must be true")
    if section.get("mode", "shadow") != "shadow":  # parse_lifecycle's default
        problems.append(f"{LIFECYCLE}.mode must be shadow")
    return problems
