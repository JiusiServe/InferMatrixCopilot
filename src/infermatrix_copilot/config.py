"""Settings loaded from environment / .env (never committed)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlparse

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[2]


class TierNotConfiguredError(RuntimeError):
    """A performance-mode run was requested but no performance backend is
    configured. Deliberately NOT a silent fallback to the eco model — that
    fallback is how a run once carried a high-capability label while the
    endpoint silently served the eco-class model."""


@dataclass(frozen=True)
class ResolvedTarget:
    """One immutable LLM destination: which model, on which endpoint, with
    which credential — resolved centrally by `Settings.tier_target` so loose
    (model, client) pairs can never recombine a tier's model with the wrong
    backend. `source` labels the resolution for traces ("tier:eco" /
    "tier:performance" / "global"); the key itself never appears in logs."""

    role: str
    model: str
    base_url: str
    api_key: str
    source: str

    @property
    def host(self) -> str:
        """Endpoint hostname for traces/echo lines (default Anthropic when no
        base_url override is set)."""
        return urlparse(self.base_url).netloc if self.base_url else "api.anthropic.com"


class Settings(BaseSettings):
    """Process-wide configuration, populated from the environment / `.env` and
    grouped by concern (LLM, repos, engine, push safety, metrics, escalation).
    Values are the defaults; secrets stay empty here and arrive from `.env`."""

    # the repo's own .env loads regardless of cwd; a cwd-local .env overrides it
    model_config = SettingsConfigDict(
        env_file=(str(_REPO_ROOT / ".env"), ".env"),
        env_file_encoding="utf-8", extra="ignore",
    )

    # LLM (Anthropic-SDK-compatible endpoint; DeepSeek's /anthropic works)
    anthropic_api_key: str = ""
    anthropic_base_url: str = ""
    agent_model: str = "claude-sonnet-5"
    reviewer_model: str = ""  # empty -> agent_model
    intent_model: str = ""  # empty -> agent_model
    # Dual-path (双路径) model tiers for agent reasoning. The tier is chosen from
    # intent — `eco` by default, `performance` only when the user explicitly asks
    # for the high-performance model — and selects the model per run via
    # `model_for`. Both empty -> `agent_model` (so the split is a no-op until
    # `performance_model` is configured, and never changes existing behavior).
    eco_model: str = ""          # empty -> agent_model (the cost-effective default)
    performance_model: str = ""  # empty -> performance mode FAILS UPFRONT (tier_target)
    # Per-tier backends (plan v2): each tier may override the shared ANTHROPIC_*
    # backend. Atomic rule (validated below): a tier is fully unset (inherit
    # everything), model-only (different model on the shared backend), or
    # model+base_url+api_key all three (an independent backend). Partial
    # URL/key combos are startup errors — a tier URL must never receive the
    # shared credential, nor a tier credential the shared URL.
    eco_base_url: str = ""
    eco_api_key: str = ""
    performance_base_url: str = ""
    performance_api_key: str = ""
    # Served-model guard: "fail" (default) raises when a response names a
    # different model than requested (after alias normalization) — the
    # endpoint is substituting models; "warn" records loudly and continues.
    model_mismatch_policy: Literal["fail", "warn"] = "fail"
    # Audited requested->served equivalences that are NOT substitutions
    # (e.g. a gateway echoing a canonical/dated name). JSON in .env,
    # single-quoted; every application is traced (model_alias_applied).
    model_aliases: Annotated[dict, NoDecode] = {}
    llm_max_tokens: int = 16000  # 8k truncated verbose lens replies mid-JSON

    # Repos
    default_repo: str = "vllm-omni"
    repo_paths: dict[str, str] = {}
    # alias -> "owner/repo" full GitHub identity (REPO_FULL_NAMES env JSON).
    # Used by intent URL routing to validate that a pasted URL really refers to
    # a configured repo — a same-named repo under a different owner must be
    # rejected, not silently run against the local checkout. When an alias is
    # absent here, the checkout's `git remote get-url origin` is the fallback
    # authority (resolved lazily, cached per process).
    repo_full_names: dict[str, str] = {}

    # MCP server (mcp_server.py) — read-only surface for Claude Code / Codex.
    # The allowlist defaults to just `default_repo` (least privilege); extra
    # repos must be named explicitly. mcp_report_max_bytes caps a get_result
    # page so a report is never dumped unbounded over the stdio protocol.
    mcp_repo_allowlist: list[str] = []
    mcp_report_max_bytes: int = 65536

    # Shared, human-curated knowledge base — vendored from the community docs
    # (see doc/KNOWLEDGE.md), organized as general/ (cross-repo experience) +
    # repos/<repo>/ (repo-specific). Adapters reference only their repos/<repo>/
    # slice (manifest `knowledge.repo_subdir`); general/ is shared across all
    # repos. knowledge_general_docs is the always-on general slice; every deeper
    # doc is reachable on demand via doc_search/doc_read.
    knowledge_dir: Path = _REPO_ROOT / "knowledge"
    knowledge_general_docs: list[str] = ["general/_index.md"]

    # Engine
    run_root: Path = Path.home() / ".infermatrix-copilot" / "runs"
    max_step_retries: int = 1
    max_agent_iters: int = 40
    playbooks_dir: Path = _REPO_ROOT / "playbooks"
    adapters_dir: Path = _REPO_ROOT / "adapters"

    # Push safety — dry-run by default; protected branches never force-pushed.
    allow_push: bool = False
    allow_post: bool = False  # outward writes (PR comments / issue replies) dry-run by default
    protected_branches: list[str] = ["main"]

    # PR debug
    buildkite_api_token: str = ""
    pr_debug_max_groups: int = 6

    # External locked rebase pipeline (the existing 5-phase orchestrator)
    rebase_orchestrator_cmd: str = "omni-rebase-orchestrator --dry-run"
    # Sibling checkout by default, derived from this file's location — never a
    # hardcoded machine path. Override with REBASE_AGENT_ROOT if it lives elsewhere.
    rebase_agent_root: Path = _REPO_ROOT.parent / "vllm-omni-rebase-agent"
    rebase_poll_interval: int = 30

    # Repo profiles (design v2 §V2.3)
    profile_stale_days: int = 90        # dormancy window for unconfirmed facts
    profile_briefing_enabled: bool = True  # =0: the {no-profile} ablation arm
                                        # (§V2.3.5) — briefing + review.md
                                        # injection off, machine channel stays

    # Agent-step runtime (engine/agent_runtime/)
    review_max_iters: int = 12          # tool-loop budget for agent steps
    skills_dir: Path = _REPO_ROOT / "skills"
    memory_db: Path = Path.home() / ".infermatrix-copilot" / "debug_memory.db"
    evidence_item_chars: int = 24000  # was 6000: starving lenses pushed them
                                      # to re-read full files as per-lens tool
                                      # results — uncached tokens x n_lenses;
                                      # evidence lives ONCE in the shared
                                      # cached prefix instead
    evidence_caps: dict[str, int] = {"pr_diff": 120_000, "issue_text": 30_000,
                                     "pr_context": 15_000}     # per-item cap; full text archived to run dir
    # PR context bundle (W1): description/discussion/linked issues fed to the
    # reviewer. "no_discussion" excludes comments/review threads — REQUIRED for
    # eval arms (the frozen dataset's ground truth IS the review discussion;
    # PR_CONTEXT_MODE=no_discussion keeps candidate inputs baseline-equivalent).
    pr_context_mode: Literal["full", "no_discussion"] = "full"
    skills_top_k: int = 3

    # Ensemble agent steps (run_agent_step_ensemble): perspective-diverse
    # fan-out + verify-and-merge — trades tokens for run-to-run robustness.
    review_ensemble: bool = True        # pr-review uses the lens ensemble
    ensemble_parallel: bool = True      # lenses are independent — run concurrently
    ensemble_samples_per_lens: int = 1  # >1 buys union recall at ~linear cost;
                                        # measured: 2x cost, no recall gain (eval iter-3)
    ensemble_zero_yield_retry: bool = True  # one single-lens re-ask on an
                                        # empty candidate list (T3 #6)
    ensemble_stagger_seconds: float = 8.0  # head start for lens 0 so the
                                        # shared prompt prefix is cached
                                        # before sibling lenses send it
    ensemble_lens_max_iters: int = 10  # rounds are ~3x cheaper with windowed
                                       # reads; 6 starved lenses into paging
                                       # death (and 38/40 truncated at T0)    # per-lens tool budget — replicate means
                                        # dropped when this was cut to 4 (recall
                                        # starvation); 6 is the measured setting
    ensemble_merge_evidence_chars: int = 60_000  # must fit the pr_diff — a
                                        # reducer that can't see the diff
                                        # can't verify (T3 forensics #5)

    # Adaptive review depth (hybrid planner, review/planner.py): deterministic
    # rules decide the clear cases in pure code; only the gray middle zone
    # spends one small LLM call, and that call can pick standard/full but
    # never light. review_ensemble=False stays the hard kill-switch (single
    # pass, no planner — beats even a forced "full"). Per-run override:
    # --task-param review_depth=... / MCP start_review(review_depth=...).
    review_depth: Literal["auto", "light", "standard", "full"] = "auto"
    review_light_max_files: int = 3   # light ceiling (with lines below):
    review_light_max_lines: int = 80  #   at/under, with no API/default or
                                      #   risk signals -> one-pass review
    review_light_max_iters: int = 12  # light-pass tool budget — the token
                                      #   bound for small PRs. The solo pass
                                      #   sweeps the WHOLE checklist that four
                                      #   10-iter lenses split: 8 starved it
                                      #   into a forced block on a real 60-line
                                      #   PR (5156: cut at 11 tool calls)
    review_planner_model: str = ""    # gray-zone planner; empty -> the run's
                                      #   tier model (model_for(mode))

    # Mixture-of-Agents (design W6; JSON in LLM_MIXTURE, single-quoted in .env).
    # Schema: {"members": [{"model": str, "base_url"?: str, "api_key_env"?: str
    # (NAMES an env var — the secret-reference mechanism; raw "api_key" accepted
    # but discouraged)], "aggregator"?: <member>, "layers"?: 1}. Malformed JSON
    # degrades to {} (MoA off) — this optional feature must never take down the
    # copilot. Members whose model has no MODEL_PRICES entry are rejected at
    # parse (the budget cap must stay enforceable). Member identity in traces
    # is model@host only; keys are never logged.
    llm_mixture: Annotated[dict, NoDecode] = {}
    moa_when: Literal["off", "full", "performance", "always"] = "full"
    moa_member_timeout_s: float = 240.0  # per-request HTTP timeout ceiling
    moa_deadline_s: float = 480.0        # overall fan-out deadline; each request
                                         #   timeout = min(member, remaining)
    moa_max_usd: float = 1.50            # per-run MoA spend cap (reservations)
    moa_max_members: int = 4

    @field_validator("model_aliases", mode="before")
    @classmethod
    def _parse_aliases(cls, v):
        """Strictly parse MODEL_ALIASES env JSON: malformed ⇒ ValueError (this
        is a guard-policy surface — a silently-dropped alias would turn a
        legitimate equivalence into a run-killing mismatch, or vice versa)."""
        import json as _json

        if isinstance(v, dict):
            return v
        if not (isinstance(v, str) and v.strip()):
            return {}
        obj = _json.loads(v)  # raises on malformed — never tolerated here
        if not isinstance(obj, dict) or not all(
                isinstance(k, str) and isinstance(val, str)
                for k, val in obj.items()):
            raise ValueError("MODEL_ALIASES must be a JSON object of "
                             "string->string equivalences")
        return obj

    @model_validator(mode="after")
    def _validate_tier_atomicity(self):
        """Reject partial tier backends at startup: URL or key alone could pair
        the shared credential with a tier host (or the reverse)."""
        for tier in ("eco", "performance"):
            model = getattr(self, f"{tier}_model")
            url = getattr(self, f"{tier}_base_url")
            key = getattr(self, f"{tier}_api_key")
            if (url or key) and not (url and key and model):
                raise ValueError(
                    f"partial {tier} backend: {tier.upper()}_BASE_URL, "
                    f"{tier.upper()}_API_KEY and {tier.upper()}_MODEL must be "
                    "set together (or the URL/key both left unset to inherit "
                    "the shared ANTHROPIC_* backend)")
        return self

    @field_validator("llm_mixture", mode="before")
    @classmethod
    def _parse_mixture(cls, v):
        """Tolerantly parse LLM_MIXTURE env JSON: malformed ⇒ {} (MoA off)."""
        import json as _json

        if isinstance(v, dict):
            return v
        try:
            obj = _json.loads(v) if isinstance(v, str) and v.strip() else {}
            return obj if isinstance(obj, dict) else {}
        except (ValueError, TypeError):
            import logging

            logging.getLogger("infermatrix_copilot").warning(
                "ignoring malformed LLM_MIXTURE JSON — MoA stays off")
            return {}

    # Patch-review trigger thresholds
    large_diff_lines: int = 400
    large_diff_files: int = 8
    high_risk_modules: list[str] = ["worker_runner", "model_executor", "scheduler"]

    # Metrics (eval/METRICS_RESEARCH.md) — per-run metrics.json: CATQ = Q·S/C.
    # Reference budgets are EXPLICIT deployment assumptions (RQS3e precedent):
    # at the ref cost the log discount is ~23%; raise a ref where that
    # resource is nearly free in your deployment.
    metrics_enabled: bool = True
    token_price_in_per_mtok: float = 0.0   # 0 -> metrics.MODEL_PRICES table
    cache_read_price_factor: float = 0.0   # 0 -> provider default (0.1x input)
    token_price_out_per_mtok: float = 0.0
    ci_rate_usd_per_min: float = 0.0       # billed CI $/min, folded into usd
    cost_ref_usd: dict[str, float] = {
        "default": 1.0, "pr_review": 1.0, "pr_debug": 3.0, "pr_rebase": 3.0,
        "repo_rebase": 10.0, "issue_answer": 0.30, "issue_filter": 0.10,
    }
    cost_ref_min: dict[str, float] = {
        "default": 10.0, "pr_review": 10.0, "pr_debug": 30.0, "pr_rebase": 30.0,
        "repo_rebase": 240.0, "issue_answer": 5.0, "issue_filter": 2.0,
    }

    # Escalation email
    notify_email: str = ""
    resend_api_key: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    @property
    def reviewer(self) -> str:
        """The reviewer model, falling back to `agent_model` when unset."""
        return self.reviewer_model or self.agent_model

    @property
    def intent(self) -> str:
        """The intent-classification model, falling back to `agent_model`."""
        return self.intent_model or self.agent_model

    def tier_target(self, mode: str, role: str = "agent") -> ResolvedTarget:
        """Central tier→backend resolution (双路径, plan v2): the ONLY place a
        tier's model is paired with an endpoint and credential. `eco` (the
        default) -> `eco_model` or `agent_model` on the eco backend (or the
        shared one); `performance` with no `performance_model` raises
        `TierNotConfiguredError` — failing upfront replaced the silent
        agent_model fallback that once mislabeled a whole run."""
        if mode == "performance":
            if not self.performance_model:
                raise TierNotConfiguredError(
                    "performance tier is not configured — set PERFORMANCE_MODEL "
                    "in .env (plus PERFORMANCE_BASE_URL + PERFORMANCE_API_KEY "
                    "for an independent backend), or run without requesting "
                    "the high-performance model")
            if self.performance_base_url:
                return ResolvedTarget(role, self.performance_model,
                                      self.performance_base_url,
                                      self.performance_api_key,
                                      "tier:performance")
            return ResolvedTarget(role, self.performance_model,
                                  self.anthropic_base_url,
                                  self.anthropic_api_key, "global")
        model = self.eco_model or self.agent_model
        if self.eco_base_url:
            return ResolvedTarget(role, model, self.eco_base_url,
                                  self.eco_api_key, "tier:eco")
        return ResolvedTarget(role, model, self.anthropic_base_url,
                              self.anthropic_api_key, "global")

    def model_for(self, mode: str) -> str:
        """The agent-reasoning model name for an execution tier — delegates to
        `tier_target` (same upfront failure for an unconfigured performance
        tier; no silent fallback)."""
        return self.tier_target(mode).model

    @property
    def mcp_allowed_repos(self) -> list[str]:
        """Effective MCP repo allowlist: the configured list, or `[default_repo]`
        when unset (least privilege — never every installed adapter)."""
        return list(self.mcp_repo_allowlist) or [self.default_repo]

    def repo_path(self, name: str) -> Path | None:
        """The configured filesystem path for repo `name`, or None if unknown."""
        p = self.repo_paths.get(name)
        return Path(p) if p else None
