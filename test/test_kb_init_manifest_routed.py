"""kb init on a repository routed by its adapter manifest (``review_routes``).

Regression for the first real run (afd-plugin skeleton, PR #265): a
knowledge-side ``_routes.yaml`` takes precedence over the manifest and changed
every route, and rules appended to a briefing doc pushed the index out of the
briefing cap. Offline, on the skeleton/modules/deepen suites' toy world.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from infermatrix_copilot.kb_service.init_coverage import (
    Owner, most_specific, owner_table, owners_from_review_routes, routes_file,
)
from infermatrix_copilot.kb_service.init_deepen import SYSTEM_CODE_RULES
from infermatrix_copilot.kb_service.init_modules import SYSTEM_CARD
from infermatrix_copilot.kb_service.init_stages import SYSTEM_MAP, review_route_line, run_stage
from infermatrix_copilot.kb_service.models import ModelReply
from infermatrix_copilot.knowledge_service.lifecycle import Page

from test_kb_init_deepen import PKG_RULE, CodeGateway
from test_kb_init_modules import TOOLS
from test_kb_init_skeleton import (  # noqa: F401 - the fixture is used by name
    DOC_RULE, DOC_RULE2, FakeGateway, _commit, _index, _lifecycle, _runtime, _tree, world,
)

MANIFEST = """name: toy
repo:
  full_name: o/toy
  language: python
knowledge:
  repo_subdir: repos/toy
  briefing_docs:
  - repos/toy/rules.md
  - repos/toy/_index.md
review_routes:
- prefix: pkg/
  owner: core
  doc: repos/toy/components/core/rules.md
knowledge_lifecycle:
  enabled: false
  mode: shadow
"""

DOCS_ONLY_RULE = {"title": "Guides ship in both languages",
                  "body": "- 强制：every page under `docs/` has a translated twin before review.",
                  "evidence": [{"path": "docs/guide.md", "start": 1, "end": 2}]}

CORE_RULES = ('---\ntitle: "Core rules"\ncreated: 2026-09-01\nupdated: 2026-09-01\ntype: rule\n'
              "tags: [toy]\nsources: []\n---\n\n# Core rules\n\n"
              "## Direct 代码快速入口\n\n| PR 描述在做什么 | 精确规则 | 第一批 live 源码 |\n|---|---|---|\n"
              "| engine tick | (none yet) | `pkg/core.py` |\n")


def _manifest_routed_kb(world, *, core_rules: str = CORE_RULES) -> None:
    """The toy knowledge base as afd-plugin's is shaped: a top-level rule
    page that is a briefing doc, component pages the manifest routes to, and
    no ``_routes.yaml``."""
    _commit(world["origin"], {
        "adapters/toy/manifest.yaml": MANIFEST,
        "knowledge/repos/toy/_index.md": _index("Toy", "toy", "- [Toy rules](rules.md)\n- [Components](components/_index.md)\n"),
        "knowledge/repos/toy/rules.md": (
            '---\ntitle: "Toy rules"\ncreated: 2026-09-01\nupdated: 2026-09-01\ntype: rule\n'
            "tags: [toy]\nsources: []\n---\n\n# Toy rules\n\n## TOY-1a — Ticks are counted\n\n"
            "- 强制：every worker counts its ticks.\n"),
        "knowledge/repos/toy/components/_index.md": _index("Components", "toy", "- [Core](core/_index.md)\n"),
        "knowledge/repos/toy/components/core/_index.md": _index("Core", "toy", "The engine.\n\n- [Core rules](rules.md)\n"),
        "knowledge/repos/toy/components/core/rules.md": core_rules,
    }, "toy is routed by its manifest")


class ManifestGateway(FakeGateway):
    """The map proposes the manifest's owner with one prefix it lacks."""

    def call_json(self, role, *, system, prompt, validate=None, max_budget_usd=None):
        reply = super().call_json(role, system=system, prompt=prompt, validate=validate,
                                  max_budget_usd=max_budget_usd)
        if system == SYSTEM_MAP:
            reply.data["owners"] = [{"owner": "core", "title": "Core", "page": "repos/toy/components/core/rules.md",
                                     "signals": ["engine"], "scope_prefixes": ["pkg/", "tests/"]}]
        return reply


def _toy(**init):
    return _lifecycle(**{"source_roots": ("pkg/", "tools/"), "min_module_loc": 0, **init})


# -- the owner table ------------------------------------------------------------------

def test_owner_table_prefers_a_routes_file_then_the_manifest():
    manifest = yaml.safe_load(MANIFEST)
    manifest["review_routes"] += [{"prefix": "pkg/util.py", "owner": "core", "doc": "repos/toy/components/core/rules.md"},
                                  {"prefix": "tools/", "owner": "core", "doc": "repos/toy/components/tools.md"},
                                  {"prefix": "nodoc/", "owner": "x"}]
    owners = owners_from_review_routes(manifest)
    assert owners == [Owner("core", "repos/toy/components/core/rules.md", ("pkg/", "pkg/util.py")),
                      Owner("core/tools", "repos/toy/components/tools.md", ("tools/",))]
    assert owner_table(None, manifest) == ("manifest", owners)
    # Direct falls back to the manifest when the routes file names no owners
    # (direct_routing: ``routes_table is None or not routes_table["owners"]``),
    # so an empty file defers too; it is the knowledge-side table only when
    # the manifest routes nothing either
    assert owner_table("schema_version: 1\nowners: []\n", manifest) == ("manifest", owners_from_review_routes(manifest))
    assert owner_table("schema_version: 1\nowners: []\n", {"review_routes": []}) == ("routes_file", [])
    assert owner_table("schema_version: 1\nowners: []\n", None) == ("routes_file", [])
    assert owner_table(None, {"name": "toy"}) == ("none", [])
    # one owner name, three docs whose stems collide: three distinct owners, never a merged one
    three = {"review_routes": [{"prefix": f"pkg/{n}.py", "owner": "core", "doc": f"repos/toy/components/{n}/rules.md"}
                               for n in ("a", "b", "c")]}
    assert [o.owner for o in owners_from_review_routes(three)] == ["core", "core/rules", "core/rules-2"]
    assert [o.path for o in owners_from_review_routes(three)] == [f"repos/toy/components/{n}/rules.md" for n in "abc"]
    import pytest

    with pytest.raises(ValueError):
        owner_table("schema_version: 2\nowners: []\n", manifest)   # never silently replaced by the manifest


def test_a_malformed_routes_file_blocks_at_the_shared_input_boundary(world):
    """Every stage reads its owner table in ``_Stage._inputs``; a routes file
    this copilot cannot read blocks there, before any model call, instead of
    escaping as a ValueError (the skeleton is the stage with no earlier chain
    to satisfy; the later stages share the same path)."""
    _commit(world["origin"], {"knowledge/repos/toy/_routes.yaml": "schema_version: 2\nowners: []\n"},
            "a routes file this copilot does not read")
    gateway = FakeGateway()
    record = run_stage(_runtime(world, gateway), _lifecycle(), "skeleton", dry_run=True)
    assert record.status == "blocked"
    assert record.problems == ["repos/toy/_routes.yaml is not a valid route table: unsupported _routes.yaml "
                               "schema_version 2"]
    assert gateway.calls == []
    assert review_route_line("tests/", "core", "repos/toy/components/core/rules.md") == \
        "review_routes (adapter PR): {prefix: tests/, owner: core, doc: repos/toy/components/core/rules.md}"


# -- skeleton ----------------------------------------------------------------------------

def test_skeleton_writes_no_routes_file_and_places_rules_on_the_manifest_owner(world):
    _manifest_routed_kb(world)
    gateway = ManifestGateway(doc_rules=[DOC_RULE, DOC_RULE2, DOCS_ONLY_RULE])
    record = run_stage(_runtime(world, gateway), _toy(), "skeleton", dry_run=True)
    assert record.status == "dry_run", record.problems
    tree = _tree(record)
    assert "knowledge/repos/toy/_routes.yaml" not in tree
    # the briefing doc is untouched (a dry-run snapshot holds changed files only);
    # init's rules went to the owner page the manifest routes to
    assert "knowledge/repos/toy/rules.md" not in tree
    core = Page.parse(tree["knowledge/repos/toy/components/core/rules.md"])
    placed = {s.rule_id: s.text for s in core.rules()}
    assert "pkg/util.py" in placed["TOY-I1"] and "pkg/core.py" in placed["TOY-I2"]
    assert "## Direct 代码快速入口" in tree["knowledge/repos/toy/components/core/rules.md"]
    # a rule about nothing the manifest routes keeps init's own page, never the briefing doc
    own = Page.parse(tree["knowledge/repos/toy/rules-init.md"])
    assert [s.rule_id for s in own.rules()] == ["TOY-I3"] and "docs/" in own.rules()[0].text
    assert "](rules-init.md)" in tree["knowledge/repos/toy/_index.md"]
    assert any("repos/toy/rules.md is a briefing doc" in c for c in record.checklist)
    # the generator's proposal became the exact review_routes entry the manifest lacks
    assert review_route_line("tests/", "core", "repos/toy/components/core/rules.md") in record.checklist
    assert not any("{prefix: pkg/" in c for c in record.checklist)
    assert any(c.startswith("no route reaches repos/toy/rules-seed-other-rules.md: add a review_routes entry")
               for c in record.checklist)
    assert any(n.startswith("routes come from the adapter manifest") for n in record.notes)
    body = (Path(record.pr["dry_run_dir"]) / "PR_BODY.md").read_text(encoding="utf-8")
    assert "review_routes (adapter PR): {prefix: tests/" in body


def test_a_knowledge_routed_repository_is_unchanged(world):
    """The toy of the other suites: no manifest routes, so the skeleton still
    writes the routes file and its rules page."""
    record = run_stage(_runtime(world, FakeGateway()), _lifecycle(), "skeleton", dry_run=True)
    assert record.status == "dry_run", record.problems
    tree = _tree(record)
    assert "knowledge/repos/toy/_routes.yaml" in tree and "knowledge/repos/toy/rules.md" in tree
    assert not any("review_routes (adapter PR)" in c for c in record.checklist)


# -- modules ---------------------------------------------------------------------------------

class ManifestCardGateway(ManifestGateway):
    def call_json(self, role, *, system, prompt, validate=None, max_budget_usd=None):
        if system != SYSTEM_CARD:
            return super().call_json(role, system=system, prompt=prompt, validate=validate,
                                     max_budget_usd=max_budget_usd)
        self.calls.append({"role": role.name, "system": system, "prompt": prompt, "max_budget_usd": max_budget_usd})
        payload = json.loads(prompt.split("\n", 1)[1].rsplit("</untrusted_data>", 1)[0])
        files = [f["path"] for f in payload["files"]]
        data = {"title": f"Module {payload['module']}", "purpose": "Checks worker configs before a tick runs.",
                "entry_points": [{"path": files[0], "what": "the entry"}], "key_files": [], "docs": [],
                "signals": ["lint"], "group": "tooling", "group_title": "Tooling", "headings": {}}
        if validate is not None:
            validate(data)
        return ModelReply(role, data, json.dumps(data), role.model, {}, 0.1, cost_usd=0.01)


def test_modules_suggests_review_routes_instead_of_writing_them(world):
    _manifest_routed_kb(world)
    _commit(world["upstream"], TOOLS, "tools")
    gateway = ManifestCardGateway(doc_rules=[])
    skeleton = run_stage(_runtime(world, gateway), _toy(), "skeleton", dry_run=True)
    assert skeleton.status == "dry_run", skeleton.problems
    record = run_stage(_runtime(world, gateway), _toy(), "modules", dry_run=True)
    assert record.status == "dry_run", record.problems
    tree = _tree(record)
    assert "knowledge/repos/toy/_routes.yaml" not in tree
    # cards and their group are written; the routes they would have taken are suggested
    assert "knowledge/repos/toy/components/tooling/tools-lint.md" in tree
    assert "](tooling/_index.md)" in tree["knowledge/repos/toy/components/_index.md"]
    suggested = [c for c in record.checklist if c.startswith("review_routes (adapter PR)")]
    assert review_route_line("tools/lint/", "tooling", "repos/toy/components/tooling/_index.md") in suggested
    assert review_route_line("tools/fmt/", "tooling", "repos/toy/components/tooling/_index.md") in suggested
    assert review_route_line("tools/gen/", "tooling", "repos/toy/components/tooling/_index.md") in suggested
    assert record.coverage["routes_source"] == "manifest"
    assert record.coverage["modules"]["before"] < 1 and record.coverage["modules"]["after"] == 1
    assert any("3 review_routes entries are suggested" in n for n in record.notes)
    body = (Path(record.pr["dry_run_dir"]) / "PR_BODY.md").read_text(encoding="utf-8")
    assert "Routes come from the adapter manifest" in body


# -- deepen ----------------------------------------------------------------------------------

EMPTY_CORE_RULES = ('---\ntitle: "Core rules"\ncreated: 2026-09-01\nupdated: 2026-09-01\ntype: rule\n'
                    "tags: [toy]\nsources: []\n---\n\n# Core rules\n\n"
                    "## Direct 代码快速入口\n\n| PR 描述在做什么 | 精确规则 | 第一批 live 源码 |\n|---|---|---|\n"
                    "| engine tick | (none yet) | `pkg/core.py` |\n")


class ManifestCodeGateway(CodeGateway):
    """Map proposals as ManifestGateway's; code rules as CodeGateway's."""

    def call_json(self, role, *, system, prompt, validate=None, max_budget_usd=None):
        reply = super().call_json(role, system=system, prompt=prompt, validate=validate,
                                  max_budget_usd=max_budget_usd)
        if system == SYSTEM_MAP:
            reply.data["owners"] = [{"owner": "core", "title": "Core", "page": "repos/toy/components/core/rules.md",
                                     "signals": ["engine"], "scope_prefixes": ["pkg/"]}]
        return reply


def test_deepen_writes_onto_the_manifest_owner_page_and_still_flips(world):
    _manifest_routed_kb(world, core_rules=EMPTY_CORE_RULES)
    _commit(world["upstream"], TOOLS, "tools")
    _commit(world["upstream"], {"pkg/util.py": "def helper():\n    return 2\n\n# tick helper\n"}, "util")
    gateway = ManifestCodeGateway(doc_rules=[], seed_rules=False)
    for stage in ("skeleton", "modules"):
        record = run_stage(_runtime(world, gateway), _toy(seeds=()), stage, dry_run=True)
        assert record.status in ("dry_run", "empty"), (stage, record.problems)
    record = run_stage(_runtime(world, gateway), _toy(seeds=()), "deepen", dry_run=True)
    assert record.status == "dry_run", record.problems
    tree = _tree(record)
    assert "knowledge/repos/toy/_routes.yaml" not in tree
    core = Page.parse(tree["knowledge/repos/toy/components/core/rules.md"])
    assert [s.rule_id for s in core.rules()] and PKG_RULE["title"] in core.rules()[0].text
    assert "knowledge/repos/toy/rules.md" not in tree     # the briefing doc is never written to
    assert "enabled: true" in tree["adapters/toy/manifest.yaml"]
    assert record.coverage["routes_source"] == "manifest"
    shown = [json.loads(c["prompt"].split("\n", 1)[1].rsplit("</untrusted_data>", 1)[0])
             for c in gateway.calls if c["system"] == SYSTEM_CODE_RULES]
    assert [p["module"] for p in shown] == ["pkg/"]     # the tools modules are unrouted: no group to deepen
    assert any("no route reaches" in n and "(modules stage)" in n for n in record.notes)


def test_deepen_without_any_routes_blocks(world):
    _commit(world["origin"], {"adapters/toy/manifest.yaml": "name: toy\nrepo:\n  full_name: o/toy\n  language: python\n"
                              "knowledge:\n  repo_subdir: repos/toy\nknowledge_lifecycle:\n  enabled: false\n  mode: shadow\n"},
            "adapter without routes")
    gateway = CodeGateway(doc_rules=[])
    for stage in ("skeleton", "modules"):
        record = run_stage(_runtime(world, gateway), _toy(seeds=()), stage, dry_run=True)
        assert record.status in ("dry_run", "empty"), (stage, record.problems)
    # drop the routes file the skeleton wrote from its dry-run snapshot: the
    # deepen stage then finds no routes file and no review_routes
    routes = Path(world["tmp"]) / "state" / "init" / "toy" / "skeleton-dryrun" / "tree" / "knowledge/repos/toy/_routes.yaml"
    routes.unlink()
    record = run_stage(_runtime(world, gateway), _toy(seeds=()), "deepen", dry_run=True)
    assert record.status == "blocked"
    assert "declares no review_routes" in record.problems[0]


# -- gate findings on this change -----------------------------------------------------

DIR_RULE = {"title": "The package is reviewed as one unit",
            "body": "- 强制：a change under `pkg/` is reviewed together with its guide.",
            "evidence": [{"path": "docs/guide.md", "start": 1, "end": 2}]}


def test_a_rule_naming_a_directory_reaches_the_owner_of_that_directory():
    """``claims_in`` strips the trailing slash of ``pkg/``; the manifest
    prefix keeps it. The directory still reaches its owner."""
    core = Owner("core", "repos/toy/components/core/rules.md", ("pkg/",))
    assert routes_file("pkg", [core]) == [core] and most_specific("pkg", [core]) == [core]
    assert routes_file("pkg/core.py", [core]) == [core]
    assert routes_file("pkgs", [core]) == [] and routes_file("pk", [core]) == []


def test_a_directory_rule_with_docs_evidence_lands_on_the_manifest_owner(world):
    _manifest_routed_kb(world)
    gateway = ManifestGateway(doc_rules=[DIR_RULE], seed_rules=False)
    record = run_stage(_runtime(world, gateway), _toy(seeds=()), "skeleton", dry_run=True)
    assert record.status == "dry_run", record.problems
    tree = _tree(record)
    core = Page.parse(tree["knowledge/repos/toy/components/core/rules.md"])
    assert any(DIR_RULE["title"] in s.text for s in core.rules())
    assert "knowledge/repos/toy/rules.md" not in tree and "knowledge/repos/toy/rules-init.md" not in tree


BRIEFING_OWNER_MANIFEST = MANIFEST.replace("doc: repos/toy/components/core/rules.md", "doc: repos/toy/rules.md")
EMPTY_TOY_RULES = ('---\ntitle: "Toy rules"\ncreated: 2026-09-01\nupdated: 2026-09-01\ntype: rule\n'
                   "tags: [toy]\nsources: []\n---\n\n# Toy rules\n\nNothing yet.\n")


def test_rules_redirected_beside_a_briefing_doc_count_as_its_owners(world):
    """The manifest routes ``pkg/`` to the top-level rule page, a briefing doc
    init never appends to: deepen writes to ``rules-init.md`` beside it, and
    coverage must see that page as the owner's, or deepen would regenerate
    forever."""
    _commit(world["origin"], {
        "adapters/toy/manifest.yaml": BRIEFING_OWNER_MANIFEST,
        "knowledge/repos/toy/_index.md": _index("Toy", "toy", "- [Toy rules](rules.md)\n"),
        "knowledge/repos/toy/rules.md": EMPTY_TOY_RULES,
    }, "toy routes to its briefing doc")
    _commit(world["upstream"], TOOLS, "tools")
    _commit(world["upstream"], {"pkg/util.py": "def helper():\n    return 2\n\n# tick helper\n"}, "util")
    gateway = ManifestCodeGateway(doc_rules=[], seed_rules=False)
    for stage in ("skeleton", "modules"):
        record = run_stage(_runtime(world, gateway), _toy(seeds=()), stage, dry_run=True)
        assert record.status in ("dry_run", "empty"), (stage, record.problems)
    record = run_stage(_runtime(world, gateway), _toy(seeds=()), "deepen", dry_run=True)
    assert record.status == "dry_run", record.problems
    tree = _tree(record)
    assert "knowledge/repos/toy/rules.md" not in tree
    beside = Page.parse(tree["knowledge/repos/toy/rules-init.md"])
    assert [s.rule_id for s in beside.rules()]
    cov = record.coverage["pr_rule_bearing"]
    assert cov["after"] > cov["before"], cov
    assert not any("target not reached" in n and "0%" in n for n in record.notes)
