"""
Data Cleaner
============
Validates and cleans scraped lead data for maximum quality.
"""

import re
from typing import Optional, Set


# Known invalid email domains (mail providers, disposable, etc.)
INVALID_EMAIL_DOMAINS = {
    "example.com", "test.com", "localhost", "mail.exchanger",
    "larousse.fr", "google.com", "gmail.com", "outlook.com",
    "yahoo.com", "hotmail.com", "aol.com", "protonmail.com",
    "mail.com", "email.com", "inbox.com", "live.com",
    "msn.com", "icloud.com", "zoho.com", "yandex.com",
    "gmx.com", "tutanota.com", "proton.me", "hey.com",
    "stackoverflow.com", "github.com", "gitlab.com", "bitbucket.org",
    "cloudflare.com", "wix.com", "squarespace.com",
    "weebly.com", "godaddy.com", "namecheap.com",
    "wordpress.com", "blogspot.com", "typepad.com",
    "mailinator.com", "guerrillamail.com", "tempmail.com",
    "throwaway.email", "10minutemail.com",
    "fastmail.com", "mail.ru", "yopmail.com", "sharklasers.com",
    "orange.fr", "wanadoo.fr", "free.fr", "laposte.net",
}

# Known invalid email prefixes (use startswith matching)
INVALID_EMAIL_PREFIXES = {
    "conso", "admin", "webmaster", "postmaster", "hostmaster",
    "nobody", "daemon", "mailer-daemon", "unsubscribe", "bounce",
    "noreply", "no-reply", "donotreply", "mail.exchanger",
    "edito", "editeur", "redac", "stages", "www",
    "abuse", "spam", "trash", "null", "fake",
}

# Generic business names to skip
GENERIC_NAMES = {
    "business", "company", "enterprise", "establishment", "shop",
    "store", "office", "centre", "center", "clinic",
    "restaurant", "cafe", "bar", "hotel",
}


def clean_phone(phone: str) -> str:
    """Clean and validate phone number. Returns empty string if invalid."""
    if not phone:
        return ""

    # Remove all non-digit characters except leading +
    cleaned = re.sub(r"[^\d+]", "", phone)

    # Ensure only one leading + sign
    if cleaned.count("+") > 1:
        cleaned = "+" + re.sub(r"\D", "", cleaned)

    # Get digits only
    digits_only = re.sub(r"\D", "", cleaned)

    # Must have at least 9 digits to be valid (international format)
    if len(digits_only) < 9:
        return ""

    # Must not be all same digit (111111111)
    if len(set(digits_only)) <= 1:
        return ""

    # Must not be a fax/test number pattern
    if re.match(r"^(1234567890|0{8,}|1{8,})$", digits_only):
        return ""

    # Must not be an IP address pattern (1.26.227.394)
    if re.match(r"^\d+\.\d+\.\d+\.\d+$", phone):
        return ""

    # Must have country code (+ prefix) or be a known local format
    if not cleaned.startswith("+"):
        # Morocco numbers: 212XXXXXXXXX (11 digits) or 0XXXXXXXXX (10 digits)
        if digits_only.startswith("212") and len(digits_only) >= 11:
            cleaned = "+" + digits_only
        elif digits_only.startswith("0") and len(digits_only) >= 10:
            cleaned = "+212" + digits_only[1:]
        else:
            # No country code = invalid
            return ""

    # Validate total digit count
    if cleaned.startswith("+"):
        code_digits = re.sub(r"\D", "", cleaned[1:])
        # Must have 9-12 digits total (country code + number)
        if len(code_digits) < 9 or len(code_digits) > 12:
            return ""

    return cleaned


def clean_email(email: str) -> str:
    """Validate and clean email address. Returns empty string if invalid."""
    if not email:
        return ""

    email = email.lower().strip()
    email = email.strip("<>'\"")

    # Basic format validation
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        return ""

    # Check domain
    domain = email.split("@")[1] if "@" in email else ""
    if domain in INVALID_EMAIL_DOMAINS:
        return ""

    # Domain must have at least 2 parts (e.g., example.com)
    domain_parts = domain.split(".")
    if len(domain_parts) < 2:
        return ""

    # Domain TLD must be at least 2 chars
    if len(domain_parts[-1]) < 2:
        return ""

    # Domain name part (before TLD) must be at least 3 chars
    if len(domain_parts[-2]) < 3:
        return ""

    # Check for known mail provider substrings in domain
    mail_providers = ["google.com", "outlook.com", "microsoft.com", "yahoo.com",
                      "hotmail.com", "protonmail.com", "zoho.com", "yandex.com",
                      "gmail-smtp", "googlemail"]
    if any(x in domain for x in mail_providers):
        return ""

    # Check prefix - use startswith for better matching
    prefix = email.split("@")[0] if "@" in email else ""
    if any(prefix.startswith(p) for p in INVALID_EMAIL_PREFIXES):
        return ""

    # Must have at least 4 chars before @
    if len(prefix) < 4:
        return ""

    # Must not contain numbers only before @
    if prefix.isdigit():
        return ""

    return email


def clean_url(url: str) -> str:
    """Clean and normalize URL."""
    if not url:
        return ""

    url = url.strip()

    # Add protocol if missing
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # Remove trailing slashes
    url = url.rstrip("/")

    # Remove common tracking parameters
    if "?" in url:
        base, query = url.split("?", 1)
        params = [p for p in query.split("&") if not re.match(r"utm_\w+=", p)]
        url = base + ("?" + "&".join(params) if params else "")
    else:
        url = re.sub(r"[?&](utm_\w+=[^&]*)", "", url)

    return url


def clean_address(address: str) -> str:
    """Clean address string."""
    if not address:
        return ""

    # Remove extra whitespace
    address = re.sub(r"\s+", " ", address).strip()

    # Remove "Unnamed Road" type placeholders
    if "unnamed" in address.lower():
        return ""

    # Remove very long addresses (likely junk)
    if len(address) > 200:
        # Try to extract just the street part
        parts = address.split(",")
        if parts:
            address = parts[0].strip()

    return address


def clean_business_name(name: str) -> str:
    """Clean business name - remove junk and normalize."""
    if not name:
        return ""

    name = name.strip()

    # Remove OSN/Overpass generic prefixes
    name = re.sub(r"^(Dentist|Restaurant|Shop|Cafe|Bar|Hotel|Pharmacy|Bakery|Gym|Salon|Spa|Clinic|Lawyer|Mechanic|Plumber|Electrician)\s*#\d+", "", name)

    # Remove trailing numbers that look like IDs
    name = re.sub(r"\s+\d{5,}$", "", name)

    # Remove extra whitespace
    name = re.sub(r"\s+", " ", name).strip()

    # Skip if too short
    if len(name) < 3:
        return ""

    # Skip if it's just a category name (exact or with articles)
    name_lower = name.lower().strip()
    if name_lower in GENERIC_NAMES:
        return ""
    # Also skip with common articles
    for prefix in ["the ", "a ", "an ", "le ", "la ", "les ", "un ", "une "]:
        if name_lower.startswith(prefix) and name_lower[len(prefix):] in GENERIC_NAMES:
            return ""

    return name


def extract_city_from_address(address: str) -> str:
    """Try to extract city from address string."""
    if not address:
        return ""

    # Pattern: "123 Main St, Austin, TX 78701"
    parts = address.split(",")
    if len(parts) >= 2:
        # City is usually the second part
        city = parts[1].strip()
        # Remove state and zip
        city = re.sub(r"\s+[A-Z]{2}\s+\d{5}.*", "", city)
        # Remove non-ASCII characters (Arabic, etc.)
        city = re.sub(r"[^\x00-\x7F]+", "", city).strip()
        if city and len(city) > 2:
            return city

    return ""


def extract_zip_code(address: str) -> str:
    """Try to extract zip code from address."""
    if not address:
        return ""

    match = re.search(r"\b(\d{5}(?:-\d{4})?)\b", address)
    return match.group(1) if match else ""


def extract_state_from_address(address: str) -> str:
    """Try to extract state from address string."""
    if not address:
        return ""

    # Common US state abbreviations
    state_pattern = r",\s*([A-Z]{2})\s*\d{5}"
    match = re.search(state_pattern, address)
    if match:
        return match.group(1)

    return ""


def validate_lead(lead) -> bool:
    """Validate a lead has minimum quality data."""
    # Must have a business name
    if not lead.business_name or len(lead.business_name) < 3:
        return False

    # Name must not be generic
    if lead.business_name.lower().strip() in GENERIC_NAMES:
        return False

    # Must not be a URL as name
    if lead.business_name.startswith(("http://", "https://", "www.")):
        return False

    # Must not contain junk characters (allow & for business names like "A & B")
    if re.search(r"[<>{}|\\^~\[\]`]", lead.business_name):
        return False

    return True
