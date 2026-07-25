"""
Business Scraper
================
Uses Lead Generator Pro's existing scraper.
All 7 data sources, deduplication, email extraction — already built.

Created by: Mustapha Elasri
"""

import sys
import os
from typing import List, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lead_generator"))

from lead_generator.scrapers.google_maps import GoogleMapsScraper
from lead_generator.config import ScraperConfig


def scrape_businesses(query: str, location: str, max_results: int = 50) -> List[Dict]:
    """Scrape businesses using Lead Generator Pro's existing scraper."""
    print(f"  Searching for '{query}' in '{location}'...")

    config = ScraperConfig()
    config.max_results_per_query = max_results
    config.fast_mode = True

    scraper = GoogleMapsScraper(config)
    leads = scraper.search(query, location)

    businesses = []
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
            businesses.append(biz)

    print(f"  Found {len(businesses)} businesses")
    return businesses
