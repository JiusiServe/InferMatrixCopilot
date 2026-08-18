# RFC — Provider registry: subscription-auth harness backends for Strict

- Status: accepted (grilling session 2026-08-14); M1 (registry, api
  parity, tool bridge, cursor transport) merged in PR #81 and live-smoked;
  M2 claude-code and M3 codex implemented on this branch — claude-code
  live-smoked on subscription auth, codex offline-tested only (no ChatGPT
  login on the dev machine; readiness reports the login gap). The bridge
  additionally serves the on-demand `repo_map`; skill/memory search tools
  remain in-process only (cross-process candidate writes deliberately not
  opened).
- Owner: LLM/backend layer (`llm.py`, `config.py`), agent runtime
  (`engine/agent_runtime/runner.py`), new `src/infermatrix_copilot/providers/`
- Prior art studied: Hermes Agent `api_mode` transports
  (hermes-agent.nousresearch.com/docs/developer-guide/adding-providers) ·
  opencode provider registry (opencode.ai/v2/docs/providers)

## Motivation

Strict mode runs the full execution spine, and every model call goes through
`llm.py::LLM` — a raw Anthropic/OpenAI-compatible completions client that
requires `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`. Users whose only model
access is a coding-agent subscription (Claude Code Pro/Max, ChatGPT plan for
Codex CLI, Cursor) cannot run Strict at all.

Claude Code, Codex CLI and cursor-agent expose no raw completions API on
subscription auth — they are *agent harnesses* that own their tool loop. So
the plug-in point cannot be `LLM.create()` (stateless
`system+messages+tools → tool_use` round trips); it has to sit one level up,
where a whole agent step is delegated.

Hermes solves the adjacent problem with an `api_mode` transport abstraction
(canonical internal message shape; per-mode adapters for request building,
response normalization, usage extraction; one standardized runtime-resolution
record). This codebase is already half-way there: the Anthropic block
protocol is our canonical shape, `_openai_messages()` is a transport adapter,
and `Settings.tier_target()` → `ResolvedTarget` is runtime resolution. This
RFC formalizes that into a provider registry and adds the axis Hermes only
needed for its out-of-process Codex path: **transport kind** (`api` vs
`harness`).

## Decisions (locked with the maintainer, 2026-08-14)

1. **Purpose: product reach.** Strict on subscription auth for users without
   raw API keys. Fidelity is best-effort per harness and labeled per run.
   Eval/campaign tables are unaffected — a harness backend measures
   loop+model and is *never* pooled into generator-ablation tables (standing
   rule: generator arms ride our pipeline with only the model swapped).
2. **Explicit selection, hard error.** A `.env` key selects the backend. For
   a Strict run with no selected backend the server errors upfront with the
   exact missing item (same philosophy as `TierNotConfiguredError` /
   `strict_readiness`). No auto-detection, no silent fallback.
3. **Tools bridged, preventive-first.** Harness sessions get the copilot's
   own tools over MCP, every call passing `tools.dispatch`
   (ToolScope/PathScope choke point preserved). Vendor built-ins are
   disabled where the harness supports it; cursor-agent additionally gets
   the productized post-run audit (defense in depth), with the control class
   disclosed in RUN_REPORT.
4. **Unified registry.** The existing API path becomes provider `api` under
   the same registry — one resolution path, one trace vocabulary. Parity
   ratchet: with provider `api`, behavior is byte-identical and the existing
   test suite is the gate.
5. **Phasing: cursor-agent first**, then Claude Code, then Codex.

## Design

### Vocabulary

- **provider id** — registry key and the value of the selection config:
  `api`, `cursor`, `claude-code`, `codex`.
- **kind** — `api` (stateless completions; implements `complete`) or
  `harness` (owns a tool loop; implements `run_session` + one-shot
  `complete`).
- **api_mode** — the wire protocol *within* the `api` provider:
  `anthropic_messages` | `chat_completions`. This is exactly today's
  `Settings.resolved_llm_provider`; the term "provider" in existing code
  (`llm_provider`, `ResolvedTarget.provider`) keeps meaning the API vendor
  protocol and maps onto api_mode unchanged.

### Package layout

```
src/infermatrix_copilot/providers/
  __init__.py     re-exports; register_builtin_providers()
  base.py         ProviderSpec + Transport protocol + session dataclasses
  api.py          provider "api": wraps the existing LLM class (both
                  api_modes). Wrapper, not rewrite — LLM internals,
                  tier_target, served-model guard, tracing all unchanged.
  cursor.py       M1 harness transport (cursor-agent CLI)
  claude_code.py  M2 harness transport (claude -p)
  codex.py        M3 harness transport (codex exec)
  audit.py        post-run session audit (productized from
                  eval/dataset/run_cursor_arm.py)
  registry.py     PROVIDER_REGISTRY + resolve_provider(settings)
src/infermatrix_copilot/tool_bridge.py
                  stdio MCP server exposing the run's scoped tools
                  (entry: python -m infermatrix_copilot.tool_bridge)
```

### base.py — the contracts

```python
@dataclass(frozen=True)
class ProviderSpec:
    id: str                      # "api" | "cursor" | "claude-code" | "codex"
    kind: Literal["api", "harness"]
    display: str
    cli_names: tuple[str, ...] = ()      # binaries to probe (harness)
    capabilities: frozenset[str] = frozenset()
    # capability flags: "mcp_tools", "builtin_tools_off", "max_turns",
    # "system_prompt", "usage_reporting", "cost_reporting"

class Transport(Protocol):
    # api kind + tool-less harness calls; signature mirrors LLM.create
    def complete(self, *, system, messages, tools=None, model=None,
                 max_tokens=None, on_text=None, role="") -> Reply: ...
    # harness kind only: one whole agent step
    def run_session(self, req: AgentSessionRequest) -> AgentOutcome: ...

@dataclass
class AgentSessionRequest:
    system: str          # contract preamble (harnesses without a system-
    prompt: str          #   prompt channel prepend it to the prompt)
    scope: ToolScope
    bridge_spec_path: Path   # written by the runner; see tool bridge
    model: str
    max_iters: int       # mapped to --max-turns where supported, else
    timeout_s: float     #   wall-clock timeout + budget-discipline prompt
    run_dir: Path
```

`run_session` returns the existing `agent_loop.AgentOutcome` (text,
iterations, tool_calls, truncated, refusals, token usage, tools_used) so
everything downstream of the runner branch — `_coerce_output`, the
`agent_output` trace event, `_to_step_result` — is untouched. Fields a
harness cannot know (iterations) are best-effort; `tools_used` comes from
the bridge trace.

### Resolution — one place, extended

`ResolvedTarget` (config.py) gains two fields with defaults that keep every
existing construction site valid:

```python
provider_id: str = "api"
kind: Literal["api", "harness"] = "api"
```

`Settings.tier_target()` stays the only place model×endpoint×credential pair
up; when `strict_backend` selects a harness provider it returns a target
with that provider id/kind and the harness model (`STRICT_BACKEND_MODEL` or
the provider default) — base_url/api_key empty (subscription auth lives in
the harness CLI, never in our config). `LLM.for_target()` is only consulted
for `kind == "api"` targets.

Selection scope: `STRICT_BACKEND` is **required for Strict runs** — checked
in `CopilotMCP.strict_readiness()` (mcp_server.py:175, alongside the current
`shared_api_key` check, which becomes the `api`-provider readiness item) and
re-checked at `--execute-strict-reserved` startup in the child. The CLI path
(`run_task`) treats empty as `api` — no breaking change for maintainers —
and may grow a `--backend` flag later.

### Runner branch — the single integration point

In `run_agent_step` (engine/agent_runtime/runner.py:170), the current call

```python
outcome = await asyncio.to_thread(run_agent, step_llm, system=..., ...)
```

becomes a two-way branch on the resolved target's kind. `harness` targets
write the bridge spec (below) into the run dir and call
`provider.run_session(...)` in the same worker thread. Everything before the
branch (dispatch context, evidence pack, briefing, scope binding to the
PR-time worktree root, `agent_dispatch` trace) and everything after
(`_coerce_output` with its one repair round and escalation salvage,
`agent_output` trace, skill touch) is shared — the harness rides the exact
v13 prompt bundle and output contract.

Tool-less roles (review planner gray-zone call, ensemble reducer/merge,
coverage promotion, `_coerce_output` repair) go through a `HarnessLLM`
adapter implementing the `LLM.create()` signature: it raises if `tools` is
non-empty, runs a one-shot CLI invocation, and returns a normalized `Reply`
with usage from the CLI's JSON. Its `available` property mirrors doctor's
CLI probe so `run_agent_step`'s `ctx.llm.available` gate keeps working. For
cursor, one-shot completions run in an **empty scratch cwd** so native tools
have nothing to read.

MoA (`for_member`) rejects harness providers as mixture members in v1 — the
reservation ledger requires per-request pricing that subscription CLIs
cannot provide.

### The tool bridge — choke-point preservation

`python -m infermatrix_copilot.tool_bridge --spec <run_dir>/bridge/<step>.json`
is a stdio MCP server (FastMCP, already in the `[mcp]` extra) exposing
exactly the tools the step's scope allows. The spec file serializes:

- the `ToolScope` (frozen dataclass → JSON: name, allowed_tools, read_only,
  root, path_scope patterns) — trivially round-trippable;
- repo name + repo_path (the PR-time worktree), run_dir;
- which extra tool families to reconstruct (knowledge/doc/repo_map) — these
  are rebuilt in the bridge process from `Settings()` + the adapter, the
  same factories the runner uses (`_knowledge_tools`, `_repo_map_tool`,
  `_repo_docs_tool`).

Every MCP tool handler is a thin shim over `tools.dispatch(name, args,
scope=scope, trace=bridge_trace, extra=extra)` — refusals, out-of-scope
records, path resolution against the worktree root, and result bounding all
behave identically to the in-process loop. The bridge appends to
`bridge_trace.jsonl` in the run dir (its own file: append-only jsonl from a
second process must not interleave with the parent's `run_trace.jsonl`);
after the session the runner folds a summary (tool_calls, tools_used,
refusals) into the normal trace events.

Guard test (the exfiltration case): a bridged `read_file` of
`~/.infermatrix-copilot/.env` — outside the scope root — is refused and
traced.

### Environment sanitization — load-bearing

Harness subprocesses get a constructed allowlist env (PATH, HOME, TERM,
LANG/LC_*, PYTHON* as needed, plus provider-specific vars), **never**
`os.environ` passthrough. Concrete hazards on this very machine:

- our `.env` points `ANTHROPIC_BASE_URL` at a DeepSeek-compatible gateway —
  leaked into `claude`, subscription calls would route to the wrong endpoint
  and bill the wrong account;
- `ANTHROPIC_API_KEY`/`OPENAI_API_KEY` present in env would silently switch
  the CLIs from subscription auth to API billing;
- `CLAUDECODE`/host markers confuse nested-CC when the Strict host *is*
  Claude Code.

The Strict child itself already receives a curated env from the server
worker (mcp_server.py:100–115); the same discipline extends one level down.

### Guards and accounting

- **Served-model guard**: harness CLIs report the model used in their JSON
  output; recorded via the existing `llm.served` event with the same
  verdict logic (mismatch → fail per `MODEL_MISMATCH_POLICY`; absent →
  `unverified`, warn).
- **Usage/cost**: token counts parsed from CLI JSON (claude `-p
  --output-format json` includes usage + cost; codex `--json` emits token
  events; cursor stream-json includes usage). `metrics.py` records cost
  source `subscription` and does not consult `MODEL_PRICES` for harness
  providers — CATQ's C term must not fabricate USD.
- **Ensemble stagger** (`ensemble_stagger_seconds`) is disabled for harness
  targets: there is no shared prompt-cache prefix across CLI sessions to
  warm. Each delegated pass is one harness session, so context caching
  within the 32-iter deep pass is the harness's own concern.
- **Concurrency**: `STRICT_BACKEND_CONCURRENCY` (default 2) is a semaphore
  over concurrent sessions (deep passes + verify fan-out) — subscription
  rate windows are real; auth/limit errors surface as BLOCKED, never
  retried into a lockout.

### Config schema (.env)

```
STRICT_BACKEND=                # REQUIRED for Strict: api | cursor | claude-code | codex
STRICT_BACKEND_MODEL=          # model id inside the harness (optional)
STRICT_BACKEND_CONCURRENCY=2   # concurrent harness sessions
STRICT_BACKEND_CLI=            # binary path override (else PATH lookup)
STRICT_BACKEND_TIMEOUT_S=1800  # per-session wall-clock ceiling
```

Installer and `.env.template` write `STRICT_BACKEND=api` so existing setups
migrate with the file refresh; `strict_readiness` names the exact fix line
when it is missing. `doctor` gains per-provider checks: binary found +
version, auth status, bridge self-test (spawn, list tools, one scoped read);
`doctor --probe` performs one cheap round trip through the selected
provider.

### Cursor transport (M1 specifics)

- Invocation: `cursor-agent --print --output-format stream-json --force`,
  prompt on stdin, `--model` from config, MCP config file pointing at the
  tool bridge, cwd = the PR-time worktree.
- Parsing, session accounting, and the boundary prompt line reuse what the
  Composer eval arm already learned (`eval/dataset/run_cursor_arm.py`) —
  including the incident where a smoke run read `~/.claude/skills/`.
- **Open question to spike first**: whether cursor-agent can disable its
  built-in tools when MCP tools are configured. If yes → preventive; if no →
  the bridge is additive and `providers/audit.py` is the enforcement layer:
  realpath-normalized worktree bound on every file access, write ban,
  discussion-access regex; verdict + flags traced and rendered in
  RUN_REPORT ("backend: cursor — native tools possible, audit: clean/N
  flags").
- No `--max-turns` equivalent → wall-clock timeout + the existing
  budget-discipline prompt lines (reserve final rounds for the contract).

### Claude Code (M2) and Codex (M3)

- `claude -p --output-format json --mcp-config <bridge> --allowedTools
  <bridge tools only> --max-turns <budget> --model <m>`; cleanest harness
  citizen (built-ins fully off, native max-turns, system prompt supported,
  usage+cost in output).
- `codex exec --json --sandbox read-only` + MCP servers in config; no
  system-prompt channel (contract prepended to prompt); budget via timeout.

## Milestones and acceptance

**M1 — provider layer + cursor-agent**
1. `providers/` + registry + `ResolvedTarget` extension + `api` provider
   wrapping `LLM`. Acceptance: full existing suite green with no config
   change; `STRICT_BACKEND=api` byte-identical (parity ratchet).
2. Tool bridge + bridge tests. Acceptance: dispatch parity (same refusals/
   bounds as in-process), `.env` exfiltration read refused + traced.
3. Cursor transport + audit + doctor checks + readiness wiring. Acceptance:
   fake-CLI offline tests green; one live Strict smoke on a small PR with
   backend label, usage, and audit verdict in RUN_REPORT; unset
   `STRICT_BACKEND` on a Strict start yields the exact fix-line error.

**M2 — claude-code** · **M3 — codex**: same acceptance shape (offline
fake-CLI tests + one live smoke each); M2 additionally proves nested-CC
(Strict host = Claude Code) works under the sanitized env.

## Test plan (offline-first, house discipline)

- `test_providers.py` — registry resolution; strict-vs-CLI empty-selection
  behavior; `HarnessLLM` raising on tools; MoA member rejection; tier
  interplay (`tier_target` returning harness targets).
- `test_tool_bridge.py` — spec round-trip; scope enforcement through the
  bridge; bridge trace contents.
- `test_provider_cursor.py` — fixture script emitting canned stream-json:
  final-text extraction, usage parsing, timeout → truncated outcome, audit
  flag surfacing.
- Doctor: per-provider check rendering + fix lines.
- Ratchets untouched: `test_repo_neutral_core`, `test_llm_providers.py`,
  `test_tier_split.py`, `test_thin_mcp_server.py`, `test_mcp.py`.
- New SPEC pages under `doc/SPEC/` for `providers/` and `tool_bridge.py`
  once implemented (house rule: file-level constraints live there).

## Risks and open questions

1. cursor-agent built-in tool restriction unknown → M1 spike; governance
   fallback already decided (audit as enforcement).
2. Contract compliance without a system-prompt channel (cursor/codex) —
   absorbed by the existing repair + escalation-salvage path; watched in
   smoke before trusting.
3. Harness inner reasoning is invisible to our trace; only bridged tool
   calls are audited. Disclosed per run — never presented as full-fidelity
   Strict tracing.
4. Subscription ToS/rate limits: concurrency capped, limit errors BLOCK
   loudly. Users choose their own account exposure by selecting the
   backend explicitly.
5. Model naming inside harnesses (composer ids, codex model slugs) —
   `doctor --probe` reports what the CLI actually serves; served-model
   guard records it per call.
