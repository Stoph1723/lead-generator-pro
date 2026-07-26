"""
Client Finder — Main Script
===========================
2 modes:
  Mode 1: Scrape businesses -> Find emails -> AI writes -> Send
  Mode 2: Dork emails directly (@ operator) -> AI writes -> Send

Usage:
    python -m client_finder.main
    python -m client_finder.main --query "dentist" --location "London UK" --dork

Created by: Mustapha Elasri
"""

import sys
import os
import json
import argparse
import time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BG_BLUE = "\033[44m"
    BG_GREEN = "\033[42m"
    BG_RED = "\033[41m"
    BG_YELLOW = "\033[43m"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_header():
    print()
    print(f"{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}")
    print("+" + "=" * 62 + "+")
    print("|" + " " * 62 + "|")
    print("|" + "  CLIENT FINDER".center(62) + "|")
    print("|" + "  Cold Email Outreach Tool".center(62) + "|")
    print("|" + " " * 62 + "|")
    print("+" + "=" * 62 + "+")
    print(f"{Colors.RESET}")
    print(f"  {Colors.DIM}Created by Mustapha Elasri{Colors.RESET}")
    print()


def print_menu():
    print(f"  {Colors.CYAN}{'=' * 50}{Colors.RESET}")
    print(f"  {Colors.BOLD}{Colors.WHITE}  MAIN MENU{Colors.RESET}")
    print(f"  {Colors.CYAN}{'=' * 50}{Colors.RESET}")
    print()
    print(f"  {Colors.GREEN}[1]{Colors.RESET}  {Colors.BOLD}Scrape Mode{Colors.RESET}     - Find businesses -> emails -> send")
    print(f"  {Colors.GREEN}[2]{Colors.RESET}  {Colors.BOLD}Dork Mode{Colors.RESET}        - Find emails via @ operator (faster)")
    print(f"  {Colors.GREEN}[3]{Colors.RESET}  {Colors.BOLD}Quick Dork{Colors.RESET}       - One-click dork with default settings")
    print()
    print(f"  {Colors.CYAN}[4]{Colors.RESET}  {Colors.BOLD}Website List{Colors.RESET}     - Crawl your own list of websites")
    print(f"  {Colors.GREEN}[5]{Colors.RESET}  {Colors.BOLD}Google Maps{Colors.RESET}      - Serper API (direct Google data)")
    print()
    print(f"  {Colors.RED}[0]{Colors.RESET}  {Colors.BOLD}Exit{Colors.RESET}")
    print()
    print(f"  {Colors.CYAN}{'=' * 50}{Colors.RESET}")
    print()


def print_step(current, total, message):
    bar_len = 30
    filled = int(bar_len * current / total)
    bar = f"{Colors.GREEN}{'█' * filled}{Colors.DIM}{'░' * (bar_len - filled)}{Colors.RESET}"
    print(f"\r  {Colors.BOLD}[{current}/{total}]{Colors.RESET} {bar} {message}", end="", flush=True)
    if current == total:
        print()


def print_success(message):
    print(f"  {Colors.GREEN}✓{Colors.RESET} {message}")


def print_error(message):
    print(f"  {Colors.RED}✗{Colors.RESET} {message}")


def print_info(message):
    print(f"  {Colors.CYAN}ℹ{Colors.RESET} {message}")


def print_warning(message):
    print(f"  {Colors.YELLOW}!{Colors.RESET} {message}")


def safe_int(value, default=100):
    """Convert string to int safely, returning default on failure."""
    try:
        result = int(value)
        return result if result > 0 else default
    except (ValueError, TypeError):
        return default


def print_box(title, lines, color=Colors.CYAN):
    width = 55
    print()
    print(f"  {color}┌{'─' * width}┐{Colors.RESET}")
    print(f"  {color}│{Colors.RESET} {Colors.BOLD}{title}{Colors.RESET}")
    print(f"  {color}├{'─' * width}┤{Colors.RESET}")
    for line in lines:
        print(f"  {color}│{Colors.RESET}  {line}")
    print(f"  {color}└{'─' * width}┘{Colors.RESET}")
    print()


def get_input(prompt, default=""):
    if default:
        value = input(f"  {Colors.CYAN}>{Colors.RESET} {prompt} [{Colors.DIM}{default}{Colors.RESET}]: ").strip()
        return value if value else default
    else:
        while True:
            value = input(f"  {Colors.CYAN}>{Colors.RESET} {prompt}: ").strip()
            if value:
                return value
            print(f"  {Colors.RED}  Required!{Colors.RESET}")


def get_yes_no(prompt, default=True):
    hint = "Y/n" if default else "y/N"
    value = input(f"  {Colors.CYAN}>{Colors.RESET} {prompt} [{hint}]: ").strip().lower()
    if not value:
        return default
    return value in ("y", "yes")


def show_config_issues(issues):
    if issues:
        print_box("Config Warnings", issues, Colors.YELLOW)


POPULAR_TYPES = [
    ("1", "Dentists"),
    ("2", "Restaurants"),
    ("3", "Hair Salons"),
    ("4", "Barbers"),
    ("5", "Nail Salons"),
    ("6", "Gyms"),
    ("7", "Cafes"),
    ("8", "Hotels"),
    ("9", "Real Estate"),
    ("10", "Law Firms"),
    ("11", "Plumbers"),
    ("12", "Electricians"),
    ("13", "Cleaning Companies"),
    ("14", "Car Dealerships"),
    ("15", "Beauty Salons"),
    ("16", "Veterinary Clinics"),
    ("17", "Medical Clinics"),
    ("18", "Pharmacies"),
    ("19", "Spas"),
    ("20", "Moving Companies"),
    ("21", "Pest Control"),
    ("22", "Accountants"),
    ("23", "Insurance Agencies"),
    ("24", "Pet Groomers"),
    ("25", "Tutors"),
    ("26", "Language Schools"),
]

TOP_COUNTRIES = [
    ("1", "London"),
    ("2", "New York"),
    ("3", "Los Angeles"),
    ("4", "Chicago"),
    ("5", "Toronto"),
    ("6", "Paris"),
    ("7", "Berlin"),
    ("8", "Madrid"),
    ("9", "Rome"),
    ("10", "Amsterdam"),
    ("11", "Dubai"),
    ("12", "Sydney"),
    ("13", "Melbourne"),
    ("14", "Manchester"),
    ("15", "Birmingham"),
    ("16", "Istanbul"),
    ("17", "Tokyo"),
    ("18", "Seoul"),
    ("19", "Singapore"),
    ("20", "Mumbai"),
    ("21", "Sao Paulo"),
    ("22", "Mexico City"),
    ("23", "Cairo"),
    ("24", "Lagos"),
    ("25", "Cape Town"),
    ("26", "Stockholm"),
]

LANGUAGES = [
    ("1", "English", "en"),
    ("2", "French", "fr"),
    ("3", "Spanish", "es"),
    ("4", "German", "de"),
    ("5", "Arabic", "ar"),
    ("6", "Portuguese", "pt"),
    ("7", "Italian", "it"),
    ("8", "Turkish", "tr"),
    ("9", "Russian", "ru"),
    ("10", "Japanese", "ja"),
    ("11", "Chinese", "zh"),
    ("12", "Korean", "ko"),
    ("13", "Dutch", "nl"),
    ("14", "Swedish", "sv"),
    ("15", "Polish", "pl"),
    ("16", "Hindi", "hi"),
]


def pick_business_type():
    """Show business types and let user pick."""
    print()
    print(f"  {Colors.BOLD}POPULAR BUSINESS TYPES:{Colors.RESET}")
    print()

    col1 = POPULAR_TYPES[:13]
    col2 = POPULAR_TYPES[13:]

    for i in range(len(col1)):
        num1, name1 = col1[i]
        line = f"  {Colors.GREEN}[{num1:>2}]{Colors.RESET} {name1:<22}"
        if i < len(col2):
            num2, name2 = col2[i]
            line += f"{Colors.GREEN}[{num2:>2}]{Colors.RESET} {name2}"
        print(line)

    print()
    print(f"  {Colors.DIM}Or type your own (comma separated): plumber,electrician{Colors.RESET}")
    print()

    choice = input(f"  {Colors.CYAN}Pick numbers or type custom>{Colors.RESET} ").strip()

    if not choice:
        return "dentist"

    selected = []
    for part in choice.split(","):
        part = part.strip()
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(POPULAR_TYPES):
                selected.append(POPULAR_TYPES[idx][1].lower().split(" ")[0])
        else:
            selected.append(part.lower())

    return ",".join(selected) if selected else "dentist"


def pick_location():
    """Show top cities and let user pick."""
    print()
    print(f"  {Colors.BOLD}TOP CITIES:{Colors.RESET}")
    print()

    col1 = TOP_COUNTRIES[:13]
    col2 = TOP_COUNTRIES[13:]

    for i in range(len(col1)):
        num1, name1 = col1[i]
        line = f"  {Colors.GREEN}[{num1:>2}]{Colors.RESET} {name1:<15}"
        if i < len(col2):
            num2, name2 = col2[i]
            line += f"{Colors.GREEN}[{num2:>2}]{Colors.RESET} {name2}"
        print(line)

    print()
    print(f"  {Colors.DIM}Or type your own city: berlin{Colors.RESET}")
    print()

    choice = input(f"  {Colors.CYAN}Pick number or type custom>{Colors.RESET} ").strip()

    if not choice:
        return "London"

    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(TOP_COUNTRIES):
            return TOP_COUNTRIES[idx][1]
        return "London"

    return choice


def pick_language():
    """Show languages and let user pick."""
    print()
    print(f"  {Colors.BOLD}LANGUAGES:{Colors.RESET}")
    print()

    col1 = LANGUAGES[:8]
    col2 = LANGUAGES[8:]

    for i in range(len(col1)):
        num1, name1, code1 = col1[i]
        line = f"  {Colors.GREEN}[{num1:>2}]{Colors.RESET} {name1:<15}"
        if i < len(col2):
            num2, name2, code2 = col2[i]
            line += f"{Colors.GREEN}[{num2:>2}]{Colors.RESET} {name2}"
        print(line)

    print()
    print(f"  {Colors.DIM}Or type language code: en, fr, de{Colors.RESET}")
    print()

    choice = input(f"  {Colors.CYAN}Pick numbers or type custom>{Colors.RESET} ").strip()

    if not choice:
        return "en"

    selected = []
    for part in choice.split(","):
        part = part.strip()
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(LANGUAGES):
                selected.append(LANGUAGES[idx][2])
        else:
            selected.append(part.lower())

    return ",".join(selected) if selected else "en"


_WARP_ACTIVE = False


def _setup_warp_for_session():
    """Detect and connect Cloudflare WARP for this session."""
    global _WARP_ACTIVE
    from client_finder.config import (
        is_warp_installed, get_warp_status, connect_warp,
        setup_warp_proxy, WARP_PROXY_URL
    )

    print()
    print(f"  {Colors.CYAN}--- Cloudflare WARP Setup ---{Colors.RESET}")

    if not is_warp_installed():
        print_error("Cloudflare WARP not installed")
        print(f"  Download: {Colors.CYAN}https://1.1.1.1/{Colors.RESET}")
        print(f"  Install it, then run with {Colors.BOLD}--warp{Colors.RESET} again")
        return False

    print_success("WARP installed")

    status = get_warp_status()
    if status == "Connected":
        print_success("WARP already connected")
        _WARP_ACTIVE = True
        return True

    print_info("Connecting to WARP...")
    ok, msg = connect_warp()
    if ok:
        print_success(msg)
    else:
        print_warning(f"{msg} — trying proxy mode anyway")

    print_info("Switching to proxy mode...")
    ok, msg = setup_warp_proxy()
    if ok:
        print_success(msg)
        _WARP_ACTIVE = True
        return True
    else:
        print_error(msg)
        print_info("Will try direct connections")
        return False


def run_interactive():
    """Interactive menu mode."""
    clear_screen()
    print_header()

    from client_finder.config import (
        MAX_BUSINESSES,
        MAX_EMAILS_TO_SEND,
        ENRICHMENT_WORKERS,
        OPENROUTER_API_KEY,
        BREVO_SMTP_KEY,
        TELEGRAM_BOT_TOKEN,
    )

    issues = []
    if not OPENROUTER_API_KEY:
        issues.append("OpenRouter API key not set (AI will use fallback)")
    if not BREVO_SMTP_KEY:
        issues.append("Brevo SMTP key not set (emails will NOT be sent)")
    if not TELEGRAM_BOT_TOKEN:
        issues.append("Telegram token not set (alerts print to console)")

    show_config_issues(issues)

    while True:
        print_menu()
        choice = input(f"  {Colors.CYAN}Pick an option>{Colors.RESET} ").strip()

        if choice == "1":
            run_scrape_interactive()
        elif choice == "2":
            run_dork_interactive()
        elif choice == "3":
            run_quick_dork()
        elif choice == "4":
            run_website_list_interactive()
        elif choice == "5":
            run_serper_interactive()
        elif choice == "0":
            print()
            print(f"  {Colors.GREEN}Goodbye!{Colors.RESET}")
            print()
            break
        else:
            print_error("Invalid option. Try again.")
            time.sleep(1)


def run_website_list_file(filepath, dry_run=False):
    """Crawl websites from a file (CLI mode)."""
    if not os.path.isfile(filepath):
        print(f"File not found: {filepath}")
        return

    websites = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if not line.startswith("http"):
                    line = "https://" + line
                websites.append(line)

    if not websites:
        print("No websites in file.")
        return

    print(f"Loaded {len(websites)} websites from {filepath}")

    from client_finder.emails import find_emails_batch
    from client_finder.ai_writer import write_cold_email
    from client_finder.sender import send_emails_batch
    from client_finder.tracker import track_email_sent, check_opens
    from client_finder.notifier import notify_emails_sent, notify_leads_found, send_telegram
    from client_finder.config import ENRICHMENT_WORKERS

    def _url_to_name(url):
        domain = url.split("//")[-1].split("/")[0]
        if domain.startswith("www."):
            domain = domain[4:]
        name = domain.split(".")[0].replace("-", " ").replace("_", " ")
        return name.title()

    biz_list = [{"name": _url_to_name(w), "website": w, "email": "", "phone": "", "city": "", "category": "website"} for w in websites]
    enriched = find_emails_batch(biz_list, ENRICHMENT_WORKERS)
    with_email = [b for b in enriched if b.get("email")]

    if not with_email:
        print("No emails found.")
        send_telegram(f"<b>Website List Mode</b>\n\nCrawled {len(websites)} websites\nNo emails found.")
        return

    for b in with_email:
        print(f"  {b['website']} -> {b['email']} [{b.get('category', 'unknown')}]")

    send_telegram(
        f"<b>📧 Leads Found!</b>\n\n"
        f"Websites crawled: {len(websites)}\n"
        f"Emails found: {len(with_email)}\n\n"
        + "\n".join(f"  {b['email']}" for b in with_email[:10])
    )

    for biz in with_email:
        email_data = write_cold_email(biz)
        if email_data:
            biz["subject"] = email_data["subject"]
            biz["body"] = email_data["body"]

    if not dry_run:
        send_items = [b for b in with_email if b.get("subject") and b.get("body")]
        stats = send_emails_batch(send_items, len(send_items))
        for item in stats.get("results", []):
            if item.get("status") == "sent":
                track_email_sent(name=item.get("name", ""), email=item.get("email", ""), subject=item.get("subject", ""))
        print(f"Sent: {stats.get('sent', 0)} | Failed: {stats.get('failed', 0)}")
        notify_emails_sent(stats)

    check_opens()
    print(f"Done! Found {len(with_email)} emails from {len(websites)} websites.")


def run_serper_interactive():
    """Google Maps search via Serper API."""
    clear_screen()
    print_header()

    print(f"  {Colors.GREEN}{Colors.BOLD}GOOGLE MAPS MODE (Serper API){Colors.RESET}")
    print(f"  Direct Google Maps data — no scraping needed")
    print()

    from client_finder.config import SERPER_API_KEY, MAX_BUSINESSES, MAX_EMAILS_TO_SEND, ENRICHMENT_WORKERS
    if not SERPER_API_KEY:
        print_error("SERPER_API_KEY not set in config.py")
        print(f"  Sign up: {Colors.CYAN}https://serper.dev{Colors.RESET}")
        return

    cities = ["San Diego", "Los Angeles", "New York", "Houston", "Phoenix",
              "San Francisco", "Las Vegas", "Miami", "Chicago", "Seattle",
              "Denver", "Austin", "Dallas", "Atlanta", "Boston"]
    print(f"  {Colors.DIM}Suggested cities:{Colors.RESET}")
    for i, c in enumerate(cities):
        print(f"    {Colors.GREEN}{i+1:2}.{Colors.RESET} {c}")
    print()

    city_input = input(f"  {Colors.CYAN}City (number or name)>{Colors.RESET} ").strip()
    if not city_input:
        print_error("City is required")
        return
    try:
        city_idx = int(city_input) - 1
        if 0 <= city_idx < len(cities):
            city = cities[city_idx]
        else:
            city = city_input
    except ValueError:
        city = city_input

    categories = ["gym", "barbershop", "restaurant", "dental", "plumber",
                  "cleaning", "landscaping", "real estate", "lawyer", "spa",
                  "photography", "cafe", "hotel", "pharmacy", "auto repair"]
    print(f"\n  {Colors.DIM}Suggested categories:{Colors.RESET}")
    for i, c in enumerate(categories):
        print(f"    {Colors.GREEN}{i+1:2}.{Colors.RESET} {c}")
    print()

    cat_input = input(f"  {Colors.CYAN}Category (number or name, default: gym)>{Colors.RESET} ").strip() or "gym"
    try:
        cat_idx = int(cat_input) - 1
        if 0 <= cat_idx < len(categories):
            category = categories[cat_idx]
        else:
            category = cat_input
    except ValueError:
        category = cat_input

    max_biz = safe_int(input(f"  Max businesses (default {MAX_BUSINESSES})> ").strip(), MAX_BUSINESSES)
    dry = input(f"  {Colors.YELLOW}Dry run (no sending)? [Y/n]:{Colors.RESET} ").strip().lower() != "n"

    print()
    print(f"  {Colors.CYAN}{'=' * 50}{Colors.RESET}")
    print(f"  {Colors.BOLD}{Colors.WHITE}  Run Settings{Colors.RESET}")
    print(f"  {Colors.CYAN}{'=' * 50}{Colors.RESET}")
    print(f"  | {Colors.BOLD}City:{Colors.RESET}     {city}")
    print(f"  | {Colors.BOLD}Category:{Colors.RESET} {category}")
    print(f"  | {Colors.BOLD}Max:{Colors.RESET}       {max_biz}")
    print(f"  | {Colors.BOLD}Mode:{Colors.RESET}     {'DRY RUN' if dry else 'LIVE SEND'}")
    print(f"  {Colors.CYAN}{'=' * 50}{Colors.RESET}")
    print()

    # Search Serper
    print(f"  [{Colors.GREEN}1/4{Colors.RESET}] Searching Google Maps for {category} in {city}...")
    from client_finder.serper import serper_search_multi, build_serper_queries
    queries = build_serper_queries(city, category)
    businesses = []
    for q in queries:
        results = serper_search_multi(q, max_results=max_biz)
        businesses.extend(results)
    businesses = businesses[:max_biz]

    if not businesses:
        print_error("No businesses found on Google Maps")
        return

    print(f"  {Colors.GREEN}Found {len(businesses)} businesses{Colors.RESET}")
    for b in businesses[:5]:
        print(f"    {Colors.GREEN}✓{Colors.RESET} {b['name']} ({b.get('type', 'N/A')}) - {b.get('reviews', 0)} reviews")
    if len(businesses) > 5:
        print(f"    ... and {len(businesses) - 5} more")
    print()

    # Find emails
    print(f"  [{Colors.GREEN}2/4{Colors.RESET}] Finding emails...")
    from client_finder.emails import find_emails_batch
    businesses = find_emails_batch(businesses, ENRICHMENT_WORKERS)
    with_email = [b for b in businesses if b.get("email")]
    print(f"  {Colors.GREEN}Found {len(with_email)}/{len(businesses)} emails{Colors.RESET}")
    print()

    if not with_email:
        print_error("No emails found")
        send_telegram(f"<b>Google Maps Mode</b>\n\nSearched {len(businesses)} businesses\nNo emails found.")
        return

    # Write AI emails
    print(f"  [{Colors.GREEN}3/4{Colors.RESET}] Writing personalized emails...")
    from client_finder.ai_writer import write_cold_email
    to_send = []
    for i, item in enumerate(with_email):
        if i > 0:
            time.sleep(8)
        email_data = write_cold_email(item)
        if email_data:
            item["subject"] = email_data["subject"]
            item["body"] = email_data["body"]
            to_send.append(item)
            print(f"    {Colors.GREEN}✓{Colors.RESET} {item['name']}: {item['subject'][:50]}...")
    print()

    # Send emails
    if dry:
        print(f"  [{Colors.YELLOW}4/4{Colors.RESET}] Dry run — showing first email:")
        if to_send:
            print(f"\n  To: {to_send[0]['email']}")
            print(f"  Subject: {to_send[0].get('subject', '')}")
            print(f"  Body:\n{to_send[0].get('body', '')[:500]}")
            msg_lines = [f"🔍 Dry Run: Found {len(to_send)} emails ({category} in {city}):"]
            for item in to_send[:10]:
                msg_lines.append(f"  → {item['name']} ({item['email']})")
            send_telegram("\n".join(msg_lines))
        print(f"\n  {Colors.YELLOW}DRY RUN — No emails sent{Colors.RESET}")
        return

    print(f"  [{Colors.GREEN}4/4{Colors.RESET}] Sending {len(to_send)} emails...")
    from client_finder.sender import send_emails_batch
    result = send_emails_batch(to_send, MAX_EMAILS_TO_SEND)

    # Track
    from client_finder.tracker import track_email_sent, check_opens
    for r in result.get("results", []):
        if r["status"] == "sent":
            track_email_sent(name=r.get("name", ""), email=r["email"], subject=r["subject"])
    try:
        check_opens()
    except Exception:
        pass

    # Notify
    if result["sent"] > 0:
        msg_lines = [f"✅ Sent {result['sent']} emails via Google Maps:"]
        for r in result.get("results", [])[:10]:
            if r["status"] == "sent":
                msg_lines.append(f"  → {r['name']} ({r['email']})")
        send_telegram("\n".join(msg_lines))

    print(f"\n  {Colors.GREEN}Done!{Colors.RESET} Sent {result['sent']}, Failed {result['failed']}")


def run_website_list_interactive():
    """Crawl a list of websites for emails."""
    clear_screen()
    print_header()

    print(f"  {Colors.CYAN}{Colors.BOLD}WEBSITE LIST MODE{Colors.RESET}")
    print(f"  {Colors.DIM}Paste websites (one per line) or type a file path{Colors.RESET}")
    print(f"  {Colors.DIM}When done, type 'done' on a new line{Colors.RESET}")
    print()

    websites = []
    print(f"  {Colors.DIM}Option 1: Paste websites (one per line):{Colors.RESET}")
    print(f"  {Colors.DIM}Option 2: Type file path (e.g. C:\\websites.txt){Colors.RESET}")
    print()

    source = input(f"  {Colors.CYAN}Paste websites or file path>{Colors.RESET} ").strip()

    if not source:
        print_error("No input provided")
        input(f"\n  {Colors.DIM}Press Enter to return to menu...{Colors.RESET}")
        return

    if os.path.isfile(source):
        try:
            with open(source, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if not line.startswith("http"):
                            line = "https://" + line
                        websites.append(line)
            print_success(f"Loaded {len(websites)} websites from file")
        except Exception as e:
            print_error(f"Failed to read file: {e}")
            input(f"\n  {Colors.DIM}Press Enter to return to menu...{Colors.RESET}")
            return
    else:
        websites.append(source)
        print(f"  {Colors.DIM}Paste more websites (type 'done' when finished):{Colors.RESET}")
        while True:
            line = input(f"  {Colors.DIM}>{Colors.RESET} ").strip()
            if line.lower() == "done":
                break
            if line:
                if not line.startswith("http"):
                    line = "https://" + line
                websites.append(line)

    if not websites:
        print_error("No websites provided")
        input(f"\n  {Colors.DIM}Press Enter to return to menu...{Colors.RESET}")
        return

    send_real = get_yes_no("Send real emails?", default=False)
    dry_run = not send_real

    print()
    print_box("Run Settings", [
        f"Websites: {Colors.BOLD}{len(websites)}{Colors.RESET}",
        f"Mode:     {Colors.BOLD}{Colors.GREEN}LIVE SEND{Colors.RESET}" if not dry_run else f"Mode:     {Colors.BOLD}{Colors.YELLOW}DRY RUN{Colors.RESET}",
    ])

    from client_finder.emails import find_emails_batch
    from client_finder.ai_writer import write_cold_email
    from client_finder.sender import send_emails_batch
    from client_finder.tracker import track_email_sent, check_opens
    from client_finder.notifier import notify_emails_sent, notify_leads_found, send_telegram
    from client_finder.config import ENRICHMENT_WORKERS

    def _url_to_name(url):
        domain = url.split("//")[-1].split("/")[0]
        if domain.startswith("www."):
            domain = domain[4:]
        name = domain.split(".")[0].replace("-", " ").replace("_", " ")
        return name.title()

    print()
    print_step(1, 4, f"Crawling {len(websites)} websites...")
    biz_list = [{"name": _url_to_name(w), "website": w, "email": "", "phone": "", "city": "", "category": "website"} for w in websites]
    enriched = find_emails_batch(biz_list, ENRICHMENT_WORKERS)
    with_email = [b for b in enriched if b.get("email")]
    print_success(f"Found {len(with_email)}/{len(websites)} emails")

    if not with_email:
        print_warning("No emails found.")
        send_telegram(f"<b>Website List Mode</b>\n\nCrawled {len(websites)} websites\nNo emails found.")
        input(f"\n  {Colors.DIM}Press Enter to return to menu...{Colors.RESET}")
        return

    for b in with_email:
        btype = b.get("category", "unknown")
        print(f"    {Colors.GREEN}✓{Colors.RESET} {b['website']} -> {Colors.CYAN}{b['email']}{Colors.RESET} [{Colors.YELLOW}{btype}{Colors.RESET}]")

    send_telegram(
        f"<b>📧 Leads Found!</b>\n\n"
        f"Websites crawled: {len(websites)}\n"
        f"Emails found: {len(with_email)}\n\n"
        + "\n".join(f"  • {b.get('name', b['website'].split('//')[-1].split('/')[0])} → {b['email']}" for b in with_email[:10])
    )

    print()
    print_step(2, 4, "Writing AI emails...")
    for i, biz in enumerate(with_email):
        if i > 0:
            time.sleep(8)
        email_data = write_cold_email(biz)
        if email_data:
            biz["subject"] = email_data["subject"]
            biz["body"] = email_data["body"]
    print_success("AI emails ready")

    if dry_run:
        print_step(3, 4, "DRY RUN - skipping send")
    else:
        send_items = [b for b in with_email if b.get("subject") and b.get("body")]
        print_step(3, 4, f"Sending {len(send_items)} emails...")
        stats = send_emails_batch(send_items, len(send_items))
        for item in stats.get("results", []):
            if item.get("status") == "sent":
                track_email_sent(name=item.get("name", ""), email=item.get("email", ""), subject=item.get("subject", ""))
        print_success(f"Sent: {stats.get('sent', 0)} | Failed: {stats.get('failed', 0)}")
        notify_emails_sent(stats)

    print_step(4, 4, "Checking opens...")
    check_opens()
    print_success("Done")

    print()
    print_box("SUMMARY", [
        f"Websites:   {Colors.GREEN}{len(websites)}{Colors.RESET}",
        f"Emails:     {Colors.GREEN}{len(with_email)}{Colors.RESET}",
        f"Sent:       {Colors.GREEN}{stats.get('sent', 0) if not dry_run else 0}{Colors.RESET}" if not dry_run else f"Mode:       {Colors.YELLOW}DRY RUN{Colors.RESET}",
    ])

    input(f"\n  {Colors.DIM}Press Enter to return to menu...{Colors.RESET}")


def run_scrape_interactive():
    """Interactive scrape mode."""
    clear_screen()
    print_header()

    print(f"  {Colors.GREEN}{Colors.BOLD}SCRAPE MODE{Colors.RESET}")
    print(f"  {Colors.DIM}Find businesses -> websites -> emails -> AI writes -> send{Colors.RESET}")
    print()

    query = pick_business_type()
    location = pick_location()
    max_biz = get_input("Max businesses per query", "200")
    max_emails = get_input("Max emails to send", "200")
    send_real = get_yes_no("Send real emails?", default=True)
    dry_run = not send_real

    print()
    print_box("Run Settings", [
        f"Query:      {Colors.BOLD}{query}{Colors.RESET}",
        f"Location:   {Colors.BOLD}{location}{Colors.RESET}",
        f"Max biz:    {Colors.BOLD}{max_biz}{Colors.RESET}",
        f"Max emails: {Colors.BOLD}{max_emails}{Colors.RESET}",
        f"Mode:       {Colors.BOLD}{Colors.GREEN}LIVE SEND{Colors.RESET}" if not dry_run else f"Mode:       {Colors.BOLD}{Colors.YELLOW}DRY RUN{Colors.RESET}",
    ])

    from client_finder.scraper import scrape_businesses
    from client_finder.emails import find_emails_batch, find_website_for_business
    from client_finder.ai_writer import write_cold_email
    from client_finder.sender import send_emails_batch
    from client_finder.tracker import track_email_sent, check_opens
    from client_finder.notifier import notify_leads_found, notify_emails_sent, notify_summary
    from client_finder.config import ENRICHMENT_WORKERS

    queries = [q.strip() for q in query.split(",")]
    locations = [l.strip() for l in location.split(",")]
    total_sent = 0
    with_email = []
    businesses = []

    for qi, q in enumerate(queries):
        for li, loc in enumerate(locations):
            print()
            print(f"  {Colors.BOLD}{'=' * 50}{Colors.RESET}")
            print(f"  {Colors.BOLD}{q} in {loc}{Colors.RESET}")
            print(f"  {Colors.BOLD}{'=' * 50}{Colors.RESET}")

            print_step(1, 6, "Scraping businesses...")
            businesses = scrape_businesses(q, loc, safe_int(max_biz))
            print_success(f"Found {len(businesses)} businesses")

            if not businesses:
                print_warning("No businesses found. Skipping.")
                continue

            print_step(2, 6, "Finding websites...")
            for biz in businesses:
                if not biz.get("website"):
                    website = find_website_for_business(biz)
                    if website:
                        biz["website"] = website
            with_website = sum(1 for b in businesses if b.get("website"))
            print_success(f"{with_website}/{len(businesses)} have websites")

            print_step(3, 6, "Finding emails...")
            businesses = find_emails_batch(businesses, ENRICHMENT_WORKERS)
            with_email = [b for b in businesses if b.get("email")]
            print_success(f"Found {len(with_email)} emails")

            if not with_email:
                print_warning("No emails found. Skipping send.")
                continue

            print_step(4, 6, "Writing AI emails...")
            for i, biz in enumerate(with_email):
                if i > 0:
                    time.sleep(8)
                email_data = write_cold_email(biz)
                if email_data:
                    biz["subject"] = email_data["subject"]
                    biz["body"] = email_data["body"]
            print_success("AI emails ready")

            if dry_run:
                print_step(5, 6, "DRY RUN - skipping send")
                stats = {"sent": 0, "failed": 0, "total": 0}
            else:
                send_items = [b for b in with_email if b.get("subject") and b.get("body")]
                print_step(5, 6, f"Sending {len(send_items)} emails...")
                stats = send_emails_batch(send_items, safe_int(max_emails))
                total_sent += stats.get("sent", 0)

                for item in stats.get("results", []):
                    if item.get("status") == "sent":
                        track_email_sent(
                            name=item.get("name", ""),
                            email=item.get("email", ""),
                            subject=item.get("subject", ""),
                        )
                print_success(f"Sent: {stats.get('sent', 0)} | Failed: {stats.get('failed', 0)}")

            print_step(6, 6, "Checking opens...")
            check_opens()
            print_success("Done")

            notify_leads_found(businesses, q, loc)
            notify_summary(
                query=q, location=loc,
                businesses=len(businesses),
                emails_found=len(with_email),
                emails_sent=stats.get("sent", 0),
            )

    print()
    print_box("SUMMARY", [
        f"Businesses found:  {Colors.GREEN}{len(businesses)}{Colors.RESET}",
        f"Emails found:      {Colors.GREEN}{len(with_email)}{Colors.RESET}",
        f"Emails sent:       {Colors.GREEN}{total_sent}{Colors.RESET}" if not dry_run else f"Mode:              {Colors.YELLOW}DRY RUN{Colors.RESET}",
    ])

    input(f"\n  {Colors.DIM}Press Enter to return to menu...{Colors.RESET}")


def run_dork_interactive():
    """Interactive dork mode."""
    clear_screen()
    print_header()

    print(f"  {Colors.GREEN}{Colors.BOLD}DORK MODE{Colors.RESET}")
    print(f"  {Colors.DIM}Find emails via @ operator -> AI writes -> send{Colors.RESET}")
    print()

    query = pick_business_type()
    location = pick_location()
    max_results = get_input("Max emails to find", "200")
    send_real = get_yes_no("Send real emails?", default=True)
    dry_run = not send_real

    print()
    print_box("Run Settings", [
        f"Query:    {Colors.BOLD}{query}{Colors.RESET}",
        f"Location: {Colors.BOLD}{location}{Colors.RESET}",
        f"Max:      {Colors.BOLD}{max_results}{Colors.RESET}",
        f"Mode:     {Colors.BOLD}{Colors.GREEN}LIVE SEND{Colors.RESET}" if not dry_run else f"Mode:     {Colors.BOLD}{Colors.YELLOW}DRY RUN{Colors.RESET}",
    ])

    from client_finder.dorker import find_emails_by_dorking
    from client_finder.ai_writer import write_cold_email
    from client_finder.sender import send_emails_batch
    from client_finder.tracker import track_email_sent, check_opens
    from client_finder.notifier import notify_emails_sent, send_telegram
    from client_finder.config import MAX_EMAILS_TO_SEND, get_warp_proxies

    queries = [q.strip() for q in query.split(",")]
    locations = [l.strip() for l in location.split(",")]
    all_emails = []

    for qi, q in enumerate(queries):
        for li, loc in enumerate(locations):
            print()
            print(f"  {Colors.BOLD}{'=' * 50}{Colors.RESET}")
            print(f"  {Colors.BOLD}{q} in {loc}{Colors.RESET}")
            print(f"  {Colors.BOLD}{'=' * 50}{Colors.RESET}")

            print_step(1, 4, "Dorking for emails...")
            warp_proxies = get_warp_proxies() if _WARP_ACTIVE else None
            emails = find_emails_by_dorking(q, loc, safe_int(max_results), proxies=warp_proxies)
            all_emails.extend(emails)
            print_success(f"Found {len(emails)} emails")

    if not all_emails:
        print()
        print_error("No emails found.")
        input(f"\n  {Colors.DIM}Press Enter to return to menu...{Colors.RESET}")
        return

    print()
    print_step(2, 4, "Writing AI emails...")
    for i, item in enumerate(all_emails):
        if i > 0:
            time.sleep(8)
        email_data = write_cold_email(item)
        if email_data:
            item["subject"] = email_data["subject"]
            item["body"] = email_data["body"]
    print_success("AI emails ready")

    if dry_run:
        print_step(3, 4, "DRY RUN - skipping send")
        print()
        print_box("Found Emails", [
            f"{Colors.GREEN}{e.get('name', 'Unknown')}{Colors.RESET} <{Colors.CYAN}{e.get('email', 'N/A')}{Colors.RESET}>"
            for e in all_emails[:10]
        ])
        stats = {"sent": 0}
    else:
        send_items = [e for e in all_emails if e.get("subject") and e.get("body")]
        print_step(3, 4, f"Sending {len(send_items)} emails...")
        stats = send_emails_batch(send_items, safe_int(MAX_EMAILS_TO_SEND))

        for item in stats.get("results", []):
            if item.get("status") == "sent":
                track_email_sent(
                    name=item.get("name", ""),
                    email=item.get("email", ""),
                    subject=item.get("subject", ""),
                )
        print_success(f"Sent: {stats.get('sent', 0)} | Failed: {stats.get('failed', 0)}")

    print_step(4, 4, "Checking opens...")
    check_opens()
    print_success("Done")

    # Save results
    os.makedirs("output", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join("output", f"dork_{timestamp}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(all_emails, f, indent=2, ensure_ascii=False)

    print()
    print_box("SUMMARY", [
        f"Emails found:  {Colors.GREEN}{len(all_emails)}{Colors.RESET}",
        f"Emails sent:   {Colors.GREEN}{stats.get('sent', 0)}{Colors.RESET}" if not dry_run else f"Mode:          {Colors.YELLOW}DRY RUN{Colors.RESET}",
        f"Saved to:      {Colors.DIM}{filepath}{Colors.RESET}",
    ])

    if all_emails:
        msg_lines = [f"📧 Dork Mode: Found {len(all_emails)} emails ({query} in {location})"]
        for e in all_emails[:10]:
            msg_lines.append(f"  → {e.get('name', 'Unknown')} ({e.get('email', '')})")
        send_telegram("\n".join(msg_lines))

    input(f"\n  {Colors.DIM}Press Enter to return to menu...{Colors.RESET}")


def run_quick_dork():
    """One-click dork with defaults."""
    clear_screen()
    print_header()

    print(f"  {Colors.GREEN}{Colors.BOLD}QUICK DORK{Colors.RESET}")
    print(f"  {Colors.DIM}Finding emails for dentists in London...{Colors.RESET}")
    print()

    from client_finder.dorker import find_emails_by_dorking
    from client_finder.ai_writer import write_cold_email
    from client_finder.sender import send_emails_batch
    from client_finder.tracker import track_email_sent, check_opens
    from client_finder.notifier import notify_emails_sent, send_telegram
    from client_finder.config import MAX_EMAILS_TO_SEND, get_warp_proxies

    print_step(1, 4, "Dorking for emails...")
    warp_proxies = get_warp_proxies() if _WARP_ACTIVE else None
    emails = find_emails_by_dorking("dentist", "London", 50, proxies=warp_proxies)
    print_success(f"Found {len(emails)} emails")

    if not emails:
        print_error("No emails found.")
        input(f"\n  {Colors.DIM}Press Enter to return to menu...{Colors.RESET}")
        return

    print_step(2, 4, "Writing AI emails...")
    for i, item in enumerate(emails):
        if i > 0:
            time.sleep(8)
        email_data = write_cold_email(item)
        if email_data:
            item["subject"] = email_data["subject"]
            item["body"] = email_data["body"]
    print_success("AI emails ready")

    print_step(3, 4, "Sending emails...")
    send_items = [e for e in emails if e.get("subject") and e.get("body")]
    stats = send_emails_batch(send_items, safe_int(MAX_EMAILS_TO_SEND))

    for item in stats.get("results", []):
        if item.get("status") == "sent":
            track_email_sent(
                name=item.get("name", ""),
                email=item.get("email", ""),
                subject=item.get("subject", ""),
            )
    print_success(f"Sent: {stats.get('sent', 0)} | Failed: {stats.get('failed', 0)}")

    print_step(4, 4, "Checking opens...")
    check_opens()
    print_success("Done")

    print()
    print_box("SUMMARY", [
        f"Emails found:  {Colors.GREEN}{len(emails)}{Colors.RESET}",
        f"Emails sent:   {Colors.GREEN}{stats.get('sent', 0)}{Colors.RESET}",
    ])

    if emails:
        msg_lines = [f"⚡ Quick Dork: Found {len(emails)} emails (dentist in London)"]
        for e in emails[:10]:
            msg_lines.append(f"  → {e.get('name', 'Unknown')} ({e.get('email', '')})")
        send_telegram("\n".join(msg_lines))

    input(f"\n  {Colors.DIM}Press Enter to return to menu...{Colors.RESET}")


def show_stats():
    """Show email stats."""
    clear_screen()
    print_header()

    from client_finder.tracker import get_stats
    stats = get_stats()

    print(f"  {Colors.GREEN}{Colors.BOLD}EMAIL STATS{Colors.RESET}")
    print()

    print_box("Overview", [
        f"  Emails Sent:    {Colors.GREEN}{stats['sent']}{Colors.RESET}",
        f"  Emails Opened:  {Colors.CYAN}{stats['opened']}{Colors.RESET} ({stats['open_rate']}%)",
        f"  Emails Replied: {Colors.MAGENTA}{stats['replied']}{Colors.RESET}",
        f"  Not Opened:     {Colors.YELLOW}{stats['not_opened']}{Colors.RESET}",
    ])

    if stats["opened_list"]:
        print_box("Opened Emails", [
            f"  {Colors.GREEN}✓{Colors.RESET} {s['name']} - {s.get('open_count', 1)}x"
            for s in stats["opened_list"][:10]
        ], Colors.GREEN)

    if stats["not_opened_list"]:
        print_box("Not Opened (follow up)", [
            f"  {Colors.YELLOW}!{Colors.RESET} {s['name']} <{s['email']}>"
            for s in stats["not_opened_list"][:5]
        ], Colors.YELLOW)

    input(f"\n  {Colors.DIM}Press Enter to return to menu...{Colors.RESET}")


def check_opens_interactive():
    """Check for new opens."""
    clear_screen()
    print_header()

    from client_finder.tracker import check_opens

    print(f"  {Colors.CYAN}{Colors.BOLD}CHECKING OPENS...{Colors.RESET}")
    print()

    new_opens = check_opens()

    if new_opens:
        print_box("New Opens!", [
            f"  {Colors.GREEN}✓{Colors.RESET} {s['name']} - opened {s.get('open_count', 1)}x"
            for s in new_opens
        ], Colors.GREEN)
    else:
        print_info("No new opens yet.")

    input(f"\n  {Colors.DIM}Press Enter to return to menu...{Colors.RESET}")


def main():
    parser = argparse.ArgumentParser(description="Client Finder — cold email outreach")
    parser.add_argument("--query", help="Business types (comma separated)")
    parser.add_argument("--location", help="Locations (comma separated)")
    parser.add_argument("--max", type=int, default=200, help="Max results")
    parser.add_argument("--max-emails", type=int, default=200, help="Max emails to send")
    parser.add_argument("--dork", action="store_true", help="Use dork mode")
    parser.add_argument("--dry-run", action="store_true", help="Find leads but don't send")
    parser.add_argument("--stats", action="store_true", help="Show email stats")
    parser.add_argument("--check-opens", action="store_true", help="Check for new opens")
    parser.add_argument("--warp", action="store_true", help="Route traffic through Cloudflare WARP")
    parser.add_argument("--websites", help="File with list of websites to crawl")
    args = parser.parse_args()

    # If no arguments, show interactive menu
    if len(sys.argv) == 1:
        run_interactive()
        return

    # Handle --warp flag
    if args.warp:
        _setup_warp_for_session()

    # Handle --websites flag
    if args.websites:
        run_website_list_file(args.websites, args.dry_run)
        return

    # Direct command line mode
    if args.stats:
        from client_finder.tracker import stats_to_telegram
        stats_to_telegram()
        return

    if args.check_opens:
        from client_finder.tracker import check_opens
        new_opens = check_opens()
        if new_opens:
            print(f"{len(new_opens)} new opens found!")
        else:
            print("No new opens.")
        return

    if not args.query or not args.location:
        parser.error("--query and --location are required (or run without arguments for menu)")

    if args.dork:
        from client_finder.dorker import find_emails_by_dorking
        from client_finder.ai_writer import write_cold_email
        from client_finder.sender import send_emails_batch
        from client_finder.tracker import track_email_sent, check_opens
        from client_finder.notifier import notify_emails_sent
        from client_finder.config import MAX_EMAILS_TO_SEND, get_warp_proxies

        queries = [q.strip() for q in args.query.split(",")]
        locations = [l.strip() for l in args.location.split(",")]
        all_emails = []

        for q in queries:
            for loc in locations:
                warp_proxies = get_warp_proxies() if _WARP_ACTIVE else None
                emails = find_emails_by_dorking(q, loc, args.max, proxies=warp_proxies)
                all_emails.extend(emails)

        if not all_emails:
            print("No emails found.")
            return

        for i, item in enumerate(all_emails):
            if i > 0:
                time.sleep(8)
            email_data = write_cold_email(item)
            if email_data:
                item["subject"] = email_data["subject"]
                item["body"] = email_data["body"]

        if not args.dry_run:
            send_items = [e for e in all_emails if e.get("subject") and e.get("body")]
            stats = send_emails_batch(send_items, args.max_emails)
            for item in stats.get("results", []):
                if item.get("status") == "sent":
                    track_email_sent(name=item.get("name", ""), email=item.get("email", ""), subject=item.get("subject", ""))
            notify_emails_sent(stats)
        else:
            print(f"DRY RUN — found {len(all_emails)} emails")

        check_opens()
    else:
        from client_finder.scraper import scrape_businesses
        from client_finder.emails import find_emails_batch, find_website_for_business
        from client_finder.ai_writer import write_cold_email
        from client_finder.sender import send_emails_batch
        from client_finder.tracker import track_email_sent, check_opens
        from client_finder.notifier import notify_leads_found, notify_emails_sent, notify_summary
        from client_finder.config import ENRICHMENT_WORKERS

        queries = [q.strip() for q in args.query.split(",")]
        locations = [l.strip() for l in args.location.split(",")]
        total_sent = 0

        for q in queries:
            for loc in locations:
                businesses = scrape_businesses(q, loc, args.max)
                if not businesses:
                    continue

                for biz in businesses:
                    if not biz.get("website"):
                        website = find_website_for_business(biz)
                        if website:
                            biz["website"] = website

                businesses = find_emails_batch(businesses, ENRICHMENT_WORKERS)
                with_email = [b for b in businesses if b.get("email")]

                for i, biz in enumerate(with_email):
                    if i > 0:
                        time.sleep(8)
                    email_data = write_cold_email(biz)
                    if email_data:
                        biz["subject"] = email_data["subject"]
                        biz["body"] = email_data["body"]

                if not args.dry_run:
                    send_items = [b for b in with_email if b.get("subject") and b.get("body")]
                    stats = send_emails_batch(send_items, args.max_emails)
                    total_sent += stats.get("sent", 0)
                    for item in stats.get("results", []):
                        if item.get("status") == "sent":
                            track_email_sent(name=item.get("name", ""), email=item.get("email", ""), subject=item.get("subject", ""))
                    notify_emails_sent(stats)
                else:
                    stats = {"sent": 0, "failed": 0, "total": 0}

                check_opens()
                notify_leads_found(businesses, q, loc)
                notify_summary(query=q, location=loc, businesses=len(businesses), emails_found=len(with_email), emails_sent=stats.get("sent", 0))

        print(f"\nDone! Total sent: {total_sent}")


if __name__ == "__main__":
    main()
