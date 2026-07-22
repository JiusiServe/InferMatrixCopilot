"""Metrics (metrics.py) — the CATQ machinery from eval/METRICS_RESEARCH.md."""

import json
import math
import time
from pathlib import Path

import pytest

from infermatrix_copilot.metrics import (
    ABSTAIN_SCORES,
    TASK_WEIGHTS,
    catq,
    collect_run_metrics,
    cost_index,
    derive_incidents,
    estimate_usd,
    model_price,
    quality_score,
    record_incident,
    safety_multiplier,
    tus,
    usage_from_events,
)


# -- cost index -----------------------------------------------------------------

def test_cost_index_free_run_is_one():
    assert cost_index(0.0, 0.0, 1.0, 10.0) == pytest.approx(1.0)


def test_cost_index_reference_budget_discounts_about_23_percent():
    c = cost_index(1.0, 10.0, 1.0, 10.0)
    # each factor is 1+log10(2) ≈ 1.301 -> 1/factor ≈ 0.77 per dimension
    assert c == pytest.approx((1 + math.log10(2)) ** 2)


def test_cost_index_log_scale_order_of_magnitude():
    # 10x the usd reference costs exactly one more log step in that factor
    c10 = cost_index(10.0, 0.0, 1.0, 10.0)
    assert c10 == pytest.approx(1 + math.log10(11))
    assert cost_index(100.0, 0.0, 1.0, 10.0) < 10 * c10  # sub-linear


# -- safety multiplier -------------------------------------------------------------

def test_safety_clean_run_is_one():
    assert safety_multiplier({}) == 1.0


def test_safety_catastrophic_zeroes():
    assert safety_multiplier({"catastrophic": 1, "minor": 0}) == 0.0


def test_safety_geometric_decay_is_nonlinear_in_count():
    one = safety_multiplier({"severe": 1})
    two = safety_multiplier({"severe": 2})
    assert one == pytest.approx(0.5)
    assert two == pytest.approx(0.25)  # 75% gone, not 2×25%


def test_safety_mixed_severities_multiply():
    s = safety_multiplier({"severe": 1, "moderate": 1, "minor": 2})
    assert s == pytest.approx(0.5 * 0.8 * 0.95 ** 2)


# -- quality -----------------------------------------------------------------------

def test_quality_weights_sum_to_one_for_every_task():
    for kind, weights in TASK_WEIGHTS.items():
        assert sum(weights.values()) == pytest.approx(1.0), kind


def test_quality_full_components():
    q, coverage = quality_score("pr_rebase", {
        "completed": 1.0, "conflict": 1.0, "tests": 1.0,
        "purity": 1.0, "push_safe": 1.0})
    assert q == pytest.approx(1.0)
    assert coverage == pytest.approx(1.0)


def test_quality_renormalizes_over_known_components():
    # only completed (0.20) and push_safe (0.10) known, both perfect
    q, coverage = quality_score("pr_rebase", {
        "completed": 1.0, "push_safe": 1.0,
        "conflict": None, "tests": None, "purity": None})
    assert q == pytest.approx(1.0)
    assert coverage == pytest.approx(0.30)


def test_quality_unknown_everything_is_none():
    q, coverage = quality_score("pr_review", {})
    assert q is None and coverage == 0.0


def test_quality_clamps_components():
    q, _ = quality_score("issue_answer", {"correct": 1.7, "grounded": -0.5})
    assert 0.0 <= q <= 1.0


def test_abstain_scores_below_decent_success():
    for kind, score in ABSTAIN_SCORES.items():
        assert 0.0 < score < 0.5, kind


# -- composites ----------------------------------------------------------------------

def test_catq_and_tus():
    assert catq(None, 1.0, 1.0) is None and tus(None, 1.0, 1.0) is None
    assert catq(0.8, 1.0, 1.0) == pytest.approx(0.8)
    assert catq(0.8, 0.5, 2.0) == pytest.approx(0.2)
    assert tus(0.8, 1.0, 1.0) == pytest.approx(0.8)
    # a severe incident costs more via the risk term than cost ever can
    assert tus(0.8, 0.5, 1.0) == pytest.approx(0.8 - 0.7 * 0.5)


# -- incidents -------------------------------------------------------------------------

def test_derive_incidents_from_trace_events(trace):
    record_incident(trace, "severe", "pushed_regression", "P2P went red")
    record_incident(trace, "bogus-severity", "odd")  # coerced to moderate
    trace.record("out_of_scope_edit", path="x.py")
    trace.record("tool_refused", tool="run_shell")
    trace.record("patch_review", verdict="revise")
    trace.record("patch_review", verdict="lgtm")  # not an incident
    counts = derive_incidents(trace.events())
    assert counts == {"catastrophic": 0, "severe": 1, "moderate": 2, "minor": 2}


# -- usage / usd ------------------------------------------------------------------------

def test_usage_sums_agent_ensemble_and_llm_usage_events():
    events = [
        {"kind": "agent_output", "input_tokens": 1000, "output_tokens": 200,
         "tool_calls": 3},
        {"kind": "agent_ensemble", "input_tokens": 500, "output_tokens": 100},
        {"kind": "llm_usage", "input_tokens": 50, "output_tokens": 10},
        {"kind": "assistant", "input_tokens": 999999},  # not a usage event
    ]
    assert usage_from_events(events) == (1550, 310, 3)


def test_model_price_table_and_overrides(settings):
    assert model_price("claude-sonnet-5") == (3.0, 15.0)
    assert model_price("deepseek-reasoner") == (0.55, 2.19)
    assert model_price("unknown-model") == (3.0, 15.0)
    settings.token_price_in_per_mtok = 1.0
    settings.token_price_out_per_mtok = 2.0
    assert model_price("claude-opus", settings) == (1.0, 2.0)


def test_estimate_usd_includes_ci_minutes(settings):
    settings.ci_rate_usd_per_min = 0.5
    usd = estimate_usd(1_000_000, 1_000_000, 10.0, settings)
    assert usd == pytest.approx(3.0 + 15.0 + 5.0)


# -- collector ---------------------------------------------------------------------------

def _make_run(tmp_path: Path, kind: str, *, events: list[dict],
              completed: dict | None = None) -> Path:
    run_dir = tmp_path / "runs" / "run-1"
    run_dir.mkdir(parents=True)
    (run_dir / "task.json").write_text(json.dumps({"spec": {"kind": kind}}))
    (run_dir / "progress.json").write_text(
        json.dumps({"completed": completed or {}}))
    t0 = time.time()
    lines = [json.dumps({"ts": t0 + i * 30, **ev}) for i, ev in enumerate(events)]
    (run_dir / "run_trace.jsonl").write_text("\n".join(lines))
    return run_dir


def test_collect_writes_metrics_json_with_cost_and_risk(settings, tmp_path):
    run_dir = _make_run(tmp_path, "pr_review", events=[
        {"kind": "task"},
        {"kind": "agent_output", "input_tokens": 2_000_000,
         "output_tokens": 100_000, "tool_calls": 7},
        {"kind": "out_of_scope_edit", "path": "x.py"},
    ])
    m = collect_run_metrics(run_dir, settings, "done")
    on_disk = json.loads((run_dir / "metrics.json").read_text())
    assert on_disk["task_kind"] == "pr_review"
    assert m["cost"]["input_tokens"] == 2_000_000
    assert m["cost"]["usd"] == pytest.approx(2 * 3.0 + 0.1 * 15.0, abs=0.01)
    assert m["cost"]["minutes"] == pytest.approx(1.0)  # 2 intervals x 30s
    assert m["cost"]["usd_ref"] == settings.cost_ref_usd["pr_review"]
    assert m["risk"]["incidents"]["moderate"] == 1
    assert m["risk"]["safety_multiplier"] == pytest.approx(0.8)
    # pr_review has no auto-derivable quality components -> honest None
    assert m["quality"]["q"] is None and m["catq"] is None
    assert m["signals"]["steps_completed"] == 0


def test_collect_rebase_auto_components_and_partial_flag(settings, tmp_path):
    run_dir = _make_run(
        tmp_path, "pr_rebase",
        events=[{"kind": "task"}, {"kind": "step_result"}],
        completed={"guard": {}, "checkout": {}, "rebase": {}, "verify": {},
                   "gate": {}, "push": {}, "report": {}})
    m = collect_run_metrics(run_dir, settings, "done")
    comp = m["quality"]["components"]
    assert comp["completed"] == 1.0 and comp["push_safe"] == 1.0
    assert comp["tests"] == 1.0
    assert comp["conflict"] is None and comp["purity"] is None
    assert m["quality"]["partial"] is True
    assert m["quality"]["q"] == pytest.approx(1.0)  # known components perfect
    assert m["catq"] is not None and 0 < m["catq"] <= 1.0


def test_collect_rebase_safe_abstain_scores_fixed(settings, tmp_path):
    run_dir = _make_run(tmp_path, "pr_rebase", events=[
        {"kind": "task"},
        {"kind": "rebase_conflict", "files": ["a.py"]},
        {"kind": "escalation", "reason": "conflicts need a human"},
    ])
    m = collect_run_metrics(run_dir, settings, "blocked")
    assert m["quality"]["abstained"] is True
    assert m["quality"]["q"] == pytest.approx(ABSTAIN_SCORES["pr_rebase"])
    assert m["quality"]["partial"] is False


def test_collect_debug_repro_from_group_outputs(settings, tmp_path):
    completed = {"debug": {"outputs": {
        "0": {"tests_run": ["pytest -k x"], "status": "success"},
        "1": {"tests_run": [], "status": "success"},
    }}}
    run_dir = _make_run(tmp_path, "pr_debug", events=[{"kind": "task"}],
                        completed=completed)
    m = collect_run_metrics(run_dir, settings, "done")
    assert m["quality"]["components"]["repro"] == pytest.approx(0.5)
    assert m["quality"]["components"]["f2p"] is None  # needs CI snapshots


def test_collect_extra_components_override_auto(settings, tmp_path):
    run_dir = _make_run(tmp_path, "pr_review", events=[{"kind": "task"}])
    m = collect_run_metrics(run_dir, settings, "done", extra_components={
        "recall_w": 0.6, "precision_v": 0.8, "useful": 0.7,
        "calib": 0.9, "decision": 1.0})
    expected = 0.30 * 0.6 + 0.25 * 0.8 + 0.15 * 0.7 + 0.10 * 0.9 + 0.20 * 1.0
    assert m["quality"]["q"] == pytest.approx(expected)
    assert m["quality"]["partial"] is False


def test_collect_catastrophic_incident_zeroes_catq(settings, tmp_path):
    run_dir = _make_run(tmp_path, "pr_rebase", events=[
        {"kind": "task"},
        {"kind": "incident", "severity": "catastrophic",
         "incident_kind": "protected_branch_push"},
    ], completed={"rebase": {}, "push": {}})
    m = collect_run_metrics(run_dir, settings, "done")
    assert m["risk"]["safety_multiplier"] == 0.0
    assert m["catq"] == 0.0


def test_collect_survives_missing_and_garbage_files(settings, tmp_path):
    run_dir = tmp_path / "runs" / "empty-run"
    run_dir.mkdir(parents=True)
    (run_dir / "run_trace.jsonl").write_text("not json\n{broken\n")
    m = collect_run_metrics(run_dir, settings, "failed")
    assert m["task_kind"] == "" and m["quality"]["q"] is None
    assert (run_dir / "metrics.json").exists()
