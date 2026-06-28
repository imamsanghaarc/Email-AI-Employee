---
name: scheduler-silver-tier
description: Orchestrates the vault-watcher and task-planner in a continuous or single-pass loop. Supports daemon mode, status reporting, and automatic log rotation.
---

# Silver Tier Scheduler Skill

This skill provides the main orchestration layer for the AI Employee. It manages the lifecycle of tasks from detection to execution.

## Goal
To provide a reliable, single entry point for the AI Employee's autonomous operations, ensuring that tasks are processed consistently and that system status is always available.

## Components
- **Orchestrator**: `scripts/run_ai_employee.py` (also available at `.agents/skills/scheduler-silver-tier/scripts/run_ai_employee.py`)
- **Logging**: `logs/ai_employee.log` (Rotates at 5MB)
- **Locking**: `logs/ai_employee.lock` (Prevents duplicate instances)
- **Dependencies**:
  - `scripts/task_planner.py`
  - `run_ai_employee.py` (root script for task processing)

## CLI Usage

### Status Check
View current file counts in all vault folders and check if the daemon is active:
```bash
python scripts/run_ai_employee.py --status
# or
python .agents/skills/scheduler-silver-tier/scripts/run_ai_employee.py --status
```

### Single Execution Pass
Run one cycle of planning and processing:
```bash
python scripts/run_ai_employee.py --once
```

### Daemon Mode
Run the AI Employee continuously (default interval: 5 minutes):
```bash
python scripts/run_ai_employee.py --daemon
```

Override the default interval (e.g., every 60 seconds):
```bash
python scripts/run_ai_employee.py --daemon --interval 60
```

## Rules
- **Idempotency**: Leverages downstream scripts to ensure no file is processed twice.
- **Persistence**: Log rotation prevents log files from consuming excessive disk space.
- **Safety**: File locking ensures that multiple schedulers do not conflict.
- **Traceability**: All sub-processes (Planner, Runner) have their outputs captured in the main scheduler log.
