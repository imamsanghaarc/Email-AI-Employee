import asyncio
from playwright.async_api import async_playwright
import os
import sys
import subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
TWITTER_USER = os.environ.get("TWITTER_USER")
TWITTER_PASSWORD = os.environ.get("TWITTER_PASSWORD")

async def post_twitter(content):
    """Posts a tweet to Twitter/X with full login and publishing flow."""
    if not TWITTER_USER or not TWITTER_PASSWORD:
        print("[FAIL] Twitter credentials missing in environment.")
        return False

    async with async_playwright() as p:
        print(f"[*] Launching Browser for Twitter/X...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        page.set_default_timeout(60000)

        # Stealth scripts
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            # 1. Navigate to Twitter
            print("[*] Navigating to Twitter/X...")
            await page.goto("https://twitter.com/login", wait_until="domcontentloaded", timeout=30000)

            # 2. Login flow
            print("[*] Logging into Twitter/X...")
            
            # Wait for username field
            await page.wait_for_selector("input[autocomplete='username'], input[name='text']", timeout=30000)
            
            # Try username selector
            username_selectors = [
                "input[autocomplete='username']",
                "input[name='text']",
                "input[role='textbox']"
            ]
            
            username_filled = False
            for selector in username_selectors:
                try:
                    username_field = await page.wait_for_selector(selector, timeout=5000)
                    if username_field:
                        await username_field.fill(TWITTER_USER)
                        await page.keyboard.press("Enter")
                        username_filled = True
                        print("[OK] Username entered.")
                        await asyncio.sleep(3)
                        break
                except:
                    continue

            if not username_filled:
                print("[FAIL] Could not find username field.")
                await page.screenshot(path="logs/twitter_username_fail.png")
                await browser.close()
                return False

            # Wait for password field
            await page.wait_for_selector("input[name='password'], input[type='password']", timeout=30000)
            password_selectors = [
                "input[name='password']",
                "input[type='password']"
            ]
            
            for selector in password_selectors:
                try:
                    password_field = await page.wait_for_selector(selector, timeout=5000)
                    if password_field:
                        await password_field.fill(TWITTER_PASSWORD)
                        await page.keyboard.press("Enter")
                        print("[OK] Password entered.")
                        break
                except:
                    continue

            # Wait for home page to load
            try:
                await page.wait_for_url("**/home**", timeout=60000)
                print("[OK] Logged into Twitter/X.")
            except:
                # Check for verification/challenge
                if "challenge" in page.url or "verify" in page.url:
                    print("[FAIL] Verification challenge detected. Please complete manually.")
                    await asyncio.sleep(60)
                    await browser.close()
                    return False
                print("[WARN] Login may have failed. Continuing anyway...")

            await asyncio.sleep(3)

            # 3. Compose tweet
            print("[*] Opening tweet composer...")
            
            # Try to click "Tweet" or "Post" button
            tweet_button_selectors = [
                "[data-testid='SideNav_NewTweet_Button']",
                "a[href='/compose/post']",
                "button:has-text('Post')",
                "button:has-text('Tweet')",
                "[aria-label='Tweet']"
            ]
            
            composer_opened = False
            for selector in tweet_button_selectors:
                try:
                    tweet_btn = await page.wait_for_selector(selector, timeout=10000)
                    if tweet_btn:
                        await tweet_btn.click()
                        print("[OK] Tweet composer opened.")
                        await asyncio.sleep(3)
                        composer_opened = True
                        break
                except:
                    continue

            if not composer_opened:
                # Try direct navigation to compose
                print("[*] Tweet button not found, navigating to compose URL...")
                await page.goto("https://twitter.com/compose/post", wait_until="domcontentloaded")
                await asyncio.sleep(5)
                composer_opened = True

            # 4. Enter tweet content
            print(f"[*] Entering tweet content: {content[:50]}...")
            
            tweet_editor_selectors = [
                "[role='textbox'][aria-label='Tweet text']",
                "[role='textbox'][data-testid='tweetTextarea_0']",
                "div[contenteditable='true']",
                "[role='textbox']",
                "div.public-DraftEditor-content"
            ]
            
            content_filled = False
            for selector in tweet_editor_selectors:
                try:
                    editor = await page.wait_for_selector(selector, timeout=10000)
                    if editor:
                        # Twitter uses contenteditable divs
                        await editor.click()
                        await page.keyboard.type(content, delay=50)
                        print("[OK] Tweet content entered.")
                        content_filled = True
                        await asyncio.sleep(2)
                        break
                except:
                    continue

            if not content_filled:
                print("[FAIL] Could not find tweet editor. Taking screenshot...")
                await page.screenshot(path="logs/twitter_editor_fail.png")
                await browser.close()
                return False

            # 5. Publish tweet
            print("[*] Publishing tweet...")
            
            post_button_selectors = [
                "[data-testid='tweetButton']",
                "[data-testid='tweetButtonInline']",
                "button:has-text('Post')",
                "button:has-text('Tweet')",
                "[aria-label='Post']"
            ]
            
            tweet_published = False
            for selector in post_button_selectors:
                try:
                    post_btn = await page.wait_for_selector(selector, timeout=10000)
                    if post_btn and await post_btn.is_enabled():
                        await post_btn.click()
                        print("[OK] Tweet published!")
                        tweet_published = True
                        await asyncio.sleep(5)
                        break
                except:
                    continue

            if not tweet_published:
                print("[FAIL] Could not publish tweet. Taking screenshot...")
                await page.screenshot(path="logs/twitter_publish_fail.png")

            # Log to Social Summary
            log_to_social_summary("twitter", content)

            await asyncio.sleep(5)
            await browser.close()
            return True

        except Exception as e:
            print(f"[FAIL] Twitter Error: {e}")
            try:
                await page.screenshot(path="logs/twitter_error.png")
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
    content = sys.argv[1] if len(sys.argv) > 1 else "Automated tweet from AI Employee - Testing autonomous posting"
    asyncio.run(post_twitter(content))
