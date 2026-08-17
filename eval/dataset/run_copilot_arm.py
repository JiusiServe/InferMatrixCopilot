#!/usr/bin/env python3
"""Run the copilot arm (the real infermatrix-copilot product CLI) over dataset items.

Unlike the in-process copilot_v2 arm of eval/run_eval.py, this drives the full
shipped pipeline end-to-end: LLM intent parse -> planner (vetted playbook) ->
executor (pr-review@4 with the 4-lens ensemble / issue-answer with gated post
off) -> RUN_REPORT.md. LLM per .env (DeepSeek-routed); ALLOW_POST/ALLOW_PUSH
stay off, so nothing touches the live repo.

Usage: run_copilot_arm.py [splits] [only_stem]
  splits: comma list, default "val,train" (test is frozen — untouched by default)
  only_stem: e.g. pr4816 to run a single item

Outputs (resumable — existing non-empty .md files are skipped):
  eval/dataset/arms/copilot_v2/{pr|issue}<N>.md        (RUN_REPORT.md)
  eval/dataset/arms/copilot_v2/{pr|issue}<N>.cost.json (metrics.json + trace tokens)
"""
from __future__ import annotations

import gzip
import json
import subprocess
import uuid
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# infermatrix-copilot names run dirs run-<YYYYmmdd-HHMMSS>: two runs whose STARTUP
# reaches run-dir naming in the same second COLLIDE and overwrite each other's
# artifacts (observed live twice: pr4810+pr4893, then issue4827+issue4793 even
# with staggered Popen — import latency varies). Bulletproof fix: every
# invocation gets its own private RUN_ROOT (env-overridable Settings field),
# so collisions are structurally impossible. A small start stagger remains to
# avoid thundering-herd startup.
_START_LOCK = threading.Lock()
_last_start = [0.0]

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trace_pack  # noqa: E402

HERE = Path(__file__).parent
DATASET = HERE / "vllm_omni_dataset.yaml"
# ARM_OUT selects the arm directory (default T0). For the post-learning T1 pass:
#   ARM_OUT=copilot_v2_t1 run_copilot_arm.py val
import os as _os
import shutil as _shutil

OUT = HERE / "arms" / _os.environ.get("ARM_OUT", "copilot_v2")
RUN_ROOT = Path.home() / ".infermatrix-copilot" / "runs"
CLI = _os.environ.get("OMNI_CLI") or _shutil.which("infermatrix-copilot") or "infermatrix-copilot"
CWD = HERE.parent.parent  # repo root, where .env lives
SPLIT_ORDER = {"val": 0, "train": 1, "test": 2, "holdout": 3, "holdout3": 4,
               "holdout4": 5, "holdout5": 6}


def _find_run_dir(private_root: Path, kind: str, n: int) -> Path | None:
    """The newest run dir under this item's PRIVATE run root (spec verified)."""
    best = None
    for d in private_root.glob("run-*"):
        try:
            task = json.loads((d / "task.json").read_text())
        except Exception:
            continue
        spec = task.get("spec") or task  # task.json nests the TaskSpec under "spec"
        key = "pr" if kind == "pr_review" else "issue"
        if spec.get(key) == n and spec.get("kind") == kind:
            if best is None or d.stat().st_mtime > best.stat().st_mtime:
                best = d
    return best


def _trace_tokens(run_dir: Path) -> dict:
    """Canonical span-based cost for one run dir (W7 — replaces the old
    event-key readout whose keys never existed, so it always reported 0)."""
    import sys

    sys.path.insert(0, str(CWD / "src"))
    from infermatrix_copilot.metrics import cost_from_spans

    span = cost_from_spans(run_dir / "trace.jsonl")
    if span is None:
        return {"llm_calls": 0, "input_tokens": 0, "output_tokens": 0,
                "usd": 0.0, "source": "no-trace"}
    return {"llm_calls": span["llm_calls"], "input_tokens": span["input_tokens"],
            "output_tokens": span["output_tokens"], "usd": span["usd"],
            "source": "spans"}


def _attempt_records(private_root: Path, inv_ids: list[str]) -> list[dict]:
    """EVERY attempted cost artifact for this item (design W7): each attempt's
    invocation record (pre-run spend — clarify/blocked attempts included) plus
    the span cost of every run dir it produced. Pareto/cost gates must sum
    these, not just the newest run."""
    out: list[dict] = []
    inv_dir = Path.home() / ".infermatrix-copilot" / "invocations"
    for iid in inv_ids:
        rec_path = inv_dir / f"{iid}.json"
        rec = {}
        try:
            rec = json.loads(rec_path.read_text())
        except Exception:
            rec = {"invocation_id": iid, "outcome": "missing-record"}
        out.append(rec)
    for d in sorted(private_root.glob("run-*")):
        out.append({"run_dir": d.name, **_trace_tokens(d)})
    return out


def one(kind: str, n: int, split: str) -> str:
    stem = ("pr" if kind == "pr_review" else "issue") + str(n)
    md, cj = OUT / f"{stem}.md", OUT / f"{stem}.cost.json"
    if md.exists() and md.stat().st_size > 50:
        return f"skip {stem} (done)"
    # "do not post" pins post=false at intent parse (the LLM parser once
    # hallucinated post=true); ALLOW_POST=0 already dry-runs posting regardless.
    prompt = (f"review pr {n}, do not post" if kind == "pr_review"
              else f"answer issue {n}, do not post")
    import os

    private_root = OUT / "runs" / stem
    private_root.mkdir(parents=True, exist_ok=True)
    # eval-leakage policy (design W1): the frozen PR ground truth IS the human
    # review discussion — arm runs must never see it
    env = dict(os.environ, RUN_ROOT=str(private_root),
               PR_CONTEXT_MODE="no_discussion")
    t0 = time.time()
    blocked_retries = 0
    inv_ids: list[str] = []
    for attempt in range(4):
        # unique invocation id per attempt: correlates each paid attempt
        # (incl. clarify retries that create NO run dir) under concurrency
        inv_id = f"inv-{uuid.uuid4().hex[:8]}"
        inv_ids.append(inv_id)
        env["OMNI_INVOCATION_ID"] = inv_id
        with _START_LOCK:
            gap = time.time() - _last_start[0]
            if gap < 0.5:
                time.sleep(0.5 - gap)
            _last_start[0] = time.time()
        # harness-backend runs chain many vendor-CLI sessions per item and can
        # legitimately exceed the api-backend default — ARM_TIMEOUT_S raises it
        proc = subprocess.run([CLI, "-p", prompt, "--yes"], capture_output=True,
                              text=True,
                              timeout=int(os.environ.get("ARM_TIMEOUT_S", "3000")),
                              cwd=str(CWD), env=env)
        # the LLM-only intent parser occasionally returns a clarify instead of
        # a TaskSpec ("I couldn't parse that") — nondeterministic; retry.
        if "couldn't parse" in proc.stdout:
            print(f"[copilot-arm] retry {stem} (intent clarify, "
                  f"attempt {attempt + 1})", flush=True)
            continue
        # rc=3 (blocked/escalated) is usually a bad roll (T3: $0.017/attempt,
        # the same item answered fine in a sibling replicate) — one retry.
        if proc.returncode == 3 and blocked_retries < 1:
            blocked_retries += 1
            print(f"[copilot-arm] retry {stem} (blocked rc=3)", flush=True)
            continue
        break
    wall = round(time.time() - t0, 1)
    run_dir = _find_run_dir(private_root, kind, n)
    report = ""
    if run_dir and (run_dir / "RUN_REPORT.md").exists():
        report = (run_dir / "RUN_REPORT.md").read_text()
    if not report.strip():
        # fall back to CLI stdout so failures stay diagnosable
        report = (f"(no RUN_REPORT.md — rc={proc.returncode})\n\n"
                  f"## stdout\n{proc.stdout[-8000:]}\n\n## stderr\n{proc.stderr[-4000:]}")
    attempts = _attempt_records(private_root, inv_ids)
    cost = {"wall_s": wall, "split": split, "rc": proc.returncode,
            "run_dir": str(run_dir) if run_dir else None,
            "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "attempts": attempts,
            "attempt_usd_total": round(sum(
                (a.get("usd") or (a.get("pre_run") or {}).get("usd") or 0.0)
                for a in attempts), 6)}
    if run_dir:
        cost.update(_trace_tokens(run_dir))
        mfile = run_dir / "metrics.json"
        if mfile.exists():
            try:
                cost["metrics"] = json.loads(mfile.read_text())
            except Exception:
                pass
    # Pack the run directory into the committed trace BEFORE the resume key is written.
    # `runs/` is gitignored and has historically lived on machines that no longer exist
    # (the wave-1 arm's run_dir points at a vanished /rebase path), so the packed trace
    # is the only durable record of how Strict actually reviewed anything. `md` is the
    # resume predicate and is therefore written LAST: a crash mid-write leaves the item
    # looking unfinished and it re-runs, instead of being accepted with no trace.
    trace_note = {}
    try:
        packed = trace_pack.pack_copilot_item(OUT, stem, private_root, {
            "arm": OUT.name, "stem": stem, "split": split, "backfilled": False,
            "rc": proc.returncode, "recorded_at": cost["recorded_at"],
        })
        trace_note = {"trace": packed.name,
                      "trace_bytes": packed.stat().st_size}
    except Exception as exc:  # noqa: BLE001 — recorded, never fatal to a paid item
        trace_note = {"trace": None, "trace_error": repr(exc)[:300]}
    cost.update(trace_note)
    cj.write_text(json.dumps(cost, indent=2))
    md.write_text(report, encoding="utf-8")
    status = "done" if run_dir and proc.returncode == 0 else "DONE-WITH-ISSUES"
    return (f"{status} {stem} [{split}] {wall}s rc={proc.returncode} "
            f"tok_out={cost.get('output_tokens', '?')}")


def main() -> None:
    d = yaml.safe_load(DATASET.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    want = (sys.argv[1] if len(sys.argv) > 1 else "val,train").split(",")
    only = sys.argv[2] if len(sys.argv) > 2 else ""
    # KINDS restricts the sweep to one task kind (e.g. the 20-case PR-review
    # campaign: KINDS=pr_review with splits train,val,test). Default = both,
    # so existing invocations are unchanged.
    kinds = [k for k in (_os.environ.get("KINDS") or
                         "pr_review,issue_answer").split(",") if k]
    items = ([("pr_review", i["pr"], i["split"]) for i in d["pr_review"]]
             + [("pr_review", i["pr"], i["split"])
                for i in (d.get("pr_review_wave2") or [])]
             + [("pr_review", i["pr"], i["split"])
                for i in (d.get("pr_review_wave3") or [])]
             + [("pr_review", i["pr"], i["split"])
                for i in (d.get("pr_review_wave4") or [])]
             + [("pr_review", i["pr"], i["split"])
                for i in (d.get("pr_review_wave5") or [])]
             + [("issue_answer", i["issue"], i["split"]) for i in d["issue_answer"]])
    items = [t for t in items if t[2] in want and t[0] in kinds]
    if only:
        items = [t for t in items
                 if ("pr" if t[0] == "pr_review" else "issue") + str(t[1]) == only]
    items.sort(key=lambda t: SPLIT_ORDER[t[2]])
    (OUT / "manifest.json").write_text(json.dumps({
        "arm": OUT.name, "engine": "infermatrix-copilot CLI (shipped pipeline, "
        "pr-review@6 adaptive-depth ensemble; issue-answer dry-run)",
        "llm": "per .env (DeepSeek-routed)", "dataset": DATASET.name,
        "splits": want, "kinds": kinds, "n_items": len(items),
        "trace": {k: _os.environ.get(k, "(default)") for k in
                  ("AGENT_TRACE", "AGENT_TRACE_IO", "AGENT_TRACE_IO_FULL")},
        "moa_when": _os.environ.get("MOA_WHEN", "(default)"),
        "pr_context_mode": _os.environ.get("PR_CONTEXT_MODE", "(default)"),
        # RESOLVED settings, not the env strings above. On 2026-08-17 this
        # manifest recorded moa_when "(default)" while the resolved value was
        # "full", and a whole 15-item probe ran as a three-vendor mixture
        # unnoticed. Provenance that records the INPUT cannot detect a default
        # that changed underneath it.
        "resolved": _resolved_settings(),
    }, indent=2))
    print(f"[copilot-arm] {len(items)} items -> {OUT}", flush=True)
    for gap in _preflight_gaps():
        print(f"[copilot-arm] PREFLIGHT: {gap}", flush=True)
        return 2
    # ARM_JOBS: item-level concurrency. Historical default 2 predates knowing
    # the endpoint's real limits (deepseek-v4-pro allows 500 concurrent
    # requests; one item peaks at ~15 in-flight calls) — a full split can run
    # wide. Item starts are already staggered; RUN_ROOT is private per item.
    with ThreadPoolExecutor(
            max_workers=int(_os.environ.get("ARM_JOBS", "2"))) as ex:
        futs = {ex.submit(one, *t): t for t in items}
        for f in as_completed(futs):
            try:
                print(f"[copilot-arm] {f.result()}", flush=True)
            except Exception as e:  # noqa: BLE001 — keep the sweep going
                print(f"[copilot-arm] FAIL {futs[f]}: {e}", flush=True)
    # Trace gate: an arm that cannot be explained later is not a finished arm. This is
    # the arm the gate exists for — wave 1's Strict traces were lost silently and its
    # coverage shortfall is now permanently unexplainable.
    problems, checked = trace_pack.verify_arm(OUT)
    print(f"[copilot-arm] trace gate: {checked} packed trace(s) verified", flush=True)
    for p in problems:
        print(f"[copilot-arm]   {p}", flush=True)
    routing_problems = _verify_routed_seats(OUT)
    for p in routing_problems:
        print(f"[copilot-arm]   {p}", flush=True)
    print("[copilot-arm] sweep complete", flush=True)
    return 1 if (problems or routing_problems) else 0


def _resolved_settings() -> dict:
    """The settings that will actually govern this sweep, resolved.

    Env-string provenance is not provenance: `MOA_WHEN` unset reads as
    "(default)" in a manifest while resolving to "full" in the code, which is
    how a DeepSeek-only arm silently became a mimo/qwen mixture on 12 of 15
    items (2026-08-17). Recording the resolved values makes the same mistake
    visible in the artifact rather than three hours later in a trace scan.
    """
    try:
        import sys as _sys

        _sys.path.insert(0, str(CWD / "src"))
        from infermatrix_copilot.config import Settings

        s = Settings()
        members = [m.get("model") for m in
                   ((s.llm_mixture or {}).get("members") or [])
                   if isinstance(m, dict)]
        return {
            "moa_when": s.moa_when,
            "moa_eligible_full_depth_pr": s.moa_when in ("always", "full"),
            "llm_mixture_members": members,
            "strict_backend": s.strict_backend or "api",
            "strict_backend_model": s.strict_backend_model,
            "review_lens_backends": dict(s.review_lens_backends or {}),
            "agent_model": s.agent_model,
            "review_planner_model": getattr(s, "review_planner_model", ""),
            "review_promotion_model": getattr(s, "review_promotion_model", ""),
        }
    except Exception as exc:  # noqa: BLE001 — provenance must never block a run
        return {"error": f"could not resolve settings: {type(exc).__name__}: {exc}"}


def _preflight_gaps() -> list[str]:
    """Refuse to start a sweep that is already known to fail.

    Two 402 Insufficient Balance events in three days (2026-08-15 wave-4
    replicate 2, 2026-08-17 v17ds) each converted an empty account into
    contaminated artifacts: rc=3 stubs that the pipeline judged as zeros and
    that had to be found and quarantined afterwards. A refusal to start is
    strictly cheaper than that cleanup.
    """
    gaps: list[str] = []
    key = ""
    for line in (CWD / ".env").read_text(errors="ignore").splitlines() \
            if (CWD / ".env").is_file() else []:
        if line.startswith("ANTHROPIC_API_KEY="):
            key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        return gaps  # nothing to check against; let the run surface it
    try:
        import urllib.request

        req = urllib.request.Request(
            "https://api.deepseek.com/user/balance",
            headers={"Authorization": f"Bearer {key}"})
        data = json.loads(urllib.request.urlopen(req, timeout=20).read())
    except Exception:  # noqa: BLE001 — a probe outage must not block a sweep
        return gaps
    if not data.get("is_available", True):
        gaps.append("DeepSeek account reports is_available=false — top up "
                    "before spending a sweep (this is the failure that "
                    "produced rc=3 stubs twice)")
    for info in data.get("balance_infos") or []:
        if info.get("currency") == "CNY":
            try:
                if float(info.get("total_balance", 0)) < 20:
                    gaps.append(
                        f"DeepSeek balance is only {info['total_balance']} CNY "
                        "— a full split costs ~10-15 CNY per 10 items; refusing "
                        "to start a sweep that may die halfway")
            except (TypeError, ValueError):
                pass
    return gaps


def _verify_no_unintended_mixture(out_dir: Path) -> list[str]:
    """Report any MoA member that actually served a lens.

    The routed-seat gate below only inspects `REVIEW_LENS_BACKENDS`, so the
    mixture-of-agents path walked straight past it: on 2026-08-17 an arm
    labelled DeepSeek-only dispatched round-1 lenses to mimo-v2.5 and
    qwen3.6-plus on 12 of 15 items, and nothing in the sweep noticed. An arm
    that ran a vendor its label does not name is not the arm it claims to be,
    whatever the deltas say.

    Reports rather than fails: a deliberate MoA arm is legitimate, it just
    has to be visible in the sweep output instead of discoverable only by
    grepping traces afterwards.
    """
    out: list[str] = []
    for gz in sorted(out_dir.glob("pr*.trace.json.gz")):
        stem = gz.name.split(".")[0]
        try:
            packed = json.loads(gzip.open(gz).read())
            events = [e for run in packed["streams"]["runs"]
                      for e in (run.get("run_trace") or [])]
        except Exception:  # noqa: BLE001 — the trace gate reports unreadables
            continue
        members = sorted({str(e.get("model")) for e in events
                          if e.get("kind") == "agent_dispatch" and e.get("model")
                          and str(e.get("model")) != _os.environ.get(
                              "STRICT_BACKEND_MODEL", "")})
        dispatched = [e for e in events if e.get("kind") == "moa_dispatch"]
        if dispatched:
            out.append(
                f"MIXTURE GATE: {stem}: MoA dispatched (MOA_WHEN resolves to "
                f"{_resolved_settings().get('moa_when')!r}) — models seen: "
                f"{', '.join(members) or 'none recorded'}. If this arm is "
                f"labelled single-model, it is mislabelled.")
    return out


def _verify_routed_seats(out_dir: Path) -> list[str]:
    """Assert that every seat REVIEW_LENS_BACKENDS routed actually produced
    work, on every item.

    Measured 2026-08-16: a Fable-5 quota exhaustion made each routed session
    fail at the transport and return a contract-shaped `status: blocked` with
    zero tokens; the ensemble's zero-yield retry then re-ran the seat on the
    default backend. The sweep reported success on all 10 items, and an arm
    whose whole identity was "Fable in two seats" was measured — and briefly
    reported — with the Fable seats mostly absent. A label this load-bearing
    has to be checked, not trusted."""
    problems = _verify_no_unintended_mixture(out_dir)
    routed = _os.environ.get("REVIEW_LENS_BACKENDS") or ""
    if not routed.strip():
        return problems
    try:
        seats = sorted(json.loads(routed))
    except ValueError as exc:
        return [f"ROUTING GATE: REVIEW_LENS_BACKENDS is not valid JSON: {exc}"]
    for gz in sorted(out_dir.glob("pr*.trace.json.gz")):
        stem = gz.name.split(".")[0]
        try:
            packed = json.loads(gzip.open(gz).read())
            events = [e for run in packed["streams"]["runs"]
                      for e in (run.get("run_trace") or [])]
        except Exception as exc:  # noqa: BLE001
            problems.append(f"ROUTING GATE: {stem}: unreadable trace ({exc})")
            continue
        for seat in seats:
            work = [e for e in events
                    if e.get("kind") == "agent_output"
                    and str(e.get("step", "")).endswith(f"#{seat}")
                    and (e.get("tool_calls") or e.get("output_tokens"))]
            if not work:
                problems.append(
                    f"ROUTING GATE: {stem}: routed seat '{seat}' produced no "
                    f"work — the arm did NOT run the configuration it is "
                    f"labelled with (check the backend's quota/auth)")
    return problems


if __name__ == "__main__":
    raise SystemExit(main())
