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
        if biz["name"]:
            if _is_excluded(biz):
                excluded_count += 1
            else:
                businesses.append(biz)

    if excluded_count > 0:
        print(f"  Filtered out {excluded_count} unwanted businesses")

    print(f"  Found {len(businesses)} businesses")
    return businesses
