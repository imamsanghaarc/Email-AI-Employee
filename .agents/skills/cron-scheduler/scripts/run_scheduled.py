#!/usr/bin/env python3
"""
Run Scheduled Task - Wrapper for executing AI Employee tasks with logging and error handling.
"""

import os
import sys
import subprocess
import logging
from datetime import datetime

# Configuration
LOG_FILE = "logs/cron_scheduler.log"
LOCK_DIR = "logs"

# Ensure directories exist
os.makedirs("logs", exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Task definitions
TASKS = {
    "gmail_watcher": {
        "script": ".agents/skills/gmail-watcher/scripts/watch_gmail.py",
        "description": "Monitor Gmail for new emails",
        "timeout": 120
    },
    "linkedin_watcher": {
        "script": ".agents/skills/linkedin-watcher/scripts/watch_linkedin.py",
        "description": "Monitor LinkedIn activity",
        "timeout": 180
    },
    "task_planner": {
        "script": ".agents/skills/task-planner/scripts/claude_reasoning_loop.py",
        "description": "Generate execution plans",
        "timeout": 300
    },
    "task_processor": {
        "script": "run_ai_employee.py",
        "description": "Process completed tasks",
        "args": ["--once"],
        "timeout": 120
    },
    "linkedin_post": {
        "script": ".agents/skills/linkedin-business-poster/scripts/post_business_content.py",
        "description": "Publish LinkedIn business post",
        "args": ["--template", "thought_leadership"],
        "timeout": 180
    },
    "log_rotation": {
        "script": "log_manager.py",
        "description": "Rotate log files",
        "timeout": 60
    }
}


def acquire_lock(task_name):
    """Acquire a lock file to prevent duplicate executions."""
    lock_file = os.path.join(LOCK_DIR, f"{task_name}.lock")
    
    if os.path.exists(lock_file):
        try:
            with open(lock_file, "r") as f:
                pid = int(f.read().strip())
            # Check if process is running
            os.kill(pid, 0)
            logger.warning(f"Task {task_name} is already running (PID: {pid})")
            return False
        except (ProcessLookupError, ValueError, OSError):
            # Process not running, remove stale lock
            os.remove(lock_file)
    
    with open(lock_file, "w") as f:
        f.write(str(os.getpid()))
    
    return True


def release_lock(task_name):
    """Release the lock file."""
    lock_file = os.path.join(LOCK_DIR, f"{task_name}.lock")
    if os.path.exists(lock_file):
        os.remove(lock_file)


def run_task(task_name):
    """Execute a scheduled task with error handling."""
    if task_name not in TASKS:
        logger.error(f"Unknown task: {task_name}")
        return False
    
    task = TASKS[task_name]
    
    # Acquire lock
    if not acquire_lock(task_name):
        return False
    
    try:
        logger.info(f"Starting task: {task_name} - {task['description']}")
        
        # Build command
        cmd = [sys.executable, task["script"]]
        if "args" in task:
            cmd.extend(task["args"])
        
        # Execute task
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=task.get("timeout", 300)
        )
        
        if result.returncode == 0:
            logger.info(f"SUCCESS: {task_name} completed")
            if result.stdout:
                logger.info(f"Output: {result.stdout[:200]}")
            return True
        else:
            logger.error(f"FAILED: {task_name} exited with code {result.returncode}")
            if result.stderr:
                logger.error(f"Error: {result.stderr[:500]}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"TIMEOUT: {task_name} exceeded time limit")
        return False
    except Exception as e:
        logger.error(f"ERROR: {task_name} failed with exception: {e}")
        return False
    finally:
        release_lock(task_name)


def list_tasks():
    """List all available tasks."""
    print("\nAvailable scheduled tasks:")
    print("-" * 60)
    
    for name, task in TASKS.items():
        print(f"  {name:20} - {task['description']}")
    
    print()


def show_status():
    """Show status of scheduled tasks."""
    print("\nTask Execution Status:")
    print("-" * 60)
    
    for task_name in TASKS.keys():
        lock_file = os.path.join(LOCK_DIR, f"{task_name}.lock")
        status = "RUNNING" if os.path.exists(lock_file) else "IDLE"
        print(f"  {task_name:20} - {status}")
    
    print()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Scheduled Task")
    parser.add_argument("--task", type=str, help="Task name to execute")
    parser.add_argument("--list", action="store_true", help="List available tasks")
    parser.add_argument("--status", action="store_true", help="Show task status")
    
    args = parser.parse_args()
    
    if args.list:
        list_tasks()
    elif args.status:
        show_status()
    elif args.task:
        success = run_task(args.task)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
