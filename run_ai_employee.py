import os
import argparse
import re
from datetime import datetime

# --- CONFIGURATION ---
VAULT_DIR = "AI_Employee_Vault"
NEEDS_ACTION_DIR = os.path.join(VAULT_DIR, "Needs_Action")
DONE_DIR = os.path.join(VAULT_DIR, "Done")
DASHBOARD_FILE = os.path.join(VAULT_DIR, "Dashboard.md")
SYSTEM_LOG_FILE = "System_Log.md"

def process_tasks():
    """Implements the 'Process Tasks' workflow from GEMINI.md."""
    if not os.path.exists(NEEDS_ACTION_DIR):
        print(f"Directory {NEEDS_ACTION_DIR} does not exist.")
        return

    os.makedirs(DONE_DIR, exist_ok=True)
    
    tasks = [f for f in os.listdir(NEEDS_ACTION_DIR) if f.endswith(".md")]
    if not tasks:
        print("No tasks found in Needs_Action.")
        return

    processed_count = 0
    for task_file in tasks:
        task_path = os.path.join(NEEDS_ACTION_DIR, task_file)
        with open(task_path, "r") as f:
            content = f.read()

        # Update frontmatter: set status: completed
        content = re.sub(r"status: pending", "status: completed", content)
        
        # Update body: check review items
        content = re.sub(r"- \[ \]", "- [x]", content)

        # Move to Done
        done_path = os.path.join(DONE_DIR, task_file)
        with open(done_path, "w") as f:
            f.write(content)
        
        os.remove(task_path)
        print(f"Processed and moved: {task_file}")
        
        # Update Dashboard
        update_dashboard(task_file)
        processed_count += 1

    # Log Activity
    if processed_count > 0:
        log_activity(f"Processed {processed_count} tasks from Needs_Action.")

def update_dashboard(task_filename):
    """Updates Dashboard.md according to GEMINI.md rules."""
    if not os.path.exists(DASHBOARD_FILE):
        return

    with open(DASHBOARD_FILE, "r") as f:
        content = f.read()

    lines = content.split("\n")
    new_lines = []
    
    in_pending = False
    found_pending_header = False
    found_completed_header = False
    
    # First pass: Remove from pending and identify headers
    for line in lines:
        if "## Pending Tasks" in line:
            in_pending = True
            found_pending_header = True
            new_lines.append(line)
            continue
        
        if line.startswith("##") and in_pending:
            in_pending = False
        
        if in_pending and (task_filename in line or task_filename.replace(".md.md", ".md") in line):
            continue # Remove the task from pending
            
        if "## Completed Tasks" in line:
            found_completed_header = True
            
        new_lines.append(line)

    # Second pass: Add to completed tasks
    if not found_completed_header:
        new_lines.append("\n## Completed Tasks")
    
    final_lines = []
    added_to_completed = False
    for i, line in enumerate(new_lines):
        final_lines.append(line)
        if "## Completed Tasks" in line:
            final_lines.append(f"- [x] {task_filename}")
            added_to_completed = True
            
    if not added_to_completed:
        final_lines.append(f"- [x] {task_filename}")

    with open(DASHBOARD_FILE, "w") as f:
        f.write("\n".join(final_lines))

def log_activity(message):
    """Appends to System_Log.md activity log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"- [{timestamp}] {message}\n"
    
    if os.path.exists(SYSTEM_LOG_FILE):
        with open(SYSTEM_LOG_FILE, "a") as f:
            f.write(entry)
    else:
        with open(SYSTEM_LOG_FILE, "w") as f:
            f.write(f"# System Log\n\n## Activity Log\n{entry}")

def main():
    parser = argparse.ArgumentParser(description="AI Employee Runner")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    if args.once:
        process_tasks()
    else:
        print("Continuous mode not implemented in this version.")

if __name__ == "__main__":
    main()
