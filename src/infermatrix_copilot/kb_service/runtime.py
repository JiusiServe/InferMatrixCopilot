"""The knowledge service's runtime: one object wiring ledger, sources, models,
outbox and the intake -> gate -> publish flow for one repository at a time.

Change sets live as JSON under ``$KB_STATE_DIR/changesets/<id>.json`` (the
full proposed file texts are too large for ledger rows); the ledger holds
their status, operations and decisions.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .config import RepoLifecycle, general_lifecycle, load_registry
from .gate import changes_between, run_gate
from .intake import draft_changes, merge_drafts, operations_json
from .ledger import Ledger
from .models import ModelGateway, ModelRole, ModelUnavailable, roles_from_env
from .sources import GitHubReader, KnowledgeRepo, SourceError, load_lessons

DEFAULT_BACKFILL_DAYS = 1


@dataclass
class KbRuntime:
    state_dir: Path
    ledger: Ledger
    registry: dict[str, RepoLifecycle]
    gateway: ModelGateway
    generator: ModelRole
    judge: ModelRole
    knowledge: KnowledgeRepo
    github: GitHubReader
    outbox: object | None = None
    clock: Callable[[], float] = time.time
    release_label: Callable[[str], str] = field(default=lambda repo: "")

    @classmethod
    def from_env(cls, settings, *, state_dir: Path | None = None) -> "KbRuntime":
        from ..sdk._resources import adapters_root
        from .cli import DEFAULT_STATE_DIR

        state_dir = Path(state_dir or os.environ.get("KB_STATE_DIR") or DEFAULT_STATE_DIR).expanduser()
        general = general_lifecycle(enabled=os.environ.get("KB_GENERAL_ENABLED", "0") == "1",
                                    mode=os.environ.get("KB_GENERAL_MODE", "shadow"))
        registry = load_registry(Path(os.environ.get("ADAPTERS_DIR") or adapters_root()), general=general)
        ledger = Ledger(state_dir / "kb.db")
        for lifecycle in registry.values():
            ledger.ensure_repo(lifecycle.repo, lifecycle.mode if lifecycle.enabled else "disabled")
        generator, judge = roles_from_env()
        outbox = None
        if os.environ.get("KB_SIGNING_KEY"):
            from ..knowledge_service.signing import load_private_key
            from .outbox import Outbox

            outbox = Outbox(state_dir, load_private_key(os.environ["KB_SIGNING_KEY"]), ledger, clock=time.time)
        return cls(
            state_dir=state_dir, ledger=ledger, registry=registry,
            gateway=ModelGateway(settings, recorder=_trace_recorder(state_dir)),
            generator=generator, judge=judge,
            knowledge=KnowledgeRepo(Path(os.environ.get("KB_KNOWLEDGE_CLONE") or state_dir / "knowledge-repo")),
            github=GitHubReader(), outbox=outbox,
        )

    # -- helpers -------------------------------------------------------------

    def today(self) -> str:
        return dt.datetime.fromtimestamp(self.clock(), dt.timezone.utc).date().isoformat()

    def release_for(self, repo: str) -> str:
        return self.ledger.get_cursor(repo, "release") or self.release_label(repo) or f"r{self.today()}"

    def changeset_path(self, changeset_id: str) -> Path:
        return self.state_dir / "changesets" / f"{changeset_id}.json"

    def save_changeset_files(self, changeset_id: str, data: dict) -> None:
        from .outbox import atomic_write_json

        atomic_write_json(self.changeset_path(changeset_id), data)

    def load_changeset_files(self, changeset_id: str) -> dict:
        return json.loads(self.changeset_path(changeset_id).read_text(encoding="utf-8"))


def _trace_recorder(state_dir: Path):
    """Append every model call (inputs, outputs, usage) to the service trace."""
    path = state_dir / "traces" / "model_calls.jsonl"

    def record(entry: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"at": time.time(), **entry}, ensure_ascii=False) + "\n")

    return record


# -- intake ------------------------------------------------------------------------

def collect_events(rt: KbRuntime, lifecycle: RepoLifecycle) -> int:
    """Record new events for one repository; returns how many were new."""
    new = 0
    if lifecycle.intake.merged_prs and lifecycle.full_name:
        cursor = rt.ledger.get_cursor(lifecycle.repo, "merged_since")
        if cursor is None:
            days = int(os.environ.get("KB_INTAKE_BACKFILL_DAYS", DEFAULT_BACKFILL_DAYS))
            cursor = (dt.datetime.fromtimestamp(rt.clock(), dt.timezone.utc)
                      - dt.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ") + "|0"
            rt.ledger.set_cursor(lifecycle.repo, "merged_since", cursor)
        since, _, after = cursor.partition("|")
        # merge-time order; the cursor is (merge time, PR number) of the last
        # PROCESSED PR, so nothing is skipped and ties cannot stall discovery
        for number, merged_at in rt.github.merged_prs_since(
                lifecycle.full_name, since, after_number=int(after or 0)):
            pr = rt.github.pull_request(lifecycle.full_name, number)
            if rt.ledger.record_event(lifecycle.repo, "merged_pr", str(number), pr.evidence()) is not None:
                new += 1
            rt.ledger.set_cursor(lifecycle.repo, "merged_since", f"{merged_at}|{number}")
    if lifecycle.intake.copilot_runs:
        for lesson in load_lessons(rt.state_dir / "inbox", lifecycle.repo):
            evidence = {"source_reference": f"run {lesson['run_ref']}", "title": "Copilot run lesson",
                        "body": lesson["summary"], "changed_files": [], "diff_excerpt": lesson["diff_excerpt"]}
            if rt.ledger.record_event(lifecycle.repo, "copilot_run", lesson["event_id"], evidence) is not None:
                new += 1
            Path(lesson["path"]).rename(Path(lesson["path"]).with_suffix(".consumed"))
    return new


def run_intake(rt: KbRuntime, lifecycle: RepoLifecycle, *, max_events: int = 10) -> str | None:
    """Draft, gate and stage one change set from pending events. Returns the
    change set id, or None when nothing was proposed or another process holds
    the single-writer lease (two writers would draft the same events and
    request duplicate PRs)."""
    from .ledger import LeaseError

    try:
        with rt.ledger.lease() as owner:
            return _run_intake_locked(rt, lifecycle, max_events=max_events, owner=owner)
    except LeaseError:
        return None


def _run_intake_locked(rt: KbRuntime, lifecycle: RepoLifecycle, *, max_events: int, owner: str) -> str | None:
    events = rt.ledger.events(lifecycle.repo, "pending", limit=max_events)
    if not events:
        return None
    try:
        base_sha = rt.knowledge.fetch()
        base = rt.knowledge.knowledge_files(base_sha)
        external = rt.knowledge.external_texts(base_sha)
    except SourceError:
        return None  # retried next tick; events stay pending
    release, today = rt.release_for(lifecycle.repo), rt.today()
    drafts = []
    for event in events:
        rt.ledger.heartbeat(owner)  # model calls are slow; keep the lease live
        try:
            drafts.append(draft_changes(
                repo=lifecycle.repo, repo_dir=lifecycle.knowledge_dir, event_id=event["id"],
                evidence=event["payload"], files=base, gateway=rt.gateway,
                generator=rt.generator, release=release, today=today))
        except ModelUnavailable as exc:
            # fenced: if this worker lost its lease meanwhile, the new holder may
            # already have staged the event; an unfenced reset would undo that
            rt.ledger.set_event_statuses(owner, [(event["id"], "pending", f"generator unavailable: {exc}")])
            return None  # no weaker fallback; wait for the pinned model
    operations, result, kept, conflicting = merge_drafts(base, drafts, release=release, today=today)
    kept_ids = {i for d in kept for i in d.event_ids}
    updates = []
    for draft in drafts:
        for event_id in draft.event_ids:
            if event_id in kept_ids or draft in conflicting:
                continue  # kept: staged below; conflicting: stays pending, redrafted later
            if draft.rejected:
                updates.append((event_id, "rejected", json.dumps(draft.attempts, ensure_ascii=False)[:2000]))
            else:
                updates.append((event_id, "done", "no rules"))
    rt.ledger.set_event_statuses(owner, updates)
    if not operations or result is None:
        return None
    outside = sorted(p for p in result.files if not p.startswith(lifecycle.knowledge_dir + "/"))
    if outside:  # defence in depth: drafting already refuses these
        rt.ledger.set_event_statuses(owner, [
            (event_id, "rejected", f"writes outside {lifecycle.knowledge_dir}: {outside}")
            for event_id in kept_ids])
        return None
    head = {**base, **result.files}
    evidence = [e["payload"] for e in events if e["id"] in kept_ids]
    rt.ledger.heartbeat(owner)
    decision = run_gate(
        base=base, head=head, changes=changes_between(base, head), external_texts=external,
        evidence=evidence, gateway=rt.gateway, judge=rt.judge, release=release,
        repo_dir=lifecycle.knowledge_dir, protected_rules=lifecycle.protected_rules,
        retire_ratio=lifecycle.retire_ratio, max_files=lifecycle.max_files)
    status = {"pass": "gated", "fail": "failed", "human": "human"}[decision.status]
    verdicts = [{"layer": "L2", "verdict": b.verdict, "block_id": b.block.block_id,
                 "model": b.model, "detail": b.to_dict()} for b in decision.blocks]
    verdicts.append({"layer": "gate", "verdict": decision.status, "detail": {"reasons": decision.reasons}})
    # files first (a crash leaves an orphan file, never a change set without
    # files), then every ledger write in one transaction fenced on the lease
    changeset_id = rt.ledger.new_changeset_id(lifecycle.repo, "intake")
    rt.save_changeset_files(changeset_id, {"base_sha": base_sha, "files": result.files,
                                           "deleted": [], "evidence": evidence})
    try:
        rt.ledger.stage_intake(
            owner, lifecycle.repo, changeset_id, status=status, verdicts=verdicts,
            human_reason="; ".join(decision.reasons) if decision.status == "human" else "",
            drafted_events=sorted(kept_ids),
            detail={
                "operations": operations_json(operations), "event_ids": sorted(kept_ids),
                "base_sha": base_sha, "release": release, "decision": decision.to_dict(),
                "generator": rt.generator.label(), "judge": rt.judge.label(),
            })
    except Exception:
        rt.changeset_path(changeset_id).unlink(missing_ok=True)
        raise
    return changeset_id


def publish(rt: KbRuntime, lifecycle: RepoLifecycle, changeset_id: str) -> str:
    """Hand a gated change set to the publisher, or record it in shadow mode.

    Shadow (and any repository that does not publish) records what WOULD be
    opened and writes nothing to the outbox. The rest of the merge flow
    (verdict signing, enqueue, activation) is driven by the scheduler once the
    publisher reports the PR."""
    changeset = rt.ledger.changeset(changeset_id)
    if changeset["status"] != "gated":
        return changeset["status"]
    state = rt.ledger.repo_state(lifecycle.repo)
    if not lifecycle.auto_merge or not lifecycle.publishes or state["paused"] or rt.outbox is None:
        rt.ledger.update_changeset(changeset_id, status="shadow_recorded")
        return "shadow_recorded"
    if not calibration_current(rt, lifecycle):
        # auto_merge is only as good as the judge: no current passing
        # calibration for THIS judge and THIS case set, no publication
        rt.ledger.update_changeset(changeset_id, status="calibration_required")
        rt.ledger.enqueue_human(lifecycle.repo, "judge calibration missing or outdated", changeset_id)
        return "calibration_required"
    data = rt.load_changeset_files(changeset_id)
    detail = changeset["detail"]
    rt.outbox.issue(lifecycle.repo, "open_pr", {
        "changeset_id": changeset_id,
        "base_sha": data["base_sha"],
        "branch": f"kb/{lifecycle.repo}/{changeset_id}",
        "files": {f"knowledge/{rel}": text for rel, text in data["files"].items()},
        "deleted": [f"knowledge/{rel}" for rel in data.get("deleted", [])],
        "title": f"knowledge({lifecycle.repo}): {len(detail['operations'])} change(s) from intake",
        "body": _pr_body(changeset_id, detail),
    })
    rt.ledger.update_changeset(changeset_id, status="pr_requested")
    return "pr_requested"


def _pr_body(changeset_id: str, detail: dict) -> str:
    lines = [
        f"Generated automatically by the Copilot knowledge service (changeset `{changeset_id}`).",
        "",
        "| op | page | rule |", "|---|---|---|",
    ]
    for op in detail["operations"]:
        lines.append(f"| {op['kind']} | `{op['page']}` | {op.get('new_rule_id') or op['rule_id']} |")
    lines += ["", f"Generator: `{detail['generator']}` · judge: `{detail['judge']}`.",
              "Merge eligibility is decided by the kb-gate check in the merge queue."]
    return "\n".join(lines)


def calibration_record(rt: KbRuntime, lifecycle: RepoLifecycle) -> dict | None:
    raw = rt.ledger.get_cursor(lifecycle.repo, "calibration")
    return json.loads(raw) if raw else None


def calibration_current(rt: KbRuntime, lifecycle: RepoLifecycle) -> bool:
    from .calibration import case_set_digest

    record = calibration_record(rt, lifecycle)
    if not record or not record.get("passed") or lifecycle.adapter_dir is None:
        return False
    return (record.get("judge") == rt.judge.label()
            and record.get("case_set") == case_set_digest(lifecycle.adapter_dir / lifecycle.calibration_set))


def record_calibration(rt_ledger, repo: str, *, judge: str, case_set: str, passed: bool, at: float) -> None:
    rt_ledger.set_cursor(repo, "calibration", json.dumps(
        {"judge": judge, "case_set": case_set, "passed": passed, "at": at}, sort_keys=True))

