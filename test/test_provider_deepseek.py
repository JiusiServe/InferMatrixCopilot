"""DeepSeek Harness transport — fully offline.

The SDK is not a CLI we can fake with a shell script (it is an in-process
Python class that spawns its own runtime), so the seam under test is the
`DeepSeekHarness` constructor+run: a stub class records exactly the config it
was handed and returns a scripted `RunResult`. That covers the two things
worth guarding — the generated Cordis composition, and the mapping from
`finish_reason` onto `AgentOutcome` — without touching the network.
"""

import sys
import types
from dataclasses import dataclass, field, replace
from pathlib import Path

import pytest

from infermatrix_copilot.config import Settings
from infermatrix_copilot.providers.base import AgentSessionRequest
from infermatrix_copilot.providers.deepseek import DeepSeekHarnessTransport
from infermatrix_copilot.providers.registry import transport_for_id
from infermatrix_copilot.scopes import read_only_scope
from infermatrix_copilot.tool_bridge import write_bridge_spec


@dataclass
class _FakeRunResult:
    session_id: str = "s1"
    final_response: str = "REVIEW"
    finish_reason: str = "completed"
    events: list = field(default_factory=list)
    notifications: list = field(default_factory=list)
    session_root: str = ""


class _FakeHarness:
    """Records construction kwargs; returns the scripted result."""

    captured: dict = {}
    result = _FakeRunResult()
    raises: Exception | None = None

    def __init__(self, **kwargs):
        type(self).captured = dict(kwargs)
        if type(self).raises is not None:
            raise type(self).raises

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def run(self, prompt, **kwargs):
        type(self).captured["prompt"] = prompt
        return type(self).result


@pytest.fixture
def fake_sdk(monkeypatch):
    """Install a stub `deepseek_harness` module and reset the fake."""
    module = types.ModuleType("deepseek_harness")
    module.DeepSeekHarness = _FakeHarness
    monkeypatch.setitem(sys.modules, "deepseek_harness", module)
    _FakeHarness.captured = {}
    _FakeHarness.result = _FakeRunResult()
    _FakeHarness.raises = None
    return _FakeHarness


def _settings(**kw):
    # _env_file=None: the repo .env holds a real DeepSeek key, and a test that
    # silently picks it up would pass for the wrong reason (and could spend).
    kw.setdefault("anthropic_api_key", "sk-test")
    return Settings(_env_file=None, strict_backend="deepseek",
                    strict_backend_model="deepseek-v4-pro", **kw)


def _request(tmp_path, *, bridge=True, read_only=True):
    (tmp_path / "worktree").mkdir(exist_ok=True)
    scope = replace(read_only_scope(), root=str(tmp_path / "worktree"),
                    read_only=read_only)
    run_dir = tmp_path / "run"
    run_dir.mkdir(exist_ok=True)
    spec = (write_bridge_spec(run_dir=run_dir, step_name="agent.review#lens",
                              scope=scope, repo="vllm-omni")
            if bridge else None)
    return AgentSessionRequest(
        system="SYSTEM", prompt="PROMPT", scope=scope,
        model="deepseek-v4-pro", max_iters=14, timeout_s=60.0,
        run_dir=run_dir, step_name="agent.review#lens",
        bridge_spec_path=spec)


def test_registry_resolves_deepseek():
    t = transport_for_id(_settings(), "deepseek")
    assert isinstance(t, DeepSeekHarnessTransport)
    assert "api_keyed" in t.spec.capabilities


def test_composition_pins_sandbox_and_never_grants_full_access(tmp_path):
    """The upstream minimal composition ships danger-full-access; on a shared
    machine that is not acceptable, so the generated one must pin the mode to
    the step's own scope and must never emit the dangerous value."""
    t = DeepSeekHarnessTransport(_settings())
    ro = t._composition(run_dir=tmp_path, step_name="s", cwd=tmp_path,
                        read_only=True, bridge_spec_path=None).read_text()
    rw = t._composition(run_dir=tmp_path, step_name="s2", cwd=tmp_path,
                        read_only=False, bridge_spec_path=None).read_text()
    assert "mode: read-only" in ro
    assert "mode: workspace-write" in rw
    assert "danger-full-access" not in ro
    assert "danger-full-access" not in rw
    # minimal's defining properties: no compaction plugin, no skills, no
    # runtime-context injection
    assert "compaction" not in ro
    assert "includeRuntimeContext: false" in ro
    assert "enabled: false" in ro
    # a truncated turn must be reported, never silently accepted
    assert "maxTokensAsSuccess: false" in ro


def test_composition_never_names_the_absent_mcp_plugin(tmp_path):
    """The bundled runtime compiles in 122 plugins and mcp-client is not one.
    Naming it does not fail fast -- the runtime dies on load while the SDK
    waits in initialize, which cost 30 minutes per lens when measured."""
    t = DeepSeekHarnessTransport(_settings())
    for spec in (tmp_path / "spec.json", None):
        text = t._composition(run_dir=tmp_path, step_name=f"s{spec}",
                              cwd=tmp_path, read_only=True,
                              bridge_spec_path=spec).read_text()
        assert "dsh-mcp-client" not in text
        assert "dsh-tool-bash-persistent" in text
        assert "dsh-tool-str-replace-editor" in text


def test_absent_plugin_fails_immediately_rather_than_timing_out(monkeypatch):
    """The guard that turns a boot failure into an instant, named error."""
    from infermatrix_copilot.providers import deepseek as mod
    monkeypatch.setattr(mod, "_runtime_plugins",
                        lambda: {"@deepseek-ai/dsh-fs-local"})
    with pytest.raises(RuntimeError, match="dsh-mcp-client"):
        mod._assert_plugins_bundled(
            "- id: x\n  name: '@deepseek-ai/dsh-mcp-client'\n")
    # an unscannable runtime must degrade to a no-op, never block a run
    monkeypatch.setattr(mod, "_runtime_plugins", lambda: set())
    mod._assert_plugins_bundled("- id: x\n  name: '@deepseek-ai/dsh-mcp-client'\n")


def test_unbridgeable_tools_are_traced_as_a_capability_gap(fake_sdk, tmp_path):
    """An arm that ran on native bash must never be describable as having had
    the tool bridge -- three arms in this campaign were already measured under
    labels they did not match."""
    class _Trace:
        def __init__(self): self.records = []
        def record(self, kind, **fields): self.records.append((kind, fields))
    trace = _Trace()
    req = _request(tmp_path)
    req.trace = trace
    DeepSeekHarnessTransport(_settings()).run_session(req)
    gaps = [f for k, f in trace.records if k == "capability_gap"]
    assert gaps and gaps[0]["capability"] == "review.mcp_tool_bridge"
    sessions = [f for k, f in trace.records if k == "harness_session"]
    assert sessions and sessions[0]["mcp_bridged"] is False


def test_env_never_leaks_model_endpoint_or_keys(tmp_path, monkeypatch):
    """An inherited ANTHROPIC_BASE_URL would silently reroute the harness."""
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://api.deepseek.com/anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-leak")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-leak2")
    t = DeepSeekHarnessTransport(_settings())
    env = t._env(cwd=tmp_path, model="m", system="S",
                 session_root=tmp_path / "sess")
    assert "ANTHROPIC_BASE_URL" not in env
    assert "ANTHROPIC_API_KEY" not in env
    assert "OPENAI_API_KEY" not in env
    assert env["DSH_MODEL"] == "m"
    assert env["DSH_SYSTEM_PROMPT"] == "S"


def test_run_session_maps_a_completed_run(fake_sdk, tmp_path):
    fake_sdk.result = _FakeRunResult(final_response="  FINDINGS  ",
                                     finish_reason="completed")
    t = DeepSeekHarnessTransport(_settings())
    out = t.run_session(_request(tmp_path))
    assert out.text == "FINDINGS"
    assert out.truncated is False
    assert out.refusals == []
    # credential travels through the SDK config, not the subprocess env
    assert fake_sdk.captured["api_key"] == "sk-test"
    assert "DEEPSEEK_API_KEY" not in fake_sdk.captured["env"]


def test_max_tokens_surfaces_as_truncation_not_success(fake_sdk, tmp_path):
    """The bug class this codebase already paid for: a pass that burns its
    completion ceiling must not read as a quietly accepted empty final."""
    fake_sdk.result = _FakeRunResult(final_response="", finish_reason="max-tokens")
    t = DeepSeekHarnessTransport(_settings())
    out = t.run_session(_request(tmp_path))
    assert out.truncated is True


def test_harness_failure_becomes_an_outcome_not_a_raise(fake_sdk, tmp_path):
    """A dead harness must not sink the ensemble: the lens reports empty with
    a refusal so the zero-yield retry can fire."""
    fake_sdk.raises = RuntimeError("runtime exploded")
    t = DeepSeekHarnessTransport(_settings())
    out = t.run_session(_request(tmp_path))
    assert out.text == ""
    assert out.refusals and "runtime exploded" in out.refusals[0]


def test_activity_parser_degrades_instead_of_inventing():
    t = DeepSeekHarnessTransport(_settings())
    calls, tools, usage = t._activity(["garbage", None, {"no": "kind"}])
    assert (calls, tools, usage.input_tokens, usage.output_tokens) == (0, [], 0, 0)
    calls, tools, usage = t._activity([
        {"kind": "tool/call", "data": {"name": "bash"}},
        {"kind": "tool/result", "data": {"name": "bash"}},
        {"kind": "turn/end", "data": {"usage": {"input_tokens": 7,
                                                "output_tokens": 3},
                                      "model": "deepseek-v4-pro"}},
    ])
    assert calls == 1 and tools == ["bash"]
    assert (usage.input_tokens, usage.output_tokens) == (7, 3)
    assert usage.served_model == "deepseek-v4-pro"


def test_auth_gap_reports_a_missing_credential(monkeypatch):
    t = DeepSeekHarnessTransport(_settings(anthropic_api_key="",
                                           openai_api_key=""))
    monkeypatch.setattr(t, "cli_path", lambda: "/usr/bin/python3")
    gap = t.auth_gap()
    assert gap and "DEEPSEEK_HARNESS_API_KEY" in gap


def test_require_cli_names_the_pip_install(monkeypatch):
    t = DeepSeekHarnessTransport(_settings())
    monkeypatch.setattr(t, "cli_path", lambda: None)
    with pytest.raises(RuntimeError, match="deepseek-harness-sdk"):
        t.require_cli()


def test_runaway_session_is_stopped_by_the_step_cap(fake_sdk, tmp_path):
    """dsh owns its own loop and its bundled runtime exposes no step cap, so
    max_iters cannot be handed to the harness. Measured on pr4816: two lenses
    finished in ~40 steps while a third ran 558 steps / 564 tool calls and was
    still going 50 minutes later. The cap is ours or there is none."""
    closed = {"n": 0}

    class _Runaway(_FakeHarness):
        def run(self, prompt, **kwargs):
            cb = kwargs.get("on_notification")
            for _ in range(10_000):          # a loop that never ends on its own
                if cb:
                    cb({"type": "step/end"})
                if closed["n"]:
                    raise RuntimeError("runtime closed")
            return _FakeRunResult()

        def close(self):
            closed["n"] += 1

    import sys as _sys
    _sys.modules["deepseek_harness"].DeepSeekHarness = _Runaway
    req = _request(tmp_path)
    req.max_iters = 5
    out = DeepSeekHarnessTransport(_settings()).run_session(req)
    assert closed["n"] >= 1, "the watchdog never closed the runaway harness"
    assert out.refusals and "step cap" in out.refusals[0]
