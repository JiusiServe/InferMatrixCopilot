"""Existing adjacent manuals are retrieval evidence, never invented tests."""

from types import SimpleNamespace

import pytest

from infermatrix_copilot.kb_service.depth_inputs import DepthContext, SYSTEM_DEPTH, prompt, system_prompt
from infermatrix_copilot.kb_service.init_knowledge_depth import _KnowledgeDepth
from test_kb_depth_shared_index import PIN, POLICY, _index, _write
from test_kb_init_skeleton import world  # noqa: F401


def _stage(generic=()):
    stage = object.__new__(_KnowledgeDepth)
    stage._docs_for = lambda tree, owner: list(generic)
    return stage


def _feature(source, docs=()):
    return SimpleNamespace(id="tool", entry_points=(source,), source_globs=(source,), docs=tuple(docs))


def _context(root, source, index, mode="lightweight", **kwargs):
    return DepthContext(root, [source], index=index, pin=PIN, policy_sha256=POLICY, mode=mode, **kwargs)


def _docs(stage, root, feature, context):
    return stage._docs(root, feature, None, context=context, facets=("validation",))


def _assert_real_spans(root, docs):
    assert sum(len(line.encode("utf-8")) + 1 for d in docs for line in d["text"]) <= 8000
    for d in docs:
        assert d["text"] == (root / d["path"]).read_text().splitlines()[d["start"] - 1:d["end"]]


def test_source_only_skill_gets_late_existing_manual_commands_before_owner_docs(tmp_path):
    root = tmp_path / "repo"
    source = "skills/docx/scripts/main.py"
    _write(root, source, "def inspect(path):\n    return path\n")
    skill = "skills/docx/SKILL.md"
    _write(root, skill, "context only\n" * 1200 + "## 完成后的验证\nRun inspect output.docx.\n预期标题树与表格数一致，残留计数为0。\n")
    generic = "docs/owner.md"
    _write(root, generic, "Generic navigation.\n" * 3000)
    _write(root, "TESTING.md", "验证 pytest expected assert manual 测试步骤预期。\n" * 3000)
    foreign = "skills/other/SKILL.md"
    _write(root, foreign, "验证 foreign tool; expected everything passed.\n")
    index = _index(root, [source])
    context = _context(root, source, index)
    stage = _stage([{"path": generic, "start": 1, "text": (root / generic).read_text(), "end": 3000}])
    docs = _docs(stage, root, _feature(source), context)
    _assert_real_spans(root, docs)
    assert any(d["path"] == skill and d["end"] > 1200 and "Run inspect output.docx." in d["text"] for d in docs)
    assert all(d["path"] != foreign for d in docs)
    assert all(d["path"] != "TESTING.md" for d in docs)
    packet = context.build(_feature(source), "", docs, facets=("validation",))
    assert any(d["path"] == skill and d["end"] > 1200 for d in packet["docs"])
    assert packet["source_index"]["sha256"] == index.sha256
    assert packet["source_bytes"] <= 24000
    _assert_real_spans(root, packet["docs"])


@pytest.mark.parametrize("manual", ["SKILL.md", "README.zh-CN.rst", "DESIGN_中文.adoc"])
def test_ancestor_docs_are_language_independent_and_direct_sibling_reference_is_available(tmp_path, manual):
    root = tmp_path / "repo"
    source = "pkg/tool/scripts/run.unknown"
    _write(root, source, "RUN operation\n")
    path = "pkg/tool/" + manual
    _write(root, path, "## 验证步骤\nmanual run tool --check\nexpected point_map.json has points with labels.\n")
    reference = "pkg/tool/reference.md"
    _write(root, reference, "manual run tool input output\nexpected output includes point IDs.\n")
    index = _index(root, [source])
    docs = _docs(_stage(), root, _feature(source), _context(root, source, index))
    assert {path, reference}.issubset({d["path"] for d in docs})
    _assert_real_spans(root, docs)


def test_explicit_docs_remain_first_and_unreadable_or_foreign_docs_are_not_offered(tmp_path):
    root = tmp_path / "repo"
    source = "pkg/tool/main.py"
    _write(root, source, "def run():\n    return 1\n")
    _write(root, "guide.md", "manual expected output equals one.\n")
    _write(root, "pkg/tool/SKILL.md", "manual expected result is one.\n")
    _write(root, "pkg/other/SKILL.md", "manual expected result is anything.\n")
    (root / "pkg/tool/DESIGN.md").write_bytes(b"\xff")
    index = _index(root, [source])
    docs = _docs(_stage(), root, _feature(source, ("guide.md",)), _context(root, source, index))
    assert docs[0]["path"] == "guide.md"
    assert not {"pkg/tool/DESIGN.md", "pkg/other/SKILL.md"}.intersection(d["path"] for d in docs)
    _assert_real_spans(root, docs)
    with pytest.raises(ValueError, match="identity"):
        DepthContext(root, [source], index=index, pin="c" * 40, policy_sha256=POLICY, mode="lightweight")


def test_strict_and_no_index_paths_keep_legacy_numbered_input_and_prompt(tmp_path):
    root = tmp_path / "repo"
    source = "pkg/main.py"
    _write(root, source, "def run():\n    return 1\n")
    _write(root, "guide.md", "Existing guide.\nmanual expected one.\n")
    _write(root, "pkg/SKILL.md", "manual expected two.\n")
    feature = _feature(source, ("guide.md",))
    stage = _stage()
    legacy = stage._docs(root, feature, None)
    index = _index(root, [source])
    assert _docs(stage, root, feature, _context(root, source, index, mode="strict")) == legacy
    assert _docs(stage, root, feature, DepthContext(root, [source], mode="lightweight")) == legacy
    assert legacy[0]["text"] == ["1: Existing guide.", "2: manual expected one."]
    assert system_prompt("strict") == SYSTEM_DEPTH
    payload = {"feature": {"id": "saved"}, "files": [], "docs": legacy}
    assert prompt(payload) == prompt(payload, mode="strict")


def test_final_packet_cannot_reexpand_generic_owner_doc_over_local_manual(tmp_path):
    root = tmp_path / "repo"
    source = "skills/tool/scripts/main.py"
    _write(root, source, "def inspect(value):\n    return value\n")
    skill = "skills/tool/SKILL.md"
    _write(root, skill, "## 验证步骤\nmanual run inspect output.\n预期标题与表格计数一致。\n")
    generic = "docs/owner.md"
    _write(root, generic, "验证 pytest expected assert manual 测试步骤预期。\n" * 3000)
    index = _index(root, [source])
    context = _context(root, source, index)
    stage = _stage([{"path": generic, "start": 1, "end": 3000, "text": (root / generic).read_text()}])
    docs = _docs(stage, root, _feature(source), context)
    packet = context.build(_feature(source), "", docs, facets=("validation",))
    assert packet["docs"] == [{"path": skill, "start": 1, "end": 3,
                              "text": (root / skill).read_text().splitlines()}]
    _assert_real_spans(root, packet["docs"])


def test_stage_injects_selected_manual_once_and_resumes_saved_drafts_unchanged(world, monkeypatch):
    from dataclasses import replace
    import hashlib
    import json
    from infermatrix_copilot.kb_service.depth_index import build_depth_index
    from infermatrix_copilot.kb_service.init_stages import run_stage
    from infermatrix_copilot.kb_service.knowledge_coverage import inventory, policy_path
    from test_kb_knowledge_depth import _baseline, _complete_breadth
    from test_kb_lightweight_runtime import LightGateway
    from test_kb_init_modules import _modules_lifecycle
    from test_kb_init_skeleton import _commit, _git, _runtime

    built = []
    real_build = DepthContext.build

    def capture(context, *args, **kwargs):
        result = real_build(context, *args, **kwargs)
        built.append(result)
        return result

    monkeypatch.setattr(DepthContext, "build", capture)
    policy = _baseline(world)
    manual = "## 验证步骤\nmanual run Engine.step with integer input.\n预期返回递增整数；本轮未执行。\n"
    _commit(world["upstream"], {"pkg/SKILL.md": manual}, "add actual existing manual")
    _complete_breadth(world, policy)
    pin = _git(world["upstream"], "rev-parse", "HEAD")
    raw_policy = (world["origin"] / policy_path("toy")).read_text()
    cache = world["tmp"] / "retrieval-index.json"
    build_depth_index(world["upstream"], inventory(world["upstream"], policy), pin=pin,
                      policy_sha256=hashlib.sha256(raw_policy.encode()).hexdigest(), cache_path=cache)
    gateway = LightGateway(reject="api")
    rt = _runtime(world, gateway, state_dir=world["tmp"] / "depth-adjacent")
    lifecycle = replace(_modules_lifecycle(), init=replace(_modules_lifecycle().init, budget_usd=10))
    args = dict(dry_run=True, from_existing=True, subscription_generator=True,
                acceptance_mode="lightweight", depth_index_path=cache)
    record = run_stage(rt, lifecycle, "knowledge-deepen", **args)
    assert len(gateway.depth_calls) == 4
    packet = gateway.depth_calls[0]
    assert any(d["path"] == "pkg/SKILL.md" and d["text"] == manual.splitlines() for d in packet["docs"])
    retrieval = {key: value for key, value in built[0].items() if key != "context_sha256"}
    assert packet["context_sha256"] == hashlib.sha256(json.dumps(retrieval, sort_keys=True,
                          separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    drafts = json.dumps(record.depth, sort_keys=True)
    resumed = run_stage(rt, lifecycle, "knowledge-deepen", retry_unfinished=True, **args)
    assert len(gateway.depth_calls) == 4
    assert json.dumps(resumed.depth, sort_keys=True) == drafts


def test_reference_command_and_observable_output_survive_giant_skill_and_prose_list(tmp_path):
    root = tmp_path / "repo"
    source = "skills/trace/scripts/preprocess.py"
    _write(root, source, "def preprocess(value):\n    return value\n")
    _write(root, "skills/trace/SKILL.md", "验证 pytest expected assert manual 测试步骤预期。\n" * 2000)
    reference = "skills/trace/reference.md"
    _write(root, reference, ("preprocess.py is one tool; expected manual check. " * 90 + "\n") * 20
           + "## 现有运行与验证步骤\n```bash\npython preprocess.py input output\n```\n"
           + "预期 output/point_map.json 具有以下结构，本轮未执行。\n```json\n{\"points\": {\"1\": {\"label\": \"work\"}}}\n```\n")
    index = _index(root, [source])
    context = _context(root, source, index)
    docs = _docs(_stage(), root, _feature(source), context)
    manual = "\n".join(line for d in docs if d["path"] == reference for line in d["text"])
    assert "python preprocess.py input output" in manual and '"points"' in manual
    _assert_real_spans(root, docs)
