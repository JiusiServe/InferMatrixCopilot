"""THE local test loop — port of the parent's `run_manifest_test_loop`
(phase 3; phase 4's local-CI fallback reuses it).

Control-flow parity, pinned by tests: per-test resume from checkpointed
progress (this run only — substate is run-stamped); GPU-count skips; a
failure re-runs the SAME test on the main-baseline worktree to split
pre-existing failures from rebase regressions (an unavailable worktree must
not mask a regression behind a git error — it is treated as a regression);
regressions go to the debug loop; every transition checkpoints.

One recorded divergence stands (plan §6.8): the PR1 runner produces TYPED
skip outcomes, so the parent's `_shell_skipped` rc=0 heuristic is not
ported — a skip can never masquerade as a pass here by construction.

The three ACTIONS are injected (run-on-rebase, run-on-baseline, debug) —
the assembly step supplies real implementations (TestRunner, worktree,
module agents); the loop owns only the decisions.
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable, Mapping, Sequence

from .substate import Substate

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class TestRunResult:
    __test__ = False
    rc: int
    output: str = ""
    skipped: bool = False
    skip_reason: str = ""
    # non-empty = INFRASTRUCTURE failure (timeout, watchdog kill, harness
    # crash) — Rev 8 §2.3 classifies these STRUCTURAL, never as ordinary
    # test-assertion failures, so the loop must keep them out of
    # `failed_tests` (which the push gate passes through flagged)
    infra: str = ""


# run_fn(slug) -> TestRunResult; baseline_fn(slug) -> TestRunResult | None
# (None = baseline worktree unavailable); debug_fn(slug, label, rc, output)
# -> bool (fixed)
RunFn = Callable[[str], TestRunResult]
BaselineFn = Callable[[str], "TestRunResult | None"]
DebugFn = Callable[[str, str, int, str], Awaitable[bool]]


async def run_test_loop(
    jobs: Sequence[Mapping],
    *,
    substate: Substate,
    run_fn: RunFn,
    baseline_fn: BaselineFn,
    debug_fn: DebugFn,
    visible_gpus: int = 0,
    phase_label: str = "Phase 3",
) -> dict:
    """Returns the parent's shape plus the structural split:
    ``{"passed", "failed", "failed_tests", "skipped_tests",
    "completed_slugs", "infra_failures"}`` — `failed_tests` holds ONLY
    assertion failures; infrastructure failures live in `infra_failures`. Progress lives under the
    substate's ``phase3_progress`` (run-stamped, so a phase-4 fallback in
    the same run resumes past everything phase 3 already ran)."""
    prev = substate.get("phase3_progress", {}) or {}
    prev_completed = set(prev.get("completed", []))
    prev_failed = set(prev.get("failed", []))
    prev_skipped = set(prev.get("skipped", []))
    prev_infra = list(prev.get("infra", []))
    if prev_completed or prev_failed or prev_skipped:
        log.info("%s resume: %d passed, %d failed, %d skipped from previous "
                 "attempt", phase_label, len(prev_completed),
                 len(prev_failed), len(prev_skipped))

    passed = failed = 0
    skipped_tests: list[str] = []
    failed_tests: list[str] = []
    completed_slugs: list[str] = []
    infra_failures: list[str] = list(prev_infra)
    infra_slugs = {i.split(":", 1)[0] for i in prev_infra}

    def checkpoint(current: str = "") -> None:
        substate.update({"phase3_progress": {
            "completed": completed_slugs, "failed": failed_tests,
            "skipped": skipped_tests, "infra": infra_failures,
            "current": current}})

    for job in jobs:
        slug = job.get("slug", "unknown")
        label = job.get("label", slug)
        min_gpus = int(job.get("min_gpus", 1))

        if slug in prev_completed:
            log.info("  [RESUME] %s — already passed, skipping", label)
            passed += 1
            completed_slugs.append(slug)
            continue
        if slug in prev_skipped:
            skipped_tests.append(slug)
            continue
        if slug in infra_slugs:
            # a recorded infrastructure failure stays structural on resume —
            # re-running could flip a timeout into a pass and un-block the gate
            failed += 1
            continue

        if visible_gpus > 0 and min_gpus > visible_gpus:
            log.warning("  SKIP: %s needs %d GPUs, only %d visible",
                        label, min_gpus, visible_gpus)
            skipped_tests.append(slug)
            checkpoint(slug)
            continue

        log.info("Running: %s", label)
        checkpoint(slug)
        result = run_fn(slug)
        if result.skipped:
            # typed skip from the runner (hw gate): never a pass, never
            # "completed" — a completed skip would survive resume and
            # inflate the report with tests that never ran (parent-documented)
            log.warning("  SKIPPED (%s): %s", result.skip_reason, label)
            skipped_tests.append(slug)
            checkpoint(slug)
            continue
        if result.rc == 0:
            log.info("  PASSED: %s", label)
            passed += 1
            completed_slugs.append(slug)
            checkpoint()
            continue
        if result.infra:
            # STRUCTURAL (Rev 8 §2.3): timeouts / watchdog kills / harness
            # crashes never enter the baseline-vs-regression split or the
            # assertion pass-through — the push gate blocks on these
            log.warning("  INFRA FAILURE (%s): %s (rc=%d)", result.infra,
                        label, result.rc)
            infra_failures.append(f"{slug}: {result.infra}")
            infra_slugs.add(slug)
            failed += 1
            checkpoint()
            continue

        baseline = baseline_fn(slug)
        if baseline is None:
            # infra failure preparing the worktree — do not mask a possible
            # regression behind a git error; treat as a regression
            log.warning("  FAILED on rebase: %s (rc=%d); baseline "
                        "unavailable — treating as REGRESSION", label,
                        result.rc)
        elif baseline.rc != 0:
            log.info("  [PRE-EXISTING] %s fails on main too (rebase rc=%d, "
                     "main rc=%d) — skipping, not a regression", label,
                     result.rc, baseline.rc)
            skipped_tests.append(slug)
            checkpoint(slug)
            continue

        log.info("  [REGRESSION] %s passes on main but fails on rebase — "
                 "debugging", label)
        fixed = await debug_fn(slug, label, result.rc, result.output)
        if fixed:
            passed += 1
            completed_slugs.append(slug)
        else:
            failed_tests.append(slug)
            failed += 1
        checkpoint()

    if failed_tests:
        log.warning("%s: %d test(s) still failing: %s", phase_label,
                    len(failed_tests), ", ".join(failed_tests[:5]))
    return {"passed": passed, "failed": failed,
            "failed_tests": failed_tests, "skipped_tests": skipped_tests,
            "completed_slugs": completed_slugs,
            "infra_failures": infra_failures}


# ── main-baseline worktree helpers ───────────────────────────────────────────

def ensure_main_worktree(repo: Path, worktree_path: Path,
                         base_ref: str = "origin/main") -> Path | None:
    """A detached worktree at the baseline ref for pre-existing-vs-regression
    comparison. Returns None on failure (the loop treats that as
    regression-preserving, never as a silent pass)."""
    repo, worktree_path = Path(repo), Path(worktree_path)
    if (worktree_path / ".git").exists():
        return worktree_path
    r = subprocess.run(["git", "-C", str(repo), "worktree", "add",
                        "--detach", str(worktree_path), base_ref],
                       capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        log.warning("main worktree creation failed: %s", r.stderr.strip())
        return None
    return worktree_path


def remove_main_worktree(repo: Path, worktree_path: Path) -> None:
    subprocess.run(["git", "-C", str(repo), "worktree", "remove", "--force",
                    str(worktree_path)], capture_output=True, text=True,
                   timeout=120)
