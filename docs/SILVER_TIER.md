# 🥈 Silver Tier - Advanced Autonomous Operations

## Overview

The Silver Tier introduces scheduling, daemon management, human approvals, enhanced task planning, and error recovery. This is the production-ready tier for organizations needing autonomous operations with human oversight.

**Purpose:** Scheduled autonomous operations with human-in-the-loop approvals

**Complexity:** Medium | **Autonomy Level:** Advanced with oversight

---

## Components

### 1. Silver Tier Scheduler (`scripts/run_ai_employee.py`)

The central orchestrator for Silver Tier operations.

#### Features
- **Daemon Mode**: Runs continuously with configurable intervals
- **Single Pass Mode**: Execute once and exit
- **Lock Management**: Prevents multiple instances from running
- **Rotating Logs**: 5MB max log size with automatic rotation
- **Status Reporting**: View system health and queue counts

#### Running the Scheduler

```bash
# Start daemon mode (continuous execution every 5 minutes)
python scripts/run_ai_employee.py --daemon --interval 300

# Single execution pass
python scripts/run_ai_employee.py --once

# Check system status
python scripts/run_ai_employee.py --status
```

#### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--daemon` | Run in daemon mode (continuous) | False |
| `--interval N` | Seconds between cycles (daemon mode) | 300 |
| `--once` | Single execution pass and exit | False |
| `--status` | Show system status and exit | False |
| `--log-level LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO |

#### Daemon Mode Behavior

```python
# Pseudocode
acquire_lock()  # Prevent duplicate instances
try:
    while running:
        process_inbox()
        execute_tasks()
        cleanup()
        sleep(interval)
except KeyboardInterrupt:
    release_lock()
    cleanup()
```

---

### 2. Enhanced Inbox Watcher (`scripts/watch_inbox.py`)

Enhanced watcher with integrated AI processing triggering.

#### Features
- Monitors Inbox every **20 seconds** (configurable)
- Automatically moves files to Needs_Action
- Triggers AI processing workflow when new files detected
- Comprehensive logging to `logs/actions.log`

#### Running the Watcher
```bash
python scripts/watch_inbox.py
```

#### Differences from Bronze Watcher

| Feature | Bronze `watcher.py` | Silver `scripts/watch_inbox.py` |
|---------|---------------------|--------------------------------|
| Polling interval | 5 seconds | 20 seconds |
| AI processing | ❌ | ✅ Triggers automatically |
| Logging | `System_Log.md` | `logs/actions.log` |
| Error handling | Basic | Comprehensive |

---

### 3. Task Planner (`scripts/task_planner.py`)

Generates strategic execution plans for incoming tasks.

#### Features
- Reads files from Inbox and generates step-by-step plans
- Creates/updates `Plan.md` in Needs_Action directory
- Automatically moves planned files to Done
- Template-based plan generation (no API key required)
- LLM integration fallback (OpenRouter, Gemini, Claude, OpenAI)

#### Plan Generation Flow

```
Task file in Inbox/
  → Task Planner reads task
  → Generates execution plan:
    - If LLM configured: Calls API for intelligent planning
    - If no LLM: Uses template-based generation
  → Creates Plan_YYYY-MM-DD_HH-MM-SS.md in Plans/
  → Moves task to Needs_Action/ with plan reference
```

#### LLM Configuration

At least one of the following environment variables enables LLM planning:

```env
OPENROUTER_API_KEY=your_key
GEMINI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
```

---

### 4. Claude Reasoning Loop (`scripts/claude_reasoning_loop.py`)

LLM-driven planning engine supporting **5 API backends**.

#### Supported Backends

| Backend | Environment Variables | Model Selection |
|---------|----------------------|-----------------|
| **OpenRouter** | `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` | Multi-model routing |
| **Gemini** | `GEMINI_API_KEY`, `GEMINI_MODEL` | Google's Gemini |
| **Claude** | `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` | Anthropic Claude |
| **OpenAI** | `OPENAI_API_KEY`, `OPENAI_MODEL` | GPT-4/3.5 |
| **Template** | None required | Rule-based fallback |

#### Running the Reasoning Loop
```bash
python scripts/claude_reasoning_loop.py
```

#### Testing LLM Connectivity
```bash
# Test Gemini API
python scripts/test_gemini_api.py

# Test all configured APIs
python scripts/setup_credentials.py
```

---

### 5. Human Approval System (`scripts/request_approval.py`)

Implements human-in-the-loop decision making for sensitive operations.

#### Features
- Creates approval request files in `Needs_Approval/`
- Blocks execution until human provides APPROVED or REJECTED
- Configurable timeout (default: 1 hour)
- Renames files with `.approved`, `.rejected`, or `.timedout` suffixes
- Polls every 5 seconds for response

#### Risk Detection Keywords

The following keywords trigger human approval requests:
- `post`, `send`, `delete`, `remove`, `email`
- `update`, `create`, `modify`, `publish`

#### Running the Approval System

```bash
# Request approval for an action
python scripts/request_approval.py <filename>

# With custom timeout (seconds)
python scripts/request_approval.py <filename> --timeout 3600
```

#### Approval File Format

```markdown
---
type: approval_request
status: pending
created_at: 2026-04-13 10:30:00
timeout: 3600
action: "post to LinkedIn"
---

# Approval Request: Post to LinkedIn

## Action Details
- **Platform**: LinkedIn
- **Content**: "Excited to announce..."
- **Risk Level**: Medium

## Instructions
Write APPROVED or REJECTED in this file to allow or block the action.
```

#### Approval Workflow

```
Risky action detected
  → Creates file in Needs_Approval/
  → Execution blocks (polls every 5s)
  → Human reviews and writes APPROVED or REJECTED
  → File renamed with suffix (.approved/.rejected/.timedout)
  → Execution continues or aborts based on response
```

---

### 6. Ralph Wiggum Autonomous Loop (`scripts/ralph_wiggum_loop.py`)

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

| Mechanism | Description |
|-----------|-------------|
| **Max Iterations** | Limits execution to 5 iterations per cycle |
| **Risk Detection** | Scans for sensitive keywords before execution |
| **Human Approval** | Routes risky actions to Needs_Approval/ |
| **Lock Files** | Prevents duplicate daemon instances |
| **Graceful Shutdown** | Handles Ctrl+C and releases resources |
| **No Simulation Rule** | Always performs actual file operations |

---

### 7. Error Recovery (`scripts/error_recovery.py`)

Automated error handling and task recovery.

#### Features
- Logs errors to `logs/errors.log`
- Moves failed files to `AI_Employee_Vault/Errors/`
- Manages a 5-minute background retry
- Comprehensive error tracking with timestamps

#### Running Error Recovery

```bash
# Handle a failed task
python scripts/error_recovery.py <file_path> <error_message> --retry_cmd "<command>"

# Example
python scripts/error_recovery.py AI_Employee_Vault/Needs_Action/task_123.md "API timeout" --retry_cmd "python scripts/task_planner.py"
```

#### Error Recovery Flow

```
Task fails during execution
  → Logged to logs/errors.log
  → File moved to AI_Employee_Vault/Errors/
  → Background retry scheduled (5-minute delay)
  → Retry executes
  → Success: file restored to Needs_Action/
  → Failure: file remains in Errors/ for manual review
```

---

### 8. Cron Scheduler (`.agents/skills/cron-scheduler/`)

OS-level scheduling for Linux cron and Windows Task Scheduler.

#### Features
- **Linux**: Cron job configuration with templates
- **Windows**: Task Scheduler XML import
- **Wrapper Scripts**: `run_scheduled.py` for reliable execution
- **Failure Notifications**: Email alerts on failures

#### Setting Up Scheduled Execution

**Linux (Cron):**
```bash
# Edit crontab
crontab -e

# Add line (every 5 minutes)
*/5 * * * * cd /path/to/ai_employee && python scripts/run_ai_employee.py --once >> logs/cron.log 2>&1
```

**Windows (Task Scheduler):**
```bash
# Import task from XML
schtasks /create /tn "AI Employee" /xml .agents/skills/cron-scheduler/windows_task.xml
```

---

## Logs & Monitoring

| Log File | Purpose | Rotation |
|----------|---------|----------|
| `logs/ai_employee.log` | Silver Tier scheduler log | 5MB auto-rotate |
| `logs/actions.log` | Detailed execution history | 2MB + archive |
| `logs/ralph_wiggum.log` | Autonomous loop activities | 2MB + archive |
| `logs/errors.log` | Error tracking and recovery | 2MB + archive |
| `System_Log.md` | High-level AI activities | Manual |

---

## System Status

Check system health at any time:

```bash
python scripts/run_ai_employee.py --status
```

**Sample Output:**
```
=== AI Employee Status ===
Daemon: Running (PID: 12345)
Last run: 2026-04-13 10:30:00
Next run: 2026-04-13 10:35:00

Queue Status:
  Inbox: 0 files
  Needs_Action: 2 files
  Needs_Approval: 1 file
  Errors: 0 files

Log Size: 2.3MB / 5MB
```

---

## Upgrading to Gold Tier

Silver Tier provides robust autonomous operations. Upgrade to [Gold Tier](GOLD_TIER.md) for:

- ✅ Social media automation (LinkedIn, Facebook, Twitter, Instagram)
- ✅ Odoo ERP integration (Accounting, CRM, Sales)
- ✅ Gmail monitoring and sending
- ✅ LinkedIn activity watching and sales content generation
- ✅ Weekly CEO Briefing reports
- ✅ Docker deployment for Odoo
- ✅ Full business autonomy

---

## Troubleshooting

### Daemon not starting
1. Check for lock file: `ls *.lock`
2. Remove stale lock: `rm ai_employee.lock`
3. Check logs: `tail -f logs/ai_employee.log`

### Approval requests timing out
1. Verify human is monitoring `Needs_Approval/`
2. Increase timeout: `--timeout 7200` (2 hours)
3. Check file permissions on approval files

### Error recovery not retrying
1. Check `Errors/` directory for failed files
2. Verify retry command is valid
3. Review `logs/errors.log` for error details

### LLM planning not working
1. Verify API keys in `.env`
2. Test connectivity: `python scripts/test_gemini_api.py`
3. Check fallback to template mode in logs

---

## Next Steps

- **[Bronze Tier Guide](BRONZE_TIER.md)** - Basic monitoring (prerequisites)
- **[Gold Tier Guide](GOLD_TIER.md)** - Full business autonomy with ERP and social media
- **[Setup Guide](../SETUP_GUIDE.md)** - Configuration reference
- **[Architecture Overview](../ARCHITECTURE.md)** - System design
