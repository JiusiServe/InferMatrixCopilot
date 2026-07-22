"""Deterministic-first NL routing (intent.py pre-parse + validation + retry):
URLs carry their full repo identity, unambiguous refs skip the LLM, missing
targets clarify upfront, and the LLM fallback gets exactly one repair retry."""

import json

import pytest

from infermatrix_copilot.intent import (
    parse_intent,
    parse_intents,
    pre_parse,
    resolve_repo_alias,
    validate_spec,
)
from infermatrix_copilot.llm import Block, Reply
from infermatrix_copilot.task_spec import TaskSpec


class NeverLLM:
    """An LLM whose use is a test failure — proves the fast path skipped it."""
    available = True

    def create(self, **_):
        raise AssertionError("LLM must not be called on the deterministic path")


class ScriptedLLM:
    def __init__(self, replies):
        self._replies = list(replies)
        self.calls = 0
        self.available = True

    def create(self, **_):
        self.calls += 1
        return self._replies.pop(0)


def _reply(obj_or_text):
    text = obj_or_text if isinstance(obj_or_text, str) else json.dumps(obj_or_text)
    return Reply(blocks=[Block(type="text", text=text)])


@pytest.fixture
def rsettings(settings):
    settings.default_repo = "vllm-omni"
    settings.repo_paths = {"vllm-omni": "/nonexistent/vllm-omni"}
    settings.repo_full_names = {"vllm-omni": "vllm-project/vllm-omni"}
    return settings


URL = "https://github.com/vllm-project/vllm-omni/pull/5156"


def test_url_routes_with_full_identity(rsettings):
    r = parse_intent(f"review {URL}", llm=NeverLLM(), settings=rsettings)
    s = r.spec
    assert s and s.kind == "pr_review" and s.pr == 5156 and s.repo == "vllm-omni"


def test_url_owner_mismatch_is_rejected_not_defaulted(rsettings):
    r = parse_intent("review https://github.com/evil/vllm-omni/pull/5156",
                     llm=NeverLLM(), settings=rsettings)
    assert r.needs_clarification
    assert "evil/vllm-omni" in r.clarify and "vllm-omni" in r.clarify


def test_issue_url_routes_to_answer(rsettings):
    r = parse_intent("https://github.com/vllm-project/vllm-omni/issues/4842",
                     llm=NeverLLM(), settings=rsettings)
    assert r.spec and r.spec.kind == "issue_answer" and r.spec.issue == 4842


def test_depth_phrase_carries_params(rsettings):
    r = parse_intent("do a full depth review of pr 5156", llm=NeverLLM(),
                     settings=rsettings)
    assert r.spec and r.spec.params.get("review_depth") == "full"
    r2 = parse_intent(f"quick review of {URL}", llm=NeverLLM(),
                      settings=rsettings)
    assert r2.spec and r2.spec.params.get("review_depth") == "light"


def test_bare_verb_ref_skips_llm(rsettings):
    r = parse_intent("review pr 5134", llm=NeverLLM(), settings=rsettings)
    assert r.spec and r.spec.kind == "pr_review" and r.spec.pr == 5134
    r = parse_intent("answer issue 4842", llm=NeverLLM(), settings=rsettings)
    assert r.spec and r.spec.kind == "issue_answer" and r.spec.issue == 4842


def test_bare_number_without_verb_goes_to_llm(rsettings):
    llm = ScriptedLLM([_reply({"kind": "pr_review", "pr": 123,
                               "confidence": 0.9, "clarify": ""})])
    r = parse_intent("#123", llm=llm, settings=rsettings)
    assert llm.calls == 1  # ambiguous ref fell through to the classifier
    assert r.spec and r.spec.pr == 123


def test_missing_target_clarifies_upfront(rsettings):
    llm = ScriptedLLM([_reply({"kind": "pr_review", "pr": None,
                               "confidence": 0.95, "clarify": ""})])
    r = parse_intent("review this", llm=llm, settings=rsettings)
    assert r.needs_clarification and "PR number or URL" in r.clarify


def test_llm_gets_exactly_one_repair_retry(rsettings):
    llm = ScriptedLLM([
        _reply("sure! I think you want a review of PR 99"),   # unparseable
        _reply({"kind": "pr_review", "pr": 99, "confidence": 0.9,
                "clarify": ""}),                              # repair succeeds
    ])
    r = parse_intent("could you take a look at ninety-nine", llm=llm,
                     settings=rsettings)
    assert llm.calls == 2
    assert r.spec and r.spec.pr == 99

    flaky = ScriptedLLM([_reply("prose"), _reply("more prose")])
    r2 = parse_intent("gibberish request", llm=flaky, settings=rsettings)
    assert flaky.calls == 2 and r2.needs_clarification


def test_llm_review_depth_field_validated(rsettings):
    llm = ScriptedLLM([_reply({"kind": "pr_review", "pr": 7, "confidence": 0.9,
                               "clarify": "", "review_depth": "FULL"})])
    r = parse_intent("give seven a going-over", llm=llm, settings=rsettings)
    assert r.spec and r.spec.params.get("review_depth") == "full"
    llm2 = ScriptedLLM([_reply({"kind": "pr_review", "pr": 7, "confidence": 0.9,
                                "clarify": "", "review_depth": "bogus"})])
    r2 = parse_intent("check seven", llm=llm2, settings=rsettings)
    assert r2.spec and "review_depth" not in r2.spec.params


def test_resolve_repo_alias_uses_explicit_map_first(rsettings):
    assert resolve_repo_alias("vllm-project", "vllm-omni", rsettings) == "vllm-omni"
    assert resolve_repo_alias("evil", "vllm-omni", rsettings) is None


def test_validate_spec_rules():
    assert "PR number" in validate_spec(TaskSpec(kind="pr_review"))
    assert validate_spec(TaskSpec(kind="pr_review", pr=1)) == ""
    assert "issue" in validate_spec(TaskSpec(kind="issue_answer"))
    assert validate_spec(TaskSpec(kind="issue_filter")) == ""  # batch triage ok


def test_compound_still_carries_refs(rsettings):
    llm = ScriptedLLM([_reply({"kind": "pr_rebase", "pr": 12,
                               "confidence": 0.9, "clarify": ""})])
    results = parse_intents("rebase pr 12, then review it", llm=llm,
                            settings=rsettings)
    assert len(results) == 2
    assert results[0].spec and results[0].spec.kind == "pr_rebase"
    # segment 2 "review it pr 12" hits the deterministic path — no extra LLM call
    assert results[1].spec and results[1].spec.kind == "pr_review" \
        and results[1].spec.pr == 12
    assert llm.calls == 1


def test_triage_url_with_filter_verb(rsettings):
    r = parse_intent(
        "triage https://github.com/vllm-project/vllm-omni/issues/5123",
        llm=NeverLLM(), settings=rsettings)
    assert r.spec and r.spec.kind == "issue_filter" and r.spec.issue == 5123
