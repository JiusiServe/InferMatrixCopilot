"""Synthetic offline evidence: no native model calls or live campaign mutation."""
import importlib.util
import json
from pathlib import Path

import pytest


PATH = Path(__file__).resolve().parents[1] / "eval/jiuwenswarm_ab_diagnostics.py"
SPEC = importlib.util.spec_from_file_location("ab_diagnostics", PATH)
diag = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(diag)


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n")


def _lines(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


def _root(tmp_path):
    root = tmp_path / "study"
    _write(root / "identity.json", {"identity_sha256": "identity", "campaign_sha256": "campaign"})
    return root


def _review(root, pr=1, arm="A", repeat=1, intervals=((10, 30),), events=(), violation=None, covered=True, status="valid", error=""):
    item = root / f"items/review-pr{pr}-{arm}-r{repeat}"
    attempts = []
    for ordinal, (started, finished) in enumerate(intervals, 1):
        a = item / f"attempt-{ordinal}"
        a.mkdir(parents=True)
        (a / "prompt.txt").write_text("review prompt")
        _write(a / "bridge-spec.json", {"case": {"sources": {"tests/nested/test_core.py": "unused"}}})
        _write(a / "tool-state.json", {"source_calls": 20 * ordinal, "knowledge_chars": 5990 + ordinal,
            "prompt_ranges": [[0, 13 if covered else 5]], "violations": [violation] if violation else []})
        bridge = []
        if violation:
            body = json.dumps({"error": violation["error"]})
            bridge.append({**violation, "args": {"path": violation.get("path", "tests/")},
                           "result": body, "result_sha256": diag._sha(body.encode())})
        _lines(a / "bridge-events.jsonl", bridge)
        journal = a / "traces/attempts/native/native-events.jsonl"
        _lines(journal, [{"type": "native.throttle.started", "payload": {"at": started}}, *events])
        _write(journal.parent / "attempt.json", {"finished_at": finished, "trace_id": f"receipt{ordinal}",
            "native_events_sha256": "sha256:" + diag._sha(journal.read_bytes()), "status": status})
        files = {p.relative_to(a).as_posix(): diag._sha(p.read_bytes()) for p in a.rglob("*") if p.is_file()}
        attempts.append({"ordinal": ordinal, "attempt_root": str(a), "status": status,
                         "native_trace_id": f"receipt{ordinal}", "artifacts": files})
    _write(item / "result.json", {"number": pr, "arm": arm, "repetition": repeat, "status": status,
        "preflight": False, "identity_sha256": "identity", "campaign_sha256": "campaign", "attempts": attempts, "error": error})
    return item


def _bind(root, item):
    path = item / "result.json"
    result = json.loads(path.read_text())
    _write(root / "reviews-manifest.json", {"schema": "jiuwenswarm-pr-reviews-v1", "identity_sha256": "identity", "campaign_sha256": "campaign",
        "reviews": [{"pr": result["number"], "arm": result["arm"], "repeat": result["repetition"] - 1,
            "run_result_path": str(path), "run_result_sha256": diag._sha(path.read_bytes()),
            "native_status": result["status"], "status": "complete" if result["status"] == "valid" else "failed",
            "identity_sha256": "identity", "campaign_sha256": "campaign"}]})


def _rate(request="r1", delay=3000):
    error = {"type": "session.updated", "eventId": "error" + request,
             "payload": {"errorCode": "model_rate_limited", "statusCode": 429, "errorPhase": "stream",
                         "providerRequestId": request, "attempt": 1, "maxAttempts": 11}}
    retry = {"type": "session.updated", "eventId": "retry" + request,
             "payload": {"errorCode": "model_rate_limited", "statusCode": 429, "requestId": request,
                         "attempt": 1, "nextAttempt": 2, "maxAttempts": 11, "delayMs": delay}}
    return error, retry


def test_duplicates_and_stderr_do_not_multiply_provider_requests_or_cli_attempts(tmp_path):
    root = _root(tmp_path)
    error, retry = _rate()
    _review(root, events=[error, error, retry, retry,
        {"type": "native.stderr", "text": "responseStatus: 429"},
        {"type": "native.throttle.cooldown", "payload": {"cause": "native_429_or_account_1302"}}])
    # Bootstrap calls must never contribute to formal review diagnostics.
    _write(root / "items/preflight-pr1-A-r0/result.json", {"attempts": ["unrelated"]})
    report = diag.diagnose_run(root)
    arm = report["by_arm"]["A"]
    assert arm["native_cli_attempts"] == 1
    assert arm["rate_limits"]["affected_reviews_observed"] == 1
    assert arm["rate_limits"]["provider_429_notifications_observed"] == 1
    assert arm["rate_limits"]["duplicate_429_notifications_ignored"] == 1
    assert arm["rate_limits"]["internal_retry_schedules_observed"] == 1
    assert arm["rate_limits"]["requested_retry_delay_ms_observed_sum"] == 3000
    assert arm["rate_limits"]["max_attempts_observed"] == [11]
    assert arm["rate_limits"]["highest_requested_attempt"] == 2
    assert arm["attempt_integrity_counts"] == {"verified": 1}


def test_cumulative_counts_are_not_added_across_native_transport_retry(tmp_path):
    root = _root(tmp_path)
    _review(root, intervals=((10, 20), (25, 35)))
    row = diag.diagnose_run(root)["reviews"][0]
    assert row["native_cli_attempts"] == 2
    assert row["source_calls_cumulative"] == 40
    assert row["knowledge_chars_cumulative"] == 5992


def test_active_peak_uses_completed_native_intervals_and_excludes_queue(tmp_path):
    root = _root(tmp_path)
    _review(root, pr=1, intervals=((10, 30),))
    _review(root, pr=2, arm="B", intervals=((20, 40),))
    _review(root, pr=3, intervals=((40, 50),))
    report = diag.diagnose_run(root)
    timing = report["native_timing"]
    assert timing["native_active_peak_completed_intervals"] == 2
    assert timing["batch_native_span_seconds"] == 40
    assert timing["peak_is_lower_bound"] is False
    pending = root / "items/review-pr4-A-r1"
    pending.mkdir()
    report = diag.diagnose_run(root)
    assert report["native_timing"]["peak_is_lower_bound"] is True
    assert report["incomplete_items"] == [pending.name]


@pytest.mark.parametrize("path,reason", [("tests/", "directory_trailing_slash_protocol_rejection"),
    ("../private.py", "frozen_scope_violation"), ("missing-dir/", "unknown_bridge_protocol")])
def test_invalid_scope_classification_requires_proven_directory(tmp_path, path, reason):
    root = _root(tmp_path)
    _review(root, status="invalid_run", violation={"tool": "source_grep", "error": "path must be repository-relative without traversal", "path": path})
    assert diag.diagnose_run(root)["reviews"][0]["invalid_run_reasons"] == [reason]


def test_incomplete_prompt_and_native_bypass_are_separate_proven_failures(tmp_path):
    root = _root(tmp_path)
    _review(root, status="invalid_run", covered=False,
            events=[{"type": "tool.updated", "payload": {"kind": "completed", "toolName": "Read"}}])
    reasons = diag.diagnose_run(root)["reviews"][0]["invalid_run_reasons"]
    assert reasons == ["incomplete_prompt", "native_tool_bypass_attempt"]


def test_missing_trace_is_unknown_instead_of_verified_no_rate_limits(tmp_path):
    root = _root(tmp_path)
    item = _review(root)
    (item / "attempt-1/traces/attempts/native/native-events.jsonl").unlink()
    report = diag.diagnose_run(root)
    arm = report["by_arm"]["A"]
    assert arm["rate_limits"]["complete_trace_reviews"] == 0
    assert arm["rate_limits"]["unknown_trace_reviews"] == 1
    assert report["native_timing"]["native_active_peak_completed_intervals"] is None


def test_changed_journal_rejects_receipt_and_file_hash_not_hiding_partial_tail(tmp_path):
    root = _root(tmp_path)
    item = _review(root)
    journal = item / "attempt-1/traces/attempts/native/native-events.jsonl"
    journal.write_bytes(journal.read_bytes() + b'{"partial":')
    report = diag.diagnose_run(root)
    attempt = report["reviews"][0]["attempts"][0]
    assert attempt["integrity"] == "mismatch"
    assert "native_receipt_event_hash_mismatch" in attempt["issues"]
    assert "native:partial_jsonl_tail" in attempt["issues"]
    assert attempt["rate_limits"] is None
    assert attempt["source_calls_cumulative"] is None


def test_missing_requested_delay_stays_unknown(tmp_path):
    root = _root(tmp_path)
    error, retry = _rate()
    del retry["payload"]["delayMs"]
    _review(root, events=[error, retry])
    rate = diag.diagnose_run(root)["by_arm"]["A"]["rate_limits"]
    assert rate["requested_retry_delay_ms_observed_sum"] is None
    assert rate["requested_retry_delay_unknown_events"] == 1


def test_stderr_only_429_is_not_verified_as_no_rate_limit(tmp_path):
    root = _root(tmp_path)
    _review(root, events=[{"type": "native.stderr", "text": "responseStatus: 429,"}])
    rates = diag.diagnose_run(root)["by_arm"]["A"]["rate_limits"]
    assert rates["affected_reviews_observed"] == 1
    assert rates["provider_429_notifications_observed"] == 0  # no unique request IDs
    assert rates["unknown_trace_reviews"] == 1


def test_native_receipt_digest_is_checked_independently_of_artifact_digest(tmp_path):
    root = _root(tmp_path)
    item = _review(root)
    journal = item / "attempt-1/traces/attempts/native/native-events.jsonl"
    with journal.open("a") as handle:
        handle.write(json.dumps({"type": "session.updated", "payload": {"status": "added"}}) + "\n")
    result_path = item / "result.json"
    result = json.loads(result_path.read_text())
    result["attempts"][0]["artifacts"][journal.relative_to(item / "attempt-1").as_posix()] = diag._sha(journal.read_bytes())
    _write(result_path, result)
    attempt = diag.diagnose_run(root)["reviews"][0]["attempts"][0]
    assert attempt["integrity"] == "mismatch"
    assert attempt["issues"] == ["native_receipt_event_hash_mismatch"]


def test_unavailable_receipt_digest_stays_unknown_even_with_artifact_hash(tmp_path):
    root = _root(tmp_path)
    item = _review(root)
    meta = item / "attempt-1/traces/attempts/native/attempt.json"
    value = json.loads(meta.read_text())
    del value["native_events_sha256"]
    _write(meta, value)
    result_path = item / "result.json"
    result = json.loads(result_path.read_text())
    result["attempts"][0]["artifacts"][meta.relative_to(item / "attempt-1").as_posix()] = diag._sha(meta.read_bytes())
    _write(result_path, result)
    report = diag.diagnose_run(root)
    assert report["reviews"][0]["attempts"][0]["integrity"] == "unknown"
    assert report["by_arm"]["A"]["rate_limits"]["unknown_trace_reviews"] == 1


def test_unknown_invalid_run_is_not_claimed_to_be_scope_escape(tmp_path):
    root = _root(tmp_path)
    _review(root, status="invalid_run")
    assert diag.diagnose_run(root)["reviews"][0]["invalid_run_reasons"] == ["unknown"]


@pytest.mark.parametrize("error,expected", [
    ("model output does not satisfy successful review contract", "output_schema_or_contract_rejected"),
    ("review comment has missing required fields", "output_schema_or_contract_rejected"),
    ("review comment line is invalid", "output_schema_or_contract_rejected"),
    ("review comment severity/disposition is invalid", "output_schema_or_contract_rejected"),
    ("review comment text must be a string", "output_schema_or_contract_rejected"),
    ("this read-only harness cannot execute tests", "output_schema_or_contract_rejected"),
    ("review comment has missing required fields: file", "output_schema_or_contract_rejected"),
    ("review comment has missing required fields possibly", "unknown"),
    ("unrecognized failure", "unknown")])
def test_canonical_output_contract_failures_require_bound_verified_evidence(tmp_path, error, expected):
    root = _root(tmp_path)
    item = _review(root, status="invalid_run", error=error)
    _bind(root, item)
    row = diag.diagnose_run(root)["reviews"][0]
    assert row["result_manifest_binding_verified"] is True
    assert row["invalid_run_reasons"] == [expected]


@pytest.mark.parametrize("fault", ["missing_binding", "wrong_result_hash", "missing_trace"])
def test_canonical_error_without_verified_binding_or_trace_remains_unknown(tmp_path, fault):
    root = _root(tmp_path)
    item = _review(root, status="invalid_run", error="review comment has missing required fields")
    if fault != "missing_binding":
        _bind(root, item)
    if fault == "wrong_result_hash":
        manifest = json.loads((root / "reviews-manifest.json").read_text())
        manifest["reviews"][0]["run_result_sha256"] = "0" * 64
        _write(root / "reviews-manifest.json", manifest)
    elif fault == "missing_trace":
        (item / "attempt-1/traces/attempts/native/native-events.jsonl").unlink()
    assert diag.diagnose_run(root)["reviews"][0]["invalid_run_reasons"] == ["unknown"]
