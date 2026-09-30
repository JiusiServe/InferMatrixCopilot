"""Owner specificity in kb init (found by the afd-plugin pilot, 2026-09-30).

A catch-all prefix (``pkg/``) reaches every file a component owner
(``pkg/sub/``) reaches. The pilot's modules stage absorbed the package root by
appending ``pkg/`` to an aggregate owner, the deepen stage then wrote one
module's rules to that owner's page, and rule-bearing coverage read 100%:
every file counted because SOME matching owner had rules. Coverage, absorption
and deepen now all go by the MOST specific owner.
"""

from __future__ import annotations

from infermatrix_copilot.kb_service.init_coverage import (
    Owner, make_include, most_specific, pr_weighted_coverage, shadowing,
)
from infermatrix_copilot.kb_service.init_deepen import _Deepen
from infermatrix_copilot.kb_service.init_modules import cover_prefixes

AGG = Owner("components", "repos/r/components/_index.md", ("pkg/connectors/", "pkg/models/", "pkg/"))
CONN = Owner("connectors", "repos/r/components/connectors/_index.md", ("pkg/connectors/",))
MODELS = Owner("models", "repos/r/components/models/_index.md", ("pkg/models/",))
WORKER = Owner("worker", "repos/r/components/worker/_index.md", ("pkg/worker/runner.py",))
OWNERS = [AGG, CONN, MODELS, WORKER]


def test_the_longest_prefix_wins_and_a_deeper_page_breaks_a_tie():
    assert most_specific("pkg/connectors/cam.py", OWNERS) == [CONN]      # same prefix: deeper page
    assert most_specific("pkg/worker/runner.py", OWNERS) == [WORKER]     # a file beats pkg/
    assert most_specific("pkg/plugin.py", OWNERS) == [AGG]               # only the catch-all
    assert most_specific("other/x.py", OWNERS) == []
    twins = [Owner("a", "repos/r/a/_index.md", ("pkg/x/",)), Owner("b", "repos/r/b/_index.md", ("pkg/x/",))]
    assert most_specific("pkg/x/y.py", twins) == twins                   # a real tie keeps both


def test_rules_on_a_catch_all_page_do_not_make_component_files_rule_bearing():
    prs = [["pkg/connectors/cam.py", "pkg/models/llama.py"], ["pkg/worker/runner.py"], ["pkg/plugin.py"]]
    include = make_include(["pkg/"], [])
    on_catch_all = pr_weighted_coverage(prs, OWNERS, include=include, rule_pages={AGG.path})
    assert on_catch_all.routed == 4 and on_catch_all.rule_bearing == 1          # only pkg/plugin.py
    on_component = pr_weighted_coverage(prs, OWNERS, include=include, rule_pages={CONN.path})
    assert on_component.rule_bearing == 1 and on_component.rule_bearing_ratio == 0.25


def test_shadowing_names_every_prefix_that_is_an_ancestor_of_another_owners():
    found = {(o, p, other) for o, p, other, _ in shadowing(OWNERS)}
    assert ("components", "pkg/", "connectors") in found
    assert ("components", "pkg/", "worker") in found
    assert not any(o == "connectors" for o, _, _ in found)
    # a file prefix is never an ancestor
    assert shadowing([Owner("a", "p.md", ("pkg/x.py",)), Owner("b", "q.md", ("pkg/x.py.bak",))]) == []


# -- absorption never swallows another module or owner ---------------------------------

MODULES = {
    "pkg/": {"files": ["pkg/plugin.py", "pkg/config.py", "pkg/utils/a.py", "pkg/utils/b.py"]},
    "pkg/connectors/": {"files": ["pkg/connectors/cam.py"]},
    "pkg/models/": {"files": ["pkg/models/llama.py"]},
    "pkg/worker/": {"files": ["pkg/worker/runner.py", "pkg/worker/dbo.py"]},
}
ALL = sorted(f for m in MODULES.values() for f in m["files"])


def test_a_package_root_with_child_modules_is_covered_by_its_own_files_only():
    owners = [CONN, MODELS, WORKER]
    cover = cover_prefixes("pkg/", MODULES["pkg/"]["files"], ALL, owners, MODULES,
                           members=MODULES["pkg/"]["files"], owner="connectors")
    assert cover == ["pkg/config.py", "pkg/plugin.py", "pkg/utils/"]
    assert "pkg/" not in cover


def test_a_module_directory_is_used_only_when_no_other_owner_sits_inside_it():
    files = MODULES["pkg/worker/"]["files"]
    blocked = cover_prefixes("pkg/worker/", ["pkg/worker/dbo.py"], ALL, [WORKER, CONN], MODULES,
                             members=files, owner="connectors")
    assert blocked == ["pkg/worker/dbo.py"]            # worker's own file prefix sits in pkg/worker/
    extending = cover_prefixes("pkg/worker/", ["pkg/worker/dbo.py"], ALL, [WORKER, CONN], MODULES,
                               members=files, owner="worker")
    assert extending == ["pkg/worker/"]                # the owner widening its own area is fine


def test_the_repository_root_module_is_never_one_prefix():
    modules = {"./": {"files": ["setup.py", "tools/gen.py"]}, "pkg/": {"files": ["pkg/a.py"]}}
    cover = cover_prefixes("./", ["setup.py", "tools/gen.py"], ["pkg/a.py", "setup.py", "tools/gen.py"],
                           [], modules)
    assert cover == ["setup.py", "tools/"]


# -- deepen targets the most specific owner ---------------------------------------------

def test_deepen_gives_a_component_module_to_its_component_owner():
    assert _Deepen._owner(MODULES["pkg/connectors/"]["files"], OWNERS) == CONN
    assert _Deepen._owner(["pkg/worker/runner.py", "pkg/worker/dbo.py"], OWNERS + [
        Owner("platforms", "repos/r/components/platforms/_index.md", ("pkg/worker/dbo.py",))]).owner in {
        "worker", "platforms"}
    assert _Deepen._owner(MODULES["pkg/"]["files"], OWNERS) == AGG


def test_the_pilot_shape_keeps_coverage_honest():
    """The afd-plugin pilot, in miniature: an aggregate owner listing its
    components' prefixes, component owners, and a package root absorbed into
    the owner that owns most of its files most specifically. One module's
    rules must not read as full coverage."""
    owners = [Owner("components", "repos/r/components/_index.md", ("pkg/connectors/", "pkg/models/")),
              CONN, MODELS, WORKER]
    root = MODULES["pkg/"]["files"]
    cover = cover_prefixes("pkg/", root, ALL, owners, MODULES, members=root, owner="components")
    assert "pkg/" not in cover                       # the pilot appended exactly this
    owners[0] = Owner(owners[0].owner, owners[0].path, owners[0].prefixes + tuple(cover))
    prs = [["pkg/connectors/cam.py"], ["pkg/models/llama.py"], ["pkg/worker/runner.py"],
           ["pkg/plugin.py", "pkg/utils/a.py"], ["pkg/connectors/cam.py"]]
    include = make_include(["pkg/"], [])
    before = pr_weighted_coverage(prs, owners, include=include, rule_pages=set())
    hottest = _Deepen._owner(MODULES["pkg/connectors/"]["files"], owners)
    assert hottest == CONN                           # not the aggregate that also lists pkg/connectors/
    after = pr_weighted_coverage(prs, owners, include=include, rule_pages={hottest.path})
    assert before.rule_bearing_ratio == 0.0
    assert 0 < after.rule_bearing_ratio < 1.0
    assert after.rule_bearing == 2                   # the two cam.py changes only


def test_the_skeleton_flags_an_owner_prefix_that_shadows_others():
    from types import SimpleNamespace

    from infermatrix_copilot.kb_service.init_stages import _Skeleton

    stage = SimpleNamespace(record=SimpleNamespace(checklist=[]))
    _Skeleton._note_shadowing(stage, [
        {"owner": "components", "path": AGG.path, "scope_prefixes": ["pkg/"]},
        {"owner": "connectors", "path": CONN.path, "scope_prefixes": ["pkg/connectors/"]},
        {"owner": "models", "path": MODELS.path, "scope_prefixes": ["pkg/models/"]},
    ])
    assert stage.record.checklist == [
        "owner components: prefix pkg/ is an ancestor of the prefixes of connectors, models; "
        "those files count for the more specific owner only — narrow it if it is a catch-all"]
