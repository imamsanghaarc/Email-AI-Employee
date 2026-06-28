---
name: gmail-watcher
description: Monitors Gmail inbox for new emails and creates tasks in AI Employee vault. Uses IMAP to check for unread emails every 60 seconds. Use when automatic email monitoring and task generation is needed. Triggers on new unread emails in Gmail inbox.
---

# Gmail Watcher

Monitors Gmail inbox via IMAP and automatically generates tasks in the AI Employee vault system.

## Overview

Watches Gmail inbox for new unread emails, extracts key information, and creates structured task files in `AI_Employee_Vault/Inbox/` for AI processing.

## Components

- **Script**: `scripts/watch_gmail.py`
- **Output**: Creates `.md` files in `AI_Employee_Vault/Inbox/`
- **Log**: `logs/gmail_watcher.log`
- **State File**: `logs/gmail_watcher_state.json` (tracks processed emails)

## Usage

### Start Gmail Watcher
```bash
python .agents/skills/gmail-watcher/scripts/watch_gmail.py
```

### Configuration
Requires `.env` file with:
```env
GMAIL_ADDRESS=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password
```

**Note**: Must use Gmail App Password, not regular password. Generate at: https://myaccount.google.com/apppasswords

### How It Works

1. Connects to Gmail via IMAP every 60 seconds
2. Searches for UNSEEN emails in INBOX
3. For each new email:
   - Extracts: sender, subject, date, snippet
   - Creates task file: `AI_Employee_Vault/Inbox/email_{timestamp}_{subject_slug}.md`
   - Marks email as seen (prevents re-processing)
   - Logs action to `logs/gmail_watcher.log`
4. AI Employee processes task files via normal workflow

### Task File Format

Generated task files follow this structure:
```markdown
---
type: email
status: pending
priority: medium
created_at: 2024-01-15 10:30:00
sender: john@example.com
subject: Project Update Request
---

# Email Task: Project Update Request

## Details
- **From**: john@example.com
- **Received**: 2024-01-15 10:30:00
- **Subject**: Project Update Request

## Content
[Email body excerpt...]

## Actions Required
- [ ] Review email content
- [ ] Determine appropriate response or action
- [ ] Move to Done when complete
```

## Rules

- **No API Keys Required**: Uses standard IMAP protocol
- **Stateful**: Tracks processed emails to prevent duplicates
- **Non-Destructive**: Only marks emails as read, never deletes
- **Error Handling**: Gracefully handles connection failures
- **Resource Efficient**: 60-second polling interval
- **Security**: App passwords stored in `.env`, never logged

## Troubleshooting

**Connection Failed**: Verify Gmail address and app password
**No Emails Found**: Ensure IMAP is enabled in Gmail settings
**Permission Denied**: Check 2FA is enabled and app password is valid
