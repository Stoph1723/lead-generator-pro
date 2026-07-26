<div align="center">

# Lead Generator Pro

**Free, open-source business lead scraper + cold email outreach tool.**

**Find businesses → Extract emails → Write AI emails → Send with tracking.**

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey?style=for-the-badge)
![Stars](https://img.shields.io/github/stars/Stoph1723/lead-generator-pro?style=for-the-badge&color=yellow)
![Forks](https://img.shields.io/github/forks/Stoph1723/lead-generator-pro?style=for-the-badge&color=blue)

</div>

---

## Screenshots

### Interactive Menu
![Interactive Menu](screenshots/menu.png)

### Scraping in Progress
![Scraping Progress](screenshots/scraping.png)

### Excel Dashboard
![Excel Dashboard](screenshots/dashboard.png)

### Excel Leads Sheet
![Excel Leads Sheet](screenshots/leads.png)

---

## What Is This?

Two tools in one:

1. **Lead Generator** — Scrapes business data from 8 sources, extracts emails, exports to Excel
2. **Client Finder** — Finds businesses via Google Maps API, writes personalized AI emails, sends via Brevo with open tracking

### What You Get

| Feature | Description |
|---------|-------------|
| **Google Maps Search** | Serper API — real Google Maps data (name, address, phone, website, reviews) |
| **Email Extraction** | 64 contact paths, MX validation, pattern guessing, domain language detection |
| **AI Email Writing** | Groq/LLaMA — personalized cold emails in any language |
| **Email Sending** | Brevo API — 300 free emails/day with open/click tracking |
| **Telegram Alerts** | Get notified when emails are sent |
| **Website List Mode** | Paste your own websites, crawl for emails |
| **Telegram Chatbot** | AI assistant on Telegram |
| **Cloudflare WARP** | Bypass network blocks |

---

## Quick Start

### 1. Install

```bash
git clone https://github.com/Stoph1723/lead-generator-pro.git
cd lead-generator-pro
pip install -r requirements.txt
```

### 2. Set Up API Keys

```bash
# Copy the template
cp config_template.py client_finder/config.py

# Edit with your keys (get free accounts at each service)
```

**Free API keys you need:**

| Service | What For | Free Limit | Sign Up |
|---------|----------|------------|---------|
| **Groq** | AI email writing | Unlimited | [console.groq.com](https://console.groq.com) |
| **Serper** | Google Maps search | 2500 searches | [serper.dev](https://serper.dev) |
| **Brevo** | Email sending | 300/day | [app.brevo.com](https://app.brevo.com) |
| **Telegram** | Notifications | Unlimited | [t.me/BotFather](https://t.me/BotFather) |

**Optional (alternative AI providers):**

| Service | What For | Free Limit | Sign Up |
|---------|----------|------------|---------|
| **OpenRouter** | AI fallback | 50/day (1000 with $10) | [openrouter.ai](https://openrouter.ai) |
| **Google Gemini** | AI alternative | 1500/day (needs billing) | [aistudio.google.com](https://aistudio.google.com/apikey) |

**Alternative SMTP providers (instead of Brevo):**

| Provider | Free Limit | Notes |
|----------|------------|-------|
| **Brevo** | 300/day | Recommended — tracking included |
| **SendGrid** | 100/day | Popular, good deliverability |
| **Mailgun** | 500/month | Good for developers |
| **Amazon SES** | Pay per email | $0.10 per 1000 emails |
| **Gmail SMTP** | 500/day | Use App Password, less reliable |

To use a different SMTP, edit `sender.py` and replace the Brevo API calls with your provider's API.

### 3. Run

```bash
# Interactive menu
python -m client_finder.main

# Or direct Google Maps search
python -m client_finder.main --query "dentist" --location "Los Angeles"
```

---

## Client Finder Modes

| Mode | Description |
|------|-------------|
| **[1] Scrape Mode** | Find businesses from multiple sources → emails → AI write → send |
| **[2] Dork Mode** | Find emails via search engine @ operator |
| **[3] Quick Dork** | One-click dork with default settings |
| **[4] View Stats** | Check email open rates |
| **[5] Check Opens** | See who opened your emails |
| **[6] WARP VPN** | Bypass network blocks |
| **[7] Website List** | Crawl your own list of websites |
| **[8] Telegram Bot** | AI chatbot on Telegram |
| **[9] Google Maps** | Serper API — direct Google Maps data |

---

## Google Maps Mode (Recommended)

The fastest way to find leads:

```
City: Los Angeles
Category: dental
Max: 10

[1/4] Searching Google Maps... Found 10 businesses
[2/4] Finding emails... Found 9/10
[3/4] Writing AI emails... Done
[4/4] Sending... Sent 9 emails
```

**Returns:** Business name, address, phone, website, rating, reviews, type, description, hours.

---

## Email Features

- **64 contact paths** crawled per website
- **MX record validation** before sending
- **Domain language detection** — writes emails in French, Spanish, German, etc.
- **Signature adapts** — Best → Cordialement, etc.
- **Junk email filtering** — noreply, postmaster, placeholder emails rejected
- **Open tracking** — Brevo API tracks who opens your emails
- **Deduplication** — won't send to the same email twice

---

## Architecture

```
lead-generator-pro/
├── lead_generator/          # Public scraper (no API keys needed)
│   ├── main.py              # CLI + interactive
│   ├── config.py            # Settings
│   └── scrapers/            # 8 data sources
├── client_finder/           # Cold email tool (needs API keys)
│   ├── main.py              # 8 menu modes
│   ├── config_template.py   # Copy to config.py with your keys
│   ├── serper.py            # Google Maps API
│   ├── emails.py            # Email extraction
│   ├── ai_writer.py         # AI email writing (Groq)
│   ├── sender.py            # Brevo email sending
│   ├── tracker.py           # Open/click tracking
│   ├── chatbot.py           # Telegram AI bot
│   └── dorker.py            # Search engine dorking
└── screenshots/             # UI screenshots
```

---

## Requirements

- Python 3.10+
- Windows / macOS / Linux

```
beautifulsoup4>=4.12.0
lxml>=5.0.0
requests>=2.32.0
openpyxl>=3.1.0
dnspython>=2.0.0
```

---

## Disclaimer

This tool is for **educational and legitimate business purposes only**. Users are responsible for complying with the terms of service of any website they scrape. The author is not responsible for any misuse.

---

## License

**CC BY-NC 4.0** — Free to use, share, and adapt with attribution. No commercial use.

---

## Credits

Created by [Mustapha Elasri](https://github.com/Stoph1723)

If you use this project, please credit:
> Lead Generator Pro by Mustapha Elasri — https://github.com/Stoph1723/lead-generator-pro
