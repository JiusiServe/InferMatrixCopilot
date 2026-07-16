from eval.pr_review.adjudication.bipartite_matcher import MatchEdge, maximum_weight_matching


def test_global_matching_beats_greedy_choice():
    # Greedy would take P1-G1=.9 and leave P2-G2=.1; optimum is .8+.8.
    edges = [
        MatchEdge("P1", "G1", 0.9),
        MatchEdge("P1", "G2", 0.8),
        MatchEdge("P2", "G1", 0.8),
        MatchEdge("P2", "G2", 0.1),
    ]
    result = maximum_weight_matching(["P1", "P2"], ["G1", "G2"], edges)
    assert {(edge.prediction_id, edge.gt_id) for edge in result} == {("P1", "G2"), ("P2", "G1")}


def test_matching_can_leave_nodes_unmatched():
    result = maximum_weight_matching(
        ["P1", "P2"], ["G1"], [MatchEdge("P1", "G1", 0.7)], min_weight=0.5
    )
    assert result == [MatchEdge("P1", "G1", 0.7)]
