"""Paired offline benchmark for the knowledge-intake drafting step (kb-intake.draft).

Repo-invariant: an item set built by ``eval.kb_distill.items`` from any
knowledge-service state directory, the drafting code as it is
(``kb_service.intake.draft_changes``), the production quality gate as it is
(L1 ``check_changeset`` + the pinned L2 judge on every block, with the same
per-rule evidence expansion), and the meta-improvement engine's paired
statistics. Nothing here reaches GitHub, the ledger or the outbox: the only
side effects are model calls and records in the benchmark's own trace store.

Arms
----
* ``replay``: the incumbent as recorded — the production generator's reply to
  the byte-identical prompt (``items.py`` verified it), re-appended as a unit
  of this store so it is judged exactly like every other arm;
* ``run``: a live arm — generator × drafting strategy — on the same items,
  ``N`` replicates each (a subscription generator is cheap; the variance of
  drafting is not).

Every unit is a ``decision(type=draft_result)`` plus its model calls, under
``context.workflow = kb-intake.draft`` with the declared configuration
fingerprint, so the engine's reader, lints and adapter see it as a Tier 2
unit. ``judge`` writes ``outcome`` records (``gate_block`` per block,
``gate_summary`` per unit); ``report`` pairs arms against the incumbent per
item with ``improve.stats``.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sqlite3
import statistics as st
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Iterable

from infermatrix_copilot.config import Settings
from infermatrix_copilot.improve import stats
from infermatrix_copilot.improve.enroll import declarations_for
from infermatrix_copilot.improve.fingerprint import compute as fingerprint_of
from infermatrix_copilot.kb_service.evidence import for_rule
from infermatrix_copilot.kb_service.gate import changes_between, run_gate
from infermatrix_copilot.kb_service.intake import (
    MAX_OPS_PER_EVENT, _validate_reply, draft_changes, operations_json,
)
from infermatrix_copilot.kb_service.models import ModelGateway, ModelRole, ModelUnavailable, parse_json_object
from infermatrix_copilot.kb_service.runtime import trace_recorder
from infermatrix_copilot.kb_service.sources import KnowledgeRepo
from infermatrix_copilot.kb_service.upstream_facts import MirrorObserver
from infermatrix_copilot.knowledge_service.lifecycle import LifecycleError
from infermatrix_copilot.knowledge_service.ops import KnowledgeOperation, apply_operations
from infermatrix_copilot.trace_store import TraceStore, trace_context

WORKFLOW = "kb-intake.draft"
PLAYBOOK = "kb-intake"
DEFAULT_JUDGE = "codex:gpt-6-sol:medium"
INCUMBENT_GENERATOR = "claude-code:claude-opus-5-5"
METRICS = ("net_pass", "yield_pass", "fail", "human", "empty", "rejected", "precision", "gate_score", "gate_pass")


def _github_pull(full_name: str):
    """The read-only PR lookup the gate's fact attestation needs, exactly as
    the service builds it (``GitHubReader``): ``KB_GITHUB_READ_TOKEN`` when
    set, else the gh login's token taken from the CLI at run time (never
    written anywhere), else anonymous. Answers are cached per PR number."""
    import subprocess

    from infermatrix_copilot.kb_service.sources import GitHubReader

    token = os.environ.get("KB_GITHUB_READ_TOKEN", "")
    if not token:
        try:
            token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=30,
                                   check=False).stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            token = ""
    reader = GitHubReader(token=token)
    cache: dict[int, dict] = {}
    lock = threading.Lock()

    def pull(number: int) -> dict:
        with lock:
            if number not in cache:
                cache[number] = reader.get(f"/repos/{full_name}/pulls/{number}")
            return cache[number]
    return pull


@contextlib.contextmanager
def _environ(**values: str):
    """Set process environment variables for the block (the drafting strategy
    knob is read from the environment, the way the service reads it)."""
    previous = {k: os.environ.get(k) for k in values}
    os.environ.update({k: v for k, v in values.items() if v is not None})
    try:
        yield
    finally:
        for k, v in previous.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def incumbent_operations(reply: str, files: dict[str, str], *, repo_dir: str, release: str, today: str,
                         production_rejected: bool = False) -> tuple[list[KnowledgeOperation], bool, str, str]:
    """``(operations, rejected, error, rationale)`` of a recorded reply under
    the production drafting's own checks: the schema, every destination inside
    the repository, and ``apply_operations`` on the base tree. A reply the
    production run itself rejected (repairs exhausted: no change set was
    staged although the last reply carried operations) stays rejected — the
    incumbent's yield is what production got, never more."""
    if production_rejected:
        return [], True, "production rejected this draft after repairs", ""
    try:
        data = parse_json_object(reply)
        _validate_reply(data, MAX_OPS_PER_EVENT)
        operations = [KnowledgeOperation.from_dict(o) for o in data["operations"]]
        outside = [page for op in operations for page in (op.page, op.new_page)
                   if page and not page.startswith(repo_dir + "/")]
        if outside:
            raise LifecycleError(f"{outside[0]} is outside {repo_dir}/")
        if operations:
            apply_operations(files, operations, release=release, today=today)
    except (ModelUnavailable, ValueError, LifecycleError) as exc:
        return [], True, f"recorded reply no longer applies: {exc}", ""
    return operations, False, "", str(data.get("rationale") or "")[:2000]


def incumbent_sample_problem(chosen: dict, *, generator: str = INCUMBENT_GENERATOR,
                             prompt_verified: bool = True) -> str:
    """Why a recorded generator call may NOT stand in for the incumbent under
    the current fingerprint: another generator, an older system prompt, or a
    user prompt the current code does not reproduce. Empty when it may."""
    recorded = f"{chosen.get('provider') or ''}:{chosen.get('model') or ''}"
    if recorded != generator:
        return f"recorded generator {recorded} is not the incumbent {generator}"
    if not chosen.get("system_verified"):
        return "recorded system prompt is not the current drafting prompt"
    if not prompt_verified:
        return "recorded user prompt is not reproduced by the current drafting code"
    return ""


class Bench:
    def __init__(self, bench_dir: str | Path, items_path: str | Path, git_dir: str | Path, *,
                 mirror_dir: str | Path | None = None, state_dir: str | Path | None = None,
                 settings: Settings | None = None, judge: str = ""):
        self.dir = Path(bench_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        data = json.loads(Path(items_path).read_text(encoding="utf-8"))
        self.repo: str = data["repo"]
        self.repo_dir: str = data["repo_dir"]
        self.items: dict[str, dict] = {i["item"]: i for i in data["items"]}
        self.full_name = next((i.get("full_name") for i in data["items"] if i.get("full_name")), "")
        from infermatrix_copilot.kb_service.config import load_registry
        from infermatrix_copilot.sdk._resources import adapters_root

        # the repository's gate parameters (protected rules, circuit breakers) as the service reads them
        self.lifecycle = load_registry(Path(os.environ.get("ADAPTERS_DIR") or adapters_root()))[self.repo]
        self.knowledge = KnowledgeRepo(git_dir)
        self.state_dir = Path(state_dir) if state_dir else Path(data["state_dir"])
        self.store = TraceStore(self.dir / "traces")
        self.settings = settings or Settings(_env_file=None)
        self.gateway = ModelGateway(self.settings, recorder=trace_recorder(self.store))
        self.judge = ModelRole.parse("judge", judge or os.environ.get("KB_JUDGE") or DEFAULT_JUDGE)
        self.decl = declarations_for(self.settings)[WORKFLOW]
        self.observer = MirrorObserver(Path(mirror_dir), self.full_name, _github_pull(self.full_name)) \
            if mirror_dir else None
        self._observer_lock = threading.Lock()
        self._files: dict[str, dict[str, str]] = {}
        self._external: dict[str, dict[str, str]] = {}
        self._lock = threading.RLock()   # re-entrant: a judging is merged and persisted under one hold
        self.units_path = self.dir / "units.json"
        self.units: dict[str, dict] = json.loads(self.units_path.read_text(encoding="utf-8")) \
            if self.units_path.exists() else {}

    # -- state ------------------------------------------------------------------
    def _save_units(self) -> None:
        tmp = self.units_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.units, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
        tmp.replace(self.units_path)

    def _register(self, unit: dict) -> None:
        with self._lock:
            self.units[unit["unit_id"]] = unit
            self._save_units()

    def files(self, base_sha: str) -> dict[str, str]:
        with self._lock:
            if base_sha not in self._files:
                self._files[base_sha] = self.knowledge.knowledge_files(base_sha)
            return self._files[base_sha]

    def external(self, base_sha: str) -> dict[str, str]:
        with self._lock:
            if base_sha not in self._external:
                self._external[base_sha] = self.knowledge.external_texts(base_sha)
            return self._external[base_sha]

    def fingerprint(self, generator: str, strategy: str) -> str:
        fp, manifest = fingerprint_of(self.decl, self.settings,
                                      environ={"KB_GENERATOR": generator, "KB_DRAFT_STRATEGY": strategy})
        if not fp:
            raise RuntimeError(f"incomplete fingerprint: {manifest.get('missing')}")
        self.store.put_blob(json.dumps(manifest, sort_keys=True, ensure_ascii=False))
        return fp

    def select(self, only: Iterable[str] | None) -> list[str]:
        wanted = [i.strip() for i in (only or []) if i.strip()]
        if not wanted:
            return list(self.items)
        missing = [w for w in wanted if w not in self.items]
        if missing:
            raise SystemExit(f"unknown items: {missing}")
        return wanted

    def unit_context(self, unit_id: str, item: dict, *, arm: str, replicate: int, generator: str,
                     strategy: str, fingerprint: str) -> dict:
        return dict(playbook=PLAYBOOK, step="draft", workflow=WORKFLOW, unit_id=unit_id, item=item["item"],
                    fingerprint=fingerprint, repo=self.repo, pr=item["pr"], arm=arm, replicate=replicate,
                    generator=generator, strategy=strategy, unit_tag=os.environ.get("IMPROVE_UNIT_TAG") or None)

    # -- arms -----------------------------------------------------------------------
    def replay(self, arm: str, items: list[str], *, strategy: str = "v1", replicate: int = 1) -> list[str]:
        """The incumbent's recorded reply as a unit of this store. There is
        one recorded sample per item: a ``replicate`` above 1 carries that same
        sample again (an experiment's incumbent side), never a new draw."""
        fp = self.fingerprint(INCUMBENT_GENERATOR, strategy)
        source = TraceStore(self.state_dir / "traces")
        done = []
        for item_id in items:
            unit_id = f"{arm}:{item_id}:{replicate}"
            if unit_id in self.units:
                continue
            item = self.items[item_id]
            chosen = item["incumbent"]
            problem = incumbent_sample_problem(chosen, generator=INCUMBENT_GENERATOR,
                                               prompt_verified=bool(item.get("prompt_verified")))
            if problem:
                # not a sample of the incumbent fingerprint: the item has no incumbent, it is never faked
                print(f"  skipped {unit_id}: {problem}", flush=True)
                continue
            ctx = self.unit_context(unit_id, item, arm=arm, replicate=replicate, generator=INCUMBENT_GENERATOR,
                                    strategy=strategy, fingerprint=fp)
            with trace_context(**ctx):
                for attempt in item["attempts"]:
                    rec = source.get(attempt["record_id"])
                    self.store.append(
                        "model_call",
                        inputs={"system": source.blob(rec["inputs"]["system"]),
                                "prompt": source.blob(rec["inputs"]["prompt"])},
                        outputs={"reply": source.blob(rec["outputs"]["reply"])} if rec.get("outputs", {}).get("reply") else {},
                        model=rec.get("model") or {}, usage=rec.get("usage") or {}, seconds=rec.get("seconds"),
                        result={**(rec.get("result") or {}), "replayed_from": rec["id"], "recorded_at": rec["at"]},
                        error=rec.get("error") or "", context={"attempt": attempt["attempt"]})
                operations, rejected, error, rationale = incumbent_operations(
                    chosen["reply"], self.files(item["base_sha"]), repo_dir=self.repo_dir,
                    release=item["release"], today=item["today"],
                    production_rejected=bool(chosen.get("production_rejected")))
                rec = self.store.append("decision", result={
                    "type": "draft_result", "arm": arm, "replicate": replicate, "generator": INCUMBENT_GENERATOR,
                    "strategy": strategy, "replayed": True, "recorded_record": chosen["record_id"],
                    "operations": operations_json(operations), "rejected": rejected, "empty": not operations,
                    "rationale": rationale, "attempts": len(item["attempts"]) - 1,
                    "seconds": chosen.get("seconds")}, error=error)
            self._register({"unit_id": unit_id, "item": item_id, "arm": arm, "replicate": replicate,
                            "generator": INCUMBENT_GENERATOR, "strategy": strategy, "fingerprint": fp,
                            "decision_id": rec["id"], "status": "drafted", "created": time.time()})
            done.append(unit_id)
        return done

    def run(self, arm: str, items: list[str], *, generator: str, strategy: str, replicates: int = 1,
            workers: int = 3, only_replicate: int | None = None) -> list[str]:
        """A live arm: ``draft_changes`` as the service calls it, per item and
        replicate (``only_replicate``: exactly that replicate index)."""
        role = ModelRole.parse("generator", generator)
        # a strategy the drafting code of this tree does not implement would
        # run as v1 under a v2 fingerprint: refuse rather than mislabel
        from infermatrix_copilot.kb_service import intake as intake_module

        known = tuple(getattr(intake_module, "STRATEGIES", ("v1",)))
        if strategy not in known:
            raise SystemExit(f"strategy {strategy!r} is not implemented by this tree's kb_service.intake "
                             f"(known: {known})")
        fp = self.fingerprint(generator, strategy)
        reps = [only_replicate] if only_replicate else list(range(1, replicates + 1))
        todo = [(i, r) for i in items for r in reps if f"{arm}:{i}:{r}" not in self.units]

        def work(item_id: str, rep: int) -> str:
            item = self.items[item_id]
            unit_id = f"{arm}:{item_id}:{rep}"
            files = self.files(item["base_sha"])
            ctx = self.unit_context(unit_id, item, arm=arm, replicate=rep, generator=generator,
                                    strategy=strategy, fingerprint=fp)
            started = time.time()
            with trace_context(**ctx):
                draft, error = None, ""
                try:
                    draft = draft_changes(repo=self.repo, repo_dir=self.repo_dir, event_id=item["event_id"],
                                          evidence=item["evidence"], files=files, gateway=self.gateway,
                                          generator=role, release=item["release"], today=item["today"])
                except ModelUnavailable as exc:
                    error = str(exc)
                rec = self.store.append("decision", result={
                    "type": "draft_result", "arm": arm, "replicate": rep, "generator": generator,
                    "strategy": strategy, "replayed": False, "seconds": round(time.time() - started, 3),
                    "operations": operations_json(draft.operations) if draft else [],
                    "rejected": draft.rejected if draft else True, "empty": (not draft.operations) if draft else True,
                    "rationale": (draft.rationale if draft else "")[:2000],
                    "attempts": len(draft.attempts) if draft else 0}, error=error)
            self._register({"unit_id": unit_id, "item": item_id, "arm": arm, "replicate": rep, "generator": generator,
                            "strategy": strategy, "fingerprint": fp, "decision_id": rec["id"], "status": "drafted",
                            "created": time.time(), "error": error})
            return unit_id

        done: list[str] = []
        with _environ(KB_DRAFT_STRATEGY=strategy, KB_GENERATOR=generator):
            with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
                futures = {pool.submit(work, i, r): (i, r) for i, r in todo}
                for fut in as_completed(futures):
                    item_id, rep = futures[fut]
                    try:
                        done.append(fut.result())
                        print(f"  drafted {arm} {item_id} r{rep}", flush=True)
                    except Exception as exc:  # noqa: BLE001 - one unit must not stop the arm
                        print(f"  FAILED {arm} {item_id} r{rep}: {type(exc).__name__}: {exc}", flush=True)
        return done

    def retag(self, unit_id: str, tag: str, **fields: Any) -> dict:
        """Mark an existing judged unit as a run of an experiment: one more
        terminal decision carrying the experiment's unit tag, under the
        unit's own context (the engine finds units by tag)."""
        unit = self.units[unit_id]
        item = self.items[unit["item"]]
        ctx = self.unit_context(unit_id, item, arm=unit["arm"], replicate=unit["replicate"],
                                generator=unit["generator"], strategy=unit["strategy"],
                                fingerprint=unit["fingerprint"])
        ctx["unit_tag"] = tag
        with trace_context(**ctx):
            rec = self.store.append("decision", result={"type": "unit_reused", "unit_id": unit_id, **fields})
        unit.setdefault("tags", []).append(tag)
        self._register(unit)
        return rec

    # -- the gate as judge ----------------------------------------------------------
    def _evidence_for(self):
        if self.observer is None:
            return None

        def narrow(text: str, evidence: list[dict]) -> list[dict]:
            with self._observer_lock:
                return for_rule(text, evidence, self.observer)
        return narrow

    def judge_unit(self, unit_id: str, judge_rep: int = 1) -> dict:
        """The production gate (``kb_service.gate.run_gate``: L1, upstream fact
        attestation, L2 per block with the per-rule evidence expansion, the
        owner-directory consistency check, protected rules and circuit
        breakers) on the unit's draft applied to its base tree. The summary
        keeps the gate's own verdict: a change set the gate FAILS lands
        nothing, so its passing blocks count as failed; a change set sent to
        people keeps its block verdicts (nothing merges until someone looks)."""
        unit = self.units[unit_id]
        item = self.items[unit["item"]]
        decision = self.store.get(unit["decision_id"])
        result = decision["result"]
        operations = [KnowledgeOperation.from_dict(o) for o in result.get("operations") or []]
        base = self.files(item["base_sha"])
        judging_id = uuid.uuid4().hex[:12]
        summary: dict[str, Any] = {"type": "gate_summary", "gate_version": 2, "judge_rep": judge_rep,
                                   "judging_id": judging_id, "unit_id": unit_id,
                                   "judge": self.judge.label(), "rejected": bool(result.get("rejected")),
                                   "empty": not operations, "n_blocks": 0, "rule_blocks": 0,
                                   "pass": 0, "fail": 0, "human": 0, "l1_ok": True, "l1_issues": [],
                                   "gate_status": "pass" if not operations else "", "gate_reasons": []}
        outcome_ctx = {"unit_id": unit_id, "item": item["item"], "of": unit_id, "workflow": WORKFLOW,
                       "repo": self.repo, "pr": item["pr"]}
        if operations:
            try:
                applied = apply_operations(base, operations, release=item["release"], today=item["today"])
            except LifecycleError as exc:
                summary.update({"l1_ok": False, "l1_issues": [f"apply: {exc}"], "fail": len(operations),
                                "n_blocks": len(operations), "rule_blocks": len(operations),
                                "gate_status": "fail", "gate_reasons": [f"apply: {exc}"]})
                self.store.append("outcome", context=outcome_ctx, result=summary)
                self._record_judging(unit, summary)
                return summary
            head = {**base, **applied.files}
            rule_ids = sorted({op.new_rule_id or op.rule_id for op in operations if (op.new_rule_id or op.rule_id)})
            if self.observer is not None:
                with self._observer_lock:
                    self.observer.sync()
            with trace_context(playbook=PLAYBOOK, step="gate", unit_id=f"{unit_id}:gate", of=unit_id,
                               item=item["item"], repo=self.repo, pr=item["pr"], rule_ids=rule_ids):
                gate = run_gate(base=base, head=head, changes=changes_between(base, head),
                                external_texts=self.external(item["base_sha"]), evidence=[item["evidence"]],
                                gateway=self.gateway, judge=self.judge, release=item["release"],
                                repo_dir=self.repo_dir, protected_rules=self.lifecycle.protected_rules,
                                retire_ratio=self.lifecycle.retire_ratio, max_files=self.lifecycle.max_files,
                                facts=self.observer, evidence_for=self._evidence_for())
            rule_blocks = [b for b in gate.l1.blocks if b.kind == "rule"]
            summary.update({"l1_issues": [f"{i.code} {i.path} {i.detail}" for i in gate.l1.issues],
                            "l1_ok": gate.l1.ok, "n_blocks": len(gate.l1.blocks), "rule_blocks": len(rule_blocks),
                            "gate_status": gate.status, "gate_reasons": list(gate.reasons),
                            "consistency": [{k: v for k, v in c.items() if k != "pages"} for c in gate.consistency],
                            "facts": len(gate.facts)})
            for verdict in gate.blocks:
                self.store.append("outcome", context=outcome_ctx,
                                  result={"type": "gate_block", "gate_version": self.GATE_VERSION,
                                          "judge_rep": judge_rep, "judging_id": judging_id, **verdict.to_dict()})
                if verdict.block.kind == "rule":
                    summary[verdict.verdict] += 1
            if gate.status == "fail":
                # nothing of a failed change set reaches the knowledge base
                summary["fail"] = len(rule_blocks)
                summary["pass"] = summary["human"] = 0
        self.store.append("outcome", context=outcome_ctx, result=summary)
        self._record_judging(unit, summary)
        return summary

    GATE_VERSION = 2

    def _record_judging(self, unit: dict, summary: dict) -> None:
        """Keep every judging of the unit (one per judge replicate of the
        current gate version); ``summary`` stays the latest for display."""
        with self._lock:                  # read, merge, update and persist under ONE hold
            kept = [s for s in unit.get("judgings") or []
                    if not (s.get("gate_version") == summary["gate_version"]
                            and s.get("judge_rep") == summary["judge_rep"])]
            unit.update({"status": "judged", "summary": summary, "judgings": [*kept, summary]})
            self._register(unit)

    def judgings(self, unit: dict) -> list[dict]:
        """The unit's judgings under the current gate version (a unit judged
        only by an older gate has none and is judged again)."""
        return [s for s in unit.get("judgings") or [] if s.get("gate_version") == self.GATE_VERSION]

    def judge_all(self, unit_ids: list[str], *, workers: int = 4, rejudge: bool = False, replicates: int = 1) -> None:
        """Judge every unit ``replicates`` times (the judge is one vote per
        block in production; a measurement averages several votes)."""
        todo = []
        for u in unit_ids:
            done = {s.get("judge_rep") for s in self.judgings(self.units[u])}
            todo += [(u, k) for k in range(1, replicates + 1) if rejudge or k not in done]
        if self.observer is not None:
            with self._observer_lock:
                self.observer.sync()
        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            futures = {pool.submit(self.judge_unit, u, k): (u, k) for u, k in todo}
            for fut in as_completed(futures):
                unit_id, k = futures[fut]
                try:
                    s = fut.result()
                    print(f"  judged {unit_id} j{k}: blocks {s['rule_blocks']} pass {s['pass']} fail {s['fail']} "
                          f"human {s['human']} gate {s['gate_status']}", flush=True)
                except Exception as exc:  # noqa: BLE001
                    print(f"  FAILED judge {unit_id} j{k}: {type(exc).__name__}: {exc}", flush=True)

    # -- scores -------------------------------------------------------------------
    @staticmethod
    def scores(summary: dict) -> dict[str, float | None]:
        judged = summary["pass"] + summary["fail"]
        n = summary["pass"] + summary["fail"] + summary["human"]
        return {
            # the gate's own verdict on the change set: 1 = it would auto-merge
            "gate_pass": 1.0 if summary.get("gate_status", "pass" if summary["empty"] else "") == "pass" else 0.0,
            "net_pass": float(summary["pass"] - summary["fail"]),
            "yield_pass": float(summary["pass"]),
            "fail": float(summary["fail"]),
            "human": float(summary["human"]),
            "empty": 1.0 if summary["empty"] else 0.0,
            "rejected": 1.0 if summary["rejected"] else 0.0,
            "precision": (summary["pass"] / judged) if judged else None,
            # every proposed rule scored pass=1 / human=0.5 / fail=0; an empty draft is 0 (nothing gained)
            "gate_score": ((summary["pass"] + 0.5 * summary["human"]) / n) if n else 0.0,
        }

    def unit_scores(self, unit: dict) -> dict[str, float | None]:
        """The unit's metrics averaged over its judgings (a metric undefined
        in every judging stays None)."""
        rows = [self.scores(s) for s in (self.judgings(unit) or [unit["summary"]])]
        out: dict[str, float | None] = {}
        for metric in METRICS:
            vals = [r[metric] for r in rows if r[metric] is not None]
            out[metric] = st.mean(vals) if vals else None
        return out

    def arm_units(self, arm: str) -> list[dict]:
        return [u for u in self.units.values() if u["arm"] == arm and u.get("status") == "judged"]

    def report(self, incumbent: str, arms: list[str], *, min_effect: float = 0.25) -> dict:
        inc_by_item: dict[str, list[dict]] = {}
        for u in self.arm_units(incumbent):
            inc_by_item.setdefault(u["item"], []).append(self.unit_scores(u))
        out: dict[str, Any] = {"incumbent": incumbent, "arms": {}, "n_items": len(self.items)}
        out["arms"][incumbent] = self._aggregate(self.arm_units(incumbent))
        for arm in arms:
            units = self.arm_units(arm)
            by_item: dict[str, list[dict]] = {}
            for u in units:
                by_item.setdefault(u["item"], []).append(self.unit_scores(u))
            paired: dict[str, dict] = {}
            for metric in METRICS:
                deltas: dict[str, list[float]] = {}
                for item_id, reps in by_item.items():
                    inc = inc_by_item.get(item_id)
                    if not inc:
                        continue
                    a = [r[metric] for r in reps if r[metric] is not None]
                    b = [r[metric] for r in inc if r[metric] is not None]
                    if not a or not b:
                        continue
                    # replicates averaged inside the item: one paired delta per item
                    deltas[item_id] = [st.mean(a) - st.mean(b)]
                res = stats.paired(deltas, metric)
                n_required = stats.items_required(res.sd or stats.__dict__.get("PRIOR_SD", 0.13), min_effect) \
                    if res.n_items >= 2 else stats.MIN_ITEMS
                direction = "lower" if metric in ("fail", "human", "rejected") else "higher"
                paired[metric] = {"n_items": res.n_items, "mean": round(res.mean, 4), "lo": round(res.lo, 4),
                                  "hi": round(res.hi, 4), "sd": round(res.sd, 4), "n_required": n_required,
                                  "label": stats.label(res, n_required=n_required, direction=direction)}
            out["arms"][arm] = {**self._aggregate(units), "paired_vs_incumbent": paired}
        return out

    def _aggregate(self, units: list[dict]) -> dict:
        if not units:
            return {"units": 0}
        rows = [self.unit_scores(u) for u in units]
        agg: dict[str, Any] = {"units": len(units), "items": len({u["item"] for u in units}),
                               "judgings_per_unit": round(st.mean(len(self.judgings(u) or [u["summary"]]) for u in units), 2)}
        for metric in METRICS:
            vals = [r[metric] for r in rows if r[metric] is not None]
            agg[metric] = round(st.mean(vals), 4) if vals else None
        # block totals over the units, each unit's counts averaged over its judgings
        agg["blocks"] = sum(u["summary"]["rule_blocks"] for u in units)
        agg["pass"] = round(sum(r["yield_pass"] or 0 for r in rows), 2)
        agg["fail_blocks"] = round(sum(r["fail"] or 0 for r in rows), 2)
        agg["human_blocks"] = round(sum(r["human"] or 0 for r in rows), 2)
        agg["gate_fail_units"] = round(sum(1 - (r["gate_pass"] or 0) for u, r in zip(units, rows)
                                           if not u["summary"]["empty"]), 2)
        agg["l1_failures"] = sum(1 for u in units if not u["summary"]["l1_ok"])
        secs, toks_in, toks_out = [], [], []
        for u in units:
            calls = [r for r in self.store.query(kind="model_call", limit=10_000)
                     if (r.get("context") or {}).get("unit_id") == u["unit_id"]]
            secs.append(sum(float(r.get("seconds") or 0) for r in calls))
            toks_in.append(sum(int((r.get("usage") or {}).get("input_tokens") or 0)
                               + int((r.get("usage") or {}).get("cache_creation_input_tokens") or 0)
                               + int((r.get("usage") or {}).get("cache_read_input_tokens") or 0) for r in calls))
            toks_out.append(sum(int((r.get("usage") or {}).get("output_tokens") or 0) for r in calls))
        agg["mean_seconds"] = round(st.mean(secs), 1) if secs else None
        agg["mean_input_tokens"] = round(st.mean(toks_in)) if toks_in else None
        agg["mean_output_tokens"] = round(st.mean(toks_out)) if toks_out else None
        return agg

    # -- forensics ---------------------------------------------------------------------
    def lints(self, arms: list[str] | None = None) -> dict:
        """The engine's Tier 1 lints over every drafting unit, aggregated per
        arm: hit units per lint id, with the record ids that back them."""
        from infermatrix_copilot.improve.lints import Baseline, run_lints
        from infermatrix_copilot.improve.reader import units_between

        baseline = Baseline(settings=self.settings)
        out: dict[str, dict] = {}
        for unit_id, unit in units_between(self.store, 0.0, float("inf"), grace=0.0, lookback=0.0).items():
            if unit.workflow != WORKFLOW or unit_id not in self.units:
                continue
            arm = self.units[unit_id]["arm"]
            if arms and arm not in arms:
                continue
            bucket = out.setdefault(arm, {"units": 0, "hits": {}})
            bucket["units"] += 1
            for finding in run_lints(unit, self.store, baseline):
                hit = bucket["hits"].setdefault(finding.lint, {"units": 0, "examples": []})
                hit["units"] += 1
                if len(hit["examples"]) < 3:
                    hit["examples"].append({"unit": unit_id, "detail": finding.detail[:200]})
        return out

    def show(self, unit_id: str) -> str:
        unit = self.units[unit_id]
        decision = self.store.get(unit["decision_id"])
        lines = [f"# {unit_id}  item {unit['item']}  arm {unit['arm']}  status {unit.get('status')}",
                 f"error: {decision.get('error') or '-'}", f"rationale: {decision['result'].get('rationale', '')[:600]}"]
        for op in decision["result"].get("operations") or []:
            lines.append(f"## op {op.get('kind')} {op.get('page')} {op.get('rule_id')} -> {op.get('new_rule_id') or ''}")
            lines.append((op.get("section_markdown") or "")[:1500])
        for rec in self.store.query(kind="outcome", limit=10_000):
            if (rec.get("context") or {}).get("unit_id") != unit_id:
                continue
            r = rec["result"]
            if r.get("type") == "gate_block":
                lines.append(f"## verdict {r.get('rule_id')} {r.get('op')}: {r.get('verdict')} {r.get('dimensions')}")
                for k, v in (r.get("reasons") or {}).items():
                    lines.append(f"   - {k}: {v}")
            elif r.get("type") == "gate_summary":
                lines.append(f"## summary {json.dumps({k: r[k] for k in ('pass', 'fail', 'human', 'l1_ok', 'l1_issues', 'empty', 'rejected')}, ensure_ascii=False)}")
        return "\n".join(lines)


def _bench(args) -> Bench:
    return Bench(args.bench, args.items, args.git, mirror_dir=args.mirror or None, state_dir=args.state_dir or None,
                 judge=args.judge or "")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("--bench", required=True, help="benchmark directory (trace store + unit registry)")
    parser.add_argument("--items", required=True, help="items.json from eval.kb_distill.items")
    parser.add_argument("--git", required=True, help="knowledge repository checkout/clone (read only)")
    parser.add_argument("--mirror", default="", help="bare mirror of the upstream for the judge's evidence")
    parser.add_argument("--state-dir", default="", help="state snapshot the items came from (replay)")
    parser.add_argument("--judge", default="", help="judge role provider:model[:effort] (default KB_JUDGE)")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("replay", help="the incumbent's recorded replies as units")
    p.add_argument("--arm", default="opus-recorded")
    p.add_argument("--only", default="")
    p = sub.add_parser("run", help="a live arm")
    p.add_argument("--arm", required=True)
    p.add_argument("--generator", required=True)
    p.add_argument("--strategy", default="v1")
    p.add_argument("--replicates", type=int, default=1)
    p.add_argument("--workers", type=int, default=3)
    p.add_argument("--only", default="")
    p = sub.add_parser("judge", help="run the quality gate over drafted units")
    p.add_argument("--arm", default="")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--rejudge", action="store_true", help="judge again units already judged (a newer gate)")
    p.add_argument("--replicates", type=int, default=1, help="judge each unit this many times and average")
    p = sub.add_parser("report")
    p.add_argument("--incumbent", default="opus-recorded")
    p.add_argument("--arms", required=True)
    p.add_argument("--min-effect", type=float, default=0.25)
    p.add_argument("--json", default="")
    p = sub.add_parser("show")
    p.add_argument("unit")
    p = sub.add_parser("lints", help="the engine's Tier 1 lints per arm")
    p.add_argument("--arms", default="")
    args = parser.parse_args(argv)
    bench = _bench(args)
    if args.command == "replay":
        done = bench.replay(args.arm, bench.select(args.only.split(",")))
        print(f"replayed {len(done)} units into arm {args.arm}")
    elif args.command == "run":
        done = bench.run(args.arm, bench.select(args.only.split(",")), generator=args.generator,
                         strategy=args.strategy, replicates=args.replicates, workers=args.workers)
        print(f"drafted {len(done)} units into arm {args.arm}")
    elif args.command == "judge":
        ids = [u for u, v in bench.units.items() if not args.arm or v["arm"] == args.arm]
        bench.judge_all(ids, workers=args.workers, rejudge=args.rejudge, replicates=args.replicates)
    elif args.command == "report":
        report = bench.report(args.incumbent, [a for a in args.arms.split(",") if a], min_effect=args.min_effect)
        text = json.dumps(report, ensure_ascii=False, indent=1)
        if args.json:
            Path(args.json).write_text(text, encoding="utf-8")
        print(text)
    elif args.command == "show":
        print(bench.show(args.unit))
    elif args.command == "lints":
        print(json.dumps(bench.lints([a for a in args.arms.split(",") if a]), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
