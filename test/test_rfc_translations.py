import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from infermatrix_copilot.rfc_service.application import RFCService
from infermatrix_copilot.rfc_service.models import RFCError
from infermatrix_copilot.rfc_service.translations import source_strings


class Translator:
    model = "GLM-5.3-Flash"
    def __init__(self): self.calls = []; self.hook = None; self.invalid = False
    def translate(self, entries):
        self.calls.append(entries)
        if self.hook: self.hook()
        return {item["segment"]: ("bad 999" if self.invalid else "译文 " + item["source"]) for item in entries}


@pytest.fixture
def workspace(tmp_path):
    translator = Translator(); service = RFCService(tmp_path, providers={"github": object()}, translator=translator)
    service.translations.ui = ["登录", "成果"]
    token = service.bootstrap_admin("owner"); principal = service.authenticate(token["token"])
    repo = service.dispatch(principal, "repositories.create", {"name": "repo", "provider": "github", "external_name": "owner/repo"})
    rfc = service.dispatch(principal, "rfcs.draft", {"repo_id": repo["id"], "title": "Technical plan", "body": "## Goals\nServe 12 FPS.\n\n#### F1. Work\nKeep `/v1/realtime/video` unchanged.\n\n## Acceptance criteria\n- Throughput verified.\n"})
    return service, principal, repo, rfc, translator


def get(service, principal, rfc, language="zh"):
    return service.dispatch(principal, "rfcs.get", {"rfc_id": rfc["id"], "view": "detail", "language": language})


def process_all(service):
    for _ in range(10):
        if not service.translations.process()["processed"]: break


def test_automatic_projection_is_incremental_and_never_edits_source(workspace):
    service, p, repo, rfc, translator = workspace
    service.translations.reconcile(); process_all(service)
    view = get(service, p, rfc)
    assert view["translations"]["pending"] == 0
    assert view["translations"]["strings"]["Serve 12 FPS."] == "译文 Serve 12 FPS."
    assert view["body"] == rfc["body"] and view["revision"] == rfc["revision"]
    calls = len(translator.calls)
    service.translations.reconcile(); process_all(service)
    assert len(translator.calls) == calls
    revised = service.dispatch(p, "rfcs.update", {"rfc_id": rfc["id"], "expected_revision": view["revision"], "body": rfc["body"].replace("12 FPS", "24 FPS")})
    fresh = get(service, p, revised)
    assert "Serve 12 FPS." not in fresh["translations"]["strings"]
    assert fresh["translations"]["pending"] == 1
    process_all(service)
    assert get(service, p, revised)["translations"]["ready"] == fresh["translations"]["total"]


def test_code_urls_and_internal_metadata_do_not_enter_translation():
    strings = source_strings({"body": "## Goals\nUse `secret_code` and [report](https://example.com/private).\n<!-- roadmap-people: PRIVATE_AUTHOR -->\n```python\nprivate_code = 1\n```\n```mermaid\nflowchart LR\nF1[Deliver 12 FPS] --> F2[Validation]\n```\n"})
    assert "Deliver 12 FPS" in strings
    assert "secret_code" not in strings
    assert all("private_code" not in text and "PRIVATE_AUTHOR" not in text and "https://example.com/private" not in text for text in strings)


def test_group_titles_follow_rfc_permissions_and_stay_out_of_public_catalog(workspace):
    service, owner, repo, rfc, translator = workspace
    service.dispatch(owner, "rfcs.work", {"rfc_id": rfc["id"], "op": "add", "feature": {"id": "F2", "title": "Second work"}})
    service.dispatch(owner, "rfcs.graph", {"rfc_id": rfc["id"], "op": "merge", "feature_ids": ["F1", "F2"], "title": "Private merged delivery"})
    service.translations.reconcile(); process_all(service)
    assert "Private merged delivery" in get(service, owner, rfc)["translations"]["strings"]
    assert "Private merged delivery" not in service.translations.public_ui("zh")["strings"]
    private = service.dispatch(owner, "rfcs.draft", {"repo_id": repo["id"], "title": "Private source", "body": "Source",
        "source": {"provider": "github", "repository": "owner/repo", "kind": "issue", "identifier": "90"}})
    service.dispatch(owner, "rfcs.acl", {"rfc_id": private["id"], "restricted": True, "grants": {}})
    with service.store.transaction() as con:
        row = con.execute("SELECT model FROM rfcs WHERE id=?", (rfc["id"],)).fetchone(); model = json.loads(row["model"])
        next(f for f in model["features"] if f["id"] == "F2")["auto_source"] = private["source"]
        con.execute("UPDATE rfcs SET model=? WHERE id=?", (json.dumps(model), rfc["id"]))
    reader = service.dispatch(owner, "users.create", {"name": "Group reader"})
    issued = service.dispatch(owner, "tokens.create", {"user_id": reader["id"]})
    service.dispatch(owner, "grants.set", {"repo_id": repo["id"], "user_id": reader["id"], "role": "reader"})
    visible = get(service, service.authenticate(issued["token"]), rfc)
    assert visible["node_groups"] == []
    assert "Private merged delivery" not in visible["translations"]["strings"]


def test_numbers_are_validated_and_failure_does_not_replace_source(workspace):
    service, p, repo, rfc, translator = workspace
    service.translations.ui = []; translator.invalid = True
    view = get(service, p, rfc); service.translations.process()
    failed = get(service, p, rfc)
    assert failed["translations"]["failed"] == view["translations"]["total"]
    assert failed["translations"]["strings"] == {}
    assert failed["body"] == rfc["body"]


def test_revoked_authority_stops_queued_model_calls(workspace):
    service, p, repo, rfc, translator = workspace
    service.translations.ui = []
    reader = service.dispatch(p, "users.create", {"name": "reader"})
    issued = service.dispatch(p, "tokens.create", {"user_id": reader["id"]})
    service.dispatch(p, "grants.set", {"repo_id": repo["id"], "user_id": reader["id"], "role": "reader"})
    rp = service.authenticate(issued["token"])
    get(service, rp, rfc)
    service.dispatch(p, "grants.set", {"repo_id": repo["id"], "user_id": reader["id"], "role": ""})
    assert service.translations.process()["processed"] == 0
    assert not translator.calls
    with pytest.raises(RFCError): get(service, rp, rfc)


def test_changes_and_revocations_during_model_call_discard_results(workspace):
    service, p, repo, rfc, translator = workspace
    service.translations.ui = []
    get(service, p, rfc)
    translator.hook = lambda: service.dispatch(p, "rfcs.update", {"rfc_id": rfc["id"], "expected_revision": rfc["revision"], "body": "## Goals\nNew goal."})
    service.translations.process()
    fresh = get(service, p, rfc)
    assert "Serve 12 FPS." not in fresh["translations"]["strings"]


def test_public_catalog_never_contains_rfc_or_other_repo_translations(workspace):
    service, p, repo, rfc, translator = workspace
    get(service, p, rfc); service.translations.reconcile(); process_all(service)
    public = service.translations.public_ui("en")
    assert set(public["strings"]) == {"登录", "成果"}
    assert "Technical plan" not in json.dumps(public)
    reader = service.dispatch(p, "users.create", {"name": "reader"})
    rp = service.authenticate(service.dispatch(p, "tokens.create", {"user_id": reader["id"]})["token"])
    with pytest.raises(RFCError): get(service, rp, rfc)
    with pytest.raises(RFCError): get(service, p, rfc, "fr")


def test_private_auto_source_strings_are_filtered_before_cache_return(workspace):
    service, p, repo, rfc, translator = workspace
    private = service.dispatch(p, "rfcs.draft", {"repo_id": repo["id"], "title": "Private", "body": "## Goals\nPrivate goal.", "source": {"provider": "github", "repository": "owner/repo", "kind": "issue", "identifier": "99"}})
    service.dispatch(p, "rfcs.acl", {"rfc_id": private["id"], "restricted": True, "grants": {}})
    with service.store.transaction() as con:
        row = con.execute("SELECT model FROM rfcs WHERE id=?", (rfc["id"],)).fetchone(); model = json.loads(row["model"])
        model["features"].append({"id": "F2", "title": "CONFIDENTIAL TASK", "track": "Private track", "depends_on": [], "links": [], "auto_source": private["source"]})
        con.execute("UPDATE rfcs SET model=? WHERE id=?", (json.dumps(model), rfc["id"]))
    get(service, p, rfc); process_all(service)
    reader = service.dispatch(p, "users.create", {"name": "reader"})
    service.dispatch(p, "grants.set", {"repo_id": repo["id"], "user_id": reader["id"], "role": "reader"})
    rp = service.authenticate(service.dispatch(p, "tokens.create", {"user_id": reader["id"]})["token"])
    assert "CONFIDENTIAL" not in json.dumps(get(service, rp, rfc))


def test_concurrent_workers_translate_each_batch_once(workspace):
    service, p, repo, rfc, translator = workspace
    service.translations.ui = []; get(service, p, rfc)
    with ThreadPoolExecutor(2) as pool: list(pool.map(lambda _: service.translations.process(), range(2)))
    assert len(translator.calls) == 1


def test_revocation_during_model_call_discards_completed_translation(workspace):
    service, p, repo, rfc, translator = workspace
    service.translations.ui = []
    reader = service.dispatch(p, "users.create", {"name": "reader"})
    service.dispatch(p, "grants.set", {"repo_id": repo["id"], "user_id": reader["id"], "role": "reader"})
    rp = service.authenticate(service.dispatch(p, "tokens.create", {"user_id": reader["id"]})["token"])
    get(service, rp, rfc)
    translator.hook = lambda: service.dispatch(p, "grants.set", {"repo_id": repo["id"], "user_id": reader["id"], "role": ""})
    assert service.translations.process()["ready"] == 0
    with service.store.transaction() as con:
        assert con.execute("SELECT COUNT(*) FROM translations WHERE status='ready'").fetchone()[0] == 0


def test_expired_lease_recovers_and_retries_continue_after_four_failures(workspace):
    service, p, repo, rfc, translator = workspace
    service.translations.ui = []; get(service, p, rfc)
    with service.store.transaction() as con:
        con.execute("UPDATE translations SET status='running',worker='lost',lease_until=?,attempts=4", (service.clock() - 1,))
    assert service.translations.process()["ready"] > 0
    translator.invalid = True
    with service.store.transaction() as con:
        con.execute("UPDATE translations SET status='failed',retry_at=0,attempts=4")
    assert service.translations.process()["processed"] > 0
    calls = len(translator.calls)
    assert service.translations.process()["processed"] == 0
    assert len(translator.calls) == calls
    translator.invalid = False
    with service.store.transaction() as con: con.execute("UPDATE translations SET retry_at=0")
    assert service.translations.process()["ready"] > 0


def test_zcode_adapter_shields_literals_before_model_translation():
    from types import SimpleNamespace
    from infermatrix_copilot.rfc_service.translations import ZcodeTranslator
    translator = ZcodeTranslator.__new__(ZcodeTranslator); translator.model = 'GLM-5.3-Flash'
    class Transport:
        def complete(self, **kwargs):
            texts = json.loads(kwargs['messages'][0]['content'])
            assert '12' not in texts[0]['text'] and 'generate()' not in texts[0]['text']
            assert 'https://' not in texts[0]['text'] and '⟪P0⟫' in texts[0]['text']
            return SimpleNamespace(text=json.dumps({'0': '译文 ' + texts[0]['text']}), stop_reason='end_turn')
    translator.transport = Transport()
    source = 'Use generate() at 12 FPS; see https://example.com/report and `source_code`.'
    assert translator.translate([{'segment':'key','source':source,'language':'zh'}])['key'] == '译文 ' + source


def test_protected_identifiers_remain_valid_next_to_chinese():
    from collections import Counter
    from infermatrix_copilot.rfc_service.translations import _PROTECTED
    assert Counter(_PROTECTED.findall('H200 and E8 use generate() and source_code.')) == Counter(_PROTECTED.findall('使用H200和E8调用generate()以及source_code。'))


def test_interface_catalog_includes_labels_inside_dynamic_templates():
    from infermatrix_copilot.rfc_service.translations import ui_strings
    assert {'工作空间', 'RFC 详情', '负责人', '验收', '实现'} <= set(ui_strings())
