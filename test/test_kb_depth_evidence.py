"""Feature depth retrieval must find evidence beyond prefixes and root tests."""

from types import SimpleNamespace

import pytest

from infermatrix_copilot.kb_service.depth_inputs import DepthContext
from infermatrix_copilot.kb_service.knowledge_coverage import SUFFIXES


def _write(root, path, text):
    file = root / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(text, encoding="utf-8")


def _feature(paths, *, entry=None):
    return SimpleNamespace(id="transport", entry_points=(entry or paths[0],), source_globs=tuple(paths), docs=())


def _shown(data):
    return "\n".join(line for file in data["files"] for line in file["text"])


def test_test_inventory_detector_version_is_shared_with_absence_validation():
    from infermatrix_copilot.kb_service.depth_inputs import TEST_ASSOCIATION_VERSION
    from infermatrix_copilot.knowledge_service.lifecycle import DEPTH_ABSENCE_DETECTOR

    assert TEST_ASSOCIATION_VERSION == DEPTH_ABSENCE_DETECTOR == "static-test-association-v2"


@pytest.mark.parametrize("suffix", SUFFIXES)
def test_global_test_inventory_includes_every_policy_supported_code_suffix(tmp_path, suffix):
    source, test = "pkg/core.py", "sdk/nested/tests/contract" + suffix
    _write(tmp_path, source, "def send(value):\n    return value\n")
    _write(tmp_path, test, "language specific test fixture\n")
    report = DepthContext(tmp_path, [source]).test_association(_feature([source]))
    assert report["scope_files"] == [test]
    assert not report["complete"]
    assert any(test in problem for problem in report["unresolved_files"])


def test_go_cli_test_cannot_be_silently_excluded_from_python_feature_absence(tmp_path):
    from infermatrix_copilot.kb_service.knowledge_depth import build_absence_certificate

    source, test = "pkg/cli.py", "tests/cli_test.go"
    _write(tmp_path, source, "def main():\n    print('ok')\nif __name__ == '__main__':\n    main()\n")
    _write(tmp_path, test, 'package tests\nimport ("os/exec"; "strings"; "testing")\n'
           'func TestCLI(t *testing.T) {\n'
           ' out, err := exec.Command("python3", "-m", "pkg.cli").Output()\n'
           ' if err != nil || strings.TrimSpace(string(out)) != "ok" {\n'
           '  t.Fatalf("bad CLI output: %s, %v", out, err)\n }\n}\n')
    _write(tmp_path, "docs.md", "CLI documentation.\n")
    feature = _feature([source])
    feature.docs = ("docs.md",)
    report = DepthContext(tmp_path, [source]).test_association(feature)
    assert report["scope_files"] == [test]
    assert not report["complete"]
    assert any(test in problem and "checker" in problem for problem in report["unresolved_files"])
    policy = SimpleNamespace(roots=("pkg/",), exclude=(), suffixes=(".py",), filenames=())
    assert build_absence_certificate(tmp_path, policy, feature, "a" * 40) is None


def test_configuration_search_covers_all_reviewed_files_and_actual_use(tmp_path):
    paths = [f"pkg/part{i}.py" for i in range(6)]
    for path in paths[:-1]:
        _write(tmp_path, path, "def unrelated():\n    return None\n")
    _write(tmp_path, paths[-1], "# padding\n" * 220 + "RETRY_TIMEOUT = 17\ndef connect(timeout=RETRY_TIMEOUT):\n    return timeout\n")
    data = DepthContext(tmp_path, paths).build(_feature(paths), "", [], facets=["configuration"])
    assert data["source_scope"] == sorted(paths)
    assert "RETRY_TIMEOUT = 17" in _shown(data)
    assert "def connect(timeout=RETRY_TIMEOUT):" in _shown(data)
    assert data["source_bytes"] <= 64_000


def test_validation_finds_nested_sdk_mjs_and_late_assertions(tmp_path):
    source = "sdk/src/transport.mjs"
    _write(tmp_path, source, "export function send(value) { return value; }\n")
    test = "sdk/tests/requests.test.mjs"
    _write(tmp_path, test, "import {send} from '../src/transport.mjs';\n" + "// padding\n" * 250
           + "test('returns input', () => {\n  assert.equal(send(7), 7);\n});\n")
    data = DepthContext(tmp_path, [source]).build(_feature([source]), "", [], facets=["validation"])
    assert data["test_search"]["matched_files"] == [test]
    assert "assert.equal(send(7), 7)" in _shown(data)
    assert any(f["path"] == test and f["end"] > 250 for f in data["files"])


def test_aliased_javascript_test_and_assertion_entries_cannot_certify_absence(tmp_path):
    from infermatrix_copilot.kb_service.knowledge_depth import build_absence_certificate

    source, test = "pkg/core.mjs", "tests/roundtrip.test.mjs"
    _write(tmp_path, source, "export function send(value) { return value; }\n")
    _write(tmp_path, test, "import {test as scenario} from 'node:test';\n"
                         "import {strictEqual as equal} from 'node:assert';\n"
                         "import {send} from '../pkg/core.mjs';\n"
                         "scenario('roundtrip', () => equal(send(3), 3));\n")
    _write(tmp_path, "docs.md", "Core API documentation.\n")
    feature = _feature([source])
    feature.docs = ("docs.md",)
    report = DepthContext(tmp_path, [source]).test_association(feature)
    assert not report["complete"]
    assert any(test in problem and "static test entry" in problem for problem in report["unresolved_files"])
    policy = SimpleNamespace(roots=("pkg/",), exclude=(), suffixes=(".mjs",), filenames=())
    assert build_absence_certificate(tmp_path, policy, feature, "a" * 40) is None


@pytest.mark.parametrize("link", ["symbol", "docs"])
def test_unrecognized_test_entry_with_symbol_or_doc_link_remains_unknown(tmp_path, link):
    source, test = "pkg/core.py", "tests/check_behavior.py"
    _write(tmp_path, source, "def send(value):\n    return value\n")
    _write(tmp_path, test, "def check_behavior():\n    send(3)\n" if link == "symbol" else "def check_behavior():\n    pass\n")
    docs = [{"text": "External runner invokes " + test}] if link == "docs" else []
    report = DepthContext(tmp_path, [source]).test_association(_feature([source]), docs)
    assert not report["complete"] and any(test in problem for problem in report["unresolved_files"])


def test_python_call_neighbours_use_the_same_exact_root_module_as_source_audit(tmp_path):
    from infermatrix_copilot.kb_service.knowledge_depth import verify_trace

    caller, actual, copy = "pkg/caller.py", "pkg/helpers.py", "sdks/client/pkg/helpers.py"
    _write(tmp_path, "pkg/__init__.py", "")
    _write(tmp_path, caller, "from pkg.helpers import finish\ndef run(value):\n    return finish(value)\n")
    _write(tmp_path, actual, "def finish(value):\n    return value + 1\n")
    _write(tmp_path, copy, "def finish(value):\n    return value + 2\n")
    context = DepthContext(tmp_path, [caller, actual, copy])
    assert context._resolve_module("pkg.helpers") == actual
    assert context._import_targets(caller)[0] == {actual}
    node = context._file(caller)[2][0]
    assert [path for path, _ in context._neighbours(caller, node)] == [actual]
    trace = [{"path": caller, "symbol": "run", "start": 2, "end": 3},
             {"path": actual, "symbol": "finish", "start": 1, "end": 2}]
    verify_trace(tmp_path, trace)
    with pytest.raises(ValueError):
        verify_trace(tmp_path, [trace[0], {**trace[1], "path": copy}])


def test_python_module_and_package_ambiguity_remains_unknown(tmp_path):
    caller = "pkg/caller.py"
    _write(tmp_path, caller, "from pkg.helpers import finish as invoke\ndef run():\n    return invoke()\n")
    _write(tmp_path, "pkg/helpers.py", "def finish():\n    return 1\n")
    _write(tmp_path, "pkg/helpers/__init__.py", "def finish():\n    return 2\n")
    context = DepthContext(tmp_path, [caller, "pkg/helpers.py", "pkg/helpers/__init__.py"])
    assert context._resolve_module("pkg.helpers") is None
    targets, unresolved = context._import_targets(caller)
    assert not targets and unresolved


def test_unique_nested_sdk_python_module_retains_a_proven_call_pair(tmp_path):
    from infermatrix_copilot.kb_service.knowledge_depth import verify_trace

    caller, helper = "caller.py", "sdks/client/src/pkg/helpers.py"
    _write(tmp_path, caller, "from pkg.helpers import finish\ndef run():\n    return finish()\n")
    _write(tmp_path, helper, "def finish():\n    return 1\n")
    context = DepthContext(tmp_path, [caller, helper])
    assert context._resolve_module("pkg.helpers") == helper
    assert context._import_targets(caller)[0] == {helper}
    assert context._neighbours(caller, context._file(caller)[2][0])[0][0] == helper
    verify_trace(tmp_path, [{"path": caller, "symbol": "run", "start": 2, "end": 3},
                            {"path": helper, "symbol": "finish", "start": 1, "end": 2}])


def test_relative_python_import_cannot_fall_back_to_a_different_source_root(tmp_path):
    caller, copy = "pkg/caller.py", "sdks/client/pkg/helpers.py"
    _write(tmp_path, caller, "from .helpers import finish as invoke\ndef run():\n    return invoke()\n")
    _write(tmp_path, copy, "def finish():\n    return 1\n")
    context = DepthContext(tmp_path, [caller, copy])
    assert context._resolve_module("pkg.helpers") == copy
    assert context._resolve_module("pkg.helpers", exact=True) is None
    targets, unresolved = context._import_targets(caller)
    assert not targets and unresolved
    assert not context._neighbours(caller, context._file(caller)[2][0])


def test_association_propagates_python_test_helper_imports_and_excludes_init(tmp_path):
    source = "pkg/core.py"
    _write(tmp_path, source, "def send(value):\n    return value\n")
    _write(tmp_path, "tests/helper.py", "from pkg.core import send\n")
    _write(tmp_path, "tests/test_request.py", "from tests.helper import send\ndef test_send():\n    assert send(7) == 7\n")
    _write(tmp_path, "tests/__init__.py", "# package marker\n")
    _write(tmp_path, "tests/test_other.py", "def test_other():\n    assert 1 == 1\n")
    report = DepthContext(tmp_path, [source]).test_association(_feature([source]))
    assert report["matched_files"] == ["tests/test_request.py"]
    assert "tests/__init__.py" in report["scope_files"]
    assert report["complete"]
    assert not report["unresolved_files"]


@pytest.mark.parametrize("test_source", [
    "def test_broken(:\n    pass\n",
    "import importlib\ndef test_dynamic():\n    imported = importlib.import_module('pkg.core')\n    assert imported\n",
])
def test_test_search_parse_and_dynamic_failures_cannot_certify_absence(tmp_path, test_source):
    source = "pkg/core.py"
    _write(tmp_path, source, "def send(value):\n    return value\n")
    _write(tmp_path, "tests/test_unknown.py", test_source)
    report = DepthContext(tmp_path, [source]).test_association(_feature([source]))
    assert not report["complete"]
    assert report["unresolved_files"]
    assert not report["matched_files"]


def test_lexical_client_and_kotlin_ranges_are_retrieval_hints(tmp_path):
    paths = ["web/src/client.ts", "desktop/src/Client.kt"]
    _write(tmp_path, paths[0], "export async function connect(value: number) {\n  return finish(value);\n}\nfunction finish(value: number) {\n  return value + 1;\n}\n")
    _write(tmp_path, paths[1], "fun connect(value: Int): Int {\n  return finish(value)\n}\nfun finish(value: Int): Int {\n  return value + 1\n}\n")
    data = DepthContext(tmp_path, paths).build(_feature(paths), "", [], facets=["flow"])
    assert {(d["path"], d["symbol"]) for d in data["definitions"]} == {(p, symbol) for p in paths for symbol in ("connect", "finish")}
    assert all(d["kind"] == "lexical" for d in data["definitions"])
    assert "dynamic dispatch" in data["limitations"]


def test_bounded_retry_changes_offered_evidence_and_hash(tmp_path):
    source = "pkg/core.py"
    _write(tmp_path, source, "\n".join(f"def branch_{i}():\n    raise ValueError('failure {i}')\n" for i in range(80)))
    context = DepthContext(tmp_path, [source])
    first = context.build(_feature([source]), "", [], facets=["failure_modes"], limit=700)
    later = context.build(_feature([source]), "", [], facets=["failure_modes"], limit=700, evidence_round=1,
                          previous_review="Read the alternate error branch")
    assert first["source_bytes"] <= 700 and later["source_bytes"] <= 700
    assert first["files"] != later["files"]
    assert first["context_sha256"] != later["context_sha256"]


def test_nonpython_parse_failures_and_missing_parser_cannot_certify_absence(tmp_path):
    source = "pkg/core.py"
    _write(tmp_path, source, "def send(value):\n    return value\n")
    _write(tmp_path, "web/tests/broken.test.mjs", "test( => broken syntax }\n")
    _write(tmp_path, "web/tests/unknown.test.ts", "test('sample', () => expect(1).toBe(1));\n")
    report = DepthContext(tmp_path, [source]).test_association(_feature([source]))
    assert not report["complete"]
    assert any("broken.test.mjs" in p for p in report["unresolved_files"])
    assert any("unknown.test.ts" in p for p in report["unresolved_files"])


def test_automatic_conftest_link_is_visible_to_nested_tests(tmp_path):
    source = "pkg/core.py"
    _write(tmp_path, source, "def send(value):\n    return value\n")
    _write(tmp_path, "conftest.py", "from pkg.core import send\n")
    _write(tmp_path, "tests/nested/test_request.py", "def test_send():\n    assert 1 == 1\n")
    report = DepthContext(tmp_path, [source]).test_association(_feature([source]))
    # Automatic fixtures can exercise the feature without a direct test import.
    assert report["matched_files"] == ["tests/nested/test_request.py"]


@pytest.mark.parametrize("evidence_round", [0, 1, 4])
def test_direct_exercised_feature_tests_rank_before_transitive_shared_imports(tmp_path, evidence_round):
    source = "pkg/cron.py"
    _write(tmp_path, source, "def schedule(value):\n    return value + 1\n")
    _write(tmp_path, "pkg/shared.py", "from pkg.cron import schedule\ndef other(value):\n    return value\n")
    _write(tmp_path, "tests/a_test_video.py", "from pkg.shared import other\ndef test_video():\n    assert other(1) == 1\n")
    direct = "tests/z_test_scheduler.py"
    _write(tmp_path, direct, "from pkg.cron import schedule\ndef test_scheduling():\n    assert schedule(1) == 2\n")
    context = DepthContext(tmp_path, [source, "pkg/shared.py"])
    report = context.test_association(_feature([source]))
    assert report["matched_files"] == [direct, "tests/a_test_video.py"]
    data = context.build(_feature([source]), "", [], facets=["validation"], limit=180, evidence_round=evidence_round)
    assert "assert schedule(1) == 2" in _shown(data)
    assert data["files"][0]["path"] == direct


@pytest.mark.parametrize("exports", ["./src/api.mjs", {".": {"import": "./src/api.mjs", "require": "./src/api.cjs"}}])
def test_workspace_package_alias_cannot_certify_feature_test_absence(tmp_path, exports):
    import json

    source = "packages/client/src/api.mjs"
    _write(tmp_path, source, "export function send(value) { return value; }\n")
    _write(tmp_path, "packages/client/package.json", json.dumps({"name": "@acme/client", "exports": exports}))
    test = "tests/roundtrip.test.mjs"
    _write(tmp_path, test, "import {send} from '@acme/client';\nimport assert from 'node:assert';\n"
                         "test('roundtrip', () => { assert.equal(send(3), 3); });\n")
    report = DepthContext(tmp_path, [source]).test_association(_feature([source]))
    if isinstance(exports, str):
        assert report["matched_files"] == [test]
    else:
        assert not report["complete"]
        assert any("@acme/client" in problem for problem in report["unresolved_files"])
    assert report["matched_files"] or not report["complete"]
    from infermatrix_copilot.kb_service.knowledge_depth import build_absence_certificate
    policy = SimpleNamespace(roots=("packages/",), exclude=(), suffixes=(".mjs",), filenames=())
    assert build_absence_certificate(tmp_path, policy, _feature([source]), "a" * 40) is None


def test_unreadable_workspace_manifest_keeps_association_unknown(tmp_path):
    source = "packages/client/src/api.mjs"
    _write(tmp_path, source, "export function send(value) { return value; }\n")
    (tmp_path / "packages/client/package.json").write_bytes(b"\xff")
    _write(tmp_path, "tests/roundtrip.test.mjs", "import {send} from '@acme/client';\n"
                                             "test('roundtrip', () => { assert.equal(send(3), 3); });\n")
    report = DepthContext(tmp_path, [source]).test_association(_feature([source]))
    assert not report["complete"]
    assert any("package.json" in problem for problem in report["unresolved_files"])


@pytest.mark.parametrize("evidence_round", [0, 1, 2, 3])
def test_large_class_cannot_hide_a_late_named_setting(tmp_path, evidence_round):
    source = "pkg/controller.py"
    _write(tmp_path, source, "class Controller:\n" + "".join(
        f"    def configure_{i}(self, default={i}):\n        return default\n" for i in range(100))
        + "    def actual_connection(self, timeout=17):\n        return timeout\n")
    feature = _feature([source])
    feature.id = "connection"
    data = DepthContext(tmp_path, [source]).build(feature, "", [], facets=["configuration"],
                                               limit=300, evidence_round=evidence_round)
    assert "actual_connection(self, timeout=17)" in _shown(data)
    assert data["source_bytes"] <= 300


def test_archive_and_checkout_use_the_same_tracked_test_inventory(tmp_path):
    import shutil
    import subprocess

    checkout, archive = tmp_path / "checkout", tmp_path / "archive"
    source = "pkg/core.py"
    _write(checkout, source, "def send(value):\n    return value\n")
    for path in ["build/sdk/tests/test_roundtrip.py", "dist/tests/test_roundtrip.py"]:
        _write(checkout, path, "from pkg.core import send\ndef test_roundtrip():\n    assert send(3) == 3\n")
    subprocess.run(["git", "init", "-q", str(checkout)], check=True)
    subprocess.run(["git", "-C", str(checkout), "add", "."], check=True)
    shutil.copytree(checkout, archive, ignore=shutil.ignore_patterns(".git"))
    before = DepthContext(checkout, [source]).test_association(_feature([source]))
    after = DepthContext(archive, [source]).test_association(_feature([source]))
    assert before == after
    assert before["matched_files"] == ["build/sdk/tests/test_roundtrip.py", "dist/tests/test_roundtrip.py"]


@pytest.mark.parametrize("execution", [
    "subprocess.run([sys.executable, '-m', 'pkg.cli'], capture_output=True, text=True)",
    "runpy.run_module('pkg.cli', run_name='__main__')",
    "os.system('python -m pkg.cli')",
    "launch([sys.executable, '-m', 'pkg.cli'], capture_output=True, text=True)",
    "rp.run_module('pkg.cli', run_name='__main__')",
])
def test_external_python_execution_cannot_certify_no_feature_test(tmp_path, execution):
    from infermatrix_copilot.kb_service.knowledge_depth import build_absence_certificate

    source = "pkg/cli.py"
    _write(tmp_path, source, "def main():\n    print('ok')\nif __name__ == '__main__':\n    main()\n")
    _write(tmp_path, "tests/test_contract.py", "import subprocess, sys, runpy, os\nfrom subprocess import run as launch\nimport runpy as rp\n"
           + "def test_cli():\n    result = " + execution + "\n    assert result is not None\n")
    feature = _feature([source])
    report = DepthContext(tmp_path, [source]).test_association(feature)
    assert not report["complete"]
    assert report["unresolved_files"]
    policy = SimpleNamespace(roots=("pkg/",), exclude=(), suffixes=(".py",), filenames=())
    assert build_absence_certificate(tmp_path, policy, feature, "a" * 40) is None


@pytest.mark.parametrize("evidence_round", [0, 1, 4])
def test_large_generic_caller_cannot_crowd_out_feature_scope_or_flow_pair(tmp_path, evidence_round):
    from infermatrix_copilot.kb_service.knowledge_depth import verify_trace

    entry, helper, scoped = "pkg/cron.py", "pkg/cron_util.py", "pkg/cron_config.py"
    _write(tmp_path, entry, "from pkg.cron_util import finish\ndef schedule(value):\n    return finish(value)\n")
    _write(tmp_path, helper, "def finish(value):\n    return value + 1\n")
    _write(tmp_path, scoped, "TIMEOUT = 17\ndef configure(timeout=TIMEOUT):\n    return timeout\n")
    caller = "pkg/interface_deep.py"
    _write(tmp_path, caller, "from pkg.cron import schedule\ndef generic_stream():\n" + "".join(
        f"    config_{i} = 'default retry await request session cache return timeout'\n" for i in range(1000))
        + "    return schedule(1)\n")
    feature = _feature([entry, scoped])
    feature.id = "cron"
    data = DepthContext(tmp_path, [entry, helper, scoped, caller]).build(feature, "", [], limit=900,
                                                                     evidence_round=evidence_round)
    paths = {f["path"] for f in data["files"]}
    assert {entry, helper, scoped} <= paths
    assert "return finish(value)" in _shown(data) and "return value + 1" in _shown(data)
    assert "TIMEOUT = 17" in _shown(data)
    assert data["source_bytes"] <= 900
    trace = [{"path": entry, "symbol": "schedule", "start": 2, "end": 3},
             {"path": helper, "symbol": "finish", "start": 1, "end": 2}]
    assert all(any(f["path"] == s["path"] and f["start"] <= s["start"] <= s["end"] <= f["end"]
                   for f in data["files"]) for s in trace)
    verify_trace(tmp_path, trace)


@pytest.mark.parametrize("evidence_round", [0, 1, 4])
def test_padding_cannot_spend_file_quota_before_the_setting_signature(tmp_path, evidence_round):
    entry, settings = "pkg/entry.py", "pkg/settings.py"
    _write(tmp_path, entry, "def entry(value):\n    return value\n")
    _write(tmp_path, settings, "#\n" * 195 + ("# " + "0" * 100 + "\n") * 5
           + "def configure(timeout=17):\n    return timeout\n")
    data = DepthContext(tmp_path, [entry, settings]).build(_feature([entry, settings]), "", [],
             facets=["configuration"], limit=900, evidence_round=evidence_round)
    assert "def configure(timeout=17)" in _shown(data)
    assert "return timeout" in _shown(data)
    assert data["source_bytes"] <= 900


def test_long_owned_function_offers_late_default_assertion_before_padding(tmp_path):
    source = "pkg/transport.py"
    _write(tmp_path, source, "def configure_transport():\n" + "    value = 1\n" * 1000
           + "    timeout = 17\n    assert timeout > 0\n    return timeout\n")
    data = DepthContext(tmp_path, [source]).build(_feature([source]), "", [],
             facets=["configuration", "validation"], limit=600)
    shown = _shown(data)
    assert "def configure_transport()" in shown
    assert "timeout = 17" in shown
    assert "assert timeout > 0" in shown
    assert "return timeout" in shown
    assert data["source_bytes"] <= 600
