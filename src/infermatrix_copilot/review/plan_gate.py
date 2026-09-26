"""Plan-review verdict policy and mode-aware context for generated playbooks.

The application supplies its reviewer and retains the human confirmation gate.
"""

from __future__ import annotations

from dataclasses import dataclass

import yaml

from ..playbooks.store import playbook_to_doc


def _mode_review_context(playbook, spec) -> str:
    """Plan-review context for MODE-AWARE playbooks: the reviewer sees the
    raw yaml's FULL step list, but the `when:` gates resolve against the
    ALREADY-RESOLVED mode (`resolve_effective_mode` runs before the review
    gate) — without this context a report-only plan looks like it runs its
    write/push steps and gets spuriously blocked. The active-step set is
    the same mechanical truth the executor computes, never prose."""
    if not getattr(playbook, "mode_aware", False):
        return ""
    mode = str((getattr(spec, "params", None) or {})
               .get("rebase_mode", "") or "")
    if not mode:
        return ""
    from ..engine.executor import _eval_when
    from ..rebase_engine.modes import mode_state_flags

    flags = {"task_spec": {}, **mode_state_flags(mode)}
    active = [s.get("id", s.get("step", "?"))
              for s in playbook_to_doc(playbook).get("steps", [])
              if "when" not in s or _eval_when(s["when"], flags)]
    repo = str(getattr(spec, "repo", "") or "")
    repo_line = (f"\nTarget repo (authoritative): {repo!r} — bound at "
                 "runtime from the TaskSpec; the yaml `repos:` list is a "
                 "planner RECALL FILTER where empty means repo-neutral, "
                 "never untargeted." if repo else "")
    return (f"\n\nResolved mode context (authoritative): "
            f"rebase_mode={mode}. Under this mode the `when:` gates run "
            f"ONLY these steps: {active}. Every other listed step is "
            "statically gated OFF for this run — judge the plan for THIS "
            "mode's step set."
            + repo_line +
            "\nWrite/push governance (authoritative): the mode's own "
            "push/CI steps are governed at runtime by the push-gate "
            "ruling, guard_push, and the ALLOW_PUSH env double-gate — "
            "the task tier does not forbid steps this mode activates.")


@dataclass(frozen=True)
class PlanGateResult:
    allowed: bool
    notices: tuple[str, ...] = ()


def review_plan_gate(
    resolution, spec, llm, model, assume_yes, *, review_fn
) -> PlanGateResult:
    """Interpret a reviewer verdict without owning confirmation or output."""
    if not resolution.requires_review:
        return PlanGateResult(True)
    doc = yaml.safe_dump(playbook_to_doc(resolution.playbook), sort_keys=False)
    task_text = spec.describe() + _mode_review_context(resolution.playbook, spec)
    verdict = review_fn(llm, playbook_doc=doc, task=task_text, model=model)
    notices = []
    if verdict.verdict != "unavailable":
        notices.append(f"  plan review: {verdict.verdict}"
                       + (f" — {verdict.critiques}" if verdict.critiques else ""))
    if verdict.verdict == "block":
        notices.append("✋ plan blocked by reviewer.")
        return PlanGateResult(False, tuple(notices))
    if verdict.passing:
        return PlanGateResult(True, tuple(notices))
    # A non-passing verdict can only proceed through explicit human review.
    # --yes removes that confirmation, so revise/unavailable must block.
    if assume_yes:
        reason = ("no reviewer LLM" if verdict.verdict == "unavailable"
                  else f"plan review returned {verdict.verdict}")
        notices.append(f"✋ {reason} and --yes leaves no human to gate it — blocked.")
        return PlanGateResult(False, tuple(notices))
    if verdict.verdict == "unavailable":
        notices.append("  ⚠ no reviewer LLM — your confirmation is the plan-review gate")
    return PlanGateResult(True, tuple(notices))
