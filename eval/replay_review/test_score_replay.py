from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).parent
SPEC = importlib.util.spec_from_file_location("score_replay", HERE / "score_replay.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_examples_are_blind_and_pass_gate():
    examples = HERE / "examples"
    assert MODULE.validate_split(examples / "cases.jsonl",
                                 examples / "labels.jsonl")["status"] == "valid"
    report = MODULE.score(examples / "labels.jsonl",
                          examples / "predictions.jsonl",
                          examples / "judgments.jsonl")
    assert report["passes_mvp_gate"] is True
    assert report["weighted_same_opinion_recall"] == 1.0
    assert report["all_run_weighted_recall"] == 1.0


def test_public_case_rejects_hidden_review_fields(tmp_path):
    case = tmp_path / "cases.jsonl"
    label = tmp_path / "labels.jsonl"
    case.write_text(
        '{"case_id":"x","repo":"r","pr":1,"base_sha":"a",'
        '"review_sha":"b","mode":"performance","knowledge_snapshot":"k",'
        '"review_comments":[]}\n',
        encoding="utf-8")
    label.write_text(
        '{"case_id":"x","findings":[{"id":"g","severity":"major",'
        '"root_cause":"c","impact_path":"p","evidence":"e"}]}\n',
        encoding="utf-8")
    try:
        MODULE.validate_split(case, label)
    except ValueError as exc:
        assert "forbidden public keys" in str(exc)
    else:
        raise AssertionError("expected hidden review field to be rejected")
