"""Thin MCP: curated review knowledge for the host model, with no model client."""

from __future__ import annotations

import json
import re
import signal
import sys
import uuid
from pathlib import Path
from typing import Any

from .knowledge_docs import KnowledgeDocs, KnowledgeDocsError

_ROOT = Path(__file__).resolve().parents[2]
_KNOWLEDGE = _ROOT / "knowledge"
_RUN_ROOT = Path.home() / ".infermatrix-copilot" / "host-review-runs"
_STAGES = ("evidence", "gates", "review", "verify", "publish", "complete")
_SEVERITIES = frozenset({"blocker", "major", "minor", "nit"})
_REPO_ALIASES = {
    "vllm-project/vllm-omni": "vllm-omni",
}
_ROUTES = {
    "vllm_omni/config/": "repos/vllm-omni/components/config/rules.md",
    "vllm_omni/core/": "repos/vllm-omni/components/scheduler/rules.md",
    "vllm_omni/entrypoints/": "repos/vllm-omni/components/serving/rules.md",
    "vllm_omni/model_executor/": "repos/vllm-omni/components/model-executor/rules.md",
    "vllm_omni/models/": "repos/vllm-omni/models/_index.md",
    "vllm_omni/diffusion/": "repos/vllm-omni/components/diffusion/rules.md",
}


def _normalize_repo(repo: str) -> str:
    selected = str(repo or "vllm-omni").strip()
    return _REPO_ALIASES.get(selected.casefold(), selected)


def _supported_repos() -> list[str]:
    if not (_KNOWLEDGE / "repos").is_dir():
        return []
    return sorted(
        path.name for path in (_KNOWLEDGE / "repos").iterdir()
        if path.is_dir() and (path / "_index.md").is_file()
    )


def _docs(repo: str) -> KnowledgeDocs:
    repo = _normalize_repo(repo)
    repo_dir = _KNOWLEDGE / "repos" / repo
    if not repo_dir.is_dir():
        raise KnowledgeDocsError(f"unsupported knowledge repo: {repo}")
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
    repo = _normalize_repo(repo)
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


def _normalize_finding(finding: Any, index: int) -> dict:
    """Return one verified finding in the stable host-delivery schema."""
    if not isinstance(finding, dict):
        raise ValueError(f"verified_findings[{index}] must be an object")
    path = str(finding.get("path") or finding.get("file") or "").strip()
    line = finding.get("line")
    location = str(finding.get("location") or "").strip()
    if (not path or line is None) and ":" in location:
        candidate_path, candidate_line = location.rsplit(":", 1)
        path = path or candidate_path.strip()
        line = line if line is not None else candidate_line.strip()
    path = path.replace("\\", "/").removeprefix("./")
    try:
        line = int(line)
    except (TypeError, ValueError):
        line = 0
    severity = str(finding.get("severity") or "").strip().casefold()
    title = str(finding.get("title") or "").strip()
    body = str(finding.get("body") or finding.get("evidence") or "").strip()
    missing = [name for name, value in (
        ("path", path), ("line", line), ("severity", severity),
        ("title", title), ("body", body),
    ) if not value]
    if missing:
        raise ValueError(
            f"verified_findings[{index}] missing required fields: {missing}")
    if line < 1:
        raise ValueError(f"verified_findings[{index}].line must be positive")
    if severity not in _SEVERITIES:
        raise ValueError(
            f"verified_findings[{index}].severity must be one of "
            f"{sorted(_SEVERITIES)}")
    return {"path": path, "line": line, "severity": severity,
            "title": title, "body": body}


def _validate_diff_hunks(artifact: dict) -> None:
    """Validate compact new-side diff anchors supplied by the host."""
    hunks = artifact.get("diff_hunks")
    if not isinstance(hunks, list):
        raise ValueError("diff_hunks must be a list")
    changed = {
        str(path).replace("\\", "/").removeprefix("./")
        for path in artifact["changed_files"]
    }
    normalized = []
    for index, hunk in enumerate(hunks):
        if not isinstance(hunk, dict):
            raise ValueError(f"diff_hunks[{index}] must be an object")
        path = str(hunk.get("path") or "").replace("\\", "/").removeprefix("./")
        try:
            start = int(hunk.get("right_start"))
            count = int(hunk.get("right_count"))
        except (TypeError, ValueError):
            raise ValueError(
                f"diff_hunks[{index}] needs integer right_start/right_count")
        if path not in changed:
            raise ValueError(
                f"diff_hunks[{index}].path is not in changed_files: {path}")
        if start < 1 or count < 0:
            raise ValueError(
                f"diff_hunks[{index}] has invalid right-side range")
        normalized.append(
            {"path": path, "right_start": start, "right_count": count})
    artifact["diff_hunks"] = normalized


def _is_inline_anchor(finding: dict, hunks: list[dict]) -> bool:
    return any(
        hunk["path"] == finding["path"]
        and hunk["right_start"]
        <= finding["line"]
        < hunk["right_start"] + hunk["right_count"]
        for hunk in hunks
    )


def _review_delivery(run: dict) -> dict:
    """Build the exact GitHub payload plus separately tracked delivery counts."""
    findings = run["artifacts"]["verify"]["verified_findings"]
    hunks = run["artifacts"]["evidence"].get("diff_hunks") or []
    inline = []
    fallback = []
    for finding in findings:
        if _is_inline_anchor(finding, hunks):
            inline.append({
                "path": finding["path"],
                "line": finding["line"],
                "side": "RIGHT",
                "body": (
                    f"**[{finding['severity']}] {finding['title']}**\n\n"
                    f"{finding['body']}"
                ),
            })
        else:
            fallback.append(finding)

    blocking = any(
        finding["severity"] in {"blocker", "major"} for finding in findings)
    merge_state = str(
        run["artifacts"].get("gates", {}).get("merge_state") or "").upper()
    event = "COMMENT" if "MERGED" in merge_state else (
        "REQUEST_CHANGES" if blocking else "COMMENT" if findings else "APPROVE")
    body = [
        "Strict review completed against "
        f"`{run['artifacts']['evidence']['head']}`.",
        "",
        f"- Verified findings: {len(findings)}",
        f"- Inline comments: {len(inline)}",
        f"- Findings included in this review body: {len(fallback)}",
    ]
    if fallback:
        body.extend([
            "",
            "### Findings not posted inline",
            "These verified findings do not map to a current right-side diff line:",
        ])
        for finding in fallback:
            body.extend([
                "",
                f"**[{finding['severity']}] {finding['title']}**",
                f"`{finding['path']}:{finding['line']}`",
                finding["body"],
            ])
    return {
        "github_review": {
            "commit_id": run["artifacts"]["evidence"]["head"],
            "body": "\n".join(body),
            "event": event,
            "comments": inline,
        },
        "inline_count": len(inline),
        "fallback_count": len(fallback),
    }


def _completion(run: dict) -> dict:
    out = {
        "run_id": run["run_id"],
        "mode": "strict",
        "stage": "complete",
        "final_report": run["final_report"],
        "verified_findings": run["artifacts"]["verify"]["verified_findings"],
    }
    if run.get("review_delivery"):
        delivery = run["review_delivery"]
        out["github_review"] = delivery["github_review"]
        out["delivery_counts"] = {
            "inline_count": delivery["inline_count"],
            "fallback_count": delivery["fallback_count"],
        }
    if run["artifacts"].get("publish"):
        out["publication"] = run["artifacts"]["publish"]
    return out


def _next_stage(run: dict, stage: str) -> str:
    stages = _STAGES if run.get("post") else tuple(
        item for item in _STAGES if item != "publish")
    return stages[stages.index(stage) + 1]


def _next_action(stage: str, run: dict | None = None) -> dict:
    actions = {
        "evidence": {
            "task": "Inspect the live target and submit immutable review evidence.",
            "required": ["head", "base", "changed_files", "diff_summary"],
            "artifact_example": {
                "head": "<commit SHA>",
                "base": "<commit SHA>",
                "changed_files": ["path/to/file.py"],
                "diff_summary": "<short summary>",
                "diff_hunks": [{
                    "path": "path/to/file.py",
                    "right_start": 10,
                    "right_count": 5,
                }],
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
                    "path": "path/to/file.py",
                    "line": 12,
                    "severity": "major",
                    "body": "<evidence and impact>",
                }],
            },
        },
        "verify": {
            "task": "Re-check every candidate against current code; discard weak findings.",
            "required": ["verified_findings", "discarded_findings"],
            "artifact_example": {
                "verified_findings": [{
                    "title": "<finding title>",
                    "path": "path/to/file.py",
                    "line": 12,
                    "severity": "major",
                    "body": "<verified evidence and impact>",
                }],
                "discarded_findings": [],
            },
        },
        "publish": {
            "task": (
                "Submit exactly one GitHub pull request review using "
                "github_review. Keep comments inline; never flatten them into "
                "a PR Conversation comment. With a GitHub connector, map "
                "event→action, body→review, and comments→file_comments. Then "
                "submit the publication proof."
            ),
            "required": [
                "review_url", "event", "inline_count", "fallback_count"],
            "artifact_example": {
                "review_url": "https://github.com/owner/repo/pull/1#pullrequestreview-1",
                "event": "REQUEST_CHANGES",
                "inline_count": 1,
                "fallback_count": 0,
            },
        },
        "complete": {
            "task": "Return final_report to the user.",
            "required": [],
            "artifact_example": {},
        },
    }
    action = {"stage": stage, **actions[stage]}
    if stage == "evidence" and run and run.get("post"):
        action["required"] = [*action["required"], "diff_hunks"]
    if stage == "publish":
        delivery = (run or {}).get("review_delivery", {})
        action["github_review"] = delivery.get("github_review", {})
        action["expected_publication"] = {
            "event": delivery.get("github_review", {}).get("event"),
            "inline_count": delivery.get("inline_count"),
            "fallback_count": delivery.get("fallback_count"),
        }
    return action


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
            "artifacts through submit_review_stage until complete. Set post=true "
            "only when the user explicitly asks to publish. At the publish stage, "
            "submit github_review as one pull request review with its inline "
            "comments; never flatten it into a PR Conversation comment. For a "
            "GitHub connector, map event to action, body to review, and comments "
            "to file_comments."
        ),
    )

    @mcp.tool()
    def review(target: str, repo: str = "vllm-omni",
               mode: str = "direct", post: bool = False) -> dict:
        """Begin a review. Use direct unless the user explicitly requests strict.

        `target` is a PR URL/number or a short description of local changes.
        Direct mode ignores `repo`; strict mode accepts a knowledge short name
        or its canonical owner/name.
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
            if post and selected_mode != "strict":
                raise ValueError("post=true requires strict mode")
            if selected_mode == "strict":
                selected_repo = _normalize_repo(repo)
                _docs(selected_repo)
                record = {
                    "run_id": uuid.uuid4().hex,
                    "target": str(target).strip(),
                    "repo": selected_repo,
                    "mode": "strict",
                    "post": bool(post),
                    "stage": "evidence",
                    "artifacts": {},
                }
                _save_run(record)
                return {
                    "run_id": record["run_id"],
                    "mode": "strict",
                    "post": record["post"],
                    "next_action": _next_action("evidence", record),
                }
            return {"knowledge_entry": _knowledge_entry("AGENTS.md")}

        return _guard(run)

    @mcp.tool()
    def update_knowledge(repo: str = "vllm-omni") -> dict:
        """Return the knowledge contribution entrypoint for the host to follow.

        `repo` is accepted for compatibility but intentionally ignored.
        The host model reads the documentation map, chooses the owner, edits the
        Markdown files, and runs the documented checks. The MCP does not decide
        placement and does not write knowledge itself.
        """
        def run() -> dict:
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
                return _completion(record)
            if stage != current:
                raise ValueError(
                    f"expected stage {current!r}, received {stage!r}")
            required = tuple(_next_action(stage, record)["required"])
            _require(artifact, required)
            if stage == "evidence" and (
                    not isinstance(artifact["changed_files"], list)
                    or not artifact["changed_files"]):
                raise ValueError("changed_files must be a non-empty list")
            if stage == "evidence" and record.get("post"):
                _validate_diff_hunks(artifact)
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
            if stage == "verify":
                artifact["verified_findings"] = [
                    _normalize_finding(finding, index)
                    for index, finding in enumerate(
                        artifact["verified_findings"])
                ]
            if stage == "publish":
                delivery = record["review_delivery"]
                expected = {
                    "event": delivery["github_review"]["event"],
                    "inline_count": delivery["inline_count"],
                    "fallback_count": delivery["fallback_count"],
                }
                if not re.match(
                        r"^https://github\.com/[^/]+/[^/]+/pull/\d+"
                        r"#pullrequestreview-\d+$",
                        str(artifact["review_url"])):
                    raise ValueError(
                        "review_url must identify a GitHub pull request review")
                for field in ("event", "inline_count", "fallback_count"):
                    if artifact[field] != expected[field]:
                        raise ValueError(
                            f"publication proof {field} does not match "
                            "github_review")
            record["artifacts"][stage] = artifact
            next_stage = _next_stage(record, stage)
            record["stage"] = next_stage
            if stage == "verify":
                record["final_report"] = _render_report(record)
                if record.get("post"):
                    record["review_delivery"] = _review_delivery(record)
            _save_run(record)
            out = {"run_id": run_id, "stage": next_stage,
                   "next_action": _next_action(next_stage, record)}
            if stage == "evidence":
                out["knowledge"] = _review_knowledge(
                    record["repo"], artifact["changed_files"])
            if next_stage == "complete":
                return _completion(record)
            return out

        return _guard(run)

    @mcp.tool()
    def get_review_status(run_id: str) -> dict:
        """Resume a strict run and return its current next action/report."""
        def run() -> dict:
            record = _load_run(run_id)
            if record["stage"] == "complete":
                return _completion(record)
            return {
                "run_id": run_id,
                "mode": "strict",
                "stage": record["stage"],
                "next_action": _next_action(record["stage"], record),
            }

        return _guard(run)

    @mcp.tool()
    def doc_search(query: str, repo: str = "vllm-omni",
                   limit: int = 20) -> dict:
        """Search knowledge; repo accepts a short name or canonical owner/name."""
        def run() -> dict:
            selected_repo = _normalize_repo(repo)
            repo_dir = _KNOWLEDGE / "repos" / selected_repo
            if not repo_dir.is_dir():
                supported = ", ".join(_supported_repos()) or "(none)"
                return {
                    "error": (
                        f"unsupported knowledge repo: {repo}. "
                        f"Supported: {supported}. The repo argument selects a "
                        "knowledge scope; put search terms in query."
                    )
                }
            matches = _docs(selected_repo).search(query, limit=limit)
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
        """Read a doc_search page; repo accepts short or canonical owner/name."""
        def run() -> dict:
            selected_repo = _normalize_repo(repo)
            return {
                "repo": selected_repo,
                **_docs(selected_repo).read(path, offset=offset),
            }

        return _guard(run)

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
