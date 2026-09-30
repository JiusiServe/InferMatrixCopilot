"""L1: the deterministic half of the knowledge quality gate.

Two entry points, both pure functions over ``{knowledge-relative path: text}``
mappings so the service's gate and the publisher's local gate agree exactly:

* ``check_tree(files)`` — structural issues in one tree (footers, supersede
  links, tombstones, ``_routes.yaml``).
* ``check_changeset(base, head, changes)`` — what one change set may do: only
  whitelisted files and modes, no new duplicate or reused rule IDs, no dangling
  references to rules it retired or purged, no NEW tree issues, and a
  classification of every change into blocks:

  ``rule``        a rule section added / edited / retired / superseded / purged.
                  Needs a per-block L2 verdict (keyed by ``block_id``).
  ``prose``       any other wording change (page head, non-rule sections,
                  guides, ``_routes.yaml``). Needs an L2 prose verdict.
  ``mechanical``  ``updated:``/``sources:`` frontmatter, index lines for new
                  pages, tombstones. Recomputed here; a mismatch is an issue,
                  never a block a verdict could cover.

``check_changeset`` with ``bootstrap`` set is for ``kb init`` only (the one
allowed caller is ``kb_service/init_stages.py``; a test pins that). It relaxes
exactly two rules so a repository's knowledge can be created: an ``_index.md``
may be created in a directory that had no files before, and the shared
``repos/_index.md`` may be edited to list a new repository.
``check_index_links(base, head)`` is the init-side link check for the index
edits that bootstrap produces.

Standard library + PyYAML + ``lifecycle``/``ops`` only.
"""

from __future__ import annotations

import hashlib
import json
import posixpath
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterable, Mapping

import yaml

from .lifecycle import LifecycleError, Page, Section, expected_sources
from .ops import (
    INDEX_NAME, TOMBSTONES_NAME, all_rule_ids, all_tombstoned_ids,
    load_tombstones, page_over_capacity, render_tombstones,
)

ROUTES_NAME = "_routes.yaml"
KNOWLEDGE_PREFIX = "knowledge/"
_WHITELIST = (
    re.compile(r"knowledge/(?:repos/[^/]+|general)/(?:[^/]+/)*[^/]+\.md"),
    re.compile(r"knowledge/repos/[^/]+/_routes\.yaml"),
    re.compile(r"knowledge/(?:repos/[^/]+|general)/_tombstones\.yaml"),
)
_DENY = re.compile(r"knowledge/(?:skills|tools|\.claude)/|knowledge/[^/]+$")
_REGULAR_MODE = "100644"
_INDEX_LINE = re.compile(r"- \[[^\]\n]+\]\((?P<file>[^)/\s]+\.md)\)")
# bootstrap only: the shared list of repositories, edited to link a new one
_REPOS_INDEX = "knowledge/repos/_index.md"
# inline links (optional <angle> target and "title" / 'title' / (title)) and
# reference definitions; any other "](" is unparsed and refused by the link check
_LINK_TITLE = r"""(?:\s+(?:"[^"\n]*"|'[^'\n]*'|\([^)\n]*\)))?"""
_MD_LINK = re.compile(r"\]\(\s*(?:<(?P<angle>[^>\n]*)>|(?P<target>[^)\s]+))" + _LINK_TITLE + r"\s*\)")
_MD_REF = re.compile(r"(?m)^ {0,3}\[(?P<label>[^\]\n]+)\]:[ \t]*(?:<(?P<angle>[^>\n]*)>|(?P<target>\S+))"
                     + _LINK_TITLE + r"[ \t]*$")
# a reference definition counts only where it is used: [text][label], [label][], [label]
_REF_FULL = re.compile(r"\[(?P<text>[^\]\n]+)\]\[(?P<label>[^\]\n]*)\]")
_REF_SHORT = re.compile(r"\[(?P<label>[^\]\n]+)\](?![(\[:])")
# Link visibility, fail-closed. No Markdown parser is complete, so the checks
# split by direction: every link-like text counts when checking that links
# resolve (a link "hidden in code" is still checked), and only a CERTAINLY
# visible link counts as navigation (for "is the page linked" and "was the link
# kept"). Certainly visible: no fence-like line at or before it, and no
# backtick before it in its block (paragraph, list item, heading, quote, or
# table cell, which a code span cannot cross).
_FENCE_LIKE = re.compile(r"^[\s>*+\-\d.)]*(?:`{3,}|~{3,})")
_BLOCK_START = re.compile(r" {0,3}(?:#{1,6}(?:\s|$)|[-*+]\s|\d{1,9}[.)]\s|>)")
_TABLE_ROW = re.compile(r" {0,3}\|")
_TABLE_DELIM = re.compile(r" {0,3}\|?\s*:?-+:?\s*(?:\|\s*:?-+:?\s*)*\|?\s*")


def _table_body_row(lines: list[str], k: int) -> bool:
    """``lines[k]`` is a body row of a pipe table: a run of pipe lines that
    starts after a blank line (a table does not interrupt a paragraph), whose
    second line is a delimiter row, and ``lines[k]`` comes after it."""
    if not _TABLE_ROW.match(lines[k]):
        return False
    first = k
    while first > 0 and _TABLE_ROW.match(lines[first - 1]):
        first -= 1
    return (k >= first + 2 and (first == 0 or not lines[first - 1].strip())
            and _TABLE_DELIM.fullmatch(lines[first + 1]) is not None)


def _certainly_visible(text: str, pos: int) -> bool:
    line_start = text.rfind("\n", 0, pos) + 1
    line_end = text.find("\n", pos)
    line_end = len(text) if line_end < 0 else line_end
    lines = text[:line_end].split("\n")
    if any(_FENCE_LIKE.match(line) for line in lines):
        return False
    line = lines[-1]
    if _table_body_row(lines, len(lines) - 1):
        cell_start = max((m.end() for m in re.finditer(r"(?<!\\)\|", line[:pos - line_start])), default=0)
        return "`" not in line[cell_start:pos - line_start]
    start = len(lines) - 1  # walk back to the first line of the block
    while start > 0 and not _BLOCK_START.match(lines[start]) and lines[start - 1].strip():
        start -= 1
    block_start = sum(len(item) + 1 for item in lines[:start])
    return "`" not in text[block_start:pos]


def _block_span(text: str, pos: int) -> tuple[int, int]:
    """Offsets of the whole block holding ``pos`` (a table body row is its
    own block)."""
    lines = text.split("\n")
    k = text.count("\n", 0, pos)
    start = end = k
    if not _table_body_row(lines, k):
        while start > 0 and not _BLOCK_START.match(lines[start]) and lines[start - 1].strip():
            start -= 1
        while end + 1 < len(lines) and lines[end + 1].strip() \
                and not _BLOCK_START.match(lines[end + 1]) and not _table_body_row(lines, end + 1):
            end += 1
    offset = sum(len(line) + 1 for line in lines[:start])
    return offset, offset + len("\n".join(lines[start:end + 1]))


def _block_context(text: str, pos: int) -> tuple[str, tuple[str, ...]]:
    """The block holding ``pos`` and the fence-like lines before it: the same
    block after the same fences renders the same way."""
    start, end = _block_span(text, pos)
    return text[start:end], tuple(line for line in text[:start].split("\n") if _FENCE_LIKE.match(line))


def _contexts(text: str) -> set[tuple[str, tuple[str, ...]]]:
    starts = [0] + [m.end() for m in re.finditer("\n", text)]
    return {_block_context(text, pos) for pos in starts}


@dataclass(frozen=True)
class Issue:
    code: str
    path: str
    detail: str

    def to_dict(self) -> dict:
        return {"code": self.code, "path": self.path, "detail": self.detail}


@dataclass(frozen=True)
class Change:
    """One changed path as git reports it (repository-relative)."""

    path: str
    status: str            # A, M, D (renames are reported as D + A)
    old_mode: str = ""
    new_mode: str = ""


@dataclass(frozen=True)
class Block:
    kind: str       # rule | prose
    path: str       # knowledge-relative
    rule_id: str    # "" for prose
    op: str         # add | edit | retire | supersede | purge | prose
    sha256: str     # of the text the verdict judges

    @property
    def block_id(self) -> str:
        identity = json.dumps([self.kind, self.path, self.rule_id, self.op, self.sha256],
                              separators=(",", ":"))
        return hashlib.sha256(identity.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict:
        return {"block_id": self.block_id, "kind": self.kind, "path": self.path,
                "rule_id": self.rule_id, "op": self.op, "sha256": self.sha256}


@dataclass(frozen=True)
class ChangesetResult:
    issues: tuple[Issue, ...]
    blocks: tuple[Block, ...]
    retired: tuple[str, ...]
    purged: tuple[str, ...]
    external_refs: tuple[tuple[str, str], ...] = ()  # (rule_id, repo path)

    @property
    def ok(self) -> bool:
        return not self.issues


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _norm(text: str) -> str:
    """Section text without trailing blank lines: appending a section adds a
    separator to the previous one, which is layout, not a change of words."""
    return text.rstrip("\n") + "\n"


# -- tree-level ----------------------------------------------------------------

def _rule_pages(files: Mapping[str, str]) -> dict[str, Page]:
    pages: dict[str, Page] = {}
    for path, text in files.items():
        if path.endswith(".md"):
            page = Page.parse(text)
            if page.rules():
                pages[path] = page
    return pages


def check_tree(files: Mapping[str, str]) -> list[Issue]:
    issues: list[Issue] = []
    footers: dict[str, tuple[str, object]] = {}
    for path, page in _rule_pages(files).items():
        for section in page.rules():
            try:
                footer = section.footer
            except LifecycleError as exc:
                issues.append(Issue("footer_invalid", path, f"{section.rule_id}: {exc}"))
                continue
            footers.setdefault(section.rule_id, (path, footer))
    for rule_id, (path, footer) in footers.items():
        if footer.superseded_by:
            target = footers.get(footer.superseded_by)
            if target is None or target[1].supersedes != rule_id:
                issues.append(Issue("supersede_link_broken", path,
                                    f"{rule_id} -> {footer.superseded_by} has no matching supersedes"))
        if footer.supersedes:
            source = footers.get(footer.supersedes)
            if source is not None and source[1].superseded_by != rule_id:
                issues.append(Issue("supersede_link_broken", path,
                                    f"{rule_id} supersedes {footer.supersedes}, which does not name it"))
    try:
        tombstoned = all_tombstoned_ids(files)
    except (LifecycleError, yaml.YAMLError) as exc:
        issues.append(Issue("tombstones_invalid", "", str(exc)))
        tombstoned = set()
    for rule_id in sorted(tombstoned & set(all_rule_ids(files))):
        issues.append(Issue("tombstoned_id_reused", "", rule_id))
    for path, text in files.items():
        if PurePosixPath(path).name == ROUTES_NAME:
            issues.extend(_check_routes(path, text, files))
    return issues


def _check_routes(path: str, text: str, files: Mapping[str, str]) -> list[Issue]:
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return [Issue("routes_invalid", path, f"not YAML: {exc}")]
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        return [Issue("routes_invalid", path, "schema_version must be 1")]
    issues = []
    seen: set[str] = set()
    for index, owner in enumerate(data.get("owners") or []):
        if not isinstance(owner, dict) or not owner.get("owner") or not owner.get("path"):
            issues.append(Issue("routes_invalid", path, f"owners[{index}] needs owner and path"))
            continue
        if owner["owner"] in seen:
            issues.append(Issue("routes_invalid", path, f"duplicate owner {owner['owner']}"))
        seen.add(owner["owner"])
        if str(owner["path"]) not in files:
            issues.append(Issue("routes_page_missing", path, str(owner["path"])))
        for key in ("signals", "scope_prefixes"):
            if not isinstance(owner.get(key) or [], list):
                issues.append(Issue("routes_invalid", path, f"{owner['owner']}.{key} must be a list"))
    models = data.get("models")
    if models is not None and (not isinstance(models, dict) or not models.get("dir") or not models.get("page")):
        issues.append(Issue("routes_invalid", path, "models needs dir and page"))
    return issues


# -- change-set level ----------------------------------------------------------

def _whitelist_issues(changes: Iterable[Change], bootstrap: bool = False) -> list[Issue]:
    issues = []
    for change in changes:
        path = change.path
        if bootstrap and path == _REPOS_INDEX and change.status == "M":
            pass  # a new repository is listed in the shared index
        elif not path.startswith(KNOWLEDGE_PREFIX) or _DENY.match(path) \
                or not any(p.fullmatch(path) for p in _WHITELIST):
            issues.append(Issue("path_not_whitelisted", path, "only knowledge rule/guide pages, _routes.yaml and _tombstones.yaml auto-merge"))
            continue
        if change.status != "D" and change.new_mode != _REGULAR_MODE:
            issues.append(Issue("mode_not_regular", path, f"mode {change.new_mode or '?'} (need 100644)"))
    return issues


def _text_issues(path: str, text: str | None) -> list[Issue]:
    if text is None:
        return []
    if "\x00" in text or "�" in text:
        return [Issue("not_utf8_text", path, "binary or non-UTF-8 content")]
    return []


def _frontmatter_mechanical(path: str, base: Page, head: Page) -> list[Issue]:
    """Only ``updated:`` and ``sources:`` may change, and sources exactly as recomputed."""
    base_data, head_data = base.frontmatter_data(), head.frontmatter_data()
    issues = []
    for key in sorted(set(base_data) | set(head_data)):
        if key in ("updated", "sources"):
            continue
        if base_data.get(key) != head_data.get(key):
            issues.append(Issue("frontmatter_changed", path, f"{key} may not change"))
    if str(head_data.get("updated", "")) < str(base_data.get("updated", "")):
        issues.append(Issue("frontmatter_changed", path, "updated went backwards"))
    want = expected_sources(base.sources(), head)
    if head.sources() != want:
        issues.append(Issue("sources_mismatch", path, f"expected {want}, got {head.sources()}"))
    return issues


def _new_page_mechanical(path: str, head: Page) -> list[Issue]:
    data = head.frontmatter_data()
    issues = []
    if data.get("type") != "rule":
        issues.append(Issue("new_page_invalid", path, "a new page must be type: rule"))
    if not str(data.get("title") or "").strip():
        issues.append(Issue("new_page_invalid", path, "a new page needs a title"))
    want = expected_sources([], head)
    if head.sources() != want:
        issues.append(Issue("sources_mismatch", path, f"expected {want}, got {head.sources()}"))
    return issues


def _classify_page(path: str, base_text: str | None, head_text: str | None,
                   blocks: list[Block], issues: list[Issue],
                   retired: list[str], purged: list[tuple[str, str]],
                   purge_retired_at: dict[str, str]) -> None:
    base = Page.parse(base_text) if base_text is not None else None
    head = Page.parse(head_text) if head_text is not None else None
    if head is None:
        issues.append(Issue("page_deleted", path, "pages are never deleted; purge rules instead"))
        return
    base_is_rule = base is not None and (
        base.frontmatter_data().get("type") == "rule" or bool(base.rules()))
    is_rule_page = base_is_rule or head.frontmatter_data().get("type") == "rule"
    if base_is_rule and head.frontmatter_data().get("type") != base.frontmatter_data().get("type"):
        # a page may not leave the lifecycle by changing its type
        issues.append(Issue("page_type_changed", path, "a rule page keeps its type"))
    if not is_rule_page:
        if base is None or base.render() != head.render():
            blocks.append(Block("prose", path, "", "prose", _sha(head.render())))
        return
    if base is None:
        issues.extend(_new_page_mechanical(path, head))
        base_rules: dict[str, Section] = {}
        base_other: list[str] = []
        base_head = ""
    else:
        issues.extend(_frontmatter_mechanical(path, base, head))
        base_rules = {s.rule_id: s for s in base.rules()}
        base_other = [_norm(s.text) for s in base.sections if not s.is_rule]
        base_head = base.head
    head_rules = {s.rule_id: s for s in head.rules()}
    head_other = [_norm(s.text) for s in head.sections if not s.is_rule]
    if (base is None and head.head.strip() != f"# {head.frontmatter_data().get('title', '')}") \
            or (base is not None and head.head != base_head) or head_other != base_other:
        blocks.append(Block("prose", path, "", "prose",
                            _sha(head.head + "".join(head_other))))
    for rule_id, section in head_rules.items():
        old = base_rules.get(rule_id)
        try:
            footer = section.footer
            old_footer = old.footer if old is not None else None
        except LifecycleError as exc:
            issues.append(Issue("footer_invalid", path, f"{rule_id}: {exc}"))
            continue
        if old is None:
            if footer.status != "active":
                issues.append(Issue("rule_added_retired", path, rule_id))
            blocks.append(Block("rule", path, rule_id, "add", _sha(_norm(section.text))))
            continue
        if _norm(old.text) == _norm(section.text):
            continue
        if old_footer.status == "retired":
            issues.append(Issue("retired_rule_changed", path, f"{rule_id} is retired and frozen"))
            continue
        if old_footer.protected and not footer.protected:
            issues.append(Issue("protection_removed", path, rule_id))
        if footer.status == "retired":
            if section.body_without_footer != old.body_without_footer:
                issues.append(Issue("retire_changed_text", path, f"{rule_id}: retiring may not reword"))
            if old_footer.protected or footer.protected:
                issues.append(Issue("protected_rule_retired", path, rule_id))
            op = "supersede" if footer.reason == "superseded" else "retire"
            retired.extend(dict.fromkeys((rule_id, *section.nested_rule_ids)))
            blocks.append(Block("rule", path, rule_id, op, _sha(_norm(section.text))))
        else:
            if footer != old_footer:
                issues.append(Issue("footer_changed", path, f"{rule_id}: an edit keeps its footer"))
            if old_footer.protected or footer.protected:
                issues.append(Issue("protected_rule_edited", path, rule_id))
            if set(section.nested_rule_ids) != set(old.nested_rule_ids):
                # a nested rule leaves only by retiring and purging its parent
                issues.append(Issue("nested_rule_ids_changed", path,
                                    f"{rule_id}: {sorted(set(old.nested_rule_ids) ^ set(section.nested_rule_ids))}"))
            blocks.append(Block("rule", path, rule_id, "edit", _sha(_norm(section.text))))
    for rule_id, old in base_rules.items():
        if rule_id in head_rules:
            continue
        if old.footer.status != "retired":
            issues.append(Issue("active_rule_removed", path, f"{rule_id}: retire before purging"))
            continue
        if old.footer.protected:
            issues.append(Issue("protected_rule_purged", path, rule_id))
        purged.extend((rid, path) for rid in dict.fromkeys((rule_id, *old.nested_rule_ids)))
        purge_retired_at[rule_id] = old.footer.retired_at
        blocks.append(Block("rule", path, rule_id, "purge", _sha(_norm(old.text))))


def _index_mechanical(path: str, base_text: str | None, head_text: str | None,
                      new_pages: set[str], issues: list[Issue], blocks: list[Block],
                      head: Mapping[str, str] | None = None, *,
                      base: Mapping[str, str] | None = None, bootstrap: bool = False) -> None:
    if bootstrap and base_text is None and head_text is not None and head is not None:
        _index_created(path, base or {}, head, issues, blocks)
        return
    if base_text is None or head_text is None:
        issues.append(Issue("index_added_or_deleted", path, "index files are never created or deleted by a change set"))
        return
    directory = str(PurePosixPath(path).parent)
    expected_new = sorted(PurePosixPath(p).name for p in new_pages
                          if str(PurePosixPath(p).parent) == directory
                          and p.endswith(".md") and PurePosixPath(p).name != INDEX_NAME)
    # pages already in the directory but missing from the old index may be
    # linked too (the release sweep's T1 repair); new pages MUST be
    allowed = set(expected_new) | {
        PurePosixPath(p).name for p in (head or {})
        if str(PurePosixPath(p).parent) == directory and p.endswith(".md")
        and PurePosixPath(p).name != INDEX_NAME and f"]({PurePosixPath(p).name})" not in base_text
    }
    for name in expected_new:  # required whatever else the index change does
        if f"]({name})" not in head_text:
            issues.append(Issue("index_missing", path, f"new page {name} is not linked"))
    if not head_text.startswith(base_text.rstrip("\n") + "\n") and head_text != base_text:
        blocks.append(Block("prose", path, "", "prose", _sha(head_text)))
        return
    added = head_text[len(base_text.rstrip("\n") + "\n"):].splitlines()
    files = []
    for line in added:
        match = _INDEX_LINE.fullmatch(line.strip())
        if match is None:
            blocks.append(Block("prose", path, "", "prose", _sha(head_text)))
            return
        files.append(match.group("file"))
    if not set(expected_new) <= set(files) or not set(files) <= allowed or len(files) != len(set(files)):
        issues.append(Issue("index_mismatch", path,
                            f"index lines must cover new pages {expected_new} and only link unlisted pages; got {files}"))


def _link_occurrences(directory: str, text: str, *, certain: bool = False
                      ) -> list[tuple[str, str, tuple[int, ...]]]:
    """Relative links of an index as (written target without anchor, resolved
    knowledge-relative path, positions of the link text and, for a reference,
    its definition). URLs and anchor-only links are not targets; a link that
    leaves the knowledge tree resolves to a path starting ``..``. ``certain``
    keeps only links that are certainly visible (see above); a reference
    counts only where it is used."""
    def target_of(match) -> str:
        return match.group("angle") if match.group("angle") is not None else match.group("target")

    def keep(pos: int) -> bool:
        return not certain or _certainly_visible(text, pos)

    # every definition of a label: which one renders depends on which are in
    # code, so resolution checks all of them, and navigation trusts a label
    # only when it has exactly one definition and that one is visible
    definitions: dict[str, list] = {}
    for m in _MD_REF.finditer(text):
        definitions.setdefault(m.group("label").strip().lower(), []).append(m)
    used = [(m.group("label").strip().lower() or m.group("text").strip().lower(), m.start())
            for m in _REF_FULL.finditer(text) if keep(m.start())]
    used += [(m.group("label").strip().lower(), m.start())
             for m in _REF_SHORT.finditer(text) if keep(m.start())]
    found: list[tuple[str, tuple[int, ...]]] = [
        (target_of(m), (m.start(),)) for m in _MD_LINK.finditer(text) if keep(m.start())]
    for label, pos in used:
        defs = definitions.get(label, [])
        if not certain:
            found += [(target_of(m), (pos, m.start())) for m in defs]
        elif len(defs) == 1 and keep(defs[0].start()):
            found.append((target_of(defs[0]), (pos, defs[0].start())))
    out = []
    for raw, positions in found:
        target = raw.split("#", 1)[0]
        if not target or "://" in target or target.startswith("mailto:"):
            continue
        resolved = ".." if target.startswith("/") else \
            posixpath.normpath(posixpath.join(directory, target))  # absolute: never inside
        out.append((target, resolved, positions))
    return out


def _link_targets(directory: str, text: str, *, certain: bool = False) -> dict[str, str]:
    """{written target: resolved path} of ``_link_occurrences``."""
    return {written: resolved for written, resolved, _ in _link_occurrences(directory, text, certain=certain)}


def _dropped_links(directory: str, before: str, after: str) -> set[str]:
    """Links ``before`` has that ``after`` may no longer show, fail-closed: a
    link is kept only when it is certainly visible in ``after``, or every block
    it sits in is unchanged in ``after`` after the same fence-like lines."""
    raw_after = _link_targets(directory, after)
    visible_after = _link_targets(directory, after, certain=True)
    contexts_after = _contexts(after)
    dropped = set()
    for written, _resolved, positions in _link_occurrences(directory, before):
        if written not in raw_after:
            dropped.add(written)
        elif written not in visible_after and not all(
                _block_context(before, pos) in contexts_after for pos in positions):
            dropped.add(written)
    return dropped


def _unparsed_links(text: str) -> set[str]:
    """Each "](" no inline-link pattern accounts for, as its line: link syntax
    the checker cannot read is refused rather than skipped."""
    parsed = {m.start() for m in _MD_LINK.finditer(text)}
    return {text[text.rfind("\n", 0, i) + 1:].split("\n", 1)[0].strip()
            for i in (m.start() for m in re.finditer(r"\]\(", text)) if i not in parsed}


def _dir_entries(head: Mapping[str, str], directory: str) -> list[str]:
    """Pages directly in ``directory`` and the indexes of its child directories."""
    prefix = f"{directory}/" if directory else ""
    out = []
    for p in sorted(head):
        if not p.startswith(prefix) or not p.endswith(".md"):
            continue
        rest = p[len(prefix):].split("/")
        if (len(rest) == 1 and rest[0] != INDEX_NAME) or (len(rest) == 2 and rest[1] == INDEX_NAME):
            out.append(p)
    return out


def _index_created(path: str, base: Mapping[str, str], head: Mapping[str, str],
                   issues: list[Issue], blocks: list[Block]) -> None:
    """Bootstrap: an index created for a directory that is new in this change set."""
    directory = posixpath.dirname(path)
    if any(p.startswith(f"{directory}/") for p in base):
        issues.append(Issue("index_added_or_deleted", path,
                            "an index may be created only for a new directory"))
        return
    linked = set(_link_targets(directory, head[path], certain=True).values())
    for entry in _dir_entries(head, directory):
        if entry not in linked:
            issues.append(Issue("index_missing", path, f"{entry} is not linked"))
    if directory:
        parent = posixpath.join(posixpath.dirname(directory), INDEX_NAME)
        # a parent index created in the same change set reports its own children
        if parent in base and parent in head and path not in set(
                _link_targets(posixpath.dirname(parent), head[parent], certain=True).values()):
            issues.append(Issue("index_missing", parent, f"the new {path} is not linked"))
    blocks.append(Block("prose", path, "", "prose", _sha(head[path])))


def check_index_links(base: Mapping[str, str], head: Mapping[str, str]) -> list[Issue]:
    """Links of every index added or changed from ``base`` to ``head``: each
    link the change adds resolves inside the knowledge tree to a file (or a
    directory) of ``head``; a changed index keeps every link it had; every
    page or child index new in ``head`` is linked from its parent index.
    Links an index already had are not re-judged (some point into doc/)."""
    issues: list[Issue] = []
    head_dirs = {posixpath.dirname(p) for p in head}
    for path in sorted(p for p in head if posixpath.basename(p) == INDEX_NAME):
        if base.get(path) == head[path]:
            continue
        directory = posixpath.dirname(path)
        before = _link_targets(directory, base.get(path) or "")
        after = _link_targets(directory, head[path])
        for line in sorted(_unparsed_links(head[path]) - _unparsed_links(base.get(path) or "")):
            issues.append(Issue("index_link_unparsed", path, line[:120]))
        for written in sorted(_dropped_links(directory, base.get(path) or "", head[path])):
            issues.append(Issue("index_link_dropped", path, written))
        for written, resolved in sorted(after.items()):
            if written in before:
                continue
            if resolved == ".." or resolved.startswith("../"):
                issues.append(Issue("index_link_escapes", path, written))
            elif resolved not in head and not any(d == resolved or d.startswith(resolved + "/")
                                                  for d in head_dirs):
                issues.append(Issue("index_link_broken", path, written))
    for page in sorted(p for p in head if p not in base and p.endswith(".md")):
        directory = posixpath.dirname(page)
        if posixpath.basename(page) == INDEX_NAME:
            if not directory:
                continue
            directory = posixpath.dirname(directory)
        parent = posixpath.join(directory, INDEX_NAME)
        if parent not in head:
            if directory:  # the knowledge root has no index
                issues.append(Issue("index_unlinked", page, f"{parent} does not exist"))
            continue
        if page not in set(_link_targets(directory, head[parent], certain=True).values()):
            issues.append(Issue("index_unlinked", page, f"{parent} does not link it"))
    return issues


def check_changeset(
    base: Mapping[str, str],
    head: Mapping[str, str],
    changes: Iterable[Change],
    *,
    external_texts: Mapping[str, str] | None = None,
    release: str = "",
    bootstrap: bool = False,
) -> ChangesetResult:
    """Gate one change set. ``base``/``head`` map knowledge-relative paths
    (``repos/...``) to text; ``changes`` are repository-relative git changes.
    ``external_texts`` (repo path -> text, outside ``knowledge/``) is scanned
    for references to rules this change retires or purges. ``release`` is the
    trusted current release (from the signed verdict); when given, purges must
    carry it as ``purged_at``. A purge is always rejected in the release that
    retired the rule. ``bootstrap`` is for ``kb init`` only (module docstring)."""
    changes = list(changes)
    issues = _whitelist_issues(changes, bootstrap)
    blocks: list[Block] = []
    retired: list[str] = []
    purged: list[tuple[str, str]] = []  # (rule id, page)
    purge_retired_at: dict[str, str] = {}
    knowledge_paths = [c.path[len(KNOWLEDGE_PREFIX):] for c in changes
                       if c.path.startswith(KNOWLEDGE_PREFIX)]
    for path in knowledge_paths:
        issues.extend(_text_issues(path, head.get(path)))
        if path.endswith(".md") and head.get(path) is not None:
            over = page_over_capacity(head[path])
            if over:
                issues.append(Issue("page_over_capacity", path, over))
    new_pages = {p for p in knowledge_paths if p not in base and p in head}
    for page_path in sorted(new_pages):
        index = str(PurePosixPath(page_path).with_name(INDEX_NAME))
        if page_path.endswith(".md") and PurePosixPath(page_path).name != INDEX_NAME \
                and index not in knowledge_paths:
            issues.append(Issue("index_missing", page_path, f"{index} must list the new page"))
    tombstone_paths = []
    for path in sorted(knowledge_paths):
        name = PurePosixPath(path).name
        if name == INDEX_NAME:
            _index_mechanical(path, base.get(path), head.get(path), new_pages, issues, blocks, head,
                              base=base, bootstrap=bootstrap)
        elif name == TOMBSTONES_NAME:
            tombstone_paths.append(path)
        elif name == ROUTES_NAME:
            blocks.append(Block("prose", path, "", "prose", _sha(head.get(path) or "")))
        elif path.endswith(".md"):
            try:
                _classify_page(path, base.get(path), head.get(path), blocks, issues,
                               retired, purged, purge_retired_at)
            except (LifecycleError, yaml.YAMLError) as exc:
                issues.append(Issue("page_unparseable", path, str(exc)))
    # tombstones: exactly the IDs purged in this change set, appended
    for path in tombstone_paths:
        try:
            before = load_tombstones(base.get(path))
            after = load_tombstones(head.get(path))
        except (LifecycleError, yaml.YAMLError) as exc:
            issues.append(Issue("tombstones_invalid", path, str(exc)))
            continue
        scope = str(PurePosixPath(path).parent)
        purged_here = [rid for rid, page_path in purged if page_path.startswith(scope + "/")]
        appended = after[len(before):]
        if after[:len(before)] != before or sorted(i["id"] for i in appended) != sorted(purged_here):
            issues.append(Issue("tombstones_mismatch", path, f"expected appended tombstones for {sorted(purged_here)}"))
        for item in appended:
            retired_at = purge_retired_at.get(str(item["id"]))
            purged_at = str(item.get("purged_at") or "")
            if retired_at is None:
                continue  # a nested ID; its parent carries the timing
            if not purged_at or purged_at == retired_at:
                issues.append(Issue("purge_too_early", path,
                                    f"{item['id']}: purged in the release it was retired ({retired_at})"))
            if release and purged_at != release:
                issues.append(Issue("purge_release_mismatch", path,
                                    f"{item['id']}: purged_at {purged_at} is not this release {release}"))
        if head.get(path) != render_tombstones(after):
            issues.append(Issue("tombstones_mismatch", path, "tombstones are not in canonical form"))
    for rule_id, _page in purged:
        if rule_id not in all_tombstoned_ids(head):
            issues.append(Issue("purge_without_tombstone", "", rule_id))
    # no NEW duplicate IDs, no reuse of retired or tombstoned IDs
    base_ids, head_ids = all_rule_ids(base), all_rule_ids(head)
    for rule_id, count in head_ids.items():
        if count > base_ids.get(rule_id, 0) and count > 1:
            issues.append(Issue("duplicate_rule_id", "", rule_id))
    base_tomb = all_tombstoned_ids(base)
    for block in blocks:
        if block.op == "add" and (block.rule_id in base_tomb or block.rule_id in base_ids):
            issues.append(Issue("rule_id_reused", block.path, block.rule_id))
    # dangling references to what this change set retired or purged
    gone = set(retired) | {rid for rid, _page in purged}
    if gone:
        issues.extend(_dangling_refs(head, gone))
    external = tuple(
        (rule_id, path)
        for path, text in sorted((external_texts or {}).items())
        for rule_id in sorted(gone) if re.search(rf"(?<![\w-]){re.escape(rule_id)}(?![\w-])", text)
    )
    # no NEW tree-level issues
    before = {(i.code, i.detail) for i in check_tree(base)}
    issues.extend(i for i in check_tree(head) if (i.code, i.detail) not in before)
    return ChangesetResult(tuple(issues), tuple(blocks), tuple(retired),
                           tuple(rid for rid, _page in purged), external)


def _dangling_refs(head: Mapping[str, str], gone: set[str]) -> list[Issue]:
    """References in ACTIVE text to rules that are now retired or purged.
    Allowed: the rule's own section, lifecycle footers, tombstones."""
    issues = []
    for path, text in head.items():
        if not path.endswith(".md"):
            continue
        page = Page.parse(text)
        chunks = [page.head] + [
            s.body_without_footer for s in page.sections
            if s.rule_id not in gone and (not s.is_rule or _active(s))
        ]
        body = "\n".join(chunks)
        for rule_id in sorted(gone):
            if re.search(rf"(?<![\w-]){re.escape(rule_id)}(?![\w-])", body):
                issues.append(Issue("dangling_reference", path, rule_id))
    return issues


def _active(section: Section) -> bool:
    try:
        return section.footer.status == "active"
    except LifecycleError:
        return True
