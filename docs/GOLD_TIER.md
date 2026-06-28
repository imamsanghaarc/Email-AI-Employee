# 🥇 Gold Tier - Full Business Autonomy

## Overview

The Gold Tier represents the pinnacle of AI Employee automation, integrating with external business systems, automating social media presence, and generating executive-level business intelligence reports.

**Purpose:** Full business autonomy with external system integrations

**Complexity:** High | **Autonomy Level:** Full (with safety mechanisms)

---

## Architecture

Gold Tier builds on Silver Tier capabilities and adds:

```
┌─────────────────────────────────────────────────────────────┐
│                    Gold Tier Components                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Ralph       │  │  CEO         │  │  Social Media    │  │
│  │  Wiggum      │  │  Briefing    │  │  Automation      │  │
│  │  Loop        │  │  Generator   │  │  Suite           │  │
│  │              │  │              │  │                  │  │
│  │ • Autonomous │  │ • Financial  │  │ • LinkedIn       │  │
│  │   execution  │  │   reports    │  │ • Facebook       │  │
│  │ • Risk       │  │ • Task       │  │ • Twitter/X      │  │
│  │   detection  │  │   analytics  │  │ • Instagram      │  │
│  │ • Approval   │  │ • System     │  │                  │  │
│  │   routing    │  │   health     │  │                  │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
│         │                 │                    │            │
│  ┌──────▼─────────────────▼────────────────────▼─────────┐  │
│  │              MCP Server Integrations                   │  │
│  │                                                        │  │
│  │  • Odoo MCP (Basic) - JSON-RPC to Odoo Community      │  │
│  │  • Odoo MCP Advanced - Docker, SSE, HTTP, Prod-ready  │  │
│  │  • Business MCP - Email, LinkedIn, Logging            │  │
│  │  • MCP Server Skill - HTTP/WebSocket on 8765          │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              Communication Channels                     │  │
│  │                                                        │  │
│  │  • Gmail Watcher - IMAP monitoring (60s)              │  │
│  │  • Gmail Sender - SMTP email sending                   │  │
│  │  • LinkedIn Watcher - Activity monitoring (300s)       │  │
│  │  • LinkedIn Sales Generator - LLM content creation     │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Ralph Wiggum Autonomous Loop

**Path:** `scripts/ralph_wiggum_loop.py`

Fully autonomous task execution with built-in safety mechanisms.

#### Features
- **Iterative Execution**: Processes plan steps one at a time with verification
- **Risk Detection**: Identifies dangerous keywords (post, send, delete, email, etc.)
- **Human Approval Integration**: Automatically routes risky actions to `Needs_Approval/`
- **Iteration Limits**: Prevents runaway execution (`MAX_ITERATIONS = 5`)
- **Comprehensive Logging**: All activities logged to `logs/ralph_wiggum.log`

#### Running the Loop
```bash
python scripts/ralph_wiggum_loop.py
```

#### Safety Mechanisms

| Mechanism | Description | Configuration |
|-----------|-------------|---------------|
| **Max Iterations** | Limits execution per cycle | `MAX_ITERATIONS = 5` |
| **Risk Detection** | Scans for sensitive keywords | `RISKY_KEYWORDS = [...]` |
| **Human Approval** | Routes risky actions | Automatic |
| **Lock Files** | Prevents duplicate instances | `ai_employee.lock` |
| **Graceful Shutdown** | Handles Ctrl+C | Signal handler |

---

### 2. CEO Briefing Generator

**Path:** `scripts/generate_ceo_briefing_pro.py`

Comprehensive weekly business intelligence reporting.

#### Report Sections
- **Financial Data**: Pulls real accounting data from Odoo via MCP/JSON-RPC
- **Social Media Activity**: Aggregates posting logs and engagement metrics
- **Task Completion**: Analyzes completed tasks and productivity metrics
- **System Health**: Reports on daemon status, error rates, and recovery success
- **Strategic Insights**: AI-generated recommendations based on weekly performance

#### Running the Briefing
```bash
python scripts/generate_ceo_briefing_pro.py
```

**Output:** `AI_Employee_Vault/Reports/CEO_Weekly_Gold.md`

#### Prerequisites
- Odoo MCP configured (at least basic)
- Social media logs present in `Reports/Social_Logs.md`
- Completed tasks in `Done/` directory

---

### 3. Social Media Automation Suite

All social media posting uses **Playwright browser automation** for reliable, API-independent posting.

#### LinkedIn Posting (`scripts/linkedin_post_direct.py`)

**Features:**
- Playwright-based browser automation
- Direct posting without API dependencies
- Credential-based authentication via `.env`
- Supports rich text formatting and hashtags

**Running:**
```bash
python scripts/linkedin_post_direct.py "Your post content here #hashtags"
```

**Configuration:**
```env
LINKEDIN_EMAIL=your@linkedin.com
LINKEDIN_PASSWORD=your_password
```

#### Facebook Posting (`scripts/facebook_post.py`)

**Features:**
- Automated Facebook page updates
- Browser automation via Playwright
- Business page management integration

**Running:**
```bash
python scripts/facebook_post.py "Your business update here"
```

**Configuration:**
```env
FB_EMAIL=your@facebook.com
FB_PASSWORD=your_password
```

#### Twitter/X Posting (`scripts/twitter_post.py`)

**Features:**
- Automated tweet generation and posting
- Character count validation (280 limit)
- Hashtag and mention support

**Running:**
```bash
python scripts/twitter_post.py "Your tweet here @mentions #hashtags"
```

**Configuration:**
```env
TWITTER_USER=your_handle
TWITTER_PASSWORD=your_password
```

#### Instagram Posting (`scripts/instagram_post.py`)

**Features:**
- Photo and caption posting automation
- Browser-based authentication
- Hashtag optimization support
- Mobile emulation via iPhone 12 device profile

**Running:**
```bash
python scripts/instagram_post.py "caption" --image "path/to/image.jpg"
```

**Configuration:**
```env
INSTA_USER=your_insta_handle
INSTA_PASSWORD=your_password
```

---

### 4. LinkedIn Sales Content Generator

**Path:** `.agents/skills/linkedin-sales-generator/generate_sales_post.py`

LLM-powered sales content creation for LinkedIn.

#### Content Categories (6 Types)
1. **Problem Awareness** - Highlight pain points your audience faces
2. **Case Study** - Share success stories and results
3. **Tip Series** - Educational content with actionable advice
4. **Direct Offer** - Clear calls-to-action for your services
5. **Thought Leadership** - Industry insights and perspectives
6. **Social Proof** - Testimonials, reviews, and endorsements

#### Running the Sales Generator
```bash
python .agents/skills/linkedin-sales-generator/generate_sales_post.py
```

**Configuration:**
```env
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
COMPANY_NAME=Your Company
BUSINESS_DESCRIPTION=What your business does
TARGET_AUDIENCE=Who you serve
KEY_SERVICES=Your main offerings
CALL_TO_ACTION=What you want prospects to do
```

---

### 5. Gmail Integration

#### Gmail Watcher (`scripts/watch_gmail.py`)

Monitors Gmail inbox for new emails and creates tasks.

**Features:**
- IMAP polling every **60 seconds**
- Creates task files in Inbox for new emails
- Stateful tracking via JSON state file
- Unread email detection

**Running:**
```bash
python scripts/watch_gmail.py
```

**Configuration:**
```env
GMAIL_ADDRESS=your@gmail.com
GMAIL_APP_PASSWORD=your_app_password
```

#### Gmail Sender (`.agents/skills/gmail-send/send_email.py`)

Send real emails via SMTP.

**Running:**
```python
from send_email import send_email

send_email(
    to="recipient@example.com",
    subject="Your Subject",
    body="Your message here"
)
```

**Configuration:**
```env
EMAIL_ADDRESS=your@gmail.com
EMAIL_APP_PASSWORD=your_app_password
```

---

### 6. LinkedIn Activity Watcher

**Path:** `scripts/watch_linkedin.py`

Monitors LinkedIn for new connections, messages, and opportunities.

**Features:**
- Playwright-based browser automation
- Polls every **300 seconds** (5 minutes)
- Monitors:
  - New connections
  - New messages
  - Profile views
  - Job posts
- Creates tasks for new activity

**Running:**
```bash
python scripts/watch_linkedin.py
```

**Configuration:**
```env
LINKEDIN_EMAIL=your@linkedin.com
LINKEDIN_PASSWORD=your_password
```

---

## 🔌 MCP Server Integrations

### 1. Odoo MCP (Basic)

**Path:** `mcp/odoo-mcp/server.py`

JSON-RPC integration with local Odoo Community.

#### Available Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `search_read` | Query any Odoo model | `model`, `domain`, `fields` |
| `create_record` | Create new records | `model`, `values` |
| `update_record` | Update existing records | `model`, `id`, `values` |
| `get_accounting_summary` | Financial overview | None |

#### Running the Server
```bash
cd mcp/odoo-mcp
python server.py
```

**Configuration:**
```env
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USER=admin
ODOO_PASSWORD=admin
```

#### Testing Connection
```bash
python scripts/test_odoo_connection.py
```

---

### 2. Odoo MCP Advanced (Production)

**Path:** `mcp/mcp-odoo-adv/`

Full-featured Odoo MCP server with enterprise capabilities.

#### Features
- **Multiple Transport Modes**: SSE, HTTP Streamable
- **Docker Deployment**: 3 Dockerfiles for different environments
- **Odoo 19+ Support**: JSON-RPC 2.0 protocol
- **Production Ready**: Comprehensive deployment configs
- **Configurable**: Timeouts, SSL, API version options

#### Documentation
- `CHANGELOG.md` - Version history
- `COOKBOOK.md` - Usage examples
- `SECURITY.md` - Security best practices
- `DOCKER.md` - Docker deployment guide
- `TRANSPORTS.md` - Transport mode configuration

#### Quick Start
```bash
cd mcp/mcp-odoo-adv

# Copy configuration
cp .env.example .env
# Edit .env with your credentials

# Run server
python run_server.py        # HTTP mode
python run_server_sse.py    # SSE mode
python run_server_http.py   # HTTP Streamable mode
```

#### Docker Deployment
```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

**Configuration Reference:**
```env
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USERNAME=admin
ODOO_PASSWORD=admin
MCP_TRANSPORT=http  # http, sse, http_streamable
MCP_HOST=0.0.0.0
MCP_PORT=8765
REQUEST_TIMEOUT=30
SSL_ENABLED=false
```

📖 **See [mcp/mcp-odoo-adv/README.md](../mcp/mcp-odoo-adv/README.md) for full documentation.**

---

### 3. Business MCP

**Path:** `mcp/ex-business-mcp/server.py`

External business action orchestration.

#### Available Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `send_email` | SMTP email sending | `to`, `subject`, `body` |
| `post_linkedin` | LinkedIn posting | `content` |
| `log_activity` | Business activity logging | `activity`, `details` |

#### Running the Server
```bash
cd mcp/ex-business-mcp
python server.py
```

**Configuration:**
```env
SENDER_EMAIL=your@email.com
SENDER_PASSWORD=your_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
LINKEDIN_EMAIL=your@linkedin.com
LINKEDIN_PASSWORD=your_password
```

---

### 4. MCP Server Skill (Standalone)

**Path:** `.agents/skills/mcp-server/mcp_server.py`

Standalone MCP server with tool discovery and approval workflow.

#### Features
- HTTP/WebSocket on port **8765**
- Tool discovery and parameter validation
- Built-in approval workflow
- Health check endpoints

#### Running the Server
```bash
python .agents/skills/mcp-server/mcp_server.py
```

**Endpoints:**
- `GET /health` - Health check
- `GET /tools` - Available tools list
- `POST /call` - Execute tool

---

## 🐳 Docker Deployment

Gold Tier includes Docker Compose for **Odoo 18.0 + PostgreSQL 17**.

### Running with Docker

```bash
# Start Odoo + PostgreSQL
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes (caution: deletes data)
docker-compose down -v
```

### Accessing Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **Odoo** | http://localhost:8069 | admin / admin |
| **PostgreSQL** | localhost:5432 | odoo / odoo |

### Docker Configuration

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  web:
    image: odoo:18.0
    depends_on:
      - db
    ports:
      - "8069:8069"
    environment:
      - HOST=db
      - USER=odoo
      - PASSWORD=odoo
  db:
    image: postgres:17
    environment:
      - POSTGRES_USER=odoo
      - POSTGRES_PASSWORD=odoo
      - POSTGRES_DB=postgres
```

---

## 📊 Social Media Summary

| Platform | Script | Auth | Features |
|----------|--------|------|----------|
| **LinkedIn** | `linkedin_post_direct.py` | Email/Password | Rich text, hashtags |
| **Facebook** | `facebook_post.py` | Email/Password | Page updates |
| **Twitter/X** | `twitter_post.py` | User/Password | 280 chars, mentions |
| **Instagram** | `instagram_post.py` | User/Password | Photos, mobile emulation |

### Social Activity Logging

All social media activity is logged to:
- `AI_Employee_Vault/Reports/Social_Logs.md` - Activity log
- `.agents/skills/social-summary/social_summary.py` - Logging utility

---

## 🔧 Testing & Diagnostics

```bash
# Test Odoo connection
python scripts/test_odoo_connection.py

# Test Gemini API
python scripts/test_gemini_api.py

# Test LinkedIn integration
python scripts/test_linkedin_integration.py

# Validate all credentials
python scripts/setup_credentials.py

# Check system status
python scripts/run_ai_employee.py --status
```

---

## ⚙️ Configuration

### Required Environment Variables

```env
# Email
EMAIL_ADDRESS=your@gmail.com
EMAIL_APP_PASSWORD=your_app_password
GMAIL_ADDRESS=your@gmail.com
GMAIL_APP_PASSWORD=your_app_password

# LinkedIn
LINKEDIN_EMAIL=your@linkedin.com
LINKEDIN_PASSWORD=your_password

# Social Media
FB_EMAIL=your@facebook.com
FB_PASSWORD=your_password
TWITTER_USER=your_handle
TWITTER_PASSWORD=your_password
INSTA_USER=your_insta_handle
INSTA_PASSWORD=your_password

# Odoo ERP
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USER=admin
ODOO_PASSWORD=admin
ODOO_API_VERSION=
ODOO_API_KEY=

# LLM APIs (at least one required)
OPENROUTER_API_KEY=
GEMINI_API_KEY=
ANTHROPIC_API_KEY=
OPENAI_API_KEY=

# Business Context
COMPANY_NAME=Your Company
BUSINESS_DESCRIPTION=What your business does
TARGET_AUDIENCE=Who you serve
KEY_SERVICES=Your main offerings
CALL_TO_ACTION=What you want prospects to do

# MCP Server
MCP_HOST=0.0.0.0
MCP_PORT=8765
MCP_SSE_PATH=/sse
MCP_HTTP_PATH=/http
```

📖 **See [Setup Guide](../SETUP_GUIDE.md) for complete variable reference.**

---

## 📈 Weekly CEO Briefing Workflow

```
Every Monday (or manual trigger)
  ↓
generate_ceo_briefing_pro.py executes
  ↓
  ├─ Pull financial data from Odoo (JSON-RPC)
  ├─ Read social media logs
  ├─ Analyze completed tasks
  ├─ Check system health metrics
  └─ Generate AI-powered insights
  ↓
Report saved to Reports/CEO_Weekly_Gold.md
  ↓
Report available for review and distribution
```

---

## 🔒 Safety Mechanisms

Gold Tier includes comprehensive safety features:

| Mechanism | Description |
|-----------|-------------|
| **Risk Detection** | Scans for keywords: post, send, delete, email, etc. |
| **Human Approval** | Routes risky actions to Needs_Approval/ |
| **Max Iterations** | Limits autonomous loops to 5 iterations |
| **Lock Files** | Prevents duplicate daemon instances |
| **Graceful Shutdown** | Handles Ctrl+C and releases resources |
| **Error Quarantine** | Failed tasks moved to Errors/ for review |
| **No Simulation Rule** | Always performs actual operations |
| **Audit Trail** | Comprehensive logging of all activities |

---

## 📚 Additional Resources

- **[LinkedIn Strategy](../LINKEDIN_STRATEGY.md)** - Automation approaches and bot detection evasion
- **[Odoo MCP Advanced](../mcp/mcp-odoo-adv/README.md)** - Production deployment guide
- **[Architecture Overview](../ARCHITECTURE.md)** - System design
- **[Silver Tier Guide](SILVER_TIER.md)** - Scheduling and human approvals
- **[Setup Guide](../SETUP_GUIDE.md)** - Configuration reference

---

## 🚀 Production Deployment Checklist

- [ ] All credentials configured in `.env`
- [ ] Odoo ERP connection tested
- [ ] Social media credentials verified
- [ ] LLM API keys configured and tested
- [ ] Docker services running (if using Odoo)
- [ ] CEO Briefing generated successfully
- [ ] Error recovery tested
- [ ] Human approval workflow verified
- [ ] Logs rotating properly
- [ ] Daemon mode running stably

---

*Gold Tier - Full Business Autonomy with Enterprise-Grade Integrations*
