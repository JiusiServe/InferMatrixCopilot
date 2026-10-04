"""The engine's statistics (design §8): paired, item-clustered effect sizes
with t intervals (ported from ``eval/dataset/paired_analysis.py`` — the
campaign learned the hard way that raw means across judgment sets drift by
±.08 on identical reviews), the item count an effect needs, the five
experiment labels, and Cohen's kappa for calibrating a judge against human
labels.
"""

from __future__ import annotations

import math
import statistics as st
from dataclasses import dataclass, field

# two-sided 95% t critical values by degrees of freedom (df >= 30 -> 1.96)
_T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306,
        9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131,
        16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086, 25: 2.060, 30: 2.042}
Z_ALPHA = 1.96    # two-sided 95%
Z_POWER = 0.84    # 80% power
MIN_ITEMS = 8
LABELS = ("supported", "refuted", "neutral", "underpowered", "invalid")


def t95(df: int) -> float:
    if df in _T95:
        return _T95[df]
    for k in sorted(_T95):
        if df <= k:
            return _T95[k]
    return 1.96


@dataclass
class PairedResult:
    metric: str
    n_items: int
    n_verdicts: int
    mean: float = 0.0
    lo: float = 0.0
    hi: float = 0.0
    sd: float = 0.0
    per_item: dict[str, float] = field(default_factory=dict)


def paired(deltas_by_item: dict[str, list[float]], metric: str = "") -> PairedResult:
    """``arm - incumbent`` paired inside each verdict, replicates averaged per
    item, the 95% t interval taken over items (df = n_items - 1)."""
    per_item = {k: st.mean(v) for k, v in deltas_by_item.items() if v}
    vals = list(per_item.values())
    n_verdicts = sum(len(v) for v in deltas_by_item.values())
    if len(vals) < 2:
        return PairedResult(metric, len(vals), n_verdicts, mean=vals[0] if vals else 0.0, per_item=per_item)
    m = st.mean(vals)
    sd = st.stdev(vals)
    h = t95(len(vals) - 1) * sd / math.sqrt(len(vals))
    return PairedResult(metric, len(vals), n_verdicts, mean=m, lo=m - h, hi=m + h, sd=sd, per_item=per_item)


def items_required(sd_item: float, min_effect: float, *, alpha_z: float = Z_ALPHA, power_z: float = Z_POWER) -> int:
    """Items needed to resolve ``min_effect`` at 95%/80% given the item-level
    sd of the paired delta; at least MIN_ITEMS."""
    if min_effect <= 0:
        raise ValueError("min_effect must be positive")
    n = ((alpha_z + power_z) * sd_item / min_effect) ** 2
    return max(MIN_ITEMS, math.ceil(n))


def label(result: PairedResult, *, n_required: int, direction: str = "higher",
          invalid: bool = False) -> str:
    """The pre-registered decision rule over the interval and the power the
    retained items actually give."""
    if invalid or result.n_items < MIN_ITEMS:
        return "invalid"
    if result.n_items < n_required:
        return "underpowered"
    # a "lower is better" metric is judged on the mirrored interval [-hi, -lo]
    lo, hi = (result.lo, result.hi) if direction == "higher" else (-result.hi, -result.lo)
    if lo > 0:
        return "supported"
    if hi < 0:
        return "refuted"
    return "neutral"


def cohen_kappa(a: list[str], b: list[str]) -> float:
    """Agreement between two labelings of the same cells, chance-corrected."""
    if len(a) != len(b) or not a:
        raise ValueError("kappa needs two equal, non-empty label lists")
    n = len(a)
    cats = sorted(set(a) | set(b))
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    if pe >= 1.0:
        return 1.0
    return (po - pe) / (1 - pe)
