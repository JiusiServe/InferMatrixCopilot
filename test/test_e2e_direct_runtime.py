"""Real reservation/child/executor/polling, with only a temporary fake model CLI."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from infermatrix_copilot.sdk.v1 import (ChangedPath, DirectReviewRequest,
    DirectReviewRunRequest, RepositoryRef, ReviewRuntime, ReviewRuntimeConfig, StrictRuntime)


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def setup(tmp_path, monkeypatch, provider, count):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "offline@example.invalid")
    git(repo, "config", "user.name", "offline")
    (repo / "source.py").write_text("value = 1\n")
    git(repo, "add", "source.py")
    git(repo, "commit", "-qm", "snapshot")
    git(repo, "remote", "add", "origin", "https://github.com/vllm-project/vllm-omni.git")
    head = git(repo, "rev-parse", "HEAD")
    payload = {"reviewed_head_sha": head, "summary": "Reviewed exact frozen source.",
        "findings": [{"severity":"P1", "title":f"Issue {i}", "body":"Verified source evidence",
                      "path":"source.py", "line":i + 1} for i in range(count)],
        "review_checks": {}, "subtraction_signal":"none", "subtraction":[], "minimality_proof":None,
        "existing_feedback_status":"checked", "finding_rechecks":[],
        "finding_dispositions":[{"anchor":f"source.py:{i + 1}", "disposition":"new",
                                 "existing_thread":"", "head_recheck":""} for i in range(count)]}
    cli = tmp_path / "fake_model.py"
    cli.write_text('''import json, os, pathlib, sys
prompt = sys.stdin.read()
assert "Provider-issued knowledge context" in prompt
assert "GH_TOKEN" not in os.environ
payload = ''' + repr(payload) + '''
if "--output-last-message" in sys.argv:
    assert sys.argv[sys.argv.index("--sandbox") + 1] == "read-only"
    pathlib.Path(sys.argv[sys.argv.index("--output-last-message") + 1]).write_text(json.dumps(payload))
else:
    assert "--mode=ask" in sys.argv and "--force" not in sys.argv
    print(json.dumps({"type":"result", "subtype":"success", "result":json.dumps(payload)}))
''')
    monkeypatch.setenv("PYTHONPATH", str(Path(__file__).resolve().parents[1] / "src"))
    monkeypatch.setenv("GH_TOKEN", "publisher-secret-must-not-reach-model")
    repository = RepositoryRef(alias="vllm-omni", full_name="vllm-project/vllm-omni")
    config = ReviewRuntimeConfig(repository, str(repo), str(tmp_path), run_root=str(tmp_path / "runs"))
    request = DirectReviewRunRequest(DirectReviewRequest("offline", repository, 7, head, "change", "body",
        (ChangedPath("source.py", "modified"),)), str(repo), f"offline-{provider}-{count}", "Frozen business input",
        {"type":"object"}, {"provider":provider, "command":[sys.executable, str(cli)],
            "model":"auto" if provider == "cursor" else "", "idle_timeout_s":5, "absolute_timeout_s":5})
    from dataclasses import replace
    config = replace(config, direct_profiles={provider: request.profile})
    return config, request


def poll(runtime, run_id):
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        result = runtime.get_result(run_id)
        if result.terminal:
            return result
        time.sleep(.05)
    raise AssertionError("offline Direct child did not finish")


@pytest.mark.parametrize("provider", ["codex", "cursor"])
@pytest.mark.parametrize("count", [0, 2])
def test_reserved_direct_runs_on_executor_and_old_runtime_alias(tmp_path, monkeypatch, provider, count):
    config, request = setup(tmp_path, monkeypatch, provider, count)
    assert StrictRuntime is ReviewRuntime
    with ReviewRuntime(config=config) as runtime:
        first = runtime.reserve_direct_review(request)
        second = runtime.reserve_direct_review(request)
        assert first.created and not second.created and first.run_id == second.run_id
        result = poll(runtime, first.run_id)
    assert result.state == "done", result.payload
    assert len(result.review.direct_result["findings"]) == count
    run_dir = Path(config.run_root) / first.run_id
    assert json.loads((run_dir / "knowledge.json").read_text())["injection_status"] == "confirmed"
    events = [json.loads(line) for line in (run_dir / "run_trace.jsonl").read_text().splitlines()]
    assert {row.get("spec") for row in events if row.get("kind") == "step_result"} == {
        "review.direct.prepare", "review.direct.model", "review.direct.complete"}
    assert json.loads((run_dir / "direct-context.json").read_text())["expected_head_sha"] == request.review.expected_head_sha
    with ReviewRuntime(config=config) as recovered:
        handle = recovered.find_review(request.idempotency_key, expected_head_sha=request.review.expected_head_sha)
        assert handle.run_id == first.run_id and not handle.created
        assert recovered.get_result(handle.run_id).review.direct_result == result.review.direct_result


def test_unregistered_and_queued_tampered_command_never_runs(tmp_path, monkeypatch):
    from dataclasses import replace
    from infermatrix_copilot.sdk.v1 import InvalidRequestError
    config, request = setup(tmp_path, monkeypatch, "codex", 0)
    with ReviewRuntime(config=replace(config, direct_profiles={})) as runtime:
        with pytest.raises(InvalidRequestError, match="trusted deployment"):
            runtime.reserve_direct_review(request)
    with ReviewRuntime(config=config) as runtime:
        monkeypatch.setattr(runtime._core._q, "put", lambda *args: None)
        handle = runtime.reserve_direct_review(request)
        path = Path(config.run_root) / handle.run_id / "request.json"
        saved = json.loads(path.read_text())
        saved["params"]["direct_review"]["profile"]["command"] = ["bash", "-c", "touch forbidden"]
        path.write_text(json.dumps(saved))
        monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: pytest.fail("tampered command launched"))
        with pytest.raises(ValueError, match="request changed"):
            runtime._core._launch(handle.run_id)


def test_child_refuses_request_changed_after_parent_authorization(tmp_path, monkeypatch):
    import asyncio
    import hashlib
    from infermatrix_copilot.engine.steps.review.direct_run import execute
    from infermatrix_copilot.sdk.v1 import InvalidRequestError
    config, request = setup(tmp_path, monkeypatch, "codex", 0)
    with ReviewRuntime(config=config) as runtime:
        monkeypatch.setattr(runtime._core._q, "put", lambda *args: None)
        handle = runtime.reserve_direct_review(request)
        run_dir = Path(config.run_root) / handle.run_id
        path = run_dir / "request.json"
        monkeypatch.setenv("COPILOT_DIRECT_REQUEST_SHA256", hashlib.sha256(path.read_bytes()).hexdigest())
        monkeypatch.setenv("COPILOT_DIRECT_PROFILE", json.dumps(request.profile))
        saved = json.loads(path.read_text())
        saved["params"]["direct_review"]["prompt"] = "changed after launch"
        path.write_text(json.dumps(saved))
        monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: pytest.fail("tampered child invoked model"))
        with pytest.raises(InvalidRequestError, match="changed after its authorized launch"):
            asyncio.run(execute(runtime._core.settings, run_dir))


@pytest.mark.parametrize("invalid_json, expected", [(False, "backend"), (True, "invalid_result")])
def test_direct_terminal_failures_preserve_typed_category(tmp_path, monkeypatch, invalid_json, expected):
    config, request = setup(tmp_path, monkeypatch, "codex", 0)
    cli = Path(request.profile["command"][1])
    if invalid_json:
        cli.write_text("import pathlib,sys\npathlib.Path(sys.argv[sys.argv.index('--output-last-message')+1]).write_text('invalid-json')\n")
    else:
        cli.write_text("raise SystemExit(42)\n")
    with ReviewRuntime(config=config) as runtime:
        handle = runtime.reserve_direct_review(request)
        result = poll(runtime, handle.run_id)
    assert result.state != "done"
    assert result.payload["execution_failure"]["failure_class"] == expected
    pin = json.loads((Path(config.run_root) / handle.run_id / "knowledge.json").read_text())
    assert pin["injection_status"] == "unknown"
    assert not pin["knowledge_usage"].get("injected_units")


@pytest.mark.parametrize("mutation", ["drop_marker", "replace_params"])
def test_direct_dispatch_identity_survives_untrusted_marker_changes(tmp_path, monkeypatch, mutation):
    config, request = setup(tmp_path, monkeypatch, "codex", 0)
    with ReviewRuntime(config=config) as runtime:
        monkeypatch.setattr(runtime._core._q, "put", lambda *args: None)
        handle = runtime.reserve_direct_review(request)
        path = Path(config.run_root) / handle.run_id / "request.json"
        saved = json.loads(path.read_text())
        if mutation == "drop_marker":
            saved["params"].pop("direct_review")
        else:
            saved["params"] = {"review_depth":"standard"}
        path.write_text(json.dumps(saved))
        monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: pytest.fail("changed mode launched a child"))
        with pytest.raises(ValueError, match="request changed"):
            runtime._core._launch(handle.run_id)
        with pytest.raises(ValueError, match="request changed"):
            runtime.find_review(request.idempotency_key, expected_head_sha=request.review.expected_head_sha)
