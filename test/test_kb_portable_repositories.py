"""Real committed-tree and optional-forge tests; no model/network fixtures."""

import json
import subprocess
from pathlib import Path

import pytest

from infermatrix_copilot.kb_service.git_source import GitSource, GitHubForge, GitLabForge, forge_provider, public_locator
from infermatrix_copilot.kb_service.repo_spec import RepoRegistry, RepoSpec, RepoSpecError, acceptance_receipt, propose_repository, repository_inventory, canonical_json
from infermatrix_copilot.kb_service.sources import SourceError
from infermatrix_copilot.kb_service.init_support import UpstreamPin


def _git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=False)
    assert result.returncode == 0, result.stderr.decode()
    return result.stdout.decode().strip()


def _repository(tmp_path, object_format="sha1"):
    root = tmp_path / "source"
    root.mkdir()
    _git(root, "init", "-q", "--initial-branch=main", f"--object-format={object_format}")
    _git(root, "config", "user.email", "fixture@example.invalid")
    _git(root, "config", "user.name", "Fixture")
    files = {"src/library.py": "def public(): return 1\n", "ui/index.ts": "export const api=1;\n",
             "knowledge/runtime.py": "def supported_package(): return 1\n", "README.md": "Library usage\n",
             "sdk/tests/deep/test_api.py": "assert True\n", "sdk/src/api.go": "package api\n",
             "lib/custom.langx": "public capability x\n", "src/icon.png": b"\x89PNG\xff\0",
             "vendor/copied.py": "foreign\n", "sdk/node_modules/pkg/index.js": "foreign\n",
             ".infermatrix/knowledge/repos/example/generated.md": "own output\n"}
    for path, body in files.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body.encode() if isinstance(body, str) else body)
    for n in range(70):
        target = root / f"lib/part{n:03d}.py"
        target.write_text(f"def feature{n}(): return {n}\n")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "Initial implementation")
    return root


@pytest.mark.parametrize("object_format,width", [("sha1", 40), ("sha256", 64)])
def test_any_committed_git_tree_no_origin_dirty_files_and_mirror(tmp_path, object_format, width):
    root = _repository(tmp_path, object_format)
    source = GitSource(root)
    pin = source.resolve()
    assert len(pin) == width and source.object_format == object_format
    (root / "src/library.py").write_text("dirty replacement")
    assert source.read(pin, "src/library.py") == b"def public(): return 1\n"
    assert source.origin() == ""
    mirror = GitSource.acquire(root, tmp_path / "mirror.git")
    assert mirror.resolve() == pin and mirror.git_dir == tmp_path / "mirror.git"
    exported = mirror.export(pin, tmp_path / "export")
    assert (exported / "src/library.py").read_bytes() == source.read(pin, "src/library.py")
    assert not (exported / ".git").exists()
    with pytest.raises(SourceError):
        source.resolve("--help")
    with pytest.raises(SourceError):
        source.read(pin, "../outside")


def test_proposal_inventory_is_full_multilingual_nested_and_unknown_not_self_ingested(tmp_path):
    source = GitSource(_repository(tmp_path))
    proposal = propose_repository(source, repo_id="library")
    spec = RepoSpec.from_dict(proposal["spec"])
    inventory = proposal["inventory"]
    assert proposal["accepted"] is False
    assert "lib/part069.py" in inventory["production"]
    assert "knowledge/runtime.py" in inventory["production"]
    assert "sdk/tests/deep/test_api.py" in inventory["tests"]
    assert "README.md" in inventory["docs"]
    assert "src/icon.png" in inventory["assets"] and "src/icon.png" not in inventory["production"]
    assert "lib/custom.langx" in inventory["unknown_language_paths"]
    assert set(spec.languages) == {"python", "typescript", "go", "unknown"}
    assert len(inventory["excluded"]) == 3
    restricted = RepoSpec.from_dict({**spec.to_dict(), "source_roots": ["src"]})
    outside = repository_inventory(source, restricted)
    assert "sdk/src/api.go" in outside["scope_expansion_proposals"]
    assert "sdk/src/api.go" not in outside["production"]
    assert "README.md" in outside["docs"] and "sdk/tests/deep/test_api.py" in outside["tests"]
    assert "README.md" not in outside["outside_scope"]


@pytest.mark.parametrize("object_format", ["sha1", "sha256"])
def test_export_materializes_exact_blobs_despite_archive_attributes(tmp_path, object_format):
    source = GitSource(_repository(tmp_path, object_format))
    (source.path / ".gitattributes").write_text("src/library.py export-ignore\nversion.txt export-subst\n")
    (source.path / "version.txt").write_bytes(b"$Format:%H$\n\0binary\n")
    _git(source.path, "add", ".")
    _git(source.path, "commit", "-qm", "Archive attributes")
    pin = source.head()
    exported = source.export(pin, tmp_path / "export")
    actual = {path.relative_to(exported).as_posix() for path in exported.rglob("*") if path.is_file()}
    assert actual == set(source.files(pin))
    assert (exported / "src/library.py").read_bytes() == source.read(pin, "src/library.py")
    assert (exported / "version.txt").read_bytes() == b"$Format:%H$\n\0binary\n"
    bare = GitSource.acquire(source.path, tmp_path / "bare.git")
    observer = UpstreamPin(bare.path, "repo://fixture", remote=str(source.path))
    actual = observer.export(observer.resolve(pin), tmp_path / "observer-export")
    assert (actual / "src/library.py").read_bytes() == source.read(pin, "src/library.py")
    assert (actual / "version.txt").read_bytes() == source.read(pin, "version.txt")
    assert {p.relative_to(actual).as_posix() for p in actual.rglob("*") if p.is_file()} == set(source.files(pin))


def test_marked_canonical_knowledge_is_reviewed_exclusion_not_package_name(tmp_path):
    source = GitSource(_repository(tmp_path))
    previous = RepoSpec.from_dict(propose_repository(source, repo_id="library")["spec"])
    for path, text in {"shared-kb/AGENTS.md": "Canonical rules\n", "shared-kb/_format.yaml": "format_version: 2\n",
                       "shared-kb/repos/_index.md": "Repository index\n", "shared-kb/repos/library/new.md": "Generated knowledge\n"}.items():
        target = source.path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    _git(source.path, "add", ".")
    _git(source.path, "commit", "-qm", "Committed canonical KB")
    proposal = propose_repository(source, repo_id="library")
    assert "shared-kb/**" in proposal["spec"]["exclude"]
    assert proposal["inventory"]["generated_knowledge_roots"] == ["shared-kb"]
    assert "shared-kb/repos/library/new.md" in proposal["inventory"]["excluded"]
    assert "knowledge/runtime.py" in proposal["inventory"]["production"]
    # Existing accepted scope is reported unchanged until its new exclusion
    # proposal is reviewed; recognizing a marker must not lower its denominator.
    current = RepoSpec.from_dict({**previous.to_dict(), "source_pin": source.head()})
    inventory = repository_inventory(source, current)
    assert inventory["generated_knowledge_exclusion_proposals"] == ["shared-kb/**"]
    assert "shared-kb/repos/library/new.md" in inventory["docs"]


def test_generated_mirror_root_requires_actual_manifest_and_committed_byte_binding(tmp_path):
    from infermatrix_copilot.knowledge_view import build_manifest
    import hashlib
    source = GitSource(_repository(tmp_path))
    root = source.path / "mirror-copy"
    for path, body in {"knowledge/AGENTS.md": "Shared rules\n", "knowledge/_format.yaml": "format_version: 2\n",
                       "knowledge/repos/_index.md": "Repositories\n"}.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body)
    raw = canonical_json(build_manifest(root / "knowledge", "copied-source"))
    (root / "MANIFEST.json").write_bytes(raw)
    (root / "MIRROR.json").write_bytes(canonical_json({"readonly": True, "manifest_sha256": hashlib.sha256(raw).hexdigest()}))
    _git(source.path, "add", ".")
    _git(source.path, "commit", "-qm", "Bound generated mirror")
    proposal = propose_repository(source, repo_id="library")
    assert proposal["inventory"]["generated_knowledge_roots"] == ["mirror-copy"]
    assert "mirror-copy/**" in proposal["spec"]["exclude"]
    (root / "knowledge/repos/_index.md").write_text("Modified beyond mirror provenance\n")
    _git(source.path, "add", ".")
    _git(source.path, "commit", "-qm", "Unbound mirror bytes")
    proposal = propose_repository(source, repo_id="library")
    assert proposal["inventory"]["generated_knowledge_roots"] == ["mirror-copy/knowledge"]
    assert "mirror-copy/**" not in proposal["spec"]["exclude"]


def test_stable_local_identity_and_sanitized_nested_gitlab_identity(tmp_path):
    source = GitSource(_repository(tmp_path))
    local_id = propose_repository(source)["spec"]["repo_id"]
    clone = GitSource.acquire(source.path, tmp_path / "moved.git")
    assert propose_repository(clone)["spec"]["repo_id"] == local_id
    _git(source.path, "remote", "add", "origin", "https://user:secret@git.example/group/nested/project.git?token=private")
    proposal = propose_repository(source, forge_kind="gitlab")
    assert proposal["spec"]["forge_project"] == "group/nested/project"
    serialized = json.dumps(proposal)
    assert "secret" not in serialized and "private" not in serialized and str(source.path) not in serialized
    assert public_locator("git@git.example:group/nested/project.git") == "ssh://git.example/group/nested/project.git"
    assert public_locator("C:\\work\\repo") == ""


def test_actual_commit_diffs_preserve_renames_as_deleted_and_added_paths(tmp_path):
    source = GitSource(_repository(tmp_path))
    old = source.head()
    assert source.parents(old) == () and source.changed_paths(old, old) == []
    _git(source.path, "mv", "src/library.py", "src/renamed.py")
    (source.path / "new.ts").write_text("export const added=1;\n")
    _git(source.path, "add", ".")
    _git(source.path, "commit", "-qm", "Move and add")
    new = source.head()
    assert source.parents(new) == (old,)
    assert source.changed_paths(old, new) == ["new.ts", "src/library.py", "src/renamed.py"]
    _git(source.path, "remote", "add", "origin", "https://github.com/Owner/Repo.git")
    https_id = propose_repository(source)["spec"]["repo_id"]
    _git(source.path, "remote", "set-url", "origin", "git@github.com:Owner/Repo.git")
    assert propose_repository(source)["spec"]["repo_id"] == https_id


@pytest.mark.parametrize("changes", [{"coverage_target": .84}, {"per_facet_gt": .89},
                                      {"coverage_target": True}, {"source_roots": ["../outside"]},
                                      {"source_locator": "https://user:secret@example/repo.git"},
                                      {"knowledge_slice": "repos/another"}])
def test_every_repo_keeps_global_minimum_gates_and_safe_public_spec(changes):
    with pytest.raises(RepoSpecError):
        RepoSpec.from_dict({"repo_id": "repo", **changes})


def test_registration_exact_scope_and_head_no_public_runtime_paths(tmp_path):
    source = GitSource(_repository(tmp_path))
    spec = RepoSpec.from_dict(propose_repository(source, repo_id="library")["spec"])
    registry = RepoRegistry(tmp_path / "state")
    receipt = acceptance_receipt(spec, source, source.head(), accepted=True)
    registry.register(spec, receipt, source_path=source.path, knowledge_root=tmp_path / "canonical")
    assert registry.resolve("library")["spec"] == spec.to_dict()
    assert registry.get("library")["bindings"]["source_path"] == str(source.path)
    public = canonical_json(registry.public_snapshot())
    assert str(source.path).encode() not in public and b"bindings" not in public
    with pytest.raises(RepoSpecError):
        registry.register(spec, {**receipt, "spec_sha256": "0" * 64}, source_path=source.path, knowledge_root=tmp_path / "canonical")
    with pytest.raises(RepoSpecError):
        acceptance_receipt(spec, source, source.head(), accepted=False)


def test_dependencies_are_public_versioned_links_without_runtime_bindings():
    link = {"repo_id": "sdk", "status": "confirmed", "source_pin": "1" * 40,
            "catalog_hash": "a" * 64, "evidence": [{"path": "src/client.py", "start": 2, "end": 4}]}
    spec = RepoSpec(repo_id="service", dependencies=(link,))
    assert spec.to_dict()["dependencies"] == [link]
    assert RepoSpec(repo_id="service", dependencies=({"repo_id": "sdk", "status": "unknown"},)).dependencies
    for invalid in ({**link, "source_path": "/runtime/private"}, {**link, "token": "runtime-only"},
                    {**link, "source_pin": ""}, {**link, "catalog_hash": ""},
                    {**link, "evidence": [{"path": "/runtime/private"}]},
                    {**link, "evidence": [{"path": "src/a.py", "token": "private"}]}):
        with pytest.raises(RepoSpecError):
            RepoSpec(repo_id="service", dependencies=(invalid,))


def test_optional_forges_share_git_independent_source_and_nested_project_encoding():
    calls = []
    def request(*args):
        calls.append(args)
        return {"number": 1}
    gh = GitHubForge("owner/repo", token="runtime-only", request=request)
    gh.open_review(title="T", body="B", head="topic", base="main")
    gl = GitLabForge("group/nested/repo", host="https://git.example", token="runtime-only", request=request)
    gl.open_review(title="T", body="B", head="topic", base="main")
    gl.review(3)
    assert calls[0][1] == "https://api.github.com/repos/owner/repo/pulls"
    assert calls[1][1] == "https://git.example/api/v4/projects/group%2Fnested%2Frepo/merge_requests"
    assert calls[1][2]["source_branch"] == "topic"
    assert calls[2][1].endswith("/merge_requests/3")
    assert "runtime-only" not in json.dumps(calls)
    with pytest.raises(SourceError):
        forge_provider("none").open_review(title="T", body="B", head="topic", base="main")


@pytest.mark.parametrize("kind", ["github", "gitlab"])
def test_forge_acceptance_checks_exact_merged_head_without_claiming_ci(kind):
    head, merge = "1" * 40, "2" * 40
    row = {"merged": True, "state": "merged", "head": {"sha": head}, "sha": head, "merge_commit_sha": merge}
    provider = forge_provider(kind, "owner/repo", host="https://forge.example", request=lambda *args: row)
    accepted = provider.acceptance(3, head)
    assert accepted["review_head"] == head and accepted["publication_head"] == merge
    assert accepted["ci_verified"] is False
    with pytest.raises(SourceError):
        provider.acceptance(3, "3" * 40)
    row.update(merged=False, state="opened")
    with pytest.raises(SourceError):
        provider.acceptance(3, head)
