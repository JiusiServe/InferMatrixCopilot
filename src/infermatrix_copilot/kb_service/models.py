"""Pinned model roles with an explicitly configured generator fallback.

The generator drafts knowledge changes; the judge (a different model family)
grades them. Both are pinned by (provider, model, reasoning effort) and
recorded on every call. ``KB_GENERATOR_FALLBACK`` may name one pinned model
to try when generation is unavailable. Judges never fall back, and schema
repair and spend limits retain their existing behavior. If both generators
are unavailable, the caller leaves the work queued.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass, replace
from typing import Any, Callable

GENERATOR_ENV = "KB_GENERATOR"   # "provider:model[:effort]"
GENERATOR_FALLBACK_ENV = "KB_GENERATOR_FALLBACK"
JUDGE_ENV = "KB_JUDGE"
DEFAULT_GENERATOR = "claude-code:claude-opus-5-5"
DEFAULT_JUDGE = "codex:gpt-6-sol:medium"
_JSON_FENCE = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)
logger = logging.getLogger(__name__)


class ModelUnavailable(RuntimeError):
    """The pinned backend could not produce a usable reply; work stays queued."""

    def __init__(self, message: str, *, allow_fallback: bool = True):
        super().__init__(message)
        self.allow_fallback = allow_fallback


@dataclass(frozen=True)
class ModelRole:
    name: str
    provider: str
    model: str
    effort: str = ""
    fallback: ModelRole | None = None

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
    fallback_spec = os.environ.get(GENERATOR_FALLBACK_ENV, "").strip()
    if fallback_spec:
        fallback = ModelRole.parse("generator", fallback_spec)
        if fallback.label().casefold() == generator.label().casefold():
            raise ValueError("the generator fallback must differ from the primary generator")
        generator = replace(generator, fallback=fallback)
    for candidate in (generator, generator.fallback):
        if candidate is not None and candidate.provider == judge.provider \
                and candidate.model.casefold().split("-")[0] == judge.model.casefold().split("-")[0]:
            raise ValueError("the judge must come from a different model family than every generator")
    return generator, judge


@dataclass(frozen=True)
class ModelReply:
    role: ModelRole
    data: dict
    text: str
    served_model: str
    usage: dict
    seconds: float
    cost_usd: float | None = None  # the transport's reported spend (None: unknown)
    trace_id: str = ""
    reply_sha256: str = ""


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
                 recorder: Callable[[dict], None] | None = None, zcode_pacer=None):
        self._settings = settings
        self._factory = transport_factory
        self._recorder = recorder
        self._subscription_transports: dict[str, Any] = {}
        self._zcode_pacer = zcode_pacer

    def configure_zcode_pacing(self, pacer):
        """Only the explicit native campaign configures shared dispatch pacing."""
        self._zcode_pacer = pacer

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
                  validate: Callable[[dict], None] | None = None,
                  max_budget_usd: float | None = None, record_payload: bool = True) -> ModelReply:
        """Try the primary, then one configured generator on unavailability.

        Both attempts use the same validation and payload policy. Calls with
        a spend threshold and schema errors never trigger a second model call:
        the caller has reserved for one model, and Zcode cannot enforce a cap.
        """
        kwargs = dict(system=system, prompt=prompt, validate=validate,
                      max_budget_usd=max_budget_usd, record_payload=record_payload)
        try:
            return self._call_json(role, **kwargs)
        except ModelUnavailable as primary_error:
            if role.name != "generator" or role.fallback is None \
                    or max_budget_usd is not None or not primary_error.allow_fallback:
                raise
            logger.warning("Knowledge generator %s unavailable; trying configured fallback %s",
                           role.label(), role.fallback.label())
            try:
                return self._call_json(role.fallback, fallback_from=role.label(), **kwargs)
            except ModelUnavailable as fallback_error:
                raise ModelUnavailable(
                    f"{role.label()} unavailable: {primary_error}; "
                    f"fallback {role.fallback.label()} unavailable: {fallback_error}",
                    allow_fallback=False) from fallback_error

    def _call_json(self, role: ModelRole, *, system: str, prompt: str,
                   validate: Callable[[dict], None] | None = None,
                   max_budget_usd: float | None = None, record_payload: bool = True,
                   fallback_from: str = "") -> ModelReply:
        """``max_budget_usd`` is a per-call STOP THRESHOLD, not a hard cap:
        the transport starts no further API request once the call's spend
        reaches it, but the request that crosses it is billed in full. A
        caller enforcing a hard ceiling must reserve the threshold plus one
        request's worst case before calling. Requesting a threshold from a
        transport that cannot stop at one (``stops_at_spend`` False) is
        refused before dispatch; it is never approximated with ``max_tokens``."""
        started = time.time()
        identity = {"role": role.name, "requested": role.label(), "provider": role.provider,
                    "model": role.model, "effort": role.effort, "fallback_from": fallback_from}
        payload = {"system": system if record_payload else "", "prompt": prompt if record_payload else ""}
        begin = getattr(self._recorder, "begin_call", None)
        archive = begin({**identity, **payload}) if callable(begin) else None
        native_events: list[dict] = []
        transport = None
        pacer = self._zcode_pacer if role.provider == "zcode" else None
        pacing_ticket = None

        def event_sink(event):
            native_events.append(event)
            if archive is not None and record_payload:
                archive.event(event)
            if pacer is not None and pacing_ticket is not None:
                pacer.observe(pacing_ticket, event, event_sink)

        def record_call(entry, status):
            if archive is not None:
                entry.update(archive.payload())
            receipt = self._recorder(entry) if self._recorder else None
            if archive is not None:
                archive.finish(receipt if isinstance(receipt, dict) else None, entry, status=status)
            return receipt

        try:
            if self._zcode_pacer is not None and self._zcode_pacer.stop_file and self._zcode_pacer.stop_file.exists():
                event_sink({"type": "native.throttle.stopped", "payload": {"at": time.time(), "before_dispatch": True}})
                canceled = ModelUnavailable("campaign stop requested before native dispatch", allow_fallback=False)
                canceled.pre_dispatch_cancelled = True
                raise canceled
            transport = self._subscription_transports.pop(role.label(), None)
            if transport is None:
                transport = self._transport(role.provider)
            cap: dict = {}
            if max_budget_usd is not None:
                if not max_budget_usd > 0:
                    raise ModelUnavailable(f"{role.label()}: max_budget_usd must be positive", allow_fallback=False)
                if not getattr(transport, "stops_at_spend", False):
                    raise ModelUnavailable(f"{role.provider} cannot stop a call at a spend threshold",
                                           allow_fallback=False)
                cap = {"max_budget_usd": max_budget_usd}
            if (archive is not None or pacer is not None) and getattr(transport, "supports_native_events", False):
                cap["native_event_sink"] = event_sink
            if pacer is not None:
                if not getattr(transport, "supports_native_events", False):
                    raise ModelUnavailable("paced Zcode dispatch requires native error events", allow_fallback=False)
                from .depth_pacing import PacingStopped
                try:
                    pacing_ticket = pacer.acquire(event_sink)
                    if pacer.stop_file and pacer.stop_file.exists():
                        event_sink({"type": "native.throttle.stopped", "payload": {"at": time.time(), "before_dispatch": True}})
                        raise PacingStopped("campaign stop requested before Zcode dispatch")
                except PacingStopped as exc:
                    canceled = ModelUnavailable(str(exc), allow_fallback=False)
                    canceled.pre_dispatch_cancelled = True
                    raise canceled from exc
            reply = transport.complete(
                system=system, messages=[{"role": "user", "content": prompt}],
                model=role.model, effort=role.effort, role=role.name, **cap)
            if pacer is not None:
                pacer.finish(pacing_ticket, success=True, sink=event_sink)
        except BaseException as exc:  # preserve partial native events on interruption too
            snapshot = getattr(transport, "native_snapshot", None)
            partial = snapshot(native_events) if callable(snapshot) else {}
            reported_cost = (partial.get("usage") or {}).get("cost_usd")
            partial_cost = float(reported_cost) if isinstance(reported_cost, (int, float)) and not isinstance(reported_cost, bool) else None
            record_call({**identity, "served_model": partial.get("served_model", ""),
                                "stop_reason": "canceled_before_dispatch" if getattr(exc, "pre_dispatch_cancelled", False) else "", "usage": partial.get("usage") or {},
                                "cost_usd": partial_cost, "max_budget_usd": max_budget_usd,
                                "seconds": round(time.time() - started, 3),
                                **payload, "reply": partial.get("text", "") if record_payload else "",
                                "error": (str(exc) or type(exc).__name__)[:2000] if record_payload else "transport failed (payload omitted)"},
                        "canceled_before_dispatch" if getattr(exc, "pre_dispatch_cancelled", False)
                        else "failed" if isinstance(exc, Exception) else "interrupted")
            if not isinstance(exc, Exception):
                raise
            if isinstance(exc, ModelUnavailable):
                raise
            raise ModelUnavailable(f"{role.label()} failed: {exc}") from exc
        seconds = time.time() - started
        text = "".join(getattr(block, "text", "") or "" for block in getattr(reply, "blocks", []))
        usage = dict(getattr(reply, "usage", {}) or {})
        cost = usage.get("cost_usd")
        cost_usd = float(cost) if isinstance(cost, (int, float)) and not isinstance(cost, bool) else None
        record = {
            **identity,
            "served_model": getattr(reply, "model", "") or "",
            "stop_reason": getattr(reply, "stop_reason", ""),
            "usage": usage, "cost_usd": cost_usd, "max_budget_usd": max_budget_usd,
            "seconds": round(seconds, 3), "system": system if record_payload else "",
            "prompt": prompt if record_payload else "", "reply": text if record_payload else "",
        }
        # the record carries the call's FINAL verdict: a truncated, empty,
        # unparseable or schema-failing reply is recorded as a failure, so it
        # never becomes a training example
        failure: ModelUnavailable | None = None
        data: dict = {}
        if getattr(reply, "stop_reason", "") == "max_budget":
            failure = ModelUnavailable(f"{role.label()} stopped at its spend threshold ${max_budget_usd}",
                                       allow_fallback=False)
        elif getattr(reply, "stop_reason", "") == "max_tokens" or not text.strip():
            failure = ModelUnavailable(f"{role.label()} timed out or returned nothing")
        else:
            try:
                data = parse_json_object(text)
                if validate is not None:
                    try:
                        validate(data)
                    except Exception as exc:  # any malformed shape is a controlled refusal
                        raise ModelUnavailable(f"{role.label()} reply failed its schema: {exc!r}",
                                               allow_fallback=False) from exc
            except ModelUnavailable as exc:
                failure = exc
            except BaseException as exc:
                # A native response may already have returned when the caller
                # interrupts validation. Preserve that response and its usage.
                record_call({**record, "error": (str(exc) or type(exc).__name__)[:2000]},
                            "failed" if isinstance(exc, Exception) else "interrupted")
                raise
        receipt = record_call({**record, "error": str(failure) if failure else ""},
                              "failed" if failure else "complete")
        if failure is not None:
            raise failure
        receipt = receipt if isinstance(receipt, dict) else {}
        return ModelReply(role, data, text, record["served_model"], usage, seconds, cost_usd,
                          receipt.get("id", ""), receipt.get("outputs", {}).get("reply", "").removeprefix("sha256:"))

    def subscription_billing(self, role: ModelRole) -> bool:
        """Bind the authenticated subscription backend to the next dispatch."""
        self._subscription_transports.pop(role.label(), None)
        transport = self._transport(role.provider)
        if getattr(transport, "subscription_billing", False) is not True:
            return False
        self._subscription_transports[role.label()] = transport
        return True
