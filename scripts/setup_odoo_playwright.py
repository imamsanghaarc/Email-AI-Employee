<<<<<<< HEAD
from playwright.sync_api import sync_playwright
import time

def setup_odoo_database():
=======
import os
import sys

from playwright.sync_api import sync_playwright

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

REQUIRED = {
    "ODOO_DB": "database name",
    "ODOO_ADMIN_NAME": "administrator name",
    "ODOO_LOGIN": "administrator login email",
    "ODOO_PASSWORD": "administrator password",
}


def setup_odoo_database():
    missing = [
        f"  {key} ({label})" for key, label in REQUIRED.items() if not os.environ.get(key)
    ]
    if missing:
        sys.exit(
            "Missing required environment variables:\n"
            + "\n".join(missing)
            + "\n\nSet them in .env or the shell. No credentials are hardcoded."
        )

    url = os.environ.get("ODOO_URL", "http://localhost:8069")
    phone = os.environ.get("ODOO_PHONE", "")
    country = os.environ.get("ODOO_COUNTRY", "US")

>>>>>>> c57ffdb (De-risk before public release: scrub PII, remove hardcoded credential, git init)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
<<<<<<< HEAD
        
        # Navigate to Odoo
        page.goto("http://localhost:8069")
        
        # Fill in database details
        # Using the same inputs you provided
        page.fill('input[name="db"]', 'ai_business')
        page.fill('input[name="name"]', 'Imam Sanghaar')
        page.fill('input[name="login"]', 'sanghaar.ai@gmail.com')
        page.fill('input[name="password"]', 'odoo123')
        page.fill('input[name="phone"]', '1234567890')
        page.select_option('select[name="country_code"]', 'US')
        
        # Uncheck demo data if visible (using simple selector)
        if page.is_checked('input[name="demo"]'):
            page.uncheck('input[name="demo"]')
            
        # Submit
        page.click('button[type="submit"]')
        
        # Wait for the dashboard to load (look for the "Apps" menu or similar)
        # This is a heuristic - we wait for the page to navigate away from the setup page
        page.wait_for_load_state('networkidle')
        
        print("Database creation process initiated.")
        time.sleep(10) # Give it time to process
        
        browser.close()

if __name__ == "__main__":
    setup_odoo_database()
=======

        # Navigate to Odoo
        page.goto(url)

        # Fill in database details
        page.fill('input[name="db"]', os.environ["ODOO_DB"])
        page.fill('input[name="name"]', os.environ["ODOO_ADMIN_NAME"])
        page.fill('input[name="login"]', os.environ["ODOO_LOGIN"])
        page.fill('input[name="password"]', os.environ["ODOO_PASSWORD"])
        page.fill('input[name="phone"]', phone)
        page.select_option('select[name="country_code"]', country)

        # Uncheck demo data if visible (using simple selector)
        if page.is_checked('input[name="demo"]'):
            page.uncheck('input[name="demo"]')

        # Submit
        page.click('button[type="submit"]')

        # Wait for the dashboard to load (look for the "Apps" menu or similar)
        # This is a heuristic - we wait for the page to navigate away from the setup page
        page.wait_for_load_state("networkidle")

        print("Database creation process initiated.")
        import time

        time.sleep(10)  # Give it time to process

        browser.close()


if __name__ == "__main__":
    setup_odoo_database()
>>>>>>> c57ffdb (De-risk before public release: scrub PII, remove hardcoded credential, git init)
