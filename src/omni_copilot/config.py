"""Settings loaded from environment / .env (never committed)."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[2]


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
    performance_model: str = ""  # empty -> agent_model (high-capability path)
    llm_max_tokens: int = 16000  # 8k truncated verbose lens replies mid-JSON

    # Repos
    default_repo: str = "vllm-omni"
    repo_paths: dict[str, str] = {}

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
    run_root: Path = Path.home() / ".omni-copilot" / "runs"
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
    rebase_agent_root: Path = Path("/rebase/vllm-omni-rebase-agent")
    rebase_poll_interval: int = 30

    # Repo profiles (design v2 §V2.3)
    profile_stale_days: int = 90        # dormancy window for unconfirmed facts
    profile_briefing_enabled: bool = True  # =0: the {no-profile} ablation arm
                                        # (§V2.3.5) — briefing + review.md
                                        # injection off, machine channel stays

    # Agent-step runtime (engine/agent_runtime/)
    review_max_iters: int = 12          # tool-loop budget for agent steps
    skills_dir: Path = _REPO_ROOT / "skills"
    memory_db: Path = Path.home() / ".omni-copilot" / "debug_memory.db"
    evidence_item_chars: int = 24000  # was 6000: starving lenses pushed them
                                      # to re-read full files as per-lens tool
                                      # results — uncached tokens x n_lenses;
                                      # evidence lives ONCE in the shared
                                      # cached prefix instead
    evidence_caps: dict[str, int] = {"pr_diff": 120_000, "issue_text": 30_000}     # per-item cap; full text archived to run dir
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

    def model_for(self, mode: str) -> str:
        """The agent-reasoning model for an execution tier (双路径):
        `performance` -> the high-capability model (`performance_model`, falling
        back to `agent_model`); anything else (`eco`, the default) -> the
        cost-effective model (`eco_model`, falling back to `agent_model`)."""
        if mode == "performance":
            return self.performance_model or self.agent_model
        return self.eco_model or self.agent_model

    @property
    def mcp_allowed_repos(self) -> list[str]:
        """Effective MCP repo allowlist: the configured list, or `[default_repo]`
        when unset (least privilege — never every installed adapter)."""
        return list(self.mcp_repo_allowlist) or [self.default_repo]

    def repo_path(self, name: str) -> Path | None:
        """The configured filesystem path for repo `name`, or None if unknown."""
        p = self.repo_paths.get(name)
        return Path(p) if p else None
