"""Review engine: REAL headless Claude Code + the vllm-omni-review skill.

Eval-validated (eval/ANALYSIS.md): on the same model, Claude Code + skill beat
every prompt-only configuration on actionability (0.92) and ground-truth hits,
because the skill's value lives in the harness (subagents, gh evidence).

Safety: the CLI runs with a tool allowlist of read-only tools plus
`gh pr view/diff/checks` — posting is structurally impossible from the review
engine; outward writes remain the copilot's gated pr.post_review step.
Falls back to the single-shot reviewer when the CLI or skill is unavailable.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from .step import FailureKind, StepContext, StepResult, StepSpec

_ALLOWED_TOOLS = [
    "Skill", "Task", "Agent", "Read", "Grep", "Glob", "LS", "TodoWrite",
    "Bash(gh pr view:*)", "Bash(gh pr diff:*)", "Bash(gh pr checks:*)",
]


def _cc_env(ctx: StepContext) -> dict:
    import os

    env = dict(os.environ)
    s = ctx.settings
    env.update(
        ANTHROPIC_API_KEY=s.anthropic_api_key,
        ANTHROPIC_AUTH_TOKEN=s.anthropic_api_key,
        ANTHROPIC_MODEL=s.agent_model,
    )
    if s.anthropic_base_url:
        env["ANTHROPIC_BASE_URL"] = s.anthropic_base_url
    return env


def _prepare_workdir(ctx: StepContext, skill_dir: Path) -> Path:
    workdir = ctx.run_dir / "cc_review"
    dst = workdir / ".claude" / "skills" / skill_dir.name
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(skill_dir, dst)
    return workdir


async def _fallback_single_shot(ctx: StepContext, reason: str) -> StepResult:
    """Degrade to the shipped single-shot reviewer so pr_review always works."""
    from .builtin_steps import _agent_step

    handler = _agent_step(
        "You are a meticulous code reviewer for the vLLM-Omni repo. "
        "Review the diff for correctness, scope and risk; output concise "
        "findings as a markdown list with file:line references.",
        "diff_text", "review_text")
    result = await handler(ctx)
    if result.ok:
        result.summary = f"single-shot review (fallback: {reason}) — {result.summary}"
    return result


async def _cc_review(ctx: StepContext) -> StepResult:
    spec = ctx.state.get("task_spec") or {}
    pr = spec.get("pr") if isinstance(spec, dict) else None
    if not pr:
        return StepResult(False, FailureKind.BLOCKED, "no PR number in task spec")

    skill_dir = Path(ctx.settings.review_skill_dir or "")
    if not ctx.settings.review_skill_dir or not (skill_dir / "SKILL.md").exists():
        return await _fallback_single_shot(ctx, "REVIEW_SKILL_DIR not configured")
    if shutil.which(ctx.settings.claudecode_bin) is None:
        return await _fallback_single_shot(ctx, "claude CLI not installed")

    workdir = _prepare_workdir(ctx, skill_dir)
    repo = ctx.state.get("repo_path") or ""
    prompt = (
        f"Use the {skill_dir.name} skill to review PR #{pr} of "
        f"vllm-project/vllm-omni."
        + (f" A read-only checkout of the repo is at {repo}." if repo else "")
        + " IMPORTANT: do NOT post anything to GitHub — output the complete "
          "review (verdict + comments with file:line) as your final message."
    )
    cmd = [ctx.settings.claudecode_bin, "-p", prompt,
           "--output-format", "json",
           "--max-turns", str(ctx.settings.claudecode_max_turns),
           "--allowedTools", ",".join(_ALLOWED_TOOLS)]
    ctx.trace.record("cc_review_start", pr=pr, max_turns=ctx.settings.claudecode_max_turns)
    try:
        out = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=ctx.settings.claudecode_timeout_sec,
                             env=_cc_env(ctx), cwd=str(workdir))
    except subprocess.TimeoutExpired:
        return await _fallback_single_shot(ctx, "claude CLI timed out")
    except FileNotFoundError:
        return await _fallback_single_shot(ctx, "claude CLI not found")

    try:
        data = json.loads(out.stdout)
    except json.JSONDecodeError:
        return await _fallback_single_shot(
            ctx, f"claude CLI returned no JSON (exit {out.returncode})")
    review = str(data.get("result") or "").strip()
    if not review or data.get("is_error"):
        return await _fallback_single_shot(ctx, "claude CLI returned an error/empty result")

    usage = data.get("usage") or {}
    ctx.trace.record("cc_review_done", turns=data.get("num_turns"),
                     output_tokens=usage.get("output_tokens"))
    ctx.state["review_text"] = review
    return StepResult(
        True,
        summary=f"Claude Code + skill review produced ({data.get('num_turns')} "
                f"turns, {len(review)} chars)",
        outputs={"review_text": review[:4_000], "engine": "claudecode_skill",
                 "turns": data.get("num_turns")})


def register_cc_review_steps(registry) -> None:
    registry.register(StepSpec(
        "review.claudecode_skill", "agent", "read", _cc_review,
        "PR review via headless Claude Code + the vllm-omni-review skill "
        "(read-only gh allowlist; falls back to the single-shot reviewer)."))
