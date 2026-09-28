"""The kb-gate verifier (PR precheck and merge group) and its pinned bundle, offline."""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from infermatrix_copilot.kb_service.gate import changes_between, run_gate, signable_blocks
from infermatrix_copilot.kb_service.models import ModelReply, ModelRole
from infermatrix_copilot.knowledge_service import gate_verifier as gv
from infermatrix_copilot.knowledge_service.ops import KnowledgeOperation as Op, apply_operations
from infermatrix_copilot.knowledge_service.signing import public_key_text, sign
from infermatrix_copilot.knowledge_service.verdict import build_verdict, manifest_from_files

ROOT = Path(__file__).resolve().parents[1]
REPO = "acme/kb"
PAGE = "repos/demo/core/rules.md"
JUDGE = ModelRole("judge", "codex", "gpt-6-sol", "medium")
KEY = Ed25519PrivateKey.generate()


def _rule(rule_id: str, cite: str = "PR #10") -> str:
    return (f"## {rule_id} — keep the demo queue bounded\n\n"
            "- 触发：修改 demo queue 的容量或背压逻辑时。\n"
            "- 强制：队列满时拒绝新请求并返回明确错误，不能无界增长。\n"
            f"- 验收：测试覆盖满队列拒绝路径。 ^[{cite}]\n")


def _tree() -> dict[str, str]:
    return {
        "repos/demo/_index.md": "# demo\n",
        "repos/demo/core/_index.md": "# core\n\n- [rules](rules.md)\n",
        "repos/demo/api/_index.md": "# api\n",
        "repos/demo/_routes.yaml": (
            "schema_version: 1\nowners:\n  - owner: core\n    path: repos/demo/core/rules.md\n"
            "    signals: [queue]\n    scope_prefixes: [demo/core/]\n"),
        PAGE: ("---\ntitle: \"Demo core rules\"\ncreated: 2026-09-01\nupdated: 2026-09-01\n"
               "type: rule\ntags: [demo]\nsources: [\"PR #10\"]\n---\n\n# Demo core rules\n\n"
               + _rule("DEMO-1a")),
    }


class _Gateway:
    def call_json(self, role, *, system, prompt, validate=None):
        if '"directory"' in prompt:
            data = {"verdict": "consistent", "conflicts": []}
        else:
            dims = json.loads(prompt.split("<untrusted_data>\n", 1)[1].rsplit("\n</untrusted_data>", 1)[0])
            data = {"dimensions": {d: "yes" for d in dims["dimensions_to_answer"]}, "reasons": {}}
        return ModelReply(role, data, json.dumps(data), role.model, {}, 0.1)


# -- a git "remote" with main and PR refs, and the verifier's clone -----------------

def _git(cwd: Path, *args: str, env: dict | None = None) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True,
                          env={**os.environ, **(env or {})}).stdout.strip()


def _write(repo: Path, files: dict[str, str | None], *, prefix: str = "knowledge/") -> None:
    for rel, text in files.items():
        path = repo / (prefix + rel)
        if text is None:
            path.unlink()
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@e", "commit", "-q", "--allow-empty", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


class World:
    """remote repo + verifier clone + a fake GitHub API."""

    def __init__(self, tmp_path: Path):
        self.remote = tmp_path / "remote"
        self.remote.mkdir()
        _git(self.remote, "init", "-q", "-b", "main")
        _write(self.remote, _tree())
        (self.remote / "src").mkdir()
        (self.remote / "src" / "app.py").write_text("x = 1\n")
        self.main = _commit(self.remote, "base")
        self.ws = tmp_path / "ws"
        _git(tmp_path, "clone", "-q", str(self.remote), str(self.ws))
        self.prs: dict[int, dict] = {}
        self.comments: dict[int, list[dict]] = {}
        self.reviews: dict[tuple[int, int], dict] = {}
        self.posts: list[tuple[str, dict]] = []
        self.holds = {"global": False, "repos": [], "prs": []}
        self.holds_age = 0.0
        self.codeowners = "/.github/ @alice\n"

    # branches ----------------------------------------------------------------
    def branch(self, number: int, files: dict[str, str | None], *, code: dict[str, str] | None = None,
               start: str | None = None) -> str:
        _git(self.remote, "checkout", "-q", "-B", f"pr-{number}", start or self.main)
        _write(self.remote, files)
        if code:
            _write(self.remote, code, prefix="")
        head = _commit(self.remote, f"pr {number}")
        _git(self.remote, "update-ref", f"refs/pull/{number}/head", head)
        _git(self.remote, "checkout", "-q", "main")
        self.prs[number] = {"number": number, "state": "open", "draft": False, "labels": [],
                            "head": {"sha": head}, "base": {"ref": "main"}}
        return head

    def advance_main(self, files: dict[str, str | None], *, code: dict[str, str] | None = None) -> str:
        _git(self.remote, "checkout", "-q", "main")
        _write(self.remote, files)
        if code:
            _write(self.remote, code, prefix="")
        self.main = _commit(self.remote, "main moves")
        return self.main

    def merge_group(self, numbers: list[int]) -> str:
        """gh-readonly-queue style: one merge commit per PR on top of main."""
        _git(self.remote, "checkout", "-q", "-B", "queue", self.main)
        for number in numbers:
            _git(self.remote, "-c", "user.name=q", "-c", "user.email=q@e", "merge", "-q", "--no-ff",
                 "-m", f"Merge pull request #{number}", self.prs[number]["head"]["sha"])
        head = _git(self.remote, "rev-parse", "HEAD")
        _git(self.remote, "checkout", "-q", "main")
        _git(self.ws, "fetch", "-q", "origin", f"+{head}:refs/queue/head")
        return head

    # verdicts ----------------------------------------------------------------
    def verdict(self, number: int, head_files: dict[str, str], *, key=KEY, source="auto", pr=None,
                head_sha=None, issued_at=None, mutate=None, **kw) -> dict:
        base = _tree()
        head = {**base, **head_files}
        touched = set(head_files)
        decision = run_gate(base=base, head=head, changes=changes_between(base, head), external_texts={},
                            evidence=[], gateway=_Gateway(), judge=JUDGE, release="v1", repo_dir="repos/demo",
                            retire_ratio=1.0)
        assert decision.status == "pass", decision.reasons
        verdict = build_verdict(
            repository=REPO, pr=pr or number, head_sha=head_sha or self.prs[number]["head"]["sha"],
            context_base_sha=kw.pop("context_base_sha", self.main),
            manifest=manifest_from_files({k: v for k, v in base.items() if k in touched},
                                         {k: v for k, v in head.items() if k in touched}),
            blocks=[] if source != "auto" else signable_blocks(decision),
            consistency=[] if source != "auto" else [
                {"owner_dir": c["owner_dir"], "verdict": c["verdict"], "pages": c["pages"]}
                for c in decision.consistency],
            release="v1", upstream={}, facts=[], models={}, source=source,
            issued_at=time.time() - 5 if issued_at is None else issued_at, **kw)
        if mutate:
            mutate(verdict)
        envelope = sign("kb-gate-verdict", verdict, key)
        self.comments.setdefault(number, []).append(
            {"body": f"{gv.VERDICT_MARKER}\n```json\n{json.dumps(envelope, ensure_ascii=False)}\n```\n"})
        return verdict

    # the fake GitHub API -----------------------------------------------------
    def get(self, path: str):
        path = path.split("?", 1)[0]
        parts = path.strip("/").split("/")
        if parts[-2:] == ["comments"] or parts[-1] == "comments":
            return self.comments.get(int(parts[-2]), [])
        if len(parts) == 7 and parts[5] == "reviews":
            return self.reviews[(int(parts[4]), int(parts[6]))]
        if parts[-1] == "pulls":
            return [pr for pr in self.prs.values() if pr["state"] == "open"]
        if parts[-2] == "pulls":
            return self.prs[int(parts[-1])]
        raise AssertionError(path)

    def get_all(self, path: str, *, pages: int = 10):
        return self.get(path)

    def post(self, path: str, body: dict):
        self.posts.append((path, body))
        return {}

    def context(self) -> gv.Context:
        payload = {"issued_at": time.time() - self.holds_age, "sequence": 1, **self.holds}
        return gv.Context(git=gv.Git(self.ws), github=self, repository=REPO, public_key=KEY.public_key(),
                          holds_loader=lambda: sign("kb-holds", payload, KEY),
                          codeowners=gv.parse_codeowners(self.codeowners), now=time.time())


def _add_rule() -> dict[str, str]:
    base = _tree()
    return apply_operations(base, [Op("add", PAGE, "DEMO-2a", _rule("DEMO-2a", "PR #11"))],
                            release="v1", today="2026-09-28").files


def _pr(world: World, ctx=None, number: int = 1) -> list[str]:
    _head, problems = gv.verify_pr(ctx or world.context(), number)
    return problems


@pytest.fixture
def world(tmp_path):
    return World(tmp_path)


# -- PR stage ----------------------------------------------------------------------

def test_a_pr_that_does_not_touch_knowledge_passes_without_a_verdict(world):
    world.branch(1, {}, code={"src/app.py": "x = 2\n"})
    assert _pr(world) == []


def test_a_signed_auto_verdict_for_this_head_passes(world):
    files = _add_rule()
    world.branch(1, files)
    world.verdict(1, files)
    assert _pr(world) == []


def test_a_knowledge_pr_without_a_valid_verdict_fails(world):
    files = _add_rule()
    world.branch(1, files)
    assert any("no valid signed verdict" in p for p in _pr(world))
    # replayed from another PR, bound to another head, signed by another key, expired
    world.verdict(1, files, pr=2)
    world.verdict(1, files, head_sha="f" * 40)
    world.verdict(1, files, key=Ed25519PrivateKey.generate())
    world.verdict(1, files, issued_at=time.time() - 73 * 3600)
    problems = _pr(world)
    assert len(problems) == 1 and "no valid signed verdict" in problems[0]
    assert "another repository or pull request" in problems[0]


def test_a_verdict_whose_manifest_omits_a_change_fails(world):
    files = _add_rule()
    world.branch(1, files)
    world.verdict(1, files, mutate=lambda v: v.update(manifest=[]))
    assert "the signed patch manifest does not match the change as applied" in _pr(world)


def test_a_block_table_that_does_not_cover_the_change_fails(world):
    files = _add_rule()
    world.branch(1, files)
    world.verdict(1, files, mutate=lambda v: v.update(blocks=v["blocks"][1:]))
    assert "the signed block table does not cover exactly the changed blocks" in _pr(world)


def test_mixed_code_and_knowledge_and_executable_files_fail_even_with_a_verdict(world):
    files = _add_rule()
    world.branch(1, files, code={"src/app.py": "x = 3\n"})
    world.verdict(1, files)
    problems = _pr(world)
    assert "the signed patch manifest does not match the change as applied" in problems
    assert any(p.startswith("L1 path_not_whitelisted src/app.py") for p in problems)

    world.branch(2, {})
    _git(world.remote, "checkout", "-q", "pr-2")
    page = world.remote / "knowledge" / PAGE
    page.write_text(page.read_text() + "\n")
    page.chmod(0o755)
    head = _commit(world.remote, "exec bit")
    _git(world.remote, "update-ref", "refs/pull/2/head", head)
    _git(world.remote, "checkout", "-q", "main")
    world.prs[2]["head"]["sha"] = head
    problems = _pr(world, number=2)
    assert any(p.startswith("L1 ") and "100755" in p for p in problems), problems


def test_holds_labels_and_a_stale_or_missing_hold_list_fail_closed(world):
    files = _add_rule()
    world.branch(1, files)
    world.verdict(1, files)
    assert _pr(world) == []
    world.prs[1]["labels"] = [{"name": "kb:hold"}]
    assert "PR #1 carries kb:hold" in _pr(world)
    world.prs[1]["labels"] = []
    for holds, needle in (({"global": True}, "global pause"), ({"prs": [1]}, "hold list"),
                          ({"repos": ["demo"]}, "repository demo is paused")):
        world.holds = {"global": False, "repos": [], "prs": [], **holds}
        assert any(needle in p for p in _pr(world)), holds
    world.holds = {"global": False, "repos": [], "prs": []}
    world.holds_age = 11 * 60
    assert any("stale" in p for p in _pr(world))
    world.holds_age = 0
    ctx = world.context()

    def unreachable():
        raise gv.GateError("hold list unreachable: timeout")
    ctx.holds_loader = unreachable
    assert any("unreachable" in p for p in _pr(world, ctx))


def test_a_context_change_since_judging_invalidates_the_verdict(world):
    files = _add_rule()
    world.branch(1, files)
    world.verdict(1, files)
    world.advance_main({}, code={"src/app.py": "x = 9\n"})         # unrelated: still fine
    assert _pr(world) == []
    world.advance_main({"repos/demo/core/_index.md": "# core\n\n- [rules](rules.md)\n\nmore\n"})
    problems = _pr(world)
    assert any("context changed since the verdict was judged: repos/demo/core/_index.md" in p for p in problems)


def test_the_status_is_posted_on_the_verified_head(world):
    files = _add_rule()
    head = world.branch(1, files)
    world.verdict(1, files)
    root = world.ws
    (root / ".github").mkdir()
    (root / ".github" / "kb-gate.pub").write_text(public_key_text(KEY.public_key()) + "\n")
    original = gv.fetch_holds
    payload = {"issued_at": time.time(), "sequence": 1, "global": False, "repos": [], "prs": []}
    gv.fetch_holds = lambda url: sign("kb-holds", payload, KEY)
    try:
        assert gv.main(["pr", "--repository", REPO, "--pr", "1", "--root", str(root), "--post-status"],
                       github=world) == 0
    finally:
        gv.fetch_holds = original
    assert world.posts == [(f"/repos/{REPO}/statuses/{head}",
                            {"state": "success", "context": "kb-gate", "description": "knowledge verdict verified"})]


# -- human-approved ------------------------------------------------------------------

def test_a_human_approved_verdict_needs_a_live_maintainer_approval_on_this_head(world):
    files = _add_rule()
    head = world.branch(1, files)
    world.verdict(1, files, source="human-approved", review_ids=(7,), reviewers=("alice",))
    world.prs[1]["labels"] = [{"name": "kb:human-approved"}]
    world.reviews[(1, 7)] = {"state": "APPROVED", "commit_id": head, "user": {"login": "alice"}}
    assert _pr(world) == []
    world.reviews[(1, 7)]["state"] = "DISMISSED"
    assert "review 7 is no longer APPROVED" in _pr(world)
    world.reviews[(1, 7)]["state"] = "APPROVED"
    world.prs[1]["labels"] = []
    assert "kb:human-approved was removed" in _pr(world)
    world.prs[1]["labels"] = [{"name": "kb:human-approved"}]
    world.codeowners = "/.github/ @bob\n"
    assert any("knowledge maintainer" in p for p in _pr(world))


def test_a_human_approval_admits_paths_outside_the_auto_merge_whitelist(world):
    tool = {"tools/check.py": "print('ok')\n"}
    head = world.branch(1, tool)
    manifest = manifest_from_files({}, tool)
    world.verdict(1, {}, source="human-approved", review_ids=(7,), reviewers=("alice",),
                  mutate=lambda v: v.update(manifest=manifest))
    world.reviews[(1, 7)] = {"state": "APPROVED", "commit_id": head, "user": {"login": "alice"}}
    world.prs[1]["labels"] = [{"name": "kb:human-approved"}]
    assert _pr(world) == []
    world.verdict(1, {}, mutate=lambda v: v.update(manifest=manifest, source="auto"))
    world.comments[1] = world.comments[1][1:]            # only the auto verdict remains
    assert any(p.startswith("L1 path_not_whitelisted knowledge/tools/check.py") for p in _pr(world))


def test_a_human_approved_edit_of_a_non_governed_markdown_file_passes(world):
    world.advance_main({"skills/demo/SKILL.md": "# demo skill\n"})
    edit = {"skills/demo/SKILL.md": "# demo skill\n\nmore\n"}
    head = world.branch(1, edit)
    manifest = manifest_from_files({"skills/demo/SKILL.md": "# demo skill\n"}, edit)
    world.verdict(1, {}, source="human-approved", review_ids=(7,), reviewers=("alice",),
                  mutate=lambda v: v.update(manifest=manifest))
    world.reviews[(1, 7)] = {"state": "APPROVED", "commit_id": head, "user": {"login": "alice"}}
    world.prs[1]["labels"] = [{"name": "kb:human-approved"}]
    assert _pr(world) == []


def test_a_hold_on_general_applies_to_general_pages(world):
    world.branch(1, {"general/guide.md": "# guide\n"})
    world.holds["repos"] = ["general"]
    assert "repository general is paused by the knowledge service" in _pr(world)


# -- merge group -------------------------------------------------------------------

def test_the_merge_group_verifies_every_knowledge_segment(world):
    files = _add_rule()
    world.branch(1, files)
    world.branch(2, {}, code={"src/app.py": "x = 5\n"})
    world.verdict(1, files)
    # knowledge first, code last: the knowledge segment is still verified
    assert gv.verify_merge_group(world.context(), world.merge_group([1, 2])) == []
    assert gv.verify_merge_group(world.context(), world.merge_group([2, 1])) == []
    world.comments[1] = []
    problems = gv.verify_merge_group(world.context(), world.merge_group([1, 2]))
    assert problems and all(p.startswith("PR #1: ") for p in problems)


def test_the_merge_group_rechecks_draft_and_hold_state(world):
    files = _add_rule()
    world.branch(1, files)
    world.verdict(1, files)
    group = world.merge_group([1])
    world.prs[1]["draft"] = True
    assert "PR #1: PR #1 is a draft (paused)" in gv.verify_merge_group(world.context(), group)
    world.prs[1]["draft"] = False
    world.holds["prs"] = [1]
    assert any("hold list" in p for p in gv.verify_merge_group(world.context(), group))


def test_a_merge_group_segment_that_is_not_a_merge_commit_is_rejected(world):
    files = _add_rule()
    head = world.branch(1, files)
    world.verdict(1, files)
    _git(world.ws, "fetch", "-q", "origin", f"+{head}:refs/queue/head")   # fast-forward "group"
    problems = gv.verify_merge_group(world.context(), head)
    assert problems == [f"segment {head[:12]} is not a two-parent merge commit; the group cannot be attributed"]


def test_a_later_queued_pr_in_the_same_owner_directory_invalidates_the_earlier_verdict(world):
    files = _add_rule()
    world.branch(1, files)
    world.verdict(1, files)
    other = {"repos/demo/core/_index.md": "# core\n\n- [rules](rules.md)\n\nnote\n"}
    world.branch(3, other)
    world.verdict(3, other)   # judged on main; PR 1 lands in front of it in the group
    problems = gv.verify_merge_group(world.context(), world.merge_group([1, 3]))
    assert any(p.startswith("PR #3: ") and "context changed" in p for p in problems)


def test_a_rule_retired_in_front_of_a_pr_that_cites_it_fails_in_the_landing_tree(world):
    base = _tree()
    retire = apply_operations(base, [Op("retire", PAGE, "DEMO-1a", reason="upstream-removed",
                                        evidence="PR #13")], release="v1", today="2026-09-28").files
    text = _rule("DEMO-3a", "PR #12").replace("队列满时", "与 DEMO-1a 一致，队列满时")
    cite = apply_operations(base, [Op("add", "repos/demo/api/rules.md", "DEMO-3a", text,
                                      page_title="Demo api rules")], release="v1", today="2026-09-28").files
    world.branch(1, retire)
    world.branch(3, cite)
    world.verdict(1, retire)
    world.verdict(3, cite)
    assert _pr(world, number=1) == [] and _pr(world, number=3) == []   # each is fine alone
    for order in ([1, 3], [3, 1]):
        problems = gv.verify_merge_group(world.context(), world.merge_group(order))
        assert any(p.startswith("PR #1: L1 dangling_reference repos/demo/api/rules.md DEMO-1a")
                   for p in problems), (order, problems)


# -- the pinned bundle -------------------------------------------------------------

def test_the_bundle_is_fresh():
    proc = subprocess.run([sys.executable, str(ROOT / "tools" / "build_kb_gate_bundle.py"), "--check"],
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout


def test_the_bundle_imports_only_the_stdlib_its_siblings_and_pinned_deps():
    bundle = ROOT / ".github" / "kb-gate"
    siblings = {p.stem for p in bundle.glob("*.py")}
    allowed = siblings | {"yaml", "cryptography"} | set(sys.stdlib_module_names)
    for path in bundle.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module or ""]
            for name in names:
                assert name.split(".")[0] in allowed, f"{path.name} imports {name}"
    lock = (bundle / "requirements.lock").read_text()
    for pin in ("cryptography==", "cffi==", "pycparser==", "PyYAML=="):
        assert pin in lock
    assert "--hash=sha256:" in lock


def test_the_bundled_verifier_runs_standalone(world, tmp_path):
    """Run .github/kb-gate/kb_gate.py as the workflow does, outside the source
    tree: a code-only group passes, a knowledge group without the key fails."""
    world.branch(2, {}, code={"src/app.py": "x = 5\n"})
    group = world.merge_group([2])
    script = ROOT / ".github" / "kb-gate" / "kb_gate.py"
    env = {"PATH": os.environ["PATH"], "HOME": str(tmp_path), "GITHUB_TOKEN": "none"}
    run = lambda head: subprocess.run(  # noqa: E731
        [sys.executable, "-E", "-s", str(script), "merge-group", "--repository", REPO,
         "--head-sha", head, "--root", str(world.ws)], cwd=tmp_path, env=env, capture_output=True, text=True)
    proc = run(group)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    world.branch(1, _add_rule())
    proc = run(world.merge_group([1]))
    assert proc.returncode == 1 and "kb-gate.pub is not committed" in proc.stdout
