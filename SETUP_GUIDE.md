# Setup Guide - AI Employee Configuration

## Overview

This guide covers all configuration options for the AI Employee framework. Credentials are managed via `.env` file at the project root.

---

## Quick Start

```bash
# 1. Copy the example template (if available)
cp .env.example .env

# 2. Or create from scratch
touch .env  # Linux/Mac
echo. > .env  # Windows

# 3. Edit with your credentials
# Use any text editor
```

---

## Environment Variables by Tier

### 🥉 Bronze Tier

**No configuration required.** Bronze Tier works out of the box with default settings.

Optional:
```env
# Custom vault path (default: AI_Employee_Vault/)
VAULT_PATH=E:\ai_employee\AI_Employee_Vault
```

---

### 🥈 Silver Tier

#### LLM API Keys (Recommended - At Least One)

| Variable | Provider | Get Key From |
|----------|----------|--------------|
| `OPENROUTER_API_KEY` | OpenRouter | https://openrouter.ai/keys |
| `GEMINI_API_KEY` | Google Gemini | https://aistudio.google.com/app/apikey |
| `ANTHROPIC_API_KEY` | Anthropic Claude | https://console.anthropic.com/ |
| `OPENAI_API_KEY` | OpenAI | https://platform.openai.com/api-keys |

#### Model Selection (Optional)

```env
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
GEMINI_MODEL=gemini-2.0-flash
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
OPENAI_MODEL=gpt-4o
```

#### System Settings

```env
# Vault path
VAULT_PATH=E:\ai_employee\AI_Employee_Vault

# Scheduler interval (seconds)
SCHEDULER_INTERVAL=300

# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
```

---

### 🥇 Gold Tier

#### Email Configuration

```env
# Gmail Watcher (IMAP)
GMAIL_ADDRESS=your@gmail.com
GMAIL_APP_PASSWORD=your_app_password

# Gmail Sender (SMTP)
EMAIL_ADDRESS=your@gmail.com
EMAIL_APP_PASSWORD=your_app_password
```

**Creating Gmail App Password:**
1. Go to https://myaccount.google.com/apppasswords
2. Sign in to your Google Account
3. Select "App" > "Mail" > "Other (Custom name)"
4. Enter "AI Employee" as the name
5. Copy the 16-character password

#### LinkedIn Configuration

```env
LINKEDIN_EMAIL=your@linkedin.com
LINKEDIN_PASSWORD=your_password
```

#### Social Media Credentials

```env
# Facebook
FB_EMAIL=your@facebook.com
FB_PASSWORD=your_password

# Twitter/X
TWITTER_USER=your_twitter_handle
TWITTER_PASSWORD=your_password

# Instagram
INSTA_USER=your_insta_handle
INSTA_PASSWORD=your_password
```

#### Odoo ERP Configuration

```env
# Basic Odoo Connection
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USER=admin
ODOO_PASSWORD=admin

# Advanced Odoo (optional)
ODOO_API_VERSION=
ODOO_API_KEY=
```

#### LLM APIs (At Least One Required)

```env
# Choose at least one
OPENROUTER_API_KEY=your_key
GEMINI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
```

#### Business Context (for Sales Content)

```env
COMPANY_NAME=Your Company Name
BUSINESS_DESCRIPTION=What your business does
TARGET_AUDIENCE=Who you serve (e.g., "Small business owners")
KEY_SERVICES=Your main offerings (e.g., "Web development, SEO")
CALL_TO_ACTION=What you want prospects to do (e.g., "Book a free consultation")
```

#### MCP Server Configuration

```env
# MCP Server Settings
MCP_HOST=0.0.0.0
MCP_PORT=8765
MCP_SSE_PATH=/sse
MCP_HTTP_PATH=/http
```

---

## Complete Variable Reference

| Variable | Required By | Tier | Description |
|----------|-------------|------|-------------|
| `VAULT_PATH` | All components | All | Path to Obsidian vault |
| `SCHEDULER_INTERVAL` | Silver scheduler | Silver+ | Seconds between cycles |
| `LOG_LEVEL` | All loggers | All | Logging verbosity |
| `OPENROUTER_API_KEY` | Task Planner | Silver+ | OpenRouter API |
| `GEMINI_API_KEY` | Task Planner, CEO Briefing | Silver+ | Google Gemini API |
| `ANTHROPIC_API_KEY` | Claude Loop, Sales Gen | Silver+ | Anthropic Claude API |
| `OPENAI_API_KEY` | Task Planner, Sales Gen | Silver+ | OpenAI GPT API |
| `OPENROUTER_MODEL` | Task Planner | Silver+ | Model for OpenRouter |
| `GEMINI_MODEL` | Task Planner | Silver+ | Model for Gemini |
| `ANTHROPIC_MODEL` | Claude Loop, Sales Gen | Silver+ | Model for Claude |
| `OPENAI_MODEL` | Task Planner, Sales Gen | Silver+ | Model for OpenAI |
| `EMAIL_ADDRESS` | Gmail Sender, MCP | Gold | Gmail address |
| `EMAIL_APP_PASSWORD` | Gmail Sender, MCP | Gold | Gmail app password |
| `GMAIL_ADDRESS` | Gmail Watcher | Gold | Gmail for IMAP watching |
| `GMAIL_APP_PASSWORD` | Gmail Watcher | Gold | Gmail app password |
| `LINKEDIN_EMAIL` | LinkedIn Poster, Watcher | Gold | LinkedIn email |
| `LINKEDIN_PASSWORD` | LinkedIn Poster, Watcher | Gold | LinkedIn password |
| `FB_EMAIL` | Facebook Poster | Gold | Facebook email |
| `FB_PASSWORD` | Facebook Poster | Gold | Facebook password |
| `TWITTER_USER` | Twitter Poster | Gold | Twitter handle |
| `TWITTER_PASSWORD` | Twitter Poster | Gold | Twitter password |
| `INSTA_USER` | Instagram Poster | Gold | Instagram username |
| `INSTA_PASSWORD` | Instagram Poster | Gold | Instagram password |
| `ODOO_URL` | Odoo MCP | Gold | Odoo server URL |
| `ODOO_DB` | Odoo MCP | Gold | Odoo database name |
| `ODOO_USER` | Odoo MCP | Gold | Odoo username |
| `ODOO_PASSWORD` | Odoo MCP | Gold | Odoo password/API key |
| `ODOO_API_VERSION` | Odoo MCP Advanced | Gold | API version (optional) |
| `ODOO_API_KEY` | Odoo MCP Advanced | Gold | API key (optional) |
| `COMPANY_NAME` | Sales Generator | Gold | Company name |
| `BUSINESS_DESCRIPTION` | Sales Generator | Gold | Business description |
| `TARGET_AUDIENCE` | Sales Generator | Gold | Target audience |
| `KEY_SERVICES` | Sales Generator | Gold | Key services offered |
| `CALL_TO_ACTION` | Sales Generator | Gold | Call to action |
| `MCP_HOST` | MCP Server | Gold | MCP server host |
| `MCP_PORT` | MCP Server | Gold | MCP server port |
| `MCP_SSE_PATH` | MCP Server | Gold | SSE endpoint path |
| `MCP_HTTP_PATH` | MCP Server | Gold | HTTP endpoint path |
| `SENDER_EMAIL` | Business MCP | Gold | SMTP sender email |
| `SENDER_PASSWORD` | Business MCP | Gold | SMTP sender password |
| `SMTP_SERVER` | Business MCP | Gold | SMTP server address |
| `SMTP_PORT` | Business MCP | Gold | SMTP server port |

---

## Configuration Validation

### Test All Credentials

```bash
python scripts/setup_credentials.py
```

This script validates all required environment variables are present and properly formatted.

### Test Individual Integrations

```bash
# Test Odoo connection
python scripts/test_odoo_connection.py

# Test Gemini API
python scripts/test_gemini_api.py

# Test LinkedIn integration
python scripts/test_linkedin_integration.py
```

---

## Docker Configuration

### Odoo MCP Advanced

```bash
cd mcp/mcp-odoo-adv

# Copy example config
cp .env.example .env

# Edit with your Odoo credentials
# ODOO_URL=http://your-odoo-server.com
# ODOO_DB=your_database
# ODOO_USERNAME=your_username
# ODOO_PASSWORD=your_password
```

### Docker Compose

```bash
# Start Odoo + PostgreSQL
docker-compose up -d

# Access Odoo at http://localhost:8069
# Default credentials: admin / admin
```

---

## Troubleshooting

### Missing Credentials Error

If you see errors like:
```
KeyError: 'LINKEDIN_EMAIL'
```

**Solution:** Add the missing variable to `.env` and restart the service.

### Invalid Credentials Error

If authentication fails:
```
AuthenticationError: Invalid credentials for LinkedIn
```

**Solutions:**
1. Verify username/password are correct
2. Check for extra whitespace in `.env`
3. Ensure 2FA is not blocking login (use app passwords)
4. Test with manual login first

### Gmail App Password Issues

**Common Problems:**
- Using regular password instead of app password
- 2-Step Verification not enabled
- App password not generated for "Other" category

**Solution:**
1. Enable 2-Step Verification in Google Account
2. Generate app password: https://myaccount.google.com/apppasswords
3. Select "Other" and enter "AI Employee"
4. Copy the 16-character password (no spaces)

### Odoo Connection Fails

**Check:**
1. Odoo server is running: `http://localhost:8069`
2. Database name is correct
3. Username/password are valid
4. API key is configured (if using Odoo 19+)

**Test:**
```bash
python scripts/test_odoo_connection.py
```

### LLM API Not Working

**Verify:**
1. API key is correct (no extra spaces)
2. Account has sufficient credits/quota
3. Model name is valid
4. Network connectivity to API endpoint

**Test:**
```bash
python scripts/test_gemini_api.py  # For Gemini
# Or check logs for other providers
```

---

## Security Best Practices

### 1. Protect Your `.env` File

```bash
# Ensure .env is in .gitignore
echo ".env" >> .gitignore

# Set restrictive permissions (Linux/Mac)
chmod 600 .env

# Never commit .env to version control
```

### 2. Use App Passwords

Never use your main account passwords. Always generate app-specific passwords:
- **Gmail**: https://myaccount.google.com/apppasswords
- **LinkedIn**: Use account email/password (no app passwords)
- **Other services**: Check security settings

### 3. Rotate Credentials Regularly

- Change API keys every 90 days
- Review app passwords quarterly
- Monitor for unauthorized access

### 4. Principle of Least Privilege

- Grant only required permissions to API keys
- Use separate service accounts where possible
- Avoid using personal accounts for automation

---

## Next Steps

- **[Bronze Tier Guide](docs/BRONZE_TIER.md)** - Basic monitoring setup
- **[Silver Tier Guide](docs/SILVER_TIER.md)** - Advanced autonomous operations
- **[Gold Tier Guide](docs/GOLD_TIER.md)** - Full business autonomy
- **[README](README.md)** - Main project documentation

---

*Configuration complete! You're ready to run AI Employee.*
