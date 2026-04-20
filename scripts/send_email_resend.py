#!/usr/bin/env python3
"""
Send a Markdown file as email via Resend API.

Usage:
    RESEND_API_KEY=re_xxx EMAIL_TO=you@example.com EMAIL_FROM=onboarding@resend.dev \
        python scripts/send_email_resend.py --subject "标题" --body-file path/to/file.md
"""
import os
import argparse
import urllib.request
import urllib.error
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Send email via Resend API")
    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument("--body-file", required=True, help="Path to .md file to send as body")
    args = parser.parse_args()

    api_key   = os.environ.get("RESEND_API_KEY", "")
    email_to  = os.environ.get("EMAIL_TO", "")
    email_from = os.environ.get("EMAIL_FROM", "onboarding@resend.dev")

    if not api_key:
        print("ERROR: RESEND_API_KEY not set.")
        raise SystemExit(1)
    if not email_to:
        print("ERROR: EMAIL_TO not set.")
        raise SystemExit(1)

    body_path = Path(args.body_file)
    if not body_path.exists():
        print(f"ERROR: Body file not found: {args.body_file}")
        raise SystemExit(1)

    body = body_path.read_text(encoding="utf-8")

    payload = json.dumps({
        "from": email_from,
        "to": [email_to],
        "subject": args.subject,
        "text": body,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode())
            print(f"[OK] Email sent. id={result.get('id')} to={email_to}")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        print(f"ERROR {e.code}: {err_body}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
