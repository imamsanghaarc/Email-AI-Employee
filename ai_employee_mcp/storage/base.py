"""Storage interface.

The MCP server talks only to these types. Two implementations exist: an
in-memory one for tests and local development, and a Supabase/Postgres one for
production. Keeping the port narrow is what lets the whole test suite run with
no database and no network.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol


def utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class User:
    id: str
    email: str
    password_hash: str
    is_active: bool = True
    created_at: datetime = field(default_factory=utcnow)
    failed_logins: int = 0
    locked_until: datetime | None = None


@dataclass(slots=True)
class Session:
    token_jti: str
    user_id: str
    issued_at: datetime
    expires_at: datetime
    revoked: bool = False


@dataclass(slots=True)
class StoredCredential:
    id: str
    user_id: str
    provider: str
    fields: dict[str, str]
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class Approval:
    id: str
    user_id: str
    action: str
    summary: str
    status: str = "pending"
    created_at: datetime = field(default_factory=utcnow)
    decided_at: datetime | None = None
    decided_by: str | None = None

    def is_expired(self, timeout_seconds: int) -> bool:
        if self.decided_at is not None:
            return False
        return utcnow() > self.created_at + timedelta(seconds=timeout_seconds)


class Storage(Protocol):
    async def create_user(self, email: str, password_hash: str) -> User: ...

    async def get_user_by_email(self, email: str) -> User | None: ...

    async def get_user(self, user_id: str) -> User | None: ...

    async def record_failed_login(self, user_id: str, locked_until: datetime | None) -> None: ...

    async def create_session(self, session: Session) -> None: ...

    async def get_session(self, token_jti: str) -> Session | None: ...

    async def revoke_session(self, token_jti: str) -> None: ...

    async def upsert_credential(
        self, user_id: str, provider: str, fields: dict[str, str]
    ) -> StoredCredential: ...

    async def get_credential(self, user_id: str, provider: str) -> StoredCredential | None: ...

    async def list_credential_providers(self, user_id: str) -> list[str]: ...

    async def delete_credential(self, user_id: str, provider: str) -> bool: ...

    async def create_approval(self, approval: Approval) -> Approval: ...

    async def get_approval(self, approval_id: str) -> Approval | None: ...

    async def list_approvals(self, user_id: str) -> list[Approval]: ...

    async def decide_approval(
        self, approval_id: str, status: str, decided_by: str
    ) -> Approval | None: ...

    async def append_audit(
        self,
        user_id: str | None,
        action: str,
        outcome: str,
        detail: dict[str, Any] | None = None,
    ) -> None: ...