import asyncio
from playwright.async_api import async_playwright
import os
import sys
import subprocess
from datetime import datetime

# --- CONFIGURATION ---
FB_EMAIL = os.environ.get("FB_EMAIL")
FB_PASSWORD = os.environ.get("FB_PASSWORD")

async def post_facebook(content):
    if not FB_EMAIL or not FB_PASSWORD:
        print("[FAIL] Facebook credentials missing.")
        return False

    async with async_playwright() as p:
        print(f"[*] Launching Facebook Browser...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        page.set_default_timeout(60000)
        
        try:
            await page.goto("https://www.facebook.com/")
            
            # Login Logic
            if await page.query_selector("#email"):
                await page.fill("#email", FB_EMAIL)
                await page.fill("#pass", FB_PASSWORD)
                await page.click("button[name='login']")
                await page.wait_for_url("https://www.facebook.com/**")
                print("[OK] Logged into Facebook.")

            # Open Create Post (Simulating the click on 'What's on your mind?')
            await page.wait_for_selector("text=What's on your mind?")
            await page.click("text=What's on your mind?")
            
            # Type and Post
            await page.wait_for_selector("div[role='textbox']")
            await page.fill("div[role='textbox']", content)
            await page.click("div[aria-label='Post']")
            
            print(" Facebook post published!")
            
            # Log to Social Summary
            summary_script = "scripts/social_summary.py"
            if os.path.exists(summary_script):
                subprocess.run(["python3", summary_script, "log", "facebook", content], capture_output=True)
            
            await asyncio.sleep(5)
            await browser.close()
            return True
        except Exception as e:
            print(f"[FAIL] Facebook Error: {e}")
            await browser.close()
            return False

if __name__ == "__main__":
    content = sys.argv[1] if len(sys.argv) > 1 else "Automated Facebook Post"
    asyncio.run(post_facebook(content))
