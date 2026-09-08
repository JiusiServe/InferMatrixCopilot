"""AFD harness bridge exercised through real MCP handlers, entirely offline."""

from __future__ import annotations

import asyncio
import json
import os
import shlex
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from infermatrix_copilot.agent_loop import AgentOutcome
from infermatrix_copilot.config import Settings
from infermatrix_copilot.engine.steps import rebase_v3
from infermatrix_copilot.providers.base import AgentSessionRequest
from infermatrix_copilot.providers.codex import CodexTransport
from infermatrix_copilot.rebase_engine.prompt_builder import ModulePromptData, build_module_prompt
from infermatrix_copilot.rebase_engine.rebase_tools import RebasePaths, load_tool_schemas
from infermatrix_copilot.rebase_engine.substate import Substate
from infermatrix_copilot.run_trace import RunTrace
from infermatrix_copilot.tool_bridge import build_server

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "adapters" / "afd_plugin" / "rebase"


@pytest.fixture()
def bridge_env(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "subject.py").write_text("version = 'old'\n")
    (repo / "test_subject.py").write_text(
        "import os, subject\n"
        "def test_adaptation():\n"
        "    assert subject.version == 'fixed'\n"
        "    assert os.environ['VIRTUAL_ENV'].endswith('target-env')\n")
    target_venv = tmp_path / "target-env"
    (target_venv / "bin").mkdir(parents=True)
    for name in ("python", "python3"):
        executable = target_venv / "bin" / name
        executable.write_text(f"#!/bin/sh\nexec {shlex.quote(sys.executable)} \"$@\"\n")
        executable.chmod(0o755)
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    (upstream / "reference.py").write_text("version = 'fixed'\n")
    run = tmp_path / "run"
    run.mkdir()
    settings = Settings(
        _env_file=None, strict_backend="codex", strict_backend_model="test-model",
        adapters_dir=ROOT / "adapters", knowledge_dir=ROOT / "knowledge",
        memory_db=tmp_path / "memory.db", imx_knowledge_runtime="")
    ctx = SimpleNamespace(
        settings=settings, run_dir=run, trace=RunTrace(run / "trace.jsonl"),
        item="plugin_boundary", params={},
        state={"repo_path": str(repo), "upstream_path": str(upstream), "run_id": "offline-bridge",
               "task_spec": {"repo": "afd-plugin", "mode": "eco"}})
    manifest = {"repo": {"venv": str(target_venv)},
                "modules": {"plugin_boundary": {"local_paths": ["subject.py"]}},
                "rebase": {"testing": {"pytest_command": "python -m pytest"}}}
    target_env = {"PATH": str(target_venv / "bin") + os.pathsep + os.environ["PATH"],
                  "HOME": str(tmp_path), "PYTHONPATH": str(repo), "VIRTUAL_ENV": str(target_venv),
                  "CUDA_VISIBLE_DEVICES": ""}
    paths = RebasePaths(str(repo), str(upstream), env=target_env)
    definitions = load_tool_schemas(ADAPTER / "tool_schemas.json")
    scope = rebase_v3._module_scope(str(repo), "plugin_boundary", manifest, run)
    return ctx, manifest, paths, definitions, scope


def mcp_request(server, name, arguments):
    types = pytest.importorskip("mcp.types")
    request = types.CallToolRequest(
        method="tools/call", params=types.CallToolRequestParams(
            name=name, arguments=arguments))
    response = asyncio.run(server._mcp_server.request_handlers[types.CallToolRequest](request))
    return response.root


def test_module_completion_uses_real_mcp_tools_and_target_runtime(bridge_env, monkeypatch):
    """Exercise actual module step -> fake Codex -> MCP -> tools -> pytest.

    Only the transport and fixture manifest are replaced. The nested plan
    reviewer takes the same fake Codex path and must never construct Anthropic.
    """
    types = pytest.importorskip("mcp.types")
    ctx, manifest, paths, definitions, scope = bridge_env
    review_prompts = []
    Substate(ctx.run_dir, "offline-bridge").update({"upstream_tracking": {
        "main_sha": "a" * 40, "selected_sha": "b" * 40,
        "version": "0.29.0.dev7", "index_url": "https://wheels.example/commit/cu130/"}})
    monkeypatch.setattr(rebase_v3, "_adapter_manifest", lambda _: manifest)
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "")

    def forbid_anthropic(*args, **kwargs):
        pytest.fail("Codex rebase must not construct an Anthropic client")

    monkeypatch.setattr("anthropic.Anthropic", forbid_anthropic)
    monkeypatch.setattr("anthropic.AsyncAnthropic", forbid_anthropic)
    sessions = []

    class OfflineHarness:
        def cli_path(self):
            return "offline-codex"

        def auth_gap(self):
            return None

        def complete(self, *, system, messages, model, max_tokens, role):
            assert model == "test-model" and role == "plan_reviewer"
            review_prompts.append(messages[0]["content"])
            return SimpleNamespace(
                text='{"verdict":"approve","summary":"Compatible API change","concerns":[]}',
                stop_reason="end_turn")

        def run_session(self, request):
            sessions.append(request)
            assert request.bridge_managed_writes
            assert '"status":"success|failed|blocked"' in request.prompt
            assert "vllm==0.29.0.dev7" in request.prompt
            server = build_server(request.bridge_spec_path)
            if len(sessions) == 2:
                # A bounded first session ended after the decision. Its
                # automatic debug retry must retain the unlocked gate.
                imported = mcp_request(server, "run_import_check", {
                    "import_code": "import subject; assert subject.version == 'fixed'"})
                assert not imported.isError
                assert json.loads(imported.content[0].text)["exit_code"] == 0
                return AgentOutcome(text='{"status":"success","summary":"Retry verified API"}',
                                    iterations=1, tool_calls=1, truncated=False, refusals=[])
            listed = asyncio.run(server._mcp_server.request_handlers[types.ListToolsRequest](
                types.ListToolsRequest(method="tools/list"))).root.tools
            assert {t.name for t in listed} == {d["name"] for d in definitions}
            assert next(t for t in listed if t.name == "run_pytest").inputSchema["required"] == ["test_paths"]

            # The first attempt cannot change product code or run commands.
            refused = mcp_request(server, "write_file", {"file_path": "subject.py", "content": "bad"})
            assert refused.isError and "locked" in refused.content[0].text
            assert mcp_request(server, "run_shell", {"command": "true"}).isError
            assert mcp_request(server, "run_pytest", {"test_paths": ["test_subject.py"]}).isError
            inspected = mcp_request(server, "read_file", {"file_path": "subject.py"})
            assert not inspected.isError and "old" in inspected.content[0].text

            plan = ctx.run_dir / "plans/module-plugin_boundary/dispatch_initial/plan-v0-offline"
            for suffix, text in ((".json", '{"plan_id":"v0-offline","changes":["update API"]}'),
                                 (".md", "Update the API and run the targeted test.")):
                written = mcp_request(server, "write_file", {"file_path": str(plan) + suffix, "content": text})
                assert not written.isError
            decision_args = {"file_path": str(plan) + ".decision.md", "content": "Accept reviewer advice."}
            assert mcp_request(server, "write_file", decision_args).isError
            reviewed = mcp_request(server, "request_plan_review", {
                "plan_json_path": str(plan) + ".json", "plan_md_path": str(plan) + ".md", "kind": "rebase"})
            assert not reviewed.isError
            assert json.loads(reviewed.content[0].text)["verdict"] == "approve"
            assert mcp_request(server, "write_file", decision_args).isError is False

            edited = mcp_request(server, "edit_file", {
                "file_path": "subject.py", "old_string": "'old'", "new_string": "'fixed'"})
            assert not edited.isError
            assert mcp_request(server, "write_file", {
                "file_path": str(Path(paths.vllm_path) / "reference.py"), "content": "bad"}).isError
            for tool in ("run_pytest", "reproduce"):
                tested = mcp_request(server, tool, {"test_paths": ["test_subject.py"], "timeout": 30})
                assert not tested.isError
                result = json.loads(tested.content[0].text)
                assert result["exit_code"] == 0, result
                assert result["passed"]
            imported = mcp_request(server, "run_import_check", {
                "import_code": "import subject; assert subject.version == 'fixed'"})
            assert json.loads(imported.content[0].text)["exit_code"] == 0
            return AgentOutcome(text='{"status":"success","summary":"Updated API; tests passed"}',
                                iterations=1, tool_calls=12, truncated=True, refusals=[])

    def transport_for_id(settings, provider_id):
        assert provider_id == "codex" and settings.strict_backend == "codex"
        return OfflineHarness()

    monkeypatch.setattr("infermatrix_copilot.providers.registry.transport_for_id", transport_for_id)
    result = asyncio.run(rebase_v3._v3_module_rebase(ctx))
    assert result.ok, result
    assert result.outputs["state_updates"]["module_plugin_boundary_status"] == "done", result
    assert Substate(ctx.run_dir, "offline-bridge").get("modules.plugin_boundary.status") == "done"
    assert len(sessions) == 2 and len(review_prompts) == 1
    assert Substate(ctx.run_dir, "offline-bridge").get("modules.plugin_boundary.debug_attempts") == 1
    assert "Update the API" in review_prompts[0]
    assert list((ctx.run_dir / "tests").glob("**/*.log"))


def test_bridge_controlled_writes_keep_codex_native_read_only(bridge_env, monkeypatch):
    ctx, _, _, _, scope = bridge_env
    transport = CodexTransport(ctx.settings)
    calls = []

    def fake_run(text, **kwargs):
        calls.append(kwargs)
        return [{"item": {"type": "agent_message", "text": "{}"}}], False

    monkeypatch.setattr(transport, "_run", fake_run)
    transport.run_session(AgentSessionRequest(
        system="offline", prompt="offline", scope=scope, model="test-model", max_iters=1,
        timeout_s=5, run_dir=ctx.run_dir, bridge_managed_writes=True))
    assert calls[0]["sandbox"] == "read-only"


def test_debug_step_uses_the_same_bridge_without_relocking_the_plan(bridge_env, monkeypatch):
    pytest.importorskip("mcp.types")
    ctx, manifest, paths, _, _ = bridge_env
    calls = []

    class OfflineHarness:
        def cli_path(self):
            return "offline-codex"

        def auth_gap(self):
            return None

        def run_session(self, request):
            calls.append(request)
            assert request.step_name == "rebase.debug.unit-subject"
            assert request.bridge_managed_writes
            assert '"status":"success|failed|blocked"' in request.prompt
            server = build_server(request.bridge_spec_path)
            edited = mcp_request(server, "edit_file", {
                "file_path": "subject.py", "old_string": "'old'", "new_string": "'fixed'"})
            assert not edited.isError
            return AgentOutcome(text='{"status":"success","summary":"Fixed API"}',
                                iterations=1, tool_calls=1, truncated=False, refusals=[])

    monkeypatch.setattr("infermatrix_copilot.providers.registry.transport_for_id",
                        lambda *args: OfflineHarness())
    result = asyncio.run(rebase_v3._run_debug_agent(
        ctx, manifest, "plugin_boundary", "unit-subject", "old API failed"))
    assert result == "done"
    assert len(calls) == 1
    assert (Path(paths.omni_path) / "subject.py").read_text() == "version = 'fixed'\n"


def test_afd_import_prompt_is_an_executable_python_command(bridge_env):
    ctx, _, paths, _, _ = bridge_env
    data = ModulePromptData.load(ADAPTER)
    prompt = build_module_prompt(
        "plugin_boundary", data, vllm_path=paths.vllm_path, omni_path=paths.omni_path,
        script_dir=str(ADAPTER), log_dir=str(ctx.run_dir), live=True,
        run_git=lambda *args: "offline")
    command = prompt.split("Run this import check when applicable:\n", 1)[1].splitlines()[0]
    assert shlex.split(command) == ["python3", "-c", "import afd_plugin; print('OK')"]
