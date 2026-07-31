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
    rebase_dir = os.environ.get("IMX_ADAPTER_REBASE", "")
    if rebase_dir:
        pat_file = Path(rebase_dir).parent / "testing" / \
            "watchdog_patterns.yaml"
        if pat_file.is_file():
            patterns = WatchdogPatterns.from_yaml(pat_file)

    timeout = int(os.environ.get("TEST_TIMEOUT_SEC", "7200"))
    cuda = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    runner = TestRunner(
        repo_root=Path(repo), tests_dir=Path(log_dir) / "tests",
        patterns=patterns, gpu_lock_dir=Path(log_dir) / "gpu_lock",
        cuda_visible_devices=cuda)
    job = TestJob(key=_job_key(args), command=command, timeout_sec=timeout,
                  min_gpus=1 if _needs_gpu_lock(args) else 0, index=0)
    outcome = runner.run(job, dict(os.environ))
    if outcome.skipped:
        print(f"imx-omni-pytest: skipped — {outcome.skip_reason}",
              file=sys.stderr)
    return outcome.rc


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
