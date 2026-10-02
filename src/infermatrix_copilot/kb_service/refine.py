"""Refine and recheck: what happens to a change the quality gate rejected.

A change the gate rejects is never merged (design v8, D12). For the service's
own change sets the generator gets the rejection reasons, proposes a refined
change on current main, and the WHOLE gate runs again (L1, L2 per block,
consistency; nothing from the rejected judgement is reused). At most
``MAX_REFINES`` refinements per original change; after that it stays unmerged
and goes to people with every round's reasons.

Triggers: a change set the gate failed when it was staged (``failed`` with a
``fail`` decision), and a PR the publisher's local gate refused because of the
change itself (``refine_needed``). A refinement of a change that already has a
PR replaces it the way a rebuild does: the old PR waits in ``superseding``
until its close is observed, the refined change gets a PR of its own.
"""

from __future__ import annotations

import uuid
from pathlib import PurePosixPath

MAX_REFINES = 2
REFINE_MARK = "refine of "
REFINABLE = ("intake", "rebuild", "refine")


def operation_key(operation: dict) -> str:
    return f"{operation['page']}::{operation.get('new_rule_id') or operation['rule_id']}"


def rejected_operations(operations: list[dict], detail: dict) -> set[str]:
    """Name the operations implicated by block, structural or owner failures."""
    from ..knowledge_service.facts import claims_in, holds
    from ..knowledge_service.ops import all_rule_ids

    decision = detail.get("decision") or {}
    ids = {b.get("rule_id") for b in decision.get("blocks") or [] if b.get("verdict") == "fail"}
    owners = {c.get("owner_dir") for c in decision.get("consistency") or []
              if c.get("verdict") == "conflict"}
    bad_facts = {(f["kind"], f.get("pr") or 0, f.get("path") or "", f.get("symbol") or "")
                 for f in decision.get("facts") or [] if f.get("must_hold") and not holds(f)}
    top_level = {path.split("/", 1)[0] for _kind, _pr, path, _symbol in bad_facts if path}
    affected = set()
    for op in operations:
        paths = [p for p in (op["page"], op.get("new_page")) if p]
        names = {op["rule_id"], op.get("new_rule_id")} - {None, ""}
        names.update(all_rule_ids({op["page"]: op.get("section_markdown") or ""}))
        claims = claims_in(op.get("section_markdown") or "", top_level, active=True)
        claims += claims_in("", top_level, active=False, evidence=op.get("evidence") or "")
        if any(claim.key in bad_facts for claim in claims):
            affected.add(operation_key(op))
        if names & ids or any(str(PurePosixPath(p).parent) in owners for p in paths):
            affected.add(operation_key(op))
        for issue in decision.get("l1_issues") or []:
            path = str(issue.get("path") or "").removeprefix("knowledge/")
            if str(issue.get("detail") or "").strip() in names or path in paths or (
                    PurePosixPath(path).name == "_index.md" and
                    any(PurePosixPath(p).parent == PurePosixPath(path).parent for p in paths)):
                affected.add(operation_key(op))
        if any(name in str(problem) for name in names for problem in detail.get("gate_problems") or []):
            affected.add(operation_key(op))
    return affected


def refinement_validator(previous: list[dict], rejected: set[str], audit: dict):
    """Restore untouched learning; every change/drop needs a named disposition.

    Output keys allow a failed add to be renamed, or one conclusion to split
    into several operations. Missing operations never mean implicit removal.
    """
    originals = {operation_key(op): op for op in previous}
    if len(originals) != len(previous):
        from ..knowledge_service.lifecycle import LifecycleError

        raise LifecycleError("refinement original operation keys are not unique; explicit consolidation required")

    def validate(data: dict) -> None:
        supplied = {operation_key(op): op for op in data["operations"]}
        if len(supplied) != len(data["operations"]):
            raise ValueError("refinement output operation keys must be unique")
        entries = data.get("operation_dispositions", [])
        if not isinstance(entries, list):
            raise ValueError("operation_dispositions must be a list")
        dispositions = {}
        for entry in entries:
            if not isinstance(entry, dict) or entry.get("operation") not in originals \
                    or entry.get("operation") in dispositions or entry.get("action") not in ("keep", "revise", "drop") \
                    or not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
                raise ValueError("each disposition needs a unique original operation, action and reason")
            dispositions[entry["operation"]] = entry
        used, complete, normalized = set(), [], []
        for key, op in originals.items():
            entry = dispositions.get(key)
            if key not in rejected:
                if entry and entry["action"] != "keep" or key in supplied and supplied[key] != op:
                    raise ValueError(f"unrejected operation must remain unchanged: {key}")
                entry = {"operation": key, "action": "keep", "reason": "outside rejected gate scope"}
            elif entry is None:
                raise ValueError(f"missing explicit disposition for rejected operation: {key}")
            action = entry["action"]
            replacements = entry.get("replacements", [])
            if not isinstance(replacements, list) or any(not isinstance(k, str) for k in replacements):
                raise ValueError("replacements must list output operation keys")
            if action == "revise":
                if not replacements or len(set(replacements)) != len(replacements) \
                        or any(k not in supplied or k in used for k in replacements):
                    raise ValueError(f"revision needs unclaimed output operations: {key}")
                complete.extend(supplied[k] for k in replacements)
                used.update(replacements)
            else:
                if replacements or action == "drop" and key in supplied:
                    raise ValueError(f"{action} must not carry replacement operations: {key}")
                if action == "keep":
                    if key in supplied and supplied[key] != op:
                        raise ValueError(f"kept operation must remain unchanged: {key}")
                    complete.append(op)
                    if key in supplied:
                        used.add(key)
            normalized.append(entry)
        if set(supplied) - used:
            raise ValueError("refinement contains operations without an original disposition")
        data["operations"] = complete
        audit["operation_dispositions"] = normalized

    return validate


def reasons_of(changeset: dict) -> list[str]:
    """Everything the gate said against this change, most specific first."""
    detail = changeset["detail"]
    return list(dict.fromkeys([str(p) for p in detail.get("gate_problems") or []]
                              + reasons_from_decision(detail.get("decision") or {})))[:30]


def reasons_from_decision(decision: dict) -> list[str]:
    reasons: list[str] = []
    for issue in decision.get("l1_issues") or []:
        reasons.append(f"L1 {issue.get('code')} {issue.get('path', '')} {issue.get('detail', '')}".strip())
    for block in decision.get("blocks") or []:
        if block.get("verdict") == "fail":
            why = "; ".join(f"{k}: {v}" for k, v in (block.get("reasons") or {}).items())
            reasons.append(f"L2 rejected {block.get('rule_id') or block.get('path')}: {why}".strip())
    for item in decision.get("consistency") or []:
        if item.get("verdict") == "conflict":
            reasons.append(f"consistency conflict in {item.get('owner_dir')}: {item.get('conflicts')}")
    reasons += [str(r) for r in decision.get("reasons") or []]
    return list(dict.fromkeys(r for r in reasons if r))[:30]


def needs_refinement(changeset: dict) -> bool:
    detail = changeset["detail"]
    if changeset["kind"] not in REFINABLE or detail.get("refined_as"):
        return False
    if changeset["status"] == "refine_needed":
        return True
    return changeset["status"] == "failed" and (detail.get("decision") or {}).get("status") == "fail"


def _refine_of(rt, repo: str, old_id: str) -> str | None:
    """A refinement already staged for ``old_id`` (resumed, never staged twice),
    in whatever status staging left it (companion_pending included)."""
    for candidate in rt.ledger.changesets_of_kind(repo, "refine"):
        try:
            evidence = rt.load_changeset_files(candidate["id"]).get("evidence") or []
        except (OSError, ValueError):
            continue
        if any(str(item.get("source_reference") or "") == REFINE_MARK + old_id for item in evidence):
            return candidate["id"]
    return None


def refine(rt, lifecycle, changeset: dict) -> str | None:
    """Refine one rejected change set; returns the refined change set's id or
    None (sent to people). Needs the scheduler's lease."""
    from ..knowledge_service.facts import EVIDENCE_PR, FactsError
    from ..knowledge_service.lifecycle import LifecycleError
    from ..trace_store import accepted_key, trace_context
    from .evidence import for_rule
    from .intake import MAX_OPS_PER_EVENT, draft_changes, draft_prompt
    from .merge import _outcome, _request_close
    from .models import ModelUnavailable
    from .packets import MAX_PACKET_BYTES, observer_for
    from .runtime import gate_and_stage, publish
    from .sources import SourceError

    owner = getattr(rt, "lease_owner", None)
    if not owner:
        return None
    detail = changeset["detail"]
    reasons = reasons_of(changeset) or ["the quality gate rejected the change"]
    round_ = int(detail.get("refine_round") or 0) + 1
    history = [*(detail.get("refine_history") or []), {"changeset": changeset["id"], "reasons": reasons}]

    def to_people(why: str) -> None:
        rt.ledger.update_changeset(changeset["id"], status="refine_exhausted",
                                   detail={**detail, "refine_history": history})
        lines = [f"round {i}: {h['changeset']}: " + "; ".join(h["reasons"])[:300] for i, h in enumerate(history)]
        rt.ledger.enqueue_human(lifecycle.repo, f"{why}; not merged. " + " | ".join(lines)[:1800], changeset["id"])
        _outcome(rt, changeset, "refine_exhausted", rounds=len(history))

    if round_ > MAX_REFINES:
        to_people(f"still rejected after {MAX_REFINES} refinements")
        return None
    new_id = _refine_of(rt, lifecycle.repo, changeset["id"])
    if new_id is None:
        base_sha = rt.knowledge.fetch()
        base = rt.knowledge.knowledge_files(base_sha)
        external = rt.knowledge.external_texts(base_sha)
        evidence = rt.load_changeset_files(changeset["id"]).get("evidence") or []
        release, today = rt.release_for(lifecycle.repo), rt.today()
        # Keep every original operation, but only the failed claims' bounded
        # source context enters the generator. The whole gate retains the
        # complete canonical evidence and rejudges every inherited operation.
        previous = detail.get("operations") or []
        rejected = rejected_operations(previous, detail)
        audit: dict = {}
        focus_operations = [op for op in previous if operation_key(op) in rejected] or previous
        focus = "\n\n".join(op.get("section_markdown", "") + "\n" + op.get("evidence", "") + "\n" +
                              " ".join(f"^[PR #{m.group('n')}]" for m in EVIDENCE_PR.finditer(op.get("evidence", "")))
                              for op in focus_operations)
        try:
            bounded_evidence = for_rule(focus, evidence, observer_for(rt, lifecycle, evidence))
        except (FactsError, SourceError) as exc:
            to_people(f"refinement evidence context unavailable: {exc}")
            return None
        prompt_evidence = {"title": "; ".join(str(e.get("title") or "") for e in evidence if e.get("title"))[:500],
                           "changed_files": sorted({f for e in bounded_evidence for f in e.get("changed_files") or []}),
                           "evidence": bounded_evidence,
                           "source_catalog": [{"source_reference": e.get("source_reference", ""),
                                               "title": str(e.get("title") or "")[:200]}
                                              for e in evidence],
                           "previous_operations": previous,
                           "rejected_operations": sorted(rejected),
                           "gate_feedback": reasons,
                           "instruction": "The quality gate rejected the previous operations for the reasons in "
                                          "gate_feedback. Correct only rejected_operations; all other original "
                                          "operations are inherited unchanged. Return operation_dispositions: "
                                          "[{operation: '<old page>::<old new_rule_id or rule_id>', "
                                          "action: 'keep|revise|drop', reason: '<evidence-backed reason>', "
                                          "replacements: ['<output page>::<output new_rule_id or rule_id>']}]. "
                                          "Every rejected operation needs a disposition. revise maps to one or "
                                          "more operations in your reply; drop explicitly explains why the "
                                          "cited evidence makes this learning incorrect, obsolete or duplicate. "
                                          "Omit unchanged operations; never silently omit rejected learning. "
                                          "Acceptance checks describe required future verification, not a "
                                          "claim that an unobserved test run passed. A changed meaning requires "
                                          "replace with a fresh successor ID, not edit_same_meaning."}
        prompt_size = len(draft_prompt(lifecycle.repo, prompt_evidence, base, lifecycle.knowledge_dir).encode("utf-8"))
        if prompt_size > MAX_PACKET_BYTES:
            to_people(f"refinement prompt exceeds {MAX_PACKET_BYTES} bytes ({prompt_size}); no truncated refinement")
            return None
        key, holder = f"refine:{lifecycle.repo}:{changeset['id']}:{uuid.uuid4().hex[:8]}", {}
        try:
            with trace_context(draft_key=key, _accepted=holder, step="refine", refine_of=changeset["id"]):
                # the whole change set is refined at once: as many operations as
                # the events it combines may carry
                limit = max(MAX_OPS_PER_EVENT * max(1, len(evidence)), len(detail.get("operations") or []))
                draft = draft_changes(repo=lifecycle.repo, repo_dir=lifecycle.knowledge_dir, event_id=0,
                                      evidence=prompt_evidence, files=base, gateway=rt.gateway,
                                      generator=rt.generator, release=release, today=today,
                                      max_operations=limit,
                                      reply_validator=refinement_validator(previous, rejected, audit))
        except ModelUnavailable:
            return None  # the pinned generator is unavailable: tried again next pass
        except LifecycleError as exc:
            to_people(f"refinement could not be drafted: {exc}")
            return None
        if draft.rejected or not draft.operations or draft.result is None:
            detail = {**detail, **audit}
            rt.trace("outcome", context={"changeset_id": changeset["id"], "step": "refine"},
                     result={"outcome": "refinement_invalid", "action": "refinement", "status": "no_valid_refinement", **audit})
            to_people("the generator proposed no valid refinement")
            return None
        mark = {"source_reference": REFINE_MARK + changeset["id"], "title": "; ".join(reasons)[:300]}
        source_events = detail.get("source_event_ids") or detail.get("event_ids") or []
        rt.trace("outcome", context={"changeset_id": changeset["id"], "step": "refine",
                                     "source_event_ids": source_events},
                 result={"outcome": "refinement_prepared", "action": "refinement", **audit})
        new_id = gate_and_stage(rt, lifecycle, owner, kind="refine", base=base, base_sha=base_sha,
                                external=external, operations=draft.operations, result=draft.result,
                                evidence=[*evidence, mark], event_ids=[], release=release,
                                draft_keys=[accepted_key(key, holder)] if accepted_key(key, holder) else [],
                                extra_detail={"refine_round": round_, "refine_history": history,
                                              "source_event_ids": source_events, **audit,
                                              "generator": draft.generator})
    open_pr = changeset.get("pr_number") is not None
    rt.ledger.update_changeset(changeset["id"], status="superseding" if open_pr else "refined",
                               detail={**detail, "refined_as": new_id, "refine_history": history,
                                       "superseded_because": "refined after the quality gate rejected it"})
    _outcome(rt, changeset, "refined", replaced_by=new_id, round=round_)
    if open_pr:
        _request_close(rt, lifecycle.repo, rt.ledger.changeset(changeset["id"]))
    if rt.ledger.changeset(new_id)["status"] == "gated":
        publish(rt, lifecycle, new_id)
    return new_id


def refine_pending(rt, lifecycle) -> list[str]:
    """One pass: refine every rejected change set of this repository."""
    events: list[str] = []
    if not getattr(rt, "lease_owner", None):
        return events
    for changeset in rt.ledger.changesets(lifecycle.repo, ("failed", "refine_needed")):
        if not needs_refinement(changeset):
            continue
        new_id = refine(rt, lifecycle, changeset)
        events.append(f"refined {changeset['id']} as {new_id}" if new_id else f"refine_stopped {changeset['id']}")
    return events
