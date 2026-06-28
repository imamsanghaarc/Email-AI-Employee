# AI Employee - Multi-Tier Autonomous Framework

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tier System](https://img.shields.io/badge/tiers-Bronze%20%7C%20Silver%20%7C%20Gold-orange)](#-tier-comparison)

A modular, production-ready local AI employee framework built on a structured Obsidian vault system. Provides multi-tier autonomous operations from basic file monitoring to full business autonomy with ERP integrations, social media automation, and executive intelligence reports.

---

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Tier Comparison](#-tier-comparison)
- [Architecture Overview](#-architecture-overview)
- [Core Vault Structure](#-core-vault-structure)
- [Detailed Tier Documentation](#-detailed-tier-documentation)
- [Skills Registry](#-skills-registry-18-skills)
- [MCP Server Integrations](#-mcp-server-integrations)
- [Configuration](#-configuration)
- [Testing & Diagnostics](#-testing--diagnostics)
- [Contributing](#-contributing)

---

## 🚀 Quick Start

```bash
# 1. Clone and install dependencies
git clone <repository-url>
cd ai_employee
pip install playwright requests
playwright install

# 2. Configure credentials
cp .env.example .env  # Create from template
# Edit .env with your API keys and credentials

# 3. Start Bronze Tier (basic monitoring)
python watcher.py

# 4. Or start Silver Tier daemon (advanced operations)
python scripts/run_ai_employee.py --daemon --interval 300

# 5. Or run Gold Tier full autonomy
python scripts/ralph_wiggum_loop.py
```

📖 **See [Setup Guide](SETUP_GUIDE.md) for detailed configuration instructions.**

---

## 📊 Tier Comparison

| Feature | 🥉 Bronze | 🥈 Silver | 🥇 Gold |
|---------|-----------|-----------|---------|
| **Purpose** | Basic Monitoring | Advanced Operations | Full Business Autonomy |
| **Inbox Watching** | ✅ 5s polling | ✅ 20s polling + AI trigger | ✅ Full pipeline |
| **Task Processing** | ✅ Basic | ✅ LLM planning | ✅ Autonomous execution |
| **Daemon Mode** | ❌ | ✅ Configurable intervals | ✅ Continuous loop |
| **Human Approvals** | ❌ | ✅ Blocking workflow | ✅ Risk detection |
| **LLM Integration** | ❌ | ✅ Template + LLM | ✅ 5 API backends |
| **Error Recovery** | ❌ | ✅ Retry logic | ✅ Full quarantine |
| **Social Media** | ❌ | ❌ | ✅ 4 platforms |
| **ERP Integration** | ❌ | ❌ | ✅ Odoo (basic + adv) |
| **Email Monitoring** | ❌ | ❌ | ✅ Gmail IMAP/SMTP |
| **LinkedIn Monitoring** | ❌ | ❌ | ✅ Activity watcher |
| **CEO Briefing** | ❌ | ❌ | ✅ Weekly reports |
| **OS Scheduling** | ❌ | ✅ Cron/Task Scheduler | ✅ Integrated |
| **Docker Support** | ❌ | ❌ | ✅ Odoo + PostgreSQL |

**Choose your tier based on autonomy needs:**
- 🥉 **Bronze**: File monitoring and task tracking
- 🥈 **Silver**: Scheduled autonomous operations with human oversight
- 🥇 **Gold**: Full business automation with external integrations

---

## 🏗 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      AI Employee Framework                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  🥉 Bronze   │  │  🥈 Silver   │  │      🥇 Gold         │  │
│  │              │  │              │  │                      │  │
│  │ • watcher.py │  │ • Scheduler  │  │ • Ralph Wiggum Loop  │  │
│  │ • run_ai.py  │  │ • Watcher    │  │ • CEO Briefing       │  │
│  │ • log_mgr.py │  │ • Planner    │  │ • Social Media (4)   │  │
│  │              │  │ • Approval   │  │ • Odoo MCP (2)       │  │
│  └──────┬───────┘  └──────┬───────┘  │ • Gmail/LinkedIn     │  │
│         │                 │          │ • Error Recovery     │  │
│         └────────┬────────┘          │ • Cron Scheduler     │  │
│                  │                   └──────────┬───────────┘  │
│                  ▼                              │              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Obsidian Vault (Inbox System)               │   │
│  │  Inbox → Needs_Action → Needs_Approval → Done/Errors    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                  │                                              │
│  ┌───────────────▼──────────────────────────────────────────┐  │
│  │              Agent Skills (18 Modules)                    │  │
│  │  task-planner | error-recovery | social-media | email    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              MCP Servers (3 Integrations)                 │   │
│  │  Odoo Basic | Odoo Advanced (Docker) | Business MCP     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### LLM Backend Support

The framework supports **5 LLM backends** for task planning and reasoning:

| Backend | Environment Variable | Used By |
|---------|---------------------|---------|
| **OpenRouter** | `OPENROUTER_API_KEY` | Task Planner |
| **Gemini** | `GEMINI_API_KEY` | Task Planner, CEO Briefing |
| **Claude** | `ANTHROPIC_API_KEY` | Claude Reasoning Loop, Sales Generator |
| **OpenAI** | `OPENAI_API_KEY` | Task Planner, Sales Generator |
| **Template** | N/A | Fallback (no API key required) |

All LLM integrations include graceful fallback to template-based execution if API keys are not configured.

---

## 📁 Core Vault Structure

```
AI_Employee_Vault/
├── Inbox/              # Entry point for new files/tasks
├── Needs_Action/       # Tasks generated by Watcher
├── Needs_Approval/     # Tasks requiring human authorization (Silver+)
├── Done/               # Completed tasks archive
├── Errors/             # Failed tasks for manual review
├── Plans/              # Strategic execution plans
├── Reports/            # Generated reports (CEO Briefing, Social Logs)
├── Accounting/         # Financial tracking (Gold Tier)
│   └── Odoo_Reports/   # Odoo financial reports
├── Logs/               # Runtime logs (git-ignored)
├── Dashboard.md        # Real-time system status
└── Company_Handbook.md # Organizational context
```

### File Lifecycle

```
File added to Inbox/
  → Watcher detects file (5s/20s polling)
  → Creates task file in Needs_Action/
  → Task Planner generates execution plan (LLM or template)
  → Ralph Wiggum Loop executes plan steps (Gold Tier)
  → Risky actions routed to Needs_Approval/ for human review
  → Completed tasks moved to Done/
  → Failed tasks moved to Errors/ with retry scheduling
```

---

## 📚 Detailed Tier Documentation

Each tier has dedicated documentation with API references, configuration options, and troubleshooting:

- **[🥉 Bronze Tier Guide](docs/BRONZE_TIER.md)** - Basic monitoring, watcher, task processor, log management
- **[🥈 Silver Tier Guide](docs/SILVER_TIER.md)** - Daemon scheduling, LLM planning, human approvals, error recovery, cron scheduling
- **[🥇 Gold Tier Guide](docs/GOLD_TIER.md)** - Full autonomy, social media, Odoo ERP, Gmail, LinkedIn, CEO briefing, Docker deployment

---

## 🛠 Skills Registry (18 Skills)

Agent skills are modular capabilities located in `.agents/skills/`. Each skill includes scripts, documentation, and example usage.

### Core Operations

| Skill | Script | Description |
|-------|--------|-------------|
| **file-watcher** | `file_watcher.py` | Vault monitoring and task lifecycle management |
| **task-planner** | `claude_reasoning_loop.py`, `task_planner.py` | LLM-driven execution planning with 5 API backends |
| **vault-file-manager** | `move_task.py` | Atomic file movement between vault directories |
| **error-recovery** | `error_recovery.py` | Automated error handling with 5-minute retry |
| **human-approval** | `request_approval.py` | Blocking human verification workflow |

### Business & Finance

| Skill | Script | Description |
|-------|--------|-------------|
| **odoo-manager** | `accounting_manager.py` | Full Odoo ERP client (accounting, sales, CRM) with JSON-RPC 2.0 |
| **accounting-manager** | `accounting_manager.py` | Business finance tracking in Obsidian vault |
| **ceo-briefing** | `generate_ceo_briefing.py` | Weekly executive report aggregation |

### Communication

| Skill | Script | Description |
|-------|--------|-------------|
| **gmail-watcher** | `watch_gmail.py` | Gmail IMAP monitoring (60s polling, creates tasks) |
| **gmail-send** | `send_email.py` | SMTP email sending via Gmail |
| **linkedin-watcher** | `watch_linkedin.py` | LinkedIn activity monitoring (connections, messages, views) |
| **linkedin-poster** | `linkedin_poster.py` | LinkedIn posting via Playwright |
| **linkedin-sales-generator** | `generate_sales_post.py` | LLM-powered sales content (6 categories) |
| **facebook-poster** | `facebook_post.py` | Facebook page posting via Playwright |
| **twitter-poster** | `twitter_post.py` | Twitter/X posting via Playwright |
| **instagram-poster** | `instagram_post.py` | Instagram posting (mobile emulation) |
| **social-summary** | `social_summary.py` | Social media activity logging |

### Infrastructure

| Skill | Script | Description |
|-------|--------|-------------|
| **scheduler-silver-tier** | `run_ai_employee.py` | Silver Tier daemon orchestration |
| **cron-scheduler** | `setup_scheduler.py`, `run_scheduled.py` | OS-level scheduling (Linux cron + Windows Task Scheduler) |
| **mcp-server** | `mcp_server.py` | External MCP server (HTTP/WebSocket on port 8765) |
| **vault-watcher** | `watch_inbox.py` | Continuous Inbox monitoring with AI trigger |

---

## 🔌 MCP Server Integrations

Model Context Protocol (MCP) servers provide standardized APIs for external business systems.

### 1. Odoo MCP (Basic)

**Path:** `mcp/odoo-mcp/server.py`

JSON-RPC integration with local Odoo Community.

**Tools:**
- `search_read` - Query any Odoo model
- `create_record` - Create new records
- `update_record` - Update existing records
- `get_accounting_summary` - Financial overview

**Configuration:**
```env
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USER=admin
ODOO_PASSWORD=admin
```

### 2. Odoo MCP Advanced (Production)

**Path:** `mcp/mcp-odoo-adv/`

Full-featured Odoo MCP server with enterprise capabilities.

**Features:**
- Multiple transport modes: SSE, HTTP Streamable
- Docker deployment support (3 Dockerfiles)
- Odoo 19+ JSON-RPC 2.0 support
- Production deployment configs
- Comprehensive documentation (CHANGELOG, COOKBOOK, SECURITY, DOCKER, TRANSPORTS)
- Configurable timeouts, SSL, API version options

**Quick Start:**
```bash
cd mcp/mcp-odoo-adv
cp .env.example .env
# Edit .env with your Odoo credentials
python run_server.py  # HTTP mode
# OR
python run_server_sse.py  # SSE mode
```

📖 **See [mcp/mcp-odoo-adv/README.md](mcp/mcp-odoo-adv/README.md) for full documentation.**

### 3. Business MCP

**Path:** `mcp/ex-business-mcp/server.py`

External business action orchestration.

**Tools:**
- `send_email` - SMTP email sending
- `post_linkedin` - LinkedIn posting via Playwright
- `log_activity` - Business activity logging

**Configuration:**
```env
SENDER_EMAIL=your@email.com
SENDER_PASSWORD=your_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
LINKEDIN_EMAIL=your@linkedin.com
LINKEDIN_PASSWORD=your_password
```

### 4. MCP Server Skill (Standalone)

**Path:** `.agents/skills/mcp-server/mcp_server.py`

Standalone MCP server with tool discovery and approval workflow.

**Features:**
- HTTP/WebSocket on port 8765
- Tool discovery and parameter validation
- Built-in approval workflow
- Health check endpoints

---

## ⚙️ Configuration

All credentials are managed via `.env` file at project root.

### Required Variables by Tier

#### Bronze Tier
No configuration required.

#### Silver Tier
```env
# LLM API Keys (at least one recommended)
OPENROUTER_API_KEY=
GEMINI_API_KEY=
ANTHROPIC_API_KEY=
OPENAI_API_KEY=

# System
VAULT_PATH=E:\ai_employee\AI_Employee_Vault
SCHEDULER_INTERVAL=300
```

#### Gold Tier
```env
# Email
EMAIL_ADDRESS=your@email.com
EMAIL_APP_PASSWORD=your_app_password
GMAIL_ADDRESS=your@gmail.com
GMAIL_APP_PASSWORD=your_app_password

# LinkedIn
LINKEDIN_EMAIL=your@linkedin.com
LINKEDIN_PASSWORD=your_password

# Social Media
FB_EMAIL=your@facebook.com
FB_PASSWORD=your_password
TWITTER_USER=your_twitter_handle
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

📖 **See [Setup Guide](SETUP_GUIDE.md) for complete variable reference and setup instructions.**

---

## 🧪 Testing & Diagnostics

The framework includes several diagnostic utilities:

```bash
# Test Odoo connection
python scripts/test_odoo_connection.py

# Test Gemini API
python scripts/test_gemini_api.py

# Test LinkedIn integration
python scripts/test_linkedin_integration.py

# Validate credentials
python scripts/setup_credentials.py

# Check system status (Silver Tier)
python scripts/run_ai_employee.py --status
```

---

## 🐳 Docker Deployment

Gold Tier includes Docker Compose for Odoo 18.0 + PostgreSQL 17:

```bash
# Start Odoo + PostgreSQL
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

📖 **See [docker-compose.yml](docker-compose.yml) for configuration.**

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

### Development Setup

```bash
# Install development dependencies
pip install playwright requests pytest

# Run tests
pytest tests/

# Lint code
flake8 scripts/ .agents/skills/
```

---

## 👥 Contributors & Contact

- **Core Framework**: [imsanghaar](https://github.com/imsanghaar) | [imamsanghaar@gmail.com](mailto:imamsanghaar@gmail.com)
- **Reasoning Engine**: [Qwen](https://chat.qwen.ai)
- **Agent Orchestration**: [Claude Code](https://claude.ai)
- **Intelligence Model**: [Gemini](https://gemini-google.com)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🔗 Additional Resources

- **[Architecture Overview](ARCHITECTURE.md)** - System architecture and design decisions
- **[Operational Mandates](GEMINI.md)** - Workflow specifications and operational rules
- **[Lessons Learned](LESSONS_LEARNED.md)** - Development insights and best practices
- **[LinkedIn Strategy](LINKEDIN_STRATEGY.md)** - Automation approaches and bot detection evasion

---

*AI Employee - From Bronze Foundation to Silver Production-Ready Operations to Gold Full Business Autonomy. A modular framework for local AI-driven business operations.*
