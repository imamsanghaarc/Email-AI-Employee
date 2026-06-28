# LinkedIn Posting Strategy & Automation

This document outlines the strategy and code for automating LinkedIn posts as part of the AI Employee workflow.

## Strategy: Direct Playwright vs. MCP Server

During development, we explored two main approaches for automating LinkedIn:

1.  **Playwright MCP Server (`@playwright/mcp`)**: An abstraction layer that allows LLMs to use browser tools. While powerful, it encountered issues with LinkedIn's slow loading times and anti-bot measures when running in "shared browser context".
2.  **Direct Playwright Script (`linkedin_post_direct.py`)**: A standalone Python script using `playwright-python`. This proved more robust as it allowed for:
    *   **Custom Stealth Measures**: Overriding `navigator.webdriver` to evade basic bot detection.
    *   **Specific Error Handling**: Retrying selectors and handling LinkedIn's dynamic UI.
    *   **Visibility**: Running in non-headless mode (`headless: false`) using `DISPLAY=:0`, allowing for real-time monitoring and manual intervention if needed (e.g., security checkpoints).

## Key Files
- `linkedin_post_direct.py`: The primary, robust script for direct LinkedIn posting.
- `linkedin_post_mcp.py`: The MCP-based implementation (requires an active MCP server).
- `watcher.py`: A watchdog script that monitors for new files in the inbox and triggers tasks.

## Implementation Details

### 1. Stealth & Robustness
LinkedIn is highly sensitive to automation. We implemented:
-   **User-Agent Spoofer**: Emulating a modern Chrome browser on Windows.
-   **Stealth Script**: `Object.defineProperty(navigator, 'webdriver', {get: () => undefined})`.
-   **Wait Strategies**: Using `domcontentloaded` and specific `asyncio.sleep` to allow the feed to settle before looking for the post button.

### 2. Post Workflow
1.  **Launch Browser**: Non-headless to allow user to see the post happening.
2.  **Login**: Uses credentials from `.env`. Checks if already logged in by looking for the feed URL.
3.  **Open Post Dialog**: Uses multiple selector strategies (button text, class, aria-label) and direct URL navigation (`/?share=true`) as a fallback.
4.  **Type & Publish**: Finds the `.ql-editor` and clicks the primary publish button.

## Usage
To run a direct post:
```bash
DISPLAY=:0 python3 linkedin_post_direct.py "Your post content here"
```

## Watchdog Integration
The `watcher.py` (or `scripts/watch_inbox.py`) script runs in the background to monitor the `AI_Employee_Vault/Inbox`. When a new task is detected, it's moved to `Needs_Action` for processing.
