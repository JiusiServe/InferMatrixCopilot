"""Thin MCP: curated review knowledge for the host model, with no model client."""

from __future__ import annotations

import json
import signal
import sys
import uuid
from pathlib import Path
from typing import Any

from .knowledge_docs import KnowledgeDocs, KnowledgeDocsError

_ROOT = Path(__file__).resolve().parents[2]
_KNOWLEDGE = _ROOT / "knowledge"
_RUN_ROOT = Path.home() / ".infermatrix-copilot" / "host-review-runs"
_STAGES = ("evidence", "gates", "review", "verify", "complete")
_ROUTES = {
    "vllm_omni/config/": "repos/vllm-omni/components/config/rules.md",
    "vllm_omni/core/": "repos/vllm-omni/components/scheduler/rules.md",
    "vllm_omni/entrypoints/": "repos/vllm-omni/components/serving/rules.md",
    "vllm_omni/model_executor/": "repos/vllm-omni/components/model-executor/rules.md",
    "vllm_omni/models/": "repos/vllm-omni/models/_index.md",
    "vllm_omni/diffusion/": "repos/vllm-omni/components/diffusion/rules.md",
}


def _docs(repo: str) -> KnowledgeDocs:
    repo = (repo or "vllm-omni").strip()
    repo_dir = _KNOWLEDGE / "repos" / repo
    if not repo_dir.is_dir():
        raise KnowledgeDocsError(f"unsupported knowledge repo: {repo}")
    return KnowledgeDocs(_KNOWLEDGE, f"repos/{repo}")


def _guard(fn):
    try:
        return fn()
    except (KnowledgeDocsError, FileNotFoundError, ValueError) as exc:
        return {"error": str(exc)}


def _review_knowledge(repo: str, changed_files: list[str]) -> list[dict]:
    docs = _docs(repo)
    paths = [
        "general/review/_index.md",
        f"repos/{repo}/rules.md",
        f"repos/{repo}/review/_index.md",
        f"repos/{repo}/review/guides/maintainer-pattern-routing.md",
    ]
    if repo == "vllm-omni":
        folded_files = [str(path).replace("\\", "/").casefold()
                        for path in changed_files]
        for prefix, doc in _ROUTES.items():
            if any(prefix in path for path in folded_files):
                paths.append(doc)
    entries = []
    for path in dict.fromkeys(paths):
        try:
            entries.append(docs.read(path, limit=24_000))
        except FileNotFoundError:
            continue
    return entries


def _run_path(run_id: str) -> Path:
    if not run_id or any(ch not in "0123456789abcdef" for ch in run_id):
        raise ValueError("invalid run_id")
    return _RUN_ROOT / f"{run_id}.json"


def _load_run(run_id: str) -> dict:
    path = _run_path(run_id)
    if not path.is_file():
        raise ValueError(f"unknown run_id: {run_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def _save_run(run: dict) -> None:
    _RUN_ROOT.mkdir(parents=True, exist_ok=True)
    path = _run_path(run["run_id"])
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _require(artifact: dict, fields: tuple[str, ...]) -> None:
    if not isinstance(artifact, dict):
        raise ValueError("artifact must be an object")
    missing = [name for name in fields
               if name not in artifact or artifact[name] is None
               or (isinstance(artifact[name], str) and not artifact[name].strip())]
    if missing:
        raise ValueError(f"artifact missing required fields: {missing}")


def _next_action(stage: str) -> dict:
    actions = {
        "evidence": {
            "task": "Inspect the live target and submit immutable review evidence.",
            "required": ["head", "base", "changed_files", "diff_summary"],
        },
        "gates": {
            "task": "Check merge state, CI state, and deterministic risk signals.",
            "required": ["merge_state", "ci_status", "risk_areas"],
        },
        "review": {
            "task": "Review the routed modules and submit grounded candidate findings.",
            "required": ["coverage", "findings"],
        },
        "verify": {
            "task": "Re-check every candidate against current code; discard weak findings.",
            "required": ["verified_findings", "discarded_findings"],
        },
        "complete": {"task": "Return final_report to the user.", "required": []},
    }
    return {"stage": stage, **actions[stage]}


def _render_report(run: dict) -> str:
    verified = run["artifacts"]["verify"]["verified_findings"]
    if not verified:
        return "No actionable findings."
    lines = ["# Review findings", ""]
    for index, finding in enumerate(verified, 1):
        if isinstance(finding, dict):
            title = finding.get("title") or f"Finding {index}"
            location = finding.get("location") or finding.get("path") or ""
            body = finding.get("body") or finding.get("evidence") or ""
            lines.extend([f"## {index}. {title}",
                          f"`{location}`" if location else "", str(body), ""])
        else:
            lines.extend([f"## {index}. Finding", str(finding), ""])
    return "\n".join(line for line in lines if line is not None).strip()


def build_mcp():
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP(
        "infermatrix-copilot",
        instructions=(
            "This server has two host-model modes and never calls another model. "
            "Default direct mode: inspect the target first, then call "
            "prepare_review with its changed_files. Strict mode: call "
            "start_strict_review and obey each next_action, submitting artifacts "
            "through submit_review_stage until complete. Only a completed strict "
            "run has a final_report. Use doc_search/doc_read for deeper rules."
        ),
    )

    @mcp.tool()
    def prepare_review(target: str, changed_files: list[str],
                       change_summary: str = "",
                       repo: str = "vllm-omni") -> dict:
        """Prepare best-effort direct review knowledge after Codex inspects code.

        `target` is a PR URL/number or a short description of local changes.
        `changed_files` makes knowledge routing target-specific. This tool does
        not fetch code; the host inspects the PR/worktree with its normal tools.
        """
        def run() -> dict:
            if not str(target).strip():
                raise ValueError("target must not be empty")
            if not isinstance(changed_files, list) or not changed_files:
                raise ValueError(
                    "changed_files is required; inspect the target before calling")
            return {
                "target": str(target).strip(),
                "repo": repo,
                "mode": "direct",
                "changed_files": changed_files,
                "change_summary": change_summary,
                "instructions": [
                    "Apply the supplied rules only to their owning modules.",
                    "Use doc_search then doc_read for changed models/components.",
                    "Report only actionable findings with current file/line anchors.",
                ],
                "knowledge": _review_knowledge(repo, changed_files),
            }

        return _guard(run)

    @mcp.tool()
    def start_strict_review(target: str, repo: str = "vllm-omni") -> dict:
        """Start the server-enforced host workflow; returns run_id + next_action."""
        def run() -> dict:
            if not str(target).strip():
                raise ValueError("target must not be empty")
            _docs(repo)
            record = {
                "run_id": uuid.uuid4().hex,
                "target": str(target).strip(),
                "repo": repo,
                "mode": "strict",
                "stage": "evidence",
                "artifacts": {},
            }
            _save_run(record)
            return {"run_id": record["run_id"], "mode": "strict",
                    "next_action": _next_action("evidence")}

        return _guard(run)

    @mcp.tool()
    def submit_review_stage(run_id: str, stage: str,
                            artifact: dict[str, Any]) -> dict:
        """Submit the current strict stage; skipping or stale stages are refused."""
        def run() -> dict:
            record = _load_run(run_id)
            current = record["stage"]
            if current == "complete":
                return {"run_id": run_id, "stage": current,
                        "final_report": record["final_report"]}
            if stage != current:
                raise ValueError(
                    f"expected stage {current!r}, received {stage!r}")
            required = tuple(_next_action(stage)["required"])
            _require(artifact, required)
            if stage == "evidence" and (
                    not isinstance(artifact["changed_files"], list)
                    or not artifact["changed_files"]):
                raise ValueError("changed_files must be a non-empty list")
            list_fields = {
                "gates": ("risk_areas",),
                "review": ("coverage", "findings"),
                "verify": ("verified_findings", "discarded_findings"),
            }.get(stage, ())
            for list_field in list_fields:
                if not isinstance(artifact[list_field], list):
                    raise ValueError(f"{list_field} must be a list")
            if stage == "review" and not artifact["coverage"]:
                raise ValueError("coverage must be a non-empty list")
            record["artifacts"][stage] = artifact
            next_stage = _STAGES[_STAGES.index(stage) + 1]
            record["stage"] = next_stage
            if next_stage == "complete":
                record["final_report"] = _render_report(record)
            _save_run(record)
            out = {"run_id": run_id, "stage": next_stage,
                   "next_action": _next_action(next_stage)}
            if stage == "evidence":
                out["knowledge"] = _review_knowledge(
                    record["repo"], artifact["changed_files"])
            if next_stage == "complete":
                out["final_report"] = record["final_report"]
            return out

        return _guard(run)

    @mcp.tool()
    def get_review_status(run_id: str) -> dict:
        """Resume a strict run and return its current next action/report."""
        return _guard(lambda: {
            "run_id": run_id,
            "mode": "strict",
            "stage": (record := _load_run(run_id))["stage"],
            "next_action": _next_action(record["stage"]),
            **({"final_report": record["final_report"]}
               if record["stage"] == "complete" else {}),
        })

    @mcp.tool()
    def doc_search(query: str, repo: str = "vllm-omni",
                   limit: int = 20) -> dict:
        """Search general and repository-specific curated review knowledge."""
        return _guard(lambda: {
            "query": query,
            "repo": repo,
            "matches": _docs(repo).search(query, limit=limit),
        })

    @mcp.tool()
    def doc_read(path: str, repo: str = "vllm-omni",
                 offset: int = 0) -> dict:
        """Read a Markdown page returned by doc_search; follow next_offset."""
        return _guard(lambda: {"repo": repo, **_docs(repo).read(path, offset=offset)})

    return mcp


def main() -> int:
    if sys.platform == "win32":
        signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        mcp = build_mcp()
    except ImportError:
        sys.stderr.write(
            "infermatrix-copilot-mcp needs the MCP SDK. Install with "
            "pip install -e '.[mcp]'\n"
        )
        return 1
    mcp.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
