#!/usr/bin/env python3
"""
Error Recovery System - Automated error handling and task recovery.
Logs errors to logs/errors.log, moves failed files to AI_Employee_Vault/Errors/,
and manages a 5-minute background retry.
"""

import os
import sys
import time
import argparse
import subprocess
import threading
from datetime import datetime

# --- CONFIGURATION ---
VAULT_DIR = "AI_Employee_Vault"
ERRORS_DIR = os.path.join(VAULT_DIR, "Errors")
ERROR_LOG = "logs/errors.log"
RETRY_DELAY = 300  # 5 minutes

def ensure_dirs():
    """Ensure required directories exist."""
    os.makedirs(ERRORS_DIR, exist_ok=True)
    os.makedirs("logs", exist_ok=True)

def log_error(message, level="ERROR"):
    """Log error to errors.log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [{level}] {message}"
    print(entry)

    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        f.write(entry + "\n")

def move_to_errors(file_path, error_message=None):
    """Move a failed file to the Errors vault."""
    if not os.path.exists(file_path):
        log_error(f"File not found, cannot move to errors: {file_path}", "WARNING")
        return False

    ensure_dirs()

    filename = os.path.basename(file_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    error_filename = f"error_{timestamp}_{filename}"
    dest_path = os.path.join(ERRORS_DIR, error_filename)

    try:
        # Read file content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Add error context
        if error_message:
            error_context = f"""---
error_at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
error_message: {error_message}
original_file: {filename}
---

{content}
"""
        else:
            error_context = content

        # Write to Errors directory
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(error_context)

        # Remove original file
        os.remove(file_path)

        log_error(f"Moved to Errors: {filename} -> {error_filename}")
        return True

    except Exception as e:
        log_error(f"Failed to move file to Errors: {e}")
        return False

def schedule_retry(retry_cmd, file_path=None):
    """Schedule a background retry after 5 minutes."""
    def retry_task():
        log_error(f"Waiting {RETRY_DELAY}s before retry: {retry_cmd}", "RETRY")
        time.sleep(RETRY_DELAY)

        log_error(f"Executing retry: {retry_cmd}", "RETRY")
        try:
            result = subprocess.run(
                retry_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                log_error(f"Retry SUCCESS: {retry_cmd}", "RETRY")
                # Move file back from Errors if it was moved there
                if file_path and file_path.startswith(ERRORS_DIR):
                    original_name = "_".join(os.path.basename(file_path).split("_")[2:])
                    original_path = os.path.join(VAULT_DIR, "Needs_Action", original_name)
                    os.makedirs(os.path.dirname(original_path), exist_ok=True)
                    os.rename(file_path, original_path)
                    log_error(f"Restored file to Needs_Action: {original_name}", "RETRY")
            else:
                log_error(f"Retry FAILED (code {result.returncode}): {result.stderr}", "RETRY")
                # Second failure - leave in Errors for manual review
                log_error(f"File remains in Errors for manual review: {file_path}", "RETRY")

        except subprocess.TimeoutExpired:
            log_error(f"Retry TIMED OUT: {retry_cmd}", "RETRY")
        except Exception as e:
            log_error(f"Retry ERROR: {e}", "RETRY")

    # Start retry in background thread
    thread = threading.Thread(target=retry_task, daemon=True)
    thread.start()
    log_error(f"Background retry scheduled: {retry_cmd}")
    return thread

def handle_error(file_path, error_message, retry_cmd=None):
    """Main error handling workflow."""
    log_error(f"Error detected: {file_path} - {error_message}")

    # 1. Log the error
    log_error(f"Processing error recovery for: {os.path.basename(file_path)}")

    # 2. Move file to Errors vault
    moved = move_to_errors(file_path, error_message)

    if not moved:
        log_error("Failed to move file to Errors directory", "CRITICAL")
        return False

    # 3. Schedule retry if command provided
    if retry_cmd:
        error_file = os.path.join(ERRORS_DIR, [f for f in os.listdir(ERRORS_DIR)
                                                if os.path.basename(file_path) in f][-1])
        schedule_retry(retry_cmd, error_file)

    return True

def main():
    parser = argparse.ArgumentParser(description="Error Recovery System")
    parser.add_argument("file_path", help="Path to the file that caused the error")
    parser.add_argument("error_message", help="Description of the error")
    parser.add_argument("--retry_cmd", help="Command to retry with after 5 minutes", default=None)

    args = parser.parse_args()

    success = handle_error(args.file_path, args.error_message, args.retry_cmd)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
