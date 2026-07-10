"""Vendored tracer + wiring into llm.create."""
import importlib


def _fresh(monkeypatch, enabled="1"):
    monkeypatch.setenv("AGENT_TRACE", enabled)
    import omni_copilot.tracing as tracing
    importlib.reload(tracing)
    return tracing


def test_span_tree(monkeypatch, tmp_path):
    tr = _fresh(monkeypatch)
    tr.init("run-1", tmp_path / "trace.jsonl")
    with tr.span("step", step="rebase"):
        with tr.span("llm", model="m") as sp:
            sp.set(prompt_tokens=9)
    spans = {s["name"]: s for s in tr.load_spans(tmp_path / "trace.jsonl")}
    assert spans["llm"]["parent"] == spans["step"]["span_id"]
    assert spans["step"]["attr"]["step"] == "rebase"
    assert spans["llm"]["attr"]["inflight"] == 1


def test_disabled_noop(monkeypatch, tmp_path):
    tr = _fresh(monkeypatch, enabled="0")
    assert tr.init("r", tmp_path / "t.jsonl") is None
    with tr.span("llm", model="m") as sp:
        sp.mark_ttft()
        sp.set(x=1)
    assert not (tmp_path / "t.jsonl").exists()


def test_llm_create_records_span(monkeypatch, tmp_path):
    tr = _fresh(monkeypatch)
    tr.init("run-llm", tmp_path / "trace.jsonl")
    from omni_copilot.config import Settings
    from omni_copilot.llm import LLM

    class Usage:
        input_tokens = 800
        output_tokens = 12
        cache_read_input_tokens = 300

    class Resp:
        stop_reason = "tool_use"
        usage = Usage()
        content = []

    llm = LLM(Settings(anthropic_api_key="x"))
    monkeypatch.setattr(llm._client.messages, "create", lambda **kw: Resp())
    reply = llm.create(system="s", messages=[{"role": "user", "content": "hi"}])
    assert reply.usage["input_tokens"] == 800
    span = [s for s in tr.load_spans(tmp_path / "trace.jsonl") if s["name"] == "llm"][0]
    assert span["attr"]["prompt_tokens"] == 800
    assert span["attr"]["cache_read_tokens"] == 300
    assert span["attr"]["stop_reason"] == "tool_use"
