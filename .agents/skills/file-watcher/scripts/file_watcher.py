"""
File Watcher Skill - Core task management for AI Employee.
Monitors the Obsidian vault for new tasks and manages the task lifecycle.
Implements: Process Tasks, Make a Plan for Tasks workflows.
"""
import os
import sys
import re
import shutil
from datetime import datetime

# Configuration
BASE_VAULT = os.environ.get("VAULT_PATH", "AI_Employee_Vault")
INBOX_DIR = os.path.join(BASE_VAULT, "Inbox")
NEEDS_ACTION_DIR = os.path.join(BASE_VAULT, "Needs_Action")
DONE_DIR = os.path.join(BASE_VAULT, "Done")
PLANS_DIR = os.path.join(BASE_VAULT, "Plans")
DASHBOARD_FILE = os.path.join(BASE_VAULT, "Dashboard.md")
SYSTEM_LOG_FILE = "System_Log.md"


def ensure_directories():
    """Ensures the vault structure exists."""
    for folder in [INBOX_DIR, NEEDS_ACTION_DIR, DONE_DIR, PLANS_DIR]:
        os.makedirs(folder, exist_ok=True)


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


def update_dashboard_completed(task_filename):
    """Moves a task from Pending to Completed in Dashboard.md."""
    if not os.path.exists(DASHBOARD_FILE):
        return

    with open(DASHBOARD_FILE, "r") as f:
        content = f.read()

    lines = content.split("\n")
    new_lines = []
    in_pending = False

    # Remove from pending
    for line in lines:
        if "## Pending Tasks" in line:
            in_pending = True
            new_lines.append(line)
            continue
        if line.startswith("##") and in_pending:
            in_pending = False
        if in_pending and task_filename in line:
            continue
        new_lines.append(line)

    # Add to completed
    if "## Completed Tasks" not in content:
        new_lines.append("\n## Completed Tasks")

    final_lines = []
    for line in new_lines:
        final_lines.append(line)
        if "## Completed Tasks" in line:
            final_lines.append(f"- [x] {task_filename}")

    with open(DASHBOARD_FILE, "w") as f:
        f.write("\n".join(final_lines))


def update_dashboard_pending(task_filename):
    """Adds a task to the Pending Tasks section in Dashboard.md."""
    if not os.path.exists(DASHBOARD_FILE):
        return

    with open(DASHBOARD_FILE, "r") as f:
        content = f.read()

    task_entry = f"- [ ] {task_filename}"
    if task_entry not in content:
        if "## Pending Tasks" not in content:
            if "## Tasks" in content:
                content = content.replace("## Tasks", "## Tasks\n\n## Pending Tasks\n" + task_entry)
            else:
                content = f"## Pending Tasks\n{task_entry}\n\n" + content
        else:
            lines = content.split("\n")
            new_lines = []
            for line in lines:
                new_lines.append(line)
                if "## Pending Tasks" in line:
                    new_lines.append(task_entry)
            content = "\n".join(new_lines)

    with open(DASHBOARD_FILE, "w") as f:
        f.write(content)


def process_tasks():
    """
    Implements the 'Process Tasks' workflow:
    1. Scan Needs_Action/ for Markdown files.
    2. For each task: read, update frontmatter, move to Done/.
    3. Update Dashboard.md.
    4. Log activity.
    """
    ensure_directories()

    tasks = [f for f in os.listdir(NEEDS_ACTION_DIR) if f.endswith(".md")]
    if not tasks:
        print("No tasks found in Needs_Action.")
        return 0

    processed_count = 0
    for task_file in tasks:
        task_path = os.path.join(NEEDS_ACTION_DIR, task_file)
        with open(task_path, "r") as f:
            content = f.read()

        # Update frontmatter: set status: completed
        content = re.sub(r"status: pending", "status: completed", content)

        # Check off review items
        content = re.sub(r"- \[ \]", "- [x]", content)

        # Move to Done
        done_path = os.path.join(DONE_DIR, task_file)
        with open(done_path, "w") as f:
            f.write(content)
        os.remove(task_path)

        # Update Dashboard
        update_dashboard_completed(task_file)
        processed_count += 1
        log_activity(f"Processed and moved task: {task_file}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] PROCESSED: {task_file}")

    if processed_count > 0:
        log_activity(f"Processed {processed_count} tasks from Needs_Action.")

    return processed_count


def make_plan():
    """
    Implements the 'Make a Plan for Tasks' workflow:
    1. Scan Needs_Action/.
    2. Analyze tasks (priority, type).
    3. Generate a new plan in Plans/Plan_<timestamp>.md.
    4. Log the planning activity.
    """
    ensure_directories()

    tasks = [f for f in os.listdir(NEEDS_ACTION_DIR) if f.endswith(".md")]
    if not tasks:
        print("No tasks to plan for.")
        return None

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    plan_filename = f"Plan_{timestamp}.md"
    plan_path = os.path.join(PLANS_DIR, plan_filename)

    plan_content = f"""# Execution Plan - {timestamp}

## Tasks to Process
"""
    for task_file in tasks:
        task_path = os.path.join(NEEDS_ACTION_DIR, task_file)
        with open(task_path, "r") as f:
            task_content = f.read()

        # Extract priority from frontmatter
        priority_match = re.search(r"priority:\s*(\w+)", task_content)
        priority = priority_match.group(1) if priority_match else "medium"

        # Extract type from frontmatter
        type_match = re.search(r"type:\s*(.+)", task_content)
        task_type = type_match.group(1).strip() if type_match else "general"

        plan_content += f"""
### {task_file}
- **Type:** {task_type}
- **Priority:** {priority}
- **Steps:**
  - [ ] Read and analyze task content
  - [ ] Determine required actions
  - [ ] Execute actions
  - [ ] Verify completion
  - [ ] Move to Done/
"""

    with open(plan_path, "w") as f:
        f.write(plan_content)

    # Also update master Plan.md in Needs_Action for Ralph Wiggum loop
    master_plan_path = os.path.join(NEEDS_ACTION_DIR, "Plan.md")
    with open(master_plan_path, "w") as f:
        f.write(plan_content)

    log_activity(f"Generated execution plan: {plan_filename}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] PLAN CREATED: {plan_filename}")
    return plan_path


def run_watcher_cycle():
    """
    Runs a full watcher cycle: detect new files in Inbox, create task files.
    This is the file system monitoring workflow.
    """
    ensure_directories()

    try:
        files = [f for f in os.listdir(INBOX_DIR) if os.path.isfile(os.path.join(INBOX_DIR, f))]
        new_count = 0

        for file in files:
            # Avoid double .md extension
            base_name = file[:-3] if file.endswith(".md") else file
            task_filename = f"task_{base_name}.md"
            task_path = os.path.join(NEEDS_ACTION_DIR, task_filename)

            if not os.path.exists(task_path):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                content = f"""---
type: file_review
status: pending
priority: medium
created_at: {timestamp}
related_file: ["{file}"]
---

# Task File: Review {file}

## Description
A new file named `{file}` was detected in the Inbox. It needs to be reviewed and categorized.

## Checklist
- [ ] Open and read {file}
- [ ] Determine if it needs to be moved to a specific project or folder
- [ ] Update Dashboard.md with progress
- [ ] Move this task to Done/

## Notes
- Automatically generated by File Watcher Skill.
"""
                with open(task_path, "w") as f:
                    f.write(content)

                update_dashboard_pending(task_filename)
                log_activity(f"Detected new file in Inbox: {file}")
                print(f"[{datetime.now().strftime('%H:%M:%S')}] DETECTED: {file}")
                new_count += 1

        return new_count
    except Exception as e:
        print(f"ERROR in watcher cycle: {e}")
        return 0


def main():
    """CLI entry point for the File Watcher skill."""
    import argparse

    parser = argparse.ArgumentParser(description="File Watcher Skill - Task management for AI Employee")
    parser.add_argument("--process", action="store_true", help="Process pending tasks in Needs_Action/")
    parser.add_argument("--plan", action="store_true", help="Generate execution plan for tasks")
    parser.add_argument("--watch", action="store_true", help="Run one watcher cycle (detect new Inbox files)")
    parser.add_argument("--daemon", action="store_true", help="Run continuous watcher loop")
    parser.add_argument("--interval", type=int, default=5, help="Watcher interval in seconds (default: 5)")

    args = parser.parse_args()

    ensure_directories()

    if args.process:
        count = process_tasks()
        print(f"Processed {count} tasks.")
    elif args.plan:
        path = make_plan()
        print(f"Plan generated at: {path}" if path else "No tasks to plan.")
    elif args.watch:
        count = run_watcher_cycle()
        print(f"Watcher cycle complete. {count} new files detected.")
    elif args.daemon:
        import time
        print(f"File Watcher Daemon running. Interval: {args.interval}s")
        print(f"Monitoring: {INBOX_DIR}")
        processed_files = set()
        while True:
            try:
                files = [f for f in os.listdir(INBOX_DIR) if os.path.isfile(os.path.join(INBOX_DIR, f))]
                for file in files:
                    if file not in processed_files:
                        base_name = file[:-3] if file.endswith(".md") else file
                        task_filename = f"task_{base_name}.md"
                        task_path = os.path.join(NEEDS_ACTION_DIR, task_filename)
                        if not os.path.exists(task_path):
                            run_watcher_cycle()
                            processed_files.add(file)
            except Exception as e:
                print(f"ERROR: {e}")
            time.sleep(args.interval)
    else:
        # Default: run both watch and process
        new_count = run_watcher_cycle()
        processed_count = process_tasks()
        print(f"Watcher cycle: {new_count} new, {processed_count} processed.")


if __name__ == "__main__":
    main()
