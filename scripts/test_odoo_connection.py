import os
from dotenv import load_dotenv
import requests

# Load from .env
load_dotenv()

# For Odoo Online, ensure URL starts with https://
ODOO_URL = os.getenv("ODOO_URL", "").strip()
if ODOO_URL and not ODOO_URL.startswith("http"):
    ODOO_URL = f"https://{ODOO_URL}"

ODOO_DB = os.getenv("ODOO_DB")
ODOO_USER = os.getenv("ODOO_USER")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")

def test_connection():
    print(f"[*] Testing Odoo Online Connection to {ODOO_URL}...")
    print(f"[*] DB: {ODOO_DB} | User: {ODOO_USER}")
    
    # Odoo Online uses the same JSON-RPC endpoint
    endpoint = f"{ODOO_URL}/jsonrpc"
    
    data = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "service": "common",
            "method": "authenticate",
            "args": [ODOO_DB, ODOO_USER, ODOO_PASSWORD, {}]
        },
        "id": 1,
    }
    
    try:
        # Verify=True is default for SSL check
        response = requests.post(endpoint, json=data, timeout=15)
        result = response.json()
        
        uid = result.get("result")
        if uid:
            print(f"✅ SUCCESS: Connected to Odoo Online! User ID: {uid}")
            return True
        else:
            print(f"❌ FAILED: Authentication failed. Check your API Key and DB name.")
            print(f"Debug: {result}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Connection failed. Are you sure the URL is correct?")
        print(f"Error details: {e}")
        return False

if __name__ == "__main__":
    if not ODOO_URL or not ODOO_DB or not ODOO_USER or not ODOO_PASSWORD:
        print("❌ ERROR: Missing credentials in .env file.")
    else:
        test_connection()
