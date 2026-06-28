---
name: human-approval
description: Blocks execution for human verification. Monitors Needs_Approval for APPROVED/REJECTED. Use for sensitive actions.
---

# Human Approval

Safe-guard for autonomous operations requiring human oversight.

## Usage
```bash
python .agents/skills/human-approval/scripts/request_approval.py "deploy.md" --details "Action description"
```

## Rules
- **Blocking**: Script polls every 5 seconds.
- **Decision**: Must write result in the `DECISION ZONE`.
- **Output**: Returns status and renames file.
