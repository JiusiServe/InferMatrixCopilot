"""Autonomous entry leads, saturated inputs and truthful residual checkpoints."""
import hashlib
import json
from types import SimpleNamespace

import pytest

from infermatrix_copilot.kb_service.feature_discovery_index import (
    build_discovery_index, contract_units, unit_evidence,
    build_for_stage,
)
from infermatrix_copilot.kb_service.init_feature_discovery import DiscoveryEngine, _hash
from infermatrix_copilot.kb_service.init_budget import BudgetExhausted
from infermatrix_copilot.kb_service.models import ModelReply, ModelRole

PIN = "a" * 40


def make_index(root, files):
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text if isinstance(text, bytes) else text.encode())
    return build_discovery_index(root, pin=PIN, scope={"roots": ["src/"], "exclude": []}, doc_globs=["docs/*.md"])


def payload(prompt):
    return json.loads(prompt.split("\n", 1)[1].rsplit("\n", 1)[0])


def row(key, path="src/library.py", start=1, end=2):
    return {"id": key, "title": key, "description": "Return an explicit caller value.", "owner": "core",
            "relation": "new", "related_id": "", "aliases": [],
            "evidence": [{"path": path, "start": start, "end": end}]}


def reply(role, data):
    text = json.dumps(data)
    model = ModelRole(role, "zcode" if role == "generator" else "codex", "GLM-5.3" if role == "generator" else "gpt-6-sol")
    return ModelReply(model, data, text, model.model, {}, .1, None, "native-test",
                      hashlib.sha256(text.encode()).hexdigest())


def judge(data, supported="yes"):
    return {"decisions": {r["id"]: {"supported": supported, "relation": "new", "related_id": "",
                                   "reason": "Supplied implementation establishes the explicit value."}
                          for r in data["candidates"]}}


def test_multilanguage_entries_do_not_require_document_keywords(tmp_path):
    index = make_index(tmp_path, {
        "src/library.py": "def public(value):\n    return _helper(value)\n\ndef _helper(value):\n    return value\n",
        "src/plugin.ts": "// implementation\nexport const run = (value: string) => value;\nrouter.post('/start', run);\n",
        "src/library.unknown": "publish values to caller\n",
        "src/broken.py": b"\xff",
        "sdks/nested/tests/test_public.py": "def test_public():\n    assert public(1) == 1\n",
    })
    units = contract_units(index)
    assert {u["path"] for u in units} == set(index.production)
    assert any(u["name"] == "run" for u in units)
    assert any(u["kind"] == "registration" for u in units)
    assert any(u["language"] == "unknown" for u in units)
    unreadable = next(u for u in units if u["path"] == "src/broken.py")
    assert unreadable["status"] == "error" and unit_evidence(index, unreadable) == []
    public = next(u for u in units if u["name"] == "public")
    excerpts = unit_evidence(index, public)
    assert any("def _helper" in e["text"] for e in excerpts)
    assert any(e["path"] == "sdks/nested/tests/test_public.py" and "assert" in e["text"] for e in excerpts)
    assert sum(len(e["text"]) + 150 for e in excerpts) <= 12000


def test_unknown_candidate_cannot_hide_another_entry_in_the_same_file(tmp_path):
    index = make_index(tmp_path, {"src/library.py": "def first():\n    return 1\n\ndef second():\n    return 2\n"})
    first, second = row("first"), row("second", start=4, end=5)
    for r in (first, second):
        r.update(generator_receipts=[{"trace_id": "g"}], origin_rounds=["source"])
    reviews = {"first": {**judge({"candidates": [first]})["decisions"]["first"], "candidate_sha256": _hash(first), "judge_receipt": {"trace_id": "j"}},
               "second": {"supported": "unsure", "relation": "unknown", "reason": "Unknown boundary", "attempts": 4}}
    engine = DiscoveryEngine(index, seeds=[], owners=[], state={"candidates": {r["id"]: r for r in (first, second)}, "reviews": reviews}, call=None, save=lambda: None)
    resolution = engine.unit_resolution()
    assert resolution["associated"] == 1
    assert [u["name"] for u in resolution["unassociated_units"]] == ["second"]


def test_broad_accepted_reference_cannot_hide_unexplained_entries(tmp_path):
    index = make_index(tmp_path, {"src/library.py": "def first():\n    return 1\n\ndef second():\n    return 2\n"})
    candidate = row("first", end=5)
    candidate.update(description="The first public contract returns one.",
                     generator_receipts=[{"trace_id": "g"}], origin_rounds=["source"])
    review = {**judge({"candidates": [candidate]})["decisions"]["first"],
              "candidate_sha256": _hash(candidate), "judge_receipt": {"trace_id": "j"}}
    engine = DiscoveryEngine(index, seeds=[], owners=[],
        state={"candidates": {"first": candidate}, "reviews": {"first": review}},
        call=None, save=lambda: None)
    resolution = engine.unit_resolution()
    assert resolution["associated"] == 1
    assert [u["name"] for u in resolution["unassociated_units"]] == ["second"]


def test_saturated_packet_is_split_and_resume_does_not_resample(tmp_path):
    index = make_index(tmp_path, {"src/library.py": "\n".join(f"value_{n} = {n}" for n in range(64))})
    sizes = []
    def call(role, system, prompt, validate):
        data = payload(prompt)
        lines = sum(e["end"] - e["start"] + 1 for e in data["files"])
        sizes.append(lines)
        anchor = data["files"][0]
        result = {"candidates": [row(f"entry-{n}", start=anchor["start"], end=anchor["start"])
                                  for n in range(24)]}
        validate(result)
        return reply(role, result)
    state = {}
    engine = DiscoveryEngine(index, seeds=[], owners=[], state=state, call=call, save=lambda: None, concurrency=1)
    assert engine.scan()
    assert sorted(sizes) == [16, 16, 16, 16, 32, 32, 64]
    assert sum(bool(t.get("overflow_unknown")) for t in state["tasks"].values()) == 4
    assert max(t["split_depth"] for t in state["tasks"].values()) == 2
    resumed = DiscoveryEngine(index, seeds=[], owners=[], state=state,
                              call=lambda *a, **k: pytest.fail("successful task was sampled again"), save=lambda: None)
    assert resumed.scan()


def test_residual_pass_finds_unexplained_entry_and_preserves_four_round_cap(tmp_path):
    index = make_index(tmp_path, {"src/library.py": "def first():\n    return 1\n\ndef second():\n    return 2\n"})
    calls = []
    def call(role, system, prompt, validate):
        data = payload(prompt)
        calls.append((role, data.get("round")))
        if role == "generator":
            result = {"candidates": [row("second", start=4, end=5) if data["round"].startswith("residual") else row("first")]}
        else:
            result = judge(data)
        validate(result)
        return reply(role, result)
    engine = DiscoveryEngine(index, seeds=[], owners=[], state={}, call=call, save=lambda: None)
    assert engine.scan() and engine.review() and engine.supplemental_scan()
    assert engine.unit_resolution()["associated"] == 2
    assert set(engine.state["residual_rounds"]) == {"1", "2"}
    assert sum(role == "generator" and (kind or "").startswith("residual") for role, kind in calls) == 1
    assert engine.state["residual_complete"]
    frozen = json.loads(json.dumps(engine.state))
    resumed = DiscoveryEngine(index, seeds=[], owners=[], state=frozen,
                              call=lambda *a, **k: pytest.fail("completed residual task was sampled again"), save=lambda: None)
    assert resumed.scan() and resumed.review() and resumed.supplemental_scan()


def test_budget_stop_preserves_residual_plan_and_completed_source(tmp_path):
    index = make_index(tmp_path, {"src/library.py": "def first():\n    return 1\n\ndef second():\n    return 2\n"})
    blocked = True
    calls = []
    def call(role, system, prompt, validate):
        data = payload(prompt)
        calls.append(data.get("round", "judge"))
        if role == "generator" and data["round"].startswith("residual") and blocked:
            raise BudgetExhausted("save checkpoint")
        result = {"candidates": [row("first") if data.get("round") == "source" else row("second", start=4, end=5)]} if role == "generator" else judge(data)
        return reply(role, result)
    state = {}
    first = DiscoveryEngine(index, seeds=[], owners=[], state=state, call=call, save=lambda: None, concurrency=1)
    assert first.scan() and first.review() and not first.supplemental_scan()
    assert not state["residual_rounds"]["1"]["complete"]
    assert any(t["status"] == "pending" for t in state["tasks"].values())
    blocked = False
    resumed = DiscoveryEngine(index, seeds=[], owners=[], state=state, call=call, save=lambda: None)
    assert resumed.scan() and resumed.review() and resumed.supplemental_scan()
    assert calls.count("source") == 1 and resumed.unit_resolution()["associated"] == 2


def test_exhausted_candidate_with_new_evidence_does_not_reset_review_counter(tmp_path):
    index = make_index(tmp_path, {"src/library.py": "def first():\n    return 1\n\ndef second():\n    return 2\n"})
    calls = []
    def call(role, system, prompt, validate):
        data = payload(prompt)
        calls.append(role)
        result = {"candidates": [row("first", end=5 if data["round"].startswith("residual") else 2)]} if role == "generator" else judge(data, "unsure")
        return reply(role, result)
    state = {}
    engine = DiscoveryEngine(index, seeds=[], owners=[], state=state, call=call, save=lambda: None)
    assert engine.scan() and engine.review()
    assert calls.count("judge") == 4
    assert engine.supplemental_scan()
    assert calls.count("judge") == 4 and state["review_attempts"]["first"] == 4
    assert engine.unit_resolution()["associated"] == 0


def test_discovery_index_accepts_sha256_commit_identity(tmp_path):
    path = tmp_path / "src/library.py"
    path.parent.mkdir()
    path.write_text("def public(): return 1\n")
    index = build_discovery_index(tmp_path, pin="a" * 64, scope={"roots": ["src/"], "exclude": []})
    assert index.identity["pin"] == "a" * 64


def test_portable_scope_uses_approved_suffixes_and_custom_tests(tmp_path):
    from infermatrix_copilot.kb_service.config import InitConfig
    tree, state = tmp_path / "repo", tmp_path / "state"
    make_index(tree, {"src/library.fiction": "publish caller value\n",
                      "src/unused.py": "def outside_suffix(): pass\n",
                      "extra/unapproved.fiction": "unapproved first party contract\n",
                      "qa/check_contract.fiction": "check caller value\n",
                      "src/vendor/tests/imported.py": "assert copied_behavior()\n"})
    stage = SimpleNamespace(
        lifecycle=SimpleNamespace(init=InitConfig(source_roots=("src/",), exclude=("qa/**", "src/vendor/**")), repo="demo"),
        record=SimpleNamespace(pin=PIN), manifest={"portable_scope": {"suffixes": [".fiction"], "filenames": [], "test_globs": ["qa/**"]}},
        _coverage_policy_path=lambda: "coverage.yaml", _base_sha="b" * 40,
        rt=SimpleNamespace(state_dir=state, knowledge=SimpleNamespace(show=lambda *a: None)))
    index = build_for_stage(tree, stage)
    assert index.production == ["src/library.fiction"]
    assert index.tests == ["qa/check_contract.fiction"]
    assert index.identity["scope"]["suffixes"] == [".fiction"]
    assert index.identity["scope"]["test_globs"] == ["qa/**"]
    assert index.scope_suggestions == [
        {"path": "extra/unapproved.fiction", "reason": "code outside declared production roots"},
        {"path": "src/unused.py", "reason": "unsupported suffix outside declared suffix scope"}]


def test_incremental_paths_limit_work_but_do_not_shrink_inventory(tmp_path):
    index = make_index(tmp_path, {"src/changed.py": "def changed():\n    return 1\n",
                                  "src/untouched.py": "def untouched():\n    return 2\n",
                                  "docs/guide.md": "# Untouched capability\n"})
    offered = []
    def call(role, system, prompt, validate):
        data = payload(prompt)
        offered.extend(e["path"] for e in data["files"])
        return reply(role, {"candidates": []})
    engine = DiscoveryEngine(index, seeds=[], owners=[], state={}, call=call, save=lambda: None,
                             scan_paths=["src/changed.py"])
    assert engine.scan() and engine.review() and engine.supplemental_scan()
    assert set(offered) == {"src/changed.py"}
    assert index.production == ["src/changed.py", "src/untouched.py"]
    assert {u["path"] for u in engine.units} == {"src/changed.py"}
    with pytest.raises(ValueError, match="outside the frozen index"):
        DiscoveryEngine(index, seeds=[], owners=[], state={}, call=None, save=lambda: None,
                        scan_paths=["src/deleted.py"])
