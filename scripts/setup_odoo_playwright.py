from playwright.sync_api import sync_playwright
import time

def setup_odoo_database():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
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
