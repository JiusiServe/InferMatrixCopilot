"""Review subsystem: cheap deterministic diff summarization, conditional
trigger evaluation, and the fail-closed patch reviewer. Re-exports the public
surface (`DiffSummary`/`build_diff_summary`, `evaluate_triggers`,
`ReviewVerdict`/`run_patch_review`) so callers import from the package, not its
modules."""

from .diff_summary import DiffSummary, build_diff_summary  # noqa: F401
from .triggers import evaluate_triggers  # noqa: F401
from .reviewer import ReviewVerdict, run_patch_review  # noqa: F401
