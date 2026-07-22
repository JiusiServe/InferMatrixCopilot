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


# ── run header: which workflow produced this trace ───────────────────────────
def test_run_meta_round_trip_and_report_header(monkeypatch, tmp_path):
    tr = _fresh(monkeypatch)
    path = tmp_path / "trace.jsonl"
    tr.init("run-meta", path)
    tr.run_meta(playbook="issue-triage@2", task_kind="issue_filter",
                repo="vllm-omni", tier="L2")
    with tr.span("step", step="issue.fetch", step_id="fetch"):
        pass
    meta = tr.load_run_meta(path)
    assert meta["playbook"] == "issue-triage@2" and meta["repo"] == "vllm-omni"
    # the header must not pollute the span stream
    assert [s["name"] for s in tr.load_spans(path)] == ["step"]
    out = tr.report(path)
    assert "playbook=issue-triage@2" in out and "task_kind=issue_filter" in out


def test_run_meta_redacts_non_allowlisted_params(monkeypatch, tmp_path):
    """A trace gets shared for workload analysis, so free-form params (paths,
    shell commands) must not ride along -- keys yes, values only if allowlisted."""
    tr = _fresh(monkeypatch)
    path = tmp_path / "trace.jsonl"
    tr.init("run-redact", path)
    tr.run_meta(playbook="p@1", params={
        "limit": 5,                                  # allowlisted -> kept
        "review_depth": "full",                      # allowlisted -> kept
        "command": "omni-rebase --token s3cr3t",     # free-form  -> redacted
        "state_file": "/home/me/private/state.json",  # path      -> redacted
    })
    p = tr.load_run_meta(path)["params"]
    assert p["limit"] == 5 and p["review_depth"] == "full"
    assert p["command"] == "<redacted>" and p["state_file"] == "<redacted>"
    assert set(p) == {"limit", "review_depth", "command", "state_file"}  # keys kept
    assert "s3cr3t" not in path.read_text() and "private" not in path.read_text()


def test_run_meta_is_size_bounded(monkeypatch, tmp_path):
    tr = _fresh(monkeypatch)
    path = tmp_path / "trace.jsonl"
    tr.init("run-big", path)
    tr.run_meta(playbook="p@1", params={f"k{i}": f"v{i}" for i in range(500)})
    line = [l for l in path.read_text().splitlines() if l.strip()][0]
    assert len(line) <= 2048
    meta = tr.load_run_meta(path)
    assert meta["truncated"] is True and "params" not in meta
    assert meta["playbook"] == "p@1"        # identity survives the truncation


def test_resume_appends_a_second_header_and_last_wins(monkeypatch, tmp_path):
    """Resuming re-inits onto the same trace file. Both executions are recorded;
    readers take the last as current and the report says the trace is spliced."""
    tr = _fresh(monkeypatch)
    path = tmp_path / "trace.jsonl"
    tr.init("run-r", path)
    tr.run_meta(playbook="p@1", resuming=False)
    with tr.span("step", step="a", step_id="a"):
        pass
    tr.init("run-r", path)                   # <- resume: same file
    tr.run_meta(playbook="p@1", resuming=True)
    with tr.span("step", step="b", step_id="b"):
        pass
    assert len(tr.load_run_metas(path)) == 2
    assert tr.load_run_meta(path)["resuming"] is True     # last wins
    assert len(tr.load_spans(path)) == 2                  # spans from both
    assert "resumed ×2" in tr.report(path)


def test_report_without_a_run_header_still_renders(monkeypatch, tmp_path):
    """Traces written before headers existed must keep reporting."""
    tr = _fresh(monkeypatch)
    path = tmp_path / "trace.jsonl"
    tr.init("run-old", path)
    with tr.span("step", step="issue.fetch"):
        with tr.span("llm", model="m") as sp:
            tr.set_usage(sp, {"input_tokens": 10, "output_tokens": 2})
    assert tr.load_run_meta(path) == {}
    out = tr.report(path)
    assert "TRACE run-old" in out and "issue.fetch" in out


# ── rollup attribution ───────────────────────────────────────────────────────
def test_rollup_falls_back_to_steps_and_attributes_per_span(monkeypatch, tmp_path):
    """Two foreach siblings share a step name; each row must get only its own
    calls/tokens. Keying the rollup by name would fold them together."""
    tr = _fresh(monkeypatch)
    path = tmp_path / "trace.jsonl"
    tr.init("run-fan", path)
    for mod, ntok in (("model_executor", 100), ("scheduler", 700)):
        with tr.span("step", step="rebase.module_rebase", step_id="wave1", item=mod):
            with tr.span("llm", model="m") as sp:
                tr.set_usage(sp, {"input_tokens": ntok, "output_tokens": 1})
    out = tr.report(path)
    rows = [l for l in out.splitlines() if "wave1[" in l]
    assert len(rows) == 2                       # not merged into one row
    me = [r for r in rows if "model_executor" in r][0]
    sc = [r for r in rows if "scheduler" in r][0]
    assert me.split()[-2:] == ["100", "1"]      # in_tok / out_tok, own only
    assert sc.split()[-2:] == ["700", "1"]
    assert "  step " in out and "phase" not in out.split("Top time sinks")[0]


def test_rollup_does_not_double_count_a_retry(monkeypatch, tmp_path):
    tr = _fresh(monkeypatch)
    path = tmp_path / "trace.jsonl"
    tr.init("run-retry", path)
    for attempt, ntok in ((1, 50), (2, 60)):
        with tr.span("step", step="s.flaky", step_id="flaky", attempt=attempt):
            with tr.span("llm", model="m") as sp:
                tr.set_usage(sp, {"input_tokens": ntok, "output_tokens": 1})
    out = tr.report(path)
    rows = [l for l in out.splitlines() if l.strip().startswith("flaky")]
    assert len(rows) == 2
    assert rows[0].split()[-2] == "50"
    assert "flaky#2" in rows[1] and rows[1].split()[-2] == "60"
