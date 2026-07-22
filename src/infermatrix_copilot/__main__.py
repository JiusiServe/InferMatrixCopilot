"""`python -m infermatrix_copilot` entry.

Used by the MCP server (mcp_server.py) to launch a reserved run in a fresh
subprocess via the current interpreter — `sys.executable -m infermatrix_copilot
--execute-reserved <run_id>` — so the child is isolated (its stdout goes to the
run's console.log, and the process-global tracer / last_run_dir are per-run).
"""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
