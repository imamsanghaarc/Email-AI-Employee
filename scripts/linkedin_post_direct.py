from playwright.sync_api import sync_playwright
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def post_linkedin(content):
    """
    Posts content to LinkedIn using Playwright.
    Requires LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env.
    """
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    
    if not email or not password:
        print("Error: LINKEDIN_EMAIL or LINKEDIN_PASSWORD not set.")
        return False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        # Login
        page.goto("https://www.linkedin.com/login")
        page.fill('input[name="session_key"]', email)
        page.fill('input[name="session_password"]', password)
        page.click('button[type="submit"]')
        
        # Post
        page.wait_for_selector('.share-box-feed-entry__trigger')
        page.click('.share-box-feed-entry__trigger')
        page.wait_for_selector('.ql-editor')
        page.fill('.ql-editor', content)
        page.click('button.share-actions__primary-action')
        
        print("Successfully posted to LinkedIn.")
        browser.close()
        return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        post_linkedin(sys.argv[1])
    else:
        print("Usage: python linkedin_post_direct.py 'Your content here'")
