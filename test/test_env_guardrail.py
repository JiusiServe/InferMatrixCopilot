"""D8 — the process-env mutation guardrail, scoped-global (plan §2.9).

AST census over `src/infermatrix_copilot/`: every mutation of the process
environment — subscript assignment/deletion on `os.environ` (alias-aware),
mutating method calls (`update`/`setdefault`/`pop`/`clear`), and
`os.putenv`/`os.unsetenv` — is forbidden EXCEPT the pinned census below:
exactly the v1 backend's recorded bridge sites (`rebase_native.py`, the
owner-accepted exception with a PR7 sunset). The census is exact per
site-kind and count, so a NEW mutation inside the exempt module fails too,
and the list can only shrink (PR7 empties it). Dynamic circumvention
(getattr strings, exec) is out of scope — the runtime guardrail fixtures
remain the second layer.
"""

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src" / "infermatrix_copilot"

# the recorded census — {relpath: {mutation-kind: count}}:
# * rebase_native.py: the v1 env bridge (plan §4 exception 1; sunset PR7)
# * cli/entry.py: process-START bootstrap stamping the invocation id into
#   the CLI's own env before any run exists (self-identity propagation to
#   run subprocesses — not a run-time mutation; pre-existing, recorded)
EXEMPT_CENSUS = {
    "engine/steps/rebase_native.py": {"subscript-assign": 7},
    "cli/entry.py": {"subscript-assign": 1},
}

_MUTATING_METHODS = {"update", "setdefault", "pop", "clear"}


class _EnvMutationVisitor(ast.NodeVisitor):
    def __init__(self):
        self.os_aliases = {"os"}
        self.environ_aliases = set()
        self.hits: list[tuple[str, int]] = []

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name == "os":
                self.os_aliases.add(alias.asname or "os")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module == "os":
            for alias in node.names:
                if alias.name == "environ":
                    self.environ_aliases.add(alias.asname or "environ")
                if alias.name in ("putenv", "unsetenv"):
                    self.environ_aliases.add(
                        f"__call__:{alias.asname or alias.name}")
        self.generic_visit(node)

    def _is_environ(self, node) -> bool:
        if isinstance(node, ast.Attribute) and node.attr == "environ" \
                and isinstance(node.value, ast.Name) \
                and node.value.id in self.os_aliases:
            return True
        return isinstance(node, ast.Name) and node.id in self.environ_aliases

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Subscript) \
                    and self._is_environ(target.value):
                self.hits.append(("subscript-assign", node.lineno))
        self.generic_visit(node)

    def visit_AugAssign(self, node):
        if isinstance(node.target, ast.Subscript) \
                and self._is_environ(node.target.value):
            self.hits.append(("subscript-assign", node.lineno))
        self.generic_visit(node)

    def visit_Delete(self, node):
        for target in node.targets:
            if isinstance(target, ast.Subscript) \
                    and self._is_environ(target.value):
                self.hits.append(("subscript-del", node.lineno))
        self.generic_visit(node)

    def visit_Call(self, node):
        fn = node.func
        if isinstance(fn, ast.Attribute):
            if fn.attr in _MUTATING_METHODS and self._is_environ(fn.value):
                self.hits.append((f"call-{fn.attr}", node.lineno))
            if fn.attr in ("putenv", "unsetenv") \
                    and isinstance(fn.value, ast.Name) \
                    and fn.value.id in self.os_aliases:
                self.hits.append((f"call-{fn.attr}", node.lineno))
        elif isinstance(fn, ast.Name) \
                and f"__call__:{fn.id}" in self.environ_aliases:
            self.hits.append((f"call-{fn.id}", node.lineno))
        self.generic_visit(node)


def _scan(path: Path) -> list[tuple[str, int]]:
    visitor = _EnvMutationVisitor()
    visitor.visit(ast.parse(path.read_text(encoding="utf-8")))
    return visitor.hits


def test_process_env_never_mutated_outside_the_census():
    offenders: dict[str, dict[str, int]] = {}
    for path in sorted(SRC.rglob("*.py")):
        rel = path.relative_to(SRC).as_posix()
        hits = _scan(path)
        if not hits:
            continue
        counts: dict[str, int] = {}
        for kind, _line in hits:
            counts[kind] = counts.get(kind, 0) + 1
        if counts != EXEMPT_CENSUS.get(rel):
            offenders[rel] = counts
    assert offenders == {}, (
        "process-env mutation outside the recorded v1-bridge census "
        f"(plan §2.9; the census can only SHRINK): {offenders}")


def test_census_matches_reality_exactly():
    """The exemption is a census, not a pass: the exempt module must have
    EXACTLY the recorded sites — a new mutation there fails as loudly as
    one anywhere else, and a removed one must shrink the census."""
    for rel, expected in EXEMPT_CENSUS.items():
        hits = _scan(SRC / rel)
        counts: dict[str, int] = {}
        for kind, _line in hits:
            counts[kind] = counts.get(kind, 0) + 1
        assert counts == expected, (rel, counts)


def test_visitor_catches_all_mutation_forms(tmp_path):
    """The scanner itself is tested: every covered mutation form in every
    alias spelling is caught; reads are not flagged."""
    sample = tmp_path / "sample.py"
    sample.write_text(
        "import os\n"
        "import os as _o\n"
        "from os import environ\n"
        "from os import environ as E\n"
        "from os import putenv as pv\n"
        "os.environ['A'] = '1'\n"
        "_o.environ['B'] = '1'\n"
        "environ['C'] = '1'\n"
        "E['D'] = '1'\n"
        "del os.environ['A']\n"
        "os.environ.update(X='1')\n"
        "environ.setdefault('Y', '1')\n"
        "E.pop('Z', None)\n"
        "os.environ.clear()\n"
        "os.putenv('P', '1')\n"
        "_o.unsetenv('P')\n"
        "pv('Q', '1')\n"
        "x = os.environ.get('R')\n"          # read: not flagged
        "y = dict(os.environ)\n",            # read: not flagged
        encoding="utf-8")
    hits = _scan(sample)
    kinds = sorted(k for k, _ in hits)
    assert kinds == sorted([
        "subscript-assign", "subscript-assign", "subscript-assign",
        "subscript-assign", "subscript-del", "call-update",
        "call-setdefault", "call-pop", "call-clear", "call-putenv",
        "call-unsetenv", "call-pv"]), kinds
