#!/usr/bin/env python3
"""
MCP Server - Model Context Protocol server for external actions.
Provides standardized API for AI Employee to execute external actions like sending emails.
"""

import os
import sys
import json
import time
import logging
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from urllib.parse import urlparse, parse_qs

# Configuration
DEFAULT_PORT = 8765
LOG_FILE = "logs/mcp_server.log"

# Ensure directories exist
os.makedirs("logs", exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_env():
    """Load environment variables from .env file."""
    env_file = ".env"
    if not os.path.exists(env_file):
        return {}
    
    env_vars = {}
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()
    
    return env_vars


# ============================================================================
# Tool Implementations
# ============================================================================

def send_email(params):
    """Send an email via SMTP."""
    required = ["to", "subject", "body"]
    for param in required:
        if param not in params:
            return {"error": f"Missing parameter: {param}", "status": "error"}
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        env = load_env()
        email_address = env.get("EMAIL_ADDRESS")
        email_password = env.get("EMAIL_APP_PASSWORD") or env.get("EMAIL_PASSWORD")
        
        if not email_address or not email_password:
            return {"error": "Email credentials not configured", "status": "error"}
        
        msg = MIMEMultipart()
        msg["From"] = email_address
        msg["To"] = params["to"]
        msg["Subject"] = params["subject"]
        
        is_html = params.get("html", False)
        content_type = "html" if is_html else "plain"
        msg.attach(MIMEText(params["body"], content_type))
        
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(email_address, email_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email sent to {params['to']}")
        return {
            "status": "success",
            "message": f"Email sent to {params['to']}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return {"error": str(e), "status": "error"}


def post_linkedin(params):
    """Post content to LinkedIn using Playwright MCP server."""
    if "content" not in params:
        return {"error": "Missing parameter: content", "status": "error"}
    
    try:
        # Call the LinkedIn poster script which uses Playwright MCP
        import subprocess
        
        cmd = [
            "python",
            ".agents/skills/linkedin-business-poster/scripts/post_business_content.py",
            "--content", params["content"]
        ]
        
        if params.get("require_approval"):
            cmd.append("--require-approval")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        
        if result.returncode == 0:
            logger.info("LinkedIn post published via Playwright MCP")
            return {
                "status": "success",
                "message": "Post published to LinkedIn via Playwright MCP",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {"error": result.stderr or result.stdout, "status": "error"}
    except Exception as e:
        logger.error(f"Failed to post to LinkedIn: {e}")
        return {"error": str(e), "status": "error"}


def check_gmail(params):
    """Check Gmail for new emails."""
    try:
        import imaplib
        import email as email_lib
        from email.header import decode_header
        
        env = load_env()
        email_address = env.get("GMAIL_ADDRESS") or env.get("EMAIL_ADDRESS")
        email_password = env.get("GMAIL_APP_PASSWORD") or env.get("EMAIL_APP_PASSWORD") or env.get("EMAIL_PASSWORD")

        if not email_address or not email_password:
            return {"error": "Gmail credentials not configured", "status": "error"}
        
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(email_address, email_password)
        mail.select("INBOX")
        
        max_results = params.get("max_results", 10)
        status, messages = mail.search(None, "UNSEEN")
        
        if status != "OK":
            return {"error": "Failed to search emails", "status": "error"}
        
        email_ids = messages[0].split()[-max_results:]
        emails = []
        
        for email_id in email_ids:
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            if status == "OK":
                msg = email_lib.message_from_bytes(msg_data[0][1])
                emails.append({
                    "from": msg.get("From"),
                    "subject": msg.get("Subject"),
                    "date": msg.get("Date")
                })
        
        mail.close()
        mail.logout()
        
        return {
            "status": "success",
            "emails": emails,
            "count": len(emails),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to check Gmail: {e}")
        return {"error": str(e), "status": "error"}


def check_linkedin(params):
    """Check LinkedIn for new activity."""
    return {
        "status": "success",
        "message": "LinkedIn checking not implemented via MCP. Use linkedin-watcher skill directly.",
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# Tool Registry
# ============================================================================

TOOLS = {
    "send_email": {
        "name": "send_email",
        "description": "Send an email via SMTP",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string", "description": "Email subject"},
                "body": {"type": "string", "description": "Email body content"},
                "html": {"type": "boolean", "description": "Whether body is HTML (default: false)"}
            },
            "required": ["to", "subject", "body"]
        },
        "execute": send_email
    },
    "post_linkedin": {
        "name": "post_linkedin",
        "description": "Post content to LinkedIn",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "LinkedIn post content"},
                "require_approval": {"type": "boolean", "description": "Require human approval (default: false)"}
            },
            "required": ["content"]
        },
        "execute": post_linkedin
    },
    "check_gmail": {
        "name": "check_gmail",
        "description": "Check Gmail for new emails",
        "parameters": {
            "type": "object",
            "properties": {
                "max_results": {"type": "integer", "description": "Maximum emails to retrieve (default: 10)"}
            }
        },
        "execute": check_gmail
    },
    "check_linkedin": {
        "name": "check_linkedin",
        "description": "Check LinkedIn for new activity",
        "parameters": {
            "type": "object",
            "properties": {
                "activity_types": {"type": "array", "description": "Types of activity to check"}
            }
        },
        "execute": check_linkedin
    }
}


# ============================================================================
# HTTP Server
# ============================================================================

class MCPHandler(BaseHTTPRequestHandler):
    """HTTP request handler for MCP server."""
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy", "timestamp": datetime.now().isoformat()}).encode())
        
        elif parsed_path.path == "/tools":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            tools_list = []
            for name, tool in TOOLS.items():
                tools_list.append({
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                })
            
            self.wfile.write(json.dumps({"tools": tools_list}).encode())
        
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)
        path_parts = parsed_path.path.strip("/").split("/")
        
        if len(path_parts) >= 2 and path_parts[0] == "tools":
            tool_name = path_parts[1]
            
            if tool_name not in TOOLS:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Tool not found: {tool_name}"}).encode())
                return
            
            # Read request body
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            
            try:
                params = json.loads(post_data.decode("utf-8"))
            except json.JSONDecodeError:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
                return
            
            # Execute tool
            logger.info(f"Executing tool: {tool_name}")
            result = TOOLS[tool_name]["execute"](params)
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def log_message(self, format, *args):
        """Override to use our logger."""
        logger.info(f"{self.client_address[0]} - {format % args}")


def run_server(port=DEFAULT_PORT):
    """Start the MCP server."""
    server = HTTPServer(("0.0.0.0", port), MCPHandler)
    logger.info(f"MCP Server starting on port {port}")
    logger.info(f"Available tools: {', '.join(TOOLS.keys())}")
    logger.info("Server endpoints:")
    logger.info(f"  GET  /tools              - List available tools")
    logger.info(f"  POST /tools/{{name}}       - Execute a tool")
    logger.info(f"  GET  /health             - Health check")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down MCP Server...")
        server.shutdown()


def list_tools():
    """List all available tools."""
    print("\n" + "=" * 60)
    print("MCP Server - Available Tools")
    print("=" * 60 + "\n")
    
    for name, tool in TOOLS.items():
        print(f"Tool: {tool['name']}")
        print(f"Description: {tool['description']}")
        print(f"Parameters: {json.dumps(tool['parameters'], indent=2)}")
        print("-" * 60 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="MCP Server for AI Employee")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Server port (default: {DEFAULT_PORT})")
    parser.add_argument("--list-tools", action="store_true", help="List available tools and exit")
    
    args = parser.parse_args()
    
    if args.list_tools:
        list_tools()
        return
    
    run_server(args.port)


if __name__ == "__main__":
    main()
