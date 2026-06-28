---
name: vault-file-manager
description: Manages task state by moving files between Inbox, Needs_Action, and Done. Use for workflow transitions.
---

# Vault File Manager

Orchestrates file movement within the AI Employee vault.

## Usage
```bash
python .agents/skills/vault-file-manager/scripts/move_task.py "task.md" --from-dir inbox --to-dir needs_action
```

## Folder Keys
- `inbox`
- `needs_action`
- `done`

## Rules
- **Atomic**: Moves are verified.
- **Paths**: Rooted in `AI_Employee_Vault/`.
