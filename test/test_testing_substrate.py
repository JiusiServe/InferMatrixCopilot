"""PR1 guardrails: the testing substrate (gpu_lock, process_tree, watchdog,
watchdog_learn, env_plan, runner) ported from the rebase agent's shell layer.
Everything runs offline via injected collaborators."""

import os
import signal
import time
from pathlib import Path

import pytest

from infermatrix_copilot.testing import env_plan, process_tree, watchdog_learn
from infermatrix_copilot.testing.gpu_lock import (
    GpuLock, cleanup_orphan_gpu_procs, wait_gpu_memory_idle)
from infermatrix_copilot.testing.runner import (
    PY_TIMEOUT_MARGIN_SEC, TIMEOUT_RC, TestJob, TestRunner,
    append_silent_log_footer, backup_prev_log, strip_cov_flags)
from infermatrix_copilot.testing.watchdog import LogWatchdog, WatchdogPatterns

PATTERNS_YAML = (Path(__file__).resolve().parent.parent
                 / "adapters" / "vllm_omni" / "testing"
                 / "watchdog_patterns.yaml")


@pytest.fixture()
def patterns() -> WatchdogPatterns:
    return WatchdogPatterns.from_yaml(PATTERNS_YAML)


# -- watchdog pattern translation (bash ERE -> re) -----------------------------

def test_tier1_positive_and_negative(patterns):
    assert patterns.last_match(["torch.cuda.OutOfMemoryError: boom"], "critical")
    assert patterns.last_match(["  Killed  "], "critical")  # bare OOM Killed
    # benign teardown line must NOT match the whole-line Killed pattern
    assert patterns.last_match(
        ["WARNING StageDiffusionProc was killed by signal 15"],
        "critical") is None
    assert patterns.last_match(["all good here"], "critical") is None


def test_tier1_case_insensitive_like_grep_i(patterns):
    assert patterns.last_match(["fatal: something broke"], "critical")


def test_simulation_allowlist_suppresses_kills(patterns):
    line = "raised EngineDeadError (simulated)"  # allowlisted substring
    assert patterns.is_simulated(line)
    # non_fatal test names match Tier-1 FATAL case-insensitively — allowlisted
    assert patterns.is_simulated(
        "tests/x.py::test_non_fatal_client_error_preserves_non_400_status")
    # error-passthrough test NAMES are simulated even when the line is not
    assert patterns.is_simulated("ordinary line", "test_dead_engine_recovers")


def test_noise_is_case_sensitive_and_stripped(patterns):
    noisy = "PytestUnknownMarkWarning: unknown mark"
    assert patterns.is_noise(noisy)
    assert not patterns.is_noise("pytestunknownmarkwarning lowercased")
    kept = patterns.strip_noise([noisy, "RuntimeError: real"])
    assert kept == ["RuntimeError: real"]


def test_last_match_is_last_line(patterns):
    lines = ["ValueError: first", "middle", "RuntimeError: second"]
    assert patterns.last_match(lines, "review") == "RuntimeError: second"


# -- watchdog behavior ---------------------------------------------------------

def _wd(tmp_path, patterns, *, review=None, test_name="tests/x.py"):
    log = tmp_path / "t.log"
    log.write_text("")
    kills, records = [], []
    wd = LogWatchdog(patterns, log, pid=99999, test_name=test_name,
                     review_fn=review,
                     kill_fn=lambda pid: kills.append(pid),
                     record_fn=lambda p, v, t: records.append((p, v)),
                     pid_alive=lambda pid: True)
    return wd, log, kills, records


def test_tier1_kills_and_marks_log(tmp_path, patterns):
    wd, log, kills, _ = _wd(tmp_path, patterns)
    log.write_text("something\nCUDA out of memory\n")
    assert wd.check_once() is True
    assert kills == [99999]
    assert wd.result.tier == 1
    assert "[watchdog/kill] tier=1" in log.read_text()


def test_tier2_kill_needs_reviewer_confirmation(tmp_path, patterns):
    wd, log, kills, records = _wd(tmp_path, patterns,
                                  review=lambda t, s: "verdict: KILL")
    log.write_text("RuntimeError: engine wedged\n")
    assert wd.check_once() is True
    assert kills == [99999] and wd.result.tier == 2
    assert records == [("RuntimeError: engine wedged", "KILL")]


def test_tier2_defaults_to_continue_on_garbage_or_exception(tmp_path, patterns):
    for review in (lambda t, s: "no verdict here",
                   lambda t, s: (_ for _ in ()).throw(TimeoutError())):
        wd, log, kills, records = _wd(tmp_path, patterns, review=review)
        log.write_text("RuntimeError: maybe fine\n")
        assert wd.check_once() is False
        assert kills == []
        assert records[-1][1] == "CONTINUE"


def test_tier2_without_reviewer_never_kills(tmp_path, patterns):
    wd, log, kills, _ = _wd(tmp_path, patterns, review=None)
    log.write_text("RuntimeError: whatever\n")
    assert wd.check_once() is False and kills == []


def test_size_delta_gate_skips_unchanged_log(tmp_path, patterns):
    calls = []
    wd, log, _, _ = _wd(tmp_path, patterns,
                        review=lambda t, s: calls.append(1) or "CONTINUE")
    log.write_text("RuntimeError: x\n")
    wd.check_once()
    wd.check_once()  # unchanged size: no second review
    assert len(calls) == 1


def test_noise_never_reaches_the_reviewer(tmp_path, patterns):
    calls = []
    wd, log, _, _ = _wd(tmp_path, patterns,
                        review=lambda t, s: calls.append(1) or "CONTINUE")
    log.write_text("DeprecationWarning: Error: not really\n")
    assert wd.check_once() is False and calls == []


# -- watchdog_learn ------------------------------------------------------------

def test_learn_promotion_rules(tmp_path):
    logf = tmp_path / "decisions.jsonl"
    import json
    rows = []
    # qualifies: 3 CONTINUEs spanning 6 days
    for day in (1, 4, 7):
        rows.append({"ts": f"2026-07-0{day} 10:00:00",
                     "pattern": "loky KeyError teardown", "verdict": "CONTINUE"})
    # disqualified: one KILL
    for day in (1, 7):
        rows.append({"ts": f"2026-07-0{day} 10:00:00",
                     "pattern": "engine dead maybe", "verdict": "CONTINUE"})
    rows.append({"ts": "2026-07-08 10:00:00",
                 "pattern": "engine dead maybe", "verdict": "KILL"})
    # disqualified: same-day burst
    for h in (1, 2, 3):
        rows.append({"ts": f"2026-07-01 0{h}:00:00",
                     "pattern": "burst warning", "verdict": "CONTINUE"})
    logf.write_text("\n".join(json.dumps(r) for r in rows))

    got = watchdog_learn.eligible_patterns(
        watchdog_learn.read_decisions(logf), existing=set())
    assert got == ["loky KeyError teardown"]
    # already covered by seed (substring either direction) -> not promoted
    assert watchdog_learn.eligible_patterns(
        watchdog_learn.read_decisions(logf),
        existing={"KeyError teardown"}) == []


def test_learn_promote_appends_escaped_to_overlay(tmp_path):
    import json

    import yaml
    logf = tmp_path / "d.jsonl"
    logf.write_text("\n".join(json.dumps(
        {"ts": f"2026-07-0{d} 10:00:00", "pattern": "odd (x) warning",
         "verdict": "CONTINUE"}) for d in (1, 7, 9)))
    overlay = tmp_path / "overlay.yaml"
    new = watchdog_learn.promote(logf, overlay, seed_noise=["UserWarning"])
    assert new == ["odd (x) warning"]
    doc = yaml.safe_load(overlay.read_text())
    assert doc["noise"] == [r"odd\ \(x\)\ warning"] or doc["noise"] == [
        "odd\\ \\(x\\)\\ warning"]
    # overlay feeds back into pattern loading
    p = WatchdogPatterns.from_yaml(PATTERNS_YAML, overlay=overlay)
    assert p.is_noise("odd (x) warning")


def test_learn_promote_is_idempotent(tmp_path):
    import json
    logf = tmp_path / "d.jsonl"
    logf.write_text("\n".join(json.dumps(
        {"ts": f"2026-07-0{d} 10:00:00", "pattern": "odd (y) warning",
         "verdict": "CONTINUE"}) for d in (1, 7, 9)))
    overlay = tmp_path / "overlay.yaml"
    assert watchdog_learn.promote(logf, overlay, seed_noise=[]) == \
        ["odd (y) warning"]
    before = overlay.read_text()
    assert watchdog_learn.promote(logf, overlay, seed_noise=[]) == []
    assert overlay.read_text() == before  # second call appends nothing


def test_learn_record_normalizes_pid_prefix(tmp_path):
    logf = tmp_path / "d.jsonl"
    watchdog_learn.record(logf, pattern="(StageEngineCoreProc pid=123) boom",
                          verdict="continue")
    row = watchdog_learn.read_decisions(logf)[0]
    assert row["pattern"] == "boom" and row["verdict"] == "CONTINUE"


# -- env_plan ------------------------------------------------------------------

def test_env_overlay_order_and_no_mutation(tmp_path):
    before = dict(os.environ)
    env = env_plan.build_subprocess_env(
        venv=tmp_path / "v", cuda_visible_devices="0,1", hf_home="/hf",
        pythonpath_prepend="/wt", job_env={"CUDA_VISIBLE_DEVICES": "2"})
    assert env["CUDA_VISIBLE_DEVICES"] == "2"  # per-job pair wins
    assert env["VIRTUAL_ENV"] == str(tmp_path / "v")
    assert env["PATH"].startswith(str(tmp_path / "v" / "bin"))
    assert env["PYTHONPATH"].split(os.pathsep)[0] == "/wt"
    assert dict(os.environ) == before  # our own env never mutated


def test_agent_shell_scrub():
    env = {"ANTHROPIC_API_KEY": "k", "GITHUB_TOKEN": "t", "HF_TOKEN": "h",
           "PATH": "/bin", "OPENAI_API_KEY": "o", "GIT_ASKPASS": "a"}
    out = env_plan.scrub_agent_shell_env(env)
    assert set(out) == {"HF_TOKEN", "PATH"}
    assert "HF_TOKEN" not in env_plan.scrub_agent_shell_env(
        env, keep_hf_token=False)
    assert env["ANTHROPIC_API_KEY"] == "k"  # pure function


# -- gpu_lock ------------------------------------------------------------------

def test_gpu_lock_protocol_and_dead_owner_steal(tmp_path):
    d = tmp_path / "gpu_lock"
    lock = GpuLock(d, poll_sec=0.01, timeout_sec=5).acquire()
    assert (d / "lock").read_text() == str(os.getpid())
    lock.release()
    assert not (d / "lock").exists()
    # dead-owner steal: plant a lock held by a pid that cannot exist
    d.mkdir(exist_ok=True)
    (d / "lock").write_text("999999")
    (d / "owner").write_text("999999")
    GpuLock(d, poll_sec=0.01, timeout_sec=5).acquire().release()


def test_gpu_cleanup_parses_pmon_pid_column_never_kills_zero():
    """pmon rows are `<gpu> <pid> <type> ...`; the shell awk'd field 1 (the
    gpu index) — on GPU 0 that meant `kill 0`, signalling its own process
    group. The port must take field 2 and refuse non-positive pids."""
    pmon = ("# gpu   pid  type  sm  mem  enc  dec  command\n"
            "# Idx     #   C/G   %    %    %    %  name\n"
            "    0  7777     C  42   10    0    0  python\n")
    outs = iter(["", pmon, "", pmon])  # compute-apps empty; pmon has the row
    kills = []
    cleanup_orphan_gpu_procs("0", run=lambda cmd: next(outs, ""),
                             kill=lambda pid, sig: kills.append((pid, sig)),
                             sleep=lambda s: None)
    assert (7777, 15) in kills
    assert all(pid > 0 for pid, _ in kills)  # never 0, never the gpu index


def test_gpu_cleanup_excludes_own_tree_and_escalates():
    kills = []
    outs = iter([
        "4242\n", "",          # first pass: compute-apps, pmon
        "4242\n", "",          # second pass (post-TERM survivors)
    ])
    killed = cleanup_orphan_gpu_procs(
        "0", run=lambda cmd: next(outs, ""),
        kill=lambda pid, sig: kills.append((pid, sig)),
        sleep=lambda s: None)
    assert killed == 1
    assert (4242, 15) in kills and (4242, 9) in kills
    assert all(pid != os.getpid() for pid, _ in kills)


def test_gpu_wait_memory_idle_parses_and_times_out():
    assert wait_gpu_memory_idle("0", run=lambda c: "500, 80000\n",
                                sleep=lambda s: None) is True
    assert wait_gpu_memory_idle("0", run=lambda c: "79000, 80000\n",
                                timeout_sec=0.1, poll_sec=0.05,
                                sleep=lambda s: None) is False


# -- process_tree --------------------------------------------------------------

def test_collect_descendants_bfs_dedup():
    children = {1: [2, 3], 2: [4], 3: [4], 4: []}
    assert process_tree.collect_descendants(
        1, children_of=lambda p: children.get(p, [])) == [1, 2, 3, 4]


def test_kill_tree_term_then_kill_survivors():
    events = []
    alive = {10: 2}  # survives one TERM round

    def kill(pid, sig):
        events.append((pid, sig))
        if sig == signal.SIGTERM and alive.get(pid):
            alive[pid] -= 1

    import infermatrix_copilot.testing.process_tree as pt
    orig = pt._alive
    pt._alive = lambda pid: alive.get(pid, 0) > 0
    try:
        survivors = process_tree.kill_tree(
            [10], kill=kill, sleep=lambda s: None)
    finally:
        pt._alive = orig
    assert (10, signal.SIGTERM) in events and (10, signal.SIGKILL) in events
    assert survivors == [10]  # our fake never really dies


# -- runner --------------------------------------------------------------------

@pytest.fixture()
def runner(tmp_path, patterns) -> TestRunner:
    (tmp_path / "repo").mkdir()
    return TestRunner(repo_root=tmp_path / "repo", tests_dir=tmp_path / "tests",
                      patterns=patterns, artifact_globs=["test_*.wav"],
                      cuda_visible_devices="", available_gpus=lambda: 0,
                      watchdog_interval=0.05)


def test_dry_run_returns_exact_plan(runner):
    job = TestJob(key="k", command="pytest tests/x", timeout_sec=60,
                  min_gpus=2, env={"A": "1"}, index=3)
    out = runner.run(job, {}, dry_run=True)
    assert out.plan.argv == ["bash", "-c", "set -e\npytest tests/x"]
    assert out.plan.env_overlay == {"A": "1"}
    assert out.plan.timeout_sec == 60 and out.plan.needs_gpu_lock
    assert out.plan.log_file.endswith("03_k.log")


def test_hw_gate_is_an_explicit_skip_not_a_pass(runner, tmp_path):
    job = TestJob(key="gpu8", command="echo hi", timeout_sec=5, min_gpus=8)
    out = runner.run(job, dict(os.environ))
    assert out.skipped and "8 GPU(s)" in out.skip_reason
    assert not (tmp_path / "tests" / ".passed_gpu8").exists()  # no false pass


def test_pass_marker_and_prev_backup(runner, tmp_path):
    job = TestJob(key="ok", command="echo one", timeout_sec=10, min_gpus=0,
                  index=1)
    out = runner.run(job, dict(os.environ))
    assert out.rc == 0
    assert (tmp_path / "tests" / ".passed_ok").exists()
    log = tmp_path / "tests" / "01_ok.log"
    first = log.read_text()
    runner.run(TestJob(key="ok", command="echo two", timeout_sec=10,
                       min_gpus=0, index=1), dict(os.environ))
    assert (tmp_path / "tests" / "01_ok.log.prev").read_text() == first


def test_baseline_suffix(runner, tmp_path):
    job = TestJob(key="b", command="echo x", timeout_sec=10, min_gpus=0, index=2)
    runner.run(job, dict(os.environ), baseline=True)
    assert (tmp_path / "tests" / "02_b_main_baseline.log").exists()
    assert (tmp_path / "tests" / ".passed_b_main_baseline").exists()


def test_silent_footer_variants(tmp_path):
    log = tmp_path / "a.log"
    log.write_text("no signal at all\n")
    append_silent_log_footer(log, 1)
    assert "SILENT EXIT" in log.read_text()
    log2 = tmp_path / "b.log"
    log2.write_text("ERROR: file or directory not found: tests/gone.py\n")
    append_silent_log_footer(log2, 4)
    text = log2.read_text()
    assert "COLLECTION/PATH ERROR" in text and "do NOT retry on GPU" in text
    log3 = tmp_path / "c.log"  # real pytest signal: footer must no-op
    log3.write_text("=== 1 failed in 2.2s ===\n")
    append_silent_log_footer(log3, 1)
    assert "postmortem" not in log3.read_text()


def test_cov_strip_sed_parity():
    cmd = ("pytest -q tests/x --cov=vllm_omni --cov-branch "
           "--cov-report=term-missing tests/y")
    assert strip_cov_flags(cmd) == "pytest -q tests/x tests/y"


def test_cov_fallback_retries_once(runner, tmp_path):
    probe = tmp_path / "repo" / "probe.sh"
    probe.write_text("#!/bin/bash\n"
                     'if [[ "$*" == *--cov* ]]; then\n'
                     '  echo "ERROR: unrecognized arguments: --cov=x"; exit 2\n'
                     "fi\necho fine\n")
    job = TestJob(key="cov", command="bash probe.sh --cov=x", timeout_sec=20,
                  min_gpus=0, index=4)
    out = runner.run(job, dict(os.environ))
    assert out.rc == 0
    assert "[coverage-fallback]" in (tmp_path / "tests" / "04_cov.log").read_text()


def test_timeout_kills_group_and_reports_124(runner):
    job = TestJob(key="slow", command="sleep 30", timeout_sec=0.3, min_gpus=0,
                  index=5)
    t0 = time.monotonic()
    out = runner.run(job, dict(os.environ))
    assert out.rc == TIMEOUT_RC and out.timed_out
    assert time.monotonic() - t0 < 90  # primary fired, not the safety timer


def test_watchdog_kill_during_run(runner, tmp_path):
    log = tmp_path / "tests" / "06_wd.log"
    job = TestJob(
        key="wd", timeout_sec=30, min_gpus=0, index=6,
        command=f"echo 'CUDA out of memory' >> {log}; sleep 30")
    out = runner.run(job, dict(os.environ))
    assert out.watchdog_triggered and out.rc != 0
    assert "[watchdog/kill] tier=1" in log.read_text()


def test_artifact_cleanup_depth_one_only(runner, tmp_path):
    repo = tmp_path / "repo"
    (repo / "test_deadbeef.wav").write_text("x")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_fixture.wav").write_text("keep")
    runner.run(TestJob(key="clean", command="true", timeout_sec=10,
                       min_gpus=0, index=7), dict(os.environ))
    assert not (repo / "test_deadbeef.wav").exists()
    assert (repo / "tests" / "test_fixture.wav").exists()  # never recursive


def test_timeout_layering_constants():
    # the safety margin is the load-bearing 900 s from phase3; the safety
    # timer fires strictly after the primary by construction (timeout + margin)
    assert PY_TIMEOUT_MARGIN_SEC == 900


def test_timeout_kills_own_pgroup_descendants(runner, tmp_path):
    """A spawn-mode child in its OWN process group must die too: killpg never
    reaches it, and the leader exiting must not end the escalation."""
    pidfile = tmp_path / "child.pid"
    job = TestJob(
        key="orphan", timeout_sec=0.5, min_gpus=0, index=8,
        command=(f"setsid bash -c 'echo $$ > {pidfile}; exec sleep 60' &\n"
                 f"sleep 60"))
    out = runner.run(job, dict(os.environ))
    assert out.timed_out
    deadline = time.monotonic() + 10
    child = int(pidfile.read_text().strip())
    while time.monotonic() < deadline:
        try:
            os.kill(child, 0)
        except ProcessLookupError:
            break
        time.sleep(0.1)
    else:
        os.kill(child, signal.SIGKILL)
        pytest.fail(f"own-pgroup descendant {child} survived the tree kill")


def test_cov_fallback_runs_under_the_gpu_lock(patterns, tmp_path):
    """Missing pytest-cov is exactly when the fallback does the real GPU
    workload — it must run while the lock is still held."""
    (tmp_path / "repo").mkdir()
    lock_dir = tmp_path / "gpu_lock"
    r = TestRunner(repo_root=tmp_path / "repo", tests_dir=tmp_path / "tests",
                   patterns=patterns, gpu_lock_dir=lock_dir,
                   cuda_visible_devices="", available_gpus=lambda: 1,
                   watchdog_interval=0.05)
    probe = tmp_path / "repo" / "probe.sh"
    probe.write_text(
        "#!/bin/bash\n"
        'if [[ "$*" == *--cov* ]]; then\n'
        '  echo "ERROR: unrecognized arguments: --cov=x"; exit 2\nfi\n'
        f'test -f {lock_dir / "lock"} && echo LOCKED-DURING-FALLBACK\n')
    out = r.run(TestJob(key="covlock", command="bash probe.sh --cov=x",
                        timeout_sec=20, min_gpus=1, index=9),
                dict(os.environ))
    assert out.rc == 0
    log = (tmp_path / "tests" / "09_covlock.log").read_text()
    assert "LOCKED-DURING-FALLBACK" in log
    assert not (lock_dir / "lock").exists()  # released afterwards


def test_setup_timeout_is_best_effort(runner, tmp_path):
    job = TestJob(key="setup", command="echo main-ran", timeout_sec=0.4,
                  min_gpus=0, index=10, setup="sleep 60")
    out = runner.run(job, dict(os.environ))
    assert out.rc == 0  # the job itself still ran and passed
    log = (tmp_path / "tests" / "10_setup.log").read_text()
    assert "[setup] ignored failure" in log and "main-ran" in log


def test_artifact_globs_cannot_escape_or_recurse(runner, tmp_path):
    from infermatrix_copilot.testing.runner import cleanup_test_artifacts
    repo = tmp_path / "repo"
    (repo / "sub").mkdir()
    (repo / "sub" / "nested.wav").write_text("keep")
    outside = tmp_path / "outside.wav"
    outside.write_text("keep")
    removed = cleanup_test_artifacts(
        repo, ["**/*.wav", "../outside.wav", "sub/nested.wav"])
    assert removed == 0
    assert (repo / "sub" / "nested.wav").exists() and outside.exists()


def test_final_scan_catches_fast_failures(runner, tmp_path):
    """A job shorter than the watchdog poll interval that prints a critical
    line and exits 0 must NOT earn a pass marker — the final scan sees it."""
    job = TestJob(key="fast", timeout_sec=30, min_gpus=0, index=12,
                  command="echo 'CUDA out of memory'; true")
    out = runner.run(job, dict(os.environ))
    assert out.watchdog_triggered and out.rc != 0
    assert not (tmp_path / "tests" / ".passed_fast").exists()


def test_timeout_return_waits_for_tree_kill(runner, tmp_path):
    """_spawn must not return while the fired primary timer is still
    escalating: by return time the own-pgroup child is already dead."""
    pidfile = tmp_path / "child2.pid"
    job = TestJob(
        key="join", timeout_sec=0.5, min_gpus=0, index=13,
        command=(f"setsid bash -c 'echo $$ > {pidfile}; exec sleep 60' &\n"
                 f"sleep 0.2; wait"))
    out = runner.run(job, dict(os.environ))
    assert out.timed_out
    child = int(pidfile.read_text().strip())
    with pytest.raises(ProcessLookupError):  # dead already, not eventually
        os.kill(child, 0)


def test_setup_nonzero_rc_is_logged(runner, tmp_path):
    job = TestJob(key="setuprc", command="echo main-ran", timeout_sec=10,
                  min_gpus=0, index=14, setup="false")
    out = runner.run(job, dict(os.environ))
    assert out.rc == 0
    log = (tmp_path / "tests" / "14_setuprc.log").read_text()
    assert "[setup] ignored failure: rc=1" in log


def test_setup_timeout_kills_its_session_children(runner, tmp_path):
    pidfile = tmp_path / "setup_child.pid"
    job = TestJob(
        key="setupkill", command="echo main-ran", timeout_sec=1, min_gpus=0,
        index=15,
        setup=f"bash -c 'echo $$ > {pidfile}; exec sleep 60' &\nsleep 60")
    out = runner.run(job, dict(os.environ))
    assert out.rc == 0
    child = int(pidfile.read_text().strip())
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            os.kill(child, 0)
            time.sleep(0.1)
        except ProcessLookupError:
            break
    else:
        os.kill(child, signal.SIGKILL)
        pytest.fail("setup's background child survived the group kill")


def test_job_cuda_override_governs_gate_and_cleanup(patterns, tmp_path):
    """A job redirecting itself to other GPUs is gated on ITS devices and
    cleaned up on ITS devices, not the runner's."""
    (tmp_path / "repo").mkdir()
    cleaned = []
    import infermatrix_copilot.testing.runner as rmod
    orig_clean, orig_wait = rmod.cleanup_orphan_gpu_procs, rmod.wait_gpu_memory_idle
    rmod.cleanup_orphan_gpu_procs = lambda dev, **k: cleaned.append(dev) or 0
    rmod.wait_gpu_memory_idle = lambda dev, **k: True
    try:
        r = TestRunner(repo_root=tmp_path / "repo",
                       tests_dir=tmp_path / "tests", patterns=patterns,
                       gpu_lock_dir=tmp_path / "gl",
                       cuda_visible_devices="0",
                       available_gpus=lambda: 1, watchdog_interval=0.05)
        # runner has 1 GPU, but the job redirects to 2 — gate on the job's
        out = r.run(TestJob(key="redir", command="true", timeout_sec=10,
                            min_gpus=2, index=16,
                            env={"CUDA_VISIBLE_DEVICES": "2,3"}),
                    dict(os.environ))
        assert not out.skipped and out.rc == 0
        assert cleaned == ["2,3"]  # cleanup targeted the job's devices
        # and the reverse: runner has GPUs, job pins itself to none
        out = r.run(TestJob(key="none", command="true", timeout_sec=10,
                            min_gpus=1, index=17,
                            env={"CUDA_VISIBLE_DEVICES": ""}),
                    dict(os.environ))
        assert out.skipped
    finally:
        rmod.cleanup_orphan_gpu_procs = orig_clean
        rmod.wait_gpu_memory_idle = orig_wait


def test_gpu_lock_steal_never_removes_live_lock_under_contention(tmp_path):
    """The steal path re-verifies staleness inside its flock'd critical
    section: a live lock created in the race window survives every steal."""
    d = tmp_path / "gl"
    live = GpuLock(d, poll_sec=0.01, timeout_sec=5).acquire()  # us, alive
    thief = GpuLock(d, poll_sec=0.01, timeout_sec=0.05)
    assert thief._steal_if_stale() is False
    assert (d / "lock").read_text() == str(os.getpid())  # untouched
    live.release()


def test_watchdog_never_fires_twice(tmp_path, patterns):
    """The kill marker grows the log; a later scan must not rediscover the
    same error and kill/record/report a second time."""
    kills, reports = [], []
    log = tmp_path / "t.log"
    log.write_text("CUDA out of memory\n")
    wd = LogWatchdog(patterns, log, pid=99999, test_name="t",
                     kill_fn=lambda pid: kills.append(pid),
                     report_fn=lambda *a: reports.append(a),
                     pid_alive=lambda pid: True)
    assert wd.check_once() is True
    assert wd.check_once() is True  # final scan: no re-fire
    assert len(kills) == 1 and len(reports) == 1


def test_reconcile_after_wait_is_child_scoped(tmp_path):
    """A duplicate child's parent reaping its loser must not mark the
    winner's live run interrupted (mcp_server passes the reaped pid)."""
    from infermatrix_copilot import run_status as rs
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    rs.init_queued(run_dir, run_id="r", owner_server_id="s", owner_server_pid=1)
    rs.mark_child_started(run_dir, child_pid=4242, state=rs.RUNNING)
    # the reaped pid differs from the recorded (winning) child: no-op
    # (_locked_update returns the untouched current record on opt-out)
    out = rs.reconcile_after_wait(run_dir, child_pid=9999)
    assert out["state"] == rs.RUNNING
    assert rs.read_status(run_dir)["state"] == rs.RUNNING
    # the recorded child's own parent may reconcile
    out = rs.reconcile_after_wait(run_dir, child_pid=4242)
    assert out["state"] == rs.INTERRUPTED


def test_setup_group_kill_reaps_term_ignoring_child(runner, tmp_path):
    """The setup leader exiting promptly must not spare a background child
    that ignores SIGTERM — the unconditional group KILL reaps it."""
    pidfile = tmp_path / "stubborn.pid"
    job = TestJob(
        key="stubborn", command="echo main-ran", timeout_sec=1, min_gpus=0,
        index=18,
        setup=(f"bash -c 'trap \"\" TERM; echo $$ > {pidfile}; "
               f"exec sleep 60' &\nsleep 60"))
    out = runner.run(job, dict(os.environ))
    assert out.rc == 0
    child = int(pidfile.read_text().strip())
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            os.kill(child, 0)
            time.sleep(0.1)
        except ProcessLookupError:
            break
    else:
        os.kill(child, signal.SIGKILL)
        pytest.fail("TERM-ignoring setup child survived the group KILL")


def test_base_env_cuda_override_also_governs_gate(patterns, tmp_path):
    """CUDA redirection in the BASE env (not job.env) must govern gating too:
    the child sees {**env, **job.env}."""
    (tmp_path / "repo").mkdir()
    r = TestRunner(repo_root=tmp_path / "repo", tests_dir=tmp_path / "tests",
                   patterns=patterns, cuda_visible_devices="0,1",
                   available_gpus=lambda: 2, watchdog_interval=0.05)
    env = dict(os.environ)
    env["CUDA_VISIBLE_DEVICES"] = ""  # base env pins the child to no GPUs
    out = r.run(TestJob(key="basecuda", command="true", timeout_sec=10,
                        min_gpus=1, index=19), env)
    assert out.skipped  # gated on the child's effective devices, not ours


def test_gpu_lock_steal_grace_for_unparseable_lock(tmp_path):
    """An empty lock younger than the grace window is a writer mid-create,
    not a crash artifact — it must not be stolen."""
    d = tmp_path / "gl"
    d.mkdir()
    (d / "lock").write_text("")
    lock = GpuLock(d, poll_sec=0.01, timeout_sec=0.05)
    with pytest.raises(Exception):
        lock.acquire()  # fresh empty lock: honored, so acquire times out


def test_failure_and_skip_clear_stale_pass_marker(runner, tmp_path):
    ok = TestJob(key="flip", command="true", timeout_sec=10, min_gpus=0,
                 index=11)
    runner.run(ok, dict(os.environ))
    marker = tmp_path / "tests" / ".passed_flip"
    assert marker.exists()
    runner.run(TestJob(key="flip", command="false", timeout_sec=10,
                       min_gpus=0, index=11), dict(os.environ))
    assert not marker.exists()  # failure removed the stale marker
    runner.run(ok, dict(os.environ))
    assert marker.exists()
    runner.run(TestJob(key="flip", command="true", timeout_sec=10,
                       min_gpus=9, index=11), dict(os.environ))  # hw skip
    assert not marker.exists()  # a skip must not retain a misleading marker
