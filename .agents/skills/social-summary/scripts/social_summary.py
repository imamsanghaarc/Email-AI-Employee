import os
import sys
import argparse
from datetime import datetime

# --- CONFIGURATION ---
REPORTS_DIR = "AI_Employee_Vault/Reports"
SOCIAL_LOGS_FILE = os.path.join(REPORTS_DIR, "Social_Logs.md")

def ensure_file_exists():
    """Ensure the Reports directory and Social_Logs.md exist with headers."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    if not os.path.exists(SOCIAL_LOGS_FILE):
        with open(SOCIAL_LOGS_FILE, "w") as f:
            f.write("# Social Media Logs\n\n")
            f.write("| Date | Platform | Content Summary |\n")
            f.write("|------|----------|-----------------|\n")

def log_post(platform, content):
    """Logs a social media post to Social_Logs.md."""
    ensure_file_exists()
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Truncate content for the table summary
    summary = content.replace("\n", " ").strip()
    if len(summary) > 100:
        summary = summary[:97] + "..."
        
    entry = f"| {date_str} | {platform.capitalize()} | {summary} |\n"
    
    try:
        with open(SOCIAL_LOGS_FILE, "a") as f:
            f.write(entry)
        print(f"Logged {platform} post to {SOCIAL_LOGS_FILE}")
        return True
    except Exception as e:
        print(f"Error logging social post: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Social Media Summary Logger")
    parser.add_argument("platform", help="Social media platform (e.g., LinkedIn, Twitter)")
    parser.add_argument("content", help="The content of the post")
    
    args = parser.parse_args()
    
    success = log_post(args.platform, args.content)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
