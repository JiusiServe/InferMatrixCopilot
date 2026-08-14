"""`HarnessLLM` — LLM-shaped adapter over a harness transport, TOOL-LESS only.

Callers that today hold an `llm.LLM` (intent classification, ensemble
reducer/merge, output repair, chat) keep their `create()` call sites; under
a harness backend those tool-less calls become one-shot CLI invocations.
Any call that passes tools raises: agent steps must route through
`run_session` (the harness owns its loop), and a loud error here is the
guard against silently running a second, ungoverned tool loop.
"""

from __future__ import annotations

from .base import HarnessTransport


class HarnessLLM:
    """Duck-typed `llm.LLM` replacement for harness backends. `available`
    reflects CLI presence so every existing `ctx.llm.available` degrade path
    keeps working; `for_member` still returns a REAL api-backed client — MoA
    members carry their own endpoint+key and are independent of the run's
    backend selection."""

    def __init__(self, settings, transport: HarnessTransport):
        self.settings = settings
        self._transport = transport

    @property
    def available(self) -> bool:
        """True when the harness CLI is installed (auth is probed by doctor,
        not here — presence is the cheap honest signal)."""
        return self._transport.cli_path() is not None

    def for_target(self, target) -> HarnessLLM:
        """Per-target client. Harness targets are served by this adapter; an
        api target (possible when MoA/tier config mixes backends) gets a real
        `llm.LLM` so it never silently rides the harness."""
        if getattr(target, "kind", "api") == "harness":
            return self
        from ..llm import LLM

        return LLM(self.settings).for_target(target)

    def for_member(self, member):
        """MoA members are raw-API endpoints with their own credentials —
        delegate to the real client; the harness never serves members."""
        from ..llm import LLM

        return LLM(self.settings).for_member(member)

    def create(self, *, system: str, messages: list[dict],
               tools: list[dict] | None = None, model: str | None = None,
               max_tokens: int | None = None, on_text=None, role: str = ""):
        """Tool-less one-shot completion via the harness CLI. `tools` raises
        by design (see module docstring)."""
        if tools:
            raise RuntimeError(
                "harness backend supports tool-less create() only — agent "
                "steps run through the provider's run_session "
                "(doc/RFC-provider-registry.md)")
        reply = self._transport.complete(
            system=system, messages=messages,
            model=model or self.settings.strict_backend_model,
            max_tokens=max_tokens, role=role)
        if on_text is not None and reply.text:
            on_text(reply.text)
        return reply
