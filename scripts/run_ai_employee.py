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
            # Check if process is actually running (cross-platform)
            if sys.platform == "win32":
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.OpenProcess(0x0400, False, pid)
                if handle:
                    kernel32.CloseHandle(handle)
                    logger.error(f"Another instance is already running (PID: {pid}).")
                    return False
            else:
                os.kill(pid, 0)
                logger.error(f"Another instance is already running (PID: {pid}).")
                return False
        except (ProcessLookupError, ValueError, OSError, AttributeError):
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
    
    # 1. Run Watcher/Detector logic
    logger.info("Running Task Planner...")
    result = subprocess.run([sys.executable, "scripts/task_planner.py"], capture_output=True, text=True)
    if result.stdout:
        for line in result.stdout.splitlines():
            logger.info(f"[PLANNER] {line}")
    
    # 2. Check Needs_Action and require approval
    NEEDS_ACTION_DIR = os.path.join(VAULT_DIR, "Needs_Action")
    for filename in os.listdir(NEEDS_ACTION_DIR):
        if filename.endswith(".md"):
            logger.info(f"Task found: {filename}. Requesting human approval...")
            
            # Move to Needs_Approval
            import shutil
            approval_path = os.path.join(VAULT_DIR, "Needs_Approval", filename)
            os.makedirs(os.path.join(VAULT_DIR, "Needs_Approval"), exist_ok=True)
            shutil.move(os.path.join(NEEDS_ACTION_DIR, filename), approval_path)
            
            # Call the approval script
            approval_result = subprocess.run([sys.executable, "scripts/request_approval.py", filename], capture_output=True)
            
            if approval_result.returncode != 0:
                logger.warning(f"Task {filename} was not APPROVED. Aborting execution.")
                continue
            
            # If approved, move to Done for execution
            # The script renames the file to silver_verify.md.approved
            # We need to find the approved file correctly
            approved_file = os.path.join(VAULT_DIR, "Needs_Approval", filename + ".approved")
            if not os.path.exists(approved_file):
                # Try simple filename if not renamed
                approved_file = os.path.join(VAULT_DIR, "Needs_Approval", filename)
                
            shutil.move(approved_file, os.path.join(VAULT_DIR, "Done", filename))
            logger.info(f"Task {filename} APPROVED. Moving to Done.")
    
    # 3. Execute Ralph Wiggum Autonomous Loop
    logger.info("Starting Ralph Wiggum Autonomous Execution Loop...")
    if os.path.exists("scripts/ralph_wiggum_loop.py"):
        result = subprocess.run([sys.executable, "scripts/ralph_wiggum_loop.py"], capture_output=True, text=True)
        if result.stdout:
            for line in result.stdout.splitlines():
                logger.info(f"[RALPH-WIGGUM] {line}")
    else:
        logger.warning("scripts/ralph_wiggum_loop.py not found. Skipping autonomous loop.")

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
