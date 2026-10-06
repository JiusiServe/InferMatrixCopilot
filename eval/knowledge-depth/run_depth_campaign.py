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


def baseline_inputs(args):
    """Resolve the adapter from the immutable baseline, including aliased dirs."""
    import yaml
    from infermatrix_copilot.kb_service.knowledge_coverage import policy_path

    names = subprocess.check_output(["git", "-C", str(args.root), "ls-tree", "-r", "--name-only",
                                     args.baseline, "adapters"], text=True).splitlines()
    found = []
    for name in names:
        if not re.fullmatch(r"adapters/[A-Za-z0-9_-]+/manifest\.yaml", name):
            continue
        text = subprocess.check_output(["git", "-C", str(args.root), "show", args.baseline + ":" + name], text=True)
        manifest = yaml.safe_load(text)
        if isinstance(manifest, dict) and isinstance(manifest.get("knowledge"), dict) \
                and manifest["knowledge"].get("repo_subdir") == "repos/" + args.repo:
            found.append((name, manifest))
    if len(found) != 1:
        raise ValueError("campaign baseline must contain exactly one adapter for this knowledge repository")
    name, manifest = found[0]
    relative = policy_path(args.repo, Path(name).parent)
    text = subprocess.check_output(["git", "-C", str(args.root), "show", args.baseline + ":" + relative], text=True)
    return manifest, text, relative


def discovery_handoff(args):
    """Validate a genuine completed record against the merged frozen catalog."""
    from types import SimpleNamespace
    from infermatrix_copilot.kb_service.init_stages import _Chain, _Stage
    from infermatrix_copilot.kb_service.init_support import InitRecord
    from infermatrix_copilot.kb_service.sources import KnowledgeRepo

    manifest, _, relative = baseline_inputs(args)
    report_path = f"eval/feature-discovery/{args.repo}-{args.pin[:12]}.json"
    knowledge = KnowledgeRepo(args.root)
    report = knowledge.show(args.baseline, report_path)
    lifecycle = manifest.get("knowledge_lifecycle") or {}
    configured = lifecycle.get("init") or {} if isinstance(lifecycle, dict) else None
    if not isinstance(configured, dict):
        raise ValueError("campaign baseline lifecycle/init must be a mapping")
    path = getattr(args, "discovery_record", None)
    if path is None:
        if report is not None or configured.get("feature_discovery_required"):
            raise ValueError("this campaign baseline requires --discovery-record; the frozen catalog gate cannot be omitted")
        return None
    path = Path(path).resolve()
    raw = path.read_bytes()
    record_hash = hashlib.sha256(raw).hexdigest()
    expected = getattr(args, "discovery_record_sha256", None)
    if expected is not None and record_hash != expected:
        raise ValueError("discovery prerequisite record changed after campaign binding")
    data = json.loads(raw)
    if not isinstance(data, dict) or not isinstance(data.get("discovery"), dict):
        raise ValueError("discovery handoff record must contain a discovery mapping")
    record = InitRecord(**data)
    if record.stage != "feature-discovery" or record.repo != args.repo or record.pin != args.pin \
            or record.status not in ("published", "empty") or record.discovery.get("done") is not True \
            or record.status == "published" and record.dry_run:
        raise ValueError("discovery handoff requires the original published/empty completed record for this repository and pin")
    # Reuse the production gate: verify real PR state, complete report, feature
    # IDs, owners and the exact catalog/report hashes at the merged baseline.
    # The temporary file is the original record's bytes, never a replacement
    # status or a fabricated prerequisite. Native archives stay at their origin.
    with tempfile.TemporaryDirectory(prefix="discovery-handoff-") as scratch:
        state = Path(scratch)
        copied = InitRecord.path(state, args.repo, "feature-discovery")
        copied.parent.mkdir(parents=True)
        copied.write_bytes(raw)
        stage = _Stage(SimpleNamespace(state_dir=state, knowledge=knowledge, gh_run=subprocess.run),
                       SimpleNamespace(repo=args.repo, knowledge_dir="repos/" + args.repo,
                                       adapter_dir=Path(relative).parent,
                                       init=SimpleNamespace(feature_discovery_required=True)),
                       dry_run=False, pin=args.pin)
        stage.STAGE = "knowledge-deepen"
        stage.repo_dir, stage._base_sha = "repos/" + args.repo, args.baseline
        chain = _Chain()
        stage._discovery_gate(chain, args.pin)
        if chain.problems:
            raise ValueError("discovery handoff failed the merged catalog gate: " + "; ".join(chain.problems))
        binding = stage._discovery_binding()
    return {"record_path": str(path), "record_sha256": record_hash,
            "report_path": report_path, **binding}


def foundation_handoff(args):
    """Bind explicit partial depth to the genuine published foundation bytes."""
    mode = getattr(args, "foundation_mode", "strict")
    path = getattr(args, "foundation_record", None)
    if mode == "strict" and path is None:
        return None
    if mode != "partial" or path is None:
        raise ValueError("partial depth requires --foundation-record; strict depth cannot use one")
    from infermatrix_copilot.kb_service.foundation_publication import foundation_handoff as validate
    from infermatrix_copilot.kb_service.init_support import InitError
    from infermatrix_copilot.kb_service.sources import KnowledgeRepo

    try:
        binding = validate(Path(path), knowledge=KnowledgeRepo(args.root), baseline=args.baseline,
                           repo=args.repo, pin=args.pin)
    except InitError as exc:
        raise ValueError(str(exc)) from exc
    expected = getattr(args, "foundation_record_sha256", None)
    if expected is not None and expected != binding["record_sha256"]:
        raise ValueError("foundation prerequisite record changed after campaign binding")
    return binding


def install_discovery_handoff(args, state, binding):
    """Copy the exact immutable prerequisite into a worker without rewriting it."""
    if binding is None:
        return
    from infermatrix_copilot.kb_service.init_support import InitRecord

    raw = Path(binding["record_path"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != binding["record_sha256"]:
        raise ValueError("discovery prerequisite record changed before worker handoff")
    dest = InitRecord.path(state, args.repo, "feature-discovery")
    if dest.exists():
        if dest.read_bytes() != raw:
            raise ValueError("worker discovery prerequisite differs from the immutable campaign record")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    temporary = dest.with_suffix(".json.tmp")
    temporary.write_bytes(raw)
    os.replace(temporary, dest)


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
    if getattr(args, "repair_guidance", None):
        os.environ["KB_DEPTH_REPAIR_GUIDANCE"] = str(args.repair_guidance)
        os.environ["KB_DEPTH_REPAIR_GUIDANCE_SHA256"] = args.repair_guidance_sha256
    else:
        os.environ.pop("KB_DEPTH_REPAIR_GUIDANCE", None)
        os.environ.pop("KB_DEPTH_REPAIR_GUIDANCE_SHA256", None)
    if KnowledgeRepo(state / "init/knowledge-repo").fetch() != args.baseline:
        raise RuntimeError("worker knowledge baseline differs from the immutable campaign")
    previous = InitRecord.load(state, args.repo, "knowledge-deepen")
    if previous and (previous.kb_base_sha != args.baseline or previous.pin != args.pin):
        raise RuntimeError("worker checkpoint source or knowledge baseline differs from campaign")
    binding = discovery_handoff(args)
    if binding is not None:
        metadata = json.loads((args.state / "campaign.json").read_bytes())
        if metadata.get("discovery") != binding:
            raise RuntimeError("worker discovery handoff differs from the frozen campaign identity")
        install_discovery_handoff(args, state, binding)
    foundation = foundation_handoff(args)
    if foundation is not None:
        metadata = json.loads((args.state / "campaign.json").read_bytes())
        if metadata.get("foundation_mode") != "partial" or metadata.get("foundation") != foundation:
            raise RuntimeError("worker foundation handoff differs from the frozen campaign identity")
    runtime = InitRuntime.from_env(Settings(_env_file=None), state_dir=state)
    from infermatrix_copilot.kb_service.depth_pacing import SharedZcodePacer
    runtime.gateway.configure_zcode_pacing(SharedZcodePacer(
        getattr(args, "zcode_pacing_path", None) or args.state / "zcode-pacing.json",
        start_interval=getattr(args, "zcode_start_interval", 15.0),
        rate_cooldown=getattr(args, "zcode_rate_cooldown", 90.0),
        stop_file=getattr(args, "stop_file", None) or args.state / "STOP"))
    runtime.upstream_remote = lambda _: str(args.upstream_mirror)
    record = run_stage(runtime, runtime.registry[args.repo], "knowledge-deepen", dry_run=True,
                       from_existing=True, pin=args.pin, unlimited_subscription=True,
                       feature_ids=tuple(args.feature_ids.split(",")), retry_unfinished=args.retry,
                       acceptance_mode=getattr(args, "acceptance_mode", "strict"),
                       depth_index_path=getattr(args, "depth_index_path", None),
                       stop_file=getattr(args, "stop_file", None),
                       **({"foundation_mode": "partial", "foundation_record_path": Path(foundation["record_path"])}
                          if foundation is not None else {}))
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
    parser.add_argument("--repair-guidance", type=Path, help="Pinned, immutable localization hints for a newly authorized gap-repair batch")
    parser.add_argument("--repair-guidance-sha256", help=argparse.SUPPRESS)
    parser.add_argument("--discovery-record", type=Path,
                        help="Original completed, merged feature-discovery record; required for a discovered catalog")
    parser.add_argument("--discovery-record-sha256", help=argparse.SUPPRESS)
    parser.add_argument("--foundation-mode", choices=("strict", "partial"), default="strict")
    parser.add_argument("--foundation-record", type=Path,
                        help="Original published partial foundation record; required for explicit partial depth")
    parser.add_argument("--foundation-record-sha256", help=argparse.SUPPRESS)
    parser.add_argument("--zcode-pacing-path", type=Path)
    parser.add_argument("--zcode-start-interval", type=float, default=15.0)
    parser.add_argument("--zcode-rate-cooldown", type=float, default=90.0)
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
    if args.repair_guidance:
        args.repair_guidance = args.repair_guidance.resolve()
    if args.discovery_record:
        args.discovery_record = args.discovery_record.resolve()
    if args.foundation_record:
        args.foundation_record = args.foundation_record.resolve()
    if (args.foundation_mode == "partial") != bool(args.foundation_record):
        parser.error("partial foundation mode requires --foundation-record; strict mode cannot use one")
    if args.zcode_pacing_path:
        args.zcode_pacing_path = args.zcode_pacing_path.resolve()
    from infermatrix_copilot.kb_service.depth_pacing import SharedZcodePacer
    try:
        SharedZcodePacer(args.zcode_pacing_path or args.state / "zcode-pacing.json",
                         start_interval=args.zcode_start_interval, rate_cooldown=args.zcode_rate_cooldown)
    except ValueError as exc:
        parser.error(str(exc))
    if args.worker is not None:
        if not 0 <= args.worker < args.workers or not args.feature_ids:
            parser.error("worker must belong to the campaign and have feature IDs")
        if args.repair_guidance and not re.fullmatch(r"[0-9a-f]{64}", args.repair_guidance_sha256 or ""):
            parser.error("guided workers require their parent's immutable guidance hash")
        if args.discovery_record and not re.fullmatch(r"[0-9a-f]{64}", args.discovery_record_sha256 or ""):
            parser.error("discovery workers require their parent's immutable prerequisite hash")
        if args.foundation_record and not re.fullmatch(r"[0-9a-f]{64}", args.foundation_record_sha256 or ""):
            parser.error("partial workers require their parent's immutable foundation hash")
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
    from infermatrix_copilot.kb_service.knowledge_coverage import load_policy
    from infermatrix_copilot.kb_service.sources import KnowledgeRepo
    from infermatrix_copilot.kb_service.outbox import atomic_write_json

    manifest, text, _ = baseline_inputs(args)
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
    try:
        binding = discovery_handoff(args)
        foundation = foundation_handoff(args)
    except (ValueError, TypeError, OSError) as exc:
        parser.error(str(exc))
    if binding is not None:
        summary["discovery"] = binding
    if foundation is not None:
        summary.update(foundation_mode="partial", foundation=foundation)
    if getattr(args, "repair_guidance", None):
        from infermatrix_copilot.kb_service.depth_inputs import load_repair_guidance
        guidance = load_repair_guidance(args.repair_guidance, pin=args.pin,
                                        policy_sha256=hashlib.sha256(text.encode()).hexdigest(), baseline=args.baseline)
        if summary["acceptance_mode"] != "lightweight" or set(row["feature"] for row in guidance["rows"]) - {f.id for f in policy.features}:
            parser.error("repair guidance must address declared features in lightweight mode")
        summary["repair_guidance_sha256"] = guidance["guidance_sha256"]
        summary["repair_guidance_facets"] = len(guidance["rows"])
    metadata = args.state / "campaign.json"
    if metadata.exists():
        prior = json.loads(metadata.read_text())
        if (prior.get("foundation_mode", "strict") != summary.get("foundation_mode", "strict")
                or prior.get("foundation") != summary.get("foundation")
                or prior.get("repair_guidance_sha256") != summary.get("repair_guidance_sha256")) or any(
                prior.get(key) != value for key, value in summary.items()):
            parser.error("campaign identity changed; use a fresh state directory")
    stop_file = getattr(args, "stop_file", None) or args.state / "STOP"
    from infermatrix_copilot.kb_service.depth_pacing import SharedZcodePacer
    pacing_path = getattr(args, "zcode_pacing_path", None) or args.state / "zcode-pacing.json"
    pacer = SharedZcodePacer(pacing_path, start_interval=getattr(args, "zcode_start_interval", 15.0),
                            rate_cooldown=getattr(args, "zcode_rate_cooldown", 90.0), stop_file=stop_file)
    pacer.prepare()
    summary["zcode_pacing"] = {"path": str(pacing_path), **pacer.config}
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
        try:
            install_discovery_handoff(args, state, binding)
        except (ValueError, OSError) as exc:
            parser.error(str(exc))
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
                "--acceptance-mode", summary["acceptance_mode"], "--stop-file", str(stop_file),
                "--zcode-pacing-path", str(pacing_path),
                "--zcode-start-interval", str(pacer.config["start_interval_s"]),
                "--zcode-rate-cooldown", str(pacer.config["rate_cooldown_s"])]
        if index_path:
            argv += ["--depth-index-path", str(index_path)]
        if getattr(args, "repair_guidance", None):
            argv += ["--repair-guidance", str(args.repair_guidance),
                     "--repair-guidance-sha256", summary["repair_guidance_sha256"]]
        if binding is not None:
            argv += ["--discovery-record", binding["record_path"],
                     "--discovery-record-sha256", binding["record_sha256"]]
        if foundation is not None:
            argv += ["--foundation-mode", "partial", "--foundation-record", foundation["record_path"],
                     "--foundation-record-sha256", foundation["record_sha256"]]
        if args.retry:
            argv.append("--retry")
        jobs.append((number, argv))
        checkpoints.append(state / f"init/{args.repo}/knowledge-deepen.json")
    atomic_write_json(metadata, summary)
    processes = []

    last_snapshots = {}

    def snapshots():
        result = []
        for number, path in enumerate(checkpoints):
            try:
                record = json.loads(path.read_bytes())
            except FileNotFoundError:
                continue
            except (OSError, json.JSONDecodeError) as exc:
                result.append({**last_snapshots.get(number, {"worker": number}),
                               "snapshot_error": {"type": type(exc).__name__, "errno": getattr(exc, "errno", None)},
                               "using_last_safe_snapshot": number in last_snapshots})
                continue
            entries = record.get("depth", {}).get("features", {})
            snapshot = {"worker": number, "visited": sum(e.get("attempts", 0) > 0 for e in entries.values()),
                               "pages": len(record.get("depth", {}).get("accepted", {})),
                               "active": [f for f, e in entries.items() if e.get("status") in ("extracting", "extracted")],
                               "accounted_usd": record.get("spent_usd"), "status": record["status"]}
            last_snapshots[number] = snapshot
            result.append(snapshot)
        return result

    def save_drain():
        inflight = []
        try:
            journals = list(args.state.glob("worker-*/init/traces/attempts/*/attempt.json"))
        except OSError as exc:
            journals = []
            inflight.append({"operation": "journal_glob", "read_error": {"type": type(exc).__name__, "errno": exc.errno}})
        for path in journals:
            try:
                attempt = json.loads(path.read_bytes())
            except (OSError, json.JSONDecodeError) as exc:
                inflight.append({"path": str(path), "read_error": {"type": type(exc).__name__, "errno": getattr(exc, "errno", None)}})
                continue
            if attempt.get("status") == "inflight":
                inflight.append({"path": str(path), "id": attempt["id"], "model": attempt.get("model", {})})
        try:
            requested_at = stop_file.stat().st_mtime
        except OSError as exc:
            requested_at = None
            inflight.append({"operation": "stop_stat", "read_error": {"type": type(exc).__name__, "errno": exc.errno}})
        report = {"requested_at": requested_at,
                          "observed_at": time.time(), "progress": snapshots(), "inflight": inflight,
                          "running_workers": [n for n, p, _ in processes if p.poll() is None]}
        try:
            atomic_write_json(args.state / "drain.json", report)
        except OSError as exc:
            print(json.dumps({"drain_snapshot_error": {"type": type(exc).__name__, "errno": exc.errno}}), flush=True)

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
