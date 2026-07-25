"""
Email Sender (Brevo SMTP)
=========================
Sends cold emails via Brevo SMTP.
Free tier: 300 emails/day.

Created by: Mustapha Elasri
"""

import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List

from client_finder.config import (
    BREVO_SMTP_KEY,
    BREVO_LOGIN,
    SENDER_EMAIL,
    SENDER_NAME_EMAIL,
    DELAY_BETWEEN_EMAILS,
)


def _get_smtp_server():
    """Connect to Brevo SMTP server."""
    server = smtplib.SMTP_SSL("smtp-relay.brevo.com", 465, timeout=30)
    server.login(BREVO_LOGIN, BREVO_SMTP_KEY)
    return server


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send one email via Brevo SMTP. Returns True on success."""
    if not BREVO_SMTP_KEY or not SENDER_EMAIL:
        print(f"  [!] Brevo not configured. Would send to: {to_email}")
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{SENDER_NAME_EMAIL} <{SENDER_EMAIL}>"
    msg["To"] = to_email
    msg["Subject"] = subject

    html_body = body.replace("\n", "<br>")
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; font-size: 14px; color: #333; line-height: 1.6;">
    {html_body}
    </body>
    </html>
    """

    msg.attach(MIMEText(body, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        server = _get_smtp_server()
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"  [!] Failed to send to {to_email}: {e}")
        return False


def send_emails_batch(emails: List[Dict], max_emails: int = 30) -> Dict:
    """Send cold emails to a list of businesses.
    Each dict must have: email, subject, body, name.
    Returns stats dict."""

    sent = 0
    failed = 0
    results = []

    total = min(len(emails), max_emails)
    print(f"  Sending {total} emails via Brevo...")

    for i, item in enumerate(emails[:max_emails]):
        to_email = item.get("email", "")
        subject = item.get("subject", "")
        body = item.get("body", "")
        name = item.get("name", "")

        if not to_email or not subject or not body:
            continue

        success = send_email(to_email, subject, body)

        if success:
            sent += 1
            results.append({
                "name": name,
                "email": to_email,
                "status": "sent",
            })
            print(f"  [{sent}/{total}] Sent to {name} <{to_email}>")
        else:
            failed += 1
            results.append({
                "name": name,
                "email": to_email,
                "status": "failed",
            })

        if i < total - 1:
            time.sleep(DELAY_BETWEEN_EMAILS)

    return {
        "sent": sent,
        "failed": failed,
        "total": total,
        "results": results,
    }
