"""Run independent execution partitions with the unchanged global coverage policy.

Each worker uses the native init generator, judge, checkpoints and publication
gate. Partial partitions never publish. Their accepted pages are assembled for
the separate native/source/retrieval audits before the authorized PR.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path


def git(*args):
    subprocess.run(["git", *map(str, args)], check=True, stdout=subprocess.DEVNULL)


def worker(args):
    state = args.state / f"worker-{args.worker}"
    state.mkdir(parents=True, exist_ok=True)
    with (state / ".worker.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return run_worker(args, state)


def run_worker(args, state):
    from infermatrix_copilot.config import Settings
    from infermatrix_copilot.kb_service.init_support import InitRuntime
    from infermatrix_copilot.kb_service.init_stages import run_stage
    from infermatrix_copilot.kb_service.sources import KnowledgeRepo
    from infermatrix_copilot.kb_service.init_support import InitRecord

    os.environ["KB_INIT_KNOWLEDGE_CLONE"] = str(state / "init/knowledge-repo")
    os.environ["ADAPTERS_DIR"] = str(args.root / "adapters")
    if KnowledgeRepo(state / "init/knowledge-repo").fetch() != args.baseline:
        raise RuntimeError("worker knowledge baseline differs from the immutable campaign")
    previous = InitRecord.load(state, args.repo, "knowledge-deepen")
    if previous and (previous.kb_base_sha != args.baseline or previous.pin != args.pin):
        raise RuntimeError("worker checkpoint source or knowledge baseline differs from campaign")
    runtime = InitRuntime.from_env(Settings(_env_file=None), state_dir=state)
    runtime.upstream_remote = lambda _: str(args.upstream_mirror)
    record = run_stage(runtime, runtime.registry[args.repo], "knowledge-deepen", dry_run=True,
                       from_existing=True, pin=args.pin, unlimited_subscription=True,
                       feature_ids=tuple(args.feature_ids.split(",")), retry_unfinished=args.retry)
    if record.kb_base_sha != args.baseline or record.pin != args.pin:
        raise RuntimeError("worker completed against a different source or knowledge baseline")
    print(json.dumps({"worker": args.worker, "status": record.status, "problems": record.problems,
                      "recognized": record.coverage.get("semantic_depth", {}).get("recognized_facets"),
                      "accounted_usd": record.spent_usd}, ensure_ascii=False), flush=True)
    return 1 if record.status == "blocked" else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pin", required=True)
    parser.add_argument("--upstream-mirror", type=Path, required=True)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--priority-features", default="", help="Visit these policy features first without changing audit scope")
    parser.add_argument("--retry", action="store_true")
    parser.add_argument("--worker", type=int)
    parser.add_argument("--feature-ids")
    args = parser.parse_args()
    if args.worker is not None:
        return worker(args)
    if not 1 <= args.workers <= 4:
        parser.error("workers must be between one and four")
    args.root, args.state, args.upstream_mirror = args.root.resolve(), args.state.resolve(), args.upstream_mirror.resolve()
    args.baseline = subprocess.check_output(["git", "-C", str(args.root), "rev-parse", args.baseline + "^{commit}"], text=True).strip()
    args.state.mkdir(parents=True, exist_ok=True)
    with (args.state / ".campaign.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error("campaign is already running in this state directory")
        return campaign(args, parser)


def campaign(args, parser):
    from infermatrix_copilot.kb_service.knowledge_coverage import load_policy, policy_path
    from infermatrix_copilot.kb_service.sources import KnowledgeRepo
    import yaml

    manifest = yaml.safe_load((args.root / f"adapters/{args.repo}/manifest.yaml").read_text())
    text = subprocess.check_output(["git", "-C", str(args.root), "show", args.baseline + ":" + policy_path(args.repo)], text=True)
    policy = load_policy(text, manifest["knowledge"]["repo_subdir"])
    if policy.semantic_depth_per_facet_gt is None:
        parser.error("campaign baseline must declare its global semantic completion target")
    if not re.fullmatch(r"[0-9a-f]{40}", args.pin):
        parser.error("campaign pin must be a full immutable commit SHA")
    kind = subprocess.check_output(["git", "--git-dir", str(args.upstream_mirror), "cat-file", "-t", args.pin], text=True).strip()
    if kind != "commit":
        parser.error("source pin is not a commit in the upstream mirror")
    partitions = {str(n): [f.id for i, f in enumerate(policy.features) if i % args.workers == n]
                  for n in range(args.workers)}
    priority = list(dict.fromkeys(filter(None, getattr(args, "priority_features", "").split(","))))
    if set(priority) - {f.id for f in policy.features}:
        parser.error("priority features must belong to the unchanged coverage policy")
    for worker, group in partitions.items():
        partitions[worker] = [fid for fid in priority if fid in group] + [fid for fid in group if fid not in priority]
    summary = {"baseline": args.baseline, "pin": args.pin, "repo": args.repo,
               "features": len(policy.features), "denominator": len(policy.features) * 7,
               "workers": args.workers, "partitions": partitions}
    metadata = args.state / "campaign.json"
    if metadata.exists():
        prior = json.loads(metadata.read_text())
        if any(prior.get(key) != value for key, value in summary.items()):
            parser.error("campaign identity changed; use a fresh state directory")
    origin = args.state / "knowledge-origin.git"
    if not origin.exists():
        git("init", "--bare", origin)
        git("-C", args.root, "push", origin, args.baseline + ":refs/heads/main")
        git("--git-dir", origin, "symbolic-ref", "HEAD", "refs/heads/main")
    if subprocess.check_output(["git", "--git-dir", str(origin), "rev-parse", "main"], text=True).strip() != args.baseline:
        parser.error("campaign baseline is immutable; use a fresh state directory")
    jobs, checkpoints = [], []
    for number in range(args.workers):
        state = args.state / f"worker-{number}"
        clone = state / "init/knowledge-repo"
        if not clone.exists():
            clone.parent.mkdir(parents=True, exist_ok=True)
            git("clone", "--quiet", "--shared", "--no-checkout", origin, clone)
        remote = subprocess.check_output(["git", "-C", str(clone), "remote", "get-url", "origin"], text=True).strip()
        if Path(remote).resolve() != origin or KnowledgeRepo(clone).fetch() != args.baseline:
            parser.error("worker clone no longer belongs to the immutable campaign")
        features = partitions[str(number)]
        argv = [sys.executable, __file__, "--root", str(args.root), "--state", str(args.state),
                "--repo", args.repo, "--pin", args.pin, "--upstream-mirror", str(args.upstream_mirror),
                "--baseline", args.baseline, "--worker", str(number), "--feature-ids", ",".join(features)]
        if args.retry:
            argv.append("--retry")
        jobs.append((number, argv))
        checkpoints.append(state / f"init/{args.repo}/knowledge-deepen.json")
    metadata.write_text(json.dumps(summary, indent=2) + "\n")
    processes = []
    try:
        for number, argv in jobs:
            log = (args.state / f"worker-{number}.log").open("a")
            try:
                process = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            except BaseException:
                log.close()
                raise
            processes.append((number, process, log))
        while any(process.poll() is None for _, process, _ in processes):
            snapshots = []
            for number, path in enumerate(checkpoints):
                if path.exists():
                    record = json.loads(path.read_text())
                    entries = record.get("depth", {}).get("features", {})
                    snapshots.append({"worker": number, "visited": sum(e.get("attempts", 0) > 0 for e in entries.values()),
                                      "pages": len(record.get("depth", {}).get("accepted", {})),
                                      "active": [f for f, e in entries.items() if e.get("status") in ("extracting", "extracted")],
                                      "accounted_usd": record.get("spent_usd"), "status": record["status"]})
            print(json.dumps({"progress": snapshots}, ensure_ascii=False), flush=True)
            time.sleep(20)
    finally:
        cleanup_errors = []
        for _, process, log in processes:
            try:
                # The leader may have exited while a model child still owns
                # this process group. Stop the owned group in either case.
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait()
            except Exception as exc:
                cleanup_errors.append(exc)
            finally:
                log.close()
        if cleanup_errors:
            raise cleanup_errors[0]
    summary["exit_codes"] = {number: process.returncode for number, process, _ in processes}
    metadata.write_text(json.dumps(summary, indent=2) + "\n")
    return int(any(process.returncode != 0 for _, process, _ in processes))


if __name__ == "__main__":
    raise SystemExit(main())
