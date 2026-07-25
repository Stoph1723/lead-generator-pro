"""
AI Email Writer
===============
Uses OpenRouter free AI to write personalized cold emails.
Only mentions services you actually offer.

Created by: Mustapha Elasri
"""

import json
import requests
from typing import Dict, Optional

from client_finder.config import (
    OPENROUTER_API_KEY,
    SENDER_NAME,
    SENDER_TITLE,
    SENDER_PORTFOLIO,
    MY_SERVICES,
)

FREE_MODELS = [
    "meta-llama/llama-3.1-8b-instruct:free",
    "qwen/qwen-2-7b-instruct:free",
    "google/gemma-2-9b-it:free",
    "mistralai/mistral-7b-instruct:free",
]


def write_cold_email(business: Dict, model: str = None) -> Optional[Dict]:
    """Write a personalized cold email for a business using AI.
    Returns dict with 'subject' and 'body', or None on failure."""

    if not OPENROUTER_API_KEY:
        print("  [!] No OpenRouter API key set in config.py")
        return _fallback_email(business)

    biz_name = business.get("name", "your business")
    biz_category = business.get("category", "business")
    biz_city = business.get("city", "")
    biz_country = business.get("country", "")
    location = f"{biz_city}, {biz_country}".strip(", ")

    services_text = "\n".join(f"- {s}" for s in MY_SERVICES)

    prompt = f"""Write a short, professional cold email to {biz_name} ({biz_category} in {location}).

Rules:
- Subject line: short, catchy, no spam words
- Greeting: use the business name
- First line: mention their business and location
- Body: list 3-4 relevant services from the list below (pick what fits their business type)
- Call to action: ask them to reply
- Signature: use the name and title below
- Keep it under 150 words
- Do NOT use emojis
- Do NOT make up services not in the list
- Format as JSON: {{"subject": "...", "body": "..."}}

Services I offer:
{services_text}

My name: {SENDER_NAME}
My title: {SENDER_TITLE}
My portfolio: {SENDER_PORTFOLIO}"""

    for model_name in FREE_MODELS:
        if model:
            model_name = model
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 500,
                },
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                content = content.strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[1]
                    content = content.rsplit("```", 1)[0]
                result = json.loads(content)
                if "subject" in result and "body" in result:
                    return result
            else:
                continue
        except Exception:
            continue
        if model:
            break

    print(f"  [!] AI failed for {biz_name}, using fallback")
    return _fallback_email(business)


def _fallback_email(business: Dict) -> Dict:
    """Fallback email if AI fails."""
    biz_name = business.get("name", "your business")
    biz_category = business.get("category", "business")

    subject = f"Automation bots for {biz_name}"
    body = f"""Hi {biz_name} team,

I found your {biz_category} business and wanted to reach out.

I'm a Python developer specializing in automation bots. I can build:

- Lead scraping bots to find new customers
- WhatsApp/Telegram bots for customer support
- Email automation and data enrichment
- ChatGPT/Claude AI integration

I work fast and deliver clean, working code.

Interested? Just reply to this email.

Best,
{SENDER_NAME}
{SENDER_TITLE}
{SENDER_PORTFOLIO}"""

    return {"subject": subject, "body": body}
