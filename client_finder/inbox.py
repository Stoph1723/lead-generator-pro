"""
Gmail Inbox Monitor
===================
Checks Gmail for client replies using IMAP.
Shows unread replies in Telegram.

Created by: Mustapha Elasri
"""

import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from client_finder.config import SENDER_EMAIL, GMAIL_IMAP_PASSWORD
from client_finder.notifier import send_telegram


def _decode_subject(subject: str) -> str:
    """Decode email subject."""
    if not subject:
        return "(no subject)"
    decoded_parts = decode_header(subject)
    result = ""
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            result += part.decode(encoding or "utf-8", errors="replace")
        else:
            result += part
    return result.strip()


def _get_body(msg) -> str:
    """Extract plain text body from email."""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    body = payload.decode(charset, errors="replace")
                    break
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            body = payload.decode(charset, errors="replace")
    return body.strip()[:1000]


def check_replies() -> List[Dict]:
    """Check Gmail for new replies. Returns list of reply dicts."""
    if not GMAIL_IMAP_PASSWORD:
        return []

    replies = []

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(SENDER_EMAIL, GMAIL_IMAP_PASSWORD)
        mail.select("INBOX")

        since = (datetime.now() - timedelta(hours=24)).strftime("%d-%b-%Y")
        status, messages = mail.search(None, f'(SINCE "{since}" UNSEEN)')

        if status != "OK":
            return []

        msg_ids = messages[0].split()

        for msg_id in msg_ids:
            status, data = mail.fetch(msg_id, "(RFC822)")
            if status != "OK":
                continue

            msg = email.message_from_bytes(data[0][1])

            subject = _decode_subject(msg.get("Subject", ""))
            from_addr = msg.get("From", "")
            date = msg.get("Date", "")
            body = _get_body(msg)

            if "re:" in subject.lower():
                name = from_addr.split("<")[0].strip().strip('"')
                email_addr = from_addr.split("<")[-1].rstrip(">") if "<" in from_addr else from_addr

                replies.append({
                    "name": name,
                    "email": email_addr,
                    "subject": subject,
                    "body": body,
                    "date": date,
                    "msg_id": msg_id.decode(),
                })

        mail.logout()

    except Exception as e:
        print(f"  [!] Gmail error: {e}")

    return replies


def notify_new_replies():
    """Check for new replies and send Telegram alerts."""
    replies = check_replies()

    if not replies:
        return

    for reply in replies:
        msg = (
            f"<b>💬 NEW REPLY</b>\n\n"
            f"From: {reply['name']}\n"
            f"Email: {reply['email']}\n"
            f"Subject: {reply['subject']}\n\n"
            f"<b>Message:</b>\n{reply['body'][:500]}\n\n"
            f"Reply: reply: &lt;your response&gt;"
        )
        send_telegram(msg)

    return replies
