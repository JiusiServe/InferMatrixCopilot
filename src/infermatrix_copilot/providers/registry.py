"""Provider registry — the one table of ways to reach a model.

All four ids resolve to shipped transports (M1 cursor, M2 claude-code,
M3 codex — doc/features/provider-registry.md). `_UNSHIPPED` remains the
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
        # The one API-KEYED harness: dsh is driven through its Python SDK
        # (no PATH binary — the bundled runtime ships in the wheel) and needs
        # a DeepSeek credential, unlike the three subscription CLIs above.
        # `api_keyed` marks that asymmetry for callers that assume "harness
        # ⇒ the vendor holds the credential" (see providers/deepseek.py).
        # NOTE: no `mcp_tools`. The bundled dsh runtime compiles in 122 plugins
        # and `@deepseek-ai/dsh-mcp-client` is not among them, so our tool
        # bridge is unreachable and sessions run on the harness's native bash
        # (providers/deepseek.py traces a `review.mcp_tool_bridge`
        # capability_gap and reports mcp_bridged=False). Declaring the flag
        # here claimed a capability the transport measurably does not have —
        # and `base.ProviderSpec` defines these as "flags the integration can
        # rely on". Nothing branches on it today, which is exactly why the
        # false claim survived: it only ever misled readers.
        # `default_model`: dsh has no built-in default — constructing it with
        # an empty model kills every turn with "has no provider/model", so an
        # unset STRICT_BACKEND_MODEL must resolve to something here rather
        # than inside the transport, where the resolved target would keep
        # reporting "" while the harness actually served this model.
        ProviderSpec(
            id="deepseek", kind="harness",
            display="DeepSeek Harness (dsh) via deepseek-harness-sdk",
            cli_names=(),
            capabilities=frozenset({
                "sandbox_read_only", "system_prompt", "api_keyed"}),
            default_model="deepseek-v4-pro"),
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
            "(doc/features/provider-registry.md)")
    if spec.id == "cursor":
        from .cursor import CursorTransport

        return CursorTransport(settings)
    if spec.id == "claude-code":
        from .claude_code import ClaudeCodeTransport

        return ClaudeCodeTransport(settings)
    if spec.id == "deepseek":
        from .deepseek import DeepSeekHarnessTransport

        return DeepSeekHarnessTransport(settings)
    from .codex import CodexTransport

    return CodexTransport(settings)
