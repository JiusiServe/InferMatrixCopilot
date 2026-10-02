"""Report denominators must retain failures and exclude advice from defect rates."""
import json

import pytest

from eval.jiuwenswarm_ab_report import distribution, matching_diagnostics, paired_quality, paired_speed, pct, public_paths, subgroup_operational, validate_evaluation


def test_subgroup_keeps_failures_unknown_and_excludes_other_prs():
    reviews = [
        {"number": 1, "arm": "A", "status": "valid", "native_seconds": 10},
        {"number": 1, "arm": "A", "status": "timeout", "native_seconds": 1800},
        {"number": 2, "arm": "A", "status": "valid", "native_seconds": 1},
        {"number": 1, "arm": "B", "status": "valid", "preflight": True},
    ]
    samples = [{"pr": 1, "arm": "A", "status": "complete", "metrics":
                {"TP": 1, "FP": 1, "unknown": 2, "nondefect_advice": 20}},
               {"pr": 2, "arm": "A", "status": "complete", "metrics": {"TP": 100}}]
    result = subgroup_operational(reviews, samples, [1])
    assert result["A"]["expected"] == 3
    assert result["A"]["terminal"] == 2
    assert result["A"]["valid"] == 1
    assert result["A"]["unknown_share"] == .5
    assert result["A"]["counts"]["TP"] == 1
    assert result["A"]["timings_valid"]["native_seconds"]["p50"] == 10
    assert result["B"]["unknown_share"] is None
    assert result["B"]["terminal"] == 0
    assert result["B"]["counts"]["FP"] is None


def test_missing_metrics_are_not_zero_and_percentiles_are_linear():
    assert pct(None) == "不可计算"
    assert distribution([None, True])["mean"] is None
    assert distribution([0, 10])["p90_linear"] == 9
    assert distribution([10])["p50"] == 10


@pytest.mark.parametrize("artifact", ["truth", "scores"])
def test_report_rejects_foreign_campaign_even_with_equal_counters(tmp_path, artifact):
    campaign = {"cases": [{"number": 1}]}
    (tmp_path / "campaign.json").write_text(json.dumps(campaign))
    foreign = {"campaign_sha256": "f" * 64, "frozen": True, "completed_results": 72}
    with pytest.raises(ValueError, match="different campaign"):
        validate_evaluation(tmp_path, campaign, {}, foreign if artifact == "truth" else {},
                            foreign if artifact == "scores" else {})


def test_public_archive_paths_are_portable(tmp_path):
    state, project = tmp_path / "archive", tmp_path / "repository"
    value = {"path": str(state / "items/raw.json"), "other": [str(project / "eval/result.json")],
             "unexpected": "/private/host/config.json"}
    assert public_paths(value, state, project) == {
        "path": "archive/items/raw.json", "other": ["repository/eval/result.json"],
        "unexpected": "external-artifact/config.json"}


def test_quality_delta_uses_same_applicable_prs():
    rows = [{"pr": 1, "arms": {"A": {"defect_precision": 1.0}, "B": {"defect_precision": None}}},
            {"pr": 2, "arms": {"A": {"defect_precision": .5}, "B": {"defect_precision": .75}}}]
    result = paired_quality(rows)
    assert result["defect_precision"] == {"A": .5, "B": .75, "B_minus_A": .25, "applicable_prs": 1, "prs": [2]}
    assert result["confirmed_recall"]["A"] is None
    assert result["confirmed_recall"]["applicable_prs"] == 0


def test_speed_pairs_same_repeats_and_weights_prs_equally():
    def row(pr, arm, rep, seconds, status="valid"):
        return {"number": pr, "arm": arm, "repetition": rep, "native_seconds": seconds, "status": status}
    reviews = [row(1,"A",1,10), row(1,"B",1,20), row(1,"A",2,30), row(1,"B",2,40),
               row(1,"A",3,900), row(1,"B",3,1800,"timeout"), row(2,"A",1,100), row(2,"B",1,90),
               row(2,"B",2,1), row(3,"A",1,1000), row(3,"B",1,1)]
    result = paired_speed(reviews,[1,2])["native_seconds"]
    assert result["A"] == 60
    assert result["B"] == 60
    assert result["B_minus_A_seconds"] == 0
    assert result["applicable_prs"] == 2
    assert result["paired_repeats"] == 3


def test_final_diagnostics_cannot_mix_equal_slot_counts_with_different_statuses():
    rows = [{"number": pr, "arm": arm, "repetition": rep, "status": "valid"}
            for pr in range(12) for arm in "AB" for rep in (1,2,3)]
    collection = {"completed_results": 72, "results": rows}
    diagnostics = {"identity_sha256": "fixed", "reviews": [
        {"pr": r["number"], "arm": r["arm"], "repeat": r["repetition"] - 1, "status": r["status"]} for r in rows]}
    assert matching_diagnostics(diagnostics, collection, {"identity_sha256": "fixed"})
    diagnostics["reviews"][0]["status"] = "invalid_run"
    with pytest.raises(ValueError, match="statuses"):
        matching_diagnostics(diagnostics, collection, {"identity_sha256": "fixed"})
    collection["completed_results"] = 71
    assert not matching_diagnostics(diagnostics, collection, {"identity_sha256": "fixed"})
