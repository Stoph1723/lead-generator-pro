"""
Email Finder
============
Finds emails from business websites.
Reuses Lead Generator Pro's email extraction pipeline.

Created by: Mustapha Elasri
"""

import sys
import os
from typing import List, Dict, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lead_generator"))

from lead_generator.scrapers.email_finder import WebsiteIntelligenceExtractor
from lead_generator.scrapers.crawler import AntiBypassCrawler


def find_email(business: Dict) -> Optional[str]:
    """Find email from a business's website. Returns email or None."""
    website = business.get("website", "")
    if not website:
        return None

    if not website.startswith("http"):
        website = "https://" + website

    crawler = AntiBypassCrawler(timeout=10, max_retries=2, fast_mode=True)
    extractor = WebsiteIntelligenceExtractor(crawler)

    try:
        info = extractor.find_contacts(website)
        if info and info.get("emails"):
            return info["emails"][0]
    except Exception:
        pass

    return None


def find_emails_batch(businesses: List[Dict], max_workers: int = 8) -> List[Dict]:
    """Find emails for a list of businesses. Updates businesses with emails."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    print(f"  Finding emails for {len(businesses)} businesses...")

    def _process(biz):
        if biz.get("email"):
            return biz
        email = find_email(biz)
        if email:
            biz["email"] = email
        return biz

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_process, biz): biz for biz in businesses}
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception:
                results.append(futures[future])

    found = sum(1 for b in results if b.get("email"))
    print(f"  Found {found}/{len(results)} emails")
    return results
