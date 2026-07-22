"""MCP stdio server — the copilot's read-only V1 surface for Claude Code / Codex.

Both hosts speak MCP, so this is the one portable boundary. Knowledge lookup is
synchronous through repo-scoped `doc_search` / `doc_read`. A review takes 5–12
min, which would blow a synchronous host-call timeout, so workflow tasks use a
**start + poll** pair: `start_*` reserves a run and returns a `run_id`
immediately; `get_result`/`get_status` poll it. The heavy workflow runs in an
**isolated subprocess** (`python -m infermatrix_copilot --execute-reserved <id>`), which
(a) keeps the copilot's stdout out of this process's JSON-RPC stdio channel —
child stdout goes to `<run_dir>/console.log` — and (b) makes the process-global
tracer / `last_run_dir` per-run.

Safety is structural, not host-trusted: `enforce_mcp_policy` runs here AND
(authoritatively) in the child, so only the three `READ_ONLY_KINDS` ever run,
`post` is always False, and only allow-listed repos are reachable — regardless of
what a tampered `request.json` claims. Runs are serialized through one worker
thread; the durable `run_status.json` + ownership-aware reconciliation
(run_status.py) make polling correct across restarts and multiple servers.

This module imports the optional `mcp` SDK; it is gated behind the `[mcp]` extra
and never imported by the core package.
"""

from __future__ import annotations

import json
import os
import queue
import signal
import subprocess
import sys
import threading
import uuid
from pathlib import Path
from typing import Any, Callable, Literal, Optional

from . import run_status as rs
from .config import Settings
from .knowledge_docs import KnowledgeDocs, KnowledgeDocsError
from .mcp_policy import PolicyError, enforce_mcp_policy
from .task_spec import READ_ONLY_KINDS


class CopilotMCP:
    """The server core: a serialized run queue over isolated subprocesses, plus
    ownership-aware reconciliation. Framework-agnostic (no `mcp` import) so it is
    unit-testable without a live protocol connection."""

    def __init__(self, settings: Optional[Settings] = None):
        """Wire settings + a `Copilot` (for `reserve_run`/`execute_reserved` path
        helpers), register this server's liveness token, reconcile any runs
        orphaned by a previous server, and start the single worker thread."""
        from .cli.copilot import Copilot

        self.settings = settings or Settings()
        self.copilot = Copilot(self.settings)
        self.run_root = Path(self.settings.run_root)
        self.run_root.mkdir(parents=True, exist_ok=True)
        self.server_id = uuid.uuid4().hex
        self.pid = os.getpid()
        rs.register_server(self.run_root, self.server_id, self.pid)
        rs.startup_reconcile(self.run_root)
        self._q: "queue.Queue[str]" = queue.Queue()
        self._worker = threading.Thread(target=self._worker_loop, daemon=True,
                                        name="omni-mcp-worker")
        self._worker.start()

    # -- worker: one run at a time, each an isolated subprocess ---------------
    def _worker_loop(self) -> None:
        """Drain the queue forever, launching one run subprocess at a time. A
        launch failure marks the run failed but never kills the worker."""
        while True:
            run_id = self._q.get()
            try:
                self._launch(run_id)
            except Exception as exc:  # noqa: BLE001 - worker must survive
                try:
                    rs.mark(self.run_root / run_id, rs.FAILED,
                            note=f"launch error: {type(exc).__name__}: {exc}")
                except Exception:
                    pass
            finally:
                self._q.task_done()

    def _launch(self, run_id: str) -> None:
        """Run one reserved run as `python -m infermatrix_copilot --execute-reserved
        <id>`, child stdout+stderr -> console.log, outward-write env forced off.
        After `.wait()` the child is reaped, so we reconcile as sole writer."""
        run_dir = self.run_root / run_id
        env = dict(os.environ)
        env["ALLOW_POST"] = "0"  # defense in depth; policy already forces post off
        env["ALLOW_PUSH"] = "0"
        # The Windows Store Python runtime otherwise inherits the machine's
        # legacy console code page (commonly GBK). Reports legitimately contain
        # Unicode markers such as ✓; force the isolated child's stdio to UTF-8
        # so rendering a completed report cannot fail after all work is done.
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        # The child builds its own Settings() from env/.env, so make THIS server's
        # effective config authoritative for it: the same run_root (to locate the
        # reserved dir) and the same read-only allowlist (its policy re-check).
        env["RUN_ROOT"] = str(self.run_root)
        env["MCP_REPO_ALLOWLIST"] = json.dumps(self.settings.mcp_allowed_repos)
        env["DEFAULT_REPO"] = self.settings.default_repo
        popen_kwargs: dict[str, Any] = {}
        if os.name == "nt":
            # Codex/Claude launch the MCP server over stdio.  Without a new
            # Windows process group, host or transport shutdown can propagate a
            # console control event into the long-running review child and turn
            # it into KeyboardInterrupt.  CREATE_NO_WINDOW also prevents a
            # console flash for every MCP run.
            popen_kwargs["creationflags"] = (
                subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
            )
        else:
            # Keep the durable child alive and independently reconcilable when
            # its stdio MCP parent is restarted.
            popen_kwargs["start_new_session"] = True
        with open(run_dir / "console.log", "ab") as log:
            proc = subprocess.Popen(
                [sys.executable, "-m", "infermatrix_copilot", "--execute-reserved", run_id],
                stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                cwd=str(self.run_root), env=env,
                **popen_kwargs,
            )
            proc.wait()
        rs.reconcile_after_wait(run_dir)

    # -- start (reserve + enqueue) -------------------------------------------
    def start(self, spec_dict: dict) -> str:
        """Boundary policy enforcement + reserve + enqueue; returns the run id."""
        spec = enforce_mcp_policy(spec_dict, allowed_repos=self.settings.mcp_allowed_repos, settings=self.settings)
        run_id = self.copilot.reserve_run(
            spec, owner_server_id=self.server_id, owner_server_pid=self.pid)
        self._q.put(run_id)
        return run_id

    # -- poll -----------------------------------------------------------------
    def get_status(self, run_id: str) -> dict:
        """Lazy-reconcile then return `run_status.json` + `progress.json` (when
        present — queued/planning runs have none)."""
        run_dir = self.copilot._contained_run_dir(run_id)
        rs.reconcile_if_dead(run_dir, self.run_root)
        status = rs.read_status(run_dir) or {}
        progress = None
        pf = run_dir / "progress.json"
        if pf.exists():
            try:
                progress = json.loads(pf.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                progress = None
        return {"run_id": run_id, "status": status, "progress": progress}

    def get_result(self, run_id: str, offset: int = 0) -> dict:
        """Lazy-reconcile then return the run state; once terminal, attach a
        size-capped page of the report (RUN_REPORT.md, or ESCALATION.md when
        blocked) with `next_offset` + `report_path` for paging — never an
        unbounded dump over the protocol."""
        run_dir = self.copilot._contained_run_dir(run_id)
        rs.reconcile_if_dead(run_dir, self.run_root)
        status = rs.read_status(run_dir) or {}
        state = status.get("state")
        out: dict[str, Any] = {"run_id": run_id, "state": state,
                               "note": status.get("note", "")}
        if state not in rs.TERMINAL:
            return out  # still queued/planning/running — poll again
        report_path = run_dir / "RUN_REPORT.md"
        if state == rs.BLOCKED and (run_dir / "ESCALATION.md").exists():
            report_path = run_dir / "ESCALATION.md"
        if report_path.exists():
            text = report_path.read_text(encoding="utf-8", errors="replace")
            offset = max(0, int(offset))
            cap = self.settings.mcp_report_max_bytes
            out["report"] = text[offset:offset + cap]
            out["report_path"] = str(report_path)
            nxt = offset + cap
            out["next_offset"] = nxt if nxt < len(text) else None
        else:
            out.update(report=None, report_path=None, next_offset=None)
        return out

    def list_playbooks(self) -> dict:
        """The read-only V1 surface: the exposed kinds and the vetted playbooks
        backing them (read-only introspection; no run started)."""
        pbs = [line for line in self.copilot.playbooks().splitlines()
               if any(k in line for k in READ_ONLY_KINDS)]
        return {"read_only_kinds": sorted(READ_ONLY_KINDS), "playbooks": pbs}

    def _docs(self, repo: str) -> KnowledgeDocs:
        """Build the same repo-scoped knowledge view used by workflow agents."""
        from .adapters.base import AdapterRegistry

        repo = repo or self.settings.default_repo
        if repo not in self.settings.mcp_allowed_repos:
            raise PolicyError(f"repo {repo!r} is not permitted")
        try:
            adapter = AdapterRegistry(self.settings.adapters_dir).resolve(
                name=repo.replace("-", "_"))
        except Exception as exc:
            raise PolicyError(f"no knowledge adapter for repo {repo!r}") from exc
        kn = adapter.manifest.get("knowledge") or {}
        return KnowledgeDocs(self.settings.knowledge_dir, kn.get("repo_subdir"))

    def doc_search(self, query: str, repo: str = "", limit: int = 40) -> dict:
        """Search general + the selected repo's curated Markdown knowledge."""
        selected = repo or self.settings.default_repo
        hits = self._docs(selected).search(query, limit=limit)
        return {"query": query, "repo": selected, "matches": hits,
                "truncated": len(hits) >= max(1, min(int(limit), 100))}

    def doc_read(self, path: str, repo: str = "", offset: int = 0) -> dict:
        """Read one document from general + the selected repo's slice."""
        selected = repo or self.settings.default_repo
        try:
            page = self._docs(selected).read(path, offset=offset)
        except FileNotFoundError as exc:
            raise KnowledgeDocsError(f"no such document: {path}") from exc
        return {"repo": selected, **page}

    def close(self) -> None:
        """Deregister this server's liveness token (best-effort, on shutdown)."""
        rs.unregister_server(self.run_root, self.server_id)


def _guard(fn: Callable[[], dict]) -> dict:
    """Run a tool body, converting a policy/validation refusal into a clean
    `{"error": …}` result rather than a protocol-level crash."""
    try:
        return fn()
    except (PolicyError, ValueError) as exc:
        return {"error": str(exc)}


def build_mcp(settings: Optional[Settings] = None):
    """Build the FastMCP server with the V1 read-only tools bound to a
    `CopilotMCP`. Importing FastMCP here keeps the `mcp` dependency out of the
    core import path (it lives behind the `[mcp]` extra)."""
    from mcp.server.fastmcp import FastMCP

    core = CopilotMCP(settings)
    mcp = FastMCP("infermatrix-copilot")

    @mcp.tool()
    def start_review(pr: int, repo: str = "", review_depth: str = "",
                     mode: Literal["eco", "performance"] = "eco") -> dict:
        """Start a read-only review of PR `pr` in eco or performance mode.
        Returns {run_id}; poll get_result. `review_depth` optionally pins the
        adaptive depth (light|standard|full|auto; policy-validated)."""
        req: dict = {"kind": "pr_review",
                     "repo": repo or core.settings.default_repo,
                     "pr": pr, "mode": mode}
        if review_depth:
            req["params"] = {"review_depth": review_depth}
        return _guard(lambda: {"run_id": core.start(req)})

    @mcp.tool()
    def start_issue_answer(issue: int, repo: str = "") -> dict:
        """Draft a read-only answer to issue `issue` (never posted). Returns
        {run_id}; poll get_result."""
        return _guard(lambda: {"run_id": core.start(
            {"kind": "issue_answer", "repo": repo or core.settings.default_repo, "issue": issue})})

    @mcp.tool()
    def start_issue_triage(repo: str = "") -> dict:
        """Start a read-only triage of recent open issues. Returns {run_id};
        poll get_result."""
        return _guard(lambda: {"run_id": core.start(
            {"kind": "issue_filter", "repo": repo or core.settings.default_repo})})

    @mcp.tool()
    def get_result(run_id: str, offset: int = 0) -> dict:
        """Poll a run: {state, report?, report_path?, next_offset?}. `report` is
        size-capped; page with `offset` = the prior `next_offset`."""
        return _guard(lambda: core.get_result(run_id, offset))

    @mcp.tool()
    def get_status(run_id: str) -> dict:
        """Poll a run's progress: {status, progress?} (progress absent until the
        run is executing)."""
        return _guard(lambda: core.get_status(run_id))

    @mcp.tool()
    def list_playbooks() -> dict:
        """List the read-only task kinds and the playbooks backing them."""
        return _guard(core.list_playbooks)

    @mcp.tool()
    def doc_search(query: str, repo: str = "", limit: int = 40) -> dict:
        """Search curated general and repo-specific knowledge without a workflow."""
        return _guard(lambda: core.doc_search(query, repo, limit))

    @mcp.tool()
    def doc_read(path: str, repo: str = "", offset: int = 0) -> dict:
        """Read a Markdown document returned by doc_search; results are paged."""
        return _guard(lambda: core.doc_read(path, repo, offset))

    return mcp


def main() -> int:
    """Console-script entry (`infermatrix-copilot-mcp`): serve over stdio."""
    if os.name == "nt":
        # Codex/terminal hosts can emit a console Ctrl+C event while keeping the
        # stdio transport open.  anyio turns that inherited event into
        # KeyboardInterrupt and tears down the MCP server mid-run.  Stdio EOF
        # remains the authoritative, portable shutdown signal.
        signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        mcp = build_mcp()
    except ImportError:
        sys.stderr.write(
            "infermatrix-copilot-mcp needs the MCP SDK. Install it with:\n"
            "    pip install 'infermatrix-copilot[mcp]'\n")
        return 1
    mcp.run()  # stdio transport by default
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
