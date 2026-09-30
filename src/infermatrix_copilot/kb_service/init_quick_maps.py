"""Direct quick maps on the pages kb init routes to.

Direct's product is the embedded map: for a repository routed by a
knowledge-side ``_routes.yaml``, every owner page must carry a ``## … Direct …``
section (``direct_routing._direct_quick_map_text``: the first such heading up to
the next ``## ``, non-empty, at most 3500 characters), and
``test_every_routed_page_yields_a_quick_map`` fails CI on any page that does
not. The first real run (afd-plugin skeleton, PR #265) routed pages that had
none.

kb init therefore renders that section deterministically on every owner page
of the routes file it writes or extends — the rules on the page as rows, or one
row for a map card or an entry page — keeps it the first section after the
title, regenerates it whenever it appends rules to the page (deepen), and
blocks a change whose routed pages would not yield a map. A map init did not
write (no ``MARKER``) is somebody's hand-written map and is never rewritten. A
repository routed by its adapter manifest carries no routes file and is exempt:
Direct's manifest fallback reports ``read_required`` for its pages.

Standard library plus the knowledge format; nothing here names a repository.
"""

from __future__ import annotations

import re
from dataclasses import replace
from typing import Iterable, Mapping, Sequence

from ..knowledge_service.facts import CODE_SPAN, PATH
from ..knowledge_service.lifecycle import LifecycleError, Page, Section

# The ID scanner of the knowledge format (``lifecycle.ANY_RULE_HEADING``) reads
# ``## Word ...`` as the ID ``Word`` and L1 refuses one ID on two pages, so the
# heading opens with a word that scanner cannot take for an ID; Direct only
# needs "Direct" somewhere on the heading line.
QUICK_MAP_HEADING = "## 代码快速入口（Direct）"
MARKER = "<!-- kb-init:quick-map -->"
MAX_CHARS = 3000          # what init renders (rows are dropped past it)
HARD_CAP = 3500           # what Direct serves whole (``_direct_quick_map`` cap)
MAX_CELL = 80
MAX_SOURCES = 3
_DIRECT = re.compile(r"^##\s+.*Direct", re.IGNORECASE)
_TRIGGER = re.compile(r"^\s*[-*]\s*(?:\*\*)?触发(?:\*\*)?\s*[:：]\s*(?P<text>.+?)\s*$")
_TITLE = re.compile(r"^#{2,3}\s+[A-Za-z0-9][A-Za-z0-9-]{1,40}\s+[—-]\s+(?P<title>.+?)\s*$")
_HEADER = ("| PR 描述在做什么 | 精确规则 | 第一批 live 源码 |", "|---|---|---|")
_MORE = "| … | … | … |"


def _cell(text: str, limit: int = MAX_CELL) -> str:
    text = " ".join(str(text).split()).replace("|", "\\|")
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def _paths_in(text: str, limit: int = MAX_SOURCES) -> list[str]:
    """The repository paths (``path`` or ``path::Symbol``) ``text`` names in
    backticks, in order of first appearance."""
    out: list[str] = []
    for match in CODE_SPAN.finditer(text):
        token = match.group("tok").strip()
        if PATH.fullmatch(token.split("::", 1)[0]) and token not in out:
            out.append(token)
            if len(out) >= limit:
                break
    return out


def _trigger(section: Section) -> str:
    for line in section.text.splitlines()[1:]:
        match = _TRIGGER.match(line)
        if match:
            return match.group("text")
    match = _TITLE.match(section.heading)
    return match.group("title") if match else section.rule_id


def _sources(paths: Sequence[str], fallback: Sequence[str]) -> str:
    chosen = list(paths) or list(fallback)[:MAX_SOURCES]
    return "、".join(f"`{p}`" for p in chosen) if chosen else "—"


def render_quick_map(page_text: str, *, signals: Sequence[str], prefixes: Sequence[str],
                     key_files: Sequence[str] = ()) -> str:
    """The Direct section for ``page_text``: one row per active rule on the
    page (its 触发 line or title, its ID, the paths it names), or one row for
    a page without rules (a map card or an entry page: the owner's signals,
    its key files or scope prefixes). Deterministic; at most ``MAX_CHARS``
    (rows are dropped from the end behind a ``…`` row), never over
    ``HARD_CAP``."""
    try:
        rules = [s for s in Page.parse(page_text).rules() if s.footer.status == "active"]
    except LifecycleError:
        rules = []
    rows: list[str] = []
    for section in rules:
        rows.append(f"| {_cell(_trigger(section))} | {section.rule_id} | "
                    f"{_sources(_paths_in(section.text), prefixes)} |")
    if not rows:
        files = list(key_files) or _paths_in(page_text, MAX_SOURCES)
        rows.append(f"| {_cell('、'.join(signals) or '（无触发词）')} | 入口 | {_sources(files, prefixes)} |")
    lead = (("触发词：" + "、".join(_cell(s, 40) for s in list(signals)[:12]) + "。") if signals else "")
    lead += "PR 描述或改动命中下表一行时，先读该行的规则，再读页面其余部分。"

    def render(kept: list[str], more: bool) -> str:
        return "\n".join([QUICK_MAP_HEADING, MARKER, "", lead, "", *_HEADER, *kept, *([_MORE] if more else [])])

    kept, more = list(rows), False
    text = render(kept, more)
    while len(text) > MAX_CHARS and kept:
        kept.pop()
        more = True
        text = render(kept, more)
    if len(text) > HARD_CAP:      # pragma: no cover - the lead alone is far under the cap
        raise ValueError(f"quick map cannot fit under {HARD_CAP} characters")
    return text + "\n"


def _after_table(section_text: str) -> str:
    """The lines of init's map section that follow ITS table (content the
    page gained after the map was written: an index line, prose, even a
    second table); "" when there are none. The generated table is the run of
    ``|`` lines right after the ``|---|---|---|`` separator, so anything past
    that run — including another table behind prose — is the page's."""
    lines = section_text.splitlines()
    separator = next((i for i, line in enumerate(lines) if line.strip() == _HEADER[1]), None)
    if separator is None:
        return ""
    end = separator + 1
    while end < len(lines) and lines[end].startswith("|"):
        end += 1
    return "\n".join(lines[end:])


def has_map(page_text: str) -> bool:
    """The page carries a Direct section (init's or hand-written)."""
    return any(_DIRECT.match(s.heading) for s in Page.parse(page_text).sections)


def has_hand_written_map(page_text: str) -> bool:
    """A Direct section that init did not write (no ``MARKER``)."""
    for section in Page.parse(page_text).sections:
        if _DIRECT.match(section.heading):
            return MARKER not in section.text
    return False


def with_quick_map(page_text: str, section_text: str) -> str:
    """``page_text`` with ``section_text`` as its Direct section: init's own
    map replaced in place, a page without one gets it as the first section
    after the title, a hand-written map is left exactly as it is."""
    page = Page.parse(page_text)
    body = section_text.rstrip("\n") + "\n\n"
    sections = list(page.sections)
    for index, section in enumerate(sections):
        if _DIRECT.match(section.heading):
            if MARKER not in section.text:
                return page_text
            # what the page gained after the map (an index line appended to an
            # entry page, say) belongs to the page, not to the map: keep it
            tail = _after_table(section.text)
            last = index == len(sections) - 1
            trailing = section.text[len(section.text.rstrip("\n")):] if last else "\n\n"
            rendered = section_text.rstrip("\n") + ("\n\n" + tail.rstrip("\n") if tail.strip() else "")
            sections[index] = Section(rendered + (trailing or "\n"))
            return replace(page, sections=tuple(sections)).render()
    head = page.head if page.head.endswith("\n\n") else page.head.rstrip("\n") + "\n\n"
    if not sections:
        body = section_text.rstrip("\n") + "\n"
    return replace(page, head=head, sections=(Section(body), *sections)).render()


def mapped(page_text: str, *, signals: Sequence[str], prefixes: Sequence[str]) -> str | None:
    """``page_text`` with its Direct quick map, or None when the map would
    push the page over the knowledge format's capacity (``page_over_capacity``:
    the caller keeps the page as it is and says so)."""
    from ..knowledge_service.ops import page_over_capacity

    text = with_quick_map(page_text, render_quick_map(page_text, signals=signals, prefixes=prefixes))
    return None if page_over_capacity(text) else text


def map_inputs(routes_text: str | None, page: str) -> tuple[list[str], list[str]]:
    """The (signals, scope_prefixes) the routes file gives ``page``'s first
    owner — what its map is rendered with — or empty lists."""
    import yaml

    try:
        doc = yaml.safe_load(routes_text or "") or {}
    except yaml.YAMLError:
        return [], []
    for owner in (doc.get("owners") or []) if isinstance(doc, dict) else []:
        if isinstance(owner, dict) and str(owner.get("path") or "") == page:
            return ([str(x) for x in owner.get("signals") or []],
                    [str(x) for x in owner.get("scope_prefixes") or []])
    return [], []


def refresh_quick_maps(head: Mapping[str, str], base: Mapping[str, str], routes_text: str | None, *,
                       briefing_docs: Iterable[str]) -> tuple[dict[str, str], list[str], list[str]]:
    """``head`` with init's Direct quick map on every owner page of the
    routes file that this change touched or that has no map yet, plus the
    checklist lines and the BLOCKING problems that produced. An owner page
    unchanged since ``base`` that already has a map is left alone (routing
    drift makes no churn); a briefing doc is never written (checklist; the
    presence check then blocks); a page whose regenerated map no longer
    fits the format's capacity is a problem, never a stale map."""
    out, checklist, problems = dict(head), [], []
    off_limits = set(briefing_docs)
    try:
        pages = owner_pages(routes_text)
    except ValueError:
        return out, checklist, problems       # the routes file is reported by the validators
    for page in pages:
        text = out.get(page)
        if text is None or not page.endswith(".md"):
            continue
        if page in off_limits:
            checklist.append(f"{page} is a briefing doc (knowledge.briefing_docs): init does not write its "
                             "Direct quick map; add one by hand or route another page")
            continue
        if text == base.get(page) and has_map(text):
            continue
        signals, prefixes = map_inputs(routes_text, page)
        with_map = mapped(text, signals=signals, prefixes=prefixes)
        if with_map is None:
            problems.append(f"quick map: {page} has no room for its Direct quick map (page capacity): "
                            "split the page by hand, or route another page")
            continue
        out[page] = with_map
    return out, checklist, problems


def owner_pages(routes_text: str | None) -> list[str]:
    """The owner pages a routes file names, in routing order, each once."""
    from .init_coverage import load_owners

    if routes_text is None:
        return []
    return list(dict.fromkeys(o.path for o in load_owners(routes_text)))


def quick_map_problems(files: Mapping[str, str], pages: Iterable[str],
                       base: Mapping[str, str] | None = None) -> list[str]:
    """Why Direct could not serve the routed ``pages`` of ``files``: the same
    extraction the server runs (``_direct_quick_map_text``), page by page.
    Blocking: a route without a map hands the host nothing, and a map the
    server would truncate is not whole — CI refuses newly truncated maps,
    so a page this change wrote or changed (``base``) may not truncate."""
    from ..direct_routing import _direct_quick_map_text

    problems = []
    for page in pages:
        text = files.get(page)
        if text is None:
            problems.append(f"quick map: routed page {page} does not exist")
            continue
        _, status = _direct_quick_map_text(text)
        if status == "unavailable":
            problems.append(f"quick map: {page} yields no Direct quick map (a routed page needs a "
                            f"`{QUICK_MAP_HEADING[3:]}` section with a non-empty body)")
        elif status == "truncated" and (base is None or base.get(page) != text):
            problems.append(f"quick map: {page}: the Direct section as served exceeds {HARD_CAP} characters "
                            "(truncated); keep the map first and short, and start the rules with a `## ` "
                            "heading so level-three rules are not part of it")
    return problems
