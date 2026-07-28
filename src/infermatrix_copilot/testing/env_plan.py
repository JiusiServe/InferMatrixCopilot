"""Subprocess environment construction — replaces the rebase agent's
`_export_all_settings` global-env bridge.

The contract is inherit-plus-overlay: children get a full copy of the current
process environment (exactly what the shell era gave them — proxies, certs,
locale, NCCL settings all ride along implicitly) plus the job-specific
overlay. The fix over the old world is only that **our own process env is
never mutated**; and the agent-shell variant additionally scrubs credentials.
"""

from __future__ import annotations

import os
from pathlib import Path

# Credential material the agent shell must not see. HF_TOKEN is deliberately
# NOT here — gated-model downloads need it; adapters opt in via manifest.
AGENT_SHELL_SCRUB_PREFIXES = (
    "ANTHROPIC_", "OPENAI_", "CURSOR_", "RESEND_", "SMTP_",
)
AGENT_SHELL_SCRUB_EXACT = (
    "BUILDKITE_API_TOKEN", "GITHUB_TOKEN", "GH_TOKEN",
    "GIT_ASKPASS", "SSH_ASKPASS",
)


def build_subprocess_env(*, venv: Path | None = None,
                         cuda_visible_devices: str | None = None,
                         hf_home: str | None = None,
                         job_env: dict[str, str] | None = None,
                         pythonpath_prepend: str | None = None,
                         base: dict[str, str] | None = None) -> dict[str, str]:
    """The env dict for one test/tool subprocess. Overlay order (later wins):
    inherited base → venv PATH/VIRTUAL_ENV → CUDA/HF → PYTHONPATH prepend →
    per-job pairs (a job may deliberately override CUDA_VISIBLE_DEVICES)."""
    env = dict(base if base is not None else os.environ)
    if venv is not None:
        venv = Path(venv)
        env["VIRTUAL_ENV"] = str(venv)
        env["PATH"] = f"{venv / 'bin'}{os.pathsep}{env.get('PATH', '')}"
    if cuda_visible_devices is not None:
        env["CUDA_VISIBLE_DEVICES"] = cuda_visible_devices
    if hf_home is not None:
        env["HF_HOME"] = hf_home
    if pythonpath_prepend:
        # the main-baseline worktree must beat the editable install
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (f"{pythonpath_prepend}{os.pathsep}{existing}"
                             if existing else pythonpath_prepend)
    env.update(job_env or {})
    return env


def scrub_agent_shell_env(env: dict[str, str], *,
                          keep_hf_token: bool = True) -> dict[str, str]:
    """Strip credential material from an agent-shell child env. Pure function:
    returns a new dict, never mutates. `keep_hf_token=False` also drops
    HF_TOKEN for adapters that don't declare gated-model tests."""
    out = {
        k: v for k, v in env.items()
        if not k.startswith(AGENT_SHELL_SCRUB_PREFIXES)
        and k not in AGENT_SHELL_SCRUB_EXACT
    }
    if not keep_hf_token:
        out.pop("HF_TOKEN", None)
        out.pop("HUGGING_FACE_HUB_TOKEN", None)
    return out
