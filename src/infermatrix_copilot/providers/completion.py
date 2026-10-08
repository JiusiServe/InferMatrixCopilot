"""One native completion, including partial events and its final receipt.

Callers supply reply validation and policy errors; this layer does not know
knowledge schemas, model roles, budgets, or application runtimes.
"""

from __future__ import annotations

import time

from ..budgeting import call_budget


def complete_native(
    transport_factory, *, request: dict, identity: dict | None = None,
    payload: dict | None = None, recorder=None, validate=None,
    record_payload=True, pacer=None, stop_file=None,
    cancelled_errors=(), passthrough_errors=(), make_error=None,
    capture=False,
):
    """Return ``(reply, validated_value, record, receipt)`` without retrying.

    The receipt is finalized once, after validation. Unknown native usage is
    retained on failures and interruption. A stop threshold is accepted only
    from a transport that attests it; it never becomes a token approximation.
    """
    with call_budget({**request, "kind": "harness",
                      "provider_id": (identity or {}).get("provider", "")}) as budget:
        started = time.time()
        capture_started = time.monotonic()
        identity = dict(identity or {})
        payload = dict(payload if payload is not None else
                       {k: request[k] for k in ("system", "messages") if k in request})
        if not record_payload:
            payload = {key: "" for key in payload}
        begin = getattr(recorder, "begin_call", None)
        archive = begin({**identity, **payload}) if callable(begin) else None
        native_events, transport, ticket = [], None, None
        label = identity.get("requested") or request.get("model") or identity.get("provider", "native")
        threshold = request.get("max_budget_usd")

        def failure(message, allow_fallback=False):
            return make_error(message, allow_fallback) if make_error else RuntimeError(message)

        def canceled(message):
            error = failure(message)
            error.pre_dispatch_cancelled = True
            return error

        def event_sink(event):
            native_events.append(event)
            if archive is not None and record_payload:
                archive.event(event)
            if pacer is not None and ticket is not None:
                pacer.observe(ticket, event, event_sink)

        reply, value, error, native_complete = None, None, None, False
        try:
            if stop_file and stop_file.exists():
                event_sink({"type": "native.throttle.stopped", "payload": {"at": time.time(), "before_dispatch": True}})
                raise canceled("campaign stop requested before native dispatch")
            transport = transport_factory()
            kwargs = dict(request)
            if threshold is not None:
                if not threshold > 0:
                    raise failure(f"{label}: max_budget_usd must be positive")
                if not getattr(transport, "stops_at_spend", False):
                    raise failure(f"{identity.get('provider', '')} cannot stop a call at a spend threshold")
            if (archive is not None or pacer is not None) and getattr(transport, "supports_native_events", False):
                kwargs["native_event_sink"] = event_sink
            if pacer is not None:
                if not getattr(transport, "supports_native_events", False):
                    raise failure("paced Zcode dispatch requires native error events")
                try:
                    ticket = pacer.acquire(event_sink)
                except cancelled_errors as exc:
                    raise canceled(str(exc)) from exc
                if pacer.stop_file and pacer.stop_file.exists():
                    event_sink({"type": "native.throttle.stopped", "payload": {"at": time.time(), "before_dispatch": True}})
                    raise canceled("campaign stop requested before Zcode dispatch")
            budget["sent"] = True
            reply = transport.complete(**kwargs)
            if pacer is not None:
                pacer.finish(ticket, success=True, sink=event_sink)
            native_complete = True
            seconds = time.time() - started
            value = validate(reply) if validate is not None else None
        except BaseException as exc:
            error = exc

        if native_complete:
            text = "".join(getattr(block, "text", "") or "" for block in getattr(reply, "blocks", []))
            budget.update(reply=reply, usage=getattr(reply, "usage", None))
            usage = dict(getattr(reply, "usage", {}) or {})
            served_model, stop_reason = getattr(reply, "model", "") or "", getattr(reply, "stop_reason", "")
        else:
            snapshot = getattr(transport, "native_snapshot", None)
            partial = snapshot(native_events) if callable(snapshot) else {}
            text, usage = partial.get("text", ""), partial.get("usage") or {}
            budget["usage"] = partial.get("usage")
            served_model = partial.get("served_model", "")
            stop_reason = "canceled_before_dispatch" if getattr(error, "pre_dispatch_cancelled", False) else ""
            seconds = round(time.time() - started, 3)
        budget["outcome"] = "completed" if error is None else "failed"
        reported = usage.get("cost_usd")
        record = {**identity, "served_model": served_model, "stop_reason": stop_reason, "usage": usage,
                  "cost_usd": float(reported) if isinstance(reported, (int, float)) and not isinstance(reported, bool) else None,
                  "max_budget_usd": threshold, "seconds": seconds,
                  **payload, "reply": text if record_payload else ""}
        error_text = (str(error) or type(error).__name__) if error is not None else ""
        entry = {**record, "seconds": round(seconds, 3),
                 "error": error_text if native_complete else error_text[:2000] if record_payload else "transport failed (payload omitted)"}
        if archive is not None:
            entry.update(archive.payload())
        receipt = recorder(entry) if recorder else None
        receipt = receipt if isinstance(receipt, dict) else {}
        if archive is not None:
            status = "complete" if error is None else "canceled_before_dispatch" if getattr(error, "pre_dispatch_cancelled", False) \
                else "failed" if isinstance(error, Exception) else "interrupted"
            archive.finish(receipt, entry, status=status)
        if capture:
            from ..llm import capture_model_call
            options = capture if isinstance(capture, dict) else {}
            capture_model_call({**request, "tools": []}, request.get("role", ""),
                               options.get("provider", f"harness:{identity.get('provider', '')}"),
                               reply if native_complete else None,
                               time.monotonic() - capture_started, error=error_text,
                               extra_result=options.get("extra_result"))
        if error is not None:
            if native_complete or not isinstance(error, Exception) or isinstance(error, passthrough_errors) or make_error is None:
                raise error
            raise failure(f"{label} failed: {error}", True) from error
        return reply, value, record, receipt
