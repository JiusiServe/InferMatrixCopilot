"""Pure CLI helpers: argument coercion and metrics-line formatting. No state,
no I/O — extracted from `Copilot._execute` and `main` so those carry flow, not
string/parse plumbing.
"""

from __future__ import annotations

from pathlib import Path


def parse_task_params(kvs: list[str]) -> dict:
    """`--task-param KEY=VALUE` pairs → a typed params dict (bool/int coercion)."""
    params: dict = {}
    for kv in kvs:
        key, _, raw = kv.partition("=")
        value: object = raw
        if raw.lower() in ("true", "false"):
            value = raw.lower() == "true"
        elif raw.isdigit():
            value = int(raw)
        params[key.strip()] = value
    return params


def format_metrics_line(m: dict, run_dir: Path) -> str:
    """One-line run-cost/quality summary from a collected metrics dict."""
    cost, risk, catq = m["cost"], m["risk"], m["catq"]
    catq_str = (f" CATQ={catq:.3f}" + ("*" if m["quality"]["partial"] else "")
                if catq is not None else "")
    return (f"  metrics: usd≈{cost['usd']:.2f} {cost['minutes']:.1f}min "
            f"S={risk['safety_multiplier']:.2f}{catq_str}"
            f"  ({run_dir / 'metrics.json'})")
