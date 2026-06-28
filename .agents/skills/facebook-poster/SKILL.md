---
name: facebook-poster
description: Automatically post content to Facebook using Playwright browser automation. Use when business updates need to be published on Facebook.
---

# Facebook Poster

This skill automates the process of publishing posts to a Facebook profile or page.

## 🚀 Workflows

### 1. Publish Post
Call the script with the content you wish to post.

```bash
python .agents/skills/facebook-poster/scripts/facebook_post.py "Your post content here"
```

## 🛠️ Configuration
Ensure the following environment variables are set:
- `FB_EMAIL`: Your Facebook login email.
- `FB_PASSWORD`: Your Facebook login password.

## 📋 Best Practices
- Keep posts engaging and platform-appropriate.
- Use `social-summary` after each successful post to maintain the audit trail.
