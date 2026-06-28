#!/usr/bin/env python3
"""
Cron Scheduler Setup - Interactive setup for scheduling AI Employee tasks.
Supports both Linux (cron) and Windows (Task Scheduler).
"""

import os
import sys
import platform
import subprocess
from datetime import datetime

# Configuration
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SKILL_DIR)))
LOG_FILE = os.path.join(PROJECT_ROOT, "logs/cron_scheduler.log")

# Ensure directories exist
os.makedirs(os.path.join(PROJECT_ROOT, "logs"), exist_ok=True)


def log_message(message):
    """Log a message to the cron scheduler log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {message}\n"
    
    try:
        with open(LOG_FILE, "a") as f:
            f.write(entry)
    except IOError:
        pass
    
    print(message)


def detect_os():
    """Detect operating system."""
    system = platform.system()
    if system == "Linux":
        return "linux"
    elif system == "Windows":
        return "windows"
    else:
        return "unknown"


def setup_linux_cron():
    """Setup cron jobs on Linux."""
    log_message("Setting up Linux cron jobs...")
    
    cron_template = os.path.join(SKILL_DIR, "..", "assets", "cron_template.txt")
    
    if not os.path.exists(cron_template):
        log_message("ERROR: Cron template not found")
        return False
    
    try:
        # Read template
        with open(cron_template, "r") as f:
            cron_content = f.read()
        
        # Replace placeholder with actual project path
        cron_content = cron_content.replace("{PROJECT_PATH}", PROJECT_ROOT)
        cron_content = cron_content.replace("{PYTHON}", sys.executable)
        
        # Install cron jobs
        process = subprocess.run(
            ["crontab", "-"],
            input=cron_content,
            text=True,
            capture_output=True
        )
        
        if process.returncode == 0:
            log_message("SUCCESS: Cron jobs installed")
            
            # Verify installation
            verify = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
            if verify.returncode == 0:
                log_message("Verified: Cron jobs active")
                print("\nActive cron jobs:")
                print(verify.stdout)
            
            return True
        else:
            log_message(f"ERROR: Failed to install cron jobs: {process.stderr}")
            return False
            
    except Exception as e:
        log_message(f"ERROR: {e}")
        return False


def setup_windows_task():
    """Setup Task Scheduler on Windows."""
    log_message("Setting up Windows Task Scheduler...")
    
    task_xml = os.path.join(SKILL_DIR, "..", "assets", "windows_task.xml")
    
    if not os.path.exists(task_xml):
        log_message("ERROR: Windows task template not found")
        return False
    
    try:
        # Read and customize XML
        with open(task_xml, "r") as f:
            xml_content = f.read()
        
        xml_content = xml_content.replace("{PROJECT_PATH}", PROJECT_ROOT)
        xml_content = xml_content.replace("{PYTHON}", sys.executable)
        
        # Save customized XML
        customized_xml = os.path.join(PROJECT_ROOT, "logs", "ai_employee_task.xml")
        with open(customized_xml, "w") as f:
            f.write(xml_content)
        
        # Import task
        cmd = f'schtasks /create /tn "AI_Employee" /xml "{customized_xml}" /f'
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if process.returncode == 0:
            log_message("SUCCESS: Task created in Task Scheduler")
            
            # Verify installation
            verify = subprocess.run(
                'schtasks /query /tn "AI_Employee"',
                shell=True,
                capture_output=True,
                text=True
            )
            
            if verify.returncode == 0:
                log_message("Verified: Task active in Task Scheduler")
                print("\nTask details:")
                print(verify.stdout)
            
            return True
        else:
            log_message(f"ERROR: Failed to create task: {process.stderr}")
            log_message("Try running this script as Administrator")
            return False
            
    except Exception as e:
        log_message(f"ERROR: {e}")
        return False


def interactive_setup():
    """Interactive setup wizard."""
    print("\n" + "=" * 60)
    print("AI Employee - Cron Scheduler Setup")
    print("=" * 60 + "\n")
    
    os_name = detect_os()
    log_message(f"Detected OS: {os_name}")
    
    if os_name == "unknown":
        log_message("ERROR: Unsupported operating system")
        return False
    
    print("\nThis will schedule the following tasks:")
    print("  1. Gmail Watcher (every 5 minutes)")
    print("  2. LinkedIn Watcher (every 15 minutes)")
    print("  3. Task Planner (every hour)")
    print("  4. Task Processor (every 30 minutes)")
    print("  5. LinkedIn Business Post (daily at 9 AM)")
    print("  6. Log Rotation (daily at midnight)")
    print()
    
    response = input("Continue? (y/n): ").strip().lower()
    if response != "y":
        log_message("Setup cancelled by user")
        return False
    
    if os_name == "linux":
        return setup_linux_cron()
    elif os_name == "windows":
        return setup_windows_task()
    
    return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cron Scheduler Setup")
    parser.add_argument("--auto", action="store_true", help="Automatic setup without prompts")
    parser.add_argument("--status", action="store_true", help="Show scheduled tasks status")
    
    args = parser.parse_args()
    
    if args.status:
        os_name = detect_os()
        if os_name == "linux":
            subprocess.run(["crontab", "-l"])
        elif os_name == "windows":
            subprocess.run('schtasks /query /tn "AI_Employee"', shell=True)
        return
    
    if args.auto:
        os_name = detect_os()
        if os_name == "linux":
            setup_linux_cron()
        elif os_name == "windows":
            setup_windows_task()
    else:
        interactive_setup()


if __name__ == "__main__":
    main()
