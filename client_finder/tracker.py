"""
Email Tracker
=============
Checks Brevo API for email opens and sends Telegram alerts.
Saves sent emails to track who opened what.

Created by: Mustapha Elasri
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List

from client_finder.config import BREVO_API_KEY
from client_finder.notifier import send_telegram

TRACKING_FILE = os.path.join(os.path.dirname(__file__), "..", "output", "tracking.json")


def _load_tracking() -> Dict:
    """Load tracking data from file."""
    if os.path.exists(TRACKING_FILE):
        with open(TRACKING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"sent": [], "opened": [], "replied": []}


def _save_tracking(data: Dict):
    """Save tracking data to file."""
    os.makedirs(os.path.dirname(TRACKING_FILE), exist_ok=True)
    with open(TRACKING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def track_email_sent(name: str, email: str, subject: str):
    """Record that an email was sent."""
    data = _load_tracking()

    entry = {
        "name": name,
        "email": email,
        "subject": subject,
        "sent_at": datetime.now().isoformat(),
        "opened": False,
        "open_count": 0,
        "last_opened": None,
    }

    existing = [i for i, s in enumerate(data["sent"]) if s["email"].lower() == email.lower()]
    if existing:
        data["sent"][existing[0]] = entry
    else:
        data["sent"].append(entry)

    _save_tracking(data)


def check_opens() -> List[Dict]:
    """Check Brevo API for email opens. Returns list of newly opened emails."""
    if not BREVO_API_KEY:
        return []

    data = _load_tracking()
    new_opens = []

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
    }

    try:
        url = "https://api.brevo.com/v3/smtp/statistics/events"
        params = {"limit": 50, "offset": 0}
        response = requests.get(url, headers=headers, params=params, timeout=15)

        if response.status_code == 200:
            events = response.json().get("events", [])
            for event in events:
                if event.get("event") == "open":
                    email = event.get("email", "")
                    for sent in data["sent"]:
                        if sent["email"].lower() == email.lower() and not sent.get("alerted_open"):
                            sent["opened"] = True
                            sent["open_count"] = sent.get("open_count", 0) + 1
                            sent["last_opened"] = datetime.now().isoformat()
                            sent["alerted_open"] = True
                            new_opens.append(sent)

                            send_telegram(
                                f"<b>Email Opened!</b>\n\n"
                                f"To: {sent['name']} &lt;{email}&gt;\n"
                                f"Subject: {sent.get('subject', 'N/A')}\n"
                                f"Opened: {sent['open_count']}x\n\n"
                                f"They're interested! Follow up."
                            )

            _save_tracking(data)

    except Exception as e:
        print(f"  [!] Tracking error: {e}")

    return new_opens


def get_stats() -> Dict:
    """Get email statistics."""
    data = _load_tracking()

    sent = len(data.get("sent", []))
    opened = sum(1 for s in data.get("sent", []) if s.get("opened"))
    replied = sum(1 for s in data.get("sent", []) if s.get("replied"))

    opened_list = [s for s in data.get("sent", []) if s.get("opened")]
    not_opened = [s for s in data.get("sent", []) if not s.get("opened")]
    replied_list = [s for s in data.get("sent", []) if s.get("replied")]

    return {
        "sent": sent,
        "opened": opened,
        "replied": replied,
        "not_opened": len(not_opened),
        "open_rate": round((opened / sent * 100) if sent > 0 else 0, 1),
        "opened_list": opened_list,
        "not_opened_list": not_opened,
        "replied_list": replied_list,
    }


def stats_to_telegram():
    """Send stats report to Telegram."""
    stats = get_stats()

    msg = f"<b>EMAIL STATS</b>\n"
    msg += f"Sent: {stats['sent']}\n"
    msg += f"Opened: {stats['opened']} ({stats['open_rate']}%)\n"
    msg += f"Replied: {stats['replied']}\n"
    msg += f"Not opened: {stats['not_opened']}\n"

    if stats["opened_list"]:
        msg += f"\n<b>OPENED:</b>\n"
        for s in stats["opened_list"][:10]:
            msg += f"  {s['name']} - opened {s.get('open_count', 1)}x\n"

    if stats["replied_list"]:
        msg += f"\n<b>REPLIED:</b>\n"
        for s in stats["replied_list"][:10]:
            msg += f"  {s['name']}\n"

    if stats["not_opened_list"]:
        msg += f"\n<b>NOT OPENED:</b>\n"
        for s in stats["not_opened_list"][:5]:
            msg += f"  {s['name']} &lt;{s['email']}&gt;\n"

    send_telegram(msg)
