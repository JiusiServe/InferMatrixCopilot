from eval.pr_review.adjudication.jury import run_position_swapped_jury
from eval.pr_review.adjudication.models import JudgeVote


class Judge:
    def __init__(self, judge_id, decision, family=None):
        self.judge_id = judge_id
        self.model_family = family or judge_id
        self.decision = decision

    def decide(self, *, task, payload, position):
        return JudgeVote(
            judge_id=self.judge_id,
            model_family=self.model_family,
            position=position,
            decision=self.decision,
            confidence=0.9,
            rationale="ok",
        )


def test_standard_six_vote_gate_requires_five():
    result = run_position_swapped_jury(
        [Judge("a", "MATCH"), Judge("b", "MATCH"), Judge("c", "NO_MATCH")],
        task="x",
        payload={},
    )
    assert result.decision is None
    result = run_position_swapped_jury(
        [Judge("a", "MATCH"), Judge("b", "MATCH"), Judge("c", "MATCH")],
        task="x",
        payload={},
    )
    assert result.decision == "MATCH"
    assert len(result.votes) == 6

def test_single_model_position_swap_can_reach_consensus():
    result = run_position_swapped_jury(
        [Judge("only", "MATCH")],
        task="x",
        payload={},
        required_votes=2,
    )
    assert result.decision == "MATCH"
    assert len(result.votes) == 2
