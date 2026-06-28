import os
import sys
import json
import shutil
import requests
from datetime import datetime

# --- CONFIGURATION ---
INBOX_DIR = "AI_Employee_Vault/Inbox"
NEEDS_ACTION_DIR = "AI_Employee_Vault/Needs_Action"
DONE_DIR = "AI_Employee_Vault/Done"
PLANS_DIR = "AI_Employee_Vault/Plans"
LOG_FILE = "logs/actions.log"
PLAN_FILE = os.path.join(NEEDS_ACTION_DIR, "Plan.md")

def log_action(message):
    """Logs an action to logs/actions.log."""
    if not os.path.exists("logs"):
        os.makedirs("logs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] [PLANNER] {message}\n")
    print(f"[{timestamp}] [PLANNER] {message}")

def ensure_dirs():
    for d in [INBOX_DIR, NEEDS_ACTION_DIR, DONE_DIR, PLANS_DIR]:
        os.makedirs(d, exist_ok=True)

def load_env():
    """Load environment variables from .env file."""
    env_file = ".env"
    if not os.path.exists(env_file):
        return {}
    env_vars = {}
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()
    return env_vars

def generate_plan_gemini(tasks):
    """Generate plan using Google Gemini API (direct)."""
    env = load_env()
    api_key = os.environ.get("GEMINI_API_KEY") or env.get("GEMINI_API_KEY")
    model = os.environ.get("GEMINI_MODEL") or env.get("GEMINI_MODEL", "gemini-2.0-flash")

    if not api_key:
        return None

    task_context = "\n\n".join([
        f"Task {i+1}: {t['filename']}\nContent:\n{t['content'][:500]}"
        for i, t in enumerate(tasks)
    ])

    prompt = f"""You are an expert task planner for an AI Employee system. Analyze the following tasks and create a comprehensive execution plan.

{task_context}

Generate a plan in the following format:

# Task Execution Plan

## Task Analysis
[Analyze objectives]

## Dependencies
[List prerequisites]

## Step-by-Step Plan
- [ ] Step 1
- [ ] Step 2

## Complexity: [Low/Medium/High]
## Priority: [Urgent/High/Medium/Low]
"""

    try:
        import requests

        response = requests.post(
            url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2048
                }
            },
            timeout=30
        )
        data = response.json()

        if "candidates" in data and len(data["candidates"]) > 0:
            plan = data["candidates"][0]["content"]["parts"][0]["text"]
            log_action(f"Generated plan using Gemini ({model})")
            return plan
        else:
            log_action(f"Gemini response format unexpected: {data}")
            return None
    except Exception as e:
        log_action(f"Gemini API error: {e}")
        return None

def generate_plan_openrouter(tasks):
    """Generate plan using OpenRouter API (primary LLM)."""
    env = load_env()
    api_key = os.environ.get("OPENROUTER_API_KEY") or env.get("OPENROUTER_API_KEY")
    model = os.environ.get("OPENROUTER_MODEL") or env.get("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")

    if not api_key:
        return None

    task_context = "\n\n".join([
        f"Task {i+1}: {t['filename']}\nContent:\n{t['content'][:500]}"
        for i, t in enumerate(tasks)
    ])

    prompt = f"""You are an expert task planner for an AI Employee system. Analyze the following tasks and create a comprehensive execution plan.

{task_context}

Generate a plan in the following format:

# Task Execution Plan

## Task Analysis
[Analyze objectives]

## Dependencies
[List prerequisites]

## Step-by-Step Plan
- [ ] Step 1
- [ ] Step 2

## Complexity: [Low/Medium/High]
## Priority: [Urgent/High/Medium/Low]
"""

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://ai-employee.local",
                "X-Title": "AI Employee Task Planner"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30
        )
        data = response.json()
        if "choices" in data and len(data["choices"]) > 0:
            plan = data['choices'][0]['message']['content']
            log_action(f"Generated plan using OpenRouter ({model})")
            return plan
        else:
            log_action(f"OpenRouter response format unexpected: {data}")
            return None
    except Exception as e:
        log_action(f"OpenRouter error: {e}")
        return None

def generate_plan_claude(tasks):
    """Generate plan using Anthropic Claude API."""
    env = load_env()
    api_key = os.environ.get("ANTHROPIC_API_KEY") or env.get("ANTHROPIC_API_KEY")
    model = os.environ.get("ANTHROPIC_MODEL") or env.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    if not api_key:
        return None

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        task_context = "\n\n".join([
            f"Task {i+1}: {t['filename']}\nContent:\n{t['content'][:500]}"
            for i, t in enumerate(tasks)
        ])

        prompt = f"""You are an expert task planner for an AI Employee system. Analyze the following tasks and create a comprehensive execution plan.

{task_context}

Generate a plan with: Task Analysis, Dependencies, Step-by-Step Plan (using - [ ] format), Complexity, Priority, and Notes."""

        message = client.messages.create(
            model=model,
            max_tokens=2000,
            temperature=0.7,
            system="You are a strategic planning assistant for an AI Employee system.",
            messages=[{"role": "user", "content": prompt}]
        )

        plan = message.content[0].text
        log_action(f"Generated plan using Claude ({model})")
        return plan
    except ImportError:
        log_action("anthropic package not installed")
        return None
    except Exception as e:
        log_action(f"Claude API error: {e}")
        return None

def generate_plan_openai(tasks):
    """Generate plan using OpenAI GPT API."""
    env = load_env()
    api_key = os.environ.get("OPENAI_API_KEY") or env.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL") or env.get("OPENAI_MODEL", "gpt-4o-mini")

    if not api_key:
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        task_context = "\n\n".join([
            f"Task {i+1}: {t['filename']}\nContent:\n{t['content'][:500]}"
            for i, t in enumerate(tasks)
        ])

        prompt = f"""You are an expert task planner for an AI Employee system. Analyze these tasks and create a comprehensive execution plan.

{task_context}

Generate a plan with: Task Analysis, Dependencies, Step-by-Step Plan (using - [ ] format), Complexity, Priority, and Notes."""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a strategic planning assistant for an AI Employee system."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )

        plan = response.choices[0].message.content
        log_action(f"Generated plan using OpenAI ({model})")
        return plan
    except ImportError:
        log_action("openai package not installed")
        return None
    except Exception as e:
        log_action(f"OpenAI API error: {e}")
        return None

def generate_plan_template(tasks):
    """Generate plan using template-based approach (fallback)."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    plan = f"""# Task Execution Plan

Generated: {timestamp}
Tasks Analyzed: {len(tasks)}

## Task Analysis
"""

    for i, task in enumerate(tasks, 1):
        plan += f"""
### Task {i}: {task['filename']}
- **Type**: {task.get('type', 'general')}
- **Priority**: {task.get('priority', 'medium')}
- **Overview**: {task['content'][:200]}...
"""

    plan += f"""
## Dependencies
- Review each task individually
- Identify any shared resources or prerequisites
- Check for task interdependencies

## Step-by-Step Plan
- [ ] Review all {len(tasks)} tasks in Needs_Action directory
- [ ] Categorize tasks by type and priority
- [ ] Execute high-priority tasks first
- [ ] Handle dependent tasks in order
- [ ] Verify completion of each task
- [ ] Move completed tasks to Done directory

## Complexity: Medium
## Priority: High
## Notes
- Follow the AI Employee workflow guidelines
- Log all actions in System_Log.md
- Update Dashboard.md after completing each task
- Use human approval workflow for sensitive actions
"""

    log_action("Generated plan using template mode (LLM fallback)")
    return plan

def read_task_file(filepath):
    """Read and parse a task file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        metadata = {}
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 2:
                frontmatter = parts[1]
                for line in frontmatter.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        metadata[key.strip()] = value.strip()
        return {
            "filename": os.path.basename(filepath),
            "content": content,
            "type": metadata.get("type", "general"),
            "priority": metadata.get("priority", "medium")
        }
    except Exception as e:
        log_action(f"Error reading {filepath}: {e}")
        return None

def run_planner():
    ensure_dirs()
    files = [f for f in os.listdir(INBOX_DIR) if f.endswith(".md")]

    if not files:
        log_action("No new files to plan.")
        return

    # Read all tasks
    tasks = []
    processed_files = []

    for file in files:
        file_path = os.path.join(INBOX_DIR, file)
        log_action(f"Reading file for planning: {file}")

        task = read_task_file(file_path)
        if task:
            tasks.append(task)
            processed_files.append(file)

    if not tasks:
        log_action("No valid tasks found.")
        return

    # LLM-first planning: Try APIs in order
    plan_content = None

    # 1. Try OpenRouter (primary - user has key)
    if not plan_content:
        plan_content = generate_plan_openrouter(tasks)

    # 2. Try Gemini (fallback #1 - user has key)
    if not plan_content:
        plan_content = generate_plan_gemini(tasks)

    # 3. Try Claude (fallback #2)
    if not plan_content:
        plan_content = generate_plan_claude(tasks)

    # 4. Try OpenAI (fallback #3)
    if not plan_content:
        plan_content = generate_plan_openai(tasks)

    # 5. Fallback to template
    if not plan_content:
        plan_content = generate_plan_template(tasks)

    if not plan_content:
        log_action("ERROR: All planning methods failed!")
        return

    # Save timestamped plan to Plans directory
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    plan_filename = f"Plan_{timestamp}.md"
    plan_path = os.path.join(PLANS_DIR, plan_filename)

    try:
        with open(plan_path, "w", encoding="utf-8") as f:
            f.write(plan_content)
        log_action(f"Saved plan to: {plan_path}")
    except Exception as e:
        log_action(f"Failed to save plan: {e}")

    # Update master Plan.md in Needs_Action
    try:
        with open(PLAN_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n\n---\n# Plan Generated: {timestamp}\n\n")
            f.write(plan_content)
        log_action(f"Updated master plan: {PLAN_FILE}")
    except Exception as e:
        log_action(f"Failed to update master plan: {e}")

    # Move processed files to Done
    for file in processed_files:
        src = os.path.join(INBOX_DIR, file)
        dst = os.path.join(DONE_DIR, file)

        if os.path.exists(dst):
            base, ext = os.path.splitext(file)
            dst = os.path.join(DONE_DIR, f"{base}_{int(datetime.now().timestamp())}{ext}")

        shutil.move(src, dst)
        log_action(f"MOVED: '{file}' to Done folder.")

    log_action(f"Plan generation complete for {len(tasks)} tasks")

if __name__ == "__main__":
    run_planner()
