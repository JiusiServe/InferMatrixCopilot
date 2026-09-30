"""Coverage metrics for ``kb init`` (design: kb-init v3 §7).

Pure and deterministic. Two measures of how much of a repository its
knowledge routes reach:

* **module coverage** — the share of modules (``profiles.establish.
  scan_modules_at_depth``) whose every source file matches some owner's
  ``scope_prefixes`` in ``_routes.yaml``;
* **PR-weighted coverage** — over a window of merged PRs, the share of changed
  source files (counted once per PR that changed them) that route to an owner
  (*routed*), and to an owner whose page carries rules (*rule-bearing*).

An empty population counts as fully covered (ratio 1.0): there is nothing a
route could miss.
"""

from __future__ import annotations

import fnmatch
from collections import Counter
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Callable, Mapping, Sequence

import yaml

# equals profiles.establish.ROOT_MODULE (kb_service stays free of profile
# imports; a test pins the two together)
ROOT_MODULE = "./"


@dataclass(frozen=True)
class Owner:
    owner: str
    path: str
    prefixes: tuple[str, ...]


@dataclass(frozen=True)
class Coverage:
    covered: list[str]
    uncovered: list[str]
    ratio: float


@dataclass(frozen=True)
class PrCoverage:
    total: int
    routed: int
    rule_bearing: int
    routed_ratio: float
    rule_bearing_ratio: float
    uncovered_hot: list[tuple[str, int]]


def load_owners(routes_yaml_text: str) -> list[Owner]:
    """The ``owners`` of a ``_routes.yaml`` (schema_version 1); ``models`` are
    name-matched, not path-matched, and play no part in coverage."""
    data = yaml.safe_load(routes_yaml_text) or {}
    if not isinstance(data, dict):
        raise ValueError("_routes.yaml must be a mapping")
    if data.get("schema_version", 1) != 1:
        raise ValueError(f"unsupported _routes.yaml schema_version {data.get('schema_version')!r}")
    owners = data.get("owners") or []
    if not isinstance(owners, list):
        raise ValueError("_routes.yaml owners must be a list")
    out = []
    for item in owners:
        if not isinstance(item, dict) or not item.get("owner") or not item.get("path"):
            raise ValueError(f"malformed _routes.yaml owner: {item!r}")
        prefixes = item.get("scope_prefixes") or []
        if not isinstance(prefixes, list) or any(not isinstance(p, str) or not p for p in prefixes):
            raise ValueError(f"{item['owner']}: scope_prefixes must be a list of non-empty strings")
        out.append(Owner(str(item["owner"]), str(item["path"]), tuple(prefixes)))
    return out


def routes_file(path: str, owners: Sequence[Owner]) -> list[Owner]:
    """Every owner whose scope prefixes reach ``path``, in routing order."""
    return [o for o in owners if any(path.startswith(p) for p in o.prefixes)]


def module_coverage(modules: Mapping[str, Mapping], owners: Sequence[Owner]) -> Coverage:
    covered, uncovered = [], []
    for key in sorted(modules):
        files = modules[key].get("files") or []
        (covered if all(routes_file(f, owners) for f in files) else uncovered).append(key)
    total = len(covered) + len(uncovered)
    return Coverage(covered, uncovered, len(covered) / total if total else 1.0)


def _normalize(path: str) -> str:
    """Repo-relative POSIX form without leading ``./`` or slashes; the repository
    root is ``""`` (same rule as ``profiles.establish.normalize_root``)."""
    text = PurePosixPath(path.strip().strip("/") or ".").as_posix()
    return "" if text == "." else text


def make_include(source_roots: Sequence[str], exclude: Sequence[str],
                 suffixes: Sequence[str] = ()) -> Callable[[str], bool]:
    """A filter for changed paths: under a source root (any path when none are
    given), with a source suffix (any when none are given), matching no
    ``exclude`` fnmatch glob. Tests, docs and generated files are the caller's
    ``exclude`` globs; nothing repository-specific is built in."""
    normalized = {_normalize(r) for r in source_roots}
    # the repository root (".", "./", "") admits every path
    roots = () if "" in normalized else tuple(sorted(r + "/" for r in normalized))
    sfx = tuple(suffixes)

    def include(path: str) -> bool:
        path = _normalize(path)
        if roots and not path.startswith(roots):
            return False
        if sfx and not path.endswith(sfx):
            return False
        return not any(fnmatch.fnmatch(path, glob) for glob in exclude)

    return include


def pr_weighted_coverage(prs: Sequence[Sequence[str]], owners: Sequence[Owner], *,
                         include: Callable[[str], bool],
                         rule_pages: set[str] | None = None) -> PrCoverage:
    """Each file a PR changes counts once for that PR. ``rule_pages`` are the
    knowledge paths (as ``_routes.yaml`` names them) holding at least one
    active rule; without them nothing is rule-bearing."""
    pages = rule_pages or set()
    total = routed = rule_bearing = 0
    missed: Counter[str] = Counter()
    for files in prs:
        for path in sorted({_normalize(f) for f in files}):
            if not include(path):
                continue
            total += 1
            hits = routes_file(path, owners)
            if hits:
                routed += 1
                if any(o.path in pages for o in hits):
                    rule_bearing += 1
            else:
                missed[path] += 1
    hot = sorted(missed.items(), key=lambda item: (-item[1], item[0]))
    return PrCoverage(total, routed, rule_bearing,
                      routed / total if total else 1.0,
                      rule_bearing / total if total else 1.0, hot)


def module_of(path: str, modules: Mapping[str, Mapping]) -> str | None:
    """The module owning ``path``: the longest module key that prefixes it (a
    file in a folded directory belongs to the ancestor it folded into)."""
    best = None
    for key in modules:
        prefix = "" if key == ROOT_MODULE else key
        if path.startswith(prefix) and (best is None or len(prefix) > len(best[1])):
            best = (key, prefix)
    return best[0] if best else None


def churn_by_module(prs: Sequence[Sequence[str]], modules: Mapping[str, Mapping]) -> list[tuple[str, int]]:
    """File changes per module over the PR window, highest first (ties by
    module path). Paths no module owns are not counted."""
    counts: Counter[str] = Counter()
    for files in prs:
        for path in sorted({_normalize(f) for f in files}):
            key = module_of(path, modules)
            if key is not None:
                counts[key] += 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))
