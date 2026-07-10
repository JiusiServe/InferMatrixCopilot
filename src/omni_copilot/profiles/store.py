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
    pass


def _today() -> str:
    return time.strftime("%Y-%m-%d")


@dataclass
class Fact:
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
        return self.confirmations >= STABLE_CONFIRMATIONS

    def to_doc(self) -> dict:
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
        fact = self.facts.get(str(op.get(key, "")))
        if fact is None:
            raise ProfileError(f"unknown fact id {op.get(key)!r}")
        return fact

    def _op_add_evidence(self, op: dict) -> None:
        fact = self._fact(op)
        for e in op.get("evidence") or []:
            if str(e).strip() and e not in fact.evidence:
                fact.evidence.append(str(e))
        fact.confirmations += 1
        fact.last_confirmed = _today()

    def _op_bump_confirmed(self, op: dict) -> None:
        fact = self._fact(op)
        fact.confirmations += 1
        fact.last_confirmed = _today()

    def _op_rewrite_fact(self, op: dict) -> None:
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
        self._fact(op).status = "stale"

    # -- persistence -----------------------------------------------------------

    def save(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        doc = {**self.meta,
               "facts": [f.to_doc() for f in self.facts.values()]}
        self.profile_file.write_text(
            yaml.safe_dump(doc, sort_keys=False, allow_unicode=True))
        (self.root / "PROFILE_REPORT.md").write_text(self.render_report())

    def _append_ops_log(self, ops: list[dict], *, tier: str, actor: str) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.ops_log.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"date": _today(), "tier": tier, "actor": actor,
                                "ops": ops}, ensure_ascii=False) + "\n")

    # -- consumption -----------------------------------------------------------

    def active(self, *, channel: str | None = None,
               module: str | None = None) -> list[Fact]:
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
