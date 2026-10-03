"""Offline input/label isolation checks for a fresh protocol retest."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess

import pytest

from eval import jiuwenswarm_ab_retest as retest
from eval import jiuwenswarm_ab_report as report


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root).decode().strip()


@pytest.fixture
def frozen(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    git(source, "init", "-q")
    git(source, "config", "user.email", "retest@example.invalid")
    git(source, "config", "user.name", "Offline retest")
    (source / "core.py").write_text("def run(value=None):\n    if value is None:\n        return 0\n    return value\n")
    git(source, "add", ".")
    git(source, "commit", "-qm", "baseline")
    base = git(source, "rev-parse", "HEAD")
    baseline = tmp_path / "baseline"
    git(source, "worktree", "add", "--quiet", "--detach", str(baseline), base)
    (source / "core.py").write_text("def run(value=None):\n    return value + 1\n")
    git(source, "commit", "-qam", "new missing guard")
    head = git(source, "rev-parse", "HEAD")
    numbers = (7639, 7641, 7642, 7645, 7647, 7649, 7650, 7651, 7654, 7655, 7656, 7675)
    monkeypatch.setattr(retest.prepare, "HEADS", {n: head for n in numbers})
    monkeypatch.setattr(retest.prepare, "BASE", base)
    monkeypatch.setattr(retest.judge, "SOURCE_PIN", base)
    previous = tmp_path / "archive/evaluation-v2"
    previous.mkdir(parents=True)
    cli = tmp_path / "zcode"
    cli.write_text("offline CLI fixture; never execute\n")
    protocol = tmp_path / "new-harness.py"
    protocol.write_text("# revised protocol\n")
    arms, frozen_arms, snapshots = {}, {}, {}
    for arm in ("A", "B"):
        root = tmp_path / "snapshots" / arm
        doc = root / "repos/jiuwenswarm/architecture.md"
        doc.parent.mkdir(parents=True)
        doc.write_text(f"# Architecture {arm}\nExplains a real source behavior.\n")
        manifest = retest.harness.document_manifest(root)
        items = [{"path": k, "sha256": v} for k, v in manifest.items()]
        arms[arm] = {"doc_root": str(root), "repo_subdir": "repos/jiuwenswarm", "sha256": retest.digest(retest.canonical(items))}
        frozen_arms[arm] = {"doc_root": str(root), "repo_subdir": "repos/jiuwenswarm", "documents": manifest}
        snapshots[arm] = {**arms[arm], "items": items}
    cases = []
    for number in numbers:
        directory = previous / "cases" / str(number)
        directory.mkdir(parents=True)
        context = directory / "context.json"
        retest.write(context, {"number": number, "frozen_base": base, "frozen_target": base,
                               "frozen_head": head, "title": "Frozen case", "body": "No additional docs"})
        diff = directory / "diff.patch"
        diff.write_bytes(retest.harness.git(source, "diff", "--no-ext-diff", "--no-color", base, head, "--"))
        cases.append({"number": number, "base": base, "target": base, "head": head,
                      "source_root": str(source), "diff_path": str(diff), "diff_sha256": retest.sha(diff),
                      "context_path": str(context), "context_sha256": retest.sha(context),
                      "changed_files": ["core.py"], "target_base_diverged": False})
    campaign = {"schema": retest.harness.SCHEMA, "run_root": str(previous), "baseline_source_sha": base,
                "baseline_source_root": str(baseline), "cases": cases, "arms": arms,
                "budget": deepcopy(retest.EXPECTED_BUDGET), "native": deepcopy(retest.EXPECTED_NATIVE),
                "analysis_groups": retest.prepare.analysis_groups(cases)}
    retest.write(previous / "campaign.json", campaign)
    campaign_sha = retest.sha(previous / "campaign.json")
    identity = {"schema": retest.harness.SCHEMA, "campaign_sha256": campaign_sha,
                "baseline_source_sha": base, "harness_sha256": "a" * 64,
                "arms": frozen_arms, "cases": [{**c, "sources": retest.harness.tracked_sources(source)} for c in cases],
                "native": {"model": "GLM-5.3", "provider_id": retest.SUBSCRIPTION_PROVIDER,
                           "reasoning_level": "max", "cli_path": str(cli), "cli_sha256": retest.sha(cli)},
                "limits": {"knowledge_chars": 6000, "source_calls": 60, "source_result_chars": 24000,
                           "timeout_s": 1800, "start_interval_s": 15, "rate_cooldown_s": 90, "workers": 13}}
    identity["identity_sha256"] = retest.digest(json.dumps(identity, sort_keys=True).encode())
    retest.write(previous / "identity.json", identity)
    rows = []
    for case in cases:
        number = case["number"]
        record = {"schema": retest.judge.TRUTH_SCHEMA, "pr": number, "base": base, "head": head,
                  "campaign_sha256": campaign_sha, "inputs_sha256": "b" * 64, "started_at": 123,
                  "status": "failed" if number == 7656 else "complete", "cost_usd": None}
        if number == 7656:
            record["error"] = "existing source needs explicit baseline evidence"
        else:
            record["data"] = {"issues": [], "excluded_candidates": []}
        if number == 7639:
            record["data"]["issues"] = [{"issue_id": "PR7639-D1", "root_cause": "removed None guard",
                "title": "Default input raises", "body": "None cannot be incremented", "file": "core.py", "line": 2,
                "severity": "P2", "introduced_or_worsened": "introduced", "trigger": "call run()",
                "consequence": "TypeError", "baseline_comparison": "Baseline returns zero",
                "evidence": [{"version": "base", "path": "core.py", "start": 1, "end": 4},
                             {"version": "head", "path": "core.py", "start": 1, "end": 2}]}]
        path = previous / "private-codex/truth" / f"pr-{number}.json"
        retest.write(path, record)
        rows.append({"pr": number, "base": base, "head": head, "status": record["status"],
                     "confirmed_defects": len(record["data"]["issues"]) if record["status"] == "complete" else None,
                     **retest.bind(path)})
    manifest = {"schema": "jiuwenswarm-truth-manifest-v1", "campaign_sha256": campaign_sha,
                "source_pin": base, "frozen": True, "no_resampling": True,
                "truth_complete_cases": 11, "truth_failed_cases": 1, "cases": rows}
    manifest_path = previous / "private-codex/truth-manifest.json"
    retest.write(manifest_path, manifest)
    retest.write(previous / "truth-prerequisite.json", {**retest.bind(manifest_path),
                "campaign_sha256": campaign_sha, "accounted_prs": list(numbers)})
    inventory_path = previous.parent / "mapping/inventory.json"
    retest.write(inventory_path, {"pin": base, "snapshots": snapshots})
    reference = tmp_path / "published-report.json"
    retest.write(reference, {"source_pin": base, "snapshot_sha256": {a: arms[a]["sha256"] for a in arms},
                "inputs": {"campaign": retest.bind(previous / "campaign.json"),
                           "runtime_identity": retest.bind(previous / "identity.json"),
                           "truth": retest.bind(manifest_path), "inventory": retest.bind(inventory_path)}})
    return {"previous": previous, "root": tmp_path / "retest/evaluation-v2", "reference": reference,
            "protocol": protocol, "source": source, "campaign": campaign}


def run(frozen):
    return retest.prepare_retest(frozen["previous"], frozen["root"], reference_report=frozen["reference"],
                                 protocol_harness=frozen["protocol"])


def test_new_campaign_preserves_labels_unknown_and_original_bytes(frozen, monkeypatch):
    def no_models(*_a, **_k):
        pytest.fail("preparation must never call native models")
    monkeypatch.setattr(retest.judge, "call_native", no_models)
    before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in frozen["previous"].rglob("*") if p.is_file()}
    proof = run(frozen)
    assert proof["native_calls"] == 0 and proof["truth_reused_cases"] == 12 and proof["truth_unknown_cases"] == 1
    assert proof["campaign"]["sha256"] != proof["origin"]["campaign"]["sha256"]
    assert len(proof["truth_records"]) == 12
    root = frozen["root"]
    campaign = retest.load(root / "campaign.json")
    truths, _ = retest.judge.bound_truth(campaign, retest.sha(root / "campaign.json"), root / "private-codex")
    assert truths[7656] is None and truths[7639][0]["issue_id"] == "PR7639-D1"
    failed = retest.load(root / "private-codex/truth/pr-7656.json")
    assert failed["status"] == "failed" and "data" not in failed and "baseline evidence" in failed["error"]
    report.validate_evaluation(root, campaign, {}, retest.load(root / "private-codex/truth-manifest.json"), {})
    assert {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in before} == before
    resumed = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in root.rglob("*") if p.is_file()}
    assert run(frozen) == proof
    assert {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in resumed} == resumed


@pytest.mark.parametrize("kind", ["campaign", "identity", "truth", "inventory", "diff", "context", "source", "doc", "cli"])
def test_previous_frozen_byte_tampering_rejected_before_new_files(frozen, kind):
    c = frozen["campaign"]
    paths = {"campaign": frozen["previous"] / "campaign.json", "identity": frozen["previous"] / "identity.json",
             "truth": frozen["previous"] / "private-codex/truth-manifest.json",
             "inventory": frozen["previous"].parent / "mapping/inventory.json",
             "diff": Path(c["cases"][0]["diff_path"]), "context": Path(c["cases"][0]["context_path"]),
             "source": frozen["source"] / "core.py",
             "doc": Path(c["arms"]["B"]["doc_root"]) / "repos/jiuwenswarm/architecture.md",
             "cli": Path(retest.load(frozen["previous"] / "identity.json")["native"]["cli_path"])}
    paths[kind].write_bytes(paths[kind].read_bytes() + b"\n# tampered\n")
    with pytest.raises(ValueError):
        run(frozen)
    assert not frozen["root"].exists()


def test_source_checkout_head_mismatch_is_rejected(frozen):
    git(frozen["source"], "checkout", "--quiet", frozen["campaign"]["baseline_source_sha"])
    with pytest.raises(ValueError, match="HEAD differs"):
        run(frozen)


@pytest.mark.parametrize("extra", ["doc", "truth"])
def test_added_bridge_document_or_hidden_truth_record_is_rejected(frozen, extra):
    if extra == "doc":
        path = Path(frozen["campaign"]["arms"]["A"]["doc_root"]) / "repos/jiuwenswarm/unfrozen.md"
    else:
        path = frozen["previous"] / "private-codex/truth/pr-9999.json"
    path.write_text("{}\n")
    with pytest.raises(ValueError, match="manifest differs|extra or missing"):
        run(frozen)


@pytest.mark.parametrize("field", ["budget", "native", "cases"])
def test_reference_refresh_cannot_authorize_changed_fixed_experiment_policy(frozen, field):
    previous = frozen["previous"]
    campaign = retest.load(previous / "campaign.json")
    if field == "budget":
        campaign["budget"]["knowledge_chars"] = 12000
    elif field == "native":
        campaign["native"]["model"] = "Other-model"
    else:
        campaign["cases"].append(deepcopy(campaign["cases"][0]))
    retest.write(previous / "campaign.json", campaign)
    identity = retest.load(previous / "identity.json")
    identity["campaign_sha256"] = retest.sha(previous / "campaign.json")
    identity.pop("identity_sha256")
    identity["identity_sha256"] = retest.digest(json.dumps(identity, sort_keys=True).encode())
    retest.write(previous / "identity.json", identity)
    reference = retest.load(frozen["reference"])
    reference["inputs"]["campaign"] = retest.bind(previous / "campaign.json")
    reference["inputs"]["runtime_identity"] = retest.bind(previous / "identity.json")
    retest.write(frozen["reference"], reference)
    with pytest.raises(ValueError, match="budgets|selected PRs"):
        run(frozen)


@pytest.mark.parametrize("target", ["diff", "campaign", "truth", "origin", "harness"])
def test_resume_rejects_changed_inputs_labels_and_protocol(frozen, target):
    run(frozen)
    paths = {"diff": frozen["root"] / "cases/7639/diff.patch", "campaign": frozen["root"] / "campaign.json",
             "truth": frozen["root"] / "private-codex/truth/pr-7639.json",
             "origin": frozen["root"] / "private-codex/origin-truth/pr-7656.json", "harness": frozen["protocol"]}
    paths[target].write_bytes(paths[target].read_bytes() + b"\n")
    with pytest.raises(ValueError):
        run(frozen)


def test_interrupted_preparation_does_not_publish_partial_campaign(frozen, monkeypatch):
    real_write = retest.write
    def interrupt(path, value):
        if path.name == "truth-manifest.json":
            raise OSError("simulated interrupted setup")
        return real_write(path, value)
    monkeypatch.setattr(retest, "write", interrupt)
    with pytest.raises(OSError, match="interrupted"):
        run(frozen)
    assert not frozen["root"].exists()
    assert not list(frozen["root"].parent.glob("*.prepare-*"))
    monkeypatch.setattr(retest, "write", real_write)
    assert run(frozen)["truth_reused_cases"] == 12


def test_previous_study_cannot_be_reused_as_output(frozen):
    with pytest.raises(ValueError, match="previous study"):
        retest.prepare_retest(frozen["previous"], frozen["previous"], reference_report=frozen["reference"])
