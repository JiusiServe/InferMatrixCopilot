"""Shared amount rules and reservation lifetime; storage and policy stay local."""
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
import math


_CALL_BUDGETS = ContextVar("model_call_budgets", default={})


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


def usage_cost(usage, input_price, output_price, *, cache_read_factor=.1, cache_create_factor=1.25):
    """Price complete normalized token facts; missing or malformed facts stay unknown."""
    keys = ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_read_tokens",
            "cache_creation_input_tokens", "cache_creation_tokens")
    if not isinstance(usage, dict) or not valid_token_counts(usage.get("input_tokens"), usage.get("output_tokens")) \
            or not valid_token_counts(*(usage[key] for key in keys if key in usage)):
        return None
    read = usage.get("cache_read_input_tokens") or usage.get("cache_read_tokens") or 0
    create = usage.get("cache_creation_input_tokens") or usage.get("cache_creation_tokens") or 0
    return (input_price * (usage["input_tokens"] + read * cache_read_factor + create * cache_create_factor)
            + output_price * usage["output_tokens"]) / 1_000_000


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


@contextmanager
def bind_call_budget(key, acquire, finish):
    """Bind one account without changing its storage, prices or refund policy.

    An inner binding replaces the same key instead of charging it twice.
    Passing ``acquire=None`` temporarily removes that account.
    """
    bindings = dict(_CALL_BUDGETS.get())
    if acquire is None:
        bindings.pop(key, None)
    else:
        bindings[key] = (acquire, finish)
    token = _CALL_BUDGETS.set(bindings)
    try:
        yield
    finally:
        _CALL_BUDGETS.reset(token)


@contextmanager
def call_budget(request):
    """Reserve bound accounts before dispatch and report facts to each owner.

    No model selection, billing or recovery policy lives here. Owners receive
    the actual dispatch flag and unmodified usage, including unknown usage.
    Every acquired account is finalized even if another refuses or fails.
    """
    facts = {"sent": False, "reply": None, "usage": None, "outcome": "unknown"}
    with ExitStack() as stack:
        for acquire, finish in _CALL_BUDGETS.get().values():
            ticket = acquire(request)
            stack.callback(finish, ticket, facts)
        yield facts
