---
name: file-watcher
description: Monitors the Obsidian vault for new tasks and manages the task lifecycle (Process Tasks, Make a Plan).
---

# File Watcher Skill

This skill implements the core logic for the AI Employee's task management system.

## Workflows

### Process Tasks
When triggered, follow these steps to process pending tasks:
1. Scan `vault/Needs_Action/` for Markdown files.
2. For each task:
   - Read content.
   - Update frontmatter to `status: completed`.
   - Check off review items in the body.
   - Move file to `vault/Done/`.
3. Update `vault/Dashboard.md`:
   - Add filename to ## Completed Tasks.
   - Remove from ## Pending Tasks.
4. Log activity to `System_Log.md`.

### Make a Plan for Tasks
When triggered, follow these steps:
1. Scan `vault/Needs_Action/`.
2. Analyze tasks (priority, type).
3. Generate a new plan in `vault/Plans/Plan_<timestamp>.md`.
4. Log the planning activity to `System_Log.md`.

## Rules
- **Atomicity**: Ensure each task is fully moved and logged before proceeding.
- **No Simulation**: Always perform actual file system operations.
- **Scope**: Only operate within the `vault/` directory.
