import os
import sys
import time
import argparse
from datetime import datetime

DIR = "AI_Employee_Vault/Needs_Approval"

def request_approval(file, details):
    os.makedirs(DIR, exist_ok=True)
    path = os.path.join(DIR, file)
    
    with open(path, "w") as f:
        f.write(f"--- APPROVAL REQUEST ---\nTime: {datetime.now()}\nAction: {details}\n")
        f.write("INSTRUCTIONS: Write 'APPROVED' or 'REJECTED' on a new line below.\n")
        f.write("--- DECISION ZONE ---\n")

    print(f"[*] Request created: {path}\n[*] Waiting for decision...")

    try:
        while True:
            if not os.path.exists(path):
                print("ERROR: Request file removed.")
                return False
            
            with open(path, "r") as f:
                lines = f.readlines()
            
            zone = False
            for line in lines:
                if "--- DECISION ZONE ---" in line: zone = True; continue
                if zone:
                    cmd = line.strip().upper()
                    if cmd == "APPROVED":
                        print("SUCCESS: Approved.")
                        os.rename(path, path + ".approved")
                        return True
                    if cmd in ["REJECTED", "REJECTION"]:
                        print("ABORTED: Rejected.")
                        os.rename(path, path + ".rejected")
                        return False
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nABORTED: Cancelled.")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("--details", required=True)
    args = parser.parse_args()
    sys.exit(0 if request_approval(args.file, args.details) else 1)
