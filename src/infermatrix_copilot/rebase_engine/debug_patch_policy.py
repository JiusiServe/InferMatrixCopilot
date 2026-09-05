"""Fail-closed policy for patches produced by automatic debug agents.

Remote CI remains the final judge for product-code changes that cannot run on
the local host. Tests are different: weakening the oracle can manufacture a
green result. This module snapshots the small policy-sensitive surface before
an agent runs and evaluates only the delta introduced by that attempt.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

_SENSITIVE_LINE = re.compile(
    r"\bassert\b|pytest\.(?:raises|approx)|"
    r"\b(?:atol|rtol|tolerance|threshold|similarity|ssim|psnr|wer)\b",
    re.IGNORECASE,
)
_POLICY_SUFFIXES = {
    ".cfg", ".ini", ".j2", ".jinja", ".json", ".md", ".py", ".sh",
    ".toml", ".txt", ".yaml", ".yml",
}


@dataclass(frozen=True)
class PatchPolicySnapshot:
    """Relevant file state immediately before one debug-agent attempt."""

    sensitive_lines: dict[str, tuple[str, ...]]
    test_hashes: dict[str, str]


@dataclass(frozen=True)
class PatchPolicyDecision:
    allowed: bool
    reason: str = ""
    paths: tuple[str, ...] = ()


def _repo_files(repo: Path) -> tuple[str, ...]:
    proc = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "-co", "--exclude-standard", "-z"],
        capture_output=True,
        timeout=60,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError("cannot enumerate repository files for debug-patch policy")
    return tuple(
        p.decode("utf-8", errors="surrogateescape")
        for p in proc.stdout.split(b"\0")
        if p
    )


def _is_test_file(relative: str) -> bool:
    path = Path(relative)
    parts = {part.lower() for part in path.parts[:-1]}
    name = path.name.lower()
    return (
        "test" in parts
        or "tests" in parts
        or name.startswith("test_")
        or name.endswith("_test.py")
    )


def _read(repo: Path, relative: str) -> bytes:
    path = repo / relative
    try:
        return path.read_bytes() if path.is_file() else b""
    except OSError:
        return b""


def capture_patch_policy(repo: Path) -> PatchPolicySnapshot:
    """Capture assertion/tolerance lines and complete test-file hashes."""
    repo = Path(repo)
    sensitive: dict[str, tuple[str, ...]] = {}
    tests: dict[str, str] = {}
    for relative in _repo_files(repo):
        is_test = _is_test_file(relative)
        if not is_test and Path(relative).suffix.lower() not in _POLICY_SUFFIXES:
            continue
        content = _read(repo, relative)
        if Path(relative).suffix.lower() in _POLICY_SUFFIXES:
            text = content.decode("utf-8", errors="replace")
            lines = tuple(line.strip() for line in text.splitlines()
                          if _SENSITIVE_LINE.search(line))
            if lines:
                sensitive[relative] = lines
        if is_test:
            tests[relative] = hashlib.sha256(content).hexdigest()
    return PatchPolicySnapshot(sensitive, tests)


def evaluate_debug_patch(
    repo: Path,
    before: PatchPolicySnapshot,
    *,
    local_verdict: str,
) -> PatchPolicyDecision:
    """Reject oracle changes, and reject any unverified test-file change."""
    after = capture_patch_policy(repo)
    sensitive_paths = tuple(sorted(
        path for path in set(before.sensitive_lines) | set(after.sensitive_lines)
        if before.sensitive_lines.get(path) != after.sensitive_lines.get(path)
    ))
    if sensitive_paths:
        return PatchPolicyDecision(
            False,
            "automatic debug patches may not change assertions or tolerances",
            sensitive_paths,
        )

    test_paths = tuple(sorted(
        path for path in set(before.test_hashes) | set(after.test_hashes)
        if before.test_hashes.get(path) != after.test_hashes.get(path)
    ))
    if test_paths and local_verdict != "passed":
        return PatchPolicyDecision(
            False,
            f"test-file changes require a passing local verification "
            f"(got {local_verdict})",
            test_paths,
        )
    return PatchPolicyDecision(True)
