"""Complete, branch-scoped source preparation and bounded owner packets.

The collection cursor records discovery, not an extraction-ready excerpt.
Preparation refuses incomplete sources; every discussion item is assigned to
one packet and must receive a recorded conclusion or explicit drop.
"""
from __future__ import annotations

import hashlib
import json
import re

from ..knowledge_service.facts import FactsError
from .init_coverage import load_owners, most_specific
from .init_history_routes import offered_models
from .sources import SourceError
from .upstream_facts import MirrorObserver

MAX_SOURCE_BYTES = 5_000_000
MAX_PACKET_BYTES = 300_000


def digest(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def prepare_event(rt, lifecycle, event: dict, base: dict) -> dict:
    payload = dict(event["payload"])
    if event["source"] != "merged_pr":
        return payload
    if not lifecycle.full_name:
        raise SourceError("merged PR preparation requires an upstream repository")
    source = rt.github.history_evidence(lifecycle.full_name, int(event["external_id"]),
                                        max_bytes=MAX_SOURCE_BYTES)
    if source.get("number") != int(event["external_id"]) or source.get("repository") != lifecycle.full_name:
        raise SourceError("prepared PR identity differs from the discovered event")
    branch = (source.get("base") or {}).get("ref")
    sha = source.get("merge_commit_sha")
    if not source.get("merged_at") or not branch or not re.fullmatch(r"[0-9a-fA-F]{40}", sha or ""):
        raise SourceError("merged PR evidence lacks a merged commit or base branch")
    if payload.get("merge_commit_sha") and payload["merge_commit_sha"] != sha:
        raise SourceError("merged PR commit changed since discovery")
    source["changed_files"] = [item["filename"] for item in source["files"]]
    source["source_scope"] = {"repository": lifecycle.full_name, "base_branch": branch}
    source["source_sha256"] = digest(source)
    return source


def observer_for(rt, lifecycle, evidence):
    items = evidence if isinstance(evidence, list) else [evidence]
    scopes = {(s["repository"], s["base_branch"]) for item in items
              if (s := item.get("source_scope"))}
    if len(scopes) > 1 or any(repo != lifecycle.full_name for repo, _branch in scopes):
        raise SourceError("an intake batch must have one upstream repository and base branch")
    observer = rt.upstream_facts(lifecycle)
    if not scopes or observer is None:
        return observer
    _repo, branch = next(iter(scopes))
    if isinstance(observer, MirrorObserver):
        try:
            return MirrorObserver(observer.git_dir, observer.repository, observer._pull,
                                  url=observer._url, branch=branch)
        except FactsError as exc:
            raise SourceError(str(exc)) from exc
    # Injected observers implement their own immutable scope; never replace
    # one with a network-backed default during tests or offline evaluation.
    return observer


def owner_packets(evidence: dict, base: dict, repo_dir: str, observer) -> list[dict]:
    if "files" not in evidence:
        return [evidence]
    routes = base.get(f"{repo_dir}/_routes.yaml", "")
    owners = load_owners(routes)
    paths = evidence["changed_files"]
    models = offered_models(base, routes, repo_dir, paths,
                            evidence.get("title", "") + "\n" + evidence.get("body", ""))
    groups: dict[str, list[str]] = {}
    path_owner = {}
    supporting = []
    for path in paths:
        matches = [m["path"] for m in models if path in m["specific_paths"]]
        if not matches:
            matches = [o.path for o in most_specific(path, owners)]
        if len(set(matches)) > 1:
            raise SourceError(f"ambiguous knowledge owner for {path}")
        if not matches:
            supporting.append(path)
            continue
        owner = matches[0]
        groups.setdefault(owner, []).append(path)
        path_owner[path] = owner
    if not groups:
        raise SourceError("changed files have no knowledge owner; routing must be resolved before extraction")
    # Preserve raw diff blocks if no mirror is injected. Quoted filenames
    # are left intact in the fallback full diff rather than guessed.
    blocks = re.split(r"(?=^diff --git )", evidence.get("diff", ""), flags=re.M)
    by_path = {}
    for block in blocks:
        header = re.match(r"diff --git a/(.+) b/(.+)\n", block)
        if header:
            by_path[header[2]] = block
    packets = []
    common = {k: v for k, v in evidence.items()
              if k not in ("files", "changed_files", "diff", "threads", "reviews", "replies")}
    # Shared conversation remains available to every affected owner. Its
    # accounting unit is assigned once below; visibility is not ownership.
    common["shared_discussion"] = {kind: evidence.get(kind, []) for kind in ("reviews", "replies")}
    common["shared_discussion"]["unmapped_threads"] = [
        item for item in evidence.get("threads", []) if item.get("path") not in path_owner]
    common["supporting_files"] = supporting
    for owner, assigned in groups.items():
        packet = {**common, "owner_page": owner, "changed_files": [], "diffs": {},
                  "threads": [], "reviews": [], "replies": [], "extraction_units": []}
        packet["owned_files"] = assigned
        for path in [*assigned, *supporting]:
            try:
                patch = (observer.pr_diff(evidence["number"], evidence["merge_commit_sha"], path)
                         if observer is not None and hasattr(observer, "pr_diff")
                         else by_path.get(path, evidence.get("diff", "")))
            except FactsError as exc:
                raise SourceError(f"cannot prepare {path}: {exc}") from exc
            trial = {**packet, "changed_files": [*packet["changed_files"], path],
                     "diffs": {**packet["diffs"], path: patch}}
            if len(json.dumps(trial, ensure_ascii=False).encode()) > MAX_PACKET_BYTES:
                if not packet["changed_files"]:
                    raise SourceError(f"source file {path} exceeds the owner packet budget")
                packets.append(packet)
                packet = {**packet, "changed_files": [], "diffs": {}, "threads": [],
                          "reviews": [], "replies": [], "extraction_units": []}
                trial = {**packet, "changed_files": [path], "diffs": {path: patch}}
                if len(json.dumps(trial, ensure_ascii=False).encode()) > MAX_PACKET_BYTES:
                    raise SourceError(f"source file {path} exceeds the owner packet budget")
            packet = trial
        packets.append(packet)
    for kind in ("threads", "reviews", "replies"):
        for item in evidence.get(kind, []):
            owner = path_owner.get(item.get("path"))
            target = next((p for p in packets if p["owner_page"] == owner
                           and item.get("path") in p["changed_files"]), packets[0])
            unit = f"{kind}:{item['id']}"
            if kind == "threads" and item.get("path") in path_owner:
                target[kind].append(item)
            target["extraction_units"].append({"id": unit, "kind": kind})
    for packet in packets:
        packet["packet_sha256"] = digest(packet)
        if len(json.dumps(packet, ensure_ascii=False).encode()) > MAX_PACKET_BYTES:
            raise SourceError("PR discussion exceeds the owner packet budget; no partial extraction")
    return packets
