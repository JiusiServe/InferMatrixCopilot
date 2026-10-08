"""Shared amount rules and reservation lifetime; storage and policy stay local."""
from contextlib import contextmanager
import math


def request_cost_bound(input_bytes, input_price, output_tokens, output_price, *, cache_factor=1.25, threshold=0.0):
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0
           for v in (input_bytes, input_price, output_tokens, output_price, cache_factor, threshold)):
        raise ValueError("cost bounds require finite nonnegative amounts")
    return threshold + (input_bytes * cache_factor * input_price + output_tokens * output_price) / 1_000_000


def reservation_fits(limit, settled, reserved, requested, *, tolerance=1e-12):
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0
           for v in (settled, reserved, requested)):
        raise ValueError("budget amounts must be finite and nonnegative")
    return limit is None or settled + reserved + requested <= limit + tolerance


def settlement_charge(reserved, actual=None, *, outcome="completed", fixed_accounting=False):
    known = not isinstance(actual, bool) and isinstance(actual, (int, float)) and math.isfinite(actual) and actual >= 0
    if outcome != "completed" or fixed_accounting or not known:
        return max(reserved, actual if known else 0)
    return float(actual)


def valid_token_counts(*counts):
    return all(type(value) is int and value >= 0 for value in counts)


@contextmanager
def reserved_call(acquire, finish):
    """Acquire durably before yielding; always finalize, with execution outside locks.

    Callers mark ``sent`` immediately before dispatch and record a trusted
    ``actual_usd``/``outcome`` as soon as billing is known. The finish callback
    owns atomic, idempotent persistence and its domain's refusal exceptions.
    """
    call = {"reservation": acquire(), "sent": False, "actual_usd": None, "outcome": "unknown"}
    try:
        yield call
    finally:
        finish(call)
