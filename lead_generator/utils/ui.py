"""
Terminal UI - Beautiful console output using ANSI colors.
No external dependencies needed - works on Windows 10+, macOS, Linux.
"""

import sys
import os
import time
import shutil
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")


class Colors:
    """ANSI color codes."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"

    # Foreground
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Background
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"


C = Colors


def enable_ansi():
    """Enable ANSI escape codes on Windows."""
    if os.name == "nt":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass


enable_ansi()


def clear():
    """Clear terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def get_width():
    """Get terminal width."""
    return shutil.get_terminal_size().columns


def print_centered(text, color="", width=None):
    """Print centered text."""
    w = width or get_width()
    padded = text.center(w)
    print(f"{color}{padded}{C.RESET}")


def print_line(char="─", color=C.DIM):
    """Print a horizontal line."""
    print(f"{color}{char * get_width()}{C.RESET}")


def print_double_line(char="═", color=C.CYAN):
    """Print a double horizontal line."""
    print(f"{color}{char * get_width()}{C.RESET}")


def banner():
    """Print the application banner."""
    clear()
    print()
    print_double_line()
    print()
    print_centered(f"{C.BRIGHT_CYAN}{C.BOLD}LEAD GENERATOR PRO{C.RESET}", width=get_width())
    print_centered(f"{C.DIM}WorldWide Business Lead Scraper v2.0{C.RESET}", width=get_width())
    print()
    print_double_line()
    print()
    print_centered(f"{C.DIM}Made by {C.BOLD}Mustapha Elasri{C.RESET}{C.DIM} | github.com/Stoph1723{C.RESET}", width=get_width())
    print()


def section_header(title, icon="►"):
    """Print a section header."""
    print()
    print(f"  {C.BRIGHT_CYAN}{icon} {C.BOLD}{title}{C.RESET}")
    print(f"  {C.DIM}{'─' * (len(title) + 4)}{C.RESET}")
    print()


def success(msg):
    """Print success message."""
    print(f"  {C.BRIGHT_GREEN}✓ {msg}{C.RESET}")


def error(msg):
    """Print error message."""
    print(f"  {C.BRIGHT_RED}✗ {msg}{C.RESET}")


def warning(msg):
    """Print warning message."""
    print(f"  {C.BRIGHT_YELLOW}⚠ {msg}{C.RESET}")


def info(msg):
    """Print info message."""
    print(f"  {C.BRIGHT_BLUE}ℹ {msg}{C.RESET}")


def found(msg, count=""):
    """Print found items."""
    if count:
        print(f"  {C.BRIGHT_GREEN}+ {C.BOLD}{count}{C.RESET} {C.DIM}{msg}{C.RESET}")
    else:
        print(f"  {C.BRIGHT_GREEN}+ {msg}{C.RESET}")


def searching(msg):
    """Print searching message."""
    print(f"  {C.CYAN}⟳ {C.DIM}Searching: {C.RESET}{C.WHITE}{msg}{C.RESET}")


def progress_bar(current, total, prefix="", suffix="", width=40):
    """Print a progress bar."""
    if total == 0:
        return
    pct = current / total
    filled = int(width * pct)
    bar = "█" * filled + "░" * (width - filled)
    print(
        f"\r  {C.CYAN}{prefix} {C.BRIGHT_CYAN}{bar}{C.RESET} "
        f"{C.BOLD}{pct*100:.0f}%{C.RESET} "
        f"{C.DIM}{suffix}{C.RESET}",
        end="",
        flush=True,
    )
    if current >= total:
        print()


def stat_box(stats):
    """Print a statistics box."""
    print()
    print(f"  {C.BG_BLUE}{C.BRIGHT_WHITE}{C.BOLD} STATISTICS {C.RESET}")
    print(f"  {C.BLUE}{'─' * 36}{C.RESET}")

    for label, value, color in stats:
        val_str = str(value)
        print(f"  {C.DIM}{label:.<28}{C.RESET} {color}{C.BOLD}{val_str}{C.RESET}")

    print(f"  {C.BLUE}{'─' * 36}{C.RESET}")
    print()


def menu(title, options, back_option=False):
    """Print a menu and get user choice."""
    section_header(title, "☰")

    for i, option in enumerate(options, 1):
        num = f"{C.BRIGHT_CYAN}{C.BOLD}{i:2}{C.RESET}"
        label = f"{C.WHITE}{option}{C.RESET}"
        print(f"    {num}. {label}")

    if back_option:
        num = f"{C.BRIGHT_RED}{C.BOLD} 0{C.RESET}"
        label = f"{C.DIM}Back{C.RESET}"
        print(f"    {num}. {label}")

    print()
    choice = input(f"  {C.BRIGHT_CYAN}➤ {C.RESET}").strip()
    return choice


def ask(question, default="", options=None):
    """Ask user a question with optional default."""
    prompt = f"  {C.BRIGHT_CYAN}?{C.RESET} {C.WHITE}{question}{C.RESET}"
    if default:
        prompt += f" {C.DIM}({default}){C.RESET}"
    if options:
        prompt += f"\n  {C.DIM}Options: {', '.join(options)}{C.RESET}"
    prompt += f"\n  {C.BRIGHT_CYAN}➤ {C.RESET}"

    answer = input(prompt).strip()
    return answer if answer else default


def ask_yes_no(question, default=True):
    """Ask yes/no question."""
    default_str = "Y/n" if default else "y/N"
    prompt = f"  {C.BRIGHT_CYAN}?{C.RESET} {C.WHITE}{question}{C.RESET} {C.DIM}({default_str}){C.RESET}"
    prompt += f"\n  {C.BRIGHT_CYAN}➤ {C.RESET}"

    answer = input(prompt).strip().lower()
    if not answer:
        return default
    return answer in ("y", "yes")


def table_row(*cells, widths=None):
    """Print a table row."""
    if widths is None:
        widths = [20] * len(cells)

    parts = []
    for cell, w in zip(cells, widths):
        truncated = str(cell)[:w].ljust(w)
        parts.append(truncated)

    print(f"  {'│'.join(parts)}")


def table_header(*headers, widths=None):
    """Print a table header."""
    if widths is None:
        widths = [20] * len(headers)

    parts = []
    for h, w in zip(headers, widths):
        parts.append(h.upper().ljust(w))

    line = "│".join("─" * w for w in widths)
    print(f"  {C.DIM}{line}{C.RESET}")
    print(f"  {C.BOLD}{'│'.join(parts)}{C.RESET}")
    print(f"  {C.DIM}{line}{C.RESET}")


def table_end(widths):
    """Print table end line."""
    line = "│".join("─" * w for w in widths)
    print(f"  {C.DIM}{line}{C.RESET}")


def lead_preview(lead, index=0):
    """Print a lead preview."""
    score = lead.lead_score
    tier = lead.lead_tier

    if tier == "HOT":
        tier_color = C.BRIGHT_RED
        tier_icon = "🔥"
    elif tier == "WARM":
        tier_color = C.BRIGHT_YELLOW
        tier_icon = "🌡"
    else:
        tier_color = C.DIM
        tier_icon = "❄"

    print()
    print(f"  {C.DIM}#{index}{C.RESET} {tier_color}{tier_icon} {C.BOLD}{lead.business_name}{C.RESET} {C.DIM}[{score}/100]{C.RESET}")

    if lead.phone:
        print(f"     {C.BRIGHT_GREEN}📞 {lead.phone}{C.RESET}")
    if lead.email:
        print(f"     {C.BRIGHT_GREEN}📧 {lead.email}{C.RESET}")
    if lead.website:
        print(f"     {C.CYAN}🌐 {lead.website}{C.RESET}")
    if lead.address:
        addr = lead.address[:60] + "..." if len(lead.address) > 60 else lead.address
        print(f"     {C.DIM}📍 {addr}{C.RESET}")
    if lead.facebook or lead.instagram or lead.linkedin:
        socials = []
        if lead.facebook:
            socials.append("FB")
        if lead.instagram:
            socials.append("IG")
        if lead.linkedin:
            socials.append("LI")
        if lead.twitter:
            socials.append("TW")
        print(f"     {C.BRIGHT_MAGENTA}📱 {' · '.join(socials)}{C.RESET}")


def run_complete(stats, elapsed):
    """Print run complete summary."""
    print()
    print_double_line("═", C.BRIGHT_GREEN)
    print()
    print_centered(f"{C.BRIGHT_GREEN}{C.BOLD}✓ RUN COMPLETE{C.RESET}")
    print()

    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)

    stat_box([
        ("Time Elapsed", f"{minutes}m {seconds}s", C.WHITE),
        ("Total Scraped", stats["total"], C.BRIGHT_CYAN),
        ("With Email", stats["with_email"], C.BRIGHT_GREEN),
        ("With Phone", stats["with_phone"], C.BRIGHT_GREEN),
        ("With Website", stats.get("with_website", 0), C.BRIGHT_GREEN),
        ("Hot Leads", stats["hot_leads"], C.BRIGHT_RED),
        ("Warm Leads", stats["warm_leads"], C.BRIGHT_YELLOW),
        ("Cold Leads", stats["cold_leads"], C.DIM),
        ("Average Score", stats["avg_score"], C.BRIGHT_CYAN),
    ])


def instructions():
    """Print usage instructions."""
    print()
    print_double_line("═", C.BRIGHT_YELLOW)
    print()
    print_centered(f"{C.BRIGHT_YELLOW}{C.BOLD}HOW TO USE{C.RESET}")
    print()
    print_double_line("─", C.DIM)
    print()

    steps = [
        ("1", "Choose search mode", "Pick from 6 search modes"),
        ("2", "Enter business types", "e.g. dentist,pharmacy,restaurant,boulangerie (ANY language!)"),
        ("3", "Enter locations", "e.g. Agadir Morocco,London UK,Tokyo Japan"),
        ("4", "Set max results", "How many results per query (default: 50)"),
        ("5", "Enable email crawl", "Crawl websites to find emails (slower but worth it)"),
        ("6", "Get results", "Check the output folder for CSV/Excel files"),
    ]

    for num, title, desc in steps:
        print(f"    {C.BRIGHT_CYAN}{C.BOLD}{num}{C.RESET} {C.WHITE}{C.BOLD}{title}{C.RESET}")
        print(f"      {C.DIM}{desc}{C.RESET}")
        print()

    print(f"  {C.BRIGHT_GREEN}Search Modes:{C.RESET}")
    print(f"    {C.DIM}1. Business type + location (Worldwide) - All 4 sources")
    print(f"    2. Google Maps URL - Parse URL, search all sources")
    print(f"    3. Country-wide category - Search entire country")
    print(f"    4. Bing Web only - Direct web search for businesses")
    print(f"    5. Cache only - Instant results from pre-fetched data")
    print(f"    6. Bulk from file - Run multiple searches at once{C.RESET}")
    print()

    print(f"  {C.BRIGHT_GREEN}Google Maps URL format:{C.RESET}")
    print(f"    {C.CYAN}https://www.google.com/maps/search/dentist+agadir/@30.4,-9.6,14z{C.RESET}")
    print()
    print(f"  {C.BRIGHT_GREEN}Supported search terms:{C.RESET}")
    print(f"    {C.DIM}dentist, dentiste, pharmacy, pharmacie, restaurant, hotel,")
    print(f"    cafe, bar, gym, hairdresser, bakery, boulangerie, supermarket,")
    print(f"    doctor, clinic, hospital, school, bank, lawyer, accountant,")
    print(f"    plumber, electrician, spa, optician, jewelry, furniture, etc.{C.RESET}")
    print()
    print(f"  {C.BRIGHT_GREEN}Supported locations:{C.RESET}")
    print(f"    {C.DIM}Any city worldwide: London UK, Paris France, Tokyo Japan,")
    print(f"    Dubai UAE, Agadir Morocco, New York USA, etc.{C.RESET}")
    print()
    print_double_line("─", C.DIM)
    print()
