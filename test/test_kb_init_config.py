"""kb init: the adapter's knowledge_lifecycle.init block (design kb-init §3)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from infermatrix_copilot.adapters.base import RepoAdapter
from infermatrix_copilot.kb_service.config import (
    DEFAULT_DOC_GLOBS, InitConfig, LifecycleConfigError, parse_lifecycle, validate_seeds,
)


def _adapter(tmp_path: Path, init: object = None, *, extra: dict | None = None,
             with_init: bool = True) -> RepoAdapter:
    root = tmp_path / "demo_adapter"
    root.mkdir(exist_ok=True)
    section: dict = {"enabled": False, "mode": "shadow"}
    if with_init:
        section["init"] = init
    manifest = {
        "name": "demo_adapter",
        "repo": {"full_name": "org/demo", "path": "/x"},
        "knowledge": {"repo_subdir": "repos/demo"},
        "knowledge_lifecycle": section,
        **(extra or {}),
    }
    (root / "manifest.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    return RepoAdapter(name="demo_adapter", root=root, manifest=manifest)


def test_absent_init_is_none(tmp_path):
    assert parse_lifecycle(_adapter(tmp_path, with_init=False)).init is None


def test_empty_init_gets_defaults(tmp_path):
    init = parse_lifecycle(_adapter(tmp_path, {})).init
    assert init == InitConfig()
    assert init.doc_globs == DEFAULT_DOC_GLOBS
    assert (init.module_depth, init.min_module_loc) == (2, 300)
    assert (init.pr_window_count, init.pr_window_max_age_days) == (200, 180)
    assert (init.coverage_target, init.budget_usd, init.judge_call_usd) == (0.85, 30.0, 0.50)
    assert init.seeds == init.source_roots == init.exclude == ()


def test_full_init_parses(tmp_path):
    init = parse_lifecycle(_adapter(tmp_path, {
        "seeds": ["general/review/x.md", "repos/other/ci"],
        "doc_globs": ["README.md"],
        "source_roots": ["pkg/"],
        "exclude": ["*/tests/*"],
        "module_depth": 3,
        "min_module_loc": 0,
        "pr_window": {"count": 50, "max_age_days": 30},
        "coverage_target": 1,
        "budget_usd": 5,
        "judge_call_usd": 0,
    })).init
    assert init.seeds == ("general/review/x.md", "repos/other/ci")
    assert init.doc_globs == ("README.md",)
    assert init.source_roots == ("pkg/",)
    assert init.exclude == ("*/tests/*",)
    assert (init.module_depth, init.min_module_loc) == (3, 0)
    assert (init.pr_window_count, init.pr_window_max_age_days) == (50, 30)
    assert (init.coverage_target, init.budget_usd, init.judge_call_usd) == (1.0, 5.0, 0.0)


def test_source_roots_default_to_ut_coverage(tmp_path):
    adapter = _adapter(tmp_path, {}, extra={"ut_coverage": {"source_roots": ["pkg/", "csrc/"]}})
    assert parse_lifecycle(adapter).init.source_roots == ("pkg/", "csrc/")
    adapter = _adapter(tmp_path, {"source_roots": ["only/"]},
                       extra={"ut_coverage": {"source_roots": ["pkg/"]}})
    assert parse_lifecycle(adapter).init.source_roots == ("only/",)


@pytest.mark.parametrize("init, message", [
    ("nope", "must be a mapping"),
    ({"surprise": 1}, "unknown keys"),
    ({"pr_window": {"count": 1, "days": 2}}, "unknown keys"),
    ({"seeds": "general/x.md"}, "list of non-empty strings"),
    ({"seeds": [""]}, "list of non-empty strings"),
    ({"seeds": ["general/x.md", "general/x.md"]}, "duplicates"),
    ({"seeds": ["repos/demo/rules.md"]}, "names the repository being initialised"),
    ({"seeds": ["/abs/general/x.md"]}, "relative knowledge path"),
    ({"seeds": ["general/../repos/demo/x.md"]}, "relative knowledge path"),
    ({"seeds": ["general//x.md"]}, "relative knowledge path"),
    ({"seeds": ["skills/x.md"]}, "general/ or repos/"),
    ({"seeds": ["repos"]}, "general/ or repos/"),
    ({"seeds": ["repos/Bad Name/x.md"]}, "general/ or repos/"),
    ({"doc_globs": [1]}, "list of non-empty strings"),
    ({"exclude": "x"}, "list of non-empty strings"),
    ({"module_depth": 0}, "module_depth must be an integer >= 1"),
    ({"module_depth": True}, "module_depth must be an integer"),
    ({"min_module_loc": -1}, "min_module_loc must be an integer >= 0"),
    ({"min_module_loc": 1.5}, "min_module_loc must be an integer"),
    ({"pr_window": {"count": 0}}, "pr_window.count"),
    ({"pr_window": {"max_age_days": 0}}, "pr_window.max_age_days"),
    ({"coverage_target": 0}, "coverage_target must be in"),
    ({"coverage_target": 1.01}, "coverage_target must be in"),
    ({"coverage_target": "high"}, "coverage_target must be a finite number"),
    ({"budget_usd": 0}, "budget_usd must be > 0"),
    ({"budget_usd": True}, "budget_usd must be a finite number"),
    ({"judge_call_usd": -0.1}, "judge_call_usd must be >= 0"),
    ({"budget_usd": float("nan")}, "budget_usd must be a finite number"),
    ({"budget_usd": float("inf")}, "budget_usd must be a finite number"),
    ({"judge_call_usd": float("nan")}, "judge_call_usd must be a finite number"),
    ({"judge_call_usd": float("inf")}, "judge_call_usd must be a finite number"),
    ({"coverage_target": float("nan")}, "coverage_target must be a finite number"),
])
def test_invalid_init_is_rejected(tmp_path, init, message):
    with pytest.raises(LifecycleConfigError, match=message):
        parse_lifecycle(_adapter(tmp_path, init))


def test_non_finite_yaml_values_are_rejected(tmp_path):
    adapter = _adapter(tmp_path, {})
    adapter.manifest["knowledge_lifecycle"]["init"] = yaml.safe_load("budget_usd: .inf")
    with pytest.raises(LifecycleConfigError, match="finite"):
        parse_lifecycle(adapter)


def test_validate_seeds_reports_missing_paths(tmp_path):
    root = tmp_path / "knowledge"
    (root / "general" / "review").mkdir(parents=True)
    (root / "general" / "review" / "x.md").write_text("x", encoding="utf-8")
    (root / "repos" / "other" / "ci").mkdir(parents=True)
    ok = InitConfig(seeds=("general/review/x.md", "repos/other/ci"))
    assert validate_seeds(ok, root) == []
    missing = InitConfig(seeds=("general/review/x.md", "repos/other/gone.md"))
    assert validate_seeds(missing, root) == ["seed repos/other/gone.md does not exist in the knowledge tree"]


def test_validate_seeds_refuses_escape(tmp_path):
    root = tmp_path / "knowledge"
    root.mkdir()
    (tmp_path / "outside.md").write_text("x", encoding="utf-8")
    (root / "general").mkdir()
    (root / "general" / "link.md").symlink_to(tmp_path / "outside.md")
    assert validate_seeds(InitConfig(seeds=("general/link.md",)), root) == [
        "seed general/link.md escapes the knowledge root"]
