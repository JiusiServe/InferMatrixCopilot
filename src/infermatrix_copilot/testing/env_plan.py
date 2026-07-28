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

# The agent shell env is ALLOWLIST-based: two rounds of denylist review each
# found surviving credential shapes (tier keys, then AWS_SECRET_ACCESS_KEY /
# GOOGLE_APPLICATION_CREDENTIALS), and unknown forms are unenumerable in an
# inherited environment. Fail-closed means: a name not matching a known-safe
# prefix is dropped. The list is generous for runtime knobs (CUDA/NCCL/
# TORCH/VLLM/proxies/locale) and includes GIT_CONFIG_ because the push-block
# env-config injection must survive the scrub. HF tokens re-enter only on
# explicit opt-in (adapter manifests declaring gated-model tests).
# Scalar names match EXACTLY (treating "HOME"/"USER"/"HOST" as prefixes let
# HOME_TOKEN/USER_PASSWORD/HOST_API_KEY through); only genuine families are
# prefixes. A final credential-suffix veto backstops both lists.
AGENT_SHELL_SAFE_EXACT = frozenset({
    "PATH", "HOME", "LANG", "TERM", "TMPDIR", "TMP", "TEMP", "USER",
    "LOGNAME", "SHELL", "PWD", "OLDPWD", "HOST", "HOSTNAME", "TZ",
    "DISPLAY", "COLUMNS", "LINES", "VIRTUAL_ENV", "HF_HOME",
    "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY",
    "http_proxy", "https_proxy", "no_proxy",
})
AGENT_SHELL_SAFE_PREFIXES = (
    "LC_", "XDG_", "PYTHON", "PIP_", "CONDA_", "LD_",
    "CUDA_", "NCCL_", "TORCH_", "VLLM_", "HF_HUB_", "OMP_",
    "MKL_", "NVIDIA_", "TRITON_",
    "SSL_CERT", "REQUESTS_CA", "CURL_CA",
    "GIT_CONFIG_",
)
# even an allowlisted-by-prefix name is dropped when it is shaped like a
# credential (PYTHON_API_KEY, GIT_CONFIG_TOKEN, ...)
AGENT_SHELL_CRED_SUFFIXES = (
    "_TOKEN", "_SECRET", "_PASSWORD", "_API_KEY", "_ACCESS_KEY",
    "_CREDENTIALS", "_ASKPASS",
)
_HF_TOKEN_KEYS = ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN")


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
                          keep_hf_token: bool = False,
                          extra_safe_prefixes: tuple[str, ...] = ()
                          ) -> dict[str, str]:
    """Build the agent-shell child env by allowlist. Pure function: returns a
    new dict, never mutates. Anything not matching a known-safe prefix is
    dropped (fail-closed for unknown credential shapes). HF tokens are
    re-added only on explicit opt-in; adapters with legitimate extra runtime
    vars widen via `extra_safe_prefixes` (manifest data), never by weakening
    the default."""
    prefixes = AGENT_SHELL_SAFE_PREFIXES + extra_safe_prefixes
    out = {
        k: v for k, v in env.items()
        if (k in AGENT_SHELL_SAFE_EXACT or k.startswith(prefixes))
        and not k.endswith(AGENT_SHELL_CRED_SUFFIXES)
        and k not in _HF_TOKEN_KEYS
    }
    if keep_hf_token:
        for k in _HF_TOKEN_KEYS:
            if k in env:
                out[k] = env[k]
    return out
