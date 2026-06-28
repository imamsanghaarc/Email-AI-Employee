import os
import sys
from dotenv import load_dotenv, set_key

ENV_PATH = ".env"
VAULT_DIR = "AI_Employee_Vault"

REQUIRED_VARS = {
    "Bronze (no config needed)": {},
    "Silver - LLM (at least one)": {
        "OPENROUTER_API_KEY": "OpenRouter API key (https://openrouter.ai/keys)",
        "GEMINI_API_KEY": "Google Gemini API key (https://aistudio.google.com/app/apikey)",
        "ANTHROPIC_API_KEY": "Anthropic Claude API key (https://console.anthropic.com/)",
        "OPENAI_API_KEY": "OpenAI API key (https://platform.openai.com/api-keys)",
    },
    "Gold - Email": {
        "EMAIL_ADDRESS": "Gmail address for sending emails",
        "EMAIL_APP_PASSWORD": "Gmail app password (16 chars, no spaces)",
    },
    "Gold - LinkedIn": {
        "LINKEDIN_EMAIL": "LinkedIn email/username",
        "LINKEDIN_PASSWORD": "LinkedIn password",
    },
    "Gold - Social Media": {
        "FB_EMAIL": "Facebook email",
        "FB_PASSWORD": "Facebook password",
        "TWITTER_USER": "Twitter/X username",
        "TWITTER_PASSWORD": "Twitter/X password",
        "INSTA_USER": "Instagram username",
        "INSTA_PASSWORD": "Instagram password",
    },
    "Gold - Odoo ERP": {
        "ODOO_URL": "Odoo server URL (default: http://localhost:8069)",
        "ODOO_DB": "Odoo database name",
        "ODOO_USER": "Odoo username",
        "ODOO_PASSWORD": "Odoo password",
    },
}

def check_existing():
    load_dotenv()
    found = []
    missing = []
    for category, vars_dict in REQUIRED_VARS.items():
        for var, desc in vars_dict.items():
            val = os.getenv(var)
            if val:
                found.append(var)
            else:
                missing.append((var, desc, category))
    return found, missing

def interactive_setup():
    print("=" * 60)
    print("  AI EMPLOYEE - Interactive Credentials Setup")
    print("=" * 60)
    print()

    if os.path.exists(ENV_PATH):
        print(f"[OK] Found existing {ENV_PATH}")
    else:
        print(f"[*] Creating {ENV_PATH} from .env.example...")
        if os.path.exists(".env.example"):
            with open(".env.example", "r") as src:
                with open(ENV_PATH, "w") as dst:
                    dst.write(src.read())
            print("[OK] Created. Now let's configure your credentials.")
        else:
            with open(ENV_PATH, "w") as f:
                f.write("# AI Employee Environment Configuration\n")
            print("[OK] Created empty .env file.")

    found, missing = check_existing()

    if found:
        print(f"\n[OK] Already configured: {', '.join(found)}")
    print()

    if not missing:
        print("[OK] All credentials are configured! Ready to run.")
        return

    print(f"Still need {len(missing)} credential(s). Let's set them up.\n")

    by_category = {}
    for var, desc, category in missing:
        by_category.setdefault(category, []).append((var, desc))

    for category, vars_list in by_category.items():
        print(f"\n--- {category} ---")
        for var, desc in vars_list:
            val = input(f"  {desc}\n    [{var}]: ").strip()
            if val:
                set_key(ENV_PATH, var, val)
                os.environ[var] = val
                print(f"    [OK] {var} saved")
            else:
                print(f"    [SKIP] {var} (set later in .env)")

    print("\n" + "=" * 60)
    print("Setup complete!")
    print(f"Edit {ENV_PATH} anytime to change values.")
    print("=" * 60)

def quick_check():
    load_dotenv()
    print("Checking required credentials...")
    any_missing = False
    for category, vars_dict in REQUIRED_VARS.items():
        for var, desc in vars_dict.items():
            if os.getenv(var):
                print(f"  [OK] {var}")
            else:
                print(f"  [MISSING] {var}")
                any_missing = True
    if any_missing:
        print("\nSome credentials missing. Run: python scripts/setup_credentials.py --interactive")
    else:
        print("\nAll credentials found!")

if __name__ == "__main__":
    if "--interactive" in sys.argv or "-i" in sys.argv:
        interactive_setup()
    else:
        quick_check()
