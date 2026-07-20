#!/usr/bin/env python3
"""Prepare and optionally run a history-free Codex PR-review replay.

The runner consumes only public cases. It exports the review tree with
``git archive`` (no .git/history), writes the pinned diff and knowledge page,
and invokes Codex in read-only mode. Hidden labels are never opened here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import time
from pathlib import Path
from typing import Any

KNOWLEDGE_DOC = "repos/vllm-omni/review/guides/recent-maintainer-patterns.md"
DEFAULT_KNOWLEDGE = Path("knowledge") / KNOWLEDGE_DOC

OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["verdict", "summary", "findings"],
    "properties": {
        "verdict": {"type": "string", "enum": ["approve", "request_changes"]},
        "summary": {"type": "string"},
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["id", "severity", "file", "line", "root_cause",
                             "impact_path", "comment", "evidence"],
                "properties": {
                    "id": {"type": "string"},
                    "severity": {"type": "string",
                                 "enum": ["blocker", "major", "minor", "nit"]},
                    "file": {"type": "string"},
                    "line": {"type": "integer"},
                    "root_cause": {"type": "string"},
                    "impact_path": {"type": "string"},
                    "comment": {"type": "string"},
                    "evidence": {"type": "string"},
                },
            },
        },
    },
}


def load_case(path: Path, case_id: str) -> dict[str, Any]:
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        row = json.loads(raw)
        if row.get("case_id") == case_id:
            return row
    raise ValueError(f"case not found: {case_id}")


def run_git(repo: Path, *args: str, text: bool = True):
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=text,
        encoding="utf-8" if text else None,
        errors="replace" if text else None,
    ).stdout


def verify_commit(repo: Path, sha: str) -> None:
    run_git(repo, "cat-file", "-e", f"{sha}^{{commit}}")


def verify_base_is_ancestor(repo: Path, base_sha: str, review_sha: str) -> None:
    """Reject a drifting base that would inject unrelated main-branch changes."""
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", base_sha, review_sha],
        cwd=repo, capture_output=True, text=True, encoding="utf-8",
        errors="replace")
    if result.returncode == 0:
        return
    if result.returncode != 1:
        raise subprocess.CalledProcessError(
            result.returncode, result.args, result.stdout, result.stderr)
    merge_base = run_git(repo, "merge-base", base_sha, review_sha).strip()
    raise ValueError(
        "base_sha is not an ancestor of review_sha; this would mix unrelated "
        f"branch drift into the replay diff. Pin the review-time merge base: {merge_base}"
    )


def _scope_key(path: str) -> str:
    parts = Path(path).as_posix().split("/")
    if parts[:3] in (["vllm_omni", "diffusion", "models"],
                     ["vllm_omni", "model_executor", "models"]):
        return "/".join(parts[:4]) if len(parts) >= 4 else "/".join(parts)
    if parts and parts[0] == "tests":
        return "/".join(parts[:3]) if len(parts) >= 3 else "/".join(parts)
    return "/".join(parts[:2]) if len(parts) >= 2 else parts[0]


def _review_routes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Route changed paths to concrete review questions without asserting bugs."""
    joined = "\n".join(row["path"] for row in rows)
    routes: list[dict[str, Any]] = []

    def add(route: str, *questions: str) -> None:
        routes.append({"route": route, "questions": list(questions)})

    if "/diffusion/models/" in joined:
        add("diffusion-sampling-semantics",
            "Does every scheduler mode/config match the algorithm, including stochastic or distilled modes?",
            "If the algorithm re-noises at each step, is stochastic sampling explicitly forced or validated instead of trusting checkpoint/default config?",
            "Are fixed-step schedules, request step counts, zero-valued parameters, and request-local generators preserved end to end?")
        add("diffusion-memory-and-acceleration",
            "Do sibling components declare the same layerwise/component offload block contracts?",
            "Do cache/graph/compile assumptions match actual forward count, CFG mode, step horizon, dtype, and eager behavior?")
        add("diffusion-model-integration",
            "Are registry, loader dtype/config fetch, pipeline bridge, postprocess, output shape, and online/offline paths all covered?")
    if "/entrypoints/" in joined or "/protocol/" in joined:
        add("serving-preflight-and-streaming",
            "Are predictable request errors rejected before engine scheduling and before the first stream chunk?",
            "Do streaming failures reach the client instead of becoming silent EOF after HTTP 200?")
        add("protocol-backend-single-source",
            "Do schema values/defaults, serving validation, encoder MIME/format handling, docs, and first-party clients share one capability source?")
    if "/distributed/" in joined or "hsdp" in joined.casefold():
        add("distributed-real-path",
            "Does a real process group/sharding path prove parameter representation and device behavior rather than only mock calls?")
    if "prefix_cache" in joined or "/cache/" in joined:
        add("async-cache-lifetime",
            "Can the next step reuse or mutate a side-stream source or persistent buffer before the copy finishes, producing wrong cached data?",
            "Treat pageable staging, an unaccelerated fallback, or an unsupported platform branch as performance/context unless the changed path proves a correctness failure or contradicts an explicit PR contract.")
    if "/metrics/" in joined or "metric" in joined.casefold():
        add("metrics-ownership",
            "Are throttles, cleanup-time gauges, labels, and collector registration owned per stage/replica/request lifecycle?")
    add("compatibility-and-scope",
        "Does every removed or moved public symbol keep an identity-preserving compatibility path?",
        "Are findings tied to changed lines and are tests exercising the behavior claimed by this diff?")
    return routes


def build_scope(repo: Path, base_sha: str, review_sha: str) -> dict[str, Any]:
    """Build a deterministic changed-file/module coverage map for the reviewer."""
    rows: list[dict[str, Any]] = []
    for raw in run_git(repo, "diff", "--numstat", base_sha, review_sha,
                       "--").splitlines():
        added, deleted, path = raw.split("\t", 2)
        add_n = int(added) if added.isdigit() else 0
        del_n = int(deleted) if deleted.isdigit() else 0
        rows.append({"path": path, "added": add_n, "deleted": del_n,
                     "churn": add_n + del_n, "scope": _scope_key(path)})
    rows.sort(key=lambda row: (-row["churn"], row["path"]))
    scopes: dict[str, dict[str, Any]] = {}
    for row in rows:
        group = scopes.setdefault(row["scope"], {"churn": 0, "files": []})
        group["churn"] += row["churn"]
        group["files"].append(row["path"])
    ordered_scopes = [
        {"scope": key, **value}
        for key, value in sorted(scopes.items(),
                                 key=lambda item: (-item[1]["churn"], item[0]))
    ]
    return {"base_sha": base_sha, "review_sha": review_sha,
            "changed_files": len(rows), "total_churn": sum(r["churn"] for r in rows),
            "scopes": ordered_scopes, "review_routes": _review_routes(rows),
            "files": rows}


def verify_knowledge(root: Path, case: dict[str, Any]) -> Path:
    docs = case.get("knowledge_docs") or []
    if docs != [KNOWLEDGE_DOC]:
        raise ValueError("replay runner currently requires the pinned performance guide")
    path = root / DEFAULT_KNOWLEDGE
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if case.get("knowledge_snapshot") != f"sha256:{digest}":
        raise ValueError("knowledge snapshot hash does not match the public case")
    return path


def safe_extract(archive: Path, destination: Path) -> None:
    with tarfile.open(archive) as bundle:
        base = destination.resolve()
        for member in bundle.getmembers():
            target = (destination / member.name).resolve()
            try:
                target.relative_to(base)
            except ValueError as exc:
                raise ValueError(f"archive path escapes snapshot: {member.name}") from exc
        bundle.extractall(destination)


def prepare(case: dict[str, Any], repo: Path, project_root: Path,
            run_dir: Path) -> tuple[Path, Path]:
    base_sha = str(case["base_sha"])
    review_sha = str(case["review_sha"])
    verify_commit(repo, base_sha)
    verify_commit(repo, review_sha)
    verify_base_is_ancestor(repo, base_sha, review_sha)
    knowledge = verify_knowledge(project_root, case)
    if run_dir.exists():
        raise FileExistsError(f"refusing to overwrite replay run: {run_dir}")
    run_dir.mkdir(parents=True)
    snapshot = run_dir / "snapshot"
    snapshot.mkdir()

    archive = run_dir / "snapshot.tar"
    with archive.open("wb") as stream:
        subprocess.run(
            ["git", "archive", "--format=tar", review_sha], cwd=repo,
            check=True, stdout=stream, stderr=subprocess.PIPE)
    safe_extract(archive, snapshot)
    archive.unlink()

    diff = run_git(repo, "diff", "--no-ext-diff", "--unified=40",
                   base_sha, review_sha, "--")
    (snapshot / "REPLAY_DIFF.patch").write_text(diff, encoding="utf-8")
    (snapshot / "REPLAY_KNOWLEDGE.md").write_bytes(knowledge.read_bytes())
    public_case = dict(case)
    (snapshot / "REPLAY_CASE.json").write_text(
        json.dumps(public_case, ensure_ascii=False, indent=2), encoding="utf-8")
    (snapshot / "REPLAY_SCOPE.json").write_text(
        json.dumps(build_scope(repo, base_sha, review_sha), ensure_ascii=False,
                   indent=2), encoding="utf-8")
    (run_dir / "output_schema.json").write_text(
        json.dumps(OUTPUT_SCHEMA, ensure_ascii=False, indent=2), encoding="utf-8")
    assert not (snapshot / ".git").exists()
    return snapshot, run_dir / "output_schema.json"


def prompt_for(case: dict[str, Any]) -> str:
    return f"""Review replay case {case['case_id']} as a vLLM-Omni maintainer.

Inputs inside the current directory:
- REPLAY_CASE.json: public case metadata.
- REPLAY_SCOPE.json: exact changed files grouped into review scopes and sorted by churn.
- REPLAY_DIFF.patch: the exact diff from base_sha to review_sha.
- REPLAY_KNOWLEDGE.md: the pinned performance review knowledge.
- The remaining files: repository tree exactly at review_sha, without .git.

Hard isolation rules:
- Do not use network, GitHub, gh, web search, PR comments, review threads, git
  history, or knowledge outside this snapshot.
- Do not infer later fixes. Review only the supplied diff and tree.
- Read the knowledge first, then investigate every candidate against current
  source. Similar keywords are not evidence.
- Use REPLAY_SCOPE.json as a coverage ledger. Inspect every changed scope before
  finalizing, then spend deeper effort on the highest-churn and cross-scope paths.
- For every item in `review_routes`, inspect the referenced changed code and
  explicitly prove or reject each question internally. Routes are investigation
  prompts, not findings; emit nothing unless the diff supplies concrete evidence.
- Do not finalize until every routed question has a code-backed answer or is
  demonstrably not applicable to the changed paths.
- Treat only files in the pinned ancestor-base diff as PR changes. Repository
  context may explain impact, but must not become an unrelated finding.
- Emit only findings that require a change in this PR. Each must state the root
  cause and complete affected path, with concrete file/line evidence.
- Before emitting, apply a high-confidence reporting gate: the failure must be
  reachable through the changed behavior and materially affect correctness,
  compatibility, or the PR's claimed performance. Do not report a merely
  possible optimization, unverified platform branch, or speculative risk.
- Consolidate multiple symptoms or performance consequences of one ownership,
  lifetime, or synchronization defect into one root-cause finding. Split only
  independently fixable problems. Use stable descriptive IDs.

Return exactly the requested JSON schema."""


def invoke_codex(snapshot: Path, schema: Path, output: Path, prompt: str,
                 version: str, model: str) -> float:
    npx = shutil.which("npx.cmd") or shutil.which("npx")
    if not npx:
        raise FileNotFoundError("npx executable not found on PATH")
    command = [
        npx, "-y", f"@openai/codex@{version}", "exec",
        "--ignore-user-config", "-C", str(snapshot), "--sandbox", "read-only",
        "--skip-git-repo-check", "-m", model,
        "-c", "model_reasoning_effort=high",
        "--output-schema", str(schema), "-o", str(output), "-",
    ]
    env = os.environ.copy()
    # Subscription authentication comes from the user's existing Codex login.
    # No repo .env or API key is read or forwarded explicitly by this runner.
    started = time.monotonic()
    with (output.parent / "codex.log").open("w", encoding="utf-8") as log:
        subprocess.run(command, input=prompt, text=True, encoding="utf-8",
                       cwd=snapshot, env=env, check=True, stdout=log, stderr=log)
    return time.monotonic() - started


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--codex-version", default="0.144.6")
    parser.add_argument("--model", default="gpt-5.6-sol")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[2]
    case = load_case(args.cases.resolve(), args.case_id)
    if case.get("mode") != "performance":
        raise ValueError("run_replay only executes performance cases")
    snapshot, schema = prepare(case, args.repo.resolve(), project_root,
                               args.run_dir.resolve())
    print(json.dumps({"case_id": args.case_id, "snapshot": str(snapshot),
                      "diff_bytes": (snapshot / "REPLAY_DIFF.patch").stat().st_size,
                      "status": "prepared"}, ensure_ascii=False))
    if args.prepare_only:
        return
    raw_output = args.run_dir.resolve() / "review.json"
    elapsed = invoke_codex(snapshot, schema, raw_output, prompt_for(case),
                           args.codex_version, args.model)
    review = json.loads(raw_output.read_text(encoding="utf-8"))
    prediction = {"case_id": args.case_id, "run_id": args.run_id,
                  "findings": review.get("findings") or []}
    (args.run_dir.resolve() / "prediction.jsonl").write_text(
        json.dumps(prediction, ensure_ascii=False) + "\n", encoding="utf-8")
    (args.run_dir.resolve() / "run_meta.json").write_text(json.dumps({
        "case_id": args.case_id, "run_id": args.run_id,
        "model": args.model, "reasoning_effort": "high",
        "codex_version": args.codex_version, "elapsed_seconds": elapsed,
        "user_config_ignored": True, "sandbox": "read-only",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"case_id": args.case_id, "run_id": args.run_id,
                      "findings": len(prediction["findings"]),
                      "status": "completed"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
