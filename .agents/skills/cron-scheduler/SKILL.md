---
name: cron-scheduler
description: Schedules and runs AI Employee tasks using cron jobs (Linux) or Task Scheduler (Windows). Provides automated execution of watchers, planners, and processors on configurable schedules. Use when time-based task automation is needed.
---

# Cron Scheduler

Automates AI Employee task execution via system schedulers (cron/Task Scheduler).

## Overview

Provides scripts and configurations to schedule AI Employee operations using native system schedulers. Supports both Linux (cron) and Windows (Task Scheduler).

## Components

- **Setup Script**: `scripts/setup_scheduler.py`
- **Cron Template**: `assets/cron_template.txt`
- **Windows Task Template**: `assets/windows_task.xml`
- **Log**: `logs/cron_scheduler.log`

## Usage

### Quick Setup (Recommended)
```bash
python .agents/skills/cron-scheduler/scripts/setup_scheduler.py
```

This interactive script will:
1. Detect your OS (Linux/Windows)
2. Ask which tasks to schedule
3. Configure execution intervals
4. Install the scheduled tasks

### Manual Setup - Linux (cron)

1. Edit the cron template:
```bash
nano .agents/skills/cron-scheduler/assets/cron_template.txt
```

2. Install cron jobs:
```bash
crontab .agents/skills/cron-scheduler/assets/cron_template.txt
```

3. Verify installation:
```bash
crontab -l
```

### Manual Setup - Windows (Task Scheduler)

1. Edit the task template:
```bash
notepad .agents/skills/cron-scheduler/assets/windows_task.xml
```

2. Import task:
```bash
schtasks /create /tn "AI_Employee" /xml .agents/skills/cron-scheduler/assets/windows_task.xml
```

3. Verify installation:
```bash
schtasks /query /tn "AI_Employee"
```

## Default Schedule

The default configuration runs these tasks:

| Task | Frequency | Time | Description |
|------|-----------|------|-------------|
| Gmail Watcher | Every 5 minutes | All day | Check for new emails |
| LinkedIn Watcher | Every 15 minutes | Business hours | Monitor LinkedIn activity |
| Task Planner | Every hour | All day | Generate plans for new tasks |
| Task Processor | Every 30 minutes | All day | Process completed tasks |
| LinkedIn Post | Daily | 9:00 AM | Publish scheduled business post |
| Log Rotation | Daily | 11:59 PM | Rotate and archive logs |

## Customization

### Change Execution Frequency

Edit the cron schedule (Linux):
```cron
# Format: minute hour day month weekday command
*/5 * * * * python /path/to/scripts/watch_gmail.py  # Every 5 minutes
0 9 * * 1-5 python /path/to/post_business_content.py --template thought_leadership  # Weekdays at 9 AM
```

### Change Execution Time (Windows)

Edit the XML template and modify:
```xml
<StartBoundary>2024-01-15T09:00:00</StartBoundary>
<ScheduleByDay>
  <DaysInterval>1</DaysInterval>
</ScheduleByDay>
```

### Add Custom Tasks

Add any script to the schedule:

**Linux (cron):**
```cron
*/10 * * * * python3 /path/to/your_script.py >> /path/to/logs/custom.log 2>&1
```

**Windows:**
Create a new task via GUI:
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger and action
4. Point to your script

## Wrapper Script

For reliable execution with logging, use the wrapper:

```bash
python .agents/skills/cron-scheduler/scripts/run_scheduled.py --task gmail_watcher
```

This wrapper:
- Logs execution to `logs/cron_scheduler.log`
- Handles errors gracefully
- Prevents duplicate runs
- Sends notifications on failure (optional)

### Available Tasks

```bash
python .agents/skills/cron-scheduler/scripts/run_scheduled.py --list
```

Output:
```
Available scheduled tasks:
  - gmail_watcher: Monitor Gmail for new emails
  - linkedin_watcher: Monitor LinkedIn activity
  - task_planner: Generate execution plans
  - task_processor: Process completed tasks
  - linkedin_post: Publish LinkedIn business post
  - log_rotation: Rotate log files
```

## Monitoring

### Check Last Execution

```bash
python .agents/skills/cron-scheduler/scripts/run_scheduled.py --status
```

### View Execution Logs

```bash
tail -f logs/cron_scheduler.log
```

### Remove All Scheduled Tasks

**Linux:**
```bash
crontab -r
```

**Windows:**
```bash
schtasks /delete /tn "AI_Employee" /f
```

## Rules

- **Absolute Paths**: Always use absolute paths in cron/task definitions
- **Logging**: All executions logged with timestamps
- **Error Handling**: Failures don't stop other tasks from running
- **Idempotent**: Safe to run multiple times without side effects
- **Resource Management**: Prevents overlapping executions via lock files
- **Notifications**: Optional email alerts on failures (configure in `.env`)

## Troubleshooting

**Task Not Running**: 
- Verify cron/Task Scheduler is active
- Check script permissions (`chmod +x` for Linux)
- Review logs for errors

**Permission Denied**:
- Linux: Ensure scripts are executable
- Windows: Run Task Scheduler as Administrator

**Python Not Found**:
- Use full path to Python executable
- Example: `/usr/bin/python3` or `C:\Python39\python.exe`

**Overlapping Executions**:
- Increase interval between runs
- Check lock files in `logs/` directory

## Integration with AI Employee

The cron scheduler integrates seamlessly with all AI Employee skills:

1. **Watchers**: Run on schedule to monitor external services
2. **Planners**: Generate plans periodically for new tasks
3. **Processors**: Execute completed tasks automatically
4. **Posters**: Publish content at optimal times
5. **Maintenance**: Rotate logs, cleanup old files

This creates a fully autonomous AI Employee that operates 24/7 without manual intervention.
