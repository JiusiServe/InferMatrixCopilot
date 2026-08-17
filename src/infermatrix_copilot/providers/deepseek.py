"""DeepSeek Harness (`dsh`) transport — Strict on DeepSeek's own agent harness.

Driven through the published Python SDK (`pip install deepseek-harness-sdk`),
which is itself a subprocess SDK: it launches the bundled `dsh-jsonrpc-agent`
runtime and speaks JSON-RPC over stdio. The bundled wheel carries the runtime,
so the target machine needs no Node.js and there is no CLI on PATH — hence the
`cli_path` override below.

TWO WAYS THIS BREAKS THE REGISTRY'S HARNESS ASSUMPTIONS, both deliberate:

1. **It is API-keyed, not subscription-authed.** `base.py` states that harness
   providers "hold their subscription auth inside the vendor CLI's own state
   and this codebase never sees it", and `Settings.tier_target` returns an
   empty key for every harness for exactly that reason. dsh is the exception:
   it needs `DEEPSEEK_API_KEY`, so this transport resolves the credential the
   api path would use and hands it over `DeepSeekHarnessConfig.api_key`. For
   cursor/claude-code/codex, injecting a key would be a bug; here it is the
   only way the harness runs at all.
2. **The composition is ours, not the vendor's default.** `minimal.cordis.yml`
   upstream mounts no MCP client, so our scoped tools would be unreachable and
   the lenses would lose the archaeology tools (`show_commit`,
   `search_history`, `file_at_base`) that produced the campaign's largest
   single win. We therefore generate the composition per session: upstream
   minimal (no compaction, no runtime-context injection, no skills) PLUS one
   `dsh-mcp-client` layer pointed at our tool bridge.

Sandbox: upstream minimal ships `mode: danger-full-access` and its own README
says to run it "only against a disposable checkout or container". This machine
is shared — `/data/<name>/` belongs to different people and our `.env` holds
live credentials — so the generated composition pins the mode to the session's
own scope (`read-only` for reviews, `workspace-write` otherwise) with
`workspaceRoot` at the scope root. dsh's vocabulary is exactly
`read-only | workspace-write | danger-full-access`, and its own default is
`read-only`; we never emit the third.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

from ..agent_loop import AgentOutcome
from ..llm import Block, Reply
from .base import (
    AgentSessionRequest,
    HarnessTransport,
    SessionUsage,
    flatten_messages,
    sanitized_env,
)
from .registry import PROVIDERS

# Env the dsh runtime subprocess keeps, on top of `sanitized_env()`. The
# credential does NOT travel here — it goes through the SDK config field so it
# never lands in a subprocess environment we also hand to bash.
_DSH_ENV_KEEP = ("DSH_HOME",)


class DeepSeekHarnessTransport(HarnessTransport):
    """`dsh` (DeepSeek Harness) as a Strict backend, via its Python SDK."""

    spec = PROVIDERS["deepseek"]

    # -- availability --------------------------------------------------------
    def cli_path(self) -> str | None:
        """The bundled runtime, or None when the SDK is not installed.

        Overridden because dsh ships no PATH binary: the runtime executable
        lives inside the `deepseek-harness-runtime-bin` wheel that
        `deepseek-harness-sdk` pulls in. An explicit `STRICT_BACKEND_CLI`
        still wins, so a source build can be pointed at directly.
        """
        override = getattr(self.settings, "strict_backend_cli", "")
        if override:
            return override
        try:
            import deepseek_harness  # noqa: F401
        except ImportError:
            return None
        return sys.executable  # the SDK spawns its own runtime from here

    def require_cli(self) -> str:
        cli = self.cli_path()
        if not cli:
            raise RuntimeError(
                "deepseek backend selected but the SDK is not installed — "
                "run: pip install deepseek-harness-sdk (it carries the "
                "bundled runtime; no Node.js needed)")
        return cli

    def _credential(self) -> tuple[str, str]:
        """(api_key, base_url) for dsh. `tier_target` deliberately blanks
        credentials for harness backends, so resolve from the api-side
        settings the same key would serve — our `.env` holds the DeepSeek key
        under the Anthropic names because the api path talks to DeepSeek's
        Anthropic-compatible gateway. `base_url` stays empty unless explicitly
        set: dsh's own `llm-deepseek` plugin speaks to DeepSeek's native
        endpoint, which is NOT the `/anthropic` gateway URL.
        """
        key = (getattr(self.settings, "deepseek_harness_api_key", "")
               or getattr(self.settings, "anthropic_api_key", "")
               or getattr(self.settings, "openai_api_key", ""))
        return key, getattr(self.settings, "deepseek_harness_base_url", "")

    def auth_gap(self) -> str | None:
        if not self.cli_path():
            return None  # the SDK-missing gap is reported by require_cli
        key, _ = self._credential()
        if not key:
            return ("no DeepSeek credential for the dsh backend — set "
                    "DEEPSEEK_HARNESS_API_KEY (or ANTHROPIC_API_KEY, which "
                    "this machine points at DeepSeek) in "
                    "~/.infermatrix-copilot/.env")
        return None

    # -- composition ---------------------------------------------------------
    def _composition(self, *, run_dir: Path, step_name: str, cwd: Path,
                     read_only: bool, bridge_spec_path: Path | None) -> Path:
        """Write this session's Cordis composition and return its path.

        Upstream `minimal.cordis.yml` verbatim in shape — one system prompt,
        persistent bash + str_replace_editor, JSONL persistence, no
        compaction, no runtime-context injection, no skills — with two
        deliberate edits: the sandbox mode is pinned to the session's scope
        instead of `danger-full-access`, and an `dsh-mcp-client` layer mounts
        our tool bridge so scoped tools reach the model as
        `mcp__infermatrix__<name>`.
        """
        stem = re.sub(r"[^A-Za-z0-9._-]+", "_", step_name or "step") or "step"
        out_dir = Path(run_dir) / "dsh"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{stem}.cordis.yml"
        mode = "read-only" if read_only else "workspace-write"
        package_root = Path(__file__).resolve().parents[2]

        blocks = [
            # maxTokensAsSuccess:false — a turn that burns the completion
            # ceiling must surface as `max-tokens`, not as a quietly accepted
            # empty final. That silent-drop is a bug class this codebase has
            # already paid for once (ensemble.py zero-yield retry).
            "- id: sdk-jsonrpc-server\n"
            "  name: '@deepseek-ai/dsh-sdk-jsonrpc-server'\n"
            "  config:\n"
            "    maxTokensAsSuccess: false\n",
            "- id: llm-deepseek\n"
            "  name: '@deepseek-ai/dsh-llm-deepseek'\n"
            "  config:\n"
            "    apiKeyEnv: DEEPSEEK_API_KEY\n"
            "    streamIdleTimeoutMs: 172800000\n"
            "    models:\n"
            "      - id: !!js process.env.DSH_MODEL\n"
            "        contextWindow: !!js Number(process.env."
            "DSH_CONTEXT_WINDOW ?? 1000000)\n",
            "- id: sandbox\n  name: '@deepseek-ai/dsh-sandbox-local'\n",
            f"- id: sandbox-policy\n"
            f"  name: '@deepseek-ai/dsh-sandbox-policy'\n"
            f"  config:\n"
            f"    mode: {mode}\n"
            f"    workspaceRoot: {json.dumps(str(cwd))}\n",
            "- id: subprocess\n  name: '@deepseek-ai/dsh-subprocess-local'\n",
            "- id: pty\n  name: '@deepseek-ai/dsh-terminal'\n",
            "- id: terminal-bash\n"
            "  name: '@deepseek-ai/dsh-terminal-bash'\n"
            "  config:\n    timeoutMs: 300000\n",
            f"- id: fs-local\n"
            f"  name: '@deepseek-ai/dsh-fs-local'\n"
            f"  config:\n    cwd: {json.dumps(str(cwd))}\n",
            "- id: agent-spine\n"
            "  name: '@deepseek-ai/dsh-agent-spine-demo'\n"
            "  config:\n"
            "    includeHarnessIdentity: false\n"
            "    includeRuntimeContext: false\n"
            "    persona: !!js process.env.DSH_SYSTEM_PROMPT\n"
            "    workspaceContext: false\n"
            "    skills:\n      enabled: false\n"
            "    toolBash: false\n    toolJobs: false\n",
            "- id: persistent-bash\n"
            "  name: '@deepseek-ai/dsh-tool-bash-persistent'\n"
            "  config:\n    timeoutMs: 300000\n",
            "- id: str-replace-editor\n"
            "  name: '@deepseek-ai/dsh-tool-str-replace-editor'\n"
            "  config:\n    maxOutputChars: 16000\n",
            "- id: sessions\n"
            "  name: '@deepseek-ai/dsh-session-persistence-jsonl'\n"
            "  config:\n"
            "    root: !!js process.env.DSH_SESSION_ROOT\n"
            "    compression: none\n",
        ]
        if bridge_spec_path is not None:
            # failOnStartupError: a silently tool-less lens looks like a shy
            # model, not a broken bridge. The cursor backend learned this the
            # hard way (--approve-mcps missing ⇒ native tools only, unnoticed).
            blocks.append(
                "- id: mcp-infermatrix\n"
                "  name: '@deepseek-ai/dsh-mcp-client'\n"
                "  config:\n"
                "    serverName: infermatrix\n"
                "    transport: stdio\n"
                f"    command: {json.dumps(sys.executable)}\n"
                "    args: ['-m', 'infermatrix_copilot.tool_bridge', "
                f"'--spec', {json.dumps(str(bridge_spec_path))}]\n"
                f"    cwd: {json.dumps(str(cwd))}\n"
                "    env:\n"
                f"      PYTHONPATH: {json.dumps(str(package_root))}\n"
                "    failOnStartupError: true\n")
        header = ("# Generated per session by providers/deepseek.py — upstream\n"
                  "# minimal composition, sandbox pinned to this step's scope,\n"
                  "# plus the infermatrix tool bridge. Do not hand-edit.\n")
        path.write_text(header + "\n".join(blocks), encoding="utf-8")
        return path

    def _env(self, *, cwd: Path, model: str, system: str,
             session_root: Path) -> dict[str, str]:
        """Explicit environment for the runtime subprocess. Built from the
        allowlist, never `os.environ` passthrough — an inherited
        `ANTHROPIC_BASE_URL` (a DeepSeek gateway on this machine) or a stray
        `OPENAI_API_KEY` is exactly the class of leak the RFC calls out."""
        env = sanitized_env()
        for name in _DSH_ENV_KEEP:
            if name in env:
                continue
        env.update({
            "DSH_CWD": str(cwd),
            "DSH_MODEL": model or self.settings.strict_backend_model
            or "deepseek-v4-pro",
            "DSH_SYSTEM_PROMPT": system,
            "DSH_SESSION_ROOT": str(session_root),
        })
        return env

    # -- result mapping ------------------------------------------------------
    @staticmethod
    def _activity(events: list) -> tuple[int, list[str], SessionUsage]:
        """Best-effort (tool_calls, tools_used, usage) from the event stream.

        The SDK documents `RunResult.events` as root-session events but not
        their per-kind schema, and the shape is not worth guessing at: this
        parser accepts the plausible spellings and degrades to zeros rather
        than inventing numbers. `run_session` traces the observed event kinds
        so the first live run tells us the real shape instead of us asserting
        it here.
        """
        usage = SessionUsage()
        tools: list[str] = []
        calls = 0
        for event in events or []:
            if not isinstance(event, dict):
                continue
            kind = str(event.get("kind") or event.get("type") or "")
            data = event.get("data") if isinstance(event.get("data"), dict) else event
            if "tool" in kind and "result" not in kind:
                calls += 1
                name = data.get("name") or data.get("tool") or ""
                if name:
                    tools.append(str(name))
            raw = data.get("usage")
            if isinstance(raw, dict):
                usage.input_tokens += int(raw.get("input_tokens")
                                          or raw.get("inputTokens") or 0)
                usage.output_tokens += int(raw.get("output_tokens")
                                           or raw.get("outputTokens") or 0)
            served = data.get("model")
            if isinstance(served, str) and served:
                usage.served_model = served
        usage.tools_used = tools
        return calls, tools, usage

    # -- transport contract --------------------------------------------------
    def run_session(self, req: AgentSessionRequest) -> AgentOutcome:
        self.require_cli()
        from deepseek_harness import DeepSeekHarness

        cwd = Path(req.scope.root or req.run_dir)
        session_root = Path(req.run_dir) / "dsh" / "sessions"
        session_root.mkdir(parents=True, exist_ok=True)
        cordis = self._composition(
            run_dir=req.run_dir, step_name=req.step_name, cwd=cwd,
            read_only=req.scope.read_only,
            bridge_spec_path=req.bridge_spec_path)
        key, base_url = self._credential()
        model = req.model or self.settings.strict_backend_model

        finish = ""
        result = None
        error = ""
        try:
            with DeepSeekHarness(
                    provider="deepseek-official", model=model,
                    cwd=str(cwd), session_root=str(session_root),
                    cordis=str(cordis), api_key=key,
                    base_url=base_url or None,
                    env=self._env(cwd=cwd, model=model, system=req.system,
                                  session_root=session_root),
                    request_timeout_seconds=req.timeout_s) as harness:
                result = harness.run(req.prompt)
            finish = str(getattr(result, "finish_reason", "") or "")
        except Exception as exc:  # noqa: BLE001 — a dead harness is an outcome
            error = f"{type(exc).__name__}: {exc}"[:300]

        events = list(getattr(result, "events", None) or [])
        calls, tools, usage = self._activity(events)
        text = str(getattr(result, "final_response", "") or "").strip()
        # `max-tokens` is a TRUNCATION, not a success: surfacing it lets the
        # ensemble's zero-yield retry fire on a real signal instead of
        # inferring the ceiling from an empty final after the fact.
        truncated = finish == "max-tokens"
        refusals = []
        if error:
            refusals.append(f"dsh session failed: {error}")
        elif finish and finish not in ("completed", "max-tokens"):
            refusals.append(f"dsh finish_reason={finish}")

        if req.trace is not None:
            req.trace.record(
                "harness_session", provider=self.spec.id, step=req.step_name,
                finish_reason=finish or None, error=error or None,
                tool_calls=calls, truncated=truncated,
                served_model=usage.served_model,
                mcp_bridged=req.bridge_spec_path is not None,
                sandbox_mode=("read-only" if req.scope.read_only
                              else "workspace-write"),
                # first-run instrumentation: the SDK does not document the
                # per-kind event schema, so record what actually arrived
                event_kinds=sorted({str(e.get("kind") or e.get("type") or "?")
                                    for e in events
                                    if isinstance(e, dict)})[:20])
        return AgentOutcome(
            text=text,
            iterations=0,  # the harness does not expose its round count
            tool_calls=calls,
            truncated=truncated,
            refusals=refusals,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            tools_used=tools[:40])

    def complete(self, *, system: str, messages: list[dict],
                 model: str = "", max_tokens: int | None = None,
                 role: str = "") -> Reply:
        """Tool-less one-shot in an EMPTY scratch cwd — the containment for
        calls that need no repo at all (intent, reducer, repair). No bridge
        spec, so no MCP layer is written; bash and the editor see an empty
        directory under a read-only policy."""
        self.require_cli()
        from deepseek_harness import DeepSeekHarness

        scratch = Path(tempfile.mkdtemp(prefix="imc-dsh-oneshot-"))
        key, base_url = self._credential()
        selected = model or self.settings.strict_backend_model
        text, finish = "", ""
        try:
            cordis = self._composition(
                run_dir=scratch, step_name="oneshot", cwd=scratch,
                read_only=True, bridge_spec_path=None)
            with DeepSeekHarness(
                    provider="deepseek-official", model=selected,
                    cwd=str(scratch), session_root=str(scratch / "sessions"),
                    cordis=str(cordis), api_key=key,
                    base_url=base_url or None,
                    env=self._env(cwd=scratch, model=selected, system=system,
                                  session_root=scratch / "sessions"),
                    request_timeout_seconds=(
                        self.settings.strict_backend_timeout_s)) as harness:
                result = harness.run(flatten_messages(system, messages))
            text = str(getattr(result, "final_response", "") or "").strip()
            finish = str(getattr(result, "finish_reason", "") or "")
            _, _, usage = self._activity(
                list(getattr(result, "events", None) or []))
        except Exception:  # noqa: BLE001 — mirror cursor: empty reply, no raise
            usage = SessionUsage()
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
        return Reply(
            blocks=[Block(type="text", text=text)] if text else [],
            stop_reason="max_tokens" if finish == "max-tokens" else "end_turn",
            usage={"input_tokens": usage.input_tokens,
                   "output_tokens": usage.output_tokens,
                   "cache_read_input_tokens": 0,
                   "cache_creation_input_tokens": 0},
            model=usage.served_model)
