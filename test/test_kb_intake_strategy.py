"""Knowledge intake drafting strategies: v1 unchanged, v2 contract, normalization, verification."""

from __future__ import annotations

import json

import pytest

from infermatrix_copilot.kb_service import intake
from infermatrix_copilot.kb_service.intake import (
    SYSTEM, SYSTEM_V2, VERIFY_SYSTEM, allowed_pages, draft_changes, draft_prompt, normalize_reply,
    page_language, page_summary_v2, strategy_from_env, suggest_rule_ids,
)
from infermatrix_copilot.kb_service.models import ModelReply, ModelRole, ModelUnavailable

GEN = ModelRole("generator", "zcode", "GLM-5.3-Flash")
DIR = "repos/demo/core"
PAGE = f"{DIR}/rules.md"
TOPIC = f"{DIR}/rules-queue.md"
EVIDENCE = {"source_reference": "PR #10", "title": "Bound the queue", "body": "reject when full",
            "changed_files": ["demo/core/queue.py"], "diff_excerpt": "+if full: raise QueueFull"}


def _rule(rule_id: str, cite: str = "PR #10", claim: str = "队列满时拒绝新请求并返回明确错误") -> str:
    return (f"## {rule_id} — keep the demo queue bounded\n\n"
            "- 触发：修改 demo queue 的容量或背压逻辑时。\n"
            f"- 强制：{claim}，不能无界增长。\n"
            f"- 验收：测试覆盖满队列拒绝路径。 ^[{cite}]\n")


def _footer(rule_id_since: str = "r1") -> str:
    return f'<!-- kb:rule status="active" since="{rule_id_since}" -->\n'


def _tree() -> dict[str, str]:
    return {
        "repos/demo/_index.md": "# demo\n",
        f"{DIR}/_index.md": "# core\n\n- [rules](rules.md)\n",
        "repos/demo/_routes.yaml": (
            "schema_version: 1\nowners:\n  - owner: core\n    path: repos/demo/core/rules.md\n"
            "    signals: [queue]\n    scope_prefixes: [demo/core/]\n"),
        PAGE: ("---\ntitle: \"Demo core rules\"\ncreated: 2026-09-01\nupdated: 2026-09-01\n"
               "type: rule\ntags: [demo]\nsources: [\"PR #10\"]\n---\n\n# Demo core rules\n\n"
               + _rule("DEMO-1a") + _footer() + "\n" + _rule("DEMO-1b") + _footer()),
        "repos/demo/other/_index.md": "# other\n",
        "repos/demo/other/rules.md": ("---\ntitle: \"Other\"\ncreated: 2026-09-01\nupdated: 2026-09-01\n"
                                      "type: rule\ntags: [demo]\nsources: []\n---\n\n# Other\n\n"
                                      + _rule("DEMO-2a") + _footer()),
    }


class ScriptedGateway:
    def __init__(self, answers):
        self.answers = list(answers)
        self.calls: list[tuple[str, str, str]] = []

    def call_json(self, role, *, system, prompt, validate=None):
        self.calls.append((role.name, system, prompt))
        data = self.answers.pop(0)
        if isinstance(data, Exception):
            raise data
        data = json.loads(json.dumps(data))
        if validate is not None:
            try:
                validate(data)
            except (KeyError, TypeError, ValueError) as exc:
                raise ModelUnavailable(f"{role.label()} reply failed its schema: {exc!r}") from exc
        return ModelReply(role, data, json.dumps(data), role.model, {}, 0.1)


# -- strategy selection and v1 stability ---------------------------------------------

def test_strategy_from_env_defaults_to_v1_and_rejects_unknown(monkeypatch):
    monkeypatch.delenv("KB_DRAFT_STRATEGY", raising=False)
    assert strategy_from_env() == "v1"
    monkeypatch.setenv("KB_DRAFT_STRATEGY", "v2")
    assert strategy_from_env() == "v2"
    monkeypatch.setenv("KB_DRAFT_STRATEGY", "v9")
    with pytest.raises(ValueError, match="KB_DRAFT_STRATEGY"):
        strategy_from_env()


def test_v1_prompt_and_system_are_untouched():
    """The incumbent's recorded calls stay comparable: v1 renders the same prompt as before."""
    files = _tree()
    prompt = draft_prompt("demo", EVIDENCE, files, "repos/demo")
    assert prompt == draft_prompt("demo", EVIDENCE, files, "repos/demo", strategy="v1")
    context = json.loads(prompt.split("\n\n<untrusted_data>", 1)[0].split("\n", 1)[1])
    assert set(context["related_pages"][0]) == {"page", "near_capacity", "sibling_pages", "rules"}
    assert "suggested_rule_ids" not in prompt
    assert "Decide in this order" not in SYSTEM and "Decide in this order" in SYSTEM_V2


# -- v2 context ---------------------------------------------------------------------

def test_page_language_detects_cjk_prose():
    assert page_language(_tree()[PAGE]) == "zh"
    assert page_language("# Rules\n\n## R-1a — keep it bounded\n\n- trigger: queue changes\n") == "en"


def test_suggested_ids_continue_the_family_and_skip_the_whole_tree():
    files = _tree()
    assert suggest_rule_ids(files, PAGE) == ["DEMO-2b", "DEMO-2c", "DEMO-3a"]  # DEMO-2a lives on another page
    # a new topic page borrows its directory's family; an exclusion is honoured
    assert suggest_rule_ids(files, TOPIC, 2) == ["DEMO-2b", "DEMO-2c"]
    assert suggest_rule_ids(files, TOPIC, 1, exclude={"DEMO-2b"}) == ["DEMO-2c"]
    # tombstoned IDs are reserved forever
    files["repos/demo/_tombstones.yaml"] = "schema_version: 1\nids:\n  - {id: DEMO-2b, purged_at: r0, page: x}\n"
    assert suggest_rule_ids(files, PAGE, 1) == ["DEMO-2c"]
    # a directory without any rule family falls back to its name
    assert suggest_rule_ids({"repos/demo/model-executor/rules.md": files["repos/demo/other/rules.md"].replace("DEMO-2a", "X")},
                            "repos/demo/model-executor/rules-new.md", 1) == ["MODEL-EXECUTOR-1a"]


def test_v2_prompt_carries_language_style_capacity_and_ids():
    files = _tree()
    prompt = draft_prompt("demo", EVIDENCE, files, "repos/demo", strategy="v2")
    context = json.loads(prompt.split("\n\n<untrusted_data>", 1)[0].split("\n", 1)[1])
    page = context["related_pages"][0]
    assert page["language"] == "zh"
    assert page["style_example"].startswith("## DEMO-1b — keep the demo queue bounded")
    assert page["suggested_rule_ids"] == ["DEMO-2b", "DEMO-2c", "DEMO-3a"]
    assert page["capacity"]["bytes_free"] > 0 and page["capacity"]["lines_free"] > 0
    assert page_summary_v2(files, PAGE)["rules"][0]["rule_id"] == "DEMO-1a"
    assert "<untrusted_data>" in prompt and "\\u003c" not in prompt.split("<untrusted_data>")[0]


def test_allowed_pages_keeps_rules_inside_the_related_owner_directories():
    files = _tree()
    related = [PAGE]
    assert allowed_pages(files, related, PAGE)
    assert allowed_pages(files, related, TOPIC)                    # a new topic page of the owner
    assert not allowed_pages(files, related, "repos/demo/other/rules.md")
    assert not allowed_pages(files, related, "repos/demo/rules.md")
    assert not allowed_pages(files, related, f"{DIR}/notes.md")


# -- v2 normalization -----------------------------------------------------------------

def test_normalize_fixes_types_pages_ids_headings_and_citations():
    files = _tree()
    data = {"operations": [
        {"kind": "add", "page": PAGE, "new_page": True, "page_title": 7, "rule_id": "DEMO-1a",
         "section_markdown": "## DEMO-1a — bounded\n\n- 触发：x\n- 强制：y\n- 禁止：z\n- 验收：w\n"},
        {"kind": "add", "page": PAGE, "new_page": TOPIC, "rule_id": "DEMO-9a",
         "section_markdown": "## DEMO-8a — titled rule\n\n- 触发：x ^[PR #10]\n"},
        {"kind": "retire", "page": PAGE, "rule_id": "DEMO-1b", "reason": "incorrect", "evidence": None},
    ]}
    notes = normalize_reply(data, files, EVIDENCE)
    first, second, third = data["operations"]
    assert "new_page" not in first and first["page_title"] == "7"
    assert first["rule_id"] == "DEMO-2b" and first["section_markdown"].startswith("## DEMO-2b — bounded")
    assert first["section_markdown"].rstrip().endswith("^[PR #10]")
    assert second["page"] == TOPIC and "new_page" not in second
    assert second["page_title"] == "titled rule"
    assert second["section_markdown"].startswith("## DEMO-9a — titled rule")
    assert third["evidence"] == "PR #10"
    assert any("renamed to DEMO-2b" in n for n in notes) and any("citation" in n for n in notes)
    intake._validate_reply(data)   # the normalized reply passes the schema as-is


def test_normalize_gives_two_colliding_adds_distinct_fresh_ids():
    files = _tree()
    data = {"operations": [
        {"kind": "add", "page": PAGE, "rule_id": "DEMO-1a", "section_markdown": _rule("DEMO-1a")},
        {"kind": "add", "page": PAGE, "rule_id": "DEMO-1a", "section_markdown": _rule("DEMO-1a")},
    ]}
    normalize_reply(data, files, EVIDENCE)
    ids = [op["rule_id"] for op in data["operations"]]
    assert ids == ["DEMO-2b", "DEMO-2c"]
    assert all(op["section_markdown"].startswith(f"## {rid} ") for op, rid in zip(data["operations"], ids))


def test_normalize_leaves_a_clean_reply_alone():
    data = {"operations": [{"kind": "add", "page": PAGE, "rule_id": "DEMO-2b", "section_markdown": _rule("DEMO-2b")}],
            "rationale": "r"}
    before = json.dumps(data, sort_keys=True)
    assert normalize_reply(data, _tree(), EVIDENCE) == []
    assert json.dumps(data, sort_keys=True) == before


# -- v2 drafting end to end (scripted generator) ----------------------------------------

def _draft(gateway, strategy="v2", files=None):
    return draft_changes(repo="demo", repo_dir="repos/demo", event_id=1, evidence=EVIDENCE,
                         files=files or _tree(), gateway=gateway, generator=GEN, release="r2", today="2026-10-01",
                         strategy=strategy)


def test_v2_normalizes_then_verifies_and_keeps_the_verified_rule():
    gateway = ScriptedGateway([
        # the draft: a colliding ID and a boolean new_page — fixed without a repair round
        {"operations": [{"kind": "add", "page": PAGE, "new_page": True, "rule_id": "DEMO-1a",
                         "section_markdown": _rule("DEMO-1a", claim="队列满时拒绝新请求")}], "rationale": "contract"},
        # the verification narrows the claim
        {"operations": [{"kind": "add", "page": PAGE, "rule_id": "DEMO-2b",
                         "section_markdown": _rule("DEMO-2b", claim="队列满时拒绝新请求并抛出 QueueFull")}],
         "rationale": "verified", "changes": ["narrowed 强制 to the raised error"]},
    ])
    draft = _draft(gateway)
    assert not draft.rejected and len(draft.operations) == 1
    assert draft.operations[0].rule_id == "DEMO-2b"
    assert "QueueFull" in draft.operations[0].section_markdown
    assert draft.rationale == "verified"
    assert [c[1] for c in gateway.calls] == [SYSTEM_V2, VERIFY_SYSTEM]
    assert '"proposed_operations"' in gateway.calls[1][2] and '"related_rules"' in gateway.calls[1][2]
    phases = [a for a in draft.attempts if a.get("phase") == "verify"]
    assert phases and phases[0]["kept"] == 1 and phases[0]["changes"] == ["narrowed 强制 to the raised error"]
    assert any("renamed to DEMO-2b" in n for a in draft.attempts for n in a.get("normalized", []))


def test_v2_verification_can_withdraw_the_draft():
    gateway = ScriptedGateway([
        {"operations": [{"kind": "add", "page": PAGE, "rule_id": "DEMO-2b", "section_markdown": _rule("DEMO-2b")}]},
        {"operations": [], "rationale": "restates the PR", "changes": ["dropped DEMO-2b"]},
    ])
    draft = _draft(gateway)
    assert draft.empty and not draft.rejected and draft.rationale == "restates the PR"
    assert draft.attempts[-1]["withdrawn"] is True


def test_v2_keeps_the_draft_when_verification_is_unusable():
    unusable = ModelUnavailable("zcode:GLM-5.3-Flash reply failed its schema: ValueError('x')")
    gateway = ScriptedGateway([
        {"operations": [{"kind": "add", "page": PAGE, "rule_id": "DEMO-2b", "section_markdown": _rule("DEMO-2b")}]},
        unusable,
    ])
    draft = _draft(gateway)
    assert len(draft.operations) == 1 and draft.attempts[-1]["phase"] == "verify"
    # a verified set that does not apply (an edit of a rule that does not exist) is discarded, the draft kept
    gateway = ScriptedGateway([
        {"operations": [{"kind": "add", "page": PAGE, "rule_id": "DEMO-2b", "section_markdown": _rule("DEMO-2b")}]},
        {"operations": [{"kind": "edit_same_meaning", "page": PAGE, "rule_id": "DEMO-7z",
                         "section_markdown": _rule("DEMO-7z")}]},
    ])
    draft = _draft(gateway)
    assert len(draft.operations) == 1 and draft.operations[0].kind == "add" and draft.operations[0].page == PAGE
    assert "do not apply" in draft.attempts[-1]["error"]


def test_v2_rejects_a_rule_routed_to_another_owner_and_repairs():
    gateway = ScriptedGateway([
        {"operations": [{"kind": "add", "page": "repos/demo/other/rules.md", "rule_id": "DEMO-2b",
                         "section_markdown": _rule("DEMO-2b")}]},
        {"operations": [{"kind": "add", "page": TOPIC, "page_title": "Queue", "rule_id": "DEMO-2b",
                         "section_markdown": _rule("DEMO-2b")}]},
        {"operations": [{"kind": "add", "page": TOPIC, "page_title": "Queue", "rule_id": "DEMO-2b",
                         "section_markdown": _rule("DEMO-2b")}], "changes": []},
    ])
    draft = _draft(gateway)
    assert draft.operations and draft.operations[0].page == TOPIC
    assert "not one of the related_pages" in gateway.calls[1][2]
    assert draft.result is not None and TOPIC in draft.result.files


def test_v2_empty_draft_skips_verification():
    gateway = ScriptedGateway([{"operations": [], "rationale": "docs only"}])
    draft = _draft(gateway)
    assert draft.empty and len(gateway.calls) == 1


def test_v1_makes_no_verification_call_and_no_normalization():
    gateway = ScriptedGateway([
        {"operations": [{"kind": "add", "page": PAGE, "new_page": True, "rule_id": "DEMO-2b",
                         "section_markdown": _rule("DEMO-2b")}]},
        {"operations": [{"kind": "add", "page": PAGE, "rule_id": "DEMO-2b", "section_markdown": _rule("DEMO-2b")}]},
    ])
    draft = _draft(gateway, strategy="v1")
    assert len(draft.operations) == 1 and len(gateway.calls) == 2   # the boolean cost a repair round in v1
    assert gateway.calls[0][1] == SYSTEM and "did not match the required JSON shape" in gateway.calls[1][2]


def test_v2_verification_may_not_move_a_rule_to_another_owner():
    other = "repos/demo/other/rules.md"
    gateway = ScriptedGateway([
        {"operations": [{"kind": "add", "page": PAGE, "rule_id": "DEMO-2b", "section_markdown": _rule("DEMO-2b")}]},
        {"operations": [{"kind": "add", "page": other, "rule_id": "DEMO-2b", "section_markdown": _rule("DEMO-2b")}],
         "changes": ["moved to other"]},
    ])
    draft = _draft(gateway)
    assert len(draft.operations) == 1 and draft.operations[0].page == PAGE
    assert "left the allowed pages" in draft.attempts[-1]["error"]
    # a verified operation outside the repository is refused the same way
    gateway = ScriptedGateway([
        {"operations": [{"kind": "add", "page": PAGE, "rule_id": "DEMO-2b", "section_markdown": _rule("DEMO-2b")}]},
        {"operations": [{"kind": "add", "page": "repos/elsewhere/rules.md", "rule_id": "DEMO-2b",
                         "section_markdown": _rule("DEMO-2b")}]},
    ])
    draft = _draft(gateway)
    assert draft.operations[0].page == PAGE and "left the allowed pages" in draft.attempts[-1]["error"]


@pytest.mark.parametrize("changes", [True, 1, "narrowed", {"a": 1}, None])
def test_v2_verification_tolerates_a_malformed_changes_field(changes):
    gateway = ScriptedGateway([
        {"operations": [{"kind": "add", "page": PAGE, "rule_id": "DEMO-2b", "section_markdown": _rule("DEMO-2b")}]},
        {"operations": [{"kind": "add", "page": PAGE, "rule_id": "DEMO-2b",
                         "section_markdown": _rule("DEMO-2b", claim="队列满时拒绝新请求并抛出 QueueFull")}],
         "changes": changes},
    ])
    draft = _draft(gateway)
    assert len(draft.operations) == 1 and "QueueFull" in draft.operations[0].section_markdown
    assert draft.attempts[-1]["changes"] == []


def test_v2_acceptance_and_export_name_the_verified_reply(tmp_path):
    """The change set's draft_keys (and the dataset export) point at the reply
    whose operations became the change: the verified one when it replaced the
    draft, the draft's own when verification kept it."""
    from types import SimpleNamespace

    from infermatrix_copilot.kb_service.intake import VERIFY_ATTEMPT
    from infermatrix_copilot.kb_service.models import ModelGateway
    from infermatrix_copilot.kb_service.replay import export_dataset
    from infermatrix_copilot.kb_service.runtime import trace_recorder
    from infermatrix_copilot.trace_store import TraceStore, accepted_key, trace_context

    store = TraceStore(tmp_path / "t", environ={})
    replies = iter([
        {"operations": [{"kind": "add", "page": PAGE, "rule_id": "DEMO-2b",
                         "section_markdown": _rule("DEMO-2b", claim="original claim 原稿")}]},
        {"operations": [{"kind": "add", "page": PAGE, "rule_id": "DEMO-2b",
                         "section_markdown": _rule("DEMO-2b", claim="verified claim 已核")}], "changes": ["narrowed"]},
    ])

    class Transport:
        def complete(self, **kw):
            return SimpleNamespace(blocks=[SimpleNamespace(text=json.dumps(next(replies), ensure_ascii=False))],
                                   stop_reason="end_turn", usage={}, model="GLM-5.3-Flash")

    gateway = ModelGateway(None, transport_factory=lambda p: Transport(), recorder=trace_recorder(store))
    key, holder = "event:demo:1:abcd1234", {}
    with trace_context(playbook="kb-intake", repo="demo", run_id="r1", draft_key=key, _accepted=holder, step="draft"):
        draft = _draft(gateway)
    assert "已核" in draft.operations[0].section_markdown
    assert accepted_key(key, holder) == f"{key}#{VERIFY_ATTEMPT}"
    calls = {r["context"]["attempt"]: r for r in store.query(kind="model_call", limit=100)}
    assert set(calls) == {0, VERIFY_ATTEMPT}
    assert "已核" in store.blob(calls[VERIFY_ATTEMPT]["outputs"]["reply"])
    # the change set names the verified call; the export attaches the decision to it only
    store.append("decision", context={"changeset_id": "cs1", "draft_keys": [accepted_key(key, holder)],
                                      "step": "gate", "rule_ids": ["DEMO-2b"]},
                 result={"status": "pass"})
    export_dataset(store, tmp_path / "rows.jsonl", role="generator")
    rows = {json.loads(l)["id"]: json.loads(l) for l in (tmp_path / "rows.jsonl").read_text(encoding="utf-8").splitlines()}
    assert rows[calls[VERIFY_ATTEMPT]["id"]]["decision"] == {"status": "pass"}
    assert rows[calls[VERIFY_ATTEMPT]["id"]]["changeset_id"] == "cs1"
    assert rows[calls[0]["id"]]["decision"] is None and rows[calls[0]["id"]]["changeset_id"] == ""


def test_v2_acceptance_stays_on_the_draft_when_verification_is_kept_out():
    from infermatrix_copilot.trace_store import accepted_key, trace_context

    gateway = ScriptedGateway([
        {"operations": [{"kind": "add", "page": PAGE, "rule_id": "DEMO-2b", "section_markdown": _rule("DEMO-2b")}]},
        {"operations": [{"kind": "edit_same_meaning", "page": PAGE, "rule_id": "DEMO-7z",
                         "section_markdown": _rule("DEMO-7z")}]},        # does not apply: draft kept
    ])
    key, holder = "event:demo:1:abcd1234", {}
    with trace_context(draft_key=key, _accepted=holder, step="draft"):
        draft = _draft(gateway)
    assert len(draft.operations) == 1 and accepted_key(key, holder) == f"{key}#0"
