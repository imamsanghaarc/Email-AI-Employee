# 🏗️ AI Employee Architecture

## Overview
The AI Employee is a modular, multi-tier autonomous framework designed to manage business operations, accounting, and social presence. It follows the **Model Context Protocol (MCP)** and utilizes a structured **Obsidian Vault** for long-term memory and human interaction.

## 🧱 Core Components

### 1. The Vault (`AI_Employee_Vault/`)
- **Inbox**: Raw data and incoming requests.
- **Needs_Action**: Structured tasks for the AI.
- **Done**: Archival of completed tasks.
- **Reports**: Weekly strategic summaries.
- **Accounting**: Real-time financial tracking (using local Markdown file for now).
- **Errors**: Failed tasks for review.
- **Plans**: Generated execution plans.
- **Needs_Approval**: Tasks awaiting human decision.

### 2. Autonomous Loops
- **Watcher**: Triggers actions based on file system changes (`watcher.py`, `scripts/watch_inbox.py`).
- **Task Planner**: Generates multi-step execution plans. Uses LLM (OpenRouter) or template fallback (`scripts/task_planner.py`, `.agents/skills/task-planner/`).
- **Ralph Wiggum Loop**: Iteratively executes plan steps with safety checks and human approval (`scripts/ralph_wiggum_loop.py`).

### 3. Integrations (MCP & Skills)
- **Odoo MCP:** JSON-RPC integration for accounting (`mcp/odoo-mcp/server.py`). Requires `.env` credentials.
- **Business MCP:** General actions (Email, LinkedIn) (`mcp/ex-business-mcp/server.py`).
- **Social Posters:** Playwright-based automation for FB, IG, TW (`scripts/facebook_post.py`, `instagram_post.py`, `twitter_post.py`). Requires `.env` credentials and potential manual login.
- **Error Recovery Skill:** Handles task failures (`.agents/skills/error-recovery/`).
- **Social Summary Skill:** Logs social posts (`.agents/skills/social-summary/`).

## 🛡️ Safety & Reliability
- **Human-in-the-Loop:** Critical actions require `APPROVED` state via `scripts/request_approval.py`.
- **Error Recovery:** Automatic logging to `logs/errors.log`, file movement to `AI_Employee_Vault/Errors/`, and background retries.
- **Log Rotation:** `log_manager.py` handles log file size management.
- **Concurrency Control:** Lock file mechanism in `scripts/run_ai_employee.py` prevents duplicate daemon runs.

## ⚙️ Configuration

- **`.env` file:** Stores all sensitive credentials (Odoo, LinkedIn, FB, Insta, Twitter, LLM API keys).
- **Odoo:** Requires `ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_PASSWORD` (API Key).
- **Social Media:** Requires credentials for each platform (`FB_EMAIL`, `FB_PASSWORD`, `INSTA_USER`, etc.).
- **LLM:** `OPENROUTER_API_KEY` for task planning.

## 🚀 Key Workflows

1.  **Task Processing:** File in `Inbox` -> `watcher.py` -> `task-planner` (LLM/Template) -> `Needs_Action` -> `run_ai_employee.py` (calls `task_planner`, `ralph_wiggum_loop`) -> `Done`.
2.  **CEO Briefing:** `scripts/generate_ceo_briefing_pro.py` aggregates data from Odoo, social logs, task completion, and system health. Scheduled via `cron-scheduler` skill.
3.  **External Actions:** MCP servers (`odoo-mcp`, `ex-business-mcp`) and direct scripts (`linkedin_post_direct.py`) handle external integrations.

## 🔧 Tooling & Dependencies

- **Python 3.10+**
- **Playwright:** For browser automation.
- **Requests:** For HTTP calls (Odoo MCP, OpenRouter).
- **Odoorpc:** For Odoo interaction.
- **Anthropic/OpenAI SDKs:** Optional, for LLM planning fallback.
- **Gemini/OpenRouter:** Primary LLM for planning.
