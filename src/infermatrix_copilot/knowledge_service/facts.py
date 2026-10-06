"""Upstream fact attestations: what a changed rule claims about its upstream.

A rule states facts about the upstream repository it describes: the PRs it
cites (``^[PR #N]``) were merged, and the files (and ``path::Symbol``
definitions) it names exist. The service observes those facts on a pinned
upstream SHA when it gates a change and signs them into the verdict; the
publisher observes every one again from the upstream itself (the GitHub API
and its own mirror) right before merging, and does not merge on any
difference (design v8 §7.1, §8.2).

Only claims that can be resolved are facts: a backticked token is a path claim
when its first segment is a top-level entry of the upstream tree (``pkg/
x.py`` is, ``config/x.py`` is not). Active rules must hold every claim; a
retired rule's claims are recorded as observed (the behaviour may have moved
without the file going away), but the PR its retirement names as evidence
must be merged.

Standard library only.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import Iterable, Protocol

PR_CITATION = re.compile(r"\^\[\s*PR\s*#(?P<n>\d{1,7})\s*\]")
EVIDENCE_PR = re.compile(r"\bPR\s*#(?P<n>\d{1,7})\b")
CODE_SPAN = re.compile(r"`(?P<tok>[^`\n]{1,200})`")
SEGMENT = re.compile(r"[A-Za-z0-9_.-]+")
PATH = re.compile(r"(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]*")  # at least one slash
SYMBOL = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*")
MAX_FACTS = 200


class FactsError(RuntimeError):
    """The upstream could not be read (unreachable, unknown SHA, API error)."""


class Observer(Protocol):
    """Reads one upstream repository. Raises FactsError when it cannot tell."""

    repository: str

    def head(self) -> str: ...

    def top_level(self, sha: str) -> set[str]: ...

    def path_exists(self, sha: str, path: str) -> bool: ...

    def file_text(self, sha: str, path: str) -> str | None: ...

    def pull(self, number: int) -> dict: ...


@dataclass(frozen=True)
class Claim:
    kind: str            # pr | path | symbol
    must_hold: bool      # an active rule's claim (a retired rule's is only recorded)
    pr: int = 0
    path: str = ""
    symbol: str = ""

    @property
    def key(self) -> tuple:
        return (self.kind, self.pr, self.path, self.symbol)


def claims_in(text: str, top_level: set[str], *, active: bool, evidence: str = "") -> list[Claim]:
    """The resolvable claims of one rule's text (and of its retirement evidence)."""
    out: list[Claim] = [Claim("pr", active, pr=int(m.group("n"))) for m in PR_CITATION.finditer(text)]
    if not active:
        out += [Claim("pr", True, pr=int(m.group("n"))) for m in EVIDENCE_PR.finditer(evidence)]
    for m in CODE_SPAN.finditer(text):
        token = m.group("tok").strip()
        path, _, symbol = token.partition("::")
        # a bare top-level name is a claim only with a symbol (`setup.py::main`):
        # alone it is too often a word (`tests`, `docs`)
        resolvable = PATH.fullmatch(path) or (symbol and SEGMENT.fullmatch(path))
        if not resolvable or path.split("/", 1)[0] not in top_level:
            continue
        if any(part and set(part) == {"."} for part in path.split("/")):
            continue  # `..` escapes, `...` placeholders
        if symbol:
            if SYMBOL.fullmatch(symbol) and not path.endswith("/"):
                out.append(Claim("symbol", active, path=path, symbol=symbol))
            continue
        out.append(Claim("path", active, path=path.rstrip("/")))
    return out


def merge_claims(claims: Iterable[Claim]) -> list[Claim]:
    """One claim per fact; it must hold when any rule requires it."""
    merged: dict[tuple, Claim] = {}
    for claim in claims:
        seen = merged.get(claim.key)
        if seen is None or (claim.must_hold and not seen.must_hold):
            merged[claim.key] = claim
    return sorted(merged.values(), key=lambda c: c.key)


def defines(text: str, symbol: str, path: str = "") -> bool:
    """The file defines ``symbol``. Python is parsed (text in strings and
    comments never counts): ``A.b`` must be a qualified definition, a single
    name may be defined at any depth. Other files, or Python this
    interpreter cannot parse, fall back to line patterns."""
    if path.endswith((".py", ".pyi")):
        try:
            names = _python_definitions(ast.parse(text))
        except (SyntaxError, ValueError, RecursionError):
            names = None
        if names is not None:
            return symbol in names or ("." not in symbol and any(n.rsplit(".", 1)[-1] == symbol for n in names))
    for part in symbol.split("."):
        name = re.escape(part)
        if not re.search(rf"(?m)^\s*(?:async\s+def|def|class)\s+{name}\b|^\s*{name}\s*(?::[^=\n]*)?=", text):
            return False
    return True


def _python_definitions(tree: ast.AST) -> set[str]:
    """Qualified names of every def, class, assigned and imported name (``A.b`` for a member)."""
    out: set[str] = set()

    def visit(node: ast.AST, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out.add(prefix + child.name)
                visit(child, prefix + child.name + ".")
                continue
            targets = child.targets if isinstance(child, ast.Assign) else \
                [child.target] if isinstance(child, (ast.AnnAssign, ast.AugAssign)) else []
            for target in targets:
                out.update(prefix + name for name in _bound(target))
            if isinstance(child, (ast.Import, ast.ImportFrom)):  # a re-export binds the name too
                out.update(prefix + (a.asname or a.name.split(".")[0]) for a in child.names if a.name != "*")
            visit(child, prefix)

    visit(tree, "")
    return out


def _bound(target: ast.AST) -> list[str]:
    """Names an assignment target binds: ``a``, ``a, (b, *c)``; never the names
    it only reads (``d[k] = v``, ``obj.attr = v``)."""
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, ast.Starred):
        return _bound(target.value)
    if isinstance(target, (ast.Tuple, ast.List)):
        return [name for element in target.elts for name in _bound(element)]
    return []


def observe(claim: Claim, observer: Observer, sha: str) -> dict:
    """The fact as the upstream shows it at ``sha`` (raises FactsError)."""
    fact: dict = {"kind": claim.kind, "repository": observer.repository, "must_hold": claim.must_hold}
    if claim.kind == "pr":
        pull = observer.pull(claim.pr)
        fact.update(pr=claim.pr, merged=bool(pull.get("merged")),
                    merge_commit_sha=str(pull.get("merge_commit_sha") or "") if pull.get("merged") else "")
    elif claim.kind == "path":
        fact.update(sha=sha, path=claim.path, exists=observer.path_exists(sha, claim.path))
    else:
        text = observer.file_text(sha, claim.path)
        fact.update(sha=sha, path=claim.path, symbol=claim.symbol,
                    defined=text is not None and defines(text, claim.symbol, claim.path))
    return fact


def holds(fact: dict) -> bool:
    return bool(fact.get("merged") if fact["kind"] == "pr" else
                fact.get("exists") if fact["kind"] == "path" else fact.get("defined"))


def describe(fact: dict) -> str:
    if fact["kind"] == "pr":
        return f"{fact['repository']} PR #{fact['pr']} is not merged"
    if fact["kind"] == "path":
        return f"{fact['path']} does not exist at {fact['repository']}@{fact['sha'][:12]}"
    return f"{fact['path']}::{fact['symbol']} is not defined at {fact['repository']}@{fact['sha'][:12]}"


def attest(claims: list[Claim], observer: Observer) -> tuple[dict, list[dict], list[str]]:
    """Observe every claim on the upstream's current head: (upstream, facts,
    problems). A problem is a claim an active rule (or a retirement's
    evidence) requires that does not hold."""
    sha = observer.head()
    claims = merge_claims(claims)
    if len(claims) > MAX_FACTS:
        raise FactsError(f"{len(claims)} upstream claims (limit {MAX_FACTS}); split the change")
    facts = [observe(claim, observer, sha) for claim in claims]
    problems = [describe(f) for f in facts if f["must_hold"] and not holds(f)]
    return {"repository": observer.repository, "sha": sha}, facts, problems


def recheck(upstream: dict, facts: list[dict], observer: Observer) -> list[str]:
    """The publisher's side: every signed fact observed again, independently.
    Raises FactsError when the upstream cannot be read (not a verdict on the
    facts: retried)."""
    if not facts:
        return []
    problems = []
    if upstream.get("repository") != observer.repository:
        return [f"facts are about {upstream.get('repository')}, not {observer.repository}"]
    sha = str(upstream.get("sha") or "")
    if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", sha):
        return ["the verdict names no pinned upstream SHA"]
    for fact in facts:
        try:
            claim = Claim(str(fact["kind"]), bool(fact["must_hold"]), pr=int(fact.get("pr") or 0),
                          path=str(fact.get("path") or ""), symbol=str(fact.get("symbol") or ""))
        except (KeyError, TypeError, ValueError):
            problems.append(f"malformed fact: {str(fact)[:120]}")
            continue
        if claim.kind not in ("pr", "path", "symbol") or fact.get("repository") != observer.repository \
                or (claim.kind != "pr" and fact.get("sha") != sha):
            problems.append(f"malformed fact: {str(fact)[:120]}")
            continue
        if claim.must_hold and not holds(fact):
            problems.append("signed a fact that does not hold: " + describe(fact))
            continue
        actual = observe(claim, observer, sha)
        if actual != fact:
            problems.append(f"upstream disagrees: signed {_short(fact)}, observed {_short(actual)}")
    return problems


def _short(fact: dict) -> str:
    keep = ("pr", "merged", "merge_commit_sha", "path", "symbol", "exists", "defined")
    return ", ".join(f"{k}={fact[k]}" for k in keep if k in fact)
