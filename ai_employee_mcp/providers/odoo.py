"""Odoo provider over JSON-RPC 2.0.

Authentication uses the user's own login + API key. No LLM is involved: the
connecting agent supplies the domain and the caller-supplied domain is passed
through as a structured domain list, never string-interpolated into a query.
"""

from __future__ import annotations

import re
from typing import Any

import httpx

from ..errors import ProviderError, ValidationError

MODEL_NAME = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$")
REQUEST_TIMEOUT = 30.0
JSONRPC_VERSION = "2.0"

ACCOUNTING_DOMAIN = [("state", "in", ("posted", "paid"))]
LEDGER_MODELS = {
    "invoices": "account.move",
    "partners": "res.partner",
    "products": "product.product",
}


def validate_model_name(model: str) -> str:
    if not MODEL_NAME.match(model):
        raise ValidationError(
            f"Invalid Odoo model name {model!r}. Expected dotted lowercase identifiers "
            "such as 'res.partner' or 'account.move'."
        )
    return model


class OdooClient:
    def __init__(
        self,
        url: str,
        db: str,
        username: str,
        api_key: str,
        api_version: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.url = url.rstrip("/")
        self.db = db
        self.username = username
        self.api_key = api_key
        self.api_version = api_version
        self._transport = transport
        self._uid: int | None = None
        self._request_id = 0

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=self._transport)

    @property
    def endpoint(self) -> str:
        return f"{self.url}/jsonrpc"

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    async def _rpc(
        self, client: httpx.AsyncClient, service: str, method: str, args: list[Any]
    ) -> Any:
        payload = {
            "jsonrpc": JSONRPC_VERSION,
            "method": "call",
            "params": {"service": service, "method": method, "args": args},
            "id": self._next_id(),
        }
        try:
            response = await client.post(self.endpoint, json=payload, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            body = response.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:400] if exc.response is not None else ""
            raise ProviderError(f"Odoo returned HTTP {exc.response.status_code}: {detail}") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"Could not reach Odoo at {self.endpoint}: {exc}") from exc
        except ValueError as exc:
            raise ProviderError("Odoo returned a non-JSON response") from exc

        if "error" in body and body["error"] is not None:
            error = body["error"]
            raise ProviderError(
                f"Odoo error {error.get('code')}: {error.get('message')} "
                f"[{error.get('data', {}).get('name', 'n/a')}]"
            )
        return body.get("result")

    async def authenticate(self, client: httpx.AsyncClient) -> int:
        uid = await self._rpc(
            client, "common", "login", [self.db, self.username, self.api_key]
        )
        if not uid:
            raise ProviderError(
                "Odoo rejected the username + API key. Check the url, db, username "
                "and that the API key is still valid."
            )
        self._uid = int(uid)
        return self._uid

    async def _execute(
        self,
        client: httpx.AsyncClient,
        model: str,
        method: str,
        args: list[Any],
        kwargs: dict[str, Any] | None = None,
    ) -> Any:
        if self._uid is None:
            await self.authenticate(client)
        return await self._rpc(
            client,
            "object",
            "call",
            [self.db, self._uid, self.api_key, model, method, args, kwargs or {}],
        )

    async def search_read(
        self,
        model: str,
        domain: list[Any] | None = None,
        fields: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        validate_model_name(model)
        if not isinstance(limit, int) or not 1 <= limit <= 500:
            raise ValidationError("limit must be an integer between 1 and 500")
        if not isinstance(offset, int) or offset < 0:
            raise ValidationError("offset must be a non-negative integer")
        domain = domain or []
        fields = fields or []
        if not isinstance(domain, list):
            raise ValidationError("domain must be a list, e.g. [[\"state\",\"=\",\"posted\"]]")
        if not isinstance(fields, list) or any(not isinstance(f, str) for f in fields):
            raise ValidationError("fields must be a list of strings")

        async with self._client() as client:
            result = await self._execute(
                client,
                model,
                "search_read",
                [domain, fields, limit, offset],
            )
        if not isinstance(result, list):
            raise ProviderError(f"Expected a list of records, got {type(result).__name__}")
        return result

    async def create_record(self, model: str, values: dict[str, Any]) -> int:
        validate_model_name(model)
        if not isinstance(values, dict) or not values:
            raise ValidationError("values must be a non-empty dict of Odoo fields")
        async with self._client() as client:
            new_id = await self._execute(client, model, "create", [values])
        if new_id is False or new_id is None:
            raise ProviderError(f"Odoo refused to create a {model} record")
        return int(new_id)

    async def update_record(
        self, model: str, record_id: int, values: dict[str, Any]
    ) -> bool:
        validate_model_name(model)
        if not isinstance(record_id, int) or record_id <= 0:
            raise ValidationError("record_id must be a positive integer")
        if not isinstance(values, dict) or not values:
            raise ValidationError("values must be a non-empty dict of Odoo fields")
        async with self._client() as client:
            result = await self._execute(
                client, model, "write", [[record_id], values]
            )
        return bool(result)

    async def accounting_summary(self) -> dict[str, Any]:
        summary: dict[str, Any] = {"database": self.db}
        async with self._client() as client:
            await self.authenticate(client)

            moves = await self._execute(
                client,
                LEDGER_MODELS["invoices"],
                "search_read",
                [
                    [("state", "in", ("posted", "paid"))],
                    ["amount_total", "state"],
                    200,
                    0,
                ],
            )
            partners = await self._execute(
                client, LEDGER_MODELS["partners"], "search_count", [[[]]]
            )
            products = await self._execute(
                client, LEDGER_MODELS["products"], "search_count", [[[]]]
            )

        posted = [m for m in (moves or []) if isinstance(m, dict)]
        total = sum(float(m.get("amount_total") or 0) for m in posted)
        summary.update(
            posted_invoices=len(posted),
            posted_invoices_total=round(total, 2),
            partners=partners if isinstance(partners, int) else None,
            products=products if isinstance(products, int) else None,
        )
        return summary


def build_client(creds: dict[str, str], default_url: str) -> OdooClient:
    return OdooClient(
        url=creds.get("url") or default_url,
        db=creds["db"],
        username=creds["username"],
        api_key=creds["api_key"],
        api_version=creds.get("api_version"),
    )