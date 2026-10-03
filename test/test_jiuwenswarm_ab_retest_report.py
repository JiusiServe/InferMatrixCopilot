"""Retests preserve frozen denominators, truth, input bytes and failed outcomes."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from eval import jiuwenswarm_ab_retest_report as report
from eval.jiuwenswarm_ab_judge import review_metrics
from eval.jiuwenswarm_ab_report import binding


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True))
    return path


@pytest.fixture
def studies(tmp_path):
    values = []
    reference = tmp_path / "previous-report.md"
    reference.write_text("previous report")
    inventory = write(tmp_path / "inventory.json", {"fixed": True})
    for tag in ("previous", "retest"):
        root = tmp_path / tag / "evaluation-v2"
        root.mkdir(parents=True)
        campaign = {"run_root": str(root), "cases": [], "arms": {}, "budget": {"workers": 13, "repetitions": 3},
                    "native": {"model": "GLM-5.3", "reasoning_level": "max"}, "baseline_source_sha": "f"*40,
                    "knowledge_checkout_sha": "c"*40,
                    "analysis_groups": {"primary_prospective": list(report.PRIMARY), "older_fork_exploratory": list(report.EXPLORATORY)}}
        identity = {"cases": [], "arms": {}, "native": {"model": "GLM-5.3", "provider_id": "account:coding-plan"}}
        harness = root.parent / "harness.py"
        harness.write_text(tag)
        identity["harness_sha256"] = binding(harness)["sha256"]
        for arm in "AB":
            docs = root.parent / ("docs-" + arm)
            docs.mkdir()
            (docs / "feature.md").write_text("same documents " + arm)
            campaign["arms"][arm] = {"doc_root": str(docs)}
            identity["arms"][arm] = {"doc_root": str(docs), "documents": {"feature.md": binding(docs / "feature.md")["sha256"]}}
        for pr in report.PRS:
            source = root.parent / f"source-{pr}"
            source.mkdir()
            (source / "entry.py").write_text("first party code")
            context = write(root / f"cases/{pr}/context.json", {"pr": pr})
            diff = root / f"cases/{pr}/diff.patch"
            diff.write_text("same diff")
            case = {"number": pr, "target": "f"*40, "base": "b"*40, "head": "h"*40,
                    "context_path": str(context), "diff_path": str(diff), "context_sha256": binding(context)["sha256"],
                    "diff_sha256": binding(diff)["sha256"], "source_root": str(source)}
            campaign["cases"].append(case)
            identity["cases"].append({**case, "sources": {"entry.py": binding(source / "entry.py")["sha256"]}})
        campaign_path = write(root / "campaign.json", campaign)
        campaign_sha = binding(campaign_path)["sha256"]
        identity["campaign_sha256"] = campaign_sha
        identity["identity_sha256"] = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        write(root / "identity.json", identity)
        truth = {"campaign_sha256": campaign_sha, "frozen": True, "cases": []}
        for pr in report.PRS:
            record = {"campaign_sha256": campaign_sha, "pr": pr, "base": "b"*40, "head": "h"*40,
                      "status": "failed" if pr == 7656 else "complete"}
            if pr == 7656: record["error"] = "unknown baseline evidence"
            else: record["data"] = {"issues": []}
            if tag == "retest": record["retest_origin"] = {"retained": True}
            path = write(root / f"private-codex/truth/pr-{pr}.json", record)
            truth["cases"].append({"pr": pr, **binding(path), "status": record["status"]})
        truth_path = write(root / "private-codex/truth-manifest.json", truth)
        write(root / "truth-prerequisite.json", {"sha256": binding(truth_path)["sha256"]})
        values.append(report.read_study(root))
    old, new = values
    proofs = []
    for before, after in zip(old["truth"]["cases"], new["truth"]["cases"]):
        record = old["truth_records"][before["pr"]]
        payload = {k: v for k, v in record.items() if k != "campaign_sha256"}
        proofs.append({"pr": before["pr"], "status": record["status"], "origin_record": binding(before["path"]),
                       "rebound_record": binding(after["path"]), "preserved_payload_sha256": hashlib.sha256(
                           json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()})
    provenance = {"schema": "jiuwenswarm-protocol-retest-v1", "original_archive_mutated": False,
                  "campaign": binding(new["study"] / "campaign.json"),
                  "origin": {"campaign": binding(old["study"] / "campaign.json"),
                             "runtime_identity": binding(old["study"] / "identity.json"),
                             "truth": binding(old["study"] / "private-codex/truth-manifest.json"), "inventory": binding(inventory)},
                  "reference_report": binding(reference), "truth_manifest": binding(new["study"] / "private-codex/truth-manifest.json"),
                  "protocol": {"previous_harness_sha256": old["identity"]["harness_sha256"],
                               "retest_harness": binding(new["study"].parent / "harness.py")}, "truth_records": proofs}
    return old, new, provenance


def test_same_sources_docs_and_unknown_truth_are_comparable(studies):
    old, new, proof = studies
    report.verify_comparable(old, new, proof)
    assert new["truth_records"][7656]["status"] == "failed"


@pytest.mark.parametrize("field", ["target", "base", "head", "context_sha256", "diff_sha256"])
def test_retest_rejects_changed_source_identity(studies, field):
    old, new, proof = studies
    new["campaign"]["cases"][0][field] = "changed"
    with pytest.raises(ValueError, match="PR inputs changed"):
        report.verify_comparable(old, new, proof)


@pytest.mark.parametrize("field", ["budget", "native"])
def test_retest_rejects_model_or_budget_change(studies, field):
    old, new, proof = studies
    new["campaign"][field]["extra"] = "changed"
    with pytest.raises(ValueError, match="comparable configuration"):
        report.verify_comparable(old, new, proof)


def test_unknown_truth_cannot_be_replaced_with_zero_issues(studies):
    old, new, proof = studies
    new["truth_records"][7656].update(status="complete", data={"issues": []})
    with pytest.raises(ValueError, match="including unknown"):
        report.verify_comparable(old, new, proof)


def test_truth_payload_and_harness_binding_are_not_only_counters(studies):
    old, new, proof = studies
    proof["truth_records"][0]["preserved_payload_sha256"] = "0"*64
    with pytest.raises(ValueError, match="preserved payload"):
        report.verify_comparable(old, new, proof)
    proof["truth_records"][0]["preserved_payload_sha256"] = hashlib.sha256(json.dumps(
        {k: v for k, v in old["truth_records"][7639].items() if k != "campaign_sha256"},
        sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    new["identity"]["harness_sha256"] = "1"*64
    with pytest.raises(ValueError, match="harness identity"):
        report.verify_comparable(old, new, proof)


@pytest.mark.parametrize("kind", ["source", "document", "diff", "truth"])
def test_reread_rejects_tampered_frozen_bytes(studies, kind):
    old, new, _ = studies
    if kind == "source": path = Path(new["identity"]["cases"][0]["source_root"]) / "entry.py"
    elif kind == "document": path = Path(new["identity"]["arms"]["A"]["doc_root"]) / "feature.md"
    elif kind == "diff": path = Path(new["campaign"]["cases"][0]["diff_path"])
    else: path = Path(new["truth"]["cases"][0]["path"])
    if kind == "truth": write(path, {"tampered": True})
    else: path.write_text("tampered")
    with pytest.raises(ValueError, match="changed"):
        report.read_study(new["study"])


def test_equal_count_scores_from_foreign_campaign_are_rejected(studies):
    _, new, _ = studies
    write(new["study"] / "private-codex/results.json", {"campaign_sha256": "foreign", "scoring_completion": {"scored_review_samples": 72}})
    with pytest.raises(ValueError, match="different campaign"):
        report.read_study(new["study"])


def slots():
    return [{"number": pr, "arm": arm, "repetition": rep, "status": "valid"} for pr in report.PRS for arm in "AB" for rep in (1,2,3)]


def test_all_slots_and_every_valid_scored_are_required():
    rows = slots()
    samples = [{"pr": r["number"], "arm": r["arm"], "repeat": r["repetition"]-1, "status": "complete"} for r in rows]
    value = {"rows": rows, "scores": {"samples": samples}}
    assert report.completion(value) == "completed"
    samples[0]["status"] = "failed"
    assert report.completion(value) == "incomplete"
    rows[0]["status"] = "invalid_run"
    assert report.completion(value) == "completed_with_failures"
    rows.pop()
    assert report.completion(value) == "incomplete"


def test_partial_completion_retains_24_and_36_denominators(monkeypatch):
    monkeypatch.setattr(report, "knowledge_exposure", lambda *_: {})
    rows = [{"number": 7641, "arm": "A", "repetition": 1, "status": "valid", "native_seconds": 10},
            {"number": 7641, "arm": "A", "repetition": 2, "status": "invalid_run", "native_seconds": 1800}]
    metrics = review_metrics([{"label": "unknown", "root_cause": "unverified", "matched_issue_ids": []},
                              {"label": "nondefect_advice", "root_cause": "style", "matched_issue_ids": [], "advice_valid": True}], [])
    samples = [{"pr": 7641, "arm": "A", "repeat": 0, "status": "complete", "review_status": "complete", "metrics": metrics}]
    value = {"rows": rows, "scores": {"samples": samples}, "collection": {}, "campaign": {}, "study": Path("/unused")}
    result = report.summarize(value, {})
    primary = result["groups"]["primary_prospective"]["operational"]["A"]
    assert primary["expected"] == 24 and primary["terminal"] == 2 and primary["valid"] == 1
    assert result["groups"]["all"]["operational"]["A"]["expected"] == 36
    assert primary["counts"]["FP"] == 0 and primary["counts"]["unknown"] == 1
    assert primary["counts"]["nondefect_advice"] == 1
    assert primary["timings_valid"]["native_seconds"]["p50"] == 10
    assert result["groups"]["primary_prospective"]["paired_quality"]["defect_precision"]["applicable_prs"] == 0


def test_score_metrics_are_recomputed_and_unknown_truth_has_no_recall(studies):
    _, value, _ = studies
    root = value["study"]
    row = {"number": 7656, "arm": "B", "repetition": 1, "status": "valid", "item": "review-pr7656-B-r1",
           "normalized_output_sha256": "1"*64}
    path = write(root / "items" / row["item"] / "result.json", row)
    comments = [{"label": "TP", "root_cause": "new valid defect", "matched_issue_ids": []},
                {"label": "unknown", "root_cause": "uncertain", "matched_issue_ids": []}]
    metrics = review_metrics(comments, None)
    sample = {"pr": 7656, "arm": "B", "repeat": 0, "status": "complete", "review_status": "complete", "metrics": metrics}
    write(root / "private-codex/scores/pr-7656.json", {"status": "complete",
        "truth_manifest_sha256": binding(root / "private-codex/truth-manifest.json")["sha256"],
        "blind_mapping": {"R1": {"pr": 7656, "arm": "B", "repeat": 0, "run_result_sha256": binding(path)["sha256"], "normalized_output_sha256": "1"*64}},
        "data": {"reviews": {"R1": {"comments": comments}}}})
    value["rows"] = [row]
    value["scores"] = {"samples": [sample]}
    report.verify_scores(value)
    assert sample["metrics"]["confirmed_recall"] is None
    assert sample["metrics"]["novel_valid_defects"] is None
    sample["metrics"]["FP"] = 1
    with pytest.raises(ValueError, match="classified comments"):
        report.verify_scores(value)


def test_invalid_native_trial_cannot_be_scored_as_valid():
    value = {"rows": [{"number": 7639, "arm": "A", "repetition": 1, "status": "invalid_run"}],
             "scores": {"samples": [{"pr": 7639, "arm": "A", "repeat": 0, "review_status": "failed", "status": "complete", "metrics": {}}]}}
    with pytest.raises(ValueError, match="cannot receive"):
        report.verify_scores(value)


def traced_row(tmp_path, count):
    row = {"number": 7641, "arm": "B", "repetition": 1, "status": "valid", "source_calls_cumulative": count-1, "attempts": []}
    for index, size in enumerate((1, count-1)):
        root = tmp_path / f"attempt-{index}"
        state = write(root / "tool-state.json", {"events": size})
        events = root / "bridge-events.jsonl"
        events.write_text("\n".join(json.dumps({"tool": "source_read", "error": "prompt_not_complete: read first" if index == 0 else ""}) for _ in range(size)))
        row["attempts"].append({"attempt_root": str(root), "artifacts": {"tool-state.json": binding(state)["sha256"], "bridge-events.jsonl": binding(events)["sha256"]}})
    return row


def test_actual_call_audit_counts_denied_calls_across_attempts(tmp_path):
    result = report.actual_source_calls(traced_row(tmp_path, 60))
    assert result["actual_requests"] == 60 and result["stored_counter"] == 59
    assert result["early_prompt_gate_denied"] == 1


def test_actual_call_61_blocks_report_even_when_counter_says_60(tmp_path):
    with pytest.raises(ValueError, match="actual source/compute"):
        report.actual_source_calls(traced_row(tmp_path, 61))


def test_actual_call_journal_is_hash_bound(tmp_path):
    row = traced_row(tmp_path, 2)
    Path(row["attempts"][0]["attempt_root"]).joinpath("bridge-events.jsonl").write_text("")
    with pytest.raises(ValueError, match="event bytes changed"):
        report.actual_source_calls(row)


@pytest.mark.parametrize("missing,reason", [("anchor_snippet", "optional_anchor_contract_conflict"), ("evidence", "unclassified")])
def test_old_failure_label_requires_actual_matching_output_shape(tmp_path, missing, reason):
    root = tmp_path / "attempt"
    root.mkdir()
    comment = {"file": "entry.py", "line": 1, "anchor_snippet": "pass", "severity": "major", "comment": "fix", "evidence": "proof", "disposition": "publish"}
    comment.pop(missing)
    write(root / "tool-state.json", {"violations": []})
    (root / "bridge-events.jsonl").write_text("")
    write(root / "reply.txt", {"status": "success", "review_comments": [comment]})
    artifacts = {name: binding(root / name)["sha256"] for name in ("tool-state.json", "bridge-events.jsonl", "reply.txt")}
    row = {"number": 7641, "arm": "B", "repetition": 1, "status": "invalid_run", "error": "review comment has missing required fields", "attempts": [{"attempt_root": str(root), "artifacts": artifacts}]}
    result = report.previous_failure_audit({"rows": [row]})
    assert result["counts"] == {reason: 1}
    assert result["old_failures_remain_failures"] is True


def native_row(tmp_path, *, content='{"paths":"entry.py"}', truncated=False, before_mcp_error=False, calls=1, certified=True):
    root = tmp_path / "native-attempt"
    root.mkdir(parents=True)
    bridge = root / "bridge-events.jsonl"
    bridge.write_text("" if before_mcp_error else "\n".join(json.dumps({"result": content}) for _ in range(calls)))
    events = []
    for index in range(calls):
        events += [{"type": "tool.updated", "payload": {"kind": "scheduled", "toolCallId": f"call-{index}", "toolName": report.BRIDGE_PREFIX + "source_list"}},
                   {"type": "tool.updated", "payload": {"kind": "result", "toolCallId": f"call-{index}", "result": {
                       "content": content, "truncated": truncated, "success": not before_mcp_error,
                       "originalBytes": len(content.encode()), "returnedBytes": len(content.encode())}}}]
    journal = root / "traces/attempts/native/native-events.jsonl"
    journal.parent.mkdir(parents=True)
    journal.write_text("\n".join(json.dumps(event) for event in events))
    row = {"number": 7641, "arm": "B", "repetition": 1, "status": "valid", "attempts": [{"attempt_root": str(root),
           "artifacts": {"bridge-events.jsonl": binding(bridge)["sha256"], "traces/attempts/native/native-events.jsonl": binding(journal)["sha256"]}}]}
    if certified:
        row["native_protocol_guard"] = {"schema": "jiuwenswarm-native-protocol-guard-v1", "status": "passed",
            "native_source_calls_cumulative": calls, "max_native_result_chars": len(content),
            "max_native_result_utf8_bytes": len(content.encode()), "truncated_result_records": int(truncated)*calls,
            "violations": []}
        row["attempts"][0]["native_protocol_guard"] = row["native_protocol_guard"]
    return row


def test_current_native_guard_requires_literal_cap_no_truncation_and_bound_bytes(tmp_path):
    row = native_row(tmp_path)
    value = report.native_journal_guard(row, require_certified=True)
    assert value["certified"] is True and value["source_call_ids"] == 1
    assert "provider request body unavailable" in value["evidence_basis"]
    row["native_protocol_guard"]["native_source_calls_cumulative"] = 0
    with pytest.raises(ValueError, match="measurement_mismatch"):
        report.native_journal_guard(row, require_certified=True)


@pytest.mark.parametrize("content,truncated", [("x"*24001, False), ("中"*8001, False), ("small", True), ('{}\n\nStructured content:{}', False)])
def test_literal_cap_utf8_truncation_and_double_render_reject_valid_trial(tmp_path, content, truncated):
    with pytest.raises(ValueError, match="lacks certified native"):
        report.native_journal_guard(native_row(tmp_path, content=content, truncated=truncated), require_certified=True)


def test_old_baseline_keeps_stats_but_literal_rendering_is_not_certified(tmp_path):
    row = native_row(tmp_path, content="x"*24001, truncated=True, certified=False)
    value = report.native_journal_guard(row, require_certified=False)
    assert value["certified"] is False and value["baseline_literal_cap_certified"] is False
    assert value["adapter_truncated_results"] == 1
    assert value["violation_counts"]["native_result_character_cap_exceeded"] == 1
    assert row["status"] == "valid"


def test_native_call_limit_includes_schema_rejections_before_bridge_execution(tmp_path):
    row = native_row(tmp_path, content="invalid tool arguments", before_mcp_error=True, calls=60)
    value = report.native_journal_guard(row, require_certified=True)
    assert value["source_call_ids"] == 60 and value["certified"] is True
    row = native_row(tmp_path / "over-limit", content="invalid tool arguments", before_mcp_error=True, calls=61)
    with pytest.raises(ValueError, match="native source/compute call IDs"):
        report.native_journal_guard(row, require_certified=True)


def test_missing_native_guard_cannot_certify_current_valid_result(tmp_path):
    with pytest.raises(ValueError, match="stored_native_guard"):
        report.native_journal_guard(native_row(tmp_path, certified=False), require_certified=True)


def test_invalid_budget_breaches_stay_failed_in_denominator(tmp_path):
    row = traced_row(tmp_path, 61)
    row["status"] = "invalid_run"
    actual = report.actual_source_calls(row)
    assert actual["actual_requests"] == 61 and actual["budget_passed"] is False
    row = native_row(tmp_path / "native", calls=61)
    row["status"] = "invalid_run"
    guard = report.native_journal_guard(row, require_certified=True)
    assert guard["certified"] is False and guard["source_call_ids"] == 61


def test_unknown_early_transport_failure_stays_unknown_not_zero(tmp_path):
    row = {"number": 7641, "arm": "B", "repetition": 1, "status": "transport_failed", "attempts": [
           {"attempt_root": str(tmp_path), "status": "transport_failed", "artifacts": {}}]}
    audit = report.actual_source_calls(row)
    assert audit["actual_requests"] is None and audit["unknown_attempts"] == 1 and audit["budget_passed"] is False


def test_finalized_hash_bound_empty_transport_can_precede_valid_retry(tmp_path):
    empty = tmp_path / "empty"
    metadata = write(empty / "traces/attempts/id/attempt.json", {"schema": "native-attempt/1", "status": "transport_failed",
        "finished_at": 1, "trace_id": "t", "native_events_sha256": "sha256:" + hashlib.sha256(b"").hexdigest()})
    attempt = {"attempt_root": str(empty), "status": "transport_failed", "native_trace_id": "t",
               "artifacts": {"traces/attempts/id/attempt.json": binding(metadata)["sha256"]}}
    row = {"number": 7641, "arm": "B", "repetition": 1, "status": "valid", "attempts": [attempt]}
    audit = report.actual_source_calls(row)
    assert audit["actual_requests"] == 0 and audit["proven_empty_transport_attempts"] == 1
    assert report.empty_transport_evidence(attempt) is True


def test_duplicate_result_phase_is_still_checked_for_cap_and_content_conflict(tmp_path):
    row = native_row(tmp_path)
    attempt = row["attempts"][0]
    journal = Path(attempt["attempt_root"]) / "traces/attempts/native/native-events.jsonl"
    events = [json.loads(line) for line in journal.read_text().splitlines()]
    phase = copy.deepcopy(events[-1])
    phase["payload"]["kind"] = "running"
    phase["payload"]["result"].update(content="x"*24001, originalBytes=24001, returnedBytes=24001)
    journal.write_text("\n".join(json.dumps(e) for e in [*events, phase]))
    attempt["artifacts"]["traces/attempts/native/native-events.jsonl"] = binding(journal)["sha256"]
    row["status"] = "invalid_run"
    guard = report.native_journal_guard(row, require_certified=True)
    assert guard["maximum_content_chars"] == 24001
    assert guard["violation_counts"]["native_result_delivery_conflict"] == 1
    assert guard["violation_counts"]["native_result_character_cap_exceeded"] == 1
