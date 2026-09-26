#!/usr/bin/env python3
"""Prove that pinned historical bases reproduce every frozen review diff."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
HUNK = re.compile(r"^(@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@).*$")


def normalized(diff: str) -> str:
    """Ignore Git object IDs and optional hunk function names only."""
    lines = []
    for line in diff.splitlines():
        if line.startswith("index "):
            continue
        match = HUNK.fullmatch(line)
        lines.append(match.group(1) if match else line)
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    if not (repo / ".git").exists():
        parser.error("--repo must be a local vllm-omni Git checkout")
    heads = json.loads((HERE / "goal-eval/expected_pr_heads.json").read_text())
    bases = json.loads((HERE / "goal-eval/expected_pr_bases.json").read_text())
    if len(bases) != 15:
        parser.error("expected exactly 15 train+val historical base pins")
    for pr, base in sorted(bases.items(), key=lambda pair: int(pair[0])):
        head = heads[pr]
        actual = subprocess.run(
            ["git", "-C", str(repo), "diff", "--no-ext-diff", "--binary",
             "--no-color", f"{base}..{head}"],
            capture_output=True, text=True, check=True,
        ).stdout
        expected = (HERE / "gt" / f"pr{pr}.diff").read_text()
        if normalized(actual) != normalized(expected):
            raise SystemExit(f"pr{pr}: pinned base/head diff differs from frozen GT")
        print(f"pr{pr}: frozen diff verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
