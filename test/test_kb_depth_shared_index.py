"""Shared retrieval snapshots localize evidence without asserting absence."""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from types import SimpleNamespace

import pytest

from infermatrix_copilot.kb_service import depth_index
from infermatrix_copilot.kb_service.depth_index import build_depth_index, load_depth_index
from infermatrix_copilot.kb_service.depth_inputs import (
    DepthContext, SYSTEM_DEPTH, bounded_existing, prompt, system_prompt,
)

PIN, POLICY = "a" * 40, "b" * 64


def _write(root, path, text):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _feature(paths, docs=()):
    return SimpleNamespace(id="transport", entry_points=(paths[0],), source_globs=tuple(paths), docs=tuple(docs))


def _index(root, production, *, cache=None):
    # Cache lives outside the indexed source tree, as it does in campaigns.
    return build_depth_index(root, production, pin=PIN, policy_sha256=POLICY,
                             cache_path=cache or root.parent / (root.name + "-index.json"))


def _context(root, production, index):
    return DepthContext(root, production, index=index, pin=PIN, policy_sha256=POLICY, mode="lightweight")


def test_shared_snapshot_builds_once_and_thirteen_readers_have_isolated_caches(tmp_path, monkeypatch):
    root = tmp_path / "source"
    _write(root, "pkg/core.py", "def send(value=17):\n    return value\n")
    _write(root, "tests/test_core.py", "from pkg.core import send\ndef test_send():\n    assert send() == 17\n")
    cache = tmp_path / "index.json"
    builds = []
    real_build = depth_index._build

    def counted(*args):
        builds.append(True)
        return real_build(*args)

    monkeypatch.setattr(depth_index, "_build", counted)
    with ThreadPoolExecutor(max_workers=4) as pool:
        indexes = list(pool.map(lambda _: _index(root, ["pkg/core.py"], cache=cache), range(4)))
    assert len(builds) == 1
    contexts = [_context(root, ["pkg/core.py"], indexes[0]) for _ in range(13)]
    assert all(context.index.sha256 == indexes[0].sha256 for context in contexts)
    contexts[0].cache["sentinel"] = None
    assert all("sentinel" not in context.cache for context in contexts[1:])
    with pytest.raises(TypeError):
        indexes[0].files["pkg/core.py"]["lines"] = ()
    with pytest.raises(TypeError):
        indexes[0].data["tests"]["tests/test_core.py"]["closure"] = ()


@pytest.mark.parametrize("field,value", [("pin", "c" * 40), ("policy_sha256", "c" * 64)])
def test_wrong_pin_or_policy_is_rejected(tmp_path, field, value):
    root = tmp_path / "source"
    _write(root, "core.py", "def run():\n    return 1\n")
    cache = tmp_path / "index.json"
    _index(root, ["core.py"], cache=cache)
    identity = {"pin": PIN, "policy_sha256": POLICY}
    identity[field] = value
    with pytest.raises(ValueError, match="differs"):
        load_depth_index(cache, **identity, production=["core.py"])


def test_modified_snapshot_and_foreign_production_inventory_are_rejected(tmp_path):
    root = tmp_path / "source"
    _write(root, "core.py", "def run():\n    return 1\n")
    cache = tmp_path / "index.json"
    _index(root, ["core.py"], cache=cache)
    with pytest.raises(ValueError, match="differs"):
        load_depth_index(cache, pin=PIN, policy_sha256=POLICY, production=["foreign.py"])
    envelope = json.loads(cache.read_text())
    envelope["data"]["files"]["core.py"]["lines"][1] = "    return 9"
    cache.write_text(json.dumps(envelope))
    with pytest.raises(ValueError, match="content hash"):
        load_depth_index(cache, pin=PIN, policy_sha256=POLICY)


def test_index_uses_original_byte_hash_and_direct_and_reverse_imports(tmp_path):
    root = tmp_path / "source"
    _write(root, "pkg/core.py", "from pkg.helper import finish\ndef send(value):\n    return finish(value)\n")
    _write(root, "pkg/helper.py", "def finish(value):\n    return value\n")
    index = _index(root, ["pkg/core.py", "pkg/helper.py"])
    assert index.files["pkg/core.py"]["sha256"] == hashlib.sha256((root / "pkg/core.py").read_bytes()).hexdigest()
    assert index.files["pkg/core.py"]["imports"] == ("pkg/helper.py",)
    assert index.data["reverse_imports"]["pkg/helper.py"] == ("pkg/core.py",)
    assert index.files["pkg/helper.py"]["definitions"][0]["symbol"] == "finish"


def test_conftest_and_direct_helper_links_retrieve_actual_assertion_without_global_scan(tmp_path, monkeypatch):
    root = tmp_path / "source"
    source = "pkg/core.py"
    _write(root, source, "def send(value):\n    return value\n")
    _write(root, "tests/conftest.py", "from pkg.core import send\n")
    _write(root, "tests/helper.py", "from pkg.core import send\ndef exercise():\n    return send(7)\n")
    _write(root, "tests/nested/test_request.py", "from tests.helper import exercise\ndef test_roundtrip():\n    assert exercise() == 7\n")
    for number in range(100):
        _write(root, f"other/tests/test_unrelated_{number}.py", "def test_other():\n    assert 1 == 1\n")
    index = _index(root, [source])
    context = _context(root, [source], index)
    monkeypatch.setattr(context, "_closure", lambda *args: pytest.fail("per-feature closure scan"))
    monkeypatch.setattr(context, "_file", lambda *args: pytest.fail("per-feature candidate file scan"))
    report = context.test_association(_feature([source]))
    assert "tests/nested/test_request.py" in report["matched_files"]
    assert not any(path.startswith("other/") for path in report["matched_files"])
    assert index.data["tests"]["tests/nested/test_request.py"]["conftest_ancestors"] == ("tests/conftest.py",)
    assert report["entry_hints"]["tests/nested/test_request.py"]["assertion_lines"] == [3]
    assert not report["complete"]
    assert len(report["scope_files"]) == 103
    report["matched_files"].clear()
    assert context.test_association(_feature([source]))["matched_files"]


def test_lightweight_packing_uses_indexed_lines_and_definitions_without_reparsing_candidates(tmp_path, monkeypatch):
    from infermatrix_copilot.kb_service import depth_inputs

    root = tmp_path / "source"
    source = "pkg/core.py"
    _write(root, source, "def send(timeout=17):\n    return timeout\n")
    _write(root, "tests/conftest.py", "from pkg.core import send\n")
    _write(root, "tests/test_core.py", "from pkg.core import send\ndef test_send():\n    assert send() == 17\n")
    for number in range(30):
        _write(root, f"tests/test_other_{number}.py", "# padding\n" * 100 + "def test_other():\n    assert 1 == 1\n")
    index = _index(root, [source])
    monkeypatch.setattr(depth_inputs.ast, "parse", lambda *args, **kwargs: pytest.fail("reparsed indexed source/test"))
    context = _context(root, [source], index)
    packet = context.build(_feature([source]), "", [], facets=["validation", "configuration"], limit=800)
    shown = "\n".join(line for item in packet["files"] for line in item["text"])
    assert "assert send() == 17" in shown
    assert packet["source_bytes"] <= 800


@pytest.mark.parametrize("test_text,kind", [
    ("import {readFileSync} from 'node:fs';\nconst source = readFileSync(new URL('../src/entry.ts', import.meta.url), 'utf8');\ntest('contract', () => assert.ok(source.includes('send')));\n", "literal_file_input"),
    ("import {build} from 'esbuild';\nawait build({entryPoints: ['src/entry.ts'], outdir: 'out'});\ntest('contract', () => assert.equal(1, 1));\n", "literal_bundle_entry"),
])
def test_literal_file_and_bundle_inputs_localize_tests_but_never_claim_runtime_edges(tmp_path, test_text, kind):
    root = tmp_path / "source"
    source, test = "src/entry.ts", "tests/runtime.test.mjs"
    _write(root, source, "export function send(value) { return value; }\n")
    _write(root, test, test_text)
    index = _index(root, [source])
    report = _context(root, [source], index).test_association(_feature([source]))
    assert test in report["matched_files"]
    assert index.files[test]["literal_links"][0]["kind"] == kind
    assert index.files[test]["literal_links"][0]["path"] == source
    assert not report["complete"]


def test_literal_calls_inside_strings_or_comments_do_not_create_input_links(tmp_path):
    root = tmp_path / "source"
    _write(root, "src/core.ts", "export function send() { return 1; }\n")
    _write(root, "tests/other.test.mjs", "const note = \"readFileSync('src/core.ts')\";\n// readFileSync('src/core.ts')\nconst bundle = \"entryPoints: ['src/core.ts']\";\n")
    index = _index(root, ["src/core.ts"])
    assert not index.files["tests/other.test.mjs"]["literal_links"]


def test_package_root_bundle_script_is_positive_candidate_and_old_absence_scope_is_unchanged(tmp_path):
    root = tmp_path / "source"
    source, test = "frontend/src/entry.ts", "frontend/scripts/test-build.mjs"
    _write(root, "frontend/package.json", '{"name":"frontend"}\n')
    _write(root, source, "export function send(value) { return value; }\n")
    _write(root, test, "import {build} from 'esbuild';\nawait build({entryPoints: ['src/entry.ts']});\nassert.equal(1, 1);\n")
    index = _index(root, [source])
    report = _context(root, [source], index).test_association(_feature([source]))
    assert test in report["matched_files"]
    assert index.files[test]["literal_links"][0]["path"] == source
    assert test not in DepthContext(root, [source]).test_association(_feature([source]))["scope_files"]


def test_lightweight_manual_validation_uses_existing_procedure_and_does_not_require_trace(tmp_path):
    root = tmp_path / "source"
    source, doc = "extension/client.ts", "docs/acceptance.md"
    _write(root, source, "export const items = values.map(value => value.name);\n")
    _write(root, doc, "Click the extension action, then expect the sidebar to open. Manual acceptance, not executed.\n")
    index = _index(root, [source])
    packet = _context(root, [source], index).build(_feature([source], [doc]), "", [], facets=["flow", "validation"])
    assert "Click the extension action" in "\n".join(line for item in packet["docs"] for line in item["text"])
    assert not packet["retrieval_edges"]
    system = system_prompt("lightweight")
    assert "trace is OPTIONAL" in system and "NOT EXECUTED" in system
    for kind in ("automated_runtime", "automated_source_text", "helper_unit", "documented_manual"):
        assert kind in system


def test_dynamic_and_unknown_test_entry_remain_unknown(tmp_path):
    root = tmp_path / "source"
    _write(root, "pkg/core.py", "def send(value):\n    return value\n")
    _write(root, "tests/check_core.py", "import importlib\nfrom pkg.core import send\ndef externally_run():\n    return importlib.import_module('other').send()\n")
    index = _index(root, ["pkg/core.py"])
    report = _context(root, ["pkg/core.py"], index).test_association(_feature(["pkg/core.py"]))
    assert "tests/check_core.py" in report["matched_files"]
    assert not report["entry_hints"]["tests/check_core.py"]["entry_detected"]
    assert any("dynamic" in problem for problem in report["unresolved_files"])
    assert not report["complete"]


def test_lightweight_packet_keeps_late_default_assertion_and_document_acceptance(tmp_path):
    root = tmp_path / "source"
    source, test, doc = "pkg/core.py", "tests/test_core.py", "docs/setup.md"
    _write(root, source, "# padding\n" * 500 + "def send(timeout=17):\n    return timeout\n")
    _write(root, test, "from pkg.core import send\n" + "# padding\n" * 500 + "def test_send():\n    assert send() == 17\n")
    _write(root, doc, "Unrelated introduction.\n" * 1500 + "## 验收测试\nRun pytest tests/test_core.py and assert timeout defaults to 17.\n")
    index = _index(root, [source])
    context = _context(root, [source], index)
    packet = context.build(_feature([source], [doc]), "", [], facets=["configuration", "validation"])
    shown = "\n".join(line for item in packet["files"] for line in item["text"])
    assert "def send(timeout=17)" in shown and "assert send() == 17" in shown
    assert packet["source_bytes"] <= 24_000
    assert "pytest tests/test_core.py" in "\n".join(line for item in packet["docs"] for line in item["text"])
    assert sum(len(line.encode()) + 1 for item in packet["docs"] for line in item["text"]) <= 8_000
    assert any(item["start"] > 1000 for item in packet["docs"])
    for item in packet["docs"]:
        actual = (root / item["path"]).read_text().splitlines()
        assert item["text"] == actual[item["start"] - 1:item["end"]]


def test_rejection_reference_rereads_real_late_document_lines_and_scoped_source(tmp_path):
    root = tmp_path / "source"
    source, doc = "pkg/core.py", "docs/setup.md"
    _write(root, source, "# padding\n" * 300 + "def send(timeout=17):\n    return timeout\n")
    _write(root, doc, "prefix\n" * 300 + "Specific contract condition.\n")
    index = _index(root, [source])
    context = _context(root, [source], index)
    review = "Need docs/setup.md:L301-L301 and pkg/core.py:L301-L302"
    packet = context.build(_feature([source], [doc]), "", [], facets=["configuration"], previous_review=review, limit=700)
    assert "def send(timeout=17)" in "\n".join(line for item in packet["files"] for line in item["text"])
    slices = context.document_slices([], paths=[doc], previous_review=review, limit=100)
    assert any(item["start"] <= 301 <= item["end"] for item in slices)
    assert "Specific contract condition." in "\n".join(line for item in slices for line in item["text"])


def test_strict_defaults_and_prompt_schema_remain_compatible(tmp_path):
    assert system_prompt() == SYSTEM_DEPTH
    assert len(system_prompt("lightweight")) < len(SYSTEM_DEPTH)
    assert "Unknown is not absence" in system_prompt("lightweight")
    assert prompt({"files": [], "docs": []}) == prompt({"files": [], "docs": []}, mode="strict")
    with pytest.raises(ValueError, match="mode"):
        system_prompt("unsafe")
    root = tmp_path / "source"
    _write(root, "core.py", "def send():\n    return 17\n")
    context = DepthContext(root, ["core.py"])
    packet = context.build(_feature(["core.py"]), "", [])
    assert "acceptance_mode" not in packet and "docs" not in packet
    assert context.test_association(_feature(["core.py"]))["complete"]
    assert not DepthContext(root, ["core.py"], mode="lightweight").test_association(_feature(["core.py"]))["complete"]
    existing = bounded_existing({"page": "汉字\n" * 3000})
    assert sum(len(text.encode()) for text in existing.values()) <= 4000
