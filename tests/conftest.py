import base64
import os

import pytest

from ai_employee_mcp.config import Settings, reset_settings_cache
from ai_employee_mcp.crypto import CredentialCipher
from ai_employee_mcp.server import AppState, configure
from ai_employee_mcp.storage.memory import InMemoryStorage

VALID_PASSWORD = "Str0ng-Passw0rd!"

ODOO_CREDS = {
    "url": "http://odoo.test:8069",
    "db": "prod",
    "username": "admin",
    "api_key": "s3cret-api-key",
}


@pytest.fixture
def master_key() -> str:
    return base64.b64encode(os.urandom(32)).decode("ascii")


@pytest.fixture
def settings(master_key: str) -> Settings:
    return Settings(
        environment="local",
        master_key=master_key,
        jwt_secret="test-secret-not-for-production",
        static_token="",
        odoo_default_url="http://odoo.test:8069",
    )


@pytest.fixture
def storage() -> InMemoryStorage:
    return InMemoryStorage()


@pytest.fixture
def state(settings: Settings, storage: InMemoryStorage):
    return configure(AppState.build(settings=settings, storage=storage))


@pytest.fixture
def cipher(master_key: str) -> CredentialCipher:
    return CredentialCipher(base64.b64decode(master_key))


@pytest.fixture
async def account(state: AppState) -> dict[str, str]:
    from ai_employee_mcp import server

    result = await server.register("user@example.com", VALID_PASSWORD)
    assert result["status"] == "ok"
    return {"user_id": result["user_id"], "email": result["email"], "token": result["token"]}


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    reset_settings_cache()
    yield
    reset_settings_cache()


class FakeHeaders(dict):
    def get(self, key, default=None):
        lowered = key.lower()
        for existing, value in self.items():
            if existing.lower() == lowered:
                return value
        return default


class FakeRequestContext:
    def __init__(self, token: str | None) -> None:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.request = type("Req", (), {"headers": FakeHeaders(headers)})()


class FakeContext:
    def __init__(self, token: str | None) -> None:
        self.request_context = FakeRequestContext(token)


@pytest.fixture
def ctx_for():
    return FakeContext


@pytest.fixture
def ctx(account: dict[str, str]) -> FakeContext:
    return FakeContext(account["token"])