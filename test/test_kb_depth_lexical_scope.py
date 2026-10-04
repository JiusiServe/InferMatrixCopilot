"""Lexical call witnesses bind definitions and exclude deferred local bodies."""

import pytest

from infermatrix_copilot.kb_service.knowledge_depth import verify_trace


def _step(symbol, start, end=None, path="client.ts"):
    return {"symbol": symbol, "start": start, "end": end or start, "path": path}


def test_homonymous_class_method_cannot_impersonate_module_target(tmp_path):
    (tmp_path / "client.ts").write_text(
        "function helper() { return 1; }\n"
        "class Wrong {\n"
        "  helper() { return 2; }\n"
        "}\n"
        "function run() { return helper(); }\n"
    )
    with pytest.raises(ValueError, match="not a pinned module-level"):
        verify_trace(tmp_path, [_step("run", 5), _step("helper", 3)])
    verify_trace(tmp_path, [_step("run", 5), _step("helper", 1)])


def test_import_name_still_requires_correct_target_definition_span(tmp_path):
    (tmp_path / "client.ts").write_text(
        "import { helper as imported } from './helper';\n"
        "function run() { return imported(); }\n"
    )
    (tmp_path / "helper.ts").write_text(
        "export function helper() { return 1; }\n"
        "class Wrong { helper() { return 2; } }\n"
    )
    with pytest.raises(ValueError, match="not a pinned module-level"):
        verify_trace(tmp_path, [_step("run", 2), _step("helper", 2, path="helper.ts")])
    verify_trace(tmp_path, [_step("run", 2), _step("helper", 1, path="helper.ts")])


@pytest.mark.parametrize("nested", [
    "function neverCalled() { return helper(); }",
    "async function neverCalled() { return helper(); }",
    "class NeverConstructed { method() { return helper(); } }",
    "const unused = { method() { return helper(); } };",
    "const unused = () => helper();",
    "const unused = async () => { return helper(); };",
    "const unused = function () { return helper(); };",
])
def test_unexecuted_local_callable_body_cannot_witness_outer_call(tmp_path, nested):
    (tmp_path / "client.ts").write_text(
        "function helper() { return 1; }\n"
        "function run() {\n"
        f"  {nested}\n"
        "  return 2;\n"
        "}\n"
    )
    with pytest.raises(ValueError, match="does not show the next call"):
        verify_trace(tmp_path, [_step("run", 2, 5), _step("helper", 1)])


def test_actual_outer_call_survives_a_nested_unused_body(tmp_path):
    (tmp_path / "client.ts").write_text(
        "function helper() { return 1; }\n"
        "function run(enabled: boolean) {\n"
        "  function neverCalled() { return helper(); }\n"
        "  if (enabled) return helper();\n"
        "  return 2;\n"
        "}\n"
    )
    verify_trace(tmp_path, [_step("run", 2, 6), _step("helper", 1)])


def test_nested_named_binding_shadows_the_module_helper(tmp_path):
    (tmp_path / "client.ts").write_text(
        "function helper() { return 1; }\n"
        "function run() {\n"
        "  function helper() { return 2; }\n"
        "  return helper();\n"
        "}\n"
    )
    with pytest.raises(ValueError, match="does not show the next call"):
        verify_trace(tmp_path, [_step("run", 2, 5), _step("helper", 1)])


@pytest.mark.parametrize("binding", [
    "(1)\nconst other = () => 2",
    "(1); const other = () => 2",
    "(value)\nconst other = () => helper()",
    "() =>",
])
def test_initializer_cannot_borrow_later_arrow_or_omit_body(tmp_path, binding):
    (tmp_path / "client.ts").write_text(
        "function run() { return helper(); }\nconst helper = " + binding + ";\n"
    )
    with pytest.raises(ValueError, match="not declared"):
        verify_trace(tmp_path, [_step("run", 1), _step("helper", 2, 1 + len(binding.splitlines()))])


@pytest.mark.parametrize("binding", [
    "() => 1", "async (value) => value", "(value: number): number => value",
    "function () { return 1; }",
])
def test_valid_module_initializer_callable_still_binds(tmp_path, binding):
    (tmp_path / "client.ts").write_text(
        "function run() { return helper(); }\nconst helper = " + binding + ";\n"
    )
    verify_trace(tmp_path, [_step("run", 1), _step("helper", 2)])


def test_jsx_outside_the_reviewed_function_does_not_invalidate_its_binding(tmp_path):
    (tmp_path / "client.tsx").write_text(
        "function run() { return helper(); }\n"
        "function helper() { return 1; }\n"
        "function Component() { return <div />; }\n"
    )
    verify_trace(tmp_path, [_step("run", 1, path="client.tsx"), _step("helper", 2, path="client.tsx")])


def test_regex_contents_do_not_create_a_lexical_call_witness(tmp_path):
    (tmp_path / "client.ts").write_text(
        "function run() { const pattern = /helper()/; return 2; }\n"
        "function helper() { return 1; }\n"
    )
    with pytest.raises(ValueError, match="unresolved regex"):
        verify_trace(tmp_path, [_step("run", 1), _step("helper", 2)])


@pytest.mark.parametrize("body", [
    "    def helper():\n        return 2\n    return helper()\n",
    "    class helper:\n        pass\n    return helper()\n",
    "    from foreign import helper\n    return helper()\n",
    "    import foreign as helper\n    return helper()\n",
    "    try:\n        return 2\n    except Exception as helper:\n        return helper()\n",
    "    helper = lambda: 2\n    return helper()\n",
])
def test_python_local_binding_cannot_impersonate_module_helper(tmp_path, body):
    (tmp_path / "core.py").write_text("def helper():\n    return 1\ndef run():\n" + body)
    with pytest.raises(ValueError, match="does not call the next"):
        verify_trace(tmp_path, [_step("run", 3, 3 + len(body.splitlines()), "core.py"),
                                _step("helper", 1, 2, "core.py")])


@pytest.mark.parametrize("rebinding", ["helper = lambda: 2", "del helper", "from foreign import helper"])
def test_python_module_rebinding_invalidates_the_definition_target(tmp_path, rebinding):
    (tmp_path / "core.py").write_text(
        "def helper():\n    return 1\n" + rebinding + "\ndef run():\n    return helper()\n"
    )
    with pytest.raises(ValueError):
        verify_trace(tmp_path, [_step("run", 4, 5, "core.py"), _step("helper", 1, 2, "core.py")])


def test_python_definition_header_rebinding_invalidates_module_helper(tmp_path):
    (tmp_path / "core.py").write_text(
        "def helper():\n    return 1\ndef run(value=(helper := lambda: 2)):\n    return helper()\n"
    )
    with pytest.raises(ValueError):
        verify_trace(tmp_path, [_step("run", 3, 4, "core.py"), _step("helper", 1, 2, "core.py")])


@pytest.mark.parametrize("import_statement,call", [
    ("from helper import helper as known", "known()"),
    ("import helper as known", "known.helper()"),
])
def test_python_pinned_target_alias_stays_provable(tmp_path, import_statement, call):
    (tmp_path / "core.py").write_text(import_statement + "\ndef run():\n    return " + call + "\n")
    (tmp_path / "helper.py").write_text("def helper():\n    return 1\n")
    verify_trace(tmp_path, [_step("run", 2, 3, "core.py"), _step("helper", 1, 2, "helper.py")])


def test_python_foreign_local_import_cannot_reuse_a_target_module_alias(tmp_path):
    (tmp_path / "core.py").write_text(
        "from helper import helper as known\n"
        "def run():\n    from foreign import helper as known\n    return known()\n"
    )
    (tmp_path / "helper.py").write_text("def helper():\n    return 1\n")
    with pytest.raises(ValueError, match="does not call the next"):
        verify_trace(tmp_path, [_step("run", 2, 4, "core.py"), _step("helper", 1, 2, "helper.py")])


def test_python_local_target_alias_stays_provable(tmp_path):
    (tmp_path / "core.py").write_text("def run():\n    from helper import helper as known\n    return known()\n")
    (tmp_path / "helper.py").write_text("def helper():\n    return 1\n")
    verify_trace(tmp_path, [_step("run", 1, 3, "core.py"), _step("helper", 1, 2, "helper.py")])


def test_python_wildcard_import_cannot_leave_a_module_definition_provable(tmp_path):
    (tmp_path / "core.py").write_text(
        "def helper():\n    return 1\nfrom foreign import *\ndef run():\n    return helper()\n"
    )
    with pytest.raises(ValueError):
        verify_trace(tmp_path, [_step("run", 4, 5, "core.py"), _step("helper", 1, 2, "core.py")])


@pytest.mark.parametrize("pattern", ["helper", "[ *helper ]", "{ 'key': value, **helper }"])
def test_python_match_capture_shadows_module_definition(tmp_path, pattern):
    (tmp_path / "core.py").write_text(
        "def helper():\n    return 1\ndef run(value):\n    match value:\n        case "
        + pattern + ":\n            return helper()\n"
    )
    with pytest.raises(ValueError, match="does not call the next"):
        verify_trace(tmp_path, [_step("run", 3, 6, "core.py"), _step("helper", 1, 2, "core.py")])


def test_python_lambda_default_runs_in_the_enclosing_binding_scope(tmp_path):
    (tmp_path / "core.py").write_text(
        "def helper():\n    return 1\ndef run(other):\n"
        "    callback = lambda value=(helper := other): None\n    return helper()\n"
    )
    with pytest.raises(ValueError, match="does not call the next"):
        verify_trace(tmp_path, [_step("run", 3, 5, "core.py"), _step("helper", 1, 2, "core.py")])


@pytest.mark.parametrize("write", ["helper = () => 2;", "helper &&= other;", "helper++;",
                                   "[helper] = others;", "({ helper } = other);"])
@pytest.mark.parametrize("scope", ["module", "local"])
def test_client_direct_name_writes_invalidate_the_old_callable_binding(tmp_path, write, scope):
    body = (write + "\nfunction run() { return helper(); }\n") if scope == "module" else (
        "function run() { " + write + " return helper(); }\n")
    (tmp_path / "client.ts").write_text("function helper() { return 1; }\n" + body)
    with pytest.raises(ValueError):
        verify_trace(tmp_path, [_step("run", 3 if scope == "module" else 2), _step("helper", 1)])


def _python_helper(tree, path, value):
    target = tree / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("def helper():\n    return " + str(value) + "\n")


def test_root_absolute_import_cannot_bind_to_a_nested_sdk_copy(tmp_path):
    _python_helper(tmp_path, "pkg/helper.py", 1)
    _python_helper(tmp_path, "packages/sdk/pkg/helper.py", 2)
    (tmp_path / "pkg/__init__.py").write_text("")
    (tmp_path / "caller.py").write_text("from pkg.helper import helper\ndef run():\n    return helper()\n")
    with pytest.raises(ValueError, match="does not call the next"):
        verify_trace(tmp_path, [_step("run", 2, 3, "caller.py"),
                                _step("helper", 1, 2, "packages/sdk/pkg/helper.py")])
    verify_trace(tmp_path, [_step("run", 2, 3, "caller.py"), _step("helper", 1, 2, "pkg/helper.py")])


def test_unique_nested_sdk_absolute_import_remains_provable(tmp_path):
    _python_helper(tmp_path, "packages/sdk/pkg/helper.py", 2)
    (tmp_path / "caller.py").write_text("from pkg.helper import helper\ndef run():\n    return helper()\n")
    verify_trace(tmp_path, [_step("run", 2, 3, "caller.py"),
                            _step("helper", 1, 2, "packages/sdk/pkg/helper.py")])


def test_multiple_nested_absolute_module_candidates_are_unknown(tmp_path):
    _python_helper(tmp_path, "packages/sdk/pkg/helper.py", 2)
    _python_helper(tmp_path, "packages/other/pkg/helper.py", 3)
    (tmp_path / "caller.py").write_text("from pkg.helper import helper\ndef run():\n    return helper()\n")
    with pytest.raises(ValueError, match="does not call the next"):
        verify_trace(tmp_path, [_step("run", 2, 3, "caller.py"),
                                _step("helper", 1, 2, "packages/sdk/pkg/helper.py")])


def test_relative_import_uses_caller_package_without_suffix_fallback(tmp_path):
    _python_helper(tmp_path, "src/pkg/helper.py", 1)
    _python_helper(tmp_path, "packages/sdk/pkg/helper.py", 2)
    (tmp_path / "src/pkg/caller.py").write_text("from .helper import helper\ndef run():\n    return helper()\n")
    verify_trace(tmp_path, [_step("run", 2, 3, "src/pkg/caller.py"),
                            _step("helper", 1, 2, "src/pkg/helper.py")])
    (tmp_path / "src/pkg/helper.py").unlink()
    with pytest.raises(ValueError, match="does not call the next"):
        verify_trace(tmp_path, [_step("run", 2, 3, "src/pkg/caller.py"),
                                _step("helper", 1, 2, "packages/sdk/pkg/helper.py")])


@pytest.mark.parametrize("receiver,write", [
    ("self", "self.helper = lambda: 2"),
    ("self", "del self.helper"),
    ("self", "self.helper += other"),
    ("cls", "cls.helper = lambda: 2"),
])
def test_explicit_method_attribute_write_invalidates_its_definition_binding(tmp_path, receiver, write):
    (tmp_path / "core.py").write_text(
        "class Owner:\n    def helper(self):\n        return 1\n"
        f"    def caller({receiver}):\n        {write}\n        return {receiver}.helper()\n"
    )
    with pytest.raises(ValueError, match="does not call the next"):
        verify_trace(tmp_path, [_step("Owner.caller", 4, 6, "core.py"),
                                _step("Owner.helper", 2, 3, "core.py")])


def test_unrelated_attribute_write_keeps_a_known_method_binding(tmp_path):
    (tmp_path / "core.py").write_text(
        "class Owner:\n    def helper(self):\n        return 1\n"
        "    def caller(self):\n        self.unrelated = lambda: 2\n        return self.helper()\n"
    )
    verify_trace(tmp_path, [_step("Owner.caller", 4, 6, "core.py"), _step("Owner.helper", 2, 3, "core.py")])
