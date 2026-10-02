"""Offline protocol tests; no model/API calls or repository knowledge writes."""
import importlib.util
import json
from pathlib import Path
import stat
import subprocess
import sys

import pytest

from infermatrix_copilot.config import Settings
from infermatrix_copilot.providers.zcode import ZCodeTransport

MODULE_PATH = Path(__file__).resolve().parents[1] / "eval/jiuwenswarm_pr_review_ab.py"
SPEC = importlib.util.spec_from_file_location("jiuwenswarm_pr_review_ab", MODULE_PATH)
ab = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ab
SPEC.loader.exec_module(ab)


def _tools(tmp_path, initial=0):
    source = tmp_path / "source"
    source.mkdir()
    (source / "core.py").write_text("VALUE = 1\n" * 4000)
    (source / "binary.png").write_bytes(b"\xff\xfe\x00")
    docs = tmp_path / "docs"
    page = docs / "repos/jiuwenswarm/guide.md"
    page.parent.mkdir(parents=True)
    page.write_text("---\nrepo: jiuwenswarm\ntype: guide\ntitle: Core\nsources:\n  - jiuwenswarm@" + "a" * 40 + ":core.py\n---\n# Core\n" + "Document knowledge.\n" * 500)
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("prompt" * 9000)
    root = tmp_path / "attempt"
    root.mkdir()
    spec = {"attempt_root": str(root), "prompt_path": str(prompt), "prompt_sha256": ab.digest(prompt.read_bytes()),
            "initial_knowledge_chars": initial,
            "case": {"source_root": str(source), "head": "b" * 40, "base": "a" * 40,
                     "sources": {p.name: ab.digest(p.read_bytes()) for p in source.iterdir()}},
            "arm": {"doc_root": str(docs), "repo_subdir": "repos/jiuwenswarm",
                    "documents": {page.relative_to(docs).as_posix(): ab.digest(page.read_bytes())}}}
    return ab.ClosedTools(spec), spec


def test_prompt_paging_must_cover_all_bytes(tmp_path):
    tools, spec = _tools(tmp_path)
    result = json.loads(tools.call("read_prompt", {"offset": 0}))
    assert not ab.covered_prompt(tools.state, result["total_chars"])
    while result["next_offset"] is not None:
        result = json.loads(tools.call("read_prompt", {"offset": result["next_offset"]}))
    assert ab.covered_prompt(tools.state, result["total_chars"])
    assert tools.state["knowledge_chars"] == 0
    Path(spec["prompt_path"]).write_text("changed")
    assert "frozen prompt changed" in tools.call("read_prompt", {})


def test_knowledge_reads_share_closed_cumulative_quota(tmp_path):
    tools, _ = _tools(tmp_path, initial=5900)
    first = json.loads(tools.call("doc_read", {"path": "repos/jiuwenswarm/guide.md"}))
    assert len(first["content"]) == 100
    assert tools.state["knowledge_chars"] == 6000
    assert "budget_exhausted" in tools.call("doc_search", {"query": "knowledge"})
    assert tools.state["violations"] == []


def test_search_snippets_consume_same_knowledge_quota(tmp_path):
    tools, _ = _tools(tmp_path, initial=5950)
    result = json.loads(tools.call("doc_search", {"query": "knowledge"}))
    assert len(result["matches"]) == 50
    assert tools.state["knowledge_chars"] == 6000


@pytest.mark.parametrize("tool,args", [
    ("source_read", {"path": "../private.txt"}),
    ("source_read", {"path": "/etc/passwd"}),
    ("doc_read", {"path": "../other-arm/guide.md"}),
    ("source_read", {"path": "docs/private.md"}),
    ("source_read", {"path": ".git/config"}),
])
def test_scope_and_document_budget_cannot_be_bypassed(tmp_path, tool, args):
    tools, _ = _tools(tmp_path)
    assert "error" in json.loads(tools.call(tool, args))
    assert tools.state["violations"]


def test_read_miss_does_not_taint_a_valid_review(tmp_path):
    tools, _ = _tools(tmp_path)
    assert "not found" in tools.call("source_read", {"path": "missing.py"})
    assert tools.state["violations"] == []


def test_source_outputs_and_calls_bounded_and_binary_grep_skipped(tmp_path):
    tools, _ = _tools(tmp_path)
    result = tools.call("source_read", {"path": "core.py"})
    assert len(result) <= 24000
    assert json.loads(result)["next_offset"] is not None
    assert "core.py:1:VALUE" in tools.call("source_grep", {"pattern": "VALUE"})
    while tools.state["source_calls"] < 60:
        tools.call("source_list", {})
    assert "budget_exhausted" in tools.call("source_list", {})
    assert tools.state["violations"] == []


def test_changed_source_or_other_arm_document_is_refused(tmp_path):
    tools, spec = _tools(tmp_path)
    Path(spec["case"]["source_root"], "core.py").write_text("tampered")
    assert "frozen input changed" in tools.call("source_read", {"path": "core.py"})
    assert tools.state["violations"]
    assert "error" in json.loads(tools.call("doc_read", {"path": "repos/other/guide.md"}))


def test_reply_fences_allowed_without_model_repair():
    raw = '```json\n{"status":"success","summary":"Fine","review_comments":[],"tests_run":[]}\n```'
    assert ab.validate_reply(raw)["review_comments"] == []
    with pytest.raises(ValueError):
        ab.validate_reply('{"status":"success","review_comments":[],"tests_run":["pytest"]}')
    with pytest.raises(ValueError):
        ab.validate_reply("malformed")


def test_native_command_disables_reads_and_session_tools(tmp_path, monkeypatch):
    settings = Settings(_env_file=None, strict_backend_cli="/usr/bin/true", zcode_provider_id="account:bigmodel-individual-coding-plan")
    transport = ZCodeTransport(settings)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "private-test-value")
    cmd, env, native = ab.configure_session(tmp_path, transport, tmp_path / "bridge-spec.json")
    assert "--attach" not in cmd
    assert all(name in native["native_disallowed_tools"] for name in ("Read", "Grep", "Glob", "ReadSessionContext", "TaskOutput"))
    assert "ANTHROPIC_API_KEY" not in env
    config = json.loads(Path(env[zcode_module_key()]).read_text())
    assert config["config"]["defaultModelSelection"]["modelId"] == "GLM-5.3"
    assert native["provider_config_sha256"] == ab.digest(Path(env[zcode_module_key()]).read_bytes())


def zcode_module_key():
    return "ZCODE_PERSONAL_PROVIDER_CONFIG_FILE"


class FakePacer:
    def acquire(self, sink):
        sink({"type": "native.throttle.started", "payload": {"at": 1}})
        return object()
    def observe(self, *args):
        pass
    def finish(self, ticket, **kwargs):
        pass


def _fake_cli(tmp_path, rogue=False, wrong_model=False, fail=False, rogue_phase="scheduled", source_uses=1, knowledge_nearcap=False):
    cli = tmp_path / "zcode"
    text = """#!/usr/bin/env python3
import json, pathlib, sys
root = pathlib.Path.cwd()
sys.path.insert(0, REPO_SRC)
import importlib.util
s = importlib.util.spec_from_file_location('ab_child', MODULE)
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
tools = m.ClosedTools(json.loads((root/'bridge-spec.json').read_text()))
result = json.loads(tools.call('read_prompt', {'offset':0}))
while result['next_offset'] is not None:
    result = json.loads(tools.call('read_prompt', {'offset':result['next_offset']}))
tools.call('source_list', {})
for _ in range(SOURCE_USES - 1):
    tools.call('source_list', {})
tools.call('doc_search', {'query':'__bootstrap_no_match__'})
if KNOWLEDGE_NEARCAP:
    page = 'repos/jiuwenswarm/guide.md'
    size = len(tools.docs.read(page, limit=65536)['content'])
    tools.call('doc_read', {'path':page, 'offset':size-2990})
    tools.call('doc_read', {'path':page, 'offset':0})
print(json.dumps({'type':'session.updated','payload':{'modelId':MODEL,'providerId':'account:bigmodel-individual-coding-plan'}}))
if ROGUE:
    print(json.dumps({'type':'tool.updated','payload':{'kind':PHASE,'toolName':'Read','input':{'file_path':'/etc/passwd'}}}))
if FAIL:
    print('transport failure',file=sys.stderr);sys.exit(1)
print(json.dumps({'type':'result','response':json.dumps({'status':'success','bootstrap':True,'review_comments':[]}),
 'usage':{'inputTokens':42,'outputTokens':9}}))
"""
    text = text.replace("REPO_SRC", repr(str(ab.REPO_ROOT / "src"))).replace("MODULE", repr(str(MODULE_PATH)))
    text = text.replace("MODEL", repr("other-model" if wrong_model else "GLM-5.3")).replace("ROGUE", repr(rogue)).replace("FAIL", repr(fail))
    text = text.replace("PHASE", repr(rogue_phase)).replace("SOURCE_USES", repr(source_uses))
    text = text.replace("KNOWLEDGE_NEARCAP", repr(knowledge_nearcap))
    cli.write_text(text)
    cli.chmod(cli.stat().st_mode | stat.S_IXUSR)
    return cli


def _native_case(tmp_path):
    tools, spec = _tools(tmp_path)
    diff = tmp_path / "diff.txt"
    diff.write_text("diff --git a/core.py b/core.py\n")
    context = tmp_path / "context.txt"
    context.write_text("Change core")
    case = {**spec["case"], "number": 1, "changed_files": ["core.py"], "diff_path": str(diff),
            "context_path": str(context), "diff_sha256": ab.digest(diff.read_bytes()),
            "context_sha256": ab.digest(context.read_bytes())}
    identity = {"identity_sha256": "a" * 64, "campaign_sha256": "c" * 64,
                "cases": [case], "arms": {"A": spec["arm"], "B": spec["arm"]}}
    return case, identity


@pytest.mark.parametrize("rogue,wrong,expected", [(False, False, "valid"), (True, False, "invalid_run"), (False, True, "invalid_run")])
def test_native_trace_bootstrap_identity_and_invalid_tools(tmp_path, rogue, wrong, expected):
    case, identity = _native_case(tmp_path)
    cli = _fake_cli(tmp_path, rogue=rogue, wrong_model=wrong)
    transport = ZCodeTransport(Settings(_env_file=None, strict_backend_cli=str(cli), zcode_provider_id="account:bigmodel-individual-coding-plan"))
    result = ab.run_one(identity, transport, case, "A", 0, tmp_path / "runs", FakePacer(), preflight=True)
    assert result["status"] == expected, result["error"]
    assert len(result["attempts"]) == 1  # No content/tool-failure resampling.
    assert Path(result["attempt_root"], "provider_config.json").is_file()
    assert list(Path(result["attempt_root"], "traces/attempts").glob("*/native-events.jsonl"))
    ab.result_integrity(result)
    reused = ab.run_one(identity, transport, case, "A", 0, tmp_path / "runs", FakePacer(), preflight=True)
    assert reused == result
    Path(result["attempt_root"], "reply.txt").write_text("changed")
    with pytest.raises(ValueError, match="resume artifact"):
        ab.run_one(identity, transport, case, "A", 0, tmp_path / "runs", FakePacer(), preflight=True)


def test_only_transport_failure_retried_once_with_durable_records(tmp_path):
    case, identity = _native_case(tmp_path)
    cli = _fake_cli(tmp_path, fail=True)
    transport = ZCodeTransport(Settings(_env_file=None, strict_backend_cli=str(cli), zcode_provider_id="account:bigmodel-individual-coding-plan"))
    result = ab.run_one(identity, transport, case, "A", 0, tmp_path / "runs", FakePacer(), preflight=True)
    assert result["status"] == "transport_failed"
    assert len(result["attempts"]) == 2
    for attempt in result["attempts"]:
        ab.result_integrity(attempt)
        assert "transport failure" in attempt["error"]


@pytest.mark.parametrize("phase", ["started", "completed", "result"])
def test_native_reads_rejected_in_all_tool_event_phases(tmp_path, phase):
    case, identity = _native_case(tmp_path)
    cli = _fake_cli(tmp_path, rogue=True, rogue_phase=phase)
    transport = ZCodeTransport(Settings(_env_file=None, strict_backend_cli=str(cli), zcode_provider_id="account:bigmodel-individual-coding-plan"))
    result = ab.run_one(identity, transport, case, "A", 0, tmp_path / "runs", FakePacer(), preflight=True)
    assert result["status"] == "invalid_run"
    assert "Read" in result["error"]
    assert len(result["attempts"]) == 1


def test_native_nameless_results_and_batches_require_known_bridge_call_ids():
    def event(**payload):
        return {"type": "tool.updated", "payload": payload}
    events = [event(kind="scheduled", toolName=ab.BRIDGE_PREFIX + "read_prompt", toolCallId="c1"),
              event(kind="started", toolName=ab.BRIDGE_PREFIX + "read_prompt", toolCallId="c1"),
              event(kind="result", toolCallId="c1"), event(kind="batch", toolCallIds=["c1"])]
    assert ab.native_tool_violations(events) == []
    assert ab.native_tool_violations(events + [event(kind="completed", toolName="Read", toolCallId="c1")]) == ["Read"]
    assert ab.native_tool_violations(events + [event(kind="result", toolCallId="unknown")]) == ["unrecognized_tool_event"]


def test_source_limit_cumulative_across_only_transport_retry(tmp_path):
    case, identity = _native_case(tmp_path)
    cli = _fake_cli(tmp_path, fail=True, source_uses=59)
    transport = ZCodeTransport(Settings(_env_file=None, strict_backend_cli=str(cli), zcode_provider_id="account:bigmodel-individual-coding-plan"))
    result = ab.run_one(identity, transport, case, "A", 0, tmp_path / "runs", FakePacer(), preflight=True)
    assert len(result["attempts"]) == 2
    assert [a["source_calls_cumulative"] for a in result["attempts"]] == [59, 60]
    second = ab.read_json(Path(result["attempts"][1]["attempt_root"]) / "tool-state.json")
    assert second["source_calls"] == 60
    assert second["violations"] == []


def test_knowledge_quota_cumulative_across_transport_retry_near_cap(tmp_path):
    case, identity = _native_case(tmp_path)
    cli = _fake_cli(tmp_path, fail=True, knowledge_nearcap=True)
    transport = ZCodeTransport(Settings(_env_file=None, strict_backend_cli=str(cli), zcode_provider_id="account:bigmodel-individual-coding-plan"))
    result = ab.run_one(identity, transport, case, "A", 0, tmp_path / "runs", FakePacer(), preflight=True)
    assert [a["knowledge_chars_cumulative"] for a in result["attempts"]] == [5990, 6000]
    retry = Path(result["attempts"][1]["attempt_root"])
    assert ab.read_json(retry / "bridge-spec.json")["initial_knowledge_chars"] == 5990
    assert ab.read_json(retry / "tool-state.json")["knowledge_chars"] == 6000
    events = [json.loads(line) for line in (retry / "bridge-events.jsonl").read_text().splitlines()]
    reads = [event for event in events if event["tool"] == "doc_read"]
    assert len(reads) == 2
    assert any("budget_exhausted" in str(event) for event in reads)


@pytest.mark.parametrize("fail_at", ["cat-file", "ls-tree", "show"])
def test_base_read_failures_never_become_absence(tmp_path, monkeypatch, fail_at):
    tools, _ = _tools(tmp_path)
    def fake_git(root, *args):
        if args[0] == fail_at:
            raise ValueError("simulated git read failure")
        if args[0] == "ls-tree":
            return b"100644 blob abc\tcore.py\0"
        return b""
    monkeypatch.setattr(ab, "git", fake_git)
    result = json.loads(tools.call("file_at_base", {"path": "core.py"}))
    assert "error" in result
    assert "absent_at_base" not in result
    assert tools.state["violations"] == []


def test_base_absence_requires_successful_object_and_tree_reads(tmp_path, monkeypatch):
    tools, _ = _tools(tmp_path)
    calls = []
    def fake_git(root, *args):
        calls.append(args[0])
        return b""
    monkeypatch.setattr(ab, "git", fake_git)
    assert json.loads(tools.call("file_at_base", {"path": "missing.py"}))["absent_at_base"] is True
    assert calls == ["cat-file", "ls-tree"]


def _diverged_campaign(tmp_path, monkeypatch):
    import shutil
    tools, spec = _tools(tmp_path)
    source = Path(spec["case"]["source_root"])
    def command(*args):
        return subprocess.run(["git", *args], cwd=source, capture_output=True, check=True).stdout.decode().strip()
    command("init", "--initial-branch=main")
    command("config", "user.email", "offline@example.invalid")
    command("config", "user.name", "Offline protocol test")
    command("add", ".")
    command("commit", "-m", "common")
    base = command("rev-parse", "HEAD")
    (source / "target_only.py").write_text("TARGET = 1\n")
    command("add", ".")
    command("commit", "-m", "target")
    target = command("rev-parse", "HEAD")
    command("checkout", "-b", "pr", base)
    (source / "core.py").write_text("VALUE = 2\n")
    command("add", ".")
    command("commit", "-m", "PR")
    head = command("rev-parse", "HEAD")
    diff = tmp_path / "diff.txt"
    diff.write_bytes(ab.git(source, "diff", "--no-ext-diff", "--no-color", base, head, "--"))
    context = tmp_path / "context.txt"
    context.write_text("PR acceptance criteria")
    docs_b = tmp_path / "docs-b"
    shutil.copytree(spec["arm"]["doc_root"], docs_b)
    campaign = {"schema": ab.SCHEMA, "run_root": str(tmp_path / "runs"), "baseline_source_sha": target,
                "cases": [{"number": 123, "target": target, "base": base, "head": head,
                           "source_root": str(source), "diff_path": str(diff), "context_path": str(context)}],
                "arms": {"A": {"doc_root": spec["arm"]["doc_root"]}, "B": {"doc_root": str(docs_b)}}}
    path = tmp_path / "campaign.json"
    ab.atomic_json(path, campaign)
    transport = ZCodeTransport(Settings(_env_file=None, strict_backend_cli="/usr/bin/true", zcode_provider_id="account:bigmodel-individual-coding-plan"))
    monkeypatch.setattr(ab, "configured_transport", lambda native: transport)
    return path, campaign


def test_real_merge_base_and_diff_for_diverged_pr(tmp_path, monkeypatch):
    path, campaign = _diverged_campaign(tmp_path, monkeypatch)
    _, identity, _ = ab.load_campaign(path)
    assert identity["cases"][0]["base"] != identity["baseline_source_sha"]
    assert identity["cases"][0]["changed_files"] == ["core.py"]
    campaign["cases"][0]["base"] = campaign["baseline_source_sha"]
    ab.atomic_json(path, campaign)
    with pytest.raises(ValueError, match="merge-base"):
        ab.load_campaign(path)


def test_arm_ancestor_overlap_rejected(tmp_path, monkeypatch):
    path, campaign = _diverged_campaign(tmp_path, monkeypatch)
    campaign["arms"]["B"]["doc_root"] = campaign["arms"]["A"]["doc_root"]
    ab.atomic_json(path, campaign)
    with pytest.raises(ValueError, match="distinct"):
        ab.load_campaign(path)


def test_truth_gate_binds_all_terminal_records_without_injecting_truth(tmp_path, monkeypatch):
    path, _ = _diverged_campaign(tmp_path, monkeypatch)
    _, identity, _ = ab.load_campaign(path)
    case = identity["cases"][0]
    record = tmp_path / "private-truth/pr123.json"
    ab.atomic_json(record, {"pr": 123, "base": case["base"], "head": case["head"], "status": "failed"})
    truth = tmp_path / "private-truth/manifest.json"
    ab.atomic_json(truth, {"schema": "jiuwenswarm-truth-manifest-v1", "frozen": True,
                          "campaign_sha256": identity["campaign_sha256"], "source_pin": identity["baseline_source_sha"],
                          "cases": [{"pr": 123, "status": "failed", "path": str(record), "sha256": ab.digest(record.read_bytes())}]})
    ab.freeze_truth_prerequisite(tmp_path / "runs", identity, truth)
    binding = ab.read_json(tmp_path / "runs/truth-prerequisite.json")
    assert binding["accounted_prs"] == [123]
    assert "issues" not in binding
    record.write_text("changed")
    with pytest.raises(ValueError, match="truth record changed"):
        ab.freeze_truth_prerequisite(tmp_path / "runs", identity, truth)


def test_collector_uses_canonical_reported_usage_and_null_missing(tmp_path):
    root = tmp_path / "runs"
    ab.atomic_json(root / "identity.json", {"identity_sha256": "x", "campaign_sha256": "y", "cases": [{"number": 1}]})
    output = root / "output.json"
    ab.atomic_json(output, {"review_comments": []})
    result = {"identity_sha256": "x", "campaign_sha256": "y", "preflight": False, "number": 1, "arm": "A", "repetition": 1,
              "status": "valid", "item": "review-pr1-A-r1", "normalized_output_path": str(output),
              "normalized_output_sha256": ab.digest(output.read_bytes()), "initial_document_pages": 1,
              "initial_knowledge_chars": 20, "injected_dimensions": {}, "error": "",
              "attempts": [{"attempt_root": str(root), "artifacts": {}, "usage": {"input_tokens": 42, "output_tokens": 9}}]}
    ab.atomic_json(root / "items/review-pr1-A-r1/result.json", result)
    collection = ab.collect(root)
    reported = collection["by_arm"]["A"]["reported_usage"]
    assert reported["input_tokens"]["reported_subtotal"] == 42
    assert reported["cache_read_input_tokens"]["reported_subtotal"] is None
    assert reported["total_tokens"]["missing_calls"] == 1
    manifest = ab.read_json(root / "reviews-manifest.json")
    row = manifest["reviews"][0]
    assert row["repeat"] == 0
    assert row["normalized_output_sha256"] == ab.digest(output.read_bytes())
    assert row["run_result_sha256"] == ab.digest(Path(row["run_result_path"]).read_bytes())
    assert row["identity_sha256"] == manifest["identity_sha256"] == "x"
    assert row["campaign_sha256"] == manifest["campaign_sha256"] == "y"
