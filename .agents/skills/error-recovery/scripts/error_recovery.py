import os
import sys
import shutil
import time
import argparse
import subprocess
from datetime import datetime

# --- CONFIGURATION ---
ERROR_LOG = "logs/errors.log"
ERRORS_VAULT = "AI_Employee_Vault/Errors/"
RETRY_DELAY = 300  # 5 minutes in seconds

def log_error(file_path, error_msg):
    """Log the error to logs/errors.log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] ERROR: {file_path} - {error_msg}\n"
    os.makedirs(os.path.dirname(ERROR_LOG), exist_ok=True)
    with open(ERROR_LOG, "a") as f:
        f.write(entry)
    print(f"Logged error for {file_path}")

def move_to_errors(file_path):
    """Move the failing file to AI_Employee_Vault/Errors/."""
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return None
    
    os.makedirs(ERRORS_VAULT, exist_ok=True)
    filename = os.path.basename(file_path)
    dest_path = os.path.join(ERRORS_VAULT, filename)
    
    try:
        shutil.move(file_path, dest_path)
        print(f"Moved {filename} to {ERRORS_VAULT}")
        return dest_path
    except Exception as e:
        print(f"Error moving file: {e}")
        return None

def handle_retry(file_path, command):
    """Wait 5 minutes and retry the command once in the background."""
    print(f"Retry scheduled for {file_path} in {RETRY_DELAY/60} minutes...")
    
    # Simple background retry using a detached process
    retry_cmd = f"sleep {RETRY_DELAY} && {command}"
    try:
        # We use Popen to run it in the background without blocking
        subprocess.Popen(retry_cmd, shell=True, start_new_session=True)
        print("Background retry process started.")
    except Exception as e:
        print(f"Failed to start background retry: {e}")

def main():
    parser = argparse.ArgumentParser(description="Error Recovery System")
    parser.add_argument("file_path", help="Path to the failing file")
    parser.add_argument("error_msg", help="Error message to log")
    parser.add_argument("--retry_cmd", help="Command to run for retry (optional)")
    
    args = parser.parse_args()
    
    # 1. Log the error
    log_error(args.file_path, args.error_msg)
    
    # 2. Move the file to Errors/
    moved_path = move_to_errors(args.file_path)
    
    # 3. If retry command provided, schedule retry
    if args.retry_cmd and moved_path:
        # Update command to use the new path if necessary
        # This is a simplistic replacement; assumes the command took the file path as an arg
        new_cmd = args.retry_cmd.replace(args.file_path, moved_path)
        handle_retry(moved_path, new_cmd)

if __name__ == "__main__":
    main()
