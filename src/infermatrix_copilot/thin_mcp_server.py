"""Thin MCP: curated review knowledge for the host model, with no model client."""

from __future__ import annotations

import json
import signal
import sys
import uuid
from pathlib import Path
from typing import Any

from .adapters import AdapterError, AdapterRegistry, RepoAdapter
from .knowledge_docs import KnowledgeDocs, KnowledgeDocsError

_ROOT = Path(__file__).resolve().parents[2]
_KNOWLEDGE = _ROOT / "knowledge"
_ADAPTERS = _ROOT / "adapters"
_RUN_ROOT = Path.home() / ".infermatrix-copilot" / "host-review-runs"
_STAGES = ("evidence", "gates", "review", "verify", "complete")


def _supported_repos() -> list[str]:
    if not (_KNOWLEDGE / "repos").is_dir():
        return []
    return sorted(
        path.name for path in (_KNOWLEDGE / "repos").iterdir()
        if path.is_dir() and (path / "_index.md").is_file()
    )


def _adapter_for_repo(repo: str) -> RepoAdapter | None:
    try:
        return AdapterRegistry(_ADAPTERS).resolve(name=repo)
    except AdapterError:
        return None


def _repo_scope(repo: str) -> tuple[str, RepoAdapter | None]:
    repo = (repo or "vllm-omni").strip()
    adapter = _adapter_for_repo(repo)
    if adapter is not None:
        repo_subdir = str(
            (adapter.manifest.get("knowledge") or {}).get("repo_subdir") or "")
        if repo_subdir.startswith("repos/"):
            repo = repo_subdir.removeprefix("repos/").strip("/")
    repo = repo.replace("_", "-")
    repo_dir = _KNOWLEDGE / "repos" / repo
    if not repo_dir.is_dir():
        supported = ", ".join(_supported_repos()) or "(none)"
        raise KnowledgeDocsError(
            f"unsupported knowledge repo: {repo}. Supported: {supported}")
    return repo, adapter


def _docs(repo: str) -> KnowledgeDocs:
    repo, _adapter = _repo_scope(repo)
    return KnowledgeDocs(_KNOWLEDGE, f"repos/{repo}")


def _guard(fn):
    try:
        return fn()
    except (KnowledgeDocsError, FileNotFoundError, ValueError) as exc:
        return {"error": str(exc)}


def _knowledge_entry(name: str) -> str:
    path = (_KNOWLEDGE / name).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"knowledge entry is missing: {path}")
    return str(path)


def _review_knowledge(repo: str, changed_files: list[str]) -> list[dict]:
    repo, adapter = _repo_scope(repo)
    docs = _docs(repo)
    paths = [
        "general/review/_index.md",
        f"repos/{repo}/rules.md",
        f"repos/{repo}/_index.md",
        f"repos/{repo}/review/_index.md",
        f"repos/{repo}/review/guides/maintainer-pattern-routing.md",
    ]
    if adapter is not None:
        knowledge = adapter.manifest.get("knowledge") or {}
        paths.extend(knowledge.get("briefing_docs") or [])
        paths.extend(knowledge.get("briefing_docs_extra") or [])
        routes = adapter.review_routes
    else:
        routes = []
    routed: list[dict] = []
    unmatched: list[str] = []
    for changed_file in changed_files:
        path = str(changed_file).replace("\\", "/")
        folded = path.casefold()
        hits = []
        for route in routes:
            prefix = str(route.get("prefix", "")).replace("\\", "/").casefold()
            doc = str(route.get("doc", ""))
            if prefix and doc and folded.startswith(prefix):
                paths.append(doc)
                hits.append({
                    "path": path,
                    "owner": route.get("owner") or prefix.rstrip("/"),
                    "doc": doc,
                })
        if hits:
            routed.extend(hits)
        else:
            unmatched.append(path)
    entries = []
    if changed_files:
        lines = ["# Changed-file routing", "", f"repo: {repo}", ""]
        if routed:
            lines.append("## Routed")
            for item in routed:
                lines.append(
                    f"- `{item['path']}` -> {item['owner']} -> `{item['doc']}`")
            lines.append("")
        if unmatched:
            lines.append("## Unmatched")
            for path in unmatched:
                lines.append(f"- `{path}`")
            lines.append("")
            lines.append(
                "Unmatched changed paths remain reviewer-visible and must not "
                "be treated as covered.")
        entries.append({
            "path": "changed-file-routing",
            "content": "\n".join(lines).strip(),
            "next_offset": None,
        })
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
        raise TypeError("artifact must be an object")
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
            "artifact_example": {
                "head": "<commit SHA>",
                "base": "<commit SHA>",
                "changed_files": ["path/to/file.py"],
                "diff_summary": "<short summary>",
            },
        },
        "gates": {
            "task": "Check merge state, CI state, and deterministic risk signals.",
            "required": ["merge_state", "ci_status", "risk_areas"],
            "artifact_example": {
                "merge_state": "<state>",
                "ci_status": "<status and validation boundary>",
                "risk_areas": ["<risk area>"],
            },
        },
        "review": {
            "task": "Review the routed modules and submit grounded candidate findings.",
            "required": ["coverage", "findings"],
            "artifact_example": {
                "coverage": ["path/to/reviewed_file.py"],
                "findings": [{
                    "title": "<finding title>",
                    "location": "path/to/file.py:line",
                    "body": "<evidence and impact>",
                }],
            },
        },
        "verify": {
            "task": "Re-check every candidate against current code; discard weak findings.",
            "required": ["verified_findings", "discarded_findings"],
            "artifact_example": {
                "verified_findings": [],
                "discarded_findings": [],
            },
        },
        "complete": {
            "task": "Return final_report to the user.",
            "required": [],
            "artifact_example": {},
        },
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
            "In direct mode, read the returned knowledge_entry and let the host "
            "model follow its routing instructions. "
            "Always begin with the review tool. Unless the user explicitly asks "
            "for strict workflow mode, use its default direct mode. Never choose "
            "strict mode merely because it is available. This server never calls "
            "another model. In strict mode, obey each next_action and submit "
            "artifacts through submit_review_stage until complete."
        ),
    )

    @mcp.tool()
    def review(target: str, repo: str = "vllm-omni",
               mode: str = "direct") -> dict:
        """Begin a review. Use direct unless the user explicitly requests strict.

        `target` is a PR URL/number or a short description of local changes.
        Direct mode returns the knowledge entrypoint; the host model reads its
        routing map and decides what applies. Strict mode starts the staged
        workflow and returns a run_id plus its first next_action.
        """
        def run() -> dict:
            if not str(target).strip():
                raise ValueError("target must not be empty")
            selected_mode = str(mode).strip().casefold() or "direct"
            if selected_mode not in {"direct", "strict"}:
                raise ValueError("mode must be 'direct' or 'strict'")
            if selected_mode == "strict":
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
                return {
                    "run_id": record["run_id"],
                    "mode": "strict",
                    "next_action": _next_action("evidence"),
                }
            _docs(repo)
            return {"knowledge_entry": _knowledge_entry("AGENTS.md")}

        return _guard(run)

    @mcp.tool()
    def update_knowledge(repo: str = "vllm-omni") -> dict:
        """Return the knowledge contribution entrypoint for the host to follow.

        The host model reads the documentation map, chooses the owner, edits the
        Markdown files, and runs the documented checks. The MCP does not decide
        placement and does not write knowledge itself.
        """
        def run() -> dict:
            _docs(repo)
            return {"knowledge_entry": _knowledge_entry("CONTRIBUTING.md")}

        return _guard(run)

    @mcp.tool()
    def submit_review_stage(run_id: str, stage: str,
                            artifact: dict[str, Any]) -> dict:
        """Advance strict mode using the artifact_example from next_action.

        Fields documented as arrays also accept one scalar item and normalize it
        to a one-item array, so a harmless shape mismatch does not block a run.
        """
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
                    artifact[list_field] = [artifact[list_field]]
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
        """Literal text search over knowledge; use entries for task routing."""
        def run() -> dict:
            selected_repo, _adapter = _repo_scope(repo)
            matches = _docs(repo).search(query, limit=limit)
            result = {"query": query, "repo": selected_repo, "matches": matches}
            if not matches:
                result["hint"] = (
                    "No literal text match. For review routing, call review and "
                    "read its knowledge_entry. For knowledge edits, call "
                    "update_knowledge and read its knowledge_entry."
                )
            return result

        return _guard(run)

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
