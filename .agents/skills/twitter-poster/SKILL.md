---
name: twitter-poster
description: Automatically post content to Twitter (X) using Playwright browser automation. Use when business updates need to be published on Twitter.
---

# Twitter (X) Poster

This skill automates the process of publishing posts to a Twitter (X) account.

## 🚀 Workflows

### 1. Publish Tweet
Call the script with the content you wish to tweet.

```bash
python .agents/skills/twitter-poster/scripts/twitter_post.py "Your tweet here"
```

## 🛠️ Configuration
Ensure the following environment variables are set:
- `TWITTER_USER`: Your Twitter username.
- `TWITTER_PASSWORD`: Your Twitter password.

## 📋 Best Practices
- Keep tweets concise and use relevant hashtags.
- Use `social-summary` after each successful tweet to maintain the audit trail.
