"""PR2 — phase-1 cluster: wheel picker/pin, worktree guard extensions,
commit assignment, module path sync, api-drift guard helpers.

Every parity behavior called out in the module docstrings is pinned here, and
`test_phase1_partial_e2e` chains the whole cluster over fixture git repos
(upstream + target) the way the rebase pipeline will drive it.
"""

from __future__ import annotations

import asyncio
import re
import subprocess
from pathlib import Path

import pytest

from infermatrix_copilot.engine.registry import StepRegistry
from infermatrix_copilot.engine.step import FailureKind, StepContext
from infermatrix_copilot.engine.steps import register_builtin_steps
from infermatrix_copilot.rebase_engine import assign, path_sync, wheel, worktree
from infermatrix_copilot.rebase_engine.path_sync import CuratedEntry, PathSyncError
from infermatrix_copilot.rebase_engine.wheel import (
    PinSpec, WheelInstallError, WheelPickError, WheelSpec)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=str(repo), check=True, text=True,
                       capture_output=True)
    return r.stdout.strip()


def _make_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-q")
    _git(path, "checkout", "-q", "-B", "main")
    _git(path, "config", "user.name", "fixture")
    _git(path, "config", "user.email", "fixture@example.com")
    return path


def _commit(repo: Path, files: dict[str, str], msg: str) -> str:
    for rel, content in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)
    return _git(repo, "rev-parse", "HEAD")


SPEC = WheelSpec(package="pkg", variant="cu000", arch="x86_64",
                 index_url_template="https://idx.example/{commit}/{variant}/{package}/",
                 import_check_modules=("pkg._C",), reinstall_retries=3)


@pytest.fixture()
def upstream_pair(tmp_path):
    """(source, clone): 4 commits c1..c4 on main; the clone has origin set."""
    src = _make_repo(tmp_path / "up-src")
    shas = [
        _commit(src, {"vllm/config/x.py": "1"}, "c1"),
        _commit(src, {"vllm/v1/worker/y.py": "1"}, "c2"),
        _commit(src, {"vllm/config/x.py": "2"}, "c3"),
        _commit(src, {"README.md": "r"}, "c4"),
    ]
    clone = tmp_path / "up"
    subprocess.run(["git", "clone", "-q", str(src), str(clone)], check=True)
    _git(clone, "config", "user.name", "fixture")
    _git(clone, "config", "user.email", "fixture@example.com")
    return src, clone, shas


# -- wheel: pick ---------------------------------------------------------------

def test_pick_walk_order_and_baseline_fallback(upstream_pair):
    _, clone, shas = upstream_pair
    c1, c2, c3, c4 = shas
    probed = []

    def probe(rev):
        probed.append(rev)
        return rev == c1

    found = wheel.pick_wheel_commit(clone, "main", SPEC, probe=probe,
                                    baseline=c2)
    # newest-first; the baseline is probed twice (loop head + explicit
    # fallback — shell parity), then the walk continues past it
    assert probed == [c4, c3, c2, c2, c1]
    assert found == c1
    assert _git(clone, "rev-parse", "HEAD") == c1


def test_pick_first_hit_wins(upstream_pair):
    _, clone, shas = upstream_pair
    c1, c2, c3, c4 = shas
    found = wheel.pick_wheel_commit(clone, "main", SPEC,
                                    probe=lambda r: r == c3, baseline=c1)
    assert found == c3


def test_pick_no_wheel_anywhere_raises(upstream_pair):
    _, clone, _ = upstream_pair
    with pytest.raises(WheelPickError, match="no commit with a"):
        wheel.pick_wheel_commit(clone, "main", SPEC, probe=lambda r: False)


def test_pick_forced_commit(upstream_pair):
    _, clone, shas = upstream_pair
    c2 = shas[1]
    assert wheel.pick_wheel_commit(clone, "main", SPEC, probe=lambda r: r == c2,
                                   force_commit=c2[:8]) == c2
    with pytest.raises(WheelPickError, match="no .* wheel"):
        wheel.pick_wheel_commit(clone, "main", SPEC, probe=lambda r: False,
                                force_commit=c2)
    with pytest.raises(WheelPickError, match="could not be resolved"):
        wheel.pick_wheel_commit(clone, "main", SPEC, probe=lambda r: True,
                                force_commit="deadbeef00")
    # release mode skips the probe for a forced commit
    assert wheel.pick_wheel_commit(clone, "main", SPEC, probe=lambda r: False,
                                   force_commit=c2, release_mode=True) == c2


def test_pick_release_mode_uses_tip_without_probe(upstream_pair):
    _, clone, shas = upstream_pair
    probed = []
    found = wheel.pick_wheel_commit(clone, "main", SPEC,
                                    probe=lambda r: probed.append(r),
                                    release_mode=True)
    assert found == shas[-1] and probed == []


def test_pick_resets_diverged_local_branch(upstream_pair):
    """A leftover local commit (prior run's detached HEAD re-attached, or an
    experiment) must not halt the pick: the reference checkout is
    deterministically reset to origin's tip."""
    _, clone, shas = upstream_pair
    stray = _commit(clone, {"stray.txt": "x"}, "stray local commit")
    found = wheel.pick_wheel_commit(clone, "main", SPEC,
                                    probe=lambda r: r == shas[-1])
    assert found == shas[-1]
    assert stray not in _git(clone, "log", "--format=%H", "main")


def test_missing_remote_branch_raises(upstream_pair):
    _, clone, _ = upstream_pair
    with pytest.raises(WheelPickError, match="origin/nope does not exist"):
        wheel.pick_wheel_commit(clone, "nope", SPEC, probe=lambda r: True)


def test_arch_probe_requires_arch_in_listing():
    spec = SPEC
    listings = {"https://idx.example/aaa/cu000/pkg/": "pkg-1.0-x86_64.whl",
                "https://idx.example/bbb/cu000/pkg/": "pkg-1.0-aarch64.whl",
                "https://idx.example/ccc/cu000/pkg/": ""}
    probe = wheel.make_arch_probe(spec, fetch=lambda url: listings.get(url, ""))
    assert probe("aaa") is True
    assert probe("bbb") is False   # listing exists but only a foreign arch
    assert probe("ccc") is False   # empty listing


# -- wheel: install ------------------------------------------------------------

def test_version_matches_commit():
    full = "5af684c31" + "0" * 31
    assert wheel.version_matches_commit(f"0.9.dev+{full}", full)
    assert wheel.version_matches_commit(f"0.9.dev+g{full[:12]}x", full)
    # embedded +g hash SHORTER than 12 chars still matches by prefix
    assert wheel.version_matches_commit("0.9.dev0+g5af684c31.precompiled", full)
    assert not wheel.version_matches_commit("0.9.dev0+gdeadbeef.pre", full)
    assert not wheel.version_matches_commit("", full)


def test_import_check_snippet_semantics(tmp_path):
    ok = WheelSpec(package="json", variant="v", arch="a",
                   index_url_template="u", import_check_modules=("json.decoder",))
    rc = subprocess.run(["python3", "-c", wheel.build_import_check_snippet(ok)])
    assert rc.returncode == 0
    bad = WheelSpec(package="json", variant="v", arch="a",
                    index_url_template="u",
                    import_check_modules=("no_such_module_xyz",))
    rc = subprocess.run(["python3", "-c", wheel.build_import_check_snippet(bad)],
                        capture_output=True, text=True)
    assert rc.returncode != 0 and "extension missing" in rc.stderr


def _fake_exec(script: dict):
    """Dispatch fake for wheel's RunFn keyed on argv[0..2]; records calls."""
    calls = []

    def run(cmd, **kw):
        calls.append(cmd)
        key = tuple(cmd[:3])
        for match, result in script.items():
            if key[:len(match)] == match:
                return result() if callable(result) else result
        return 0, "", ""
    return run, calls


def test_install_skips_when_healthy(tmp_path, monkeypatch):
    monkeypatch.setattr(wheel, "release_editable_install_locks",
                        lambda repo, **k: [])
    commit = "a" * 40
    run, calls = _fake_exec({
        ("python3", "-c"): (0, f"1.0+g{commit[:9]}\n", ""),
    })
    changed = wheel.ensure_wheel_installed(
        tmp_path, commit, SPEC, python="python3",
        install_log=tmp_path / "i.log", import_check_log=tmp_path / "c.log",
        pre_checkout_head=commit, run=run)
    assert changed is False
    assert not any(c[0] == "uv" for c in calls)


def test_install_retries_only_import_failures(tmp_path, monkeypatch):
    """Install failure aborts immediately; import-check failure retries with a
    stale-artifact clean between attempts."""
    monkeypatch.setattr(wheel, "release_editable_install_locks",
                        lambda repo, **k: [])
    import dataclasses
    spec = dataclasses.replace(SPEC, stale_artifact_globs=("_C*.so",))
    commit = "b" * 40
    stale = tmp_path / "pkg" / "_C.abi3.so"
    stale.parent.mkdir()
    stale.write_text("stale")
    check_results = iter([(1, "", "undefined symbol: foo"),   # initial health
                          (1, "", "undefined symbol: foo"),   # attempt 1
                          (0, "ok", "")])                     # attempt 2

    def run(cmd, **kw):
        if cmd[0] == "python3" and "import importlib" in cmd[2]:
            return next(check_results)
        if cmd[0] == "python3":
            return 0, "0.1\n", ""            # version present but mismatched
        return 0, "", ""                     # uv calls succeed
    changed = wheel.ensure_wheel_installed(
        tmp_path, commit, spec, python="python3",
        install_log=tmp_path / "i.log", import_check_log=tmp_path / "c.log",
        pre_checkout_head=commit, run=run)
    assert changed is True
    assert not stale.exists()               # cleaned before attempt 2

    def failing_install(cmd, **kw):
        if cmd[:3] == ["uv", "pip", "install"]:
            return 1, "", "boom"
        if cmd[0] == "python3" and "import importlib" in cmd[2]:
            return 1, "", "broken"
        return 0, "", ""
    with pytest.raises(WheelInstallError, match="wheel install failed"):
        wheel.ensure_wheel_installed(
            tmp_path, commit, SPEC, python="python3",
            install_log=tmp_path / "i.log",
            import_check_log=tmp_path / "c.log", run=failing_install)


def test_install_exhausted_retries_mentions_broken_extension(tmp_path,
                                                             monkeypatch):
    monkeypatch.setattr(wheel, "release_editable_install_locks",
                        lambda repo, **k: [])

    def run(cmd, **kw):
        if cmd[0] == "python3" and "import importlib" in cmd[2]:
            return 1, "", "Duplicate registration of op"
        if cmd[0] == "python3":
            return 0, "", ""
        return 0, "", ""
    with pytest.raises(WheelInstallError, match="broken compiled extension"):
        wheel.ensure_wheel_installed(
            tmp_path, "c" * 40, SPEC, python="python3",
            install_log=tmp_path / "i.log",
            import_check_log=tmp_path / "c.log", run=run)


# -- wheel: Dockerfile pin -----------------------------------------------------

PIN = PinSpec(dockerfile="docker/Dockerfile.ci",
              url_pattern=r"wheels\.example\.ai/[0-9a-f]{40}",
              url_template="wheels.example.ai/{commit}",
              commit_env_var="PRECOMPILED_WHEEL_COMMIT")


def _dockerfile(tmp_path, content):
    p = tmp_path / "docker" / "Dockerfile.ci"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return p


def test_pin_dockerfile_all_three_forms(tmp_path):
    old, new = "0" * 40, "f" * 40
    p = _dockerfile(tmp_path, (
        f"FROM base\n"
        f"RUN pip install https://wheels.example.ai/{old}/x.whl\n"
        f"  ENV PRECOMPILED_WHEEL_COMMIT={old}\n"
        f"ARG PRECOMPILED_WHEEL_COMMIT={old}\n"
        f"ENV OTHER=keepme\n"))
    assert wheel.pin_dockerfile(tmp_path, new, PIN) is True
    text = p.read_text()
    assert f"https://wheels.example.ai/{new}/x.whl" in text
    # the ENV line's leading indentation is normalized away (sed parity)
    assert f"\nENV PRECOMPILED_WHEEL_COMMIT={new}\n" in text
    assert f"\nARG PRECOMPILED_WHEEL_COMMIT={new}\n" in text
    assert old not in text and "ENV OTHER=keepme" in text
    # idempotent: second call is a no-op
    assert wheel.pin_dockerfile(tmp_path, new, PIN) is False


def test_pin_dockerfile_current_form_never_shields_stale_sibling(tmp_path):
    """One already-current pin form must not skip the rewrite of a stale
    sibling (the shell's seds are unconditional)."""
    old, new = "0" * 40, "f" * 40
    p = _dockerfile(tmp_path, (
        f"RUN pip install https://wheels.example.ai/{new}/x.whl\n"
        f"ENV PRECOMPILED_WHEEL_COMMIT={old}\n"))
    assert wheel.pin_dockerfile(tmp_path, new, PIN) is True
    text = p.read_text()
    assert f"ENV PRECOMPILED_WHEEL_COMMIT={new}" in text and old not in text


def test_pin_dockerfile_failure_modes(tmp_path):
    with pytest.raises(wheel.PinError, match="not found"):
        wheel.pin_dockerfile(tmp_path, "f" * 40, PIN)
    _dockerfile(tmp_path, "FROM base\nRUN echo no-pin-here\n")
    with pytest.raises(wheel.PinError, match="failed to update"):
        wheel.pin_dockerfile(tmp_path, "f" * 40, PIN)


# -- worktree ------------------------------------------------------------------

def _conflicted_merge(repo: Path) -> None:
    _commit(repo, {"f.txt": "base"}, "base")
    _git(repo, "checkout", "-q", "-b", "side")
    _commit(repo, {"f.txt": "side"}, "side edit")
    _git(repo, "checkout", "-q", "main")
    _commit(repo, {"f.txt": "main"}, "main edit")
    r = subprocess.run(["git", "merge", "side"], cwd=str(repo),
                       capture_output=True, text=True)
    assert r.returncode != 0  # conflict is the fixture's point


def test_abort_stale_merge_state(tmp_path):
    repo = _make_repo(tmp_path / "r")
    _conflicted_merge(repo)
    assert worktree.porcelain(repo)             # UU entry
    aborted = worktree.abort_stale_inflight_state(repo)
    assert aborted == ["merge"]
    assert worktree.porcelain(repo) == ""
    assert worktree.abort_stale_inflight_state(repo) == []   # idempotent


def test_discard_untracked_matching_touches_only_matches(tmp_path):
    repo = _make_repo(tmp_path / "r")
    _commit(repo, {"tracked.py": "x"}, "init")
    (repo / "tests/e2e/stage_configs").mkdir(parents=True)
    (repo / "tests/e2e/stage_configs/cfg_123456.yaml").write_text("a")
    (repo / "tests/e2e/stage_configs/keep.yaml").write_text("b")
    (repo / "tracked.py").write_text("modified")
    removed = worktree.discard_untracked_matching(
        repo, [r"^tests/e2e/stage_configs/.*_[0-9]{6,}\.yaml$"])
    assert removed == ["tests/e2e/stage_configs/cfg_123456.yaml"]
    assert not (repo / "tests/e2e/stage_configs/cfg_123456.yaml").exists()
    assert (repo / "tests/e2e/stage_configs/keep.yaml").exists()
    assert (repo / "tracked.py").read_text() == "modified"   # never touched


def test_apply_dirty_worktree_decision(tmp_path):
    up = _make_repo(tmp_path / "up")
    tg = _make_repo(tmp_path / "tg")
    _commit(up, {"a.py": "1"}, "init")
    _commit(tg, {"b.py": "1"}, "init")
    (tg / "b.py").write_text("dirty")
    (tg / "junk.txt").write_text("junk")
    (up / "new.py").write_text("keep me")
    decision = {
        "vllm": {"discard": [],
                 "commit": {"message": "keep new file", "paths": ["new.py"]}},
        "omni": {"discard": ["b.py", "junk.txt"], "commit": None},
    }
    worktree.apply_dirty_worktree_decision(
        decision, {"vllm": up, "omni": tg},
        author_name="Fixture Bot", author_email="bot@example.com")
    assert worktree.porcelain(up) == "" and worktree.porcelain(tg) == ""
    show = _git(up, "log", "-1", "--format=%an <%ae>%n%B")
    assert "Fixture Bot <bot@example.com>" in show
    assert "Signed-off-by: Fixture Bot <bot@example.com>" in show
    assert (tg / "b.py").read_text() == "1"

    with pytest.raises(worktree.DecisionError, match="escapes repo|'..'|not allowed"):
        worktree.apply_dirty_worktree_decision(
            {"vllm": {"discard": ["../evil"]}, "omni": {"discard": []}},
            {"vllm": up, "omni": tg},
            author_name="x", author_email="y@z")
    with pytest.raises(worktree.DecisionError, match="missing or invalid"):
        worktree.apply_dirty_worktree_decision(
            {"vllm": {"discard": []}}, {"vllm": up, "omni": tg},
            author_name="x", author_email="y@z")


def test_decision_paths_are_literal_never_globs(tmp_path):
    """A decision naming `*.py` must touch only a file literally named
    `*.py` — pathspec expansion would discard/commit far more than the
    agent said."""
    up = _make_repo(tmp_path / "up")
    tg = _make_repo(tmp_path / "tg")
    _commit(up, {"a.py": "1"}, "init")
    _commit(tg, {"victim.py": "1"}, "init")
    (tg / "victim.py").write_text("dirty")       # must survive
    (tg / "*.py").write_text("glob-named junk")  # untracked, literal name
    (up / "keep me.py").write_text("new")
    (up / "x.py").write_text("must not be committed")
    decision = {
        "vllm": {"discard": [],
                 "commit": {"message": "one literal file",
                            "paths": ["keep me.py"]}},
        "omni": {"discard": ["*.py"], "commit": None},
    }
    worktree.apply_dirty_worktree_decision(
        decision, {"vllm": up, "omni": tg},
        author_name="Bot", author_email="b@e.c")
    assert not (tg / "*.py").exists()                     # the literal file
    assert (tg / "victim.py").read_text() == "dirty"      # glob did NOT expand
    committed = [ln for ln in _git(up, "show", "--name-only", "--format=",
                                   "HEAD").splitlines() if ln.strip()]
    assert committed == ["keep me.py"]                    # x.py not swept in
    assert (up / "x.py").exists()


def test_release_editable_install_locks_scoped_to_repo(tmp_path):
    """Only stale installs whose cwd is inside THIS repo are killed — an
    active install in an unrelated checkout must be untouched."""
    repo = tmp_path / "repo"
    (repo / "sub").mkdir(parents=True)
    other = tmp_path / "other"
    other.mkdir()
    cwds = {101: repo / "sub", 102: other, 103: None}
    killed = []
    got = wheel.release_editable_install_locks(
        repo, pgrep=lambda args: [101, 102, 103],
        proc_cwd=lambda pid: cwds[pid],
        kill=lambda pids: killed.extend(pids) or [])
    assert got == [101] and killed == [101]


def test_load_decision_json_tolerates_chatter(tmp_path):
    p = tmp_path / "d.json"
    p.write_text('I decided the following:\n{"vllm": {"discard": []}}\n')
    assert worktree.load_decision_json(p) == {"vllm": {"discard": []}}
    p.write_text("no json here")
    with pytest.raises(worktree.DecisionError):
        worktree.load_decision_json(p)


def test_guard_clean_rebase_step_and_readonly_split(settings, trace, tmp_path):
    """The mutating passes live in `workspace.guard_clean_rebase` with risk
    `write_workspace`; plain `workspace.guard_clean` stays read-only and its
    dirty verdict is byte-identical to the old behavior — even when handed
    the rebase step's params."""
    registry = register_builtin_steps(StepRegistry())
    guard = registry.get("workspace.guard_clean")
    rebase_guard = registry.get("workspace.guard_clean_rebase")
    assert guard.risk == "read"
    assert rebase_guard.risk == "write_workspace"
    repo = _make_repo(tmp_path / "r")
    _conflicted_merge(repo)

    params = {"abort_stale_state": True,
              "discard_untracked_patterns":
                  [r"^tests/e2e/stage_configs/.*_[0-9]{6,}\.yaml$"]}
    ctx = StepContext(settings=settings, state={"repo_path": str(repo)},
                      params=params, run_dir=tmp_path, trace=trace)
    result = asyncio.run(guard.handler(ctx))
    assert not result.ok and result.failure is FailureKind.BLOCKED
    assert worktree.porcelain(repo)      # read-only guard mutated nothing

    result = asyncio.run(rebase_guard.handler(ctx))
    assert result.ok and "aborted stale in-flight state" in result.summary


# -- assign --------------------------------------------------------------------

MODULE_PATHS = {"model_config": ["vllm/config/"],
                "worker_runner": ["vllm/v1/worker/"],
                "benchmarks": ["vllm/benchmarks/"]}


def test_assign_commits_by_path(upstream_pair):
    _, clone, shas = upstream_pair
    a = assign.assign_commits(clone, shas[0], MODULE_PATHS,
                              target_branch="main",
                              base_class_watch_paths=["vllm/config/x.py"])
    assert a.total_commits == 3          # c2..c4
    assert a.counts == {"model_config": 1, "worker_runner": 1, "benchmarks": 0}
    assert a.skip == {"model_config": False, "worker_runner": False,
                      "benchmarks": True}
    assert len(a.base_class_commits) == 1 and "c3" in a.base_class_commits[0]
    assert a.missing_paths == [("benchmarks", "vllm/benchmarks/")]


def test_assign_unusable_range_fails_loudly(upstream_pair, tmp_path):
    """A bad baseline must raise, not classify zero commits everywhere and
    silently skip the whole rebase (shell `set -e` parity)."""
    _, clone, _ = upstream_pair
    with pytest.raises(assign.AssignError, match="unusable|bad baseline"):
        assign.assign_commits(clone, "0" * 40, MODULE_PATHS)
    not_a_repo = tmp_path / "empty"
    not_a_repo.mkdir()
    with pytest.raises(assign.AssignError):
        assign.assign_commits(not_a_repo, "HEAD~1", MODULE_PATHS)


def test_assignment_report_structure(upstream_pair):
    _, clone, shas = upstream_pair
    a = assign.assign_commits(clone, shas[0], MODULE_PATHS, target_branch="main")
    md = assign.render_assignment_report(a, repo_label="vLLM",
                                         path_sync_report="### snapshot")
    assert md.startswith("# vLLM Commits Assignment Report")
    assert f"- Last rebase commit: `{shas[0]}`" in md
    assert "- **WARNING**: 1 path mapping(s) missing" in md
    assert "## model_config (1 commits)" in md
    assert "## benchmarks (0 commits)" in md and "(no relevant commits)" in md
    assert "## Base Class Inheritance Changes" in md and "(none)" in md
    assert "### snapshot" in md
    drift = assign.render_drift_report(a.head[:12], a.missing_paths)
    assert "- **MISSING**: `vllm/benchmarks/` (module: benchmarks)" in drift
    assert "All paths valid." in assign.render_drift_report("abc", [])


# -- path_sync -----------------------------------------------------------------

def test_sync_path_map_filters_and_merges_overlays(tmp_path):
    for rel in ("a/keep.py", "b/curated.py"):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x")
    current = {"m1": ["a/keep.py", "a/gone.py"], "m2": ["missing/everything.py"]}
    curated = {"m1": CuratedEntry(candidates=("b/curated.py", "b/gone.py"),
                                  fallback="b/curated.py")}
    out = path_sync.sync_path_map(tmp_path, current, curated)
    # curated coverage MERGES with surviving current entries — it never
    # replaces them (coarse scoping prefixes must survive a sync)
    assert out["m1"] == ["a/keep.py", "b/curated.py"]
    assert out["m2"] == ["missing/everything.py"]     # fallback = first entry
    with pytest.raises(PathSyncError, match="unknown module"):
        path_sync.sync_path_map(tmp_path, current,
                                {"nope": CuratedEntry(("x",), "x")})


def test_sync_with_real_manifest_overlays_preserves_coarse_prefixes(tmp_path):
    """Apply the ACTUAL configured curated overlays from the adapter manifest
    against a fixture tree: the coarse prefixes (vllm_omni/outputs/,
    vllm_omni/entrypoints/) must survive the first sync — losing them would
    silently narrow review/rebase scope."""
    import yaml as _yaml
    manifest = _yaml.safe_load(
        (REPO_ROOT / "adapters/vllm_omni/manifest.yaml").read_text())
    curated_cfg = manifest["rebase"]["path_sync"]["curated"]["local_paths"]
    curated = {k: CuratedEntry.from_data(v) for k, v in curated_cfg.items()}
    current = {m: list(spec["local_paths"])
               for m, spec in manifest["modules"].items()}
    # fixture tree: every current dir prefix + a subset of curated candidates
    for rel in ("vllm_omni/inputs/data.py", "vllm_omni/outputs/x.py",
                "vllm_omni/entrypoints/omni.py",
                "vllm_omni/entrypoints/openai/api_server.py",
                "vllm_omni/engine/async_omni_engine.py", "vllm_omni/request.py"):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x")
    out = path_sync.sync_path_map(tmp_path, current, curated)
    assert "vllm_omni/outputs/" in out["input_output"]
    assert "vllm_omni/inputs/" in out["input_output"]
    assert "vllm_omni/entrypoints/" in out["online_serving"]
    assert "vllm_omni/entrypoints/openai/api_server.py" in out["online_serving"]


def test_apply_decision_validation(tmp_path):
    (tmp_path / "ok.py").write_text("x")
    current = {"m1": ["old.py"], "m2": ["keep.py"]}
    out = path_sync.apply_decision(tmp_path, current,
                                   {"m1": "ok.py"})       # space-joined form
    assert out == {"m1": ["ok.py"], "m2": ["keep.py"]}    # omitted key kept
    with pytest.raises(PathSyncError, match="non-existent path"):
        path_sync.apply_decision(tmp_path, current, {"m1": ["nope.py"]})
    with pytest.raises(PathSyncError, match="missing or empty"):
        path_sync.apply_decision(tmp_path, current, {"m1": []})
    # a typo'd module key must fail loudly, not silently apply nothing
    with pytest.raises(PathSyncError, match="unknown module key"):
        path_sync.apply_decision(tmp_path, current, {"m1_typo": "ok.py"})


def test_rewrite_manifest_modules_surgical(tmp_path):
    src = REPO_ROOT / "adapters" / "vllm_omni" / "manifest.yaml"
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(src.read_text())
    before = manifest.read_text()

    changed = path_sync.rewrite_manifest_modules(
        manifest, {"input_output": {"local_paths": ["vllm_omni/inputs/data.py"],
                                    "test_paths": ["tests/test_outputs.py"]}})
    assert changed is True
    after = manifest.read_text()
    import yaml as _yaml
    data = _yaml.safe_load(after)
    mod = data["modules"]["input_output"]
    assert mod["local_paths"] == ["vllm_omni/inputs/data.py"]
    assert mod["test_paths"] == ["tests/test_outputs.py"]
    assert mod["wave"] == 1                       # scalars survive
    # every byte OUTSIDE the modules section is untouched
    pre_before, _, tail_before = before.partition("\nmodules:")
    pre_after, _, tail_after = after.partition("\nmodules:")
    assert pre_before == pre_after
    nxt = re.search(r"\n(?=# Phase-1 rebase machinery data)", before)
    assert before[nxt.start():] == after[after.index("\n# Phase-1 rebase machinery data"):]
    # unknown module / non-path field refuse loudly
    with pytest.raises(PathSyncError, match="unknown module"):
        path_sync.rewrite_manifest_modules(manifest, {"zzz": {"local_paths": []}})
    with pytest.raises(PathSyncError, match="non-path field"):
        path_sync.rewrite_manifest_modules(manifest, {"platform": {"wave": [2]}})


def test_manifest_local_paths_cover_parent_module_map():
    """Every entry of the parent orchestrator's MODULE_OMNI_FILES must be
    covered by a local_paths prefix of the same module — module rebases scope
    their work by local_paths, and an uncovered file silently falls out of
    its module's rebase."""
    import yaml as _yaml
    manifest = _yaml.safe_load(
        (REPO_ROOT / "adapters/vllm_omni/manifest.yaml").read_text())
    parent_map = {  # config.sh MODULE_OMNI_FILES, verbatim
        "model_config": ["vllm_omni/config/model.py", "vllm_omni/engine/arg_utils.py"],
        "input_output": ["vllm_omni/inputs/data.py", "vllm_omni/inputs/preprocess.py",
                         "vllm_omni/engine/async_omni_engine.py",
                         "vllm_omni/engine/orchestrator.py",
                         "vllm_omni/engine/serialization.py",
                         "vllm_omni/engine/stage_init_utils.py",
                         "vllm_omni/engine/stage_engine_core_client.py",
                         "vllm_omni/engine/output_processor.py", "vllm_omni/request.py"],
        "scheduler": ["vllm_omni/core/sched/omni_ar_scheduler.py",
                      "vllm_omni/core/sched/omni_generation_scheduler.py",
                      "vllm_omni/core/sched/output.py"],
        "worker_runner": ["vllm_omni/worker/gpu_model_runner.py",
                          "vllm_omni/worker/gpu_ar_model_runner.py",
                          "vllm_omni/worker/gpu_generation_model_runner.py",
                          "vllm_omni/worker/gpu_ar_worker.py"],
        "model_executor": ["vllm_omni/model_executor/"],
        "online_serving": ["vllm_omni/entrypoints/omni_base.py",
                           "vllm_omni/entrypoints/omni.py",
                           "vllm_omni/entrypoints/async_omni.py",
                           "vllm_omni/entrypoints/openai/api_server.py",
                           "vllm_omni/entrypoints/openai/serving_chat.py",
                           "vllm_omni/entrypoints/openai/serving_speech.py",
                           "vllm_omni/entrypoints/openai/utils.py"],
        "benchmarks": ["vllm_omni/benchmarks/serve.py",
                       "vllm_omni/benchmarks/patch/patch.py",
                       "vllm_omni/benchmarks/metrics/metrics.py",
                       "vllm_omni/entrypoints/cli/benchmark/serve.py"],
        "platform": ["vllm_omni/platforms/cuda/platform.py",
                     "vllm_omni/platforms/rocm/platform.py",
                     "vllm_omni/platforms/xpu/platform.py",
                     "vllm_omni/platforms/interface.py"],
    }
    for module, parent_entries in parent_map.items():
        local = manifest["modules"][module]["local_paths"]
        for entry in parent_entries:
            assert any(entry == p or entry.startswith(p.rstrip("/") + "/")
                       or entry == p.rstrip("/")
                       for p in local), (
                f"{module}: parent entry {entry} uncovered by local_paths {local}")


# -- api drift guard (adapter script) helpers ---------------------------------

@pytest.fixture()
def drift_guard(monkeypatch):
    import importlib.util
    import sys
    # the script chdirs to OMNI_PATH at import when set — not wanted in tests
    monkeypatch.delenv("OMNI_PATH", raising=False)
    path = REPO_ROOT / "adapters" / "vllm_omni" / "rebase" / "api_drift_guard.py"
    spec = importlib.util.spec_from_file_location("_drift_guard_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    meta_before = list(sys.meta_path)
    spec.loader.exec_module(mod)
    yield mod
    sys.meta_path[:] = meta_before   # drop the flash-attn import blocker


def test_drift_guard_removed_base_method_calls(drift_guard):
    class Base:
        def kept(self):
            return 1

    class Sub(Base):
        def __init__(self):
            self.attr_set = 1

        def caller(self):
            self.kept()
            self.attr_set
            return self.gone_method()   # base removed/renamed this

    bad = drift_guard.removed_base_method_calls(Sub)
    assert [name for name, _ in bad] == ["gone_method"]


def test_drift_guard_self_assigned_attrs(drift_guard):
    class C:
        def __init__(self):
            self.direct = 1
            setattr(self, "via_setattr", 2)

    names = drift_guard._self_assigned_attrs(C)
    assert {"direct", "via_setattr"} <= names


def test_drift_guard_forbidden_test_imports(drift_guard, tmp_path, monkeypatch):
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "t_bad.py").write_text(
        "from vllm.utils.torch_utils import cuda_device_count_stateless\n")
    (tests / "t_star.py").write_text("from vllm.utils.torch_utils import *\n")
    (tests / "t_ok.py").write_text("from vllm.utils.torch_utils import safe\n")
    monkeypatch.chdir(tmp_path)
    findings = drift_guard._forbidden_test_imports()
    assert len(findings) == 2
    assert any("cuda_device_count_stateless" in f for f in findings)
    assert any("wildcard import" in f for f in findings)


# -- partial e2e ---------------------------------------------------------------

def test_phase1_partial_e2e(settings, trace, tmp_path, monkeypatch):
    """Chain the phase-1 cluster over fixture repos exactly as the pipeline
    will drive it: guard (stale merge + artifact discard) → wheel pick →
    Dockerfile pin → commit assignment → path sync into a manifest copy."""
    # target repo: conflicted merge leftover + pytest artifact + Dockerfile
    target = _make_repo(tmp_path / "target")
    old_pin = "0" * 40
    _commit(target, {
        "docker/Dockerfile.ci": f"FROM base\nENV PRECOMPILED_WHEEL_COMMIT={old_pin}\n",
        "vllm_omni/inputs/data.py": "x",
        "tests/test_outputs.py": "x",
    }, "target init")
    _conflicted_merge(target)
    (target / "tests/e2e/stage_configs").mkdir(parents=True)
    (target / "tests/e2e/stage_configs/cfg_999999.yaml").write_text("junk")

    # 1. guard: aborts the stale merge, discards the artifact, ends clean
    registry = register_builtin_steps(StepRegistry())
    guard = registry.get("workspace.guard_clean_rebase")
    ctx = StepContext(
        settings=settings, state={"repo_path": str(target)},
        params={"abort_stale_state": True,
                "discard_untracked_patterns":
                    [r"^tests/e2e/stage_configs/.*_[0-9]{6,}\.yaml$"]},
        run_dir=tmp_path, trace=trace)
    result = asyncio.run(guard.handler(ctx))
    assert result.ok, result.summary
    assert worktree.porcelain(target) == ""

    # 2. upstream: pick the newest commit with a wheel (fixture: c3)
    src = _make_repo(tmp_path / "up-src")
    c1 = _commit(src, {"vllm/config/x.py": "1"}, "c1")
    c2 = _commit(src, {"vllm/v1/worker/y.py": "1"}, "c2")
    c3 = _commit(src, {"vllm/config/x.py": "2"}, "c3")
    c4 = _commit(src, {"README.md": "r"}, "c4")
    up = tmp_path / "up"
    subprocess.run(["git", "clone", "-q", str(src), str(up)], check=True)
    found = wheel.pick_wheel_commit(up, "main", SPEC,
                                    probe=lambda r: r in (c1, c3), baseline=c1)
    assert found == c3
    assert _git(up, "rev-parse", "HEAD") == c3

    # 3. pin the target's CI Dockerfile to the picked commit
    assert wheel.pin_dockerfile(target, found, PIN) is True
    assert f"ENV PRECOMPILED_WHEEL_COMMIT={found}" in (
        target / "docker/Dockerfile.ci").read_text()

    # 4. assign upstream commits to modules against the baseline
    a = assign.assign_commits(up, c1, MODULE_PATHS, target_branch="main")
    assert a.counts["model_config"] == 1 and a.counts["worker_runner"] == 1
    assert a.skip["benchmarks"] is True
    report = assign.render_assignment_report(a, repo_label="Upstream")
    assert "## model_config (1 commits)" in report

    # 5. path sync: retarget a manifest copy against the target tree
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        (REPO_ROOT / "adapters/vllm_omni/manifest.yaml").read_text())
    synced = path_sync.sync_path_map(
        target,
        {"input_output": ["vllm_omni/inputs/data.py", "vllm_omni/gone.py"]},
        None)
    assert synced["input_output"] == ["vllm_omni/inputs/data.py"]
    assert path_sync.rewrite_manifest_modules(
        manifest, {"input_output": {"local_paths": synced["input_output"]}})
    import yaml as _yaml
    assert _yaml.safe_load(manifest.read_text())["modules"]["input_output"][
        "local_paths"] == ["vllm_omni/inputs/data.py"]
