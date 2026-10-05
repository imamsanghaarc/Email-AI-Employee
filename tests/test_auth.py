import time

import pytest

from ai_employee_mcp import server
from ai_employee_mcp.errors import STATUS_AUTH_REQUIRED, STATUS_OK

from .conftest import VALID_PASSWORD, FakeContext


async def test_register_returns_user_and_token(state):
    result = await server.register("user@example.com", VALID_PASSWORD)
    assert result["status"] == STATUS_OK
    assert result["email"] == "user@example.com"
    assert result["token"]
    assert result["expires_at"]


async def test_register_normalises_email_case(state):
    result = await server.register("Mixed.Case@Example.COM", VALID_PASSWORD)
    assert result["email"] == "mixed.case@example.com"


@pytest.mark.parametrize(
    "weak",
    ["short1A!", "alllowercase1!", "NOLOWERCASE1!", "NoDigits!!", "NoSymbols123"],
)
async def test_register_rejects_weak_passwords(state, weak):
    result = await server.register("user@example.com", weak)
    assert result["status"] == "error"
    assert result["code"] in {"weak_password", "validation_error"}


async def test_register_rejects_common_password(state):
    result = await server.register("user@example.com", "password123")
    assert result["status"] == "error"


async def test_register_rejects_invalid_email(state):
    result = await server.register("not-an-email", VALID_PASSWORD)
    assert result["status"] == "error"
    assert "email" in result["error"].lower()


async def test_register_rejects_duplicate_email(state, account):
    result = await server.register(account["email"], VALID_PASSWORD)
    assert result["status"] == "error"
    assert "already registered" in result["error"]


async def test_login_issues_a_second_working_token(state, account):
    result = await server.login("user@example.com", VALID_PASSWORD)
    assert result["status"] == STATUS_OK
    who = await server.whoami(ctx=FakeContext(result["token"]))
    assert who["status"] == STATUS_OK
    assert who["email"] == account["email"]


async def test_login_with_wrong_password_is_refused(state, account):
    result = await server.login("user@example.com", "Wr0ng-Password!")
    assert result["status"] == STATUS_AUTH_REQUIRED


async def test_login_for_unknown_email_is_indistinguishable(state, account):
    unknown = await server.login("nobody@example.com", VALID_PASSWORD)
    wrong = await server.login("user@example.com", "Wr0ng-Password!")
    assert unknown["error"] == wrong["error"]


async def test_repeated_failures_lock_the_account(state, account, settings):
    for _ in range(settings.login_max_attempts):
        await server.login("user@example.com", "Wr0ng-Password!")
    locked = await server.login("user@example.com", VALID_PASSWORD)
    assert locked["status"] == STATUS_AUTH_REQUIRED
    assert "many failed attempts" in locked["error"]


async def test_whoami_requires_a_token(state):
    result = await server.whoami(ctx=FakeContext(None))
    assert result["status"] == STATUS_AUTH_REQUIRED
    assert result["next_tool"] == "login"


async def test_whoami_rejects_a_garbage_token(state):
    result = await server.whoami(ctx=FakeContext("not-a-jwt"))
    assert result["status"] == STATUS_AUTH_REQUIRED


async def test_whoami_rejects_a_token_signed_with_another_secret(state, account):
    from ai_employee_mcp.auth.tokens import issue_token

    forged, _ = issue_token("usr_1", "a-different-secret", 3600)
    result = await server.whoami(ctx=FakeContext(forged))
    assert result["status"] == STATUS_AUTH_REQUIRED


async def test_logout_revokes_the_session(state, account):
    ctx = FakeContext(account["token"])
    assert (await server.whoami(ctx=ctx))["status"] == STATUS_OK
    await server.logout(ctx=ctx)
    after = await server.whoami(ctx=ctx)
    assert after["status"] == STATUS_AUTH_REQUIRED
    assert "revoked" in after["error"]


async def test_logout_only_affects_its_own_session(state, account):
    second = await server.login("user@example.com", VALID_PASSWORD)
    await server.logout(ctx=FakeContext(account["token"]))
    still_valid = await server.whoami(ctx=FakeContext(second["token"]))
    assert still_valid["status"] == STATUS_OK


async def test_static_token_fallback_for_local_runs(settings, storage, state):
    from ai_employee_mcp.auth.tokens import issue_token
    from ai_employee_mcp.storage.base import Session

    registered = await server.register("u@example.com", VALID_PASSWORD)
    settings.static_token = "dev-static-token"
    settings.static_user_id = registered["user_id"]
    token, claims = issue_token(
        registered["user_id"], settings.resolved_jwt_secret(), 3600
    )
    await storage.create_session(
        Session(
            token_jti=claims.jti,
            user_id=claims.user_id,
            issued_at=server.utcnow(),
            expires_at=claims.expires_at,
        )
    )

    assert (await server.whoami(ctx=FakeContext(token)))["status"] == STATUS_OK
    result = await server.whoami(ctx=FakeContext(None))
    assert result["status"] == STATUS_OK
    assert result["email"] == "u@example.com"


async def test_expired_session_is_rejected(state, account, storage):
    from datetime import timedelta

    from ai_employee_mcp.auth.tokens import decode_token

    claims = decode_token(account["token"], state.settings.resolved_jwt_secret())
    session = await storage.get_session(claims.jti)
    session.expires_at = server.utcnow() - timedelta(seconds=1)
    result = await server.whoami(ctx=FakeContext(account["token"]))
    assert result["status"] == STATUS_AUTH_REQUIRED
    assert "expired" in result["error"]


async def test_auth_events_are_audited(state, account, storage):
    actions = [entry["action"] for entry in storage.audit_log]
    assert "auth.register" in actions


async def test_bad_password_attempt_is_audited(state, account, storage):
    before = len(storage.audit_log)
    await server.login("user@example.com", "Wr0ng-Password!")
    entries = storage.audit_log[before:]
    assert any(e["outcome"] == "bad_password" for e in entries)


async def test_registration_is_reasonably_slow_because_of_argon2(state):
    start = time.perf_counter()
    await server.register("slow@example.com", VALID_PASSWORD)
    elapsed = time.perf_counter() - start
    assert elapsed > 0.05, "Argon2id should not be trivially fast"