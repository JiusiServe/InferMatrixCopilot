"""Spend accounting for ``kb init`` (design kb-init §10 "Budget").

A stage's ``budget_usd`` is a hard ceiling. A generator call is handed a spend
threshold (``generator_call_usd``) that its transport honours, but the claude
CLI checks it only after each API request completes, so a call can overshoot by
one request. Every call therefore RESERVES, before it is dispatched,

    threshold + worst_request
    worst_request = input_bytes * 1.25 * in_price + max_output_tokens * out_price

where input bytes upper-bound input tokens (bytes, never chars/4) and 1.25
covers cache-write pricing. The call runs only if the reservation fits in
what is left; afterwards the reported cost replaces it (the whole reservation
when the cost is unknown or the call failed). A generator model without a
price is refused (fail closed).

Judge calls go through a subscription transport with no per-call price; they
count a fixed ``judge_call_usd`` each. That part is an accounting convention,
not a spend bound.
"""

from __future__ import annotations

import json
import math
import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, Mapping

PRICES_ENV = "KB_INIT_PRICES"
CACHE_WRITE_FACTOR = 1.25


@dataclass(frozen=True)
class Price:
    in_usd_per_mtok: float
    out_usd_per_mtok: float
    max_output_tokens: int


# Anthropic list prices, cached 2026-09-25. Override or extend with
# KB_INIT_PRICES='{"<model>": [in_usd_per_mtok, out_usd_per_mtok, max_output_tokens]}'.
DEFAULT_PRICES: dict[str, Price] = {
    "claude-opus-5-5": Price(4.00, 20.00, 128_000),
}


class BudgetExhausted(RuntimeError):
    """A reservation does not fit in what is left of the stage's budget."""


class PriceError(ValueError):
    """The price table is malformed, or has no entry for a model."""


def _price(model: str, raw: object) -> Price:
    if not isinstance(raw, list) or len(raw) != 3:
        raise PriceError(f"{PRICES_ENV}[{model}] must be [in, out, max_output_tokens]")
    in_price, out_price, max_out = raw
    for value in (in_price, out_price):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) \
                or value < 0:
            raise PriceError(f"{PRICES_ENV}[{model}] prices must be finite numbers >= 0")
    if isinstance(max_out, bool) or not isinstance(max_out, int) or max_out < 1:
        raise PriceError(f"{PRICES_ENV}[{model}] max_output_tokens must be an integer >= 1")
    return Price(float(in_price), float(out_price), max_out)


def load_prices(environ: Mapping[str, str] | None = None) -> dict[str, Price]:
    """The default table, with ``KB_INIT_PRICES`` entries added or overriding."""
    environ = os.environ if environ is None else environ
    prices = dict(DEFAULT_PRICES)
    raw = environ.get(PRICES_ENV, "").strip()
    if not raw:
        return prices
    try:
        data = json.loads(raw)
    except ValueError as exc:
        raise PriceError(f"{PRICES_ENV} is not JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise PriceError(f"{PRICES_ENV} must be a JSON object")
    for model, value in data.items():
        prices[str(model)] = _price(str(model), value)
    return prices


def price_for(prices: Mapping[str, Price], model: str) -> Price:
    try:
        return prices[model]
    except KeyError:
        raise PriceError(f"no price for generator model {model!r}; add it to {PRICES_ENV}") from None


def worst_request_usd(price: Price, input_bytes: int) -> float:
    """The most one request can cost: every input byte a token (at the
    cache-write rate) plus a full-length reply."""
    if input_bytes < 0:
        raise ValueError("input_bytes must be >= 0")
    return (input_bytes * CACHE_WRITE_FACTOR * price.in_usd_per_mtok
            + price.max_output_tokens * price.out_usd_per_mtok) / 1_000_000


def generator_reservation(price: Price, threshold_usd: float, input_bytes: int) -> float:
    return threshold_usd + worst_request_usd(price, input_bytes)


class Reservation:
    """One reserved amount; ``charge`` records what the call actually cost."""

    def __init__(self, amount: float):
        self.amount = amount
        self.charged: float | None = None

    def charge(self, actual: float | None) -> None:
        """Record the call's cost; None (unknown) charges the full reservation.
        A reported cost above the reservation is charged as reported."""
        if actual is None or isinstance(actual, bool) or not isinstance(actual, (int, float)) \
                or not math.isfinite(actual) or actual < 0:
            self.charged = self.amount
        else:
            self.charged = float(actual)


class Budget:
    """What a stage may still spend. Not thread-safe (stages call models one
    at a time)."""

    def __init__(self, limit_usd: float, *, spent_usd: float = 0.0):
        if not math.isfinite(limit_usd) or limit_usd <= 0:
            raise ValueError("limit_usd must be a finite number > 0")
        if not math.isfinite(spent_usd) or spent_usd < 0:
            raise ValueError("spent_usd must be a finite number >= 0")
        self.limit_usd = float(limit_usd)
        self.spent_usd = float(spent_usd)
        self._reserved = 0.0

    @property
    def remaining_usd(self) -> float:
        return self.limit_usd - self.spent_usd - self._reserved

    @contextmanager
    def reserve(self, amount: float) -> Iterator[Reservation]:
        """Hold ``amount`` for one call. Raises ``BudgetExhausted`` before the
        call when it does not fit. On exit the charge (or, when the block did
        not charge, e.g. because the call raised, the whole reservation) is
        added to what was spent."""
        if not math.isfinite(amount) or amount < 0:
            raise ValueError("a reservation must be a finite number >= 0")
        if amount > self.remaining_usd + 1e-12:
            raise BudgetExhausted(
                f"reserving ${amount:.4f} would exceed the budget "
                f"(spent ${self.spent_usd:.4f} of ${self.limit_usd:.2f})")
        reservation = Reservation(amount)
        self._reserved += amount
        try:
            yield reservation
        finally:
            self._reserved -= amount
            self.spent_usd += reservation.charged if reservation.charged is not None else amount
