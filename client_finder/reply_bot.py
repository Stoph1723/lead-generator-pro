"""
Telegram Reply Bot
=================
Talk to your Telegram bot to:
- See client replies from Gmail
- Get AI-generated responses
- Track email opens
- Check stats

Commands:
  /start — Show help
  /stats — Email stats
  /inbox — Check for new replies
  reply: <client message> — Get AI reply
  send: <email> | <subject> | <body> — Send email directly

Created by: Mustapha Elasri
"""

import sys
import os
import json
import time
import requests
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from client_finder.config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    OPENROUTER_API_KEY,
    AI_MODEL,
    SENDER_NAME,
    MY_SERVICES,
)
from client_finder.notifier import send_telegram
from client_finder.tracker import stats_to_telegram, check_opens
from client_finder.inbox import check_replies, notify_new_replies
from client_finder.sender import send_email

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
_offset = 0


def _send_message(text: str, chat_id: str = None):
    """Send message to Telegram."""
    if not chat_id:
        chat_id = TELEGRAM_CHAT_ID
    url = f"{TELEGRAM_API}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }, timeout=10)


def _get_updates():
    """Get new messages from Telegram."""
    global _offset
    url = f"{TELEGRAM_API}/getUpdates"
    params = {"offset": _offset, "timeout": 5}
    try:
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        if data.get("ok"):
            for update in data.get("result", []):
                _offset = update["update_id"] + 1
                yield update
    except Exception:
        pass


def _ai_generate(prompt: str) -> str:
    """Generate AI response."""
    if not OPENROUTER_API_KEY:
        return "AI not configured."

    services_text = "\n".join(f"- {s}" for s in MY_SERVICES)

    system_prompt = f"""You are Mustapha Elasri, a Python bot developer.
You reply to client emails professionally but casually — like a real person.

Your services:
{services_text}

Rules:
- Keep replies short (under 80 words)
- Be friendly and helpful
- If they ask about price, give a range ($200-$500)
- If they ask about timeline, say "1-5 days"
- If interested, suggest a quick call
- Don't use emojis
- Don't be pushy"""

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": AI_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
                "max_tokens": 300,
            },
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"AI error: {e}"

    return "Failed to generate reply."


def _handle_message(text: str, chat_id: str):
    """Handle incoming Telegram message."""
    text_lower = text.strip().lower()

    if text_lower == "/start":
        _send_message(
            f"<b>Client Finder Bot</b>\n\n"
            f"Hey {SENDER_NAME}!\n\n"
            f"<b>Commands:</b>\n"
            f"/inbox — Check client replies\n"
            f"/stats — Email stats\n"
            f"/opens — Check email opens\n"
            f"/services — List your services\n\n"
            f"<b>Reply to client:</b>\n"
            f"reply: &lt;their message&gt;\n\n"
            f"<b>Send email:</b>\n"
            f"send: email@example.com | Subject | Body",
            chat_id,
        )
        return

    if text_lower == "/stats":
        stats_to_telegram()
        return

    if text_lower == "/opens":
        _send_message("Checking opens...", chat_id)
        new_opens = check_opens()
        if new_opens:
            _send_message(f"Found {len(new_opens)} new opens!", chat_id)
        else:
            _send_message("No new opens.", chat_id)
        return

    if text_lower == "/inbox":
        _send_message("Checking Gmail for replies...", chat_id)
        replies = check_replies()

        if not replies:
            _send_message("No new replies.", chat_id)
            return

        for i, reply in enumerate(replies[:10]):
            _send_message(f"Generating reply for {reply['name']}...", chat_id)

            ai_reply = _ai_generate(
                f"A client replied to my cold email. Their message:\n\n"
                f'"{reply["body"]}"\n\n'
                f"Write a short, friendly reply."
            )

            msg = (
                f"<b>Reply {i+1}/{len(replies)}</b>\n\n"
                f"From: {reply['name']}\n"
                f"Email: {reply['email']}\n"
                f"Subject: {reply['subject']}\n\n"
                f"<b>Their message:</b>\n{reply['body'][:500]}\n\n"
                f"<b>Suggested reply (copy this):</b>\n\n"
                f"{ai_reply}\n\n"
                f"To edit: reply: &lt;your modified response&gt;"
            )
            _send_message(msg, chat_id)
            time.sleep(1)
        return

    if text_lower == "/services":
        services = "\n".join(f"  {s}" for s in MY_SERVICES)
        _send_message(f"<b>Your Services:</b>\n\n{services}", chat_id)
        return

    if text_lower.startswith("reply:"):
        client_message = text[6:].strip()
        if not client_message:
            _send_message("Send: reply: &lt;client message&gt;", chat_id)
            return

        _send_message("Thinking...", chat_id)

        ai_reply = _ai_generate(
            f"A client replied to my cold email. Their message:\n\n"
            f'"{client_message}"\n\n'
            f"Write a short, friendly reply."
        )

        _send_message(
            f"<b>Client said:</b>\n{client_message}\n\n"
            f"<b>Your reply (copy this):</b>\n\n"
            f"{ai_reply}",
            chat_id,
        )
        return

    if text_lower.startswith("send:"):
        parts = text[5:].strip().split("|")
        if len(parts) < 3:
            _send_message(
                "Format: send: email@example.com | Subject | Body",
                chat_id,
            )
            return

        to_email = parts[0].strip()
        subject = parts[1].strip()
        body = parts[2].strip()

        _send_message(f"Sending to {to_email}...", chat_id)

        success = send_email(to_email, subject, body)
        if success:
            _send_message(f"Email sent to {to_email}!", chat_id)
        else:
            _send_message(f"Failed to send to {to_email}", chat_id)
        return

    _send_message("Unknown command. Send /start for help.", chat_id)


def run_bot():
    """Run the Telegram bot."""
    print("=" * 50)
    print("  TELEGRAM BOT RUNNING")
    print("  https://t.me/client_finder12bot")
    print("=" * 50)
    print()
    print("  Commands:")
    print("    /inbox — Check client replies")
    print("    /stats — Email stats")
    print("    /opens — Check email opens")
    print("    reply: <message> — Get AI reply")
    print("    send: email | subject | body — Send email")
    print()
    print("  Press Ctrl+C to stop")
    print()

    _send_message(
        f"<b>Client Finder Bot Online</b>\n\n"
        f"Send /start for commands.\n"
        f"Send /inbox to check replies.",
    )

    while True:
        try:
            for update in _get_updates():
                message = update.get("message", {})
                chat_id = str(message.get("chat", {}).get("id", ""))
                text = message.get("text", "")

                if chat_id == TELEGRAM_CHAT_ID and text:
                    print(f"  Received: {text[:50]}...")
                    _handle_message(text, chat_id)

            time.sleep(1)

        except KeyboardInterrupt:
            print("\n  Bot stopped.")
            _send_message("Bot stopped.", TELEGRAM_CHAT_ID)
            break
        except Exception as e:
            print(f"  Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    run_bot()
