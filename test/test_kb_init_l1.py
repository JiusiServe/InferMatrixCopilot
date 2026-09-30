"""L1 bootstrap mode (kb init creates a repository's indexes) and the init-side
index link check (design kb init v3 §9.2, §9.3)."""

from __future__ import annotations

import re
from pathlib import Path

from infermatrix_copilot.knowledge_service.l1 import (
    Change, check_changeset, check_index_links,
)

PAGE = (
    "---\n"
    'title: "Demo rules"\n'
    "created: 2026-09-30\n"
    "updated: 2026-09-30\n"
    "type: rule\n"
    "tags: [demo]\n"
    "sources: []\n"
    "---\n\n"
    "# Demo rules\n"
)


def _base() -> dict[str, str]:
    return {
        "repos/_index.md": "# repos\n\n| repo | where |\n|---|---|\n| old | [old](old/_index.md) |\n",
        "repos/old/_index.md": "# old\n\n- [rules](rules.md)\n",
        "repos/old/rules.md": PAGE,
        "general/_index.md": "# general\n\n- [method](method.md)\n",
        "general/method.md": "# method\n",
    }


def _new_repo(base: dict[str, str]) -> dict[str, str]:
    head = dict(base)
    head["repos/_index.md"] = base["repos/_index.md"] + "| new | [new](new/_index.md) |\n"
    head["repos/new/_index.md"] = (
        "# new\n\n| page | when |\n|---|---|\n| [rules](rules.md) | always |\n"
        "| [core](core/_index.md) | core |\n\n- [method](../../general/method.md)\n"
    )
    head["repos/new/rules.md"] = PAGE
    head["repos/new/core/_index.md"] = "# core\n\n- [cards](cards.md)\n"
    head["repos/new/core/cards.md"] = "# cards\n"
    return head


def _changes(base: dict, head: dict) -> list[Change]:
    out = []
    for path in sorted(set(base) | set(head)):
        if base.get(path) == head.get(path):
            continue
        status = "A" if path not in base else "D" if path not in head else "M"
        out.append(Change(f"knowledge/{path}", status, "100644", "" if status == "D" else "100644"))
    return out


def _codes(result) -> set[str]:
    return {i.code for i in result.issues}


def test_new_directory_indexes_pass_only_in_bootstrap():
    base = _base()
    head = _new_repo(base)
    boot = check_changeset(base, head, _changes(base, head), bootstrap=True)
    assert boot.ok, boot.issues
    created = {b.path for b in boot.blocks if b.kind == "prose"}
    assert {"repos/new/_index.md", "repos/new/core/_index.md"} <= created
    plain = check_changeset(base, head, _changes(base, head))
    assert {"index_added_or_deleted", "path_not_whitelisted"} <= _codes(plain)


def test_default_mode_is_unchanged_for_an_existing_index():
    base = _base()
    head = {**base, "repos/old/extra.md": PAGE,
            "repos/old/_index.md": base["repos/old/_index.md"] + "- [extra](extra.md)\n"}
    assert check_changeset(base, head, _changes(base, head)).ok
    assert check_changeset(base, head, _changes(base, head), bootstrap=True).ok


def test_index_in_an_existing_directory_is_still_refused():
    base = _base()
    base.pop("repos/old/_index.md")
    head = {**base, "repos/old/_index.md": "# old\n\n- [rules](rules.md)\n"}
    result = check_changeset(base, head, _changes(base, head), bootstrap=True)
    assert "index_added_or_deleted" in _codes(result)


def test_created_index_must_link_its_pages_and_child_indexes():
    base = _base()
    head = _new_repo(base)
    head["repos/new/_index.md"] = "# new\n\n- [rules](rules.md)\n"
    result = check_changeset(base, head, _changes(base, head), bootstrap=True)
    missing = [i for i in result.issues if i.code == "index_missing"]
    assert [i.detail for i in missing] == ["repos/new/core/_index.md is not linked"]


def test_parent_index_must_link_the_created_index():
    base = _base()
    head = _new_repo(base)
    head["repos/_index.md"] = base["repos/_index.md"]
    result = check_changeset(base, head, _changes(base, head), bootstrap=True)
    assert any(i.code == "index_missing" and i.path == "repos/_index.md" for i in result.issues)


def test_deleting_an_index_is_refused_in_bootstrap():
    base = _base()
    head = dict(base)
    head.pop("repos/old/_index.md")
    result = check_changeset(base, head, _changes(base, head), bootstrap=True)
    assert "index_added_or_deleted" in _codes(result)


def test_repos_index_whitelist_is_edit_only():
    base = _base()
    head = _new_repo(base)
    changes = [c if c.path != "knowledge/repos/_index.md" else Change(c.path, "A", "", "100644")
               for c in _changes(base, head)]
    result = check_changeset(base, head, changes, bootstrap=True)
    assert "path_not_whitelisted" in _codes(result)


def test_index_links_accept_a_valid_bootstrap():
    base = _base()
    assert check_index_links(base, _new_repo(base)) == []


def test_index_links_report_broken_escaping_dropped_and_unlinked():
    base = _base()
    head = _new_repo(base)
    head["repos/new/_index.md"] += "- [gone](missing.md)\n- [out](../../../README.md)\n- [abs](/etc/x.md)\n"
    head["repos/old/_index.md"] = "# old\n"                      # dropped a link
    head["repos/new/core/orphan.md"] = "# orphan\n"               # new page, not linked
    issues = {(i.code, i.path, i.detail) for i in check_index_links(base, head)}
    assert ("index_link_broken", "repos/new/_index.md", "missing.md") in issues
    assert ("index_link_escapes", "repos/new/_index.md", "../../../README.md") in issues
    assert ("index_link_escapes", "repos/new/_index.md", "/etc/x.md") in issues
    assert ("index_link_dropped", "repos/old/_index.md", "rules.md") in issues
    assert any(code == "index_unlinked" and path == "repos/new/core/orphan.md"
               for code, path, _ in issues)


def test_index_links_read_titles_angles_and_reference_definitions():
    base = _base()
    head = _new_repo(base)
    head["repos/new/_index.md"] += (
        '- [out](../../../README.md "title")\n'
        "- [gone](<missing.md> 'title')\n"
        "- [ref][r]\n\n[r]: ../../../ref.md \"t\"\n"
        "[ok]: rules.md\n"
    )
    issues = {(i.code, i.detail) for i in check_index_links(base, head)}
    assert issues == {("index_link_escapes", "../../../README.md"),
                      ("index_link_broken", "missing.md"),
                      ("index_link_escapes", "../../../ref.md")}


def test_unused_reference_definitions_are_not_links():
    base = _base()
    head = _new_repo(base)
    head["repos/new/core/_index.md"] = "# core\n\n[c]: cards.md\n"   # defined, never used
    issues = {(i.code, i.path) for i in check_index_links(base, head)}
    assert ("index_unlinked", "repos/new/core/cards.md") in issues
    head["repos/new/core/_index.md"] = "# core\n\n- [Cards][c]\n\n[c]: cards.md\n"
    assert check_index_links(base, head) == []
    head["repos/new/core/_index.md"] = "# core\n\n- [c]\n\n[C]: cards.md\n"  # shortcut, case-folded
    assert check_index_links(base, head) == []


def test_code_never_hides_a_link_from_the_resolution_checks():
    """Every link-like text is resolved, even one that may sit in code."""
    base = _base()
    head = _new_repo(base)
    core = "repos/new/core/_index.md"
    for tail in (
        "```example```\n\n- [broken](missing.md)\n",           # inline code, not a fence
        "`` literal [broken](missing.md) `\n",                   # unmatched backticks
        "A literal ` here.\n\n[broken](missing.md)\n\nAnother literal ` here.\n",
        "\\` [broken](missing.md) `\n",                          # escaped backtick
        "- ```\n  example\n  ```\n\n[broken](missing.md)\n",     # fence inside a list
        "~~~\n- [broken](missing.md)\n",                          # inside a real fence
    ):
        head[core] = "# core\n\n- [cards](cards.md)\n\n" + tail
        assert {i.code for i in check_index_links(base, head)} == {"index_link_broken"}, tail


def test_only_certainly_visible_links_count_as_navigation():
    base = _base()
    head = _new_repo(base)
    core = "repos/new/core/_index.md"
    for text in (
        "# core\n\n`` a ```` [cards](cards.md) ``\n",          # unequal runs: inside code
        "# core\n\nsee `code\n[cards](cards.md)` here\n",       # span across a line break
        "# core\n\n```\n\n- [cards](cards.md)\n",                # after a fence-like line
        "# core\n\n[cards]`example`(cards.md)\n",                # not a link at all
    ):
        head[core] = text
        issues = {(i.code, i.path) for i in check_index_links(base, head)}
        assert ("index_unlinked", "repos/new/core/cards.md") in issues, text
    # a table cell is its own block: code in another cell does not matter
    head[core] = "# core\n\n| page | note |\n|---|---|\n| `x/y` | [cards](cards.md) |\n"
    assert check_index_links(base, head) == []


def test_a_definition_in_code_cannot_shadow_the_real_one():
    base = _base()
    head = dict(base)
    head["repos/old/_index.md"] = (base["repos/old/_index.md"]
                                   + "[x][r]\n\n```\n[r]: rules.md\n```\n\n[r]: ../../../secret.md\n")
    issues = {(i.code, i.detail) for i in check_index_links(base, head)}
    assert ("index_link_escapes", "../../../secret.md") in issues


def test_pipe_lines_without_a_table_header_are_not_table_cells():
    base = _base()
    head = _new_repo(base)
    core = "repos/new/core/_index.md"
    head[core] = "# core\n\n| `example | [cards](cards.md)` |\n"
    issues = {(i.code, i.path) for i in check_index_links(base, head)}
    assert ("index_unlinked", "repos/new/core/cards.md") in issues
    # a table right after a paragraph line is not a table either (GFM)
    head[core] = "# core\ntext `a\n| h | i |\n|---|---|\n| x | [cards](cards.md) |\n"
    issues = {(i.code, i.path) for i in check_index_links(base, head)}
    assert ("index_unlinked", "repos/new/core/cards.md") in issues


def test_a_visible_link_after_code_that_becomes_code_is_dropped():
    base = _base()
    base["repos/old/_index.md"] = "# old\n\n- `rules` [rules](rules.md)\n"
    head = dict(base)
    head["repos/old/_index.md"] = "# old\n\n- `rules [rules](rules.md)\n"
    assert {i.code for i in check_index_links(base, head)} == {"index_link_dropped"}
    # unchanged block, unrelated edit elsewhere: kept
    head["repos/old/_index.md"] = base["repos/old/_index.md"] + "\nmore words\n"
    assert check_index_links(base, head) == []


def test_a_link_after_a_closed_fence_that_reopens_is_dropped():
    base = _base()
    base["repos/old/_index.md"] = "# old\n\n```\nx\n```\n\n- [rules](rules.md)\n"
    head = dict(base)
    head["repos/old/_index.md"] = "# old\n\n```\nx\n\n- [rules](rules.md)\n"
    assert {i.code for i in check_index_links(base, head)} == {"index_link_dropped"}
    head["repos/old/_index.md"] = base["repos/old/_index.md"] + "\n- [more](rules.md#a)\n"
    assert check_index_links(base, head) == []


def test_moving_a_closing_fence_past_an_unchanged_link_drops_it():
    base = _base()
    base["repos/old/_index.md"] = "# old\n\n```\nx\n```\n\n- [rules](rules.md)\n"
    head = dict(base)
    head["repos/old/_index.md"] = "# old\n\n```\nx\n\n- [rules](rules.md)\n\n```\n"
    assert {i.code for i in check_index_links(base, head)} == {"index_link_dropped"}


def test_moving_a_link_into_code_drops_it():
    base = _base()
    head = dict(base)
    head["repos/old/_index.md"] = "# old\n\n- `[rules](rules.md)`\n"
    assert {i.code for i in check_index_links(base, head)} == {"index_link_dropped"}


def test_duplicate_definitions_are_all_resolved_and_never_navigation():
    base = _base()
    head = _new_repo(base)
    head["repos/new/core/_index.md"] = "# core\n\n- [Cards][c]\n\n[c]: missing.md\n[c]: cards.md\n"
    issues = {(i.code, i.detail if i.code != "index_unlinked" else i.path)
              for i in check_index_links(base, head)}
    assert issues == {("index_link_broken", "missing.md"),
                      ("index_unlinked", "repos/new/core/cards.md")}


def test_removing_a_reference_usage_drops_the_link():
    base = _base()
    base["repos/old/_index.md"] = "# old\n\n- [Rules][r]\n\n[r]: rules.md\n"
    head = dict(base)
    head["repos/old/_index.md"] = "# old\n\n[r]: rules.md\n"
    assert {i.code for i in check_index_links(base, head)} == {"index_link_dropped"}


def test_index_links_detect_dropped_titled_links_and_refuse_unparsed_syntax():
    base = _base()
    base["repos/old/_index.md"] = '# old\n\n- [rules](rules.md "the rules")\n'
    head = dict(base)
    head["repos/old/_index.md"] = '# old\n\n- [x](rules.md "unterminated\n'
    issues = {i.code for i in check_index_links(base, head)}
    assert issues == {"index_link_dropped", "index_link_unparsed"}


def test_index_links_ignore_urls_anchors_and_links_the_base_already_had():
    base = _base()
    base["general/_index.md"] += "- [schema](../../doc/knowledge/SCHEMA.md)\n"
    head = dict(base)
    head["general/_index.md"] += "- [site](https://example.com/x)\n- [top](#top)\n- [m](method.md#a)\n"
    assert check_index_links(base, head) == []


def test_only_kb_init_may_pass_bootstrap():
    root = Path(__file__).resolve().parents[1] / "src" / "infermatrix_copilot"
    allowed = {root / "kb_service" / "init_stages.py"}
    offenders = [
        str(path.relative_to(root)) for path in root.rglob("*.py")
        if path not in allowed and re.search(r"bootstrap\s*=\s*True", path.read_text(encoding="utf-8"))
    ]
    assert offenders == []
