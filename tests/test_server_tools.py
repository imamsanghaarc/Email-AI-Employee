"""Tool-level behaviour: auth, credential contracts, approvals, and error surfacing."""

from datetime import timedelta

import httpx
import pytest

from ai_employee_mcp import server
from ai_employee_mcp.errors import (
    STATUS_APPROVAL_REQUIRED,
    STATUS_AUTH_REQUIRED,
    STATUS_CREDENTIALS_REQUIRED,
    STATUS_OK,
)
from ai_employee_mcp.providers.odoo import OdooClient
from ai_employee_mcp.storage.base import Approval
from tests.test_odoo_client import FakeOdoo

from .conftest import ODOO_CREDS, FakeContext


@pytest.fixture
def fake_odoo():
    return FakeOdoo()


@pytest.fixture
def odoo_wired(monkeypatch, fake_odoo):
    """Point server.build_client at an in-memory Odoo so tools never hit the network."""

    def build(creds, default_url):
        return OdooClient(
            url=creds.get("url") or default_url,
            db=creds["db"],
            username=creds["username"],
            api_key=creds["api_key"],
            transport=httpx.MockTransport(fake_odoo.handler),
        )

    monkeypatch.setattr(server, "build_client", build)
    return fake_odoo


@pytest.fixture
async def wired(ctx):
    await server.save_credentials(provider="odoo", credentials=ODOO_CREDS, ctx=ctx)
    return ctx


def orm_calls(fake):
    return [c["args"][4] for c in fake.calls if c["service"] == "object"]


# --- auth boundary -----------------------------------------------------------


async def test_tool_requires_auth(state):
    result = await server.odoo_search_read("res.partner", ctx=FakeContext(None))
    assert result["status"] == STATUS_AUTH_REQUIRED
    assert result["next_tool"] == "login"


async def test_tool_rejects_revoked_token(account, ctx):
    await server.logout(ctx=ctx)
    result = await server.odoo_search_read("res.partner", ctx=ctx)
    assert result["status"] == STATUS_AUTH_REQUIRED


# --- credential contract -----------------------------------------------------


async def test_odoo_tool_without_credentials_tells_the_agent_what_to_do(ctx):
    result = await server.odoo_search_read("res.partner", ctx=ctx)
    assert result["status"] == STATUS_CREDENTIALS_REQUIRED
    assert result["provider"] == "odoo"
    assert set(result["missing"]) == {"url", "db", "username", "api_key"}
    assert result["next_tool"] == "save_credentials"


async def test_partial_credentials_report_the_remainder(ctx):
    first = await server.save_credentials(
        provider="odoo", credentials={"url": "http://x:8069", "db": "prod"}, ctx=ctx
    )
    assert first["status"] == STATUS_OK
    assert set(first["stored_fields"]) == {"url", "db"}
    assert set(first["still_missing"]) == {"username", "api_key"}

    again = await server.odoo_search_read("res.partner", ctx=ctx)
    assert again["status"] == STATUS_CREDENTIALS_REQUIRED
    assert set(again["missing"]) == {"username", "api_key"}


async def test_completed_credentials_unlock_the_tool(wired):
    result = await server.credentials_status(ctx=wired)
    assert result["configured_providers"] == ["odoo"]
    assert result["available_providers"] == ["gmail", "linkedin", "odoo"]
    assert result["required_fields"]["odoo"] == ["url", "db", "username", "api_key"]


async def test_credentials_status_never_leaks_secret_material(wired):
    result = await server.credentials_status(ctx=wired)
    blob = str(result)
    assert "s3cret-api-key" not in blob
    assert "admin" not in blob, "no field values, only field names, may be reported"


async def test_disconnect_relocks_the_provider(wired):
    await server.disconnect_provider("odoo", ctx=wired)
    result = await server.odoo_search_read("res.partner", ctx=wired)
    assert result["status"] == STATUS_CREDENTIALS_REQUIRED


async def test_save_credentials_cannot_target_another_user():
    """There is no user_id parameter, so cross-account writes are structurally impossible."""
    import inspect

    params = list(inspect.signature(server.save_credentials).parameters)
    assert "user_id" not in params
    assert params == ["provider", "credentials", "ctx"]


async def test_two_users_have_independent_credentials(ctx):
    await server.save_credentials(provider="odoo", credentials=ODOO_CREDS, ctx=ctx)
    other = await server.register("second@example.com", "An0ther-Passw0rd!")
    other_ctx = FakeContext(other["token"])

    assert (await server.odoo_search_read("res.partner", ctx=other_ctx))["status"] == (
        STATUS_CREDENTIALS_REQUIRED
    )
    assert "odoo" in (await server.credentials_status(ctx=ctx))["configured_providers"]
    assert "odoo" not in (
        await server.credentials_status(ctx=other_ctx)
    )["configured_providers"]


# --- odoo reads --------------------------------------------------------------


async def test_odoo_search_read_returns_records(wired, odoo_wired):
    result = await server.odoo_search_read(
        "res.partner", domain=[], fields=["name"], limit=10, ctx=wired
    )
    assert result["status"] == STATUS_OK
    assert result["count"] == 2
    assert result["records"][0]["name"] == "Alpha"


async def test_odoo_read_rejects_bad_model(wired, odoo_wired):
    result = await server.odoo_search_read("res.partner; DROP TABLE x", ctx=wired)
    assert result["status"] == "error"
    assert result["code"] == "validation_error"
    assert orm_calls(odoo_wired) == []


async def test_odoo_accounting_summary(wired, odoo_wired):
    result = await server.odoo_accounting_summary(ctx=wired)
    assert result["status"] == STATUS_OK
    assert result["posted_invoices_total"] == 150.0


async def test_provider_failure_is_surfaced_not_raised(wired, monkeypatch, fake_odoo):
    fake_odoo.raise_rpc_error = True

    def build(creds, default_url):
        return OdooClient(
            url=creds["url"],
            db=creds["db"],
            username=creds["username"],
            api_key=creds["api_key"],
            transport=httpx.MockTransport(fake_odoo.handler),
        )

    monkeypatch.setattr(server, "build_client", build)
    result = await server.odoo_accounting_summary(ctx=wired)
    assert result["status"] == "error"
    assert result["code"] == "provider_error"


async def test_bad_odoo_login_is_reported_as_provider_error(wired, monkeypatch, fake_odoo):
    monkeypatch.setattr(
        server,
        "build_client",
        lambda creds, default_url: OdooClient(
            url=creds["url"],
            db=creds["db"],
            username=creds["username"],
            api_key=creds["api_key"],
            transport=httpx.MockTransport(
                lambda r: httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "result": False})
            ),
        ),
    )
    result = await server.odoo_search_read("res.partner", ctx=wired)
    assert result["status"] == "error"
    assert result["code"] == "provider_error"
    assert "API key" in result["error"]


# --- approval gate -----------------------------------------------------------


async def test_write_without_approval_does_not_run(wired, odoo_wired):
    result = await server.odoo_create_record("res.partner", {"name": "X"}, ctx=wired)
    assert result["status"] == STATUS_APPROVAL_REQUIRED
    assert result["next_tool"] == "approval_status"
    assert result["approval_id"]
    assert orm_calls(odoo_wired) == []


async def test_pending_approval_still_blocks(wired, odoo_wired):
    first = await server.odoo_create_record("res.partner", {"name": "X"}, ctx=wired)
    retry = await server.odoo_create_record(
        "res.partner", {"name": "X"}, approval_id=first["approval_id"], ctx=wired
    )
    assert retry["status"] == STATUS_APPROVAL_REQUIRED
    assert "pending" in retry["error"]
    assert orm_calls(odoo_wired) == []


async def test_approved_write_proceeds(wired, odoo_wired, storage):
    first = await server.odoo_create_record("res.partner", {"name": "X"}, ctx=wired)
    await storage.decide_approval(first["approval_id"], "approved", "human")

    status = await server.approval_status(first["approval_id"], ctx=wired)
    assert status["status"] == "approved"
    assert status["decided_by"] == "human"

    done = await server.odoo_create_record(
        "res.partner", {"name": "X"}, approval_id=first["approval_id"], ctx=wired
    )
    assert done["status"] == STATUS_OK
    assert done["record_id"] == 101
    assert "create" in orm_calls(odoo_wired)


async def test_rejected_approval_blocks(wired, odoo_wired, storage):
    first = await server.odoo_create_record("res.partner", {"name": "X"}, ctx=wired)
    await storage.decide_approval(first["approval_id"], "rejected", "human")
    retry = await server.odoo_create_record(
        "res.partner", {"name": "X"}, approval_id=first["approval_id"], ctx=wired
    )
    assert retry["status"] == STATUS_APPROVAL_REQUIRED
    assert "rejected" in retry["error"]
    assert orm_calls(odoo_wired) == []


async def test_expired_approval_blocks(wired, odoo_wired, storage):
    first = await server.odoo_create_record("res.partner", {"name": "X"}, ctx=wired)
    approval = await storage.get_approval(first["approval_id"])
    approval.created_at = approval.created_at - timedelta(hours=1)
    retry = await server.odoo_create_record(
        "res.partner", {"name": "X"}, approval_id=first["approval_id"], ctx=wired
    )
    assert retry["status"] == STATUS_APPROVAL_REQUIRED
    assert "expired" in retry["error"]
    assert orm_calls(odoo_wired) == []


async def test_approval_status_marks_stale_pending_as_expired(wired, storage):
    first = await server.odoo_create_record("res.partner", {"name": "X"}, ctx=wired)
    approval = await storage.get_approval(first["approval_id"])
    approval.created_at = approval.created_at - timedelta(hours=1)
    result = await server.approval_status(first["approval_id"], ctx=wired)
    assert result["status"] == "expired"


async def test_approval_cannot_be_replayed_for_another_action(wired, odoo_wired, storage):
    create = await server.odoo_create_record("res.partner", {"name": "X"}, ctx=wired)
    await storage.decide_approval(create["approval_id"], "approved", "human")
    misuse = await server.odoo_update_record(
        "res.partner", 1, {"name": "Y"}, approval_id=create["approval_id"], ctx=wired
    )
    assert misuse["status"] == "error"
    assert "covers" in misuse["error"]
    assert orm_calls(odoo_wired) == []


async def test_foreign_approval_id_is_refused(wired, odoo_wired, storage):
    other = await storage.create_user(email="other@example.com", password_hash="x")  # noqa: S106
    await storage.create_approval(
        Approval(id="a" * 16, user_id=other.id, action="odoo_create_record", summary="x")
    )
    result = await server.odoo_create_record(
        "res.partner", {"name": "X"}, approval_id="a" * 16, ctx=wired
    )
    assert result["status"] == "error"
    assert "for this account" in result["error"]
    assert orm_calls(odoo_wired) == []


async def test_unknown_approval_id_is_refused(wired, odoo_wired):
    result = await server.odoo_create_record(
        "res.partner", {"name": "X"}, approval_id="f" * 16, ctx=wired
    )
    assert result["status"] == "error"


async def test_pending_approvals_lists_only_my_requests(wired, storage):
    other = await storage.create_user(email="other2@example.com", password_hash="x")  # noqa: S106
    await storage.create_approval(
        Approval(id="b" * 16, user_id=other.id, action="x", summary="theirs")
    )
    mine = await server.odoo_create_record("res.partner", {"name": "X"}, ctx=wired)
    listing = await server.pending_approvals(ctx=wired)
    ids = [a["approval_id"] for a in listing["approvals"]]
    assert mine["approval_id"] in ids
    assert "b" * 16 not in ids


async def test_approval_status_of_another_user_is_refused(wired, storage):
    other = await storage.create_user(email="other3@example.com", password_hash="x")  # noqa: S106
    await storage.create_approval(
        Approval(id="c" * 16, user_id=other.id, action="x", summary="theirs")
    )
    result = await server.approval_status("c" * 16, ctx=wired)
    assert result["status"] == "error"


async def test_gate_can_be_disabled_for_local_work(settings, ctx, odoo_wired):
    settings.require_approval_for_side_effects = False
    await server.save_credentials(provider="odoo", credentials=ODOO_CREDS, ctx=ctx)
    result = await server.odoo_create_record("res.partner", {"name": "X"}, ctx=ctx)
    assert result["status"] == STATUS_OK


async def test_approval_decisions_are_audited(wired, storage, odoo_wired):
    first = await server.odoo_create_record("res.partner", {"name": "X"}, ctx=wired)
    await storage.decide_approval(first["approval_id"], "approved", "human")
    await server.odoo_create_record(
        "res.partner", {"name": "X"}, approval_id=first["approval_id"], ctx=wired
    )
    actions = [e["action"] for e in storage.audit_log]
    assert "approval.requested:odoo_create_record" in actions
    assert "approval.used:odoo_create_record" in actions