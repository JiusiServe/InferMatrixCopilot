"""Provider-layer contracts (doc/features/provider-registry.md).

A *provider* is one way to reach a model. Two kinds exist:

- ``api`` — a raw Anthropic/OpenAI-compatible completions endpoint (today's
  `llm.LLM`, resolved by `Settings.tier_target`). Stateless
  ``system+messages+tools -> tool_use`` round trips; our `agent_loop` owns
  the tool loop.
- ``harness`` — a subscription-authed vendor agent CLI (cursor-agent,
  claude -p, codex exec). Harnesses own their tool loop, so the integration
  seam is a WHOLE agent step (`run_session`), never `LLM.create`; tool
  access flows back through the MCP tool bridge so every call still passes
  `tools.dispatch`.

The credential model is deliberately asymmetric: api providers resolve
key+endpoint through Settings; harness providers hold their subscription
auth inside the vendor CLI's own state and this codebase never sees it.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from ..scopes import ToolScope

# Env a harness CLI subprocess keeps. Everything else — API keys, base URLs,
# gh tokens, host markers like CLAUDECODE — is dropped: subscription auth
# lives in HOME state, and an inherited ANTHROPIC_BASE_URL (a gateway on
# this class of machine) would silently reroute a vendor CLI's traffic.
_ENV_KEEP = {"PATH", "HOME", "TERM", "COLORTERM", "LANG", "USER", "LOGNAME",
             "SHELL", "TMPDIR"}
_ENV_KEEP_PREFIXES = ("LC_", "XDG_")


def sanitized_env() -> dict[str, str]:
    """The allowlisted environment for spawning a harness CLI."""
    return {k: v for k, v in os.environ.items()
            if k in _ENV_KEEP or k.startswith(_ENV_KEEP_PREFIXES)}


@dataclass(frozen=True)
class ProviderSpec:
    """One registry entry: identity, kind, and the capability flags the
    integration can rely on (``mcp_tools``, ``builtin_tools_off``,
    ``max_turns``, ``system_prompt``, ``usage_reporting``,
    ``cost_reporting``). `cli_names` are the binaries probed on PATH for
    harness kinds."""

    id: str
    kind: Literal["api", "harness"]
    display: str
    cli_names: tuple[str, ...] = ()
    capabilities: frozenset[str] = frozenset()


@dataclass
class AgentSessionRequest:
    """One delegated agent step: the SAME prompt bundle `run_agent` would
    receive (contract `system` + rendered dispatch context `prompt`), the
    step's `scope`, and the session bounds. `bridge_spec_path` points at the
    serialized tool-bridge spec the harness's MCP config should launch;
    `max_iters` maps to a native turn cap where the harness has one
    (claude --max-turns) and otherwise rides `timeout_s` plus the prompt's
    budget-discipline lines."""

    system: str
    prompt: str
    scope: ToolScope
    model: str
    max_iters: int
    timeout_s: float
    run_dir: Path
    step_name: str = ""
    bridge_spec_path: Path | None = None
    trace: Any = None  # RunTrace-shaped (record(kind, **fields)) or None


@dataclass
class SessionUsage:
    """Best-effort usage extracted from a harness CLI's output. Harnesses
    report unevenly; absent numbers stay 0 and cost stays None (metrics must
    record source "subscription", never fabricate USD)."""

    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float | None = None
    served_model: str = ""
    tools_used: list[str] = field(default_factory=list)


class HarnessTransport:
    """Base for harness-kind transports. Subclasses set `spec` and implement
    `run_session` (a whole agent step) and `complete` (one-shot TOOL-LESS
    call for `HarnessLLM`). `cli_path` is the shared binary resolution:
    explicit `STRICT_BACKEND_CLI` first, then the spec's names on PATH."""

    spec: ProviderSpec

    def __init__(self, settings):
        self.settings = settings

    def cli_path(self) -> str | None:
        """The harness binary to execute, or None when not installed."""
        override = getattr(self.settings, "strict_backend_cli", "")
        if override:
            return override
        for name in self.spec.cli_names:
            found = shutil.which(name)
            if found:
                return found
        return None

    def require_cli(self) -> str:
        """`cli_path` or a RuntimeError naming the exact fix."""
        cli = self.cli_path()
        if not cli:
            raise RuntimeError(
                f"{self.spec.id} backend selected but no CLI found "
                f"({' / '.join(self.spec.cli_names)}) — install it or set "
                "STRICT_BACKEND_CLI=/path/to/cli in ~/.infermatrix-copilot/.env")
        return cli

    def auth_gap(self) -> str | None:
        """A one-line auth problem with its fix, or None when unknown/fine.
        Cheap enough for `strict_readiness` (one fast CLI status call at
        most); transports without a cheap check return None and let the run
        surface auth errors loudly."""
        return None

    # -- contract ------------------------------------------------------------
    def run_session(self, req: AgentSessionRequest):
        """Run one delegated agent step; returns `agent_loop.AgentOutcome`."""
        raise NotImplementedError

    def complete(self, *, system: str, messages: list[dict],
                 model: str = "", max_tokens: int | None = None,
                 role: str = ""):
        """One-shot tool-less completion; returns a normalized `llm.Reply`."""
        raise NotImplementedError


def flatten_messages(system: str, messages: list[dict]) -> str:
    """Render an internal block-protocol conversation as one prompt string for
    harnesses without a messages channel. Tool-less conversations only (the
    caller guarantees it): content is either a string or text blocks."""
    parts = [system] if system else []
    for message in messages:
        role = str(message.get("role", "user")).upper()
        content = message.get("content", "")
        if isinstance(content, str):
            text = content
        else:
            text = "\n".join(str(b.get("text", "")) for b in content
                             if isinstance(b, dict) and b.get("type") == "text")
        if text:
            parts.append(f"[{role}]\n{text}")
    return "\n\n".join(parts)
