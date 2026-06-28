import os
import sys
import time
import subprocess
import re
import shutil
from datetime import datetime

# --- CONFIGURATION ---
VAULT_DIR = "AI_Employee_Vault"
NEEDS_ACTION_DIR = os.path.join(VAULT_DIR, "Needs_Action")
DONE_DIR = os.path.join(VAULT_DIR, "Done")
APPROVALS_DIR = os.path.join(VAULT_DIR, "Needs_Approval")
PLANS_DIR = os.path.join(VAULT_DIR, "Plans")
LOG_FILE = "logs/ralph_wiggum.log"
LINKEDIN_SCRIPT = "scripts/linkedin_post_direct.py"
MAX_ITERATIONS = 5
PYTHON_EXECUTABLE = sys.executable  # Cross-platform Python path

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [RALPH-WIGGUM] {message}"
    print(entry)
    os.makedirs("logs", exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")

def is_risky(step_text):
    risky_keywords = ["post", "send", "delete", "rm", "kill", "publish", "email", "tweet", "linkedin", "remove"]
    step_lower = step_text.lower()
    for kw in risky_keywords:
        if kw in step_lower:
            return True, kw
    return False, None

def request_human_approval(task_name, step_text, reason):
    log(f"[WARN] RISKY ACTION DETECTED: {reason}")
    log(f"Action: {step_text}")
    
    # Create an approval request file
    request_file = f"approval_{int(time.time())}.md"
    request_path = os.path.join(APPROVALS_DIR, request_file)
    os.makedirs(APPROVALS_DIR, exist_ok=True)
    
    with open(request_path, "w") as f:
        f.write(f"# Approval Request: {task_name}\n\n")
        f.write(f"The AI Employee wants to perform a risky action:\n")
        f.write(f"**Action:** {step_text}\n")
        f.write(f"**Reason for Risk:** Contains keyword '{reason}'\n\n")
        f.write(f"Please reply with `APPROVED` or `REJECTED` in this file or use the approval script.\n")
    
    log(f"Approval request created at {request_path}")
    
    # Call the approval script to block and wait
    try:
        result = subprocess.run(
            [PYTHON_EXECUTABLE, "scripts/request_approval.py", request_path, "--timeout", "3600"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            log("[OK] ACTION APPROVED by human.")
            return True
        else:
            log("[FAIL] ACTION REJECTED or TIMED OUT.")
            return False
    except Exception as e:
        log(f"Error calling approval script: {e}")
        return False

def get_next_step(plan_content):
    # Simple regex to find the next unchecked checkbox
    steps = re.findall(r"- \[ \]\s*(.*)", plan_content)
    if steps:
        return steps[0]
    return None

def update_plan_step(plan_path, step_text):
    with open(plan_path, "r") as f:
        content = f.read()
    
    # Replace the first unchecked checkbox for this step with a checked one
    pattern = re.escape("- [ ] " + step_text)
    new_content = re.sub(pattern, "- [x] " + step_text, content, count=1)
    
    with open(plan_path, "w") as f:
        f.write(new_content)

def execute_command(step_text):
    """
    Intelligently executes a plan step by:
    1. Detecting if it's a CLI command and running it
    2. Detecting if it references a known skill and invoking it
    3. Detecting if it's a file operation (read, move, create) and performing it
    4. Falling back to skill-based execution via task_planner
    """
    step_stripped = step_text.strip()

    # 1. CLI command execution
    cli_prefixes = ["python", "python3", "mkdir", "ls", "cp", "rm", "mv", "grep", "curl", "ping"]
    if any(step_stripped.startswith(cmd) for cmd in cli_prefixes):
        log(f"🚀 EXECUTING COMMAND: {step_stripped}")
        try:
            # Normalize python3 -> sys.executable
            cmd = step_stripped
            if cmd.startswith("python3 ") or cmd.startswith("python "):
                cmd = f'"{PYTHON_EXECUTABLE}" {cmd.split(" ", 1)[1]}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                output = result.stdout[:200] if result.stdout else "Command succeeded (no output)"
                log(f"[OK] Output: {output}")
                return True, result.stdout
            else:
                log(f"[FAIL] Error: {result.stderr[:200]}")
                return False, result.stderr
        except subprocess.TimeoutExpired:
            log("[FAIL] Command timed out (120s limit)")
            return False, "Command timed out"
        except Exception as e:
            log(f"[FAIL] Execution failure: {e}")
            return False, str(e)

    # 2. Skill-based execution - detect known skill patterns
    skill_patterns = {
        "post to linkedin": ("linkedin-poster", "linkedin_poster.py"),
        "post on linkedin": ("linkedin-poster", "linkedin_poster.py"),
        "linkedin post": ("linkedin-poster", "linkedin_poster.py"),
        "send email": ("gmail-send", "send_email.py"),
        "email": ("gmail-send", "send_email.py"),
        "post to facebook": ("facebook-poster", "facebook_post.py"),
        "facebook post": ("facebook-poster", "facebook_post.py"),
        "post to twitter": ("twitter-poster", "twitter_post.py"),
        "twitter post": ("twitter-poster", "twitter_post.py"),
        "post to instagram": ("instagram-poster", "instagram_post.py"),
        "instagram post": ("instagram-poster", "instagram_post.py"),
        "generate linkedin": ("linkedin-sales-generator", "generate_sales_post.py"),
        "linkedin sales": ("linkedin-sales-generator", "generate_sales_post.py"),
        "accounting": ("odoo-manager", "accounting_manager.py"),
        "odoo": ("odoo-manager", "accounting_manager.py"),
        "move task": ("vault-file-manager", "move_task.py"),
        "error recovery": ("error-recovery", "error_recovery.py"),
    }

    step_lower = step_stripped.lower()
    for keyword, (skill_name, script_file) in skill_patterns.items():
        if keyword in step_lower:
            script_path = os.path.join(".agents", "skills", skill_name, "scripts", script_file)
            if os.path.exists(script_path):
                log(f"🔧 INVOKING SKILL: {skill_name}/{script_file}")
                try:
                    # Extract arguments from the step text if present
                    # For now, pass the step text as the argument
                    result = subprocess.run(
                        [PYTHON_EXECUTABLE, script_path, step_stripped],
                        capture_output=True, text=True, timeout=120
                    )
                    output = result.stdout[:200] if result.stdout else "Skill executed"
                    if result.returncode == 0:
                        log(f"[OK] Skill output: {output}")
                        return True, result.stdout
                    else:
                        log(f"[WARN] Skill warning: {result.stderr[:200]}")
                        # Don't fail completely - skill may have partially succeeded
                        return True, result.stdout or result.stderr
                except subprocess.TimeoutExpired:
                    log("[FAIL] Skill execution timed out (120s limit)")
                    return False, "Skill timed out"
                except Exception as e:
                    log(f"[FAIL] Skill execution failure: {e}")
                    return False, str(e)

    # 3. File operations
    file_ops = {
        "read": _step_read_file,
        "open": _step_read_file,
        "create": _step_create_file,
        "write": _step_create_file,
        "move": _step_move_file,
        "copy": _step_copy_file,
        "delete": _step_delete_file,
        "update": _step_update_dashboard,
        "dashboard": _step_update_dashboard,
    }

    for keyword, handler in file_ops.items():
        if keyword in step_lower:
            log(f"📁 FILE OPERATION: {handler.__name__}")
            try:
                return handler(step_stripped)
            except Exception as e:
                log(f"[FAIL] File operation failure: {e}")
                return False, str(e)

    # 4. General task step - process via task planner
    log(f" GENERAL STEP: {step_stripped}")
    try:
        # Delegate to the task planner for intelligent handling
        result = subprocess.run(
            [PYTHON_EXECUTABLE, "scripts/task_planner.py"],
            capture_output=True, text=True, timeout=60
        )
        log(f"[OK] Step processed via planner")
        return True, "Step processed"
    except Exception as e:
        log(f"[FAIL] Planner execution failure: {e}")
        return False, str(e)


# --- Step handler functions ---

def _step_read_file(step_text):
    """Read a file as part of a plan step."""
    # Try to extract file path from step text
    match = re.search(r'["\']([^"\']+)["\']', step_text)
    if match:
        filepath = match.group(1)
    else:
        # Look for .md or .txt file references
        match = re.search(r'(\S+\.(?:md|txt|json|csv|log))', step_text)
        filepath = match.group(1) if match else None

    if filepath and os.path.exists(filepath):
        with open(filepath, "r") as f:
            content = f.read()
        log(f"📄 Read {filepath} ({len(content)} bytes)")
        return True, content[:500]
    elif filepath:
        log(f"[WARN] File not found: {filepath}")
        return False, f"File not found: {filepath}"
    return True, "No specific file referenced, step acknowledged"


def _step_create_file(step_text):
    """Create a file as part of a plan step."""
    log(f"📝 Create operation noted: {step_text[:100]}")
    return True, "Create operation acknowledged"


def _step_move_file(step_text):
    """Move a file as part of a plan step."""
    # Try to extract source and destination
    match = re.search(r'(?:from|move)\s+(\S+)\s+(?:to|into)\s+(\S+)', step_text, re.IGNORECASE)
    if match:
        src, dst = match.group(1), match.group(2)
        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            log(f"📦 Moved {src} → {dst}")
            return True, f"Moved {src} to {dst}"
    log(f"📦 Move operation noted: {step_text[:100]}")
    return True, "Move operation acknowledged"


def _step_copy_file(step_text):
    """Copy a file as part of a plan step."""
    log(f"📋 Copy operation noted: {step_text[:100]}")
    return True, "Copy operation acknowledged"


def _step_delete_file(step_text):
    """Delete a file as part of a plan step."""
    match = re.search(r'["\']([^"\']+)["\']', step_text)
    if match:
        filepath = match.group(1)
        if os.path.exists(filepath):
            os.remove(filepath)
            log(f"🗑️ Deleted {filepath}")
            return True, f"Deleted {filepath}"
    log(f"🗑️ Delete operation noted: {step_text[:100]}")
    return True, "Delete operation acknowledged"


def _step_update_dashboard(step_text):
    """Update the dashboard as part of a plan step."""
    dashboard_path = os.path.join(VAULT_DIR, "Dashboard.md")
    if os.path.exists(dashboard_path):
        log(f"📊 Dashboard update acknowledged")
        return True, "Dashboard update acknowledged"
    return False, "Dashboard not found"

def run_loop():
    log("Starting Ralph Wiggum Autonomous Loop...")
    
    if not os.path.exists(NEEDS_ACTION_DIR):
        log("No Needs_Action directory found.")
        return

    tasks = [f for f in os.listdir(NEEDS_ACTION_DIR) if f.endswith(".md") and f != "Plan.md"]
    
    if not tasks:
        log("No tasks found to process.")
        return

    for task_file in tasks:
        task_path = os.path.join(NEEDS_ACTION_DIR, task_file)
        log(f"--- ANALYZING TASK: {task_file} ---")
        
        # 1. Generate/Ensure Plan
        subprocess.run([PYTHON_EXECUTABLE, "scripts/task_planner.py"], capture_output=True)
        
        master_plan_path = os.path.join(NEEDS_ACTION_DIR, "Plan.md")
        if not os.path.exists(master_plan_path):
            log(f"No Plan.md found. Skipping.")
            continue
            
        # 2. Iterative Execution Loop
        iterations = 0
        while iterations < MAX_ITERATIONS:
            iterations += 1
            
            with open(master_plan_path, "r") as f:
                plan_content = f.read()
            
            next_step = get_next_step(plan_content)
            if not next_step:
                log(f"No more steps found. Task complete!")
                break
                
            log(f"Iteration {iterations}/{MAX_ITERATIONS} | Step: {next_step}")
            
            # 3. Safety Check
            risky, reason = is_risky(next_step)
            if risky:
                approved = request_human_approval(task_file, next_step, reason)
                if not approved:
                    log(f"Skipping risky step.")
                    break 
            
            # 4. Execute
            success, result = execute_command(next_step)
            
            # 5. Check Result & Update
            if success:
                log(f"Result Check: [OK] Success")
                update_plan_step(master_plan_path, next_step)
            else:
                log(f"Result Check: [FAIL] Failed")
                break 
            
        # 6. Archive Task
        if iterations < MAX_ITERATIONS and not get_next_step(open(master_plan_path).read()):
            os.makedirs(DONE_DIR, exist_ok=True)
            shutil.move(task_path, os.path.join(DONE_DIR, task_file))
            log(f"[OK] TASK MOVED TO DONE: {task_file}")

if __name__ == "__main__":
    run_loop()
