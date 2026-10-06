"""Portable CLI orchestration. Reviewed previews and activation are explicit operations."""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

import yaml

from .git_source import GitSource
from .init_support import InitError, InitRecord
from .portable_init import portable_runtime, bootstrap_workspace, stage_receipt, accept_stage, _git
from .repo_spec import RepoRegistry, RepoSpec, acceptance_receipt, propose_repository, repository_inventory, REGISTRY_FILE


def add_commands(sub):
    onboard = sub.add_parser("onboard", help="propose a portable repository identity and scanning scope")
    onboard.add_argument("source")
    onboard.add_argument("--propose", action="store_true", default=True)
    onboard.add_argument("--repo-id")
    onboard.add_argument("--pin")
    onboard.add_argument("--storage", choices=("central", "in_repo"), default="central")
    onboard.add_argument("--forge", choices=("none", "github", "gitlab"))
    onboard.add_argument("--out", type=Path)
    repo = sub.add_parser("repo", help="register reviewed proposals and accept local stage previews")
    commands = repo.add_subparsers(dest="repo_command", required=True)
    review = commands.add_parser("receipt", help="record explicit acceptance of an exact repository proposal")
    review.add_argument("--proposal", type=Path, required=True)
    review.add_argument("--source", type=Path, required=True)
    review.add_argument("--out", type=Path)
    register = commands.add_parser("register")
    register.add_argument("--proposal", type=Path, required=True)
    register.add_argument("--review-receipt", type=Path, required=True)
    register.add_argument("--source", type=Path, required=True)
    register.add_argument("--knowledge-root", type=Path, required=True)
    commands.add_parser("list")
    for name in ("review-stage", "accept-stage"):
        cmd = commands.add_parser(name)
        cmd.add_argument("repo")
        cmd.add_argument("--stage", required=True)
        if name == "review-stage":
            cmd.add_argument("--reviewer", required=True)
            cmd.add_argument("--out", type=Path)
        else:
            cmd.add_argument("--review-receipt", type=Path, required=True)
    publish = commands.add_parser("publish", help="publish an accepted knowledge slice to its canonical store")
    publish.add_argument("repo")
    publish.add_argument("--snapshot-out", type=Path, required=True)
    publish.add_argument("--partial-foundation", action="store_true")
    mirror = sub.add_parser("mirror", help="export a hash-bound, read-only knowledge snapshot")
    mirror.add_argument("repo")
    mirror.add_argument("--out", type=Path, required=True)
    update = sub.add_parser("update", help="compare the fixed baseline and prepare an incremental discovery batch")
    update.add_argument("repo")
    update.add_argument("--to", required=True)
    update.add_argument("--dry-run", action="store_true")
    update.add_argument("--apply", action="store_true", help="register and prepare the new batch; extraction is a separate kb init invocation")
    update.add_argument("--out", type=Path)


def _json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def emit(value, path=None):
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text, encoding="utf-8")
    print(text, end="")


def run_portable_init(args, state_dir):
    from ..config import Settings
    from .init_stages import run_stage

    rt, lc = portable_runtime(Settings(), state_dir, args.repo)
    rt.discovery_paths = tuple(_json(Path(state_dir) / "incremental.json").get("scan_paths", [])) \
        if (Path(state_dir) / "incremental.json").is_file() else None
    if args.suggest_seeds:
        from .init_stages import suggest_seeds
        emit({"seeds": suggest_seeds(rt, lc)})
        return 0
    if not args.stage:
        raise InitError("kb init requires --stage")
    if args.pin and args.pin != rt.portable_spec.source_pin:
        raise InitError("source pin differs from registered batch; use kb update to prepare a new batch")
    previous = InitRecord.load(Path(state_dir), lc.repo, args.stage)
    if previous and previous.status == "accepted":
        from .portable_init import check_local_acceptance
        check_local_acceptance(rt, previous)
        emit({"repo_id": lc.repo, "stage": args.stage, "status": "accepted", "source_pin": previous.pin,
              "published": False, "review_required": False})
        return 0
    kwargs = {key: getattr(args, key) for key in ("pr_count", "budget_usd", "from_existing", "subscription_generator", "unlimited_subscription", "retry_unfinished", "acceptance_mode", "foundation_mode") if hasattr(args, key)}
    if rt.generator.provider == "zcode":
        kwargs["subscription_generator"] = True
        if args.stage in ("feature-discovery", "modules", "knowledge", "knowledge-deepen") and kwargs.get("budget_usd") is None:
            kwargs["unlimited_subscription"] = True
    if args.stage == "knowledge-deepen" and not getattr(args, "acceptance_mode_explicit", False):
        kwargs["acceptance_mode"] = "lightweight"
    if args.stage == "knowledge":
        # Portable foundation generates a new native batch, then offers the
        # checked partial preview. The legacy publication-only path is retained.
        kwargs["foundation_mode"] = "strict"
    elif args.stage == "knowledge-deepen":
        kwargs["foundation_mode"] = "partial"
    if getattr(args, "foundation_record", None):
        kwargs["foundation_record_path"] = args.foundation_record
    record = run_stage(rt, lc, args.stage, dry_run=True, pin=args.pin or rt.portable_spec.source_pin, **kwargs)
    emit({"repo_id": lc.repo, "stage": args.stage, "status": record.status,
          "source_pin": record.pin, "review_required": record.status == "dry_run",
          "published": False, "problems": record.problems, "preview": record.pr.get("dry_run_dir")})
    return 0 if record.status in ("dry_run", "accepted", "empty") else 1


def publish_portable(state_dir, selector, dest, *, partial=False):
    from .knowledge_store import KnowledgeStore
    from .portable_init import check_local_acceptance, LocalKnowledgeRepo, source_identity
    from types import SimpleNamespace

    row = RepoRegistry(state_dir).resolve(selector)
    if not row:
        raise InitError("repository is not registered")
    spec = RepoSpec.from_dict(row["spec"])
    stage = "knowledge" if partial else "knowledge-deepen"
    record = InitRecord.load(Path(state_dir), spec.repo_id, stage)
    if not record or record.status != "accepted":
        raise InitError("publication requires an explicitly accepted knowledge preview")
    if not partial and not record.depth.get("target_met"):
        raise InitError("seven-facet final acceptance is unmet; retain the checkpoint")
    root = bootstrap_workspace(state_dir, row)
    knowledge = LocalKnowledgeRepo(root)
    check_local_acceptance(SimpleNamespace(knowledge=knowledge), record)
    head = record.pr["local_acceptance"]["head_sha"]
    if knowledge.main_sha() != head:
        raise InitError("publication baseline contains changes after the accepted knowledge head")
    files = knowledge.knowledge_files(head)
    policy_text = knowledge.show(head, f"adapters/{spec.repo_id}/knowledge-coverage.yaml")
    if not policy_text:
        raise InitError("publication is missing the frozen feature catalog")
    catalog = hashlib.sha256(policy_text.encode()).hexdigest()
    published_spec = replace(spec, catalog_hash=catalog, policy_hash=catalog)
    canonical = Path(row["bindings"]["knowledge_root"])
    dest = Path(dest).resolve()
    canonical = canonical.resolve()
    if KnowledgeStore(canonical, spec.repo_id, mode=spec.knowledge_storage).readonly:
        raise InitError("a read-only mirror cannot be a canonical publication authority")
    if dest.exists() or dest == canonical or dest.is_relative_to(canonical) or canonical.is_relative_to(dest):
        raise InitError("snapshot destination exists or overlaps the canonical knowledge store")
    from .init_support import run_knowledge_validators
    problems = run_knowledge_validators(knowledge, head, {})
    if problems:
        raise InitError("publication format validation failed: " + "; ".join(problems[:3]))
    if partial:
        from ..config import Settings
        from .portable_init import portable_runtime
        from .init_knowledge import _Knowledge
        from .init_knowledge_parallel import validate_checkpoint
        runtime, lifecycle = portable_runtime(Settings(), state_dir, spec.repo_id)
        runtime.unlimited_subscription = True
        runtime.subscription_generator = True
        if not record.coverage.get("foundation_jobs", {}).get("tasks"):
            raise InitError("foundation publication requires replayable native task receipts")
        stage_impl = _Knowledge(runtime, lifecycle, dry_run=True, pin=record.pin)
        stage_impl.repo_dir = lifecycle.knowledge_dir
        stage_impl._base_sha = record.kb_base_sha
        stage_impl._knowledge_run_pin = record.pin
        stage_impl.overlay = {}
        validate_checkpoint(stage_impl, record, record.inputs_digest)
    with tempfile.TemporaryDirectory(prefix="kb-publish-source-") as tmp:
        tree = GitSource(row["bindings"]["source_path"]).export(spec.source_pin, Path(tmp) / "source")
        from .knowledge_coverage import load_policy, audit_coverage, coverage_targets_met, inventory as code_inventory
        from .knowledge_depth import audit_depth
        policy = load_policy(policy_text, spec.knowledge_slice)
        if (set(policy.roots) != set(spec.source_roots) or policy.target < spec.coverage_target
                or policy.semantic_depth_per_facet_gt is None
                or policy.semantic_depth_per_facet_gt < spec.per_facet_gt):
            raise InitError("catalog scope or acceptance policy differs from the reviewed repository proposal")
        # The same deterministic empty-Python-marker rule applies to both
        # inventories. No catalog suffix/exclusion may hide other production code.
        from dataclasses import replace as replace_policy
        declared = repository_inventory(GitSource(row["bindings"]["source_path"]), spec)["production"]
        eligibility = replace_policy(policy, roots=(".",), exclude=(),
            suffixes=tuple(sorted({Path(p).suffix for p in declared if Path(p).suffix})),
            filenames=tuple(sorted({Path(p).name for p in declared if not Path(p).suffix})))
        expected_production = set(code_inventory(tree, eligibility)) & set(declared)
        if set(code_inventory(tree, policy)) != expected_production:
            raise InitError("catalog production inventory differs from the reviewed fixed source scope")
        structural = audit_coverage(files, tree, policy, full_name=source_identity(spec), pin=spec.source_pin)
        if not coverage_targets_met(structural, "partial"):
            raise InitError("production-file structural coverage is unmet")
        if not partial:
            from .native_depth_audit import audit_native_approvals
            native = audit_native_approvals(root, spec.repo_id, baseline_reports=[],
                trace_dirs=[Path(state_dir) / "init/traces"],
                checkpoints=[InitRecord.path(Path(state_dir), spec.repo_id, "knowledge-deepen")])
            if native["problems"]:
                raise InitError("native approval replay failed: " + "; ".join(native["problems"][:3]))
            depth = audit_depth(files, tree, policy, spec.source_pin, approvals=native["approvals"])
            if not depth["target_met"]:
                raise InitError("current source/knowledge/native audit fails final acceptance")
    selected = {p: t for p, t in files.items() if p.startswith(spec.knowledge_slice + "/")}
    selected[f"{spec.knowledge_slice}/_catalog.yaml"] = policy_text
    discovery_record = InitRecord.load(Path(state_dir), spec.repo_id, "feature-discovery")
    if discovery_record:
        report = json.loads(knowledge.show(head, discovery_record.discovery["report_path"]))
        selected[f"{spec.knowledge_slice}/_discovery.yaml"] = yaml.safe_dump({key: report[key]
            for key in ("pin", "catalog_sha256", "index_sha256", "evidence_bundles", "scan_mode", "scan_paths") if key in report}, sort_keys=False)
    marker_path = root / ".git" / "kb-registration.json"
    marker = _json(marker_path)
    expected = {p: marker.get("canonical_files", {}).get(p, "") for p in selected}
    acceptance = {"tier": "foundation" if partial else "final", "init_complete": not partial,
        "source_pin": spec.source_pin, "catalog_sha256": catalog,
        "checks": {"source": True, "native": True, "structural": True, "format": True,
                   "retrieval": True, "semantic_depth": not partial},
        "structural": structural, "semantic_depth": {} if partial else depth,
        "unknown": record.coverage.get("foundation", {}) if partial else {},
        "native_provenance_sha256": None if partial else hashlib.sha256(json.dumps(native["provenance"], sort_keys=True).encode()).hexdigest(),
        "actual_cost": "unknown", "upstream_tests_executed": False}
    # Validate the staged full store and its served retrieval before replacing
    # canonical files. A refused export must not partly publish knowledge.
    canonical.parent.mkdir(parents=True, exist_ok=True)
    dest.parent.mkdir(parents=True, exist_ok=True)
    from .portable_publication import check_publication
    from .activate import verify_snapshot
    from ..knowledge_docs import KnowledgeDocs
    with _canonical_lock(canonical):
        if dest.exists():
            raise InitError("snapshot destination already exists")
        with tempfile.TemporaryDirectory(prefix=".kb-publish-", dir=canonical.parent) as scratch:
            staged = Path(scratch) / "knowledge"
            if canonical.exists():
                if any(p.is_symlink() for p in canonical.rglob("*")):
                    raise InitError("canonical store cannot contain symlinks")
                shutil.copytree(canonical, staged)
            else:
                staged.mkdir()
            for name in ("AGENTS.md", "_format.yaml", "general/_index.md"):
                path = staged / name
                if not path.exists():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(knowledge.show(head, "knowledge/" + name), encoding="utf-8")
            store = KnowledgeStore(staged, spec.repo_id, mode=spec.knowledge_storage)
            store.write_files(selected, expected_hashes=expected)
            registry_path = staged / REGISTRY_FILE
            registry = yaml.safe_load(registry_path.read_text()) if registry_path.exists() else {"schema_version": 1, "repos": {}}
            registry["repos"][spec.repo_id] = published_spec.to_dict()
            registry_path.write_text(yaml.safe_dump(registry, allow_unicode=True, sort_keys=False), encoding="utf-8")
            index = staged / "repos/_index.md"
            if not index.exists():
                from .portable_init import _page
                index.write_text(_page("Repositories"), encoding="utf-8")
            link = f"- [{spec.title or spec.repo_id}]({spec.repo_id}/_index.md)"
            if link not in index.read_text():
                index.write_text(index.read_text().rstrip() + "\n" + link + "\n")
            docs = KnowledgeDocs(staged, repo_subdir=spec.knowledge_slice)
            for feature in policy.features:
                from .knowledge_depth import depth_page
                page = feature.page if partial else depth_page(feature)
                if not docs.read(page)["content"].strip():
                    raise InitError(f"{feature.id}: accepted knowledge is not readable by the context service")
            store.record_acceptance(source_pin=spec.source_pin, publication_head=head, acceptance=acceptance)
            with tempfile.TemporaryDirectory(prefix=".kb-snapshot-", dir=dest.parent) as export_tmp:
                prepared = Path(export_tmp) / "snapshot"
                manifest = store.snapshot(prepared, source_pin=spec.source_pin, publication_head=head)
                view = verify_snapshot(prepared)
                # Existing partial repositories can coexist in a central store;
                # activation separately requires an explicit partial choice.
                check_publication(view, allow_partial=True)
                backup = Path(scratch) / "previous"
                if canonical.exists():
                    canonical.rename(backup)
                try:
                    staged.rename(canonical)
                    prepared.rename(dest)
                except OSError:
                    if canonical.exists():
                        shutil.rmtree(canonical)
                    if backup.exists():
                        backup.rename(canonical)
                    raise
    marker["canonical_files"] = {p: hashlib.sha256(t.encode()).hexdigest() for p, t in selected.items()}
    marker_path.write_text(json.dumps(marker))
    return manifest


@contextmanager
def _canonical_lock(root):
    import fcntl
    with (root.parent / ("." + root.name + ".kb.lock")).open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def incremental_update(state_dir, selector, revision, *, apply=False):
    from .evidence_bundle import affected_features
    row = RepoRegistry(state_dir).resolve(selector)
    if not row:
        raise InitError("repository is not registered")
    spec = RepoSpec.from_dict(row["spec"])
    source = GitSource(row["bindings"]["source_path"])
    target = source.resolve(revision)
    changed = source.changed_paths(spec.source_pin, target)
    newer = replace(spec, source_pin=target)
    inventory = repository_inventory(source, newer)
    relevant = set(inventory["production"] + inventory["docs"] + inventory["tests"])
    old_inventory = repository_inventory(source, spec)
    relevant.update(old_inventory["production"] + old_inventory["docs"] + old_inventory["tests"])
    effective = sorted(set(changed) & relevant)
    # A host-selected in-repository canonical store is generated input, even
    # when its first publication happened after the original source pin.
    canonical = Path(row["bindings"]["knowledge_root"]).resolve()
    known_generated = []
    if canonical.is_relative_to(source.path.resolve()):
        relative_root = canonical.relative_to(source.path.resolve()).as_posix()
        if relative_root in inventory.get("generated_knowledge_roots", []):
            known_generated.append(relative_root)
            effective = [p for p in effective if not p.startswith(relative_root + "/")]
    old_record = InitRecord.load(Path(state_dir), spec.repo_id, "feature-discovery")
    bundles = {}
    if old_record and old_record.discovery.get("report_path"):
        root = bootstrap_workspace(state_dir, row)
        text = _git(root, "show", f"HEAD:{old_record.discovery['report_path']}")
        bundles = json.loads(text).get("evidence_bundles", {})
    affected = affected_features(bundles, effective)
    # References owned by affected features are useful neighbouring evidence,
    # while source/docs/tests inventory remains complete at the new fixed pin.
    scanned = set(inventory["production"] + inventory["docs"] + inventory["tests"])
    scan = sorted((set(effective) | {ref["path"] for fid in affected for ref in bundles[fid]["refs"]}) & scanned)
    batch = Path(state_dir) / "batches" / spec.repo_id / target
    report = {"schema_version": 1, "repo_id": spec.repo_id, "from_pin": spec.source_pin, "to_pin": target,
        "changed_paths": changed, "effective_changed_paths": effective, "affected_features": affected,
        "scan_paths": scan, "implementation_unchanged": not effective, "batch_state_dir": str(batch),
        "catalog_review_required": bool(effective), "init_complete": False,
        "generated_input_roots": known_generated,
        "scope_exclusion_proposals": inventory.get("generated_knowledge_exclusion_proposals", []),
        "historical_knowledge": "Imported S0 prose/approvals remain historical input; they are not recognized at S1 without new evidence and review.",
        "unknown": "Dynamic dependency impact is not proven by path invalidation."}
    if apply and effective:
        if inventory.get("generated_knowledge_exclusion_proposals"):
            raise InitError("new generated knowledge roots need an updated scope proposal before this source batch")
        receipt = acceptance_receipt(newer, source, target, accepted=True)
        RepoRegistry(batch).register(newer, receipt, source_path=source.path, knowledge_root=row["bindings"]["knowledge_root"])
        previous = bootstrap_workspace(state_dir, row)
        destination = bootstrap_workspace(batch, RepoRegistry(batch).get(spec.repo_id))
        # Import accepted knowledge and the feature policy, preserving bytes and stable IDs.
        from .portable_init import LocalKnowledgeRepo
        old_knowledge = LocalKnowledgeRepo(previous)
        files = old_knowledge.knowledge_files(old_knowledge.main_sha())
        for path, text in files.items():
            if path.startswith(spec.knowledge_slice + "/"):
                target_path = destination / "knowledge" / path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(text)
        policy = old_knowledge.show(old_knowledge.main_sha(), f"adapters/{spec.repo_id}/knowledge-coverage.yaml")
        if policy:
            (destination / "adapters" / spec.repo_id / "knowledge-coverage.yaml").write_text(policy)
        _git(destination, "add", ".")
        if _git(destination, "diff", "--cached", "--name-only"):
            _git(destination, "commit", "-qm", "Import immutable historical knowledge baseline")
        (batch / "incremental.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def command(args, state_dir):
    registry = RepoRegistry(state_dir)
    if args.command == "onboard":
        path = Path(args.source).expanduser()
        if path.exists():
            source = GitSource(path)
        else:
            cache = Path(state_dir) / "sources" / (hashlib.sha256(args.source.encode()).hexdigest()[:24] + ".git")
            source = GitSource(cache) if cache.exists() else GitSource.acquire(args.source, cache)
        proposal = propose_repository(source, repo_id=args.repo_id, pin=args.pin, storage=args.storage, forge_kind=args.forge)
        emit(proposal, args.out)
        return 0
    if args.command == "update":
        if args.dry_run and args.apply:
            raise InitError("--dry-run and --apply are mutually exclusive")
        emit(incremental_update(state_dir, args.repo, args.to, apply=args.apply), args.out)
        return 0
    if args.command == "mirror":
        from .knowledge_store import KnowledgeStore
        row = registry.resolve(args.repo)
        if not row:
            raise InitError("repository is not registered")
        spec = RepoSpec.from_dict(row["spec"])
        root = bootstrap_workspace(state_dir, row)
        result = KnowledgeStore(row["bindings"]["knowledge_root"], spec.repo_id, mode=spec.knowledge_storage).sync_mirror(
            args.out, source_pin=spec.source_pin, publication_head=_git(root, "rev-parse", "HEAD"))
        emit({"mirror": str(args.out), "snapshot": result["snapshot"], "acceptance": result.get("acceptance")})
        return 0
    if args.repo_command in ("receipt", "register"):
        proposal = _json(args.proposal)
        spec = RepoSpec.from_dict(proposal["spec"])
        if proposal.get("spec_sha256") != spec.sha256:
            raise InitError("proposal spec hash differs")
        source = GitSource(args.source)
        if args.repo_command == "receipt":
            emit(acceptance_receipt(spec, source, source.head(), accepted=True), args.out)
        else:
            registry.register(spec, _json(args.review_receipt), source_path=source.path, knowledge_root=args.knowledge_root)
            emit({"repo_id": spec.repo_id, "registered": True})
        return 0
    if args.repo_command == "list":
        emit(registry.public_snapshot())
        return 0
    row = registry.resolve(args.repo)
    if not row:
        raise InitError("repository is not registered")
    repo_id = row["spec"]["repo_id"]
    if args.repo_command == "review-stage":
        emit(stage_receipt(state_dir, repo_id, args.stage, reviewer=args.reviewer), args.out)
    elif args.repo_command == "accept-stage":
        record = accept_stage(state_dir, repo_id, args.stage, _json(args.review_receipt))
        emit({"status": record.status, "repo_id": repo_id, "head_sha": record.pr["local_acceptance"]["head_sha"]})
    elif args.repo_command == "publish":
        result = publish_portable(state_dir, repo_id, args.snapshot_out, partial=args.partial_foundation)
        emit({"snapshot_path": str(args.snapshot_out), "snapshot": result["snapshot"],
              "partial": args.partial_foundation, "activated": False, "init_complete": not args.partial_foundation})
    return 0
