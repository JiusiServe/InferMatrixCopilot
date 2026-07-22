"""`enforce_mcp_policy` — the structural safety gate for the MCP surface.

The MCP server exposes the copilot to Claude Code / Codex, which are
non-interactive: there is no `[y/N]` and no human in the loop to approve an
outward write. So the guarantee *"the host cannot widen the server's
permissions"* must hold **structurally**, and it must not depend on the on-disk
`request.json` being untampered — a same-user host process could rewrite it
between reservation and execution. This gate therefore runs in **two** places
(design rev 5/6):

- at the **boundary** (the server, when a tool is called), and
- in the **child** (authoritative), right after it reads `request.json`.

Either way it re-derives a *safe* `TaskSpec` from raw input, refusing anything
outside the read-only V1 surface. The allowlist of kinds is `READ_ONLY_KINDS`
from `task_spec` verbatim, so the gate can never drift from the code's own
notion of what is read-only.
"""

from __future__ import annotations

from typing import Any

from .task_spec import READ_ONLY_KINDS, TaskSpec

# params a V1 tool may legitimately carry through to the playbook. Anything else
# in an incoming `params` map is dropped (not an error — stripped) so a tampered
# request can't smuggle a knob (e.g. force_push) into a step. Allowed params are
# strictly value-validated below — a knob may modulate cost/depth, never widen
# permissions.
_ALLOWED_PARAMS: frozenset[str] = frozenset({"review_depth"})
_REVIEW_DEPTHS = ("auto", "light", "standard", "full")


class PolicyError(ValueError):
    """Raised when a request cannot be reduced to a safe read-only V1 task."""


def enforce_mcp_policy(raw: dict[str, Any], *, allowed_repos: list[str],
                       settings: Any = None) -> TaskSpec:
    """Reduce `raw` (an untrusted tool-call / `request.json` dict) to a safe,
    read-only `TaskSpec`, or raise `PolicyError`.

    Structural guarantees, independent of what `raw` claims:
    - `kind` MUST be one of `READ_ONLY_KINDS` (pr_review / issue_answer /
      issue_filter). Any write/push-capable kind (rebase, debug, profile) is
      refused — this is what makes the surface read-only regardless of the file.
    - `post` is forced False (no outward writes over MCP, ever, in V1).
    - `repo` MUST be in `allowed_repos`.
    - `pr` / `issue`, when present, MUST be positive integers.
    - `params` is stripped to the allow-set (currently empty) so no step knob
      can be injected.
    """
    if not isinstance(raw, dict):
        raise PolicyError("request is not an object")

    kind = raw.get("kind")
    if kind not in READ_ONLY_KINDS:
        raise PolicyError(
            f"kind {kind!r} is not permitted over MCP; allowed: "
            f"{sorted(READ_ONLY_KINDS)}")

    repo = raw.get("repo")
    if isinstance(repo, str) and "/" in repo and settings is not None:
        # full `owner/repo` form: resolve through the same identity validator
        # the CLI uses, so aliases mean the same thing on every surface
        from .intent import resolve_repo_alias

        owner, _, name = repo.partition("/")
        alias = resolve_repo_alias(owner, name, settings)
        if alias is None:
            raise PolicyError(f"repo {repo!r} does not match any configured repo")
        repo = alias
    if repo not in allowed_repos:
        raise PolicyError(
            f"repo {repo!r} not in the MCP allowlist {sorted(allowed_repos)}")

    pr = _positive_or_none(raw.get("pr"), "pr")
    issue = _positive_or_none(raw.get("issue"), "issue")

    raw_params = raw.get("params") or {}
    if not isinstance(raw_params, dict):
        raise PolicyError("params must be an object")
    params = {k: v for k, v in raw_params.items() if k in _ALLOWED_PARAMS}
    if "review_depth" in params:  # strict: a typo must not silently pass
        if str(params["review_depth"]).lower() not in _REVIEW_DEPTHS:
            raise PolicyError(
                f"review_depth {params['review_depth']!r} is not one of "
                f"{list(_REVIEW_DEPTHS)}")
        params["review_depth"] = str(params["review_depth"]).lower()

    mode = raw.get("mode", "eco")
    if mode not in {"eco", "performance"}:
        raise PolicyError(
            f"mode {mode!r} is invalid; allowed: ['eco', 'performance']")

    # Build through the validated model. post is hard-forced False; report_only
    # is irrelevant for READ_ONLY_KINDS (they are read-only unless post), but we
    # normalize it off too for a clean record.
    return TaskSpec(kind=kind, mode=mode, repo=repo, pr=pr, issue=issue,
                    report_only=False, post=False, params=params)


def _positive_or_none(value: Any, field: str) -> int | None:
    """Coerce `value` to a positive int, allow None/absent, else raise."""
    if value is None:
        return None
    try:
        n = int(value)
    except (TypeError, ValueError):
        raise PolicyError(f"{field} must be an integer, got {value!r}")
    if n <= 0:
        raise PolicyError(f"{field} must be positive, got {n}")
    return n
