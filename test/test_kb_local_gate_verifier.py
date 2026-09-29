"""The knowledge verifier as the publisher's local gate runs it: adversarial cases, offline."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from infermatrix_copilot.kb_service.gate import changes_between, run_gate, signable_blocks
from infermatrix_copilot.kb_service.models import ModelReply, ModelRole
from infermatrix_copilot.kb_service import local_gate
from infermatrix_copilot.knowledge_service.gate_verifier import Git
from infermatrix_copilot.knowledge_service.ops import KnowledgeOperation as Op, apply_operations
from infermatrix_copilot.knowledge_service.signing import sign
from infermatrix_copilot.knowledge_service.verdict import VerdictError
from infermatrix_copilot.knowledge_service.verdict import build_verdict, manifest_from_files

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
    """A remote with main and PR refs, and the publisher's clone of it."""

    def __init__(self, tmp_path: Path):
        self.remote = tmp_path / "remote"
        self.remote.mkdir()
        _git(self.remote, "init", "-q", "-b", "main")
        _write(self.remote, _tree())
        (self.remote / "src").mkdir()
        (self.remote / "src" / "app.py").write_text("x = 1\n")
        self.main = _commit(self.remote, "base")
        self.ws = tmp_path / "ws"
        _git(tmp_path, "clone", "-q", "--bare", str(self.remote), str(self.ws))
        self.heads: dict[int, str] = {}
        self.envelopes: dict[int, dict] = {}

    def branch(self, number: int, files: dict[str, str | None], *, code: dict[str, str] | None = None) -> str:
        _git(self.remote, "checkout", "-q", "-B", f"pr-{number}", self.main)
        _write(self.remote, files)
        if code:
            _write(self.remote, code, prefix="")
        head = _commit(self.remote, f"pr {number}")
        _git(self.remote, "update-ref", f"refs/pull/{number}/head", head)
        _git(self.remote, "checkout", "-q", "main")
        self.heads[number] = head
        return head

    def advance_main(self, files: dict[str, str | None], *, code: dict[str, str] | None = None) -> str:
        _git(self.remote, "checkout", "-q", "main")
        _write(self.remote, files)
        if code:
            _write(self.remote, code, prefix="")
        self.main = _commit(self.remote, "main moves")
        return self.main

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
            repository=REPO, pr=pr or number, head_sha=head_sha or self.heads[number],
            context_base_sha=kw.pop("context_base_sha", self.main),
            manifest=manifest_from_files({k: v for k, v in base.items() if k in touched},
                                         {k: v for k, v in head.items() if k in touched}),
            blocks=signable_blocks(decision),
            consistency=[{"owner_dir": c["owner_dir"], "verdict": c["verdict"], "pages": c["pages"]}
                         for c in decision.consistency],
            release="v1", upstream={}, facts=[], models={},
            issued_at=time.time() - 5 if issued_at is None else issued_at, **kw)
        verdict["source"] = source  # anything else than auto is forged
        if mutate:
            mutate(verdict)
        self.envelopes[number] = sign("kb-gate-verdict", verdict, key)
        return verdict


def _gate(world: World, number: int = 1) -> list[str]:
    """The publisher's local gate on merge-tree(main, head) with the handed-over verdict."""
    _git(world.ws, "fetch", "-q", "origin", "+refs/heads/main:refs/heads/main",
         f"+refs/pull/{number}/head:refs/kb/pr-{number}")
    head = world.heads[number]
    verdict = local_gate.check_verdict(world.envelopes[number], KEY.public_key(), repository=REPO, pr=number,
                                       head_sha=head, now=time.time())
    pr = {"number": number, "state": "open", "head": {"sha": head}, "labels": []}
    return local_gate.gate(world.ws, repository=REPO, repo="demo", pr=pr, head_sha=head,
                           main_sha=Git(world.ws).rev("refs/heads/main"), verdict=verdict,
                           public_key=KEY.public_key(), now=time.time())


def _add_rule() -> dict[str, str]:
    base = _tree()
    return apply_operations(base, [Op("add", PAGE, "DEMO-2a", _rule("DEMO-2a", "PR #11"))],
                            release="v1", today="2026-09-28").files


@pytest.fixture
def world(tmp_path):
    return World(tmp_path)


def test_a_signed_verdict_for_this_head_passes(world):
    files = _add_rule()
    world.branch(1, files)
    world.verdict(1, files)
    assert _gate(world) == []


@pytest.mark.parametrize("variant", ["other_pr", "other_head", "other_key", "expired", "human"])
def test_a_verdict_for_something_else_is_refused(world, variant):
    files = _add_rule()
    world.branch(1, files)
    kw = {"other_pr": {"pr": 2}, "other_head": {"head_sha": "f" * 40},
          "other_key": {"key": Ed25519PrivateKey.generate()},
          "expired": {"issued_at": time.time() - 73 * 3600}, "human": {"source": "human-approved"}}[variant]
    world.verdict(1, files, **kw)
    with pytest.raises(VerdictError):
        _gate(world)


def test_a_verdict_whose_manifest_omits_a_change_fails(world):
    files = _add_rule()
    world.branch(1, files)
    world.verdict(1, files, mutate=lambda v: v.update(manifest=[]))
    assert "the signed patch manifest does not match the change as applied" in _gate(world)


def test_a_block_table_that_does_not_cover_the_change_fails(world):
    files = _add_rule()
    world.branch(1, files)
    world.verdict(1, files, mutate=lambda v: v.update(blocks=v["blocks"][1:]))
    assert "the signed block table does not cover exactly the changed blocks" in _gate(world)


def test_mixed_code_and_knowledge_and_executable_files_fail_even_with_a_verdict(world):
    files = _add_rule()
    world.branch(1, files, code={"src/app.py": "x = 3\n"})
    world.verdict(1, files)
    problems = _gate(world)
    assert "src/app.py: outside knowledge/ (split the PR)" in problems
    assert "the signed patch manifest does not match the change as applied" in problems

    world.branch(2, {})
    _git(world.remote, "checkout", "-q", "pr-2")
    page = world.remote / "knowledge" / PAGE
    page.write_text(page.read_text() + "\n")
    page.chmod(0o755)
    head = _commit(world.remote, "exec bit")
    _git(world.remote, "update-ref", "refs/pull/2/head", head)
    _git(world.remote, "checkout", "-q", "main")
    world.heads[2] = head
    world.verdict(2, {}, mutate=lambda v: v.update(manifest=[]))
    assert any(p.startswith("L1 ") and "100755" in p for p in _gate(world, 2))


def test_a_change_to_another_repository_than_the_items_is_refused(world):
    files = {"repos/other/x.md": "# x\n"}
    world.branch(1, files)
    world.verdict(1, {}, mutate=lambda v: v.update(manifest=[]))
    assert any("belongs to other, not to demo" in p for p in _gate(world))


def test_a_context_change_since_judging_invalidates_the_verdict(world):
    files = _add_rule()
    world.branch(1, files)
    world.verdict(1, files)
    world.advance_main({}, code={"src/app.py": "x = 9\n"})         # unrelated: still fine
    assert _gate(world) == []
    world.advance_main({"repos/demo/core/_index.md": "# core\n\n- [rules](rules.md)\n\nmore\n"})
    problems = _gate(world)
    assert any("context changed since the verdict was judged: repos/demo/core/_index.md" in p for p in problems)


def test_a_rule_retired_while_main_cites_it_fails_in_the_landing_tree(world):
    base = _tree()
    retire = apply_operations(base, [Op("retire", PAGE, "DEMO-1a", reason="upstream-removed",
                                        evidence="PR #13")], release="v1", today="2026-09-28").files
    text = _rule("DEMO-3a", "PR #12").replace("队列满时", "与 DEMO-1a 一致，队列满时")
    cite = apply_operations(base, [Op("add", "repos/demo/api/rules.md", "DEMO-3a", text,
                                      page_title="Demo api rules")], release="v1", today="2026-09-28").files
    world.branch(1, retire)
    world.verdict(1, retire)
    assert _gate(world) == []                                      # fine on its own
    world.advance_main(cite)                                       # main now cites DEMO-1a
    world.verdict(1, retire, context_base_sha=world.main)
    assert any(p.startswith("L1 dangling_reference repos/demo/api/rules.md DEMO-1a") for p in _gate(world))
