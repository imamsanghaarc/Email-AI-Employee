"""Envelope encryption for third-party credentials at rest.

AES-256-GCM. Every ciphertext is bound to a caller-supplied AAD string that
identifies the owning row (``user_id:provider:field``), so an attacker who can
write to the credentials table cannot move an encrypted blob from one user's
record to another and have it decrypt.

The plaintext is never returned by any tool - only the ciphertext blob is
persisted, and decryption is confined to this module's callers.
"""

from __future__ import annotations

import base64
import hmac
import json
import os
from dataclasses import dataclass
from typing import Any

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

VERSION = b"v1"
NONCE_BYTES = 12
KEY_BYTES = 32


class DecryptionError(Exception):
    """Raised when a ciphertext fails authentication or AAD binding."""


@dataclass(frozen=True)
class SealedSecret:
    version: str
    nonce: str
    ciphertext: str

    def to_blob(self) -> str:
        return json.dumps(
            {"v": self.version, "nonce": self.nonce, "ct": self.ciphertext},
            separators=(",", ":"),
        )

    @classmethod
    def from_blob(cls, blob: str) -> SealedSecret:
        data = json.loads(blob)
        return cls(version=data["v"], nonce=data["nonce"], ciphertext=data["ct"])


class CredentialCipher:
    def __init__(self, master_key: bytes) -> None:
        if len(master_key) != KEY_BYTES:
            raise ValueError(f"master key must be {KEY_BYTES} bytes")
        self._aead = AESGCM(master_key)

    @classmethod
    def generate_master_key(cls) -> str:
        return base64.b64encode(os.urandom(KEY_BYTES)).decode("ascii")

    @staticmethod
    def build_aad(user_id: str, provider: str, field: str) -> bytes:
        return f"aemcp:{user_id}:{provider}:{field}".encode()

    def seal(self, plaintext: str, aad: bytes) -> str:
        nonce = os.urandom(NONCE_BYTES)
        ct = self._aead.encrypt(nonce, plaintext.encode("utf-8"), aad)
        return SealedSecret(
            version=VERSION.decode(),
            nonce=base64.b64encode(nonce).decode("ascii"),
            ciphertext=base64.b64encode(ct).decode("ascii"),
        ).to_blob()

    def open(self, blob: str, aad: bytes) -> str:
        sealed = SealedSecret.from_blob(blob)
        if sealed.version != VERSION.decode():
            raise DecryptionError(f"unsupported ciphertext version {sealed.version!r}")
        nonce = base64.b64decode(sealed.nonce)
        ct = base64.b64decode(sealed.ciphertext)
        try:
            plaintext = self._aead.decrypt(nonce, ct, aad)
        except InvalidTag as exc:
            raise DecryptionError(
                "ciphertext failed authentication: wrong key, or AAD does not match "
                "the owning user/provider/field"
            ) from exc
        return plaintext.decode("utf-8")

    def seal_mapping(self, values: dict[str, str], user_id: str, provider: str) -> dict[str, str]:
        return {
            field: self.seal(value, self.build_aad(user_id, provider, field))
            for field, value in values.items()
            if value is not None and value != ""
        }

    def open_mapping(self, blob: dict[str, str], user_id: str, provider: str) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for field, value in blob.items():
            out[field] = self.open(value, self.build_aad(user_id, provider, field))
        return out


def constant_time_equals(left: str, right: str) -> bool:
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))