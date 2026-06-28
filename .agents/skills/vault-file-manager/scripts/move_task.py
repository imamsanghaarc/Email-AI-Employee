import os
import shutil
import sys
import argparse

VAULT = "AI_Employee_Vault"
PATHS = {
    "inbox": os.path.join(VAULT, "Inbox"),
    "needs_action": os.path.join(VAULT, "Needs_Action"),
    "done": os.path.join(VAULT, "Done")
}

def move_task(file, src, dst):
    if src not in PATHS or dst not in PATHS:
        print(f"ERROR: Invalid folder keys. Use: {list(PATHS.keys())}")
        return False
    
    source = os.path.join(PATHS[src], file)
    target = os.path.join(PATHS[dst], file)
    
    if not os.path.exists(source):
        print(f"ERROR: {file} not found in {src}")
        return False

    os.makedirs(PATHS[dst], exist_ok=True)
    try:
        shutil.move(source, target)
        print(f"SUCCESS: Moved {file} to {dst}")
        return True
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("--from-dir", required=True)
    parser.add_argument("--to-dir", required=True)
    args = parser.parse_args()
    sys.exit(0 if move_task(args.file, args.from_dir, args.to_dir) else 1)
