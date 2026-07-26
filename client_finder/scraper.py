"""
Business Scraper
================
Uses Lead Generator Pro's existing scraper.
Filters out unwanted business types.

Created by: Mustapha Elasri
"""

import sys
import os
from typing import List, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lead_generator.scrapers.google_maps import GoogleMapsScraper
from lead_generator.config import ScraperConfig
from client_finder.config import EXCLUDE_TYPES


def _is_excluded(biz: Dict) -> bool:
    """Check if business should be excluded."""
    name = biz.get("name", "").lower()
    category = biz.get("category", "").lower()
    combined = f"{name} {category}"

    for excluded in EXCLUDE_TYPES:
        if excluded in combined:
            return True
    return False


def scrape_businesses(query: str, location: str, max_results: int = 50) -> List[Dict]:
    """Scrape businesses using Lead Generator Pro's existing scraper."""
    print(f"  Searching for '{query}' in '{location}'...")

    config = ScraperConfig()
    config.max_results_per_query = max_results
    config.fast_mode = True

    scraper = GoogleMapsScraper(config)
    leads = scraper.search(query, location, max_results=max_results) or []

    businesses = []
    excluded_count = 0
    for lead in leads:
        biz = {
            "name": getattr(lead, "business_name", "") or "",
            "phone": getattr(lead, "phone", "") or "",
            "website": getattr(lead, "website", "") or "",
            "address": getattr(lead, "address", "") or "",
            "city": getattr(lead, "city", "") or "",
            "country": getattr(lead, "country", "") or "",
            "category": getattr(lead, "category", "") or "",
            "email": getattr(lead, "email", "") or "",
            "rating": getattr(lead, "rating", "") or "",
            "source": getattr(lead, "source", "") or "",
        }
        # Filter placeholder emails
        if biz["email"]:
            email_local = biz["email"].split("@")[0].lower()
            email_domain = biz["email"].split("@")[1].lower() if "@" in biz["email"] else ""
            placeholders = ["your", "example", "test", "admin", "email", "user", "name",
                           "sample", "demo", "placeholder", "changeme", "replace", "insert"]
            fake_domains = ["example.com", "test.com", "mysite.com", "yourdomain.com",
                           "domain.com", "email.com", "website.com", "company.com"]
            is_bad = False
            for p in placeholders:
                if email_local == p or email_local.startswith(p + ".") or email_local.startswith(p + "_"):
                    is_bad = True
                    break
            for d in fake_domains:
                if email_domain == d or email_domain.endswith("." + d):
                    is_bad = True
                    break
            if email_domain.startswith("www."):
                is_bad = True
            if is_bad:
                biz["email"] = ""
        if biz["name"]:
            if _is_excluded(biz):
                excluded_count += 1
            else:
                businesses.append(biz)

    if excluded_count > 0:
        print(f"  Filtered out {excluded_count} unwanted businesses")

    print(f"  Found {len(businesses)} businesses")
    return businesses
