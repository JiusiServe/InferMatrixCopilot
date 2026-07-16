"""Finding-micro valid precision."""

from __future__ import annotations

from ..adjudication.models import AdjudicationRow, FinalStatus
from .common import safe_div

_VALID = {FinalStatus.MATCHED_GT, FinalStatus.VALID_PARTIAL, FinalStatus.VALID_NEW}


def valid_precision(rows: list[AdjudicationRow]) -> float | None:
    return safe_div(sum(row.final_status in _VALID for row in rows), len(rows))
