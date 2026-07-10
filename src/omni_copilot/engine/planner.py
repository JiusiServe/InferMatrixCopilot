"""Planner — resolve a TaskSpec to a pipeline: reuse > adapt > generate (§3.2).

- Reuse (L0/L1): recall a registered active/locked playbook and parameterize it.
- Adapt (L1): incremental change on a vetted, NON-locked playbook -> plan review.
- Generate (L2): compose from registered steps; structurally limited to
  read/report-risk steps, plan review mandatory.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..playbooks.store import Playbook, PlaybookStep, PlaybookStore
from ..task_spec import READ_ONLY_KINDS, TaskSpec
from .registry import StepRegistry


class PlanningError(Exception):
    """A task cannot be resolved to a runnable plan — a declared, fail-closed
    refusal (capability gap, locked playbook, or a write-capable task with no
    vetted playbook) rather than a silently degraded plan."""


@dataclass
class Resolution:
    """The planner's decision for a task: which `playbook` to run, by which
    `mode` (reuse / adapt / generate), at which capability `tier`, whether it
    `requires_review` before execution, and human-readable `notes` on how it was
    chosen."""

    mode: str  # "reuse" | "adapt" | "generate"
    playbook: Playbook
    tier: str
    requires_review: bool = False
    notes: list[str] = field(default_factory=list)


# generate-tier templates: read-only step sequences per kind
_GENERATE_TEMPLATES: dict[str, list[tuple[str, str]]] = {
    "pr_review": [
        ("fetch", "pr.fetch_diff"),
        ("review", "agent.review_diff"),
        ("report", "report.final_summary"),
    ],
    "issue_answer": [
        ("fetch", "issue.fetch"),
        ("draft", "agent.draft_issue_answer"),
        ("report", "report.final_summary"),
    ],
    "issue_filter": [
        ("fetch", "issue.fetch"),
        ("triage", "agent.triage_issues"),
        ("report", "report.final_summary"),
    ],
}


class Planner:
    """Resolves a TaskSpec to a pipeline by the reuse > adapt > generate ladder,
    drawing playbooks from `store` and steps from `registry`."""

    def __init__(self, store: PlaybookStore, registry: StepRegistry):
        """Bind the planner to the playbook `store` it recalls from and the step
        `registry` it composes generate-tier plans out of."""
        self.store = store
        self.registry = registry

    def resolve(self, spec: TaskSpec,
                capabilities: set[str] | None = None) -> Resolution:
        """Pick a plan for `spec`, given the repo's available `capabilities`.

        Tries in order: **reuse** a recalled playbook when `spec.params` stay
        within its declared surface; **adapt** it (L1, review required) when there
        are extra params and it isn't locked; else **generate** an L2 plan from a
        read-only template. Raises PlanningError instead of degrading silently —
        when a vetted playbook exists but the repo can't feed it (capability gap),
        when a locked playbook would need undeclared params, or when a
        write-capable / template-less kind has no playbook. Returns a Resolution."""
        playbook = self.store.find(spec.kind, spec.repo, capabilities)
        if playbook is None and capabilities is not None:
            gaps = self.store.missing_capabilities(spec.kind, capabilities)
            if gaps and spec.kind not in READ_ONLY_KINDS:
                # a vetted playbook exists but the repo profile can't feed it:
                # declared degradation, not silent failure (§V2.2.4)
                raise PlanningError(
                    f"capability gap for '{spec.kind}' on {spec.repo}: "
                    + "; ".join(f"{name} requires {missing}"
                                for name, missing in sorted(gaps.items()))
                    + " — establish/extend the repo profile first "
                      "(run repo_profile)")

        # 1. Reuse — exact recall, parameterize only the declared surface.
        if playbook is not None:
            unknown = set(spec.params) - set(playbook.params)
            if not unknown:
                return Resolution(
                    mode="reuse", playbook=playbook, tier=spec.tier,
                    notes=[f"recalled {playbook.name}@{playbook.version} ({playbook.status})"],
                )
            # 2. Adapt — param overrides beyond the declared surface.
            if playbook.locked:
                raise PlanningError(
                    f"playbook '{playbook.name}' is locked; cannot adapt with "
                    f"undeclared params {sorted(unknown)} — run as-is or escalate"
                )
            return Resolution(
                mode="adapt", playbook=playbook, tier="L1", requires_review=True,
                notes=[f"adapting {playbook.name} with extra params {sorted(unknown)}"],
            )

        # 3. Generate — read-only kinds only, from registered steps only.
        if spec.kind not in READ_ONLY_KINDS:
            raise PlanningError(
                f"no playbook for write-capable task '{spec.kind}' — generation is "
                "not allowed for code-modifying tasks (L0/L1 only); escalate"
            )
        template = _GENERATE_TEMPLATES.get(spec.kind)
        if template is None:
            raise PlanningError(
                f"no playbook and no generate template for '{spec.kind}' — escalate")
        steps = []
        for step_id, step_name in template:
            s = self.registry.get(step_name)
            if s.risk not in ("read", "report"):
                raise PlanningError(
                    f"generated plan may not include risk={s.risk} step '{s.name}'"
                )
            steps.append(PlaybookStep(id=step_id, step=step_name))
        pb = Playbook(
            name=f"generated-{spec.kind}", version=1, status="candidate",
            task_kinds=[spec.kind], repos=[spec.repo], steps=steps,
            provenance={"created_by": "planner", "mode": "generate"},
        )
        return Resolution(
            mode="generate", playbook=pb, tier="L2", requires_review=True,
            notes=[f"generated {len(steps)}-step read-only plan from registry"],
        )
