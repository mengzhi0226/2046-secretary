#!/usr/bin/env python3
"""
Send a Markdown file as email via Resend API (no pip install required).

Usage:
    python scripts/send_email_resend.py --subject "标题" --body-file path/to/file.md

Environment variables (set in the RemoteTrigger environment):
    RESEND_API_KEY   — your Resend API key (starts with re_...)
    EMAIL_TO         — recipient address (default: mengzhi0226@gmail.com)
    EMAIL_FROM       — sender address (default: onboarding@resend.dev for testing,
                       or your verified domain address for production)
"""
import urllib.request
import urllib.error
import json
import os
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Send email via Resend API")
    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument("--body-file", required=True, help="Path to .md file to send as body")
    args = parser.parse_args()

    api_key   = os.environ.get("RESEND_API_KEY", "")
    email_to  = os.environ.get("EMAIL_TO",  "mengzhi0226@gmail.com")
    email_from = os.environ.get("EMAIL_FROM", "onboarding@resend.dev")

    if not api_key or api_key == "YOUR_RESEND_API_KEY":
        print("ERROR: RESEND_API_KEY not configured.")
        print("Get a free API key at: https://resend.com/api-keys")
        raise SystemExit(1)

    body_path = Path(args.body_file)
    if not body_path.exists():
        print(f"ERROR: Body file not found: {args.body_file}")
        raise SystemExit(1)

    body_text = body_path.read_text(encoding="utf-8")

    payload = json.dumps({
        "from": email_from,
        "to":   [email_to],
        "subject": args.subject,
        "text": body_text,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode())
            print(f"✅ Email sent to {email_to}: {args.subject}")
            print(f"   Resend ID: {result.get('id', 'unknown')}")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"ERROR {e.code}: {error_body}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
