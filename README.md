# vllm-omni-copilot

Playbook-driven repo-maintenance copilot for [vLLM-Omni], implementing the
architecture in `vllm-omni-rebase-agent/docs/copilot/copilot_design`
(3-layer RepoPlugin / Target / Engine, Step abstraction, dynamic pipelines with
reuse > adapt > generate, conversational CLI). See [doc/DESIGN.md](doc/DESIGN.md).

## Layout

```
src/omni_copilot/   implementation (engine, playbooks, plugins, review, memory, CLI)
test/               pytest suite (no GPU, no network, no API key needed)
doc/                design + implementation status
playbooks/          registered playbooks (repo-rebase is LOCKED)
plugins/            repo plugins (plugin zero: vllm_omni)
```

## Install & test

```bash
pip install -e .
pytest                      # 49 tests, all offline
cp .env.template .env       # fill in keys; .env is git-ignored, NEVER commit it
```

## Use

```bash
omni-copilot                              # REPL: natural-language commands
omni-copilot -p "rebase the repo" --plan-only
omni-copilot -p "debug the CI of pr 2744, report only"
omni-copilot -p "review pr 4830" --yes
```

Built-ins inside the REPL: `/status`, `/logs [n]`, `/playbooks`, `/quit`.

Natural language is parsed into a **TaskSpec** (kind, PR/issue, flags) and echoed
back; write/push-capable tasks require confirmation; ambiguous commands get a
clarifying question, never a guessed execution. The planner then resolves
**reuse > adapt > generate**:

- `repo_rebase` → the **locked** `repo-rebase` playbook, run verbatim (L0). It
  delegates to the proven 5-phase orchestrator (`REBASE_ORCHESTRATOR_CMD`).
- `pr_rebase` / `pr_debug` → vetted playbooks, parameterized (L1).
- `pr_review` / `issue_answer` / `issue_filter` → generated read-only plans
  (L2), plan-review gated; generation is structurally barred from write/push steps.

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
  root-cause + verification fields; skills/playbooks/plugins are
  candidate-then-promote (high-risk plugin sections are human-only).
