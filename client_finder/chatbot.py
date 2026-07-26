"""
Telegram AI Chatbot
===================
Conversational Telegram bot that knows about your client finder tool.
Powered by OpenRouter AI with full context about leads, emails, and stats.

Created by: Mustapha Elasri
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from client_finder.config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    OPENROUTER_API_KEY,
    GEMINI_API_KEY,
    GROQ_API_KEY,
    AI_MODEL,
    AI_PROVIDER,
    SENDER_NAME,
    SENDER_EMAIL,
    MY_SERVICES,
    BREVO_API_KEY,
)
from client_finder.tracker import get_stats, _load_tracking
from client_finder.notifier import send_telegram

POLL_INTERVAL = 2
TRACKING_FILE = os.path.join(os.path.dirname(__file__), "..", "output", "tracking.json")
RUNS_DIR = os.path.join(os.path.dirname(__file__), "..", "output")


def _get_system_context() -> str:
    """Build system context with all info about the tool."""
    stats = get_stats()
    tracking = _load_tracking()

    recent_sent = tracking.get("sent", [])[-10:]
    recent_lines = []
    for s in recent_sent:
        opened = "✓ opened" if s.get("opened") else "not opened"
        recent_lines.append(f"  • {s.get('name', 'Unknown')} <{s.get('email', '')}> — {opened}")

    recent_opens = [s for s in tracking.get("sent", []) if s.get("opened")][-5:]
    open_lines = []
    for s in recent_opens:
        open_lines.append(f"  • {s.get('name', 'Unknown')} — opened {s.get('open_count', 1)}x")

    services_text = "\n".join(f"  • {s}" for s in MY_SERVICES)

    output_files = []
    if os.path.exists(RUNS_DIR):
        for f in sorted(os.listdir(RUNS_DIR), reverse=True)[:5]:
            if f.endswith(".json"):
                output_files.append(f)

    context = f"""You are the Client Finder AI Assistant. You help {SENDER_NAME} manage their cold email outreach tool.

YOUR IDENTITY:
- You are a helpful, friendly AI assistant for {SENDER_NAME}
- You are powered by AI and know everything about this tool
- You speak in a casual, friendly tone
- Keep responses short and to the point
- Use emojis sparingly (only when appropriate)

TOOL CAPABILITIES:
- Scrape businesses from Google Maps
- Find emails from business websites
- Write personalized cold emails using AI
- Send emails via Brevo API (300/day free)
- Track email opens
- Telegram notifications
- Website list crawling
- Business type classification

SERVICES {SENDER_NAME} OFFERS:
{services_text}

CURRENT STATS:
- Emails sent: {stats['sent']}
- Emails opened: {stats['opened']} ({stats['open_rate']}%)
- Emails replied: {stats['replied']}
- Not opened: {stats['not_opened']}

RECENT EMAILS SENT:
{chr(10).join(recent_lines) if recent_lines else "  No emails sent yet."}

RECENT OPENS:
{chr(10).join(open_lines) if open_lines else "  No opens yet."}

RECENT OUTPUT FILES:
{chr(10).join(f'  • {f}' for f in output_files) if output_files else "  No output files yet."}

BREVO API: {'Configured (300 emails/day)' if BREVO_API_KEY else 'Not configured'}
SENDER EMAIL: {SENDER_EMAIL}

RULES:
- If asked about stats, use the data above
- If asked about how to use the tool, explain the modes (Scrape, Dork, Website List)
- If asked to send emails, remind them to use the tool's menu
- If asked about a specific email, check the tracking data
- If asked to do something outside your scope, politely explain what you can help with
- Never share API keys or sensitive config
- Be concise — no long paragraphs
"""
    return context


def _get_ai_response(user_message: str, chat_history: List[Dict]) -> str:
    """Get AI response from Gemini, Groq, or OpenRouter with retry on rate limit."""
    if not GEMINI_API_KEY and not GROQ_API_KEY and not OPENROUTER_API_KEY:
        return "AI is not configured. Set GROQ_API_KEY in config.py."

    system_context = _get_system_context()

    for attempt in range(3):
        try:
            if AI_PROVIDER == "gemini" and GEMINI_API_KEY:
                full_prompt = system_context + "\n\n" + "\n".join(
                    f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
                    for m in chat_history[-20:]
                ) + f"\n\nUser: {user_message}"

                response = requests.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{AI_MODEL}:generateContent?key={GEMINI_API_KEY}",
                    headers={"Content-Type": "application/json"},
                    json={"contents": [{"parts": [{"text": full_prompt}]}]},
                    timeout=30,
                )

                if response.status_code == 429:
                    wait = (attempt + 1) * 5
                    time.sleep(wait)
                    continue

                if response.status_code == 200:
                    data = response.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return f"AI error (status {response.status_code}). Try again later."
            elif AI_PROVIDER == "groq" and GROQ_API_KEY:
                messages = [{"role": "system", "content": system_context}]
                messages.extend(chat_history[-20:])
                messages.append({"role": "user", "content": user_message})

                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": AI_MODEL,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 500,
                    },
                    timeout=30,
                )

                if response.status_code == 429:
                    wait = (attempt + 1) * 5
                    time.sleep(wait)
                    continue

                if response.status_code == 200:
                    data = response.json()
                    if "choices" in data and data["choices"]:
                        return data["choices"][0]["message"]["content"].strip()
                    return "AI returned empty response."
                return f"AI error (status {response.status_code}). Try again later."
            else:
                messages = [{"role": "system", "content": system_context}]
                messages.extend(chat_history[-20:])
                messages.append({"role": "user", "content": user_message})

                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": AI_MODEL,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 500,
                    },
                    timeout=30,
                )

                if response.status_code == 429:
                    wait = (attempt + 1) * 5
                    time.sleep(wait)
                    continue

                if response.status_code == 200:
                    data = response.json()
                    if "choices" in data and data["choices"]:
                        content = data["choices"][0]["message"]["content"]
                        return content.strip()
                    return "Sorry, AI returned an empty response. Try again."
                return f"AI error (status {response.status_code}). Try again later."
        except Exception as e:
            return f"AI connection error: {e}"

    return "Rate limited. Please wait a moment and try again."


def _handle_command(command: str, args: str) -> Optional[str]:
    """Handle bot commands."""
    if command == "/stats" or command == "/status":
        stats = get_stats()
        return (
            f"📊 <b>Email Stats</b>\n\n"
            f"Sent: {stats['sent']}\n"
            f"Opened: {stats['opened']} ({stats['open_rate']}%)\n"
            f"Replied: {stats['replied']}\n"
            f"Not opened: {stats['not_opened']}\n"
        )

    elif command == "/emails":
        tracking = _load_tracking()
        sent = tracking.get("sent", [])[-10:]
        if not sent:
            return "No emails sent yet."
        lines = []
        for s in sent:
            opened = "✓" if s.get("opened") else "✗"
            lines.append(f"{opened} {s.get('name', 'Unknown')} — {s.get('email', '')}")
        return f"📧 <b>Recent Emails</b>\n\n" + "\n".join(lines)

    elif command == "/opens":
        tracking = _load_tracking()
        opens = [s for s in tracking.get("sent", []) if s.get("opened")][-10:]
        if not opens:
            return "No opens yet."
        lines = []
        for s in opens:
            lines.append(f"✓ {s.get('name', 'Unknown')} — opened {s.get('open_count', 1)}x")
        return f"👀 <b>Opened Emails</b>\n\n" + "\n".join(lines)

    elif command == "/help":
        return (
            f"🤖 <b>Client Finder Bot</b>\n\n"
            f"I can help you with:\n\n"
            f"• Ask me anything about your leads\n"
            f"• Check email stats and opens\n"
            f"• Get help using the tool\n"
            f"• Talk about your cold email strategy\n\n"
            f"<b>Commands:</b>\n"
            f"/stats — Email statistics\n"
            f"/emails — Recent emails sent\n"
            f"/opens — Who opened your emails\n"
            f"/help — This message\n\n"
            f"Just chat with me naturally!"
        )

    elif command == "/run":
        return "Use the tool's menu to start a run. I can't start runs from here, but I can help you plan one!"

    return None


def _get_updates(offset: int = 0) -> List[Dict]:
    """Poll Telegram for new messages."""
    if not TELEGRAM_BOT_TOKEN:
        return []
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        params = {"offset": offset, "timeout": 5, "allowed_updates": '["message"]'}
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("ok"):
                return data.get("result", [])
    except Exception:
        pass
    return []


def _send_reply(chat_id: int, text: str):
    """Send a reply to Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }, timeout=10)
    except Exception:
        pass


def start_bot():
    """Start the Telegram chatbot. Runs forever."""
    print(f"\n  🤖 Telegram Bot started!")
    print(f"  Chat with {SENDER_NAME}'s bot on Telegram")
    print(f"  Press Ctrl+C to stop\n")

    chat_history = []
    last_update_id = 0

    if TELEGRAM_CHAT_ID and TELEGRAM_CHAT_ID.isdigit():
        _send_reply(int(TELEGRAM_CHAT_ID), "🤖 <b>Client Finder Bot Online!</b>\n\nAsk me anything about your leads, emails, or the tool.\nType /help for commands.")

    print("  Listening for messages...")
    while True:
        try:
            updates = _get_updates(last_update_id)
            for update in updates:
                last_update_id = update["update_id"] + 1
                msg = update.get("message", {})
                chat_id = msg.get("chat", {}).get("id")
                text = msg.get("text", "").strip()
                from_user = msg.get("from", {}).get("first_name", "User")

                if not text or not chat_id:
                    continue

                if str(chat_id) != str(TELEGRAM_CHAT_ID):
                    _send_reply(chat_id, "Access denied.")
                    continue

                print(f"  [{from_user}] {text}")

                if text.startswith("/"):
                    parts = text.split(" ", 1)
                    command = parts[0].lower()
                    args = parts[1] if len(parts) > 1 else ""
                    reply = _handle_command(command, args)
                    if reply:
                        _send_reply(chat_id, reply)
                        print(f"  [Bot] {reply[:80]}...")
                    else:
                        _send_reply(chat_id, f"Unknown command: {command}\nType /help to see available commands.")
                    continue

                chat_history.append({"role": "user", "content": text})
                reply = _get_ai_response(text, chat_history)
                chat_history.append({"role": "assistant", "content": reply})

                if len(chat_history) > 40:
                    chat_history = chat_history[-20:]

                _send_reply(chat_id, reply)
                print(f"  [Bot] {reply[:80]}...")

            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print("\n  Bot stopped.")
            if TELEGRAM_CHAT_ID and TELEGRAM_CHAT_ID.isdigit():
                _send_reply(int(TELEGRAM_CHAT_ID), "🤖 Bot going offline. See you!")
            break
        except Exception as e:
            print(f"  [!] Bot error: {e}")
            time.sleep(5)
