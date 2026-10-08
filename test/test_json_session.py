import json
import sys

import pytest

from infermatrix_copilot.budgeting import bind_call_budget
from infermatrix_copilot.providers.json_session import (
    JSONSessionError, readonly_environment, run_readonly_json,
)


def session(tmp_path, source, provider="cursor", **kwargs):
    cli = tmp_path / "cli.py"
    cli.write_text(source, encoding="utf-8")
    return run_readonly_json("original evidence", cwd=tmp_path,
        command=[sys.executable, str(cli)], provider=provider, model="chosen",
        output_schema={"type": "object"}, idle_timeout_s=2,
        absolute_timeout_s=4, **kwargs)


def test_codex_native_schema_and_credentials(tmp_path, monkeypatch):
    monkeypatch.setenv("GH_TOKEN", "publisher-secret")
    result = session(tmp_path, '''
import json, os, pathlib, sys
args = sys.argv
assert all(flag in args for flag in ["--ephemeral", "--ignore-user-config", "--strict-config", "--json"])
assert args[args.index("--sandbox") + 1] == "read-only"
assert "GH_TOKEN" not in os.environ
pathlib.Path(args[args.index("--output-last-message") + 1]).write_text('{"accepted":true}')
print(json.dumps({"type":"turn.completed", "usage":{"input_tokens":31}}))
''', "codex")
    assert result["payload"] == {"accepted": True}
    assert result["usage"] == {"input_tokens": 31}


@pytest.mark.parametrize("output_format", ["json", "stream-json"])
def test_cursor_same_session_repair(tmp_path, output_format):
    result = session(tmp_path, '''
import json, sys
args = sys.argv
assert "--mode=ask" in args and "--force" not in args
assert args[args.index("--output-format") + 1] in {"json", "stream-json"}
sys.stdin.read()
repair = "--resume" in args
if repair:
    assert args[args.index("--resume") + 1] == "original-session"
print(json.dumps({"type":"result", "subtype":"success", "session_id":"original-session",
                  "result":'{"rules":[]}' if repair else 'not JSON'}))
''', output_format=output_format, allow_sessionless_retry=False,
        result_validator=lambda payload: None if isinstance(payload.get("rules"), list) else "rules required")
    assert result["payload"] == {"rules": []}
    assert result["session_id"] == "original-session"


def test_invalid_envelope_does_not_retry(tmp_path):
    with pytest.raises(JSONSessionError, match="invalid envelope"):
        session(tmp_path, 'print("[]")', output_format="json")


def test_budget_receipt_is_finished_for_failure(tmp_path):
    receipts = []
    with bind_call_budget("test", lambda request: request, lambda ticket, facts: receipts.append((ticket, dict(facts)))):
        with pytest.raises(JSONSessionError, match="exited with 7"):
            session(tmp_path, 'raise SystemExit(7)')
    assert len(receipts) == 1
    assert receipts[0][0]["kind"] == "harness_session"
    assert receipts[0][1]["sent"] is True
    assert receipts[0][1]["usage"] is None
    assert receipts[0][1]["outcome"] != "completed"


def test_readonly_environment_preserves_model_identity():
    result = readonly_environment({"GH_TOKEN":"secret", "OPENAI_API_KEY":"model",
        "SSH_AUTH_SOCK":"socket", "GIT_CONFIG_COUNT":"1", "GIT_CONFIG_KEY_0":"secret"})
    assert result["OPENAI_API_KEY"] == "model"
    assert "GH_TOKEN" not in result and "SSH_AUTH_SOCK" not in result
    assert "GIT_CONFIG_KEY_0" not in result


def test_zero_repairs_keeps_one_dispatch_even_with_session_id(tmp_path):
    import sys
    from infermatrix_copilot.providers.json_session import JSONSessionError, run_readonly_json
    count = tmp_path / "count"
    cli = tmp_path / "fake_cursor.py"
    cli.write_text("import json,pathlib\np=pathlib.Path(" + repr(str(count)) + ")\np.write_text(str(int(p.read_text())+1) if p.exists() else '1')\nprint(json.dumps({'session_id':'same-session','result':'invalid-json'}))\n")
    with pytest.raises(JSONSessionError) as caught:
        run_readonly_json("classification", cwd=tmp_path, command=[sys.executable, str(cli)],
            provider="cursor", output_schema={"type":"object"}, output_format="json",
            idle_timeout_s=5, absolute_timeout_s=5, max_repair_attempts=0)
    assert caught.value.failure_class == "invalid_result"
    assert count.read_text() == "1"
