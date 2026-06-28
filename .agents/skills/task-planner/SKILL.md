---
name: task-planner
description: Analyzes incoming tasks in the Inbox and generates intelligent, LLM-driven execution plans with fallback to template mode. Supports Anthropic Claude and OpenAI GPT APIs.
---

# Task Planner Skill

This skill is responsible for the "Strategy" phase of the AI Employee's workflow. It uses LLM reasoning to transform raw input files into intelligent, actionable execution plans.

## Goal
To provide AI-driven, structured, step-by-step guidance for every new task entering the system, ensuring optimal execution strategies based on task complexity and dependencies.

## Components
- **Input Folder**: `AI_Employee_Vault/Inbox`
- **Output Folder**: `AI_Employee_Vault/Plans`
- **Master Plan File**: `AI_Employee_Vault/Needs_Action/Plan.md`
- **Logging**: Appends to `logs/actions.log`.
- **Scripts**: 
  - `scripts/claude_reasoning_loop.py` (LLM-driven planning - **primary**)
  - `scripts/task_planner.py` (template-based planning - **fallback**)

## LLM Configuration

The planner supports two LLM engines (Anthropic Claude is preferred):

**Option 1: Anthropic Claude (Recommended)**
```env
ANTHROPIC_API_KEY=sk-ant-your-key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

**Option 2: OpenAI GPT**
```env
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4o-mini
```

**Fallback**: If no API keys are configured, the planner uses template-based planning automatically.

## Usage Instructions

### Running the LLM Planner (Primary)
```bash
python scripts/claude_reasoning_loop.py
# or
python .agents/skills/task-planner/scripts/claude_reasoning_loop.py
```

### Running the Template Planner (Fallback)
```bash
python scripts/task_planner.py
# or
python .agents/skills/task-planner/scripts/task_planner.py
```

### Workflow
1. **Detection**: Scans the `Inbox` for `.md` files.
2. **Context Building**: Reads the content of all detected files.
3. **LLM Reasoning**: Sends task context to Anthropic Claude or OpenAI API for analysis.
4. **Plan Generation**: Generates a comprehensive execution plan including:
   - Task Analysis & objective breakdown
   - Dependency mapping
   - Step-by-step execution steps
   - Complexity assessment (Low/Medium/High)
   - Priority ordering (Urgent/High/Medium/Low)
   - Warnings and considerations
5. **Output**: Saves timestamped plan to `Plans/` directory.
6. **Master Plan Update**: Appends to `Plan.md` in `Needs_Action` for backward compatibility.
7. **Logging**: Records success, LLM engine used, and any errors.

## Plan Output Format

LLM-generated plans follow this structure:

```markdown
# Task Execution Plan

## Task Analysis
[Core objective and scope]

## Dependencies
[Prerequisites and blocking factors]

## Step-by-Step Plan
1. [Execution step 1]
2. [Execution step 2]
...

## Complexity: [Low/Medium/High]
## Priority: [Urgent/High/Medium/Low]
## Notes
[Warnings, resources, considerations]
```

## Rules
- **LLM-First**: Always attempts API-based planning first.
- **Automatic Fallback**: Silently falls back to templates if APIs fail or are unconfigured.
- **Traceable**: Every plan includes timestamp and LLM engine identifier in logs.
- **Error Handling**: Gracefully handles API failures, rate limits, and network issues.
- **Idempotent**: Safe to run multiple times - generates new timestamped plans each run.
