"""Global maximum-weight one-to-one prediction/GT matching."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MatchEdge:
    prediction_id: str
    gt_id: str
    weight: float


def maximum_weight_matching(
    prediction_ids: list[str],
    gt_ids: list[str],
    edges: list[MatchEdge],
    *,
    min_weight: float = 0.0,
) -> list[MatchEdge]:
    """Solve rectangular assignment with dummy rows/columns via Hungarian algorithm."""
    if not prediction_ids or not gt_ids:
        return []
    p_index = {value: index for index, value in enumerate(prediction_ids)}
    g_index = {value: index for index, value in enumerate(gt_ids)}
    size = max(len(prediction_ids), len(gt_ids))
    weights = [[0.0 for _ in range(size)] for _ in range(size)]
    edge_lookup: dict[tuple[int, int], MatchEdge] = {}
    for edge in edges:
        if edge.prediction_id not in p_index or edge.gt_id not in g_index or edge.weight < min_weight:
            continue
        i, j = p_index[edge.prediction_id], g_index[edge.gt_id]
        if edge.weight > weights[i][j]:
            weights[i][j] = edge.weight
            edge_lookup[(i, j)] = edge

    max_weight = max((value for row in weights for value in row), default=0.0)
    cost = [[max_weight - value for value in row] for row in weights]

    # Hungarian algorithm for minimum-cost square assignment, 1-indexed internals.
    u = [0.0] * (size + 1)
    v = [0.0] * (size + 1)
    p = [0] * (size + 1)
    way = [0] * (size + 1)
    for i in range(1, size + 1):
        p[0] = i
        j0 = 0
        minv = [float("inf")] * (size + 1)
        used = [False] * (size + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = float("inf")
            j1 = 0
            for j in range(1, size + 1):
                if used[j]:
                    continue
                current = cost[i0 - 1][j - 1] - u[i0] - v[j]
                if current < minv[j]:
                    minv[j] = current
                    way[j] = j0
                if minv[j] < delta:
                    delta = minv[j]
                    j1 = j
            for j in range(size + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break

    result: list[MatchEdge] = []
    for j in range(1, size + 1):
        i = p[j] - 1
        column = j - 1
        edge = edge_lookup.get((i, column))
        if edge is not None and edge.weight >= min_weight:
            result.append(edge)
    return sorted(result, key=lambda edge: prediction_ids.index(edge.prediction_id))
