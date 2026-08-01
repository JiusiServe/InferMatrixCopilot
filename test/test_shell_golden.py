"""PR5 — tier-3 shell-golden parity (Rev 8 §8.3): the one-time capture of
the parent's LIVE config.sh §10/§11 arrays + test_watchdog.sh arrays
(`adapters/vllm_omni/rebase/shell_golden.json`, isolated-env `declare -p`,
2026-08-01) versus this substrate's command echo, data maps, and pattern
inventories.

The golden is the parent's OPERATIONAL truth. Two directions are pinned:
our runner must echo the parent's commands byte-for-byte (dry_run
RunPlan), and our adapter DATA (module maps, watchdog patterns, push
policy) must carry the parent's values — drift in either direction fails
offline, before any live comparison."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from infermatrix_copilot.engine.steps.rebase_v3 import _parse_env_pairs
from infermatrix_copilot.testing.runner import TestJob, TestRunner, _exec_wrap

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDEN = json.loads(
    (REPO_ROOT / "adapters/vllm_omni/rebase/shell_golden.json").read_text())
MANIFEST = yaml.safe_load(
    (REPO_ROOT / "adapters/vllm_omni/manifest.yaml").read_text())
WATCHDOG_YAML = yaml.safe_load(
    (REPO_ROOT / "adapters/vllm_omni/testing/watchdog_patterns.yaml")
    .read_text())


def test_golden_capture_sanity():
    """The capture is complete and sane: a real job population, every job
    has a non-empty command (the parent's EMPTY-command false-pass set was
    empty at capture time — new drift shows up as live-yaml slugs missing
    from here, enumerated in DRIFT_TRIAGE #4), full module maps, all four
    watchdog tiers."""
    jobs = GOLDEN["ci_tests"]
    assert len(jobs) >= 40
    assert all(t["cmd"].strip() for t in jobs.values())
    # every REAL job is labeled (__precommit__ is §10's phase-3.2 pseudo
    # entry, deliberately label-less in the parent)
    assert all(t["label"].strip() for slug, t in jobs.items()
               if slug != "__precommit__")
    assert set(GOLDEN["module_maps"]) == {
        "MODULE_VLLM_PATHS", "MODULE_OMNI_FILES", "MODULE_TEST_MAP",
        "MODULE_IMPORT_CHECK"}
    assert len(GOLDEN["module_maps"]["MODULE_VLLM_PATHS"]) == 8
    assert all(GOLDEN["watchdog"][k]
               for k in ("critical", "review", "simulation_allowlist",
                         "noise"))
    # sanitation held: no machine paths or credentials in the capture
    blob = json.dumps(GOLDEN)
    for needle in ("/PLACEHOLDER_ROOT", "/data/zhoutaichang", "sk-"):
        assert needle not in blob, needle


# ── tier 3: command echo ─────────────────────────────────────────────────────

def test_command_echo_parity(tmp_path):
    """THE tier-3 pin (and this PR's partial e2e): every golden §10 job
    driven through the REAL runner's dry_run yields a RunPlan whose child
    command embeds the parent's command BYTE-FOR-BYTE (modulo the
    documented `set -e` prefix), with the parent's timeout, env pairs, and
    GPU-lock semantics."""
    runner = TestRunner(repo_root=tmp_path, tests_dir=tmp_path / "tests")
    for slug, t in GOLDEN["ci_tests"].items():
        if slug == "__precommit__":
            continue     # phase 3.2's own step, pinned in test_assembly
        min_gpus = int(t["min_gpus"] or 1)
        job = TestJob(key=slug, command=t["cmd"],
                      timeout_sec=float(t["timeout_sec"] or 1800),
                      min_gpus=min_gpus,
                      env=_parse_env_pairs(t["env"]))
        plan = runner.run(job, {}, dry_run=True).plan
        assert plan is not None, slug
        # byte parity: bash -c <parent command>, sole wrapper is the
        # documented fail-fast prefix (absent when the command manages
        # its own -e state)
        assert plan.argv[:2] == ["bash", "-c"], slug
        assert plan.argv[2] == _exec_wrap(t["cmd"]), slug
        assert plan.argv[2].endswith(t["cmd"]), slug
        assert plan.timeout_sec == float(t["timeout_sec"]), slug
        # env pairs round-trip with the SHELL's own word-split + quote
        # semantics (the parent eval-exports these strings, so K="1"
        # must reach the child as 1, not a literal-quoted value)
        import shlex
        for token in shlex.split(t["env"] or ""):
            k, v = token.split("=", 1)
            assert plan.env_overlay.get(k) == v, (slug, token)
        # GPU-lock semantics: min_gpus>0 holds the lock (historical rule)
        assert plan.needs_gpu_lock == (min_gpus > 0), slug


def test_golden_timeouts_and_gpus_are_wellformed():
    for slug, t in GOLDEN["ci_tests"].items():
        assert t["timeout_sec"].isdigit() and int(t["timeout_sec"]) > 0, slug
        assert t["min_gpus"] == "" or t["min_gpus"].isdigit(), slug
        for pair in (t["env"] or "").split():
            assert "=" in pair, (slug, pair)


# ── module maps: adapter data == parent §11 ──────────────────────────────────

def test_module_map_parity_upstream_and_tests():
    """`modules.*.upstream_paths` / `test_paths` carry the parent's
    MODULE_VLLM_PATHS / MODULE_TEST_MAP verbatim (order preserved)."""
    mods = MANIFEST["modules"]
    golden_up = GOLDEN["module_maps"]["MODULE_VLLM_PATHS"]
    golden_tests = GOLDEN["module_maps"]["MODULE_TEST_MAP"]
    assert set(mods) == set(golden_up) == set(golden_tests)
    for mod in mods:
        assert mods[mod]["upstream_paths"] == golden_up[mod].split(), mod
        assert mods[mod]["test_paths"] == golden_tests[mod].split(), mod


def test_module_local_paths_cover_parent_omni_files():
    """DRIFT_TRIAGE #2 (CLOSED) stays closed: every parent
    MODULE_OMNI_FILES entry is covered by the module's `local_paths`
    (prefix match — local_paths is the recorded UNION superset)."""
    mods = MANIFEST["modules"]
    for mod, files in GOLDEN["module_maps"]["MODULE_OMNI_FILES"].items():
        local = tuple(mods[mod]["local_paths"])
        for f in files.split():
            assert any(f == p or f.startswith(p.rstrip("/") + "/")
                       or f.startswith(p) for p in local), (mod, f)


def test_module_import_check_parity():
    """Per-module import smoke targets match the parent's
    MODULE_IMPORT_CHECK (adapter data: modules.*.import_check)."""
    mods = MANIFEST["modules"]
    for mod, target in GOLDEN["module_maps"]["MODULE_IMPORT_CHECK"].items():
        ours = mods[mod].get("import_check", "")
        assert ours == target, (mod, ours, target)


# ── watchdog inventories: yaml seed == parent arrays (translated) ────────────

_POSIX_TO_RE = {
    "[[:space:]]": r"\s",
    r"\/": "/",           # ERE-escaped slash is a plain slash in `re`
}


def _translate(pattern: str) -> str:
    for posix, py in _POSIX_TO_RE.items():
        pattern = pattern.replace(posix, py)
    return pattern


@pytest.mark.parametrize("tier", ["critical", "review",
                                  "simulation_allowlist", "noise"])
def test_watchdog_inventory_bijection(tier):
    """Every parent watchdog pattern exists in the adapter seed (after the
    documented POSIX-class/escape translation) and vice versa — an
    inventory drift in either direction fails offline. The PR5 sweep
    itself caught one: the parent's post-PR1 'Released CuMem memory pool'
    noise entry."""
    golden = {_translate(p) for p in GOLDEN["watchdog"][tier]}
    ours = set(WATCHDOG_YAML[tier])
    assert golden == ours, {
        "only_parent": sorted(golden - ours),
        "only_seed": sorted(ours - golden)}
    for p in ours:
        re.compile(p)     # every seed pattern is valid `re`


# ── tier 1: push policy bytes ────────────────────────────────────────────────

def test_push_policy_parity():
    """Commit-message template and the never-committed unstage set match
    the parent byte-for-byte (92_push_to_ci.sh literal +
    unstage_generated_outputs case patterns)."""
    push = MANIFEST["rebase"]["push"]
    assert push["commit_message_template"] == \
        GOLDEN["push"]["commit_message_template"]
    assert push["unstage_globs"] == GOLDEN["push"]["unstage_case_patterns"]


# ── DRIFT #4: the false-pass mechanism is dead here ──────────────────────────

def test_empty_command_never_passes(tmp_path):
    """The parent's §10 false-pass (missing slug -> empty command ->
    rc=0 'pass') is structurally impossible in this substrate: the
    manifest builder DROPS labeled steps with no runnable command, and
    the §2.3 taxonomy classifies an empty command as an infrastructure
    failure if one ever arrives at the loop."""
    from infermatrix_copilot.rebase_engine.test_manifest import (
        ManifestSpec, build_manifest)
    import subprocess
    repo = tmp_path / "repo"
    (repo / ".buildkite" / "cuda").mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    (repo / ".buildkite" / "cuda" / "test-merge.yml").write_text(
        yaml.safe_dump({"steps": [
            {"label": "Real Job", "commands": ["pytest tests/x.py"]},
            {"label": "Block Step", "commands": []},
            {"label": "Export Only", "commands": ["export A=1"]},
        ]}))
    built = build_manifest(repo, ManifestSpec.from_manifest(MANIFEST))
    assert [j.slug for j in built.jobs] == ["real_job"]
    assert all(j.command.strip() for j in built.jobs)