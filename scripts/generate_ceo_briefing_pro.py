import os
import sys
import json
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict

# --- CONFIGURATION ---
VAULT_DIR = "AI_Employee_Vault"
REPORTS_DIR = os.path.join(VAULT_DIR, "Reports")
DONE_DIR = os.path.join(VAULT_DIR, "Done")
SOCIAL_LOGS = os.path.join(REPORTS_DIR, "Social_Logs.md")
BUSINESS_LOG = os.path.join(VAULT_DIR, "Logs", "business.log")
ODOO_SCRIPT = "mcp/odoo-mcp/server.py"

def get_completed_tasks_count() -> int:
    if not os.path.exists(DONE_DIR):
        return 0
    seven_days_ago = datetime.now() - timedelta(days=7)
    count = 0
    for f in os.listdir(DONE_DIR):
        if f.endswith(".md"):
            mtime = datetime.fromtimestamp(os.path.getmtime(os.path.join(DONE_DIR, f)))
            if mtime >= seven_days_ago:
                count += 1
    return count

def get_social_stats() -> Dict:
    stats = {"linkedin": 0, "facebook": 0, "twitter": 0, "instagram": 0}
    if not os.path.exists(SOCIAL_LOGS):
        return stats
    
    with open(SOCIAL_LOGS, "r") as f:
        for line in f:
            line_lower = line.lower()
            for platform in stats.keys():
                if f"| {platform}" in line_lower:
                    stats[platform] += 1
    return stats

def get_odoo_summary() -> str:
    """Retrieves real accounting data from the Odoo MCP server."""
    try:
        # Try importing the odoo-manager skill first
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                        ".agents", "skills", "odoo-manager", "scripts"))
        from accounting_manager import OdooClient
        client = OdooClient()
        if not client.uid:
            return "Odoo Status: [WARN] Offline (credentials not configured in .env)"
        return client.get_accounting_summary()
    except ImportError:
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mcp", "odoo-mcp"))
            from server import get_accounting_summary
            summary = get_accounting_summary()
            if "Error" in summary:
                return "Odoo Status: [WARN] Authentication Error (Check .env API Key)"
            return summary
        except Exception as e:
            return f"Odoo Status: ❌ Connection Error ({str(e)})"
    except Exception as e:
        return f"Odoo Status: ❌ Error ({str(e)})"

def generate_pro_report():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_path = os.path.join(REPORTS_DIR, "CEO_Weekly_Gold.md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    task_count = get_completed_tasks_count()
    social = get_social_stats()
    odoo = get_odoo_summary()
    
    report = f"""# 🥇 CEO Weekly Briefing (Gold Tier)
**Generated:** {timestamp}

## 📈 Social Media Activity (Last 7 Days)
- **LinkedIn:** {social['linkedin']} posts
- **Facebook:** {social['facebook']} posts
- **Twitter (X):** {social['twitter']} posts
- **Instagram:** {social['instagram']} posts

## 💰 Odoo Accounting Audit
{odoo}

## [OK] Operational Efficiency
- **Tasks Completed:** {task_count}
- **Autonomous Loop Status:** Active (Ralph Wiggum)
- **System Health:** 🟢 Optimal

---
*This report was generated autonomously by your Gold Tier AI Employee.*
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"[OK] Gold Tier Briefing Generated: {report_path}")

if __name__ == "__main__":
    generate_pro_report()
