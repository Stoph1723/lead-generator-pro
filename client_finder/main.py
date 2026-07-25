"""
Client Finder — Main Script
===========================
Scrapes businesses, finds emails, writes personalized cold emails with AI,
sends via Brevo SMTP, alerts you on Telegram.

Usage:
    python -m client_finder.main --query "dentist" --location "London UK"
    python -m client_finder.main --query "pharmacy,restaurant" --location "Casablanca Morocco,Marrakech"
    python -m client_finder.main --query "dentist" --location "London UK" --dry-run

Created by: Mustapha Elasri
GitHub: https://github.com/Stoph1723/lead-generator-pro
"""

import sys
import os
import json
import time
import argparse
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from client_finder.config import (
    MAX_BUSINESSES,
    MAX_EMAILS_TO_SEND,
    SEARCH_WORKERS,
    ENRICHMENT_WORKERS,
    OPENROUTER_API_KEY,
    BREVO_SMTP_KEY,
    TELEGRAM_BOT_TOKEN,
)
from client_finder.scraper import scrape_businesses
from client_finder.emails import find_emails_batch
from client_finder.ai_writer import write_cold_email
from client_finder.sender import send_emails_batch
from client_finder.notifier import (
    notify_leads_found,
    notify_emails_sent,
    notify_summary,
    send_telegram,
)


def print_banner():
    print("=" * 60)
    print("  CLIENT FINDER")
    print("  Scrape businesses -> Find emails -> AI writes -> Send")
    print("  Created by Mustapha Elasri")
    print("=" * 60)
    print()


def check_config():
    """Check if API keys are configured."""
    issues = []
    if not OPENROUTER_API_KEY:
        issues.append("OpenRouter API key not set (AI emails will use fallback)")
    if not BREVO_SMTP_KEY:
        issues.append("Brevo SMTP key not set (emails will NOT be sent)")
    if not TELEGRAM_BOT_TOKEN:
        issues.append("Telegram bot token not set (alerts will print to console)")
    return issues


def save_results(businesses, filename):
    """Save results to JSON file."""
    os.makedirs("output", exist_ok=True)
    filepath = os.path.join("output", filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(businesses, f, indent=2, ensure_ascii=False)
    print(f"  Results saved to {filepath}")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="Client Finder — cold email outreach bot")
    parser.add_argument("--query", required=True, help="Business types (comma separated)")
    parser.add_argument("--location", required=True, help="Locations (comma separated)")
    parser.add_argument("--max", type=int, default=MAX_BUSINESSES, help="Max businesses per query")
    parser.add_argument("--max-emails", type=int, default=MAX_EMAILS_TO_SEND, help="Max emails to send")
    parser.add_argument("--dry-run", action="store_true", help="Find leads but don't send emails")
    args = parser.parse_args()

    print_banner()

    issues = check_config()
    if issues:
        print("  Config issues:")
        for issue in issues:
            print(f"    - {issue}")
        print()

    queries = [q.strip() for q in args.query.split(",")]
    locations = [l.strip() for l in args.location.split(",")]

    all_businesses = []
    all_with_email = []

    for query in queries:
        for location in locations:
            print(f"\n{'='*50}")
            print(f"  {query} in {location}")
            print(f"{'='*50}")

            print(f"\n[1/5] Scraping businesses...")
            businesses = scrape_businesses(query, location, args.max)
            all_businesses.extend(businesses)

            if not businesses:
                print("  No businesses found. Skipping.")
                continue

            print(f"\n[2/5] Finding emails...")
            businesses = find_emails_batch(businesses, ENRICHMENT_WORKERS)
            with_email = [b for b in businesses if b.get("email")]
            all_with_email.extend(with_email)

            print(f"\n[3/5] Writing personalized emails with AI...")
            for biz in with_email:
                email_data = write_cold_email(biz)
                if email_data:
                    biz["subject"] = email_data["subject"]
                    biz["body"] = email_data["body"]

            if not args.dry_run:
                send_items = [b for b in with_email if b.get("subject") and b.get("body")]

                print(f"\n[4/5] Sending emails...")
                stats = send_emails_batch(send_items, args.max_emails)

                notify_emails_sent(stats)
            else:
                print(f"\n[4/5] DRY RUN — skipping email send")
                stats = {"sent": 0, "failed": 0, "total": 0}

            notify_leads_found(businesses, query, location)

            notify_summary(
                query=query,
                location=location,
                businesses=len(businesses),
                emails_found=len(with_email),
                emails_sent=stats.get("sent", 0),
            )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"client_finder_{timestamp}.json"
    save_results(all_businesses, filename)

    print(f"\n{'='*60}")
    print(f"  DONE")
    print(f"  Businesses found: {len(all_businesses)}")
    print(f"  Emails found: {len(all_with_email)}")
    if not args.dry_run:
        print(f"  Emails sent: {stats.get('sent', 0)}")
    print(f"  Results: output/{filename}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
