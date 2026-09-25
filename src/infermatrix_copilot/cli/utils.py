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


from ..metrics import format_metrics_line
