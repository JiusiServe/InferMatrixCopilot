"""Run independent execution partitions with the unchanged global coverage policy.

Each worker uses the native init generator, judge, checkpoints and publication
gate. Partial partitions never publish. Their accepted pages are assembled for
the separate native/source/retrieval audits before the authorized PR.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
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
                       feature_ids=tuple(args.feature_ids.split(",")), retry_unfinished=args.retry,
                       acceptance_mode=getattr(args, "acceptance_mode", "strict"),
                       depth_index_path=getattr(args, "depth_index_path", None),
                       stop_file=getattr(args, "stop_file", None))
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
    parser.add_argument("--workers", type=int, default=13)
    parser.add_argument("--acceptance-mode", choices=("strict", "lightweight"), default="lightweight")
    parser.add_argument("--depth-index-path", type=Path)
    parser.add_argument("--stop-file", type=Path, help="Create this file to stop new dispatch and drain active calls")
    parser.add_argument("--priority-features", default="", help="Visit these policy features first without changing audit scope")
    parser.add_argument("--retry", action="store_true")
    parser.add_argument("--worker", type=int)
    parser.add_argument("--feature-ids")
    args = parser.parse_args()
    if not 1 <= args.workers <= 13:
        parser.error("workers must be between one and thirteen")
    args.root, args.state, args.upstream_mirror = args.root.resolve(), args.state.resolve(), args.upstream_mirror.resolve()
    args.stop_file = (args.stop_file or args.state / "STOP").resolve()
    if args.depth_index_path:
        args.depth_index_path = args.depth_index_path.resolve()
    if args.worker is not None:
        if not 0 <= args.worker < args.workers or not args.feature_ids:
            parser.error("worker must belong to the campaign and have feature IDs")
        return worker(args)
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
    from infermatrix_copilot.kb_service.outbox import atomic_write_json

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
               "workers": args.workers, "partitions": partitions,
               "acceptance_mode": getattr(args, "acceptance_mode", "strict")}
    metadata = args.state / "campaign.json"
    if metadata.exists():
        prior = json.loads(metadata.read_text())
        if any(prior.get(key) != value for key, value in summary.items()):
            parser.error("campaign identity changed; use a fresh state directory")
    stop_file = getattr(args, "stop_file", None) or args.state / "STOP"
    index_path = getattr(args, "depth_index_path", None)
    if summary["acceptance_mode"] == "lightweight":
        from infermatrix_copilot.kb_service.depth_index import build_depth_index, load_depth_index
        from infermatrix_copilot.kb_service.knowledge_coverage import inventory

        index_path = index_path or args.state / "depth-index.json"
        policy_sha = hashlib.sha256(text.encode()).hexdigest()
        if index_path.exists():
            index = load_depth_index(index_path, pin=args.pin, policy_sha256=policy_sha)
        else:
            # A fresh export cannot inherit files from a previously interrupted
            # archive build. Only the complete immutable index is retained.
            with tempfile.TemporaryDirectory(prefix="source-index-", dir=args.state) as scratch:
                tree = KnowledgeRepo(args.upstream_mirror).export(args.pin, Path(scratch))
                index = build_depth_index(tree, inventory(tree, policy), pin=args.pin,
                                          policy_sha256=policy_sha, cache_path=index_path)
        summary["depth_index_sha256"] = index.sha256
        if metadata.exists() and prior.get("depth_index_sha256") != index.sha256:
            parser.error("campaign index changed; use a fresh state directory")
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
                "--baseline", args.baseline, "--workers", str(args.workers),
                "--worker", str(number), "--feature-ids", ",".join(features),
                "--acceptance-mode", summary["acceptance_mode"], "--stop-file", str(stop_file)]
        if index_path:
            argv += ["--depth-index-path", str(index_path)]
        if args.retry:
            argv.append("--retry")
        jobs.append((number, argv))
        checkpoints.append(state / f"init/{args.repo}/knowledge-deepen.json")
    atomic_write_json(metadata, summary)
    processes = []

    def snapshots():
        result = []
        for number, path in enumerate(checkpoints):
            if path.exists():
                record = json.loads(path.read_text())
                entries = record.get("depth", {}).get("features", {})
                result.append({"worker": number, "visited": sum(e.get("attempts", 0) > 0 for e in entries.values()),
                               "pages": len(record.get("depth", {}).get("accepted", {})),
                               "active": [f for f, e in entries.items() if e.get("status") in ("extracting", "extracted")],
                               "accounted_usd": record.get("spent_usd"), "status": record["status"]})
        return result

    def save_drain():
        inflight = []
        for path in args.state.glob("worker-*/init/traces/attempts/*/attempt.json"):
            attempt = json.loads(path.read_text())
            if attempt.get("status") == "inflight":
                inflight.append({"path": str(path), "id": attempt["id"], "model": attempt.get("model", {})})
        atomic_write_json(args.state / "drain.json", {"requested_at": stop_file.stat().st_mtime,
                          "observed_at": time.time(), "progress": snapshots(), "inflight": inflight,
                          "running_workers": [n for n, p, _ in processes if p.poll() is None]})

    def request_drain(signum, _frame):
        if not stop_file.exists():
            atomic_write_json(stop_file, {"signal": signal.Signals(signum).name, "at": time.time()})

    previous_handlers = {sig: signal.signal(sig, request_drain) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        for number, argv in jobs:
            if stop_file.exists():
                break
            log = (args.state / f"worker-{number}.log").open("a")
            try:
                process = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            except BaseException:
                log.close()
                raise
            processes.append((number, process, log))
        while any(process.poll() is None for _, process, _ in processes):
            if stop_file.exists():
                save_drain()
            print(json.dumps({"progress": snapshots(), "draining": stop_file.exists()}, ensure_ascii=False), flush=True)
            time.sleep(2 if stop_file.exists() else 20)
    finally:
        for sig, handler in previous_handlers.items():
            signal.signal(sig, handler)
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
    summary["drained"] = stop_file.exists()
    if summary["drained"]:
        save_drain()
    atomic_write_json(metadata, summary)
    return int(any(process.returncode != 0 for _, process, _ in processes))


if __name__ == "__main__":
    raise SystemExit(main())
