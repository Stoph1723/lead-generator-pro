"""
Telegram Notifier
=================
Sends alerts to your Telegram when:
- Emails are sent
- Client opens email
- Client replies
- New leads found

Created by: Mustapha Elasri
"""

import requests
from typing import Dict, List

from client_finder.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_telegram(message: str) -> bool:
    """Send a message to your Telegram. Returns True on success."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"  [Telegram] {message}")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        response = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
        }, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"  [!] Telegram failed: {e}")
        return False


def notify_leads_found(businesses: List[Dict], query: str, location: str):
    """Alert when new leads are found."""
    count = len(businesses)
    with_email = sum(1 for b in businesses if b.get("email"))

    msg = (
        f"<b>New Leads Found</b>\n\n"
        f"Query: {query}\n"
        f"Location: {location}\n"
        f"Total: {count} businesses\n"
        f"With email: {with_email}\n\n"
    )

    for biz in businesses[:5]:
        name = biz.get("name", "Unknown")
        email = biz.get("email", "no email")
        msg += f"  - {name} ({email})\n"

    if count > 5:
        msg += f"  ... and {count - 5} more\n"

    send_telegram(msg)


def notify_emails_sent(stats: Dict):
    """Alert when emails are sent."""
    sent = stats.get("sent", 0)
    failed = stats.get("failed", 0)
    total = stats.get("total", 0)

    msg = (
        f"<b>Emails Sent</b>\n\n"
        f"Sent: {sent}/{total}\n"
        f"Failed: {failed}\n\n"
    )

    for r in stats.get("results", []):
        status_icon = "+" if r.get("status") == "sent" else "x"
        msg += f"  [{status_icon}] {r.get('name', '')} < {r.get('email', '')}>\n"

    send_telegram(msg)


def notify_summary(query: str, location: str, businesses: int, emails_found: int, emails_sent: int):
    """Send a summary after the run."""
    msg = (
        f"<b>Run Complete</b>\n\n"
        f"Query: {query}\n"
        f"Location: {location}\n\n"
        f"Businesses found: {businesses}\n"
        f"Emails found: {emails_found}\n"
        f"Emails sent: {emails_sent}\n\n"
        f"Check Brevo dashboard for open tracking."
    )
    send_telegram(msg)
