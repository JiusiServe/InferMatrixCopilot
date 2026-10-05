"""Bounded, pinned implementation evidence for subscription module cards."""
from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace

import pytest

from infermatrix_copilot.kb_service.init_modules import (
    MAX_CARD_BYTES, SYSTEM_CARD, SYSTEM_CARD_IMPL, _implementation_payload, _Modules,
)
from infermatrix_copilot.kb_service.init_stages import _fence, run_stage
from infermatrix_copilot.kb_service.models import ModelRole
from test_kb_init_modules import CardGateway, _modules_lifecycle, _skeleton, _world_with_tools
from test_kb_init_skeleton import _commit, _runtime, world  # noqa: F401

PIN = "a" * 40


def _index(files):
    return SimpleNamespace(identity={"pin": PIN}, entries={
        path: {"status": "ready", "lines": text.splitlines(), "text": text,
               "sha256": hashlib.sha256(text.encode()).hexdigest()} for path, text in files.items()})


def _payload(paths):
    return {"files": [{"path": path} for path in paths], "doc_files": [], "groups": {}}


def test_complete_evidence_includes_late_runtime_and_conditional_defaults():
    files = {"scripts/bridge.js": "#!/usr/bin/env node\n" + "// comment\n" * 190
             + "new WebSocketServer({port:19600});\n",
             "scripts/teardown.sh": "STOP_SERVICE=0\nDISABLE_SERVICE=0\n"
             "if [ \"$STOP_SERVICE\" = 1 ]; then systemctl stop nfs; fi\n"
             "echo 'Manually run hvigorw build'\n"}
    output = _implementation_payload(_payload(files), _index(files), PIN)
    assert output["source_pin"] == PIN
    for item in output["source_evidence"]:
        assert item["status"] == "complete"
        assert item["sha256"] == hashlib.sha256(files[item["path"]].encode()).hexdigest()
        shown = item["ranges"][0]
        assert (shown["start"], shown["end"]) == (1, len(files[item["path"]].splitlines()))
        assert shown["text"] == "\n".join(f"{n}: {line}" for n, line in
                                              enumerate(files[item["path"]].splitlines(), 1))
    assert "new WebSocketServer" in output["source_evidence"][0]["ranges"][0]["text"]


def test_capped_multibyte_evidence_is_fair_numbered_and_explicitly_partial():
    files = {"scripts/large.js": "\n".join(f"const 中文{n} = '<value>';" for n in range(5000)),
             "scripts/small.js": "runtime_optional_bridge();\n"}
    output = _implementation_payload(_payload(files), _index(files), PIN)
    assert len(_fence(output).encode()) <= MAX_CARD_BYTES
    large, small = output["source_evidence"]
    assert large["status"] == "partial" and large["total_lines"] == 5000
    assert large["ranges"][0]["start"] == 1
    assert large["ranges"][-1]["end"] == 5000
    assert large["ranges"][0]["end"] < large["ranges"][-1]["start"]
    assert small["status"] == "complete"  # large first file cannot starve a later small file
    for shown in large["ranges"]:
        lines = files[large["path"]].splitlines()
        assert shown["text"] == "\n".join(f"{n}: {lines[n - 1]}" for n in
                                              range(shown["start"], shown["end"] + 1))


def test_failed_or_missing_indexed_source_stays_unknown_without_replacement_text():
    index = _index({})
    index.entries["bad.js"] = {"status": "read_failed", "text": "invalid replacement text"}
    output = _implementation_payload(_payload(["bad.js", "missing.js"]), index, PIN)
    assert all(item["status"] == "unknown" and not item["ranges"] for item in output["source_evidence"])
    assert "invalid replacement text" not in json.dumps(output)


def test_metadata_cap_and_pinned_index_identity_fail_closed():
    with pytest.raises(ValueError, match="byte cap"):
        _implementation_payload({**_payload([]), "doc_files": ["x" * MAX_CARD_BYTES]}, _index({}), PIN)
    with pytest.raises(ValueError, match="fixed source SHA"):
        _implementation_payload(_payload([]), _index({}), "b" * 40)


def test_unlimited_prompt_identity_and_instructions_leave_legacy_unchanged():
    assert _Modules._input_options(SimpleNamespace(rt=SimpleNamespace(unlimited_subscription=False))) == {}
    assert _Modules._input_options(SimpleNamespace(rt=SimpleNamespace(unlimited_subscription=True))) == {
        "module_prompt_version": 2}
    assert "never the full code" in SYSTEM_CARD and "source_pin" not in SYSTEM_CARD
    assert "never the full code" not in SYSTEM_CARD_IMPL
    assert all(text in SYSTEM_CARD_IMPL for text in
               ("default side effects", "printed/manual", "Unshown behavior remains unknown", "steps as executed"))


class ImplementationGateway(CardGateway):
    def subscription_billing(self, role):
        return True

    def call_json(self, role, *, system, prompt, **kwargs):
        reply = super().call_json(role, system=SYSTEM_CARD if system == SYSTEM_CARD_IMPL else system,
                                  prompt=prompt, **kwargs)
        if system == SYSTEM_CARD_IMPL:
            self.calls[-1]["system"] = system
        return reply


def test_official_unlimited_modules_use_actual_pinned_source_bodies(world):
    _world_with_tools(world)
    source = "def secret():\n    return optional_runtime_service()\n" + "\n".join(
        f"def another_{n}(): pass" for n in range(8)) + "\n"
    _commit(world["upstream"], {"tools/lint/runtime.py": source}, "runtime helper")
    _skeleton(world)
    gateway = ImplementationGateway()
    record = run_stage(_runtime(world, gateway, generator=ModelRole("generator", "zcode", "GLM-5.3")),
                       _modules_lifecycle(), "modules", dry_run=True, unlimited_subscription=True)
    assert record.status == "dry_run", record.problems
    calls = [call for call in gateway.calls if call["system"] == SYSTEM_CARD_IMPL]
    assert calls and all(len(call["prompt"].encode()) <= MAX_CARD_BYTES for call in calls)
    payloads = [json.loads(call["prompt"].split("\n", 1)[1].rsplit("</untrusted_data>", 1)[0]) for call in calls]
    item = next(item for payload in payloads for item in payload["source_evidence"]
                if item["path"] == "tools/lint/runtime.py")
    assert item["status"] == "complete" and item["sha256"] == hashlib.sha256(source.encode()).hexdigest()
    assert "2:     return optional_runtime_service()" in item["ranges"][0]["text"]
    assert all(payload["source_pin"] == record.pin for payload in payloads)
    assert all(len(file.get("signatures", [])) <= 4 for payload in payloads for file in payload["files"])


def test_unlimited_card_cannot_name_a_module_file_outside_its_offered_subset(world, monkeypatch):
    import infermatrix_copilot.kb_service.init_modules as modules
    monkeypatch.setattr(modules, "MAX_CARD_FILES", 1)
    _world_with_tools(world)
    _commit(world["upstream"], {"tools/lint/a.py": "def first(): pass\n"}, "another lint file")
    _skeleton(world)

    class UnofferedGateway(ImplementationGateway):
        def call_json(self, role, *, system, prompt, **kwargs):
            reply = super().call_json(role, system=system, prompt=prompt, **kwargs)
            if system == SYSTEM_CARD_IMPL and '"module": "tools/lint/"' in prompt:
                reply.data["key_files"] = [{"path": "tools/lint/y.py", "what": "unsupported unseen file"}]
            return reply

    record = run_stage(_runtime(world, UnofferedGateway(),
                                generator=ModelRole("generator", "zcode", "GLM-5.3")),
                       _modules_lifecycle(), "modules", dry_run=True, unlimited_subscription=True)
    assert record.status == "dry_run", record.problems
    assert any("key_files 'tools/lint/y.py' is not offered" in note for note in record.notes)
