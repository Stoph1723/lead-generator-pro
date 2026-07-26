"""
AI Email Writer
===============
Uses OpenRouter free AI to write personalized cold emails.
Reads business websites for extra personalization.

Created by: Mustapha Elasri
"""

import sys
import os
import re
import json
import time
import requests
from typing import Dict, Optional
from urllib.parse import urljoin

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bs4 import BeautifulSoup
from lead_generator.scrapers.crawler import AntiBypassCrawler

from client_finder.config import (
    OPENROUTER_API_KEY,
    GEMINI_API_KEY,
    GROQ_API_KEY,
    AI_MODEL,
    AI_PROVIDER,
    SENDER_NAME,
    SENDER_TITLE,
    SENDER_PORTFOLIO,
    MY_SERVICES,
)


def _read_website(website: str) -> str:
    """Read a business website and extract key info for the AI."""
    if not website:
        return ""

    if not website.startswith("http"):
        website = "https://" + website

    crawler = AntiBypassCrawler(timeout=10, max_retries=1, fast_mode=True)
    info_parts = []

    pages_to_check = [
        ("", "homepage"),
        ("/about", "about page"),
        ("/about-us", "about us"),
        ("/services", "services"),
        ("/our-services", "our services"),
    ]

    for path, label in pages_to_check:
        url = website.rstrip("/") + path
        try:
            html = crawler.fetch(url)
            if not html:
                continue

            if isinstance(html, bytes):
                html = html.decode("utf-8", errors="replace")

            if "<html" not in html.lower()[:500]:
                continue

            soup = BeautifulSoup(html, "lxml")

            for tag in soup.select("script, style, nav, footer, header"):
                tag.decompose()

            text = soup.get_text(" ", strip=True)
            text = re.sub(r'\s+', ' ', text)

            if len(text) > 50:
                info_parts.append(f"[{label}]: {text[:800]}")

            if len(info_parts) >= 3:
                break

        except Exception:
            continue

    return "\n\n".join(info_parts)[:2000]


def _detect_language(text: str) -> str:
    """Detect language using langdetect library."""
    try:
        from langdetect import detect
        lang_code = detect(text)
        return lang_code
    except Exception:
        return "en"


def _detect_language_from_domain(email: str) -> str:
    """Detect language from email domain TLD."""
    tld_map = {
        ".fr": "fr", ".de": "de", ".es": "es", ".it": "it",
        ".pt": "pt", ".nl": "nl", ".pl": "pl", ".ru": "ru",
        ".tr": "tr", ".jp": "ja", ".cn": "zh",
        ".kr": "ko", ".br": "pt", ".mx": "es", ".ar": "es",
        ".at": "de", ".ch": "de", ".be": "fr", ".ca": "fr",
        ".uk": "en", ".au": "en", ".in": "en",
        ".sa": "ar", ".ae": "ar", ".eg": "ar", ".ma": "fr",
        ".se": "en", ".no": "en", ".dk": "en", ".fi": "en",
        ".cz": "de", ".sk": "de", ".hu": "en", ".ro": "en",
    }
    domain = email.split("@")[-1].lower() if "@" in email else ""
    for tld, lang in tld_map.items():
        if domain.endswith(tld):
            return lang
    return "en"


def write_cold_email(business: Dict) -> Optional[Dict]:
    """Write a personalized cold email using AI. Auto-detects language from website."""
    from client_finder.config import GROQ_API_KEY, GEMINI_API_KEY, AI_PROVIDER
    if not GROQ_API_KEY and not GEMINI_API_KEY and not OPENROUTER_API_KEY:
        print("  [!] No AI API key set in config.py")
        return _fallback_email(business)

    biz_name = business.get("name", "your business")
    biz_category = business.get("category", "business")
    biz_city = business.get("city", "")
    biz_country = business.get("country", "")
    biz_website = business.get("website", "")
    biz_email = business.get("email", "")
    location = f"{biz_city}, {biz_country}".strip(", ")

    website_info = ""
    detected_lang = "en"
    if biz_website:
        print(f"  Reading {biz_name} website...")
        website_info = _read_website(biz_website)
        if website_info:
            detected_lang = _detect_language(website_info)
            if detected_lang != "en":
                print(f"    Detected language: {detected_lang}")

    if detected_lang == "en" and biz_email:
        detected_lang = _detect_language_from_domain(biz_email)
        if detected_lang != "en":
            print(f"    Language from domain: {detected_lang}")

    lang_names = {
        "en": "English", "fr": "French", "es": "Spanish", "de": "German",
        "it": "Italian", "pt": "Portuguese", "tr": "Turkish", "ru": "Russian",
        "ar": "Arabic", "ja": "Japanese", "ko": "Korean", "zh": "Chinese",
    }
    lang_name = lang_names.get(detected_lang, "English")

    greetings = {
        "en": "Best,", "fr": "Cordialement,", "es": "Saludos,", "de": "Mit freundlichen Grüssen,",
        "it": "Cordiali saluti,", "pt": "Atenciosamente,", "tr": "Saygılarımla,", "ru": "С уважением,",
        "ar": "مع أطيب التحيات,", "ja": "よろしくお願いします。", "ko": "감사합니다.", "zh": "此致敬礼。",
    }
    greeting = greetings.get(detected_lang, "Best,")

    services_text = "\n".join(f"- {s}" for s in MY_SERVICES)

    biz_rating = business.get("rating", "")
    biz_reviews = business.get("reviews", "")
    biz_type = business.get("type", "")
    biz_description = business.get("description", "")

    biz_context = f"Business: {biz_name}\nType: {biz_type or biz_category}\nLocation: {location}"
    if biz_rating:
        biz_context += f"\nGoogle rating: {biz_rating} stars ({biz_reviews} reviews)"
    if biz_description:
        biz_context += f"\nDescription: {biz_description}"

    website_section = ""
    if website_info:
        website_section = f"\n\nWebsite content:\n{website_info[:500]}"

    prompt = f"""Write a cold email for this business.

{biz_context}

Write in {lang_name} language.

Rules:
- Start with "Hi {biz_name} team,"
- First line: mention something specific about their business (rating, reviews, what they do)
- Pick 3-4 services that fit a {biz_category}
- After each service, explain WHY they need it — make them want it
- Format: "- Service — why they need this and what result it gets"
- End with a soft call to action
- 50-120 words total
- No buzzwords, no emojis
- ALWAYS end with: {greeting}\\n{SENDER_NAME}\\n{SENDER_PORTFOLIO}

All services (pick the best 3-4):
{services_text}

Return ONLY valid JSON: {{"subject": "...", "body": "..."}}"""

    try:
        for attempt in range(3):
            if AI_PROVIDER == "gemini" and GEMINI_API_KEY:
                response = requests.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{AI_MODEL}:generateContent?key={GEMINI_API_KEY}",
                    headers={"Content-Type": "application/json"},
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                    timeout=30,
                )
                if response.status_code == 200:
                    data = response.json()
                    content = data["candidates"][0]["content"]["parts"][0]["text"]
                elif response.status_code == 429:
                    wait = (attempt + 1) * 10
                    print(f"  [!] Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                    continue
                else:
                    print(f"  [!] AI error {response.status_code}")
                    break
            elif AI_PROVIDER == "groq" and GROQ_API_KEY:
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": AI_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 800,
                    },
                    timeout=30,
                )
                if response.status_code == 429:
                    wait = (attempt + 1) * 10
                    print(f"  [!] Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                    continue
                if response.status_code == 200:
                    data = response.json()
                    if "choices" not in data or not data["choices"]:
                        print(f"  [!] AI returned no choices")
                        return _fallback_email(business)
                    content = data["choices"][0]["message"]["content"]
                else:
                    print(f"  [!] AI error {response.status_code}")
                    break
            else:
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": AI_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 500,
                    },
                    timeout=30,
                )
                if response.status_code == 429:
                    wait = (attempt + 1) * 15
                    print(f"  [!] Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                    continue
                if response.status_code == 200:
                    data = response.json()
                    if "choices" not in data or not data["choices"]:
                        print(f"  [!] AI returned no choices")
                        return _fallback_email(business)
                    content = data["choices"][0]["message"]["content"]
                else:
                    print(f"  [!] AI error {response.status_code}")
                    break

            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0]
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                fixed = content.strip()
                if fixed.startswith("```json"):
                    fixed = fixed[7:]
                if fixed.startswith("```"):
                    fixed = fixed[3:]
                if fixed.endswith("```"):
                    fixed = fixed[:-3]
                fixed = fixed.strip()
                lines = []
                in_body = False
                body_lines = []
                for line in fixed.split("\n"):
                    if '"body"' in line:
                        in_body = True
                        continue
                    if in_body:
                        if '"subject"' in line:
                            in_body = False
                            continue
                        body_lines.append(line)
                    else:
                        lines.append(line)
                subject_line = "\n".join(lines)
                sm = re.search(r'"subject"\s*:\s*"([^"]*)"', subject_line)
                subject = sm.group(1) if sm else "Quick question"
                body = "\n".join(body_lines).strip()
                body = re.sub(r'\\n', '\n', body)
                if not subject or not body:
                    print(f"  [!] AI returned invalid JSON")
                    return _fallback_email(business)
                result = {"subject": subject, "body": body}
            if "subject" in result and "body" in result:
                body = result["body"].strip().strip('"')
                body = re.sub(r'"\s*\+\s*"', '', body)
                body = re.sub(r'\?"\s*$', '?', body)
                body = re.sub(r'"\s*$', '', body)
                body = body.rstrip("}").rstrip()
                if SENDER_NAME not in body:
                    body = body.rstrip() + "\n\n" + greeting + "\n" + SENDER_NAME + "\n" + SENDER_PORTFOLIO
                result["body"] = body
                if detected_lang != "en" and greeting != "Best,":
                    body = result["body"]
                    body = re.sub(r"Best,?\s*\n?", f"{greeting}\n", body)
                    body = re.sub(r"^Best,?\s*\n?", f"{greeting}\n", body, flags=re.M)
                    result["body"] = body
                return result
    except Exception as e:
        print(f"  [!] AI failed: {e}")

    print(f"  [!] Using fallback email for {biz_name}")
    return _fallback_email(business)


def _fallback_email(business: Dict) -> Dict:
    """Fallback email if AI fails. Uses website info for personalization."""
    biz_name = business.get("name", "your business")
    biz_category = business.get("category", "business")
    biz_website = business.get("website", "")
    biz_email = business.get("email", "")
    detected_lang = _detect_language_from_domain(biz_email) if biz_email else "en"

    greetings = {
        "en": "Best,", "fr": "Cordialement,", "es": "Saludos,", "de": "Mit freundlichen Grüssen,",
        "it": "Cordiali saluti,", "pt": "Atenciosamente,", "tr": "Saygılarımla,", "ru": "С уважением,",
        "ar": "مع أطيب التحيات,", "ja": "よろしくお願いします。", "ko": "감사합니다.", "zh": "此致敬礼。",
    }
    greeting = greetings.get(detected_lang, "Best,")

    website_info = ""
    if biz_website:
        try:
            website_info = _read_website(biz_website)
        except Exception:
            pass

    category_map = {
        "gym": "fitness",
        "barbershop": "barbershop",
        "hair_salon": "salon",
        "restaurant": "restaurant",
        "dental": "dental practice",
        "plumber": "plumbing business",
        "electrician": "electrical business",
        "cleaning": "cleaning company",
        "landscaping": "landscaping business",
        "real_estate": "real estate business",
        "lawyer": "law firm",
        "accounting": "accounting firm",
        "medical": "medical practice",
        "spa": "spa",
        "photography": "photography business",
        "web_design": "web design agency",
    }
    friendly_category = category_map.get(biz_category, biz_category)

    if website_info:
        key_info = website_info[:300].replace("\n", " ")
        body = f"""Hi {biz_name} team,

I came across your {friendly_category} and wanted to reach out.

From what I see on your site, you've built something worth talking about.

I'm a Python developer and I build automation tools that could help you:
- Lead scraping to find new customers in your area
- WhatsApp or Telegram bots for customer support
- Email automation and follow-ups
- AI chat for your website to handle common questions

I work fast and keep things simple.

Interested? Just reply to this email.

{greeting}
{SENDER_NAME}
{SENDER_PORTFOLIO}"""
    else:
        body = f"""Hi {biz_name} team,

I found your {friendly_category} and wanted to reach out.

I'm a Python developer specializing in automation bots. I can build:

- Lead scraping bots to find new customers
- WhatsApp/Telegram bots for customer support
- Email automation and data enrichment
- ChatGPT/Claude AI integration

I work fast and deliver clean, working code.

Interested? Just reply to this email.

{greeting}
{SENDER_NAME}
{SENDER_PORTFOLIO}"""

    subject = f"Quick question for {biz_name}"

    return {"subject": subject, "body": body}
