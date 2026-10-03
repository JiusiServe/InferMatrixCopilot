"""Provider contract tests use recorded-style payloads and temporary repositories."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
from urllib.parse import parse_qs, urlsplit

import pytest

from infermatrix_copilot.rfc_service.models import ProviderError, RFCError, SourceRef
from infermatrix_copilot.rfc_service import providers
from infermatrix_copilot.rfc_service.providers import AtomGitProvider, GitHubProvider, LocalProvider


class Transport:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, method, url, headers, payload):
        self.calls.append((method, url, dict(headers), deepcopy(payload)))
        if not self.responses:
            raise AssertionError("Unexpected provider request")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        if isinstance(response, tuple):
            return response
        return 200, {}, deepcopy(response)


def issue(number="7", *, body="RFC body", state="open", host="github.com", **extra):
    return {"number": number, "title": "Cache lifecycle RFC", "body": body, "state": state,
            "updated_at": "2026-10-02T08:00:00Z", "html_url": f"https://{host}/org/repo/issues/{number}",
            "user": {"login": "author"}, **extra}


def pr(number="8", **extra):
    value = issue(number, **extra)
    value["html_url"] = value["html_url"].replace("/issues/", "/pull/")
    return value


@pytest.mark.parametrize("raw,expected", [
    (pr(state="open", draft=True), "draft"),
    (pr(state="closed", draft=True), "closed"),
    (pr(state="closed", merged_at="2026-10-02T08:01:00Z"), "merged"),
    (pr(state="closed", merged=True), "merged"),
    (pr(state="open"), "open"),
    (pr(state="mystery"), "unknown"),
])
def test_github_normalizes_authoritative_pr_state(raw, expected):
    transport = Transport(raw)
    provider = GitHubProvider("secret-token", transport=transport)
    result = provider.get_item(SourceRef("github", "org/repo", "pr", "8"))
    assert result["state"] == expected
    assert result["source"]["kind"] == "pr"
    assert result["url"] == "https://github.com/org/repo/pull/8"
    assert urlsplit(transport.calls[0][1]).path == "/repos/org/repo/pulls/8"
    assert transport.calls[0][2]["Authorization"] == "Bearer secret-token"
    assert transport.calls[0][2]["X-GitHub-Api-Version"] == "2022-11-28"
    assert "secret-token" not in transport.calls[0][1]


def test_atomgit_issue_identifier_remains_opaque_case_sensitive():
    raw = issue("IAb9", host="atomgit.com", state="opened")
    transport = Transport(raw)
    result = AtomGitProvider(transport=transport).get_source(SourceRef("atomgit", "org/repo", "issue", "IAb9"))
    assert result["source"]["identifier"] == "IAb9"
    assert result["native_state"] == "opened"
    assert result["state"] == "open"
    assert urlsplit(transport.calls[0][1]).path == "/api/v5/repos/org/repo/issues/IAb9"


def test_atomgit_pr_review_participants_are_not_implementation_owners():
    raw = pr(host="atomgit.com", state="merged", draft=False, head={"sha": "abc"},
             assignees=[{"login": "reviewer"}], approval_reviewers=[{"login": "approver"}], testers=[{"login": "tester"}])
    result = AtomGitProvider(transport=Transport(raw)).get_item(SourceRef("atomgit", "org/repo", "pr", "8"))
    assert result["author"] == "author"
    assert result["owner"] == ""
    assert result["owners"] == []
    assert result["reviewers"] == ["reviewer", "approver"]
    assert result["head_sha"] == "abc"
    assert result["state"] == "merged"


def test_github_assignees_and_requested_reviewers_remain_distinct():
    raw = pr(assignees=[{"login": "implementer"}], requested_reviewers=[{"login": "reviewer"}])
    result = GitHubProvider(transport=Transport(raw)).get_item(SourceRef("github", "org/repo", "pr", "8"))
    assert result["owner"] == "implementer"
    assert result["reviewers"] == ["reviewer"]


def test_atomgit_publish_uses_v5_owner_route_and_header_auth():
    transport = Transport(issue("ICase", host="atomgit.com"))
    provider = AtomGitProvider("atom-secret", api_url="https://api.atomgit.com", transport=transport)
    ref = provider.publish("org/repo", "An RFC", "A proposal", "operation-1")
    method, url, headers, payload = transport.calls[0]
    assert method == "POST"
    assert urlsplit(url).path == "/api/v5/repos/org/issues"
    assert payload == {"repo": "repo", "title": "An RFC", "body": "A proposal\n\n<!-- imrfc-operation:operation-1 -->\n"}
    assert headers["Authorization"] == "Bearer atom-secret"
    assert "atom-secret" not in url
    assert ref.identifier == "ICase"


def test_atomgit_body_update_preserves_required_current_title():
    before = issue("ICase", host="atomgit.com", title="Human changed title")
    after = dict(before, body="New managed body", updated_at="2026-10-02T08:02:00Z")
    transport = Transport(before, before, after, after)
    provider = AtomGitProvider(transport=transport)
    ref = SourceRef("atomgit", "org/repo", "issue", "ICase")
    revision = provider.get_source(ref)["revision"]
    result = provider.update_source(ref, "New managed body", revision)
    call = transport.calls[2]
    assert call[0] == "PATCH"
    assert urlsplit(call[1]).path == "/api/v5/repos/org/issues/ICase"
    assert call[3] == {"repo": "repo", "title": "Human changed title", "body": "New managed body"}
    assert result["revision"] != revision


def test_remote_update_detects_changed_source_and_never_writes():
    before = issue()
    changed = dict(before, body="Human edit", updated_at=before["updated_at"])
    transport = Transport(before, changed)
    provider = GitHubProvider(transport=transport)
    ref = SourceRef("github", "org/repo", "issue", "7")
    revision = provider.get_source(ref)["revision"]
    with pytest.raises(RFCError) as error:
        provider.update_source(ref, "Managed edit", revision)
    assert error.value.status == 409
    assert [call[0] for call in transport.calls] == ["GET", "GET"]


def test_remote_update_detects_readback_conflict():
    before = issue()
    transport = Transport(before, before, dict(before, body="Attempted"), dict(before, body="Concurrent human edit"))
    provider = GitHubProvider(transport=transport)
    ref = SourceRef("github", "org/repo", "issue", "7")
    revision = provider.get_source(ref)["revision"]
    with pytest.raises(RFCError) as error:
        provider.update_source(ref, "Attempted", revision)
    assert error.value.status == 409


def test_publication_recovery_scans_second_page_and_ignores_prs():
    first_page = [issue(str(number)) for number in range(1, 101)]
    marked_pr = pr("107", body="<!-- imrfc-operation:op-1 -->", pull_request={"url": "ignored"})
    transport = Transport(first_page, [marked_pr, issue("108", body="<!-- imrfc-operation:op-1 -->")])
    result = GitHubProvider(transport=transport).find_publication("org/repo", "op-1")
    assert result.identifier == "108"
    assert parse_qs(urlsplit(transport.calls[1][1]).query)["page"] == ["2"]
    assert parse_qs(urlsplit(transport.calls[0][1]).query)["state"] == ["all"]


def test_incomplete_recovery_cannot_claim_absence(monkeypatch):
    monkeypatch.setattr(providers, "MAX_PAGES", 2)
    full = [issue(str(number)) for number in range(1, 101)]
    provider = GitHubProvider(transport=Transport(full, full))
    with pytest.raises(ProviderError) as error:
        provider.find_publication("org/repo", "missing-op")
    assert error.value.uncertain


def test_duplicate_operation_markers_require_reconciliation():
    marker = "<!-- imrfc-operation:op-1 -->"
    provider = GitHubProvider(transport=Transport([issue("1", body=marker), issue("2", body=marker)]))
    with pytest.raises(ProviderError) as error:
        provider.find_publication("org/repo", "op-1")
    assert error.value.uncertain


def test_short_page_with_link_next_is_not_silently_truncated():
    transport = Transport((200, {"Link": '<https://api.github.com/ignored>; rel="next"'}, [issue("1")]), [])
    assert GitHubProvider(transport=transport).find_publication("org/repo", "absent") is None
    assert len(transport.calls) == 2
    assert urlsplit(transport.calls[1][1]).path == "/repos/org/repo/issues"


def test_creation_network_failure_is_uncertain_and_sanitizes_error():
    transport = Transport(RuntimeError("secret-token http://secret@localhost"))
    with pytest.raises(ProviderError) as error:
        GitHubProvider("secret-token", transport=transport).publish("org/repo", "RFC", "body", "op-1")
    assert error.value.uncertain
    assert "secret-token" not in str(error.value)
    assert len(transport.calls) == 1


@pytest.mark.parametrize("ref", [
    SourceRef("github", "org/repo", "issue", "7", "https://127.0.0.1/private"),
    SourceRef("github", "org/repo", "issue", "7", host="metadata.internal"),
    SourceRef("github", "org/../repo", "issue", "7"),
    SourceRef("github", "org/repo", "issue", "7/../../private"),
    SourceRef("github", "org/repo", "issue", "7", "https://user:password@github.com/org/repo/issues/7"),
])
def test_arbitrary_source_hosts_and_paths_never_reach_transport(ref):
    transport = Transport()
    with pytest.raises(RFCError):
        GitHubProvider(transport=transport).get_source(ref)
    assert not transport.calls


def test_discovery_uses_atomgit_issue_and_pr_streams_not_github_search_syntax():
    relevant_issue = issue("IA", host="atomgit.com", body="cache contract")
    irrelevant_issue = issue("IB", host="atomgit.com", body="unrelated", title="Media layout")
    relevant_pr = pr("8", host="atomgit.com", title="Cache fast path", body="cache implementation", state="merged")
    transport = Transport([relevant_issue, irrelevant_issue], [relevant_pr])
    result = AtomGitProvider(transport=transport).discover("org/repo", {"keywords": ["cache"]}, "2026-10-01T00:00:00Z")
    assert [(item["source"]["kind"], item["source"]["identifier"]) for item in result] == [("issue", "IA"), ("pr", "8")]
    assert result[1]["state"] == "merged"
    assert [urlsplit(call[1]).path for call in transport.calls] == ["/api/v5/repos/org/repo/issues", "/api/v5/repos/org/repo/pulls"]
    assert parse_qs(urlsplit(transport.calls[1][1]).query)["since"] == ["2026-10-01T00:00:00Z"]


@pytest.mark.parametrize("native,expected", [
    ({"state": "closed", "pull_request": {"merged_at": "2026-10-02T08:00:00Z"}}, "merged"),
    ({"state": "closed", "pull_request": {}}, "closed"),
    ({"state": "open", "draft": True, "pull_request": {}}, "draft"),
])
def test_github_discovery_preserves_only_native_summary_state_without_detail_get(native, expected):
    summary = pr("8", body="cache", **native)
    transport = Transport([summary])
    result = GitHubProvider(transport=transport).discover("org/repo", "cache")
    assert result[0]["source"]["kind"] == "pr"
    assert result[0]["state"] == expected
    assert len(transport.calls) == 1
    assert urlsplit(transport.calls[0][1]).path == "/repos/org/repo/issues"


def test_discovery_get_budget_depends_on_pages_not_matched_pr_count():
    candidates = [pr(str(number), body="cache", state="closed", pull_request={}) for number in range(1, 251)]
    transport = Transport(candidates[:100], candidates[100:200], candidates[200:])
    result = GitHubProvider(transport=transport).discover("org/repo", "cache", "2026-10-01T00:00:00Z")
    assert len(result) == 250
    assert all(item["source"]["kind"] == "pr" and item["state"] == "closed" for item in result)
    assert len(transport.calls) == 3
    assert all(method == "GET" and urlsplit(url).path == "/repos/org/repo/issues" for method, url, _, _ in transport.calls)
    assert [parse_qs(urlsplit(call[1]).query)["page"] for call in transport.calls] == [["1"], ["2"], ["3"]]
    assert all(parse_qs(urlsplit(call[1]).query)["since"] == ["2026-10-01T00:00:00Z"] for call in transport.calls)


def discovery_context():
    return {"scope": "cache lifecycle", "source": SourceRef("github", "org/repo", "issue", "7",
            "https://github.com/org/repo/issues/7", host="github.com").to_dict(),
            "features": [{"id": "E1", "track": "Engine", "title": "Cache"},
                         {"id": "E10", "track": "Engine", "title": "Other cache work"}]}


def test_discovery_context_filters_scope_excludes_rfc_and_attaches_exact_feature():
    raw = issue("8", body="Implements E10. See https://github.com/org/repo/issues/7")
    unrelated = issue("9", title="Unrelated numerical precision", body="Vector instructions")
    transport = Transport([issue("7"), raw, unrelated])
    result = GitHubProvider(transport=transport).discover("org/repo", discovery_context())
    assert len(result) == 1
    assert result[0]["feature_id"] == "E10"
    assert result[0]["track"] == "Engine"
    assert result[0]["evidence"]["reference"] == "https://github.com/org/repo/issues/7"
    assert result[0]["within_scope"] is False
    assert "feature" not in result[0]  # Author/reviewer never becomes the feature owner.


def test_discovery_exact_backlink_retrieves_work_without_keyword_match():
    raw = issue("8", title="Allocator cleanup", body="E1 https://github.com/org/repo/issues/7")
    result = GitHubProvider(transport=Transport([raw])).discover("org/repo", discovery_context())
    assert result[0]["feature_id"] == "E1"
    assert result[0]["reason"] == "Explicit RFC reference"


@pytest.mark.parametrize("body,can_add", [
    ("Track: Engine\nScope: cache lifecycle", True),
    ("Track: Engine\nScope: cache", False),
    ("Track: Unrelated\nScope: cache lifecycle", False),
    ("Mentions Engine and cache lifecycle", False),
    ("Track: Engine\nScope: cache lifecycle\nScope: broader work", False),
])
def test_discovery_new_work_requires_explicit_track_and_exact_scope(body, can_add):
    raw = issue("8", body=body + "\nRFC: https://github.com/org/repo/issues/7")
    result = GitHubProvider(transport=Transport([raw])).discover("org/repo", discovery_context())
    assert result[0]["within_scope"] is can_add
    assert "feature_id" not in result[0]


@pytest.mark.parametrize("body", [
    "E1 and E10 https://github.com/org/repo/issues/7",  # Ambiguous target.
    "E1 https://github.com/org/repo/issues/70",  # Different RFC.
])
def test_discovery_does_not_resolve_ambiguous_or_prefix_reference(body):
    result = GitHubProvider(transport=Transport([issue("8", body=body)])).discover("org/repo", discovery_context())
    assert "feature_id" not in result[0]


def test_local_discovery_requires_explicit_relative_rfc_reference(tmp_path):
    (tmp_path / "rfc.md").write_text("# RFC\ncache lifecycle\n", encoding="utf-8")
    (tmp_path / "related.md").write_text("# Cleanup\nRFC: rfc.md\nImplements E1\n", encoding="utf-8")
    (tmp_path / "incidental.md").write_text("# cleanup\nmentions rfc.md\n", encoding="utf-8")
    context = discovery_context()
    context["source"] = SourceRef("local", "repo", "markdown", "rfc.md", path="rfc.md").to_dict()
    result = LocalProvider({"repo": tmp_path}).discover("repo", context)
    assert len(result) == 1
    assert result[0]["feature_id"] == "E1"
    assert result[0]["evidence"]["reference"] == "rfc.md"


def local_ref(path="rfcs/example.md"):
    return SourceRef("local", "repo", "markdown", path, path=path)


def test_local_publish_recovers_without_overwriting_and_detects_collision(tmp_path):
    provider = LocalProvider({"repo": tmp_path})
    ref = provider.publish("repo", "Cache RFC", "The cache proposal", "op-1", path="rfcs/example.md")
    original = provider.get_source(ref)
    assert original["revision"] == hashlib.sha256((tmp_path / ref.path).read_bytes()).hexdigest()
    assert original["title"] == "Cache RFC"
    assert provider.find_publication("repo", "op-1") == ref
    assert provider.publish("repo", "Different title", "Other body", "op-1", path=ref.path) == ref
    assert provider.get_source(ref)["body"] == original["body"]
    with pytest.raises(RFCError) as error:
        provider.publish("repo", "Another RFC", "body", "op-2", path=ref.path)
    assert error.value.status == 409


def test_local_managed_update_checks_digest_and_writes_atomically(tmp_path):
    provider = LocalProvider({"repo": tmp_path})
    ref = provider.publish("repo", "RFC", "Human prose", "op-1")
    original = provider.get_source(ref)
    updated = provider.update_source(ref, original["body"] + "\nManaged feature\n", original["revision"])
    assert updated["body"].startswith(original["body"])
    assert updated["revision"] != original["revision"]
    assert not list((tmp_path / "rfcs").glob(".imrfc-*.tmp"))
    with pytest.raises(RFCError) as error:
        provider.update_source(ref, "Stale overwrite", original["revision"])
    assert error.value.status == 409
    assert provider.get_source(ref) == updated


@pytest.mark.parametrize("path", ["../outside.md", "/etc/passwd.md", "C:\\outside.md", "rfcs/../../outside.md", ".git/private.md", "rfcs/secrets.env"])
def test_local_rejects_paths_outside_markdown_root(tmp_path, path):
    provider = LocalProvider({"repo": tmp_path})
    with pytest.raises(RFCError):
        provider.publish("repo", "RFC", "body", "op-1", path=path)
    assert list(tmp_path.iterdir()) == []


def test_local_rejects_symlink_file_and_parent_for_reads_and_publication(tmp_path):
    root = tmp_path / "allowed"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (outside / "private.md").write_text("PRIVATE")
    (root / "linked.md").symlink_to(outside / "private.md")
    (root / "linked-dir").symlink_to(outside, target_is_directory=True)
    provider = LocalProvider({"repo": root})
    for path in ["linked.md", "linked-dir/private.md"]:
        with pytest.raises(RFCError):
            provider.get_source(local_ref(path))
    with pytest.raises(RFCError):
        provider.publish("repo", "RFC", "body", "op-1", path="linked-dir/new.md")
    assert not (outside / "new.md").exists()
    assert provider.discover("repo", "PRIVATE") == []


def test_local_unknown_root_and_remote_url_are_forbidden(tmp_path):
    provider = LocalProvider({"repo": tmp_path})
    with pytest.raises(RFCError):
        provider.get_source(SourceRef("local", "other", "markdown", path="file.md"))
    with pytest.raises(RFCError):
        provider.get_source(SourceRef("local", "repo", "markdown", path="file.md", url="https://localhost/private"))


def test_local_recovery_does_not_claim_absence_on_unreadable_document(tmp_path):
    (tmp_path / "oversized.md").write_bytes(b"x" * (providers.MAX_DOCUMENT_BYTES + 1))
    with pytest.raises(ProviderError) as error:
        LocalProvider({"repo": tmp_path}).find_publication("repo", "op-1")
    assert error.value.uncertain


def test_local_discovery_respects_scope_and_timestamp(tmp_path):
    (tmp_path / "old.md").write_text("# Cache\nOld proposal")
    (tmp_path / "new.md").write_text("# Cache\nNew proposal")
    (tmp_path / "unrelated.md").write_text("# Media\nLayout")
    os.utime(tmp_path / "old.md", (1, 1))
    result = LocalProvider({"repo": tmp_path}).discover("repo", "cache", "2020-01-01T00:00:00Z")
    assert [item["source"]["path"] for item in result] == ["new.md"]


@pytest.mark.skipif(not shutil.which("git"), reason="Git is unavailable")
def test_local_git_commit_observation_does_not_infer_release_acceptance(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "README.md").write_text("# Cache\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "README.md"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "-c", "user.name=Contributor", "-c", "user.email=contributor@example.test", "commit", "-qm", "Implement cache"], check=True)
    sha = subprocess.check_output(["git", "-C", str(tmp_path), "rev-parse", "HEAD"], text=True).strip()
    item = LocalProvider({"repo": tmp_path}).get_item(SourceRef("local", "repo", "commit", sha))
    assert item["revision"] == item["head_sha"] == sha
    assert item["author"] == "Contributor"
    assert item["state"] == "unknown"
