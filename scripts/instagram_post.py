import asyncio
from playwright.async_api import async_playwright
import os
import sys
import subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
INSTA_USER = os.environ.get("INSTA_USER")
INSTA_PASSWORD = os.environ.get("INSTA_PASSWORD")

async def post_instagram(content):
    """Posts content to Instagram with text caption.
    Note: Instagram web posting requires an image. This script uses a 
    placeholder approach - for production, replace with actual image upload."""
    if not INSTA_USER or not INSTA_PASSWORD:
        print("[FAIL] Instagram credentials missing in environment.")
        return False

    async with async_playwright() as p:
        print(f"[*] Launching Browser for Instagram...")
        # Use mobile emulation - Instagram web posting works best on mobile view
        device = p.devices['iPhone 12']
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(**device)
        page = await context.new_page()
        page.set_default_timeout(60000)

        try:
            # 1. Login
            print("[*] Logging into Instagram...")
            await page.goto("https://www.instagram.com/accounts/login/")
            await page.wait_for_selector("input[name='username']", timeout=30000)
            await page.fill("input[name='username']", INSTA_USER)
            await page.fill("input[name='password']", INSTA_PASSWORD)
            await page.click("button[type='submit']")

            # Wait for successful login
            await page.wait_for_url("**/instagram.com/**", timeout=60000)
            # Handle "Save info" prompt if appears
            try:
                not_now_btn = await page.wait_for_selector("button:has-text('Not now'), button:has-text('Not Now')", timeout=5000)
                if not_now_btn:
                    await not_now_btn.click()
                    await asyncio.sleep(2)
            except:
                pass  # Prompt didn't appear, continue

            print("[OK] Logged into Instagram.")

            # 2. Navigate to create post
            print("[*] Opening Instagram post creator...")
            # Method 1: Click the + button in the navbar
            try:
                # Try the new Instagram UI create button
                create_btn = await page.wait_for_selector(
                    "svg[aria-label='Create'], a[href*='create'], button:has-text('Create'), [role='menuitem']:has-text('Create')",
                    timeout=10000
                )
                if create_btn:
                    await create_btn.click()
                    await asyncio.sleep(3)
            except:
                # Method 2: Direct navigation to create URL
                print("[*] Create button not found, trying direct URL...")
                await page.goto("https://www.instagram.com/create/details/")
                await asyncio.sleep(5)

            # 3. Handle the create post flow
            # Instagram web requires image upload first, then caption
            # For now, we'll fill the caption if the editor is available
            
            print(f"[*] Adding caption: {content[:50]}...")
            
            # Try to find caption textarea/input
            caption_selectors = [
                "textarea[aria-label='Write a caption...']",
                "textarea",
                "div[role='textbox']",
                "input[placeholder*='caption' i]",
                "input[placeholder*='Caption' i]"
            ]

            caption_filled = False
            for selector in caption_selectors:
                try:
                    caption_el = await page.wait_for_selector(selector, timeout=5000)
                    if caption_el:
                        await caption_el.fill(content)
                        print("[OK] Caption filled.")
                        caption_filled = True
                        break
                except:
                    continue

            if not caption_filled:
                print("[WARN] Could not find caption field. Instagram UI may have changed.")
                # Take screenshot for debugging
                await page.screenshot(path="logs/instagram_caption_fail.png")

            # 4. Look for Share/Post button
            print("[*] Looking for Share button...")
            share_selectors = [
                "button:has-text('Share')",
                "button:has-text('Post')",
                "div[role='button']:has-text('Share')",
                "button[type='submit']"
            ]

            share_clicked = False
            for selector in share_selectors:
                try:
                    share_btn = await page.wait_for_selector(selector, timeout=5000)
                    if share_btn and await share_btn.is_enabled():
                        await share_btn.click()
                        print("[OK] Share button clicked!")
                        share_clicked = True
                        await asyncio.sleep(5)
                        break
                except:
                    continue

            if not share_clicked:
                print("[WARN] Could not find Share button. Instagram UI may have changed.")
                await page.screenshot(path="logs/instagram_share_fail.png")

            # Log to Social Summary
            log_to_social_summary("instagram", content)

            await asyncio.sleep(5)
            await browser.close()
            return True

        except Exception as e:
            print(f"[FAIL] Instagram Error: {e}")
            try:
                await page.screenshot(path="logs/instagram_error.png")
            except:
                pass
            await browser.close()
            return False

def log_to_social_summary(platform, content):
    """Log post to social summary file."""
    try:
        reports_dir = os.path.join("AI_Employee_Vault", "Reports")
        os.makedirs(reports_dir, exist_ok=True)
        social_log = os.path.join(reports_dir, "Social_Logs.md")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"| {platform} | {timestamp} | {content[:100]} |\n"

        if not os.path.exists(social_log):
            with open(social_log, "w") as f:
                f.write("# Social Media Logs\n\n")
                f.write("| Platform | Date | Summary |\n")
                f.write("|----------|------|--------|\n")

        with open(social_log, "a") as f:
            f.write(entry)

        print(f"📊 Logged to Social Summary.")
    except Exception as e:
        print(f"[WARN] Failed to log to social summary: {e}")

if __name__ == "__main__":
    content = sys.argv[1] if len(sys.argv) > 1 else "Automated Instagram Post from AI Employee"
    asyncio.run(post_instagram(content))
