"""Gateway-injected input is reserved without widening the weekly envelope."""

import json
import pytest

from infermatrix_copilot.config import Settings
from infermatrix_copilot.improve.budget import BudgetBreach, BudgetRefused, Governor, worst_case_usd
from infermatrix_copilot.improve.shadow import assert_boundaries, shadow_env


LIMITS = {"mimo-v2.5": 1048576}
USAGE = {"input_tokens": 11430, "cache_read_input_tokens": 1664, "output_tokens": 16000}


def test_observed_gateway_usage_settles_inside_configured_context_reservation(tmp_path):
    cfg = Settings(_env_file=None, improve_input_context_limits=LIMITS)
    gov = Governor(tmp_path, usd_week=20, judge_calls_week=300, settings=cfg)
    reservation = gov.reserve_call("mimo-v2.5", 5871, 16000)
    assert gov.remaining()["usd_reserved"] == pytest.approx(0.481152)
    actual = gov.settle_call(reservation, USAGE, "mimo-v2.5")
    assert actual == pytest.approx(0.02645874)
    assert gov.remaining()["usd_settled"] == pytest.approx(actual, abs=1e-6)
    assert not gov.remaining()["breached"]


def test_gateway_reservation_refuses_before_dispatch_when_existing_cap_is_too_small(tmp_path):
    cfg = Settings(_env_file=None, improve_input_context_limits=LIMITS)
    gov = Governor(tmp_path, usd_week=0.1, judge_calls_week=300, settings=cfg)
    with pytest.raises(BudgetRefused, match="exceed the weekly envelope"):
        gov.reserve_call("mimo-v2.5", 5871, 16000)
    assert gov.remaining()["usd_settled"] == 0
    assert gov.remaining()["usd_reserved"] == 0
    assert gov.remaining()["usd_envelope"] == 0.1


def test_limits_are_exact_model_matches_and_never_reduce_visible_bound():
    cfg = Settings(_env_file=None, improve_input_context_limits=LIMITS)
    assert worst_case_usd("mimo-v2.5-pro", 5871, 16000, cfg) == worst_case_usd("mimo-v2.5-pro", 5871, 16000)
    assert worst_case_usd("mimo-v2.5", 2_000_000, 16000, cfg) == worst_case_usd("mimo-v2.5", 2_000_000, 16000)
    cfg.cache_read_price_factor = 2.0
    assert worst_case_usd("mimo-v2.5", 5871, 16000, cfg) == pytest.approx(0.7564032)


@pytest.mark.parametrize("limits", [{"": 1}, {"mimo-v2.5": True}, {"mimo-v2.5": 0},
                                    {"mimo-v2.5": -1}, {"mimo-v2.5": "1000000"}, {"mimo-v2.5": 1.5}, []])
def test_invalid_context_ceiling_is_rejected_at_configuration(limits):
    with pytest.raises(ValueError, match="context limits"):
        Settings(_env_file=None, improve_input_context_limits=limits)


def test_governed_child_receives_parent_limits_and_rejects_override(tmp_path, monkeypatch):
    env = shadow_env(shadow_dir=tmp_path, run_dir=tmp_path, trace_root=tmp_path,
                     executables_dir=tmp_path, repo_name="demo",
                     ledger_dir=tmp_path,
                     environ={"IMPROVE_INPUT_CONTEXT_LIMITS": '{"mimo-v2.5":1}'},
                     input_context_limits=LIMITS)
    expected = {"IMPROVE_INPUT_CONTEXT_LIMITS": json.dumps(LIMITS, sort_keys=True)}
    assert not assert_boundaries(env, expected=expected)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    assert Settings(_env_file=None).improve_input_context_limits == LIMITS
    env["IMPROVE_INPUT_CONTEXT_LIMITS"] = "{}"
    assert assert_boundaries(env, expected=expected)


def test_reconciling_an_estimate_breach_preserves_actual_charges_and_weekly_cap(tmp_path):
    gov = Governor(tmp_path, usd_week=20, judge_calls_week=300)
    reservation = gov.reserve_call("mimo-v2.5", 5871, 16000)
    with pytest.raises(BudgetBreach):
        gov.settle_call(reservation, USAGE, "mimo-v2.5")
    before = gov.remaining()
    gov.settings = Settings(_env_file=None, improve_input_context_limits=LIMITS)
    gov.clear_breach()
    after = gov.remaining()
    assert after["usd_settled"] == before["usd_settled"]
    assert after["usd_envelope"] == before["usd_envelope"] == 20
    assert after["usd_reserved"] == 0
    assert not after["breached"]
