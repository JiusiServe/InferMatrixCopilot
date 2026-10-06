"""Replay portable publication receipts before activating a served snapshot."""
from __future__ import annotations

import hashlib
import json

from .knowledge_store import KnowledgeStore, KnowledgeStoreError
from .repo_spec import list_snapshot_repos, resolve_snapshot_repo


def check_publication(view, *, allow_partial=False):
    """Format verification and publication acceptance are separate checks.

    These hash-bound local receipts record prior source/native/retrieval gates;
    they are not newly generated model judgments or upstream test results.
    """
    tiers = {}
    for binding in list_snapshot_repos(view):
        if not binding.source_pin:  # Existing non-portable slices keep their legacy contract.
            continue
        relative = f"_publication-{binding.repo_id}.json"
        try:
            receipt = json.loads(view.path(relative).read_text())
            summary = receipt["acceptance"]
            tier = summary["tier"]
            catalog = view.path(f"{binding.knowledge_slice}/_catalog.yaml").read_bytes()
            if (receipt.get("repo_id") != binding.repo_id
                    or receipt.get("source_pin") != binding.source_pin
                    or summary.get("source_pin") != binding.source_pin
                    or summary.get("catalog_sha256") != binding.catalog_hash
                    or hashlib.sha256(catalog).hexdigest() != binding.catalog_hash
                    or tier not in ("foundation", "final")
                    or summary.get("init_complete") is not (tier == "final")):
                raise KnowledgeStoreError("portable publication identity or tier differs")
            store = KnowledgeStore(view.root, binding.repo_id)
            if store._bound_acceptance(binding.source_pin, receipt["publication_head"]) != summary:
                raise KnowledgeStoreError("portable publication receipt differs")
            required = ("source", "native", "structural", "format", "retrieval")
            if tier == "final":
                required += ("semantic_depth",)
            if any(summary.get("checks", {}).get(key) is not True for key in required):
                raise KnowledgeStoreError("portable publication is missing passing acceptance checks")
            if tier != "final" and not allow_partial:
                raise KnowledgeStoreError("foundation publication is incomplete; use --allow-partial explicitly")
            tiers[binding.repo_id] = tier
        except (KeyError, ValueError, OSError) as exc:
            raise KnowledgeStoreError(f"{binding.repo_id}: publication acceptance is unavailable: {exc}") from exc
    if not tiers:
        raise KnowledgeStoreError("portable activation needs a bound publication receipt")
    return {"tiers": tiers, "init_complete": all(tier == "final" for tier in tiers.values())}
