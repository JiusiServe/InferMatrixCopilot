"""Incremental feature implementation depth; existing rule deepen is unchanged."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, replace
from pathlib import Path

from ..knowledge_service.l1 import Block
from ..knowledge_service.lifecycle import Page
from ..knowledge_service.ops import page_over_capacity
from ..knowledge_service.pinned_claims import Evidence, check_rules, evidence_for
from .depth_inputs import DepthContext, SYSTEM_DEPTH, prompt
from .init_budget import BudgetExhausted
from .init_coverage import Owner
from .init_history import _CheckpointBudget
from .init_knowledge import MAX_DOC_BYTES, _Knowledge
from .init_stages import _one_line, _page_frontmatter
from .init_support import InitError, InitRecord, classify_verdict, generate, judge
from .knowledge_coverage import audit_coverage, inventory
from .knowledge_depth import FACETS, audit_depth, depth_page, digest, render_block, validate_draft, verified_blocks
from .models import ModelUnavailable


@dataclass
class _KnowledgeDepth(_Knowledge):
    STAGE = "knowledge-deepen"
    retry_unfinished: bool = False

    def _chain_boundary(self) -> str:
        return "knowledge"  # same prerequisites as explanatory knowledge, no shadow flip

    def _cache_reusable(self, previous: InitRecord) -> bool:
        return bool(previous.depth.get("done")) and not self.retry_unfinished

    def _mode_identity(self) -> bool:
        return False  # promote a checked preview without repeating extraction

    def _init_identity(self) -> str:
        return repr(replace(self.lifecycle.init, budget_usd=0.0)) + (
            ":subscription-generator" if self.rt.subscription_generator else "")

    def _input_options(self) -> dict:
        return {**super()._input_options(), "depth_version": 1}

    def _base_for_run(self, latest: str) -> str:
        previous = InitRecord.load(self.rt.state_dir, self.lifecycle.repo, self.STAGE)
        if previous and previous.depth:
            if self.retry_unfinished and previous.status == "published":
                raise InitError("published depth batch is immutable; use a new state directory after merging its PR")
            if not re.fullmatch(r"[0-9a-f]{40}", previous.kb_base_sha):
                raise InitError("depth checkpoint has an invalid knowledge baseline")
            if self.rt.knowledge._git("cat-file", "-t", previous.kb_base_sha).decode().strip() != "commit":
                raise InitError("depth checkpoint knowledge baseline is unavailable")
            if not self.pin:
                self.pin = previous.pin
            return previous.kb_base_sha
        return latest

    def _restore_progress(self, previous: InitRecord | None) -> list[str]:
        if previous and previous.depth:
            current = self.record.inputs_digest
            self.record = previous
            if previous.inputs_digest != current:
                return ["depth inputs changed; use a new state directory for a new pinned batch"]
            self.record.status = "started"
            self.record.problems = []
            self.record.dry_run = self.dry_run
        self.budget = _CheckpointBudget(self.lifecycle.init.budget_usd, self.record, self.rt.state_dir)
        return []

    def _precheck(self) -> list[str]:
        problems = super()._precheck()
        if not getattr(self, "coverage_policy", None):
            problems.append("knowledge-deepen requires an explicit feature/production coverage policy")
        return problems

    def _build(self, tree: Path) -> InitRecord:
        policy = self.coverage_policy
        self.today = time.strftime("%Y-%m-%d", time.gmtime(self.record.started_at))
        state = self.record.depth
        state.setdefault("version", 1)
        states = state.setdefault("features", {})
        accepted = state.setdefault("accepted", {})
        expected = {depth_page(f) for f in policy.features}
        if set(accepted) - expected or set(states) - {f.id for f in policy.features}:
            return self._blocked(["depth checkpoint contains pages or features outside the current policy"])
        for feature in policy.features:
            page = depth_page(feature)
            if page in accepted:
                blocks, problems = verified_blocks(accepted[page], feature, tree, self.record.pin)
                entry = states.get(feature.id, {})
                if problems or not blocks or entry.get("accepted_sha256") != digest(accepted[page]):
                    return self._blocked(["depth checkpoint accepted page failed its pinned proof"])
                self.head[page] = accepted[page]
                self._link_page(page, _one_line(feature.title) + "：实现深读")
            elif page in self.head:
                _, problems = verified_blocks(self.head[page], feature, tree, self.record.pin)
                if problems:
                    return self._blocked(problems + ["refresh stale/edited depth explicitly before extending it"])
        context = DepthContext(tree, inventory(tree, policy))
        # A completed first pass takes priority over repairs, so one difficult
        # feature cannot consume the budget before the others get visited.
        ceilings = {f.id: states.get(f.id, {}).get("attempts", 0) + 2 if self.retry_unfinished else 2
                    for f in policy.features}
        stopped = False
        for repair in (False, True):
            for feature in policy.features:
                entry = states.setdefault(feature.id, {})
                current = audit_depth({depth_page(feature): self.head[depth_page(feature)]}, tree,
                                      replace(policy, features=(feature,)), self.record.pin) \
                    if depth_page(feature) in self.head else None
                if current and current["complete"]:
                    entry["status"] = "complete"
                    continue
                attempts = entry.get("attempts", 0)
                if (not repair and attempts >= ceilings[feature.id] - 1) or attempts >= ceilings[feature.id]:
                    continue
                if self.budget.spent_usd + self.lifecycle.init.judge_call_usd > self.budget.limit_usd:
                    stopped = True
                    break
                try:
                    self._attempt(tree, context, feature, entry)
                except BudgetExhausted:
                    stopped = True
                    break
                except (ModelUnavailable, ValueError) as exc:
                    entry["status"] = "unavailable"
                    entry["reason"] = str(exc)[:1000]
                    entry.pop("draft", None)
                finally:
                    self.record.save(self.rt.state_dir)
            if stopped:
                break
        state["done"] = not stopped
        depth = audit_depth(self.head, tree, policy, self.record.pin)
        breadth = audit_coverage(self.head, tree, policy, full_name=self.lifecycle.full_name, pin=self.record.pin)
        self.record.coverage = {"semantic_depth": depth, "breadth": breadth}
        self.record.unfinished = [f"depth {id_}/{facet}" for id_, item in depth["features"].items()
                                  for facet in item["missing_facets"]]
        self.record.notes = [n for n in self.record.notes if not n.startswith("knowledge depth stopped:")]
        self.record.notes.append("knowledge depth stopped: " + ("budget exhausted; checkpoints preserve remaining work"
                                  if stopped else "all features visited; unsupported facets remain explicit"))
        self.record.save(self.rt.state_dir)
        claims = {page: text for page, text in accepted.items()}
        entries = [Evidence.from_dict(e) for group in self.record.evidence.values() for e in group]
        return self._conclude(claims, entries)

    def _docs(self, tree: Path, feature, owner) -> list[dict]:
        docs = self._sources(tree, list(feature.docs), MAX_DOC_BYTES // 2)
        used = sum(len(d["text"].encode("utf-8")) for d in docs)
        for item in self._docs_for(tree, owner):
            if any(d["path"] == item["path"] for d in docs):
                continue
            lines, size = [], 0
            for line in item["text"].splitlines():
                amount = len(line.encode("utf-8"))
                if used + size + amount > MAX_DOC_BYTES:
                    break
                lines.append(line)
                size += amount
            if lines:
                docs.append({**item, "text": "\n".join(lines), "end": len(lines)})
                used += size
        return [{**d, "start": 1, "text": d["text"].splitlines()} for d in docs]

    def _judge_evidence(self, entries: list[Evidence]) -> list[dict]:
        # Supply every attested line, without the rule judge's 8KB truncation.
        # Merge overlaps so seven facets do not repeat the same large excerpt.
        out = []
        for path in dict.fromkeys(e.path for e in entries):
            spans = []
            for start, end in sorted((e.start, e.end) for e in entries if e.path == path):
                if spans and start <= spans[-1][1] + 1:
                    spans[-1] = (spans[-1][0], max(end, spans[-1][1]))
                else:
                    spans.append((start, end))
            lines = (self.observer.file_text(self.record.pin, path) or "").splitlines()
            for start, end in spans:
                out.append({"source_reference": f"{self.lifecycle.full_name}@{self.record.pin}:"
                                                 f"{path}:L{start}-L{end}",
                            "kind": "upstream_text", "text": [f"{n}: {lines[n - 1]}" for n in range(start, end + 1)]})
        return out

    def _attempt(self, tree, context, feature, entry):
        page = depth_page(feature)
        old = self.head.get(page, "")
        old_blocks, problems = verified_blocks(old, feature, tree, self.record.pin) if old else ({}, [])
        if problems:
            raise ValueError("; ".join(problems))
        owner = next((o for o in self.owners if o.owner == feature.owner),
                     Owner(feature.owner, feature.page, tuple(p.split("*", 1)[0] for p in feature.source_globs)))
        docs = self._docs(tree, feature, owner)
        existing = self._bounded_context(self._existing_knowledge(owner, self.head.get(feature.page, "")))
        retrieval = context.build(feature, self.head.get(feature.page, ""), docs)
        files = retrieval["files"]
        if not files:
            entry["attempts"] = entry.get("attempts", 0) + 1
            raise ModelUnavailable("feature has no implementation source slices")
        payload = {"repository": self.lifecycle.full_name, "pin": self.record.pin,
                   "feature": {"id": feature.id, "title": feature.title, "owner": feature.owner},
                   "facets": [f for f in FACETS if f not in old_blocks], **retrieval, "docs": docs,
                   "existing_knowledge": {p: text.splitlines() for p, text in existing.items()},
                   "language_sample": self._language_sample()}
        if entry.get("reason"):
            payload["previous_review"] = entry["reason"]
        if "draft" not in entry:
            entry["attempts"] = entry.get("attempts", 0) + 1
            entry["status"] = "extracting"
            self.record.save(self.rt.state_dir)
            entry["draft"] = generate(self.rt, self.budget, self.lifecycle.init, system=SYSTEM_DEPTH,
                                      prompt=prompt(payload), validate=validate_draft).data
            entry["context_sha256"] = digest(prompt(payload))
            entry["status"] = "extracted"
            self.record.save(self.rt.state_dir)
        elif entry.get("context_sha256") != digest(prompt(payload)):
            raise ValueError("checkpoint draft context changed")
        data = entry["draft"]
        validate_draft(data)
        offered = files + docs
        blocks = dict(old_blocks)
        for section in data["sections"]:
            if section["facet"] in old_blocks or section["facet"] not in payload["facets"]:
                raise ValueError("draft attempts to rewrite an existing depth facet")
            for evidence in section["evidence"]:
                if not any(item["path"] == evidence["path"] and item["start"] <= evidence["start"]
                           <= evidence["end"] <= item["end"] for item in offered):
                    raise ValueError("depth evidence crosses an unshown source gap")
            blocks[section["facet"]] = render_block(feature, section, tree, self.lifecycle.full_name, self.record.pin)
        if blocks == old_blocks:
            raise ModelUnavailable("no supported new depth facets")
        front = _page_frontmatter(_one_line(feature.title) + "：实现深读", kind="architecture",
                                  today=self.today, tags=self.tags)
        related = f"[功能概览]({Path(feature.page).name}) · [owner 入口](_index.md)\n\n"
        proposed = front + related + "\n\n".join(blocks[f] for f in FACETS if f in blocks) + "\n"
        # Retrieve exactly the attested spans, including retained prior facets.
        evidence = []
        for block in blocks.values():
            proof = json.loads(re.search(r"<!-- kb:depth-proof (.*?) -->", block, re.S).group(1))
            evidence += [evidence_for(self.observer, e["path"], e["start"], e["end"]) for e in proof["evidence"]]
        sources = [f"{self.lifecycle.full_name}@{self.record.pin}:{e.path}:L{e.start}-L{e.end}" for e in evidence]
        proposed = Page.parse(proposed).with_sources(list(dict.fromkeys(sources))).render()
        issues = check_rules({feature.id: proposed}, self.observer)
        if issues or page_over_capacity(proposed):
            raise ValueError("; ".join(issues) or "depth page exceeds capacity")
        hashed = digest(proposed)
        cached = entry.get("checked")
        if cached and cached.get("text_sha256") == hashed:
            label, reasons, model = cached["verdict"], cached["reasons"], cached["model"]
        else:
            result = judge(self.rt, self.budget, self.lifecycle.init,
                           Block("prose", page, "", "prose", hashed), base={page: old} if old else {},
                           head={**self.head, page: proposed}, evidence=self._judge_evidence(evidence))
            label, reasons, model = classify_verdict(result), result.reasons, result.model
            entry["checked"] = {"verdict": label, "reasons": reasons, "model": model, "text_sha256": hashed}
            self.record.save(self.rt.state_dir)
        key = "depth:" + feature.id
        self.record.verdicts[key] = entry["checked"]
        entry["shown_source_files"] = sorted({f["path"] for f in files})
        entry["status"] = label
        entry["reason"] = json.dumps(reasons, ensure_ascii=False)
        entry.pop("draft", None)
        entry.pop("checked", None)
        if label != "pass":
            return
        self.head[page] = proposed
        self.record.depth["accepted"][page] = proposed
        entry["accepted_sha256"] = digest(proposed)
        self.record.evidence[key] = [e.to_dict() for e in evidence]
        self._link_page(page, _one_line(feature.title) + "：实现深读")
