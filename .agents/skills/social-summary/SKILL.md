---
name: social-summary
description: Logs summaries of social media posts to the AI Employee Vault. Records platform, date, and a content summary to AI_Employee_Vault/Reports/Social_Logs.md. Use after any social media posting action.
---

# Social Media Summary Skill

This skill provides a standardized way to log social media activity for reporting and auditing.

## 🚀 Workflows

### 1. Log a Social Post
Immediately after a post is successfully published, call the logging script:

```bash
python scripts/social_summary.py [platform] "[content]"
```

## 📋 Log Format
The logs are maintained in `AI_Employee_Vault/Reports/Social_Logs.md` as a Markdown table:

| Date | Platform | Content Summary |
|------|----------|-----------------|
| 2026-04-11 | LinkedIn | Sharing my thoughts on AI automation... |

## 💡 Usage Guidelines
- Call this skill after every successful LinkedIn, Twitter, or other social post.
- Ensure the full post content is passed to the script; it will handle truncation for the table view.
- This log is consumed by the `ceo-briefing` skill for weekly reporting.
