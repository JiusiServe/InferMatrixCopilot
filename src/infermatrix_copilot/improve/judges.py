"""Judge calls, all under the engine's ledger (design §10).

The engine never starts a judge subprocess directly; every judge call goes
through `run_judge`, which has two paths:

* **API judges** through `LLM.create` — captured as `model_call` records by
  the choke point and priced against the dollar envelope (P3 governor);
* **CLI judges** (a subscription harness such as `cursor-agent`) through
  `governed_subprocess` — one call reserved against the judge-call envelope,
  tool-less by construction (fresh empty workspace, `--mode ask`, any tool
  call in the stream fails the verdict), recorded as a `model_call` with
  ``usd=0``.

A `Governor` (P3) gates both; without one the calls are unmetered but still
recorded. `parse_verdict` extracts the first JSON object of a reply.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from ..trace_store import current_store


class JudgeError(RuntimeError):
    pass


@dataclass(frozen=True)
class JudgeSpec:
    kind: str                 # "api" | "cli"
    model: str
    provider: str = ""        # cli: cursor | codex | claude ; api: the LLM's provider
    max_tokens: int = 2000


def parse_verdict(text: str) -> dict:
    """The first JSON object in ``text`` (judges answer with minified JSON,
    sometimes wrapped in prose or a code fence)."""
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        raise JudgeError("no JSON object in the judge reply")
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError as exc:
        raise JudgeError(f"judge reply is not valid JSON: {exc}") from exc


def _cli_argv(spec: JudgeSpec, prompt: str, workspace: Path) -> list[str]:
    if spec.provider == "cursor":
        return ["cursor-agent", "--print", "--output-format", "stream-json", "--model", spec.model,
                "--mode", "ask", "--trust", "--workspace", str(workspace), prompt]
    if spec.provider == "claude":
        return ["claude", "-p", prompt, "--output-format", "json", "--max-turns", "3",
                "--allowedTools", "", "--model", spec.model]
    if spec.provider == "codex":
        # a fresh workspace is not a git repository: codex needs the skip flag
        # the prompt goes on stdin (`-`): argv has a 128 KiB per-argument limit
        return ["codex", "exec", "--json", "-s", "read-only", "--skip-git-repo-check", "-C", str(workspace),
                "-m", spec.model, "-"]
    raise JudgeError(f"unknown CLI judge provider {spec.provider!r}")


def _tool_calls_in(events: list[dict]) -> list[str]:
    """Any sign a judge reached outside the prompt: an event type naming a
    tool, or a non-text block inside an assistant/user message (the nested
    tool_use/tool_result form). Over-broad on purpose: an unrecognised block
    fails loudly rather than passes."""
    used = []
    for e in events:
        if "tool" in str(e.get("type", "")).lower():
            used.append(str(e.get("type")))
            continue
        msg = e.get("message") or {}
        for b in (msg.get("content") or []) if isinstance(msg, dict) else []:
            if isinstance(b, dict) and b.get("type") not in (None, "text"):
                used.append(str(b.get("type")))
        item = e.get("item")
        if isinstance(item, dict):
            kind = str(item.get("item_type") or item.get("type") or "")
            if kind and "agent_message" not in kind and "reasoning" not in kind:
                used.append(kind)
    return sorted(set(used))


def _cli_result(spec: JudgeSpec, stdout: str) -> tuple[str, dict]:
    """``(final text, usage)`` from a CLI judge's output; a cursor stream that
    shows any tool call fails the verdict (a judge with a filesystem is not
    blind)."""
    if spec.provider == "cursor":
        events = []
        for line in stdout.splitlines():
            line = line.strip()
            if line.startswith("{"):
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        used = _tool_calls_in(events)
        if used:
            raise JudgeError(f"judge attempted tool calls {used[:3]} — verdict discarded")
        res = next((e for e in reversed(events) if e.get("type") == "result"), {})
        if res.get("is_error"):
            raise JudgeError(f"cursor judge errored: {str(res.get('result'))[:200]}")
        u = res.get("usage") or {}
        return str(res.get("result") or ""), {"input_tokens": u.get("inputTokens") or 0,
                                              "output_tokens": u.get("outputTokens") or 0}
    if spec.provider == "claude":
        data = json.loads(stdout or "{}")
        return str(data.get("result") or ""), {}
    if spec.provider == "codex":
        text = ""
        events = []
        for line in stdout.splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            events.append(event)
            item = event.get("item")
            if isinstance(item, dict):
                kind = str(item.get("item_type") or item.get("type") or "")
                if "agent_message" in kind and item.get("text"):
                    text = str(item["text"])
            elif event.get("type") in ("agent_message",) and event.get("text"):
                text = str(event["text"])
        used = _tool_calls_in(events)
        if used:
            raise JudgeError(f"judge attempted tool calls {used[:3]} — verdict discarded")
        return text, {}
    raise JudgeError(f"unknown CLI judge provider {spec.provider!r}")


def governed_subprocess(argv: list[str], *, governor: Any = None, timeout: int = 900,
                        cwd: str | None = None, env: dict | None = None,
                        runner: Callable[..., Any] | None = None, input: str | None = None):
    """A judge CLI call: reserved against the judge-call envelope BEFORE it
    starts (a refusal never launches the process), settled after."""
    token = governor.reserve_judge_call() if governor is not None else None
    run = runner or subprocess.run
    try:
        return run(argv, capture_output=True, text=True, timeout=timeout, cwd=cwd, env=env, input=input)
    finally:
        if governor is not None:
            governor.settle_judge_call(token)


def run_judge(spec: JudgeSpec, *, system: str, prompt: str, llm: Any = None, governor: Any = None,
              role: str = "judge", runner: Callable[..., Any] | None = None) -> dict:
    """Run one judge call and return its parsed JSON verdict (raises
    JudgeError on an unusable reply). Both paths are recorded as
    ``model_call`` records under the current trace context."""
    if spec.kind == "api":
        if llm is None:
            raise JudgeError("an API judge needs an LLM")
        reply = llm.create(system=system, messages=[{"role": "user", "content": prompt}],
                           model=spec.model, max_tokens=spec.max_tokens, role=role)
        text = "".join(b.text for b in reply.blocks if b.type == "text")
        return parse_verdict(text)
    if spec.kind != "cli":
        raise JudgeError(f"unknown judge kind {spec.kind!r}")
    workspace = Path(tempfile.mkdtemp(prefix="judge-ws-"))
    workspace.chmod(0o700)
    started = time.monotonic()
    try:
        full = prompt if not system else f"{system}\n\n{prompt}"
        proc = governed_subprocess(_cli_argv(spec, full, workspace), governor=governor, cwd=str(workspace),
                                   runner=runner, input=full if spec.provider == "codex" else None)
        text, usage = _cli_result(spec, getattr(proc, "stdout", "") or "")
        error = "" if text else f"empty judge reply (rc={getattr(proc, 'returncode', '?')})"
    except JudgeError as exc:
        text, usage, error = "", {}, str(exc)
    finally:
        shutil.rmtree(workspace, ignore_errors=True)
    store = current_store()
    if store is not None:
        try:
            store.append("model_call", inputs={"system": system, "prompt": prompt},
                         outputs={"reply": text} if text else {},
                         model={"role": role, "provider": spec.provider, "model": spec.model, "served_model": ""},
                         usage=usage, seconds=round(time.monotonic() - started, 3),
                         result={"format": "prompt/1", "usd": 0.0, "subscription": True}, error=error)
        except Exception:  # noqa: BLE001 - recording never changes a verdict
            pass
    if error:
        raise JudgeError(error)
    return parse_verdict(text)


def judge_spec_from(settings: Any, override: str = "") -> JudgeSpec | None:
    """The gold_match / paired judge from ``settings.improve_judge`` (or an
    explicit override): ``api:<model>`` or ``cli:<provider>:<model>``; None
    when unset."""
    raw = str(override or getattr(settings, "improve_judge", "") or "")
    if not raw:
        return None
    parts = raw.split(":")
    if parts[0] == "api" and len(parts) == 2:
        return JudgeSpec("api", parts[1])
    if parts[0] == "cli" and len(parts) == 3:
        return JudgeSpec("cli", parts[2], provider=parts[1])
    raise JudgeError(f"improve_judge must be api:<model> or cli:<provider>:<model>, got {raw!r}")
