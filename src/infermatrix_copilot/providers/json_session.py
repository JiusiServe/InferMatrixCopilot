"""Bounded read-only JSON sessions shared by review and knowledge workflows.

The caller owns its schema and evidence policy. This transport owns command
permissions, credential isolation, process lifetime and one formatting repair.
"""
from __future__ import annotations

import json
import math
import os
import re
import shutil
import tempfile
import time
from pathlib import Path

from ..budgeting import call_budget
from .base import json_events, run_cli, stream_cli


class JSONSessionError(RuntimeError):
    def __init__(self, message, *, failure_class="backend", timeout=False, returncode=None):
        super().__init__(message)
        self.failure_class = failure_class
        self.timeout, self.returncode = timeout, returncode


_CREDENTIAL_KEYS = frozenset({
    "GITHUB_TOKEN", "GH_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN",
    "GITHUB_PAT", "GITHUB_APP_PRIVATE_KEY", "GITHUB_APP_PRIVATE_KEY_PATH",
    "GITHUB_APP_CLIENT_SECRET", "GIT_ASKPASS", "SSH_ASKPASS", "SSH_AUTH_SOCK",
    "GIT_SSH_COMMAND", "VSCODE_GIT_IPC_HANDLE", "VSCODE_GIT_ASKPASS_NODE",
    "VSCODE_GIT_ASKPASS_EXTRA_ARGS", "VSCODE_GIT_ASKPASS_MAIN",
    "CURSOR_GIT_IPC_HANDLE", "CURSOR_GIT_ASKPASS_NODE",
    "CURSOR_GIT_ASKPASS_EXTRA_ARGS", "CURSOR_GIT_ASKPASS_MAIN",
})


def readonly_environment(source=None):
    """Keep model authentication while removing the publisher's Git identity."""
    env = dict(os.environ if source is None else source)
    for key in tuple(env):
        if key in _CREDENTIAL_KEYS or key.startswith("GIT_CONFIG_"):
            env.pop(key, None)
    env.update(GH_CONFIG_DIR=os.devnull, GIT_CONFIG_GLOBAL=os.devnull,
               GIT_CONFIG_SYSTEM=os.devnull, GIT_CONFIG_NOSYSTEM="1",
               GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
    return env


def decode_object(text):
    result = text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", result, re.DOTALL | re.IGNORECASE)
    if fenced:
        result = fenced.group(1)
    try:
        payload = json.loads(result)
    except json.JSONDecodeError as original:
        decoder = json.JSONDecoder()
        for match in re.finditer(r"\{", result):
            try:
                candidate, _ = decoder.raw_decode(result, match.start())
            except json.JSONDecodeError:
                continue
            if isinstance(candidate, dict):
                return candidate
        raise original
    if not isinstance(payload, dict):
        raise ValueError("top-level value is not an object")
    return payload


def _session_id(event):
    nested = event.get("session")
    for value in (event.get("session_id"), event.get("sessionId"),
                  event.get("conversation_id"), event.get("conversationId"),
                  nested.get("id") if isinstance(nested, dict) else None):
        if str(value or "").strip():
            return str(value).strip()
    return None


def _invoke(command, prompt, *, cwd, provider, model, idle, absolute, event_sink):
    """Stream one invocation; reserve before dispatch and settle even on failure."""
    request = {"kind": "harness_session", "provider_id": provider, "model": model,
               "system": "", "messages": [{"role": "user", "content": prompt}],
               "max_tokens": 8192}
    with call_budget(request) as budget:
        result = {"text": None, "session_id": None, "served_model": None, "usage": None}
        def observe(channel, text):
            if channel != "stdout":
                return
            for event in json_events(text):
                result["session_id"] = _session_id(event) or result["session_id"]
                if event.get("type") == "system" and event.get("model"):
                    result["served_model"] = str(event["model"])
                if event.get("usage"):
                    result["usage"] = budget["usage"] = event["usage"]
                if event.get("type") == "result" and event.get("subtype") == "success":
                    result["text"] = str(event.get("result", "")).strip()
                if event_sink:
                    event_sink(event)
        try:
            budget["sent"] = True
            stdout, stderr, code, timeout = stream_cli(command, cwd=cwd, env=readonly_environment(),
                deadline=absolute, input=prompt, idle_timeout_s=idle,
                on_line=observe, termination_grace_s=5)
        except OSError as exc:
            raise JSONSessionError(f"{provider} could not run: {exc}") from exc
        if timeout:
            raise JSONSessionError(f"{provider} exceeded maximum runtime" if timeout == "absolute" else
                                   f"{provider} idle timeout after {idle:g} seconds without stdout activity", timeout=True)
        if code:
            failures = [event.get("message") or event.get("error") for event in json_events(stdout)
                        if event.get("type") in {"error", "turn.failed"}]
            failure = next((item for item in reversed(failures) if item), None)
            detail = failure.get("message", "") if isinstance(failure, dict) else failure
            raise JSONSessionError(f"{provider} exited with {code}: {(detail or stderr or stdout)[-4000:]}", returncode=code)
        result["stdout"] = stdout
        budget.update(outcome="completed", usage=result["usage"])
        return result


def _buffered(command, prompt, *, cwd, provider, model, idle, absolute, event_sink):
    with call_budget({"kind": "harness_session", "provider_id": provider, "model": model,
                      "system": "", "messages": [{"role": "user", "content": prompt}],
                      "max_tokens": 8192}) as budget:
        budget["sent"] = True
        try:
            stdout, stderr, code, timed_out = run_cli(command, input=prompt, cwd=cwd,
                env=readonly_environment(), timeout_s=min(idle, max(0.001, absolute - time.monotonic())))
        except OSError as exc:
            raise JSONSessionError(f"{provider} could not run: {exc}") from exc
        if timed_out:
            raise JSONSessionError(f"{provider} could not run: timed out", timeout=True)
        if code:
            raise JSONSessionError(f"{provider} exited with {code}: {(stderr or stdout)[-2000:]}", returncode=code)
        if provider == "codex":
            events = json_events(stdout)
            usage = next((event["usage"] for event in reversed(events) if event.get("usage")), None)
            budget.update(outcome="completed", usage=usage)
            if event_sink:
                for event in events:
                    event_sink(event)
            return {"text": None, "session_id": None, "served_model": None, "usage": usage, "stdout": stdout}
        try:
            envelope = json.loads(stdout)
            if not isinstance(envelope, dict):
                raise ValueError("transport envelope is not an object")
            if envelope.get("is_error") or envelope.get("subtype") not in (None, "success"):
                raise ValueError("transport envelope reports failure")
        except ValueError as exc:
            raise JSONSessionError(f"{provider} returned invalid envelope: {exc}", failure_class="invalid_result") from exc
        budget.update(outcome="completed", usage=envelope.get("usage"))
        if event_sink:
            event_sink(envelope)
        return {"text": envelope.get("result"), "session_id": _session_id(envelope),
                "served_model": envelope.get("model"), "usage": envelope.get("usage"), "stdout": stdout}


def run_readonly_json(prompt, *, cwd, command, provider, model="", output_schema,
                      idle_timeout_s, absolute_timeout_s, wrap_up_after_s=None,
                      event_sink=None, result_validator=None, allow_sessionless_retry=True,
                      output_format="stream-json", repair_prompt=None, skip_git_repo_check=False, max_repair_attempts=1):
    """Return parsed payload plus session metadata; no business policy is inferred.

    The validator returns an error string or None. Cursor repairs once in the
    same session; when no session identity exists it may retry the whole request
    once. Codex uses its native output schema and never silently changes profile.
    """
    if type(max_repair_attempts) is not int or max_repair_attempts not in (0, 1):
        raise ValueError("max_repair_attempts must be 0 or 1")
    if provider not in {"codex", "cursor"} or not command:
        raise ValueError("a Codex or Cursor command is required")
    if (not all(type(value) in (int, float) and math.isfinite(value)
                for value in (idle_timeout_s, absolute_timeout_s))
            or idle_timeout_s <= 0 or absolute_timeout_s < idle_timeout_s):
        raise ValueError("maximum runtime must be at least the positive idle timeout")
    if wrap_up_after_s is not None and not 0 < wrap_up_after_s < absolute_timeout_s:
        raise ValueError("wrap-up time must be positive and below maximum runtime")
    if output_format not in {"stream-json", "json"} or (output_format == "json" and wrap_up_after_s is not None):
        raise ValueError("buffered JSON sessions cannot use streaming wrap-up")
    command = [shutil.which(command[0]) or command[0], *command[1:]]
    cwd = Path(cwd).resolve()
    original_prompt = prompt
    schema = output_schema if isinstance(output_schema, dict) else json.loads(Path(output_schema).read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="copilot-json-") as temp:
        schema_path, output = Path(temp) / "schema.json", Path(temp) / "last-message.json"
        schema_path.write_text(json.dumps(schema, ensure_ascii=False), encoding="utf-8")
        if provider == "codex":
            argv = [*command, "exec", *(["--model", model] if model else []), "--ephemeral", "--ignore-user-config", "--strict-config",
                    *(["--skip-git-repo-check"] if skip_git_repo_check else []),
                    "--sandbox", "read-only", "--json", "--output-schema", str(schema_path),
                    "--output-last-message", str(output), "-C", str(cwd), "-"]
            transport = _buffered if output_format == "json" else _invoke
            result = transport(argv, prompt, cwd=cwd, provider=provider, model=model,
                             idle=idle_timeout_s, absolute=time.monotonic() + absolute_timeout_s,
                             event_sink=event_sink)
            if not output.is_file():
                raise JSONSessionError("Codex did not write --output-last-message")
            result["text"] = output.read_text(encoding="utf-8")
        else:
            prompt += "\nReturn exactly one JSON object matching this schema:\n" + json.dumps(schema, ensure_ascii=False)
            absolute = time.monotonic() + absolute_timeout_s
            def invoke(text, session=None, deadline=absolute, idle=idle_timeout_s):
                argv = [*command, "-p", *(["--resume", session] if session else []),
                        "--mode=ask", "--output-format", output_format, "--model", model, "--trust"]
                transport = _buffered if output_format == "json" else _invoke
                return transport(argv, text, cwd=cwd, provider=provider, model=model,
                               idle=idle, absolute=deadline, event_sink=event_sink)
            # A wrap-up is a same-session continuation, bounded by the original
            # absolute deadline. It is never permission to start a new session.
            latest = {}
            def observe(event):
                latest["session_id"] = _session_id(event) or latest.get("session_id")
                if original_sink:
                    original_sink(event)
            original_sink = event_sink
            event_sink = observe if wrap_up_after_s is not None else original_sink
            if wrap_up_after_s is None:
                result = invoke(prompt)
            else:
                try:
                    result = invoke(prompt, deadline=min(absolute, time.monotonic() + wrap_up_after_s))
                except JSONSessionError as exc:
                    if "exceeded maximum runtime" not in str(exc):
                        raise
                    if not latest.get("session_id"):
                        raise JSONSessionError("Cursor reached wrap-up time without a session id") from exc
                    if event_sink:
                        event_sink({"type": "session.wrap_up"})
                    result = invoke("Stop all exploration and tool calls now. Use only the evidence already gathered. "
                                    "Immediately return the final JSON object matching the original schema; no commentary.",
                                    latest["session_id"])
            if result["text"] is None:
                raise JSONSessionError("Cursor did not return a successful result")
            try:
                result["payload"] = decode_object(result["text"])
                reason = result_validator(result["payload"]) if result_validator else None
            except (AttributeError, TypeError, ValueError) as exc:
                reason = str(exc)
            if reason:
                if max_repair_attempts == 0:
                    raise JSONSessionError("Cursor returned invalid JSON: " + reason, failure_class="invalid_result")
                if result.get("session_id"):
                    previous = result
                    if event_sink:
                        event_sink({"type": "session.repair", "reason": reason})
                    correction = repair_prompt or (
                        "Your previous final response did not match the required review "
                        f"result contract ({reason}). Do not inspect the "
                        "repository or perform any more review work. Preserve the same "
                        "findings, reviewed head SHA, review checks, and conclusions. "
                        "Correct only the invalid formatting and immediately return "
                        "exactly one JSON object matching the schema and summary contract "
                        "in the original request. Use an empty findings list if no "
                        "actionable finding was proven. Output no Markdown or commentary "
                        "outside the JSON object.")
                    result = invoke(correction,
                                    result["session_id"], time.monotonic() + min(idle_timeout_s, 120.0),
                                    min(idle_timeout_s, 120.0))
                    result["served_model"] = result["served_model"] or previous["served_model"]
                    result["session_id"] = result["session_id"] or previous["session_id"]
                    if event_sink:
                        event_sink({"type": "session.repaired"})
                elif allow_sessionless_retry:
                    if event_sink:
                        event_sink({"type": "session.retry"})
                    return run_readonly_json(original_prompt, cwd=cwd, command=command, provider=provider, model=model,
                                             output_schema=schema, idle_timeout_s=idle_timeout_s,
                                             absolute_timeout_s=absolute_timeout_s, wrap_up_after_s=wrap_up_after_s,
                                             event_sink=original_sink, result_validator=result_validator,
                                             allow_sessionless_retry=False, output_format=output_format,
                                             repair_prompt=repair_prompt, max_repair_attempts=max_repair_attempts)
                else:
                    raise JSONSessionError("Cursor returned invalid JSON: " + reason, failure_class="invalid_result")
        try:
            result["payload"] = decode_object(result["text"])
            reason = result_validator(result["payload"]) if result_validator else None
            if reason:
                raise ValueError(reason)
        except (AttributeError, TypeError, ValueError) as exc:
            raise JSONSessionError(f"{provider.title()} returned invalid JSON: {exc}", failure_class="invalid_result") from exc
        return result
