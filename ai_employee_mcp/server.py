"""The unified AI Employee MCP server.

One FastMCP application exposing auth, credential custody, guardrails and
provider tools. It serves stdio (local agents) and streamable HTTP (Cloud Run)
from the same tool definitions, because Cloud Run does not support stdio.

There is no LLM in this module or anywhere below it. All reasoning belongs to the
connecting agent; this process only performs I/O.
"""

from __future__ import annotations

import functools
import os
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from . import errors
from .auth.passwords import (
    hash_password,
    validate_password_strength,
    verify_password,
)
from .auth.tokens import TokenError, decode_token, issue_token
from .config import Settings, get_settings
from .credentials import CredentialManager
from .crypto import CredentialCipher, constant_time_equals
from .errors import (
    ApprovalRequired,
    AuthenticationRequired,
    CredentialsRequired,
    ProviderError,
    ToolError,
    ValidationError,
    ok,
)
from .providers.odoo import build_client, validate_model_name
from .storage.base import Approval, Session, Storage, User, utcnow
from .storage.memory import DuplicateEmailError, InMemoryStorage

SERVER_NAME = "ai-employee-mcp"


@dataclass
class AppState:
    settings: Settings
    storage: Storage
    cipher: CredentialCipher
    credentials: CredentialManager

    @classmethod
    def build(cls, settings: Settings | None = None, storage: Storage | None = None) -> AppState:
        resolved = settings or get_settings()
        store = storage or InMemoryStorage()
        cipher = CredentialCipher(resolved.resolved_master_key())
        return cls(
            settings=resolved,
            storage=store,
            cipher=cipher,
            credentials=CredentialManager(store, cipher),
        )


_state: AppState | None = None


def configure(state: AppState | None = None) -> AppState:
    global _state
    if state is not None:
        _state = state
    if _state is None:
        _state = AppState.build()
    return _state


def get_state() -> AppState:
    return _state or configure()


mcp = FastMCP(SERVER_NAME, instructions=(
    "Connect this user's own Odoo, Gmail and LinkedIn accounts. "
    "If a tool returns status='credentials_required', ask the user for the "
    "listed fields and call save_credentials, then retry the original call. "
    "If a tool returns status='approval_required', a human must approve the "
    "action: poll approval_status and retry only once it reports 'approved'."
))


def _token_from_context(ctx: Context | None) -> str | None:
    state = get_state()
    if ctx is not None:
        try:
            headers = ctx.request_context.request.headers
            header = headers.get("authorization") or headers.get("Authorization")
            if header and header.lower().startswith("bearer "):
                return header.split(" ", 1)[1].strip()
        except Exception:  # noqa: BLE001, S110 - ignore malformed headers
            pass
    if state.settings.static_token:
        return state.settings.static_token
    return None


async def current_user(ctx: Context | None) -> User:
    state = get_state()
    token = _token_from_context(ctx)
    if not token:
        raise AuthenticationRequired(
            "No bearer token supplied. Send 'Authorization: Bearer <token>' from login, "
            "or set AI_EMPLOYEE_STATIC_TOKEN for local single-user runs."
        )

    static_token = state.settings.static_token
    if static_token and constant_time_equals(token, static_token):
        user_id = state.settings.static_user_id
        if not user_id:
            raise AuthenticationRequired(
                "AI_EMPLOYEE_STATIC_TOKEN is set but AI_EMPLOYEE_STATIC_USER_ID is not, "
                "so the static token cannot be mapped to a user."
            )
        static_user = await state.storage.get_user(user_id)
        if static_user is None or not static_user.is_active:
            raise AuthenticationRequired(
                f"Static token user {user_id!r} does not exist or is disabled"
            )
        return static_user

    try:
        claims = decode_token(token, state.settings.resolved_jwt_secret())
    except TokenError as exc:
        raise AuthenticationRequired(str(exc)) from exc

    session = await state.storage.get_session(claims.jti)
    if session is None or session.revoked:
        raise AuthenticationRequired("Session not found or has been revoked")
    if session.expires_at <= utcnow():
        raise AuthenticationRequired("Session has expired")

    user = await state.storage.get_user(claims.user_id)
    if user is None or not user.is_active:
        raise AuthenticationRequired("Account not found or disabled")
    return user


async def _audit(user_id: str | None, action: str, outcome: str, **detail: Any) -> None:
    await get_state().storage.append_audit(user_id, action, outcome, detail or None)


def _tool(fn):
    @functools.wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await fn(*args, **kwargs)
        except CredentialsRequired as exc:
            return exc.payload()
        except AuthenticationRequired as exc:
            return exc.payload()
        except ApprovalRequired as exc:
            return exc.payload()
        except ToolError as exc:
            return exc.payload()
        except ProviderError as exc:
            return exc.payload()

    return wrapper


# --- auth --------------------------------------------------------------------


@mcp.tool()
@_tool
async def register(email: str, password: str) -> dict[str, Any]:
    """Create an account and return a session token."""
    state = get_state()
    normalized = email.strip().lower()
    if "@" not in normalized or "." not in normalized.split("@")[-1]:
        raise ValidationError(f"{email!r} is not a valid email address")
    validate_password_strength(password)
    try:
        user = await state.storage.create_user(normalized, hash_password(password))
    except DuplicateEmailError as exc:
        raise ValidationError("That email is already registered") from exc

    token, claims = issue_token(
        user.id, state.settings.resolved_jwt_secret(), state.settings.session_ttl_seconds
    )
    await state.storage.create_session(
        Session(
            token_jti=claims.jti,
            user_id=user.id,
            issued_at=utcnow(),
            expires_at=claims.expires_at,
        )
    )
    await _audit(user.id, "auth.register", "ok")
    return ok(user_id=user.id, email=user.email, token=token, expires_at=claims.expires_at)


@mcp.tool()
@_tool
async def login(email: str, password: str) -> dict[str, Any]:
    """Exchange email and password for a session token."""
    state = get_state()
    normalized = email.strip().lower()
    user = await state.storage.get_user_by_email(normalized)

    if user is None:
        await _audit(None, "auth.login", "unknown_email", email=normalized)
        raise AuthenticationRequired("Invalid email or password")
    if not verify_password(user.password_hash, password):
        locked_until = None
        if user.failed_logins + 1 >= state.settings.login_max_attempts:
            locked_until = utcnow() + timedelta(seconds=state.settings.login_window_seconds)
        await state.storage.record_failed_login(user.id, locked_until)
        await _audit(user.id, "auth.login", "bad_password", failed=user.failed_logins + 1)
        raise AuthenticationRequired("Invalid email or password")
    if user.locked_until and user.locked_until > utcnow():
        await _audit(user.id, "auth.login", "locked")
        raise AuthenticationRequired("Too many failed attempts. Try again later.")

    reset = getattr(state.storage, "reset_failed_logins", None)
    if reset is not None:
        await reset(user.id)

    token, claims = issue_token(
        user.id, state.settings.resolved_jwt_secret(), state.settings.session_ttl_seconds
    )
    await state.storage.create_session(
        Session(
            token_jti=claims.jti,
            user_id=user.id,
            issued_at=utcnow(),
            expires_at=claims.expires_at,
        )
    )
    await _audit(user.id, "auth.login", "ok")
    return ok(user_id=user.id, email=user.email, token=token, expires_at=claims.expires_at)


@mcp.tool()
@_tool
async def logout(ctx: Context = None) -> dict[str, Any]:  # type: ignore[assignment]
    """Revoke the current session token."""
    state = get_state()
    token = _token_from_context(ctx)
    if token:
        try:
            claims = decode_token(token, state.settings.resolved_jwt_secret())
            await state.storage.revoke_session(claims.jti)
            await _audit(claims.user_id, "auth.logout", "ok")
        except TokenError:
            pass
    return ok()


@mcp.tool()
@_tool
async def whoami(ctx: Context = None) -> dict[str, Any]:  # type: ignore[assignment]
    """Return the authenticated user's identity and configured providers."""
    user = await current_user(ctx)
    status = await get_state().credentials.status(user.id)
    return ok(user_id=user.id, email=user.email, **status)


# --- credentials -------------------------------------------------------------


@mcp.tool()
@_tool
async def save_credentials(
    provider: str, credentials: dict[str, str], ctx: Context = None  # type: ignore[assignment]
) -> dict[str, Any]:
    """Store this user's credentials for a provider, encrypted at rest.

    Pass only the fields you want to set or change; existing fields are kept.
    Values are never returned by this or any other tool.
    """
    user = await current_user(ctx)
    result = await get_state().credentials.save(user.id, provider, credentials or {})
    return ok(**result)


@mcp.tool()
@_tool
async def credentials_status(ctx: Context = None) -> dict[str, Any]:  # type: ignore[assignment]
    """List which providers are configured and which fields each one needs."""
    user = await current_user(ctx)
    return ok(**(await get_state().credentials.status(user.id)))


@mcp.tool()
@_tool
async def disconnect_provider(
    provider: str, ctx: Context = None  # type: ignore[assignment]
) -> dict[str, Any]:
    """Delete this user's stored credentials for a provider."""
    user = await current_user(ctx)
    return ok(**(await get_state().credentials.disconnect(user.id, provider)))


# --- odoo --------------------------------------------------------------------


@mcp.tool()
@_tool
async def odoo_search_read(
    model: str,
    domain: list[Any] | None = None,
    fields: list[str] | None = None,
    limit: int = 20,
    offset: int = 0,
    ctx: Context = None,  # type: ignore[assignment]
) -> dict[str, Any]:
    """Query Odoo records with search_read. Domain is a structured list, never a string."""
    user = await current_user(ctx)
    state = get_state()
    creds = await state.credentials.resolve(user.id, "odoo")
    client = build_client(creds, state.settings.odoo_default_url)
    records = await client.search_read(model, domain, fields, limit, offset)
    await _audit(user.id, "odoo.search_read", "ok", model=model, count=len(records))
    return ok(model=model, count=len(records), records=records)
@mcp.tool()
@_tool
async def odoo_create_record(
    model: str,
    values: dict[str, Any],
    approval_id: str | None = None,
    ctx: Context = None,  # type: ignore[assignment]
) -> dict[str, Any]:
    """Create one Odoo record. Requires human approval; pass approval_id on retry."""
    user = await current_user(ctx)
    state = get_state()
    creds = await state.credentials.resolve(user.id, "odoo")
    validate_model_name(model)
    used = await resolve_approval(
        user.id,
        "odoo_create_record",
        f"Create {model} in database {creds.get('db')!r} with fields {sorted(values)}",
        approval_id,
    )
    client = build_client(creds, state.settings.odoo_default_url)
    new_id = await client.create_record(model, values)
    await _audit(
        user.id,
        "odoo.create_record",
        "ok",
        model=model,
        record_id=new_id,
        approval_id=used,
    )
    return ok(model=model, record_id=new_id, approval_id=used)


@mcp.tool()
@_tool
async def odoo_update_record(
    model: str,
    record_id: int,
    values: dict[str, Any],
    approval_id: str | None = None,
    ctx: Context = None,  # type: ignore[assignment]
) -> dict[str, Any]:
    """Update one Odoo record. Requires human approval; pass approval_id on retry."""
    user = await current_user(ctx)
    state = get_state()
    creds = await state.credentials.resolve(user.id, "odoo")
    validate_model_name(model)
    used = await resolve_approval(
        user.id,
        "odoo_update_record",
        f"Update {model} #{record_id} in database {creds.get('db')!r} "
        f"with fields {sorted(values)}",
        approval_id,
    )
    client = build_client(creds, state.settings.odoo_default_url)
    updated = await client.update_record(model, record_id, values)
    await _audit(
        user.id,
        "odoo.update_record",
        "ok",
        model=model,
        record_id=record_id,
        approval_id=used,
    )
    return ok(model=model, record_id=record_id, updated=updated, approval_id=used)


@mcp.tool()
@_tool
async def odoo_accounting_summary(ctx: Context = None) -> dict[str, Any]:  # type: ignore[assignment]
    """Summarise posted invoices, partner count and product count."""
    user = await current_user(ctx)
    state = get_state()
    creds = await state.credentials.resolve(user.id, "odoo")
    client = build_client(creds, state.settings.odoo_default_url)
    summary = await client.accounting_summary()
    await _audit(user.id, "odoo.accounting_summary", "ok")
    return ok(**summary)


# --- guardrails --------------------------------------------------------------


@mcp.tool()
@_tool
async def approval_status(approval_id: str, ctx: Context = None) -> dict[str, Any]:  # type: ignore[assignment]
    """Poll a human approval request. Status becomes approved, rejected or expired."""
    user = await current_user(ctx)
    state = get_state()
    approval = await state.storage.get_approval(approval_id)
    if approval is None or approval.user_id != user.id:
        raise ValidationError(f"No approval request {approval_id!r} for this account")
    if approval.is_expired(state.settings.approval_timeout_seconds):
        if approval.status == "pending":
            await state.storage.decide_approval(approval_id, "expired", "system")
            approval.status = "expired"
    return ok(
        approval_id=approval.id,
        action=approval.action,
        summary=approval.summary,
        status=approval.status,
        decided_by=approval.decided_by,
        decided_at=approval.decided_at,
    )


@mcp.tool()
@_tool
async def pending_approvals(ctx: Context = None) -> dict[str, Any]:  # type: ignore[assignment]
    """List this user's approval requests awaiting a human decision."""
    user = await current_user(ctx)
    state = get_state()
    out: list[dict[str, Any]] = []
    for approval in await state.storage.list_approvals(user.id):
        out.append(
            {
                "approval_id": approval.id,
                "action": approval.action,
                "summary": approval.summary,
                "status": approval.status,
                "expires_at": (
                    approval.created_at
                    + timedelta(seconds=state.settings.approval_timeout_seconds)
                ).isoformat(),
            }
        )
    return ok(approvals=out)


async def resolve_approval(
    user_id: str, action: str, summary: str, approval_id: str | None = None
) -> str | None:
    """Gate a side-effecting action behind human approval.

    Returns None when the action may proceed. Otherwise raises: either
    ApprovalRequired (a request now exists, or the one supplied is still pending)
    or ValidationError (the supplied request is not usable for this action).

    The caller must therefore expose ``approval_id`` as an optional argument so
    the agent can poll ``approval_status`` and retry. Retrying without a usable
    approval must never silently succeed.
    """
    state = get_state()
    if not state.settings.require_approval_for_side_effects:
        return None

    if approval_id:
        approval = await state.storage.get_approval(approval_id)
        if approval is None or approval.user_id != user_id:
            raise ValidationError(f"No approval request {approval_id!r} for this account")
        if approval.action != action:
            raise ValidationError(
                f"Approval {approval_id} covers {approval.action!r}, not {action!r}. "
                "Request a fresh approval for this action."
            )
        if approval.status == "pending" and approval.is_expired(
            state.settings.approval_timeout_seconds
        ):
            await state.storage.decide_approval(approval_id, "expired", "system")
            approval.status = "expired"
        if approval.status == "approved":
            await _audit(user_id, f"approval.used:{action}", "approved", approval_id=approval_id)
            return approval_id
        raise ApprovalRequired(
            action,
            approval_id,
            f"Approval {approval_id} is {approval.status!r}, so {action!r} did not run.",
        )

    approval = Approval(id=os.urandom(8).hex(), user_id=user_id, action=action, summary=summary)
    await state.storage.create_approval(approval)
    await _audit(user_id, f"approval.requested:{action}", "pending", approval_id=approval.id)
    raise ApprovalRequired(
        action,
        approval.id,
        f"'{action}' requires human approval. Request {approval.id} is waiting.",
    )


async def require_approval(user_id: str, action: str, summary: str) -> None:
    """Deprecated shim kept for callers that only need the blocking behaviour."""
    await resolve_approval(user_id, action, summary)


__all__ = [
    "AppState",
    "SERVER_NAME",
    "configure",
    "current_user",
    "errors",
    "get_state",
    "mcp",
    "require_approval",
    "resolve_approval",
    "validate_model_name",
]