"""LLM wrapper over the Anthropic SDK (works with DeepSeek's /anthropic endpoint).

Responses are normalized so agent loop / intent / reviewer code (and test
fakes) never touch SDK types directly.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from .config import Settings


@dataclass
class Block:
    type: str  # "text" | "tool_use"
    text: str = ""
    id: str = ""
    name: str = ""
    input: dict = field(default_factory=dict)


@dataclass
class Reply:
    blocks: list[Block]
    stop_reason: str = "end_turn"
    usage: dict | None = None  # {"input_tokens": int, "output_tokens": int}

    @property
    def text(self) -> str:
        return "\n".join(b.text for b in self.blocks if b.type == "text").strip()

    @property
    def tool_uses(self) -> list[Block]:
        return [b for b in self.blocks if b.type == "tool_use"]


class LLM:
    """Thin client. `available` is False when no key is configured — callers
    must degrade (deterministic fallback / escalate), never crash."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = None
        if settings.anthropic_api_key:
            import anthropic

            kwargs: dict[str, Any] = {"api_key": settings.anthropic_api_key}
            if settings.anthropic_base_url:
                kwargs["base_url"] = settings.anthropic_base_url
            self._client = anthropic.Anthropic(**kwargs)

    @property
    def available(self) -> bool:
        return self._client is not None

    def create(
        self,
        *,
        system: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
        on_text=None,
    ) -> Reply:
        """`on_text(delta)` streams text as it is generated (terminal chat UX);
        the returned Reply is identical either way."""
        if self._client is None:
            raise RuntimeError("LLM not configured (ANTHROPIC_API_KEY missing)")
        kwargs = dict(
            model=model or self.settings.agent_model,
            system=system,
            messages=messages,
            tools=tools or [],
            max_tokens=max_tokens or self.settings.llm_max_tokens,
        )
        if on_text is not None:
            with self._client.messages.stream(**kwargs) as stream:
                for delta in stream.text_stream:
                    on_text(delta)
                resp = stream.get_final_message()
        else:
            resp = self._client.messages.create(**kwargs)
        blocks = []
        for b in resp.content:
            if b.type == "text":
                blocks.append(Block(type="text", text=b.text))
            elif b.type == "tool_use":
                blocks.append(Block(type="tool_use", id=b.id, name=b.name, input=dict(b.input)))
        usage = None
        if getattr(resp, "usage", None) is not None:
            usage = {"input_tokens": getattr(resp.usage, "input_tokens", 0),
                     "output_tokens": getattr(resp.usage, "output_tokens", 0),
                     # the endpoint reports cache reads separately (and
                     # excludes them from input_tokens) — capture for billing
                     "cache_read_input_tokens":
                         getattr(resp.usage, "cache_read_input_tokens", 0) or 0}
        return Reply(blocks=blocks, stop_reason=resp.stop_reason or "end_turn",
                     usage=usage)


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
