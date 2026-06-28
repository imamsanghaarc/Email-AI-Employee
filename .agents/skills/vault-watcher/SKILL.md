---
name: vault-watcher
description: Continuously monitors the Obsidian vault's Inbox folder for new Markdown files and triggers the AI processing workflow. Use this skill when you need to enable automatic task detection and processing.
---

# Vault Watcher Skill

This skill provides a continuous monitoring system for the AI Employee's inbox. It acts as the "trigger" for the Bronze Tier's autonomous functionality.

## Goal
To automate the detection of new tasks and initiate their processing without manual intervention.

## Components
- **Monitoring Folder**: `AI_Employee_Vault/Inbox`
- **Detection Log**: `logs/actions.log`
- **Processing Trigger**: `python run_ai_employee.py --once`
- **Script Location**: `scripts/watch_inbox.py` (also available at `.agents/skills/vault-watcher/scripts/watch_inbox.py`)

## Usage Instructions

### Starting the Watcher
To start the watcher, run the following command in a background terminal or as a separate process:

```bash
python scripts/watch_inbox.py
# or
python .agents/skills/vault-watcher/scripts/watch_inbox.py
```

### How it Works
1. The script scans the `Inbox` folder every 20 seconds.
2. When a new `.md` file is detected:
   - It logs the event in `logs/actions.log`.
   - It executes the AI processing workflow using `run_ai_employee.py`.
3. It keeps track of processed files to ensure no file is handled twice within the same session.

## Rules
- **Lightweight**: The watcher is designed for minimal CPU usage.
- **Production Ready**: Includes error handling and graceful shutdown.
- **No Simulation**: Triggers actual file operations as defined in the processing script.
- **Scope**: Limited to `.md` files in the `Inbox` directory.
