"""Provider registry: selection, harness targets, the HarnessLLM adapter, and
the run_harness_step seam (doc/RFC-provider-registry.md)."""

from types import SimpleNamespace

import pytest

from infermatrix_copilot import providers
from infermatrix_copilot.config import Settings
from infermatrix_copilot.llm import LLM, Block, Reply
from infermatrix_copilot.providers import (
    HarnessLLM,
    llm_for,
    resolve_provider,
    transport_for,
)
from infermatrix_copilot.scopes import read_only_scope


def _settings(**kw) -> Settings:
    return Settings(_env_file=None, **kw)


class FakeTransport:
    def __init__(self):
        self.calls = []
        self.cli = "/fake/cursor-agent"

    def cli_path(self):
        return self.cli

    def complete(self, **kwargs):
        self.calls.append(kwargs)
        return Reply(blocks=[Block(type="text", text="ok")])

    def run_session(self, req):
        from infermatrix_copilot.agent_loop import AgentOutcome

        self.calls.append(req)
        return AgentOutcome(text='{"status": "success"}', iterations=1,
                            tool_calls=0)


# -- selection ---------------------------------------------------------------
def test_empty_selection_resolves_api():
    assert resolve_provider(_settings()).id == "api"
    assert resolve_provider(_settings()).kind == "api"


def test_unknown_backend_rejected_at_startup():
    with pytest.raises(Exception, match="STRICT_BACKEND"):
        _settings(strict_backend="not-a-backend")


def test_every_harness_id_resolves_a_transport():
    for backend in ("cursor", "claude-code", "codex"):
        transport = transport_for(_settings(strict_backend=backend))
        assert transport.spec.id == backend
        assert transport.spec.kind == "harness"


def test_unshipped_mechanism_names_the_milestone(monkeypatch):
    from infermatrix_copilot.providers import registry

    monkeypatch.setitem(registry._UNSHIPPED, "codex", "M9")
    with pytest.raises(NotImplementedError, match="M9"):
        transport_for(_settings(strict_backend="codex"))


def test_api_provider_has_no_harness_transport():
    with pytest.raises(ValueError, match="not a harness"):
        transport_for(_settings(strict_backend="api"))


# -- harness targets ---------------------------------------------------------
def test_harness_target_shape_and_host_label():
    settings = _settings(strict_backend="cursor",
                         strict_backend_model="composer-2.5")
    target = settings.tier_target("eco")
    assert (target.kind, target.provider_id) == ("harness", "cursor")
    assert target.model == "composer-2.5"
    assert (target.base_url, target.api_key) == ("", "")  # auth lives in the CLI
    assert target.host == "cli:cursor"
    assert target.source == "backend:cursor"


def test_harness_serves_performance_mode_without_tier_config():
    # tier backends do not apply under a harness — performance must not raise
    target = _settings(strict_backend="cursor").tier_target("performance")
    assert target.kind == "harness"


def test_api_target_unchanged_by_default():
    target = _settings(anthropic_api_key="k").tier_target("eco")
    assert (target.kind, target.provider_id) == ("api", "api")
    assert target.host == "api.anthropic.com"


# -- llm_for -----------------------------------------------------------------
def test_llm_for_api_returns_the_real_client():
    assert isinstance(llm_for(_settings(anthropic_api_key="k")), LLM)


def test_llm_for_harness_returns_adapter_and_absence_degrades(monkeypatch):
    monkeypatch.setattr("infermatrix_copilot.providers.base.shutil.which",
                        lambda name: None)
    adapter = llm_for(_settings(strict_backend="cursor"))
    assert isinstance(adapter, HarnessLLM)
    assert adapter.available is False  # missing CLI == missing key: degrade


# -- HarnessLLM --------------------------------------------------------------
def test_harness_llm_refuses_tools():
    adapter = HarnessLLM(_settings(strict_backend="cursor"), FakeTransport())
    with pytest.raises(RuntimeError, match="tool-less"):
        adapter.create(system="s", messages=[], tools=[{"name": "grep"}])


def test_harness_llm_delegates_toolless_create_and_streams():
    transport = FakeTransport()
    adapter = HarnessLLM(
        _settings(strict_backend="cursor", strict_backend_model="m1"),
        transport)
    streamed = []
    reply = adapter.create(system="s",
                           messages=[{"role": "user", "content": "hi"}],
                           on_text=streamed.append)
    assert reply.text == "ok" and streamed == ["ok"]
    assert transport.calls[0]["model"] == "m1"  # backend model applied


def test_harness_llm_members_get_a_real_api_client():
    adapter = HarnessLLM(_settings(strict_backend="cursor"), FakeTransport())
    member = SimpleNamespace(api_key="k", base_url="")
    assert isinstance(adapter.for_member(member), LLM)


def test_harness_llm_for_target_routes_api_targets_to_real_client():
    adapter = HarnessLLM(_settings(strict_backend="cursor"), FakeTransport())
    api_target = SimpleNamespace(kind="api", model="m", base_url="",
                                 api_key="k", provider="anthropic")
    assert isinstance(adapter.for_target(api_target), LLM)
    harness_target = SimpleNamespace(kind="harness")
    assert adapter.for_target(harness_target) is adapter


# -- run_harness_step seam ---------------------------------------------------
def test_run_harness_step_writes_bridge_spec_and_delegates(tmp_path, monkeypatch):
    transport = FakeTransport()
    monkeypatch.setattr(providers, "transport_for", lambda s: transport)
    settings = _settings(strict_backend="cursor",
                         strict_backend_timeout_s=42.0)
    ctx = SimpleNamespace(settings=settings,
                          state={"task_spec": {"repo": "vllm-omni"}},
                          run_dir=tmp_path, trace=None)
    scope = read_only_scope()
    target = settings.tier_target("eco")

    outcome = providers.run_harness_step(
        ctx, target, step_name="agent.review_diff#lens0",
        system="SYS", prompt="PROMPT", scope=scope, max_iters=7)

    assert outcome.text == '{"status": "success"}'
    req = transport.calls[0]
    assert (req.system, req.prompt, req.max_iters) == ("SYS", "PROMPT", 7)
    assert req.timeout_s == 42.0
    assert req.bridge_spec_path is not None and req.bridge_spec_path.is_file()
    assert req.bridge_spec_path.parent == tmp_path / "bridge"
