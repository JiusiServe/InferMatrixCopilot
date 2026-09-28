"""Knowledge PRs the service did not open: auto gate, human approval, people."""

from __future__ import annotations

import json
import subprocess
import uuid

from infermatrix_copilot.kb_service import merge
from infermatrix_copilot.kb_service.external import poll_external
from infermatrix_copilot.knowledge_service.signing import load_public_key, public_key_text, verify
from infermatrix_copilot.knowledge_service.ops import KnowledgeOperation as Op, apply_operations
from test_kb_flow import KnowledgeGitHub, _flow_runtime, _items
from test_kb_intake_gate import PAGE, _rule, _tree

REPO = "JiusiServe/InferMatrixCopilot"


def _git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout.strip()


class PullsGitHub(KnowledgeGitHub):
    def __init__(self):
        super().__init__()
        self.open: dict[int, dict] = {}
        self.reviews: dict[int, list[dict]] = {}

    def _answer(self, url):
        path = url.split("?", 1)[0]
        if path.endswith(f"/repos/{REPO}/pulls"):
            return list(self.open.values()) if "page=1" in url else []
        if "/reviews" in path:
            reviews = self.reviews.get(int(path.split("/pulls/")[1].split("/")[0]), [])
            from urllib.parse import parse_qs, urlsplit
            page = int(parse_qs(urlsplit(url).query).get("page", ["1"])[0])
            return reviews[(page - 1) * 100: page * 100]
        return super()._answer(url)


def _setup(tmp_path):
    rt, lifecycle = _flow_runtime(tmp_path)
    github = PullsGitHub()
    github.prs = rt.github.prs
    rt.github = github
    rt.lease_owner = rt.ledger.acquire_lease("scheduler")
    origin = tmp_path / "origin"
    (origin / ".github").mkdir(exist_ok=True)
    (origin / ".github" / "CODEOWNERS").write_text("/.github/ @alice\n")
    _git(origin, "add", "-A")
    _git(origin, "-c", "user.name=t", "-c", "user.email=t@e", "commit", "-q", "-m", "owners")
    return rt, lifecycle, origin


def _open_human_pr(rt, origin, number, files: dict[str, str | None], *, labels=(), draft=False):
    _git(origin, "checkout", "-q", "-B", f"human-{number}", "main")
    for rel, text in files.items():
        target = origin / rel
        if text is None:
            target.unlink()
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
    _git(origin, "add", "-A")
    _git(origin, "-c", "user.name=h", "-c", "user.email=h@e", "commit", "-q", "--allow-empty",
         "-m", f"pr {number} {uuid.uuid4().hex}")      # a distinct head even for an identical tree
    head = _git(origin, "rev-parse", "HEAD")
    _git(origin, "update-ref", f"refs/pull/{number}/head", head)
    _git(origin, "checkout", "-q", "main")
    rt.github.open[number] = {"number": number, "draft": draft, "head": {"sha": head}, "title": "Add a rule",
                              "body": "from a person", "user": {"login": "dev"},
                              "labels": [{"name": name} for name in labels]}
    rt.github.prs[number] = {"state": "open", "merged": False, "head": {"sha": head}}
    return head


def _add_rule_files():
    base = _tree()
    return {f"knowledge/{rel}": text for rel, text in apply_operations(
        base, [Op("add", PAGE, "DEMO-2a", _rule("DEMO-2a", "PR #11"))], release="v1", today="2026-09-28").files.items()}


def _verdict(tmp_path, rt):
    comment = _items(tmp_path, "post_verdict")[-1]["body"]["comment"]
    envelope = json.loads(comment.split("```json\n", 1)[1].rsplit("\n```", 1)[0])
    return verify("kb-gate-verdict", envelope, load_public_key(public_key_text(rt.outbox._key.public_key())))


def test_a_human_knowledge_pr_passes_the_auto_gate_and_gets_a_verdict(tmp_path):
    rt, lifecycle, origin = _setup(tmp_path)
    head = _open_human_pr(rt, origin, 7, _add_rule_files())
    (event,) = poll_external(rt)
    assert "auto pr_open" in event
    (changeset,) = [cs for cs in rt.ledger.changesets("demo", ("pr_open",)) if cs["kind"] == "external"]
    assert changeset["pr_number"] == 7 and changeset["head_sha"] == head
    assert poll_external(rt) == []                       # judged once per head
    assert merge.advance(rt, lifecycle) == [f"verdict issued {changeset['id']}"]
    verdict = _verdict(tmp_path, rt)
    merge_base = _git(origin, "merge-base", "main", head)
    assert verdict["source"] == "auto" and verdict["pr"] == 7 and verdict["head_sha"] == head
    assert verdict["manifest"] == rt.knowledge.raw_manifest(merge_base, head)
    assert verdict["blocks"] and all(b["verdict"] == "pass" for b in verdict["blocks"])


def test_paths_outside_the_governed_pages_need_a_maintainer(tmp_path):
    rt, lifecycle, origin = _setup(tmp_path)
    head = _open_human_pr(rt, origin, 8, {"knowledge/tools/check.md": "tool notes\n"})
    (event,) = poll_external(rt)
    assert event.endswith("to people")
    assert "kb:human-approved" in rt.ledger.human_queue("demo")[-1]["reason"]
    assert poll_external(rt) == []                       # once per head
    # a maintainer approves the CURRENT head and labels it: a human-approved verdict
    rt.github.open[8]["labels"] = [{"name": "kb:human-approved"}]
    rt.github.reviews[8] = [{"id": 99, "state": "APPROVED", "commit_id": head, "user": {"login": "alice"}}]
    head2 = _open_human_pr(rt, origin, 8, {"knowledge/tools/check.md": "tool notes v2\n"},
                           labels=("kb:human-approved",))
    rt.github.reviews[8] = [{"id": 99, "state": "APPROVED", "commit_id": head, "user": {"login": "alice"}}]
    assert poll_external(rt) == []                       # approval is for the old head: wait
    rt.github.reviews[8].append({"id": 100, "state": "APPROVED", "commit_id": head2, "user": {"login": "alice"}})
    (event,) = poll_external(rt)
    assert "human-approved pr_open" in event
    (changeset,) = [cs for cs in rt.ledger.changesets("demo", ("pr_open",)) if cs["kind"] == "external"]
    merge.advance(rt, lifecycle)
    verdict = _verdict(tmp_path, rt)
    assert verdict["source"] == "human-approved" and verdict["review_ids"] == [100]
    assert verdict["reviewers"] == ["alice"] and verdict["blocks"] == []
    assert changeset["head_sha"] == head2


def test_approvals_by_non_maintainers_or_later_retracted_do_not_count(tmp_path):
    rt, lifecycle, origin = _setup(tmp_path)
    head = _open_human_pr(rt, origin, 9, {"knowledge/tools/x.md": "x\n"}, labels=("kb:human-approved",))
    rt.github.reviews[9] = [{"id": 1, "state": "APPROVED", "commit_id": head, "user": {"login": "mallory"}},
                            {"id": 2, "state": "APPROVED", "commit_id": head, "user": {"login": "alice"}},
                            {"id": 3, "state": "DISMISSED", "commit_id": head, "user": {"login": "alice"}}]
    assert poll_external(rt) == []


def test_a_pr_branched_before_main_changed_the_same_page_must_be_rebased(tmp_path):
    rt, lifecycle, origin = _setup(tmp_path)
    _open_human_pr(rt, origin, 10, _add_rule_files())
    page = origin / "knowledge" / PAGE
    page.write_text(page.read_text() + "\n<!-- main moved -->\n")
    _git(origin, "add", "-A")
    _git(origin, "-c", "user.name=t", "-c", "user.email=t@e", "commit", "-q", "-m", "main moves")
    (event,) = poll_external(rt)
    assert event.endswith("to people") and "rebased" in rt.ledger.human_queue("demo")[-1]["reason"]


def test_a_new_head_is_judged_again_and_drafts_and_our_own_prs_are_skipped(tmp_path):
    rt, lifecycle, origin = _setup(tmp_path)
    _open_human_pr(rt, origin, 11, _add_rule_files(), draft=True)
    assert poll_external(rt) == []
    rt.github.open[11]["draft"] = False
    assert len(poll_external(rt)) == 1
    (first,) = [cs for cs in rt.ledger.changesets("demo", ("pr_open",)) if cs["kind"] == "external"]
    head2 = _open_human_pr(rt, origin, 11, {**_add_rule_files(), "knowledge/repos/demo/core/_index.md":
                                            "# core\n\n- [rules](rules.md)\n"})
    assert merge.advance(rt, lifecycle) == [f"head_changed {first['id']}"]
    assert rt.ledger.human_queue("demo") == []           # an author pushing is not an incident
    (event,) = poll_external(rt)
    assert "PR #11" in event
    assert rt.ledger.changesets("demo", ("pr_open",))[-1]["head_sha"] == head2
    # a PR the service opened itself is never judged as external
    ours = rt.ledger.new_changeset_id("demo", "intake")
    rt.ledger.stage_intake(rt.lease_owner, "demo", ours, detail={}, status="pr_open", verdicts=[],
                           human_reason="", drafted_events=[])
    rt.ledger.update_changeset(ours, pr_number=12)
    _open_human_pr(rt, origin, 12, _add_rule_files())
    assert all("PR #12" not in event for event in poll_external(rt))


def _verifier_passes(tmp_path, rt, origin, number, labels=(), reviews=()):
    """Run the real kb-gate PR-stage verifier on the verdict this service posted."""
    import time

    from infermatrix_copilot.knowledge_service import gate_verifier as gv
    from infermatrix_copilot.knowledge_service.signing import sign

    (comment,) = [item["body"]["comment"] for item in _items(tmp_path, "post_verdict")
                  if item["body"]["pr"] == number]
    head = rt.github.open[number]["head"]["sha"]

    class VerifierGitHub:
        def get(self, path):
            if path.endswith(f"/pulls/{number}"):
                return {"number": number, "state": "open", "draft": False, "head": {"sha": head},
                        "labels": [{"name": name} for name in labels]}
            return {r["id"]: r for r in reviews}[int(path.rsplit("/", 1)[1])]

        def get_all(self, path):
            return list(reviews) if path.endswith("/reviews") else [{"body": comment}]

    holds = {"issued_at": time.time(), "sequence": 1, "global": False, "repos": [], "prs": []}
    ctx = gv.Context(git=gv.Git(rt.knowledge.path), github=VerifierGitHub(), repository=REPO,
                     public_key=rt.outbox._key.public_key(), holds_loader=lambda: sign("kb-holds", holds, rt.outbox._key),
                     codeowners=gv.parse_codeowners((origin / ".github" / "CODEOWNERS").read_text()), now=time.time())
    _head, problems = gv.verify_pr(ctx, number)
    return problems


def test_verdicts_for_external_prs_pass_the_real_kb_gate_verifier(tmp_path):
    rt, lifecycle, origin = _setup(tmp_path)
    rt.clock = __import__("time").time          # verdict windows are checked against the real clock
    _open_human_pr(rt, origin, 7, _add_rule_files())
    poll_external(rt)
    merge.advance(rt, lifecycle)
    assert _verifier_passes(tmp_path, rt, origin, 7) == []

    head = _open_human_pr(rt, origin, 8, {"knowledge/tools/check.md": "tool notes\n"}, labels=("kb:human-approved",))
    review = {"id": 100, "state": "APPROVED", "commit_id": head, "user": {"login": "alice"}}
    rt.github.reviews[8] = [review]
    poll_external(rt)
    merge.advance(rt, lifecycle)
    assert _verifier_passes(tmp_path, rt, origin, 8, labels=("kb:human-approved",), reviews=(review,)) == []


def test_a_retraction_on_a_later_page_of_reviews_is_seen(tmp_path):
    rt, lifecycle, origin = _setup(tmp_path)
    head = _open_human_pr(rt, origin, 20, {"knowledge/tools/x.md": "x\n"}, labels=("kb:human-approved",))
    noise = [{"id": 1000 + i, "state": "COMMENTED", "commit_id": head, "user": {"login": f"u{i}"}}
             for i in range(120)]
    rt.github.reviews[20] = [{"id": 1, "state": "APPROVED", "commit_id": head, "user": {"login": "alice"}},
                             *noise,
                             {"id": 2, "state": "CHANGES_REQUESTED", "commit_id": head, "user": {"login": "alice"}}]
    assert poll_external(rt) == []


def test_an_auto_verdict_needs_a_current_judge_calibration(tmp_path):
    from dataclasses import replace

    from test_kb_intake_gate import _calibrate

    rt, lifecycle, origin = _setup(tmp_path)
    rt.registry["demo"] = replace(rt.registry["demo"], calibration_set="missing")
    _open_human_pr(rt, origin, 21, _add_rule_files())
    (event,) = poll_external(rt)
    assert event.endswith("calibration_required")
    assert poll_external(rt) == []                       # not re-judged (no paid judge calls) until calibrated
    _calibrate(tmp_path, rt, rt.registry["demo"])
    (event,) = poll_external(rt)
    assert event.endswith("auto pr_open")


def test_a_head_sent_to_people_can_be_approved_without_a_new_push(tmp_path):
    rt, lifecycle, origin = _setup(tmp_path)
    head = _open_human_pr(rt, origin, 30, {"knowledge/tools/y.md": "y\n"})
    (event,) = poll_external(rt)
    assert event.endswith("to people")
    assert poll_external(rt) == []
    rt.github.open[30]["labels"] = [{"name": "kb:human-approved"}]
    rt.github.reviews[30] = [{"id": 7, "state": "APPROVED", "commit_id": head, "user": {"login": "alice"}}]
    (event,) = poll_external(rt)
    assert "human-approved pr_open" in event
    assert poll_external(rt) == []


def test_a_withdrawn_approval_after_signing_stops_the_pr(tmp_path):
    rt, lifecycle, origin = _setup(tmp_path)
    rt.clock = __import__("time").time          # the verifier checks the verdict window in real time
    head = _open_human_pr(rt, origin, 40, {"knowledge/tools/z.md": "z\n"}, labels=("kb:human-approved",))
    rt.github.reviews[40] = [{"id": 5, "state": "APPROVED", "commit_id": head, "user": {"login": "alice"}}]
    poll_external(rt)
    (changeset,) = [cs for cs in rt.ledger.changesets("demo", ("pr_open",)) if cs["kind"] == "external"]
    merge.advance(rt, lifecycle)
    rt.ledger.update_changeset(changeset["id"], status="verdict_posted", pending_item=None)
    rt.github.reviews[40].append({"id": 6, "state": "CHANGES_REQUESTED", "commit_id": head,
                                  "user": {"login": "alice"}})
    assert merge.advance(rt, lifecycle) == [f"approval_withdrawn {changeset['id']}"]
    assert any(item["body"]["pr"] == 40 for item in _items(tmp_path, "pause"))
    assert rt.ledger.human_queue("demo")
    # until the pause is acked it keeps its state (and so its queue slot)
    assert rt.ledger.changeset(changeset["id"])["status"] == "verdict_posted"
    assert merge.advance(rt, lifecycle) == []
    assert poll_external(rt) == []                      # never re-staged on the remaining approvals
    # the verifier sees it too, even though review 5 still reads APPROVED
    problems = _verifier_passes(tmp_path, rt, origin, 40, labels=("kb:human-approved",),
                                reviews=tuple(rt.github.reviews[40]))
    assert any("latest review no longer approves" in p for p in problems), problems


def test_rules_an_external_pr_retires_enter_the_retirement_ledger(tmp_path):
    rt, lifecycle, origin = _setup(tmp_path)
    (origin / "skills" / "x.md").write_text("no citations here\n")   # else it needs a companion PR
    _git(origin, "add", "-A")
    _git(origin, "-c", "user.name=t", "-c", "user.email=t@e", "commit", "-q", "-m", "drop citation")
    retired = apply_operations(_tree(), [Op("retire", PAGE, "DEMO-1a", reason="upstream-removed",
                                            evidence="PR #13")], release="v1", today="2026-09-28").files
    _open_human_pr(rt, origin, 41, {f"knowledge/{rel}": text for rel, text in retired.items()})
    rt.registry["demo"] = __import__("dataclasses").replace(rt.registry["demo"], retire_ratio=1.0)
    events = poll_external(rt)
    assert "auto pr_open" in events[0], (events, rt.ledger.human_queue("demo"))
    (changeset,) = [cs for cs in rt.ledger.changesets("demo", ("pr_open",)) if cs["kind"] == "external"]
    assert changeset["detail"]["retirements"] == [{"rule_id": "DEMO-1a", "page": PAGE}]
    rt.ledger.update_changeset(changeset["id"], status="verdict_posted")
    rt.github.prs[41] = {"state": "closed", "merged": True, "merge_commit_sha": "f" * 40,
                         "head": {"sha": changeset["head_sha"]}}
    merge.advance(rt, lifecycle)
    row = rt.ledger._conn.execute("SELECT rule_id, page FROM retirements WHERE repo='demo'").fetchall()
    assert [tuple(r) for r in row] == [("DEMO-1a", PAGE)]


def test_a_withdrawn_queued_pr_holds_the_slot_until_its_pause_is_acked(tmp_path):
    from test_kb_flow import _ack
    from infermatrix_copilot.knowledge_service.signing import generate_private_key, load_public_key, public_key_text

    rt, lifecycle, origin = _setup(tmp_path)
    publisher = generate_private_key(tmp_path / "pub.pem")
    rt.publisher_public_key = load_public_key(public_key_text(publisher.public_key()))
    head = _open_human_pr(rt, origin, 50, {"knowledge/tools/q.md": "q\n"}, labels=("kb:human-approved",))
    rt.github.reviews[50] = [{"id": 1, "state": "APPROVED", "commit_id": head, "user": {"login": "alice"}},
                             {"id": 2, "state": "APPROVED", "commit_id": head, "user": {"login": "bob"}}]
    (origin / ".github" / "CODEOWNERS").write_text("/.github/ @alice @bob\n")
    _git(origin, "add", "-A")
    _git(origin, "-c", "user.name=t", "-c", "user.email=t@e", "commit", "-q", "-m", "two maintainers")
    rt.github.open[50]["head"]["sha"] = head
    poll_external(rt)
    (changeset,) = [cs for cs in rt.ledger.changesets("demo", ("pr_open",)) if cs["kind"] == "external"]
    rt.ledger.update_changeset(changeset["id"], status="queued", pending_item=None)
    rt.github.reviews[50].append({"id": 3, "state": "CHANGES_REQUESTED", "commit_id": head,
                                  "user": {"login": "alice"}})
    assert merge.advance(rt, lifecycle) == [f"approval_withdrawn {changeset['id']}"]
    assert rt.ledger.changeset(changeset["id"])["status"] == "queued"       # slot still held
    _ack(tmp_path, rt, publisher, kind="pause", changeset_id=changeset["id"], ok=False)   # dequeue failed
    assert rt.ledger.changeset(changeset["id"])["status"] == "queued"
    _ack(tmp_path, rt, publisher, kind="pause", changeset_id=changeset["id"], ok=True)
    assert rt.ledger.changeset(changeset["id"])["status"] == "approval_withdrawn"
    assert poll_external(rt) == []                      # bob's approval alone does not re-stage it


def test_a_withdrawal_during_an_outstanding_enqueue_keeps_the_queue_slot(tmp_path):
    rt, lifecycle, origin = _setup(tmp_path)
    head = _open_human_pr(rt, origin, 60, {"knowledge/tools/w.md": "w\n"}, labels=("kb:human-approved",))
    rt.github.reviews[60] = [{"id": 1, "state": "APPROVED", "commit_id": head, "user": {"login": "alice"}}]
    poll_external(rt)
    (first,) = [cs for cs in rt.ledger.changesets("demo", ("pr_open",)) if cs["kind"] == "external"]
    merge.advance(rt, lifecycle)
    rt.ledger.update_changeset(first["id"], status="verdict_posted", pending_item=None)
    rt.github.statuses[head] = "success"
    assert merge.advance(rt, lifecycle) == [f"enqueue issued {first['id']}"]
    rt.github.reviews[60].append({"id": 2, "state": "DISMISSED", "commit_id": head, "user": {"login": "alice"}})
    assert merge.advance(rt, lifecycle) == [f"approval_withdrawn {first['id']}"]
    # a second, fully eligible PR must not be enqueued while the first may be queued
    second = rt.ledger.new_changeset_id("demo", "intake")
    rt.ledger.stage_intake(rt.lease_owner, "demo", second, detail={}, status="verdict_posted", verdicts=[],
                           human_reason="", drafted_events=[])
    rt.ledger.update_changeset(second, pr_number=61, head_sha="6" * 40)
    rt.github.prs[61] = {"state": "open", "merged": False, "head": {"sha": "6" * 40}}
    rt.github.statuses["6" * 40] = "success"
    assert merge.advance(rt, lifecycle) == []
    assert [i["body"]["pr"] for i in _items(tmp_path, "enqueue")] == [60]



def test_a_withdrawal_completes_only_after_every_enqueue_could_have_run(tmp_path):
    """The publisher may run the pause before a still-valid enqueue: the pause
    is repeated once that enqueue has certainly expired."""
    from test_kb_flow import _ack
    from infermatrix_copilot.knowledge_service.signing import generate_private_key, load_public_key, public_key_text

    rt, lifecycle, origin = _setup(tmp_path)
    publisher = generate_private_key(tmp_path / "pub.pem")
    rt.publisher_public_key = load_public_key(public_key_text(publisher.public_key()))
    head = _open_human_pr(rt, origin, 70, {"knowledge/tools/v.md": "v\n"}, labels=("kb:human-approved",))
    rt.github.reviews[70] = [{"id": 1, "state": "APPROVED", "commit_id": head, "user": {"login": "alice"}}]
    poll_external(rt)
    (cs,) = [c for c in rt.ledger.changesets("demo", ("pr_open",)) if c["kind"] == "external"]
    merge.advance(rt, lifecycle)
    rt.ledger.update_changeset(cs["id"], status="verdict_posted", pending_item=None)
    rt.github.statuses[head] = "success"
    assert merge.advance(rt, lifecycle) == [f"enqueue issued {cs['id']}"]
    rt.github.reviews[70].append({"id": 2, "state": "DISMISSED", "commit_id": head, "user": {"login": "alice"}})
    merge.advance(rt, lifecycle)
    _ack(tmp_path, rt, publisher, kind="pause", changeset_id=cs["id"], ok=True)   # ran before the enqueue
    assert rt.ledger.changeset(cs["id"])["status"] == "verdict_posted"           # not complete yet
    pauses = len(_items(tmp_path, "pause"))
    assert merge.advance(rt, lifecycle) == [] and len(_items(tmp_path, "pause")) == pauses
    start = rt.clock()
    rt.clock = lambda: start + 30 * 60 + merge.CLOCK_SKEW + 1
    rt.outbox._clock = rt.clock                                   # items are stamped by the outbox clock                     # the enqueue is dead now
    merge.advance(rt, lifecycle)
    assert len(_items(tmp_path, "pause")) == pauses + 1
    _ack(tmp_path, rt, publisher, kind="pause", changeset_id=cs["id"], ok=True)
    assert rt.ledger.changeset(cs["id"])["status"] == "approval_withdrawn"


def test_a_late_ack_of_an_early_pause_does_not_complete_the_withdrawal(tmp_path):
    from test_kb_flow import _ack
    from infermatrix_copilot.knowledge_service.signing import generate_private_key, load_public_key, public_key_text

    rt, lifecycle, origin = _setup(tmp_path)
    publisher = generate_private_key(tmp_path / "pub.pem")
    rt.publisher_public_key = load_public_key(public_key_text(publisher.public_key()))
    head = _open_human_pr(rt, origin, 80, {"knowledge/tools/u.md": "u\n"}, labels=("kb:human-approved",))
    rt.github.reviews[80] = [{"id": 1, "state": "APPROVED", "commit_id": head, "user": {"login": "alice"}}]
    poll_external(rt)
    (cs,) = [c for c in rt.ledger.changesets("demo", ("pr_open",)) if c["kind"] == "external"]
    merge.advance(rt, lifecycle)
    rt.ledger.update_changeset(cs["id"], status="verdict_posted", pending_item=None)
    rt.github.statuses[head] = "success"
    merge.advance(rt, lifecycle)                                  # enqueue issued
    rt.github.reviews[80].append({"id": 2, "state": "DISMISSED", "commit_id": head, "user": {"login": "alice"}})
    merge.advance(rt, lifecycle)                                  # the first pause, issued now
    start = rt.clock()
    rt.clock = lambda: start + 30 * 60 + merge.CLOCK_SKEW + 1
    rt.outbox._clock = rt.clock                                   # items are stamped by the outbox clock
    _ack(tmp_path, rt, publisher, kind="pause", changeset_id=cs["id"], ok=True)   # its ack arrives late
    assert rt.ledger.changeset(cs["id"])["status"] == "verdict_posted"
    merge.advance(rt, lifecycle)                                  # a pause issued after the boundary
    _ack(tmp_path, rt, publisher, kind="pause", changeset_id=cs["id"], ok=True)
    assert rt.ledger.changeset(cs["id"])["status"] == "approval_withdrawn"


def test_a_missing_enqueue_expiry_is_recovered_from_the_outbox(tmp_path):
    from test_kb_flow import _ack
    from infermatrix_copilot.knowledge_service.signing import generate_private_key, load_public_key, public_key_text

    rt, lifecycle, origin = _setup(tmp_path)
    publisher = generate_private_key(tmp_path / "pub.pem")
    rt.publisher_public_key = load_public_key(public_key_text(publisher.public_key()))
    head = _open_human_pr(rt, origin, 90, {"knowledge/tools/t.md": "t\n"}, labels=("kb:human-approved",))
    rt.github.reviews[90] = [{"id": 1, "state": "APPROVED", "commit_id": head, "user": {"login": "alice"}}]
    poll_external(rt)
    (cs,) = [c for c in rt.ledger.changesets("demo", ("pr_open",)) if c["kind"] == "external"]
    merge.advance(rt, lifecycle)
    rt.ledger.update_changeset(cs["id"], status="verdict_posted", pending_item=None)
    rt.github.statuses[head] = "success"
    merge.advance(rt, lifecycle)                                  # enqueue issued
    detail = rt.ledger.changeset(cs["id"])["detail"]
    detail.pop("enqueue_expires_at")                              # a restart lost the recorded expiry
    rt.ledger.update_changeset(cs["id"], detail=detail, pending_item=None)
    rt.github.reviews[90].append({"id": 2, "state": "DISMISSED", "commit_id": head, "user": {"login": "alice"}})
    merge.advance(rt, lifecycle)
    assert rt.ledger.changeset(cs["id"])["detail"]["enqueue_expires_at"] > 0   # from the signed outbox item
    _ack(tmp_path, rt, publisher, kind="pause", changeset_id=cs["id"], ok=True)
    assert rt.ledger.changeset(cs["id"])["status"] == "verdict_posted"         # not final yet
