"""Build the item set for the knowledge-distillation (kb-intake draft) benchmark.

Repo-invariant: every input comes from a knowledge-service state directory
(``kb.db``, ``changesets/``, ``traces/``) and the adapter registry, never from
anything specific to one upstream repository.

An *item* is one intake event (one merged upstream PR) together with the exact
knowledge tree the production generator drafted against. The production
generator's recorded call (``model_call`` with ``role=generator``,
``step=draft``) is the *incumbent* sample: its prompt is rebuilt from the event
evidence and the candidate base trees and must reproduce the recorded prompt
byte for byte, which pins the base commit and proves the sample is a genuine
draw of the current drafting code.

Usage::

    python -m eval.kb_distill.items --state-dir SNAPSHOT --git REPO --repo vllm-omni --out items.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sqlite3
from pathlib import Path

from infermatrix_copilot.kb_service.config import load_registry
from infermatrix_copilot.kb_service.intake import SYSTEM, draft_prompt
from infermatrix_copilot.kb_service.models import ModelUnavailable, parse_json_object
from infermatrix_copilot.kb_service.sources import KnowledgeRepo
from infermatrix_copilot.trace_store import TraceStore


def _ledger(state_dir: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{state_dir / 'kb.db'}?mode=ro", uri=True)


def _records(store: TraceStore, state_dir: Path, kind: str, **where: str) -> list[dict]:
    con = sqlite3.connect(f"file:{state_dir / 'traces' / 'index.db'}?mode=ro", uri=True)
    clauses = ["kind = ?"]
    params: list[str] = [kind]
    for key, value in where.items():
        clauses.append(f"{key} = ?")
        params.append(value)
    ids = [r[0] for r in con.execute(f"select id from records where {' and '.join(clauses)} order by at", params)]
    return [store.get(i) for i in ids]


def _ops_count(text: str) -> int | None:
    try:
        data = parse_json_object(text)
    except ModelUnavailable:
        return None
    ops = data.get("operations")
    return len(ops) if isinstance(ops, list) else None


def build_items(state_dir: Path, git_dir: Path, repo: str, adapters_dir: Path | None = None) -> dict:
    if adapters_dir is None:
        from infermatrix_copilot.sdk._resources import adapters_root

        adapters_dir = Path(adapters_root())
    lifecycle = load_registry(adapters_dir)[repo]
    store = TraceStore(state_dir / "traces")
    ledger = _ledger(state_dir)
    knowledge = KnowledgeRepo(git_dir)

    events = {}
    for row in ledger.execute("select id, external_id, payload, status, detail, created_at from events "
                              "where repo = ? and source = 'merged_pr' order by id", (repo,)):
        events[int(row[0])] = {"event_id": int(row[0]), "pr": int(row[1]), "evidence": json.loads(row[2]),
                               "status": row[3], "detail": row[4], "created_at": float(row[5])}
    changesets = {}
    for row in ledger.execute("select id, kind, detail, created_at from changesets where repo = ?", (repo,)):
        detail = json.loads(row[2])
        changesets[row[0]] = {"kind": row[1], "base_sha": detail.get("base_sha", ""), "release": detail.get("release"),
                              "event_ids": detail.get("event_ids") or [], "created_at": float(row[3]),
                              "decision": detail.get("decision") or {}, "operations": detail.get("operations") or []}
    bases = sorted({c["base_sha"] for c in changesets.values() if c["base_sha"]})
    release = ledger.execute("select value from cursors where repo = ? and name = 'release'", (repo,)).fetchone()
    release = release[0] if release else ""

    accepted: dict[str, str] = {}   # "draft_key#attempt" -> changeset id
    run_base: dict[str, str] = {}   # intake run id -> the base tree that run drafted against
    for rec in _records(store, state_dir, "decision"):
        ctx = rec.get("context") or {}
        for key in ctx.get("draft_keys") or []:
            accepted[key] = str(ctx.get("changeset_id") or "")
        changeset = changesets.get(str(ctx.get("changeset_id") or ""))
        if ctx.get("run_id") and changeset and changeset["base_sha"]:
            run_base.setdefault(str(ctx["run_id"]), changeset["base_sha"])
    # a run that staged no change set (every event taught nothing) drafted
    # against the tree the nearest earlier run used
    run_order = sorted(run_base)

    drafts: dict[str, list[dict]] = {}
    for rec in _records(store, state_dir, "model_call", role="generator"):
        ctx = rec.get("context") or {}
        if ctx.get("step") != "draft" or not str(ctx.get("draft_key", "")).startswith("event:"):
            continue
        drafts.setdefault(str(ctx["draft_key"]), []).append(rec)

    files_at: dict[str, dict[str, str]] = {}

    def files(sha: str) -> dict[str, str]:
        if sha not in files_at:
            files_at[sha] = knowledge.knowledge_files(sha)
        return files_at[sha]

    items = []
    for key, records in drafts.items():
        _, key_repo, event_id, _ = key.split(":", 3)
        if key_repo != repo:
            continue
        event = events.get(int(event_id))
        if event is None:
            continue
        records.sort(key=lambda r: r["at"])
        attempts = []
        for rec in records:
            reply = store.blob(rec["outputs"]["reply"]) if rec.get("outputs", {}).get("reply") else ""
            model = rec.get("model") or {}
            system = store.blob(rec["inputs"]["system"]) if rec.get("inputs", {}).get("system") else ""
            attempts.append({"record_id": rec["id"], "attempt": int((rec.get("context") or {}).get("attempt") or 0),
                             "at": rec["at"], "error": rec.get("error") or "", "reply": reply,
                             "ops": _ops_count(reply) if reply else None, "usage": rec.get("usage") or {},
                             "seconds": rec.get("seconds"), "served_model": model.get("served_model", ""),
                             "provider": model.get("provider", ""), "model": model.get("model", ""),
                             # the incumbent is a sample of the CURRENT drafting code only when its
                             # system prompt is the current one (the user prompt is verified below)
                             "system_verified": system.strip() == SYSTEM.strip()})
        chosen = next((a for a in attempts if f"{key}#{a['attempt']}" in accepted), None)
        if chosen is None:
            usable = [a for a in attempts if a["ops"] is not None]
            chosen = usable[-1] if usable else attempts[-1]
        changeset_id = accepted.get(f"{key}#{chosen['attempt']}", "")
        # no change set although the last reply carried operations: production
        # exhausted its repairs and consumed the event as "no rules"
        chosen["production_rejected"] = not changeset_id and bool(chosen["ops"])
        prompt = store.blob(records[0]["inputs"]["prompt"])
        run_id = str((records[0].get("context") or {}).get("run_id") or "")
        # the base the run recorded first; then every other base whose tree
        # reproduces the recorded prompt (newest run first)
        preferred = [(changesets.get(changeset_id) or {}).get("base_sha", ""), run_base.get(run_id, "")]
        candidates = [s for s in preferred if s] + [run_base[r] for r in reversed(run_order)] + bases
        base_sha = ""
        for sha in dict.fromkeys(candidates):
            rebuilt = draft_prompt(repo, event["evidence"], files(sha), lifecycle.knowledge_dir)
            if rebuilt == prompt:
                base_sha = sha
                break
        items.append({
            "item": f"{repo}#{event['pr']}", "event_id": event["event_id"], "pr": event["pr"], "repo": repo,
            "repo_dir": lifecycle.knowledge_dir, "full_name": lifecycle.full_name,
            "release": (changesets.get(changeset_id) or {}).get("release") or release,
            "today": dt.datetime.fromtimestamp(chosen["at"], dt.timezone.utc).date().isoformat(),
            "base_sha": base_sha, "prompt_verified": bool(base_sha), "draft_key": key,
            "evidence": event["evidence"], "event_status": event["status"], "event_detail": event["detail"],
            "incumbent": {**chosen, "changeset_id": changeset_id},
            "attempts": [{k: v for k, v in a.items() if k != "reply"} for a in attempts],
            "ledger_blocks": [b for b in (changesets.get(changeset_id) or {}).get("decision", {}).get("blocks", [])],
        })
    # one item per event: the latest drafting wins (its base is the newest tree)
    latest: dict[int, dict] = {}
    for item in sorted(items, key=lambda i: i["incumbent"]["at"]):
        latest[item["event_id"]] = item
    out = sorted(latest.values(), key=lambda i: i["event_id"])
    return {"repo": repo, "repo_dir": lifecycle.knowledge_dir, "state_dir": str(state_dir), "git": str(git_dir),
            "bases": bases, "items": out,
            "superseded_draftings": [i["draft_key"] for i in items if latest[i["event_id"]] is not i]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("--state-dir", required=True, help="a snapshot of the knowledge service state directory")
    parser.add_argument("--git", required=True, help="a checkout/clone of the knowledge repository (read only)")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--adapters-dir", default="")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    data = build_items(Path(args.state_dir), Path(args.git), args.repo,
                       Path(args.adapters_dir) if args.adapters_dir else None)
    Path(args.out).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    items = data["items"]
    verified = sum(1 for i in items if i["prompt_verified"])
    print(f"{len(items)} items ({verified} prompt-verified) over bases {', '.join(b[:8] for b in data['bases'])}; "
          f"{len(data['superseded_draftings'])} superseded draftings")
    for i in items:
        inc = i["incumbent"]
        print(f"  {i['item']:<18} base {i['base_sha'][:8] or '????????'} attempt {inc['attempt']} ops {inc['ops']} "
              f"cs {inc['changeset_id'] or '-'} blocks {[(b['rule_id'], b['verdict']) for b in i['ledger_blocks']]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
