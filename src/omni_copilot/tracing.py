"""Portable agent trace + timing recorder (zero external dependencies).

Records a run as a tree of **spans** (OpenTelemetry-shaped: trace_id, span_id,
parent, start, end, attributes) to an append-only JSONL file — one line per
span, written at span close, so a killed run keeps everything that finished.

Works in **both synchronous and asyncio** code: ``span()`` is a plain context
manager used with ``with`` and is safe wrapped around ``await``. Parent/child
nesting propagates through a ``contextvars.ContextVar``, which is copied per
asyncio task, so parallel agents get correct, independent trees.

    from agent import tracing
    tracing.init(run_id, log_dir / "trace.jsonl")
    with tracing.span("phase", phase="phase2"):
        with tracing.span("agent", label="module:scheduler"):
            with tracing.span("llm", model=model) as sp:
                ... call the model ...
                sp.mark_ttft()                      # at first token
                sp.set(prompt_tokens=..., completion_tokens=...)

Enable with env ``AGENT_TRACE=1`` (the default). ``AGENT_TRACE=0`` turns every
``span()`` into a zero-cost no-op.

The recorder is shared verbatim by the rebase-agent, the copilot, and the
personal-agent — keep the three copies identical.
"""
from __future__ import annotations

import contextlib
import contextvars
import json
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Iterator, Optional

_ENABLED = os.environ.get("AGENT_TRACE", "1").strip().lower() not in ("0", "false", "no", "off", "")
_current: "contextvars.ContextVar[Optional[Span]]" = contextvars.ContextVar("trace_span", default=None)


class Span:
    """One timed node. ``set()`` adds attributes; ``mark_ttft()`` stamps the
    first-token time so decode throughput can be derived from ``gen_s``."""

    __slots__ = ("name", "trace_id", "span_id", "parent", "start", "end", "attr", "_ttft")

    def __init__(self, name: str, trace_id: str, parent: Optional[str], attr: dict):
        self.name = name
        self.trace_id = trace_id
        self.span_id = uuid.uuid4().hex[:12]
        self.parent = parent
        self.start = time.time()
        self.end: Optional[float] = None
        self.attr = attr
        self._ttft: Optional[float] = None

    @property
    def elapsed_s(self) -> float:
        return (self.end or time.time()) - self.start

    @property
    def gen_s(self) -> float:
        """Seconds spent generating (since first token, if marked)."""
        base = self._ttft if self._ttft is not None else self.start
        return (self.end or time.time()) - base

    def set(self, **attrs: Any) -> "Span":
        self.attr.update(attrs)
        return self

    def mark_ttft(self) -> None:
        if self._ttft is None:
            self._ttft = time.time()
            self.attr["ttft_ms"] = round((self._ttft - self.start) * 1000, 1)


class _NullSpan:
    """Zero-cost stand-in when tracing is disabled or uninitialized."""

    __slots__ = ()

    def set(self, **attrs: Any) -> "_NullSpan":
        return self

    def mark_ttft(self) -> None:
        pass

    @property
    def gen_s(self) -> float:
        return 0.0

    @property
    def elapsed_s(self) -> float:
        return 0.0


_NULL = _NullSpan()


class Tracer:
    def __init__(self, run_id: str, out_path: os.PathLike | str):
        self.run_id = run_id
        self.path = Path(out_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._inflight = 0  # concurrent llm spans — the effective batch size

    def _write(self, span: Span) -> None:
        rec = {
            "t": "span",
            "trace_id": span.trace_id,
            "span_id": span.span_id,
            "parent": span.parent,
            "name": span.name,
            "start": round(span.start, 6),
            "end": round(span.end or span.start, 6),
            "dur_ms": round(((span.end or span.start) - span.start) * 1000, 1),
            "attr": span.attr,
        }
        line = json.dumps(rec, ensure_ascii=False, default=str)
        with self._lock, self.path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    @contextlib.contextmanager
    def span(self, name: str, **attr: Any) -> Iterator[Any]:
        if not _ENABLED:
            yield _NULL
            return
        parent = _current.get()
        sp = Span(name, self.run_id, parent.span_id if parent else None, dict(attr))
        is_llm = name == "llm"
        if is_llm:  # snapshot concurrency at request start
            with self._lock:
                self._inflight += 1
                sp.attr["inflight"] = self._inflight
        token = _current.set(sp)
        try:
            yield sp
        finally:
            sp.end = time.time()
            if is_llm:
                with self._lock:
                    self._inflight -= 1
            _current.reset(token)
            try:
                self._write(sp)
            except Exception:
                pass  # tracing must never break the agent


# ── module-level default tracer + helpers ─────────────────────────────────────
_default: Optional[Tracer] = None


def init(run_id: str, out_path: os.PathLike | str) -> Optional[Tracer]:
    """Install the default tracer for this run. No-op (returns None) when
    tracing is disabled via AGENT_TRACE=0."""
    global _default
    if not _ENABLED:
        return None
    _default = Tracer(run_id, out_path)
    return _default


def span(name: str, **attr: Any):
    """Open a span on the default tracer. A plain ``with`` context manager,
    safe in sync and async code. No-op if tracing is off or uninitialized."""
    if _default is None or not _ENABLED:
        return contextlib.nullcontext(_NULL)
    return _default.span(name, **attr)


def enabled() -> bool:
    return _ENABLED and _default is not None


def set_usage(sp: Any, usage: Any, stop_reason: str = "") -> None:
    """Convenience: copy Anthropic ``response.usage`` onto an ``llm`` span and
    derive tokens/sec. Accepts the SDK usage object or a plain dict; tolerant of
    missing fields (cache token names differ across providers)."""
    def _g(name: str) -> int:
        if usage is None:
            return 0
        if isinstance(usage, dict):
            return int(usage.get(name, 0) or 0)
        return int(getattr(usage, name, 0) or 0)

    out = _g("output_tokens")
    sp.set(
        prompt_tokens=_g("input_tokens"),
        completion_tokens=out,
        cache_read_tokens=_g("cache_read_input_tokens"),
        cache_creation_tokens=_g("cache_creation_input_tokens"),
    )
    if stop_reason:
        sp.set(stop_reason=stop_reason)
    gen = getattr(sp, "gen_s", 0.0)
    if out and gen > 0:
        sp.set(tokens_per_sec=round(out / gen, 1))


# ── reporting ─────────────────────────────────────────────────────────────────
def load_spans(trace_path: os.PathLike | str) -> list[dict]:
    spans = []
    p = Path(trace_path)
    if not p.exists():
        return spans
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("t") == "span":
            spans.append(rec)
    return spans


def _pctl(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    i = min(len(s) - 1, int(q * len(s)))
    return s[i]


def report(trace_path: os.PathLike | str) -> str:
    """Human-readable optimization rollup: per-phase wall/LLM/tool time, the
    inference-engine view (TTFT, decode rate, cache %, concurrency, context
    growth), and the top time sinks."""
    spans = load_spans(trace_path)
    if not spans:
        return f"no spans in {trace_path}"

    by_name: dict[str, list[dict]] = {}
    for s in spans:
        by_name.setdefault(s["name"], []).append(s)
    llm = by_name.get("llm", [])
    tools = by_name.get("tool", [])

    lines = [f"TRACE {spans[0]['trace_id']}   spans={len(spans)}"]

    # per-phase rollup
    phases = by_name.get("phase", [])
    if phases:
        lines.append("\n  phase        wall_s   llm_calls  tool_calls  in_tok    out_tok")
        span_by_id = {s["span_id"]: s for s in spans}

        def _phase_of(s: dict) -> Optional[str]:
            cur = s
            seen = 0
            while cur and seen < 12:
                if cur["name"] == "phase":
                    return cur["attr"].get("phase") or cur["span_id"]
                cur = span_by_id.get(cur.get("parent"))
                seen += 1
            return None

        for ph in phases:
            pname = ph["attr"].get("phase", ph["span_id"])
            plls = [s for s in llm if _phase_of(s) == pname]
            ptools = [s for s in tools if _phase_of(s) == pname]
            in_tok = sum(s["attr"].get("prompt_tokens", 0) for s in plls)
            out_tok = sum(s["attr"].get("completion_tokens", 0) for s in plls)
            lines.append(f"  {pname:<11} {ph['dur_ms']/1000:>7.1f}  {len(plls):>9}  "
                         f"{len(ptools):>10}  {in_tok:>7}  {out_tok:>7}")

    # inference-engine view
    if llm:
        ttfts = [s["attr"]["ttft_ms"] for s in llm if "ttft_ms" in s["attr"]]
        rates = [s["attr"]["tokens_per_sec"] for s in llm if "tokens_per_sec" in s["attr"]]
        prompts = [s["attr"].get("prompt_tokens", 0) for s in llm]
        comps = [s["attr"].get("completion_tokens", 0) for s in llm]
        cache_read = sum(s["attr"].get("cache_read_tokens", 0) for s in llm)
        total_in = sum(prompts) or 1
        inflight = [s["attr"].get("inflight", 1) for s in llm]
        lines.append("\nLLM (inference-engine view)")
        lines.append(f"  calls              {len(llm)}")
        if ttfts:
            lines.append(f"  TTFT     p50 {_pctl(ttfts,0.5):.0f}ms   p95 {_pctl(ttfts,0.95):.0f}ms")
        if rates:
            lines.append(f"  decode   p50 {_pctl(rates,0.5):.0f} tok/s   p95 {_pctl(rates,0.95):.0f} tok/s")
        lines.append(f"  prompt tokens      median {int(_pctl(prompts,0.5))}   max {max(prompts) if prompts else 0}")
        lines.append(f"  completion tokens  median {int(_pctl(comps,0.5))}   max {max(comps) if comps else 0}")
        lines.append(f"  prompt-cache read  {100*cache_read/total_in:.1f}%   "
                     f"({'recomputing prefill each turn — caching opportunity' if cache_read/total_in < 0.2 else 'ok'})")
        lines.append(f"  concurrency        peak {max(inflight)}   mean {sum(inflight)/len(inflight):.1f}   (effective batch size)")

    # top time sinks
    sinks = sorted(spans, key=lambda s: s.get("dur_ms", 0), reverse=True)
    lines.append("\nTop time sinks")
    for s in sinks[:8]:
        label = s["attr"].get("label") or s["attr"].get("tool") or s["attr"].get("model") or ""
        lines.append(f"  {s['name']:<8} {s['dur_ms']/1000:>7.1f}s  {label}")
    return "\n".join(lines)


def _main() -> int:
    import sys

    if len(sys.argv) < 2:
        print("usage: python -m omni_copilot.tracing <trace.jsonl | run_id>")
        return 1
    arg = sys.argv[1]
    path = Path(arg)
    if not path.exists():
        # allow passing a run_id — look under .copilot/runs/<id>/trace.jsonl
        cand = Path("runs") / arg / "trace.jsonl"
        if cand.exists():
            path = cand
    print(report(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
