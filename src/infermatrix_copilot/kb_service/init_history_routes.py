"""Model-name routing for PR learning, alongside component path ownership."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

import yaml

from ..direct_routing import _route_text, _signal_matches


def model_matches(text: str, name: str) -> bool:
    intent, signal = _route_text(text), _route_text(name)
    compact = re.sub(r"[^a-z0-9]", "", signal)
    return _signal_matches(intent, signal) or bool(
        len(compact) >= 8 and compact in re.sub(r"[^a-z0-9]", "", intent))


def model_pages(head: dict[str, str], routes: str | None, repo_dir: str) -> list[dict]:
    data = yaml.safe_load(routes or "") or {}
    if not isinstance(data, dict):
        raise ValueError("model routes must be a mapping")
    spec = data.get("models")
    if spec is None:
        return []
    if not isinstance(spec, dict) or not all(isinstance(spec.get(k), str) and spec[k] for k in ("dir", "page")):
        raise ValueError("model routes need dir and page")
    root, page = spec["dir"].rstrip("/"), spec["page"]
    for path in (root, page):
        if path.startswith("/") or "\\" in path or any(p in ("", ".", "..") for p in path.split("/")):
            raise ValueError("model routes must use safe relative paths")
    if not root.startswith(repo_dir + "/") or not page.endswith(".md"):
        raise ValueError("model rule pages must belong to this repository")
    out = []
    for path in sorted(head):
        if not path.startswith(root + "/"):
            continue
        relative = path[len(root) + 1:]
        name, _, rest = relative.partition("/")
        if rest == page:
            out.append({"owner": f"model:{name}", "model_name": name, "path": path})
    return sorted(out, key=lambda m: (-len(m["model_name"]), m["model_name"]))


def offered_models(head: dict[str, str], routes: str | None, repo_dir: str,
                   paths: list[str], description: str) -> list[dict]:
    out = []
    for model in model_pages(head, routes, repo_dir):
        specific = [p for p in paths if model_matches(p, model["model_name"])]
        if specific or model_matches(description, model["model_name"]):
            out.append({**model, "prefixes": paths, "specific_paths": specific})
    return out


def _text_models(text: str, models: list[dict]) -> set[str]:
    def compact(name):
        return re.sub(r"[^a-z0-9]", "", name.lower())

    remaining, found = _route_text(text), set()
    # Consume concrete variants before shorter family names, while preserving
    # a separate explicit mention of the family in a shared contract. Equal
    # compact aliases remain ambiguous instead of choosing one arbitrarily.
    for length in sorted({len(compact(m["model_name"])) for m in models}, reverse=True):
        matched = [m for m in models if len(compact(m["model_name"])) == length
                   and model_matches(remaining, m["model_name"])]
        found.update(m["owner"] for m in matched)
        for m in matched:
            pattern = r"[^a-z0-9]*".join(compact(m["model_name"]))
            if pattern:
                remaining = re.sub(pattern, " ", remaining)
    return found


def model_scope_valid(owner: str, text: str, paths: list[str], models: list[dict]) -> bool:
    named = _text_models(text, models)
    specific = _text_models("\n".join(paths), models)
    if owner.startswith("model:"):
        if owner not in {m["owner"] for m in models} or specific and owner not in specific:
            return False
        return specific == {owner} or named == {owner}
    # A single-model implementation/contract belongs to that model. Shared
    # contracts covering several models may stay with the component owner.
    return len(specific) != 1 and len(named) != 1


def owner_rule_pages(head: dict[str, str], page: str) -> list[str]:
    """One owner's canonical page and split topics, never another owner."""
    target = PurePosixPath(page)
    return [p for p in head if PurePosixPath(p).parent == target.parent and
            (p == page or PurePosixPath(p).stem.startswith(target.stem + "-")) and p.endswith(".md")]
