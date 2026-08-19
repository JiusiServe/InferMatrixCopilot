"""`imx-omni-pytest` — the module agents' gated test wrapper, replacing the
parent's `run_module_pytest.sh` on the PR1 substrate (GPU mutex, two-tier
watchdog, layered timeouts, artifact cleanup — one implementation, not a
parallel shell copy).

Env contract (the agent shell provides these; all neutral):
  IMX_TARGET_REPO    repo the tests run in (the parent's OMNI_PATH)
  IMX_LOG_DIR        run log dir (logs under <dir>/tests, lock under
                     <dir>/gpu_lock)
  IMX_ADAPTER_REBASE optional adapter rebase-data dir (watchdog patterns at
                     ../testing/watchdog_patterns.yaml relative to it)
  IMX_GPU_MUTEX=1    hold the GPU lock for EVERY invocation (Phase-2 module
                     agents serialize all GPU work); otherwise the lock is
                     taken only when an arg targets tests/e2e/ or
                     tests/examples/ (parent parity)
  TEST_TIMEOUT_SEC   primary timeout (default 7200)
  CUDA_VISIBLE_DEVICES  passed through to the child

Invocation parity: `imx-omni-pytest -vv -s tests/x/` runs pytest;
`imx-omni-pytest python -c '...'` runs that command under the same gating
(the parent wrapper accepted both shapes)."""

from __future__ import annotations

import os
import shlex
import sys
from pathlib import Path

from ..testing.runner import TestJob, TestRunner
from ..testing.watchdog import WatchdogPatterns


def _needs_gpu_lock(args: list[str]) -> bool:
    if os.environ.get("IMX_GPU_MUTEX") == "1":
        return True
    return any(("tests/e2e/" in a or "tests/examples/" in a)
               for a in args if not a.startswith("-"))


def _job_key(args: list[str]) -> str:
    for a in args:
        if not a.startswith("-") and "tests/" in a:
            return a.strip("/").replace("/", "_").replace(".py", "")
    return "module_pytest"


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    repo = os.environ.get("IMX_TARGET_REPO", "")
    log_dir = os.environ.get("IMX_LOG_DIR", "")
    if not repo or not log_dir:
        print("imx-omni-pytest: IMX_TARGET_REPO and IMX_LOG_DIR must be set",
              file=sys.stderr)
        return 2
    if not args:
        print("imx-omni-pytest: no test paths or command given",
              file=sys.stderr)
        return 2

    if args[0] == "python" or args[0].startswith("python3"):
        command = " ".join(shlex.quote(a) if i else a
                           for i, a in enumerate(args))
    else:
        command = "python -m pytest " + " ".join(shlex.quote(a) for a in args)

    patterns = None
    artifact_globs: list[str] = []
    rebase_dir = os.environ.get("IMX_ADAPTER_REBASE", "")
    # runtime overlay (design D4): the agent env contract may hand the
    # learned-noise overlay path down; absent ⇒ seed-only, as before
    overlay = os.environ.get("IMX_WATCHDOG_OVERLAY", "")
    if rebase_dir:
        pat_file = Path(rebase_dir).parent / "testing" / \
            "watchdog_patterns.yaml"
        if pat_file.is_file():
            patterns = WatchdogPatterns.from_yaml(
                pat_file, overlay=Path(overlay) if overlay else None)
        manifest = Path(rebase_dir).parent / "manifest.yaml"
        if manifest.is_file():
            import yaml
            data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
            artifact_globs = list(((data.get("rebase") or {})
                                   .get("testing") or {})
                                  .get("artifact_globs") or [])

    timeout = int(os.environ.get("TEST_TIMEOUT_SEC", "7200"))
    cuda = os.environ.get("CUDA_VISIBLE_DEVICES", "")

    # two-tier watchdog wiring: learning + report artifacts land under the
    # run's log dir (parent parity). The eco-tier REVIEW callback needs an
    # LLM client the standalone keyless wrapper deliberately does not own —
    # review-tier matches take the documented default-CONTINUE until the
    # assembly PR threads the copilot client through; recorded divergence.
    from ..testing import watchdog_learn

    decisions = Path(log_dir) / "watchdog_decisions.jsonl"
    # stable harvest identity (design D4): run id from the agent env
    # contract when present, else synthesized from the log dir; seq is a
    # per-process counter — the curator's exactly-once harvest dedups on
    # (run, attempt, job_key, seq)
    run_ident = os.environ.get("IMX_RUN_ID", "") or Path(log_dir).name
    import itertools
    import uuid
    _seq = itertools.count(1)
    # the seq counter restarts per PROCESS, so two wrapper invocations for
    # the same test would collide on (run, "", test, 1) and the harvest
    # would wrongly dedup a real second decision — a collision-resistant
    # attempt id makes the identity process-unique (pid+seconds can
    # collide across same-second retries or pid reuse)
    _attempt = f"wrap-{uuid.uuid4().hex[:12]}"

    def record_fn(pattern: str, verdict: str, test_name: str) -> None:
        # LogWatchdog's contract is (matched line, verdict, test name);
        # watchdog_learn.record takes keyword-only fields
        watchdog_learn.record(decisions, pattern=pattern, verdict=verdict,
                              test=test_name, run=run_ident,
                              attempt=_attempt, job_key=test_name,
                              seq=next(_seq))

    def report_fn(test_name: str, pattern: str, detail: str) -> None:
        report = Path(log_dir) / "tests" / f"{test_name}.watchdog_report"
        report.parent.mkdir(parents=True, exist_ok=True)
        with open(report, "a", encoding="utf-8") as f:
            f.write(f"pattern={pattern}\n{detail}\n")

    def review_fn(test_name: str, snippet: str) -> str:
        # explicit no-LLM reviewer BY DESIGN: this standalone keyless
        # wrapper owns no LLM client, so every tier-2 match takes the
        # documented default-CONTINUE, RECORDED (the learning pipeline
        # promotes noise from accumulated CONTINUEs — a silent
        # short-circuit would starve it). The assembly's own test loop
        # wires the eco-tier LLM reviewer (rebase_v3._watchdog_collaborators).
        return "CONTINUE"

    runner = TestRunner(
        repo_root=Path(repo), tests_dir=Path(log_dir) / "tests",
        patterns=patterns, gpu_lock_dir=Path(log_dir) / "gpu_lock",
        artifact_globs=artifact_globs,
        review_fn=review_fn, record_fn=record_fn, report_fn=report_fn,
        cuda_visible_devices=cuda)
    # the mutex SERIALIZES; it is not a hardware requirement — min_gpus=0
    # so a GPU-less box still RUNS the command (a skip would be a false
    # pass), while gpu_lock=True holds the lock for the run
    job = TestJob(key=_job_key(args), command=command, timeout_sec=timeout,
                  min_gpus=0, gpu_lock=_needs_gpu_lock(args), index=0)
    outcome = runner.run(job, dict(os.environ))
    if outcome.skipped:
        print(f"imx-omni-pytest: skipped — {outcome.skip_reason}",
              file=sys.stderr)
    return outcome.rc


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
