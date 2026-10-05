"""In-memory Storage implementation.

Used by the test suite and by `ai-employee-mcp dev`. It enforces the same
uniqueness and lookup rules as the Postgres adapter so tests cannot pass against
semantics production will not have.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from .base import Approval, Session, StoredCredential, User, utcnow


class DuplicateEmailError(Exception):
    pass


class InMemoryStorage:
    def __init__(self, max_audit_entries: int = 1000, audit_truncate_chars: int = 2000) -> None:
        self._lock = asyncio.Lock()
        self.users_by_id: dict[str, User] = {}
        self.user_ids_by_email: dict[str, str] = {}
        self.sessions: dict[str, Session] = {}
        self.credentials: dict[tuple[str, str], StoredCredential] = {}
        self.approvals: dict[str, Approval] = {}
        self.audit_log: list[dict[str, Any]] = []
        self._max_audit = max_audit_entries
        self._audit_trunc = audit_truncate_chars
        self._counter = 0

    def _next_id(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}_{self._counter:08d}"

    async def create_user(self, email: str, password_hash: str) -> User:
        async with self._lock:
            normalized = email.strip().lower()
            if normalized in self.user_ids_by_email:
                raise DuplicateEmailError(normalized)
            user = User(
                id=self._next_id("usr"),
                email=normalized,
                password_hash=password_hash,
            )
            self.users_by_id[user.id] = user
            self.user_ids_by_email[normalized] = user.id
            return user

    async def get_user_by_email(self, email: str) -> User | None:
        normalized = email.strip().lower()
        async with self._lock:
            user_id = self.user_ids_by_email.get(normalized)
            return self.users_by_id.get(user_id) if user_id else None

    async def get_user(self, user_id: str) -> User | None:
        async with self._lock:
            return self.users_by_id.get(user_id)

    async def record_failed_login(
        self, user_id: str, locked_until: datetime | None
    ) -> None:
        async with self._lock:
            user = self.users_by_id.get(user_id)
            if user is None:
                return
            user.failed_logins += 1
            user.locked_until = locked_until

    async def reset_failed_logins(self, user_id: str) -> None:
        async with self._lock:
            user = self.users_by_id.get(user_id)
            if user is not None:
                user.failed_logins = 0
                user.locked_until = None

    async def create_session(self, session: Session) -> None:
        async with self._lock:
            self.sessions[session.token_jti] = session

    async def get_session(self, token_jti: str) -> Session | None:
        async with self._lock:
            return self.sessions.get(token_jti)

    async def revoke_session(self, token_jti: str) -> None:
        async with self._lock:
            session = self.sessions.get(token_jti)
            if session is not None:
                session.revoked = True

    async def upsert_credential(
        self, user_id: str, provider: str, fields: dict[str, str]
    ) -> StoredCredential:
        async with self._lock:
            key = (user_id, provider)
            existing = self.credentials.get(key)
            if existing is None:
                existing = StoredCredential(
                    id=self._next_id("cred"),
                    user_id=user_id,
                    provider=provider,
                    fields={},
                )
                self.credentials[key] = existing
            existing.fields = dict(fields)
            existing.updated_at = utcnow()
            return existing

    async def get_credential(self, user_id: str, provider: str) -> StoredCredential | None:
        async with self._lock:
            return self.credentials.get((user_id, provider))

    async def list_credential_providers(self, user_id: str) -> list[str]:
        async with self._lock:
            return sorted(p for (uid, p) in self.credentials if uid == user_id)

    async def delete_credential(self, user_id: str, provider: str) -> bool:
        async with self._lock:
            return self.credentials.pop((user_id, provider), None) is not None

    async def create_approval(self, approval: Approval) -> Approval:
        async with self._lock:
            self.approvals[approval.id] = approval
            return approval

    async def get_approval(self, approval_id: str) -> Approval | None:
        async with self._lock:
            return self.approvals.get(approval_id)

    async def list_approvals(self, user_id: str) -> list[Approval]:
        async with self._lock:
            return [a for a in self.approvals.values() if a.user_id == user_id]

    async def decide_approval(
        self, approval_id: str, status: str, decided_by: str
    ) -> Approval | None:
        async with self._lock:
            approval = self.approvals.get(approval_id)
            if approval is None:
                return None
            approval.status = status
            approval.decided_at = utcnow()
            approval.decided_by = decided_by
            return approval

    async def append_audit(
        self,
        user_id: str | None,
        action: str,
        outcome: str,
        detail: dict[str, Any] | None = None,
    ) -> None:
        detail = dict(detail or {})
        if self._audit_trunc:
            for k, v in list(detail.items()):
                if isinstance(v, str) and len(v) > self._audit_trunc:
                    detail[k] = v[: self._audit_trunc]
        async with self._lock:
            self.audit_log.append(
                {
                    "at": utcnow().isoformat(),
                    "user_id": user_id,
                    "action": action,
                    "outcome": outcome,
                    "detail": detail,
                }
            )
            if len(self.audit_log) > self._max_audit:
                self.audit_log = self.audit_log[-self._max_audit :]