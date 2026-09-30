"""kb init coverage (design kb-init v3 §7): depth-bounded module scan, module
coverage, PR-weighted routed / rule-bearing coverage, churn ordering."""

import pytest

from infermatrix_copilot.kb_service import init_coverage as cov
from infermatrix_copilot.profiles import establish
from infermatrix_copilot.profiles.establish import scan_modules_at_depth


def _write(root, rel, lines):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"x{i} = {i}\n\n" for i in range(lines)))


def _tree(tmp_path):
    _write(tmp_path, "pkg/__init__.py", 2)
    _write(tmp_path, "pkg/big/a.py", 40)
    _write(tmp_path, "pkg/big/deep/er/b.py", 30)   # below depth 2: owned by pkg/big/deep/
    _write(tmp_path, "pkg/big/deep/c.py", 30)
    _write(tmp_path, "pkg/small/d.py", 5)          # folds into pkg/
    _write(tmp_path, "pkg/tests/test_x.py", 50)
    _write(tmp_path, "pkg/docs/e.py", 50)          # non-code dir: skipped
    _write(tmp_path, "pkg/.hidden/f.py", 50)
    _write(tmp_path, "pkg/big/README.md", 50)      # not a source suffix
    _write(tmp_path, "other/g.py", 50)             # outside the source roots


def test_scan_depth_folding_and_exclude(tmp_path):
    _tree(tmp_path)
    modules = scan_modules_at_depth(tmp_path, "python", source_roots=["pkg/"], depth=2,
                                    min_loc=20, exclude=["*/tests/*"])
    assert modules == {
        "pkg/": {"files": ["pkg/__init__.py", "pkg/small/d.py"], "loc": 7},
        "pkg/big/": {"files": ["pkg/big/a.py"], "loc": 40},
        "pkg/big/deep/": {"files": ["pkg/big/deep/c.py", "pkg/big/deep/er/b.py"], "loc": 60},
    }


def test_scan_folds_until_stable_and_roots_never_fold(tmp_path):
    _write(tmp_path, "pkg/a/b/c.py", 5)
    _write(tmp_path, "pkg/a/d.py", 5)
    modules = scan_modules_at_depth(tmp_path, "python", source_roots=["pkg"], depth=2, min_loc=8)
    # pkg/a/b/ (5) -> pkg/a/ (10, stays); the root is kept whatever its size
    assert modules == {"pkg/a/": {"files": ["pkg/a/b/c.py", "pkg/a/d.py"], "loc": 10}}
    folded = scan_modules_at_depth(tmp_path, "python", source_roots=["pkg"], depth=2, min_loc=100)
    assert folded == {"pkg/": {"files": ["pkg/a/b/c.py", "pkg/a/d.py"], "loc": 10}}


def test_scan_repo_root_nested_roots_and_unknown_language(tmp_path):
    _write(tmp_path, "top.py", 3)
    _write(tmp_path, "lib/x.py", 3)
    _write(tmp_path, "lib/inner/y.py", 3)
    whole = scan_modules_at_depth(tmp_path, "python", source_roots=[], depth=1, min_loc=0)
    assert whole == {establish.ROOT_MODULE: {"files": ["top.py"], "loc": 3},
                     "lib/": {"files": ["lib/inner/y.py", "lib/x.py"], "loc": 6}}
    nested = scan_modules_at_depth(tmp_path, "python", source_roots=["lib", "lib/inner"],
                                   depth=0, min_loc=0)
    assert nested == {"lib/": {"files": ["lib/x.py"], "loc": 3},
                      "lib/inner/": {"files": ["lib/inner/y.py"], "loc": 3}}
    assert scan_modules_at_depth(tmp_path, "cobol", source_roots=[], depth=2, min_loc=0) == {}


def test_scan_is_deterministic(tmp_path):
    _tree(tmp_path)
    kwargs = dict(source_roots=["pkg/"], depth=2, min_loc=20)
    assert scan_modules_at_depth(tmp_path, "python", **kwargs) == \
        scan_modules_at_depth(tmp_path, "python", **kwargs)


ROUTES = """\
schema_version: 1
owners:
  - owner: core
    path: repos/r/components/core/rules.md
    signals: [core]
    scope_prefixes: [pkg/big/]
  - owner: misc
    path: repos/r/components/misc/_index.md
    signals: [misc]
    scope_prefixes: [pkg/small/, pkg/big/deep/]
models:
  dir: repos/r/models
"""


def test_load_owners_and_routing_order():
    owners = cov.load_owners(ROUTES)
    assert [o.owner for o in owners] == ["core", "misc"]
    assert [o.owner for o in cov.routes_file("pkg/big/deep/c.py", owners)] == ["core", "misc"]
    assert cov.routes_file("pkg/none.py", owners) == []
    with pytest.raises(ValueError):
        cov.load_owners("schema_version: 2\nowners: []\n")
    with pytest.raises(ValueError):
        cov.load_owners("owners:\n  - owner: x\n")
    with pytest.raises(ValueError):
        cov.load_owners("owners:\n  - {owner: x, path: p, scope_prefixes: ['']}\n")


def test_module_coverage_needs_every_file_routed():
    owners = cov.load_owners(ROUTES)
    modules = {"pkg/": {"files": ["pkg/__init__.py", "pkg/small/d.py"]},
               "pkg/big/": {"files": ["pkg/big/a.py"]}}
    result = cov.module_coverage(modules, owners)
    assert result.covered == ["pkg/big/"] and result.uncovered == ["pkg/"]
    assert result.ratio == 0.5
    assert cov.module_coverage({}, owners).ratio == 1.0


def test_pr_weighted_counts_once_per_pr_and_rule_bearing():
    owners = cov.load_owners(ROUTES)
    include = cov.make_include(["pkg/"], ["*/tests/*"], suffixes=[".py"])
    prs = [
        ["pkg/big/a.py", "pkg/big/a.py", "pkg/tests/test_x.py", "README.md"],
        ["pkg/big/a.py", "pkg/small/d.py", "pkg/new.py"],
        ["pkg/new.py", "pkg/other.py"],
    ]
    result = cov.pr_weighted_coverage(prs, owners, include=include,
                                      rule_pages={"repos/r/components/core/rules.md"})
    assert (result.total, result.routed, result.rule_bearing) == (6, 3, 2)
    assert result.routed_ratio == 0.5 and result.rule_bearing_ratio == pytest.approx(2 / 6)
    assert result.uncovered_hot == [("pkg/new.py", 2), ("pkg/other.py", 1)]
    bare = cov.pr_weighted_coverage(prs, owners, include=include)
    assert bare.rule_bearing == 0
    assert cov.pr_weighted_coverage([], owners, include=include).routed_ratio == 1.0


def test_make_include_without_roots_or_suffixes():
    include = cov.make_include([], ["docs/*"])
    assert include("anything/x.txt") and not include("docs/a.md")


def test_churn_by_module_uses_longest_prefix():
    modules = {cov.ROOT_MODULE: {}, "pkg/": {}, "pkg/big/": {}}
    prs = [["pkg/big/a.py", "pkg/x.py"], ["pkg/big/gone.py", "setup.py"], ["pkg/big/a.py"]]
    assert cov.churn_by_module(prs, modules) == [("pkg/big/", 3), ("./", 1), ("pkg/", 1)]
    assert cov.module_of("elsewhere.py", {"pkg/": {}}) is None


def test_root_module_constant_matches_profiles():
    assert cov.ROOT_MODULE == establish.ROOT_MODULE


@pytest.mark.parametrize("root", ["pkg", "pkg/", "./pkg", "./pkg/", "/pkg"])
def test_scan_normalizes_roots_and_folding_stops_at_the_root(tmp_path, root):
    _write(tmp_path, "pkg/a/x.py", 3)
    _write(tmp_path, "pkg/b/y.py", 3)
    modules = scan_modules_at_depth(tmp_path, "python", source_roots=[root], depth=1, min_loc=10_000)
    assert modules == {"pkg/": {"files": ["pkg/a/x.py", "pkg/b/y.py"], "loc": 6}}
    assert establish.normalize_root(root) == "pkg"


@pytest.mark.parametrize("root", [".", "./", "", "/"])
def test_scan_repo_root_spellings_terminate(tmp_path, root):
    _write(tmp_path, "a/x.py", 3)
    _write(tmp_path, "top.py", 3)
    modules = scan_modules_at_depth(tmp_path, "python", source_roots=[root, "a"], depth=1,
                                    min_loc=10_000)
    assert modules == {establish.ROOT_MODULE: {"files": ["a/x.py", "top.py"], "loc": 6}}


@pytest.mark.parametrize("root", [".", "./", ""])
def test_make_include_repo_root_spellings_admit_everything(root):
    owners = cov.load_owners(ROUTES)
    include = cov.make_include([root], [], suffixes=[".py"])
    assert include("pkg/big/a.py") and include("./pkg/new.py") and not include("README.md")
    result = cov.pr_weighted_coverage([["./pkg/big/a.py", "pkg/new.py"]], owners, include=include)
    assert (result.total, result.routed) == (2, 1)
    assert result.uncovered_hot == [("pkg/new.py", 1)]


def test_make_include_normalizes_named_roots():
    include = cov.make_include(["./pkg/"], [])
    assert include("pkg/x.py") and include("./pkg/x.py") and not include("pkgx/y.py")
