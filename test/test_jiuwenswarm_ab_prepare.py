"""A frozen target tip must not become the diff base of an older fork."""
import json
from pathlib import Path
import subprocess

import pytest

from eval import jiuwenswarm_ab_prepare as prepare


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root).decode().strip()


def test_old_fork_uses_merge_base_and_resume_does_not_rewrite(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    git(source, "init", "-q")
    git(source, "config", "user.email", "eval@example.invalid")
    git(source, "config", "user.name", "Offline eval test")
    (source / "core.py").write_text("original = True\n")
    git(source, "add", ".")
    git(source, "commit", "-qm", "common")
    common = git(source, "rev-parse", "HEAD")
    git(source, "checkout", "-qb", "feature")
    (source / "core.py").write_text("original = False\n")
    git(source, "commit", "-qam", "feature")
    head = git(source, "rev-parse", "HEAD")
    git(source, "checkout", "-qb", "target", common)
    (source / "target_only.py").write_text("historical = True\n")
    git(source, "add", ".")
    git(source, "commit", "-qm", "target history")
    target = git(source, "rev-parse", "HEAD")
    monkeypatch.setattr(prepare, "BASE", target)
    monkeypatch.setattr(prepare, "HEADS", {1: head})
    command = prepare.command

    def metadata(args, cwd=None):
        if args[0] == "gh":
            return json.dumps({"base": {"sha": "f" * 40}, "head": {"sha": head}, "title": "feature",
                               "body": "", "html_url": "https://example.invalid/pull/1",
                               "created_at": "2026-10-03T00:00:00Z"}).encode()
        return command(args, cwd)

    monkeypatch.setattr(prepare, "command", metadata)
    root = tmp_path / "archive"
    result = prepare.prepare(root, source, source)
    case = result["cases"][0]
    assert case["base"] == common
    assert case["target"] == target
    assert case["changed_files"] == ["core.py"]
    assert "target_only.py" not in Path(case["diff_path"]).read_text()
    assert result["analysis_groups"] == {"primary_prospective": [], "older_fork_exploratory": [1]}
    inputs = [root / "campaign.json", Path(case["context_path"]), Path(case["diff_path"])]
    before = [(p.read_bytes(), p.stat().st_mtime_ns) for p in inputs]
    assert prepare.prepare(root, source, source) == result
    assert [(p.read_bytes(), p.stat().st_mtime_ns) for p in inputs] == before
    Path(case["diff_path"]).write_text("tampered\n")
    with pytest.raises(AssertionError):
        prepare.prepare(root, source, source)


def test_raw_material_rejected_inside_repository(tmp_path):
    with pytest.raises(ValueError, match="outside"):
        prepare.prepare(tmp_path / "raw", tmp_path, tmp_path)
