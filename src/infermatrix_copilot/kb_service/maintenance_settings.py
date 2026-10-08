"""Explicit, bounded rollout settings for the nightly maintenance worker."""

from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class MaintenanceConfig:
    enabled: bool = False
    daily_budget_usd: float = 50.0
    fair_budget_usd: float = 10.0
    max_units: int = 20
    owner: str = "knowledge-maintainer"
    # label -> {kind: subscription|api, accounted_usd: ...} or API pricing.
    # No guessed prices: an unpriced role cannot dispatch a maintenance call.
    costs: dict = field(default_factory=dict)
    consumers: tuple[str, ...] = ()

    @classmethod
    def from_env(cls):
        raw = os.environ.get("KB_MAINTENANCE_COSTS", "{}")
        costs = json.loads(raw)
        if not isinstance(costs, dict):
            raise ValueError("KB_MAINTENANCE_COSTS must be an object")
        for label, value in costs.items():
            if not isinstance(label, str) or not isinstance(value, dict):
                raise ValueError("maintenance cost entries must be objects keyed by model label")
            if value.get("kind") == "subscription":
                numbers = [value.get("accounted_usd")]
            elif value.get("kind") == "api":
                numbers = [value.get(k) for k in ("threshold_usd", "in_usd_per_mtok", "out_usd_per_mtok", "max_output_tokens")]
            else:
                raise ValueError("maintenance cost kind must be api or subscription")
            if any(type(n) not in (float, int) or not math.isfinite(n) or n <= 0 for n in numbers):
                raise ValueError("maintenance costs require finite positive bounds")
        consumers = json.loads(os.environ.get("KB_CONTAINMENT_CONSUMERS", "[]"))
        if not isinstance(consumers, list) or any(not isinstance(v, str) or not v.strip() for v in consumers):
            raise ValueError("KB_CONTAINMENT_CONSUMERS must be a JSON list of consumer IDs")
        maximum = int(os.environ.get("KB_MAINTENANCE_MAX_UNITS", "20"))
        if not 1 <= maximum <= 1000:
            raise ValueError("KB_MAINTENANCE_MAX_UNITS must be in 1..1000")
        return cls(enabled=os.environ.get("KB_MAINTENANCE_ENABLED", "0").lower() in {"1", "true"},
                   max_units=maximum, costs=costs,
                   owner=os.environ.get("KB_MAINTENANCE_OWNER", "knowledge-maintainer"),
                   consumers=tuple(sorted(set(consumers))))

    def digest(self, *, judge: str, generator: str, prompts: dict) -> str:
        payload = {"version": 1, "judge": judge, "generator": generator,
                   "prompts": prompts, "daily_budget_usd": self.daily_budget_usd,
                   "fair_budget_usd": self.fair_budget_usd, "costs": self.costs,
                   "max_units": self.max_units, "consumers": self.consumers}
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
