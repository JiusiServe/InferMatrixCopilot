"""The GPU-box publisher: performs signed outbox items through gh, acks back, offline."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from infermatrix_copilot.kb_service import merge
from infermatrix_copilot.kb_service.publisher import Gh, LocalTransport, Publisher, SshTransport
from infermatrix_copilot.knowledge_service.signing import generate_private_key, sign
from test_kb_flow import _flow_runtime, _open_pr
from test_kb_intake_gate import _git as _git_raw

REPO = "JiusiServe/InferMatrixCopilot"


def _git(path: Path, *args: str) -> str:
    return _git_raw(path, *args).strip()


class FakeGh:
    """Just enough of `gh` for the publisher; PR heads come from the git remote."""

    def __init__(self, origin: Path):
        self.origin = origin
        self.prs: dict[int, dict] = {}
        self.calls: list[list[str]] = []
        self.comments: list[tuple[int, str]] = []
        self.fail: set[str] = set()     # "remove-label" / "undo": that call fails

    def _by_branch(self, branch: str) -> list[dict]:
        return [pr for pr in self.prs.values() if pr["headRefName"] == branch and pr["state"] == "OPEN"]

    def __call__(self, argv, *, cwd=None, input=None, stdout=None, stderr=None, check=False):
        assert argv[0] == "gh"
        args = argv[1:]
        self.calls.append(args)
        out = ""
        if args[:2] == ["pr", "list"]:
            branch = args[args.index("--head") + 1]
            out = json.dumps([{"number": p["number"], "headRefOid": p["headRefOid"], "isDraft": p["isDraft"]}
                              for p in self._by_branch(branch)])
        elif args[:2] == ["pr", "create"]:
            branch = args[args.index("--head") + 1]
            head = _git(self.origin, "rev-parse", f"refs/heads/{branch}")
            number = 42 + len(self.prs)
            self.prs[number] = {"number": number, "state": "OPEN", "isDraft": "--draft" in args,
                                "headRefOid": head, "headRefName": branch, "id": f"PR_{number}",
                                "labels": [], "queued": False, "body": (input or b"").decode()}
        elif args[:2] == ["pr", "view"]:
            pr = self.prs[int(args[2])]
            out = json.dumps({**{k: pr[k] for k in ("number", "state", "isDraft", "headRefOid", "headRefName", "id")},
                              "labels": [{"name": name} for name in pr["labels"]]})
        elif args[:2] == ["pr", "comment"]:
            self.comments.append((int(args[2]), input.decode()))
        elif args[:2] == ["pr", "ready"]:
            if "--undo" in args and "undo" in self.fail:
                self.fail.discard("undo")   # fails once
                return subprocess.CompletedProcess(argv, 1, b"", b"HTTP 502")
            self.prs[int(args[2])]["isDraft"] = "--undo" in args
        elif args[:2] == ["pr", "merge"]:
            pr = self.prs[int(args[2])]
            if "--disable-auto" in args:
                pr["queued"] = False
            else:
                assert args[args.index("--match-head-commit") + 1] == pr["headRefOid"]
                pr["queued"] = True
        elif args[:2] == ["pr", "edit"]:
            labels = self.prs[int(args[2])]["labels"]
            if "--remove-label" in args and "remove-label" in self.fail:
                return subprocess.CompletedProcess(argv, 1, b"", b"HTTP 502")
            if "--add-label" in args:
                labels.append(args[args.index("--add-label") + 1])
            elif args[args.index("--remove-label") + 1] in labels:
                labels.remove(args[args.index("--remove-label") + 1])
        elif args[:2] == ["pr", "close"]:
            self.prs[int(args[2])]["state"] = "CLOSED"
        elif args[:2] == ["api", "graphql"]:
            for pr in self.prs.values():
                if f"id={pr['id']}" in args:
                    pr["queued"] = False
        elif args[:3] == ["api", "-X", "PUT"]:
            pass
        else:
            raise AssertionError(args)
        return subprocess.CompletedProcess(argv, 0, out.encode(), b"")

    def created(self) -> int:
        return sum(1 for call in self.calls if call[:2] == ["pr", "create"])


def _setup(tmp_path, *, allow=True, flags=None):
    rt, lifecycle = _flow_runtime(tmp_path)
    changeset_id, publisher_key = _open_pr(tmp_path, rt, lifecycle)
    rt.outbox.refresh_control()     # `kb serve` does this every tick
    origin = tmp_path / "origin"
    gh = FakeGh(origin)
    pub = Publisher(
        transport=LocalTransport(tmp_path / "state"),
        service_public_key=rt.outbox._key.public_key(),
        publisher_key=publisher_key,
        github=Gh(REPO, cwd=tmp_path, run=gh),
        state_dir=tmp_path / "publisher",
        repo_flags=flags if flags is not None else {lifecycle.repo: (True, True)},
        allow_post=allow, allow_push=allow,
        author=("tzhouam", "tzhouam@connect.ust.hk"),
        git_remote=str(origin),
        clock=rt.clock,
    )
    return rt, lifecycle, changeset_id, pub, gh


def _collect(rt):
    merge.apply_acks(rt, rt.outbox.collect_acks(rt.publisher_public_key))


def _issue(rt, lifecycle, changeset_id, kind, **body):
    return rt.outbox.issue(lifecycle.repo, kind, {"changeset_id": changeset_id, **body})


def test_open_pr_rebuilds_the_signed_change_on_its_base_and_acks_the_pr(tmp_path):
    rt, lifecycle, changeset_id, pub, gh = _setup(tmp_path)
    assert pub.run_once()["performed"] == 1
    _collect(rt)
    changeset = rt.ledger.changeset(changeset_id)
    assert changeset["status"] == "pr_open" and changeset["pr_number"] == 42
    branch = f"kb/{lifecycle.repo}/{changeset_id}"
    head = _git(tmp_path / "origin", "rev-parse", f"refs/heads/{branch}")
    assert changeset["head_sha"] == head and changeset["branch"] == branch
    data = rt.load_changeset_files(changeset_id)
    assert _git(tmp_path / "origin", "rev-parse", f"{head}^") == data["base_sha"]
    changed = _git(tmp_path / "origin", "diff", "--name-only", f"{head}^", head).split()
    assert changed == sorted(f"knowledge/{rel}" for rel in data["files"])
    for rel, text in data["files"].items():
        assert _git_raw(tmp_path / "origin", "show", f"{head}:knowledge/{rel}") == text
    assert _git(tmp_path / "origin", "log", "-1", "--format=%an <%ae>", head) == "tzhouam <tzhouam@connect.ust.hk>"
    assert gh.prs[42]["isDraft"] is False and "changeset" in gh.prs[42]["body"]


def test_without_allow_post_the_round_only_records(tmp_path):
    rt, _lifecycle, changeset_id, pub, gh = _setup(tmp_path, allow=False)
    assert pub.run_once()["dry_run"] == 1
    assert gh.calls == [] and not (tmp_path / "state" / "inbox" / "acks").exists()
    trace = (tmp_path / "publisher" / "traces" / "publisher.jsonl").read_text()
    assert '"event": "dry_run"' in trace and '"files"' not in trace
    pub.allow_post = True           # posting alone never pushes a branch
    assert pub.run_once()["dry_run"] == 1 and gh.calls == []
    assert rt.ledger.changeset(changeset_id)["status"] == "pr_requested"


def test_a_crash_after_performing_never_performs_twice(tmp_path):
    rt, _lifecycle, changeset_id, pub, gh = _setup(tmp_path)
    pub.run_once()
    for ack in (tmp_path / "state" / "inbox" / "acks").glob("*.json"):
        ack.unlink()                # the ack never reached the service
    assert pub.run_once()["resent"] == 1 and gh.created() == 1
    for done in (tmp_path / "publisher" / "done").glob("*.json"):
        done.unlink()               # crashed before even recording it
    for ack in (tmp_path / "state" / "inbox" / "acks").glob("*.json"):
        ack.unlink()
    assert pub.run_once()["performed"] == 1 and gh.created() == 1   # reuses the open PR
    _collect(rt)
    assert rt.ledger.changeset(changeset_id)["pr_number"] == 42


def test_unverifiable_unconfigured_or_stale_items_are_never_performed(tmp_path):
    rt, lifecycle, _changeset_id, pub, gh = _setup(tmp_path, flags={})
    assert pub.run_once()["skipped"] == 1 and gh.calls == []       # our config says: not auto_merge
    pub.repo_flags = {lifecycle.repo: (True, True)}
    pub.service_public_key = generate_private_key(tmp_path / "other.pem").public_key()
    assert pub.run_once()["skipped"] == 1 and gh.calls == []       # not signed by the service
    pub.service_public_key = rt.outbox._key.public_key()
    now = rt.clock()
    pub.clock = lambda: now + 11 * 60                              # control record went stale
    assert pub.run_once() == {"performed": 0, "failed": 0, "resent": 0, "undelivered": 0,
                              "dry_run": 0, "skipped": 0}
    assert gh.calls == []


def test_open_pr_refuses_paths_outside_governed_knowledge_pages(tmp_path):
    rt, lifecycle, changeset_id, pub, gh = _setup(tmp_path)
    for path in list((tmp_path / "state" / "outbox").glob("[0-9]*.json")):
        path.unlink()
    data = rt.load_changeset_files(changeset_id)
    for bad in ("src/x.py", "knowledge/tools/x.md", "knowledge/repos/demo/../../.github/x.md"):
        _issue(rt, lifecycle, f"{changeset_id}-{len(bad)}", "open_pr", base_sha=data["base_sha"],
               branch=f"kb/{lifecycle.repo}/x{len(bad)}", files={bad: "x\n"}, deleted=[], title="t", body="b")
    assert pub.run_once()["failed"] == 3 and gh.created() == 0
    acks = [json.loads(p.read_text())["payload"] for p in (tmp_path / "state" / "inbox" / "acks").glob("*.json")]
    assert all(not a["ok"] and "outside governed knowledge pages" in a["error"] for a in acks)


def test_post_verdict_enqueue_pause_and_close(tmp_path):
    rt, lifecycle, changeset_id, pub, gh = _setup(tmp_path)
    pub.run_once()
    head = gh.prs[42]["headRefOid"]
    _issue(rt, lifecycle, changeset_id, "post_verdict", pr=42, head_sha="f" * 40, comment="stale")
    _issue(rt, lifecycle, changeset_id, "post_verdict", pr=42, head_sha=head, comment="<!-- kb-gate:verdict:v1 -->")
    summary = pub.run_once()
    assert summary["performed"] == 1 and summary["failed"] == 1
    assert gh.comments == [(42, "<!-- kb-gate:verdict:v1 -->")]
    gh.prs[42]["isDraft"] = True                                   # paused earlier, then resumed
    rt.outbox.refresh_control()
    _issue(rt, lifecycle, changeset_id, "enqueue", pr=42, head_sha=head)
    assert pub.run_once()["performed"] == 1
    assert gh.prs[42]["isDraft"] is False and gh.prs[42]["queued"] is True
    _issue(rt, lifecycle, changeset_id, "pause", pr=42, reason="drill")
    assert pub.run_once()["performed"] == 1
    assert gh.prs[42]["queued"] is False and gh.prs[42]["isDraft"] is True and "kb:hold" in gh.prs[42]["labels"]
    _issue(rt, lifecycle, changeset_id, "close", pr=42, reason="superseded")
    _issue(rt, lifecycle, changeset_id, "pause", pr=42, reason="after close")
    assert pub.run_once()["performed"] == 2 and gh.prs[42]["state"] == "CLOSED"


def test_pause_is_performed_even_while_the_repository_is_paused(tmp_path):
    rt, lifecycle, changeset_id, pub, gh = _setup(tmp_path)
    pub.run_once()
    _collect(rt)                    # the PR is open, so the pause applies to it
    rt.outbox.transition(lambda: rt.ledger.bump_generation(lifecycle.repo, pause=True, reason="drill"),
                         public_repos={lifecycle.repo})
    merge.pause_open_prs(rt.ledger, rt.outbox, lifecycle.repo, "drill")
    _collect(rt)
    assert pub.run_once()["performed"] == 1 and gh.prs[42]["isDraft"] is True
    _collect(rt)
    assert rt.ledger.changeset(changeset_id)["status"] == "paused"


def test_pause_resume_regate_and_enqueue_round_trip(tmp_path):
    """pause (draft + kb:hold) -> kb resume -> fresh verdict lifts the label ->
    the gate can pass -> enqueue readies the draft and queues it."""
    rt, lifecycle, changeset_id, pub, gh = _setup(tmp_path)
    pub.run_once()
    _collect(rt)
    head = gh.prs[42]["headRefOid"]
    rt.github.prs[42] = {"number": 42, "state": "open", "merged": False, "head": {"sha": head}}
    rt.outbox.transition(lambda: rt.ledger.bump_generation(lifecycle.repo, pause=True, reason="drill"),
                         public_repos={lifecycle.repo})
    merge.pause_open_prs(rt.ledger, rt.outbox, lifecycle.repo, "drill")
    pub.run_once()
    _collect(rt)
    assert gh.prs[42]["isDraft"] and "kb:hold" in gh.prs[42]["labels"]
    assert rt.ledger.changeset(changeset_id)["status"] == "paused"

    def _resume():
        rt.ledger.resume(lifecycle.repo)
        merge.resume_paused_prs(rt.ledger, lifecycle.repo)
    rt.outbox.transition(_resume, public_repos={lifecycle.repo})
    assert merge.advance(rt, lifecycle) == [f"verdict issued {changeset_id}"]
    pub.run_once()
    _collect(rt)
    assert "kb:hold" not in gh.prs[42]["labels"] and gh.comments[-1][0] == 42
    rt.github.statuses[head] = "success"             # the precheck the comment triggered
    assert merge.advance(rt, lifecycle) == [f"enqueue issued {changeset_id}"]
    pub.run_once()
    _collect(rt)
    assert gh.prs[42]["isDraft"] is False and gh.prs[42]["queued"] is True
    assert rt.ledger.changeset(changeset_id)["status"] == "queued"


def test_a_failed_pause_is_retried_not_acknowledged(tmp_path):
    rt, lifecycle, changeset_id, pub, gh = _setup(tmp_path)
    pub.run_once()
    _collect(rt)
    gh.prs[42]["queued"] = True
    gh.fail.add("undo")
    rt.outbox.transition(lambda: rt.ledger.bump_generation(lifecycle.repo, pause=True, reason="drill"),
                         public_repos={lifecycle.repo})
    merge.pause_open_prs(rt.ledger, rt.outbox, lifecycle.repo, "drill")
    assert pub.run_once()["failed"] == 1
    assert not list((tmp_path / "state" / "inbox" / "acks").glob("*.json"))   # nothing answered
    assert pub.run_once()["performed"] == 1 and gh.prs[42]["isDraft"] is True
    _collect(rt)
    assert rt.ledger.changeset(changeset_id)["status"] == "paused"


@pytest.mark.parametrize("control", [{"payload": {"issued_at": "invalid"}}, [], {"payload": []}, "x"])
def test_malformed_control_records_and_items_never_stop_the_publisher(tmp_path, control):
    rt, _lifecycle, _changeset_id, pub, gh = _setup(tmp_path)
    good = (tmp_path / "state" / "outbox" / "control.json").read_text()
    (tmp_path / "state" / "outbox" / "control.json").write_text(json.dumps(control))
    assert pub.run_once()["performed"] == 0 and gh.calls == []
    (tmp_path / "state" / "outbox" / "control.json").write_text(good)
    (tmp_path / "state" / "outbox" / "1-bbbbbbbbbbbb.json").write_text(json.dumps(control))
    summary = pub.run_once()
    assert summary["skipped"] == 1 and summary["performed"] == 1


def test_a_verdict_is_not_posted_while_the_hold_label_cannot_be_removed(tmp_path):
    rt, lifecycle, changeset_id, pub, gh = _setup(tmp_path)
    pub.run_once()
    head = gh.prs[42]["headRefOid"]
    gh.prs[42]["labels"].append("kb:hold")
    gh.fail.add("remove-label")
    _issue(rt, lifecycle, changeset_id, "post_verdict", pr=42, head_sha=head, comment="verdict")
    assert pub.run_once()["failed"] == 1 and gh.comments == []


def test_transport_failures_keep_the_daemon_alive_and_resend_later(tmp_path):
    rt, _lifecycle, changeset_id, pub, gh = _setup(tmp_path)
    real = pub.transport

    class Flaky:
        down = True

        def list_items(self):
            return real.list_items()

        def read(self, rel):
            return real.read(rel)

        def write_ack(self, item_id, data):
            if self.down:
                raise OSError("ssh: connection reset")
            real.write_ack(item_id, data)

    pub.transport = Flaky()
    assert pub.run_once()["performed"] == 1          # performed; its ack could not be delivered
    assert not list((tmp_path / "state" / "inbox" / "acks").glob("*.json"))
    pub.transport.down = False
    assert pub.run_once()["resent"] == 1 and gh.created() == 1
    _collect(rt)
    assert rt.ledger.changeset(changeset_id)["status"] == "pr_open"

    class Unreachable:
        def read(self, rel):
            return real.read(rel)

        def list_items(self):
            raise OSError("ssh: no route to host")

    pub.transport = Unreachable()
    assert pub.run_once()["performed"] == 0          # traced, not raised
    assert "outbox_unreachable" in (tmp_path / "publisher" / "traces" / "publisher.jsonl").read_text()


def test_an_open_pr_with_other_content_is_never_adopted(tmp_path):
    rt, lifecycle, changeset_id, pub, gh = _setup(tmp_path)
    branch = f"kb/{lifecycle.repo}/{changeset_id}"
    gh.prs[7] = {"number": 7, "state": "OPEN", "isDraft": False, "headRefOid": "e" * 40,
                 "headRefName": branch, "id": "PR_7", "labels": [], "queued": False, "body": ""}
    assert pub.run_once()["failed"] == 1 and gh.created() == 0
    (ack,) = [json.loads(p.read_text())["payload"] for p in (tmp_path / "state" / "inbox" / "acks").glob("*.json")]
    assert not ack["ok"] and "does not carry the signed change" in ack["error"]


def test_a_corrupt_completion_record_is_set_aside_not_guessed(tmp_path):
    rt, lifecycle, changeset_id, pub, gh = _setup(tmp_path)
    (item_id,) = pub.transport.list_items()
    done = tmp_path / "publisher" / "done" / f"{item_id}.json"
    done.parent.mkdir(parents=True)
    done.write_text('{"item_id": "tru')              # a write interrupted by a crash
    assert pub.run_once()["skipped"] == 1 and gh.calls == []
    assert done.with_suffix(".corrupt").exists() and not done.exists()
    assert pub.run_once()["skipped"] == 1 and gh.calls == []   # still waits for a person
    assert "corrupt_record" in (tmp_path / "publisher" / "traces" / "publisher.jsonl").read_text()
    assert not list((tmp_path / "publisher" / "done").glob(".*"))  # atomic writes leave no temp files


def test_ssh_transport_quotes_paths_and_pipes_acks():
    seen = []

    def run(argv, input=None, **kw):
        seen.append((argv, input))
        out = b"1-aaaaaaaaaaaa.json\ncontrol.json\nbad name.json\n" if "ls -1" in argv[-1] else b"{}"
        return subprocess.CompletedProcess(argv, 0, out, b"")

    transport = SshTransport("bot", "/srv/kb state", run=run)
    assert transport.list_items() == ["1-aaaaaaaaaaaa"]
    transport.read("outbox/control.json")
    transport.write_ack("1-aaaaaaaaaaaa", b"ACK")
    assert seen[0][0][:4] == ["ssh", "-o", "BatchMode=yes", "bot"]
    assert "'/srv/kb state/outbox/control.json'" in seen[1][0][-1]
    assert seen[2][1] == b"ACK" and "mv '/srv/kb state/inbox/acks/.1-aaaaaaaaaaaa.tmp'" in seen[2][0][-1]
    with pytest.raises(SystemExit):
        SshTransport.parse("bot:relative/path")


def test_kb_publish_needs_both_keys(monkeypatch, tmp_path):
    from infermatrix_copilot.kb_service.cli import main

    monkeypatch.delenv("KB_SERVICE_PUBKEY", raising=False)
    with pytest.raises(SystemExit, match="KB_SERVICE_PUBKEY"):
        main(["publish", "--local", str(tmp_path), "--once"])


def test_acks_carry_the_documented_fields(tmp_path):
    rt, _lifecycle, _changeset_id, pub, _gh = _setup(tmp_path)
    pub.run_once()
    (ack_file,) = (tmp_path / "state" / "inbox" / "acks").glob("*.json")
    envelope = json.loads(ack_file.read_text())
    assert envelope["purpose"] == "kb-ack"
    assert set(envelope["payload"]) == {"item_id", "kind", "changeset_id", "ok", "pr", "head_sha", "branch", "error"}
    assert sign  # the envelope format is the shared signing module's
