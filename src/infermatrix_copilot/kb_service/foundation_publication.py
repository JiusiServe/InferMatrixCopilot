"""Explicit, publication-only partial foundation; generation proofs stay immutable."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .init_support import InitError, InitRecord, load_prepared
from .knowledge_coverage import audit_coverage, coverage_targets_met, load_policy


def _hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _file_hashes(files):
    return {path: hashlib.sha256(text.encode()).hexdigest() for path, text in sorted(files.items())}


def _payload(stage, record, files):
    targets = record.coverage.get("knowledge", {}).get("targets", {})
    scope = record.coverage.get("foundation_scope", {})
    tasks = record.coverage.get("foundation_jobs", {}).get("tasks", {})
    policy_text = stage.rt.knowledge.show(record.kb_base_sha, stage._coverage_policy_path()) or ""
    policy = load_policy(policy_text, stage.repo_dir)
    if (policy.semantic_depth_per_facet_gt is None
            or not coverage_targets_met(targets, "partial") or not scope.get("complete")
            or scope.get("features") != [f.id for f in policy.features]
            or scope.get("index_identity", {}).get("pin") != record.pin
            or scope.get("terminal_tasks") != sorted(tasks) or not tasks
            or record.coverage["foundation_jobs"].get("binding") != record.inputs_digest):
        raise InitError("partial foundation needs valid structural coverage and a complete terminal scope")
    head = stage.rt.knowledge.knowledge_files(record.kb_base_sha)
    head.update({p[len("knowledge/"):]: text for p, text in files.items() if p.startswith("knowledge/")})
    if getattr(stage.rt, "upstream", None):
        validate_initial_scope(stage, record)
    active = []
    for key, task in sorted(tasks.items()):
        for artifact in task.get("artifacts", []):
            if artifact["text"] in head.get(artifact["page"], ""):
                active.append({"task": key, "page": artifact["page"], "facet": artifact["facet"],
                               "artifact_sha256": _hash(artifact), "text_sha256": artifact["text_sha256"],
                               "generator_receipt_sha256": _hash(artifact["generator_receipt"]),
                               "judge_receipt_sha256": _hash(artifact["judge_receipt"])})
    return {"schema_version": 1, "foundation_mode": "partial", "init_complete": False,
            "repo": record.repo, "pin": record.pin, "kb_base_sha": record.kb_base_sha,
            "generation_inputs_digest": record.inputs_digest,
            "policy_path": stage._coverage_policy_path(), "policy_sha256": hashlib.sha256(policy_text.encode()).hexdigest(),
            "catalog_binding": record.discovery.get("catalog_binding"),
            "targets_sha256": _hash(targets), "foundation_targets_met": targets.get("met") is True,
            "structural_targets_met": True, "scope": scope,
            "tasks": {key: {"input_sha256": t["input_sha256"], "result_sha256": t["result_sha256"]}
                      for key, t in sorted(tasks.items())},
            "active_native_approvals": active, "files_sha256": _file_hashes(files),
            "unknown_foundation_facets": {fid: f["missing_facets"] for fid, f in targets["features"]["items"].items()
                                         if f["missing_facets"]}}


def validate_initial_scope(stage, record):
    """Fail before writers when the retained batch never processed an initial shard."""
    import tempfile
    from .init_knowledge import FACETS, _MARKER
    policy_text = stage.rt.knowledge.show(record.kb_base_sha, stage._coverage_policy_path()) or ""
    policy = load_policy(policy_text, stage.repo_dir)
    tasks = record.coverage.get("foundation_jobs", {}).get("tasks", {})
    base = stage.rt.knowledge.knowledge_files(record.kb_base_sha)
    with tempfile.TemporaryDirectory(prefix="kb-foundation-scope-") as scratch:
        source = stage.rt.upstream(record.repo, stage.lifecycle.full_name).export(record.pin, Path(scratch) / "tree")
        baseline = audit_coverage(base, source, policy, full_name=stage.lifecycle.full_name, pin=record.pin)
    for feature in policy.features:
        if not baseline["features"]["items"][feature.id]["covered"] and not any(
                t.get("owner") == "feature-" + feature.id and t.get("page") == feature.page for t in tasks.values()):
            raise InitError("partial foundation scope has a missing initial feature task")
    for owner in record.coverage.get("knowledge", {}).get("owners", {}):
        facets = {facet for text in base.values() for name, facet, pin, verdict in _MARKER.findall(text)
                  if name == owner and pin == record.pin and verdict in ("", "pass")}
        if not set(FACETS) <= facets and not any(t.get("owner") == owner for t in tasks.values()):
            raise InitError("partial foundation scope has a missing initial owner task")


def freeze_receipt(stage, files):
    """Freeze the local publication criterion after all source/native/tree checks."""
    from .init_knowledge_parallel import _validate_result
    from .models import ModelGateway
    if not isinstance(stage.rt.gateway, ModelGateway):
        raise InitError("partial foundation publication requires original native model receipts")
    for result in stage.record.coverage.get("foundation_jobs", {}).get("tasks", {}).values():
        _validate_result(stage, result)
    payload = _payload(stage, stage.record, files)
    raw = (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
    sha = hashlib.sha256(raw).hexdigest()
    folder = InitRecord.path(stage.rt.state_dir, stage.record.repo, "knowledge").parent / "foundation-publication"
    if folder.is_symlink():
        raise InitError("partial foundation receipt archive cannot be a symlink")
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (sha + ".json")
    if path.exists():
        if path.is_symlink() or path.read_bytes() != raw:
            raise InitError("partial foundation receipt archive differs")
    else:
        with path.open("xb") as stream:
            stream.write(raw)
    stage.record.coverage["foundation_publication"] = {
        "foundation_mode": "partial", "init_complete": False,
        "foundation_targets_met": payload["foundation_targets_met"],
        "structural_targets_met": True, "unknown_foundation_facets": payload["unknown_foundation_facets"],
        "receipt": {"path": str(path.resolve()), "sha256": sha, "bytes": len(raw)}}
    stage.record.notes.append("explicit partial foundation publication; six-facet targets and unknowns retained; initialization is incomplete")


def _read_receipt(record):
    try:
        ref = record.coverage["foundation_publication"]["receipt"]
        path = Path(ref["path"])
        raw = path.read_bytes()
        if (path.is_symlink() or path.name != ref["sha256"] + ".json"
                or hashlib.sha256(raw).hexdigest() != ref["sha256"] or len(raw) != ref["bytes"]):
            raise ValueError("archive hash or size differs")
        payload = json.loads(raw)
        summary = record.coverage["foundation_publication"]
        expected = {key: payload[key] for key in ("foundation_mode", "init_complete",
                    "foundation_targets_met", "structural_targets_met", "unknown_foundation_facets")}
        if {key: value for key, value in summary.items() if key != "receipt"} != expected:
            raise ValueError("publication summary differs from receipt")
        return payload, ref
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise InitError("partial foundation receipt unavailable or changed") from exc


def verify_prepared_receipt(stage, previous):
    partial = previous.coverage.get("foundation_publication", {}).get("foundation_mode") == "partial"
    if not partial and stage.foundation_mode == "strict":
        return  # Exact legacy prepared publications retain their original behavior.
    if not partial or stage.foundation_mode != "partial":
        raise InitError("prepared foundation publication mode differs; restore the original explicit mode")
    payload, ref = _read_receipt(previous)
    folder = InitRecord.path(stage.rt.state_dir, previous.repo, "knowledge").parent / "foundation-publication"
    if not Path(ref["path"]).resolve().is_relative_to(folder.resolve()):
        raise InitError("partial foundation receipt is outside its original archive")
    prepared = load_prepared(previous.pr["prepared"])
    if prepared["base_sha"] != previous.kb_base_sha or payload != _payload(stage, previous, prepared["files"]):
        raise InitError("prepared foundation publication differs from its frozen receipt")
    # Recompute structural status from actual saved bytes and the fixed source,
    # rather than trusting mutable counters in the checkpoint.
    import tempfile
    upstream = stage.rt.upstream(previous.repo, stage.lifecycle.full_name)
    with tempfile.TemporaryDirectory(prefix="kb-foundation-publication-") as scratch:
        tree = upstream.export(previous.pin, Path(scratch) / "tree")
        head = stage.rt.knowledge.knowledge_files(previous.kb_base_sha)
        head.update({p[len("knowledge/"):]: t for p, t in prepared["files"].items() if p.startswith("knowledge/")})
        policy_text = stage.rt.knowledge.show(previous.kb_base_sha, stage._coverage_policy_path())
        policy = load_policy(policy_text, stage.repo_dir)
        actual = audit_coverage(head, tree, policy, full_name=stage.lifecycle.full_name, pin=previous.pin)
        saved = dict(previous.coverage["knowledge"]["targets"])
        saved.pop("policy_sha256", None)
        if actual != saved:
            raise InitError("prepared foundation source coverage differs from its frozen receipt")


def foundation_handoff(record_path, *, knowledge, baseline, repo, pin, publisher=None):
    """Bind a new depth batch to the genuine merged partial foundation output."""
    try:
        path = Path(record_path)
        raw = path.read_bytes()
        record = InitRecord(**json.loads(raw))
        payload, ref = _read_receipt(record)
        prepared = load_prepared(record.pr["prepared"])
        if (record.stage != "knowledge" or record.status != "published" or record.dry_run or record.repo != repo or record.pin != pin
                or record.coverage["foundation_publication"]["foundation_mode"] != "partial"
                or payload["repo"] != repo or payload["pin"] != pin or payload["init_complete"] is not False
                or payload["generation_inputs_digest"] != record.inputs_digest
                or payload["kb_base_sha"] != record.kb_base_sha
                or payload["files_sha256"] != _file_hashes(prepared["files"])
                or payload["tasks"] != {k: {"input_sha256": t["input_sha256"], "result_sha256": t["result_sha256"]}
                                       for k, t in sorted(record.coverage["foundation_jobs"]["tasks"].items())}
                or not payload["scope"].get("complete")):
            raise ValueError("record/receipt binding differs")
        from types import SimpleNamespace
        import yaml
        manifest_path = str(Path(payload["policy_path"]).parent / "manifest.yaml")
        manifest = yaml.safe_load(knowledge.show(record.kb_base_sha, manifest_path))
        context = SimpleNamespace(rt=SimpleNamespace(knowledge=knowledge), repo_dir=manifest["knowledge"]["repo_subdir"],
                                  _coverage_policy_path=lambda: payload["policy_path"])
        if prepared["base_sha"] != record.kb_base_sha or payload != _payload(context, record, prepared["files"]):
            raise ValueError("raw record differs from the frozen receipt")
        for file, expected in payload["files_sha256"].items():
            actual = knowledge.show(baseline, file)
            if actual is None or hashlib.sha256(actual.encode()).hexdigest() != expected:
                raise ValueError("merged baseline differs from the emitted foundation files")
        policy_text = knowledge.show(baseline, payload["policy_path"])
        if not policy_text or hashlib.sha256(policy_text.encode()).hexdigest() != payload["policy_sha256"]:
            raise ValueError("merged foundation policy differs")
        if publisher is None:
            from .init_stages import _knowledge_repository
            from .init_support import InitPublisher
            publisher = InitPublisher(knowledge.path, _knowledge_repository())
        if publisher.pr_state(int(record.pr["number"])) != "MERGED":
            raise ValueError("foundation PR is not merged")
        return {"record_path": str(path.resolve()), "record_sha256": hashlib.sha256(raw).hexdigest(),
                "receipt_path": ref["path"], "receipt_sha256": ref["sha256"], "pin": pin,
                "policy_sha256": payload["policy_sha256"], "catalog_binding": payload["catalog_binding"],
                "files_sha256": payload["files_sha256"]}
    except (OSError, ValueError, KeyError, TypeError, InitError) as exc:
        raise InitError("partial foundation handoff is unavailable or differs from the merged baseline") from exc


def render_partial_body(record, lifecycle):
    """Bounded PR metadata; full native verdicts/history remain in the record."""
    from collections import Counter
    publication = record.coverage["foundation_publication"]
    targets = record.coverage["knowledge"]["targets"]
    core, features = targets["core"], targets["features"]
    unknown = publication["unknown_foundation_facets"]
    counts = Counter(facet for facets in unknown.values() for facet in facets)
    ref = publication["receipt"]
    lines = [f"`kb init knowledge`：`{lifecycle.repo}`（`{lifecycle.full_name}`）的基础知识部分发布。", "",
        "本次仅发布已获原生独立评审认可的内容，保留真实未知项。初始化尚未完成。", "",
        f"- 固定源码：`{record.pin}`", f"- 知识基线：`{record.kb_base_sha}`",
        f"- 原生成身份：`{record.inputs_digest}`（保留任务及修正次数）",
        f"- 六维基础知识完整功能：{features['covered']}/{features['total']}；基础目标达标：{targets['met']}。",
        f"- 生产文件结构覆盖：{core['covered']}/{core['total']}（{core['ratio']:.2%}），政策目标 {core['target']:.2%}。",
        f"- 尚未知的基础维度：{sum(counts.values())} 项，涉及 {len(unknown)} 个功能。",
        f"- 本次模型追加调用：{record.coverage['foundation_scope']['native_dispatches']}；实际订阅费用：未知。",
        "- `init_complete=false`；七维深度认可、检索验收、独立审查和 CI 仍为后续交付门槛。", "",
        "| 基础维度 | 未知项 |", "| --- | ---: |"]
    lines += [f"| {facet} | {counts.get(facet, 0)} |" for facet in
              ("architecture", "api", "configuration", "features", "tradeoffs", "validation")]
    lines += ["", f"- 冻结发布收据：`{ref['path']}`", f"- 收据 SHA-256：`{ref['sha256']}`",
        "- 完整输入、输出、工具轨迹、原生评审、失败原因和未决项保存在原始 Git 外阶段记录及收据中。",
        "- 固定 SHA 的引用、原生证明、知识结构和格式已校验；本 PR 合并仍需完整 CI 与独立审查。", ""]
    return "\n".join(lines)
