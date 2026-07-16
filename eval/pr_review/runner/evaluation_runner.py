"""Execute an evaluated agent against fixed, read-only benchmark snapshots."""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ..benchmark.io import load_benchmark
from ..repository import ReadOnlyWorkspace, RepositoryCache, diff_between, verify_commit
from ..storage import RunBundle
from .agent_adapter import AgentAdapter
from .input_builder import build_agent_input
from .output_schema import OutputContractError, parse_agent_output
from .tools import StaticToolExecutor
from .trace_collector import RunMetadata, ToolCallStats, TraceCollector


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _usage_from_trace(trace: TraceCollector) -> tuple[int, int, int, dict[str, ToolCallStats], list[str]]:
    input_tokens = output_tokens = cached_tokens = 0
    tools: dict[str, ToolCallStats] = {}
    violations: list[str] = []
    for event in trace.events():
        kind = event.get("kind")
        if kind == "model_usage":
            input_tokens += int(event.get("input_tokens", 0))
            output_tokens += int(event.get("output_tokens", 0))
            cached_tokens += int(event.get("cached_tokens", 0))
        elif kind == "tool_call":
            name = str(event.get("tool", "unknown"))
            current = tools.get(name, ToolCallStats())
            status = event.get("status", "succeeded")
            updates = {
                "total": current.total + 1,
                "succeeded": current.succeeded + (status == "succeeded"),
                "failed": current.failed + (status == "failed"),
                "refused": current.refused + (status == "refused"),
                "returned_bytes": current.returned_bytes + int(event.get("returned_bytes", 0)),
            }
            tools[name] = ToolCallStats.model_validate(updates)
        elif kind == "policy_violation":
            violations.append(str(event.get("violation", event.get("reason", "unknown"))))
    return input_tokens, output_tokens, cached_tokens, tools, violations


def run_benchmark(
    *,
    manifest_path: str | Path,
    repository_cache: str | Path,
    output_dir: str | Path,
    adapter: AgentAdapter,
    model: str = "",
    model_parameters: dict | None = None,
    prompt_version: str = "unknown",
    benchmark_filter: set[str] | None = None,
) -> Path:
    manifest, items = load_benchmark(manifest_path)
    bundle = RunBundle(output_dir)
    cache = RepositoryCache(repository_cache)
    run_group = uuid.uuid4().hex
    for item in items:
        if benchmark_filter and item.benchmark_id not in benchmark_filter:
            continue
        if item.invalidated:
            continue
        repo = cache.require(item.repository)
        base_sha = verify_commit(repo, item.base_sha)
        head_sha = verify_commit(repo, item.head_sha)
        diff = diff_between(repo, base_sha, head_sha)
        trace = TraceCollector(bundle.traces / f"{item.benchmark_id}.jsonl")
        raw = ""
        review = None
        repaired = False
        output_failure = False
        agent_failure = False
        failure_reason = None
        elapsed_ms = 0
        started_at = _utc_now()
        finished_at = started_at
        with ReadOnlyWorkspace(repo, head_sha, base_sha=base_sha) as workspace:
            agent_input = build_agent_input(item, diff=diff)
            tools = StaticToolExecutor(
                workspace=workspace,
                allowed_commits={base_sha, head_sha},
                trace=trace,
            )
            started_at = _utc_now()
            start = time.monotonic()
            trace.record("agent_started", benchmark_id=item.benchmark_id)
            try:
                raw = adapter.review(agent_input, workspace=str(workspace), tools=tools, trace=trace)
            except Exception as exc:
                agent_failure = True
                failure_reason = repr(exc)
                trace.record("agent_failure", error=repr(exc))
            finally:
                elapsed_ms = int((time.monotonic() - start) * 1000)
                finished_at = _utc_now()
                trace.record("agent_finished", benchmark_id=item.benchmark_id, wall_time_ms=elapsed_ms)

            if not agent_failure:
                try:
                    review, repaired = parse_agent_output(
                        raw, repo_root=workspace, base_sha=base_sha
                    )
                except OutputContractError as exc:
                    output_failure = True
                    failure_reason = str(exc)
                    trace.record("output_contract_failure", error=str(exc), repaired=exc.repaired)
        raw_dir = bundle.root / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / f"{item.benchmark_id}.txt").write_text(raw, encoding="utf-8")
        if review is not None:
            bundle.write_prediction(item.benchmark_id, review)
        input_tokens, output_tokens, cached_tokens, tools, violations = _usage_from_trace(trace)
        metadata = RunMetadata(
            run_id=f"{run_group}:{item.benchmark_id}",
            benchmark_version=manifest.benchmark_version,
            benchmark_id=item.benchmark_id,
            agent_version=adapter.version,
            model=model,
            model_parameters=model_parameters or {},
            prompt_version=prompt_version,
            tool_policy_version="pr-review-tool-policy-v0.1",
            repository_sha=head_sha,
            started_at=started_at,
            finished_at=finished_at,
            output_contract_valid=not output_failure and not agent_failure,
            output_contract_repaired=repaired,
            output_contract_failure=output_failure,
            agent_failure=agent_failure,
            failure_reason=failure_reason,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_tokens=cached_tokens,
            wall_time_ms=elapsed_ms,
            tool_calls=tools,
            policy_violations=violations,
        )
        bundle.write_metadata(item.benchmark_id, metadata)
    (bundle.root / "run.json").write_text(json.dumps({
        "run_group": run_group,
        "benchmark_version": manifest.benchmark_version,
        "agent_version": adapter.version,
    }, indent=2) + "\n", encoding="utf-8")
    return bundle.root
