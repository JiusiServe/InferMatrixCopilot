"""kb init, stage 3 (deepen): code rules for hot modules and the shadow flip.

Offline, on the skeleton/modules suites' toy world: the upstream gets a churn
history, the stages chain through dry runs, the models are scripted.
"""

from __future__ import annotations

import json
import os
import subprocess

import pytest
import yaml

from infermatrix_copilot.kb_service.init_deepen import SYSTEM_CODE_RULES, _Deepen, flip_to_shadow
from infermatrix_copilot.kb_service.init_stages import run_stage
from infermatrix_copilot.kb_service.init_support import InitError, UpstreamPin
from infermatrix_copilot.kb_service.models import ModelReply
from infermatrix_copilot.knowledge_service.lifecycle import Page

from test_kb_init_modules import MANIFEST, CardGateway, _modules_lifecycle, _world_with_tools
from test_kb_init_skeleton import ENV, _commit, _index, _runtime, _tree, world  # noqa: F401 - fixture by name

LINT_RULE = {"title": "Linter.run keeps its zero exit on clean configs",
             "body": "- 强制：`tools/lint/y.py::Linter` returns 0 from `run` when no config breaks a tick rule.",
             "evidence": [{"path": "tools/lint/y.py", "start": 3, "end": 5}]}
OUTSIDE_RULE = {"title": "Engine step is pure",
                "body": "- 强制：`pkg/core.py` keeps `step` free of side effects.",
                "evidence": [{"path": "pkg/core.py", "start": 1, "end": 3}]}
PKG_RULE = {"title": "The helper stays constant",
            "body": "- 强制：`pkg/util.py::helper` returns the same value for every tick.",
            "evidence": [{"path": "pkg/util.py", "start": 1, "end": 2}]}


class CodeGateway(CardGateway):
    def __init__(self, *, code_cost=0.01, **kwargs):
        super().__init__(**kwargs)
        self.code_cost = code_cost

    def call_json(self, role, *, system, prompt, validate=None, max_budget_usd=None):
        if system != SYSTEM_CODE_RULES:
            return super().call_json(role, system=system, prompt=prompt, validate=validate,
                                     max_budget_usd=max_budget_usd)
        self.calls.append({"role": role.name, "system": system, "prompt": prompt, "max_budget_usd": max_budget_usd})
        payload = json.loads(prompt.split("\n", 1)[1].rsplit("</untrusted_data>", 1)[0])
        rules = {"tools/lint/": [LINT_RULE, OUTSIDE_RULE], "pkg/": [PKG_RULE]}.get(payload["module"], [])
        data = {"page_title": "Tooling rules", "rules": rules}
        if validate is not None:
            validate(data)
        return ModelReply(role, data, json.dumps(data), role.model, {}, 0.1, cost_usd=self.code_cost)


def _churn(world) -> None:
    for i in range(3):
        _commit(world["upstream"], {"tools/lint/y.py": (
            "# Lint worker configs.\n\nclass Linter:\n    def run(self):\n        return 0\n" + f"# rev {i}\n")},
            f"lint {i}")
    _commit(world["upstream"], {"tools/fmt/z.py": "def fmt():\n    return 4\n"}, "fmt")
    _commit(world["upstream"], {"pkg/util.py": "def helper():\n    return 2\n\n# tick helper\n"}, "util")


def _chain(world, gateway, **lifecycle):
    for stage in ("skeleton", "modules"):
        record = run_stage(_runtime(world, gateway), _modules_lifecycle(**lifecycle), stage, dry_run=True)
        assert record.status in ("dry_run", "empty"), (stage, record.problems)


def test_deepen_writes_rules_for_hot_modules_and_flips_to_shadow(world):
    _world_with_tools(world)
    _churn(world)
    gateway = CodeGateway()
    _chain(world, gateway)
    record = run_stage(_runtime(world, gateway), _modules_lifecycle(), "deepen", dry_run=True)
    assert record.status == "dry_run", record.problems
    tree = _tree(record)
    # the hottest module whose owner bears no rule got them, on a new page beside its group's entry page
    page = Page.parse(tree["knowledge/repos/toy/components/tooling/rules.md"])
    assert len(page.rules()) == 1 and "Linter.run keeps its zero exit" in page.rules()[0].text
    assert page.frontmatter_data()["title"] == "Tooling rules"
    assert "](rules.md)" in tree["knowledge/repos/toy/components/tooling/_index.md"]
    rid = page.rules()[0].rule_id
    assert record.verdicts[rid]["verdict"] == "pass" and record.evidence[rid][0]["path"] == "tools/lint/y.py"
    assert any("evidence outside module tools/lint/" in d["why"] for d in record.dropped)
    # only one code call: pkg/ and tools/gen/ route to an owner that already bears rules
    code_calls = [c for c in gateway.calls if c["system"] == SYSTEM_CODE_RULES]
    assert len(code_calls) == 1 and '"module": "tools/lint/"' in code_calls[0]["prompt"]
    assert "return 0" in code_calls[0]["prompt"]          # code is read here (the depth pass)
    cov = record.coverage
    assert cov["pr_rule_bearing"]["before"] < cov["pr_rule_bearing"]["after"] == 1.0
    assert cov["pr_routed"]["after"] == 1.0 and cov["window_prs"] >= 5
    # the shadow flip: exactly the two lines
    manifest = tree["adapters/toy/manifest.yaml"]
    assert manifest == MANIFEST.replace("enabled: false", "enabled: true")
    assert "adapters/toy/manifest.yaml" in record.files


def test_deepen_stops_at_the_coverage_target_and_still_flips(world):
    _world_with_tools(world)
    _churn(world)
    gateway = CodeGateway()
    _chain(world, gateway, coverage_target=0.01)
    record = run_stage(_runtime(world, gateway), _modules_lifecycle(coverage_target=0.01), "deepen", dry_run=True)
    assert record.status == "dry_run", record.problems
    assert not [c for c in gateway.calls if c["system"] == SYSTEM_CODE_RULES]
    assert any("coverage target" in n for n in record.notes)
    assert set(_tree(record)) == {"adapters/toy/manifest.yaml"}


def test_an_exhausted_budget_keeps_the_rules_written_and_lists_the_rest(world):
    _world_with_tools(world)
    _churn(world)
    # no skeleton rules, and pkg/ is owned by the prose architecture page: it bears no rule either
    gateway = CodeGateway(code_cost=1.0, doc_rules=[], map_owner_page="repos/toy/architecture.md")
    _chain(world, gateway)
    record = run_stage(_runtime(world, gateway), _modules_lifecycle(budget_usd=6.0), "deepen", dry_run=True)
    assert record.status == "dry_run", record.problems
    assert [u.split(":")[0] for u in record.unfinished][:1] == ["module pkg/"], (record.unfinished, record.notes)
    assert record.coverage["pr_rule_bearing"]["after"] < 1.0
    # routed, but still without rules: reported, not hidden behind "routed"
    assert "pkg/util.py" in [path for path, _ in record.coverage["uncovered_hot"]]
    assert record.coverage["unrouted_hot"] == []
    assert "knowledge/repos/toy/components/tooling/rules.md" in _tree(record)
    assert record.spent_usd <= 6.0


def test_an_existing_rule_page_is_only_appended_to(world):
    _world_with_tools(world)
    _churn(world)
    old = ('---\ntitle: "Tooling rules"\ncreated: 2026-09-01\nupdated: 2026-09-01\ntype: rule\ntags: [toy]\n'
           "sources: []\n---\n\n# Tooling rules\n\nRules for the tools live here.\n")
    _commit(world["origin"], {
        "knowledge/repos/toy/_index.md": _index("Toy", "toy", "- [Components](components/_index.md)\n"),
        "knowledge/repos/toy/components/_index.md": _index("Components", "toy", "- [Tooling](tooling/_index.md)\n"),
        "knowledge/repos/toy/components/tooling/_index.md": _index("Tooling", "toy", "- [Tooling rules](rules.md)\n"),
        "knowledge/repos/toy/components/tooling/rules.md": old,
        "knowledge/repos/_index.md": ("---\ntitle: \"Repositories\"\ncreated: 2026-09-01\nupdated: 2026-09-01\n"
                                      "type: index\ntags: [other]\nsources: []\n---\n\n# Repositories\n\n"
                                      "- [other](other/_index.md)\n- [toy](toy/_index.md)\n"),
    }, "existing tooling rules page")
    gateway = CodeGateway()
    _chain(world, gateway)
    record = run_stage(_runtime(world, gateway), _modules_lifecycle(), "deepen", dry_run=True)
    assert record.status == "dry_run", record.problems
    text = _tree(record)["knowledge/repos/toy/components/tooling/rules.md"]
    assert text.split("\n---\n", 1)[1].startswith(old.split("\n---\n", 1)[1].rstrip("\n"))   # body kept
    assert text.index("Rules for the tools live here.") < text.index("## TOY-I")
    assert Page.parse(text).frontmatter_data()["title"] == "Tooling rules"      # the old title stays


def test_deepen_without_a_lifecycle_block_blocks_before_any_model_call(world):
    _commit(world["upstream"], {"tools/lint/y.py": "x = 1\n"}, "tools")    # the adapter is only "name: toy"
    gateway = CodeGateway()
    _chain(world, gateway)
    calls = len(gateway.calls)
    record = run_stage(_runtime(world, gateway), _modules_lifecycle(), "deepen", dry_run=True)
    assert record.status == "blocked" and "knowledge_lifecycle" in record.problems[0]
    assert len(gateway.calls) == calls


def test_an_empty_rule_page_owner_bears_no_rules_whatever_its_siblings_hold(world):
    from infermatrix_copilot.kb_service.init_coverage import Owner

    rule = ('---\ntitle: "R"\ncreated: 2026-09-01\nupdated: 2026-09-01\ntype: rule\ntags: [toy]\nsources: []\n'
            "---\n\n# R\n\n## TOY-1a — A rule\n\n- 强制：keep it.\n\n<!-- kb:rule status=active since=r1 -->\n")
    empty = ('---\ntitle: "E"\ncreated: 2026-09-01\nupdated: 2026-09-01\ntype: rule\ntags: [toy]\nsources: []\n'
             "---\n\n# E\n\nNothing yet.\n")
    stage = _Deepen(_runtime(world), _modules_lifecycle(), dry_run=True, pin=None)
    stage.head = {"repos/toy/a/rules.md": rule, "repos/toy/a/empty.md": empty,
                  "repos/toy/a/_index.md": _index("A", "toy", "- [R](rules.md)\n")}
    owners = [Owner("empty", "repos/toy/a/empty.md", ("x/",)), Owner("index", "repos/toy/a/_index.md", ("y/",)),
              Owner("rules", "repos/toy/a/rules.md", ("z/",))]
    assert stage._rule_pages(owners) == {"repos/toy/a/_index.md", "repos/toy/a/rules.md"}


def test_flip_to_shadow_edits_only_the_two_lines():
    base = ("name: toy\n# lifecycle below\nknowledge_lifecycle:\n  # comment\n  enabled: false   # off\n"
            "  mode: auto_merge\n  intake:\n    enabled: false\n  knowledge_dir: repos/toy\nnext: 1\n")
    assert flip_to_shadow(base) == base.replace("enabled: false   # off", "enabled: true   # off").replace(
        "mode: auto_merge", "mode: shadow")
    missing = "knowledge_lifecycle:\n  mode: shadow\nother: x\n"
    assert flip_to_shadow(missing) == "knowledge_lifecycle:\n  enabled: true\n  mode: shadow\nother: x\n"
    assert flip_to_shadow("knowledge_lifecycle:\r\n  enabled: no\r\n") == "knowledge_lifecycle:\r\n  enabled: true\r\n"
    with pytest.raises(InitError):
        flip_to_shadow("name: toy\n")


def test_the_flip_check_refuses_any_other_edit(world):
    rt = _runtime(world)
    stage = _Deepen(rt, _modules_lifecycle(), dry_run=True, pin=None)
    path = "adapters/toy/manifest.yaml"
    good = flip_to_shadow(MANIFEST)
    assert stage._check_flip(path, MANIFEST, good) == []
    sneaky = good.replace("language: python", "language: rust")
    assert stage._check_flip(path, MANIFEST, sneaky)
    assert stage._check_flip(path, MANIFEST, MANIFEST)                     # not turned on
    assert stage._check_flip("adapters/other/manifest.yaml", MANIFEST, good)
    wrong_dir = flip_to_shadow(MANIFEST.replace("repo_subdir: repos/toy", "repo_subdir: repos/elsewhere"))
    assert stage._check_flip(path, MANIFEST.replace("repos/toy", "repos/elsewhere"), wrong_dir)


def _dated_commit(repo, name, when):
    env = {**os.environ, **ENV, "GIT_AUTHOR_DATE": f"@{when} +0000", "GIT_COMMITTER_DATE": f"@{when} +0000"}
    (repo / name).write_text(f"{when}\n", encoding="utf-8")   # a unique body: every commit changes its file
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True, env=env, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", name], check=True, env=env, capture_output=True)
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True,
                          text=True).stdout.strip()


def test_the_pr_window_is_bounded_by_count_and_by_age_from_the_pin(tmp_path):
    repo = tmp_path / "up"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q", "-b", "main"], check=True)
    day = 86400
    _dated_commit(repo, "old.py", 1_000_000)
    _dated_commit(repo, "a.py", 1_000_000 + 30 * day)
    pin = _dated_commit(repo, "b.py", 1_000_000 + 31 * day)
    _dated_commit(repo, "after.py", 1_000_000 + 40 * day)          # after the pin: never in its window
    mirror = UpstreamPin(repo / ".git", "o/up")
    assert mirror.first_parent_changes(pin, count=10, max_age_days=5) == [["b.py"], ["a.py"]]
    assert mirror.first_parent_changes(pin, count=1, max_age_days=365) == [["b.py"]]
    assert mirror.first_parent_changes(pin, count=10, max_age_days=365)[-1] == ["old.py"]
    assert mirror.first_parent_changes(pin, count=0, max_age_days=365) == []


def test_the_pr_window_reads_any_file_name_and_skips_out_of_order_times(tmp_path):
    repo = tmp_path / "up"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q", "-b", "main"], check=True)
    day, pin_time = 86400, 1_000_000_000
    _dated_commit(repo, "café.py", pin_time - day)
    _dated_commit(repo, "late.py", pin_time - 10 * day)      # committed "earlier" than its parent
    pin = _dated_commit(repo, "b c.py", pin_time)
    window = UpstreamPin(repo / ".git", "o/up").first_parent_changes(pin, count=10, max_age_days=5)
    assert window == [["b c.py"], ["café.py"]]


def test_routes_and_rules_stay_valid_yaml(world):
    _world_with_tools(world)
    _churn(world)
    gateway = CodeGateway()
    _chain(world, gateway)
    record = run_stage(_runtime(world, gateway), _modules_lifecycle(), "deepen", dry_run=True)
    assert record.status == "dry_run", record.problems
    assert yaml.safe_load(_tree(record)["adapters/toy/manifest.yaml"])["knowledge_lifecycle"]["enabled"] is True
