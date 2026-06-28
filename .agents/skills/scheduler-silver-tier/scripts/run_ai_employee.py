import os
import sys
import argparse
import time
import logging
import subprocess
from logging.handlers import RotatingFileHandler
from datetime import datetime

# --- CONFIGURATION ---
VAULT_DIR = "AI_Employee_Vault"
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "ai_employee.log")
LOCK_FILE = os.path.join(LOG_DIR, "ai_employee.lock")
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3
DEFAULT_INTERVAL = 300  # 5 minutes

# Ensure directories
os.makedirs(LOG_DIR, exist_ok=True)

# --- LOGGING SETUP ---
logger = logging.getLogger("AI_Employee")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
# Also log to console
console = logging.StreamHandler()
console.setFormatter(formatter)
logger.addHandler(console)

def acquire_lock():
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                pid = int(f.read().strip())
            # Check if process is actually running
            os.kill(pid, 0)
            logger.error(f"Another instance is already running (PID: {pid}).")
            return False
        except (ProcessLookupError, ValueError, OSError):
            # Process is not running or PID file is invalid
            logger.warning("Found stale lock file. Overwriting...")
    
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
    return True

def release_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

def get_status():
    status = "--- AI Employee Status ---\n"
    counts = {
        "Inbox": len([f for f in os.listdir(os.path.join(VAULT_DIR, "Inbox")) if os.path.isfile(os.path.join(VAULT_DIR, "Inbox", f))]),
        "Needs_Action": len([f for f in os.listdir(os.path.join(VAULT_DIR, "Needs_Action")) if os.path.isfile(os.path.join(VAULT_DIR, "Needs_Action", f))]),
        "Needs_Approval": len([f for f in os.listdir(os.path.join(VAULT_DIR, "Needs_Approval")) if os.path.isfile(os.path.join(VAULT_DIR, "Needs_Approval", f))]),
        "Done": len([f for f in os.listdir(os.path.join(VAULT_DIR, "Done")) if os.path.isfile(os.path.join(VAULT_DIR, "Done", f))]),
    }
    for folder, count in counts.items():
        status += f"{folder:15}: {count} files\n"
    
    if os.path.exists(LOCK_FILE):
        status += "Status         : ACTIVE (Daemon Running)\n"
    else:
        status += "Status         : INACTIVE\n"
    
    return status

def execute_pass():
    """Executes a single pass of the watcher and planner logic."""
    logger.info("Starting execution pass...")
    
    # 1. Run Watcher/Detector logic (we use the script as a one-shot here by moving files)
    # Actually, let's call our existing scripts
    try:
        # Step A: Detect and Plan (Task Planner)
        # Note: task_planner.py already moves Inbox -> Done and generates Plan.md
        logger.info("Running Task Planner...")
        result = subprocess.run(["python3", "scripts/task_planner.py"], capture_output=True, text=True)
        if result.stdout:
            for line in result.stdout.splitlines():
                logger.info(f"[PLANNER] {line}")
        
        # Step B: Process Tasks (AI Runner - logic from the old root script)
        # We can call the old script if it still exists, or use its logic.
        # Let's assume the user wants run_ai_employee.py to be the orchestration point.
        logger.info("Running AI Processing Workflow...")
        # Since I'm creating this in scripts/, I should refer to the logic or the root script.
        # Let's try to run the root script with --once if it exists.
        if os.path.exists("run_ai_employee.py"):
            result = subprocess.run(["python3", "run_ai_employee.py", "--once"], capture_output=True, text=True)
            if result.stdout:
                for line in result.stdout.splitlines():
                    logger.info(f"[RUNNER] {line}")
        else:
            logger.warning("Root run_ai_employee.py not found. Skipping AI runner phase.")

    except Exception as e:
        logger.error(f"Error during execution pass: {e}")

def main():
    parser = argparse.ArgumentParser(description="AI Employee Silver Tier Scheduler")
    parser.add_argument("--daemon", action="store_true", help="Run continuously in the background")
    parser.add_argument("--once", action="store_true", help="Run a single execution pass")
    parser.add_argument("--status", action="store_true", help="Show active tasks & inbox count")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL, help="Interval in seconds for daemon mode")
    
    args = parser.parse_args()

    if args.status:
        print(get_status())
        return

    if not acquire_lock():
        sys.exit(1)

    try:
        if args.once:
            execute_pass()
        elif args.daemon:
            logger.info(f"Daemon mode started. Interval: {args.interval}s")
            while True:
                execute_pass()
                logger.info(f"Sleeping for {args.interval} seconds...")
                time.sleep(args.interval)
        else:
            parser.print_help()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        release_lock()

if __name__ == "__main__":
    main()
