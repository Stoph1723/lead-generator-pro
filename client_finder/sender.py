"""
Email Sender (Brevo API)
=======================
Sends cold emails via Brevo Transactional Email API.
Validates emails (MX check) before sending.

Created by: Mustapha Elasri
"""

import time
import dns.resolver
import requests
from typing import Dict, List

from client_finder.config import (
    BREVO_API_KEY,
    BREVO_SMTP_KEY,
    SENDER_EMAIL,
    SENDER_NAME_EMAIL,
    DELAY_BETWEEN_EMAILS,
)


def validate_email(email: str) -> bool:
    """Validate email by checking MX record exists."""
    if not email or "@" not in email:
        return False

    domain = email.split("@")[1]

    try:
        mx_records = dns.resolver.resolve(domain, "MX")
        return len(mx_records) > 0
    except dns.resolver.NXDOMAIN:
        return False
    except dns.resolver.NoAnswer:
        return False
    except dns.resolver.NoNameservers:
        return False
    except Exception:
        return False


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send one email via Brevo Transactional API with tracking."""
    if not BREVO_API_KEY:
        print(f"  [!] Brevo API not configured. Would send to: {to_email}")
        return False

    if not validate_email(to_email):
        print(f"  [!] Invalid email (no MX record): {to_email}")
        return False

    url = "https://api.brevo.com/v3/smtp/email"

    html_body = body.replace("\n", "<br>")
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; font-size: 14px; color: #333; line-height: 1.6;">
    {html_body}
    </body>
    </html>
    """

    payload = {
        "sender": {
            "name": SENDER_NAME_EMAIL,
            "email": SENDER_EMAIL,
        },
        "to": [
            {"email": to_email}
        ],
        "subject": subject,
        "htmlContent": html,
        "textContent": body,
        "params": {
            "name": SENDER_NAME_EMAIL,
        },
        "tags": ["cold-email", "client-finder"],
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code == 201:
            return True
        else:
            print(f"  [!] Brevo error {response.status_code}: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"  [!] Send failed: {e}")
        return False


def send_emails_batch(emails: List[Dict], max_emails: int = 100) -> Dict:
    """Send cold emails. Each dict: email, subject, body, name."""
    from client_finder.tracker import _load_tracking

    tracking = _load_tracking()
    sent_list = tracking.get("sent", [])
    if isinstance(sent_list, dict):
        already_sent = {k.lower() for k in sent_list.keys()}
    else:
        already_sent = {s.get("email", "").lower() for s in sent_list}

    sent = 0
    failed = 0
    skipped = 0
    results = []

    to_send = []
    for item in emails[:max_emails]:
        to_email = item.get("email", "")
        if to_email.lower() in already_sent:
            skipped += 1
            continue
        to_send.append(item)

    total = min(len(to_send), max_emails)
    if total == 0:
        print(f"  All emails already sent, nothing to send.")
        return {"sent": 0, "failed": 0, "skipped": skipped, "total": 0, "results": []}
    print(f"  Sending {total} emails ({skipped} already sent, skipping)...")

    for i, item in enumerate(to_send[:max_emails]):
        to_email = item.get("email", "")
        subject = item.get("subject", "")
        body = item.get("body", "")
        name = item.get("name", "")

        if not to_email or not subject or not body:
            continue

        success = send_email(to_email, subject, body)

        if success:
            sent += 1
            results.append({"name": name, "email": to_email, "subject": subject, "status": "sent"})
            print(f"  [{sent}/{total}] Sent to {name} <{to_email}>")
        else:
            failed += 1
            results.append({"name": name, "email": to_email, "subject": subject, "status": "failed"})

        if i < total - 1:
            time.sleep(DELAY_BETWEEN_EMAILS)

    return {"sent": sent, "failed": failed, "skipped": skipped, "total": total, "results": results}
