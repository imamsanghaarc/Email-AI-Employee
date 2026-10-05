from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_audit_log_is_truncated_for_large_bodies(storage, monkeypatch):
    from ai_employee_mcp import server
    from ai_employee_mcp.storage.memory import InMemoryStorage

    store = InMemoryStorage(max_audit_entries=3, audit_truncate_chars=5)
    state = type("S", (), {"storage": store})()
    monkeypatch.setattr(server, "get_state", lambda: state)
    for i in range(5):
        await store.append_audit("u", "test", "ok", {"big": "0123456789", "i": i})
    assert len(store.audit_log) == 3
    assert len(store.audit_log[-1]["detail"]["big"]) == 5