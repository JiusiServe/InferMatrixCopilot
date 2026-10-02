"""Only actual archived three-yes judgments may bind current depth prose."""

import gzip
import hashlib
import json
from types import SimpleNamespace

import pytest
import yaml

from infermatrix_copilot.kb_service.knowledge_coverage import load_policy
from infermatrix_copilot.kb_service.knowledge_depth import build_absence_certificate, render_block
from infermatrix_copilot.trace_store import TraceStore
from tools.audit_native_depth_approvals import audit_native_approvals, main

YES = {"faithful": "yes", "non_contradictory": "yes", "does_not_weaken": "yes"}
PIN = "a" * 40
PAGE = "repos/toy/components/core/feature-depth-settings.md"


def _hash(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _fence(data):
    return "<untrusted_data>\n" + json.dumps(data) + "\n</untrusted_data>"


@pytest.fixture
def native(tmp_path):
    root = tmp_path / "checkout"
    adapter = root / "adapters/toy"
    adapter.mkdir(parents=True)
    (adapter / "manifest.yaml").write_text(yaml.safe_dump({
        "repo": {"full_name": "o/toy"}, "knowledge": {"repo_subdir": "repos/toy"}}))
    feature = {"id": "settings", "title": "Settings", "owner": "core", "source_globs": ["pkg/core.py"],
               "docs": ["docs.md"], "entry_points": ["pkg/core.py"],
               "page": "repos/toy/components/core/feature-settings.md"}
    (adapter / "knowledge-coverage.yaml").write_text(yaml.safe_dump({
        "schema_version": 1, "core": {"roots": ["pkg/"], "exclude": ["*/tests/*"]}, "features": [feature]}))
    upstream = tmp_path / "source"
    (upstream / "pkg").mkdir(parents=True)
    (upstream / "pkg/core.py").write_text("DEFAULT_RETRIES = 3\n")
    section = {"facet": "configuration", "title": "Retry default", "body": "The retry default is three.",
               "interpretation": "fact", "evidence": [{"path": "pkg/core.py", "start": 1, "end": 1}]}
    block = render_block(SimpleNamespace(id="settings"), section, upstream, "o/toy", PIN)
    page = root / "knowledge" / PAGE
    page.parent.mkdir(parents=True)
    page.write_text(block + "\n")
    store = TraceStore(tmp_path / "traces", environ={})
    generator = store.append("model_call", model={"role": "generator", "provider": "zcode",
                             "model": "GLM-5.3", "served_model": "GLM-5.3"},
                             inputs={"prompt": _fence({"feature": {"id": "settings"}, "pin": PIN})},
                             outputs={"reply": json.dumps({"sections": [section]})})
    prose = "\n".join(block.splitlines()[1:-1]).split("<!-- kb:depth-proof", 1)[0].strip()
    prompt = {"feature": "settings", "pin": PIN, "sections": {"configuration": prose},
              "evidence": [{"source_reference": f"o/toy@{PIN}:pkg/core.py:L1-L1", "kind": "upstream_text",
                            "text": ["1: DEFAULT_RETRIES = 3"]}]}
    reply = {"facets": {"configuration": {"dimensions": dict(YES), "reason": "Source lines checked"}}}
    judge = store.append("model_call", model={"role": "judge", "provider": "codex", "model": "gpt-6-sol",
                         "served_model": ""}, inputs={"prompt": _fence(prompt)}, outputs={"reply": json.dumps(reply)})
    row = {"feature": "settings", "facet": "configuration", "page": PAGE, "block_sha256": _hash(block),
           "native_trace_id": judge["id"], "native_reply_sha256": judge["outputs"]["reply"].removeprefix("sha256:")}
    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps({"native_execution": {"approvals": [row]}}))
    return {"root": root, "upstream": upstream, "section": section, "page": page, "block": block,
            "store": store, "generator": generator, "judge": judge, "prompt": prompt,
            "reply": reply, "row": row, "baseline": baseline}


def _audit(native, *, baselines=None, checkpoints=None, archives=None):
    return audit_native_approvals(native["root"], "toy",
                                  baseline_reports=baselines if baselines is not None else [native["baseline"]],
                                  checkpoints=checkpoints or [],
                                  trace_dirs=archives if archives is not None else [native["store"].root])


def _replace_record(native, record, **fields):
    path = next((native["store"].root / "records").glob("*.jsonl"))
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows = [{**row, **fields} if row["id"] == record["id"] else row for row in rows]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


def _replace_reply(native, reply):
    ref = native["store"].put_blob(json.dumps(reply))
    _replace_record(native, native["judge"], outputs={"reply": ref})
    native["row"]["native_reply_sha256"] = ref.removeprefix("sha256:")
    native["baseline"].write_text(json.dumps({"approvals": [native["row"]]}))


def _replace_prompt(native, prompt):
    ref = native["store"].put_blob(_fence(prompt))
    _replace_record(native, native["judge"], inputs={"prompt": ref})


def test_legacy_dimensions_are_read_from_native_blobs_and_archives_are_read_only(native):
    index = native["store"].root / "index.db"
    before = index.read_bytes()
    report = _audit(native)
    assert report["problems"] == [] and len(report["approvals"]) == 1
    row = report["approvals"][0]
    assert row["dimensions"] == YES and row["pin"] == PIN
    assert row["model"]["served_model"] == ""  # never invent an unreported served identity
    assert row["native_generator_trace_id"] == native["generator"]["id"]
    assert index.read_bytes() == before
    assert report["provenance"]["trace_archives"][0]["archive_sha256"]
    assert "Source lines checked" not in json.dumps(report)


def test_new_checkpoint_pass_receipts_are_verified_against_actual_native_judgment(native, tmp_path):
    checkpoint = tmp_path / "checkpoint.json"
    result = {**native["row"], "verdict": "pass", "dimensions": dict(YES)}
    checkpoint.write_text(json.dumps({"pin": PIN, "verdicts": {"depth:settings": {"facets": {"configuration": result}}}}))
    report = _audit(native, baselines=[], checkpoints=[checkpoint])
    assert report["problems"] == [] and len(report["approvals"]) == 1


@pytest.mark.parametrize("dimensions", [
    {**YES, "faithful": "no"}, {**YES, "faithful": "unsure"},
    {"faithful": "yes"}, {**YES, "extra": "yes"},
])
def test_all_yes_in_receipt_cannot_override_actual_native_dimensions(native, dimensions):
    native["row"]["dimensions"] = dict(YES)
    reply = {"facets": {"configuration": {"dimensions": dimensions, "reason": "Native review result"}}}
    _replace_reply(native, reply)
    report = _audit(native)
    assert not report["approvals"] and any("three yes" in issue for issue in report["problems"])


@pytest.mark.parametrize("field, value", [("feature", "other"), ("pin", "b" * 40),
                                         ("sections", {"configuration": "A different paragraph"})])
def test_native_prompt_must_bind_current_feature_pin_and_exact_prose(native, field, value):
    ref = native["store"].put_blob(_fence({**native["prompt"], field: value}))
    _replace_record(native, native["judge"], inputs={"prompt": ref})
    report = _audit(native)
    assert not report["approvals"] and any("exact current facet prose and pin" in issue for issue in report["problems"])


def test_editing_prose_and_updating_receipt_hash_still_needs_a_new_native_judgment(native):
    block = render_block(SimpleNamespace(id="settings"), {**native["section"], "body": "A changed retry claim."},
                         native["upstream"], "o/toy", PIN)
    native["page"].write_text(block + "\n")
    native["row"]["block_sha256"] = _hash(block)
    native["baseline"].write_text(json.dumps({"approvals": [native["row"]]}))
    assert any("exact current facet prose" in issue for issue in _audit(native)["problems"])


@pytest.mark.parametrize("change", ["missing", "empty", "wrong_text", "wrong_reference", "wrong_pin",
                                    "wrong_repository", "wrong_number", "missing_line", "conflicting_line"])
def test_actual_judged_evidence_must_bind_the_current_source_proof(native, change):
    prompt = json.loads(json.dumps(native["prompt"]))
    item = prompt["evidence"][0]
    if change == "missing":
        prompt.pop("evidence")
    elif change == "empty":
        prompt["evidence"] = []
    elif change == "wrong_text":
        item["text"] = ["1: DEFAULT_RETRIES = 9"]
    elif change == "wrong_reference":
        item["source_reference"] = f"o/toy@{PIN}:pkg/other.py:L1-L1"
    elif change == "wrong_pin":
        item["source_reference"] = "o/toy@" + "b" * 40 + ":pkg/core.py:L1-L1"
    elif change == "wrong_repository":
        item["source_reference"] = f"another/repo@{PIN}:pkg/core.py:L1-L1"
    elif change == "wrong_number":
        item["text"] = ["2: DEFAULT_RETRIES = 3"]
    elif change == "missing_line":
        item["source_reference"] = f"o/toy@{PIN}:pkg/core.py:L1-L2"
    else:
        prompt["evidence"].append({**item, "text": ["1: DEFAULT_RETRIES = 9"]})
    _replace_prompt(native, prompt)
    report = _audit(native)
    assert not report["approvals"] and report["problems"]


@pytest.mark.parametrize("context", ["merged", "unterminated"])
def test_merged_judged_source_spans_and_no_final_newline_keep_exact_bindings(native, context):
    source = native["upstream"] / "pkg/core.py"
    source.write_text("DEFAULT_RETRIES = 3\n\ndef configure(): return DEFAULT_RETRIES\n" if context == "merged"
                      else "DEFAULT_RETRIES = 3")
    block = render_block(SimpleNamespace(id="settings"), native["section"], native["upstream"], "o/toy", PIN)
    native["page"].write_text(block + "\n")
    native["row"]["block_sha256"] = _hash(block)
    native["baseline"].write_text(json.dumps({"approvals": [native["row"]]}))
    prompt = json.loads(json.dumps(native["prompt"]))
    if context == "merged":
        prompt["evidence"][0].update(source_reference=f"o/toy@{PIN}:pkg/core.py:L1-L3",
                                    text=["1: DEFAULT_RETRIES = 3", "2: ", "3: def configure(): return DEFAULT_RETRIES"])
    _replace_prompt(native, prompt)
    assert _audit(native)["problems"] == []


@pytest.mark.parametrize("change", ["none", "missing", "changed", "duplicate"])
def test_verified_absence_needs_the_exact_certificate_in_the_native_judged_packet(native, change):
    (native["upstream"] / "docs.md").write_text("Settings documentation.\n")
    policy = load_policy((native["root"] / "adapters/toy/knowledge-coverage.yaml").read_text(), "repos/toy")
    feature = policy.features[0]
    certificate = build_absence_certificate(native["upstream"], policy, feature, PIN)
    assert certificate is not None
    section = {**native["section"], "facet": "validation", "basis": "verified_absent",
               "absence_certificate": certificate, "title": "Static test gap",
               "body": "No statically associated test entry; external or dynamic tests remain unknown."}
    block = render_block(feature, section, native["upstream"], "o/toy", PIN, policy=policy)
    native["page"].write_text(block + "\n")
    native["row"].update(facet="validation", block_sha256=_hash(block))
    prose = "\n".join(block.splitlines()[1:-1]).split("<!-- kb:depth-proof", 1)[0].strip()
    packet = {"kind": "replayed_absence_certificate", "certificate": dict(certificate)}
    evidence = json.loads(json.dumps(native["prompt"]["evidence"]))
    if change != "missing":
        evidence.append(packet)
    if change == "changed":
        packet["certificate"]["test_inventory_sha256"] = "0" * 64
    elif change == "duplicate":
        evidence.append(packet)
    _replace_prompt(native, {**native["prompt"], "sections": {"validation": prose}, "evidence": evidence})
    _replace_reply(native, {"facets": {"validation": {"dimensions": dict(YES), "reason": "Bounded gap checked"}}})
    report = _audit(native)
    if change == "none":
        assert not report["problems"] and len(report["approvals"]) == 1
    else:
        assert not report["approvals"] and any("absence certificate" in issue for issue in report["problems"])


@pytest.mark.parametrize("change", ["wrong_hash", "missing_trace", "generator_trace", "judge_error", "judge_api"])
def test_missing_or_misidentified_native_receipts_fail_closed(native, change):
    if change == "wrong_hash":
        native["row"]["native_reply_sha256"] = "0" * 64
    elif change == "missing_trace":
        native["row"]["native_trace_id"] = "missing"
    elif change == "generator_trace":
        native["row"]["native_trace_id"] = native["generator"]["id"]
    elif change == "judge_error":
        _replace_record(native, native["judge"], error="native call failed")
    else:
        _replace_record(native, native["judge"], model={**native["judge"]["model"], "provider": "api"})
    native["baseline"].write_text(json.dumps({"approvals": [native["row"]]}))
    report = _audit(native)
    assert not report["approvals"] and report["problems"]


def test_corrupt_reply_blob_does_not_count_as_approval(native):
    digest = native["row"]["native_reply_sha256"]
    path = native["store"].root / "blobs" / digest[:2] / (digest + ".gz")
    path.write_bytes(gzip.compress(b"{}"))
    report = _audit(native)
    assert not report["approvals"] and any("corrupt" in issue for issue in report["problems"])


def test_judge_requires_an_independent_successful_generator_context(native):
    _replace_record(native, native["generator"], model={**native["generator"]["model"],
                                                     "model": "gpt-6-mini", "served_model": "gpt-6-mini"})
    report = _audit(native)
    assert not report["approvals"] and any("independently identified" in issue for issue in report["problems"])


@pytest.mark.parametrize("served", ["claude-opus-5", "GLM-5.3", "gemini-3-pro", {"model": "gpt-6-sol"}, {}, []])
def test_explicit_incompatible_judge_served_identity_is_not_a_codex_approval(native, served):
    _replace_record(native, native["judge"], model={**native["judge"]["model"], "served_model": served})
    report = _audit(native)
    assert not report["approvals"] and any("incompatible Codex" in issue for issue in report["problems"])


@pytest.mark.parametrize("served", ["gpt-6.1-sol", "codex-mini-latest", "o3"])
def test_compatible_explicit_codex_served_identity_is_retained(native, served):
    _replace_record(native, native["judge"], model={**native["judge"]["model"], "served_model": served})
    report = _audit(native)
    assert not report["problems"] and report["approvals"][0]["model"]["served_model"] == served


def test_judge_without_successful_prior_generator_is_not_an_independent_approval(native):
    _replace_record(native, native["generator"], error="generation did not succeed")
    report = _audit(native)
    assert not report["approvals"] and any("no successful native generator" in issue for issue in report["problems"])


def test_schema_partial_native_reply_does_not_become_a_valid_receipt(native):
    prompt = {**native["prompt"], "sections": {**native["prompt"]["sections"], "api": "A second facet"}}
    ref = native["store"].put_blob(_fence(prompt))
    _replace_record(native, native["judge"], inputs={"prompt": ref})
    report = _audit(native)
    assert not report["approvals"] and any("complete judged packet" in issue for issue in report["problems"])


@pytest.mark.parametrize("duplicate", ["receipt", "current_block", "trace"])
def test_duplicate_bindings_are_not_silently_counted(native, duplicate):
    if duplicate == "receipt":
        native["baseline"].write_text(json.dumps({"approvals": [native["row"], native["row"]]}))
    elif duplicate == "current_block":
        native["page"].write_text(native["block"] + "\n" + native["block"])
    else:
        path = next((native["store"].root / "records").glob("*.jsonl"))
        with path.open("a") as handle:
            handle.write(json.dumps(native["judge"]) + "\n")
    report = _audit(native)
    assert not report["approvals"] and any("duplicate" in issue for issue in report["problems"])


def test_cli_exports_only_normalized_receipts_and_refuses_knowledge_destination(native, tmp_path, capsys):
    report_path = tmp_path / "verified.json"
    args = ["--root", str(native["root"]), "--repo", "toy", "--baseline-report", str(native["baseline"]),
            "--trace-dir", str(native["store"].root)]
    assert main(args + ["--report", str(report_path)]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["report_sha256"] == hashlib.sha256(report_path.read_bytes()).hexdigest()
    assert len(json.loads(report_path.read_text())["approvals"]) == 1
    with pytest.raises(SystemExit) as exc:
        main(args + ["--report", str(native["root"] / "knowledge" / "report.json")])
    assert exc.value.code == 2


def _lightweight(native, section=None):
    section = section or native["section"]
    block = render_block(SimpleNamespace(id="settings"), section, native["upstream"], "o/toy", PIN,
                         acceptance_mode="lightweight")
    native["page"].write_text(block + "\n")
    native["row"].update(facet=section["facet"], block_sha256=_hash(block), acceptance_mode="lightweight")
    if "validation_kind" in section:
        native["row"]["validation_kind"] = section["validation_kind"]
    data = {"repository": "o/toy", "pin": PIN, "feature": {"id": "settings"},
            "acceptance_mode": "lightweight", "facets": [section["facet"]], "files": [], "docs": []}
    judged = []
    for e in section["evidence"]:
        lines = (native["upstream"] / e["path"]).read_text().splitlines()[e["start"] - 1:e["end"]]
        numbered = [f"{n}: {line}" for n, line in enumerate(lines, e["start"])]
        kind = "docs" if e["path"].endswith(".md") else "files"
        data[kind].append({**e, "text": lines if kind == "docs" else numbered})
        judged.append({"source_reference": f"o/toy@{PIN}:{e['path']}:L{e['start']}-L{e['end']}",
                       "kind": "upstream_text", "text": numbered})
    _replace_record(native, native["generator"], inputs={"prompt": native["store"].put_blob(_fence(data))},
                    outputs={"reply": native["store"].put_blob(json.dumps({"sections": [section]}))})
    packet = {**native["prompt"], "sections": {section["facet"]:
        "\n".join(block.splitlines()[1:-1]).split("<!-- kb:depth-proof", 1)[0].strip()},
        "acceptance_modes": {section["facet"]: "lightweight"}, "evidence": judged,
        "validation_kinds": {section["facet"]: section["validation_kind"]} if "validation_kind" in section else {}}
    _replace_prompt(native, packet)
    _replace_reply(native, {"facets": {section["facet"]: {"dimensions": dict(YES), "reason": "Shown evidence checked"}}})
    return section, data


def _replace_generation(native, *, data=None, sections=None, raw_reply=None):
    fields = {}
    if data is not None:
        fields["inputs"] = {"prompt": native["store"].put_blob(_fence(data))}
    if sections is not None or raw_reply is not None:
        fields["outputs"] = {"reply": native["store"].put_blob(raw_reply if raw_reply is not None else json.dumps({"sections": sections}))}
    _replace_record(native, native["generator"], **fields)


@pytest.mark.parametrize("interpretation", ["fact", "inference"])
def test_lightweight_native_draft_binds_host_title_body_and_inference_transform(native, interpretation):
    section, _ = _lightweight(native, {**native["section"], "title": " # Retry   default # ",
                                    "interpretation": interpretation})
    _replace_generation(native, raw_reply="```json\n" + json.dumps({"sections": [section]}) + "\n```")
    report = _audit(native)
    assert not report["problems"] and len(report["approvals"]) == 1
    assert report["approvals"][0]["native_generator_trace_id"] == native["generator"]["id"]


@pytest.mark.parametrize("change", ["unrelated_facet", "title", "body", "interpretation", "evidence", "duplicate"])
def test_lightweight_three_yes_cannot_override_a_different_actual_generator_draft(native, change):
    section, _ = _lightweight(native)
    changed = {**section, "evidence": [dict(item) for item in section["evidence"]]}
    if change == "unrelated_facet":
        changed["facet"] = "api"
    elif change in ("title", "body"):
        changed[change] = "An unrelated generated claim"
    elif change == "interpretation":
        changed["interpretation"] = "inference"
    elif change == "evidence":
        changed["evidence"][0]["path"] = "pkg/another.py"
    _replace_generation(native, sections=[changed, changed] if change == "duplicate" else [changed])
    report = _audit(native)
    assert not report["approvals"] and any("exact successful Zcode" in p for p in report["problems"])


@pytest.mark.parametrize("change", ["repository", "feature", "pin", "acceptance_mode", "facets", "missing",
                                     "wrong_number", "wrong_text", "unshown"])
def test_lightweight_draft_binds_actual_extraction_context_and_shown_source(native, change):
    _, data = _lightweight(native)
    if change == "repository":
        data["repository"] = "other/toy"
    elif change == "feature":
        data["feature"] = {"id": "other"}
    elif change == "pin":
        data["pin"] = "b" * 40
    elif change == "acceptance_mode":
        data["acceptance_mode"] = "strict"
    elif change == "facets":
        data["facets"] = ["api"]
    elif change == "missing":
        data["files"] = []
    elif change == "wrong_number":
        data["files"][0]["text"] = ["2: DEFAULT_RETRIES = 3"]
    elif change == "wrong_text":
        data["files"][0]["text"] = ["1: DEFAULT_RETRIES = 9"]
    else:
        data["files"][0].update(start=2, end=2, text=["2: DEFAULT_RETRIES = 3"])
    _replace_generation(native, data=data)
    report = _audit(native)
    assert not report["approvals"] and report["problems"]


@pytest.mark.parametrize("change", ["provider", "requested_model", "served_model", "model_fallback", "result_fallback"])
def test_lightweight_generator_requires_native_zcode_glm53_without_fallback(native, change):
    _lightweight(native)
    model = dict(native["generator"]["model"])
    fields = {"model": model}
    if change == "provider":
        model.update(provider="claude", model="claude-opus-5", served_model="claude-opus-5")
    elif change == "requested_model":
        model["model"] = "GLM-5.3-Flash"
    elif change == "served_model":
        model["served_model"] = "GLM-5.3-Flash"
    elif change == "model_fallback":
        model["fallback_from"] = "zcode:glm-5.3"
    else:
        fields["result"] = {"fallback_from": "zcode:glm-5.3"}
    _replace_record(native, native["generator"], **fields)
    report = _audit(native)
    assert not report["approvals"] and any("exact successful Zcode" in p for p in report["problems"])


def test_lightweight_unreported_generator_served_model_stays_unknown(native):
    _lightweight(native)
    _replace_record(native, native["generator"], model={**native["generator"]["model"], "served_model": ""})
    report = _audit(native)
    assert not report["problems"] and report["approvals"][0]["generator_model"]["served_model"] == ""


@pytest.mark.parametrize("kind", ["documented_manual", "helper_unit"])
def test_lightweight_validation_kind_and_manual_prefix_bind_actual_raw_draft(native, kind):
    section = {**native["section"], "facet": "validation", "validation_kind": kind}
    if kind == "documented_manual":
        (native["upstream"] / "docs.md").write_text("Inspect DEFAULT_RETRIES.\nExpected: 3.\n")
        section.update(title="Documented retry inspection", body="Inspect the retry setting and expect three; this check was not executed.",
                       evidence=[{"path": "docs.md", "start": 1, "end": 2}])
    else:
        (native["upstream"] / "tests").mkdir()
        (native["upstream"] / "tests/test_helper.py").write_text("def test_retry_default():\n    assert get_retry_default() == 3\n")
        section.update(title="Helper default assertion", body="test_retry_default asserts only the helper's value is three; tests were not run.",
                       evidence=[{"path": "tests/test_helper.py", "start": 1, "end": 2}])
    section, _ = _lightweight(native, section)
    assert not _audit(native)["problems"]
    changed = {**section, "validation_kind": "automated_runtime"}
    _replace_generation(native, sections=[changed])
    report = _audit(native)
    assert not report["approvals"] and any("exact successful Zcode" in p for p in report["problems"])


def test_retained_lightweight_draft_is_bound_instead_of_a_later_unrelated_generation(native):
    _, data = _lightweight(native)
    later = native["store"].append("model_call", model=dict(native["generator"]["model"]),
        inputs={"prompt": _fence({**data, "facets": ["api"]})},
        outputs={"reply": json.dumps({"sections": [{**native["section"], "facet": "api"}]})})
    _replace_record(native, native["judge"], at=later["at"] + 1)
    report = _audit(native)
    assert not report["problems"] and report["approvals"][0]["native_generator_trace_id"] == native["generator"]["id"]


def test_strict_legacy_generator_context_is_not_reinterpreted_as_lightweight(native):
    _replace_record(native, native["generator"], model={**native["generator"]["model"],
        "provider": "claude", "model": "claude-opus-5", "served_model": "claude-opus-5"},
        outputs={"reply": native["store"].put_blob(json.dumps({"sections": []}))})
    report = _audit(native)
    assert not report["problems"] and len(report["approvals"]) == 1
