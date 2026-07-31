"""Agent/test child-env construction — the PRODUCTION wiring of the PR1
scrub substrate (plan §4: risk reduction; the control for unsupervised
agent-mutation runs is the recorded RUNBOOK acceptance, not this scrub).

Every v3 child process (test jobs, agent shells) gets a COPY of the process
env passed through `scrub_agent_shell_env` — credentials and IDE hooks never
reach children; the process env itself is never mutated."""

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
