"""Provider registry — the one table of ways to reach a model.

All four ids resolve to shipped transports (M1 cursor, M2 claude-code,
M3 codex — doc/RFC-provider-registry.md). `_UNSHIPPED` remains the
mechanism for declaring a future backend before its transport lands:
`transport_for` raises its milestone pointer so `strict_readiness`/doctor
report "not yet shipped" instead of a run failing mid-flight.
"""

from __future__ import annotations

from .base import HarnessTransport, ProviderSpec

PROVIDERS: dict[str, ProviderSpec] = {
    p.id: p for p in (
        ProviderSpec(
            id="api", kind="api",
            display="Raw API (Anthropic/OpenAI-compatible, keyed in .env)"),
        ProviderSpec(
            id="cursor", kind="harness",
            display="Cursor subscription via cursor-agent CLI",
            cli_names=("cursor-agent",),
            capabilities=frozenset({"mcp_tools", "usage_reporting"})),
        ProviderSpec(
            id="claude-code", kind="harness",
            display="Claude subscription via claude CLI",
            cli_names=("claude",),
            capabilities=frozenset({
                "mcp_tools", "builtin_tools_off", "max_turns",
                "system_prompt", "usage_reporting", "cost_reporting"})),
        ProviderSpec(
            id="codex", kind="harness",
            display="ChatGPT subscription via codex CLI",
            cli_names=("codex",),
            capabilities=frozenset({
                "mcp_tools", "sandbox_read_only", "usage_reporting"})),
    )
}

# Declared-but-unshipped backends (currently none) — transport_for names the
# milestone instead of returning a transport that cannot work.
_UNSHIPPED: dict[str, str] = {}


def resolve_provider(settings) -> ProviderSpec:
    """The selected provider: `STRICT_BACKEND`, with empty meaning `api` for
    the CLI path (Strict enforces explicit selection at its own boundary —
    `strict_readiness` — not here)."""
    selected = getattr(settings, "strict_backend", "") or "api"
    spec = PROVIDERS.get(selected)
    if spec is None:  # Settings validation rejects unknown ids upfront
        raise ValueError(
            f"unknown STRICT_BACKEND {selected!r} — one of: "
            + ", ".join(sorted(PROVIDERS)))
    return spec


def transport_for(settings) -> HarnessTransport:
    """The harness transport for the selected provider. Raises ValueError for
    api (it has no harness transport) and NotImplementedError with the
    milestone for declared-but-unshipped harnesses."""
    return transport_for_id(settings, resolve_provider(settings).id)


def transport_for_id(settings, provider_id: str) -> HarnessTransport:
    """The harness transport for an EXPLICIT provider id, independent of the
    run's `STRICT_BACKEND` selection — the seam MoA harness members use to
    ride a harness inside an api-backed run."""
    spec = PROVIDERS.get(provider_id)
    if spec is None:
        raise ValueError(f"unknown provider {provider_id!r} — one of: "
                         + ", ".join(sorted(PROVIDERS)))
    if spec.kind != "harness":
        raise ValueError("provider 'api' is not a harness — resolution stays "
                         "with Settings.tier_target/llm.LLM")
    milestone = _UNSHIPPED.get(spec.id)
    if milestone:
        raise NotImplementedError(
            f"backend {spec.id!r} is declared but ships in {milestone} "
            "(doc/RFC-provider-registry.md)")
    if spec.id == "cursor":
        from .cursor import CursorTransport

        return CursorTransport(settings)
    if spec.id == "claude-code":
        from .claude_code import ClaudeCodeTransport

        return ClaudeCodeTransport(settings)
    from .codex import CodexTransport

    return CodexTransport(settings)
