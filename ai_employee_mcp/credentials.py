"""Per-user credential custody.

Three rules this module enforces:

1. A tool never receives a raw secret unless it is the tool for that provider,
   and no tool ever returns one back to the caller.
2. A provider with no stored credentials raises ``CredentialsRequired``, which
   serialises into an instruction the agent can act on. This is how the
   "ask the user for credentials" experience is implemented within a protocol
   that has no interactive channel.
3. Gmail stores OAuth tokens, never a mailbox password.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .crypto import CredentialCipher
from .errors import CredentialsRequired, ProviderError, ValidationError
from .storage.base import Storage


@dataclass(frozen=True, slots=True)
class ProviderSpec:
    name: str
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...] = ()
    secret_fields: tuple[str, ...] = ()
    oauth: bool = False

    def missing(self, present: dict[str, str]) -> list[str]:
        return [f for f in self.required_fields if not present.get(f)]


ODOO = ProviderSpec(
    name="odoo",
    required_fields=("url", "db", "username", "api_key"),
    optional_fields=("api_version",),
    secret_fields=("api_key",),
)

GMAIL = ProviderSpec(
    name="gmail",
    required_fields=("client_id", "client_secret", "refresh_token"),
    secret_fields=("client_secret", "refresh_token"),
    oauth=True,
)

LINKEDIN = ProviderSpec(
    name="linkedin",
    required_fields=("email", "password"),
    secret_fields=("password",),
)

PROVIDERS: dict[str, ProviderSpec] = {p.name: p for p in (ODOO, GMAIL, LINKEDIN)}


def get_provider(name: str) -> ProviderSpec:
    spec = PROVIDERS.get(name.strip().lower())
    if spec is None:
        known = ", ".join(sorted(PROVIDERS))
        raise ValidationError(f"Unknown provider {name!r}. Known providers: {known}")
    return spec


class CredentialManager:
    def __init__(self, storage: Storage, cipher: CredentialCipher) -> None:
        self._storage = storage
        self._cipher = cipher

    async def save(
        self, user_id: str, provider_name: str, values: dict[str, Any]
    ) -> dict[str, Any]:
        spec = get_provider(provider_name)
        cleaned = {k: str(v).strip() for k, v in values.items() if v is not None and str(v).strip()}

        unknown = set(cleaned) - set(spec.required_fields) - set(spec.optional_fields)
        if unknown:
            allowed = ", ".join(spec.required_fields + spec.optional_fields)
            raise ValidationError(
                f"Unknown field(s) for {spec.name}: {', '.join(sorted(unknown))}. "
                f"Accepted fields: {allowed}"
            )

        if not cleaned:
            allowed = ", ".join(spec.required_fields + spec.optional_fields)
            raise ValidationError(
                f"No usable values supplied for {spec.name}. Accepted fields: {allowed}"
            )

        existing = await self._storage.get_credential(user_id, spec.name)
        if existing is None:
            merged: dict[str, str] = {}
        else:
            try:
                merged = self._cipher.open_mapping(existing.fields, user_id, spec.name)
            except Exception as exc:
                raise ProviderError(
                    f"Stored {spec.name} credentials could not be decrypted, so they "
                    "cannot be updated. Disconnect the provider and re-enter them."
                ) from exc
        merged.update(cleaned)

        sealed = self._cipher.seal_mapping(merged, user_id, spec.name)
        await self._storage.upsert_credential(user_id, spec.name, sealed)
        await self._storage.append_audit(
            user_id, f"credentials.save:{spec.name}", "ok", {"fields": sorted(merged)}
        )
        return {
            "provider": spec.name,
            "stored_fields": sorted(merged),
            "still_missing": spec.missing(dict.fromkeys(merged, "x")),
        }

    async def status(self, user_id: str) -> dict[str, Any]:
        configured: list[str] = []
        for name, spec in sorted(PROVIDERS.items()):
            record = await self._storage.get_credential(user_id, name)
            if record is None:
                continue
            fields = sorted(record.fields)
            missing = spec.missing(
                dict.fromkeys(fields, "x")
            )
            if not missing:
                configured.append(name)
        return {
            "configured_providers": configured,
            "available_providers": sorted(PROVIDERS),
            "required_fields": {
                name: list(spec.required_fields) for name, spec in sorted(PROVIDERS.items())
            },
        }

    async def disconnect(self, user_id: str, provider_name: str) -> dict[str, Any]:
        spec = get_provider(provider_name)
        deleted = await self._storage.delete_credential(user_id, spec.name)
        await self._storage.append_audit(
            user_id, f"credentials.delete:{spec.name}", "ok" if deleted else "not_found"
        )
        return {"provider": spec.name, "disconnected": deleted}

    async def resolve(self, user_id: str, provider_name: str) -> dict[str, str]:
        spec = get_provider(provider_name)
        record = await self._storage.get_credential(user_id, spec.name)
        present = self._cipher.open_mapping(record.fields, user_id, spec.name) if record else {}

        missing = spec.missing(present)
        if missing:
            hint = None
            if spec.oauth:
                hint = (
                    f"{spec.name} uses OAuth. Prefer completing the browser consent flow "
                    f"so the user never pastes a password. Then call save_credentials "
                    f"with {', '.join(spec.required_fields)}."
                )
            raise CredentialsRequired(spec.name, missing, hint)

        try:
            return present
        except Exception as exc:
            raise ProviderError(
                f"Stored {spec.name} credentials could not be decrypted: {exc}"
            ) from exc