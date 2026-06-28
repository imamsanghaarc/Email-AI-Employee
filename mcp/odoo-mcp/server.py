import os
import json
import requests
from typing import Any, Dict, List, Optional, Union
from mcp.server.fastmcp import FastMCP

# --- CONFIGURATION ---
mcp = FastMCP("odoo-mcp")

# Environment variables for Odoo credentials
ODOO_URL = os.environ.get("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.environ.get("ODOO_DB")
ODOO_USER = os.environ.get("ODOO_USER")
ODOO_PASSWORD = os.environ.get("ODOO_PASSWORD")

def json_rpc(url, method, params):
    data = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1,
    }
    try:
        response = requests.post(
            f"{url}/jsonrpc",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def call_odoo(model, method, *args, **kwargs):
    # First, authenticate to get UID
    common = f"{ODOO_URL}/xmlrpc/2/common"
    auth_params = [ODOO_DB, ODOO_USER, ODOO_PASSWORD, {}]
    
    # Use JSON-RPC to authenticate
    auth_resp = json_rpc(ODOO_URL, "call", {
        "service": "common",
        "method": "authenticate",
        "args": [ODOO_DB, ODOO_USER, ODOO_PASSWORD, {}]
    })
    
    uid = auth_resp.get("result")
    if not uid:
        return {"error": "Authentication failed", "details": auth_resp}

    # Call the model method
    result = json_rpc(ODOO_URL, "call", {
        "service": "object",
        "method": "execute_kw",
        "args": [ODOO_DB, uid, ODOO_PASSWORD, model, method, args, kwargs]
    })
    return result

@mcp.tool()
def search_read(model: str, domain: List[List[Any]] = [], fields: List[str] = [], limit: int = 10) -> str:
    """
    Search and read records from any Odoo model.
    Args:
        model: Odoo model name (e.g., 'account.move', 'res.partner').
        domain: Search filter (e.g., [['state', '=', 'posted']]).
        fields: List of fields to return.
        limit: Max number of records.
    """
    res = call_odoo(model, "search_read", domain, fields=fields, limit=limit)
    if "error" in res:
        return f"Error: {res['error']}"
    return json.dumps(res.get("result", []), indent=2)

@mcp.tool()
def create_record(model: str, values: Dict[str, Any]) -> str:
    """
    Create a new record in Odoo.
    Args:
        model: Odoo model name.
        values: Dictionary of field values.
    """
    res = call_odoo(model, "create", values)
    if "error" in res:
        return f"Error: {res['error']}"
    return f"Successfully created {model} with ID: {res.get('result')}"

@mcp.tool()
def update_record(model: str, record_id: int, values: Dict[str, Any]) -> str:
    """
    Update an existing record in Odoo.
    Args:
        model: Odoo model name.
        record_id: ID of the record to update.
        values: Dictionary of field values to update.
    """
    res = call_odoo(model, "write", [record_id], values)
    if "error" in res:
        return f"Error: {res['error']}"
    return f"Successfully updated {model} ID: {record_id}"

@mcp.tool()
def get_accounting_summary() -> str:
    """
    Get a summary of recent accounting moves (Income/Expense).
    """
    # Search for posted journal entries
    domain = [('state', '=', 'posted'), ('move_type', 'in', ['out_invoice', 'in_invoice'])]
    fields = ['name', 'date', 'amount_total', 'move_type', 'payment_state']
    res = call_odoo("account.move", "search_read", domain, fields=fields, limit=20)
    
    if "error" in res:
        return f"Error fetching accounting summary: {res['error']}"
    
    moves = res.get("result", [])
    if not moves:
        return "No recent accounting moves found."
        
    summary = "# Odoo Accounting Summary\n\n"
    summary += "| Date | Name | Type | Amount | Status |\n"
    summary += "|------|------|------|--------|--------|\n"
    for move in moves:
        m_type = "Income" if move['move_type'] == 'out_invoice' else "Expense"
        summary += f"| {move['date']} | {move['name']} | {m_type} | ${move['amount_total']:.2f} | {move['payment_state']} |\n"
        
    return summary

if __name__ == "__main__":
    mcp.run()
