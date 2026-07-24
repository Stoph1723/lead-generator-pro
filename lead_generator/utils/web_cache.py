"""
Web Search Cache
================
Stores pre-fetched business data from web searches.
The scraper loads from this cache to enrich leads with websites/emails.
"""

import os
import json
from typing import List, Dict, Optional
from datetime import datetime

from lead_generator.models.lead import Lead
from lead_generator.utils.ui import info, success, warning


class WebSearchCache:
    """Cache of business data from web searches."""

    CACHE_DIR = "cache"
    CACHE_FILE = "websearch_leads.json"

    def __init__(self):
        self.cache_path = os.path.join(self.CACHE_DIR, self.CACHE_FILE)
        self._data: List[Dict] = []
        self._load()

    def _load(self):
        """Load cache from disk."""
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                info("Loaded %d businesses from web search cache" % len(self._data))
            except Exception:
                self._data = []

    def _save(self):
        """Save cache to disk."""
        os.makedirs(self.CACHE_DIR, exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def add_business(self, name: str, website: str = "", email: str = "",
                     phone: str = "", address: str = "", city: str = "",
                     category: str = "", source: str = "websearch"):
        """Add a business to the cache."""
        entry = {
            "name": name,
            "website": website,
            "email": email,
            "phone": phone,
            "address": address,
            "city": city,
            "category": category,
            "source": source,
            "added_at": datetime.now().isoformat(),
        }
        self._data.append(entry)
        self._save()

    def add_batch(self, businesses: List[Dict]):
        """Add multiple businesses to the cache."""
        for biz in businesses:
            self._data.append({
                **biz,
                "added_at": datetime.now().isoformat(),
            })
        self._save()
        success("Added %d businesses to web search cache" % len(businesses))

    def find_website(self, business_name: str, city: str = "") -> Optional[Dict]:
        """Find a cached business by name (fuzzy match)."""
        name_lower = business_name.lower().strip()
        # Remove common prefixes/suffixes for matching
        name_clean = name_lower.replace("restaurant", "").replace("cafe", "").replace("hotel", "").strip()

        best_match = None
        best_score = 0

        for entry in self._data:
            cached_name = entry.get("name", "").lower().strip()
            cached_clean = cached_name.replace("restaurant", "").replace("cafe", "").replace("hotel", "").replace("pharmacie", "").replace("dentiste", "").replace("centre dentaire", "").strip()

            # Exact match
            if cached_name == name_lower or cached_clean == name_clean:
                return entry

            # Partial match (name is substring of cached or vice versa)
            if name_clean in cached_clean or cached_clean in name_clean:
                score = len(name_clean) / max(len(cached_clean), 1)
                if score > best_score:
                    best_score = score
                    best_match = entry
                continue

            # Word overlap
            name_words = set(name_clean.split())
            cached_words = set(cached_clean.split())
            overlap = name_words & cached_words
            if overlap:
                score = len(overlap) / max(len(name_words | cached_words), 1)
                if score > best_score:
                    best_score = score
                    best_match = entry

        if best_match and best_score >= 0.3:
            return best_match

        return None

    def find_website_for_lead(self, lead: Lead) -> Optional[str]:
        """Find a website for a lead from the cache."""
        result = self.find_website(lead.business_name, lead.city)
        if result and result.get("website"):
            return result["website"]
        return None

    def enrich_lead_from_cache(self, lead: Lead) -> bool:
        """Enrich a lead directly from cache data. Returns True if enriched."""
        result = self.find_website(lead.business_name, lead.city)
        if not result:
            return False

        enriched = False

        if result.get("website") and not lead.website:
            lead.website = result["website"]
            enriched = True

        if result.get("email") and not lead.email:
            lead.email = result["email"]
            if result["email"] not in lead.all_emails:
                lead.all_emails.append(result["email"])
            enriched = True

        if result.get("phone") and not lead.phone:
            lead.phone = result["phone"]
            enriched = True

        if result.get("address") and not lead.address:
            lead.address = result["address"]
            enriched = True

        if result.get("city") and not lead.city:
            lead.city = result["city"]
            enriched = True

        if result.get("category") and not lead.category:
            lead.category = result["category"]
            enriched = True

        if enriched:
            lead._calculate_score()

        return enriched

    def search(self, query: str, city: str = "") -> List[Dict]:
        """Search cache for businesses matching query and city."""
        query_lower = query.lower().strip()
        city_lower = city.lower().strip()
        results = []
        city_results = []

        for entry in self._data:
            name = entry.get("name", "").lower()
            entry_city = entry.get("city", "").lower()
            category = entry.get("category", "").lower()
            address = entry.get("address", "").lower()

            # Match by category or name
            query_words = query_lower.split()
            matched = (query_lower in category or query_lower in name or
                      any(w in name for w in query_words))

            if not matched:
                continue

            # Check city match
            city_match = False
            if city_lower:
                city_match = (city_lower in entry_city or city_lower in address)

            if city_match:
                city_results.append(entry)
            else:
                results.append(entry)

        # Prefer city-matched results, but include others if no city match
        if city_results:
            return city_results
        return results

    def get_all(self) -> List[Dict]:
        """Get all cached entries."""
        return self._data

    @property
    def count(self) -> int:
        return len(self._data)


def create_cache_from_websearch_results():
    """Create a sample cache file with websearch results format.

    This shows the expected JSON format for the cache file.
    Users can populate it manually or use the websearch tool.
    """
    sample = [
        {
            "name": "Restaurant El Toro",
            "website": "https://eltoroagadir.com/",
            "email": "contact@eltoroagadir.com",
            "phone": "+212 626 469 374",
            "address": "N7 Front de Mer Agadir l'Oued Souss",
            "city": "Agadir",
            "category": "restaurant",
            "source": "websearch",
        },
        {
            "name": "Le20 Moroccan Restaurant",
            "website": "https://le20.ma/en/",
            "email": "",
            "phone": "",
            "address": "20 August Street Tourist Area, Agadir 80012",
            "city": "Agadir",
            "category": "restaurant",
            "source": "websearch",
        },
        {
            "name": "Restaurant Le Vendome Agadir",
            "website": "https://agadir-levendome.com/",
            "email": "",
            "phone": "+212 (0) 528 824 816",
            "address": "Front de Mer, 80000 Agadir",
            "city": "Agadir",
            "category": "restaurant",
            "source": "websearch",
        },
        {
            "name": "Frank's Burgers",
            "website": "https://www.franks-burgers.com/",
            "email": "Admin@franks-burgers.com",
            "phone": "05 28 22 63 97",
            "address": "Hay Essalam, Agadir",
            "city": "Agadir",
            "category": "restaurant",
            "source": "websearch",
        },
        {
            "name": "Tropicana Restaurant",
            "website": "https://tropicana-restaurant.ma/",
            "email": "tropicanaagadir@gmail.com",
            "phone": "05 28 28 28 07",
            "address": "Technopole 2 Agadir bay, Agadir",
            "city": "Agadir",
            "category": "restaurant",
            "source": "websearch",
        },
        {
            "name": "La Scala Agadir",
            "website": "https://lascalaagadir.com/",
            "email": "scalagadir@gmail.com",
            "phone": "+212528846773",
            "address": "Rue oued souss Complex Tamlalet",
            "city": "Agadir",
            "category": "restaurant",
            "source": "websearch",
        },
        {
            "name": "Restaurant Friends",
            "website": "https://restaurantfriends.ma/",
            "email": "contact@restaurantfriends.ma",
            "phone": "05282-20988",
            "address": "MAG 1-2 R amal souss, Av. Moulay Hassan I, Agadir",
            "city": "Agadir",
            "category": "restaurant",
            "source": "websearch",
        },
        {
            "name": "La Medina Agadir Restaurant",
            "website": "https://www.medina-agadir.com/",
            "email": "contact@restaurantmedina.com",
            "phone": "06 66 33 88 59",
            "address": "Agadir Medina",
            "city": "Agadir",
            "category": "restaurant",
            "source": "websearch",
        },
        {
            "name": "Restaurant Les Blancs Agadir",
            "website": "https://www.lesblancsagadir.com/",
            "email": "",
            "phone": "+212 5288-28368",
            "address": "Marina Agadir, Agadir, Morocco",
            "city": "Agadir",
            "category": "restaurant",
            "source": "websearch",
        },
        {
            "name": "Signature Dentaire Agadir",
            "website": "https://signaturedentaireagadir.com/",
            "email": "signaturedentaire01@gmail.com",
            "phone": "05 28 28 35 52",
            "address": "Haut Founty, Agadir",
            "city": "Agadir",
            "category": "dentist",
            "source": "websearch",
        },
        {
            "name": "Centre Dentaire OKHSANE",
            "website": "https://centredentaireokhsane.com/",
            "email": "cdokhsane@gmail.com",
            "phone": "+212 529 186 539",
            "address": "Avenue Farhat Hachat, Hay Dakhla, Agadir",
            "city": "Agadir",
            "category": "dentist",
            "source": "websearch",
        },
        {
            "name": "Hikmat Dental Center",
            "website": "https://www.centredentairehikmat.ma/",
            "email": "",
            "phone": "+212 6 65 66 82 63",
            "address": "8 Mehdi Ben Barka Street, Agadir 80000",
            "city": "Agadir",
            "category": "dentist",
            "source": "websearch",
        },
        {
            "name": "Clinique Dentaire Internationale Agadir",
            "website": "https://cdia.ma/",
            "email": "",
            "phone": "+212 05 28 21 75 04",
            "address": "Agadir, Morocco",
            "city": "Agadir",
            "category": "dentist",
            "source": "websearch",
        },
        {
            "name": "Centre Dentaire Founty",
            "website": "https://www.hartimeriem.com/",
            "email": "contact@hartimeriem.com",
            "phone": "+212641886787",
            "address": "Founty, Agadir",
            "city": "Agadir",
            "category": "dentist",
            "source": "websearch",
        },
    ]
    return sample


if __name__ == "__main__":
    cache = WebSearchCache()
    if cache.count == 0:
        sample = create_cache_from_websearch_results()
        cache.add_batch(sample)
        print("Created sample cache with %d businesses" % len(sample))
    else:
        print("Cache has %d businesses" % cache.count)
