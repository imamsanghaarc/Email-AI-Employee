import os
import shutil
from datetime import datetime

# --- CONFIGURATION ---
# Target files to monitor
LOG_FILES = [
    "System_Log.md",
    "logs/watcher_error.log",
    "AI_Employee_Vault/Dashboard.md"
]

# Size limit in bytes (1.5 MB = 1.5 * 1024 * 1024)
SIZE_LIMIT = 1.5 * 1024 * 1024

def rotate_log(file_path):
    """
    Renames the current log file with a timestamp and creates a new empty one.
    """
    try:
        # Generate timestamp for the archive name (e.g., 2026-04-07_12-30-00)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # Split the path to insert the timestamp before the extension
        base, extension = os.path.splitext(file_path)
        archive_name = f"{base}_{timestamp}{extension}"
        
        # 1. Rename the old file to the archive name
        print(f"[*] Rotating {file_path} to {archive_name}...")
        shutil.move(file_path, archive_name)
        
        # 2. Create a new empty log file with the original name
        with open(file_path, "w") as f:
            if file_path.endswith(".md"):
                # If it's a Markdown log, add a default header
                f.write(f"# {os.path.basename(base).replace('_', ' ')}\n\n## Activity Log\n")
            else:
                f.write(f"--- Log Reset at {timestamp} ---\n")
                
        print(f"[+] Fresh log file created: {file_path}")
        
    except Exception as e:
        print(f"[!] Error rotating {file_path}: {e}")

def main():
    print("[*] Running Log Manager...")
    
    for log_path in LOG_FILES:
        # Check if the file exists first
        if os.path.exists(log_path):
            file_size = os.path.getsize(log_path)
            
            # Check if size exceeds 1.5 MB
            if file_size > SIZE_LIMIT:
                print(f"[!] {log_path} is too large ({file_size / 1024 / 1024:.2f} MB)")
                rotate_log(log_path)
            else:
                print(f"[OK] {log_path} is within size limits.")
        else:
            print(f"[?] {log_path} does not exist yet. Skipping.")

if __name__ == "__main__":
    main()
