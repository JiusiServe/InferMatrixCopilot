"""Cross-repo invariance scoring (design §V2.2.5, §V2.3.5) — pure functions;
the paid eval runs feed them, this module never calls an API.

Inputs are per-repo, per-arm replicate score lists (the campaign's hard
lesson: single rolls are ±0.1 noise — rank on replicate means only).
Outputs: replicate means, the invariance index (min/mean across repos,
target >= 0.8), and the profile-ablation verdict that gates promotion.
"""

from __future__ import annotations

from dataclasses import dataclass, field

INVARIANCE_TARGET = 0.8


def replicate_mean(scores: list[float]) -> float | None:
    """Mean over replicate runs; None when there are no scores (a missing
    arm must read as 'not measured', never as zero)."""
    return sum(scores) / len(scores) if scores else None


def invariance_index(per_repo_means: dict[str, float]) -> float | None:
    """min/mean across repos: 1.0 = identical quality everywhere; degrades as
    the weakest repo falls behind. Needs >= 2 repos to mean anything."""
    means = [m for m in per_repo_means.values() if m is not None]
    if len(means) < 2:
        return None
    mean = sum(means) / len(means)
    return (min(means) / mean) if mean > 0 else 0.0


@dataclass
class AblationVerdict:
    """§V2.3.5: a profile is promoted only when non-negative on quality at
    acceptable cost vs the {no-profile} arm on the SAME repo."""

    quality_delta: float | None       # profile mean - baseline mean
    cost_ratio: float | None          # profile cost / baseline cost
    promote: bool = False
    reason: str = ""


def ablation_verdict(with_profile: list[float], without_profile: list[float],
                     *, cost_with: float | None = None,
                     cost_without: float | None = None,
                     max_cost_ratio: float = 1.5) -> AblationVerdict:
    mean_with = replicate_mean(with_profile)
    mean_without = replicate_mean(without_profile)
    if mean_with is None or mean_without is None:
        return AblationVerdict(None, None, promote=False,
                               reason="both arms need replicate runs")
    delta = mean_with - mean_without
    ratio = (cost_with / cost_without
             if cost_with and cost_without else None)
    if delta < 0:
        return AblationVerdict(delta, ratio, promote=False,
                               reason=f"profile arm is worse "
                                      f"({mean_with:.3f} < {mean_without:.3f}) "
                                      "— the ETH failure mode; fix the "
                                      "briefing before promoting")
    if ratio is not None and ratio > max_cost_ratio:
        return AblationVerdict(delta, ratio, promote=False,
                               reason=f"cost ratio {ratio:.2f} exceeds "
                                      f"{max_cost_ratio} — trim the profile")
    return AblationVerdict(delta, ratio, promote=True,
                           reason="non-negative quality at acceptable cost")


@dataclass
class InvarianceReport:
    per_repo_means: dict[str, dict[str, float | None]] = field(default_factory=dict)
    index_per_kind: dict[str, float | None] = field(default_factory=dict)
    passing: dict[str, bool] = field(default_factory=dict)


def score_invariance(results: dict[str, dict[str, list[float]]],
                     *, target: float = INVARIANCE_TARGET) -> InvarianceReport:
    """results[repo][task_kind] = replicate scores -> per-kind invariance.

    A kind measured on fewer than two repos gets index None and passing=False:
    unmeasured cross-repo claims are worthless (§V2.2)."""
    report = InvarianceReport()
    kinds = {kind for by_kind in results.values() for kind in by_kind}
    for repo, by_kind in results.items():
        report.per_repo_means[repo] = {
            kind: replicate_mean(scores) for kind, scores in by_kind.items()}
    for kind in sorted(kinds):
        means = {repo: report.per_repo_means[repo].get(kind)
                 for repo in results if kind in results[repo]}
        idx = invariance_index(means)
        report.index_per_kind[kind] = idx
        report.passing[kind] = idx is not None and idx >= target
    return report
