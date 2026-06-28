---
name: accounting-manager
description: Manage business finances by logging income/expenses, generating weekly summaries, and calculating monthly totals in the Obsidian vault. Use when tracking business transactions or requesting financial reports.
---

# Accounting Manager

This skill manages business accounting records within the AI Employee Vault.

## Core File
Records are maintained in: `AI_Employee_Vault/Accounting/Current_Month.md`

## 🚀 Workflows

### 1. Log Transaction
Use the `scripts/accounting_manager.py log` command to record new income or expenses.

```bash
python scripts/accounting_manager.py log [income|expense] [amount] [description]
```

### 2. Get Financial Status
Retrieve monthly totals (Total Income, Total Expense, Net Balance) using the `totals` command.

```bash
python scripts/accounting_manager.py totals
```

### 3. Weekly Summary
Generate a summary for the last 7 days of activity.

```bash
python scripts/accounting_manager.py summary
```

## 📋 Table Format
The script maintains a Markdown table with the following columns:
| Date | Type | Amount | Description |

## 💡 Usage Guidelines
- Always include a concise but descriptive reason for the transaction.
- When the user mentions a financial transaction, use this skill immediately to log it.
- Proactively offer a `totals` or `summary` report at the end of the week or month.
