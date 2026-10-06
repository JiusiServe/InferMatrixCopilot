"""Ed25519 envelopes for knowledge-gate verdicts, outbox items and control records.

An envelope is ``{"payload": <object>, "key_id": <str>, "signature": <b64>}``.
The signature covers the canonical JSON of the payload (sorted keys, compact
separators, UTF-8) prefixed with a purpose tag, so a verdict signature can never
be replayed as an outbox item or a control record and vice versa.

Only ``cryptography`` beyond the standard library.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey,
)

PURPOSES = ("kb-gate-verdict", "kb-outbox-item", "kb-control", "kb-ack",
            "kb-reconciliation-plan", "kb-reviewed-reconciliation",
            "kb-reviewed-event-plan", "kb-reviewed-event-settlement")


class SignatureError(ValueError):
    """An envelope is malformed, signed for another purpose, or forged."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _message(purpose: str, payload: Any) -> bytes:
    if purpose not in PURPOSES:
        raise SignatureError(f"unknown signature purpose: {purpose}")
    return purpose.encode("ascii") + b"\0" + canonical_json(payload)


def public_key_id(public: Ed25519PublicKey) -> str:
    raw = public.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return "ed25519:" + hashlib.sha256(raw).hexdigest()[:16]


def public_key_text(public: Ed25519PublicKey) -> str:
    """The one-line form handed to the publisher (the file ``KB_SERVICE_PUBKEY`` names)."""
    raw = public.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return "ed25519 " + base64.b64encode(raw).decode("ascii")


def load_public_key(text: str) -> Ed25519PublicKey:
    parts = text.strip().split()
    if len(parts) != 2 or parts[0] != "ed25519":
        raise SignatureError("public key must be 'ed25519 <base64>'")
    try:
        return Ed25519PublicKey.from_public_bytes(base64.b64decode(parts[1], validate=True))
    except (ValueError, TypeError) as exc:
        raise SignatureError("public key is not a valid Ed25519 key") from exc


def generate_private_key(path: str | Path) -> Ed25519PrivateKey:
    """Create a new private key file readable only by its owner."""
    path = Path(path)
    if path.exists():
        raise SignatureError(f"refusing to overwrite an existing key: {path}")
    key = Ed25519PrivateKey.generate()
    data = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
    return key


def load_private_key(path: str | Path) -> Ed25519PrivateKey:
    path = Path(path)
    mode = path.stat().st_mode & 0o077
    if mode:
        raise SignatureError(f"private key must not be readable by group/others: {path}")
    key = serialization.load_pem_private_key(path.read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise SignatureError("private key is not Ed25519")
    return key


def sign(purpose: str, payload: Any, key: Ed25519PrivateKey) -> dict:
    signature = key.sign(_message(purpose, payload))
    return {
        "purpose": purpose,
        "payload": payload,
        "key_id": public_key_id(key.public_key()),
        "signature": base64.b64encode(signature).decode("ascii"),
    }


def verify(purpose: str, envelope: Any, public: Ed25519PublicKey) -> Any:
    """Return the payload of a valid envelope for ``purpose``; raise otherwise."""
    if not isinstance(envelope, dict) or set(envelope) != {"purpose", "payload", "key_id", "signature"}:
        raise SignatureError("envelope must have exactly purpose, payload, key_id and signature")
    if envelope["purpose"] != purpose:
        raise SignatureError(f"envelope is signed for {envelope['purpose']!r}, not {purpose!r}")
    if envelope["key_id"] != public_key_id(public):
        raise SignatureError("envelope was signed by a different key")
    try:
        signature = base64.b64decode(envelope["signature"], validate=True)
        public.verify(signature, _message(purpose, envelope["payload"]))
    except (InvalidSignature, ValueError, TypeError) as exc:
        raise SignatureError("signature does not verify") from exc
    return envelope["payload"]
