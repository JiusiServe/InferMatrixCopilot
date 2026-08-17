# cli/ — spec

<!-- verified-against: 2026-08-17 -->

`LOC ~1000 across 5 files · interface + orchestration façade · refactor-status: ok`

## Responsibility
The flag CLI and the `Copilot` façade: resolve → gate → execute; own the run
directory, RunTrace, notifier, and metrics wiring. Formerly one 406-line module;
now a package that separates the argparse/REPL wiring from the orchestrator.

## Package layout (one concern per file)
- `__init__.py` — re-exports `Copilot`, `main` (surface below); no logic.
- `__main__.py` — `python -m infermatrix_copilot.cli` parity.
- `copilot.py` — the `Copilot` orchestrator (resolve/run_task/run_playbook/
  run_queue/resume_last/_execute + built-ins).
- `entry.py` — `argparse`, `_handle_line`, `main` (turns argv/stdin into calls
  on `Copilot`).
- `utils.py` — pure formatters: `parse_task_params`, `format_metrics_line`.
- `doctor.py` — preflight diagnostics (added 2026-07): per-item ✓/✗ with a
  single exact fix command per failure.

## Public contract (importable from `infermatrix_copilot.cli`)
`main(argv)`; `Copilot` (`resolve`, `run_task`, `run_playbook`, `run_queue`,
`resume_last`, `status`, `logs`, `playbooks`, `_execute`, `_adapter_for`,
`_resolve_repo_path`). The re-exporting `__init__` keeps `infermatrix_copilot.cli:main`
(entry point) and `from infermatrix_copilot.cli import Copilot` unchanged.

## Invariants
- `resolve` feeds capabilities (adapter + REPO_PATHS) to the planner.
- Plan-review gate before confirm; confirm fires for
  `confirm_required or requires_review` unless `--yes` (`_gate_and_confirm`, K6).
- `_execute` is the single execution path (task / explicit-playbook / resume).
- Repo knowledge (protected branches, high-risk modules) comes from the adapter
  into run state (**A5**); blocked → exit 3 (`BLOCKED_EXIT`).
- `--playbook` is the only way to run a candidate.
- **`doctor` is read-only and never prints a secret's value** — only its name.
  It makes no paid LLM call unless `--probe` is passed, which is the single
  paid check (one token per configured tier). `--json` serves CI, and exiting
  non-zero when credentials are absent is the EXPECTED state there.
- **`--performance` is the only way to raise the model tier**; the default is
  `eco`. Raising the tier never widens permissions (`tier` stays derived from
  `kind`).
- The CLI main path gates **before** creating a run directory, so an abandoned
  plan leaves nothing behind. The MCP reservation shape (create, then plan) is
  deliberately different — see `mcp_server.md`.

## Scope — not here
No step logic, no repo-knowledge literals, no LLM prompts. Orchestration wiring
only.

## Dependencies (allowed)
`engine/*`, `playbooks/*`, `intent`, `task_spec`, `adapters/base`,
`push`, `review/reviewer`, `notify`, `run_trace`, `config`, `ui`,
`chat`. MUST NOT be imported by any lower layer (**§ARCH.4.2**).

## Extension points
New REPL command → `_handle_line` (entry.py); new run wiring → `_execute`
(copilot.py); new pure formatter → utils.py.

## Tests
`test_cli.py`, `test_phase_b.py`, `test_chat.py`, `test_ui.py`.

## Refactor notes
Split **applied** (was a cohesion-split candidate). The `Copilot` class stays
whole in `copilot.py` so the resolve→execute flow is followed in one file; only
the argparse/REPL front-end (`entry.py`) and the two pure formatters (`utils.py`)
moved out. K6 (`_gate_and_confirm`) is done and lives on the class.
