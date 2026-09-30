"""Unit-test coverage signal for new public functions in a PR (#164).

Deterministic half of a two-part check. This module finds the public
functions and methods a diff ADDS and whether any test file references them
by name — in the diff itself or, when a checkout is available, anywhere in
the reviewed tree. It never decides that a function is untested: a name with
no test reference is only a CANDIDATE, and the reviewer (Strict lenses or the
Direct agent) judges each one — covered indirectly through a caller, trivial,
or a real gap — before anything is published. Repository specifics (which
files are sources, which are tests, what to skip) are adapter data
(`ut_coverage:` in the manifest), so the core stays repo-neutral.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from fnmatch import fnmatch

# At most this many candidates are handed to a reviewer, and at most
# MAX_COMMENTS of its confirmed gaps publish as comments; the rest are named
# in one summary line.
MAX_CANDIDATES = 15
MAX_COMMENTS = 3

_DEFAULT_TEST_GLOBS = ("tests/*", "test/*", "*/tests/*", "*/test/*",
                       "test_*.py", "*/test_*.py", "*_test.py", "conftest.py",
                       "*/conftest.py")
_DEF = re.compile(r"^(?P<indent>[ \t]*)(?:async[ \t]+)?def[ \t]+"
                  r"(?P<name>[A-Za-z_]\w*)[ \t]*\(")
_CLASS = re.compile(r"^(?P<indent>[ \t]*)class[ \t]+(?P<name>[A-Za-z_]\w*)")
_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(?P<start>\d+)(?:,\d+)? @@(?P<ctx>.*)$")
_SKIP_DECORATORS = ("@overload", "@typing.overload", "@abstractmethod",
                    "@abc.abstractmethod")


@dataclass(frozen=True)
class UTCoverageRules:
    source_roots: tuple[str, ...] = ()
    test_globs: tuple[str, ...] = _DEFAULT_TEST_GLOBS
    exclude: tuple[str, ...] = ()

    @classmethod
    def from_manifest(cls, manifest: dict | None) -> "UTCoverageRules | None":
        """None when the adapter disables the check (`enabled: false`) or its
        language is not Python — the extractor only reads Python defs."""
        manifest = manifest or {}
        language = str((manifest.get("repo") or {}).get("language") or "python")
        section = manifest.get("ut_coverage") or {}
        if language.lower() != "python" or section.get("enabled") is False:
            return None
        return cls(
            source_roots=tuple(str(p) for p in section.get("source_roots") or ()),
            test_globs=tuple(str(p) for p in section.get("test_globs") or ())
            or _DEFAULT_TEST_GLOBS,
            exclude=tuple(str(p) for p in section.get("exclude") or ()),
        )

    def is_test(self, path: str) -> bool:
        return any(fnmatch(path, g) for g in self.test_globs)

    def is_source(self, path: str) -> bool:
        if not path.endswith(".py") or self.is_test(path):
            return False
        if any(fnmatch(path, g) for g in self.exclude):
            return False
        return not self.source_roots or path.startswith(self.source_roots)


@dataclass(frozen=True)
class PublicDef:
    path: str
    line: int
    name: str
    owner: str = ""        # enclosing class for a method

    @property
    def qualname(self) -> str:
        return f"{self.owner}.{self.name}" if self.owner else self.name


@dataclass
class CoverageReport:
    candidates: list[PublicDef] = field(default_factory=list)
    referenced: dict[str, list[str]] = field(default_factory=dict)
    searched_tree: bool = False
    truncated: int = 0

    def to_dict(self) -> dict:
        return {
            "candidates": [{"file": d.path, "line": d.line, "name": d.qualname}
                           for d in self.candidates],
            "referenced": {k: v for k, v in self.referenced.items()},
            "searched_tree": self.searched_tree,
            "truncated": self.truncated,
        }


def _is_public(name: str) -> bool:
    return not name.startswith("_")


def _files(diff: str):
    """Yield (path, lines) per file of a unified diff. The path is the b/
    side, or the a/ side for a deleted file: its removed defs still matter,
    because a function moved out of a deleted module is not new API."""
    path, old_path, lines = "", "", []
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            if path:
                yield path, lines
            path, old_path, lines = "", "", []
        elif line.startswith("--- ") and not path:
            source = line[4:].strip()
            old_path = "" if source == "/dev/null" else source.removeprefix("a/")
        elif line.startswith("+++ ") and not path:
            target = line[4:].strip()
            path = old_path if target == "/dev/null" else target.removeprefix("b/")
        elif path:
            lines.append(line)
    if path:
        yield path, lines


def _side_defs(lines: list[str], side: str):
    """Walk one side of a file's hunks ("+" = new, "-" = old) and yield
    (new_line, qualname, owner, name, previous_line, nested, owner_public)
    for every def written on that side. Scope comes from the hunk header and
    the lines visible on that side (context + that side's own lines), so a
    method is named by its enclosing class, never by its bare name."""
    other = "-" if side == "+" else "+"
    new_line = 0
    scope: list[tuple[int, str, str]] = []   # (indent, kind, name)
    previous = ""
    for raw in lines:
        hunk = _HUNK.match(raw)
        if hunk:
            new_line = int(hunk.group("start"))
            scope = []
            # git writes one space, then the context line WITH its source
            # indentation; keep that indentation or a method header would
            # look like a module-level def and its siblings like nested ones
            header = hunk.group("ctx").removeprefix(" ").rstrip()
            m = _CLASS.match(header) or _DEF.match(header)
            if m:
                kind = "class" if header.lstrip().startswith("class") else "def"
                scope.append((len(m.group("indent")), kind, m.group("name")))
            previous = ""
            continue
        if raw.startswith((other, "\\")):   # the other side / "\ No newline"
            continue
        text = raw[1:] if raw[:1] in ("+", "-", " ") else raw
        own = raw.startswith(side)
        if text.strip():
            indent = len(text) - len(text.lstrip())
            m_class, m_def = _CLASS.match(text), _DEF.match(text)
            if m_class or m_def:
                while scope and scope[-1][0] >= indent:
                    scope.pop()
            if m_def and own:
                name = m_def.group("name")
                parent = scope[-1] if scope else None
                owner = parent[2] if parent is not None and parent[1] == "class" else ""
                nested = parent is not None and parent[1] == "def"
                yield (new_line, f"{owner}.{name}" if owner else name, owner,
                       name, previous, nested)
            if m_class:
                scope.append((indent, "class", m_class.group("name")))
            elif m_def:
                scope.append((indent, "def", m_def.group("name")))
            previous = text
        if side == "+":
            new_line += 1


def new_public_defs(diff: str, rules: UTCoverageRules) -> list[PublicDef]:
    """Public functions and methods the diff adds to source files.

    A def is a method when an enclosing `class` is visible in the same hunk
    (context or added lines) or named in the hunk header; an indented def with
    a `def` as its visible parent is a nested helper and is skipped. Private
    names, dunders, and @overload/@abstractmethod stubs are skipped. A def
    whose qualified name (class + method, or module function) the diff also
    removes is an edit or a move, not new API; a same-named method of a
    DIFFERENT class is unrelated and still counts."""
    files = list(_files(diff))
    removed = {qual for _path, lines in files
               for (_l, qual, *_rest) in _side_defs(lines, "-")}
    found: list[PublicDef] = []
    for path, lines in files:
        if not rules.is_source(path):
            continue
        for line, qual, owner, name, previous, nested in _side_defs(lines, "+"):
            if (_is_public(name) and not nested and qual not in removed
                    and not previous.strip().startswith(_SKIP_DECORATORS)
                    and (not owner or _is_public(owner))):
                found.append(PublicDef(path, line, name, owner))
    return found


def _word(name: str) -> re.Pattern[str]:
    return re.compile(rf"\b{re.escape(name)}\b")


def _diff_test_references(diff: str, rules: UTCoverageRules,
                          defs: list[PublicDef]) -> dict[str, list[str]]:
    hits: dict[str, list[str]] = {}
    for path, lines in _files(diff):
        if not rules.is_test(path):
            continue
        added = "\n".join(l[1:] for l in lines if l.startswith("+"))
        for d in defs:
            if _word(d.name).search(added):
                hits.setdefault(d.qualname, []).append(path)
    return hits


def _tree_test_references(repo: str, rules: UTCoverageRules, name: str,
                          timeout: float) -> list[str]:
    try:
        r = subprocess.run(["git", "grep", "-l", "-w", "-F", "-e", name],
                           cwd=repo, capture_output=True, text=True,
                           timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return []
    return [p for p in (r.stdout or "").splitlines() if rules.is_test(p)][:3]


def analyze(diff: str, rules: UTCoverageRules, repo: str | None = None,
            *, timeout: float = 10.0) -> CoverageReport:
    """Candidates = new public defs with no test reference in the diff nor,
    when `repo` (the reviewed checkout) is given, in its test files."""
    report = CoverageReport(searched_tree=bool(repo))
    defs = new_public_defs(diff, rules)
    report.referenced = _diff_test_references(diff, rules, defs)
    for d in defs:
        if d.qualname in report.referenced:
            continue
        if repo:
            tree = _tree_test_references(repo, rules, d.name, timeout)
            if tree:
                report.referenced[d.qualname] = tree
                continue
        report.candidates.append(d)
    report.truncated = max(0, len(report.candidates) - MAX_CANDIDATES)
    report.candidates = report.candidates[:MAX_CANDIDATES]
    return report


REVIEWER_INSTRUCTIONS = (
    "For EACH candidate, read the function and search the tests (by its "
    "name and by its callers) before deciding: (a) covered indirectly — a "
    "test exercises it through a caller; name that test; (b) trivial — pure "
    "delegation, a constant, or a stub, where a dedicated test adds nothing; "
    "or (c) a real gap. File each real gap as ONE comment: disposition "
    "`publish`, severity `minor`, `kind: untested_api`, anchored on the "
    "def's file:line given here, naming the behavior a unit test should "
    "pin. Any other finding about the same function is a separate comment "
    "without that kind. At most "
    f"{MAX_COMMENTS} such comments; name any further gaps in one summary "
    "line. Never file (a) or (b).")


def render(report: CoverageReport) -> str:
    """The reviewer-facing evidence block; empty when there is nothing to
    judge."""
    if not report.candidates:
        return ""
    where = ("the diff and the reviewed tree's test files" if report.searched_tree
             else "the diff's test files")
    lines = [f"- {d.path}:{d.line} `{d.qualname}`" for d in report.candidates]
    if report.truncated:
        lines.append(f"- … {report.truncated} more not listed")
    return ("NEW PUBLIC FUNCTIONS WITH NO TEST REFERENCE — candidates only: "
            f"no file in {where} names them.\n" + "\n".join(lines)
            + "\n" + REVIEWER_INSTRUCTIONS)


GAP_KIND = "untested_api"


def cap_gap_comments(comments: list[dict], report: CoverageReport | None
                     ) -> tuple[list[dict], list[str]]:
    """Keep at most MAX_COMMENTS comments the reviewer classified as a
    missing unit test (`kind: untested_api`); return (kept comments, names of
    the dropped gaps) so the caller can name them in the summary instead of
    losing them. Only that explicit classification counts: any other finding
    on the same function, whatever its anchor or severity, is never capped.
    The `kind` field is internal and is removed from every comment."""
    anchors = {(d.path, d.line): d.qualname
               for d in (report.candidates if report is not None else [])}
    kept: list[dict] = []
    dropped: list[str] = []
    seen = 0
    for c in comments:
        is_gap = str(c.pop("kind", "") or "").strip().lower() == GAP_KIND
        if not is_gap:
            kept.append(c)
            continue
        seen += 1
        if seen <= MAX_COMMENTS:
            kept.append(c)
            continue
        f = str(c.get("file") or "")
        dropped.append(next(
            (name for (p, l), name in anchors.items()
             if l == c.get("line") and f and (f.endswith(p) or p.endswith(f))),
            f"{f}:{c.get('line')}"))
    return kept, dropped
