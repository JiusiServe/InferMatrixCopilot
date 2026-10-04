"""Summarize the archived 63-gap extraction batch, separately from PR review."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
from zoneinfo import ZoneInfo


def percentile(values, fraction):
    values = sorted(values)
    if not values:
        return None
    index = (len(values) - 1) * fraction
    low = int(index)
    high = min(low + 1, len(values) - 1)
    return values[low] + (values[high] - values[low]) * (index - low)


def stats(values):
    return {"n": len(values), "mean": statistics.mean(values) if values else None,
            "p50": percentile(values, .5), "p90": percentile(values, .9)}


def summarize(archive):
    archive = Path(archive)
    records = []
    for path in sorted(archive.glob("worker-*/init/traces/attempts/*/attempt.json")):
        item = json.loads(path.read_bytes())
        events_path = path.with_name("native-events.jsonl")
        events = ([json.loads(line) for line in events_path.read_text().splitlines() if line.strip()]
                  if events_path.exists() else [])
        started = [e["payload"]["at"] for e in events if e.get("type") == "native.throttle.started"]
        finished = [e["payload"]["at"] for e in events if e.get("type") == "native.throttle.finished"]
        records.append({"id": item["id"], "role": item["model"]["role"], "model": item["model"]["model"],
                        "served_model": item.get("served_model"), "status": item["status"],
                        "completed_native_reply": item["status"] == "complete" and bool(item.get("trace_id")),
                        "at": item["at"], "finished_at": item.get("finished_at"),
                        "gateway_seconds": item.get("seconds"),
                        "native_seconds": finished[-1] - started[0] if started and finished else None,
                        "queue_seconds": started[0] - item["at"] if started else None,
                        "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    generators = [r for r in records if r["role"] == "generator"]
    judges = [r for r in records if r["role"] == "judge"]
    if not records or not any(r["finished_at"] is not None for r in records):
        raise ValueError("no finished extraction attempts in this archive")
    assert len({r["id"] for r in records}) == len(records)
    low = min(r["at"] for r in records)
    high = max(r["finished_at"] for r in records if r["finished_at"] is not None)
    def local(value):
        return datetime.fromtimestamp(value, timezone.utc).astimezone(ZoneInfo("Asia/Shanghai")).isoformat()
    return {"schema": "jiuwenswarm-extraction-timing-v1", "scope": "knowledge_extraction_not_pr_review",
            "archive": str(archive), "generator_attempts": len(generators), "judge_attempts": len(judges),
            "generator_calls": sum(r["completed_native_reply"] for r in generators),
            "judge_calls": sum(r["completed_native_reply"] for r in judges),
            "call_count_basis": "completed reply with native trace identity; incomplete attempts are not inferred dispatched",
            "incomplete_dispatch_unknown": sum(not r["completed_native_reply"] for r in records),
            "all_generator_served_glm53": all(r["served_model"] == "GLM-5.3" for r in generators),
            "all_completed": all(r["status"] == "complete" for r in records),
            "window_start_cn": local(low), "window_end_cn": local(high), "model_window_seconds": high-low,
            "glm_gateway_seconds": stats([r["gateway_seconds"] for r in generators]),
            "glm_native_seconds": stats([r["native_seconds"] for r in generators if r["native_seconds"] is not None]),
            "glm_queue_seconds": stats([r["queue_seconds"] for r in generators if r["queue_seconds"] is not None]),
            "codex_gateway_seconds": stats([r["gateway_seconds"] for r in judges]),
            "actual_invoice_usd": None, "records": records}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    value = summarize(args.archive)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: value[key] for key in ("generator_calls", "judge_calls", "glm_native_seconds", "glm_queue_seconds")}))
