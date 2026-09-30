"""Per-call spend thresholds: `claude --max-budget-usd` on one-shots, and the
knowledge gateway refusing to dispatch a thresholded call to a transport that
cannot stop at one. The threshold is checked after each API request, so it
bounds the overshoot to one request; a hard ceiling is the caller's
reservation of threshold + one request's worst case. Fully offline."""

import json
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from infermatrix_copilot.config import Settings
from infermatrix_copilot.kb_service.models import ModelGateway, ModelRole, ModelUnavailable
from infermatrix_copilot.providers.base import HarnessTransport
from infermatrix_copilot.providers.claude_code import ClaudeCodeTransport
from infermatrix_copilot.providers.codex import CodexTransport
from infermatrix_copilot.providers.cursor import CursorTransport

_FAKE_CLI = """#!/usr/bin/env python3
import json, os, sys
here = os.path.dirname(os.path.abspath(__file__))
sys.stdin.read()
with open(os.path.join(here, "capture.json"), "w") as f:
    json.dump({"argv": sys.argv[1:]}, f)
over = os.path.exists(os.path.join(here, "over_budget"))
print(json.dumps({
    "type": "result", "subtype": "error_max_budget_usd" if over else "success",
    "is_error": over, "result": "partial" if over else '{"ok": true}',
    "num_turns": 1, "stop_reason": "end_turn", "total_cost_usd": 0.07,
    "usage": {"input_tokens": 10, "output_tokens": 2},
    "modelUsage": {"claude-opus-5-5": {"costUSD": 0.07}}}))
"""


def _claude(tmp_path: Path) -> ClaudeCodeTransport:
    cli = tmp_path / "bin" / "claude"
    cli.parent.mkdir(exist_ok=True)
    cli.write_text(_FAKE_CLI, encoding="utf-8")
    cli.chmod(cli.stat().st_mode | stat.S_IXUSR)
    return ClaudeCodeTransport(Settings(_env_file=None, strict_backend="claude-code",
                                        strict_backend_cli=str(cli)))


def _argv(tmp_path: Path) -> list[str]:
    return json.loads((tmp_path / "bin" / "capture.json").read_text(encoding="utf-8"))["argv"]


MESSAGES = [{"role": "user", "content": "hi"}]


def test_claude_passes_the_cap_only_when_given(tmp_path):
    transport = _claude(tmp_path)
    transport.complete(system="S", messages=MESSAGES)
    assert "--max-budget-usd" not in _argv(tmp_path)

    reply = transport.complete(system="S", messages=MESSAGES, max_budget_usd=0.5)
    argv = _argv(tmp_path)
    assert argv[argv.index("--max-budget-usd") + 1] == "0.5000"
    assert reply.usage["cost_usd"] == pytest.approx(0.07)
    assert reply.stop_reason == "end_turn"


def test_claude_reports_a_call_stopped_at_its_cap(tmp_path):
    transport = _claude(tmp_path)
    (tmp_path / "bin" / "over_budget").write_text("", encoding="utf-8")
    reply = transport.complete(system="S", messages=MESSAGES, max_budget_usd=0.01)
    assert reply.stop_reason == "max_budget"
    assert reply.text == ""  # a budget-truncated answer is never usable


def test_claude_rejects_a_non_positive_cap(tmp_path):
    with pytest.raises(ValueError):
        _claude(tmp_path).complete(system="S", messages=MESSAGES, max_budget_usd=0)


def test_only_claude_code_claims_to_stop_at_a_threshold():
    assert ClaudeCodeTransport.stops_at_spend is True
    assert HarnessTransport.stops_at_spend is False
    assert CodexTransport.stops_at_spend is False
    assert CursorTransport.stops_at_spend is False


def test_no_transport_advertises_a_hard_cap():
    """Regression: the CLI checks its budget after a request completes, so no
    transport may claim to bound a single call's spend. The old name
    (`supports_spend_cap`) promised exactly that and must not come back."""
    for cls in (HarnessTransport, ClaudeCodeTransport, CodexTransport, CursorTransport):
        assert not hasattr(cls, "supports_spend_cap")


class _Transport:
    """A gateway-level fake: records the kwargs it was called with."""

    def __init__(self, *, capped: bool, text: str = '{"ok": true}', stop: str = "end_turn",
                 usage: dict | None = None):
        self.stops_at_spend = capped
        self.calls: list[dict] = []
        self._reply = SimpleNamespace(blocks=[SimpleNamespace(text=text)], stop_reason=stop,
                                      usage=usage if usage is not None else {"cost_usd": 0.12},
                                      model="served-model")

    def complete(self, **kwargs):
        self.calls.append(kwargs)
        return self._reply


ROLE = ModelRole("generator", "claude-code", "claude-opus-5-5")


def _gateway(transport, records: list | None = None) -> ModelGateway:
    return ModelGateway(None, transport_factory=lambda provider: transport,
                        recorder=(records.append if records is not None else None))


def test_gateway_refuses_an_uncapped_transport_before_dispatch():
    transport = _Transport(capped=False)
    with pytest.raises(ModelUnavailable, match="cannot stop a call at a spend threshold"):
        _gateway(transport).call_json(ROLE, system="S", prompt="P", max_budget_usd=1.0)
    assert transport.calls == []  # fail-closed: nothing was sent


def test_gateway_passes_the_cap_and_surfaces_cost():
    transport = _Transport(capped=True)
    records: list = []
    reply = _gateway(transport, records).call_json(ROLE, system="S", prompt="P", max_budget_usd=1.5)
    assert transport.calls[0]["max_budget_usd"] == 1.5
    assert reply.cost_usd == pytest.approx(0.12)
    assert records[-1]["cost_usd"] == pytest.approx(0.12)
    assert records[-1]["max_budget_usd"] == 1.5


def test_gateway_without_a_cap_is_unchanged():
    """Existing callers pass no cap: the kwarg is not sent at all, so fakes
    and transports with the old signature keep working."""
    transport = _Transport(capped=False, usage={})
    reply = _gateway(transport).call_json(ROLE, system="S", prompt="P")
    assert "max_budget_usd" not in transport.calls[0]
    assert reply.cost_usd is None
    assert reply.data == {"ok": True}


def test_gateway_treats_a_call_stopped_at_its_cap_as_unavailable():
    transport = _Transport(capped=True, text="", stop="max_budget")
    records: list = []
    with pytest.raises(ModelUnavailable, match="spend threshold"):
        _gateway(transport, records).call_json(ROLE, system="S", prompt="P", max_budget_usd=0.2)
    assert records[-1]["error"]  # recorded as a failure, never a training example


def test_gateway_rejects_a_non_positive_cap():
    with pytest.raises(ModelUnavailable, match="positive"):
        _gateway(_Transport(capped=True)).call_json(ROLE, system="S", prompt="P", max_budget_usd=-1)
