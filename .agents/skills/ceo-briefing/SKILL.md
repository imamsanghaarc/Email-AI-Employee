---
name: ceo-briefing
description: Generates a comprehensive weekly CEO briefing report including task progress, business activity (emails/LinkedIn), financial summaries, and system health.
---

# CEO Weekly Briefing

This skill aggregates operational data from across the AI Employee Vault to create a concise strategic report.

## 🚀 Report Content
The briefing is saved to `AI_Employee_Vault/Reports/CEO_Weekly.md` and includes:
- **Business Performance**: Count of emails sent and LinkedIn posts published.
- **Financial Summary**: Total income, expense, and net balance.
- **Task Analytics**: List of tasks completed in the last 7 days.
- **Pending Approvals**: Current items requiring human-in-the-loop attention.
- **System Health**: Health status and detection of operational issues (e.g., stale locks).

## 🛠️ Usage

### Manual Trigger
You can manually generate a report at any time:

```bash
python scripts/generate_ceo_briefing.py
```

### Automatic Scheduling
This skill is designed to run every Monday at 9 AM via the system scheduler.

#### Add to Cron (Linux)
```bash
0 9 * * 1 cd /path/to/project && python .agents/skills/ceo-briefing/scripts/generate_ceo_briefing.py
```

## 📋 Best Practices
- Ensure `accounting-manager` is updated before generating the report for accurate financial data.
- Review the report weekly to monitor system health and identify bottlenecks in pending approvals.
