---
name: error-recovery
description: Automated error handling and task recovery. Logs errors to logs/errors.log, moves failed files to AI_Employee_Vault/Errors/, and manages a 5-minute background retry. Use when a task fails or a script execution errors.
---

# Error Recovery System

This skill provides a standardized workflow for handling operational failures in the AI Employee system.

## 🚀 Workflows

### 1. Basic Error Handling
Log a failure and move the problematic file to the Errors vault.

```bash
python scripts/error_recovery.py [file_path] "[error_message]"
```

### 2. Error Handling with Automated Retry
Log the error, move the file, and schedule an automatic retry after 5 minutes in the background.

```bash
python scripts/error_recovery.py [file_path] "[error_message]" --retry_cmd "[command_to_retry]"
```

## 📋 Directory Structure
- **Logs**: `logs/errors.log`
- **Error Vault**: `AI_Employee_Vault/Errors/`

## 💡 Usage Guidelines
- Always use this skill when a `run_shell_command` returns a non-zero exit code on a task.
- Provide clear and descriptive error messages for better future diagnosis.
- The `retry_cmd` should be the full command that failed (e.g., `python3 scripts/task_planner.py task_file.md`).
- Files in `Errors/` should be manually reviewed if the retry also fails.
