import pytest

from ai_employee_mcp.credentials import CredentialManager
from ai_employee_mcp.errors import CredentialsRequired, ValidationError

ODOO_KEYS = ("url", "db", "username", "api_key")


@pytest.fixture
def manager(state) -> CredentialManager:
    return state.credentials


async def test_resolve_without_credentials_requests_them(manager):
    with pytest.raises(CredentialsRequired) as excinfo:
        await manager.resolve("usr_1", "odoo")

    error = excinfo.value
    assert error.provider == "odoo"
    assert error.missing == list(ODOO_KEYS)
    assert error.payload()["status"] == "credentials_required"
    assert error.payload()["next_tool"] == "save_credentials"
    assert "odoo" in error.payload()["hint"]


async def test_gmail_missing_credentials_mentions_oauth(manager):
    with pytest.raises(CredentialsRequired) as excinfo:
        await manager.resolve("usr_1", "gmail")
    assert "OAuth" in excinfo.value.payload()["hint"]


async def test_payload_shape_is_actionable_for_an_agent(manager):
    with pytest.raises(CredentialsRequired) as excinfo:
        await manager.resolve("usr_1", "odoo")

    body = excinfo.value.payload()
    assert set(body) >= {"status", "code", "error", "provider", "missing", "next_tool", "hint"}
    assert body["provider"] == "odoo"
    assert isinstance(body["missing"], list)


async def test_partial_credentials_still_report_remaining(manager):
    await manager.save("usr_1", "odoo", {"url": "http://o.test", "db": "prod"})
    with pytest.raises(CredentialsRequired) as excinfo:
        await manager.resolve("usr_1", "odoo")
    assert excinfo.value.missing == ["username", "api_key"]


async def test_save_then_resolve_roundtrip(manager):
    values = {
        "url": "http://o.test",
        "db": "prod",
        "username": "admin",
        "api_key": "super-secret",
    }
    saved = await manager.save("usr_1", "odoo", values)
    assert saved["stored_fields"] == sorted(ODOO_KEYS)
    assert "super-secret" not in str(saved)

    resolved = await manager.resolve("usr_1", "odoo")
    assert resolved["api_key"] == "super-secret"


async def test_save_merges_instead_of_replacing(manager):
    first = await manager.save("usr_1", "odoo", {"url": "http://o.test", "db": "prod"})
    assert first["still_missing"] == ["username", "api_key"]
    await manager.save("usr_1", "odoo", {"username": "admin", "api_key": "k"})
    resolved = await manager.resolve("usr_1", "odoo")
    assert resolved["db"] == "prod"
    assert resolved["username"] == "admin"


async def test_complete_save_reports_nothing_missing(manager):
    result = await manager.save(
        "usr_1", "odoo", {"url": "u", "db": "d", "username": "n", "api_key": "k"}
    )
    assert result["still_missing"] == []


async def test_save_rejects_unknown_fields(manager):
    with pytest.raises(ValidationError, match="Unknown field"):
        await manager.save("usr_1", "odoo", {"not_a_field": "x"})


async def test_partial_save_is_allowed_and_reports_what_is_left(manager):
    result = await manager.save("usr_1", "odoo", {"db": "prod"})
    assert result["still_missing"] == ["url", "username", "api_key"]
    assert result["stored_fields"] == ["db"]


async def test_save_rejects_a_save_with_no_usable_fields(manager):
    with pytest.raises(ValidationError, match="No usable values"):
        await manager.save("usr_1", "odoo", {"db": "   "})


async def test_unknown_provider_is_rejected(manager):
    with pytest.raises(ValidationError, match="Unknown provider"):
        await manager.save("usr_1", "myspace", {"db": "x"})


async def test_status_never_reveals_secret_values(manager):
    await manager.save(
        "usr_1", "odoo", {"url": "u", "db": "d", "username": "n", "api_key": "LEAK-ME"}
    )
    body = await manager.status("usr_1")
    assert "odoo" in body["configured_providers"]
    assert "LEAK-ME" not in str(body)
    assert "odoo" in body["required_fields"]


async def test_status_reports_configured_and_available(manager):
    await manager.save("usr_1", "gmail", {"client_id": "a", "client_secret": "b", "refresh_token": "c"})
    body = await manager.status("usr_1")
    assert body["configured_providers"] == ["gmail"]
    assert body["available_providers"] == ["gmail", "linkedin", "odoo"]


async def test_users_cannot_read_each_others_credentials(manager):
    values = {"url": "u", "db": "d", "username": "n", "api_key": "alice-secret"}
    await manager.save("usr_alice", "odoo", values)

    with pytest.raises(CredentialsRequired):
        await manager.resolve("usr_bob", "odoo")

    body = await manager.status("usr_bob")
    assert body["configured_providers"] == []


async def test_disconnect_removes_credentials(manager):
    await manager.save("usr_1", "odoo", {"url": "u", "db": "d", "username": "n", "api_key": "k"})
    result = await manager.disconnect("usr_1", "odoo")
    assert result == {"provider": "odoo", "disconnected": True}
    with pytest.raises(CredentialsRequired):
        await manager.resolve("usr_1", "odoo")


async def test_disconnect_reports_when_absent(manager):
    assert (await manager.disconnect("usr_1", "odoo"))["disconnected"] is False


async def test_stored_ciphertext_never_contains_plaintext(manager, storage):
    await manager.save("usr_1", "odoo", {"url": "u", "db": "d", "username": "n", "api_key": "PLAINTEXT"})
    record = await storage.get_credential("usr_1", "odoo")
    assert record is not None
    assert "PLAINTEXT" not in str(record.fields.values())


async def test_saving_credentials_is_audited(manager, storage):
    await manager.save("usr_1", "odoo", {"url": "u", "db": "d", "username": "n", "api_key": "k"})
    actions = [entry["action"] for entry in storage.audit_log]
    assert "credentials.save:odoo" in actions


async def test_whitespace_only_values_are_not_stored(manager, storage):
    await manager.save(
        "usr_1", "odoo", {"url": "   ", "db": "d", "username": "n", "api_key": "k"}
    )
    record = await storage.get_credential("usr_1", "odoo")
    assert set(record.fields) == {"db", "username", "api_key"}
    assert "url" not in record.fields