"""LLM wrapper over the Anthropic SDK (works with DeepSeek's /anthropic endpoint).

Responses are normalized so agent loop / intent / reviewer code (and test
fakes) never touch SDK types directly.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

from .config import Settings

logger = logging.getLogger("infermatrix_copilot")


def _norm_name(name: str) -> str:
    """Case-fold and strip one trailing `[variant]` suffix (e.g. `[1m]`)."""
    return re.sub(r"\[[^\]]+\]$", "", (name or "").strip()).lower()


def canonical_model(name: str, aliases: dict | None = None) -> str:
    """Identity-normalized model name for served-vs-requested comparison ONLY
    (outbound requests and pricing keys keep the exact original strings):
    `_norm_name`, then the audited MODEL_ALIASES equivalence applied (both
    sides of the alias map are normalized the same way)."""
    n = _norm_name(name)
    amap = {_norm_name(k): _norm_name(v) for k, v in (aliases or {}).items()}
    return amap.get(n, n)


class ModelMismatchError(RuntimeError):
    """The endpoint's response named a different model than requested — it is
    substituting models (the claude-name→deepseek mapping class of incident).
    Carries the paid `reply` so budget wrappers settle actual spend before
    propagating; raised only under MODEL_MISMATCH_POLICY=fail (default)."""

    def __init__(self, *, requested: str, served: str, endpoint: str,
                 reply: "Reply | None" = None):
        super().__init__(
            f"model mismatch: requested {requested!r} but endpoint {endpoint} "
            f"served {served!r} — the backend is substituting models; fix the "
            "tier/backend config (or set MODEL_MISMATCH_POLICY=warn to accept "
            "substitutions loudly)")
        self.requested = requested
        self.served = served
        self.endpoint = endpoint
        self.reply = reply


@dataclass
class Block:
    """One content block of a reply — either assistant `text` or a `tool_use`
    request carrying the tool `id`, `name`, and parsed `input` args. The `type`
    field selects which fields are meaningful."""

    type: str  # "text" | "tool_use"
    text: str = ""
    id: str = ""
    name: str = ""
    input: dict = field(default_factory=dict)


@dataclass
class Reply:
    """A normalized model response: its content `blocks`, the `stop_reason`, and
    optional token `usage`. The provider-agnostic shape agent/intent/reviewer
    code sees instead of raw SDK types."""

    blocks: list[Block]
    stop_reason: str = "end_turn"
    usage: dict | None = None  # {"input_tokens": int, "output_tokens": int}
    model: str = ""            # SERVED model per the response (guard evidence)
    request_id: str = ""       # provider request id (header), when exposed

    @property
    def text(self) -> str:
        """The concatenated text of all text blocks, whitespace-stripped."""
        return "\n".join(b.text for b in self.blocks if b.type == "text").strip()

    @property
    def tool_uses(self) -> list[Block]:
        """The tool_use blocks (the tools the model asked to call this turn)."""
        return [b for b in self.blocks if b.type == "tool_use"]


class LLM:
    """Thin client. `available` is False when no key is configured — callers
    must degrade (deterministic fallback / escalate), never crash."""

    def __init__(self, settings: Settings):
        """Build the client only when an API key is present; otherwise stay
        unconfigured (`available` False) so callers can degrade rather than
        crash. The SDK is imported lazily so an unconfigured process needs no
        `anthropic` dependency."""
        self.settings = settings
        self._client = None
        self._default_model = ""   # set by for_target: the target's model
        self._endpoint_host = urlparse(settings.anthropic_base_url).netloc \
            if settings.anthropic_base_url else "api.anthropic.com"
        if settings.anthropic_api_key:
            import anthropic

            kwargs: dict[str, Any] = {"api_key": settings.anthropic_api_key}
            if settings.anthropic_base_url:
                kwargs["base_url"] = settings.anthropic_base_url
            self._client = anthropic.Anthropic(**kwargs)

    @property
    def available(self) -> bool:
        """True when a client was configured (an API key was present)."""
        return self._client is not None

    def for_member(self, member: Any) -> "LLM":
        """A lightweight per-member client for MoA (design W6): same Settings,
        the member's model/base_url/api_key. The member's key/base_url never
        leave the client object — logs and traces render `member.label()`
        (model@host) only."""
        clone = object.__new__(LLM)
        clone.settings = self.settings
        clone._client = None
        clone._default_model = ""
        api_key = getattr(member, "api_key", "") or self.settings.anthropic_api_key
        base = getattr(member, "base_url", "") or self.settings.anthropic_base_url
        clone._endpoint_host = urlparse(base).netloc if base else "api.anthropic.com"
        if api_key:
            import anthropic

            kwargs: dict[str, Any] = {"api_key": api_key}
            if base:
                kwargs["base_url"] = base
            clone._client = anthropic.Anthropic(**kwargs)
        return clone

    def for_target(self, target: Any) -> "LLM":
        """Per-`ResolvedTarget` client (dual-path split, plan v2): the target's
        endpoint+credential with the target's model as the default. When the
        target resolves to the shared backend, the existing SDK client is
        reused (connection pool + prompt-cache affinity preserved). Keys never
        leave the client object; traces carry host + source labels only."""
        clone = object.__new__(LLM)
        clone.settings = self.settings
        clone._default_model = getattr(target, "model", "") or ""
        base = getattr(target, "base_url", "") or ""
        key = getattr(target, "api_key", "") or ""
        clone._endpoint_host = urlparse(base).netloc if base else "api.anthropic.com"
        if (base == (self.settings.anthropic_base_url or "")
                and key == (self.settings.anthropic_api_key or "")):
            clone._client = self._client  # same backend — reuse the client
            return clone
        clone._client = None
        if key:
            import anthropic

            kwargs: dict[str, Any] = {"api_key": key}
            if base:
                kwargs["base_url"] = base
            clone._client = anthropic.Anthropic(**kwargs)
        return clone

    def create(
        self,
        *,
        system: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
        on_text=None,
        role: str = "",
    ) -> Reply:
        """`on_text(delta)` streams text as it is generated (terminal chat UX);
        the returned Reply is identical either way."""
        if self._client is None:
            raise RuntimeError("LLM not configured (ANTHROPIC_API_KEY missing)")
        kwargs = dict(
            model=model or self._default_model or self.settings.agent_model,
            system=system,
            messages=messages,
            tools=tools or [],
            max_tokens=max_tokens or self.settings.llm_max_tokens,
        )
        from . import tracing

        with tracing.span("llm", model=kwargs["model"],
                          n_tools=len(kwargs["tools"]),
                          **({"role": role} if role else {})) as _sp:
            tracing.event("llm.request", span=_sp, model=kwargs["model"],
                          n_tools=len(kwargs["tools"]), role=role or "",
                          system=kwargs.get("system", ""),
                          payload=tracing.summarize_messages(kwargs["messages"]))
            if on_text is not None:
                with self._client.messages.stream(**kwargs) as stream:
                    for delta in stream.text_stream:
                        _sp.mark_ttft()  # first streamed token = prefill done
                        on_text(delta)
                    resp = stream.get_final_message()
            else:
                resp = self._client.messages.create(**kwargs)
            tracing.set_usage(_sp, getattr(resp, "usage", None),
                              stop_reason=getattr(resp, "stop_reason", "") or "")
        blocks = []
        for b in resp.content:
            if b.type == "text":
                blocks.append(Block(type="text", text=b.text))
            elif b.type == "tool_use":
                blocks.append(Block(type="tool_use", id=b.id, name=b.name, input=dict(b.input)))
        tracing.event("llm.response", span=_sp,
                      stop_reason=resp.stop_reason or "end_turn",
                      text="".join(b.text for b in blocks if b.type == "text"),
                      tool_calls=[{"name": b.name, "id": b.id, "input": b.input}
                                  for b in blocks if b.type == "tool_use"],
                      # the endpoint exposes no token ids, so the replayable
                      # record is this text plus the counts for the same call
                      **tracing.usage_counts(getattr(resp, "usage", None)))
        usage = None
        if getattr(resp, "usage", None) is not None:
            usage = {"input_tokens": getattr(resp.usage, "input_tokens", 0),
                     "output_tokens": getattr(resp.usage, "output_tokens", 0),
                     # the endpoint reports cache reads separately (and
                     # excludes them from input_tokens) — capture for billing
                     "cache_read_input_tokens":
                         getattr(resp.usage, "cache_read_input_tokens", 0) or 0,
                     "cache_creation_input_tokens":
                         getattr(resp.usage, "cache_creation_input_tokens", 0) or 0}
        served = str(getattr(resp, "model", "") or "")
        request_id = str(getattr(resp, "_request_id", "") or "")
        reply = Reply(blocks=blocks, stop_reason=resp.stop_reason or "end_turn",
                      usage=usage, model=served, request_id=request_id)
        self._guard_served_model(kwargs["model"], reply, _sp)
        return reply

    def _guard_served_model(self, requested: str, reply: Reply, sp: Any) -> None:
        """Served-model guard (plan v2): every response's `model` is compared
        to the request after alias normalization and recorded on the span +
        an `llm.served` event (match or not — future runs carry proof of what
        served them). A contradiction raises `ModelMismatchError` under the
        default fail policy, carrying the paid reply so budget wrappers settle
        actual spend; an ABSENT served model is `unverified` (warn only — the
        strong check for silent providers is `doctor --probe`). Detects
        metadata-visible substitution only; a proxy that echoes the requested
        name defeats it."""
        from . import tracing

        aliases = getattr(self.settings, "model_aliases", {}) or {}
        served, host = reply.model, self._endpoint_host
        if not served:
            verdict = "unverified"
        elif canonical_model(served, aliases) == canonical_model(requested, aliases):
            verdict = "match"
            if _norm_name(served) != _norm_name(requested) and aliases:
                tracing.event("model_alias_applied", span=sp,
                              requested=requested, served=served)
        else:
            verdict = "mismatch"
        if sp is not None:
            sp.set(served_model=served, endpoint=host, served_verdict=verdict)
        tracing.event("llm.served", span=sp, requested=requested, served=served,
                      endpoint=host, request_id=reply.request_id, verdict=verdict)
        if verdict == "unverified":
            logger.warning("llm response from %s carries no model field — "
                           "served model unverified (requested %s); "
                           "run `doctor --probe` to check the backend",
                           host, requested)
        elif verdict == "mismatch":
            policy = getattr(self.settings, "model_mismatch_policy", "fail")
            if policy == "fail":
                raise ModelMismatchError(requested=requested, served=served,
                                         endpoint=host, reply=reply)
            logger.warning("MODEL MISMATCH accepted by policy=warn: requested "
                           "%s, endpoint %s served %s", requested, host, served)


def parse_json_reply(text: str) -> dict | None:
    """Extract a JSON object from an LLM reply (fenced or bare)."""
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidates = [fence.group(1)] if fence else []
    brace = re.search(r"\{.*\}", text, re.DOTALL)
    if brace:
        candidates.append(brace.group(0))
    for c in candidates:
        try:
            obj = json.loads(c)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue
    return None
