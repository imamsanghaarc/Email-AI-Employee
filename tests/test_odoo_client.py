import json

import httpx
import pytest

from ai_employee_mcp.errors import ProviderError, ValidationError
from ai_employee_mcp.providers.odoo import OdooClient, build_client, validate_model_name


class FakeOdoo:
    """Minimal JSON-RPC 2.0 responder covering the calls OdooClient makes.

    Odoo wraps every ORM method in service='object', method='call', with the ORM
    method name at args[4].
    """

    def __init__(self, uid: int = 7) -> None:
        self.uid = uid
        self.login_result = uid
        self.calls: list[dict] = []
        self.raise_rpc_error = False

    def handler(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        service = body["params"]["service"]
        rpc_method = body["params"]["method"]
        args = body["params"]["args"]
        self.calls.append({"service": service, "rpc_method": rpc_method, "args": args})

        if self.raise_rpc_error:
            return httpx.Response(
                200,
                json={
                    "jsonrpc": "2.0",
                    "id": body["id"],
                    "error": {"code": 200, "message": "Object does not exist"},
                },
            )

        if service == "common" and rpc_method == "login":
            result = self.login_result
        else:
            orm_method = args[4]
            orm_args = args[5]
            if orm_method == "search_read":
                limit = orm_args[2]
                rows = [
                    {"id": 1, "name": "Alpha", "amount_total": 100.0, "state": "posted"},
                    {"id": 2, "name": "Beta", "amount_total": 50.0, "state": "posted"},
                ]
                result = rows[:limit]
            elif orm_method == "search_count":
                result = 42
            elif orm_method == "create":
                result = 101
            elif orm_method == "write":
                result = True
            else:
                return httpx.Response(
                    200,
                    json={
                        "jsonrpc": "2.0",
                        "id": body["id"],
                        "error": {"code": 200, "message": f"no such method {orm_method}"},
                    },
                )
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": body["id"], "result": result})


def make_client(handler, **overrides):
    creds = {
        "url": "http://odoo.test:8069",
        "db": "prod",
        "username": "admin",
        "api_key": "key",
    }
    creds.update(overrides)
    return OdooClient(
        url=creds["url"],
        db=creds["db"],
        username=creds["username"],
        api_key=creds["api_key"],
        transport=httpx.MockTransport(handler),
    )


@pytest.fixture
def fake():
    return FakeOdoo()


@pytest.fixture
def client(fake):
    return make_client(fake.handler)


def test_validate_model_name_accepts_real_models():
    for model in ("res.partner", "account.move", "product.product", "sale.order"):
        assert validate_model_name(model) == model


@pytest.mark.parametrize(
    "bad",
    [
        "'; DROP TABLE res_partner; --",
        "res.partner; rm -rf /",
        "Res.Partner",
        "res partner",
        "",
        "../../etc/passwd",
        "res.partner\ncommand",
        "__import__('os')",
    ],
)
def test_validate_model_name_rejects_injection_attempts(bad):
    with pytest.raises(ValidationError):
        validate_model_name(bad)


async def test_search_read_authenticates_once_and_reuses_uid(client, fake):
    await client.search_read("res.partner", [["active", "=", True]], ["name"], 5)
    await client.search_read("res.partner", [], ["name"], 5)
    logins = [c for c in fake.calls if c["rpc_method"] == "login"]
    assert len(logins) == 1, "uid must be reused, not re-authenticated per call"


async def test_search_read_returns_records(client):
    records = await client.search_read("res.partner", [], ["name"], 10)
    assert len(records) == 2
    assert records[0]["name"] == "Alpha"


async def test_search_read_respects_limit(client):
    assert len(await client.search_read("res.partner", [], ["name"], 1)) == 1


async def test_search_read_rejects_out_of_range_limit(client):
    with pytest.raises(ValidationError, match="between 1 and 500"):
        await client.search_read("res.partner", [], [], 5000)
    with pytest.raises(ValidationError):
        await client.search_read("res.partner", [], [], 0)


async def test_search_read_rejects_negative_offset(client):
    with pytest.raises(ValidationError, match="non-negative"):
        await client.search_read("res.partner", [], [], 10, -1)


async def test_search_read_rejects_string_domain(client):
    with pytest.raises(ValidationError, match="domain must be a list"):
        await client.search_read("res.partner", "name = 'x'", [], 10)


async def test_search_read_rejects_non_string_fields(client):
    with pytest.raises(ValidationError, match="list of strings"):
        await client.search_read("res.partner", [], [1, 2], 10)


async def test_search_read_rejects_invalid_model(client):
    with pytest.raises(ValidationError):
        await client.search_read("not a model", [], [], 10)


async def test_failed_login_is_reported_clearly(fake):
    fake.login_result = False
    client = make_client(fake.handler)
    with pytest.raises(ProviderError, match="rejected the username"):
        await client.search_read("res.partner")


async def test_create_record_returns_new_id(client):
    assert await client.create_record("res.partner", {"name": "New"}) == 101


async def test_create_record_rejects_bad_model(client):
    with pytest.raises(ValidationError):
        await client.create_record("bad model!", {"name": "x"})


async def test_create_record_rejects_empty_values(client):
    with pytest.raises(ValidationError, match="non-empty dict"):
        await client.create_record("res.partner", {})


async def test_update_record_requires_positive_id(client):
    with pytest.raises(ValidationError, match="positive integer"):
        await client.update_record("res.partner", 0, {"name": "x"})


async def test_update_record_returns_true(client):
    assert await client.update_record("res.partner", 1, {"name": "Renamed"}) is True


async def test_accounting_summary_totals_posted_invoices(client):
    summary = await client.accounting_summary()
    assert summary["posted_invoices"] == 2
    assert summary["posted_invoices_total"] == 150.0
    assert summary["partners"] == 42
    assert summary["database"] == "prod"


async def test_rpc_error_is_surfaced_with_code(fake):
    fake.raise_rpc_error = True
    client = make_client(fake.handler)
    with pytest.raises(ProviderError, match="Odoo error 200"):
        await client.search_read("res.partner")


async def test_non_json_response_is_reported():
    client = make_client(lambda request: httpx.Response(200, text="<html>login</html>"))
    with pytest.raises(ProviderError, match="non-JSON"):
        await client.search_read("res.partner")


async def test_connection_failure_is_reported():
    def handler(request):
        raise httpx.ConnectError("connection refused")

    with pytest.raises(ProviderError, match="Could not reach Odoo"):
        await make_client(handler).search_read("res.partner")


async def test_http_error_status_is_reported():
    client = make_client(lambda request: httpx.Response(500, text="internal error"))
    with pytest.raises(ProviderError, match="HTTP 500"):
        await client.search_read("res.partner")


def test_build_client_falls_back_to_default_url():
    client = build_client(
        {"url": "", "db": "d", "username": "u", "api_key": "k"}, "http://fallback:8069"
    )
    assert client.endpoint == "http://fallback:8069/jsonrpc"


def test_endpoint_strips_trailing_slash():
    client = build_client(
        {"url": "http://x:8069/", "db": "d", "username": "u", "api_key": "k"}, "http://y"
    )
    assert client.endpoint == "http://x:8069/jsonrpc"


async def test_api_key_is_sent_as_the_password_field(fake):
    client = make_client(fake.handler, api_key="s3cret")
    await client.search_read("res.partner", [], ["name"], 1)
    login_call = [c for c in fake.calls if c["rpc_method"] == "login"][0]
    assert login_call["args"] == ["prod", "admin", "s3cret"]


async def test_uid_is_passed_on_subsequent_calls(fake):
    client = make_client(fake.handler)
    await client.search_read("res.partner", [], ["name"], 1)
    orm_calls = [c for c in fake.calls if c["service"] == "object"]
    assert orm_calls[0]["args"][1] == 7
    assert orm_calls[0]["args"][2] == "key"