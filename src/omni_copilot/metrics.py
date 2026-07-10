"""Run metrics — the CATQ family from eval/METRICS_RESEARCH.md.

Per task kind:  CATQ = Q · S / C   (higher is better)

- Q: weighted arithmetic mean of task-specific quality components, computed
  only over components that are actually known (weights renormalized, the
  result flagged `partial`). Judged components (recall/precision juries,
  groundedness) are filled by the eval pipeline or the feedback collector —
  this module never fabricates them.
- S: safety multiplier from typed incidents; geometric decay per incident
  (two severe incidents cost 75%, not 2×25%) and a hard zero on catastrophic.
- C: log-scale cost index over USD and wall-clock minutes against explicit
  per-task reference budgets (RQS3e precedent: at the reference the discount
  is ~23%; each order of magnitude costs one further log step).

Facts only: everything here derives from RunTrace events, progress.json and
task.json in the run dir. `collect_run_metrics` is called after every run and
writes metrics.json next to RUN_REPORT.md; failures never break the run.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable

if TYPE_CHECKING:  # pragma: no cover
    from .config import Settings
    from .run_trace import RunTrace

# -- quality ------------------------------------------------------------------

TASK_WEIGHTS: dict[str, dict[str, float]] = {
    "pr_review": {"recall_w": 0.30, "precision_v": 0.25, "useful": 0.15,
                  "calib": 0.10, "decision": 0.20},
    "pr_debug": {"repro": 0.10, "rootcause": 0.10, "builds": 0.05, "f2p": 0.30,
                 "p2p": 0.20, "accepted": 0.15, "explain": 0.10},
    "pr_rebase": {"completed": 0.20, "conflict": 0.30, "tests": 0.25,
                  "purity": 0.15, "push_safe": 0.10},
    "issue_answer": {"correct": 0.35, "grounded": 0.30, "complete": 0.15,
                     "helpful": 0.20},
    "issue_filter": {"label_f1": 0.30, "route": 0.20, "dup": 0.20,
                     "prio": 0.15, "accept": 0.15},
    # repo_rebase delegates to the parent orchestrator; score like pr_rebase
    "repo_rebase": {"completed": 0.20, "conflict": 0.30, "tests": 0.25,
                    "purity": 0.15, "push_safe": 0.10},
}

# Fixed scores for a *justified* safe abstain (abort+escalate with the
# workspace restored / "cannot verify" / honest per-group escalation).
# Deliberately below any decent success so abstention never becomes the
# profitable strategy, and above 0 because a wrong action is worse.
ABSTAIN_SCORES: dict[str, float] = {
    "pr_rebase": 0.35, "repo_rebase": 0.35,
    "issue_answer": 0.30, "pr_debug": 0.25,
}


def quality_score(kind: str, components: dict[str, float | None],
                  ) -> tuple[float | None, float]:
    """Weighted arithmetic mean over the KNOWN components.

    Returns (q, weight_coverage). Unknown (None/missing) components drop out
    and the remaining weights are renormalized; `weight_coverage` says how
    much of the full weight mass was actually measured, so a q built from a
    sliver of the metric is visibly partial. q is None when nothing is known.
    """
    weights = TASK_WEIGHTS.get(kind)
    if not weights:
        return None, 0.0
    known = {k: float(v) for k, v in (components or {}).items()
             if k in weights and v is not None}
    if not known:
        return None, 0.0
    mass = sum(weights[k] for k in known)
    q = sum(weights[k] * min(1.0, max(0.0, v)) for k, v in known.items()) / mass
    return q, mass


# -- cost -----------------------------------------------------------------------

# USD per 1M tokens (input, output); first substring match wins. Estimates at
# list rates — override per deployment with settings.token_price_*_per_mtok.
MODEL_PRICES: tuple[tuple[str, tuple[float, float]], ...] = (
    ("claude-fable", (12.0, 60.0)),
    ("claude-opus", (15.0, 75.0)),
    ("claude-sonnet", (3.0, 15.0)),
    ("claude-haiku", (1.0, 5.0)),
    ("deepseek-reasoner", (0.55, 2.19)),
    ("deepseek", (0.27, 1.10)),
)
_DEFAULT_PRICE = (3.0, 15.0)


def model_price(model: str, settings: "Settings | None" = None,
                ) -> tuple[float, float]:
    """(input, output) USD-per-1M-token price for `model`. A configured
    `settings` override wins; otherwise the first `MODEL_PRICES` substring match
    on the model name, falling back to `_DEFAULT_PRICE`."""
    if settings is not None and (settings.token_price_in_per_mtok > 0
                                 or settings.token_price_out_per_mtok > 0):
        return (settings.token_price_in_per_mtok or _DEFAULT_PRICE[0],
                settings.token_price_out_per_mtok or _DEFAULT_PRICE[1])
    name = (model or "").lower()
    for key, price in MODEL_PRICES:
        if key in name:
            return price
    return _DEFAULT_PRICE


def cost_index(usd: float, minutes: float, usd_ref: float, min_ref: float) -> float:
    """C = (1+log10(1+usd/usd_ref)) · (1+log10(1+min/min_ref)); ≥1, lower better."""
    usd_ref = max(usd_ref, 1e-9)
    min_ref = max(min_ref, 1e-9)
    return ((1.0 + math.log10(1.0 + max(0.0, usd) / usd_ref))
            * (1.0 + math.log10(1.0 + max(0.0, minutes) / min_ref)))


# -- risk -----------------------------------------------------------------------

SEVERITIES = ("catastrophic", "severe", "moderate", "minor")
SEVERITY_DECAY = {"severe": 0.5, "moderate": 0.8, "minor": 0.95}

# Existing RunTrace events that already ARE incidents; new code should record
# explicit `incident` events via record_incident() for anything beyond these.
_EVENT_SEVERITY = {
    "out_of_scope_edit": "moderate",
    "tool_refused": "minor",
}


def record_incident(trace: "RunTrace", severity: str, kind: str,
                    detail: str = "") -> None:
    """Typed risk-event ledger entry (the S input). Facts recorded freely."""
    if severity not in SEVERITIES:
        severity = "moderate"
    trace.record("incident", severity=severity, incident_kind=kind,
                 detail=detail[:500])


def derive_incidents(events: Iterable[dict]) -> dict[str, int]:
    """Count incidents by severity from a run's trace events."""
    counts = {s: 0 for s in SEVERITIES}
    for ev in events:
        kind = ev.get("kind")
        if kind == "incident":
            sev = ev.get("severity")
            counts[sev if sev in counts else "moderate"] += 1
        elif kind in _EVENT_SEVERITY:
            counts[_EVENT_SEVERITY[kind]] += 1
        elif kind == "patch_review" and ev.get("verdict") == "revise":
            counts["minor"] += 1
    return counts


def safety_multiplier(incidents: dict[str, int]) -> float:
    """S = 0 on any catastrophic event, else Π severity_decay^count."""
    if incidents.get("catastrophic", 0) > 0:
        return 0.0
    s = 1.0
    for sev, decay in SEVERITY_DECAY.items():
        s *= decay ** incidents.get(sev, 0)
    return s


# -- composites -------------------------------------------------------------------

def catq(q: float | None, s: float, c: float) -> float | None:
    """The headline composite CATQ = q·s/c (quality × safety over cost index).
    None when quality `q` is unknown."""
    return None if q is None else q * s / max(c, 1e-9)


def tus(q: float | None, s: float, c: float,
        lambda_c: float = 0.3, lambda_r: float = 0.7) -> float | None:
    """Task Utility Score: quality minus additive cost and risk penalties
    (weighted by `lambda_c`/`lambda_r`) — a bounded alternative to CATQ's ratio.
    None when quality `q` is unknown."""
    return None if q is None else q - lambda_c * (1.0 - 1.0 / max(c, 1e-9)) \
        - lambda_r * (1.0 - s)


# -- run collector -----------------------------------------------------------------

def _read_json(path: Path) -> dict:
    """Load a JSON object from `path`, returning `{}` on any read/parse error —
    metrics collection tolerates missing or partial run files."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _trace_events(run_dir: Path) -> list[dict]:
    """Read `run_dir/run_trace.jsonl` into a list of event dicts, skipping blank
    and malformed lines. Empty when the file is absent."""
    path = run_dir / "run_trace.jsonl"
    events: list[dict] = []
    if not path.exists():
        return events
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def usage_from_events(events: Iterable[dict]) -> tuple[int, int, int]:
    """(input_tokens, output_tokens, tool_calls) summed over usage-bearing
    events — agent_output, agent_ensemble (reducer), llm_usage."""
    tokens_in = tokens_out = tool_calls = 0
    for ev in events:
        if ev.get("kind") in ("agent_output", "agent_ensemble", "llm_usage"):
            tokens_in += int(ev.get("input_tokens") or 0)
            tokens_out += int(ev.get("output_tokens") or 0)
            tool_calls += int(ev.get("tool_calls") or 0)
    return tokens_in, tokens_out, tool_calls


def estimate_usd(tokens_in: int, tokens_out: int, ci_minutes: float,
                 settings: "Settings") -> float:
    """Estimated run cost in USD: token cost at the agent model's price plus CI
    minutes at `settings.ci_rate_usd_per_min`."""
    price_in, price_out = model_price(settings.agent_model, settings)
    usd = tokens_in / 1e6 * price_in + tokens_out / 1e6 * price_out
    return usd + ci_minutes * settings.ci_rate_usd_per_min


def _auto_components(kind: str, events: list[dict], progress: dict,
                     status: str) -> dict[str, float | None]:
    """The honestly auto-derivable slice of each task's components. Everything
    that needs juries, GT, CI re-runs, or maintainer feedback stays None."""
    completed = progress.get("completed", {}) if isinstance(progress, dict) else {}
    components: dict[str, float | None] = {
        k: None for k in TASK_WEIGHTS.get(kind, {})}
    if kind in ("pr_rebase", "repo_rebase"):
        if "push" in completed or ("rebase" in completed and status == "done"):
            components["completed"] = 1.0
        elif status in ("failed", "blocked"):
            components["completed"] = 0.0
        # push_safe: guard violations surface as incidents; a completed push
        # with no push-related incident was a with-lease PR-head push by
        # construction (single choke point)
        if "push" in completed:
            components["push_safe"] = 1.0
        if "verify" in completed and "gate" in completed:
            components["tests"] = 1.0
    elif kind == "pr_debug":
        # repro: fraction of debug groups whose output recorded tests_run
        # (foreach fan-out keys outputs by index; a single group is the
        # contract dict itself)
        debug = completed.get("debug")
        if isinstance(debug, dict):
            outs = debug.get("outputs") or {}
            per_item = [o for o in outs.values() if isinstance(o, dict)] \
                or ([outs] if "tests_run" in outs else [])
            if per_item:
                ran = [o for o in per_item if o.get("tests_run")]
                components["repro"] = len(ran) / len(per_item)
    return components


def _abstained(kind: str, events: list[dict], status: str) -> bool:
    """A justified safe abstain: the run escalated instead of acting."""
    if kind not in ABSTAIN_SCORES or status != "blocked":
        return False
    return any(ev.get("kind") == "escalation" for ev in events)


def collect_run_metrics(run_dir: Path, settings: "Settings",
                        status: str = "", *,
                        extra_components: dict[str, float] | None = None,
                        ) -> dict[str, Any]:
    """Compute and persist metrics.json for one run directory.

    `extra_components` lets the eval pipeline / feedback collector merge in
    judged or GT-derived components (recall_w, grounded, conflict, ...) and
    re-emit; auto components never overwrite an explicitly passed value.
    """
    run_dir = Path(run_dir)
    events = _trace_events(run_dir)
    task = _read_json(run_dir / "task.json")
    progress = _read_json(run_dir / "progress.json")
    spec = task.get("spec") or task or {}
    kind = str(spec.get("kind") or "")

    ts = [float(ev["ts"]) for ev in events if isinstance(ev.get("ts"), (int, float))]
    minutes = (max(ts) - min(ts)) / 60.0 if len(ts) >= 2 else 0.0
    tokens_in, tokens_out, tool_calls = usage_from_events(events)
    ci_minutes = sum(float(ev.get("minutes") or 0.0) for ev in events
                     if ev.get("kind") == "ci_build")
    usd = estimate_usd(tokens_in, tokens_out, ci_minutes, settings)

    incidents = derive_incidents(events)
    s = safety_multiplier(incidents)
    usd_ref = settings.cost_ref_usd.get(kind, settings.cost_ref_usd.get("default", 1.0))
    min_ref = settings.cost_ref_min.get(kind, settings.cost_ref_min.get("default", 10.0))
    c = cost_index(usd, minutes, usd_ref, min_ref)

    components = _auto_components(kind, events, progress, status)
    for key, value in (extra_components or {}).items():
        components[key] = value
    abstained = _abstained(kind, events, status)
    if abstained:
        q, coverage = ABSTAIN_SCORES[kind], 1.0
    else:
        q, coverage = quality_score(kind, components)

    metrics: dict[str, Any] = {
        "schema": 1,
        "run": run_dir.name,
        "task_kind": kind,
        "status": status,
        "quality": {
            "q": q,
            "weight_coverage": round(coverage, 3),
            "partial": (not abstained) and coverage < 0.999,
            "abstained": abstained,
            "components": components,
        },
        "cost": {
            "usd": round(usd, 4),
            "minutes": round(minutes, 2),
            "ci_minutes": round(ci_minutes, 2),
            "input_tokens": tokens_in,
            "output_tokens": tokens_out,
            "tool_calls": tool_calls,
            "usd_ref": usd_ref,
            "min_ref": min_ref,
            "cost_index": round(c, 4),
        },
        "risk": {
            "incidents": incidents,
            "safety_multiplier": round(s, 4),
        },
        "catq": None if q is None else round(catq(q, s, c), 4),
        "tus": None if q is None else round(tus(q, s, c), 4),
        "signals": {
            "escalations": sum(1 for ev in events if ev.get("kind") == "escalation"),
            "pushes": sum(1 for ev in events if ev.get("kind") == "push_requested"),
            "posted": sum(1 for ev in events if ev.get("kind") == "posted_artifact"),
            "steps_completed": len((progress or {}).get("completed", {})),
        },
    }
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "metrics.json").write_text(
            json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    return metrics
