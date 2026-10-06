#!/usr/bin/env python3
"""Compatibility CLI for the packaged native depth approval auditor."""
from pathlib import Path
import sys
from infermatrix_copilot.kb_service import native_depth_audit as _implementation

globals().update({key: value for key, value in vars(_implementation).items()
                  if not key.startswith("__")})

if __name__ == "__main__":
    arguments = sys.argv[1:]
    if "--root" not in arguments:
        arguments = ["--root", str(Path(__file__).resolve().parents[1]), *arguments]
    raise SystemExit(_implementation.main(arguments))
