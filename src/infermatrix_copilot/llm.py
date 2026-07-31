"""Provider-neutral LLM wrapper for Anthropic and OpenAI-compatible endpoints.

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


def _build_client(provider: str, api_key: str, base_url: str = "") -> Any:
    """Build one provider SDK client without exposing credentials elsewhere."""
    kwargs: dict[str, Any] = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    if provider == "openai":
        import openai

        return openai.OpenAI(**kwargs)
    import anthropic

    return anthropic.Anthropic(**kwargs)


def _default_host(provider: str) -> str:
    return "api.openai.com" if provider == "openai" else "api.anthropic.com"


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
        self._provider = settings.resolved_llm_provider
        base = settings.shared_base_url
        self._endpoint_host = urlparse(base).netloc if base \
            else _default_host(self._provider)
        if settings.shared_api_key:
            self._client = _build_client(
                self._provider, settings.shared_api_key, base)

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
        clone._provider = getattr(self, "_provider",
                                  self.settings.resolved_llm_provider)
        api_key = getattr(member, "api_key", "") or self.settings.shared_api_key
        base = getattr(member, "base_url", "") or self.settings.shared_base_url
        clone._endpoint_host = urlparse(base).netloc if base \
            else _default_host(clone._provider)
        if api_key:
            clone._client = _build_client(clone._provider, api_key, base)
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
        clone._provider = getattr(
            target, "provider", self.settings.resolved_llm_provider)
        clone._endpoint_host = urlparse(base).netloc if base \
            else _default_host(clone._provider)
        if (clone._provider == getattr(self, "_provider", "anthropic")
                and base == (self.settings.shared_base_url or "")
                and key == (self.settings.shared_api_key or "")):
            clone._client = self._client  # same backend — reuse the client
            return clone
        clone._client = None
        if key:
            clone._client = _build_client(clone._provider, key, base)
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
            raise RuntimeError(
                "LLM not configured (set ANTHROPIC_API_KEY or OPENAI_API_KEY)")
        provider = getattr(self, "_provider", "anthropic")
        selected_model = (
            model or self._default_model or self.settings.shared_model)
        kwargs = dict(
            model=selected_model,
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
            if provider == "anthropic" and on_text is not None:
                with self._client.messages.stream(**kwargs) as stream:
                    for delta in stream.text_stream:
                        _sp.mark_ttft()  # first streamed token = prefill done
                        on_text(delta)
                    resp = stream.get_final_message()
                blocks, stop_reason, usage, served, request_id = \
                    self._normalize_anthropic(resp)
            elif provider == "openai":
                resp = self._create_openai(**kwargs)
                blocks, stop_reason, usage, served, request_id = \
                    self._normalize_openai(resp)
                if on_text is not None:
                    _sp.mark_ttft()
                    text = "".join(
                        b.text for b in blocks if b.type == "text")
                    if text:
                        on_text(text)
            else:
                resp = self._client.messages.create(**kwargs)
                blocks, stop_reason, usage, served, request_id = \
                    self._normalize_anthropic(resp)
            tracing.set_usage(_sp, usage, stop_reason=stop_reason)
        tracing.event("llm.response", span=_sp,
                      stop_reason=stop_reason,
                      text="".join(b.text for b in blocks if b.type == "text"),
                      tool_calls=[{"name": b.name, "id": b.id, "input": b.input}
                                  for b in blocks if b.type == "tool_use"],
                      # the endpoint exposes no token ids, so the replayable
                      # record is this text plus the counts for the same call
                      **tracing.usage_counts(usage))
        reply = Reply(blocks=blocks, stop_reason=stop_reason,
                      usage=usage, model=served, request_id=request_id)
        self._guard_served_model(kwargs["model"], reply, _sp)
        return reply

    @staticmethod
    def _normalize_anthropic(resp: Any) -> tuple[
            list[Block], str, dict | None, str, str]:
        blocks = []
        for b in resp.content:
            if b.type == "text":
                blocks.append(Block(type="text", text=b.text))
            elif b.type == "tool_use":
                blocks.append(Block(
                    type="tool_use", id=b.id, name=b.name,
                    input=dict(b.input)))
        usage = None
        if getattr(resp, "usage", None) is not None:
            usage = {
                "input_tokens": getattr(resp.usage, "input_tokens", 0),
                "output_tokens": getattr(resp.usage, "output_tokens", 0),
                "cache_read_input_tokens": getattr(
                    resp.usage, "cache_read_input_tokens", 0) or 0,
                "cache_creation_input_tokens": getattr(
                    resp.usage, "cache_creation_input_tokens", 0) or 0,
            }
        return (
            blocks,
            getattr(resp, "stop_reason", "") or "end_turn",
            usage,
            str(getattr(resp, "model", "") or ""),
            str(getattr(resp, "_request_id", "") or ""),
        )

    def _create_openai(self, **kwargs: Any) -> Any:
        tools = [{
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("input_schema", {
                    "type": "object", "properties": {}}),
            },
        } for tool in kwargs["tools"]]
        request: dict[str, Any] = {
            "model": kwargs["model"],
            "messages": self._openai_messages(
                kwargs["system"], kwargs["messages"]),
        }
        # Official current OpenAI models use max_completion_tokens. Many
        # OpenAI-compatible gateways still implement the older max_tokens.
        token_field = ("max_completion_tokens"
                       if self._endpoint_host == "api.openai.com"
                       else "max_tokens")
        request[token_field] = kwargs["max_tokens"]
        if tools:
            request["tools"] = tools
        return self._client.chat.completions.create(**request)

    @staticmethod
    def _openai_messages(system: str, messages: list[dict]) -> list[dict]:
        """Translate the internal Anthropic block protocol to Chat Completions."""
        out: list[dict] = [{"role": "system", "content": system}]
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if isinstance(content, str):
                out.append({"role": role, "content": content})
                continue
            if role == "assistant":
                texts, tool_calls = [], []
                for block in content:
                    if block.get("type") == "text":
                        texts.append(str(block.get("text", "")))
                    elif block.get("type") == "tool_use":
                        tool_calls.append({
                            "id": block.get("id", ""),
                            "type": "function",
                            "function": {
                                "name": block.get("name", ""),
                                "arguments": json.dumps(
                                    block.get("input", {}),
                                    ensure_ascii=False),
                            },
                        })
                item: dict[str, Any] = {
                    "role": "assistant",
                    "content": "\n".join(texts) or None,
                }
                if tool_calls:
                    item["tool_calls"] = tool_calls
                out.append(item)
                continue
            user_texts = []
            for block in content:
                if block.get("type") == "tool_result":
                    out.append({
                        "role": "tool",
                        "tool_call_id": block.get("tool_use_id", ""),
                        "content": str(block.get("content", "")),
                    })
                elif block.get("type") == "text":
                    user_texts.append(str(block.get("text", "")))
            if user_texts:
                out.append({"role": "user", "content": "\n".join(user_texts)})
        return out

    @staticmethod
    def _normalize_openai(resp: Any) -> tuple[
            list[Block], str, dict | None, str, str]:
        choice = resp.choices[0]
        message = choice.message
        blocks = []
        content = getattr(message, "content", None)
        if content:
            blocks.append(Block(type="text", text=str(content)))
        for call in getattr(message, "tool_calls", None) or []:
            raw = getattr(call.function, "arguments", "") or "{}"
            try:
                parsed = json.loads(raw)
                args = parsed if isinstance(parsed, dict) else {"value": parsed}
            except json.JSONDecodeError:
                args = {"_raw": raw}
            blocks.append(Block(
                type="tool_use", id=call.id, name=call.function.name,
                input=args))
        raw_stop = getattr(choice, "finish_reason", "") or ""
        stop_reason = {
            "stop": "end_turn",
            "tool_calls": "tool_use",
            "length": "max_tokens",
        }.get(raw_stop, raw_stop or "end_turn")
        raw_usage = getattr(resp, "usage", None)
        usage = None
        if raw_usage is not None:
            details = getattr(raw_usage, "prompt_tokens_details", None)
            usage = {
                "input_tokens": getattr(raw_usage, "prompt_tokens", 0) or 0,
                "output_tokens": getattr(
                    raw_usage, "completion_tokens", 0) or 0,
                "cache_read_input_tokens": getattr(
                    details, "cached_tokens", 0) or 0,
                "cache_creation_input_tokens": 0,
            }
        return (
            blocks,
            stop_reason,
            usage,
            str(getattr(resp, "model", "") or ""),
            str(getattr(resp, "_request_id", "")
                or getattr(resp, "id", "") or ""),
        )

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
