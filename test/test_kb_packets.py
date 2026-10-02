"""Trace-derived source completeness, owner routing and conclusion coverage."""
import copy
from types import SimpleNamespace

import pytest

from infermatrix_copilot.kb_service import packets
from infermatrix_copilot.kb_service.intake import _validate_conclusions, draft_prompt
from infermatrix_copilot.kb_service.sources import SourceError
from infermatrix_copilot.kb_service.upstream_facts import MirrorObserver
from test_kb_intake_gate import PAGE, _tree


def source(count=1):
    paths = [f"demo/core/file{i}.py" for i in range(count)]
    return {"number": 11, "title": "queue", "body": "b" * 4000,
            "merged_at": "2026-10-01", "merge_commit_sha": "c" * 40,
            "base": {"ref": "beta"}, "repository": "org/demo",
            "files": [{"filename": p} for p in paths], "changed_files": paths,
            "source_scope": {"repository": "org/demo", "base_branch": "beta"},
            "diff": "".join(f"diff --git a/{p} b/{p}\n+changed\n" for p in paths),
            "reviews": [{"id": 1, "body": "Check this"}], "replies": [{"id": 2, "body": "Done"}],
            "threads": [{"id": 3, "path": paths[-1], "body": "Potential bug"},
                        {"id": 4, "in_reply_to_id": 3, "path": paths[-1], "body": "Withdrawn"}]}


def test_complete_preparation_replaces_discovery_excerpt_and_pins_sha():
    evidence = source(262)
    rt = SimpleNamespace(github=SimpleNamespace(history_evidence=lambda *args, **kwargs: copy.deepcopy(evidence)))
    lifecycle = SimpleNamespace(full_name="org/demo")
    event = {"source": "merged_pr", "external_id": "11", "payload": {"body": "excerpt", "merge_commit_sha": "c" * 40}}
    prepared = packets.prepare_event(rt, lifecycle, event, {})
    assert len(prepared["changed_files"]) == 262 and len(prepared["body"]) == 4000
    assert prepared["threads"][-1]["in_reply_to_id"] == 3
    assert len(prepared["source_sha256"]) == 64
    event["payload"]["merge_commit_sha"] = "d" * 40
    with pytest.raises(SourceError, match="changed since discovery"):
        packets.prepare_event(rt, lifecycle, event, {})


def test_nearest_owner_and_reviewer_units_have_exactly_one_packet():
    tree = _tree()
    tree["repos/demo/_routes.yaml"] += "  - owner: nested\n    path: repos/demo/nested/rules.md\n    scope_prefixes: [demo/core/nested/]\n"
    evidence = source(2)
    evidence["changed_files"][1] = "demo/core/nested/q.py"
    evidence["files"][1]["filename"] = evidence["changed_files"][1]
    for thread in evidence["threads"]:
        thread["path"] = evidence["changed_files"][1]
    prepared = packets.owner_packets(evidence, tree, "repos/demo", None)
    assert [(p["owner_page"], p["changed_files"]) for p in prepared] == [
        (PAGE, ["demo/core/file0.py"]), ("repos/demo/nested/rules.md", ["demo/core/nested/q.py"])]
    assert sorted(u["id"] for p in prepared for u in p["extraction_units"]) == ["replies:2", "reviews:1", "threads:3", "threads:4"]
    assert prepared[1]["threads"][1]["body"] == "Withdrawn"
    assert prepared[1]["shared_discussion"]["reviews"][0]["id"] == 1


def test_packet_budget_splits_files_and_refuses_indivisible_evidence(monkeypatch):
    evidence = source(3)
    evidence["body"] = ""
    monkeypatch.setattr(packets, "MAX_PACKET_BYTES", 1800)
    observer = SimpleNamespace(pr_diff=lambda *args: "x" * 650)
    prepared = packets.owner_packets(evidence, _tree(), "repos/demo", observer)
    assert len(prepared) > 1
    assert [p for packet in prepared for p in packet["changed_files"]] == evidence["changed_files"]
    assert sum(len(p["extraction_units"]) for p in prepared) == 4
    evidence["body"] = "x" * 4000
    with pytest.raises(SourceError, match="budget"):
        packets.owner_packets(evidence, _tree(), "repos/demo", observer)


def test_branch_scoped_observer_and_mixed_branch_refusal(tmp_path):
    observer = MirrorObserver(tmp_path / "mirror", "org/demo", lambda _n: {})
    rt = SimpleNamespace(upstream_facts=lambda _life: observer)
    life = SimpleNamespace(full_name="org/demo")
    evidence = source()
    scoped = packets.observer_for(rt, life, evidence)
    assert scoped.branch == "beta" and observer.branch is None
    other = {"source_scope": {"repository": "org/demo", "base_branch": "main"}}
    with pytest.raises(SourceError, match="one upstream"):
        packets.observer_for(rt, life, [evidence, other])


def test_mirror_failure_is_a_retryable_source_error():
    from infermatrix_copilot.knowledge_service.facts import FactsError

    observer = SimpleNamespace(pr_diff=lambda *args: (_ for _ in ()).throw(FactsError("missing PR ref")))
    with pytest.raises(SourceError, match="missing PR ref"):
        packets.owner_packets(source(), _tree(), "repos/demo", observer)


def test_unmapped_tests_are_shared_proof_for_code_owner_and_never_a_root_destination():
    evidence = source()
    test_path = "tests/test_queue.py"
    evidence["files"].append({"filename": test_path})
    evidence["changed_files"].append(test_path)
    evidence["diff"] += f"diff --git a/{test_path} b/{test_path}\n+assert backpressure\n"
    evidence["threads"][0]["path"] = test_path
    prepared = packets.owner_packets(evidence, _tree(), "repos/demo", None)
    assert [p["owner_page"] for p in prepared] == [PAGE]
    assert prepared[0]["supporting_files"] == [test_path]
    assert "assert backpressure" in prepared[0]["diffs"][test_path]
    assert prepared[0]["shared_discussion"]["unmapped_threads"][0]["id"] == 3
    evidence["changed_files"] = ["new/unrouted/feature.py"]
    with pytest.raises(SourceError, match="no knowledge owner"):
        packets.owner_packets(evidence, _tree(), "repos/demo", None)


def test_conclusions_require_complete_explicit_coverage_and_real_output_ids():
    evidence = {"owner_page": PAGE, "extraction_units": [{"id": "threads:1"}, {"id": "threads:2"}]}
    reply = {"operations": [{"kind": "add", "page": PAGE, "rule_id": "DEMO-2a"}],
             "conclusion_dispositions": [
                 {"unit_id": "threads:1", "action": "keep", "rule_ids": ["DEMO-2a"], "reason": "bounded queue"},
                 {"unit_id": "threads:2", "action": "drop", "rule_ids": [], "reason": "later reply withdrew the suggestion"}]}
    _validate_conclusions(reply, evidence)
    for mutate in (lambda r: r["conclusion_dispositions"].pop(),
                   lambda r: r["conclusion_dispositions"][0].update(rule_ids=["invented"]),
                   lambda r: r["conclusion_dispositions"][1].update(reason=""),
                   lambda r: r["operations"][0].update(page="repos/demo/other/rules.md")):
        bad = copy.deepcopy(reply)
        mutate(bad)
        with pytest.raises(ValueError):
            _validate_conclusions(bad, evidence)


def test_model_specific_paths_use_model_owner_and_all_existing_ids_are_reserved():
    tree = _tree()
    model_page = "repos/demo/models/voice/rules.md"
    tree[model_page] = tree[PAGE] + "\n### DEMO-1a1 — nested invariant\n\n- 强制：keep nested ID.\n"
    tree["repos/demo/_routes.yaml"] += "models:\n  dir: repos/demo/models\n  page: rules.md\n"
    tree["general/_tombstones.yaml"] = "schema_version: 1\nids:\n  - id: GONE-1a\n"
    tree["repos/other/rules.md"] = tree[PAGE].replace("DEMO-1a", "OTHER-1a")
    evidence = source()
    evidence["changed_files"] = ["demo/core/voice.py"]
    evidence["files"] = [{"filename": "demo/core/voice.py"}]
    prepared = packets.owner_packets(evidence, tree, "repos/demo", None)
    assert prepared[0]["owner_page"] == model_page
    prompt = draft_prompt("demo", prepared[0], tree, "repos/demo")
    assert '"DEMO-1a1"' in prompt
    assert '"GONE-1a"' in prompt and '"OTHER-1a"' in prompt


def test_shared_discussion_bodies_are_not_duplicated_in_primary_packet():
    evidence = source()
    evidence["reviews"] = [{"id": i, "body": "r" * 60000} for i in range(3)]
    prepared = packets.owner_packets(evidence, _tree(), "repos/demo", None)
    assert len(prepared) == 1
    assert prepared[0]["reviews"] == []
    assert len(prepared[0]["shared_discussion"]["reviews"]) == 3
    assert len([u for u in prepared[0]["extraction_units"] if u["kind"] == "reviews"]) == 3
