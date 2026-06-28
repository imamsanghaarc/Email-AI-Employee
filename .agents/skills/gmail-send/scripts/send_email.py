import smtplib
import os
import sys
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

def send_email(to, subject, body):
    # Load .env from project root
    load_dotenv(os.path.join(os.getcwd(), ".env"))
    user = os.getenv("EMAIL_ADDRESS")
    pw = os.getenv("EMAIL_APP_PASSWORD") or os.getenv("EMAIL_PASSWORD")

    if not user or not pw:
        print("ERROR: SMTP credentials (EMAIL_ADDRESS/EMAIL_APP_PASSWORD) missing.")
        return False

    msg = MIMEMultipart()
    msg['From'], msg['To'], msg['Subject'] = user, to, subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(user, pw)
            server.send_message(msg)
        print(f"SUCCESS: Email sent to {to}")
        return True
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--to", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body", required=True)
    args = parser.parse_args()
    sys.exit(0 if send_email(args.to, args.subject, args.body) else 1)
