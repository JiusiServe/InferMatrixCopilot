"""The curated gold set (design §6.1 "金标来源").

The raw ground truth (`eval/dataset/gt/pr<N>.inline.json`) is a list of
human review comments with no stable identity; a judge cannot deterministically
decide "which concern is this" from them. The curated set gives each concern a
stable ``gold_id`` — ``sha256(item + path + normalized concern)[:12]`` — so a
gold match is a fact about an id, re-wording is a NEW entry, and the file's
own sha is the version an experiment freezes.

``draft_gold`` turns raw comments into a draft a human curates (one entry per
comment, `status: draft`); only a file marked ``curated`` is ever used for
scoring. The set changes only through human pull requests.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .adapters import Gold, GoldEntry

CURATED_DIRNAME = "curated"


def normalize_concern(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def gold_id(item: str, path: str, concern: str) -> str:
    return hashlib.sha256(f"{item}\n{path}\n{normalize_concern(concern)}".encode("utf-8")).hexdigest()[:12]


def item_stem(item: str) -> str:
    """``repo#123@sha`` -> ``pr123`` (the eval dataset's file stem)."""
    m = re.match(r"^[^#]+#(\d+)", item)
    if m:
        return f"pr{m.group(1)}"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", item)


def draft_gold(item: str, inline_comments: list[dict], *, clip: int = 240) -> dict:
    """A draft gold file from raw inline comments: one concern per comment,
    the first sentence(s) of the body as the concern text, for a human to
    merge, reword or drop before marking the file curated."""
    entries = []
    for i, c in enumerate(inline_comments):
        body = str(c.get("body") or "").strip()
        concern = re.split(r"(?<=[.!?])\s", body, maxsplit=1)[0][:clip] if body else ""
        if not concern:
            continue
        path = str(c.get("path") or "")
        entries.append({"gold_id": gold_id(item, path, concern), "path": path, "concern": concern,
                        "kind": "defect", "severity_hint": "", "source_comments": [i],
                        "line": c.get("line")})
    return {"item": item, "status": "draft", "entries": entries,
            "note": "curate: merge duplicates, reword to one concern each, drop noise, then set status=curated"}


def write_draft(gt_dir: Path, item: str) -> Path:
    stem = item_stem(item)
    raw = gt_dir / f"{stem}.inline.json"
    if not raw.exists():
        raise FileNotFoundError(raw)
    comments = json.loads(raw.read_text(encoding="utf-8"))
    out_dir = gt_dir / CURATED_DIRNAME
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{stem}.gold.json"
    if out.exists():
        raise FileExistsError(f"{out} exists; edit it rather than re-drafting")
    out.write_text(json.dumps(draft_gold(item, comments), ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def load_gold(path: Path) -> Gold:
    """A curated gold file; refuses drafts, duplicate or mismatching ids."""
    data = json.loads(path.read_text(encoding="utf-8"))
    item = str(data.get("item") or "")
    status = str(data.get("status") or "draft")
    entries: list[GoldEntry] = []
    seen: set[str] = set()
    for e in data.get("entries") or []:
        gid = str(e.get("gold_id") or "")
        expected = gold_id(item, str(e.get("path") or ""), str(e.get("concern") or ""))
        if gid != expected:
            raise ValueError(f"{path}: gold_id {gid!r} does not match its content (expected {expected}); "
                             "a reworded concern is a new entry")
        if gid in seen:
            raise ValueError(f"{path}: duplicate gold_id {gid}")
        seen.add(gid)
        entries.append(GoldEntry(gid, str(e.get("path") or ""), str(e.get("concern") or ""),
                                 str(e.get("kind") or "defect"), str(e.get("severity_hint") or ""),
                                 tuple(int(i) for i in e.get("source_comments") or ())))
    version = hashlib.sha256(path.read_bytes()).hexdigest()
    return Gold(item=item, entries=tuple(entries), version=version, status=status)


def _split_item(item: str) -> tuple[str, str]:
    """``repo#pr@head`` -> ``("repo#pr", "head")`` (head may be empty)."""
    base, _, head = str(item or "").partition("@")
    return base, head


def same_item(gold_item: str, item: str) -> bool:
    """A gold file applies to an item when repository and PR agree and, when
    the file names a head, that head too. PR numbers are repository-local:
    ``repo-a#123`` is never ``repo-b#123``."""
    gb, gh = _split_item(gold_item)
    ib, ih = _split_item(item)
    if not gb or gb != ib:
        return False
    # a head-specific gold file needs that exact head: an item with an unknown
    # head cannot be scored against gold curated for a particular revision
    return not gh or gh == ih


def gold_for_item(gt_dir: Path, item: str) -> Gold | None:
    path = gt_dir / CURATED_DIRNAME / f"{item_stem(item)}.gold.json"
    if not path.exists():
        return None
    gold = load_gold(path)
    if gold.status != "curated" or not same_item(gold.item, item):
        return None
    return gold
