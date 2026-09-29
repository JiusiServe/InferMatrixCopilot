"""Knowledge PRs the service did not open (source ④).

The scheduler polls the knowledge repository's open PRs. For every non-draft
PR that touches ``knowledge/`` and is not one of the service's own, when every
changed path is a governed page, the change is judged with the full quality
gate (L1, L2, consistency) against CURRENT main with the PR's changes applied;
a pass gets an ``auto`` verdict. There is no human-approved path (design v8):
a PR changing anything else is not merged by the service and its author is
told so.

A PR that does not pass is never merged (design v8, D12): the author is told
why in ONE findings comment on the PR, updated in place, and the PR is checked
again once a day (not on every push) until it passes. A passing PR follows the
ordinary merge flow: a signed verdict in a ``merge`` item, the publisher's
local gate, the merge. A passing head is not judged again; a new head, or a
merge refused meanwhile, is judged at the next daily pass.

Judging "on current main" requires the PR's pre-images to equal main's:
otherwise the merge would apply different changes than were signed, and the
author is asked to rebase.
"""

from __future__ import annotations

import json
from typing import Any

from ..knowledge_service.l1 import Change
from ..knowledge_service.ops import repo_scope
from .gate import run_gate
from .merge import IN_FLIGHT, knowledge_repository
from .runtime import calibration_current

KIND = "external"
GOVERNED = ("knowledge/repos/", "knowledge/general/")
SUFFIXES = (".md", ".yaml")
# statuses after which a head is judged again at the next daily pass: it did
# not pass, or its verdict can no longer verify
REJUDGE = ("head_changed", "stale_context", "superseded", "failed", "human", "gate_failed", "rebuild_failed")
EXTERNAL_EVERY = 24 * 3600  # other people's PRs are checked once a day
CHECKED_CURSOR = "external_checked:{number}"  # per PR: a failed pass never re-judges finished ones
FINDINGS_MARKER = "<!-- kb-findings:v1 -->"
# + PR number, kept GLOBALLY (a comment belongs to the PR, whatever
# repository scope it touches now): the latest findings until delivered
FINDINGS_CURSOR = "findings:"


def _governed(path: str) -> bool:
    return path.startswith(GOVERNED) and path.endswith(SUFFIXES)


def _pulls(rt) -> list[dict]:
    out: list[dict] = []
    for page in range(1, 11):
        batch = rt.github.get(f"/repos/{knowledge_repository()}/pulls", state="open", per_page=100, page=page)
        out.extend(batch or [])
        if len(batch or []) < 100:
            break
    return out


def _scope(paths: list[str], registry: dict) -> tuple[Any, str]:
    """The one lifecycle a change belongs to, or (None, why not)."""
    scopes = set()
    for path in paths:
        rel = path[len("knowledge/"):]
        try:
            scopes.add(repo_scope(rel).split("/")[-1])
        except Exception:  # noqa: BLE001 - outside repos/ and general/
            continue
    if len(scopes) > 1:
        return None, f"spans several repositories: {sorted(scopes)}"
    if not scopes:
        # only non-governed knowledge (knowledge/tools, skills, ...): owned by
        # the cross-repository scope when it takes PRs, else the first
        # repository that does (the ledger is partitioned by repository)
        takers = [lc for name, lc in sorted(registry.items()) if lc.enabled and lc.intake.human_prs]
        general = registry.get("general")
        chosen = general if general in takers else (takers[0] if takers else None)
        if chosen is None:
            return None, "no repository takes knowledge PRs through the service"
        return chosen, ""
    lifecycle = registry.get(scopes.pop())
    if lifecycle is None or not lifecycle.enabled or not lifecycle.intake.human_prs:
        return None, "its repository does not take knowledge PRs through the service"
    return lifecycle, ""


def _judged(rt, number: int, head: str) -> bool:
    """Whether this head was already judged (the paid judge runs once per head)."""
    for lifecycle in rt.registry.values():
        for changeset in rt.ledger.changesets(lifecycle.repo, _ALL):
            if changeset["kind"] == KIND and changeset["pr_number"] == number \
                    and changeset["head_sha"] == head and changeset["status"] not in REJUDGE:
                if changeset["status"] == "calibration_required" and calibration_current(rt, lifecycle):
                    rt.ledger.update_changeset(changeset["id"], status="superseded")
                    return False  # the judge is calibrated now: judge this head again
                return True
    return False


def _ours(rt, number: int) -> bool:
    """A PR the service opened, in ANY status (refine_needed, refine_exhausted,
    superseding...): it is never judged again as someone else's PR."""
    for lifecycle in rt.registry.values():
        if any(cs["kind"] != KIND for cs in rt.ledger.changesets_for_pr(lifecycle.repo, number)):
            return True
    return False


# every status an external change set can have; the in-flight ones come from
# the merge flow itself, so a new merge state can never be judged twice
_ALL = tuple(dict.fromkeys((
    *IN_FLIGHT, "gated", "merged", "closed", "failed", "human",
    "head_changed", "stale_context", "superseded", "superseding", "gate_failed", "rebuild_failed",
    "paused", "shadow_recorded", "calibration_required")))


def poll_external(rt, *, force: bool = False) -> list[str]:
    """A pass over open knowledge PRs; needs the scheduler's lease. Each PR is
    checked at most once per ``EXTERNAL_EVERY``, recorded per PR in the ledger
    as soon as it was checked: a restart, or a pass that fails half-way, never
    checks a PR twice in a day. ``force`` ignores the daily limit."""
    owner = getattr(rt, "lease_owner", None)
    if rt.outbox is None or not owner:
        return []
    return renew_findings(rt) + _poll(rt, owner, force=force)


def _due(rt, number: int, force: bool) -> bool:
    last = float(rt.ledger.get_cursor("*", CHECKED_CURSOR.format(number=number)) or 0)
    return force or rt.clock() - last >= EXTERNAL_EVERY


def _checked(rt, number: int) -> None:
    rt.ledger.set_cursor("*", CHECKED_CURSOR.format(number=number), str(rt.clock()))


def findings_text(number: int, head: str, status: str, reasons: list[str], today: str) -> str:
    """The one comment the service keeps on another person's knowledge PR."""
    lines = [FINDINGS_MARKER, f"**Knowledge quality gate** · checked {today} at `{head[:12]}` "
             "(checked again once a day)", ""]
    if status in ("pr_open", "merged"):
        lines.append("Result: **passed**. The publisher merges it after its final check on the exact merge result.")
    elif status == "shadow_recorded":
        lines.append("Result: **passed** (this repository is in shadow mode: nothing is merged automatically yet).")
    else:
        lines.append("Result: **not passed**. This PR will not be merged until the problems below are fixed; "
                     "push a fix and it is checked again at the next daily pass.")
        lines += ["", "Problems:"] + [f"- {r}" for r in (reasons or ["the change needs a person's decision"])[:20]]
    return "\n".join(lines) + "\n"


def _findings_lifecycle(rt, paths: list[str]):
    """Which repository may carry the findings of a PR that belongs to none
    (it spans several): only when every scope it touches publishes (a private
    upstream's name must never appear), through one in auto_merge."""
    scopes = set()
    for path in paths:
        try:
            scopes.add(repo_scope(path[len("knowledge/"):]).split("/")[-1])
        except Exception:  # noqa: BLE001 - outside repos/ and general/
            continue
    lifecycles = [rt.registry.get(name) for name in sorted(scopes)]
    if not lifecycles or any(lc is None or not lc.publishes for lc in lifecycles):
        return None
    return next((lc for lc in lifecycles if lc.auto_merge), None)


def post_findings(rt, lifecycle, number: int, head: str, status: str, reasons: list[str]) -> None:
    """Hand the findings comment to the publisher (never in shadow mode, never
    for a private upstream: those publish nothing)."""
    if lifecycle is None or not lifecycle.auto_merge or not lifecycle.publishes:
        return
    comment = findings_text(number, head, status, reasons, rt.today())
    _issue_findings(rt, lifecycle.repo, number, head, comment)


def _issue_findings(rt, repo: str, number: int, head: str, comment: str, revision: float | None = None) -> None:
    """Issue the findings and remember them (one record per PR) until the
    publisher confirms delivery. ``revision`` is when the findings were
    written: the publisher drops an item older than what it already posted,
    and a renewal keeps the original revision, so it can never overtake newer
    findings."""
    revision = rt.clock() if revision is None else revision
    item = rt.outbox.issue(repo, "post_findings", {
        "pr": number, "head_sha": head, "marker": FINDINGS_MARKER, "comment": comment, "revision": revision})
    rt.ledger.set_cursor("*", f"{FINDINGS_CURSOR}{number}", json.dumps({
        "repo": repo, "item_id": item.id, "expires_at": item.expires_at, "head_sha": head, "comment": comment,
        "revision": revision, "delivered": False}))


def findings_delivered(rt, ack: dict) -> None:
    """The publisher's ack for a findings item: only the latest one counts."""
    name = f"{FINDINGS_CURSOR}{int(ack.get('pr') or 0)}"
    raw = rt.ledger.get_cursor("*", name)
    if not raw or not ack.get("ok"):
        return
    record = json.loads(raw)
    if record.get("item_id") == ack.get("item_id"):
        rt.ledger.set_cursor("*", name, json.dumps({**record, "delivered": True}))


def renew_findings(rt) -> list[str]:
    """Findings that expired undelivered (the publisher was down or GitHub
    failed for a day) are issued again with the same text: an author is
    never left without them, whatever the PR's status."""
    events = []
    for name, raw in rt.ledger.cursors_with_prefix("*", FINDINGS_CURSOR).items():
        record = json.loads(raw)
        if record.get("delivered") or float(record.get("expires_at") or 0) > rt.clock():
            continue
        lifecycle = rt.registry.get(record.get("repo"))
        if lifecycle is None or not lifecycle.auto_merge or not lifecycle.publishes:
            continue  # its repository publishes nothing any more
        number = int(name[len(FINDINGS_CURSOR):])
        _issue_findings(rt, lifecycle.repo, number, record["head_sha"], record["comment"],
                        revision=float(record.get("revision") or 0))
        events.append(f"findings reissued PR #{number}")
    return events


def _decision_reasons(decision: dict) -> list[str]:
    from .refine import reasons_from_decision

    return reasons_from_decision(decision)


def _poll(rt, owner: str, *, force: bool = False) -> list[str]:
    events: list[str] = []
    main_sha = rt.knowledge.fetch()
    for pr in _pulls(rt):
        number = int(pr["number"])
        head = str((pr.get("head") or {}).get("sha") or "")
        if pr.get("draft") or not head or _ours(rt, number) or _judged(rt, number, head):
            continue
        if not _due(rt, number, force):
            continue  # checked today already: once a day, not on every push
        if rt.knowledge.fetch_pull(number) != head:
            continue  # pushed while we looked: next poll
        merge_base = rt.knowledge.merge_base(main_sha, head)
        manifest = rt.knowledge.raw_manifest(merge_base, head)
        paths = [entry["path"] for entry in manifest]
        if not any(p.startswith("knowledge/") for p in paths):
            continue
        lifecycle, why = _scope([p for p in paths if p.startswith("knowledge/")], rt.registry)
        if lifecycle is None:
            events.append(_to_people(rt, None, number, head, f"PR #{number} {why}",
                                     findings_via=_findings_lifecycle(rt, paths)))
            _checked(rt, number)
            continue
        if not all(_governed(p) for p in paths):
            outside = sorted(p for p in paths if not _governed(p))
            events.append(_to_people(rt, lifecycle, number, head,
                                     f"PR #{number} changes paths outside the governed knowledge pages "
                                     f"({', '.join(outside[:3])}); the service only merges governed pages: "
                                     "split those changes into their own PR"))
            _checked(rt, number)
            continue
        base_main = rt.knowledge.knowledge_files(main_sha)
        pre = rt.knowledge.knowledge_files(merge_base)
        post = rt.knowledge.knowledge_files(head)
        governed = [e for e in manifest if _governed(e["path"])]
        rels = [e["path"][len("knowledge/"):] for e in governed]
        moved = [rel for rel in rels if base_main.get(rel) != pre.get(rel)]
        if moved:
            events.append(_to_people(rt, lifecycle, number, head,
                                     f"PR #{number} must be rebased: main changed {moved[:3]} since it branched"))
            _checked(rt, number)
            continue
        head_files = dict(base_main)
        for rel in rels:
            if rel in post:
                head_files[rel] = post[rel]
            else:
                head_files.pop(rel, None)
        changes = [Change(e["path"], e["status"] if e["status"] in "AMD" else "M", e["old_mode"], e["new_mode"])
                   for e in manifest]
        release = rt.release_for(lifecycle.repo)
        detail: dict[str, Any] = {"operations": [], "event_ids": [], "base_sha": main_sha, "release": release,
                                  "manifest": manifest, "external_pr": number,
                                  "title": str(pr.get("title") or ""), "author": str((pr.get("user") or {}).get("login") or "")}
        evidence = [{"source_reference": f"PR #{number}", "title": detail["title"],
                     "body": str(pr.get("body") or "")[:3000], "author": detail["author"]}]
        decision = run_gate(base=base_main, head=head_files, changes=changes,
                            external_texts=rt.knowledge.external_texts(main_sha), evidence=evidence,
                            gateway=rt.gateway, judge=rt.judge, release=release,
                            repo_dir=lifecycle.knowledge_dir, protected_rules=lifecycle.protected_rules,
                            retire_ratio=lifecycle.retire_ratio, max_files=lifecycle.max_files)
        detail.update(source="auto", generator="human", judge=rt.judge.label(), decision=decision.to_dict(),
                      **_lifecycle_bookkeeping(decision.l1, head_files))
        status = {"pass": "pr_open", "fail": "failed", "human": "human"}[decision.status]
        if status == "pr_open" and lifecycle.auto_merge and not calibration_current(rt, lifecycle):
            # an auto verdict is only as good as the judge (as for our own PRs)
            status = "calibration_required"
            detail["decision"]["reasons"] = [*detail["decision"].get("reasons", []),
                                             "judge calibration missing or outdated"]
        if status == "pr_open" and not lifecycle.auto_merge:
            status = "shadow_recorded"
        changeset_id = rt.ledger.new_changeset_id(lifecycle.repo, KIND)
        rt.save_changeset_files(changeset_id, {"base_sha": main_sha, "files": {r: head_files[r] for r in rels
                                                                              if r in head_files},
                                               "deleted": [r for r in rels if r not in head_files], "evidence": []})
        rt.ledger.stage_intake(owner, lifecycle.repo, changeset_id, kind=KIND, status=status, verdicts=[],
                               # the author fixes it (told in the findings comment): not people's queue
                               human_reason="",
                               drafted_events=[], detail=detail)
        rt.ledger.update_changeset(changeset_id, pr_number=number, head_sha=head)
        rt.trace("decision", context={"repo": lifecycle.repo, "changeset_id": changeset_id, "pr": number,
                                      "playbook": "kb-external", "step": "gate"},
                 result={"status": status, "source": detail["source"]})
        post_findings(rt, lifecycle, number, head, status,
                      [] if status in ("pr_open", "shadow_recorded") else _decision_reasons(detail["decision"]))
        _checked(rt, number)
        events.append(f"external {changeset_id} PR #{number} {detail['source']} {status}")
    return events


def _lifecycle_bookkeeping(result, head_files: dict[str, str]) -> dict:
    """The rules this change retires and purges, as the merge flow records them
    (our own change sets derive this from their operations)."""
    from ..knowledge_service.ops import all_rule_ids

    pages = {rid: page for page, text in sorted(head_files.items()) if page.endswith(".md")
             for rid in all_rule_ids({page: text})}
    return {"retirements": [{"rule_id": rid, "page": pages.get(rid, "")} for rid in result.retired],
            "purges": list(result.purged)}


def _to_people(rt, lifecycle, number: int, head: str, reason: str, findings_via=None) -> str:
    """Record a head the gate cannot take as is; the author is told why."""
    repo = lifecycle.repo if lifecycle is not None else next(iter(rt.registry))
    changeset_id = rt.ledger.new_changeset_id(repo, KIND)
    rt.save_changeset_files(changeset_id, {"base_sha": "", "files": {}, "deleted": [], "evidence": []})
    rt.ledger.stage_intake(rt.lease_owner, repo, changeset_id, kind=KIND, status="human", verdicts=[],
                           human_reason="", drafted_events=[],
                           detail={"external_pr": number, "reason": reason})
    rt.ledger.update_changeset(changeset_id, pr_number=number, head_sha=head)
    post_findings(rt, lifecycle or findings_via, number, head, "human", [reason])
    return f"external {changeset_id} PR #{number} to people"

