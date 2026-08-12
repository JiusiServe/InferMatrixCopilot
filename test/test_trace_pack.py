"""Guardrails for `eval/dataset/trace_pack.py` — the durable-trace packer.

These pin the three properties that make a packed trace trustworthy: it round-trips
exactly (modulo the declared path substitution), it never leaks the operating user's
paths, and `verify_arm` actually fails when a trace is missing or damaged. The last one
matters most: a gate that cannot fail is the state the wave-1 Strict arm was already in.
"""

import gzip
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
DATASET = ROOT / "eval" / "dataset"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def tp():
    return _load("trace_pack", DATASET / "trace_pack.py")


def _cc_events(home, workspace):
    """A Claude Code stream shaped like the real thing, carrying machine paths."""
    return [
        {"type": "system", "subtype": "init", "model": "claude-opus-5",
         "cwd": f"{workspace}/vllm-omni", "skills": [], "mcp_servers": ["x"]},
        {"type": "assistant", "message": {"model": "claude-opus-5", "content": [
            {"type": "tool_use", "id": "t1", "name": "Read",
             "input": {"file_path": f"{home}/checkout/a.py"}},
            {"type": "tool_use", "id": "t2", "name": "mcp__c__review",
             "input": {"target": "4893"}}]}},
        {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "t1", "content": "x" * 900}]}},
        {"type": "result", "num_turns": 2, "total_cost_usd": 1.5,
         "usage": {"output_tokens": 10}, "result": "done"},
    ]


def _repetitive_runs(n_msgs=12, size=4000):
    """A copilot run shaped like a real one: call *i* re-sends the whole history.

    The messages must be many, large and individually incompressible. A single repeated
    string is the wrong fixture — gzip collapses that on its own and `inline` correctly
    wins — whereas real history is dozens of distinct multi-KB messages spread over
    megabytes, far outside gzip's 32KB window, which is exactly where content-addressed
    dedup earns its keep.
    """
    import hashlib
    msgs = [{"role": "user", "content": "".join(
        hashlib.sha256(f"{i}:{j}".encode()).hexdigest() for j in range(size // 64))}
        for i in range(n_msgs)]
    return {"runs": [{"run": "run-1", "events": [
        {"kind": "llm.request", "payload": msgs[:i + 1]} for i in range(n_msgs)]}]}


def test_round_trip_is_exact_modulo_the_declared_scrub(tp):
    home, ws = str(Path.home()), str(tp.WORKSPACE)
    events = _cc_events(home, ws)
    packed = tp.pack(tp.KIND_CLAUDE_CODE, {"events": events}, [], {"arm": "t"})
    assert tp.restore(packed) == tp.scrub({"events": events}, tp.path_roots())


def test_interning_round_trips_and_dedupes_repeated_history(tp):
    """The Strict shape: one message quoted by every later call must be stored once."""
    msg = {"role": "user", "content": "m" * 2000}
    calls = [{"kind": "llm.request", "payload": [msg] * (i + 1)} for i in range(6)]
    blobs = {}
    compacted = tp.intern(tp.scrub(calls, tp.path_roots()), blobs)
    assert tp.expand(compacted, blobs) == calls
    bodies = [b for b in blobs.values() if isinstance(b, str) and b.startswith("mm")]
    assert len(bodies) == 1, "the repeated message body was stored more than once"


def test_encoding_is_chosen_by_measurement_not_by_shape(tp):
    """Interning must lose on low-redundancy streams and win on repetitive ones."""
    home, ws = str(Path.home()), str(tp.WORKSPACE)
    cc = tp.pack(tp.KIND_CLAUDE_CODE, {"events": _cc_events(home, ws)}, [], {})
    strict = tp.pack(tp.KIND_COPILOT_CLI, _repetitive_runs(), [], {})
    assert strict["meta"]["encoding"] == "interned"
    assert cc["meta"]["encoding"] == "inline"
    for packed in (cc, strict):
        sizes = packed["meta"]["encoding_sizes_gz"]
        assert sizes[packed["meta"]["encoding"]] == min(sizes.values())


def test_machine_paths_never_survive_into_the_pack(tp):
    home, ws = str(Path.home()), str(tp.WORKSPACE)
    packed = tp.pack(tp.KIND_CLAUDE_CODE, {"events": _cc_events(home, ws)}, [],
                     {"arm": "t", "cwd": f"{home}/secret"})
    blob = json.dumps(packed, ensure_ascii=False)
    assert not tp.residual_paths(blob, tp.path_roots())
    assert "$HOME" in blob or "$WORKSPACE" in blob


def test_path_map_records_hashes_not_the_paths_it_removed(tp):
    packed = tp.pack(tp.KIND_CLAUDE_CODE, {"events": []}, [], {})
    for placeholder, value in packed["meta"]["path_map"].items():
        assert placeholder.startswith("$") or "$USER" in placeholder
        assert "/" not in value, "path_map reintroduced the root the scrub removed"


def test_verify_arm_reports_a_missing_trace(tp, tmp_path):
    (tmp_path / "pr1.md").write_text("review body")
    problems, checked = tp.verify_arm(tmp_path)
    assert checked == 0
    assert any("MISSING" in p for p in problems)


def test_verify_arm_passes_on_a_freshly_written_trace(tp, tmp_path):
    (tmp_path / "pr1.md").write_text("review body")
    tp.pack_claude_code(tmp_path, "pr1", _cc_events(str(Path.home()),
                                                    str(tp.WORKSPACE)), {"arm": "t"})
    problems, checked = tp.verify_arm(tmp_path)
    assert (problems, checked) == ([], 1)


def test_verify_arm_catches_a_dangling_blob_reference(tp, tmp_path):
    (tmp_path / "pr1.md").write_text("body")
    packed = tp.pack(tp.KIND_COPILOT_CLI, _repetitive_runs(), [], {})
    assert packed["meta"]["encoding"] == "interned"
    packed["blobs"].popitem()
    tp.write(tmp_path, "pr1", packed)
    problems, _ = tp.verify_arm(tmp_path)
    assert any("dangling blob ref" in p for p in problems)


def test_verify_arm_catches_a_corrupted_blob(tp, tmp_path):
    (tmp_path / "pr1.md").write_text("body")
    packed = tp.pack(tp.KIND_COPILOT_CLI, _repetitive_runs(), [], {})
    digest = next(iter(packed["blobs"]))
    packed["blobs"][digest] = "tampered"
    tp.write(tmp_path, "pr1", packed)
    problems, _ = tp.verify_arm(tmp_path)
    assert any("fails its own hash" in p for p in problems)


def test_written_bytes_are_deterministic(tp, tmp_path):
    """A repack that changed nothing must not surface as a diff in review."""
    events = _cc_events(str(Path.home()), str(tp.WORKSPACE))
    meta = {"arm": "t", "stem": "pr1", "recorded_at": "fixed"}
    first = tp.pack_claude_code(tmp_path, "pr1", events, meta).read_bytes()
    second = tp.pack_claude_code(tmp_path, "pr1", events, meta).read_bytes()
    assert first == second
    assert gzip.decompress(first)


def test_copilot_reader_keeps_every_retry_attempt(tp, tmp_path):
    """Retried Strict items are where a systematic failure would show; both attempts
    must survive, not just the one that produced the RUN_REPORT."""
    for name in ("run-20260101-000001-aaaaaa", "run-20260101-000002-bbbbbb"):
        d = tmp_path / name
        d.mkdir()
        (d / "run_trace.jsonl").write_text(json.dumps({"kind": "task", "run": name}))
        (d / "metrics.json").write_text(json.dumps({"run": name}))
    streams, sources = tp.read_copilot_run(tmp_path)
    assert [r["run"] for r in streams["runs"]] == [
        "run-20260101-000001-aaaaaa", "run-20260101-000002-bbbbbb"]
    assert len(sources) == 4
