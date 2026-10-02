"""Read-only diagnostics for the frozen JiuwenSwarm GLM PR-review campaign.

Usage: python eval/jiuwenswarm_ab_diagnostics.py RUN_ROOT
Provider request retries are distinct from native CLI attempts. Requested retry
delays are not measured elapsed time. Partial or missing journals remain unknown.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import statistics


SCHEMA = "jiuwenswarm-pr-ab-diagnostics-v1"
TOOLS = {"read_prompt", "source_read", "source_grep", "source_list", "file_at_base", "calc", "doc_search", "doc_read"}
PREFIX = "mcp__jiuwenswarm-ab__"


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _json(path):
    return json.loads(Path(path).read_bytes())


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _distribution(values):
    values = sorted(v for v in values if _number(v))
    return {"known_reviews": len(values), "min": values[0] if values else None,
            "max": values[-1] if values else None, "p50": statistics.median(values) if values else None}


def _jsonl(data, *, keep_types=None):
    rows, errors = [], []
    for ordinal, line in enumerate(data.splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError("JSONL entry must be an object")
            if keep_types is None or row.get("type") in keep_types:
                rows.append(row)
        except (ValueError, UnicodeError):
            errors.append(f"invalid_jsonl_line:{ordinal}")
    if data and not data.endswith(b"\n"):
        errors.append("partial_jsonl_tail")
    return rows, errors


def _event_key(event, *, retry=False):
    payload = event.get("payload", {})
    if not retry and payload.get("providerRequestId"):
        return ("provider_request", str(payload["providerRequestId"]))
    if payload.get("requestId"):
        return ("request", str(payload["requestId"]), payload.get("nextAttempt") if retry else payload.get("attempt"))
    if event.get("eventId"):
        return ("event", str(event["eventId"]))
    # Exact repeated payloads are duplicate notifications; retain distinct
    # attempts/timestamps/logical calls when the provider gives no request ID.
    return ("payload", _sha(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()))


def _rate_limits(events):
    errors, retries, duplicate_errors, duplicate_retries = {}, {}, 0, 0
    unstructured = any(e.get("type") == "native.stderr" and re.search(r"responseStatus:\s*429\b", str(e.get("text", ""))) for e in events)
    for event in events:
        payload = event.get("payload")
        if event.get("type") != "session.updated" or not isinstance(payload, dict):
            continue
        if payload.get("errorCode") != "model_rate_limited" or payload.get("statusCode") != 429:
            continue
        if "errorPhase" in payload or payload.get("type") == "model_request_failed":
            key = _event_key(event)
            duplicate_errors += int(key in errors)
            errors.setdefault(key, payload)
        if "nextAttempt" in payload:
            key = _event_key(event, retry=True)
            duplicate_retries += int(key in retries)
            retries.setdefault(key, payload)
    payloads = list(errors.values()) + list(retries.values())
    delays = [p["delayMs"] for p in retries.values() if _number(p.get("delayMs")) and p["delayMs"] >= 0]
    return {"provider_429_notifications_observed": len(errors), "duplicate_429_notifications_ignored": duplicate_errors,
            "unstructured_429_evidence_observed": unstructured,
            "internal_retry_schedules_observed": len(retries), "duplicate_retry_schedules_ignored": duplicate_retries,
            "requested_retry_delay_ms": sum(delays) if len(delays) == len(retries) else None,
            "requested_retry_delay_ms_known_subtotal": sum(delays) if delays or not retries else None,
            "requested_retry_delay_known_events": len(delays), "requested_retry_delay_unknown_events": len(retries) - len(delays),
            "max_attempts_observed": sorted({p["maxAttempts"] for p in payloads if isinstance(p.get("maxAttempts"), int) and not isinstance(p["maxAttempts"], bool)}),
            "highest_requested_attempt": max([p["nextAttempt"] for p in retries.values() if isinstance(p.get("nextAttempt"), int) and not isinstance(p["nextAttempt"], bool)], default=None)}


def _native_tools(events):
    calls, bypasses, unknown = set(), set(), False
    for event in events:
        payload = event.get("payload")
        if event.get("type") != "tool.updated" or not isinstance(payload, dict):
            continue
        name = payload.get("toolName")
        if name:
            if name not in {PREFIX + tool for tool in TOOLS}:
                bypasses.add(str(name))
            elif isinstance(payload.get("toolCallId"), str):
                calls.add(payload["toolCallId"])
        elif payload.get("kind") in {"result", "completed"} and payload.get("toolCallId") in calls:
            continue
        elif payload.get("kind") == "batch" and isinstance(payload.get("toolCallIds"), list) and all(call in calls for call in payload["toolCallIds"]):
            continue
        else:
            unknown = True
    return sorted(bypasses), unknown


def _prompt_covered(state, size):
    end = 0
    try:
        for lo, hi in sorted(state["prompt_ranges"]):
            if not isinstance(lo, int) or not isinstance(hi, int) or isinstance(lo, bool) or isinstance(hi, bool) or lo < 0 or lo > end or hi < lo or hi > size:
                return False
            end = max(end, hi)
        return end >= size
    except (KeyError, TypeError, ValueError):
        return None


def _canonical_relative(path):
    return isinstance(path, str) and bool(path) and not path.startswith("/") and "\\" not in path and all(part not in {"", ".", "..", ".git"} for part in path.split("/"))


def _invalid_reasons(result, attempts):
    if result.get("status") != "invalid_run":
        return []
    reasons = set()
    for attempt in attempts:
        if attempt["integrity"] == "mismatch":
            continue
        if attempt["native_tool_names_rejected"]:
            reasons.add("native_tool_bypass_attempt")
        if attempt["unknown_native_tool_protocol"]:
            reasons.add("unknown_native_tool_protocol")
        if attempt.get("prompt_covered") is False:
            reasons.add("incomplete_prompt")
        for violation in attempt.get("bridge_violations", []):
            tool, error = violation.get("tool"), violation.get("error", "")
            matches = [e for e in attempt.get("bridge_errors", []) if e.get("tool") == tool and e.get("error") == error]
            if "unknown bridge tool" in error:
                reasons.add("unknown_bridge_tool")
            elif "changed" in error:
                reasons.add("frozen_input_changed")
            else:
                classified = False
                for match in matches:
                    path = match.get("args", {}).get("path")
                    stripped = path.rstrip("/") if isinstance(path, str) else None
                    sources = attempt.get("source_paths", [])
                    if tool == "source_grep" and isinstance(path, str) and path.endswith("/") and _canonical_relative(stripped) and any(p.startswith(stripped + "/") for p in sources):
                        reasons.add("directory_trailing_slash_protocol_rejection")
                        classified = True
                    elif isinstance(path, str) and (path.startswith("/") or ".." in PurePosixPath(path).parts or ".git" in PurePosixPath(path).parts):
                        reasons.add("frozen_scope_violation")
                        classified = True
                if not classified and any(text in error for text in ("outside frozen", "document/source scope", "source tools cannot read documentation")):
                    reasons.add("frozen_scope_violation")
                elif not classified:
                    reasons.add("unknown_bridge_protocol")
    return sorted(reasons) if reasons else ["unknown"]


def _attempt_diagnostics(attempt):
    root = Path(attempt["attempt_root"])
    issues, mismatches = [], []
    expected = attempt.get("artifacts", {})

    def read(path, *, required=True):
        try:
            data = path.read_bytes()
        except OSError:
            if required:
                issues.append("missing_file:" + path.relative_to(root).as_posix())
            return None
        key = path.relative_to(root).as_posix()
        if key in expected and _sha(data) != expected[key]:
            mismatches.append("file_hash_mismatch:" + key)
        elif key not in expected:
            issues.append("file_hash_unavailable:" + key)
        return data

    def read_object(path, *, required=True):
        data = read(path, required=required)
        if data is None:
            return None
        try:
            obj = json.loads(data)
            if not isinstance(obj, dict):
                raise ValueError()
            return obj
        except ValueError:
            issues.append("invalid_json:" + path.relative_to(root).as_posix())
            return None

    state = read_object(root / "tool-state.json")
    spec = read_object(root / "bridge-spec.json")
    prompt_data = read(root / "prompt.txt")
    bridge_data = read(root / "bridge-events.jsonl")
    bridge, bridge_issues = _jsonl(bridge_data) if bridge_data is not None else ([], [])
    issues += ["bridge:" + issue for issue in bridge_issues]
    for event in bridge:
        if not isinstance(event.get("result"), str) or _sha(event["result"].encode()) != event.get("result_sha256"):
            mismatches.append("bridge_result_hash_mismatch")
    journals = sorted((root / "traces/attempts").glob("*/native-events.jsonl"))
    events, native_metadata = [], []
    if len(journals) != 1:
        issues.append("native_journal_count:" + str(len(journals)))
    for path in journals:
        data = read(path)
        if data is None:
            continue
        parsed, parse_issues = _jsonl(data, keep_types={"session.updated", "tool.updated", "native.throttle.started", "native.stderr"})
        issues += ["native:" + issue for issue in parse_issues]
        meta = read_object(path.parent / "attempt.json")
        if meta:
            native_metadata.append(meta)
            receipt_hash = meta.get("native_events_sha256")
            if receipt_hash:
                if not isinstance(receipt_hash, str) or _sha(data) != receipt_hash.removeprefix("sha256:"):
                    mismatches.append("native_receipt_event_hash_mismatch")
            else:
                issues.append("native_receipt_event_hash_unavailable")
            if meta.get("trace_id") != attempt.get("native_trace_id"):
                mismatches.append("native_receipt_id_mismatch")
            if not _number(meta.get("finished_at")):
                issues.append("native_receipt_unfinished")
        events += parsed
    integrity = "mismatch" if mismatches else "unknown" if issues else "verified"
    bypasses, unknown_tools = _native_tools(events)
    starts = [e["payload"]["at"] for e in events if e.get("type") == "native.throttle.started" and isinstance(e.get("payload"), dict) and _number(e["payload"].get("at"))]
    finishes = [m["finished_at"] for m in native_metadata if _number(m.get("finished_at"))]
    interval = [starts[0], finishes[0]] if len(starts) == len(finishes) == 1 and finishes[0] >= starts[0] and integrity != "mismatch" else None
    try:
        prompt_size = len(prompt_data.decode()) if prompt_data is not None else None
    except UnicodeError:
        prompt_size = None
    rates = _rate_limits(events) if integrity != "mismatch" else None
    return {"ordinal": attempt.get("ordinal"), "status": attempt.get("status"), "integrity": integrity,
            "issues": sorted(set(issues + mismatches)), "native_started": bool(starts) if integrity != "mismatch" else None,
            "native_interval": interval, "rate_limits": rates,
            "rate_limit_trace_complete": integrity == "verified" and not (rates["unstructured_429_evidence_observed"] and not rates["provider_429_notifications_observed"]),
            "native_tool_names_rejected": bypasses,
            "unknown_native_tool_protocol": unknown_tools,
            "source_calls_cumulative": state.get("source_calls") if state and integrity != "mismatch" else None,
            "knowledge_chars_cumulative": state.get("knowledge_chars") if state and integrity != "mismatch" else None,
            "prompt_covered": _prompt_covered(state, prompt_size) if state is not None and prompt_size is not None else None,
            "bridge_violations": state.get("violations", []) if state else [],
            "bridge_errors": [e for e in bridge if e.get("error")],
            "source_paths": list(spec.get("case", {}).get("sources", {})) if spec else []}


def _timing(attempts):
    intervals = [a["native_interval"] for a in attempts if a["native_interval"] is not None]
    events = [(lo, 1) for lo, _ in intervals] + [(hi, -1) for _, hi in intervals]
    active = peak = 0
    for _, delta in sorted(events):
        active += delta
        peak = max(peak, active)
    missing = len(attempts) - len(intervals)
    return {"completed_native_intervals": len(intervals), "unknown_attempt_intervals": missing,
            "native_active_peak_completed_intervals": peak if intervals else None,
            "peak_is_lower_bound": bool(missing) or any(a["integrity"] != "verified" for a in attempts),
            "first_native_started_at": min(lo for lo, _ in intervals) if intervals else None,
            "last_native_finished_at": max(hi for _, hi in intervals) if intervals else None,
            "batch_native_span_seconds": max(hi for _, hi in intervals) - min(lo for lo, _ in intervals) if intervals else None,
            "clock_basis": "native.throttle.started.at to finalized native-attempt.finished_at"}


def diagnose_run(run_root):
    """Return compact diagnostics without creating files or invoking models."""
    root = Path(run_root).resolve()
    identity = _json(root / "identity.json")
    reviews, incomplete, read_errors, all_attempts = [], [], [], []
    for item in sorted((root / "items").glob("review-*")):
        path = item / "result.json"
        if not path.exists():
            incomplete.append(item.name)
            continue
        try:
            result = _json(path)
            slot = re.fullmatch(r"review-pr(\d+)-([AB])-r([123])", item.name)
            if not slot or result.get("preflight") or result.get("number") != int(slot[1]) or result.get("arm") != slot[2] or result.get("repetition") != int(slot[3]):
                raise ValueError("result_slot_mismatch")
            if result.get("identity_sha256") != identity.get("identity_sha256") or result.get("campaign_sha256") != identity.get("campaign_sha256"):
                raise ValueError("result_campaign_mismatch")
            attempts = []
            for native in result["attempts"]:
                if not Path(native["attempt_root"]).resolve().is_relative_to(item.resolve()):
                    raise ValueError("attempt_root_outside_item")
                attempts.append(_attempt_diagnostics(native))
            all_attempts += attempts
            final = attempts[-1] if attempts else {}
            row = {"pr": result["number"], "arm": result["arm"], "repeat": result["repetition"] - 1,
                   "status": result["status"], "native_cli_attempts": len(attempts),
                   "source_calls_cumulative": final.get("source_calls_cumulative"),
                   "knowledge_chars_cumulative": final.get("knowledge_chars_cumulative"),
                   "invalid_run_reasons": _invalid_reasons(result, attempts), "attempts": attempts}
            reviews.append(row)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            read_errors.append({"item": item.name, "error": type(exc).__name__ + ":" + str(exc)[:160]})
    by_arm = {}
    for arm in ("A", "B"):
        selected = [r for r in reviews if r["arm"] == arm]
        attempts = [a for r in selected for a in r["attempts"]]
        rates = [a["rate_limits"] for a in attempts if a["rate_limits"] is not None]
        known = [r for r in selected if r["attempts"] and all(a["rate_limit_trace_complete"] for a in r["attempts"])]
        affected = [r for r in selected if any(a["rate_limits"] and (a["rate_limits"]["provider_429_notifications_observed"] or a["rate_limits"]["unstructured_429_evidence_observed"]) for a in r["attempts"])]
        max_attempts = sorted({v for rate in rates for v in rate["max_attempts_observed"]})
        by_arm[arm] = {"completed_reviews": len(selected), "valid_reviews": sum(r["status"] == "valid" for r in selected),
            "status_counts": dict(Counter(r["status"] for r in selected)),
            "native_cli_attempts": len(attempts), "native_launched_attempts_observed": sum(a["native_started"] is True for a in attempts),
            "attempt_integrity_counts": dict(Counter(a["integrity"] for a in attempts)),
            "rate_limits": {"affected_reviews_observed": len(affected), "complete_trace_reviews": len(known),
                "unknown_trace_reviews": len(selected) - len(known),
                "provider_429_notifications_observed": sum(r["provider_429_notifications_observed"] for r in rates),
                "duplicate_429_notifications_ignored": sum(r["duplicate_429_notifications_ignored"] for r in rates),
                "internal_retry_schedules_observed": sum(r["internal_retry_schedules_observed"] for r in rates),
                "requested_retry_delay_ms_observed_sum": sum(r["requested_retry_delay_ms_known_subtotal"] for r in rates if r["requested_retry_delay_ms_known_subtotal"] is not None) if any(r["requested_retry_delay_ms_known_subtotal"] is not None for r in rates) else None,
                "requested_retry_delay_unknown_events": sum(r["requested_retry_delay_unknown_events"] for r in rates),
                "max_attempts_observed": max_attempts,
                "highest_requested_attempt": max((r["highest_requested_attempt"] for r in rates if r["highest_requested_attempt"] is not None), default=None)},
            "source_calls_cumulative": _distribution([r["source_calls_cumulative"] for r in selected]),
            "knowledge_chars_cumulative": _distribution([r["knowledge_chars_cumulative"] for r in selected]),
            "invalid_run_reason_counts": dict(Counter(reason for r in selected for reason in r["invalid_run_reasons"])),
            "native_timing": _timing(attempts)}
        by_arm[arm]["pending_items"] = sum(bool(re.fullmatch(r"review-pr\d+-" + arm + r"-r[123]", item)) for item in incomplete)
        if by_arm[arm]["pending_items"] or read_errors:
            by_arm[arm]["native_timing"]["peak_is_lower_bound"] = True
    # Keep details compact: do not echo source inventories, prompts, comments,
    # provider headers, or complete bridge responses into the report.
    for review in reviews:
        for attempt in review["attempts"]:
            for key in ("source_paths", "bridge_errors", "bridge_violations"):
                attempt.pop(key, None)
    timing = _timing(all_attempts)
    if incomplete or read_errors:
        timing["peak_is_lower_bound"] = True
    return {"schema": SCHEMA, "identity_sha256": identity.get("identity_sha256"), "campaign_sha256": identity.get("campaign_sha256"),
            "completed_reviews": len(reviews), "incomplete_items": incomplete, "unreadable_results": read_errors,
            "by_arm": by_arm, "native_timing": timing, "reviews": reviews,
            "limitations": ["Native CLI attempts are not provider HTTP-request retry counts.",
                            "Requested retry delays are not measured backoff wall time.",
                            "Missing/partial/unbound journals remain unknown; observed counts may be lower bounds."]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_root", type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(diagnose_run(args.run_root), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
