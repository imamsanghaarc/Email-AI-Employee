# LinkedIn Poster Skill

## Overview
Automates posting content to LinkedIn using Playwright browser automation.

## Usage
`python scripts/linkedin_poster.py "Your post content"`

## Post-Posting
After posting, the skill should call the social-summary script to log the activity:
`python .agents/skills/social-summary/scripts/social_summary.py linkedin "Your post content"`

## Configuration
Requires `LINKEDIN_EMAIL` and `LINKEDIN_PASSWORD` in your `.env` file.

## Dependencies
- playwright
- python-dotenv
