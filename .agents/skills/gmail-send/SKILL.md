---
name: gmail-send
description: Send real emails via SMTP. Requires EMAIL_ADDRESS and EMAIL_PASSWORD in .env. Use for notifications and external correspondence.
---

# Gmail Send

Sends professional emails using Gmail SMTP. 

## Usage
```bash
python .agents/skills/gmail-send/scripts/send_email.py --to "recipient@domain.com" --subject "Title" --body "Content"
```

## Rules
- **Environment**: Must have `.env` with SMTP credentials.
- **Output**: Returns `SUCCESS` or `ERROR`.
- **Safety**: No spam.
