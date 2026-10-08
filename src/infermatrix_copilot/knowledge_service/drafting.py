"""A bounded candidate attempt sequence; callers own model and repair policy."""

from __future__ import annotations


def bounded_attempts(attempt, *, max_repairs: int = 2):
    """Run ``attempt(feedback, index)`` until it returns an accepted candidate.

    Each attempt returns reply, accepted, feedback and a diagnostic. Exceptions
    propagate; an empty accepted value is distinct from the ``None`` refusal.
    A refused attempt with ``feedback=None`` ends without another dispatch.
    """
    if type(max_repairs) is not int or not 0 <= max_repairs <= 2:
        raise ValueError("max_repairs must be within 0..2")
    feedback, observations = "", []
    for index in range(max_repairs + 1):
        reply, accepted, feedback, error = attempt(feedback, index)
        if accepted is not None:
            return reply, accepted, observations
        observations.append({"attempt": index, "error": error})
        if feedback is None:
            break
    return None, None, observations
