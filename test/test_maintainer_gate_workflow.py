"""The maintainer-gate workflow is the only thing that can say a pull request
passed the bar, so the properties that make its verdict trustworthy are pinned
here rather than left to review. Each assertion below is a way the gate could
be quietly turned into something that proves nothing.

The evaluator itself lives in JiusiServe/omni-maintainer; this file guards the
copy of the workflow that runs it here.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / ".github" / "workflows" / "maintainer-gate.yml"


@pytest.fixture(scope="module")
def text() -> str:
    return GATE.read_text()


@pytest.fixture(scope="module")
def workflow(text: str) -> dict:
    return yaml.safe_load(text)


def job(workflow: dict) -> dict:
    assert list(workflow["jobs"]) == ["gate"], "one job; a second could merge"
    return workflow["jobs"]["gate"]


def index_of(step_list: list[dict], needle: str) -> int:
    hits = [i for i, st in enumerate(step_list)
            if needle in st.get("name", "") or needle in st.get("uses", "")]
    assert len(hits) == 1, f"{needle}: {hits}"
    return hits[0]


def test_the_evaluator_is_pinned_to_one_exact_commit(text: str) -> None:
    """An unpinned install would let a push to another repository change what
    is enforced here without anyone editing this file."""
    pin = re.search(r'OMNI_MAINTAINER_SHA:\s*"([^"]*)"', text)
    assert pin, "the evaluator pin is gone"
    assert re.fullmatch(r"[0-9a-f]{40}", pin.group(1)), \
        f"the pin must be a full commit SHA, not {pin.group(1)!r}"
    install = re.search(r"pip install [^\n]*omni-maintainer@\$\{OMNI_MAINTAINER_SHA\}", text)
    assert install, "the install no longer uses the pin"
    assert "@main" not in text and "@master" not in text


def test_every_action_is_pinned_by_commit_sha(text: str) -> None:
    """A tag is mutable; whoever can move it can run their code with the gate
    App token."""
    for use in re.findall(r"uses:\s*(\S+)", text):
        assert "@" in use, use
        ref = use.split("@", 1)[1]
        assert re.fullmatch(r"[0-9a-f]{40}", ref), f"{use} is not pinned by commit SHA"


def test_the_gate_runs_the_base_branch_workflow_and_reaches_the_environment(workflow: dict) -> None:
    """pull_request_target runs the base branch's copy of this file, so the
    gate environment (restricted to main) is reachable and a head branch
    cannot substitute its own workflow."""
    on = workflow[True] if True in workflow else workflow["on"]
    assert "pull_request_target" in on
    assert "pull_request" not in on, "a pull_request trigger would run the head's workflow"
    assert job(workflow)["environment"] == "gate"


def test_the_gate_never_checks_out_pull_request_code(text: str, workflow: dict) -> None:
    """Third-party code must never execute in a job holding the App token."""
    assert "actions/checkout" not in text, "the gate reads the diff through the API"
    for step in job(workflow)["steps"]:
        run = step.get("run", "")
        assert "git checkout" not in run
        # The one clone is this repository's bare objects for revert
        # verification: no working tree, so nothing can be executed from it.
        for clone in re.findall(r"git (?:-c \S+ )?clone[^\n]*", run):
            assert "--no-checkout" in clone, clone
            assert "${GITHUB_REPOSITORY}" in clone or "$GITHUB_REPOSITORY" in clone, clone


def test_the_reviewer_never_receives_the_gate_token(workflow: dict) -> None:
    """The adversarial reviewer reads pre-fetched files and writes a verdict
    file. If it held the App token it could post its own approval."""
    review = next(s for s in job(workflow)["steps"] if s.get("uses", "").startswith("anthropics/claude-code-action"))
    assert review["with"]["github_token"] == "${{ github.token }}", \
        "the reviewer must get the read-only default token, never the App token"
    assert "steps.app.outputs.token" not in str(review)
    allowed = review["with"]["allowed_tools"]
    assert "Bash" not in allowed and "WebFetch" not in allowed, allowed
    for tool in re.findall(r"(\w+)\(([^)]*)\)", allowed):
        name, scope = tool
        expected = "verdicts/" if name == "Write" else "review-input/"
        assert scope.startswith(expected), f"{name} may reach {scope}"


def test_a_verdict_is_only_ever_posted_by_the_gate_identity(text: str) -> None:
    """The first line of the reviewer's file is parsed, not trusted: anything
    but the two exact verdicts is dropped."""
    assert r"VERDICT: *\(APPROVE\|REVISE\)" in text, \
        "the first line is no longer parsed against the two exact verdicts"
    assert "gate post-verdict" in text
    post = text[text.index("Post verdicts with the gate identity"):]
    assert "GH_TOKEN: ${{ steps.app.outputs.token }}" in post


def test_a_truncated_file_list_fails_closed(text: str) -> None:
    """The compare API lists at most 300 files on its only page. A review of a
    partial diff must not be able to approve."""
    assert '-ge 300' in text
    assert "VERDICT: REVISE" in text
    assert "forced-verdicts" in text, "the forced verdict must sit outside the reviewer's writable path"
    forced = text[text.index("forced-verdicts/$pr.md"):]
    assert 'if [ -s "forced-verdicts/$pr.md" ]' in forced, "a forced verdict must win over the reviewer's"


def test_the_workflow_can_publish_a_check_but_not_merge(workflow: dict, text: str) -> None:
    assert workflow["permissions"] == {"contents": "read"}, \
        "the default token needs nothing else; the App token carries the writes"
    assert "pr merge" not in text and "--merge" not in text, "only the arbiter merges"
    assert "gate evaluate" in text and "--publish" in text


def test_a_crashing_evaluator_leaves_no_stale_success(text: str) -> None:
    """A failing bar is a failing check; only a crash fails the job, and then
    the check is missing and the ruleset blocks the merge either way."""
    tail = text[text.index("Evaluate the bar"):]
    assert 'if [ "$code" -ge 2 ]; then rc=$code; fi' in tail
    assert "exit $rc" in tail


def test_the_concurrency_group_is_per_pull_request(workflow: dict) -> None:
    """Cancelling a running gate would leave the pending check as the newest
    run, which the ruleset reads as not passing."""
    assert workflow["concurrency"]["cancel-in-progress"] is False
    assert "pull_request.number" in workflow["concurrency"]["group"]


def test_the_pending_check_is_published_before_anything_that_can_fail(workflow: dict) -> None:
    """This workflow also runs on events that do not move the head: a dismissed
    review, a removed label, the hourly sweep. On such a run the head may
    already carry a successful maintainer-gate check. If the run then fails
    before publishing anything, that older success stays the newest run and the
    ruleset reads a crashed evaluation as a pass."""
    step_list = job(workflow)["steps"]
    pending = index_of(step_list, "Invalidate the previous verdict")
    assert index_of(step_list, "Mint the gate App token") < pending
    assert index_of(step_list, "Select pull requests") < pending
    for later in ("actions/setup-python", "Install the pinned evaluator", "Bare objects",
                  "Reviewer queue", "Fetch diffs", "Claude review", "Post verdicts", "Evaluate the bar"):
        assert pending < index_of(step_list, later), \
            f"{later} runs first, so a failure there leaves a stale pass"
    for i, step in enumerate(step_list[:pending]):
        run = step.get("run", "")
        assert "pip install" not in run and "clone" not in run, \
            f"step {i} can fail before the pending check exists"


def test_selection_reads_every_head_in_one_request(workflow: dict) -> None:
    """Reading heads one pull request at a time aborts the sweep on the first
    transient failure, and every head after it keeps the check it already had."""
    step = job(workflow)["steps"][index_of(job(workflow)["steps"], "Select pull requests")]
    select = step["run"]
    assert "number,headRefOid" in select, "the heads must come with the listing"
    assert "for pr in $numbers" not in select, "a per-pull-request head lookup is the abort path"
    assert select.count("gh pr list") + select.count("gh pr view") <= 2
    assert step["env"].get("EVENT_HEAD") == "${{ github.event.pull_request.head.sha }}", \
        "an event carrying the head needs no request at all"


def test_one_failed_invalidation_still_invalidates_the_rest_and_fails(workflow: dict) -> None:
    publish = job(workflow)["steps"][index_of(job(workflow)["steps"], "Invalidate the previous verdict")]["run"]
    assert "status=in_progress" in publish and "name=maintainer-gate" in publish
    assert "conclusion" not in publish, "a pending run must not carry a conclusion"
    assert "failed=1" in publish and 'could not invalidate' in publish
    assert '[ "$failed" = 0 ] || exit 1' in publish
    assert publish.index("done < selected.txt") < publish.index('[ "$failed" = 0 ]')


def test_only_a_deleted_file_may_be_missing_and_anything_else_fails_closed(workflow: dict) -> None:
    """A file the pull request deletes cannot be read at the head. Any other
    unreadable file means the reviewer would judge an incomplete change."""
    fetch = job(workflow)["steps"][index_of(job(workflow)["steps"], "Fetch diffs")]["run"]
    assert 'select(.status != "removed")' in fetch
    assert 'done < "review-input/$pr.readable"' in fetch
    assert "2>/dev/null || true" not in fetch, "a swallowed fetch error approves an incomplete diff"
    forced = fetch[fetch.index('if [ -n "$incomplete" ]'):]
    assert "forced-verdicts/$pr.md" in forced
    assert 'sed -i "/^$pr /d" review-input/pending.txt' in forced


def test_a_sweep_lists_every_open_pull_request(workflow: dict) -> None:
    """gh pr list stops at 30 by default, and the ones past it would keep
    whatever check they already carried."""
    select = job(workflow)["steps"][index_of(job(workflow)["steps"], "Select pull requests")]["run"]
    for listing in re.findall(r"gh pr list[^\n]*", select):
        assert int(re.search(r"--limit (\d+)", listing).group(1)) >= 1000, listing


def test_the_verdict_binds_to_the_text_the_reviewer_was_shown(text: str, workflow: dict) -> None:
    """The reviewer reads the title and description and is told to judge them.
    Both are editable without moving the head, so a verdict keyed to the head
    alone would stand after the justification it read was rewritten."""
    step_list = job(workflow)["steps"]
    post = step_list[index_of(step_list, "Post verdicts")]["run"]
    assert '--ctx "$ctx"' in post and "while read -r pr head ctx" in post
    fetch = step_list[index_of(step_list, "Fetch diffs")]["run"]
    assert "cut -d' ' -f1,2 pending.txt" in fetch, \
        "the reviewer is given the pull request and head, not the digest"
    on = workflow[True] if True in workflow else workflow["on"]
    assert "edited" in on["pull_request_target"]["types"], \
        "an edited title or description must re-run the gate"

