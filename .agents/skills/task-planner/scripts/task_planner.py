import os
import shutil
from datetime import datetime

# --- CONFIGURATION ---
INBOX_DIR = "AI_Employee_Vault/Inbox"
NEEDS_ACTION_DIR = "AI_Employee_Vault/Needs_Action"
DONE_DIR = "AI_Employee_Vault/Done"
LOG_FILE = "logs/actions.log"
PLAN_FILE = os.path.join(NEEDS_ACTION_DIR, "Plan.md")

def log_action(message):
    """Logs an action to logs/actions.log."""
    if not os.path.exists("logs"):
        os.makedirs("logs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] [PLANNER] {message}\n")
    print(f"[{timestamp}] [PLANNER] {message}")

def ensure_dirs():
    for d in [INBOX_DIR, NEEDS_ACTION_DIR, DONE_DIR]:
        os.makedirs(d, exist_ok=True)

def generate_plan(filename, content):
    """Generates a simple step-by-step plan based on content."""
    # In a real scenario, this might call an LLM API. 
    # For now, we'll use a template-based plan generation.
    plan = f"\n### Plan for: {filename}\n"
    plan += f"**Triggered at:** {datetime.now()}\n"
    plan += "1. Review the original requirements mentioned in the file.\n"
    plan += "2. Categorize the task and identify dependencies.\n"
    plan += "3. Execute sub-tasks as per the established workflow.\n"
    plan += "4. Verify completion and archive the results.\n"
    plan += "---\n"
    return plan

def run_planner():
    ensure_dirs()
    files = [f for f in os.listdir(INBOX_DIR) if f.endswith(".md")]
    
    if not files:
        # log_action("No new files to plan.")
        return

    plan_entries = []
    processed_files = []

    for file in files:
        file_path = os.path.join(INBOX_DIR, file)
        log_action(f"Reading file for planning: {file}")
        
        try:
            with open(file_path, "r") as f:
                content = f.read()
            
            plan_entries.append(generate_plan(file, content))
            processed_files.append(file)
            
        except Exception as e:
            log_action(f"Error reading {file}: {e}")

    if plan_entries:
        # Append to Plan.md in Needs_Action
        mode = "a" if os.path.exists(PLAN_FILE) else "w"
        with open(PLAN_FILE, mode) as f:
            if mode == "w":
                f.write("# Task Execution Plan\n\nThis file contains generated plans for incoming tasks.\n")
            for entry in plan_entries:
                f.write(entry)
        
        log_action(f"Generated plans for {len(processed_files)} files in {PLAN_FILE}")

        # Move processed files to Done (vault-file-manager logic)
        for file in processed_files:
            src = os.path.join(INBOX_DIR, file)
            dst = os.path.join(DONE_DIR, file)
            
            # Handle filename collisions in Done
            if os.path.exists(dst):
                base, ext = os.path.splitext(file)
                dst = os.path.join(DONE_DIR, f"{base}_{int(datetime.now().timestamp())}{ext}")
            
            shutil.move(src, dst)
            log_action(f"MOVED: '{file}' to Done folder.")

if __name__ == "__main__":
    run_planner()
