"""Settings loaded from environment / .env (never committed)."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
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
    llm_max_tokens: int = 8000

    # Repos
    default_repo: str = "vllm-omni"
    repo_paths: dict[str, str] = {}

    # Engine
    run_root: Path = Path.home() / ".omni-copilot" / "runs"
    max_step_retries: int = 1
    max_agent_iters: int = 40
    playbooks_dir: Path = _REPO_ROOT / "playbooks"
    plugins_dir: Path = _REPO_ROOT / "plugins"

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

    # Agent-step runtime (engine/agent_runtime.py)
    review_max_iters: int = 12          # tool-loop budget for agent steps
    skills_dir: Path = _REPO_ROOT / "skills"
    memory_db: Path = Path.home() / ".omni-copilot" / "debug_memory.db"
    evidence_item_chars: int = 6000     # per-item cap; full text archived to run dir
    skills_top_k: int = 3

    # Ensemble agent steps (run_agent_step_ensemble): perspective-diverse
    # fan-out + verify-and-merge — trades tokens for run-to-run robustness.
    review_ensemble: bool = True        # pr-review uses the lens ensemble
    ensemble_parallel: bool = True      # lenses are independent — run concurrently
    ensemble_samples_per_lens: int = 1  # >1 buys union recall at ~linear cost;
                                        # measured: 2x cost, no recall gain (eval iter-3)
    ensemble_lens_max_iters: int = 6    # per-lens tool budget — replicate means
                                        # dropped when this was cut to 4 (recall
                                        # starvation); 6 is the measured setting
    ensemble_merge_evidence_chars: int = 35_000

    # Patch-review trigger thresholds
    large_diff_lines: int = 400
    large_diff_files: int = 8
    high_risk_modules: list[str] = ["worker_runner", "model_executor", "scheduler"]

    # Escalation email
    notify_email: str = ""
    resend_api_key: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    @property
    def reviewer(self) -> str:
        return self.reviewer_model or self.agent_model

    @property
    def intent(self) -> str:
        return self.intent_model or self.agent_model

    def repo_path(self, name: str) -> Path | None:
        p = self.repo_paths.get(name)
        return Path(p) if p else None
