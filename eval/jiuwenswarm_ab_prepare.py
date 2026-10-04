"""Freeze the previously selected JiuwenSwarm PRs for the readonly A/B eval.

Raw GitHub material and source checkouts stay outside the product repository.
The selected heads are immutable: a moved PR never silently replaces a case.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

BASE = "f0a69728c96b5961d993449f1a901cbd2f4dac5b"
HEADS = {
    7639: "c5151286cabee7debca271dbbabbc738b9686fdf",
    7641: "9b2e243e8994bfab0495858dbbcb71c502212908",
    7642: "72fd6412a39fe46ffa421c6db9ff0f25098a5906",
    7645: "42c979d144a62a6396dc2353a4e8216f839dd198",
    7647: "fade3a6baf0d5fa3122f660b0825b0bacb2a1a20",
    7649: "8bd3cf35fbe0b4c5c1e715b5195daace3ec316fd",
    7650: "a8f4f92159f875d5d8e008936ec9833f5ab8c719",
    7651: "a8a45c6d5a0d472e1d2b1019869da2124d99448c",
    7654: "4c4f803e9769624eb447e5fa64190ab43fe8e931",
    7655: "88746ded25df670749444ece22466205e329070b",
    7656: "2a1772a4b6d570d58da727bbb28ae978b47b123f",
    7675: "f7f71fce195b8437bd743ef21fcf6bd856fcf96f",
}


def command(args, cwd=None):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True).stdout


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def prepare(root: Path, source: Path, knowledge_checkout: Path):
    root, source, knowledge_checkout = (p.resolve() for p in (root, source, knowledge_checkout))
    if root.is_relative_to(knowledge_checkout):
        raise ValueError("raw campaign material must remain outside the knowledge repository")
    root.mkdir(parents=True, exist_ok=True)
    campaign_path = root / "campaign.json"
    if campaign_path.exists():
        existing = json.loads(campaign_path.read_text())
        assert {c["number"]: c["head"] for c in existing["cases"]} == HEADS
        for c in existing["cases"]:
            assert sha(c["diff_path"]) == c["diff_sha256"]
            assert sha(c["context_path"]) == c["context_sha256"]
            assert command(["git", "rev-parse", "HEAD"], c["source_root"]).decode().strip() == c["head"]
        return existing
    assert command(["git", "rev-parse", "HEAD"], source).decode().strip() == BASE
    # One sequential fetch avoids concurrent shared-repository ref locks.
    missing = []
    for value in HEADS.values():
        result = subprocess.run(["git", "cat-file", "-e", value + "^{commit}"], cwd=source, capture_output=True)
        if result.returncode:
            missing.append(value)
    if missing:
        command(["git", "fetch", "--no-tags", "--no-write-fetch-head", "origin", *missing], source)

    def case(item):
        number, head = item
        target = root / "sources" / f"pr-{number}"
        if not target.exists():
            command(["git", "worktree", "add", "--detach", str(target), head], source)
        assert command(["git", "rev-parse", "HEAD"], target).decode().strip() == head
        assert not command(["git", "status", "--porcelain"], target)
        case_root = root / "cases" / str(number)
        case_root.mkdir(parents=True, exist_ok=True)
        meta_path = case_root / "github-pr.json"
        if not meta_path.exists():
            meta_path.write_bytes(command(["gh", "api", f"repos/openJiuwen-ai/jiuwenswarm/pulls/{number}"]))
        meta = json.loads(meta_path.read_text())
        base = command(["git", "merge-base", BASE, head], target).decode().strip()
        context_path = case_root / "context.json"
        write(context_path, {"number": number, "title": meta["title"], "body": meta.get("body", ""),
                             "url": meta["html_url"], "created_at": meta["created_at"],
                             "frozen_base": base, "frozen_target": BASE, "frozen_head": head,
                             "observed_live_target": meta["base"]["sha"],
                             "observed_live_head": meta["head"]["sha"],
                             "discussion_included": False})
        diff_path = case_root / "diff.patch"
        diff_path.write_bytes(command(["git", "diff", "--no-ext-diff", "--no-color", base, head, "--"], target))
        files = command(["git", "diff", "--name-only", "-z", base, head, "--"], target).decode().split("\0")
        return {"number": number, "base": base, "target": BASE, "head": head,
                "source_root": str(target), "diff_path": str(diff_path), "context_path": str(context_path),
                "diff_sha256": sha(diff_path), "context_sha256": sha(context_path),
                "changed_files": [p for p in files if p], "url": meta["html_url"],
                "target_base_diverged": base != BASE}

    # Worktree creation changes shared metadata; avoid parallel git mutations.
    cases = [case(item) for item in HEADS.items()]
    value = {
        "schema": "jiuwenswarm-pr-review-ab-v1", "run_root": str(root), "repo": "jiuwenswarm",
        "created_at": datetime.now(timezone.utc).isoformat(), "baseline_source_sha": BASE,
        "baseline_source_root": str(source),
        "knowledge_checkout_root": str(knowledge_checkout),
        "knowledge_checkout_sha": command(["git", "rev-parse", "HEAD"], knowledge_checkout).decode().strip(),
        "knowledge_merged_pr": "https://github.com/JiusiServe/InferMatrixCopilot/pull/290",
        "knowledge_merged_head_sha": "58279d334cd827adb631891a760bb14efe376420",
        "cases": cases,
        "analysis_groups": analysis_groups(cases),
        "diff_policy": "git merge-base(frozen target, frozen head) to frozen head; source checkout is frozen PR head",
        "arms": {arm: {"doc_root": str(root / "docs" / arm), "repo_subdir": "repos/jiuwenswarm"}
                 for arm in ("A", "B")},
        "native": {"reasoning_level": "max", "model": "GLM-5.3"},
        "budget": {"workers": 13, "repetitions": 3, "timeout_s": 1800,
                   "source_calls": 60, "source_result_chars": 24000,
                   "knowledge_pages": 2, "knowledge_chars": 6000},
    }
    write(campaign_path, value)
    return value


def analysis_groups(cases):
    return {"primary_prospective": [c["number"] for c in cases if not c["target_base_diverged"]],
            "older_fork_exploratory": [c["number"] for c in cases if c["target_base_diverged"]]}


def derive_pr_campaign(previous: Path, run_root: Path):
    """Keep selected heads, but use the actual PR fork point for each diff.

    GitHub's pull.base.sha is the target tip, not necessarily the diff base.
    The old experiment inputs remain immutable evidence of that setup error.
    """
    old = json.loads(previous.read_bytes())
    run_root = run_root.resolve()
    inventory_path = previous.parent / "mapping/inventory.json"
    inv = json.loads(inventory_path.read_bytes())
    campaign_path = run_root / "campaign.json"
    # Once an experiment exists, validate it without rewriting any hashed input.
    if campaign_path.exists():
        existing = json.loads(campaign_path.read_bytes())
        assert {c["number"]: c["head"] for c in existing["cases"]} == HEADS
        assert existing["prior_setup_sha256"] == sha(previous)
        for c in existing["cases"]:
            assert sha(c["diff_path"]) == c["diff_sha256"]
            assert sha(c["context_path"]) == c["context_sha256"]
            assert command(["git", "rev-parse", "HEAD"], c["source_root"]).decode().strip() == c["head"]
            assert command(["git", "merge-base", BASE, c["head"]], c["source_root"]).decode().strip() == c["base"]
        assert existing["arms"] == {arm: {k: inv["snapshots"][arm][k] for k in ("doc_root", "repo_subdir", "sha256")}
                                    for arm in ("A", "B")}
        return existing
    rows = []
    for case in old["cases"]:
        checkout = case["source_root"]
        head = command(["git", "rev-parse", "HEAD"], checkout).decode().strip()
        assert head == case["head"] == HEADS[case["number"]]
        base = command(["git", "merge-base", BASE, head], checkout).decode().strip()
        directory = run_root / "cases" / str(case["number"])
        directory.mkdir(parents=True, exist_ok=True)
        context = json.loads(Path(case["context_path"]).read_bytes())
        context.update(frozen_base=base, frozen_target=BASE)
        context_path = directory / "context.json"
        write(context_path, context)
        diff_path = directory / "diff.patch"
        diff_path.write_bytes(command(["git", "diff", "--no-ext-diff", "--no-color", base, head, "--"], checkout))
        files = command(["git", "diff", "--name-only", "-z", base, head, "--"], checkout).decode().split("\0")
        rows.append({**case, "base": base, "target": BASE, "head": head,
                     "diff_path": str(diff_path), "context_path": str(context_path),
                     "diff_sha256": sha(diff_path), "context_sha256": sha(context_path),
                     "changed_files": [f for f in files if f],
                     "target_base_diverged": base != BASE})
    value = {**old, "run_root": str(run_root), "cases": rows,
             "analysis_groups": analysis_groups(rows),
             "created_at": datetime.now(timezone.utc).isoformat(),
             "prior_setup_path": str(previous), "prior_setup_sha256": sha(previous),
             "diff_policy": "git merge-base(frozen target, frozen head) to frozen head; source checkout is frozen PR head",
             "arms": {arm: {k: inv["snapshots"][arm][k] for k in ("doc_root", "repo_subdir", "sha256")}
                      for arm in ("A", "B")}}
    write(campaign_path, value)
    return value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--derive-pr-bases-from", type=Path,
                        help="freeze corrected PR merge-base diffs without modifying prior run records")
    parser.add_argument("--knowledge-checkout", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    if args.derive_pr_bases_from:
        result = derive_pr_campaign(args.derive_pr_bases_from.resolve(), args.run_root)
    elif args.source:
        result = prepare(args.run_root, args.source, args.knowledge_checkout)
    else:
        parser.error("--source or --derive-pr-bases-from is required")
    print(json.dumps({"campaign": str(args.run_root / "campaign.json"), "cases": len(result["cases"])}))
