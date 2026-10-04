"""Offline archive fixtures only; no live benchmark, model, or trace mutation."""
import importlib.util
import json
from pathlib import Path

import pytest


MODULE = Path(__file__).resolve().parents[1] / "eval/jiuwenswarm_ab_archive.py"
SPEC = importlib.util.spec_from_file_location("ab_archive", MODULE)
archive = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(archive)


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n")
    return archive._sha(path.read_bytes())


def _study(tmp_path):
    state = tmp_path / "state"
    run = state / "evaluation-v2"
    campaign_sha = _write(run / "campaign.json", {"schema": "jiuwenswarm-pr-review-ab-v1", "run_root": str(run),
        "cases": [{"number": pr} for pr in range(1, 13)]})
    identity = {"schema": "jiuwenswarm-pr-review-ab-v1", "campaign_sha256": campaign_sha}
    identity_sha = archive._sha(json.dumps(identity, sort_keys=True).encode())
    _write(run / "identity.json", {**identity, "identity_sha256": identity_sha})
    rows = []
    for pr in range(1, 13):
        for arm in ("A", "B"):
            for repeat in range(3):
                item = run / "items" / f"review-pr{pr}-{arm}-r{repeat + 1}"
                a = item / "attempt-1"
                _write(a / "provider_config.json", {"secret": "DO_NOT_INLINE_AUTH_VALUE"})
                output = item / "normalized-review.json"
                output_sha = _write(output, {"review_comments": []})
                result_path = item / "result.json"
                status = "invalid_run" if pr == 12 else "valid"
                result_sha = _write(result_path, {"number": pr, "arm": arm, "repetition": repeat + 1,
                    "preflight": False, "status": status, "campaign_sha256": campaign_sha, "identity_sha256": identity_sha,
                    "normalized_output_sha256": output_sha,
                    "attempts": [{"attempt_root": str(a), "status": status}]})
                rows.append({"pr": pr, "arm": arm, "repeat": repeat, "status": "failed" if status == "invalid_run" else "complete",
                    "native_status": status, "run_result_path": str(result_path), "run_result_sha256": result_sha,
                    "output_path": str(output), "normalized_output_sha256": output_sha,
                    "campaign_sha256": campaign_sha, "identity_sha256": identity_sha})
    _write(run / "reviews-manifest.json", {"schema": "jiuwenswarm-pr-reviews-v1", "campaign_sha256": campaign_sha,
                                          "identity_sha256": identity_sha, "reviews": rows})
    truth_sha = _write(run / "private-codex/truth-manifest.json", {"frozen": True, "campaign_sha256": campaign_sha})
    for pr in range(1, 13):
        _write(run / "private-codex/scores" / f"pr-{pr}.json", {"schema": "jiuwenswarm-pr-blind-score-v1", "pr": pr,
            "status": "failed" if pr == 12 else "complete", "truth_manifest_sha256": truth_sha,
            "blind_mapping": {f"R{i}": row for i, row in enumerate([r for r in rows if r["pr"] == pr], 1)}})
    _write(state / "mapping/routes.json", {"source_path": "source.py"})
    (state / "snapshots/original-docs").mkdir(parents=True)
    (state / "snapshots/original-docs/guide.md").write_text("Author documentation\n")
    _write(state / "extraction-timing.json", {"observed_seconds": 1})
    return state


def test_index_is_reproducible_sorted_and_never_inlines_raw_secrets(tmp_path):
    state = _study(tmp_path)
    output = state / "raw-trace-index.json"
    first = archive.write_index(state, output)
    original = output.read_bytes()
    second = archive.write_index(state, output)
    assert first == second
    assert output.read_bytes() == original
    assert b"DO_NOT_INLINE_AUTH_VALUE" not in original
    assert [row["path"] for row in first["files"]] == sorted(row["path"] for row in first["files"])
    assert all(set(row) == {"path", "bytes", "sha256"} for row in first["files"])
    assert all(row["path"] != "raw-trace-index.json" for row in first["files"])
    assert first["total_bytes"] == sum(row["bytes"] for row in first["files"])


def test_caches_locks_and_derived_reports_do_not_enter_the_index(tmp_path):
    state = _study(tmp_path)
    run = state / "evaluation-v2"
    for name in ["collection.json", "private-codex/results.json", "zcode-pacing.json.lock", "items/review-pr1-A-r1/attempt-1/storage/auth.json",
                 "items/review-pr1-A-r1/attempt-1/traces/index.db", "report-summary.json", "items/review-pr1-A-r1/attempt-1/temporary.tmp"]:
        _write(run / name, {"irrelevant": True})
    _write(state / "mapping/original-content-cn.md", {"derived_report": True})
    paths = {row["path"] for row in archive.build_index(state)["files"]}
    assert not any(any(part in path for part in ["collection.json", "results.json", ".lock", "storage", "index.db", "report-summary", "temporary.tmp"]) for path in paths)
    assert "mapping/original-content-cn.md" not in paths


def test_original_author_reports_and_storage_docs_remain_raw_evidence(tmp_path):
    state = _study(tmp_path)
    names = ["storage/report.md", "docs/report.md", "docs/storage/architecture.md", "results.json", "source.tmp", "source.lock", "node_modules/example.md"]
    for name in names:
        doc = state / "snapshots/original-docs" / name
        doc.parent.mkdir(parents=True, exist_ok=True)
        doc.write_text("Original frozen evidence\n")
    _write(state / "mapping/inputs/source.tmp", {"raw_input": True})
    paths = {row["path"] for row in archive.build_index(state)["files"]}
    assert {"snapshots/original-docs/" + name for name in names} <= paths
    assert "mapping/inputs/source.tmp" in paths


def test_delivery_supplemental_changes_require_a_new_index_digest(tmp_path):
    state = _study(tmp_path)
    for name in ["baseline-pr290.json", "ci-code-checks.json"]:
        _write(state / name, {"finalized": 1})
    first = archive.build_index(state)
    paths = {row["path"] for row in first["files"]}
    assert {"baseline-pr290.json", "ci-code-checks.json"} <= paths
    _write(state / "ci-code-checks.json", {"finalized": 2})
    second = archive.build_index(state)
    assert first["files_sha256"] != second["files_sha256"]


@pytest.mark.parametrize("kind", ["missing_review", "started_review", "missing_score", "started_score"])
def test_live_or_incomplete_campaign_is_rejected(tmp_path, kind):
    state = _study(tmp_path)
    if "review" in kind:
        path = state / "evaluation-v2/reviews-manifest.json"
        value = json.loads(path.read_text())
        if kind == "missing_review": value["reviews"].pop()
        else: value["reviews"][0]["status"] = "started"
        _write(path, value)
    else:
        path = state / "evaluation-v2/private-codex/scores/pr-1.json"
        if kind == "missing_score": path.unlink()
        else:
            value = json.loads(path.read_text());value["status"] = "started";_write(path, value)
    with pytest.raises(ValueError):
        archive.build_index(state)


def test_result_hash_change_is_rejected_before_raw_indexing(tmp_path):
    state = _study(tmp_path)
    path = state / "evaluation-v2/items/review-pr1-A-r1/result.json"
    path.write_text(path.read_text() + " ")
    with pytest.raises(ValueError, match="hash differs"):
        archive.build_index(state)


def test_unaccounted_native_attempt_is_rejected(tmp_path):
    state = _study(tmp_path)
    (state / "evaluation-v2/items/review-pr1-A-r1/attempt-2").mkdir()
    with pytest.raises(ValueError, match="live/incomplete native attempt"):
        archive.build_index(state)


def test_symlink_escape_and_git_output_are_rejected(tmp_path):
    state = _study(tmp_path)
    outside = tmp_path / "private"
    outside.write_text("PRIVATE_DATA")
    (state / "mapping/escape").symlink_to(outside)
    with pytest.raises(ValueError, match="symlink"):
        archive.build_index(state)
    (state / "mapping/escape").unlink()
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    with pytest.raises(ValueError, match="outside Git"):
        archive.write_index(state, repo / "index.json")


def test_output_cannot_overwrite_raw_inputs(tmp_path):
    state = _study(tmp_path)
    with pytest.raises(ValueError, match="overwrite"):
        archive.write_index(state, state / "mapping/index.json")
    with pytest.raises(ValueError, match="overwrite"):
        archive.write_index(state, state / "extraction-timing.json")
