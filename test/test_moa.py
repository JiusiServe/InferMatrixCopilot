"""MoA (design W6): member resolution, eligibility, the atomic budget ledger,
budgeted-client fallbacks, ensemble member assignment, issue propose-aggregate
fallbacks, and the no-secret-in-traces guarantee."""

import json
import time

import pytest

from infermatrix_copilot.engine.agent_runtime.moa import (
    BudgetedLLM,
    Member,
    MoaBudget,
    MoaBudgetExceeded,
    moa_eligible,
    resolve_members,
)

MIX = {"members": [
    {"model": "deepseek-chat", "base_url": "https://api.example.com/v1",
     "api_key": "sk-SECRET-A"},
    {"model": "claude-sonnet-5", "api_key_env": "MOA_TEST_KEY"},
]}


# ---- config parsing / member resolution ------------------------------------

def test_malformed_llm_mixture_degrades_to_off(monkeypatch):
    from infermatrix_copilot.config import Settings

    monkeypatch.setenv("LLM_MIXTURE", "{not json")
    assert Settings().llm_mixture == {}


def test_resolve_members_secret_env_and_pricing_gate(settings, monkeypatch):
    monkeypatch.setenv("MOA_TEST_KEY", "sk-SECRET-B")
    settings.llm_mixture = {"members": MIX["members"] + [
        {"model": "totally-unpriced-model-x"}]}
    members = resolve_members(settings)
    assert [m.model for m in members] == ["deepseek-chat", "claude-sonnet-5"]
    assert members[0].api_key == "sk-SECRET-A"
    assert members[1].api_key == "sk-SECRET-B"     # resolved via api_key_env
    # labels never contain key material
    assert all("SECRET" not in m.label() for m in members)


def test_member_cap(settings):
    settings.llm_mixture = {"members": [
        {"model": "deepseek-chat"}] * 6}
    settings.moa_max_members = 3
    assert len(resolve_members(settings)) == 3


# ---- eligibility -----------------------------------------------------------

@pytest.mark.parametrize("when,kind,mode,depth,expect", [
    ("off", "pr_review", "performance", "full", False),
    ("full", "pr_review", "eco", "full", True),
    ("full", "pr_review", "eco", "light", False),
    ("full", "pr_review", "performance", "standard", True),
    ("full", "issue_answer", "eco", "", False),
    ("full", "issue_answer", "performance", "", True),
    ("performance", "pr_review", "eco", "full", False),
    ("always", "issue_answer", "eco", "", True),
])
def test_moa_eligibility_matrix(settings, when, kind, mode, depth, expect):
    settings.moa_when = when
    assert moa_eligible(settings, kind=kind, mode=mode, depth=depth) is expect


# ---- budget ledger ---------------------------------------------------------

def _budget(max_usd=1.0, deadline_s=60.0):
    return MoaBudget(max_usd=max_usd, deadline=time.monotonic() + deadline_s,
                     member_timeout_s=30.0)


def test_reservations_are_atomic_and_capped():
    b = _budget(max_usd=1.0)
    r1 = b.reserve(0.6)
    assert r1 is not None
    assert b.reserve(0.6) is None and b.tripped       # 0.6+0.6 > 1.0
    b.settle(r1, 0.1)                                  # actual << reserved
    assert b.spent() == pytest.approx(0.1)
    assert b.reserve(0.6) is not None                  # freed headroom returns


def test_settled_never_exceeds_reserved():
    b = _budget(max_usd=1.0)
    rid = b.reserve(0.2)
    b.settle(rid, 5.0)   # a lying provider cannot blow the cap
    assert b.spent() == pytest.approx(0.2)


def test_expired_deadline_refuses_reservation():
    b = _budget(deadline_s=-1.0)
    assert b.reserve(0.01) is None


# ---- BudgetedLLM -----------------------------------------------------------

class FakeClient:
    def __init__(self, settings, text='{"status": "success"}'):
        self.settings = settings
        self.available = True
        self.calls = []

    def create(self, **kw):
        self.calls.append(kw)

        class R:
            text = '{"status": "success"}'
            usage = {"input_tokens": 100, "output_tokens": 10}
            blocks = []
        return R()


def test_budgeted_llm_strict_raises_when_capped(settings):
    m = Member(model="deepseek-chat")
    b = _budget(max_usd=0.0)          # nothing can reserve
    wrapped = BudgetedLLM(m, FakeClient(settings), b)
    with pytest.raises(MoaBudgetExceeded):
        wrapped.create(system="s", messages=[{"role": "user", "content": "x"}])


def test_budgeted_llm_fallback_reroutes_to_tier(settings):
    m = Member(model="deepseek-chat")
    b = _budget(max_usd=0.0)
    tier = FakeClient(settings)
    wrapped = BudgetedLLM(m, FakeClient(settings), b,
                          fallback=(tier, "tier-model"))
    wrapped.create(system="s", messages=[{"role": "user", "content": "x"}])
    assert tier.calls and tier.calls[0]["model"] == "tier-model"


def test_budgeted_llm_settles_actual_usage(settings):
    m = Member(model="deepseek-chat")
    b = _budget(max_usd=1.0)
    member_client = FakeClient(settings)
    wrapped = BudgetedLLM(m, member_client, b)
    wrapped.create(system="s", messages=[{"role": "user", "content": "x"}],
                   max_tokens=50)
    assert member_client.calls[0]["model"] == "deepseek-chat"
    assert member_client.calls[0]["role"] == "moa_member"
    assert 0 < b.spent() < 0.001      # 110 deepseek tokens ≈ micro-dollars


# ---- no secrets in traces ---------------------------------------------------

def test_no_secret_material_in_trace_events(settings, trace, monkeypatch):
    monkeypatch.setenv("MOA_TEST_KEY", "sk-SECRET-B")
    settings.llm_mixture = MIX
    members = resolve_members(settings)
    trace.record("moa_dispatch", members=[m.label() for m in members],
                 max_usd=1.5)
    dumped = json.dumps(list(trace.events("moa_dispatch")))
    assert "SECRET" not in dumped and "sk-" not in dumped
