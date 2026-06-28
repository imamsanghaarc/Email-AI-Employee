"""
Odoo Manager Skill - Full Odoo JSON-RPC client for accounting, CRM, and ERP operations.
Supports Odoo 19+ via JSON-RPC 2.0 API and legacy XML-RPC.
"""
import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuration
ODOO_URL = os.getenv("ODOO_URL", "https://demo.odoo.com")
ODOO_DB = os.getenv("ODOO_DB", "odoo")
ODOO_USER = os.getenv("ODOO_USER", "")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "")
ODOO_API_VERSION = os.getenv("ODOO_API_VERSION", "json-rpc")  # json-rpc or json-2


class OdooClient:
    """Odoo JSON-RPC client for business operations."""

    def __init__(self):
        self.uid = None
        self._authenticate()

    def _jsonrpc_request(self, endpoint, method, params):
        """Make a JSON-RPC 2.0 request to Odoo."""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            endpoint,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                if "error" in result:
                    raise Exception(f"Odoo JSON-RPC Error: {result['error']}")
                return result.get("result")
        except urllib.error.URLError as e:
            raise Exception(f"Connection error: {e}")

    def _authenticate(self):
        """Authenticate with Odoo and get user ID."""
        if not ODOO_USER or not ODOO_PASSWORD:
            print("Warning: ODOO_USER or ODOO_PASSWORD not set. Running in offline mode.")
            self.uid = None
            return

        endpoint = f"{ODOO_URL}/jsonrpc"
        params = {
            "db": ODOO_DB,
            "login": ODOO_USER,
            "password": ODOO_PASSWORD
        }
        try:
            self.uid = self._jsonrpc_request(endpoint, "call", {
                "service": "common",
                "method": "login",
                "args": params
            })
            if isinstance(self.uid, dict) and "uid" in self.uid:
                self.uid = self.uid["uid"]
            print(f"Authenticated with Odoo. User ID: {self.uid}")
        except Exception as e:
            print(f"Odoo authentication failed: {e}")
            self.uid = None

    def execute(self, model, method, *args, **kwargs):
        """Execute a method on an Odoo model."""
        if not self.uid:
            return {"error": "Not authenticated with Odoo"}

        endpoint = f"{ODOO_URL}/jsonrpc"
        params = {
            "service": "object",
            "method": "execute",
            "args": [ODOO_DB, self.uid, ODOO_PASSWORD, model, method] + list(args)
        }
        if kwargs:
            params["args"].append(kwargs)

        return self._jsonrpc_request(endpoint, "call", params)

    def search_read(self, model, domain=None, fields=None, limit=100, offset=0):
        """Search and read records from a model."""
        if not self.uid:
            return {"error": "Not authenticated with Odoo"}

        endpoint = f"{ODOO_URL}/jsonrpc"
        params = {
            "service": "object",
            "method": "execute_kw",
            "args": [
                ODOO_DB, self.uid, ODOO_PASSWORD,
                model, "search_read",
                [domain or []],
                {"fields": fields or [], "limit": limit, "offset": offset}
            ]
        }
        return self._jsonrpc_request(endpoint, "call", params)

    def create_record(self, model, values):
        """Create a new record."""
        if not self.uid:
            return {"error": "Not authenticated with Odoo"}

        endpoint = f"{ODOO_URL}/jsonrpc"
        params = {
            "service": "object",
            "method": "execute_kw",
            "args": [
                ODOO_DB, self.uid, ODOO_PASSWORD,
                model, "create",
                [values]
            ]
        }
        return self._jsonrpc_request(endpoint, "call", params)

    def get_accounting_summary(self):
        """Get a summary of recent invoices and bills."""
        if not self.uid:
            return "Odoo Status: Offline (credentials not configured)"

        try:
            invoices = self.search_read(
                "account.move",
                domain=[("move_type", "=", "out_invoice"), ("state", "=", "posted")],
                fields=["name", "invoice_date", "amount_total", "amount_residual", "state"],
                limit=10
            )
            bills = self.search_read(
                "account.move",
                domain=[("move_type", "=", "in_invoice"), ("state", "=", "posted")],
                fields=["name", "invoice_date", "amount_total", "amount_residual", "state"],
                limit=10
            )

            if isinstance(invoices, dict) and "error" in invoices:
                return f"Odoo Error: {invoices['error']}"

            summary = "## Odoo Accounting Summary\n\n"
            summary += "### Recent Invoices (Customer)\n"
            summary += "| Name | Date | Total | Residual | Status |\n"
            summary += "|------|------|-------|----------|--------|\n"

            if invoices and isinstance(invoices, list):
                for inv in invoices:
                    summary += f"| {inv.get('name', 'N/A')} | {inv.get('invoice_date', 'N/A')} | "
                    summary += f"{inv.get('amount_total', 0):.2f} | {inv.get('amount_residual', 0):.2f} | "
                    summary += f"{inv.get('state', 'N/A')} |\n"
            else:
                summary += "| No invoices found | - | - | - | - |\n"

            summary += "\n### Recent Bills (Vendor)\n"
            summary += "| Name | Date | Total | Residual | Status |\n"
            summary += "|------|------|-------|----------|--------|\n"

            if bills and isinstance(bills, list):
                for bill in bills:
                    summary += f"| {bill.get('name', 'N/A')} | {bill.get('invoice_date', 'N/A')} | "
                    summary += f"{bill.get('amount_total', 0):.2f} | {bill.get('amount_residual', 0):.2f} | "
                    summary += f"{bill.get('state', 'N/A')} |\n"
            else:
                summary += "| No bills found | - | - | - | - |\n"

            return summary
        except Exception as e:
            return f"Odoo Accounting Error: {str(e)}"

    def get_sales_summary(self):
        """Get summary of recent sale orders."""
        if not self.uid:
            return "Sales: Offline (credentials not configured)"

        try:
            orders = self.search_read(
                "sale.order",
                domain=[],
                fields=["name", "partner_id", "amount_total", "state", "date_order"],
                limit=10
            )

            summary = "### Recent Sales Orders\n"
            summary += "| Order | Customer | Total | Status | Date |\n"
            summary += "|-------|----------|-------|--------|------|\n"

            if orders and isinstance(orders, list):
                for order in orders:
                    partner = order.get("partner_id", [None, "Unknown"])
                    if isinstance(partner, list) and len(partner) > 1:
                        partner_name = partner[1]
                    else:
                        partner_name = str(partner)
                    summary += f"| {order.get('name', 'N/A')} | {partner_name} | "
                    summary += f"{order.get('amount_total', 0):.2f} | {order.get('state', 'N/A')} | "
                    summary += f"{order.get('date_order', 'N/A')} |\n"
            else:
                summary += "| No orders found | - | - | - | - |\n"

            return summary
        except Exception as e:
            return f"Sales Error: {str(e)}"

    def get_crm_summary(self):
        """Get summary of CRM leads."""
        if not self.uid:
            return "CRM: Offline (credentials not configured)"

        try:
            leads = self.search_read(
                "crm.lead",
                domain=[("type", "=", "opportunity")],
                fields=["name", "partner_name", "expected_revenue", "probability", "stage_id"],
                limit=10
            )

            summary = "### CRM Opportunities\n"
            summary += "| Lead | Customer | Revenue | Probability | Stage |\n"
            summary += "|------|----------|---------|-------------|-------|\n"

            if leads and isinstance(leads, list):
                for lead in leads:
                    stage = lead.get("stage_id", [None, "Unknown"])
                    if isinstance(stage, list) and len(stage) > 1:
                        stage_name = stage[1]
                    else:
                        stage_name = str(stage)
                    summary += f"| {lead.get('name', 'N/A')} | {lead.get('partner_name', 'N/A')} | "
                    summary += f"{lead.get('expected_revenue', 0):.2f} | {lead.get('probability', 0)}% | "
                    summary += f"{stage_name} |\n"
            else:
                summary += "| No opportunities found | - | - | - | - |\n"

            return summary
        except Exception as e:
            return f"CRM Error: {str(e)}"


def log_to_accounting(message):
    """Log a message to the Accounting current month file."""
    vault_dir = os.environ.get("VAULT_PATH", "AI_Employee_Vault")
    accounting_dir = os.path.join(vault_dir, "Accounting")
    os.makedirs(accounting_dir, exist_ok=True)

    current_file = os.path.join(accounting_dir, "Current_Month.md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if os.path.exists(current_file):
        with open(current_file, "r") as f:
            content = f.read()
        content += f"\n- [{timestamp}] {message}"
    else:
        content = f"""# Accounting Log - {datetime.now().strftime('%B %Y')}

## Transactions
- [{timestamp}] {message}
"""
    with open(current_file, "w") as f:
        f.write(content)


def main():
    """CLI entry point for Odoo Manager skill."""
    import argparse

    parser = argparse.ArgumentParser(description="Odoo Manager Skill - Accounting, CRM, ERP operations")
    parser.add_argument("--accounting", action="store_true", help="Get accounting summary")
    parser.add_argument("--sales", action="store_true", help="Get sales summary")
    parser.add_argument("--crm", action="store_true", help="Get CRM summary")
    parser.add_argument("--log", type=str, help="Log a transaction message")
    parser.add_argument("--search", type=str, help="Search a model (format: model:domain:fields)")
    parser.add_argument("--status", action="store_true", help="Check Odoo connection status")

    args = parser.parse_args()

    if args.status:
        client = OdooClient()
        if client.uid:
            print(f"Odoo connection: OK (User ID: {client.uid})")
        else:
            print("Odoo connection: Offline (no credentials configured)")
        return

    if not args.accounting and not args.sales and not args.crm and not args.log and not args.search:
        # Default: show all summaries
        client = OdooClient()
        print(client.get_accounting_summary())
        print()
        print(client.get_sales_summary())
        print()
        print(client.get_crm_summary())
        return

    if args.log:
        log_to_accounting(args.log)
        print(f"Logged: {args.log}")
        return

    client = OdooClient()

    if args.accounting:
        print(client.get_accounting_summary())
    if args.sales:
        print(client.get_sales_summary())
    if args.crm:
        print(client.get_crm_summary())
    if args.search:
        parts = args.search.split(":")
        model = parts[0]
        domain = json.loads(parts[1]) if len(parts) > 1 and parts[1] else []
        fields = parts[2].split(",") if len(parts) > 2 else []
        result = client.search_read(model, domain=domain, fields=fields)
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
