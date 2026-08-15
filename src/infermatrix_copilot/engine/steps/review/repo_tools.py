"""Read-only investigation tools for review agent steps: change archaeology
and a numeric probe.

Wave-2 recall forensics (2026-08-15) measured that the judge-decisive moves the
CC+Opus baseline makes and our passes cannot are all one-command capabilities
the read-only toolset simply lacked:

* `git diff --stat base..HEAD` — proved requested removals were absent from a
  docs PR (pr5715's two GT findings were exactly this check);
* reading a file at the merge-base — the "what did this look like before"
  contrast behind drive-by regressions (pr5840's FP8 finding);
* `git show <commit>` / `git log -S` — reconstructing the regression a fix
  reverts (pr5884's Bagel chain, the core of the GT thread);
* evaluating the PR's own arithmetic — pr5840's calibration polynomial and
  pr5863's memory model were both overturned by a five-line numeric probe the
  passes could not run (`read_only` scope has no shell).

Every tool here is read-only by construction: fixed argv (no shell), input
validation on anything that reaches the command line, bounded output. They are
step-provided `extra` tools, so they bypass the builtin allowlist exactly like
the gh read tools — and the tool bridge reconstructs them for harness backends
from `scope.root` (they need nothing from a live StepContext).
"""

from __future__ import annotations

import ast
import math
import re
import subprocess
from pathlib import Path

from ....tools import ToolDef, bounded

_SHA_RE = re.compile(r"^[0-9a-f]{6,40}$")
_BASE_REFS = ("origin/main", "origin/master", "main", "master")


def _git(repo: Path, *args: str, timeout: int = 30) -> tuple[int, str]:
    out = subprocess.run(["git", *args], cwd=str(repo), capture_output=True,
                         text=True, encoding="utf-8", errors="replace",
                         timeout=timeout)
    return out.returncode, (out.stdout or out.stderr or "").strip()


def _merge_base(repo: Path) -> str:
    """The PR's base commit: merge-base of HEAD with the default branch.
    Cached per repo path — worktrees are immutable for the life of a review."""
    cached = _merge_base_cache.get(str(repo))
    if cached:
        return cached
    for ref in _BASE_REFS:
        code, out = _git(repo, "merge-base", "HEAD", ref)
        if code == 0 and _SHA_RE.match(out):
            _merge_base_cache[str(repo)] = out
            return out
    raise RuntimeError("could not resolve a merge-base with the default branch")


_merge_base_cache: dict[str, str] = {}


def _safe_rel_path(path: str) -> str:
    """A repo-relative path that cannot be a git option or escape the repo.
    git resolves `<sha>:<path>` inside the object store, so traversal is inert,
    but a leading `-` would be parsed as a flag."""
    p = str(path or "").strip().replace("\\", "/")
    if not p or p.startswith(("-", "/")) or ".." in p.split("/"):
        raise ValueError(f"path must be repo-relative without '..': {path!r}")
    return p


# -- calc: restricted arithmetic ---------------------------------------------

_CALC_FUNCS = {
    "abs": abs, "min": min, "max": max, "round": round, "sum": sum,
    "len": len, "pow": pow, "sqrt": math.sqrt, "log": math.log,
    "log2": math.log2, "log10": math.log10, "exp": math.exp,
    "floor": math.floor, "ceil": math.ceil,
}
_CALC_NAMES = {"pi": math.pi, "e": math.e, **_CALC_FUNCS}
_CALC_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Compare,
    ast.BoolOp, ast.IfExp, ast.Tuple, ast.List, ast.Call, ast.Name,
    ast.Load, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod,
    ast.Pow, ast.UAdd, ast.USub, ast.Not, ast.Eq, ast.NotEq, ast.Lt,
    ast.LtE, ast.Gt, ast.GtE, ast.And, ast.Or,
)


def _calc(expr: str, **_: object) -> str:
    """Evaluate a pure-arithmetic expression (see the ToolDef description for
    the allowed surface). This is the bounded numeric probe the forensics
    called for — enough to evaluate a calibration polynomial or a memory
    model, structurally unable to touch the filesystem or the network."""
    text = str(expr or "").strip()
    if not text or len(text) > 500:
        raise ValueError("expr must be 1..500 chars")
    tree = ast.parse(text, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, _CALC_NODES):
            raise ValueError(f"disallowed syntax: {type(node).__name__}")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) \
                    or node.func.id not in _CALC_FUNCS or node.keywords:
                raise ValueError("only bare calls to the allowed functions")
        if isinstance(node, ast.Name) and node.id not in _CALC_NAMES:
            raise ValueError(f"unknown name: {node.id}")
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            exp = node.right
            if isinstance(exp, ast.Constant) and isinstance(exp.value, (int, float)) \
                    and abs(exp.value) > 1000:
                raise ValueError("exponent too large")
        if isinstance(node, ast.Constant) \
                and not isinstance(node.value, (int, float, bool)):
            raise ValueError("only numeric constants")
    result = eval(compile(tree, "<calc>", "eval"),  # noqa: S307 — AST-whitelisted
                  {"__builtins__": {}}, dict(_CALC_NAMES))
    return bounded(repr(result), 2_000, "calc")


# -- the tool set ------------------------------------------------------------

def review_repo_tools(repo: Path | None) -> dict[str, ToolDef]:
    """Change-archaeology + numeric-probe tools for one PR-time worktree.
    Returns {} when there is no repo checkout (evidence-only runs)."""
    if repo is None:
        return {}

    def diff_stat(**_: object) -> str:
        """`git diff --stat <merge-base> HEAD` — the complete changed-file
        list with sizes, independent of any diff-text truncation."""
        base = _merge_base(repo)
        code, out = _git(repo, "diff", "--stat", base, "HEAD")
        if code != 0:
            return f"git failed: {out[:400]}"
        return bounded(f"merge-base {base[:12]}\n{out}", 8_000, "diff_stat")

    def file_at_base(path: str, offset: int = 0, **_: object) -> str:
        """Read a file's content AT THE MERGE-BASE (pre-PR state), windowed
        like read_file. `(absent at base)` for files the PR added."""
        rel = _safe_rel_path(path)
        base = _merge_base(repo)
        code, out = _git(repo, "show", f"{base}:{rel}", timeout=30)
        if code != 0:
            return (f"(absent at base {base[:12]})"
                    if "does not exist" in out or "exists on disk" in out
                    else f"git failed: {out[:400]}")
        if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
            raise ValueError(f"offset must be an int >= 0, got {offset!r}")
        if offset and offset >= len(out):
            return f"[empty: offset {offset} is past end of file ({len(out)} chars)]"
        return bounded(out[offset:], 24_000, "file_at_base",
                       hint=lambda kept: f"page with offset={offset + kept}")

    def show_commit(sha: str, **_: object) -> str:
        """One commit's message + stat + patch (bounded). Use on commit-
        timeline entries to see what a listed commit actually changed
        (add-then-revert churn, the regression a fix reverts)."""
        s = str(sha or "").strip().lower()
        if not _SHA_RE.match(s):
            raise ValueError(f"sha must be 6-40 hex chars, got {sha!r}")
        code, out = _git(repo, "show", "--stat", "--patch", "--no-color", s)
        if code != 0:
            return f"git failed: {out[:400]}"
        return bounded(out, 12_000, "show_commit",
                       hint="the patch is clipped — grep the tree for specifics")

    def search_history(term: str, path: str = "", **_: object) -> str:
        """Commits whose diff ADDED or REMOVED `term` (`git log -S`), newest
        first — when was this symbol/value introduced or dropped, and by
        which commit. Optionally restricted to one path."""
        t = str(term or "").strip()
        if not t or len(t) > 200:
            raise ValueError("term must be 1..200 chars")
        args = ["log", f"-S{t}", "--oneline", "--no-color", "-n", "12"]
        if path:
            args += ["--", _safe_rel_path(path)]
        code, out = _git(repo, *args, timeout=60)
        if code != 0:
            return f"git failed: {out[:400]}"
        return bounded(out or "(no commits touch this term)", 4_000,
                       "search_history")

    _s = {"type": "string"}
    return {
        "diff_stat": ToolDef(
            "diff_stat",
            "Complete changed-file list of this PR (`git diff --stat "
            "merge-base..HEAD`) — use to verify claimed inclusions/removals "
            "and to see files a truncated diff text dropped. Read-only.",
            {"type": "object", "properties": {}, "required": []}, diff_stat),
        "file_at_base": ToolDef(
            "file_at_base",
            "Read a file AT THE MERGE-BASE (pre-PR content), windowed at "
            "24,000 chars (page with offset). Use to contrast old vs new "
            "beyond the diff's context lines. Read-only.",
            {"type": "object",
             "properties": {"path": _s, "offset": {"type": "integer"}},
             "required": ["path"]}, file_at_base),
        "show_commit": ToolDef(
            "show_commit",
            "One commit's message+stat+patch (bounded 12,000 chars). Use on "
            "commit-timeline SHAs to see what a commit really changed. "
            "Read-only.",
            {"type": "object", "properties": {"sha": _s},
             "required": ["sha"]}, show_commit),
        "search_history": ToolDef(
            "search_history",
            "`git log -S<term>` (newest 12): commits that added/removed a "
            "symbol or value — when was it introduced/dropped and by which "
            "commit. Optional `path` restricts to one file. Read-only.",
            {"type": "object", "properties": {"term": _s, "path": _s},
             "required": ["term"]}, search_history),
        "calc": ToolDef(
            "calc",
            "Evaluate a pure-arithmetic Python expression (numbers, + - * / "
            "// % **, comparisons, min/max/abs/round/sum/len/pow/sqrt/log/"
            "log2/log10/exp/floor/ceil, pi, e, list/tuple literals). Use to "
            "CHECK the PR's own numbers — a fitted polynomial, a memory "
            "model, a threshold — instead of trusting them. No variables, "
            "no I/O.",
            {"type": "object", "properties": {"expr": _s},
             "required": ["expr"]}, _calc),
    }
