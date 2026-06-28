# 🧠 Lessons Learned: AI Employee Development

## 1. Vault-Based Memory is Superior
Using an Obsidian vault as the "brain" allows for transparency. Humans can see exactly what the AI is planning and what it has completed without checking complex databases.

## 2. Browser Automation vs. APIs
While APIs (like Odoo JSON-RPC) are faster, **Browser Automation (Playwright)** is more flexible for social media. It bypasses the need for expensive "Developer Accounts" and handles UI-based workflows that APIs often restrict.

## 3. The Need for "Small Steps"
Autonomous loops (like Ralph Wiggum) succeed when tasks are broken down into tiny, verifiable steps. Large, vague steps often lead to "looping" or execution failure.

## 4. Safety First
Implementing a `MAX_ITERATIONS` limit and a mandatory `risky_keywords` check for human approval is essential. Without these, an autonomous AI can quickly spiral out of control (e.g., sending too many emails).

## 5. Standardized Logging
Centralized logs (like `Social_Logs.md` and `business.log`) are vital for generating strategic reports (CEO Briefing). Without standardized output, the AI cannot audit its own performance.

## 6. LLM Integration via Environment Variables
LLM reasoning (like Task Planner) is most effective when API keys are loaded from environment variables (`.env` file). This allows for flexible credential management and separation of concerns.

## 7. Iterative Development and Testing
The process of testing and fixing bugs (like the double `.md` extension or API key loading) highlights the importance of iterative development and clear error messages.

## 8. Skill Modularity
Breaking down functionality into distinct Agent Skills (e.g., `accounting-manager`, `error-recovery`, `social-summary`) makes the system maintainable and extensible. Each skill has a clear purpose and can be updated independently.
