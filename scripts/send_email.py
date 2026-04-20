#!/usr/bin/env python3
"""
Send a Markdown file as a plain-text email.

Usage:
    python scripts/send_email.py --subject "标题" --body-file path/to/file.md

Reads SMTP credentials from environment variables (set in .claude/settings.json):
    SMTP_HOST  (default: smtp.gmail.com)
    SMTP_PORT  (default: 587)
    SMTP_USER  (your Gmail address)
    SMTP_PASS  (Gmail App Password from myaccount.google.com/apppasswords)
    EMAIL_TO   (default: same as SMTP_USER)
"""
import smtplib
import os
import argparse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path


def _load_creds_from_aboutme():
    """Fallback: read SMTP creds from aboutme.json if env vars not set."""
    try:
        import json
        candidates = [
            Path(__file__).parent.parent / "aboutme.json",
            Path("aboutme.json"),
        ]
        for p in candidates:
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8"))
                smtp = data.get("smtp", {})
                return smtp
    except Exception:
        pass
    return {}


def main():
    parser = argparse.ArgumentParser(description="Send email with Markdown file body")
    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument("--body-file", required=True, help="Path to .md file to send as body")
    args = parser.parse_args()

    fallback = _load_creds_from_aboutme()
    smtp_host = os.environ.get("SMTP_HOST") or fallback.get("host", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT") or fallback.get("port", 587))
    smtp_user = os.environ.get("SMTP_USER") or fallback.get("user", "")
    smtp_pass = os.environ.get("SMTP_PASS") or fallback.get("password", "")
    email_to  = os.environ.get("EMAIL_TO") or fallback.get("to", smtp_user)

    if not smtp_user or not smtp_pass or smtp_pass == "YOUR_GMAIL_APP_PASSWORD":
        print("ERROR: SMTP credentials not configured.")
        print("Edit .claude/settings.json and set SMTP_USER and SMTP_PASS.")
        print("Get a Gmail App Password at: https://myaccount.google.com/apppasswords")
        raise SystemExit(1)

    body_path = Path(args.body_file)
    if not body_path.exists():
        print(f"ERROR: Body file not found: {args.body_file}")
        raise SystemExit(1)

    body = body_path.read_text(encoding="utf-8")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = args.subject
    msg["From"]    = smtp_user
    msg["To"]      = email_to
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, email_to, msg.as_string())

    print("[OK] Email sent to: " + email_to)


if __name__ == "__main__":
    main()
