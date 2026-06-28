import os
import time
import subprocess
from datetime import datetime

# --- CONFIGURATION ---
INBOX_DIR = "AI_Employee_Vault/Inbox"
LOG_FILE = "logs/actions.log"
CHECK_INTERVAL = 5 # Every 5 seconds
AI_RUNNER = "run_ai_employee.py"

def ensure_environment():
    """Ensure required folders and files exist."""
    if not os.path.exists(INBOX_DIR):
        os.makedirs(INBOX_DIR, exist_ok=True)
    if not os.path.exists("logs"):
        os.makedirs("logs", exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write(f"--- Action Log Initialized at {datetime.now()} ---\n")

def log_action(message):
    """Logs an action to logs/actions.log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def monitor_inbox():
    """Continuously monitors the Inbox for new files."""
    print(f"[*] Starting Inbox Watcher on {INBOX_DIR}...")
    print(f"[*] Interval: {CHECK_INTERVAL} seconds.")
    
    processed_files = set()
    
    # Do NOT initialize with existing files for the test to pass if we just created them
    # OR, better: just check if they are in Inbox and not yet processed.
    
    while True:
        try:
            files = [f for f in os.listdir(INBOX_DIR) if f.endswith(".md")]
            
            new_files_detected = False
            for file in files:
                if file not in processed_files:
                    log_action(f"DETECTED: New file '{file}' in Inbox.")
                    # Move from Inbox to Needs_Action for AI to process
                    src = os.path.join(INBOX_DIR, file)
                    dst = os.path.join("AI_Employee_Vault/Needs_Action", file)
                    os.rename(src, dst)
                    log_action(f"MOVED: '{file}' to Needs_Action.")
                    new_files_detected = True
                    processed_files.add(file)
            
            if new_files_detected:
                log_action("TRIGGERING: AI processing workflow...")
                result = subprocess.run([sys.executable, AI_RUNNER, "--once"], capture_output=True, text=True)
                if result.returncode == 0:
                    log_action("SUCCESS: AI processing complete.")
                else:
                    log_action(f"ERROR: AI processing failed with code {result.returncode}.\n{result.stderr}")
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n[*] Watcher shutting down...")
            break
        except Exception as e:
            log_action(f"CRITICAL ERROR in monitor_inbox: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    ensure_environment()
    monitor_inbox()
