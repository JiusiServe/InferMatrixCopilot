#!/usr/bin/env python3
"""Validate and score blind, repeated PR-review replay artifacts.

The reviewer never needs this program's labels input. An outer evaluation
controller runs the reviewer from public cases, then invokes this scorer after
predictions and independent semantic judgments have been frozen.
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
from typing import Any

SEVERITY_ORDER = {"nit": 0, "minor": 1, "major": 2, "blocker": 3}
SEVERITY_WEIGHT = {"nit": 0.5, "minor": 1.0, "major": 2.0, "blocker": 4.0}
FORBIDDEN_PUBLIC_KEYS = {
    "comments", "review_comments", "review_threads", "labels", "gold",
    "gold_findings", "resolution", "fix_commit", "merge_commit",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_no}: each line must be an object")
        rows.append(row)
    return rows


def _unique(rows: list[dict[str, Any]], key, what: str) -> dict[Any, dict[str, Any]]:
    out: dict[Any, dict[str, Any]] = {}
    for row in rows:
        value = key(row)
        if value in out:
            raise ValueError(f"duplicate {what}: {value!r}")
        out[value] = row
    return out


def validate_split(cases_path: Path, labels_path: Path) -> dict[str, Any]:
    cases = load_jsonl(cases_path)
    labels = load_jsonl(labels_path)
    case_by_id = _unique(cases, lambda x: x.get("case_id"), "case_id in cases")
    label_by_id = _unique(labels, lambda x: x.get("case_id"), "case_id in labels")
    errors: list[str] = []

    for case_id, case in case_by_id.items():
        if not case_id:
            errors.append("public case has an empty case_id")
        leaked = sorted(FORBIDDEN_PUBLIC_KEYS.intersection(case))
        if leaked:
            errors.append(f"{case_id}: forbidden public keys: {', '.join(leaked)}")
        for required in ("repo", "pr", "base_sha", "review_sha", "knowledge_snapshot"):
            if not case.get(required):
                errors.append(f"{case_id}: missing public field {required}")
        if case.get("mode") != "performance":
            errors.append(f"{case_id}: replay_review requires mode=performance")
        if case.get("knowledge_policy", "cross_pr_only") not in {
                "same_pr_distilled", "cross_pr_only"}:
            errors.append(f"{case_id}: invalid knowledge_policy")
        if case.get("review_sha") == case.get("base_sha"):
            errors.append(f"{case_id}: review_sha must differ from base_sha")

    if set(case_by_id) != set(label_by_id):
        errors.append("case/label IDs differ: "
                      f"only_cases={sorted(set(case_by_id) - set(label_by_id))}, "
                      f"only_labels={sorted(set(label_by_id) - set(case_by_id))}")

    for case_id, label in label_by_id.items():
        findings = label.get("findings")
        if not isinstance(findings, list) or not findings:
            errors.append(f"{case_id}: labels require a non-empty findings list")
            continue
        seen: set[str] = set()
        for finding in findings:
            fid = finding.get("id") if isinstance(finding, dict) else None
            if not fid or fid in seen:
                errors.append(f"{case_id}: finding IDs must be non-empty and unique")
            seen.add(fid)
            if finding.get("severity") not in SEVERITY_ORDER:
                errors.append(f"{case_id}/{fid}: invalid severity")
            for required in ("root_cause", "impact_path", "evidence"):
                if not finding.get(required):
                    errors.append(f"{case_id}/{fid}: missing {required}")

    if errors:
        raise ValueError("blind split validation failed:\n- " + "\n- ".join(errors))
    return {"cases": len(cases), "labels": len(labels), "status": "valid"}


def _severity_agreement(gold: str, predicted: str) -> float:
    if gold not in SEVERITY_ORDER or predicted not in SEVERITY_ORDER:
        return 0.0
    distance = abs(SEVERITY_ORDER[gold] - SEVERITY_ORDER[predicted])
    return 1.0 if distance == 0 else 0.5 if distance == 1 else 0.0


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def score(labels_path: Path, predictions_path: Path,
          judgments_path: Path) -> dict[str, Any]:
    labels = load_jsonl(labels_path)
    predictions = load_jsonl(predictions_path)
    judgments = load_jsonl(judgments_path)
    label_by_id = _unique(labels, lambda x: x.get("case_id"), "label case_id")
    pred_by_run = _unique(
        predictions, lambda x: (x.get("case_id"), x.get("run_id")),
        "prediction case_id/run_id")
    judgment_by_gold = _unique(
        judgments, lambda x: (x.get("case_id"), x.get("run_id"), x.get("gold_id")),
        "judgment case_id/run_id/gold_id")

    total_gold_weight = 0.0
    hit_weight = 0.0
    same_weight = 0.0
    total_predictions = 0
    matched_predictions = 0
    per_case_run: dict[str, dict[str, dict[str, Any]]] = {}

    for (case_id, run_id), pred_row in pred_by_run.items():
        if case_id not in label_by_id:
            raise ValueError(f"prediction references unknown case {case_id}")
        golds = label_by_id[case_id].get("findings") or []
        preds = pred_row.get("findings") or []
        if not isinstance(preds, list):
            raise ValueError(f"{case_id}/{run_id}: findings must be a list")
        pred_by_id = _unique(preds, lambda x: x.get("id"),
                             f"prediction id in {case_id}/{run_id}")
        used_predictions: set[str] = set()
        hit_ids: set[str] = set()
        same_ids: set[str] = set()
        run_gold_weight = 0.0
        run_hit_weight = 0.0
        run_same_weight = 0.0

        for gold in golds:
            gold_id = gold["id"]
            weight = SEVERITY_WEIGHT[gold["severity"]]
            run_gold_weight += weight
            key = (case_id, run_id, gold_id)
            if key not in judgment_by_gold:
                raise ValueError(f"missing judgment for {case_id}/{run_id}/{gold_id}")
            decision = judgment_by_gold[key]
            prediction_id = decision.get("prediction_id")
            root = decision.get("root_cause")
            path = decision.get("impact_path")
            if root not in (0, 1, 2) or path not in (0, 1, 2):
                raise ValueError(f"{case_id}/{run_id}/{gold_id}: scores must be 0, 1, or 2")
            if prediction_id is None:
                if root or path:
                    raise ValueError(f"{case_id}/{run_id}/{gold_id}: null prediction must score 0/0")
                continue
            if prediction_id not in pred_by_id:
                raise ValueError(f"{case_id}/{run_id}/{gold_id}: unknown prediction {prediction_id}")
            if prediction_id in used_predictions:
                raise ValueError(f"{case_id}/{run_id}: prediction {prediction_id} matched twice")
            used_predictions.add(prediction_id)
            severity = _severity_agreement(gold["severity"],
                                           pred_by_id[prediction_id].get("severity", ""))
            semantic = 0.45 * root / 2 + 0.40 * path / 2 + 0.15 * severity
            is_hit = root >= 1 and path >= 1 and semantic >= 0.65
            is_same = root == 2 and path == 2 and severity == 1.0
            if is_hit:
                hit_ids.add(gold_id)
                run_hit_weight += weight
            if is_same:
                same_ids.add(gold_id)
                run_same_weight += weight

        total_gold_weight += run_gold_weight
        hit_weight += run_hit_weight
        same_weight += run_same_weight
        total_predictions += len(pred_by_id)
        matched_predictions += len(used_predictions.intersection(
            {judgment_by_gold[(case_id, run_id, g["id"])].get("prediction_id")
             for g in golds if g["id"] in hit_ids}))
        per_case_run.setdefault(case_id, {})[run_id] = {
            "hit_ids": sorted(hit_ids), "same_ids": sorted(same_ids),
            "weighted_recall": run_hit_weight / run_gold_weight if run_gold_weight else 0.0,
            "weighted_same_opinion_recall": (
                run_same_weight / run_gold_weight if run_gold_weight else 0.0),
        }

    expected_runs = set(pred_by_run)
    extra_judgments = {
        (c, r) for c, r, _ in judgment_by_gold if (c, r) not in expected_runs
    }
    if extra_judgments:
        raise ValueError(f"judgments reference missing prediction runs: {sorted(extra_judgments)}")

    case_metrics: dict[str, Any] = {}
    all_run_weight = 0.0
    all_run_denominator = 0.0
    jaccards: list[float] = []
    for case_id, runs in per_case_run.items():
        hit_sets = [set(v["hit_ids"]) for v in runs.values()]
        golds = label_by_id[case_id]["findings"]
        weights = {g["id"]: SEVERITY_WEIGHT[g["severity"]] for g in golds}
        stable = set.intersection(*hit_sets) if hit_sets else set()
        denominator = sum(weights.values())
        all_run_weight += sum(weights[g] for g in stable)
        all_run_denominator += denominator
        local_jaccards: list[float] = []
        for left, right in itertools.combinations(hit_sets, 2):
            union = left | right
            local_jaccards.append(len(left & right) / len(union) if union else 1.0)
        jaccards.extend(local_jaccards)
        case_metrics[case_id] = {
            "runs": runs,
            "all_run_hit_ids": sorted(stable),
            "all_run_weighted_recall": (
                sum(weights[g] for g in stable) / denominator if denominator else 0.0),
            "mean_pairwise_hit_jaccard": _mean(local_jaccards) if len(runs) > 1 else None,
        }

    report = {
        "weighted_hit_recall": hit_weight / total_gold_weight if total_gold_weight else 0.0,
        "weighted_same_opinion_recall": (
            same_weight / total_gold_weight if total_gold_weight else 0.0),
        "precision": matched_predictions / total_predictions if total_predictions else 0.0,
        "all_run_weighted_recall": (
            all_run_weight / all_run_denominator if all_run_denominator else 0.0),
        "mean_pairwise_hit_jaccard": _mean(jaccards) if jaccards else None,
        "cases": case_metrics,
    }
    report["passes_mvp_gate"] = (
        report["weighted_hit_recall"] >= 0.80
        and report["weighted_same_opinion_recall"] >= 0.60
        and report["precision"] >= 0.70
        and report["all_run_weighted_recall"] >= 0.60
        and (report["mean_pairwise_hit_jaccard"] is not None
             and report["mean_pairwise_hit_jaccard"] >= 0.70)
        and all(len(runs) >= 3 for runs in per_case_run.values())
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--cases", type=Path, required=True)
    validate.add_argument("--labels", type=Path, required=True)
    scoring = sub.add_parser("score")
    scoring.add_argument("--labels", type=Path, required=True)
    scoring.add_argument("--predictions", type=Path, required=True)
    scoring.add_argument("--judgments", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "validate":
        result = validate_split(args.cases, args.labels)
    else:
        result = score(args.labels, args.predictions, args.judgments)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
