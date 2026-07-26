"""
Email Finder
============
Finds emails from business websites.
Also finds websites for businesses that don't have one.

Created by: Mustapha Elasri
"""

import sys
import os
import re
from typing import List, Dict, Optional
from urllib.parse import quote_plus, urlparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lead_generator.config import ScraperConfig
from lead_generator.scrapers.crawler import AntiBypassCrawler
from lead_generator.scrapers.email_finder import WebsiteIntelligenceExtractor


def find_website_for_business(business: Dict) -> Optional[str]:
    """Find website for a business using Bing search."""
    name = business.get("name", "")
    city = business.get("city", "")
    category = business.get("category", "")

    if not name:
        return None

    query = f"{name} {category} {city} website"
    crawler = AntiBypassCrawler(timeout=5, max_retries=1, fast_mode=True)

    try:
        html = crawler.fetch(f"https://www.bing.com/search?q={quote_plus(query)}&count=5")
        if not html:
            return None

        if isinstance(html, bytes):
            html = html.decode("utf-8", errors="replace")

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")

        skip_domains = [
            "bing.com", "google.com", "facebook.com", "twitter.com",
            "instagram.com", "linkedin.com", "youtube.com", "yelp.com",
            "wikipedia.org", "amazon.com", "reddit.com",
        ]

        for a in soup.select("h2 a"):
            href = a.get("href", "")
            if not href:
                continue

            from urllib.parse import parse_qs
            import base64
            if "bing.com/ck/a" in href:
                try:
                    parsed = urlparse(href)
                    params = parse_qs(parsed.query)
                    for key in ["u", "r"]:
                        if key in params:
                            enc = params[key][0]
                            if enc.startswith("a1"):
                                enc = enc[2:]
                            href = base64.b64decode(enc + "==").decode("utf-8", errors="replace")
                            if href.startswith("http"):
                                break
                except Exception:
                    pass

            if not href.startswith("http"):
                continue

            domain = urlparse(href).netloc.lower()
            if any(s in domain for s in skip_domains):
                continue

            return href

    except Exception:
        pass

    return None


def find_email(business: Dict) -> Optional[str]:
    """Find email from a business's website. Also classifies business type."""
    website = business.get("website", "")
    if not website:
        return None

    if not website.startswith("http"):
        website = "https://" + website

    config = ScraperConfig(fast_mode=True)
    extractor = WebsiteIntelligenceExtractor(config)

    try:
        info = extractor.find_contacts(website)
        if info and info.get("emails"):
            if not business.get("category") or business.get("category") == "website":
                desc = info.get("description", "")
                if desc:
                    btype = extractor.classify_business(desc)
                    if btype != "unknown":
                        business["category"] = btype
            return info["emails"][0]
    except Exception:
        pass

    return None


def find_emails_batch(businesses: List[Dict], max_workers: int = 20) -> List[Dict]:
    """Find emails for a list of businesses."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    print(f"  Finding emails for {len(businesses)} businesses...")

    def _process(biz):
        if biz.get("email"):
            return biz
        try:
            email = find_email(biz)
            if email:
                biz["email"] = email
        except Exception:
            pass
        return biz

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_process, biz): biz for biz in businesses}
        done = 0
        for future in as_completed(futures):
            done += 1
            try:
                result = future.result()
                results.append(result)
            except Exception:
                results.append(futures[future])
            if done % 20 == 0 or done == len(businesses):
                found = sum(1 for b in results if b.get("email"))
                print(f"    Progress: {done}/{len(businesses)} ({found} emails found)")

    found = sum(1 for b in results if b.get("email"))
    print(f"  Found {found}/{len(results)} emails")
    return results
