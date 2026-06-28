import os
import sys
import re
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict

PYTHON_EXECUTABLE = sys.executable  # Cross-platform Python path

# --- CONFIGURATION ---
VAULT_DIR = "AI_Employee_Vault"
REPORTS_DIR = os.path.join(VAULT_DIR, "Reports")
DONE_DIR = os.path.join(VAULT_DIR, "Done")
APPROVALS_DIR = os.path.join(VAULT_DIR, "Needs_Approval")
BUSINESS_LOG = os.path.join(VAULT_DIR, "Logs", "business.log")
SYSTEM_LOG = "System_Log.md"
ACCOUNTING_SCRIPT = os.path.join(".agents", "skills", "accounting-manager", "scripts", "accounting_manager.py")

def get_completed_tasks() -> List[str]:
    """List tasks completed in the last 7 days."""
    if not os.path.exists(DONE_DIR):
        return []
    tasks = []
    seven_days_ago = datetime.now() - timedelta(days=7)
    for f in os.listdir(DONE_DIR):
        if f.endswith(".md"):
            f_path = os.path.join(DONE_DIR, f)
            mtime = datetime.fromtimestamp(os.path.getmtime(f_path))
            if mtime >= seven_days_ago:
                tasks.append(f)
    return tasks

def get_business_activity() -> Dict[str, int]:
    """Parse business.log for emails and LinkedIn posts."""
    stats = {"emails": 0, "linkedin": 0}
    if not os.path.exists(BUSINESS_LOG):
        return stats
    
    seven_days_ago = datetime.now() - timedelta(days=7)
    with open(BUSINESS_LOG, "r") as f:
        for line in f:
            if "EMAIL SENT" in line:
                stats["emails"] += 1
            elif "LINKEDIN POST" in line:
                stats["linkedin"] += 1
    return stats

def get_pending_approvals() -> List[str]:
    """List files currently in Needs_Approval."""
    if not os.path.exists(APPROVALS_DIR):
        return []
    return [f for f in os.listdir(APPROVALS_DIR) if os.path.isfile(os.path.join(APPROVALS_DIR, f))]

def get_accounting_summary() -> str:
    """Run the accounting manager script to get totals."""
    import subprocess
    if not os.path.exists(ACCOUNTING_SCRIPT):
        return "Accounting script not found."
    
    try:
        result = subprocess.run([PYTHON_EXECUTABLE, ACCOUNTING_SCRIPT, "totals"], capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        return f"Error running accounting summary: {e}"

def get_system_health() -> str:
    """Check for lock files and directory health."""
    health = "✅ OK"
    issues = []
    
    # Check for stale locks
    if os.path.exists("logs/ai_employee.lock"):
        issues.append("Daemon Lock File Detected")
    
    # Check Inbox
    inbox_count = len(os.listdir(os.path.join(VAULT_DIR, "Inbox")))
    if inbox_count > 10:
        issues.append(f"High Inbox Volume ({inbox_count} files)")
    
    if issues:
        return "⚠️ WARNING: " + ", ".join(issues)
    return health

def generate_report():
    """Generates the CEO_Weekly.md report."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_path = os.path.join(REPORTS_DIR, "CEO_Weekly.md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    tasks = get_completed_tasks()
    business = get_business_activity()
    approvals = get_pending_approvals()
    accounting = get_accounting_summary()
    health = get_system_health()

    report_content = f"""# CEO Weekly Briefing
**Generated At:** {timestamp}
**Reporting Period:** {(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}

---

## 📊 Business Performance
- **Emails Sent:** {business['emails']}
- **LinkedIn Posts:** {business['linkedin']}

## 💰 Financial Summary
```text
{accounting}
```

## ✅ Tasks Completed ({len(tasks)})
{chr(10).join([f"- {t}" for t in tasks]) if tasks else "- No tasks completed this week."}

## ⏳ Pending Approvals ({len(approvals)})
{chr(10).join([f"- {t}" for t in approvals]) if approvals else "- No pending approvals."}

## 🛠️ System Health
**Status:** {health}

---
*End of Report*
"""
    with open(report_path, "w") as f:
        f.write(report_content)
    print(f"Report generated successfully: {report_path}")

if __name__ == "__main__":
    generate_report()
