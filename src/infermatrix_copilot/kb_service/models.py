"""Pinned model roles for the knowledge service, with no silent fallback.

The generator drafts knowledge changes; the judge (a different model family)
grades them. Both are pinned by (provider, model, reasoning effort) and
recorded on every call. An unavailable backend, a timeout or an unparseable
reply raises ``ModelUnavailable``; the caller leaves the work queued. It never
switches to a weaker model: a verdict must always say which model made it.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Callable

GENERATOR_ENV = "KB_GENERATOR"   # "provider:model[:effort]"
JUDGE_ENV = "KB_JUDGE"
DEFAULT_GENERATOR = "claude-code:claude-opus-5-5"
DEFAULT_JUDGE = "codex:gpt-6-sol:medium"
_JSON_FENCE = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)


class ModelUnavailable(RuntimeError):
    """The pinned backend could not produce a usable reply; work stays queued."""


@dataclass(frozen=True)
class ModelRole:
    name: str
    provider: str
    model: str
    effort: str = ""

    @classmethod
    def parse(cls, name: str, spec: str) -> "ModelRole":
        parts = spec.split(":")
        if len(parts) not in (2, 3) or not all(parts[:2]):
            raise ValueError(f"{name} must be provider:model[:effort], got {spec!r}")
        return cls(name, parts[0], parts[1], parts[2] if len(parts) == 3 else "")

    def label(self) -> str:
        return f"{self.provider}:{self.model}" + (f":{self.effort}" if self.effort else "")


def roles_from_env() -> tuple[ModelRole, ModelRole]:
    generator = ModelRole.parse("generator", os.environ.get(GENERATOR_ENV, DEFAULT_GENERATOR))
    judge = ModelRole.parse("judge", os.environ.get(JUDGE_ENV, DEFAULT_JUDGE))
    if generator.provider == judge.provider and generator.model.split("-")[0] == judge.model.split("-")[0]:
        raise ValueError("the judge must come from a different model family than the generator")
    return generator, judge


@dataclass(frozen=True)
class ModelReply:
    role: ModelRole
    data: dict
    text: str
    served_model: str
    usage: dict
    seconds: float


def parse_json_object(text: str) -> dict:
    """The reply's JSON object: a bare object, or the last fenced ```json block.
    Raw control characters inside strings (a newline in a multi-line value,
    e.g. a diagram) are accepted: models write them, and they are data, not
    structure (``strict=False``)."""
    text = text.strip()
    candidates = [text] + [m.group(1) for m in _JSON_FENCE.finditer(text)][::-1]
    for candidate in candidates:
        try:
            value = json.loads(candidate, strict=False)
        except ValueError:
            continue
        if isinstance(value, dict):
            return value
    raise ModelUnavailable("reply is not a JSON object")


class ModelGateway:
    """One-shot structured calls through the provider registry's harness
    transports. ``transport_factory(provider_id)`` is injectable for tests."""

    def __init__(self, settings, *, transport_factory: Callable[[str], Any] | None = None,
                 recorder: Callable[[dict], None] | None = None):
        self._settings = settings
        self._factory = transport_factory
        self._recorder = recorder

    def _transport(self, provider: str):
        if self._factory is not None:
            return self._factory(provider)
        from ..providers.registry import transport_for_id

        transport = transport_for_id(self._settings, provider)
        if transport.cli_path() is None:
            raise ModelUnavailable(f"{provider} CLI is not installed")
        gap = transport.auth_gap()
        if gap:
            raise ModelUnavailable(f"{provider} is not logged in: {gap}")
        return transport

    def call_json(self, role: ModelRole, *, system: str, prompt: str,
                  validate: Callable[[dict], None] | None = None) -> ModelReply:
        transport = self._transport(role.provider)
        started = time.time()
        identity = {"role": role.name, "requested": role.label(), "provider": role.provider,
                    "model": role.model, "effort": role.effort}
        try:
            reply = transport.complete(
                system=system, messages=[{"role": "user", "content": prompt}],
                model=role.model, effort=role.effort, role=role.name)
        except Exception as exc:  # the transport's own failure modes
            if self._recorder is not None:
                self._recorder({**identity, "served_model": "", "stop_reason": "", "usage": {},
                                "seconds": round(time.time() - started, 3), "system": system,
                                "prompt": prompt, "reply": "", "error": str(exc)[:2000]})
            raise ModelUnavailable(f"{role.label()} failed: {exc}") from exc
        seconds = time.time() - started
        text = "".join(getattr(block, "text", "") or "" for block in getattr(reply, "blocks", []))
        record = {
            **identity,
            "served_model": getattr(reply, "model", "") or "",
            "stop_reason": getattr(reply, "stop_reason", ""),
            "usage": dict(getattr(reply, "usage", {}) or {}),
            "seconds": round(seconds, 3), "system": system, "prompt": prompt, "reply": text,
        }
        # the record carries the call's FINAL verdict: a truncated, empty,
        # unparseable or schema-failing reply is recorded as a failure, so it
        # never becomes a training example
        failure: ModelUnavailable | None = None
        data: dict = {}
        if getattr(reply, "stop_reason", "") == "max_tokens" or not text.strip():
            failure = ModelUnavailable(f"{role.label()} timed out or returned nothing")
        else:
            try:
                data = parse_json_object(text)
                if validate is not None:
                    try:
                        validate(data)
                    except Exception as exc:  # any malformed shape is a controlled refusal
                        raise ModelUnavailable(f"{role.label()} reply failed its schema: {exc!r}") from exc
            except ModelUnavailable as exc:
                failure = exc
        if self._recorder is not None:
            self._recorder({**record, "error": str(failure) if failure else ""})
        if failure is not None:
            raise failure
        return ModelReply(role, data, text, record["served_model"], record["usage"], seconds)
