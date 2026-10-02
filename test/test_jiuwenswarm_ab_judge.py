"""Offline checks for immutable truth, blind labels and PR-level A/B metrics."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from eval import jiuwenswarm_ab_judge as judge


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


@pytest.fixture
def case(tmp_path):
    source = tmp_path / "source"; source.mkdir()
    git(source, "init", "--quiet")
    git(source, "config", "user.name", "Offline A/B")
    git(source, "config", "user.email", "offline@example.invalid")
    (source / "core.py").write_text("def run(value=None):\n    if value is None:\n        return 0\n    return value\n" + "# context\n" * 230)
    git(source, "add", "."); git(source, "commit", "--quiet", "-m", "Before")
    base = git(source, "rev-parse", "HEAD")
    (source / "core.py").write_text("def run(value=None):\n    return value + 1\n" + "# context\n" * 230)
    git(source, "commit", "--quiet", "-am", "After")
    head = git(source, "rev-parse", "HEAD")
    diff = tmp_path / "diff.patch"
    diff.write_bytes(subprocess.check_output(["git", "-C", str(source), "diff", base, head]))
    context = tmp_path / "context.json"
    context.write_text(json.dumps({"title": "Example PR", "body": "Untrusted description"}))
    return {"number": 1, "base": base, "head": head, "source_root": str(source),
            "diff_path": str(diff), "context_path": str(context)}


@pytest.fixture
def campaign(tmp_path, case):
    root = tmp_path / "campaign"
    data = {"schema": judge.CAMPAIGN_SCHEMA, "run_root": str(root), "source_pin": judge.SOURCE_PIN,
            "cases": [{**case, "number": n} for n in range(1, 13)],
            "arms": {a: {"doc_root": str(tmp_path / a), "repo_subdir": "repos/jiuwenswarm"} for a in ("A", "B")}}
    path = tmp_path / "campaign.json"; path.write_text(json.dumps(data))
    return path, data


def defect(pr=1):
    return {"issue_id": f"PR{pr}-D1", "root_cause": "missing None guard", "title": "None addition",
            "body": "Default input now raises TypeError", "file": "core.py", "line": 2, "severity": "P2",
            "introduced_or_worsened": "introduced", "trigger": "default None", "consequence": "TypeError",
            "baseline_comparison": "Before returned zero; after adds one to None",
            "evidence": [{"version": "base", "path": "core.py", "start": 1, "end": 4},
                         {"version": "head", "path": "core.py", "start": 1, "end": 2}]}


def annotation(label="TP", cause="missing guard", matched=None, evidence=None, cid="C1"):
    return {"comment_id": cid, "label": label, "root_cause": cause,
            "matched_issue_ids": matched or [], "reason": "Concrete pinned source reason",
            "evidence": evidence if evidence is not None else [{"version": "head", "path": "core.py", "start": 2, "end": 2}]}


def test_complete_changed_files_and_late_lines_are_frozen_without_prefix_cap(case, tmp_path):
    packet, identity = judge.prepare_case(case, tmp_path / "private-input")
    after = packet["changed_files"][0]["head"]
    assert after["line_count"] == 232
    assert Path(identity["files"][0]["head"]["path"]).read_text() == judge.source_text(case, "head", "core.py")
    assert identity["actual_diff_sha256"] == judge.sha(packet["complete_diff"]["text"])
    assert "path" not in after and "source_root" not in packet
    assert "arms" not in packet and "doc_root" not in judge.canonical(packet)


def test_confirmed_truth_requires_changed_head_and_before_evidence(case):
    validate = judge.truth_validator(case)
    validate({"issues": [defect()], "excluded_candidates": []})
    value = defect(); value["evidence"] = value["evidence"][1:]
    with pytest.raises(ValueError, match="baseline evidence"):
        validate({"issues": [value], "excluded_candidates": []})
    value = defect(); value["introduced_or_worsened"] = "fixed_by_pr"
    with pytest.raises(ValueError, match="new or worsened"):
        validate({"issues": [value], "excluded_candidates": []})


def test_zero_confirmed_truth_and_explicit_preexisting_exclusion_are_valid(case):
    judge.truth_validator(case)({"issues": [], "excluded_candidates": [
        {"classification": "fixed_by_pr", "reason": "The actual before/after comparison fixes the old bug."},
        {"classification": "uncertain", "reason": "Related behavior cannot be confirmed."}]})
    metrics = judge.review_metrics([], [])
    assert metrics["defect_precision"] is None and metrics["confirmed_recall"] is None


def test_truth_schema_failure_is_terminal_not_resampled(campaign):
    path, data = campaign
    calls = []

    def invoke(*_, **kwargs):
        calls.append(kwargs["payload"]["pr"])
        kwargs["validate"]({"issues": "malformed", "excluded_candidates": []})

    first = judge.truth(path, workers=2, invoke=invoke)
    second = judge.truth(path, workers=2, invoke=invoke)
    assert len(calls) == 12 and first["frozen"] and second["frozen"]
    assert all(x["status"] == "failed" for x in second["cases"])
    assert all(x["confirmed_defects"] is None for x in second["cases"])
    assert second["truth_complete_cases"] == 0 and second["truth_failed_cases"] == 12
    saved = json.loads((Path(data["run_root"]) / "private-codex/truth/pr-1.json").read_text())
    assert saved["cost_usd"] is None


def test_score_refuses_unfrozen_truth_before_invocation(campaign):
    path, data = campaign
    private = Path(data["run_root"]) / "private-codex"; private.mkdir(parents=True)
    (private / "truth-manifest.json").write_text(json.dumps({"frozen": False}))
    with pytest.raises(ValueError, match="must be frozen"):
        judge.score(path, invoke=lambda *_a, **_k: pytest.fail("scored before truth"))


def test_blind_comment_normalization_drops_group_metadata_but_keeps_claims():
    actual = judge.normalize_comments({"review_comments": [{"file": "core.py", "line": 2,
        "title": "[KB_B] Guard missing", "body": "知识组：B\nFailure for None.\n<!-- kb:depth feature=x -->",
        "knowledge_group": "B", "arm": "B", "repeat": 2}]})
    assert actual == [{"comment_id": "C1", "file": "core.py", "line": 2,
                       "title": "Guard missing", "body": "Failure for None."}]


def test_blind_scrubbing_removes_both_document_corpora_and_keeps_source_evidence():
    text = "依据 .doc_project_maintainer/code/reference.md 和 knowledge/repos/jiuwenswarm/feature-depth-goal.md。\n" \
           "另见 [说明](https://example.invalid/docs/zh/经验记忆.md)。\n[lightweight]\n" \
           "core.py:2 calls missing_guard(); actual source claim stays."
    scrubbed = judge.scrub_text(text)
    assert ".doc_project_maintainer" not in scrubbed and "knowledge/repos/" not in scrubbed
    assert "feature-depth" not in scrubbed and "docs/zh/" not in scrubbed and "lightweight" not in scrubbed
    assert "core.py:2 calls missing_guard(); actual source claim stays." in scrubbed


def test_unknown_is_not_fp_novel_defects_do_not_backfill_and_duplicates_do_not_count():
    comments = [annotation(matched=["PR1-D1"]), annotation(cause="other wording", matched=["PR1-D1"], cid="C2"),
                annotation(label="FP", cause="unsupported guarantee", cid="C3"),
                annotation(label="FP", cause="UNSUPPORTED GUARANTEE", cid="C4"),
                annotation(label="unknown", cause="unavailable evidence", evidence=[], cid="C5"),
                annotation(cause="second actual defect", cid="C6"),
                annotation(label="nondefect_advice", cause="style", evidence=[], cid="C7")]
    metrics = judge.review_metrics(comments, [defect()])
    assert (metrics["TP"], metrics["FP"], metrics["unknown"], metrics["novel_valid_defects"]) == (2, 1, 1, 1)
    assert metrics["defect_precision"] == pytest.approx(2 / 3) and metrics["confirmed_recall"] == 1
    assert metrics["raw_comments"] == 7 and metrics["distinct_root_causes"] == 5


def test_score_schema_requires_all_labels_comments_real_lines_and_frozen_ids(case):
    comments = [{"comment_id": "C1"}]
    validate = judge.score_validator(case, {"R4": comments}, [defect()])
    valid = {"reviews": {"R4": {"comments": [annotation(matched=["PR1-D1"])]}}}
    validate(valid)
    bad = json.loads(json.dumps(valid)); bad["reviews"]["R4"]["comments"][0]["matched_issue_ids"] = ["invented"]
    with pytest.raises(ValueError, match="frozen truth"):
        validate(bad)
    bad = json.loads(json.dumps(valid)); bad["reviews"]["R4"]["comments"][0]["evidence"][0]["end"] = 999
    with pytest.raises(ValueError, match="exceeds"):
        validate(bad)
    with pytest.raises(ValueError, match="every blind"):
        validate({"reviews": {}})


def test_advice_validity_and_actionability_are_separate_from_defect_metrics(case):
    item = annotation(label="nondefect_advice", cause="guard documentation")
    item.update(advice_valid=True, actionable=True)
    validate = judge.score_validator(case, {"R1": [{"comment_id": "C1"}]}, [defect()])
    validate({"reviews": {"R1": {"comments": [item]}}})
    metrics = judge.review_metrics([item], [defect()])
    assert metrics["TP"] == metrics["FP"] == 0 and metrics["defect_precision"] is None
    assert metrics["advice_validity"] == 1 and metrics["advice_valid_actionable"] == 1
    item["evidence"] = []
    with pytest.raises(ValueError, match="missing code evidence"):
        validate({"reviews": {"R1": {"comments": [item]}}})


def test_three_repeats_are_averaged_per_pr_before_macro_not_pooled_comments():
    records = []
    for pr, precisions in ((1, [1, 0, 0]), (2, [1, 1, 1])):
        for arm in ("A", "B"):
            for repeat, precision in enumerate(precisions):
                metrics = {"defect_precision": precision, "confirmed_recall": None if pr == 1 else 1,
                           "TP": precision, "FP": 1 - precision, "unknown": 0, "nondefect_advice": 0,
                           "novel_valid_defects": 0}
                records.append({"pr": pr, "arm": arm, "repeat": repeat, "status": "complete", "review_status": "complete", "metrics": metrics})
    result = judge.aggregate(records, [1, 2])
    assert result["macro"]["A"]["defect_precision"]["mean"] == pytest.approx(2 / 3)
    assert result["macro"]["B"]["confirmed_recall"] == {"mean": 1, "applicable_prs": 1}
    records[0].update(status="failed", review_status="failed")
    result = judge.aggregate(records, [1, 2])
    assert result["review_completion"]["completed"] == 11
    assert result["per_pr"][0]["arms"]["A"]["scored_repeats"] == 2


def test_native_stream_archives_raw_stdout_stderr_and_parsed_events(tmp_path):
    events = []
    command = [sys.executable, "-c", 'import sys; print(\'{"type":"turn.completed","usage":{"input_tokens":7}}\'); sys.stderr.write("partial-stderr")']
    parsed = judge.stream_native(command, tmp_path, {}, 5, events.append)
    assert parsed == [{"type": "turn.completed", "usage": {"input_tokens": 7}}]
    assert any(x.get("type") == "native.stdout" and x["text"].endswith("\n") for x in events)
    assert {"type": "native.stderr", "text": "partial-stderr"} in events
    assert judge.native_snapshot(parsed)["usage"] == {"input_tokens": 7}
    assert judge.native_snapshot([])["usage"] == {}


def test_native_timeout_preserves_stream_without_fabricated_usage(tmp_path):
    events = []
    command = [sys.executable, "-c", 'import sys,time; print("native-prefix", flush=True); sys.stderr.write("error-tail"); sys.stderr.flush(); time.sleep(5)']
    with pytest.raises(judge.ModelUnavailable, match="timed out"):
        judge.stream_native(command, tmp_path, {}, 0.2, events.append)
    assert any(x.get("text") == "native-prefix\n" for x in events)
    assert any(x.get("text") == "error-tail" for x in events)


def test_complete_stdin_avoids_argv_limits_and_pipe_deadlock(tmp_path):
    task = "完整任务" * 90000
    path = tmp_path / "task"; path.write_text(task)
    events = []
    command = [sys.executable, "-c", 'import sys,json; print("start", flush=True); text=sys.stdin.read(); print(json.dumps({"length":len(text)})); sys.stderr.write("tail")']
    with path.open("rb") as stdin:
        parsed = judge.stream_native(command, tmp_path, {}, 5, events.append, stdin=stdin)
    assert parsed == [{"length": len(task)}]
    assert any(e.get("text") == "tail" for e in events)


def test_closed_tools_page_only_fixed_code_and_deny_external_docs_and_private_paths(case, tmp_path):
    root = Path(case["source_root"])
    (root / "docs").mkdir(); (root / "docs/guide.md").write_text("secret doc arm marker")
    task = tmp_path / "task"; task.write_text("complete task")
    tools = judge.ClosedSourceTools({"case": case, "task_path": str(task), "task_sha256": judge.sha("complete task")})
    assert tools.read_task()["content"] == "complete task"
    result = tools.source_read("core.py", "base")
    assert result["commit"] == case["base"] and result["line_count"] == 234
    assert "if value is None" in result["content"]
    for path in (str(task), "../task", "docs/guide.md", "private-codex/blind-seed.json", ".env", "untracked.py"):
        with pytest.raises(ValueError, match="outside"):
            tools.source_read(path)
    with pytest.raises(ValueError): tools.source_read("core.py", "target")
    with pytest.raises(ValueError): tools.read_task(-1)
    assert tools.source_grep("return", "core.py", "head")["matches"][0]["line"] == 2


def test_closed_native_tool_audit_requires_task_source_and_rejects_shell_or_other_mcp():
    def mcp(tool, server=judge.BRIDGE_NAME):
        return {"type": "item.completed", "item": {"type": "mcp_tool_call", "server": server, "tool": tool, "status": "completed"}}
    good = [mcp("read_task"), mcp("source_read")]
    judge.audit_native_tools(good, source_enabled=True)
    judge.audit_native_tools([], source_enabled=False)
    for bad in (good + [{"item": {"type": "command_execution", "command": "cat anything"}}],
                good + [mcp("source_read", "other")], [mcp("source_read")]):
        with pytest.raises(judge.ModelUnavailable): judge.audit_native_tools(bad, source_enabled=True)


def test_archived_transport_sends_full_task_stdin_and_disables_host_tools(tmp_path, monkeypatch):
    from infermatrix_copilot.config import Settings
    home = tmp_path / "home"; (home / ".codex").mkdir(parents=True)
    (home / ".codex/config.toml").write_text('[mcp_servers.host-secret]\ncommand="anything"\n')
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(judge.ArchivedCodexTransport, "require_cli", lambda self: "offline-codex")
    captured = {}
    def stream(command, cwd, environ, timeout, sink, *, stdin):
        captured.update(command=command, text=stdin.read().decode())
        return [{"item": {"type": "agent_message", "text": '{"ok":true}'}}]
    monkeypatch.setattr(judge, "stream_native", stream)
    transport = judge.ArchivedCodexTransport(Settings(_env_file=None))
    transport.complete(system="full system", messages=[{"role": "user", "content": "task" * 60000}])
    assert captured["command"][-1] == "-" and "full system" in captured["text"] and "task" * 60000 in captured["text"]
    for feature in judge.DISABLED_FEATURES:
        assert captured["command"][captured["command"].index(feature) - 1] == "--disable"
    assert "mcp_servers={}" in captured["command"]
    assert not any('mcp_servers."host-secret"' in arg for arg in captured["command"])
    assert "read-only" in captured["command"]


def test_source_bridge_declares_only_readonly_idempotent_closed_tools(case, tmp_path, monkeypatch):
    import mcp.server.fastmcp
    captured = {}
    class FakeServer:
        def __init__(self, name): assert name == judge.BRIDGE_NAME
        def tool(self, *, annotations):
            def wrap(function):
                captured[function.__name__] = annotations.model_dump()
                return function
            return wrap
        def run(self): pass
    monkeypatch.setattr(mcp.server.fastmcp, "FastMCP", FakeServer)
    task = tmp_path / "task"; task.write_text("readonly task")
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({"case": case, "task_path": str(task), "task_sha256": judge.sha("readonly task")}))
    judge.source_bridge(spec)
    assert set(captured) == judge.BRIDGE_TOOLS
    assert all(v["readOnlyHint"] and v["idempotentHint"] and not v["destructiveHint"] and not v["openWorldHint"] for v in captured.values())


def test_failed_frozen_truth_is_unknown_not_zero_for_metrics():
    metrics = judge.review_metrics([annotation()], None)
    assert metrics["defect_precision"] == 1 and metrics["confirmed_recall"] is None
    assert metrics["confirmed_defects"] is None and metrics["novel_valid_defects"] is None


@pytest.fixture
def score_artifacts(campaign):
    """Pure offline artifacts; no native inference or fake published receipts."""
    campaign_path, data = campaign
    campaign_sha = judge.sha(campaign_path.read_bytes())
    root = Path(data["run_root"])
    def truth_stub(*_, **kwargs):
        if kwargs["payload"]["pr"] == 12: raise ValueError("explicit unknown truth fixture")
        value = {"issues": [], "excluded_candidates": []}
        kwargs["validate"](value)
        return {"data": value}
    truth = judge.truth(campaign_path, invoke=truth_stub)
    path = root / "private-codex/truth-manifest.json"
    judge.atomic_write_json(root / "truth-prerequisite.json", {"path": str(path), "sha256": judge.sha(path.read_bytes()), "campaign_sha256": campaign_sha})
    identity = {"schema": judge.CAMPAIGN_SCHEMA, "campaign_sha256": campaign_sha, "cases": data["cases"]}
    identity["identity_sha256"] = judge.sha(json.dumps(identity, sort_keys=True))
    judge.atomic_write_json(root / "identity.json", identity)
    reviews = []
    for case in data["cases"]:
        for arm in ("A", "B"):
            for repeat in range(3):
                item = root / "items" / f"pr-{case['number']}-{arm}-r{repeat + 1}"
                output = item / "normalized-review.json"
                judge.atomic_write_json(output, {"review_comments": [{"file": "core.py", "line": 2, "title": "Guard", "body": "[KB_B] Failure for None"}]})
                output_sha = judge.sha(output.read_bytes())
                result_path = item / "result.json"
                result = {"schema": judge.CAMPAIGN_SCHEMA + "/result", "number": case["number"], "arm": arm,
                          "repetition": repeat + 1, "preflight": False, "status": "valid", "identity_sha256": identity["identity_sha256"],
                          "campaign_sha256": campaign_sha, "normalized_output_path": str(output), "normalized_output_sha256": output_sha}
                judge.atomic_write_json(result_path, result)
                reviews.append({"pr": case["number"], "arm": arm, "repeat": repeat, "status": "complete", "native_status": "valid",
                                "identity_sha256": identity["identity_sha256"], "campaign_sha256": campaign_sha,
                                "output_path": str(output), "normalized_output_sha256": output_sha,
                                "run_result_path": str(result_path), "run_result_sha256": judge.sha(result_path.read_bytes())})
    manifest = {"schema": judge.REVIEWS_SCHEMA, "campaign_sha256": campaign_sha, "identity_sha256": identity["identity_sha256"], "reviews": reviews}
    judge.atomic_write_json(root / "reviews-manifest.json", manifest)
    return campaign_path, data, manifest, truth


def test_score_checks_all_bindings_hides_mapping_and_preserves_failed_truth_unknown(score_artifacts):
    path, data, _, _ = score_artifacts
    calls = []
    def invoke(*_, **kwargs):
        packet = kwargs["payload"]; pr = packet["pr"]
        started = json.loads((Path(data["run_root"]) / "private-codex/scores" / f"pr-{pr}.json").read_bytes())
        assert "blind_mapping" not in started
        assert "KB_B" not in judge.canonical(packet["reviews"]) and "arm" not in judge.canonical(packet["reviews"])
        reply = {"reviews": {label: {"comments": [annotation(label="unknown", evidence=[], cid=c["comment_id"])
                                                            for c in comments]} for label, comments in packet["reviews"].items()}}
        kwargs["validate"](reply); calls.append(pr)
        return {"data": reply}
    result = judge.score(path, invoke=invoke)
    assert len(calls) == 12 and result["scoring_completion"]["scored_review_samples"] == 72
    unknown = [r for r in result["samples"] if r["pr"] == 12]
    assert all(r["metrics"]["confirmed_defects"] is None and r["metrics"]["confirmed_recall"] is None for r in unknown)


def test_changed_truth_manifest_cannot_replace_frozen_prerequisite(score_artifacts):
    path, data, _, _ = score_artifacts
    target = Path(data["run_root"]) / "private-codex/truth-manifest.json"
    truth = json.loads(target.read_bytes()); truth["cases"][0].update(path=truth["cases"][1]["path"], sha256=truth["cases"][1]["sha256"])
    judge.atomic_write_json(target, truth)
    with pytest.raises(ValueError, match="prerequisite SHA"):
        judge.score(path, invoke=lambda *_a, **_k: pytest.fail("tampered truth reached model"))


def test_truth_record_swapped_across_prs_fails_even_with_updated_consistent_manifest_hash(score_artifacts):
    path, data, _, _ = score_artifacts
    root = Path(data["run_root"]); target = root / "private-codex/truth-manifest.json"
    truth = json.loads(target.read_bytes()); truth["cases"][0].update(path=truth["cases"][1]["path"], sha256=truth["cases"][1]["sha256"])
    judge.atomic_write_json(target, truth)
    binding = json.loads((root / "truth-prerequisite.json").read_bytes()); binding["sha256"] = judge.sha(target.read_bytes())
    judge.atomic_write_json(root / "truth-prerequisite.json", binding)
    with pytest.raises(ValueError, match="record PR/source/status"):
        judge.score(path, invoke=lambda *_a, **_k: pytest.fail("foreign PR truth reached model"))


@pytest.mark.parametrize("change", ["normalized_text", "receipt_bytes", "result_slot", "result_campaign", "row_identity", "output_path"])
def test_review_bytes_and_native_result_slot_identity_are_bound_before_scoring(score_artifacts, change):
    path, data, manifest, _ = score_artifacts
    row = manifest["reviews"][0]
    result_path = Path(row["run_result_path"])
    result = json.loads(result_path.read_bytes())
    if change == "normalized_text":
        judge.atomic_write_json(Path(row["output_path"]), {"review_comments": [{"body": "REPLACED AFTER COLLECTION"}]})
    elif change == "receipt_bytes":
        result["status"] = "invalid_run"; judge.atomic_write_json(result_path, result)
    elif change in ("result_slot", "result_campaign"):
        result["number" if change == "result_slot" else "campaign_sha256"] = 2 if change == "result_slot" else "f" * 64
        judge.atomic_write_json(result_path, result); row["run_result_sha256"] = judge.sha(result_path.read_bytes())
    elif change == "row_identity": row["identity_sha256"] = "f" * 64
    else: row["output_path"] = manifest["reviews"][1]["output_path"]
    judge.atomic_write_json(Path(data["run_root"]) / "reviews-manifest.json", manifest)
    with pytest.raises(ValueError, match="SHA differs|identity differs"):
        judge.score(path, invoke=lambda *_a, **_k: pytest.fail("tampered sample reached model"))


@pytest.mark.parametrize("role", ["zcode:GLM-5.3", "claude-code:claude-opus-5-5", "codex:GLM-5.3"])
def test_truth_and_score_cannot_dispatch_an_api_claude_or_same_family_judge(tmp_path, monkeypatch, role):
    monkeypatch.setenv("KB_JUDGE", role)
    with pytest.raises(ValueError, match="independent native Codex"):
        judge.make_gateway(tmp_path / "traces")
