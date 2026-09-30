"""The review bot's production-review adapter (design §6.1, descriptive only).

There is no gold. The proxy labels are what happened to each PUBLISHED
finding on the pull request thread: *accepted* (the thread was resolved, the
line changed, or the author answered in the affirmative), *disputed* (the
author pushed back), *silent* (no response). They attach to the incumbent's
own findings, so they support a description of the production fingerprint
(stage-of-loss on disputed and silent findings, proxy precision) and never a
comparative claim: v1 registers no experiment on this workflow, and every
number it produces is marked ``proxy`` and ``descriptive-only``.
"""

from __future__ import annotations

import json
import re
import subprocess
from typing import Any, Callable

from ...trace_store import TraceStore
from ..reader import Unit
from . import FindingLabel, Gold, Match, Outcome

ACCEPT_RE = re.compile(r"\b(done|fixed|addressed|good catch|thanks|applied|updated|you'?re right|agreed?)\b", re.I)
DISPUTE_RE = re.compile(r"\b(disagree|not a bug|won'?t fix|intentional|by design|false positive|incorrect|"
                        r"this is fine|not needed|out of scope)\b", re.I)
LINE_TOLERANCE = 3

FetchThreads = Callable[[str, int], dict]


def gh_threads(repo_full_name: str, pr: int, *, run: Callable[..., Any] | None = None) -> dict:
    """The PR's state and review threads through ``gh api graphql`` (read only)."""
    run = run or subprocess.run
    owner, _, name = repo_full_name.partition("/")
    query = """query($owner:String!,$name:String!,$pr:Int!){ repository(owner:$owner,name:$name){
      pullRequest(number:$pr){ state headRefOid reviewThreads(first:100){ nodes{ isResolved isOutdated
        comments(first:20){ nodes{ author{login} body path line originalLine } } } } } } }"""
    proc = run(["gh", "api", "graphql", "-f", f"query={query}", "-F", f"owner={owner}", "-F", f"name={name}",
                "-F", f"pr={int(pr)}"], capture_output=True, text=True, timeout=120)
    if getattr(proc, "returncode", 1) != 0:
        raise RuntimeError(f"gh api graphql failed: {(getattr(proc, 'stderr', '') or '')[:300]}")
    data = json.loads(proc.stdout)["data"]["repository"]["pullRequest"]
    threads = []
    for node in (data.get("reviewThreads") or {}).get("nodes") or []:
        comments = (node.get("comments") or {}).get("nodes") or []
        if not comments:
            continue
        first = comments[0]
        threads.append({"path": first.get("path") or "", "line": first.get("line") or first.get("originalLine"),
                        "body": first.get("body") or "", "author": (first.get("author") or {}).get("login", ""),
                        "resolved": bool(node.get("isResolved")), "outdated": bool(node.get("isOutdated")),
                        "replies": [{"author": (c.get("author") or {}).get("login", ""), "body": c.get("body") or ""}
                                    for c in comments[1:]]})
    return {"state": data.get("state", ""), "head": data.get("headRefOid", ""), "threads": threads}


_MARKER_RE = re.compile(r"^\s*\[([^\]\s]+)\]\s*")
_SEVERITY_RE = re.compile(r"^\s*\*\*\[[a-z]+\]\*\*\s*", re.I)


def _published_text(body: str) -> tuple[str, str]:
    """``(marker, published text)`` of a thread body in the bot's publication
    format (`engine/steps/pr/publish.py::_inline_comment`): an optional
    leading ``[id]`` marker, then ``**[severity]** <comment>`` and, when the
    finding carried evidence, a ``\n\nEvidence: ...`` trailer. Only the
    marker and the severity wrapper are removed: the trailer stays, because
    it is compared against the finding's OWN rendering (comment plus its
    evidence field) — a comment whose text itself ends in an Evidence line
    is a different finding from one whose evidence was appended."""
    m = _MARKER_RE.match(body or "")
    rest = body[m.end():] if m else (body or "")
    rest = _SEVERITY_RE.sub("", rest, count=1)
    return (m.group(1) if m else ""), rest.strip()


def _rendered_comment(finding: dict) -> str:
    """What the bot published for this finding, minus marker and severity:
    the comment, then ``Evidence: <evidence>`` when the finding has one."""
    text = str(finding.get("comment") or "").strip()
    evidence = str(finding.get("evidence") or "").strip()
    return f"{text}\n\nEvidence: {evidence}" if evidence else text


def _thread_identity(body: str) -> tuple[str, str]:
    """``(marker, first line of the published comment text)``."""
    marker, text = _published_text(body)
    first = text.splitlines()[0] if text else ""
    return marker, first


def _norm_title(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip().rstrip(".").lower()


def own_thread(finding: dict, threads: list[dict], *, bot_login: str = "") -> dict | None:
    """The thread the bot opened for THIS finding: authored by the bot (when
    its login is known), on the finding's path near its line, and carrying
    the finding's identity (its id marker, else its title or comment text).
    A resolved thread a human opened at the same line is somebody else's and
    must never label the bot's finding."""
    path = str(finding.get("path") or finding.get("file") or "")   # the copilot's findings say `file`
    line = finding.get("line")
    fid = str(finding.get("id") or "")
    title = str(finding.get("title") or "").strip()
    comment = str(finding.get("comment") or "").strip()
    nearby = []
    for t in threads:
        if str(t.get("path") or "") != path:
            continue
        if bot_login and str(t.get("author") or "") != bot_login:
            continue
        tl = t.get("line")
        if line is not None and tl is not None and abs(int(tl) - int(line)) > LINE_TOLERANCE:
            continue
        nearby.append(t)
    if fid:
        marker = re.compile(r"(?<![\w-])" + re.escape(fid) + r"(?![\w-])")   # whole marker: f-1 is not f-10
        for t in nearby:
            if marker.search(str(t.get("body") or "")):
                return t
    if title:
        # the thread's own title (its first line, minus a leading [marker])
        # must EQUAL the finding's title after whitespace normalization: a
        # title that merely extends or contains the requested one is another
        # finding's, a thread carrying a different id marker is another
        # finding's, and an ambiguous match is no match
        wanted = _norm_title(title)
        hits = []
        for t in nearby:
            marker_id, own_title = _thread_identity(str(t.get("body") or ""))
            if fid and marker_id and marker_id != fid:
                continue
            if wanted and _norm_title(own_title) == wanted:
                hits.append(t)
        if len(hits) == 1:
            return hits[0]
        return None
    if comment:
        # no title: the finding's own rendering (its comment plus its
        # evidence, exactly as the bot published it) must equal the thread's
        # published text — nothing shorter, longer, or with different evidence
        wanted = _norm_title(_rendered_comment(finding))
        hits = []
        for t in nearby:
            marker_id, published = _published_text(str(t.get("body") or ""))
            if fid and marker_id and marker_id != fid:
                continue
            if wanted and _norm_title(published) == wanted:
                hits.append(t)
        if len(hits) == 1:
            return hits[0]
        return None
    if bot_login and len(nearby) == 1 and not fid and not title:
        return nearby[0]        # nothing to match on: the bot's only thread at that spot
    return None                 # an identity that does not match is not "close enough"


def classify(finding: dict, threads: list[dict], *, bot_login: str = "") -> str:
    """accepted | disputed | silent for one published finding, judged on
    the finding's OWN thread; no identifiable thread means silent."""
    t = own_thread(finding, threads, bot_login=bot_login)
    if t is None:
        return "silent"
    replies = [r for r in t.get("replies") or [] if not bot_login or r.get("author") != bot_login]
    if any(DISPUTE_RE.search(r.get("body") or "") for r in replies):
        return "disputed"
    if t.get("resolved") or t.get("outdated") or any(ACCEPT_RE.search(r.get("body") or "") for r in replies):
        return "accepted"
    return "silent"


class RbReviewAdapter:
    name = "rb_review"
    descriptive_only = True

    def __init__(self, *, fetch_threads: FetchThreads | None = None, bot_login: str = ""):
        self.fetch_threads = fetch_threads or gh_threads
        self.bot_login = bot_login

    def gold(self, item: str) -> Gold | None:
        return None

    def _published(self, unit: Unit) -> tuple[dict | None, list[dict]]:
        for d in reversed(unit.decisions):
            res = d.get("result") or {}
            if res.get("status") in ("posted", "published") and isinstance(res.get("findings"), list):
                return d, list(res["findings"])
        return None, []

    def fetch(self, unit: Unit, store: TraceStore) -> Outcome | None:
        existing = store.query(kind="outcome", unit_id=unit.unit_id, limit=10_000)
        if any((r.get("result") or {}).get("type") == "rb_thread" for r in existing):
            return Outcome(unit.unit_id, tuple(existing))
        decision, findings = self._published(unit)
        if decision is None:
            return Outcome(unit.unit_id, tuple(existing))
        ctx = decision.get("context") or {}
        repo, pr = str(ctx.get("repo") or ""), ctx.get("pr")
        if not repo or not pr:
            return Outcome(unit.unit_id, tuple(existing))
        try:
            threads = self.fetch_threads(repo, int(pr))
        except Exception as exc:  # noqa: BLE001 - an unavailable thread is "no outcome yet", never a fabricated one
            store.append("outcome", context={"unit_id": unit.unit_id, "item": unit.item, "of": unit.unit_id,
                                             "workflow": unit.workflow},
                         result={"type": "rb_thread_unavailable", "error": str(exc)[:200]})
            return Outcome(unit.unit_id, tuple(store.query(kind="outcome", unit_id=unit.unit_id, limit=10_000)))
        labels = {}
        for i, f in enumerate(findings):
            fid = str(f.get("id") or f"{decision['id']}#{i}")
            labels[fid] = classify(f, threads.get("threads") or [], bot_login=self.bot_login)
        store.append("outcome", context={"unit_id": unit.unit_id, "item": unit.item, "of": unit.unit_id,
                                         "workflow": unit.workflow},
                     result={"type": "rb_thread", "labels": labels, "pr_state": threads.get("state", ""),
                             "head": threads.get("head", ""), "proxy": True, "descriptive_only": True})
        return Outcome(unit.unit_id, tuple(store.query(kind="outcome", unit_id=unit.unit_id, limit=10_000)))

    def match(self, unit: Unit, gold: Gold, outcome: Outcome) -> list[Match]:
        return []

    def findings(self, unit: Unit, outcome: Outcome) -> list[FindingLabel]:
        out = []
        for r in outcome.of_type("rb_thread"):
            for fid, status in (r["result"].get("labels") or {}).items():
                validity = {"accepted": "valid", "disputed": "invalid"}.get(status, "unlabeled")
                out.append(FindingLabel(str(fid), validity, "proxy", (r["id"],)))
        return out

    def review_scores(self, unit: Unit, outcome: Outcome) -> dict[str, float] | None:
        return None
