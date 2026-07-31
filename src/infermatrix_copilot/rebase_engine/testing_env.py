"""AGENT-shell child-env construction — the PRODUCTION wiring of the PR1
scrub substrate (plan §4: risk reduction; the control for unsupervised
agent-mutation runs is the recorded RUNBOOK acceptance, not this scrub).

Scope (Rev 8 §6): the scrub applies to AGENT shells only. Test subprocesses
use the inherit-plus-overlay plan (`testing.env_plan.build_subprocess_env`)
— stripping the process env from tests would erase required credentials and
runtime variables and misclassify the resulting failures. Agent shells get
a COPY of the process env passed through `scrub_agent_shell_env`; the
process env itself is never mutated."""

from __future__ import annotations

import os
from typing import Mapping

from ..testing.env_plan import scrub_agent_shell_env


def scrubbed_agent_env(extra: Mapping[str, str] | None = None, *,
                       keep_hf_token: bool = False) -> dict[str, str]:
    """The child env for agent shells and test jobs: current process env,
    scrubbed by the allowlist (exact/prefix split, credential-suffix veto),
    plus the caller's overlay. HF tokens only on explicit opt-in (the
    manifest's `validation.requires_hf_token`)."""
    env = scrub_agent_shell_env(dict(os.environ), keep_hf_token=keep_hf_token)
    if extra:
        env.update(extra)
    return env
