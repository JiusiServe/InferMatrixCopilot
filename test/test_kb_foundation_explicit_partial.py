"""Explicit partial foundation publishes genuine retained approvals, never retries."""
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from infermatrix_copilot.kb_service.init_stages import run_stage
from infermatrix_copilot.kb_service.init_support import InitError, InitRecord, load_prepared
from infermatrix_copilot.kb_service.foundation_publication import foundation_handoff
from infermatrix_copilot.kb_service.knowledge_coverage import coverage_targets_met, policy_path
from infermatrix_copilot.kb_service.models import ModelGateway, ModelRole
from infermatrix_copilot.kb_service.runtime import trace_recorder
from infermatrix_copilot.llm import Block, Reply
from infermatrix_copilot.trace_store import TraceStore
from test_kb_init_knowledge import KnowledgeGateway, _chain
from test_kb_init_modules import _modules_lifecycle
from test_kb_init_skeleton import FakeGh, _commit, _runtime, _tree, world  # noqa: F401


def _retained_native_partial(world, *, fail_create=0, semantic=True, second_feature=False):
    """Produce a real scripted native checkpoint through the default strict CLI."""
    _chain(world, KnowledgeGateway())
    seed = _runtime(world)
    baseline = {**_tree(InitRecord.load(seed.state_dir, "toy", "skeleton")),
                **_tree(InitRecord.load(seed.state_dir, "toy", "modules"))}
    baseline["adapters/toy/manifest.yaml"] = yaml.safe_dump({
        "name": "toy", "knowledge": {"repo_subdir": "repos/toy"}})
    feature_page = "repos/toy/components/tooling/feature-demo.md"
    policy = {
        "schema_version": 1, "required": True,
        "core": {"roots": ["pkg/", "tools/"], "target": 0.85},
        "features": [{"id": "demo", "title": "Demo", "owner": "tooling",
                      "source_globs": ["tools/lint/y.py"], "entry_points": ["tools/lint/y.py"],
                      "docs": ["docs/guide.md"], "page": feature_page}],
    }
    if semantic:
        policy["semantic_depth"] = {"per_facet_gt": 0.90}
    if second_feature:
        policy["features"].append({"id": "other", "title": "Engine entry", "owner": "core",
                                   "source_globs": ["pkg/core.py"], "entry_points": ["pkg/core.py"],
                                   "docs": ["docs/guide.md"],
                                   "page": "repos/toy/components/core/feature-other.md"})
    baseline[policy_path("toy")] = yaml.safe_dump(policy)
    _commit(world["origin"], baseline, "merge real prerequisites and feature policy")
    state = world["tmp"] / "explicit-partial"
    traces, calls = TraceStore(state / "init" / "traces"), []

    class NativeTransport:
        subscription_billing = True
        supports_native_events = True

        def complete(self, *, system, messages, model, effort, role, **kwargs):
            payload = json.loads(messages[0]["content"].split("\n", 1)[1].rsplit("</untrusted_data>", 1)[0])
            calls.append((role, copy.deepcopy(payload)))
            if role == "generator":
                source = payload["files"][0]
                evidence = [{"path": source["path"], "start": source.get("start", 1), "end": source["end"]}]
                if payload["docs"]:
                    doc = payload["docs"][0]
                    evidence.append({"path": doc["path"], "start": doc.get("start", 1), "end": doc["end"]})
                data = {"title": payload["owner"] + " knowledge", "sections": [
                    {"facet": facet, "title": facet.capitalize(), "interpretation": "inference",
                     "body": "The small interface keeps responsibility explicit. Consumers supply required state "
                             "and preserve the documented integration boundary when using the shown implementation.",
                     "evidence": evidence} for facet in payload["facets"]]}
            else:
                reject = (payload["change"]["page"] == feature_page
                          and "**Validation**" in payload["change"]["after"])
                data = {"dimensions": {"faithful": "no" if reject else "yes",
                                       "does_not_weaken": "yes", "non_contradictory": "yes"},
                        "reasons": {"faithful": "no supported validation claim in this fixture" if reject else "supported"}}
            return Reply(blocks=[Block(type="text", text=json.dumps(data))], model=model)

    gateway = ModelGateway(None, transport_factory=lambda _: NativeTransport(), recorder=trace_recorder(traces))
    gh = FakeGh(fail_create=fail_create)
    rt = _runtime(world, gateway, state_dir=state, gh_run=gh,
                  generator=ModelRole("generator", "zcode", "GLM-5.3"),
                  environ={"ALLOW_PUSH": "1", "ALLOW_POST": "1",
                           "KB_INIT_GIT_AUTHOR": "Tester <tester@example.com>",
                           "KB_KNOWLEDGE_CONCURRENCY": "2", "KB_KNOWLEDGE_START_INTERVAL_S": "0.001"})
    record = run_stage(rt, _modules_lifecycle(), "knowledge", dry_run=False,
                       from_existing=True, unlimited_subscription=True)
    assert record.status == "blocked" and record.pr == {}
    assert record.coverage["knowledge"]["targets"]["core"]["ratio"] >= 0.85
    assert record.coverage["knowledge"]["targets"]["features"]["covered"] == int(second_feature)
    assert record.coverage["knowledge"]["targets"]["features"]["items"]["demo"]["missing_facets"] == ["validation"]
    assert not record.coverage["knowledge"]["targets"]["met"]
    assert sum(len(t["artifacts"]) for t in record.coverage["foundation_jobs"]["tasks"].values()) == 17 + 6 * int(second_feature)
    assert not gh.pushed and not gh.created
    # Bind comparisons to the actual JSON checkpoint, including normalized
    # offered-range lists, rather than transient generator tuple values.
    return rt, InitRecord.load(state, "toy", "knowledge"), calls, traces, feature_page


def _run_partial(rt):
    return run_stage(rt, _modules_lifecycle(), "knowledge", dry_run=False,
                     from_existing=True, unlimited_subscription=True, foundation_mode="partial")


def test_partial_publication_reuses_exact_native_jobs_without_fourth_extraction(world):
    rt, original, calls, traces, page = _retained_native_partial(world)
    saved = copy.deepcopy(original.coverage["foundation_jobs"])
    before_calls = len(calls)
    record = _run_partial(rt)
    assert record.status == "published", record.problems
    assert record.inputs_digest == original.inputs_digest
    assert record.coverage["foundation_jobs"] == saved
    assert len(calls) == before_calls
    assert not record.coverage["knowledge"]["targets"]["met"]
    assert record.coverage["knowledge"]["targets"]["features"]["covered"] == 0
    assert record.coverage["knowledge"]["targets"]["features"]["items"]["demo"]["missing_facets"] == ["validation"]
    assert len(rt.gh_run.pushed) == 1 and len(rt.gh_run.created) == 1
    prepared = load_prepared(record.pr["prepared"])
    assert "facet=validation" not in prepared["files"]["knowledge/" + page]
    assert prepared["base_sha"] == original.kb_base_sha
    publication = record.coverage["foundation_publication"]
    assert publication["foundation_mode"] == "partial" and publication["init_complete"] is False
    assert publication["foundation_targets_met"] is False and publication["structural_targets_met"] is True
    assert publication["unknown_foundation_facets"] == {"demo": ["validation"]}
    ref = publication["receipt"]
    raw = Path(ref["path"]).read_bytes()
    assert Path(ref["path"]).is_absolute() and len(raw) == ref["bytes"]
    assert hashlib.sha256(raw).hexdigest() == ref["sha256"]
    receipt = json.loads(raw)
    assert receipt["generation_inputs_digest"] == original.inputs_digest
    assert receipt["tasks"] == {k: {"input_sha256": t["input_sha256"], "result_sha256": t["result_sha256"]}
                                for k, t in saved["tasks"].items()}
    assert receipt["files_sha256"] == {p: hashlib.sha256(t.encode()).hexdigest() for p, t in prepared["files"].items()}
    assert len(receipt["active_native_approvals"]) == 17


@pytest.mark.parametrize("role", ["generator", "judge"])
def test_partial_missing_native_attempt_cannot_publish_or_dispatch(world, role):
    rt, original, calls, traces, _ = _retained_native_partial(world)
    artifact = next(iter(original.coverage["foundation_jobs"]["tasks"].values()))["artifacts"][0]
    native = traces.get(artifact[role + "_receipt"]["native_trace_id"])
    attempt = traces.root / "attempts" / native["result"]["native_attempt_id"] / "attempt.json"
    attempt.unlink()
    path = InitRecord.path(rt.state_dir, "toy", "knowledge")
    before, before_calls = path.read_bytes(), len(calls)
    with pytest.raises(InitError, match="foundation"):
        _run_partial(rt)
    assert path.read_bytes() == before
    assert len(calls) == before_calls and not rt.gh_run.pushed and not rt.gh_run.created


def test_partial_prepared_resume_cannot_switch_to_strict_and_is_native_bound(world):
    rt, original, calls, traces, _ = _retained_native_partial(world, fail_create=1)
    first = _run_partial(rt)
    assert first.status == "blocked" and first.pr["prepared"]
    path = InitRecord.path(rt.state_dir, "toy", "knowledge")
    before, before_calls, before_pushes = path.read_bytes(), len(calls), len(rt.gh_run.pushed)
    with pytest.raises(InitError, match="foundation|publication|mode"):
        run_stage(rt, _modules_lifecycle(), "knowledge", dry_run=False,
                  from_existing=True, unlimited_subscription=True)
    assert path.read_bytes() == before and len(calls) == before_calls
    artifact = next(iter(first.coverage["foundation_jobs"]["tasks"].values()))["artifacts"][0]
    native = traces.get(artifact["judge_receipt"]["native_trace_id"])
    attempt = traces.root / "attempts" / native["result"]["native_attempt_id"] / "attempt.json"
    raw_attempt = attempt.read_bytes()
    attempt.unlink()
    with pytest.raises(InitError, match="foundation"):
        _run_partial(rt)
    assert path.read_bytes() == before and len(calls) == before_calls
    assert len(rt.gh_run.pushed) == before_pushes
    attempt.write_bytes(raw_attempt)
    resumed = _run_partial(rt)
    assert resumed.status == "published", resumed.problems
    assert len(calls) == before_calls
    assert resumed.coverage["foundation_jobs"] == original.coverage["foundation_jobs"]


@pytest.mark.parametrize("damage", ["receipt", "output", "counters"])
def test_partial_prepared_receipt_output_and_rehashed_counters_fail_closed(world, damage):
    rt, original, calls, traces, page = _retained_native_partial(world, fail_create=1)
    record = _run_partial(rt)
    assert record.status == "blocked" and record.pr["prepared"]
    ref = record.coverage["foundation_publication"]["receipt"]
    receipt_path = Path(ref["path"])
    if damage == "receipt":
        receipt_path.write_bytes(receipt_path.read_bytes() + b" ")
    elif damage == "output":
        path = Path(record.pr["prepared"])
        prepared = json.loads(path.read_text())
        prepared["files"]["knowledge/" + page] += "\nUnapproved altered explanation.\n"
        path.write_text(json.dumps(prepared))
    else:
        # Even self-consistent local counters/receipt hashes cannot replace an
        # audit against the actual frozen source and emitted page bytes.
        targets = record.coverage["knowledge"]["targets"]
        targets["core"]["covered"] += 1
        receipt = json.loads(receipt_path.read_bytes())
        receipt["targets_sha256"] = hashlib.sha256(json.dumps(
            targets, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        raw = (json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
        changed_sha = hashlib.sha256(raw).hexdigest()
        forged_archive = receipt_path.parent / (changed_sha + ".json")
        forged_archive.write_bytes(raw)
        ref.update(path=str(forged_archive), sha256=changed_sha, bytes=len(raw))
        record.save(rt.state_dir)
    path = InitRecord.path(rt.state_dir, "toy", "knowledge")
    before, before_calls, before_pushes = path.read_bytes(), len(calls), len(rt.gh_run.pushed)
    with pytest.raises(InitError, match="foundation"):
        _run_partial(rt)
    assert path.read_bytes() == before and len(calls) == before_calls
    assert len(rt.gh_run.pushed) == before_pushes and not rt.gh_run.created


def test_partial_scope_does_not_invent_missing_initial_feature_task(world):
    rt, original, calls, traces, page = _retained_native_partial(world)
    original.coverage["foundation_jobs"]["tasks"] = {
        k: t for k, t in original.coverage["foundation_jobs"]["tasks"].items()
        if t["owner"] != "feature-demo"}
    original.save(rt.state_dir)
    before_calls = len(calls)
    with pytest.raises(InitError, match="missing initial feature task"):
        _run_partial(rt)
    assert len(calls) == before_calls and not rt.gh_run.pushed and not rt.gh_run.created


def test_partial_depth_handoff_binds_exact_merged_output_and_raw_record(world):
    rt, original, calls, traces, page = _retained_native_partial(world)
    record = _run_partial(rt)
    prepared = load_prepared(record.pr["prepared"])
    baseline = _commit(world["origin"], prepared["files"], "merge exact partial foundation output")
    assert rt.knowledge.fetch() == baseline
    path = InitRecord.path(rt.state_dir, "toy", "knowledge")
    raw = path.read_bytes()
    merged = SimpleNamespace(pr_state=lambda number: "MERGED")
    kwargs = dict(knowledge=rt.knowledge, baseline=baseline, repo="toy", pin=record.pin, publisher=merged)
    binding = foundation_handoff(path, **kwargs)
    assert binding["record_sha256"] == hashlib.sha256(raw).hexdigest()
    assert binding["receipt_sha256"] == record.coverage["foundation_publication"]["receipt"]["sha256"]
    assert binding["files_sha256"] == {p: hashlib.sha256(t.encode()).hexdigest() for p, t in prepared["files"].items()}
    kwargs["publisher"] = SimpleNamespace(pr_state=lambda number: "OPEN")
    with pytest.raises(InitError, match="handoff"):
        foundation_handoff(path, **kwargs)
    kwargs["publisher"] = merged
    record.coverage["foundation_publication"]["unknown_foundation_facets"] = {}
    record.save(rt.state_dir)
    with pytest.raises(InitError, match="handoff|receipt"):
        foundation_handoff(path, **kwargs)
    path.write_bytes(raw)
    changed = _commit(world["origin"], {"knowledge/" + page: prepared["files"]["knowledge/" + page] + "\nChanged after publication.\n"}, "alter merged output")
    rt.knowledge.fetch()
    kwargs["baseline"] = changed
    with pytest.raises(InitError, match="handoff"):
        foundation_handoff(path, **kwargs)


def test_partial_cannot_publish_without_final_seven_facet_policy(world):
    rt, original, calls, traces, page = _retained_native_partial(world, semantic=False)
    before_calls = len(calls)
    path = InitRecord.path(rt.state_dir, "toy", "knowledge")
    before = path.read_bytes()
    with pytest.raises(InitError, match="semantic-depth acceptance policy"):
        _run_partial(rt)
    assert path.read_bytes() == before
    assert len(calls) == before_calls and not rt.gh_run.pushed and not rt.gh_run.created


@pytest.mark.parametrize("strict_met,structural_met,mode,expected", [
    (False, True, "strict", False),
    (True, True, "strict", True),
    (False, False, "partial", False),
    (False, True, "partial", True),
])
def test_explicit_selector_preserves_structure_and_strict_thresholds(strict_met, structural_met, mode, expected):
    assert coverage_targets_met({"met": strict_met, "structural": {"met": structural_met}}, mode) is expected
    with pytest.raises(ValueError, match="foundation_mode"):
        coverage_targets_met({"met": True, "structural": {"met": True}}, "automatic")


@pytest.mark.parametrize("stopped", [False, True])
def test_partial_depth_partition_completion_is_separate_from_global_semantic_acceptance(world, monkeypatch, stopped):
    from infermatrix_copilot.kb_service.init_support import InitPublisher

    rt, original, calls, traces, page = _retained_native_partial(world, second_feature=True)
    publication = _run_partial(rt)
    prepared = load_prepared(publication.pr["prepared"])
    baseline = _commit(world["origin"], prepared["files"], "merge partial foundation for depth")
    assert rt.knowledge.fetch() == baseline
    foundation_path = InitRecord.path(rt.state_dir, "toy", "knowledge")
    monkeypatch.setattr(InitPublisher, "pr_state", lambda self, number: "MERGED")
    depth_calls = []

    class EmptyDepthTransport:
        subscription_billing = True
        supports_native_events = True

        def complete(self, *, system, messages, model, effort, role, **kwargs):
            assert role == "generator"  # No offered claim can cause a native yes judgment.
            payload = json.loads(messages[0]["content"].split("\n", 1)[1].rsplit("</untrusted_data>", 1)[0])
            depth_calls.append(payload)
            return Reply(blocks=[Block(type="text", text=json.dumps({"title": "No supported claim", "sections": []}))], model=model)

    state = world["tmp"] / "partial-depth"
    gateway = ModelGateway(None, transport_factory=lambda _: EmptyDepthTransport(), recorder=trace_recorder(TraceStore(state / "init/traces")))
    depth_rt = _runtime(world, gateway, state_dir=state, generator=ModelRole("generator", "zcode", "GLM-5.3"))
    stop = state / "STOP"
    if stopped:
        state.mkdir(parents=True)
        stop.write_text("Explicit unit interruption\n")
    options = dict(dry_run=True, from_existing=True, unlimited_subscription=True, acceptance_mode="lightweight",
                   feature_ids=("demo",), foundation_mode="partial", foundation_record_path=foundation_path,
                   stop_file=stop)
    record = run_stage(depth_rt, _modules_lifecycle(), "knowledge-deepen", **options)
    assert record.depth["execution_scope"] == {"feature_ids": ["demo"], "complete": not stopped}
    assert record.depth["done"] is False and record.depth["target_met"] is False
    assert record.coverage["semantic_depth"]["total_features"] == 2
    assert record.coverage["semantic_depth"]["total_facets"] == 14
    assert record.coverage["semantic_depth"]["recognized_facets"] == 0
    assert record.coverage["breadth"]["met"] is False
    assert record.coverage["breadth"]["structural"]["met"] is True
    assert record.coverage["foundation"]["init_complete"] is False
    assert bool(depth_calls) is not stopped
    assert all(payload["feature"]["id"] == "demo" for payload in depth_calls)
    if not stopped:
        # A retained successful visit flag is not authority for a later resume
        # whose accepted-page proof fails before any extraction can begin.
        from infermatrix_copilot.kb_service.init_stages import _page_frontmatter
        from infermatrix_copilot.kb_service.knowledge_coverage import load_policy
        from infermatrix_copilot.kb_service.knowledge_depth import depth_page, digest
        invalid = _page_frontmatter("Tampered accepted page", kind="architecture", today="2026-10-01", tags=["toy"]) + "No approved depth proof remains.\n"
        policy = load_policy(rt.knowledge.show(baseline, policy_path("toy")), "repos/toy")
        target = depth_page(next(feature for feature in policy.features if feature.id == "demo"))
        record.depth["accepted"][target] = invalid
        record.depth["features"]["demo"]["accepted_sha256"] = digest(invalid)
        record.save(state)
        before_calls = len(depth_calls)
        rejected = run_stage(depth_rt, _modules_lifecycle(), "knowledge-deepen", **options)
        assert rejected.status == "blocked" and "pinned proof" in rejected.problems[0]
        assert rejected.depth["execution_scope"] == {"feature_ids": ["demo"], "complete": False}
        assert len(depth_calls) == before_calls
