#!/usr/bin/env python3
"""Exec a command with LLM_MIXTURE set to the goal's MoA trio.

Members: composer-2.5@cursor + cursor-grok-4.6-high@cursor (harness members,
provider registry) + mimo-v2.5 (raw API — endpoint+key carried over from the
repo .env's existing mixture entry). The composed JSON contains the MiMo key,
so it is exported into the child env only — never printed.

Usage: run_moa_mixture_env.py <command> [args...]
"""
from __future__ import annotations

import json
import os
import sys

from infermatrix_copilot.config import Settings


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    members = (Settings().llm_mixture or {}).get("members") or []
    mimo = next((m for m in members if "mimo" in str(m.get("model", ""))), None)
    if not mimo:
        print("no mimo member found in the repo .env LLM_MIXTURE", file=sys.stderr)
        return 1
    mixture = {"members": [
        {"model": "composer-2.5", "provider": "cursor"},
        {"model": "cursor-grok-4.6-high", "provider": "cursor"},
        mimo,
    ]}
    env = dict(os.environ, LLM_MIXTURE=json.dumps(mixture))
    os.execvpe(sys.argv[1], sys.argv[1:], env)


if __name__ == "__main__":
    raise SystemExit(main())
