"""kb init, stage 2 (modules): absorption, map cards, groups, chaining, budget.

Offline, on the skeleton suite's toy world (local git repos, scripted models,
faked ``gh``), with an upstream that has nested tool packages.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from infermatrix_copilot.kb_service.init_modules import SYSTEM_CARD, _leading_doc, declaration, routes_append_only
from infermatrix_copilot.kb_service.init_stages import run_stage
from infermatrix_copilot.kb_service.config import RepoLifecycle
from infermatrix_copilot.kb_service.init_support import InitRecord
from infermatrix_copilot.kb_service.models import ModelReply
from infermatrix_copilot.knowledge_service.lifecycle import Page

from test_kb_init_skeleton import (  # noqa: F401 - the fixture is used by name
    FakeGateway, FakeGh, _commit, _index, _lifecycle, _runtime, _tree, world,
)

MANIFEST = ("name: toy\nrepo:\n  full_name: o/toy\n  language: python\n"
            "knowledge:\n  repo_subdir: repos/toy\n"
            "knowledge_lifecycle:\n  enabled: false\n  mode: shadow\n")

TOOLS = {
    "tools/gen/x.py": '"""Generate the tick tables."""\n\ndef build():\n    return 1\n',
    "tools/gen/x2.py": "def extra():\n    return 2\n",
    "tools/lint/y.py": "# Lint worker configs.\n\nclass Linter:\n    def run(self):\n        return 0\n",
    "tools/fmt/z.py": "def fmt():\n    return 3\n",
}


class CardGateway(FakeGateway):
    """The skeleton gateway plus map cards; the map routes ``pkg/`` and one
    file of ``tools/gen/`` (so that module is absorbed, not carded)."""

    def __init__(self, *, card_cost=0.01, group="tooling", **kwargs):
        super().__init__(**kwargs)
        self.card_cost = card_cost
        self.group = group

    def call_json(self, role, *, system, prompt, validate=None, max_budget_usd=None):
        if system != SYSTEM_CARD:
            reply = super().call_json(role, system=system, prompt=prompt, validate=validate,
                                      max_budget_usd=max_budget_usd)
            if system.startswith("You set up the review knowledge base"):
                reply.data["owners"][0]["scope_prefixes"] = ["pkg/", "tools/gen/x.py"]
            return reply
        self.calls.append({"role": role.name, "system": system, "prompt": prompt, "max_budget_usd": max_budget_usd})
        payload = json.loads(prompt.split("\n", 1)[1].rsplit("</untrusted_data>", 1)[0])
        files = [f["path"] for f in payload["files"]]
        data = {"title": f"Module {payload['module']}", "purpose": "Checks worker configs before a tick runs.",
                "entry_points": [{"path": files[0], "what": "the entry"}, {"path": "not/here.py", "what": "x"}],
                "key_files": [], "docs": [{"path": "docs/guide.md", "why": "tick rules"},
                                          {"path": "docs/nope.md", "why": "x"}],
                "signals": ["lint", "tooling"], "group": self.group, "group_title": "Tooling", "headings": {}}
        if validate is not None:
            validate(data)
        return ModelReply(role, data, json.dumps(data), role.model, {}, 0.1, cost_usd=self.card_cost)


def _world_with_tools(world) -> None:
    _commit(world["upstream"], TOOLS, "tools")
    _commit(world["origin"], {"adapters/toy/manifest.yaml": MANIFEST}, "toy adapter with a language")


def _modules_lifecycle(**init):
    return _lifecycle(**{"source_roots": ("pkg/", "tools/"), "min_module_loc": 0, "seeds": (), **init})


def _skeleton(world, gateway=None, **kwargs):
    record = run_stage(_runtime(world, gateway or CardGateway(), **kwargs), _modules_lifecycle(), "skeleton",
                       dry_run=True)
    assert record.status == "dry_run", record.problems
    return record


def test_modules_dry_run_chains_on_the_skeleton_and_routes_every_module(world):
    _world_with_tools(world)
    _skeleton(world)
    gateway = CardGateway()
    record = run_stage(_runtime(world, gateway), _modules_lifecycle(), "modules", dry_run=True)
    assert record.status == "dry_run", record.problems
    tree = _tree(record)
    routes = yaml.safe_load(tree["knowledge/repos/toy/_routes.yaml"])
    core = routes["owners"][0]
    assert core["owner"] == "core" and core["scope_prefixes"] == ["pkg/", "tools/gen/x.py", "tools/gen/"]
    tooling = routes["owners"][1]
    assert tooling == {"owner": "tooling", "path": "repos/toy/components/tooling/_index.md",
                       "signals": ["lint", "tooling"], "scope_prefixes": ["tools/fmt/", "tools/lint/"]}
    # one card per unrouted module, in a new group with its own entry page, linked upward
    card = tree["knowledge/repos/toy/components/tooling/tools-lint.md"]
    assert "`tools/lint/y.py`" in card and "not/here.py" not in card
    assert "`docs/guide.md`" in card and "docs/nope.md" not in card
    assert Page.parse(card).frontmatter_data()["type"] == "architecture"
    group = tree["knowledge/repos/toy/components/tooling/_index.md"]
    assert "](tools-lint.md)" in group and "](tools-fmt.md)" in group
    assert "](tooling/_index.md)" in tree["knowledge/repos/toy/components/_index.md"]
    assert "](components/_index.md)" in tree["knowledge/repos/toy/_index.md"]
    # the card call saw signatures and docstrings, never function bodies
    prompt = next(c["prompt"] for c in gateway.calls if c["system"] == SYSTEM_CARD and "tools/lint/" in c["prompt"])
    assert "class Linter" in prompt and "return 0" not in prompt
    assert record.coverage["modules"]["before"] < 1 and record.coverage["modules"]["after"] == 1
    assert record.coverage["unrouted"] == []
    assert any("absorbed into owner core" in n for n in record.notes)
    body = (Path(record.pr["dry_run_dir"]) / "PR_BODY.md").read_text(encoding="utf-8")
    assert "| modules routed |" in body and "kb init(toy): modules" in body


def test_modules_needs_the_skeleton_first(world):
    _world_with_tools(world)
    gateway = CardGateway()
    record = run_stage(_runtime(world, gateway), _modules_lifecycle(), "modules", dry_run=True)
    assert record.status == "blocked" and "run the skeleton stage first" in record.problems[0]
    assert gateway.calls == []


def test_publishing_modules_needs_the_skeleton_pr_merged(world):
    _world_with_tools(world)
    env = {"ALLOW_PUSH": "1", "ALLOW_POST": "1", "KB_INIT_GIT_AUTHOR": "tzhouam <tzhouam@example.com>"}
    _skeleton(world)
    dry = run_stage(_runtime(world, CardGateway(), environ=env), _modules_lifecycle(), "modules", dry_run=False)
    assert dry.status == "blocked" and "only a dry run" in dry.problems[0]

    class ViewGh(FakeGh):
        def __init__(self, state):
            super().__init__()
            self.state = state

        def __call__(self, cmd, **kwargs):
            if cmd[:3] == ["gh", "pr", "view"]:
                import subprocess
                return subprocess.CompletedProcess(cmd, 0, json.dumps({"state": self.state}).encode(), b"")
            return super().__call__(cmd, **kwargs)

    state = world["tmp"] / "published"
    open_gh = ViewGh("OPEN")
    published = run_stage(_runtime(world, CardGateway(), environ=env, gh_run=open_gh, state_dir=state),
                          _modules_lifecycle(), "skeleton", dry_run=False)
    assert published.status == "published", published.problems
    gateway = CardGateway()
    waiting = run_stage(_runtime(world, gateway, environ=env, gh_run=open_gh, state_dir=state),
                        _modules_lifecycle(), "modules", dry_run=True)
    assert waiting.status == "blocked" and "merge the skeleton PR #7" in waiting.problems[0]
    assert "OPEN" in waiting.problems[0] and gateway.calls == []
    # merged: main now carries the skeleton, and the modules stage builds on it
    merged_files = {p: t for p, t in _tree_at(world, published.pr["head_sha"]).items()}
    _commit(world["origin"], merged_files, "merge the skeleton PR")
    done = run_stage(_runtime(world, CardGateway(), environ=env, gh_run=ViewGh("MERGED"), state_dir=state),
                     _modules_lifecycle(), "modules", dry_run=True)
    assert done.status == "dry_run", done.problems
    assert done.pin == published.pin


def _tree_at(world, sha: str) -> dict[str, str]:
    import subprocess

    names = subprocess.run(["git", "-C", str(world["clone"]), "ls-tree", "-r", "--name-only", sha, "knowledge/repos"],
                           check=True, capture_output=True, text=True).stdout.split()
    return {n: subprocess.run(["git", "-C", str(world["clone"]), "show", f"{sha}:{n}"], check=True,
                              capture_output=True, text=True).stdout for n in names}


def test_an_exhausted_budget_leaves_a_valid_pr_and_lists_the_rest(world):
    _world_with_tools(world)
    _skeleton(world)
    # the first card costs $1; the second cannot reserve threshold + worst request within $6
    gateway = CardGateway(card_cost=1.0)
    record = run_stage(_runtime(world, gateway), _modules_lifecycle(budget_usd=6.0), "modules", dry_run=True)
    assert record.status == "dry_run", record.problems
    assert [u.split(":")[0] for u in record.unfinished] == ["module tools/lint/"]
    assert record.coverage["unrouted"] == ["tools/lint/"]
    assert "knowledge/repos/toy/components/tooling/tools-fmt.md" in _tree(record)
    assert record.spent_usd <= 6.0


def test_cards_join_an_existing_group_append_only(world):
    _world_with_tools(world)
    existing = {
        "knowledge/repos/toy/_index.md": _index("Toy", "toy", "- [Components](components/_index.md)\n"),
        "knowledge/repos/toy/components/_index.md": _index("Components", "toy", "- [Tooling](tooling/_index.md)\n"),
        "knowledge/repos/toy/components/tooling/_index.md": _index("Tooling", "toy", "Tools the engine ships.\n"),
        "knowledge/repos/_index.md": ("---\ntitle: \"Repositories\"\ncreated: 2026-09-01\nupdated: 2026-09-01\n"
                                      "type: index\ntags: [other]\nsources: []\n---\n\n# Repositories\n\n"
                                      "## Current\n\n| repo | upstream | where |\n|---|---|---|\n"
                                      "| other | `o/other` | [other](other/_index.md) |\n"
                                      "| toy | `o/toy` | [toy](toy/_index.md) |\n"),
    }
    _commit(world["origin"], existing, "existing toy kb with a tooling group")
    _skeleton(world)
    record = run_stage(_runtime(world, CardGateway()), _modules_lifecycle(), "modules", dry_run=True)
    assert record.status == "dry_run", record.problems
    tree = _tree(record)
    group = tree["knowledge/repos/toy/components/tooling/_index.md"]
    assert group.startswith(existing["knowledge/repos/toy/components/tooling/_index.md"].rstrip("\n"))
    assert "- [Module tools/lint/](tools-lint.md)" in group
    assert "knowledge/repos/toy/components/_index.md" not in tree       # the group was already linked
    routes = yaml.safe_load(tree["knowledge/repos/toy/_routes.yaml"])
    tooling = [o for o in routes["owners"] if o["path"] == "repos/toy/components/tooling/_index.md"]
    assert len(tooling) == 1 and set(tooling[0]["scope_prefixes"]) >= {"tools/fmt/", "tools/lint/"}


def test_an_adapter_missing_at_the_base_blocks_the_modules_stage(world):
    """The pilot fail-open: an absent manifest is not "no language"."""
    _world_with_tools(world)
    _skeleton(world)
    lifecycle = RepoLifecycle(**{**_modules_lifecycle().__dict__, "adapter_dir": Path("adapters/nope")})
    gateway = CardGateway()
    record = run_stage(_runtime(world, gateway), lifecycle, "modules", dry_run=True)
    assert record.status == "blocked"
    assert record.problems == ["adapters/nope/manifest.yaml does not exist in the knowledge repository at the base"]
    assert not any("no repo.language" in item for item in record.checklist)
    assert not [c for c in gateway.calls if c["system"] == SYSTEM_CARD]


def test_no_language_means_no_scan_and_an_empty_stage(world):
    _commit(world["upstream"], TOOLS, "tools")        # the adapter still declares no language
    _skeleton(world)
    gateway = CardGateway()
    record = run_stage(_runtime(world, gateway), _modules_lifecycle(), "modules", dry_run=True)
    assert record.status == "empty"
    assert any("no repo.language" in item for item in record.checklist)
    assert not [c for c in gateway.calls if c["system"] == SYSTEM_CARD]
    # a later dry run still chains through an empty stage
    assert InitRecord.load(_runtime(world).state_dir, "toy", "modules").status == "empty"


def test_routes_append_only_catches_rewrites():
    before = {"schema_version": 1, "owners": [{"owner": "a", "path": "p", "scope_prefixes": ["x/"]}]}
    assert routes_append_only(before, {"schema_version": 1, "owners": [
        {"owner": "a", "path": "p", "scope_prefixes": ["x/", "y/"]}, {"owner": "b", "path": "q"}]}) == []
    assert routes_append_only(before, {"schema_version": 1, "owners": [
        {"owner": "a", "path": "p", "scope_prefixes": ["y/"]}]})
    assert routes_append_only(before, {"schema_version": 1, "owners": []})
    assert routes_append_only(before, {"schema_version": 2, "owners": before["owners"]})


def test_signatures_never_carry_a_body():
    assert declaration("def check(): return perform_sensitive_operation()", "python") == "def check():"
    assert declaration("class A(B): pass", "python") == "class A(B):"
    assert declaration("def f(x: int = {'a': 1}, y=lambda z: z) -> dict[str, int]: return {}", "python") \
        == "def f(x: int = {'a': 1}, y=lambda z: z) -> dict[str, int]:"
    assert declaration("def g(sep=':'):", "python") == "def g(sep=':'):"
    assert declaration("async def h(", "python") == "async def h("         # continues on the next line
    js = "javascript"
    assert declaration("export const check = () => { perform_sensitive_operation(); };", js) == "export const check"
    assert declaration("export function run(a, b) { return a + b; }", js) == "export function run(a, b)"
    assert declaration("const handler = async (req) => req.body", js) == "const handler"
    assert declaration("class Store extends Base { get() { return 1 } }", js) == "class Store extends Base"
    assert declaration("export const same = a === b", js) == "export const same"
    assert declaration("func (s *Server) Serve(ctx context.Context) error", "go") \
        == "func (s *Server) Serve(ctx context.Context) error"
    assert declaration("pub fn apply(&self, x: u32) -> u32 { x }", "rust") == "pub fn apply(&self, x: u32) -> u32"
    # no lexing for brace languages: the earliest possible body start wins
    assert declaration("export function run() /* don't inline */ { return sensitive_operation(); }", js) \
        == "export function run() /* don't inline */"
    assert declaration("function run(pattern = /[/*]/) /* note */ { sensitive_operation(); }", js) \
        == "function run(pattern"
    assert declaration("export function run() // it's { return sensitive_operation(); }", js) \
        == "export function run() // it's"
    assert declaration("function f(a = '{') { body() }", js) == "function f(a"
    assert declaration("export function cmp(a, b) { return a <= b && a != b }", js) == "export function cmp(a, b)"
    assert declaration("def f(): # don't: x()", "python") == "def f():"
    assert declaration("def g(  # it's a note", "python") == "def g("


def test_card_prompts_carry_declarations_only(world):
    _world_with_tools(world)
    _commit(world["upstream"], {"tools/lint/one.py": "def secret(): return perform_sensitive_operation()\n"},
            "one-line function")
    _skeleton(world)
    gateway = CardGateway()
    record = run_stage(_runtime(world, gateway), _modules_lifecycle(), "modules", dry_run=True)
    assert record.status == "dry_run", record.problems
    prompts = "".join(c["prompt"] for c in gateway.calls if c["system"] == SYSTEM_CARD)
    assert "def secret():" in prompts and "perform_sensitive_operation" not in prompts


def test_leading_doc_reads_docstrings_and_comment_blocks():
    assert _leading_doc('#!/usr/bin/env python\n"""Tick tables."""\nX = 1\n') == "Tick tables."
    assert _leading_doc("// Net layer.\n// Owns sockets.\npackage net\n") == "Net layer. Owns sockets."
    assert _leading_doc("x = 1\n") == ""
    assert _leading_doc("/* Docs. */ function f() { return sensitive_operation(); }\n") == "Docs."
    assert _leading_doc("/**\n * Store layer.\n * Keeps rows. */ export class S {}\nconst x = 1;\n") \
        == "Store layer. Keeps rows."


def test_an_empty_route_table_gets_owners(world):
    _world_with_tools(world)
    skeleton = _skeleton(world)
    routes = Path(skeleton.pr["dry_run_dir"]) / "tree" / "knowledge" / "repos" / "toy" / "_routes.yaml"
    routes.write_text("# emptied by hand\nschema_version: 1\nowners:\n", encoding="utf-8")
    record = run_stage(_runtime(world, CardGateway()), _modules_lifecycle(), "modules", dry_run=True)
    assert record.status == "dry_run", record.problems
    table = _tree(record)["knowledge/repos/toy/_routes.yaml"]
    assert table.startswith("# emptied by hand\n")
    assert {o["owner"] for o in yaml.safe_load(table)["owners"]} >= {"tooling"}
