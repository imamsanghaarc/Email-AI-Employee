import asyncio
import os
import smtplib
import subprocess
import sys
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP

# --- CONFIGURATION ---
VAULT_LOG_FILE = "AI_Employee_Vault/Logs/business.log"
LINKEDIN_SCRIPT = "scripts/linkedin_post_direct.py"
FACEBOOK_SCRIPT = "scripts/facebook_post.py"
TWITTER_SCRIPT = "scripts/twitter_post.py"
INSTAGRAM_SCRIPT = "scripts/instagram_post.py"
PYTHON_EXECUTABLE = sys.executable  # Cross-platform Python path

# Initialize FastMCP server
mcp = FastMCP("ex-business-mcp")

def ensure_log_dir():
    """Ensure the directory for business logs exists."""
    os.makedirs(os.path.dirname(VAULT_LOG_FILE), exist_ok=True)

@mcp.tool()
def log_activity(message: str) -> str:
    """
    Logs a business activity to the centralized vault log.
    
    Args:
        message: The activity description to log.
    """
    ensure_log_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] BUSINESS: {message}\n"
    
    try:
        with open(VAULT_LOG_FILE, "a") as f:
            f.write(log_entry)
        return f"Successfully logged: {message}"
    except Exception as e:
        return f"Error logging activity: {str(e)}"

@mcp.tool()
def send_email(to: str, subject: str, body: str) -> str:
    """
    Sends an email using SMTP (Gmail default).
    
    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Main content of the email.
    """
    # Environment variables for security
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")

    if not sender_email or not sender_password:
        return "Error: SENDER_EMAIL or SENDER_PASSWORD not set in environment."

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        log_activity(f"EMAIL SENT: To {to} | Subject: {subject}")
        return f"Email successfully sent to {to}"
    except Exception as e:
        return f"Error sending email: {str(e)}"

@mcp.tool()
def post_linkedin(content: str) -> str:
    """
    Creates and publishes a LinkedIn post using the automated browser script.

    Args:
        content: The text content for the LinkedIn post.
    """
    if not os.path.exists(LINKEDIN_SCRIPT):
        return f"Error: {LINKEDIN_SCRIPT} not found in root directory."

    try:
        # Run the existing direct posting script
        result = subprocess.run(
            [PYTHON_EXECUTABLE, LINKEDIN_SCRIPT, content],
            capture_output=True,
            text=True
        )

        if "successfully" in result.stdout.lower() or result.returncode == 0:
            log_activity(f"LINKEDIN POST: {content[:50]}...")

            # Log to Social Summary Skill
            try:
                summary_script = os.path.join(".agents", "skills", "social-summary", "scripts", "social_summary.py")
                if os.path.exists(summary_script):
                    subprocess.run([PYTHON_EXECUTABLE, summary_script, "linkedin", content], capture_output=True)
            except:
                pass

            return f"LinkedIn post successfully published."
        else:
            return f"LinkedIn post failed: {result.stdout}\n{result.stderr}"
    except Exception as e:
        return f"Error executing LinkedIn post: {str(e)}"


@mcp.tool()
def post_facebook(content: str) -> str:
    """
    Creates and publishes a Facebook post using the automated browser script.

    Args:
        content: The text content for the Facebook post.
    """
    if not os.path.exists(FACEBOOK_SCRIPT):
        return f"Error: {FACEBOOK_SCRIPT} not found."

    try:
        result = subprocess.run(
            [PYTHON_EXECUTABLE, FACEBOOK_SCRIPT, content],
            capture_output=True,
            text=True,
            timeout=180
        )

        if "successfully" in result.stdout.lower() or result.returncode == 0:
            log_activity(f"FACEBOOK POST: {content[:50]}...")
            try:
                summary_script = os.path.join(".agents", "skills", "social-summary", "scripts", "social_summary.py")
                if os.path.exists(summary_script):
                    subprocess.run([PYTHON_EXECUTABLE, summary_script, "facebook", content], capture_output=True)
            except:
                pass
            return "Facebook post successfully published."
        else:
            return f"Facebook post failed: {result.stdout}\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return "Facebook post timed out (180s limit)"
    except Exception as e:
        return f"Error executing Facebook post: {str(e)}"


@mcp.tool()
def post_twitter(content: str) -> str:
    """
    Creates and publishes a Twitter/X post using the automated browser script.

    Args:
        content: The text content for the Twitter post (max 280 characters).
    """
    if not os.path.exists(TWITTER_SCRIPT):
        return f"Error: {TWITTER_SCRIPT} not found."

    if len(content) > 280:
        return f"Error: Tweet content too long ({len(content)} chars). Max 280 characters."

    try:
        result = subprocess.run(
            [PYTHON_EXECUTABLE, TWITTER_SCRIPT, content],
            capture_output=True,
            text=True,
            timeout=180
        )

        if "successfully" in result.stdout.lower() or result.returncode == 0:
            log_activity(f"TWITTER POST: {content[:50]}...")
            try:
                summary_script = os.path.join(".agents", "skills", "social-summary", "scripts", "social_summary.py")
                if os.path.exists(summary_script):
                    subprocess.run([PYTHON_EXECUTABLE, summary_script, "twitter", content], capture_output=True)
            except:
                pass
            return "Twitter/X post successfully published."
        else:
            return f"Twitter post failed: {result.stdout}\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return "Twitter post timed out (180s limit)"
    except Exception as e:
        return f"Error executing Twitter post: {str(e)}"


@mcp.tool()
def post_instagram(content: str) -> str:
    """
    Creates and publishes an Instagram post using the automated browser script.

    Args:
        content: The caption text for the Instagram post.
    """
    if not os.path.exists(INSTAGRAM_SCRIPT):
        return f"Error: {INSTAGRAM_SCRIPT} not found."

    try:
        result = subprocess.run(
            [PYTHON_EXECUTABLE, INSTAGRAM_SCRIPT, content],
            capture_output=True,
            text=True,
            timeout=180
        )

        if "successfully" in result.stdout.lower() or result.returncode == 0:
            log_activity(f"INSTAGRAM POST: {content[:50]}...")
            try:
                summary_script = os.path.join(".agents", "skills", "social-summary", "scripts", "social_summary.py")
                if os.path.exists(summary_script):
                    subprocess.run([PYTHON_EXECUTABLE, summary_script, "instagram", content], capture_output=True)
            except:
                pass
            return "Instagram post successfully published."
        else:
            return f"Instagram post failed: {result.stdout}\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return "Instagram post timed out (180s limit)"
    except Exception as e:
        return f"Error executing Instagram post: {str(e)}"

if __name__ == "__main__":
    # Run the server via stdio
    mcp.run()
