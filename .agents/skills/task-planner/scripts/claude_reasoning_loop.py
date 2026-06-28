#!/usr/bin/env python3
"""
Claude Reasoning Loop - Generates intelligent execution plans for tasks using Anthropic Claude API.
Creates Plan.md files with step-by-step guidance for AI Employee.
Falls back to template-based planning if API is unavailable.
"""

import os
import sys
import json
import time
import logging
from datetime import datetime

# Configuration
INBOX_DIR = "AI_Employee_Vault/Inbox"
PLANS_DIR = "AI_Employee_Vault/Plans"
NEEDS_ACTION_DIR = "AI_Employee_Vault/Needs_Action"
LOG_FILE = "logs/claude_reasoning_loop.log"
PLAN_FILE = os.path.join(NEEDS_ACTION_DIR, "Plan.md")

# Ensure directories exist
os.makedirs(PLANS_DIR, exist_ok=True)
os.makedirs(NEEDS_ACTION_DIR, exist_ok=True)
os.makedirs("logs", exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


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


def generate_plan_claude(tasks):
    """Generate plan using Anthropic Claude API."""
    api_key = os.environ.get("ANTHROPIC_API_KEY") or load_env().get("ANTHROPIC_API_KEY")
    model = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not found. Falling back to template mode.")
        return None
    
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Build task context
        task_context = "\n\n".join([
            f"Task {i+1}: {t['filename']}\nContent:\n{t['content']}"
            for i, t in enumerate(tasks)
        ])
        
        prompt = f"""You are an expert task planner for an AI Employee system. Analyze the following tasks and create a comprehensive execution plan.

{task_context}

Generate a plan in the following format:

# Task Execution Plan

## Task Analysis
[Analyze all tasks and identify core objectives]

## Dependencies
[List any dependencies or prerequisites]

## Step-by-Step Plan
1. [First action step]
2. [Second action step]
...

## Complexity: [Low/Medium/High]
## Priority: [Urgent/High/Medium/Low]
## Notes
[Any warnings, resources, or considerations]

Make the plan actionable and specific. Consider task relationships and optimal execution order."""

        message = client.messages.create(
            model=model,
            max_tokens=2000,
            temperature=0.7,
            system="You are a strategic planning assistant for an AI Employee system.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        plan_content = message.content[0].text
        logger.info(f"Generated plan using Claude ({model})")
        return plan_content
        
    except ImportError:
        logger.error("anthropic package not installed. Install with: pip install anthropic")
        return None
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return None


def generate_plan_openai(tasks):
    """Generate plan using OpenAI GPT API."""
    api_key = os.environ.get("OPENAI_API_KEY") or load_env().get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    
    if not api_key:
        logger.warning("OPENAI_API_KEY not found.")
        return None
    
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=api_key)
        
        # Build task context
        task_context = "\n\n".join([
            f"Task {i+1}: {t['filename']}\nContent:\n{t['content']}"
            for i, t in enumerate(tasks)
        ])
        
        prompt = f"""You are an expert task planner for an AI Employee system. Analyze the following tasks and create a comprehensive execution plan.

{task_context}

Generate a plan in the following format:

# Task Execution Plan

## Task Analysis
[Analyze all tasks and identify core objectives]

## Dependencies
[List any dependencies or prerequisites]

## Step-by-Step Plan
1. [First action step]
2. [Second action step]
...

## Complexity: [Low/Medium/High]
## Priority: [Urgent/High/Medium/Low]
## Notes
[Any warnings, resources, or considerations]

Make the plan actionable and specific. Consider task relationships and optimal execution order."""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a strategic planning assistant for an AI Employee system."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        plan_content = response.choices[0].message.content
        logger.info(f"Generated plan using OpenAI ({model})")
        return plan_content
        
    except ImportError:
        logger.error("openai package not installed. Install with: pip install openai")
        return None
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
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
1. Review all {len(tasks)} tasks in Needs_Action directory
2. Categorize tasks by type and priority
3. Execute high-priority tasks first
4. Handle dependent tasks in order
5. Verify completion of each task
6. Move completed tasks to Done directory

## Complexity: Medium
## Priority: High
## Notes
- Follow the AI Employee workflow guidelines
- Log all actions in System_Log.md
- Update Dashboard.md after completing each task
- Use human approval workflow for sensitive actions
"""
    
    logger.info("Generated plan using template mode")
    return plan


def read_task_file(filepath):
    """Read and parse a task file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Extract metadata from frontmatter
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
        logger.error(f"Error reading {filepath}: {e}")
        return None


def generate_plan_gemini(tasks):
    """Generate plan using Google Gemini API (direct)."""
    api_key = os.environ.get("GEMINI_API_KEY") or load_env().get("GEMINI_API_KEY")
    model = os.environ.get("GEMINI_MODEL") or load_env().get("GEMINI_MODEL", "gemini-2.0-flash")

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
            logger.info(f"Generated plan using Gemini ({model})")
            return plan
        else:
            logger.warning(f"Gemini response format unexpected: {data}")
            return None
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return None

def generate_plan_openrouter(tasks):
    """Generate plan using OpenRouter API."""
    api_key = os.environ.get("OPENROUTER_API_KEY") or load_env().get("OPENROUTER_API_KEY")
    model = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")
    
    if not api_key:
        return None
    
    try:
        import requests
        
        task_context = "\n\n".join([
            f"Task {i+1}: {t['filename']}\nContent:\n{t['content']}"
            for i, t in enumerate(tasks)
        ])
        
        prompt = f"""You are an expert task planner for an AI Employee system. Analyze the following tasks and create a comprehensive execution plan.

{task_context}

Generate a plan in the following format:

# Task Execution Plan

## Task Analysis
[Analyze objectives]

## Step-by-Step Plan
- [ ] Step 1
- [ ] Step 2

## Complexity: [Low/Medium/High]
## Priority: [Urgent/High/Medium/Low]
"""

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            data=json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": prompt}]
            })
        )
        data = response.json()
        plan_content = data['choices'][0]['message']['content']
        logger.info(f"Generated plan using OpenRouter ({model})")
        return plan_content
    except Exception as e:
        logger.error(f"OpenRouter error: {e}")
        return None

def generate_plans():
    """Main function to generate execution plans for inbox tasks."""
    # Find all task files in Inbox
    if not os.path.exists(INBOX_DIR):
        logger.warning(f"Inbox directory not found: {INBOX_DIR}")
        return False

    task_files = [f for f in os.listdir(INBOX_DIR) if f.endswith(".md")]
    if not task_files:
        logger.info("No tasks in Inbox. Nothing to plan for.")
        return True

    # Read all tasks
    tasks = []
    for filename in task_files:
        filepath = os.path.join(INBOX_DIR, filename)
        task = read_task_file(filepath)
        if task:
            tasks.append(task)

    if not tasks:
        logger.warning("No valid tasks found.")
        return False

    # Try LLM APIs in order: OpenRouter -> Gemini -> Claude -> OpenAI -> Template
    plan_content = None

    # 1. Try OpenRouter first (user has this key configured)
    if not plan_content:
        plan_content = generate_plan_openrouter(tasks)

    # 2. Try Gemini (user has this key configured)
    if not plan_content:
        plan_content = generate_plan_gemini(tasks)

    # 3. Try Claude API
    if not plan_content:
        plan_content = generate_plan_claude(tasks)

    # 4. Try OpenAI API
    if not plan_content:
        plan_content = generate_plan_openai(tasks)

    # 4. Fallback to template
    if not plan_content:
        plan_content = generate_plan_template(tasks)
        if not plan_content:
            logger.error("All planning methods failed!")
            return False

    # Save timestamped plan
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    plan_filename = f"Plan_{timestamp}.md"
    plan_path = os.path.join(PLANS_DIR, plan_filename)

    try:
        with open(plan_path, "w", encoding="utf-8") as f:
            f.write(plan_content)
        logger.info(f"Saved plan to: {plan_path}")
    except IOError as e:
        logger.error(f"Failed to save plan: {e}")
        return False

    # Update master Plan.md in Needs_Action
    try:
        with open(PLAN_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n\n---\n# Plan Generated: {timestamp}\n\n")
            f.write(plan_content)
        logger.info(f"Updated master plan: {PLAN_FILE}")
    except IOError as e:
        logger.error(f"Failed to update master plan: {e}")

    logger.info("Plan generation complete!")
    return True


def main():
    """Main entry point."""
    success = generate_plans()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
