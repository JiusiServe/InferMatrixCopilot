"""Transport-neutral RFC identities and errors; no provider or server imports."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

SESSION_TTL_SECONDS = 30 * 24 * 60 * 60


class RFCError(Exception):
    def __init__(self, message: str, status: int = 400, code: str = "invalid_request"):
        super().__init__(message)
        self.status = status
        self.code = code


class ProviderError(RFCError):
    def __init__(self, message: str = "Source provider unavailable", *, uncertain: bool = False):
        super().__init__(message, 502, "outcome_unknown" if uncertain else "provider_failure")
        self.uncertain = uncertain


@dataclass(frozen=True)
class Principal:
    user_id: str
    name: str
    admin: bool = False
    credential_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceRef:
    provider: str
    repository: str = ""
    kind: str = "issue"
    identifier: str = ""
    url: str = ""
    path: str = ""
    host: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> SourceRef:
        if not isinstance(value, dict) or not value.get("provider"):
            raise RFCError("A source provider is required")
        allowed = set(cls.__dataclass_fields__)
        if set(value) - allowed:
            raise RFCError("Unknown source fields")
        return cls(**{key: str(val) for key, val in value.items() if val is not None})

    def identity(self) -> str:
        return "|".join((self.provider, self.host, self.repository, self.kind,
                         self.identifier or self.path or self.url))
