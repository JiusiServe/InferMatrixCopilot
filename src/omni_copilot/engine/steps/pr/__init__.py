"""PR-facing steps package: guarded push, diff/gate fetch, PR rebase (design
task 9), PR debug (task 10), and gated review posting.

Importing this package imports each submodule for its `@step`/`register_step`
side effects. This was one 484-line module; it is now split by concern —
`fetch` (read-only fetches), `rebase` (checkout, rebase, analyze, verify),
`debug` (CI-failure collection, grouping, fix), `publish` (guarded push + review
comment), and `utils` (the pure signature extractor). `extract_signature` is
re-exported so the pre-split import path (used by tests) is unchanged.
"""

from __future__ import annotations

from . import debug, fetch, publish, rebase  # noqa: F401 (side-effect: registration)
from .utils import extract_signature  # noqa: F401

__all__ = ["extract_signature"]
