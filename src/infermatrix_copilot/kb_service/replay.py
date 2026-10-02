"""Replay recorded model calls with another model, and export datasets.

Both work only from the trace store (``trace/1``): a recorded ``model_call``
carries its exact system prompt and prompt as blobs, so a replay sends the
same input to a substitute model and compares structured answers. Nothing here
can reach GitHub, the outbox or the ledger; the only side effects are the
substitute model call itself and a ``replay`` record.

Dataset export turns judge (or generator) calls into rows of (input, the
expensive model's output, the gate decision, the later outcome) for prompt
compression, few-shot selection or distillation. Rows that could leak the
calibration set are dropped before anything is written: calls made by a
calibration run, and prompts citing a calibration case's evidence.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

from .calibration import load_cases
from .models import ModelRole, ModelUnavailable, parse_json_object

REPLAY_PLAYBOOK = "kb-replay"
EXCLUDED_PLAYBOOKS = ("kb-calibrate", REPLAY_PLAYBOOK)


def comparable(data: dict) -> dict:
    """The decision-bearing part of a structured reply."""
    if "dimensions" in data:
        return {"dimensions": data.get("dimensions")}
    if "verdict" in data:
        return {"verdict": data.get("verdict")}
    return data


def replay(store, record_id: str, gateway, role: ModelRole) -> dict:
    from ..trace_store import trace_context

    record = store.get(record_id)
    if record["kind"] != "model_call":
        raise ValueError(f"{record_id} is a {record['kind']} record, not a model call")
    if "prompt" not in record["inputs"]:
        raise ValueError(
            f"{record_id} is a structured conversation record "
            f"(result.format={record.get('result', {}).get('format', '?')}, inputs.messages/tools); "
            "kb replay re-asks single-prompt records only")
    system, prompt = store.blob(record["inputs"]["system"]), store.blob(record["inputs"]["prompt"])
    try:
        recorded = None if record.get("error") else \
            comparable(parse_json_object(store.blob(record["outputs"]["reply"])))
    except (ModelUnavailable, ValueError, KeyError):
        recorded = None  # the recorded call failed: the replay still runs and is recorded
    with trace_context(playbook=REPLAY_PLAYBOOK, replay_of=record_id, run_id=f"replay-{record_id}"):
        try:
            reply = gateway.call_json(role, system=system, prompt=prompt)
            replayed, error = comparable(reply.data), ""
        except ModelUnavailable as exc:
            replayed, error = None, str(exc)
    result = {"replay_of": record_id, "recorded_model": record.get("model", {}), "replay_model": role.label(),
              "recorded": recorded, "replayed": replayed,
              "agree": recorded is not None and replayed is not None and recorded == replayed}
    store.append("replay", context={"replay_of": record_id, "playbook": REPLAY_PLAYBOOK},
                 model={"role": role.name, "provider": role.provider, "model": role.model, "effort": role.effort},
                 result=result, error=error)
    return {**result, "error": error}


def calibration_fingerprints(directories: Iterable[str | Path]) -> list[re.Pattern]:
    """Patterns whose match in a prompt means it overlaps a calibration case:
    each case's evidence reference ANYWHERE in the text (a rule citing
    ``^[PR #8107]`` counts, ``PR #81070`` does not) and its evidence title."""
    marks: list[re.Pattern] = []
    for directory in directories:
        for case in load_cases(directory):
            for item in case.get("evidence") or []:
                reference = str(item.get("source_reference") or "").strip()
                if reference:
                    marks.append(re.compile(rf"(?<![\w#]){re.escape(reference)}(?![\w])"))
                title = str(item.get("title") or "").strip()
                if len(title) >= 20:
                    marks.append(re.compile(re.escape(title)))
    return marks


def export_dataset(store, out_path: str | Path, *, role: str = "judge",
                   calibration_dirs: Iterable[str | Path] = ()) -> dict:
    """Write one JSON line per usable model call of ``role``; returns counts."""
    marks = calibration_fingerprints(calibration_dirs)
    decisions: dict[str, dict] = {}
    by_draft: dict[str, dict] = {}   # generator calls precede their change set: joined by draft key
    for record in store.query(kind="decision", limit=10**6):
        decisions[record["context"].get("changeset_id")] = record["result"]
        for key in record["context"].get("draft_keys") or []:
            by_draft[key] = record["context"]
    outcomes: dict[str, list[str]] = {}
    rule_outcomes: dict[str, list[str]] = {}  # e.g. rule_retired later, by another change set
    for record in store.query(kind="outcome", limit=10**6):
        result = record["result"]
        if result.get("outcome") == "rule_retired":
            rule_outcomes.setdefault(str(result.get("rule_id")), []).append("rule_retired")
        else:
            outcomes.setdefault(record["context"].get("changeset_id") or "", []).append(result["outcome"])
    counts = {"written": 0, "leak_dropped": 0, "calibration_dropped": 0, "failed_dropped": 0,
              "structured_skipped": 0}
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for record in store.query(kind="model_call", role=role, limit=10**6):
            context = record.get("context") or {}
            if context.get("playbook") in EXCLUDED_PLAYBOOKS:
                counts["calibration_dropped"] += 1
                continue
            if record.get("error"):
                counts["failed_dropped"] += 1
                continue
            if "prompt" not in record["inputs"]:
                counts["structured_skipped"] += 1   # agent conversations (messages/1) are not dataset rows
                continue
            system, prompt = store.blob(record["inputs"]["system"]), store.blob(record["inputs"]["prompt"])
            if any(mark.search(prompt) or mark.search(system) for mark in marks):
                counts["leak_dropped"] += 1
                continue
            call_key = f"{context['draft_key']}#{context['attempt']}" \
                if context.get("draft_key") and "attempt" in context else ""
            staged = by_draft.get(call_key, {})
            changeset_id = context.get("changeset_id") or staged.get("changeset_id") or ""
            context = {**context, "rule_ids": context.get("rule_ids") or staged.get("rule_ids") or []}
            handle.write(json.dumps({
                "id": record["id"], "task": f"{role}:{context.get('step') or context.get('playbook') or ''}",
                "repo": context.get("repo", ""), "changeset_id": changeset_id,
                "rule_ids": context.get("rule_ids") or [], "model": record.get("model", {}),
                "system": system, "prompt": prompt, "output": store.blob(record["outputs"]["reply"]),
                "decision": decisions.get(changeset_id), "outcomes": outcomes.get(changeset_id, []),
                "rule_outcomes": {rid: rule_outcomes[rid] for rid in context.get("rule_ids") or []
                                  if rid in rule_outcomes},
            }, ensure_ascii=False) + "\n")
            counts["written"] += 1
    return counts
