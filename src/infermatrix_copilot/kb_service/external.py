"""Knowledge PRs the service did not open (source ④), and the human-approved path.

The scheduler polls the knowledge repository's open PRs. For every non-draft
PR that touches ``knowledge/`` and is not one of the service's own:

* **human-approved**: the PR carries ``kb:human-approved`` and a knowledge
  maintainer (a CODEOWNERS owner of ``.github/kb-gate/`` on main) approved
  its CURRENT head. L1 must pass on the governed pages (the maintainer's
  approval replaces the auto-merge whitelist and L2, never the rest of L1);
  the service then signs a ``human-approved`` verdict naming those reviews.
* **auto**: every changed path is a governed page. The change is judged with
  the full quality gate (L1, L2, consistency) against CURRENT main with the
  PR's changes applied; a pass gets an ``auto`` verdict.

Anything else goes to people once per head (with what would make it pass).
A staged external change set then follows the ordinary merge flow (verdict
comment, PR-stage kb-gate, merge queue). A new head, or a verdict whose
context moved, is simply judged again at the next poll.

Judging "on current main" requires the PR's pre-images to equal main's:
otherwise the merge queue would apply different changes than were signed, and
the author is asked to rebase.
"""

from __future__ import annotations

from typing import Any

from ..knowledge_service.gate_verifier import MAINTAINER_PATH, WHITELIST_CODES, code_owners, parse_codeowners
from ..knowledge_service.l1 import Change, check_changeset
from ..knowledge_service.ops import repo_scope
from .gate import run_gate
from .merge import knowledge_repository
from .runtime import calibration_current

KIND = "external"
HUMAN_LABEL = "kb:human-approved"
GOVERNED = ("knowledge/repos/", "knowledge/general/")
SUFFIXES = (".md", ".yaml")
# statuses after which a head is judged again (the verdict can no longer verify)
REJUDGE = ("head_changed", "stale_context", "superseded")


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


def _maintainers(rt, main_sha: str) -> set[str]:
    text = rt.knowledge.show(main_sha, ".github/CODEOWNERS") or ""
    return set(code_owners(parse_codeowners(text), MAINTAINER_PATH))


def approval_stands(rt, changeset: dict) -> bool:
    """Whether a human-approved external change set's approvals still stand
    (each named maintainer's latest review approves the signed head)."""
    detail = changeset["detail"]
    ids, _names = _approvals(rt, int(changeset["pr_number"]), changeset["head_sha"],
                             {str(n).lower() for n in detail.get("reviewers") or []})
    return bool(ids) and set(detail.get("reviewers") or []) <= set(_names)


def _approvals(rt, number: int, head: str, maintainers: set[str]) -> tuple[list[int], list[str]]:
    """Reviews still standing as approvals of THIS head by maintainers (a later
    review by the same person replaces an earlier one)."""
    reviews: list[dict] = []
    for page in range(1, 51):  # every review: a later one on a further page may retract an approval
        batch = rt.github.get(f"/repos/{knowledge_repository()}/pulls/{number}/reviews",
                              per_page=100, page=page) or []
        reviews.extend(batch)
        if len(batch) < 100:
            break
    latest: dict[str, dict] = {}
    for review in reviews:
        login = str((review.get("user") or {}).get("login") or "").lower()
        if login and review.get("state") in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
            latest[login] = review
    ids, names = [], []
    for login, review in sorted(latest.items()):
        if review.get("state") == "APPROVED" and review.get("commit_id") == head and login in maintainers:
            ids.append(int(review["id"]))
            names.append(login)
    return ids, names


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


def _path_of(changeset: dict) -> str:
    detail = changeset["detail"]
    return detail.get("path") or ("human" if detail.get("source") == "human-approved" else "auto")


def _judged(rt, number: int, head: str, path: str) -> bool:
    """Whether this head was already judged on this path. The key includes the
    path: a head sent to people on the auto path is judged again once a
    maintainer approves it (no push needed), while the paid auto judge still
    runs once per head."""
    for lifecycle in rt.registry.values():
        for changeset in rt.ledger.changesets(lifecycle.repo, _ALL):
            if changeset["kind"] == KIND and changeset["pr_number"] == number and _path_of(changeset) == path \
                    and changeset["head_sha"] == head and changeset["status"] not in REJUDGE:
                if changeset["status"] == "calibration_required" and calibration_current(rt, lifecycle):
                    rt.ledger.update_changeset(changeset["id"], status="superseded")
                    return False  # the judge is calibrated now: judge this head again
                return True
    return False


def _ours(rt, number: int) -> bool:
    for lifecycle in rt.registry.values():
        for changeset in rt.ledger.changesets(lifecycle.repo, _ALL):
            if changeset["pr_number"] == number and changeset["kind"] != KIND:
                return True
    return False


_ALL = ("gated", "pr_requested", "pr_open", "verdict_posted", "queued", "merged", "closed", "failed", "human",
        "head_changed", "stale_context", "superseded", "superseding", "gate_failed", "rebuild_failed",
        "paused", "shadow_recorded", "calibration_required", "approval_withdrawn")


def poll_external(rt) -> list[str]:
    """One pass over open knowledge PRs; needs the scheduler's lease."""
    owner = getattr(rt, "lease_owner", None)
    if rt.outbox is None or not owner:
        return []
    events: list[str] = []
    main_sha = rt.knowledge.fetch()
    maintainers: set[str] | None = None
    for pr in _pulls(rt):
        number = int(pr["number"])
        head = str((pr.get("head") or {}).get("sha") or "")
        labels = {str(label.get("name")) for label in pr.get("labels") or []}
        human = HUMAN_LABEL in labels
        if pr.get("draft") or not head or _ours(rt, number) or _judged(rt, number, head, "human" if human else "auto"):
            continue
        if rt.knowledge.fetch_pull(number) != head:
            continue  # pushed while we looked: next poll
        merge_base = rt.knowledge.merge_base(main_sha, head)
        manifest = rt.knowledge.raw_manifest(merge_base, head)
        paths = [entry["path"] for entry in manifest]
        if not any(p.startswith("knowledge/") for p in paths):
            continue
        path = "human" if human else "auto"
        lifecycle, why = _scope([p for p in paths if p.startswith("knowledge/")], rt.registry)
        if lifecycle is None:
            events.append(_to_people(rt, None, number, head, f"PR #{number} {why}", path))
            continue
        if human:
            maintainers = maintainers if maintainers is not None else _maintainers(rt, main_sha)
            review_ids, reviewers = _approvals(rt, number, head, maintainers)
            if not review_ids:
                continue  # labeled but not (yet) approved on this head by a maintainer: wait
        elif not all(_governed(p) for p in paths):
            events.append(_to_people(rt, lifecycle, number, head,
                                     f"PR #{number} changes paths outside the governed knowledge pages; "
                                     f"a knowledge maintainer can approve it and add {HUMAN_LABEL}", path))
            continue
        base_main = rt.knowledge.knowledge_files(main_sha)
        pre = rt.knowledge.knowledge_files(merge_base)
        post = rt.knowledge.knowledge_files(head)
        governed = [e for e in manifest if _governed(e["path"])]
        rels = [e["path"][len("knowledge/"):] for e in governed]
        moved = [rel for rel in rels if base_main.get(rel) != pre.get(rel)]
        if moved:
            events.append(_to_people(rt, lifecycle, number, head,
                                     f"PR #{number} must be rebased: main changed {moved[:3]} since it branched", path))
            continue
        head_files = dict(base_main)
        for rel in rels:
            if rel in post:
                head_files[rel] = post[rel]
            else:
                head_files.pop(rel, None)
        changes = [Change(e["path"], e["status"] if e["status"] in "AMD" else "M", e["old_mode"], e["new_mode"])
                   for e in (governed if human else manifest)]
        release = rt.release_for(lifecycle.repo)
        detail: dict[str, Any] = {"operations": [], "event_ids": [], "base_sha": main_sha, "release": release,
                                  "manifest": manifest, "external_pr": number,
                                  "title": str(pr.get("title") or ""), "author": str((pr.get("user") or {}).get("login") or "")}
        if human:
            result = check_changeset(base_main, head_files, changes,
                                     external_texts=rt.knowledge.external_texts(main_sha), release=release)
            issues = [i for i in result.issues if i.code not in WHITELIST_CODES]
            if issues:
                events.append(_to_people(rt, lifecycle, number, head, f"PR #{number} fails L1: " + "; ".join(
                    f"{i.code} {i.path} {i.detail}" for i in issues[:3]), path))
                continue
            detail.update(source="human-approved", review_ids=review_ids, reviewers=reviewers,
                          generator="human", judge="human", decision={"blocks": [], "consistency": []},
                          **_lifecycle_bookkeeping(result, head_files))
            status = "pr_open"
        else:
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
                               human_reason="" if status in ("pr_open", "shadow_recorded")
                               else f"external PR #{number}: " + "; ".join(detail["decision"].get("reasons", [])),
                               drafted_events=[], detail=detail)
        rt.ledger.update_changeset(changeset_id, pr_number=number, head_sha=head)
        rt.trace("decision", context={"repo": lifecycle.repo, "changeset_id": changeset_id, "pr": number,
                                      "playbook": "kb-external", "step": "gate"},
                 result={"status": status, "source": detail["source"],
                         "reviewers": detail.get("reviewers", [])})
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


def _to_people(rt, lifecycle, number: int, head: str, reason: str, path: str) -> str:
    """Record a head that people must handle, once (as a human change set)."""
    repo = lifecycle.repo if lifecycle is not None else next(iter(rt.registry))
    changeset_id = rt.ledger.new_changeset_id(repo, KIND)
    rt.save_changeset_files(changeset_id, {"base_sha": "", "files": {}, "deleted": [], "evidence": []})
    rt.ledger.stage_intake(rt.lease_owner, repo, changeset_id, kind=KIND, status="human", verdicts=[],
                           human_reason=reason, drafted_events=[],
                           detail={"external_pr": number, "reason": reason, "path": path})
    rt.ledger.update_changeset(changeset_id, pr_number=number, head_sha=head)
    return f"external {changeset_id} PR #{number} to people"

