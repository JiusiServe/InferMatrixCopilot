"""Explicit breadth subscription runs preserve legacy caps and fail closed."""

import json
from types import SimpleNamespace

import pytest

from infermatrix_copilot.kb_service import cli, runner
from infermatrix_copilot.kb_service.init_budget import Budget
from infermatrix_copilot.kb_service.init_modules import _Modules
from infermatrix_copilot.kb_service.init_stages import run_stage
from infermatrix_copilot.kb_service.init_support import InitError, judge
from infermatrix_copilot.kb_service.models import ModelGateway, ModelRole, ModelUnavailable
from infermatrix_copilot.knowledge_service.l1 import Block
from infermatrix_copilot.llm import Block as ReplyBlock, Reply
from test_kb_init_knowledge import KnowledgeGateway, _chain
from test_kb_init_modules import CardGateway, _modules_lifecycle, _skeleton, _world_with_tools
from test_kb_init_skeleton import _runtime, world  # noqa: F401


GENERATOR = ModelRole("generator", "zcode", "GLM-5.3")


class SubscriptionTransport:
    def __init__(self, *, subscription=True):
        self.subscription_billing = subscription
        self.calls = []

    def complete(self, **kwargs):
        self.calls.append(kwargs)
        data = {"dimensions": {k: "yes" for k in ("faithful", "does_not_weaken", "non_contradictory")}}
        return Reply(blocks=[ReplyBlock(type="text", text=json.dumps(data))], usage={"input_tokens": 12})


@pytest.mark.parametrize("command,stage", [
    (["init", "toy", "--stage", "modules"], "modules"),
    (["init", "toy", "--stage", "knowledge"], "knowledge"),
    (["widen", "toy"], "knowledge"),
])
def test_breadth_cli_forwards_explicit_unlimited_subscription(tmp_path, monkeypatch, command, stage):
    seen = []

    def run(settings, playbook, repo, *, state_dir, params):
        seen.append(params)
        return SimpleNamespace(status="done"), tmp_path

    monkeypatch.setattr(runner, "run_playbook", run)
    assert cli.main(command + ["--unlimited-subscription", "--dry-run"]) == 0
    assert seen[0]["unlimited_subscription"] == "true" and seen[0]["stage"] == stage
    assert "budget_usd" not in seen[0]


@pytest.mark.parametrize("stage", ["modules", "knowledge"])
@pytest.mark.parametrize("unavailable_role", ["generator", "judge"])
def test_breadth_requires_both_authenticated_subscriptions_before_dispatch(world, stage, unavailable_role):
    transports = {"zcode": SubscriptionTransport(subscription=unavailable_role != "generator"),
                  "codex": SubscriptionTransport(subscription=unavailable_role != "judge")}
    rt = _runtime(world, ModelGateway(None, transport_factory=transports.__getitem__), generator=GENERATOR)
    with pytest.raises(InitError, match=unavailable_role + ":.*authenticated subscription"):
        run_stage(rt, _modules_lifecycle(), stage, dry_run=True, from_existing=True, unlimited_subscription=True)
    assert not any(transport.calls for transport in transports.values())


@pytest.mark.parametrize("stage", ["modules", "knowledge"])
def test_breadth_unlimited_budget_conflict_is_rejected_before_auth(world, stage):
    rt = _runtime(world, ModelGateway(None, transport_factory=lambda _: pytest.fail("invalid options authenticated")))
    with pytest.raises(InitError, match="conflicts with --budget-usd"):
        run_stage(rt, _modules_lifecycle(), stage, dry_run=True, unlimited_subscription=True, budget_usd=100)


@pytest.mark.parametrize("fallback_role", ["generator", "judge"])
def test_breadth_unlimited_refuses_fallback_before_auth(world, fallback_role):
    fallback = ModelRole(fallback_role, "other", "paid-model")
    generator = ModelRole("generator", "zcode", "GLM-5.3", fallback=fallback if fallback_role == "generator" else None)
    judge_role = ModelRole("judge", "codex", "gpt-6.1-sol", fallback=fallback if fallback_role == "judge" else None)
    rt = _runtime(world, ModelGateway(None, transport_factory=lambda _: pytest.fail("fallback config authenticated")),
                  generator=generator, judge=judge_role)
    with pytest.raises(InitError, match="without fallback"):
        run_stage(rt, _modules_lifecycle(), "knowledge", dry_run=True, unlimited_subscription=True)


def test_unlimited_breadth_requires_an_independent_model_even_across_providers(world):
    rt = _runtime(world, ModelGateway(None, transport_factory=lambda _: pytest.fail("same model authenticated")),
                  generator=GENERATOR, judge=ModelRole("judge", "codex", "GLM-5.3"))
    with pytest.raises(InitError, match="independent Codex"):
        run_stage(rt, _modules_lifecycle(), "knowledge", dry_run=True, unlimited_subscription=True)


class SubscriptionKnowledgeGateway(KnowledgeGateway):
    def subscription_billing(self, role):
        return True


def test_breadth_unlimited_exceeds_sixty_dollar_accounting_and_legacy_cap_remains(world):
    gateway = SubscriptionKnowledgeGateway()
    _chain(world, gateway)
    lifecycle = _modules_lifecycle(budget_usd=60, judge_call_usd=20)
    rt = _runtime(world, gateway, generator=GENERATOR)
    capped = run_stage(rt, lifecycle, "knowledge", dry_run=True, subscription_generator=True)
    assert capped.status == "dry_run", capped.problems
    assert capped.spent_usd == 60 and len(capped.verdicts) == 3
    assert any("budget exhausted" in note for note in capped.notes)
    calls_before = len(gateway.calls)
    uncapped = run_stage(rt, lifecycle, "knowledge", dry_run=True, subscription_generator=True,
                        unlimited_subscription=True)
    assert uncapped.inputs_digest != capped.inputs_digest
    assert len(gateway.calls) > calls_before  # a capped result cannot be reused as unlimited
    assert uncapped.status == "dry_run", uncapped.problems
    assert uncapped.spent_usd == 80 and len(uncapped.verdicts) == 4
    assert not any("budget exhausted" in note for note in uncapped.notes)
    assert any("observability only" in note and "remain unknown" in note for note in uncapped.notes)


def test_modules_selects_uncapped_budget_only_when_explicit(world, monkeypatch):
    _world_with_tools(world)
    _skeleton(world)
    gateway = CardGateway()
    gateway.subscription_billing = lambda role: True
    original = _Modules._build
    limits = []

    def build(stage, tree):
        limits.append(stage.budget.limit_usd)
        return original(stage, tree)

    monkeypatch.setattr(_Modules, "_build", build)
    rt = _runtime(world, gateway, generator=GENERATOR)
    legacy = run_stage(rt, _modules_lifecycle(budget_usd=60), "modules", dry_run=True, subscription_generator=True)
    unlimited = run_stage(rt, _modules_lifecycle(budget_usd=60), "modules", dry_run=True,
                          subscription_generator=True, unlimited_subscription=True)
    assert legacy.status == unlimited.status == "dry_run"
    assert limits == [60, None]
    assert legacy.inputs_digest != unlimited.inputs_digest


def test_unlimited_breadth_identity_preserves_legacy_default(world):
    rt = _runtime(world)
    lifecycle = _modules_lifecycle()
    stage = _Modules(rt, lifecycle, dry_run=True, pin=None)
    expected = repr(lifecycle.init).replace(f", pr_history_count={lifecycle.init.pr_history_count}", "") \
        .replace(", feature_discovery_required=False", "")
    assert stage._init_identity() == expected
    rt.unlimited_subscription = True
    assert stage._init_identity() == expected + ":unlimited-subscription"
    rt.subscription_generator = True
    assert stage._init_identity() == expected + ":subscription-generator:unlimited-subscription"


def test_unlimited_judge_rechecks_and_binds_subscription_transport_before_every_call(world):
    subscription, paid = SubscriptionTransport(), SubscriptionTransport(subscription=False)
    transports = iter([subscription, paid])
    rt = _runtime(world, ModelGateway(None, transport_factory=lambda _: next(transports)),
                  unlimited_subscription=True)
    budget = Budget(None)
    block = Block("prose", "repos/toy/components/core/knowledge.md", "", "prose", "digest")
    verdict = judge(rt, budget, _modules_lifecycle().init, block, base={}, head={}, evidence=[])
    assert verdict.verdict == "pass" and len(subscription.calls) == 1
    assert budget.spent_usd == _modules_lifecycle().init.judge_call_usd
    with pytest.raises(ModelUnavailable, match="subscription judge.*authenticated subscription"):
        judge(rt, budget, _modules_lifecycle().init, block, base={}, head={}, evidence=[])
    assert paid.calls == []
    assert budget.spent_usd == _modules_lifecycle().init.judge_call_usd
