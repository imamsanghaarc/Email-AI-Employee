import os
import shutil
import time
from datetime import datetime

# --- CONFIGURATION ---
LOGS_DIR = "logs"
MAX_LOG_SIZE_MB = 2.0  # 2MB Limit
ARCHIVE_DIR = os.path.join(LOGS_DIR, "archive")

def rotate_logs():
    print(f"[*] Starting Log Rotation (Limit: {MAX_LOG_SIZE_MB}MB)...")
    if not os.path.exists(LOGS_DIR):
        return

    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for filename in os.listdir(LOGS_DIR):
        if filename.endswith(".log"):
            file_path = os.path.join(LOGS_DIR, filename)
            
            # Check size
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if size_mb > MAX_LOG_SIZE_MB:
                print(f"⚠️ Rotating {filename} ({size_mb:.2f}MB)...")
                
                # Copy to archive
                archive_name = f"{filename}_{timestamp}.bak"
                shutil.copy(file_path, os.path.join(ARCHIVE_DIR, archive_name))
                
                # Clear original
                with open(file_path, "w") as f:
                    f.write(f"--- Log Rotated at {datetime.now()} ---\n")
                
                print(f"✅ {filename} rotated.")

    print("[*] Log rotation complete.")

if __name__ == "__main__":
    rotate_logs()
