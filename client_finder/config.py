"""
Client Finder Configuration
==========================
Enter your free API keys here.

Get them:
- OpenRouter: https://openrouter.ai/keys
- Brevo: https://app.brevo.com/account/keys/api
- Telegram Bot: @BotFather on Telegram
- Telegram Chat ID: @userinfobot on Telegram

Created by: Mustapha Elasri
GitHub: https://github.com/Stoph1723/lead-generator-pro
"""

# ===== YOUR API KEYS (all free) =====

# OpenRouter (free AI for writing emails)
# Sign up: https://openrouter.ai/keys
OPENROUTER_API_KEY = ""

# Brevo SMTP (free 300 emails/day)
# Sign up: https://app.brevo.com/account/keys/api
BREVO_SMTP_KEY = ""
BREVO_LOGIN = ""  # Your Brevo login email

# Telegram Bot (for notifications)
# Create bot: https://t.me/BotFather
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""  # Your chat ID from @userinfobot

# ===== EMAIL SETTINGS =====

# Your info (used in email signatures)
SENDER_NAME = "Mustapha Elasri"
SENDER_TITLE = "Python Bot Developer"
SENDER_PORTFOLIO = "https://github.com/Stoph1723/lead-generator-pro"

# Brevo sender email (must be verified in Brevo)
SENDER_EMAIL = ""  # Your verified Brevo email
SENDER_NAME_EMAIL = "Mustapha Elasri"

# ===== YOUR 12 SERVICES =====
# Only these are mentioned in cold emails

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

# ===== SCRAPING SETTINGS =====

MAX_BUSINESSES = 50  # Max businesses per search
MAX_EMAILS_TO_SEND = 30  # Max cold emails per run (Brevo free limit: 300/day)
SEARCH_WORKERS = 4  # Parallel search threads
ENRICHMENT_WORKERS = 8  # Parallel enrichment threads

# ===== DELAYS =====

DELAY_BETWEEN_EMAILS = 2  # Seconds between sending emails (avoid spam)
DELAY_BETWEEN_REQUESTS = 1  # Seconds between requests
