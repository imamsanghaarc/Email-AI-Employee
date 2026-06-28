import os
import sys
import argparse
import re
from datetime import datetime, timedelta
from typing import List, Dict

# --- CONFIGURATION ---
ACCOUNTING_FILE = "AI_Employee_Vault/Accounting/Current_Month.md"

def ensure_file_exists():
    """Ensure the Current_Month.md file exists with proper headers."""
    if not os.path.exists(ACCOUNTING_FILE):
        os.makedirs(os.path.dirname(ACCOUNTING_FILE), exist_ok=True)
        with open(ACCOUNTING_FILE, "w") as f:
            f.write(f"# Accounting - {datetime.now().strftime('%B %Y')}\n\n")
            f.write("| Date | Type | Amount | Description |\n")
            f.write("|------|------|--------|-------------|\n")

def log_transaction(t_type: str, amount: float, description: str):
    """Log a transaction to the accounting file."""
    ensure_file_exists()
    date_str = datetime.now().strftime("%Y-%m-%d")
    entry = f"| {date_str} | {t_type.capitalize()} | ${amount:.2f} | {description} |\n"
    
    with open(ACCOUNTING_FILE, "a") as f:
        f.write(entry)
    print(f"Logged {t_type}: ${amount:.2f} - {description}")

def parse_transactions() -> List[Dict]:
    """Parse the Markdown table into a list of dictionaries."""
    if not os.path.exists(ACCOUNTING_FILE):
        return []
        
    transactions = []
    with open(ACCOUNTING_FILE, "r") as f:
        lines = f.readlines()
        
    for line in lines:
        if line.startswith("|") and not line.startswith("| Date") and not line.startswith("|---"):
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 4:
                try:
                    transactions.append({
                        "date": datetime.strptime(parts[0], "%Y-%m-%d"),
                        "type": parts[1].lower(),
                        "amount": float(parts[2].replace("$", "").replace(",", "")),
                        "description": parts[3]
                    })
                except (ValueError, IndexError):
                    continue
    return transactions

def generate_totals():
    """Calculate and print total income, expense, and balance."""
    transactions = parse_transactions()
    total_income = sum(t["amount"] for t in transactions if t["type"] == "income")
    total_expense = sum(t["amount"] for t in transactions if t["type"] == "expense")
    balance = total_income - total_expense
    
    print(f"--- Monthly Totals ---")
    print(f"Total Income   : ${total_income:.2f}")
    print(f"Total Expense  : ${total_expense:.2f}")
    print(f"Net Balance    : ${balance:.2f}")

def generate_weekly_summary():
    """Generate a summary for the last 7 days."""
    transactions = parse_transactions()
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent = [t for t in transactions if t["date"] >= seven_days_ago]
    
    weekly_income = sum(t["amount"] for t in recent if t["type"] == "income")
    weekly_expense = sum(t["amount"] for t in recent if t["type"] == "expense")
    
    print(f"--- Weekly Summary (Last 7 Days) ---")
    print(f"Weekly Income  : ${weekly_income:.2f}")
    print(f"Weekly Expense : ${weekly_expense:.2f}")
    print(f"Count          : {len(recent)} transactions")

def main():
    parser = argparse.ArgumentParser(description="Accounting Manager Script")
    subparsers = parser.add_subparsers(dest="command")
    
    # Log command
    log_parser = subparsers.add_parser("log")
    log_parser.add_argument("type", choices=["income", "expense"])
    log_parser.add_argument("amount", type=float)
    log_parser.add_argument("description", nargs="+")
    
    # Summary command
    subparsers.add_parser("summary")
    
    # Totals command
    subparsers.add_parser("totals")
    
    args = parser.parse_args()
    
    if args.command == "log":
        log_transaction(args.type, args.amount, " ".join(args.description))
    elif args.command == "summary":
        generate_weekly_summary()
    elif args.command == "totals":
        generate_totals()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
