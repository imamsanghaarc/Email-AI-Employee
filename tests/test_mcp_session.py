"""End-to-end tests that speak the real MCP protocol over an in-memory transport.

These exercise tool discovery, JSON-schema generation, and call dispatch exactly as a
real agent client would, rather than calling the Python functions directly.
"""

import httpx
import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from ai_employee_mcp import server
from ai_employee_mcp.config import Settings
from ai_employee_mcp.providers.odoo import OdooClient
from ai_employee_mcp.server import AppState, configure
from ai_employee_mcp.storage.memory import InMemoryStorage
from tests.test_odoo_client import FakeOdoo

from .conftest import ODOO_CREDS, VALID_PASSWORD

EXPECTED_TOOLS = {
    "register",
    "login",
    "logout",
    "whoami",
    "save_credentials",
    "credentials_status",
    "disconnect_provider",
    "odoo_search_read",
    "odoo_create_record",
    "odoo_update_record",
    "odoo_accounting_summary",
    "approval_status",
    "pending_approvals",
}


def as_dict(result):
    """Unwrap an MCP CallToolResult into the dict our tools return."""
    import json

    raw = result.structuredContent or result.content[0].text
    return json.loads(raw) if isinstance(raw, str) else raw


@pytest.fixture
def live_state():
    """A configured state wired to an in-memory Odoo, reachable via a static token."""
    import base64
    import os

    settings = Settings(
        environment="local",
        master_key=base64.b64encode(os.urandom(32)).decode(),
        jwt_secret="e2e-test-secret",
        static_token="e2e-token",
        odoo_default_url="http://odoo.test:8069",
    )
    storage = InMemoryStorage()
    state = configure(AppState.build(settings=settings, storage=storage))
    fake = FakeOdoo()
    server.build_client = lambda creds, default_url: OdooClient(
        url=creds.get("url") or default_url,
        db=creds["db"],
        username=creds["username"],
        api_key=creds["api_key"],
        transport=httpx.MockTransport(fake.handler),
    )
    state.settings.static_user_id = ""
    return state, storage, fake


async def test_client_can_discover_every_tool(live_state):
    async with create_connected_server_and_client_session(server.mcp) as client:
        listed = await client.list_tools()
    assert {t.name for t in listed.tools} == EXPECTED_TOOLS


async def test_every_tool_has_a_usable_json_schema(live_state):
    async with create_connected_server_and_client_session(server.mcp) as client:
        listed = await client.list_tools()

    for tool in listed.tools:
        schema = tool.inputSchema
        assert schema["type"] == "object", f"{tool.name} schema is not an object"
        assert "ctx" not in schema["properties"], f"{tool.name} leaked the Context param"
        for required in schema.get("required", []):
            assert required in schema["properties"], f"{tool.name} requires undeclared {required}"
        for name in schema["properties"]:
            assert name != "ctx"


async def test_parameterised_tools_declare_their_arguments(live_state):
    async with create_connected_server_and_client_session(server.mcp) as client:
        listed = {t.name: t for t in (await client.list_tools()).tools}

    assert listed["odoo_search_read"].inputSchema["required"] == ["model"]
    assert set(listed["save_credentials"].inputSchema["required"]) == {
        "provider",
        "credentials",
    }
    assert set(listed["odoo_update_record"].inputSchema["required"]) == {
        "model",
        "record_id",
        "values",
    }
    assert listed["odoo_create_record"].inputSchema["properties"]["approval_id"]
    assert listed["odoo_search_read"].inputSchema["properties"]["domain"]


async def test_zero_argument_tools_are_allowed(live_state):
    async with create_connected_server_and_client_session(server.mcp) as client:
        listed = {t.name: t for t in (await client.list_tools()).tools}

    for name in ("logout", "whoami", "credentials_status", "pending_approvals"):
        assert listed[name].inputSchema["properties"] == {}
        assert not listed[name].inputSchema.get("required")
        assert listed[name].description, f"{name} needs a description for the agent"


async def test_register_login_and_whoami_over_the_protocol(live_state):
    state, storage, _ = live_state
    async with create_connected_server_and_client_session(server.mcp) as client:
        created = await client.call_tool(
            "register", {"email": "e2e@example.com", "password": VALID_PASSWORD}
        )
        registered = as_dict(created)
        assert registered["status"] == "ok"
        assert registered["token"]

        who = as_dict(await client.call_tool("whoami"))
        assert who["status"] == "auth_required"

        state.settings.static_token = registered["token"]
        state.settings.static_user_id = registered["user_id"]
        me = as_dict(await client.call_tool("whoami"))
        assert me["status"] == "ok"
        assert me["email"] == "e2e@example.com"


async def test_full_credential_then_query_flow_over_the_protocol(live_state):
    state, storage, _ = live_state
    async with create_connected_server_and_client_session(server.mcp) as client:
        created = await client.call_tool(
            "register", {"email": "flow@example.com", "password": VALID_PASSWORD}
        )
        data = as_dict(created)
        state.settings.static_token = data["token"]
        state.settings.static_user_id = data["user_id"]

        blocked = as_dict(await client.call_tool("odoo_search_read", {"model": "res.partner"}))
        assert blocked["status"] == "credentials_required"
        assert blocked["next_tool"] == "save_credentials"

        saved = as_dict(
            await client.call_tool(
                "save_credentials", {"provider": "odoo", "credentials": ODOO_CREDS}
            )
        )
        assert saved["status"] == "ok"
        assert saved["still_missing"] == []

        queried = as_dict(
            await client.call_tool(
                "odoo_search_read",
                {"model": "res.partner", "fields": ["name"], "limit": 10},
            )
        )
        assert queried["status"] == "ok"
        assert queried["count"] == 2


async def test_approval_gate_flows_over_the_protocol(live_state):
    state, storage, _ = live_state
    async with create_connected_server_and_client_session(server.mcp) as client:
        created = as_dict(
            await client.call_tool(
                "register", {"email": "approve@example.com", "password": VALID_PASSWORD}
            )
        )
        state.settings.static_token = created["token"]
        state.settings.static_user_id = created["user_id"]
        await client.call_tool(
            "save_credentials", {"provider": "odoo", "credentials": ODOO_CREDS}
        )

        gated = as_dict(
            await client.call_tool(
                "odoo_create_record", {"model": "res.partner", "values": {"name": "X"}}
            )
        )
        assert gated["status"] == "approval_required"

        pending = as_dict(await client.call_tool("pending_approvals"))
        assert gated["approval_id"] in [a["approval_id"] for a in pending["approvals"]]

        await storage.decide_approval(gated["approval_id"], "approved", "human")
        status = as_dict(
            await client.call_tool("approval_status", {"approval_id": gated["approval_id"]})
        )
        assert status["status"] == "approved"

        done = as_dict(
            await client.call_tool(
                "odoo_create_record",
                {
                    "model": "res.partner",
                    "values": {"name": "X"},
                    "approval_id": gated["approval_id"],
                },
            )
        )
        assert done["status"] == "ok"
        assert done["record_id"] == 101


async def test_validation_errors_come_back_as_data_not_exceptions(live_state):
    state, _, _ = live_state
    async with create_connected_server_and_client_session(server.mcp) as client:
        created = as_dict(
            await client.call_tool(
                "register", {"email": "weak@example.com", "password": "alllowercase"}
            )
        )
        assert created["status"] == "error"
        assert created["code"] in {"weak_password", "validation_error"}


async def test_unknown_provider_is_a_clean_error(live_state):
    state, _, _ = live_state
    async with create_connected_server_and_client_session(server.mcp) as client:
        created = as_dict(
            await client.call_tool(
                "register", {"email": "prov@example.com", "password": VALID_PASSWORD}
            )
        )
        state.settings.static_token = created["token"]
        state.settings.static_user_id = created["user_id"]
        bad = as_dict(
            await client.call_tool(
                "save_credentials", {"provider": "myspace", "credentials": {"x": "y"}}
            )
        )
        assert bad["status"] == "error"
        assert "myspace" in bad["error"]