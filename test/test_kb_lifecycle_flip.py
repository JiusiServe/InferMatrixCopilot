"""An adapter manifest edit may change only the named lifecycle keys (kb init §9.3)."""

from __future__ import annotations

from infermatrix_copilot.kb_service.lifecycle_flip import (
    CALIBRATION_KEYS, FLIP_KEYS, check_flip_to_shadow, check_lifecycle_flip,
)

BASE = """\
repo:
  full_name: o/r   # the upstream
knowledge_lifecycle:
  enabled: false
  mode: shadow
  knowledge_dir: repos/r
  release: {trigger: none}
"""


def test_flip_to_shadow_is_accepted_with_comments_kept():
    head = BASE.replace("enabled: false", "enabled: true  # kb init PR 3")
    assert check_flip_to_shadow(BASE, head) == []


def test_mode_may_be_left_to_its_default():
    base = BASE.replace("  mode: shadow\n", "")
    assert check_flip_to_shadow(base, base.replace("enabled: false", "enabled: true")) == []


def test_flip_must_turn_on_shadow():
    assert check_flip_to_shadow(BASE, BASE) == ["knowledge_lifecycle.enabled must be true"]
    head = BASE.replace("enabled: false", "enabled: true").replace("mode: shadow", "mode: auto_merge")
    assert check_flip_to_shadow(BASE, head) == ["knowledge_lifecycle.mode must be shadow"]


def test_any_other_change_is_refused():
    head = BASE.replace("enabled: false", "enabled: true").replace("trigger: none", "trigger: github_release")
    problems = check_flip_to_shadow(BASE, head)
    assert problems and "knowledge_lifecycle.release.trigger" in problems[0]
    head = BASE.replace("enabled: false", "enabled: true") + "push: {allowed: true}\n"
    assert "manifest key push changed" in check_flip_to_shadow(BASE, head)[0]
    head = BASE.replace("full_name: o/r", "full_name: o/other")
    assert "repo.full_name" in check_lifecycle_flip(BASE, head, allowed=FLIP_KEYS)[0]


def test_calibration_set_edit():
    head = BASE.replace("  knowledge_dir", "  calibration_set: kb-calibration\n  knowledge_dir")
    assert check_lifecycle_flip(BASE, head, allowed=CALIBRATION_KEYS) == []
    assert check_lifecycle_flip(BASE, head, allowed=FLIP_KEYS)


def test_unparseable_manifests_are_problems():
    assert "not valid YAML" in check_lifecycle_flip(BASE, "a: [", allowed=FLIP_KEYS)[0]
    assert "not a mapping" in check_lifecycle_flip("- 1\n", BASE, allowed=FLIP_KEYS)[0]


def test_yaml_aliases_cannot_hide_a_change():
    base = BASE + "other: &x {enabled: false}\nmirror: *x\n"
    head = base.replace("enabled: false}", "enabled: true}")
    problems = check_lifecycle_flip(base, head, allowed=FLIP_KEYS)
    assert any("other.enabled" in p for p in problems)
    shared = "knowledge_lifecycle: &lc {enabled: false, mode: shadow}\ncopy: *lc\n"
    flipped = "knowledge_lifecycle: &lc {enabled: true, mode: shadow}\ncopy: *lc\n"
    assert any("copy.enabled" in p for p in check_flip_to_shadow(shared, flipped))


def test_value_types_are_compared_strictly():
    base = BASE.replace("  knowledge_dir", "  calibration_set: 1\n  knowledge_dir")
    head = base.replace("enabled: false", "enabled: true").replace("calibration_set: 1", "calibration_set: true")
    assert "knowledge_lifecycle.calibration_set" in check_flip_to_shadow(base, head)[0]
    lists = "xs: [1, 2]\nys: {a: 1}\n"
    assert "xs[1]" in check_lifecycle_flip(lists, "xs: [1, 2.0]\nys: {a: 1}\n", allowed=FLIP_KEYS)[0]
    assert "xs" in check_lifecycle_flip(lists, "xs: [1]\nys: {a: 1}\n", allowed=FLIP_KEYS)[0]
    keyed = "m: {1: a}\n"
    assert check_lifecycle_flip(keyed, "m: {true: a}\n", allowed=FLIP_KEYS)
    unchanged = "x: .nan\nxs: [1, {k: [true]}]\n"
    assert check_lifecycle_flip(unchanged, unchanged, allowed=FLIP_KEYS) == []


def test_recursive_alias_is_a_problem():
    loop = "a: &a [*a]\n"
    assert "recursive alias" in check_lifecycle_flip(loop, loop, allowed=FLIP_KEYS)[0]
