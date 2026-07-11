# vllm-omni-copilot

Playbook-driven repo-maintenance copilot for [vLLM-Omni], implementing the
architecture in `vllm-omni-rebase-agent/docs/copilot/copilot_design`
(3-layer RepoAdapter / Target / Engine, Step abstraction, dynamic pipelines with
reuse > adapt > generate, conversational CLI). See [doc/DESIGN.md](doc/DESIGN.md);
new readers: start with the code walkthrough in [doc/CODE_TOUR.md](doc/CODE_TOUR.md).
The normative per-layer specification (contracts, invariants, constraints) is
in [doc/SPEC/](doc/SPEC/README.md).

## Layout

```
src/omni_copilot/   implementation (engine, playbooks, adapters, review, memory, CLI)
test/               pytest suite (no GPU, no network, no API key needed)
doc/                design + implementation status
playbooks/          registered playbooks (repo-rebase is LOCKED)
adapters/            repo adapters (adapter zero: vllm_omni)
```

## Install & test

```bash
pip install -e .
pytest                      # 49 tests, all offline
cp .env.template .env       # fill in keys; .env is git-ignored, NEVER commit it
```

## Use

```bash
omni-copilot                              # conversational chat (Claude-Code-style)
omni-copilot --no-chat                    # deterministic command REPL instead
omni-copilot -p "rebase the repo" --plan-only
omni-copilot -p "debug the CI of pr 2744, report only"
omni-copilot -p "review pr 4830" --yes
omni-copilot -p "rebase pr 4830, then review it"   # compound -> ordered queue
omni-copilot --resume                     # re-enter the last run's first incomplete step
```

Built-ins inside the REPL: `/status`, `/logs [n]`, `/playbooks`, `/resume`, `/quit`.

**Chat mode** (default when an LLM is configured): a persistent conversation with
streaming replies and full terminal chrome — session banner, spinner while
thinking, live streaming tail that resolves into markdown-rendered replies
(tables, headers, bold), color-coded tool calls and step results, and
arrow-key input history (`~/.omni-copilot/history`). Everything degrades to
plain text on pipes/non-TTY, so scripting output stays stable. The model answers questions about the repo and past runs,
and executes work through tools — `run_task`/`run_playbook` (same TaskSpec,
planner, and [y/N] confirmation path as the flag CLI; chat can never widen
permissions), `get_status`/`get_logs`/`read_run_report`, and `repo_read`/
`repo_grep` jailed to the configured repos (secret files refused). Sessions are
traced to `~/.omni-copilot/sessions/`. One-shot `-p` keeps the deterministic
parser (cheap, scriptable).

Natural language is parsed into a **TaskSpec** (kind, PR/issue, flags) and echoed
back; write/push-capable tasks require confirmation; ambiguous commands get a
clarifying question, never a guessed execution. The planner then resolves
**reuse > adapt > generate**:

- `repo_rebase` → the **locked** `repo-rebase` playbook, run verbatim (L0). It
  delegates to the proven 5-phase orchestrator (`REBASE_ORCHESTRATOR_CMD`),
  **monitored**: per-phase/per-module progress streams from the parent's
  state.json into `/status` and the run trace, failures are classified and
  escalated with artifacts, and `/resume` maps onto the parent's `--resume`.
  A native decomposition (`repo-rebase-native`, candidate) wraps the parent
  package's own phase wrappers + per-module agents as copilot steps — run it
  explicitly with `--playbook repo-rebase-native` for side-by-side validation;
  see `doc/IMPLEMENTATION_STATUS.md` for the promotion path.
- `pr_rebase` / `pr_debug` → vetted playbooks (L1): fork-aware checkout,
  rebase with agent conflict resolution (abort+escalate without an LLM),
  per-module verification, signature-grouped CI debugging — force-with-lease
  only for the rebased PR head, strictly additive pushes for debug fixes.
- `pr_review` / `issue_answer` / `issue_filter` → vetted read-only playbooks;
  posting needs the explicit `post` intent AND `ALLOW_POST=1` (dry-run otherwise).
  Kinds without a vetted playbook fall back to generated plans (L2), plan-review
  gated; generation is structurally barred from write/push steps.

## Safety posture

- **Push guard**: single choke point — pushes need an allowing `PushPolicy`,
  are dry-run unless `ALLOW_PUSH=1`, force is only `--force-with-lease`, and
  protected branches (`main`) are never pushed to, policy or not.
- **ToolScope/PathScope**: agent tool calls pass one scope-enforcing dispatcher;
  pre-plan scopes can only write the plan dir; out-of-scope edits execute but
  are recorded, never silent.
- **Conditional Patch Review**: cheap diff summary always; LLM diff review on
  risk triggers (out-of-scope, large diff, no tests, full-file rewrite,
  pre-push, knowledge edits) — fail-closed when no reviewer is available.
- **Escalation**: blocked runs write `ESCALATION.md`, email if configured, and
  exit 3 — notify, never guess.
- **Memory governance**: RunTrace records everything; debug memories require
  root-cause + verification fields; skills/playbooks/adapters are
  candidate-then-promote (high-risk adapter sections are human-only).
