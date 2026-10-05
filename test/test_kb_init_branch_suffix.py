"""Repeated init publications preserve old branches and frozen batch names."""

import json
import subprocess

import pytest

from infermatrix_copilot.kb_service.init_stages import BRANCH_SUFFIX_ENV, run_stage
from infermatrix_copilot.kb_service.init_support import InitError, load_prepared

from test_kb_init_existing_modules import ENV, _merged_baseline
from test_kb_init_modules import CardGateway, _modules_lifecycle
from test_kb_init_skeleton import FakeGateway, FakeGh, _lifecycle, _runtime, world  # noqa: F401


class BranchGh:
    """Real commit plumbing, scripted independent remote refs and PRs."""

    def __init__(self, heads):
        self.heads = dict(heads)
        self.prs = {}
        self.pushed_branches = []

    def __call__(self, cmd, **kwargs):
        if cmd[:3] == ["gh", "pr", "list"]:
            branch = cmd[cmd.index("--head") + 1]
            return subprocess.CompletedProcess(cmd, 0, json.dumps(self.prs.get(branch, [])).encode(), b"")
        if cmd[:3] == ["gh", "pr", "create"]:
            branch = cmd[cmd.index("--head") + 1]
            self.prs[branch] = [{"number": 42, "headRefOid": self.heads["refs/heads/" + branch]}]
            return subprocess.CompletedProcess(cmd, 0, b"https://example/pull/42", b"")
        if "ls-remote" in cmd:
            ref = cmd[-1]
            text = self.heads.get(ref, "")
            return subprocess.CompletedProcess(cmd, 0, (f"{text}\t{ref}\n" if text else "").encode(), b"")
        if "push" in cmd:
            value = next(arg for arg in cmd if ":refs/heads/" in arg and not arg.startswith("--"))
            commit, ref = value.split(":", 1)
            assert ref not in self.heads and f"--force-with-lease={ref}:" in cmd
            self.heads[ref] = commit
            self.pushed_branches.append(ref)
            return subprocess.CompletedProcess(cmd, 0, b"", b"")
        return subprocess.run(cmd, **kwargs)


def test_second_modules_batch_uses_a_distinct_branch_and_keeps_old_ref(world):
    pin, _, _, _ = _merged_baseline(world)
    old_ref = "refs/heads/kb/init-toy-modules"
    old_commit = world["kb_sha"]
    gh = BranchGh({old_ref: old_commit})
    environment = {**ENV, BRANCH_SUFFIX_ENV: "new-init-20261005"}
    record = run_stage(_runtime(world, CardGateway(), state_dir=world["tmp"] / "new-batch",
                                environ=environment, gh_run=gh),
                       _modules_lifecycle(feature_discovery_required=True), "modules",
                       dry_run=False, pin=pin, from_existing=True)
    assert record.status == "published", record.problems
    assert record.pr["branch"] == "kb/init-toy-modules-new-init-20261005"
    assert gh.heads[old_ref] == old_commit
    assert gh.pushed_branches == ["refs/heads/" + record.pr["branch"]]
    assert load_prepared(record.pr["prepared"])["branch"] == record.pr["branch"]


@pytest.mark.parametrize("suffix", ["Upper", "bad/name", "bad..name", "-start", "end-", "a" * 41,
                                    "bad name", "$(command)", "é", True])
def test_invalid_branch_suffix_is_refused_before_models_or_publication(world, suffix):
    gateway, gh = FakeGateway(), FakeGh()
    with pytest.raises(InitError, match=BRANCH_SUFFIX_ENV):
        run_stage(_runtime(world, gateway, environ={**ENV, BRANCH_SUFFIX_ENV: suffix}, gh_run=gh),
                  _lifecycle(), "skeleton", dry_run=False)
    assert not gateway.calls and not gh.pushed


def test_unset_and_empty_suffix_preserve_default_checkpoint_identity(world):
    gateway = FakeGateway()
    rt = _runtime(world, gateway)
    original = run_stage(rt, _lifecycle(), "skeleton", dry_run=True)
    calls = len(gateway.calls)
    rt.environ[BRANCH_SUFFIX_ENV] = ""
    cached = run_stage(rt, _lifecycle(), "skeleton", dry_run=True)
    assert cached.inputs_digest == original.inputs_digest
    assert len(gateway.calls) == calls


def test_prepared_publication_rejects_changed_suffix_and_resumes_original_without_models(world):
    environment = {**ENV, BRANCH_SUFFIX_ENV: "batch-one"}
    gateway, gh = FakeGateway(), FakeGh(fail_create=1)
    rt = _runtime(world, gateway, environ=environment, gh_run=gh)
    pending = run_stage(rt, _lifecycle(), "skeleton", dry_run=False)
    assert pending.status == "blocked" and pending.pr.get("prepared")
    prepared = load_prepared(pending.pr["prepared"])
    assert prepared["branch"] == "kb/init-toy-skeleton-batch-one"
    original_calls = len(gateway.calls)
    original_pushes = list(gh.pushed)
    rt.environ[BRANCH_SUFFIX_ENV] = "batch-two"
    rejected = run_stage(rt, _lifecycle(), "skeleton", dry_run=False)
    assert rejected.status == "blocked" and any("different branch suffix" in p for p in rejected.problems)
    assert len(gateway.calls) == original_calls and gh.pushed == original_pushes
    assert load_prepared(pending.pr["prepared"]) == prepared
    rt.environ[BRANCH_SUFFIX_ENV] = "batch-one"
    published = run_stage(rt, _lifecycle(), "skeleton", dry_run=False)
    assert published.status == "published", published.problems
    assert published.pr["branch"] == prepared["branch"]
    assert len(gateway.calls) == original_calls and gh.pushed == original_pushes
