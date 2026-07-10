"""Repo profile store — the curated layer of a repo's knowledge
(doc/DESIGN.md §V2.3), architecture borrowed from the personal agent's
profile_store: an immutable evidence layer (RunTraces + archives) below a
small curated `profile.yaml`, mutated ONLY through typed patch ops.

Rules enforced here (§V2.3.2):
- two write tiers: per-run ops are additive; only the consolidation tier may
  rewrite/merge (continuous LLM rewriting measurably corrupts memory);
- every fact carries provenance (source, evidence, first_seen,
  last_confirmed, confirmations) — facts without evidence are rejected;
- stability gate: a fact confirmed >= STABLE_CONFIRMATIONS never loses
  evidence on rewrite, and superseded text goes to `history`, never deleted;
- staleness is a status flip (facts are excluded, not erased);
- the module is the join key: every fact names the module it concerns.

Consumption channels (§V2.3.4): `machine` facts feed step logic, `briefing`
facts render into the word-budgeted always-on prompt slice, `retrieved`
facts surface only through knowledge tools.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import yaml

RUN_OPS = frozenset({"add_fact", "add_evidence", "bump_confirmed"})
CONSOLIDATE_OPS = RUN_OPS | {"rewrite_fact", "merge_facts", "mark_stale"}

CHANNELS = ("machine", "briefing", "retrieved")
KINDS = ("command", "constraint", "convention", "trap", "note")
SOURCES = ("deterministic", "agent", "human")
STABLE_CONFIRMATIONS = 3
BRIEFING_WORD_BUDGET = 350


class ProfileError(Exception):
    """Raised (and caught per-op by `apply_ops`) when a patch op violates a
    provenance or stability rule — never propagated across the write boundary."""


def _today() -> str:
    """Today's date as an `YYYY-MM-DD` string, the stamp for first_seen /
    last_confirmed and the ops log."""
    return time.strftime("%Y-%m-%d")


@dataclass
class Fact:
    """One curated fact plus its full provenance: the `module` it concerns (the
    join key; "repo-wide" for global facts), its `kind`/`channel`, the human
    `text`, and the evidence/confirmation trail (`evidence`, `first_seen`,
    `last_confirmed`, `confirmations`). `status` flips to stale/merged/retired
    rather than the fact being deleted; superseded text and merges accumulate in
    `history` for audit."""

    id: str
    module: str                      # join key ("repo-wide" for global facts)
    kind: str
    channel: str
    text: str
    source: str
    evidence: list[str] = field(default_factory=list)
    first_seen: str = ""
    last_confirmed: str = ""
    confirmations: int = 1
    status: str = "active"           # active | stale | merged | retired
    merged_into: str = ""
    history: list[str] = field(default_factory=list)

    @property
    def stable(self) -> bool:
        """True once confirmed `STABLE_CONFIRMATIONS`+ times — the stability gate
        that forbids rewrites from dropping this fact's evidence."""
        return self.confirmations >= STABLE_CONFIRMATIONS

    def to_doc(self) -> dict:
        """Serialize to the YAML-persisted dict, omitting `merged_into`/`history`
        when empty to keep `profile.yaml` uncluttered."""
        doc = {
            "id": self.id, "module": self.module, "kind": self.kind,
            "channel": self.channel, "text": self.text, "source": self.source,
            "evidence": self.evidence, "first_seen": self.first_seen,
            "last_confirmed": self.last_confirmed,
            "confirmations": self.confirmations, "status": self.status,
        }
        if self.merged_into:
            doc["merged_into"] = self.merged_into
        if self.history:
            doc["history"] = self.history
        return doc


class ProfileStore:
    """`<plugin>/profile/profile.yaml` + ops log + rendered views."""

    def __init__(self, root: str | Path):
        """Load the store rooted at `root`: reads `profile.yaml` if present into
        `meta` (non-fact top-level keys) and the `facts` map keyed by id, else
        starts empty at schema_version 1. The ops log lives beside it."""
        self.root = Path(root)
        self.profile_file = self.root / "profile.yaml"
        self.ops_log = self.root / "ops_log.jsonl"
        self.facts: dict[str, Fact] = {}
        self.meta: dict = {"schema_version": 1}
        if self.profile_file.exists():
            doc = yaml.safe_load(self.profile_file.read_text()) or {}
            self.meta = {k: v for k, v in doc.items() if k != "facts"}
            for f in doc.get("facts") or []:
                fact = Fact(**f)
                self.facts[fact.id] = fact

    # -- typed patch ops: the ONLY write surface ------------------------------

    def apply_ops(self, ops: list[dict], *, tier: str = "run",
                  actor: str = "agent") -> list[str]:
        """Apply typed ops; returns per-op rejection reasons ('' = applied).
        Malformed/forbidden ops are rejected individually, never raised."""
        allowed = RUN_OPS if tier == "run" else CONSOLIDATE_OPS
        results: list[str] = []
        applied: list[dict] = []
        for op in ops:
            kind = str((op or {}).get("op", ""))
            if kind not in allowed:
                results.append(f"op '{kind}' not allowed in tier '{tier}'")
                continue
            try:
                getattr(self, f"_op_{kind}")(op)
                results.append("")
                applied.append(op)
            except ProfileError as exc:
                results.append(str(exc))
        if applied:
            self._append_ops_log(applied, tier=tier, actor=actor)
            self.save()
        return results

    def _op_add_fact(self, op: dict) -> None:
        """`add_fact` op: create a new active Fact (both tiers). Rejects empty
        text and — the provenance rule — any fact with no evidence, and validates
        kind/channel/source against the allowed sets. Ids are derived when absent;
        an add whose id already exists is treated as a confirmation instead (bumps
        confirmations, restamps last_confirmed, unions in new evidence), never a
        duplicate fact. New facts cap stored evidence at 12 items."""
        text = str(op.get("text", "")).strip()
        evidence = [str(e) for e in op.get("evidence") or [] if str(e).strip()]
        if not text:
            raise ProfileError("add_fact: empty text")
        if not evidence:
            raise ProfileError("add_fact: a fact without evidence is rejected "
                               "(provenance rule)")
        module = str(op.get("module") or "repo-wide")
        kind = str(op.get("kind") or "note")
        channel = str(op.get("channel") or "retrieved")
        source = str(op.get("source") or "agent")
        if kind not in KINDS or channel not in CHANNELS or source not in SOURCES:
            raise ProfileError(f"add_fact: bad kind/channel/source "
                               f"({kind}/{channel}/{source})")
        fact_id = str(op.get("id") or f"{module}-{kind}-{len(self.facts) + 1}")
        existing = self.facts.get(fact_id)
        if existing is not None:  # duplicate add == confirmation, not new fact
            existing.confirmations += 1
            existing.last_confirmed = _today()
            for e in evidence:
                if e not in existing.evidence:
                    existing.evidence.append(e)
            return
        self.facts[fact_id] = Fact(
            id=fact_id, module=module, kind=kind, channel=channel, text=text,
            source=source, evidence=evidence[:12], first_seen=_today(),
            last_confirmed=_today())

    def _fact(self, op: dict, key: str = "id") -> Fact:
        """Resolve the Fact named by `op[key]` (default the `id` field), or raise
        `ProfileError` for an unknown id — the shared lookup for ops that target
        an existing fact."""
        fact = self.facts.get(str(op.get(key, "")))
        if fact is None:
            raise ProfileError(f"unknown fact id {op.get(key)!r}")
        return fact

    def _op_add_evidence(self, op: dict) -> None:
        """`add_evidence` op: append new (non-duplicate) evidence strings to an
        existing fact and count it as a fresh confirmation (bump + restamp)."""
        fact = self._fact(op)
        for e in op.get("evidence") or []:
            if str(e).strip() and e not in fact.evidence:
                fact.evidence.append(str(e))
        fact.confirmations += 1
        fact.last_confirmed = _today()

    def _op_bump_confirmed(self, op: dict) -> None:
        """`bump_confirmed` op: re-confirm an existing fact (increment
        confirmations, restamp last_confirmed) without adding new evidence —
        the "seen again, unchanged" signal that drives a fact toward stable."""
        fact = self._fact(op)
        fact.confirmations += 1
        fact.last_confirmed = _today()

    def _op_rewrite_fact(self, op: dict) -> None:
        """`rewrite_fact` op (consolidation tier only): replace a fact's text,
        pushing the old text onto `history`. `evidence` omitted keeps the existing
        set; `[]` is rejected (a fact may never be left without evidence); a new
        list replaces it, but a stable fact may not lose any evidence in the swap.
        Empty replacement text is rejected."""
        fact = self._fact(op)
        text = str(op.get("text", "")).strip()
        if not text:
            raise ProfileError("rewrite_fact: empty text")
        new_evidence = op.get("evidence")  # None = keep; [] = drop all
        if new_evidence is not None:
            new_evidence = [str(e) for e in new_evidence if str(e).strip()]
            if not new_evidence:
                raise ProfileError("rewrite_fact: a fact may never be left "
                                   "without evidence (provenance rule)")
            dropped = [e for e in fact.evidence if e not in new_evidence]
            if fact.stable and dropped:
                raise ProfileError(
                    f"rewrite_fact: fact '{fact.id}' is stable "
                    f"({fact.confirmations} confirmations) — rewrites may not "
                    f"drop evidence ({len(dropped)} item(s))")
        fact.history.append(fact.text)   # superseded text is audit, not waste
        fact.text = text
        if new_evidence is not None:
            fact.evidence = new_evidence

    def _op_merge_facts(self, op: dict) -> None:
        """`merge_facts` op (consolidation tier only): fold the `from` fact into
        the `into` fact — union evidence, sum confirmations, and log the merge in
        `into.history`. The source is not deleted: it becomes a `status: merged`
        stub pointing at `into` via `merged_into`. Rejects merging a fact into
        itself."""
        into = self._fact(op, "into")
        src = self._fact(op, "from")
        if into.id == src.id:
            raise ProfileError("merge_facts: cannot merge a fact into itself")
        for e in src.evidence:
            if e not in into.evidence:
                into.evidence.append(e)
        into.confirmations += src.confirmations
        into.history.append(f"merged '{src.id}': {src.text}")
        src.status = "merged"            # pointer stub, never deleted
        src.merged_into = into.id

    def _op_mark_stale(self, op: dict) -> None:
        """`mark_stale` op (consolidation tier only): flip a fact's status to
        `stale` so it drops out of `active` views — excluded, never erased."""
        self._fact(op).status = "stale"

    # -- persistence -----------------------------------------------------------

    def save(self) -> None:
        """Persist the full state: rewrite `profile.yaml` (meta + all facts) and
        regenerate the human-readable `PROFILE_REPORT.md`. Called after any batch
        of applied ops."""
        self.root.mkdir(parents=True, exist_ok=True)
        doc = {**self.meta,
               "facts": [f.to_doc() for f in self.facts.values()]}
        self.profile_file.write_text(
            yaml.safe_dump(doc, sort_keys=False, allow_unicode=True))
        (self.root / "PROFILE_REPORT.md").write_text(self.render_report())

    def _append_ops_log(self, ops: list[dict], *, tier: str, actor: str) -> None:
        """Append one JSONL record of the applied `ops` (with date, tier, actor)
        to `ops_log.jsonl` — the append-only audit trail of every mutation."""
        self.root.mkdir(parents=True, exist_ok=True)
        with self.ops_log.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"date": _today(), "tier": tier, "actor": actor,
                                "ops": ops}, ensure_ascii=False) + "\n")

    # -- consumption -----------------------------------------------------------

    def active(self, *, channel: str | None = None,
               module: str | None = None) -> list[Fact]:
        """Active (non-stale/merged/retired) facts, optionally filtered to a
        `channel` and/or `module` (module filter also admits "repo-wide" globals),
        sorted most-confirmed first — the consumption view the render/step layers
        read."""
        out = [f for f in self.facts.values() if f.status == "active"]
        if channel:
            out = [f for f in out if f.channel == channel]
        if module:
            out = [f for f in out if f.module in (module, "repo-wide")]
        out.sort(key=lambda f: (-f.confirmations, f.first_seen, f.id))
        return out

    def render_briefing(self, budget_words: int = BRIEFING_WORD_BUDGET) -> str:
        """The always-on prompt slice: short imperative directives only,
        most-confirmed first, hard word budget (§V2.0.1 — minimal,
        non-redundant context measurably beats overviews)."""
        lines: list[str] = []
        words = 0
        for fact in self.active(channel="briefing"):
            w = len(fact.text.split())
            if words + w > budget_words:
                break
            lines.append(f"- {fact.text}")
            words += w
        return "\n".join(lines)

    def render_report(self) -> str:
        """Render `PROFILE_REPORT.md`: every fact (regardless of status, sorted by
        id) with its module/kind/channel/source, text, confirmation trail, listed
        evidence, and merge pointer — the human audit view of provenance."""
        lines = ["# Profile report", "",
                 "Per-fact provenance: how derived, evidence, confirmations.",
                 ""]
        for fact in sorted(self.facts.values(), key=lambda f: f.id):
            lines.append(f"## {fact.id} [{fact.status}]")
            lines.append(f"- module: {fact.module} · kind: {fact.kind} · "
                         f"channel: {fact.channel} · source: {fact.source}")
            lines.append(f"- text: {fact.text}")
            lines.append(f"- confirmations: {fact.confirmations} "
                         f"(first {fact.first_seen}, last {fact.last_confirmed})")
            for e in fact.evidence:
                lines.append(f"  - evidence: {e}")
            if fact.merged_into:
                lines.append(f"- merged into: {fact.merged_into}")
            lines.append("")
        return "\n".join(lines)
