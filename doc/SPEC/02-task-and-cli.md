# 02 — Task Layer & Interfaces

Modules: `task_spec.py`, `intent.py`, `cli.py`, `chat.py`, `ui.py`, `config.py`.

---

## `task_spec.py`

- **Responsibility** — define `TaskSpec`, the structured product of intent
  parsing, and derive its permission tier from the task kind.
- **Public contract** — `TaskSpec(kind, repo, pr?, issue?, report_only, post,
  params)`; properties `tier` (L0/L1/L2), `read_only`, `confirm_required`,
  `describe()`. Constants `TaskKind` (7 kinds), `READ_ONLY_KINDS`, `KIND_TIER`.
- **Invariants** — **C1**: no settable tier field; `tier = KIND_TIER[kind]`.
  `read_only` for a read-only kind is `not post`; for others it is `report_only`.
  `confirm_required = not read_only`.
- **Scope** — pure data + derivation. No parsing, no I/O, no execution.
- **Depends on** — `pydantic` only.
- **Extension points** — a new kind: add to `TaskKind` and `KIND_TIER` (and
  `READ_ONLY_KINDS` if applicable). Nothing else in this file changes.
- **Tests** — `test_intent_taskspec.py`.

## `intent.py`

- **Responsibility** — parse one NL command into a `TaskSpec`, or a clarifying
  question; split compound commands into an ordered list.
- **Public contract** — `parse_intent(text, llm?, default_repo, model?)
  -> IntentResult`; `parse_intents(...)` for compound commands (carries the
  prior segment's PR/issue). `IntentResult(spec?, clarify)`.
- **Invariants** — deterministic parse first, LLM fallback second, **clarify on
  ambiguity — never guess** (low confidence / injection-looking → clarify). Only
  terminal input reaches here (**C7**). Guards: a `pr_*` kind needs a PR number;
  `repo_*` kinds refuse when a PR is present.
- **Scope** — text → TaskSpec only. No execution, no planning; MUST NOT read the
  repo or the network.
- **Depends on** — `llm.py`, `task_spec.py`.
- **Extension points** — a new kind: add a `_KIND_HINTS` row and, if it takes a
  target, the matching guard; extend the LLM system prompt's kind list.
- **Tests** — `test_intent_taskspec.py`,
  `test_profile_steps.py::test_intent_parses_profile_command`.

## `cli.py`

- **Responsibility** — the flag CLI and the `Copilot` façade: resolve → gate →
  execute; own the run directory, RunTrace, notifier, and metrics wiring.
- **Public contract** — `main(argv)`; `Copilot.resolve/run_task/run_playbook/
  run_queue/resume_last/status/logs/playbooks`. `_execute` is the single
  execution entry (used by task, explicit-playbook, and resume paths).
- **Invariants** — `resolve` feeds capabilities from the repo plugin + REPO_PATHS
  to the planner. Confirm gate fires for `confirm_required or requires_review`
  unless `--yes`. Plan-review gate runs before confirmation. Blocked → exit 3
  (`BLOCKED_EXIT`). `--playbook` is the only way to run a candidate. Repo
  knowledge (protected branches, high-risk modules) comes from the plugin into
  run state (**A5**).
- **Scope** — orchestration wiring only. No step logic, no repo knowledge
  literals, no LLM prompts.
- **Depends on** — `engine/*`, `playbooks/*`, `intent.py`, `task_spec.py`,
  `plugins/base.py`, `targets/base.py`, `review/reviewer.py`, `notify.py`,
  `run_trace.py`, `config.py`, `ui.py`, `chat.py`.
- **Extension points** — new built-in REPL command → `_handle_line`; new run
  wiring → `_execute`.
- **Tests** — `test_cli.py`, `test_phase_b.py`.

## `chat.py`

- **Responsibility** — the Claude-Code-style conversational REPL (default when
  an LLM is configured).
- **Public contract** — `chat_repl(copilot, assume_yes, handle_builtin)`;
  `ChatSession.turn`. Tools: `run_task`/`run_playbook` (same TaskSpec/planner/
  confirm path), `get_status`/`get_logs`/`read_run_report`/`list_playbooks`,
  `repo_read`/`repo_grep`, `resume_run`.
- **Invariants** — chat is a **frontend, not a second execution path**: it
  cannot widen permissions; it funnels into `run_task`/`run_playbook` with the
  same gates. `repo_read`/`repo_grep` are jailed to configured repo roots + run
  root; `.env*` refused. Fetched GitHub content stays data (handled inside
  steps). The system prompt is repo-neutral (interpolates `default_repo`).
- **Scope** — presentation + tool round-trips. No planning/execution logic of
  its own.
- **Depends on** — `cli.Copilot` (TYPE_CHECKING), `run_trace.py`, `task_spec.py`,
  `ui.py`.
- **Tests** — `test_chat.py`.

## `ui.py`

- **Responsibility** — terminal rendering (streaming, spinners, markdown,
  color); degrade to plain text on non-TTY/pipes.
- **Invariants** — presentation only; carries no control flow or state.
- **Scope** — no business logic. Anything that decides *what* to do belongs
  above; `ui.py` only decides *how it looks*.
- **Tests** — `test_ui.py`.

## `config.py`

- **Responsibility** — `Settings` (pydantic-settings) from env / `.env`.
- **Public contract** — one `Settings` with typed fields + defaults; helpers
  `reviewer`, `intent`, `repo_path(name)`.
- **Invariants** — secrets only via env/`.env` (git-ignored, never committed).
  Repo-specific defaults here (`default_repo`, `rebase_agent_root`,
  `high_risk_modules`) are **fallbacks only** — the plugin/profile overrides them
  (**A5**; these fallbacks are the sole allowed repo literals in this file, capped
  by the leak test).
- **Scope** — configuration surface only. No logic beyond derivation helpers.
- **Extension points** — a new tunable → a typed field with a safe default and a
  one-line comment stating its meaning/units.
