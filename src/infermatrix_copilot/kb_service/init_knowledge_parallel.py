"""Bounded foundation workers; only their coordinator changes stage state."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import posixpath
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..knowledge_service.pinned_claims import Evidence, check_evidence
from .init_support import InitError, InitRecord
from .models import ModelGateway, ModelUnavailable
from .evidence_bundle import merge_ranges


def _hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def parallelism(rt):
    if not rt.unlimited_subscription:
        return 1
    raw = rt.environ.get("KB_KNOWLEDGE_CONCURRENCY", "13")
    if str(raw) not in {str(n) for n in range(1, 14)}:
        raise InitError("KB_KNOWLEDGE_CONCURRENCY must be an integer from 1 through 13")
    return int(raw)


def start_interval(rt):
    raw = rt.environ.get("KB_KNOWLEDGE_START_INTERVAL_S", "5")
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise InitError("KB_KNOWLEDGE_START_INTERVAL_S must be finite and positive (at most 60)") from exc
    if not math.isfinite(value) or not 0 < value <= 60:
        raise InitError("KB_KNOWLEDGE_START_INTERVAL_S must be finite and positive (at most 60)")
    return value


def offered_ranges(items):
    ranges = {}
    for item in items:
        ranges.setdefault(item["path"], []).append((item.get("start", 1), item["end"]))
    return ranges


def local_privacy_reason(text):
    """Match the knowledge-tree IPv4 rule without echoing its matched value."""
    if any(not match.group().startswith("127.") for match in
           re.finditer(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])", text)):
        return ("local publication exclusion: literal IPv4; use <REMOTE_HOST> or describe "
                "wildcard binding in words while preserving the source contract. "
                "The original native approval is unchanged.")
    return ""


def related_test_sources(stage, paths, limit=20_000):
    """Shared-index localization only: direct imports, symbols and real assertions.

    Test text is evidence of the checks present, never of execution or absence.
    The caller reserves its actual bytes inside the existing source budget.
    """
    index = stage.source_index
    if index.identity["pin"] != stage.record.pin:
        raise InitError("foundation test index source pin differs")
    modules, stems, names = set(), set(), set()
    for path in paths:
        stem = path.rsplit(".", 1)[0]
        stems.add(stem)
        modules.add(stem.replace("/", "."))
        if "/src/" in stem:
            modules.add(stem.split("/src/", 1)[1].replace("/", "."))
        names.update(s["name"] for s in index.entries.get(path, {}).get("symbols", [])
                     if len(s["name"]) >= 5 and not s["name"].startswith("__"))
        if index.entries.get(path, {}).get("language") != "python":
            names.update(re.findall(r"\b(?:function|class|struct|fn|func|def|const)\s+([A-Za-z_]\w*)",
                                    "\n".join(index.entries.get(path, {}).get("lines", []))))
    if not names:
        return []
    symbols = re.compile(r"\b(?:" + "|".join(re.escape(n) for n in sorted(names)) + r")\b")
    checks = re.compile(r"\bassert\b|\braises\s*\(|\bexpect\s*\(|\bassert\w*\s*\(")
    out, used, candidates = [], 0, []
    basenames = {posixpath.basename(stem) for stem in stems}
    for path in sorted(index.tests):
        entry = index.entries[path]
        if entry.get("status") != "ready" or not entry.get("lines"):
            continue
        imports, matched_modules = [], set()
        for imported in entry.get("imports", []):
            text = imported["text"]
            tokens = re.findall(r"[A-Za-z_]\w*(?:\.\w+)*", text)
            targets = set(tokens)
            if tokens[:1] == ["from"] and "import" in tokens:
                targets.update(tokens[1] + "." + name for name in tokens[tokens.index("import") + 1:])
            quoted = re.findall(r"['\"]([^'\"]+)['\"]", text)
            resolved = {posixpath.normpath(posixpath.join(posixpath.dirname(path), spec)).rsplit(".", 1)[0]
                        if spec.startswith(".") else spec.rsplit(".", 1)[0] for spec in quoted}
            if targets & modules or resolved & stems:
                imports.append(imported["start"])
                matched_modules.update(targets & modules)
                matched_modules.update(stem.replace("/", ".") for stem in resolved & stems)
        if not imports:
            continue
        lines = entry["lines"]
        ranges = []
        for test in entry.get("symbols", []):
            start, end = test["start"], test["end"]
            body = "\n".join(lines[start - 1:end])
            if test["name"].startswith("test_") and symbols.search(body) and checks.search(body):
                ranges.append((start, end))
        if not ranges and entry.get("language") != "python":
            # Unknown/non-Python parsers expose clues, not runtime relations.
            hits = [n for n, line in enumerate(lines, 1) if checks.search(line)]
            if symbols.search("\n".join(lines)):
                ranges = [(max(1, n - 12), min(len(lines), n + 12)) for n in hits]
        if not ranges:
            continue
        spans = [(n, min(len(lines), n + 20)) for n in imports] + ranges
        test_name = posixpath.basename(path).rsplit(".", 1)[0]
        test_name = re.sub(r"^test_|(?:_test|\.test|\.spec)$", "", test_name)
        # Broad entry modules can match many unrelated tests. Rank before the
        # cap so an exact capability test cannot lose its budget to path order.
        exact = test_name in basenames
        related_name = any(len(name) >= 5 and (name in test_name or test_name in name)
                           for name in basenames if len(test_name) >= 5)
        specificity = max((len(module.split(".")) for module in matched_modules), default=0)
        candidates.append(((exact, related_name, specificity), path, entry, merge_ranges(spans)))
    for _, path, entry, merged in sorted(candidates, key=lambda row: (tuple(-int(n) for n in row[0]), row[1])):
        lines = entry["lines"]
        for start, end in merged:
            text = "\n".join(f"{n}: {lines[n - 1]}" for n in range(start, end + 1))
            size = len(text.encode())
            if used + size > limit:
                continue  # Never attest an incomplete line or silently fill gaps.
            out.append({"path": path, "start": start, "end": end, "text": text,
                        "total_lines": len(lines), "language": entry["language"],
                        "test_context": "direct import/symbol localization; tests have not been executed"})
            used += size
    return out


def range_is_offered(ranges, start, end):
    """Adjacent chunks are continuous evidence; a missing line stays a gap.

    Keep stored intervals unchanged so historical native input hashes replay.
    """
    if isinstance(ranges, int):
        ranges = [(1, ranges)]
    cursor = start
    for left, right in sorted(ranges):
        if left > cursor:
            return False
        if right >= cursor:
            cursor = right + 1
        if cursor > end:
            return True
    return False


def preferred_sources(stage, tree, feature_id, paths, limit):
    """New catalog entries use complete, verified discovery ranges before prefixes."""
    from .feature_discovery_index import language_for, validate_evidence
    report = stage._discovery_catalog()
    if report.get("full_artifact"):
        from pathlib import Path
        from .init_feature_discovery import verify_full_discovery_report
        record = InitRecord.load(stage.rt.state_dir, stage.record.repo, "feature-discovery")
        if record is None or record.pin != stage.record.pin or record.discovery.get("done") is not True:
            raise InitError("preferred discovery ranges need their genuine completed stage record")
        # A copied genuine prerequisite retains its original absolute archive paths.
        origin = Path(report["full_artifact"]["path"]).parents[3]
        if not hasattr(stage, "_foundation_full_discovery"):
            stage._foundation_full_discovery = verify_full_discovery_report(origin, report, record.discovery)
        report = stage._foundation_full_discovery
    accepted = {r["id"]: r for r in report.get("candidates", []) if r.get("status") == "accepted"}
    primary = accepted.get(feature_id)
    if not primary or primary.get("relation") != "new":
        return stage._sources(tree, paths, limit)
    def canonical(row):
        target, visited = row.get("related_id"), set()
        while target and target not in visited:
            if target == feature_id:
                return target
            visited.add(target)
            target = accepted.get(target, {}).get("related_id")
        return None
    relations = {"implementation_supplement", "alias", "subcapability", "shared_component"}
    rows = [primary] + [row for key, row in sorted(accepted.items())
                        if row.get("relation") in relations and canonical(row) == feature_id]
    out, used, seen = [], 0, set()
    for row in rows:
        for ref in row.get("evidence", []):
            path, start, end = ref["path"], ref["start"], ref["end"]
            if path not in paths or (path, start, end) in seen:
                continue
            if not validate_evidence(stage.source_index, ref):
                raise InitError(f"frozen discovery evidence no longer matches {path}:L{start}-L{end}")
            lines = stage.source_index.entries[path]["lines"]
            text = "\n".join(f"{n}: {lines[n - 1]}" for n in range(start, end + 1))
            if used + len(text.encode()) > limit:
                stage.record.unfinished.append(f"feature {feature_id}: discovery range omitted by byte cap: {path}:L{start}-L{end}")
                continue  # never attest a partially shown range
            out.append({"path": path, "start": start, "end": end, "text": text,
                        "total_lines": len(lines), "language": language_for(path)})
            used += len(text.encode())
            seen.add((path, start, end))
    # Fill with other files; do not pretend gaps in an excerpted file were read.
    out.extend(stage._sources(tree, [p for p in paths if p not in {r["path"] for r in out}], max(0, limit - used)))
    return out


class _CaptureGateway:
    def __init__(self, gateway):
        self.gateway = copy.copy(gateway) if isinstance(gateway, ModelGateway) else gateway
        if isinstance(self.gateway, ModelGateway):
            self.gateway._subscription_transports = {}  # each authenticated transport belongs to one worker
        self.last = {}

    def subscription_billing(self, role):
        return self.gateway.subscription_billing(role)

    def call_json(self, role, **kwargs):
        reply = self.gateway.call_json(role, **kwargs)
        self.last[role.name] = {"native_trace_id": reply.trace_id,
                                "native_reply_sha256": reply.reply_sha256,
                                "prompt_sha256": hashlib.sha256(kwargs["prompt"].encode()).hexdigest()}
        return reply


def _worker(stage, job):
    from .init_knowledge_inputs import foundation_evidence
    from .init_stages import _one_line
    worker = copy.copy(stage)
    worker.head = dict(stage.head)
    worker.rt = copy.copy(stage.rt)
    worker.rt.gateway = _CaptureGateway(stage.rt.gateway)
    worker.record = InitRecord(stage=stage.STAGE, repo=stage.record.repo, pin=stage.record.pin)
    worker._foundation_payload = job["payload"]
    artifacts = []
    error = ""
    try:
        if job["payload"].get("foundation_prompt_version") in (4, 5):
            foundation_evidence(worker, job["payload"])
        for data, section, result in worker._sections(job["owner"], job["page"], job["payload"],
                                                     job["offered"], job["requested"]):
            if result:
                key, text, entries, label = result
                receipt = worker.rt.gateway.last.get("judge", {})
                if isinstance(stage.rt.gateway, ModelGateway) and not receipt.get("native_trace_id"):
                    worker.record.unfinished.append(f"{key}: native judge receipt missing; retained in traces")
                    continue
                artifacts.append({"key": key, "owner": job["owner"].owner, "page": job["page"],
                                  "title": _one_line(data.get("title")) or f"{job['owner'].owner} knowledge",
                                  "facet": section["facet"], "text": text,
                                  "section": copy.deepcopy(section), "generator_title": data.get("title"),
                                  "approved_today": worker.today,
                                  "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                                  "evidence": [e.to_dict() for e in entries], "verdict": worker.record.verdicts[key],
                                  "generator_receipt": worker.rt.gateway.last.get("generator", {}),
                                  "judge_receipt": receipt})
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    result = {"input_sha256": _hash({"payload": job["payload"], "offered": job["offered"]}),
              "payload": job["payload"], "offered": job["offered"], "page": job["page"],
              "owner": job["owner"].owner, "requested": job["requested"],
              "artifacts": artifacts, "error": error, "verdicts": worker.record.verdicts,
              "dropped": worker.record.dropped, "unfinished": worker.record.unfinished}
    result["result_sha256"] = _hash(result)
    return result


def _validate_result(stage, result):
    if result.get("result_sha256") != _hash({k: v for k, v in result.items() if k != "result_sha256"}):
        raise InitError("foundation checkpoint artifact hash mismatch")
    if (result["payload"].get("pin") != stage.record.pin
            or result["payload"].get("repository") != stage.lifecycle.full_name):
        raise InitError("foundation generator repository or source pin differs")
    if result["input_sha256"] != _hash({"payload": result["payload"], "offered": result["offered"]}):
        raise InitError("foundation job input hash mismatch")
    if (result["requested"] != result["payload"]["facets"]
            or _hash(result["offered"]) != _hash(offered_ranges(result["payload"]["files"] + result["payload"]["docs"]))):
        raise InitError("foundation shown input or requested facets differ from generator payload")
    from .init_knowledge_inputs import foundation_evidence, knowledge_system
    knowledge_system(result["payload"])
    if result["payload"].get("foundation_prompt_version") in (4, 5):
        if not stage.rt.unlimited_subscription:
            raise InitError("foundation full packet requires unlimited subscription")
        foundation_evidence(stage, result["payload"])
    for artifact in result["artifacts"]:
        facet, owner = artifact["facet"], result["owner"]
        if (artifact["owner"] != owner or result["payload"]["owner"] != owner
                or artifact["page"] != result["page"] or facet not in result["requested"]
                or artifact["key"] != f"knowledge:{owner}:{facet}"
                or artifact["section"].get("facet") != facet):
            raise InitError("foundation artifact owner/page/facet binding mismatch")
        if owner.startswith("feature-"):
            feature = next((f for f in stage.coverage_policy.features if "feature-" + f.id == owner), None)
            if (feature is None or feature.page != artifact["page"]
                    or result["payload"].get("feature") != feature.title):
                raise InitError("foundation feature differs from frozen catalog")
        elif not any(o.owner == owner and stage._page_for(o) == artifact["page"] for o in stage.owners):
            raise InitError("foundation owner differs from frozen owner routes")
        if artifact["text_sha256"] != hashlib.sha256(artifact["text"].encode()).hexdigest():
            raise InitError("foundation approved text hash mismatch")
        if artifact["verdict"].get("verdict") != "pass":
            raise InitError("foundation checkpoint contains unapproved prose")
        entries = [Evidence.from_dict(e) for e in artifact["evidence"]]
        if stage._render_section(artifact["section"], entries) != artifact["text"]:
            raise InitError("foundation generated section reconstruction mismatch")
        for entry in artifact["section"]["evidence"]:
            if not range_is_offered(result["offered"].get(entry["path"], []), entry["start"], entry["end"]):
                raise InitError("foundation cached citation outside shown interval")
        if [(e.path, e.start, e.end) for e in entries] != [
                (e["path"], e["start"], e["end"]) for e in artifact["section"]["evidence"]]:
            raise InitError("foundation generated evidence binding mismatch")
        if check_evidence(entries, stage.observer):
            raise InitError("foundation checkpoint pinned evidence mismatch")
        if isinstance(stage.rt.gateway, ModelGateway):
            _validate_native(stage, artifact, result)


def _validate_native(stage, artifact, result):
    from ..trace_store import TraceStore
    from .judge_tuning import JUDGE_SYSTEM
    from .init_knowledge import knowledge_prompt
    from .init_knowledge_inputs import foundation_evidence, knowledge_system
    from .init_stages import _Stage, _one_line, _page_frontmatter
    from .models import parse_json_object
    store = TraceStore(stage.rt.state_dir / "init" / "traces")
    receipt = artifact["judge_receipt"]
    from .init_feature_discovery import _FeatureDiscovery
    for name, role in (("generator", stage.rt.generator), ("judge", stage.rt.judge)):
        proof = artifact[name + "_receipt"]
        try:
            _FeatureDiscovery._verify_archived_receipt(stage, {
                "trace_id": proof["native_trace_id"], "reply_sha256": proof["native_reply_sha256"],
                "requested": role.label()}, role)
        except ModelUnavailable as exc:
            raise InitError(f"foundation native approval unavailable: {exc}") from exc
    try:
        record = store.get(receipt["native_trace_id"])
        prompt = store.blob(record["inputs"]["prompt"])
        reply = parse_json_object(store.blob(record["outputs"]["reply"]))
        payload = json.loads(prompt.split("\n", 1)[1].rsplit("</untrusted_data>", 1)[0])
        generator_receipt = artifact["generator_receipt"]
        generator = store.get(generator_receipt["native_trace_id"])
        generator_prompt = store.blob(generator["inputs"]["prompt"])
        generated = parse_json_object(store.blob(generator["outputs"]["reply"]))
        gen_payload = json.loads(generator_prompt.split("\n", 1)[1].rsplit("</untrusted_data>", 1)[0])
        expected_gen_payload = json.loads(knowledge_prompt(result["payload"]).split("\n", 1)[1].rsplit("</untrusted_data>", 1)[0])
        generator_valid = (gen_payload == expected_gen_payload
                           and artifact["section"] in generated["sections"]
                           and artifact["generator_title"] == generated.get("title")
                           and artifact["title"] == (_one_line(generated.get("title")) or f"{artifact['owner']} knowledge")
                           and store.blob(generator["inputs"]["system"]) == knowledge_system(result["payload"])
                           and not generator.get("error") and generator["model"]["role"] == "generator"
                           and generator["model"]["provider"] == stage.rt.generator.provider
                           and generator["model"]["model"] == stage.rt.generator.model
                           and generator["outputs"]["reply"] == "sha256:" + generator_receipt["native_reply_sha256"]
                           and hashlib.sha256(generator_prompt.encode()).hexdigest() == generator_receipt["prompt_sha256"])
        valid = (generator_valid and not record.get("error") and record["model"]["role"] == "judge"
                 and record["model"]["provider"] == stage.rt.judge.provider
                 and record["model"]["model"] == stage.rt.judge.model
                 and store.blob(record["inputs"]["system"]) == JUDGE_SYSTEM
                 and record["outputs"]["reply"] == "sha256:" + receipt["native_reply_sha256"]
                 and hashlib.sha256(prompt.encode()).hexdigest() == receipt["prompt_sha256"]
                 and payload["change"]["page"] == artifact["page"]
                 and payload["change"]["after"] == _page_frontmatter(artifact["title"], kind="architecture",
                       today=artifact["approved_today"], tags=stage.tags) + "\n" + artifact["text"]
                 and payload["evidence"] == (foundation_evidence(stage, result["payload"])
                     if result["payload"].get("foundation_prompt_version") in (4, 5) else
                     _Stage._judge_evidence(stage, [Evidence.from_dict(e) for e in artifact["evidence"]]))
                 and all(reply["dimensions"].get(d) == "yes" for d in
                         ("faithful", "does_not_weaken", "non_contradictory")))
    except (KeyError, ValueError, OSError, TypeError) as exc:
        raise InitError(f"foundation native approval unavailable: {exc}") from exc
    if not valid:
        raise InitError("foundation native approval binding mismatch")


def _apply(stage, result):
    from .init_coverage import Owner
    _validate_result(stage, result)
    stage.record.verdicts.update(result["verdicts"])
    stage.record.dropped.extend(result["dropped"])
    stage.record.unfinished.extend(result["unfinished"])
    accepted = []
    for artifact in result["artifacts"]:
        reason = local_privacy_reason(artifact["text"]) if stage.rt.unlimited_subscription else ""
        if reason:
            stage.record.dropped.append({"rule_id": artifact["key"], "page": artifact["page"],
                                         "why": reason, "local_publication_exclusion": True})
            stage.record.unfinished.append(f"{artifact['key']}: {reason}")
            continue  # Original body, result hash and native pass remain immutable.
        item = stage._append_approved(Owner(artifact["owner"], artifact["page"], ()),
            artifact["page"], artifact["title"], artifact["facet"], artifact["text"],
            [Evidence.from_dict(e) for e in artifact["evidence"]])
        if item:
            accepted.append(item)
    return accepted


def validate_checkpoint(stage, previous, digest):
    """Read-only replay before cache reuse or any prepared publication write."""
    import tempfile
    from pathlib import Path
    from .feature_discovery_index import build_discovery_index, discovery_scope
    from .init_knowledge_inputs import source_owners

    saved = previous.coverage.get("foundation_jobs", {})
    if (previous.stage != "knowledge" or previous.repo != stage.lifecycle.repo
            or previous.pin != stage._knowledge_run_pin
            or previous.kb_base_sha != stage._base_sha or previous.inputs_digest != digest
            or (saved and saved.get("binding") != digest)):
        raise InitError("foundation checkpoint frozen input identity differs")
    if not saved.get("tasks"):
        return  # A genuine empty stage may reuse an already-covered merged KB.
    context = copy.copy(stage)
    context.record = copy.deepcopy(previous)
    context.base = {**stage.rt.knowledge.knowledge_files(previous.kb_base_sha),
                    **{p[len("knowledge/"):]: text for p, text in stage.overlay.items()
                       if p.startswith("knowledge/")}}
    context.tags = [stage.lifecycle.repo]
    context.today = stage.rt.today()
    problems = context._precheck()
    if problems:
        raise InitError("foundation checkpoint policy invalid: " + "; ".join(problems))
    upstream = stage.rt.upstream(stage.lifecycle.repo, stage.lifecycle.full_name)
    context.observer = upstream.observer(previous.pin, pull=stage.rt.pull)
    # Export and index live only in a temporary directory. Do not repair or
    # rewrite stage records, previews, pacing journals or shared index caches.
    with tempfile.TemporaryDirectory(prefix="kb-foundation-proof-") as scratch:
        tree = upstream.export(previous.pin, Path(scratch) / "tree")
        context._inputs(tree)
        if context.route_problem:
            raise InitError(context.route_problem)
        policy = getattr(context, "coverage_policy", None)
        docs = list(stage.lifecycle.init.doc_globs) + list(policy.catalog_sources if policy else ())
        index = build_discovery_index(tree, pin=previous.pin,
                    scope=discovery_scope(stage.lifecycle.init, policy), doc_globs=sorted(set(docs)))
        context.owners = list(source_owners(list(index.production), context.owners, policy).values())
        for result in saved["tasks"].values():
            _validate_result(context, result)


def restore_jobs(stage):
    saved = stage.record.coverage.get("foundation_jobs", {})
    if saved and saved.get("binding") != stage.record.inputs_digest:
        raise InitError("foundation checkpoint input identity mismatch")
    for result in sorted(saved.get("tasks", {}).values(), key=lambda item: item["sequence"]):
        _apply(stage, result)
    # This run has already replayed these immutable results, including native
    # approvals. Feedback preparation need not replay their archives twice.
    stage._foundation_validated_results = {r["result_sha256"] for r in saved.get("tasks", {}).values()}


def _validate_fresh(stage, result):
    """Keep each valid facet when another native proof cannot be used."""
    empty = {**result, "artifacts": []}
    empty["result_sha256"] = _hash({k: v for k, v in empty.items() if k != "result_sha256"})
    _validate_result(stage, empty)
    accepted = []
    for artifact in result["artifacts"]:
        isolated = {**result, "artifacts": [artifact]}
        isolated["result_sha256"] = _hash({k: v for k, v in isolated.items() if k != "result_sha256"})
        try:
            _validate_result(stage, isolated)
            accepted.append(artifact)
        except InitError as exc:
            result["unfinished"].append(f"{artifact['key']}: native approval unknown: {exc}")
            result["dropped"].append({"rule_id": artifact["key"], "page": artifact["page"], "why": str(exc)})
            result["verdicts"][artifact["key"]] = {**artifact["verdict"], "verdict": "unjudged",
                                                  "reasons": {"native_binding": str(exc)}}
    result["artifacts"] = accepted
    result["result_sha256"] = _hash({k: v for k, v in result.items() if k != "result_sha256"})


def _with_review_feedback(stage, jobs, saved):
    """Same-version native resumes get advisory, per-facet correction history."""
    for original in jobs:
        if (not stage.rt.unlimited_subscription
                or original["payload"].get("foundation_prompt_version") not in (4, 5)):
            yield original
            continue
        if saved.get("tasks") and saved.get("binding") != stage.record.inputs_digest:
            raise InitError("foundation feedback needs the same frozen batch identity")
        history = {}
        for prior in saved.get("tasks", {}).values():
            if (prior.get("owner") != original["owner"].owner or prior.get("page") != original["page"]
                    or prior.get("payload", {}).get("owner") != original["owner"].owner
                    or prior.get("payload", {}).get("foundation_prompt_version") != original["payload"]["foundation_prompt_version"]
                    or not set(prior.get("requested", [])) & set(original["requested"])):
                continue
            if prior.get("result_sha256") != _hash({k: v for k, v in prior.items() if k != "result_sha256"}):
                raise InitError("foundation feedback prior result hash mismatch")
            if prior.get("result_sha256") not in getattr(stage, "_foundation_validated_results", set()):
                _validate_result(stage, prior)
            history.setdefault(prior["input_sha256"], prior)
        feedback, requested = {}, []
        for facet in original["requested"]:
            attempts = sorted((p for p in history.values() if facet in p["requested"]),
                              key=lambda p: p["sequence"])
            if len(attempts) >= 4:  # Initial extraction plus at most three corrections.
                stage.record.unfinished.append(f"{original['owner'].owner}/{facet}: three review corrections exhausted; remains unknown")
                continue
            requested.append(facet)
            if attempts:
                latest = attempts[-1]
                key = f"knowledge:{original['owner'].owner}:{facet}"
                verdict = latest.get("verdicts", {}).get(key, {})
                if (verdict.get("page") != original["page"] or verdict.get("facet") != facet
                        or verdict.get("verdict") not in {"fail", "unsure", "unjudged"}):
                    verdict = {}  # Unavailable advisory review, never another facet's reasons or an approval.
                feedback[facet] = {"correction_round": len(attempts),
                    "prior_attempts": [{"input_sha256": p["input_sha256"], "result_sha256": p["result_sha256"]}
                                       for p in attempts],
                    "last_verdict": verdict.get("verdict", "unknown"),
                    "last_review_reasons": copy.deepcopy(verdict.get("reasons", {})),
                    "last_error": latest.get("error", ""),
                    "last_dropped_reasons": [p["why"] for p in latest.get("dropped", [])
                                             if p.get("rule_id") == key and p.get("page") == original["page"]]}
                for artifact in latest.get("artifacts", []):
                    if (artifact.get("key") == key and artifact.get("owner") == original["owner"].owner
                            and artifact.get("page") == original["page"] and artifact.get("facet") == facet):
                        reason = local_privacy_reason(artifact["text"])
                        if reason:
                            feedback[facet]["last_local_publication_reasons"] = [reason]
                            feedback[facet]["prior_artifact_text_sha256"] = artifact["text_sha256"]
        if not requested:
            continue
        if not feedback and requested == original["requested"]:
            yield original
            continue
        job = {**original, "payload": copy.deepcopy(original["payload"]), "requested": requested}
        job["payload"]["facets"] = requested
        if feedback:
            job["payload"]["prior_review_feedback"] = {"advisory_only": True,
                "scope": "Previous rejection/error data for these requested facets; not source evidence or approval.",
                "facets": feedback}
        yield job


def run_jobs(stage, jobs):
    """One worker's generator and judges are serial, so the pool is the shared cap."""
    workers = parallelism(stage.rt)
    if isinstance(stage.rt.gateway, ModelGateway):
        from .depth_pacing import SharedZcodePacer
        pacer = stage.rt.gateway._zcode_pacer
        if pacer is None:
            pacer = SharedZcodePacer(stage.rt.state_dir / "init" / stage.record.repo / "foundation-zcode-pacing.json",
                                    start_interval=start_interval(stage.rt), stop_file=stage.rt.state_dir / "STOP")
            pacer.prepare()
            stage.rt.gateway.configure_zcode_pacing(pacer)
    saved = stage.record.coverage.setdefault("foundation_jobs", {"binding": stage.record.inputs_digest, "tasks": {}})
    jobs = list(_with_review_feedback(stage, jobs, saved))
    if not jobs:
        return
    completed = {}
    sequence = max((r["sequence"] for r in saved["tasks"].values()), default=-1) + 1
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="kb-foundation") as pool:
        futures = {pool.submit(_worker, stage, job): n for n, job in enumerate(jobs)}
        for future in as_completed(futures):
            n = futures[future]
            result = future.result()
            result["sequence"] = sequence + n
            result["result_sha256"] = _hash({k: v for k, v in result.items() if k != "result_sha256"})
            try:
                _validate_fresh(stage, result)
            except InitError as exc:
                result["error"] = str(exc)
                result["artifacts"] = []
                result["result_sha256"] = _hash({k: v for k, v in result.items() if k != "result_sha256"})
            completed[n] = result
            key = jobs[n]["owner"].owner + ":" + result["input_sha256"]
            stage.budget.checkpoint_now(lambda: saved["tasks"].__setitem__(key, result))
    # Completion order never affects pages, navigation or approval assembly.
    for n, job in enumerate(jobs):
        result = completed[n]
        if result["error"]:
            stage.record.unfinished.append(f"{job['owner'].owner}: unusable foundation draft: {result['error']}")
        yield job, _apply(stage, result)
