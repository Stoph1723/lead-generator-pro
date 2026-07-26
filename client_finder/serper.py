"""
Serper.dev Google Maps Scraper
==============================
Uses Serper API for reliable Google Maps business data.
No scraping, no proxies, no blocks.

Created by: Mustapha Elasri
"""

import requests
from typing import Dict, List, Optional

from .config import SERPER_API_KEY


def serper_search(query: str, num: int = 10, page: int = 1, country: str = "") -> List[Dict]:
    """Search Google Maps via Serper API. Returns list of businesses."""
    if not SERPER_API_KEY:
        print("  [!] SERPER_API_KEY not set in config.py")
        return []

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {"q": query, "hl": "en", "num": min(num, 100)}
    if country:
        payload["gl"] = country

    try:
        r = requests.post(
            "https://google.serper.dev/maps",
            headers=headers,
            json=payload,
            timeout=15,
        )

        if r.status_code == 429:
            print("  [!] Serper rate limit hit")
            return []

        if r.status_code != 200:
            print(f"  [!] Serper error: {r.status_code}")
            return []

        data = r.json()
        places = data.get("places", [])

        results = []
        for p in places:
            biz = {
                "name": p.get("title", ""),
                "address": p.get("address", ""),
                "phone": p.get("phoneNumber", ""),
                "website": p.get("website", ""),
                "rating": p.get("rating", 0),
                "reviews": p.get("ratingCount", 0),
                "type": p.get("type", ""),
                "types": p.get("types", []),
                "description": p.get("description", ""),
                "lat": p.get("latitude"),
                "lng": p.get("longitude"),
                "hours": p.get("openingHours", {}),
                "place_id": p.get("placeId", ""),
                "source": "serper",
            }
            results.append(biz)

        return results

    except Exception as e:
        print(f"  [!] Serper error: {e}")
        return []


def serper_search_multi(query: str, max_results: int = 200, country: str = "") -> List[Dict]:
    """Search with pagination to get more results."""
    all_results = []
    pages_needed = (max_results + 9) // 10  # 10 per page

    for page in range(1, min(pages_needed + 1, 11)):  # Max 10 pages = 100 results
        results = serper_search(query, num=10, page=page, country=country)
        if not results:
            break
        all_results.extend(results)
        if len(all_results) >= max_results:
            break

    return all_results[:max_results]


def build_serper_queries(city: str, category: str, language: str = "en") -> List[str]:
    """Build search queries for Serper Maps."""
    category_map = {
        "gym": "gyms",
        "barbershop": "barbershops",
        "hair_salon": "hair salons",
        "restaurant": "restaurants",
        "dental": "dental clinics",
        "plumber": "plumbers",
        "electrician": "electricians",
        "cleaning": "cleaning companies",
        "landscaping": "landscaping companies",
        "real_estate": "real estate agencies",
        "lawyer": "law firms",
        "accounting": "accounting firms",
        "medical": "medical clinics",
        "spa": "spas",
        "photography": "photography studios",
        "web_design": "web design agencies",
        "auto_repair": "auto repair shops",
        "bakery": "bakeries",
        "cafe": "cafes",
        "hotel": "hotels",
        "pharmacy": "pharmacies",
        "veterinary": "veterinary clinics",
        "yoga": "yoga studios",
        "crossfit": "crossfit gyms",
        "personal_trainer": "personal trainers",
    }

    eng_category = category_map.get(category, category)
    return [f"{eng_category} in {city}"]
