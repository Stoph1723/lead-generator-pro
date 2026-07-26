"""
Client Finder Configuration
==========================
Copy this file to config.py and add your API keys.

Setup:
  cp config_template.py config.py
  # Then edit config.py with your keys

All services below have FREE tiers. No credit card needed.

Created by: Mustapha Elasri
GitHub: https://github.com/Stoph1723/lead-generator-pro
"""

import subprocess
import shutil

# ===== CLOUDFLARE WARP =====
# Optional — bypass network blocks. Install from https://1.1.1.1/

WARP_PROXY_PORT = 40000
WARP_PROXY_URL = f"socks5://127.0.0.1:{WARP_PROXY_PORT}"


def _find_warp_cli():
    """Find warp-cli executable."""
    path = shutil.which("warp-cli")
    if path:
        return path
    default = r"C:\Program Files\Cloudflare\Cloudflare WARP\warp-cli.exe"
    import os
    if os.path.exists(default):
        return default
    return None


def is_warp_installed():
    return _find_warp_cli() is not None


def get_warp_status():
    cli = _find_warp_cli()
    if not cli:
        return "NotInstalled"
    try:
        result = subprocess.run([cli, "status"], capture_output=True, text=True, timeout=5)
        output = result.stdout + result.stderr
        if "Connected" in output:
            return "Connected"
        elif "Disconnected" in output:
            return "Disconnected"
        return "Unknown"
    except Exception:
        return "Unknown"


def connect_warp():
    cli = _find_warp_cli()
    if not cli:
        return False, "WARP not installed. Download from https://1.1.1.1/"
    try:
        subprocess.run([cli, "--accept-tos", "registration", "new"], capture_output=True, timeout=10)
        subprocess.run([cli, "--accept-tos", "mode", "warp"], capture_output=True, timeout=5)
        result = subprocess.run([cli, "--accept-tos", "connect"], capture_output=True, text=True, timeout=10)
        if "Success" in result.stdout + result.stderr:
            return True, "Connected to WARP"
        return False, f"Connect failed: {(result.stdout + result.stderr).strip()}"
    except Exception as e:
        return False, f"Error: {e}"


def setup_warp_proxy():
    cli = _find_warp_cli()
    if not cli:
        return False, "WARP not installed"
    try:
        subprocess.run([cli, "--accept-tos", "mode", "proxy"], capture_output=True, timeout=5)
        subprocess.run([cli, "--accept-tos", "proxy", "port", str(WARP_PROXY_PORT)], capture_output=True, timeout=5)
        result = subprocess.run([cli, "--accept-tos", "connect"], capture_output=True, text=True, timeout=10)
        output = result.stdout + result.stderr
        if "Success" in output or "Connected" in output:
            return True, f"WARP proxy running on {WARP_PROXY_URL}"
        return False, f"Proxy setup failed: {output.strip()}"
    except Exception as e:
        return False, f"Error: {e}"


def disconnect_warp():
    cli = _find_warp_cli()
    if cli:
        try:
            subprocess.run([cli, "disconnect"], capture_output=True, timeout=5)
        except Exception:
            pass


def get_warp_proxies():
    return {"http": WARP_PROXY_URL, "https": WARP_PROXY_URL}

# ===== AI PROVIDERS =====
# At least one is required for AI email writing.
# Groq is recommended — free, fast, no rate limits.

# Groq (RECOMMENDED — free, fast inference)
# Sign up: https://console.groq.com
# Models: llama-3.3-70b-versatile, llama-3.1-8b-instant, mixtral-8x7b-32768
GROQ_API_KEY = ""

# OpenRouter (fallback — 50 free requests/day)
# Sign up: https://openrouter.ai
OPENROUTER_API_KEY = ""

# Google Gemini (alternative — 1500 free requests/day, needs billing enabled)
# Sign up: https://aistudio.google.com/apikey
GEMINI_API_KEY = ""

# ===== EMAIL PROVIDER =====
# Brevo is recommended — free 300 emails/day with tracking.
# You can also use SendGrid, Mailgun, Amazon SES, or Gmail SMTP.
# To use a different provider, edit sender.py.

# Brevo (RECOMMENDED — free 300 emails/day, open tracking)
# Sign up: https://app.brevo.com/account/keys/api
BREVO_SMTP_KEY = ""
BREVO_LOGIN = ""  # Your Brevo SMTP login (from Brevo dashboard)
BREVO_API_KEY = ""  # Brevo API key for tracking (Settings → API Keys)

# ===== SEARCH ENGINE =====
# Serper.dev — Google Maps API (free 2500 searches)
# Sign up: https://serper.dev
SERPER_API_KEY = ""

# ===== TELEGRAM NOTIFICATIONS =====
# Get real-time alerts when emails are sent.
# Create bot: https://t.me/BotFather → /newbot → copy token
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""  # Send /start to your bot, then check https://api.telegram.org/bot<TOKEN>/getUpdates

# ===== AI MODEL =====
# Which AI provider to use: "groq", "openrouter", or "gemini"

AI_PROVIDER = "groq"
AI_MODEL = "llama-3.3-70b-versatile"

# ===== EMAIL SETTINGS =====
# These appear in the cold emails sent to businesses.

SENDER_NAME = "Your Name"
SENDER_TITLE = ""
SENDER_PORTFOLIO = "See what I've built: https://github.com/YourUsername/lead-generator-pro"
SENDER_EMAIL = "your@email.com"  # Must be verified in Brevo
SENDER_NAME_EMAIL = "Your Name"

# Gmail IMAP (for reading replies — optional)
# Enable IMAP: Gmail → Settings → See all settings → Forwarding and POP/IMAP → Enable IMAP
# App Password: https://myaccount.google.com/apppasswords → Create → Mail
GMAIL_IMAP_PASSWORD = ""

# ===== YOUR SERVICES =====
# These are listed in cold emails. Edit to match what YOU offer.

MY_SERVICES = [
    "Lead scraping bots — scrape Google Maps, directories, any website",
    "Email finders — extract emails from any website",
    "Data enrichment — add emails, phones, social links to your data",
    "Telegram bots — customer service, FAQ, notifications",
    "Discord bots — moderation, music, welcome, games",
    "WhatsApp bots — auto-reply, order tracking, support",
    "Facebook Messenger bots — auto-reply, customer support",
    "Twitch bots — chat moderation, alerts, commands",
    "Slack bots — notifications, polls, workplace automation",
    "YouTube bots — subscriber alerts, comment management",
    "Email bots — auto-reply, email parsing, bulk sender",
    "ChatGPT/Claude integration — add AI chat to any bot",
]

# ===== SETTINGS =====

MAX_BUSINESSES = 200
MAX_EMAILS_TO_SEND = 200
SEARCH_WORKERS = 4
ENRICHMENT_WORKERS = 8
DELAY_BETWEEN_EMAILS = 2
DELAY_BETWEEN_REQUESTS = 1

# Business types to EXCLUDE (filtered out automatically)
EXCLUDE_TYPES = [
    "bar", "pub", "tavern", "nightclub", "lounge",
    "casino", "gambling", "betting", "bookmaker",
    "strip club", "adult", "xxx", "erotic", "escort",
    "funeral", "cemetery", "crematorium",
    "prison", "jail", "detention",
    "strip", "burlesque", "hookah", "shisha",
    "brewery", "distillery", "winery",
    "hookah lounge", "vape shop", "cannabis",
    "marijuana", "dispensary",
    "massage parlor", "brothel",
]
