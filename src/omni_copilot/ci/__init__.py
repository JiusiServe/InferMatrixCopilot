"""CI subsystem: failure-signature normalization and provider log enrichment.
Re-exports the public surface (`normalize_signature`, `provider_for`) so callers
import from the package, not its modules."""

from .normalize import normalize_signature  # noqa: F401
from .providers import provider_for  # noqa: F401
