#!/usr/bin/env python3
"""Prepare a new protocol retest without changing frozen A/B content or labels.

This command is entirely offline. It does not repeat document mapping, source
auditing, or model calls. The published report anchors the previous experiment;
all bridge-readable source and document bytes are checked before they are reused.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from eval import jiuwenswarm_ab_judge as judge
from eval import jiuwenswarm_ab_prepare as prepare
from eval import jiuwenswarm_pr_review_ab as harness

SCHEMA = "jiuwenswarm-protocol-retest-v1"
REFERENCE_REPORT = Path(__file__).resolve().parent / "knowledge-depth/jiuwenswarm-original-docs-comparison-cn-20261003.json"
EXPECTED_BUDGET = {"workers": 13, "repetitions": 3, "timeout_s": 1800,
                   "source_calls": 60, "source_result_chars": 24000,
                   "knowledge_pages": 2, "knowledge_chars": 6000}
EXPECTED_NATIVE = {"reasoning_level": "max", "model": "GLM-5.3"}
SUBSCRIPTION_PROVIDER = "account:bigmodel-individual-coding-plan"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    return digest(Path(path).read_bytes())


def load(path):
    return json.loads(Path(path).read_bytes())


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode() + b"\n")


def bind(path):
    return {"path": str(path), "sha256": sha(path)}


def check_digest(path, expected, label):
    if not path.is_file() or path.is_symlink() or sha(path) != expected:
        raise ValueError(label + " frozen bytes changed or are unreadable")


def check_case_rows(rows, label):
    if not isinstance(rows, list) or len(rows) != len(prepare.HEADS) \
            or any(type(c.get("number")) is not int for c in rows) \
            or {c["number"]: c.get("head") for c in rows} != prepare.HEADS:
        raise ValueError(label + " must contain the exact selected PRs once")


def verify_previous(previous, reference):
    """Check the published anchors, then every source/document/truth input."""
    report = load(reference)
    expected = report["inputs"]
    paths = {"campaign": previous / "campaign.json", "runtime_identity": previous / "identity.json",
             "truth": previous / "private-codex/truth-manifest.json",
             "inventory": previous.parent / "mapping/inventory.json"}
    for key, path in paths.items():
        check_digest(path, expected[key]["sha256"], key)
    campaign, identity, inventory = (load(paths[key]) for key in ("campaign", "runtime_identity", "inventory"))
    campaign_sha = sha(paths["campaign"])
    unsigned = {k: v for k, v in identity.items() if k != "identity_sha256"}
    if identity.get("identity_sha256") != digest(json.dumps(unsigned, sort_keys=True).encode()) \
            or identity.get("campaign_sha256") != campaign_sha:
        raise ValueError("previous runtime identity digest or campaign binding differs")
    if campaign.get("schema") != harness.SCHEMA or identity.get("schema") != harness.SCHEMA \
            or campaign.get("baseline_source_sha") != prepare.BASE \
            or report.get("source_pin") != prepare.BASE or inventory.get("pin") != prepare.BASE \
            or campaign.get("run_root") != str(previous):
        raise ValueError("previous source pin, schema or run root differs")
    if campaign.get("budget") != EXPECTED_BUDGET or campaign.get("native") != EXPECTED_NATIVE:
        raise ValueError("previous budgets or requested model configuration differ")
    native = identity.get("native", {})
    if any(native.get(k) != v for k, v in {"model": "GLM-5.3", "provider_id": SUBSCRIPTION_PROVIDER,
                                         "reasoning_level": "max"}.items()):
        raise ValueError("previous actual native model or subscription provider differs")
    check_digest(Path(native["cli_path"]), native["cli_sha256"], "native CLI")
    if identity.get("limits") != {"knowledge_chars": 6000, "source_calls": 60,
            "source_result_chars": 24000, "timeout_s": 1800, "start_interval_s": 15,
            "rate_cooldown_s": 90, "workers": 13}:
        raise ValueError("previous actual native limits differ")
    check_case_rows(campaign.get("cases"), "campaign")
    check_case_rows(identity.get("cases"), "runtime identity")
    if campaign.get("analysis_groups") != prepare.analysis_groups(campaign["cases"]):
        raise ValueError("previous analysis groups differ")
    source = Path(campaign["baseline_source_root"])
    if harness.git(source, "rev-parse", "HEAD").decode().strip() != prepare.BASE:
        raise ValueError("baseline source checkout HEAD differs")
    expected_cases = {c["number"]: c for c in identity["cases"]}
    for case in campaign["cases"]:
        number = case["number"]
        frozen = expected_cases[number]
        for key, value in case.items():
            if frozen.get(key) != value:
                raise ValueError("previous campaign and identity case differ")
        checkout = Path(case["source_root"])
        if case.get("target") != prepare.BASE \
                or harness.git(checkout, "rev-parse", "HEAD").decode().strip() != case["head"]:
            raise ValueError(f"PR {number} source checkout HEAD differs")
        if harness.git(checkout, "merge-base", prepare.BASE, case["head"]).decode().strip() != case["base"]:
            raise ValueError(f"PR {number} merge base differs")
        if harness.git(checkout, "status", "--porcelain", "--untracked-files=no").strip() \
                or harness.tracked_sources(checkout) != frozen.get("sources"):
            raise ValueError(f"PR {number} frozen source manifest differs")
        for kind, filename in (("diff", "diff.patch"), ("context", "context.json")):
            path = previous / "cases" / str(number) / filename
            if Path(case[kind + "_path"]) != path:
                raise ValueError("previous case input escaped its frozen case directory")
            check_digest(path, case[kind + "_sha256"], f"PR {number} {kind}")
        actual = harness.git(checkout, "diff", "--no-ext-diff", "--no-color", case["base"], case["head"], "--")
        if Path(case["diff_path"]).read_bytes() != actual:
            raise ValueError(f"PR {number} supplied diff differs from frozen source")
        changed = harness.git(checkout, "diff", "--name-only", "-z", case["base"], case["head"], "--")
        if [p for p in changed.decode().split("\0") if p] != case["changed_files"]:
            raise ValueError("previous changed-file list differs")
    if set(campaign.get("arms", {})) != {"A", "B"} or set(identity.get("arms", {})) != {"A", "B"}:
        raise ValueError("previous campaign needs exactly arms A and B")
    for arm in ("A", "B"):
        value, frozen, snapshot = campaign["arms"][arm], identity["arms"][arm], inventory["snapshots"][arm]
        if value != {key: snapshot[key] for key in ("doc_root", "repo_subdir", "sha256")} \
                or any(frozen.get(key) != value[key] for key in ("doc_root", "repo_subdir")) \
                or snapshot["sha256"] != report["snapshot_sha256"][arm]:
            raise ValueError("previous document snapshot binding differs")
        documents = harness.document_manifest(Path(value["doc_root"]))
        if documents != frozen.get("documents") \
                or {item["path"]: item["sha256"] for item in snapshot["items"]} != documents:
            raise ValueError("previous document snapshot manifest differs")
    truths, _ = judge.bound_truth(campaign, campaign_sha, previous / "private-codex")
    manifest = load(paths["truth"])
    expected_truth_paths = {Path(row["path"]) for row in manifest["cases"]}
    if set((previous / "private-codex/truth").glob("*.json")) != expected_truth_paths:
        raise ValueError("previous truth directory contains extra or missing records")
    for row in manifest["cases"]:
        if Path(row["path"]) != previous / "private-codex/truth" / f"pr-{row['pr']}.json":
            raise ValueError("previous truth record escaped its frozen directory")
    if sum(row["status"] == "complete" for row in manifest["cases"]) != manifest["truth_complete_cases"] \
            or sum(row["status"] == "failed" for row in manifest["cases"]) != manifest["truth_failed_cases"] \
            or manifest.get("no_resampling") is not True:
        raise ValueError("previous truth terminal counts or no-resampling policy differ")
    return campaign, identity, manifest, {key: bind(path) for key, path in paths.items()}, truths


def prepare_retest(previous_study, run_root, *, reference_report=REFERENCE_REPORT, protocol_harness=None):
    previous, root, reference = (Path(p).resolve() for p in (previous_study, run_root, reference_report))
    protocol_harness = Path(protocol_harness or harness.__file__).resolve()
    if root.is_relative_to(previous) or previous.is_relative_to(root) or root.is_relative_to(harness.REPO_ROOT):
        raise ValueError("retest state must be outside the repository and previous study")
    old, identity, truth, anchors, _ = verify_previous(previous, reference)
    for scope in [Path(a["doc_root"]) for a in old["arms"].values()] + [Path(c["source_root"]) for c in old["cases"]]:
        if root.is_relative_to(scope) or scope.is_relative_to(root):
            raise ValueError("retest state must not overlap source or document roots")
    protocol = {"previous_harness_sha256": identity["harness_sha256"], "retest_harness": bind(protocol_harness),
                "change_scope": "tool and output protocol only; content, native model and budgets stay frozen"}
    if root.exists():
        return verify_retest(root, previous, reference, protocol)
    root.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=root.name + ".prepare-", dir=root.parent))
    try:
        campaign = deepcopy(old)
        campaign.update(run_root=str(root), created_at=datetime.now(timezone.utc).isoformat(),
                        retest={"schema": SCHEMA, "origin": anchors,
                                "reference_report": bind(reference), "protocol": protocol,
                                "reuse_confirmed_baseline": True, "no_truth_resampling": True})
        for case in campaign["cases"]:
            for kind, filename in (("diff", "diff.patch"), ("context", "context.json")):
                dest = stage / "cases" / str(case["number"]) / filename
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(case[kind + "_path"], dest)
                case[kind + "_path"] = str(root / dest.relative_to(stage))
        write(stage / "campaign.json", campaign)
        campaign_sha = sha(stage / "campaign.json")
        records = []
        for row in truth["cases"]:
            origin_path = Path(row["path"])
            copy = stage / "private-codex/origin-truth" / origin_path.name
            copy.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(origin_path, copy)
            record = load(origin_path)
            preserved = {key: value for key, value in record.items() if key != "campaign_sha256"}
            origin = {"campaign_sha256": anchors["campaign"]["sha256"], "record": bind(origin_path),
                      "copied_record_path": str(root / copy.relative_to(stage)),
                      "preserved_payload_sha256": digest(canonical(preserved)),
                      "inputs_sha256_policy": "unchanged identity of the original independent native audit"}
            rebound = {**record, "campaign_sha256": campaign_sha, "retest_origin": origin}
            dest = stage / "private-codex/truth" / origin_path.name
            write(dest, rebound)
            records.append({**row, "path": str(root / dest.relative_to(stage)), "sha256": sha(dest)})
        manifest = {**truth, "campaign_sha256": campaign_sha, "cases": records,
                    "retest_origin": {"manifest": anchors["truth"], "no_native_reaudit": True}}
        write(stage / "private-codex/truth-manifest.json", manifest)
        write(stage / "truth-prerequisite.json", {"path": str(root / "private-codex/truth-manifest.json"),
                "sha256": sha(stage / "private-codex/truth-manifest.json"), "campaign_sha256": campaign_sha,
                "accounted_prs": sorted(prepare.HEADS)})
        proof = {"schema": SCHEMA, "campaign": {"path": str(root / "campaign.json"), "sha256": campaign_sha},
                 "origin": anchors, "reference_report": bind(reference), "protocol": protocol,
                 "all_source_and_document_hashes_verified": True,
                 "truth_manifest": {"path": str(root / "private-codex/truth-manifest.json"),
                                    "sha256": sha(stage / "private-codex/truth-manifest.json")},
                 "truth_records": [{"pr": row["pr"], "status": row["status"],
                     "origin_record": bind(Path(truth["cases"][index]["path"])),
                     "rebound_record": {"path": row["path"], "sha256": row["sha256"]},
                     "preserved_payload_sha256": load(stage / "private-codex/truth" / Path(row["path"]).name)["retest_origin"]["preserved_payload_sha256"]}
                     for index, row in enumerate(records)],
                 "truth_reused_cases": len(records), "truth_complete_cases": truth["truth_complete_cases"],
                 "truth_unknown_cases": truth["truth_failed_cases"], "native_calls": 0,
                 "original_archive_mutated": False}
        write(stage / "retest-provenance.json", proof)
        stage.rename(root)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return verify_retest(root, previous, reference, protocol)


def verify_retest(root, previous, reference, protocol):
    old, _, truth, anchors, _ = verify_previous(previous, reference)
    proof = load(root / "retest-provenance.json")
    if proof.get("schema") != SCHEMA or proof.get("origin") != anchors \
            or proof.get("reference_report") != bind(reference) or proof.get("protocol") != protocol:
        raise ValueError("retest origin or protocol provenance changed")
    check_digest(root / "campaign.json", proof["campaign"]["sha256"], "retest campaign")
    check_digest(root / "private-codex/truth-manifest.json", proof["truth_manifest"]["sha256"], "retest truth manifest")
    campaign = load(root / "campaign.json")
    expected = deepcopy(old)
    expected.update(run_root=str(root), created_at=campaign["created_at"],
                    retest={"schema": SCHEMA, "origin": anchors, "reference_report": bind(reference),
                            "protocol": protocol, "reuse_confirmed_baseline": True, "no_truth_resampling": True})
    for case in expected["cases"]:
        for kind, filename in (("diff", "diff.patch"), ("context", "context.json")):
            case[kind + "_path"] = str(root / "cases" / str(case["number"]) / filename)
            check_digest(Path(case[kind + "_path"]), case[kind + "_sha256"], "retest " + kind)
    if campaign != expected:
        raise ValueError("retest changed content, model, budget or case metadata")
    manifest = load(root / "private-codex/truth-manifest.json")
    rows = manifest["cases"]
    original = {row["pr"]: row for row in truth["cases"]}
    if manifest != {**truth, "campaign_sha256": sha(root / "campaign.json"), "cases": rows,
                    "retest_origin": {"manifest": anchors["truth"], "no_native_reaudit": True}}:
        raise ValueError("retest changed the frozen baseline manifest policy")
    if set((root / "private-codex/truth").glob("*.json")) != {Path(row["path"]) for row in rows} \
            or set((root / "private-codex/origin-truth").glob("*.json")) != {
                root / "private-codex/origin-truth" / Path(row["path"]).name for row in truth["cases"]}:
        raise ValueError("retest truth directory contains extra or missing records")
    expected_records = []
    for row in rows:
        origin = original[row["pr"]]
        old_record = load(origin["path"])
        copy = root / "private-codex/origin-truth" / Path(origin["path"]).name
        check_digest(copy, origin["sha256"], "copied origin truth")
        record = load(row["path"])
        if Path(row["path"]) != root / "private-codex/truth" / Path(origin["path"]).name:
            raise ValueError("retest truth record escaped its rebound directory")
        preserved = {key: value for key, value in record.items() if key not in {"campaign_sha256", "retest_origin"}}
        payload_sha = digest(canonical(preserved))
        if preserved != {key: value for key, value in old_record.items() if key != "campaign_sha256"} \
                or record.get("retest_origin") != {"campaign_sha256": anchors["campaign"]["sha256"],
                    "record": bind(Path(origin["path"])), "copied_record_path": str(copy),
                    "preserved_payload_sha256": payload_sha,
                    "inputs_sha256_policy": "unchanged identity of the original independent native audit"} \
                or any(row.get(key) != origin.get(key) for key in ("pr", "base", "head", "status", "confirmed_defects")):
            raise ValueError("reused truth payload, origin or status changed")
        expected_records.append({"pr": row["pr"], "status": row["status"],
            "origin_record": bind(Path(origin["path"])), "rebound_record": bind(Path(row["path"])),
            "preserved_payload_sha256": payload_sha})
    if proof.get("truth_records") != expected_records or proof.get("truth_reused_cases") != len(rows) \
            or proof.get("truth_complete_cases") != truth["truth_complete_cases"] \
            or proof.get("truth_unknown_cases") != truth["truth_failed_cases"] \
            or proof.get("native_calls") != 0 or proof.get("original_archive_mutated") is not False \
            or proof.get("all_source_and_document_hashes_verified") is not True:
        raise ValueError("retest provenance counters or truth bindings changed")
    harness.freeze_truth_prerequisite(root, {"campaign_sha256": sha(root / "campaign.json"),
        "baseline_source_sha": campaign["baseline_source_sha"], "cases": campaign["cases"],
        "arms": campaign["arms"]}, root / "private-codex/truth-manifest.json")
    judge.bound_truth(campaign, sha(root / "campaign.json"), root / "private-codex")
    return proof


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    setup = sub.add_parser("prepare", help="verify and reuse the published frozen content and pre-review labels")
    setup.add_argument("--previous-study", type=Path, required=True)
    setup.add_argument("--run-root", type=Path, required=True)
    args = parser.parse_args(argv)
    proof = prepare_retest(args.previous_study, args.run_root)
    print(json.dumps({"campaign": proof["campaign"], "provenance": str(args.run_root / "retest-provenance.json"),
                      "truth_reused_cases": proof["truth_reused_cases"],
                      "truth_unknown_cases": proof["truth_unknown_cases"], "native_calls": 0}))


if __name__ == "__main__":
    main()
