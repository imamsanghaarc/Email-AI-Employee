# AI Employee Operational Mandates

## Workflow: "Process Tasks"
Whenever the user says "Process Tasks", you MUST execute the following steps:

1. **Scan `Needs_Action`**: List all Markdown files in the `/mnt/e/ai_employee/AI_Employee_Vault/Needs_Action` folder.
2. **Process Each Task**:
   - Read the task file content.
   - Update the frontmatter: set `status: completed`.
   - Update the body: check the review items (e.g., `- [x] Review the file`).
   - Move the file to the `/mnt/e/ai_employee/AI_Employee_Vault/Done` folder.
3. **Update Dashboard**:
   - Open `/mnt/e/ai_employee/AI_Employee_Vault/Dashboard.md`.
   - Add the filename to the `## Completed Tasks` section.
   - Remove it from `## Pending Tasks` if it exists there.
4. **Log Activity**:
   - Append a concise entry to `/mnt/e/ai_employee/System_Log.md` under `## Activity Log` summarizing the tasks processed.

## Rules
- **No Simulation**: Always perform actual file system operations (move, read, write).
- **Atomicity**: Ensure each task is fully moved and logged before proceeding to the next.

## Workflow: "Make a Plan for tasks"
Whenever the user says "Make a Plan for tasks", you MUST execute the following steps:

1. **Scan `Needs_Action`**: List all files in the `/mnt/e/ai_employee/AI_Employee_Vault/Needs_Action` folder.
2. **Analyze Tasks**: Read each file to understand the type, priority, and content of pending tasks.
3. **Generate Plan**: Create a new file in `/mnt/e/ai_employee/AI_Employee_Vault/Plans/` named `Plan_<YYYY-MM-DD_HH-MM-SS>.md`.
   - **Content Requirements**:
     - Summary of all pending tasks.
     - Suggested order of execution (prioritization).
     - Identification of risks or unclear items.
     - A short strategy paragraph explaining the recommended approach.
4. **Log Planning**: Append a note to `/mnt/e/ai_employee/System_Log.md` that a new plan has been generated.

**Restriction**: This workflow is for planning only. DO NOT move files or mark them as completed during this phase.
