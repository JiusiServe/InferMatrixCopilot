"""The rebase agent loop — port of the parent's `_run_agent_loop`
(`agent/nodes/phase2_rebase.py`), kept `kind=script` by design (Rev 8 §4:
prompt bytes, mandatory streaming at 32k max_tokens with tool-input
accumulation, the `.decision.md` plan gate, and the 150-turn budget are all
cache-parity load-bearing — the copilot's `agent_runtime` is deliberately NOT
used here).

Differences from the parent, each deliberate:
- tool calls dispatch through `tools.dispatch(..., extra=...)` — the single
  choke point (C5) with the opt-in write-path scoping; result BYTES stay
  parent-shaped (handlers serialize the parent dicts; dispatch errors render
  as the parent's ``{"error": ...}``).
- the client is injected (an `AsyncAnthropic`-compatible object), so the loop
  is testable against fakes and the caller owns model/base-url/key policy.

Parity behaviors pinned by test: streaming with `get_final_message`, the
plan-review gate (edit/pytest/precommit tools withheld until a `write_file`
lands a ``.decision.md``), the incomplete write/edit input guard with the
truncation hint, the 3-strike max_tokens truncation abort, fatal-auth vs
transient stream-error classification, and the turn budget.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Callable, Mapping

from ..run_trace import RunTrace
from ..scopes import ToolScope
from ..tools import ToolDef, dispatch

# withheld until the plan-review-decision gate passes (parent parity: the
# plan and decision files are written with write_file, which stays available)
GATED_TOOL_NAMES = ("edit_file", "run_pytest", "run_precommit")

_FATAL_AUTH_MARKERS = ("401", "unauthorized", "403", "forbidden",
                       "invalid_api_key", "authentication")


def _under_plan_dir(file_path: str, plan_write_prefix: str) -> bool:
    """RESOLVED-path containment — a raw startswith is bypassable via
    `<plans>/../product.py` traversal or a `plans-evil` sibling, and dispatch
    later canonicalizes the path against the broader writable scope."""
    from pathlib import Path
    if not file_path:
        return False
    try:
        return Path(file_path).resolve().is_relative_to(
            Path(plan_write_prefix).resolve())
    except (OSError, ValueError, RuntimeError):
        # unresolvable ⇒ not provably inside ⇒ locked. RuntimeError is the
        # symlink-loop signal on supported Pythons — it must lock, not crash
        return False


def _log_writer(agent_log: str) -> Callable[[str], None]:
    def write(line: str) -> None:
        if agent_log:
            try:
                with open(agent_log, "a") as f:
                    f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {line}\n")
            except Exception:  # noqa: BLE001 - logging never breaks the loop
                pass
    return write


async def run_agent_loop(
    client: Any,
    system_prompt: str,
    *,
    model: str,
    tool_defs: list[dict],
    extra_tools: Mapping[str, ToolDef],
    scope: ToolScope | None = None,
    trace: RunTrace | None = None,
    max_turns: int = 150,
    max_tokens: int = 32000,
    require_plan_review: bool = True,
    plan_write_prefix: str = "",
    model_aliases: Mapping[str, str] | None = None,
    model_mismatch_policy: str = "fail",
    agent_log: str = "",
) -> dict:
    """Send prompt → receive tool calls → dispatch → repeat until a text-only
    response or the turn budget. Returns ``{"done", "text", "turns"}``.

    `plan_write_prefix` is REQUIRED when the plan gate is on: while locked,
    `write_file` is confined to paths under it (the run's plan directory) —
    without this, the gate is bypassable by simply overwriting product code
    with `write_file` before any decision exists."""
    if require_plan_review and not plan_write_prefix:
        raise ValueError("plan_write_prefix is required when "
                         "require_plan_review is on — the gate would be "
                         "bypassable via pre-decision write_file")
    messages: list[dict] = [{"role": "user", "content": system_prompt}]
    write_log = _log_writer(agent_log)
    write_log(f"=== Agent started (model={model}, max_turns={max_turns}) ===\n")
    write_log(f"--- Prompt ---\n{system_prompt[:2000]}...\n")

    turn = 0
    plan_done = False
    consecutive_truncations = 0

    for _ in range(max_turns):
        turn += 1
        if require_plan_review and not plan_done:
            gated_tools = [t for t in tool_defs
                           if t["name"] not in GATED_TOOL_NAMES]
        else:
            gated_tools = tool_defs

        # Streaming is mandatory: at this max_tokens the non-streaming SDK
        # path refuses (>10-minute operations), and streaming fully
        # accumulates each tool_use's input JSON so a large write_file isn't
        # silently truncated into empty input (parent-documented).
        try:
            if trace:
                trace.record("rebase_llm_request", turn=turn, model=model,
                             n_tools=len(gated_tools))
            async with client.messages.stream(
                model=model, max_tokens=max_tokens,
                tools=gated_tools, messages=messages,
            ) as stream:
                async for _ev in stream:
                    pass
                response = await stream.get_final_message()
        except Exception as exc:  # noqa: BLE001 - stream errors are outcomes
            write_log(f"\n=== Agent stream error (turn {turn}): {exc} ===\n")
            err = str(exc).lower()
            if any(kw in err for kw in _FATAL_AUTH_MARKERS):
                return {"done": False, "text": f"Fatal API error: {exc}",
                    "turns": turn, "plan_done": plan_done}
            return {"done": False, "text": f"Stream error (turn {turn}): {exc}",
                    "turns": turn, "plan_done": plan_done}

        # Served-model guard (repo invariant: model substitution fails by
        # default — a silently substituted backend once fabricated 60× cost
        # metrics). Uses the SHARED normalization (canonical_model: variant
        # suffixes like `[1m]` and the audited alias map are equivalences,
        # not substitutions) and honors MODEL_MISMATCH_POLICY=warn.
        from ..llm import canonical_model
        served = getattr(response, "model", "") or ""
        if served and canonical_model(served, dict(model_aliases or {})) != \
                canonical_model(model, dict(model_aliases or {})):
            if model_mismatch_policy == "warn":
                write_log(f"[warn] model mismatch accepted by policy: "
                          f"requested {model}, served {served}")
            else:
                write_log(f"\n=== Model mismatch: requested {model}, "
                          f"served {served} — aborting ===\n")
                return {"done": False,
                        "text": f"Model mismatch: requested {model}, "
                                f"served {served}",
                        "turns": turn, "plan_done": plan_done}

        truncated = getattr(response, "stop_reason", None) == "max_tokens"
        text_parts: list[str] = []
        tool_uses: list[Any] = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_uses.append(block)

        if trace:
            trace.record("rebase_llm_response", turn=turn,
                         stop_reason=getattr(response, "stop_reason", "") or "",
                         n_tool_calls=len(tool_uses))

        if truncated:
            consecutive_truncations += 1
            write_log(f"[warn] response truncated at max_tokens "
                      f"(turn {turn}, streak {consecutive_truncations}); "
                      f"{len(tool_uses)} tool call(s) may be incomplete")
            if consecutive_truncations >= 3:
                write_log("\n=== Agent aborted: repeated max_tokens truncation "
                          "(likely trying to rewrite a very large file) ===\n")
                return {"done": False, "text": "Aborted: repeated output truncation",
                    "turns": turn, "plan_done": plan_done}
        else:
            consecutive_truncations = 0

        write_log(f"\n--- Turn {turn} ---")
        if text_parts:
            write_log(f"[text] {''.join(text_parts)[:500]}")
        if tool_uses:
            write_log(f"[tools] {', '.join(t.name for t in tool_uses)}")

        if not tool_uses:
            if truncated:
                # Deliberate divergence from the parent (which returned
                # done=True here): a text-only response cut off at the token
                # cap is an INVOLUNTARY ending — reporting it as successful
                # completion could mark a half-finished module done.
                write_log(f"\n=== Agent output truncated with no tool calls "
                          f"(turn {turn}) — not a completion ===\n")
                return {"done": False,
                        "text": "Truncated at max_tokens with no tool calls: "
                                + "\n".join(text_parts),
                        "turns": turn, "plan_done": plan_done}
            write_log(f"\n=== Agent finished (turn {turn}) ===\n")
            return {"done": True, "text": "\n".join(text_parts),
                    "turns": turn, "plan_done": plan_done}

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        decision_written = False
        for tool_use in tool_uses:
            tinput = tool_use.input or {}
            # The tools LIST only controls advertisement — the model can
            # still emit a call it was never offered. While the plan gate is
            # closed, gated calls are rejected at dispatch, not just hidden,
            # and write_file is confined to the plan directory (product code
            # must be untouchable before a decision exists).
            gate_closed = require_plan_review and not plan_done
            locked_write = (gate_closed and tool_use.name == "write_file"
                            and not _under_plan_dir(
                                str(tinput.get("file_path", "")),
                                plan_write_prefix))
            if (gate_closed and tool_use.name in GATED_TOOL_NAMES) \
                    or locked_write:
                what = ("write_file outside the plan directory"
                        if locked_write else tool_use.name)
                write_log(f"[guard] rejected {what} before plan-review "
                          "decision")
                tool_results.append({"type": "tool_result",
                                     "tool_use_id": tool_use.id,
                                     "content": json.dumps({"error": (
                                         f"{what} is locked until the "
                                         "plan-review decision file "
                                         "(.decision.md) is written."
                                         + (" Write plan/decision files under "
                                            f"{plan_write_prefix}"
                                            if locked_write else ""))})})
                continue
            # Guard against truncated/incomplete tool input: a write/edit
            # whose JSON was cut off loses ANY of its required args, and
            # dispatching would produce the cryptic TypeError the model
            # blindly retries (a path with the content cut off is the common
            # shape, not just fully-empty input).
            _required = {"write_file": ("file_path", "content"),
                         "edit_file": ("file_path", "old_string",
                                       "new_string")}
            if tool_use.name in _required and \
                    any(k not in tinput for k in _required[tool_use.name]):
                hint = (" Your previous response was truncated at the output "
                        "token limit, so this tool call is incomplete."
                        if truncated else "")
                result_json = json.dumps({"error": (
                    f"{tool_use.name} call is missing required input (no "
                    f"file_path/content).{hint} The content is likely too "
                    f"large to emit in a single call. For large files, use "
                    f"`edit_file` with a small, targeted old_string/new_string "
                    f"instead of rewriting the whole file with `write_file`. "
                    f"Do NOT re-send the same oversized write.")})
                write_log(f"[guard] rejected incomplete {tool_use.name} call "
                          f"(truncated={truncated})")
                tool_results.append({"type": "tool_result",
                                     "tool_use_id": tool_use.id,
                                     "content": result_json})
                continue
            payload = dispatch(tool_use.name, dict(tinput), scope=scope,
                               trace=trace, extra=dict(extra_tools))
            if payload.get("ok"):
                # handlers serialize the parent-shaped dict themselves
                content = payload["result"]
                # the gate unlocks only on a SUCCESSFUL decision write: a
                # refused/failed write_file (or one whose parent-shaped
                # result carries an error) proves nothing was decided
                if (tool_use.name == "write_file"
                        and ".decision.md" in tinput.get("file_path", "")):
                    try:
                        decision_written = "error" not in json.loads(content)
                    except (TypeError, ValueError):
                        decision_written = False
            else:
                content = json.dumps({"error": payload.get("error", "unknown")})
            tool_results.append({"type": "tool_result",
                                 "tool_use_id": tool_use.id,
                                 "content": content})
        messages.append({"role": "user", "content": tool_results})

        if not plan_done and decision_written:
            plan_done = True
            write_log("\n--- PLAN-REVIEW-DECISION COMPLETE — edit "
                      "tools unlocked ---\n")

        for i, tr in enumerate(tool_results):
            write_log(f"[tool_result {i}] {str(tr.get('content', ''))[:300]}")

    write_log(f"\n=== Agent exceeded max turns ({max_turns}) ===\n")
    return {"done": False, "text": "Agent exceeded max turns",
            "turns": turn, "plan_done": plan_done}
