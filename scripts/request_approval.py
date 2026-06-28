import os
import time
import argparse
from datetime import datetime

APPROVAL_DIR = "AI_Employee_Vault/Needs_Approval"

def wait_for_approval(filename, timeout=None):
    file_path = os.path.join(APPROVAL_DIR, filename)
    # Ensure it exists with signature
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write(f"--- APPROVAL REQUEST ---\nTask: {filename}\nTime: {datetime.now()}\n\n"
                    "PLEASE WRITE 'APPROVED' BELOW THIS LINE:\n\n"
                    "--------------------------------------------------\n"
                    "[SIGNATURE PLACEHOLDER: ________________________]\n")
    
    print(f"Waiting for approval in {file_path}...")
    start_time = time.time()
    while True:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                content = f.read()
                if "APPROVED" in content.upper():
                    print("Approval detected!")
                    return True
        if timeout is not None and (time.time() - start_time) > timeout:
            print("Timeout reached waiting for approval.")
            return False
        time.sleep(2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    parser.add_argument("--timeout", type=int, default=None, help="Timeout in seconds")
    args = parser.parse_args()
    if wait_for_approval(args.filename, timeout=args.timeout):
        exit(0)
    exit(1)
