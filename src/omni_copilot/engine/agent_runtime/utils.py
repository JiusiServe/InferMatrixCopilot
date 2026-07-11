"""Stateless helpers for the agent-step runtime.

Evidence packing, the permissions view, and output coercion/mapping — the pure
functions the runner and ensemble share. They hold no agent-loop state, so they
live here instead of inflating the orchestration files (`runner`, `ensemble`).
"""

from __future__ import annotations

import json
import threading

from ...llm import parse_json_reply
from ...scopes import ToolScope
from ..step import FailureKind, StepContext, StepResult

_STATUS_TO_FAILURE = {
    "blocked": FailureKind.BLOCKED,
    "needs_review": FailureKind.ESCALATE,
}
_FAILURE_KINDS = {k.value: k for k in FailureKind}


def _build_evidence(ctx: StepContext, evidence: dict[str, str],
                    cap: int | None = None) -> tuple[dict, dict]:
    """Cap each item; archive the full text in the run dir for tool access."""
    cap = cap or ctx.settings.evidence_item_chars
    capped: dict[str, str] = {}
    refs: dict[str, str] = {}
    ev_dir = ctx.run_dir / "evidence"
    for name, text in evidence.items():
        text = str(text or "")
        if len(text) > cap:
            ev_dir.mkdir(parents=True, exist_ok=True)
            path = ev_dir / f"{name}.txt"
            # concurrent lenses archive the same evidence — write atomically
            tmp = ev_dir / f".{name}.{threading.get_ident()}.tmp"
            tmp.write_text(text, encoding="utf-8")
            tmp.replace(path)
            refs[name] = str(path)
            head = text[: int(cap * 0.75)]
            tail = text[-int(cap * 0.25):]
            capped[name] = f"{head}\n...[{len(text) - cap} chars omitted]...\n{tail}"
        else:
            capped[name] = text
    return capped, refs


def _permissions_view(scope: ToolScope, extra_tools: dict) -> dict:
    """Summarize the step's tool scope for the prompt's PERMISSIONS section:
    the sorted allowed + extra tool names, the read-only flag, writable paths,
    and whether shell is available. `push` is hard-coded False — pushing is
    never an agent-step capability."""
    return {
        "tools": sorted(scope.allowed_tools) + sorted(extra_tools),
        "read_only": scope.read_only,
        "writable_paths": list(scope.path_scope.writable) if scope.path_scope else [],
        "shell": "run_shell" in scope.allowed_tools,
        "push": False,  # push is never an agent-step capability
    }


def _coerce_output(text: str, ctx: StepContext, contract: dict) -> dict | None:
    """Parse the agent's final message into the output dict. Empty text returns
    None (no repair — a repair round on nothing would only hallucinate). A
    well-formed JSON object with a `status` is accepted as-is; otherwise one
    repair LLM call reshapes the draft to `contract`. Returns the dict, or None
    if it still lacks a `status`."""
    text = str(text or "")
    if not text.strip():
        return None  # nothing to repair — a repair round would hallucinate
    obj = parse_json_reply(text)
    if isinstance(obj, dict) and obj.get("status"):
        return obj
    # one repair round: convert the draft into the contract
    reply = ctx.llm.create(
        system=("Convert the agent's draft output into a single JSON object "
                "matching this contract exactly (fill unknowns with sensible "
                "defaults, keep all substance):\n"
                + json.dumps(contract, ensure_ascii=False)),
        messages=[{"role": "user", "content": str(text)[:20_000]}],
        max_tokens=8000)  # repair reply must fit a full contract
    obj = parse_json_reply(reply.text)
    return obj if isinstance(obj, dict) and obj.get("status") else None


def _to_step_result(output: dict, summary_prefix: str) -> StepResult:
    """Map the agent's output dict to a typed StepResult. `status=success`
    yields ok; `blocked`/`needs_review` map to fixed BLOCKED/ESCALATE kinds;
    any other status derives the FailureKind from the output's `failure_kind`
    field, defaulting to ESCALATE. The summary is prefixed (e.g. an ensemble
    tag) and capped, and `files_modified` is carried as the changed files."""
    status = str(output.get("status", "failed")).lower()
    summary = f"{summary_prefix}{output.get('summary', '')}"[:400]
    changed = [str(f) for f in output.get("files_modified", []) or []]
    if status == "success":
        return StepResult(True, summary=summary, outputs=output,
                          changed_files=changed)
    if status in _STATUS_TO_FAILURE:
        return StepResult(False, _STATUS_TO_FAILURE[status], summary,
                          outputs=output, changed_files=changed)
    kind = _FAILURE_KINDS.get(str(output.get("failure_kind") or "").lower(),
                              FailureKind.ESCALATE)
    return StepResult(False, kind, summary, outputs=output, changed_files=changed)
