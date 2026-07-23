#!/usr/bin/env python3
"""Trace-completeness gate for a campaign arm — the executable form of
"every run is fully traced".

A run is COMPLETE when all of the following hold in its run dir:

1. `trace.jsonl` (spans), `run_trace.jsonl` (RunTrace events) and
   `events.jsonl` (request/response payloads) all exist and are non-empty.
   `events.jsonl` only appears with ``AGENT_TRACE_IO=1``; its absence means the
   campaign ran without payload capture and the corpus is not replayable.
2. `trace.jsonl` carries a `run_meta` header, so the trace is self-describing
   once copied out of its directory.
3. Call counts agree: one `llm` span, one `llm.request` and one `llm.response`
   per actual provider request. A request with no response is a dropped call.
4. Token totals agree between `events.jsonl`, `trace.jsonl` and `metrics.json`.
   The counts ride on the response event precisely so events.jsonl is
   self-contained (commit f9de995); this asserts the two views never diverge.

metrics.json is derived from the spans by `cost_from_spans`, so check 4's real
content is events-vs-spans — metrics is included to catch a stale/absent file.

Usage:
  verify_traces.py <arm_dir> [<arm_dir> ...] [--json inventory.json]
Exit 0 when every run in every arm is complete, else 1 with reasons.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError:
        return []
    return out


def verify_run(run_dir: Path) -> dict:
    """Inspect one run dir; returns a record with `errors` ([] when complete)."""
    rec: dict = {"run_dir": str(run_dir), "errors": []}
    err = rec["errors"]

    spans_p = run_dir / "trace.jsonl"
    events_p = run_dir / "events.jsonl"
    rt_p = run_dir / "run_trace.jsonl"
    for name, p in (("trace.jsonl", spans_p), ("run_trace.jsonl", rt_p),
                    ("events.jsonl", events_p)):
        if not p.exists():
            err.append(f"missing {name}")
        elif p.stat().st_size == 0:
            err.append(f"empty {name}")

    spans = _jsonl(spans_p)
    events = _jsonl(events_p)
    rec["run_trace_events"] = len(_jsonl(rt_p))
    rec["bytes"] = {p.name: (p.stat().st_size if p.exists() else 0)
                    for p in (spans_p, events_p, rt_p)}

    # tracing.run_meta writes a {"t": "run"} header line into the span file so
    # the trace stays self-describing when copied out on its own
    if spans and not any(r.get("t") == "run" for r in spans):
        err.append("no run_meta header in trace.jsonl")

    llm_spans = [r for r in spans if r.get("name") == "llm"]
    reqs = [e for e in events if e.get("kind") == "llm.request"]
    resps = [e for e in events if e.get("kind") == "llm.response"]
    rec["llm_spans"] = len(llm_spans)
    rec["llm_requests"] = len(reqs)
    rec["llm_responses"] = len(resps)
    rec["spans_total"] = len(spans)
    if events_p.exists():
        if len(reqs) != len(resps):
            err.append(f"llm.request {len(reqs)} != llm.response {len(resps)} "
                       "(dropped call)")
        if len(resps) != len(llm_spans):
            err.append(f"llm.response {len(resps)} != llm spans "
                       f"{len(llm_spans)}")

    def _sum(items, keys):
        return {k: sum(int((i.get("attr", i) or {}).get(k) or 0) for i in items)
                for k in keys}

    span_tok = _sum(llm_spans, ("prompt_tokens", "completion_tokens"))
    ev_tok = _sum(resps, ("input_tokens", "output_tokens"))
    rec["tokens"] = {
        "spans": {"in": span_tok["prompt_tokens"],
                  "out": span_tok["completion_tokens"]},
        "events": {"in": ev_tok["input_tokens"], "out": ev_tok["output_tokens"]},
    }
    m_p = run_dir / "metrics.json"
    if not m_p.exists():
        err.append("missing metrics.json")
    else:
        try:
            cost = (json.loads(m_p.read_text()) or {}).get("cost") or {}
        except (OSError, json.JSONDecodeError):
            cost = {}
            err.append("unreadable metrics.json")
        rec["tokens"]["metrics"] = {"in": int(cost.get("input_tokens") or 0),
                                    "out": int(cost.get("output_tokens") or 0)}
        rec["usd"] = cost.get("usd")
    if events_p.exists() and llm_spans:
        for side, a, b in (("in", "prompt_tokens", "input_tokens"),
                           ("out", "completion_tokens", "output_tokens")):
            if span_tok[a] != ev_tok[b]:
                err.append(f"token mismatch {side}: spans={span_tok[a]} "
                           f"events={ev_tok[b]}")
        mt = rec["tokens"].get("metrics") or {}
        if mt and (mt["in"], mt["out"]) != (span_tok["prompt_tokens"],
                                            span_tok["completion_tokens"]):
            err.append(f"metrics.json tokens {mt} != spans "
                       f"{rec['tokens']['spans']}")
    return rec


def verify_arm(arm_dir: Path) -> list[dict]:
    """Every run under `<arm_dir>/runs/<stem>/run-*`, one record each."""
    out = []
    runs_root = arm_dir / "runs"
    if not runs_root.exists():
        return [{"run_dir": str(runs_root), "errors": ["no runs/ dir — the arm "
                                                       "was generated without a "
                                                       "private RUN_ROOT"]}]
    for stem_dir in sorted(runs_root.iterdir()):
        if not stem_dir.is_dir():
            continue
        run_dirs = sorted(stem_dir.glob("run-*"))
        if not run_dirs:
            out.append({"run_dir": str(stem_dir), "stem": stem_dir.name,
                        "errors": ["no run-* dir"]})
            continue
        for rd in run_dirs:
            rec = verify_run(rd)
            rec["stem"] = stem_dir.name
            out.append(rec)
    return out


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out_json = None
    if "--json" in sys.argv:
        out_json = Path(sys.argv[sys.argv.index("--json") + 1])
        args = [a for a in args if a != str(out_json)]
    inventory: dict = {"arms": {}}
    bad = 0
    for arm in args:
        arm_dir = Path(arm)
        recs = verify_arm(arm_dir)
        inventory["arms"][arm_dir.name] = recs
        n_bad = sum(1 for r in recs if r["errors"])
        bad += n_bad
        tok_in = sum((r.get("tokens", {}).get("spans", {}) or {}).get("in", 0)
                     for r in recs)
        tok_out = sum((r.get("tokens", {}).get("spans", {}) or {}).get("out", 0)
                      for r in recs)
        ev_bytes = sum((r.get("bytes", {}) or {}).get("events.jsonl", 0)
                       for r in recs)
        print(f"[{arm_dir.name}] runs={len(recs)} incomplete={n_bad} "
              f"llm_calls={sum(r.get('llm_spans', 0) for r in recs)} "
              f"tokens_in={tok_in:,} tokens_out={tok_out:,} "
              f"events={ev_bytes / 1e6:.1f}MB")
        for r in recs:
            for e in r["errors"]:
                print(f"  INCOMPLETE {r.get('stem', '?')} "
                      f"{Path(r['run_dir']).name}: {e}")
    if out_json:
        out_json.write_text(json.dumps(inventory, indent=1))
        print(f"inventory -> {out_json}")
    print("ALL TRACES COMPLETE" if not bad else f"{bad} incomplete run(s)")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
