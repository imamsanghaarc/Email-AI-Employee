# AI Employee MCP Server

An MCP (Model Context Protocol) server that lets AI agents access Odoo, Gmail, and LinkedIn with encrypted credential storage and human approval for write actions.

**MCP URL:** `https://mcp.ai-employee.example.com/mcp` (replace with your deployed HTTP endpoint)

## What this is

AI Employee is a FastMCP server that runs over:
- **stdio** for local use (Claude Desktop, Claude Code, etc.)
- **Streamable HTTP** for hosted use (Cloud Run, Railway, Fly.io, Render)

It gives agents tools for authentication, secure credential storage, Odoo read/write (with approvals), and approval management. No LLMs run inside the server.

## Quick start (hosted HTTP)

Connect any MCP client to:

```text
https://YOUR-DEPLOYED-URL/mcp
```

Your MCP client will treat it as a Streamable HTTP MCP server. No API keys or tokens are baked in — you'll register/login via the MCP tools the client exposes.

## Local usage (stdio)

```bash
# Install
pip install ai-employee-mcp

# Generate encryption key
ai-employee-mcp keygen

# Run
AI_EMPLOYEE_MASTER_KEY=YOUR_KEY AI_EMPLOYEE_JWT_SECRET=YOUR_SECRET ai-employee-mcp --transport stdio
```

Add to Claude Desktop `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ai-employee": {
      "command": "ai-employee-mcp",
      "args": ["--transport", "stdio"],
      "env": {
        "AI_EMPLOYEE_MASTER_KEY": "...",
        "AI_EMPLOYEE_JWT_SECRET": "..."
      }
    }
  }
}
```

## Tools (what agents can call)

- `register(email, password)` – create account
- `login(email, password)` – get session token
- `logout()` – revoke session
- `whoami()` – check auth + configured providers
- `save_credentials(provider, credentials)` – store encrypted creds (partial saves supported)
- `credentials_status()` – see missing/configured fields (no secrets returned)
- `disconnect_provider(provider)` – remove stored creds
- `odoo_search_read(model, domain?, fields?, limit?, offset?)` – read Odoo data
- `odoo_create_record(model, values, approval_id?)` – create (requires approval)
- `odoo_update_record(model, record_id, values, approval_id?)` – update (requires approval)
- `odoo_accounting_summary()` – posted invoices/partners/products
- `approval_status(approval_id)` – poll approval
- `pending_approvals()` – list pending approvals

## Environment (required for hosted)

| Env | Required | Notes |
|---|---|---|
| `AI_EMPLOYEE_MASTER_KEY` | Yes | Base64 32-byte key. Run `ai-employee-mcp keygen` to generate. |
| `AI_EMPLOYEE_JWT_SECRET` | Yes (prod) | Random secret for signing session tokens. |

Optional: `AI_EMPLOYEE_REQUIRE_APPROVAL_FOR_SIDE_EFFECTS` (default `true`), `AI_EMPLOYEE_HOST` (default `127.0.0.1`), `AI_EMPLOYEE_PORT` (default `8080`), `AI_EMPLOYEE_STATIC_TOKEN`/`AI_EMPLOYEE_STATIC_USER_ID` (local-only).

## How to publish to PyPI

1. **Update version** (optional) — edit `pyproject.toml` `version = "0.1.0"` to e.g. `0.1.1`.
2. **Build**:
   ```bash
   python -m build
   ```
3. **Test on TestPyPI first** (recommended):
   ```bash
   twine upload --repository testpypi dist/*
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ ai-employee-mcp
   ```
4. **Publish to PyPI**:
   ```bash
   twine upload dist/*
   ```
5. **Install**:
   ```bash
   pip install ai-employee-mcp
   ```

## License

MIT