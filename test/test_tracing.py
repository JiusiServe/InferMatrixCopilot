"""Vendored tracer + wiring into llm.create."""
import importlib


def _fresh(monkeypatch, enabled="1", io=None):
    monkeypatch.setenv("AGENT_TRACE", enabled)
    if io is None:
        monkeypatch.delenv("AGENT_TRACE_IO", raising=False)
    else:
        monkeypatch.setenv("AGENT_TRACE_IO", io)
    import infermatrix_copilot.tracing as tracing
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


def test_cache_read_pct_counts_cached_tokens_in_the_denominator(monkeypatch, tmp_path):
    """`prompt_tokens` excludes cached input, so the hit rate must divide by the
    whole prefill. Dividing by sum(prompt_tokens) alone reported e.g. 714%."""
    tr = _fresh(monkeypatch)
    path = tmp_path / "t.jsonl"
    tr.init("run-cache", path)
    with tr.span("llm", model="m") as sp:
        tr.set_usage(sp, {"input_tokens": 1000, "output_tokens": 10,
                          "cache_read_input_tokens": 0})
    with tr.span("llm", model="m") as sp:
        tr.set_usage(sp, {"input_tokens": 1000, "output_tokens": 10,
                          "cache_read_input_tokens": 9000})
    out = tr.report(path)
    # 9000 cached / (2000 uncached + 9000 cached) == 81.8%, not 450%
    assert "prompt-cache read  81.8%" in out
    assert "ok" in out.split("prompt-cache read")[1].split("\n")[0]


def test_cache_read_pct_still_flags_an_uncached_run(monkeypatch, tmp_path):
    tr = _fresh(monkeypatch)
    path = tmp_path / "t.jsonl"
    tr.init("run-nocache", path)
    with tr.span("llm", model="m") as sp:
        tr.set_usage(sp, {"input_tokens": 5000, "output_tokens": 10,
                          "cache_read_input_tokens": 0})
    out = tr.report(path)
    assert "prompt-cache read  0.0%" in out
    assert "caching opportunity" in out


def test_top_sinks_label_non_llm_spans(monkeypatch, tmp_path):
    """`step`/`phase` spans name themselves under their own attr key; a
    tool/model-only lookup rendered the biggest sinks as blank rows."""
    tr = _fresh(monkeypatch)
    path = tmp_path / "t.jsonl"
    tr.init("run-sinks", path)
    with tr.span("phase", phase="triage-phase"):
        with tr.span("step", step="agent.triage_issues"):
            with tr.span("tool", tool="run_gh"):
                pass
    sinks = tr.report(path).split("Top time sinks")[1]
    assert "agent.triage_issues" in sinks
    assert "triage-phase" in sinks
    assert "run_gh" in sinks


def test_llm_create_records_span(monkeypatch, tmp_path):
    tr = _fresh(monkeypatch)
    tr.init("run-llm", tmp_path / "trace.jsonl")
    from infermatrix_copilot.config import Settings
    from infermatrix_copilot.llm import LLM

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


def test_usage_counts_extracts_tokens_from_object_and_dict(monkeypatch):
    tr = _fresh(monkeypatch)
    expected = {"input_tokens": 800, "output_tokens": 12,
                "cache_read_tokens": 300, "cache_creation_tokens": 5}
    assert tr.usage_counts({"input_tokens": 800, "output_tokens": 12,
                            "cache_read_input_tokens": 300,
                            "cache_creation_input_tokens": 5}) == expected

    class U:
        input_tokens = 800
        output_tokens = 12
        cache_read_input_tokens = 300
        cache_creation_input_tokens = 5
    assert tr.usage_counts(U()) == expected
    # a provider omitting cache fields (or no usage at all) must not raise
    assert tr.usage_counts(None)["input_tokens"] == 0
    assert tr.usage_counts({"input_tokens": 7})["cache_read_tokens"] == 0


def test_llm_create_records_io_text_and_tokens(monkeypatch, tmp_path):
    """End-to-end through llm.create: with AGENT_TRACE_IO=1 the request text,
    the response text and that call's token counts all land on events.jsonl.
    The endpoint exposes no token ids, so text is the replayable stand-in."""
    tr = _fresh(monkeypatch, io="1")
    tr.init("run-io", tmp_path / "trace.jsonl")
    from infermatrix_copilot.config import Settings
    from infermatrix_copilot.llm import LLM

    class Usage:
        input_tokens = 1000
        output_tokens = 3
        cache_read_input_tokens = 9000
        cache_creation_input_tokens = 0

    class TextBlock:
        type = "text"
        text = "hello there"

    class Resp:
        stop_reason = "end_turn"
        usage = Usage()
        content = [TextBlock()]

    llm = LLM(Settings(anthropic_api_key="x"))
    monkeypatch.setattr(llm._client.messages, "create", lambda **kw: Resp())
    llm.create(system="s", messages=[{"role": "user", "content": "hi"}])

    events = tr.load_events(tmp_path / "trace.jsonl")
    req = [e for e in events if e["kind"] == "llm.request"][0]
    resp = [e for e in events if e["kind"] == "llm.response"][0]
    assert req["payload"][0]["content"] == "hi"        # input text recorded
    assert resp["text"] == "hello there"               # output text recorded
    assert resp["input_tokens"] == 1000                # + counts, same record
    assert resp["output_tokens"] == 3
    assert resp["cache_read_tokens"] == 9000
    assert resp["span_id"] == req["span_id"]           # joinable to the span
    assert "in=1000 out=3 cached=9000" in tr.render_events(tmp_path / "trace.jsonl")
