# External Business Action MCP Server (`ex-business-mcp`)

A production-ready Model Context Protocol (MCP) server for automating external business operations.

## 🚀 Capabilities

- **`send_email(to, subject, body)`**: Sends professional emails via SMTP (Gmail/Outlook/Custom).
- **`post_linkedin(content)`**: Publishes updates to LinkedIn using integrated browser automation.
- **`log_activity(message)`**: Centralized logging of all business actions to `AI_Employee_Vault/Logs/business.log`.

---

## 🛠️ Configuration

The server requires specific environment variables for authentication and security. These should be set in your system environment or provided during server launch.

### Email Configuration (SMTP)
- `SENDER_EMAIL`: Your full email address (e.g., `user@gmail.com`).
- `SENDER_PASSWORD`: Your email app password (for Gmail, generate an [App Password](https://myaccount.google.com/apppasswords)).
- `SMTP_SERVER`: (Optional) Defaults to `smtp.gmail.com`.
- `SMTP_PORT`: (Optional) Defaults to `587`.

### LinkedIn Configuration
- `LINKEDIN_EMAIL`: Your LinkedIn login email.
- `LINKEDIN_PASSWORD`: Your LinkedIn login password.

---

## 🏗️ Setup & Installation

### 1. Requirements
- Python 3.10+
- `mcp` Python SDK
- `playwright` (for LinkedIn automation)

### 2. Install Dependencies
```bash
pip install mcp playwright
playwright install chromium
```

### 3. Usage with Claude Desktop / MCP Clients
Add the following to your MCP configuration file (e.g., `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ex-business-mcp": {
      "command": "python3",
      "args": ["/absolute/path/to/mcp/ex-business-mcp/server.py"],
      "env": {
        "SENDER_EMAIL": "your-email@gmail.com",
        "SENDER_PASSWORD": "your-app-password",
        "LINKEDIN_EMAIL": "your-linkedin-email",
        "LINKEDIN_PASSWORD": "your-linkedin-password"
      }
    }
  }
}
```

---

## 📋 Operational Logs
Business activities are tracked in:
`AI_Employee_Vault/Logs/business.log`

Example entry:
`[2026-04-11 14:30:00] BUSINESS: EMAIL SENT: To client@example.com | Subject: New Proposal`

---

## 🛡️ Security & Production Readiness
- **Credential Protection**: Credentials are never hardcoded and must be provided via environment variables.
- **Error Handling**: Comprehensive try-except blocks with detailed error reporting.
- **Audit Trail**: Every automated action triggers an entry in the business log.
- **Integration**: Leverages the existing `linkedin_post_direct.py` script for robust browser automation.
