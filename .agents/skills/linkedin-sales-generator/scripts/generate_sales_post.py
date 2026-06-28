"""
LinkedIn Sales Content Generator - Automatically generates and posts sales-focused LinkedIn content.
Uses LLM (OpenAI/Anthropic/Gemini) or template-based generation for business development posts.
"""
import os
import sys
import json
import random
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

# Business Context
COMPANY_NAME = os.getenv("COMPANY_NAME", "Our Company")
BUSINESS_DESCRIPTION = os.getenv("BUSINESS_DESCRIPTION", "We provide innovative business solutions")
TARGET_AUDIENCE = os.getenv("TARGET_AUDIENCE", "business owners and decision makers")
KEY_SERVICES = os.getenv("KEY_SERVICES", "consulting, automation, AI integration").split(",")
CALL_TO_ACTION = os.getenv("CALL_TO_ACTION", "Contact us for a free consultation")

# Content Templates (fallback when no LLM available)
SALES_TEMPLATES = [
    {
        "category": "problem_awareness",
        "template": (
            "🚨 Are you still manually handling {pain_point}?\n\n"
            "Most {audience} waste 10+ hours/week on tasks that could be automated.\n\n"
            "At {company}, we've helped businesses:\n"
            "✅ Reduce operational costs by 40%\n"
            "✅ Save 15+ hours per week\n"
            "✅ Scale without hiring\n\n"
            "Ready to work smarter? {cta}\n\n"
            "#BusinessAutomation #Efficiency #Growth #{company}"
        )
    },
    {
        "category": "case_study",
        "template": (
            "📊 Client Success Story:\n\n"
            "A {industry} client came to us struggling with {challenge}.\n\n"
            "After implementing our {service} solution:\n"
            "📈 Revenue increased by 35%\n"
            "⏱️ Processing time cut by 60%\n"
            "💰 ROI achieved in just 60 days\n\n"
            "Want similar results? {cta}\n\n"
            "#CaseStudy #Results #BusinessGrowth #{company}"
        )
    },
    {
        "category": "tip_series",
        "template": (
            "💡 Quick Tip #{tip_number} for {audience}:\n\n"
            "{tip_content}\n\n"
            "This is just one of the strategies we implement for our clients.\n"
            "Want the full playbook? {cta}\n\n"
            "#BusinessTips #Strategy #Success #{company}"
        )
    },
    {
        "category": "direct_offer",
        "template": (
            "🎯 Limited Availability: {offer}\n\n"
            "We're opening {spots} spots for our {service} program this month.\n\n"
            "What's included:\n"
            "{included_items}\n\n"
            "Don't miss out. {cta}\n\n"
            "#Offer #Business #Opportunity #{company}"
        )
    },
    {
        "category": "thought_leadership",
        "template": (
            "🔮 The future of {industry} is here.\n\n"
            "Companies that adopt {technology} early will have a massive advantage.\n\n"
            "Here's what we're seeing at {company}:\n"
            "{insights}\n\n"
            "The question isn't IF you should adapt — it's WHEN.\n\n"
            "Let's discuss your strategy. {cta}\n\n"
            "#Innovation #FutureOfBusiness #{company}"
        )
    },
    {
        "category": "social_proof",
        "template": (
            "⭐ \"Best investment we made this year.\" - Our Client\n\n"
            "We're proud to have helped {number} businesses transform their operations.\n\n"
            "Our expertise in {services} delivers measurable results:\n"
            "✅ Faster processes\n"
            "✅ Lower costs\n"
            "✅ Happier teams\n\n"
            "Join them. {cta}\n\n"
            "#Testimonials #Trusted #Results #{company}"
        )
    }
]

BUSINESS_TIPS = [
    "Automate your lead follow-up. 78% of buyers go with the first responder.",
    "Use data dashboards to make decisions 5x faster than competitors.",
    "Implement AI-powered customer service to reduce response time by 80%.",
    "Create standardized processes before scaling — chaos doesn't scale.",
    "Track customer acquisition cost. If you don't measure it, you can't improve it.",
    "Build systems that work without you. That's the difference between a job and a business.",
    "Your CRM is only as good as the data you put in. Automate data collection.",
    "The best time to automate was yesterday. The second best time is today.",
    "Stop trading time for money. Productize your services.",
    "Document everything. Your future team will thank you."
]

INDUSTRY_CHALLENGES = {
    "retail": "inventory management and customer retention",
    "healthcare": "patient scheduling and compliance",
    "finance": "regulatory reporting and client onboarding",
    "manufacturing": "supply chain optimization and quality control",
    "technology": "rapid scaling and talent retention",
    "real_estate": "lead management and deal tracking",
    "education": "student engagement and administrative efficiency",
    "hospitality": "booking management and customer experience"
}


def generate_with_openai(topic, category="sales"):
    """Generate LinkedIn post content using OpenAI."""
    if not OPENAI_API_KEY:
        return None

    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)

        prompt = f"""Write a compelling LinkedIn post for {COMPANY_NAME} ({BUSINESS_DESCRIPTION}).

Category: {category}
Topic: {topic}
Target Audience: {TARGET_AUDIENCE}
Key Services: {', '.join(KEY_SERVICES)}
Call to Action: {CALL_TO_ACTION}

Requirements:
- Start with an attention-grabbing hook
- Use emojis strategically
- Include specific numbers/statistics
- Have a clear call to action
- End with 3-5 relevant hashtags
- Keep it under 300 words
- Make it conversational and authentic
- Focus on generating business leads"""

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional LinkedIn content strategist specializing in B2B sales and lead generation posts."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.8
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI generation error: {e}")
        return None


def generate_with_anthropic(topic, category="sales"):
    """Generate LinkedIn post content using Anthropic Claude."""
    if not ANTHROPIC_API_KEY:
        return None

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        prompt = f"""Write a compelling LinkedIn post for {COMPANY_NAME} ({BUSINESS_DESCRIPTION}).

Category: {category}
Topic: {topic}
Target Audience: {TARGET_AUDIENCE}
Key Services: {', '.join(KEY_SERVICES)}
Call to Action: {CALL_TO_ACTION}

Requirements:
- Start with an attention-grabbing hook
- Use emojis strategically
- Include specific numbers/statistics
- Have a clear call to action
- End with 3-5 relevant hashtags
- Keep it under 300 words
- Make it conversational and authentic
- Focus on generating business leads"""

        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=500,
            temperature=0.8,
            system="You are a professional LinkedIn content strategist specializing in B2B sales and lead generation posts.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.content[0].text.strip()
    except Exception as e:
        print(f"Anthropic generation error: {e}")
        return None


def generate_from_template(category=None):
    """Generate LinkedIn post content from templates."""
    if category:
        templates = [t for t in SALES_TEMPLATES if t["category"] == category]
        if not templates:
            templates = SALES_TEMPLATES
    else:
        templates = SALES_TEMPLATES

    template_data = random.choice(templates)
    category = template_data["category"]

    # Fill in template variables
    replacements = {
        "{company}": COMPANY_NAME,
        "{audience}": TARGET_AUDIENCE,
        "{pain_point}": random.choice(["leads", "invoices", "customer support", "reporting", "scheduling"]),
        "{cta}": CALL_TO_ACTION,
        "{industry}": random.choice(list(INDUSTRY_CHALLENGES.keys())),
        "{challenge}": random.choice(list(INDUSTRY_CHALLENGES.values())),
        "{service}": random.choice(KEY_SERVICES).strip(),
        "{tip_number}": str(random.randint(1, 50)),
        "{tip_content}": random.choice(BUSINESS_TIPS),
        "{offer}": "Free business automation audit for the first 5 respondents",
        "{spots}": "5",
        "{included_items}": "✅ Full process audit\n✅ Custom automation plan\n✅ 30-day implementation support\n✅ Weekly check-ins",
        "{technology}": "AI and automation",
        "{insights}": "• Companies using AI see 3x faster growth\n• Automation reduces costs by 40%\n• Early adopters capture 2x market share",
        "{number}": str(random.randint(50, 500)),
        "{services}": ", ".join(KEY_SERVICES[:3])
    }

    content = template_data["template"]
    for key, value in replacements.items():
        content = content.replace(key, value)

    return content


def generate_content(topic=None, category=None, use_llm=True):
    """
    Generate LinkedIn sales content.
    Tries LLM first, falls back to templates.
    """
    content = None

    if use_llm:
        if topic:
            # Try OpenAI first
            content = generate_with_openai(topic, category or "sales")
            if not content:
                content = generate_with_anthropic(topic, category or "sales")

        if not content:
            # Try with default topic
            default_topic = f"{COMPANY_NAME} {BUSINESS_DESCRIPTION}"
            content = generate_with_openai(default_topic, category or "sales")
            if not content:
                content = generate_with_anthropic(default_topic, category or "sales")

    # Fallback to templates
    if not content:
        content = generate_from_template(category)

    return content


def post_to_linkedin(content):
    """Post generated content to LinkedIn."""
    # Import the existing LinkedIn posting function
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    try:
        from linkedin_poster import post_linkedin
        result = post_linkedin(content)
        if result:
            print("✅ Successfully posted to LinkedIn.")
            return True
        else:
            print("❌ Failed to post to LinkedIn.")
            return False
    except ImportError:
        # Try direct Playwright approach
        try:
            from playwright.sync_api import sync_playwright

            email = os.getenv("LINKEDIN_EMAIL")
            password = os.getenv("LINKEDIN_PASSWORD")

            if not email or not password:
                print("Error: LINKEDIN_EMAIL or LINKEDIN_PASSWORD not set.")
                return False

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()

                page.goto("https://www.linkedin.com/login")
                page.fill('input[name="session_key"]', email)
                page.fill('input[name="session_password"]', password)
                page.click('button[type="submit"]')

                page.wait_for_selector('.share-box-feed-entry__trigger')
                page.click('.share-box-feed-entry__trigger')
                page.wait_for_selector('.ql-editor')
                page.fill('.ql-editor', content)
                page.click('button.share-actions__primary-action')

                print("✅ Successfully posted to LinkedIn.")
                browser.close()
                return True
        except Exception as e:
            print(f"Posting error: {e}")
            return False


def log_social_summary(content):
    """Log the post to Social_Logs.md."""
    vault_dir = os.environ.get("VAULT_PATH", "AI_Employee_Vault")
    reports_dir = os.path.join(vault_dir, "Reports")
    os.makedirs(reports_dir, exist_ok=True)

    social_log = os.path.join(reports_dir, "Social_Logs.md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary = content[:100].replace("|", "-") + "..."

    if os.path.exists(social_log):
        with open(social_log, "r") as f:
            existing = f.read()
    else:
        existing = "# Social Media Activity Log\n\n| Platform | Date | Summary |\n|----------|------|--------|\n"

    new_entry = f"| linkedin | {timestamp} | {summary} |\n"

    with open(social_log, "w") as f:
        f.write(existing + new_entry)


def main():
    """CLI entry point for LinkedIn Sales Content Generator."""
    import argparse

    parser = argparse.ArgumentParser(description="LinkedIn Sales Content Generator - Auto-generate and post sales content")
    parser.add_argument("--topic", type=str, help="Specific topic for the post")
    parser.add_argument("--category", type=str, choices=[
        "problem_awareness", "case_study", "tip_series", "direct_offer",
        "thought_leadership", "social_proof", "sales"
    ], help="Content category")
    parser.add_argument("--generate-only", action="store_true", help="Only generate content, don't post")
    parser.add_argument("--no-llm", action="store_true", help="Use templates instead of LLM")
    parser.add_argument("--count", type=int, default=1, help="Number of posts to generate")
    parser.add_argument("--schedule", action="store_true", help="Generate posts for scheduling (outputs to file)")

    args = parser.parse_args()

    if args.schedule or args.count > 1:
        # Generate multiple posts for scheduling
        vault_dir = os.environ.get("VAULT_PATH", "AI_Employee_Vault")
        inbox_dir = os.path.join(vault_dir, "Inbox")
        os.makedirs(inbox_dir, exist_ok=True)

        for i in range(args.count):
            content = generate_content(args.topic, args.category, use_llm=not args.no_llm)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(inbox_dir, f"linkedin_post_{timestamp}_{i+1}.md")

            with open(filename, "w") as f:
                f.write(f"""---
type: linkedin_post
status: pending
priority: medium
created_at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
category: {args.category or 'sales'}
---

# LinkedIn Sales Post

## Content
{content}

## Action
- [ ] Review and approve content
- [ ] Post to LinkedIn
- [ ] Log to Social_Logs.md
""")
            print(f"📝 Post saved to: {filename}")

    elif args.generate_only:
        # Just generate and display
        content = generate_content(args.topic, args.category, use_llm=not args.no_llm)
        print("\n" + "=" * 60)
        print("GENERATED LINKEDIN CONTENT:")
        print("=" * 60)
        print(content)
        print("=" * 60)

    else:
        # Generate and post
        content = generate_content(args.topic, args.category, use_llm=not args.no_llm)
        print("\n" + "=" * 60)
        print("POSTING TO LINKEDIN:")
        print("=" * 60)
        print(content)
        print("=" * 60)

        success = post_to_linkedin(content)
        if success:
            log_social_summary(content)
            print("\n✅ Post completed and logged.")
        else:
            print("\n⚠️ Content generated but posting failed. Check credentials.")


if __name__ == "__main__":
    main()
