"""Pytest evidence for adapter-declared local validation jobs."""

from __future__ import annotations

import json
import shlex
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from ..testing.runner import TestOutcome
from .test_loop import TestRunResult


def pytest_report_env(env: dict[str, str], report: Path) -> dict[str, str]:
    """Give each target/baseline/retry its own fresh machine-readable report."""
    report.parent.mkdir(parents=True, exist_ok=True)
    report.unlink(missing_ok=True)
    return {**env, "PYTEST_ADDOPTS": (
        env.get("PYTEST_ADDOPTS", "") + " --junitxml=" + shlex.quote(str(report))
    ).strip()}


def pytest_result(outcome: TestOutcome, report: Path | None = None, *,
                  runtime_required: bool = False) -> TestRunResult:
    infra = "timeout" if outcome.timed_out else (
        "watchdog kill" if outcome.watchdog_triggered else "")
    counts = {}
    failures = []
    if outcome.skipped:
        if runtime_required:
            infra = "required runtime job skipped: " + outcome.skip_reason
    elif report is not None and not infra:
        try:
            root = ET.parse(report).getroot()
            cases = list(root.iter("testcase"))
            counts = {"collected": len(cases), "passed": 0, "failed": 0,
                      "errors": 0, "skipped": 0}
            for case in cases:
                failure, error = case.find("failure"), case.find("error")
                if case.find("skipped") is not None:
                    counts["skipped"] += 1
                elif error is not None:
                    counts["errors"] += 1
                elif failure is not None:
                    counts["failed"] += 1
                    failures.append((
                        case.get("classname", "") + "::" + case.get("name", ""),
                        failure.get("type", ""), failure.get("message", "")))
                else:
                    counts["passed"] += 1
            if outcome.rc in (2, 3, 4, 5) or counts["errors"]:
                infra = f"pytest collection/setup/invocation failure (rc={outcome.rc})"
            elif not cases:
                infra = "pytest collected no tests"
            elif runtime_required and counts["skipped"]:
                infra = "required runtime tests skipped"
            elif runtime_required and not counts["passed"] and not counts["failed"]:
                infra = "required runtime tests did not execute"
        except (OSError, ET.ParseError) as exc:
            infra = f"pytest report unavailable: {exc}"
    return TestRunResult(
        rc=(outcome.rc or 1) if infra or failures else outcome.rc,
        output=outcome.log_file, skipped=outcome.skipped and not infra,
        skip_reason=outcome.skip_reason, infra=infra,
        failures=tuple(failures), counts=counts)


def runtime_identity(python: str, package: str, version: str, *,
                     env: dict[str, str], cwd: Path,
                     upstream: str = "", commit: str = "") -> dict:
    """Check the dependency actually imported by the test interpreter.

    local_rebase installs an editable dependency from its selected upstream
    checkout; verify that import origin and checkout revision too. Prepared
    local_ci environments may instead use an installed release wheel.
    """
    if not package or not version:
        raise ValueError("required runtime package and target version must be declared")
    snippet = (
        "import importlib, importlib.metadata, json, sys\n"
        "module = importlib.import_module(sys.argv[1])\n"
        "print(json.dumps({'package': sys.argv[1], "
        "'version': importlib.metadata.version(sys.argv[1]), "
        "'module_version': module.__version__, 'origin': module.__file__, "
        "'python': sys.executable}))\n"
    )
    result = subprocess.run(
        [python, "-c", snippet, package], cwd=cwd, env=env,
        capture_output=True, text=True, timeout=60, check=False)
    if result.returncode:
        raise ValueError("target runtime is not importable: " + result.stderr[-2000:])
    try:
        identity = json.loads(result.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError) as exc:
        raise ValueError("target runtime returned no identity") from exc
    # Release builds may append the selected git SHA as a PEP 440 local
    # version; a different base release is never the requested runtime.
    if (str(identity["version"]).split("+", 1)[0] != version
            or str(identity["module_version"]).split("+", 1)[0] != version):
        raise ValueError(f"target runtime version mismatch: {identity}")
    if upstream or commit:
        if not upstream or not commit:
            raise ValueError("local rebase requires the selected runtime source and commit")
        origin = Path(identity["origin"]).resolve()
        if not origin.is_relative_to(Path(upstream).resolve()):
            raise ValueError(f"runtime imports {origin}, not selected source {upstream}")
        revision = subprocess.run(
            ["git", "-C", upstream, "rev-parse", "HEAD"], capture_output=True,
            text=True, timeout=30, check=False)
        if revision.returncode or revision.stdout.strip() != commit:
            raise ValueError("imported runtime source does not match the selected commit")
        identity["commit"] = commit
    return identity
