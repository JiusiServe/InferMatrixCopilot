from __future__ import annotations

import json
import hashlib
import subprocess
from pathlib import Path

import yaml

from tools.vllm_omni_release_audit import (
    GitSnapshotReader,
    audit_release,
    main,
    snapshot_inventory,
)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout.strip()


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", ".")
    _git(
        repo,
        "-c",
        "user.name=Release Audit Test",
        "-c",
        "user.email=release-audit@example.com",
        "commit",
        "-m",
        message,
    )
    return _git(repo, "rev-parse", "HEAD")


def _write_upstream(repo: Path, *, second: bool) -> None:
    files = {
        "vllm_omni/model_executor/models/registry.py": (
            '_OMNI_MODELS = {"OldArch": ("old", "model", "Old")'
            + (', "NewArch": ("new", "model", "New")' if second else "")
            + "}\n"
        ),
        "vllm_omni/diffusion/registry.py": (
            '_DIFFUSION_MODELS = {"OldPipeline": ("old", "pipe", "Old")'
            + (', "NewPipeline": ("new", "pipe", "New")' if second else "")
            + "}\n"
        ),
        "vllm_omni/config/pipeline_registry.py": (
            'OMNI_PIPELINES: dict[str, object] = {"old": OLD'
            + (', "new": NEW' if second else "")
            + "}\n"
        ),
        (
            "vllm_omni/deploy/renamed.yaml" if second else "vllm_omni/deploy/old.yaml"
        ): "model: old\n",
        "vllm_omni/model_executor/worker.py": "VALUE = 2\n"
        if second
        else "VALUE = 1\n",
    }
    if second:
        files["vllm_omni/deploy/new.yaml"] = "model: new\n"
        files["vllm_omni/diffusion/new.py"] = "PIPELINE = 'new'\n"
    for rel, content in files.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _fixture(tmp_path: Path) -> dict[str, Path | str]:
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    _git(upstream, "init", "-b", "main")
    _write_upstream(upstream, second=False)
    stale = upstream / "vllm_omni" / "model_executor" / "removed.py"
    stale.write_text("OLD = True\n", encoding="utf-8")
    old_sha = _commit(upstream, "old")
    _write_upstream(upstream, second=True)
    stale.unlink()
    (upstream / "vllm_omni" / "deploy" / "old.yaml").unlink()
    new_sha = _commit(upstream, "new")

    project = tmp_path / "project"
    knowledge = project / "knowledge"
    page = knowledge / "repos" / "vllm-omni" / "components" / "owner" / "rules.md"
    page.parent.mkdir(parents=True)
    page.write_text(
        "---\n"
        'title: "owner"\n'
        "sources: [vllm_omni/model_executor/removed.py, "
        "vllm_omni/deploy/old.yaml]\n"
        "---\n\n# Owner\n",
        encoding="utf-8",
    )
    pin = project / "PIN.md"
    pin.parent.mkdir(parents=True, exist_ok=True)
    pin.write_text(f"verified against main @ {new_sha[:8]}\n", encoding="utf-8")

    manifest_path = project / "manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "name": "vllm_omni",
                "repo": {"path": "unused"},
                "modules": {
                    "model_executor": {"local_paths": ["vllm_omni/model_executor/"]}
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    inventory = snapshot_inventory(GitSnapshotReader(upstream), new_sha)
    baseline_path = project / "release_baseline.yaml"
    baseline_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "upstream": {
                    "repository": "test/upstream",
                    "previous_audited_sha": old_sha,
                    "audited_sha": new_sha,
                },
                "inventories": {
                    name: {
                        "count": len(value),
                        "sha256": hashlib.sha256(
                            json.dumps(
                                value,
                                ensure_ascii=False,
                                sort_keys=True,
                                separators=(",", ":"),
                            ).encode("utf-8")
                        ).hexdigest(),
                    }
                    for name, value in inventory.items()
                },
                "path_owners": {
                    "configuration": [
                        "vllm_omni/config/",
                        "vllm_omni/deploy/",
                    ],
                    "diffusion": ["vllm_omni/diffusion/"],
                    "model_executor": ["vllm_omni/model_executor/"],
                },
                "owner_documents": {
                    "configuration": ["PIN.md"],
                    "diffusion": ["PIN.md"],
                    "model_executor": ["PIN.md"],
                },
                "ignored_paths": [],
                "pin_documents": ["PIN.md"],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return {
        "upstream": upstream,
        "project": project,
        "knowledge": knowledge,
        "manifest": manifest_path,
        "baseline": baseline_path,
        "old": old_sha,
        "new": new_sha,
    }


def _audit(fixture: dict[str, Path | str]):
    return audit_release(
        upstream_repo=fixture["upstream"],
        from_ref=str(fixture["old"]),
        to_ref=str(fixture["new"]),
        baseline_path=fixture["baseline"],
        adapter_manifest_path=fixture["manifest"],
        knowledge_root=fixture["knowledge"],
        project_root=fixture["project"],
    )


def test_audit_reports_registry_deploy_and_adapter_drift(tmp_path):
    fixture = _fixture(tmp_path)
    report = _audit(fixture)

    deltas = report.data["inventory"]["deltas"]
    assert deltas["autoregressive"]["added"] == ["NewArch"]
    assert deltas["diffusion"]["added"] == ["NewPipeline"]
    assert deltas["pipelines"]["added"] == ["new"]
    assert deltas["deploy_yamls"]["added"] == [
        "vllm_omni/deploy/new.yaml",
        "vllm_omni/deploy/renamed.yaml",
    ]
    assert deltas["deploy_yamls"]["removed"] == ["vllm_omni/deploy/old.yaml"]
    assert any(
        change["status"].startswith("R")
        and change["old_path"] == "vllm_omni/deploy/old.yaml"
        and change["path"] == "vllm_omni/deploy/renamed.yaml"
        for change in report.data["paths"]["changes"]
    )
    assert "vllm_omni/diffusion/new.py" in report.data["paths"]["adapter_uncovered"]


def test_removed_active_knowledge_source_fails(tmp_path):
    fixture = _fixture(tmp_path)
    report = _audit(fixture)

    stale = [
        issue
        for issue in report.data["issues"]
        if issue["kind"] == "stale_knowledge_source"
    ]
    assert stale == [
        {
            "kind": "stale_knowledge_source",
            "document": "knowledge/repos/vllm-omni/components/owner/rules.md",
            "source": "vllm_omni/deploy/old.yaml",
            "renamed_to": "vllm_omni/deploy/renamed.yaml",
        },
        {
            "kind": "stale_knowledge_source",
            "document": "knowledge/repos/vllm-omni/components/owner/rules.md",
            "source": "vllm_omni/model_executor/removed.py",
        },
    ]


def test_unmatched_path_is_a_clear_failure(tmp_path):
    fixture = _fixture(tmp_path)
    upstream = fixture["upstream"]
    path = upstream / "unowned"
    path.mkdir()
    (path / "file.txt").write_text("new\n", encoding="utf-8")
    fixture["new"] = _commit(upstream, "unmatched")

    report = _audit(fixture)

    assert any(
        issue == {"kind": "unmatched_path", "path": "unowned/file.txt"}
        for issue in report.data["issues"]
    )


def test_enforced_baseline_requires_the_previous_audited_sha(tmp_path):
    fixture = _fixture(tmp_path)

    report = audit_release(
        upstream_repo=fixture["upstream"],
        from_ref=str(fixture["new"]),
        to_ref=str(fixture["new"]),
        baseline_path=fixture["baseline"],
        adapter_manifest_path=fixture["manifest"],
        knowledge_root=fixture["knowledge"],
        project_root=fixture["project"],
    )

    assert any(
        issue["kind"] == "baseline_from_mismatch" for issue in report.data["issues"]
    )


def test_overlapping_path_owners_are_suspicious(tmp_path):
    fixture = _fixture(tmp_path)
    baseline = yaml.safe_load(Path(fixture["baseline"]).read_text(encoding="utf-8"))
    baseline["path_owners"]["second_diffusion_owner"] = ["vllm_omni/diffusion/"]
    baseline["owner_documents"]["second_diffusion_owner"] = ["PIN.md"]
    Path(fixture["baseline"]).write_text(
        yaml.safe_dump(baseline, sort_keys=False),
        encoding="utf-8",
    )

    report = _audit(fixture)

    assert any(
        issue["kind"] == "suspicious_path_route"
        and issue["path"] == "vllm_omni/diffusion/new.py"
        for issue in report.data["issues"]
    )


def test_stale_source_map_path_and_pin_fail(tmp_path):
    fixture = _fixture(tmp_path)
    baseline = yaml.safe_load(Path(fixture["baseline"]).read_text(encoding="utf-8"))
    baseline["path_owners"]["removed_owner"] = ["vllm_omni/removed_owner/"]
    baseline["owner_documents"]["removed_owner"] = ["PIN.md"]
    Path(fixture["baseline"]).write_text(
        yaml.safe_dump(baseline, sort_keys=False),
        encoding="utf-8",
    )
    Path(fixture["project"], "PIN.md").write_text(
        "verified against main @ 00000000\n",
        encoding="utf-8",
    )

    report = _audit(fixture)
    kinds = {issue["kind"] for issue in report.data["issues"]}

    assert {"stale_source_map_path", "stale_pin"} <= kinds


def test_report_json_is_deterministic_and_audit_does_not_edit_inputs(tmp_path):
    fixture = _fixture(tmp_path)
    upstream_before = _git(fixture["upstream"], "status", "--porcelain")
    project_files_before = sorted(
        path.relative_to(fixture["project"]).as_posix()
        for path in fixture["project"].rglob("*")
        if path.is_file()
    )

    first = _audit(fixture).to_json()
    second = _audit(fixture).to_json()

    assert first == second
    assert _git(fixture["upstream"], "status", "--porcelain") == upstream_before
    assert (
        sorted(
            path.relative_to(fixture["project"]).as_posix()
            for path in fixture["project"].rglob("*")
            if path.is_file()
        )
        == project_files_before
    )


def test_cli_modes_and_json_output(tmp_path):
    fixture = _fixture(tmp_path)
    output = tmp_path / "reports" / "audit.json"
    common = [
        "--from",
        str(fixture["old"]),
        "--to",
        str(fixture["new"]),
        "--repo",
        str(fixture["upstream"]),
        "--baseline",
        str(fixture["baseline"]),
        "--adapter-manifest",
        str(fixture["manifest"]),
        "--knowledge-root",
        str(fixture["knowledge"]),
        "--project-root",
        str(fixture["project"]),
        "--json-output",
        str(output),
    ]

    assert main(common + ["--mode", "enforce"]) == 1
    assert main(common + ["--mode", "report-only"]) == 0
    assert json.loads(output.read_text(encoding="utf-8"))["result"] == "drift"
