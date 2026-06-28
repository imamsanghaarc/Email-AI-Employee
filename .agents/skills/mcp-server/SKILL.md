---
name: mcp-server
description: MCP (Model Context Protocol) server for external actions like sending emails, posting to social media, and other integrations. Provides standardized API for AI Employee to execute external actions. Use when AI needs to perform external actions beyond the vault system.
---

# MCP Server

Provides external action capabilities for the AI Employee via Model Context Protocol (MCP) server.

## Overview

Runs an MCP server that exposes external actions (email sending, social media posting, etc.) as standardized tools. Allows the AI Employee to perform real-world actions beyond file management.

## Components

- **Server Script**: `scripts/mcp_server.py`
- **Tools**: External action implementations in `scripts/tools/`
- **Log**: `logs/mcp_server.log`

## Usage

### Start MCP Server
```bash
python .agents/skills/mcp-server/scripts/mcp_server.py
```

### Test Available Tools
```bash
python .agents/skills/mcp-server/scripts/mcp_server.py --list-tools
```

### Configuration
Requires `.env` file with service credentials:
```env
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_APP_PASSWORD=your-app-password
LINKEDIN_EMAIL=your-linkedin-email
LINKEDIN_PASSWORD=your-linkedin-password
```

## Available Tools

### 1. send_email
Sends emails via SMTP.

**Parameters:**
```json
{
  "to": "recipient@example.com",
  "subject": "Email Subject",
  "body": "Email body content",
  "html": true
}
```

**Example:**
```bash
curl -X POST http://localhost:8765/tools/send_email \
  -H "Content-Type: application/json" \
  -d '{"to": "user@example.com", "subject": "Test", "body": "Hello!"}'
```

### 2. post_linkedin
Posts content to LinkedIn.

**Parameters:**
```json
{
  "content": "LinkedIn post content",
  "require_approval": false
}
```

### 3. check_gmail
Checks Gmail for new emails.

**Parameters:**
```json
{
  "max_results": 10
}
```

### 4. check_linkedin
Checks LinkedIn for new activity.

**Parameters:**
```json
{
  "activity_types": ["connections", "messages", "views"]
}
```

## MCP Protocol

The server implements the Model Context Protocol, providing:

1. **Tool Discovery**: AI can query available tools
2. **Parameter Validation**: Ensures correct tool usage
3. **Execution**: Runs tools and returns results
4. **Error Handling**: Standardized error responses

## Server Endpoints

- **HTTP**: `http://localhost:8765` (default)
- **WebSocket**: `ws://localhost:8765/ws` (for streaming)

### API Endpoints

```
GET  /tools                  - List all available tools
POST /tools/{tool_name}      - Execute a tool
GET  /health                 - Health check
POST /tools/{tool_name}/approve - Approve pending action
```

## Integration with AI Employee

The MCP server integrates with the AI Employee workflow:

1. **Task Processing**: AI calls MCP tools when executing tasks
2. **Approval Workflow**: Sensitive actions require human approval via vault
3. **Logging**: All tool executions logged to `logs/mcp_server.log`
4. **Error Recovery**: Failed actions create error tasks in Needs_Action

## Adding New Tools

To add a new tool:

1. Create tool script in `scripts/tools/`
2. Implement `execute()` function with parameters
3. Register tool in `mcp_server.py`
4. Restart MCP server

### Tool Template

```python
def send_email(params):
    """Send an email."""
    required = ["to", "subject", "body"]
    for param in required:
        if param not in params:
            return {"error": f"Missing parameter: {param}"}
    
    # Implementation here
    return {"status": "success", "message": "Email sent"}
```

## Rules

- **Security**: Credentials stored in `.env`, never exposed
- **Validation**: All parameters validated before execution
- **Logging**: Every tool execution logged with timestamp
- **Rate Limiting**: Prevents abuse (configurable per tool)
- **Approval**: Sensitive actions can require human approval
- **Error Handling**: Graceful failures with detailed error messages

## Troubleshooting

**Port Already in Use**: Change port with `--port` flag
**Tool Not Found**: Check tool is registered in mcp_server.py
**Credential Error**: Verify `.env` file has correct credentials
**Connection Refused**: Ensure server is running
