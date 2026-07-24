"""
Business Directory Scraper - WorldWide Edition
================================================
Uses 4 data sources for maximum worldwide coverage:
1. Overpass API (OpenStreetMap) - 600+ results per city
2. Nominatim (OpenStreetMap) - geocoding + details
3. Bing web search - additional businesses
4. Google Maps URL parsing
"""

import re
import time
import random
import json
import sys
import urllib.parse
from typing import List, Optional, Dict, Tuple
from urllib.parse import quote_plus, urlparse, parse_qs, unquote

import requests
from bs4 import BeautifulSoup

from lead_generator.models.lead import Lead
from lead_generator.config import ScraperConfig
from lead_generator.utils.web_cache import WebSearchCache
from lead_generator.utils.keywords import (
    expand_query, get_osm_amenity, detect_country,
    get_languages_for_country, BUSINESS_TYPES, REVERSE_MAP,
    get_osm_tags, get_osm_tags_for_bbox, fuzzy_match_osm_tag,
)

sys.stdout.reconfigure(encoding="utf-8")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

# City bounding boxes - 300+ CITIES WORLDWIDE
CITY_BBOX = {
    # Morocco
    "agadir": (30.3, -9.7, 30.6, -9.4),
    "marrakech": (31.5, -8.1, 31.8, -7.8),
    "casablanca": (33.5, -7.7, 33.7, -7.5),
    "rabat": (34.0, -6.9, 34.1, -6.7),
    "tangier": (35.7, -5.9, 35.9, -5.7),
    "fes": (34.0, -5.0, 34.1, -4.8),
    "meknes": (33.9, -5.6, 34.0, -5.5),
    "essaouira": (31.5, -9.8, 31.6, -9.6),
    "chefchaouen": (35.2, -5.3, 35.3, -5.2),
    # USA
    "austin": (30.1, -97.9, 30.5, -97.6),
    "dallas": (32.7, -96.9, 32.9, -96.7),
    "houston": (29.6, -95.5, 29.9, -95.2),
    "new york": (40.6, -74.1, 40.9, -73.7),
    "los angeles": (33.9, -118.4, 34.2, -118.1),
    "chicago": (41.8, -87.7, 42.0, -87.5),
    "miami": (25.7, -80.3, 25.9, -80.1),
    "san francisco": (37.7, -122.5, 37.8, -122.3),
    "seattle": (47.5, -122.4, 47.7, -122.2),
    "boston": (42.3, -71.1, 42.4, -70.9),
    "atlanta": (33.7, -84.4, 33.8, -84.3),
    "phoenix": (33.4, -112.1, 33.6, -111.9),
    "denver": (39.7, -105.0, 39.8, -104.8),
    "nashville": (36.1, -86.8, 36.2, -86.7),
    "detroit": (42.3, -83.1, 42.4, -82.9),
    "philadelphia": (39.9, -75.2, 40.1, -75.0),
    # UK
    "london": (51.4, -0.3, 51.7, 0.1),
    "manchester": (53.4, -2.4, 53.6, -2.2),
    "birmingham": (52.4, -2.0, 52.6, -1.8),
    "edinburgh": (55.9, -3.3, 56.0, -3.1),
    "glasgow": (55.8, -4.4, 55.9, -4.2),
    "liverpool": (53.4, -3.0, 53.5, -2.8),
    # France
    "paris": (48.8, 2.3, 49.0, 2.5),
    "lyon": (45.7, 4.8, 45.8, 4.9),
    "marseille": (43.2, 5.3, 43.4, 5.5),
    "nice": (43.7, 7.2, 43.8, 7.4),
    "bordeaux": (44.8, -0.6, 44.9, -0.4),
    "toulouse": (43.6, 1.4, 43.7, 1.6),
    "nantes": (47.2, -1.6, 47.3, -1.4),
    "strasbourg": (48.6, 7.7, 48.6, 7.9),
    # Germany
    "berlin": (52.4, 13.3, 52.6, 13.5),
    "munich": (48.1, 11.5, 48.2, 11.7),
    "hamburg": (53.5, 9.9, 53.6, 10.1),
    "frankfurt": (50.1, 8.6, 50.2, 8.8),
    "cologne": (50.9, 6.9, 51.0, 7.1),
    "stuttgart": (48.8, 9.1, 48.8, 9.3),
    "dusseldorf": (51.2, 6.7, 51.3, 6.9),
    # Spain
    "madrid": (40.4, -3.8, 40.5, -3.6),
    "barcelona": (41.3, 2.1, 41.5, 2.3),
    "seville": (37.4, -6.0, 37.5, -5.8),
    "valencia": (39.5, -0.4, 39.6, -0.2),
    "malaga": (36.7, -4.5, 36.8, -4.3),
    "bilbao": (43.3, -2.9, 43.3, -2.7),
    # Italy
    "rome": (41.9, 12.4, 42.0, 12.6),
    "milan": (45.5, 9.1, 45.6, 9.3),
    "naples": (40.8, 14.2, 40.9, 14.4),
    "florence": (43.8, 11.2, 43.8, 11.4),
    "venice": (45.4, 12.3, 45.5, 12.4),
    "turin": (45.1, 7.6, 45.1, 7.8),
    # Japan
    "tokyo": (35.6, 139.7, 35.8, 139.9),
    "osaka": (34.6, 135.4, 34.8, 135.6),
    "kyoto": (35.0, 135.7, 35.1, 135.9),
    "hiroshima": (34.4, 132.4, 34.5, 132.6),
    "nagoya": (35.2, 136.9, 35.3, 137.1),
    "fukuoka": (33.6, 130.4, 33.7, 130.6),
    "sapporo": (43.1, 141.3, 43.2, 141.5),
    # South Korea
    "seoul": (37.5, 126.9, 37.7, 127.1),
    "busan": (35.1, 129.0, 35.2, 129.2),
    # China
    "beijing": (39.9, 116.3, 40.1, 116.5),
    "shanghai": (31.2, 121.4, 31.4, 121.6),
    "hong kong": (22.3, 114.1, 22.4, 114.3),
    "shenzhen": (22.5, 114.0, 22.6, 114.2),
    "guangzhou": (23.1, 113.2, 23.3, 113.4),
    # India
    "mumbai": (18.9, 72.8, 19.1, 73.0),
    "delhi": (28.5, 77.1, 28.8, 77.4),
    "bangalore": (12.9, 77.5, 13.1, 77.7),
    "chennai": (13.0, 80.2, 13.2, 80.4),
    "kolkata": (22.5, 88.3, 22.7, 88.5),
    "hyderabad": (17.4, 78.4, 17.5, 78.6),
    "pune": (18.5, 73.8, 18.6, 74.0),
    # UAE
    "dubai": (25.1, 55.2, 25.4, 55.4),
    "abu dhabi": (24.4, 54.6, 24.5, 54.8),
    "sharjah": (25.3, 55.3, 25.4, 55.5),
    # Saudi Arabia
    "riyadh": (24.6, 46.7, 24.8, 46.9),
    "jeddah": (21.5, 39.1, 21.7, 39.3),
    "mecca": (21.4, 39.8, 21.5, 40.0),
    # Turkey
    "istanbul": (41.0, 28.9, 41.2, 29.2),
    "ankara": (39.9, 32.8, 40.0, 33.0),
    "izmir": (38.4, 27.1, 38.5, 27.3),
    # Egypt
    "cairo": (30.0, 31.2, 30.1, 31.4),
    "alexandria": (31.2, 29.9, 31.3, 30.1),
    # Nigeria
    "lagos": (6.4, 3.3, 6.6, 3.6),
    "abuja": (9.0, 7.4, 9.1, 7.6),
    # South Africa
    "cape town": (-34.0, 18.4, -33.8, 18.7),
    "johannesburg": (-26.2, 27.9, -26.0, 28.1),
    "durban": (-29.8, 30.9, -29.7, 31.1),
    # Kenya
    "nairobi": (-1.3, 36.8, -1.2, 37.0),
    # Ethiopia
    "addis ababa": (9.0, 38.7, 9.1, 38.9),
    # Ghana
    "accra": (5.5, -0.3, 5.7, -0.1),
    # Tanzania
    "dar es salaam": (-6.8, 39.2, -6.7, 39.4),
    # Brazil
    "sao paulo": (-23.7, -46.7, -23.4, -46.4),
    "rio de janeiro": (-23.1, -43.3, -22.8, -43.1),
    "brasilia": (-15.8, -47.9, -15.7, -47.7),
    "salvador": (-12.9, -38.5, -12.8, -38.3),
    "fortaleza": (-3.7, -38.5, -3.6, -38.3),
    "buenos aires": (-34.6, -58.4, -34.5, -58.2),
    # Mexico
    "mexico city": (19.3, -99.2, 19.5, -99.0),
    "cancun": (21.1, -86.9, 21.3, -86.7),
    # Colombia
    "bogota": (4.6, -74.1, 4.8, -73.9),
    "medellin": (6.2, -75.6, 6.3, -75.4),
    # Chile
    "santiago": (-33.5, -70.7, -33.3, -70.5),
    # Peru
    "lima": (-12.1, -77.1, -12.0, -76.9),
    # Canada
    "toronto": (43.6, -79.5, 43.8, -79.3),
    "vancouver": (49.2, -123.2, 49.3, -123.0),
    "montreal": (45.5, -73.6, 45.6, -73.4),
    "calgary": (51.0, -114.1, 51.1, -113.9),
    "ottawa": (45.4, -75.7, 45.5, -75.5),
    # Australia
    "sydney": (-33.9, 151.1, -33.7, 151.3),
    "melbourne": (-37.8, 144.9, -37.7, 145.1),
    "brisbane": (-27.5, 153.0, -27.3, 153.2),
    "perth": (-31.9, 115.8, -31.8, 116.0),
    # Russia
    "moscow": (55.7, 37.5, 55.9, 37.8),
    "saint petersburg": (59.9, 30.2, 60.1, 30.5),
    # Poland
    "warsaw": (52.2, 21.0, 52.3, 21.1),
    "krakow": (50.0, 19.9, 50.1, 20.1),
    # Czech Republic
    "prague": (50.1, 14.4, 50.2, 14.6),
    # Hungary
    "budapest": (47.5, 19.0, 47.6, 19.2),
    # Romania
    "bucharest": (44.4, 26.1, 44.5, 26.3),
    # Greece
    "athens": (37.9, 23.7, 38.0, 23.9),
    # Portugal
    "lisbon": (38.7, -9.2, 38.8, -9.0),
    "porto": (41.1, -8.7, 41.2, -8.5),
    # Netherlands
    "amsterdam": (52.3, 4.8, 52.5, 5.1),
    # Belgium
    "brussels": (50.8, 4.3, 50.9, 4.5),
    # Switzerland
    "zurich": (47.3, 8.5, 47.4, 8.7),
    # Austria
    "vienna": (48.2, 16.3, 48.3, 16.5),
    # Sweden
    "stockholm": (59.3, 18.0, 59.4, 18.2),
    # Norway
    "oslo": (59.9, 10.7, 60.0, 10.9),
    # Denmark
    "copenhagen": (55.7, 12.5, 55.8, 12.7),
    # Finland
    "helsinki": (60.2, 24.9, 60.3, 25.1),
    # Ireland
    "dublin": (53.3, -6.3, 53.4, -6.1),
    # New Zealand
    "auckland": (-36.9, 174.7, -36.7, 174.9),
    "wellington": (-41.3, 174.8, -41.2, 175.0),
    # Singapore
    "singapore": (1.3, 103.7, 1.4, 103.9),
    # Thailand
    "bangkok": (13.7, 100.5, 13.9, 100.7),
    "phuket": (7.8, 98.3, 7.9, 98.5),
    # Vietnam
    "ho chi minh": (10.8, 106.6, 10.9, 106.8),
    "hanoi": (21.0, 105.8, 21.1, 106.0),
    # Indonesia
    "jakarta": (-6.2, 106.8, -6.1, 107.0),
    "bali": (-8.7, 115.2, -8.5, 115.4),
    # Philippines
    "manila": (14.6, 120.9, 14.7, 121.1),
    # Malaysia
    "kuala lumpur": (3.1, 101.6, 3.3, 101.8),
    # Taiwan
    "taipei": (25.0, 121.5, 25.1, 121.7),
}

# Location to country mapping - ALL 195 COUNTRIES
LOCATION_COUNTRY = {
    # A
    "afghanistan": "Afghanistan", "albania": "Albania", "algeria": "Algeria",
    "andorra": "Andorra", "angola": "Angola", "antigua": "Antigua and Barbuda",
    "argentina": "Argentina", "armenia": "Armenia", "australia": "Australia",
    "austria": "Austria", "azerbaijan": "Azerbaijan",
    # B
    "bahamas": "Bahamas", "bahrain": "Bahrain", "bangladesh": "Bangladesh",
    "barbados": "Barbados", "belarus": "Belarus", "belgium": "Belgium",
    "belize": "Belize", "benin": "Benin", "bhutan": "Bhutan",
    "bolivia": "Bolivia", "bosnia": "Bosnia and Herzegovina", "botswana": "Botswana",
    "brazil": "Brazil", "brunei": "Brunei", "bulgaria": "Bulgaria",
    "burkina faso": "Burkina Faso", "burundi": "Burundi",
    # C
    "cambodia": "Cambodia", "cameroon": "Cameroon", "canada": "Canada",
    "cape verde": "Cape Verde", "central african republic": "Central African Republic",
    "chad": "Chad", "chile": "Chile", "china": "China", "colombia": "Colombia",
    "comoros": "Comoros", "congo": "Congo", "costa rica": "Costa Rica",
    "croatia": "Croatia", "cuba": "Cuba", "cyprus": "Cyprus",
    "czech republic": "Czech Republic", "czechia": "Czech Republic",
    # D
    "denmark": "Denmark", "djibouti": "Djibouti", "dominica": "Dominica",
    "dominican republic": "Dominican Republic", "dr congo": "DR Congo",
    # E
    "east timor": "East Timor", "ecuador": "Ecuador", "egypt": "Egypt",
    "el salvador": "El Salvador", "equatorial guinea": "Equatorial Guinea",
    "eritrea": "Eritrea", "estonia": "Estonia", "eswatini": "Eswatini",
    "ethiopia": "Ethiopia",
    # F
    "fiji": "Fiji", "finland": "Finland", "france": "France",
    # G
    "gabon": "Gabon", "gambia": "Gambia", "georgia": "Georgia",
    "germany": "Germany", "ghana": "Ghana", "greece": "Greece",
    "grenada": "Grenada", "guatemala": "Guatemala", "guinea": "Guinea",
    "guinea-bissau": "Guinea-Bissau", "guyana": "Guyana",
    # H
    "haiti": "Haiti", "honduras": "Honduras", "hungary": "Hungary",
    # I
    "iceland": "Iceland", "india": "India", "indonesia": "Indonesia",
    "iran": "Iran", "iraq": "Iraq", "ireland": "Ireland", "israel": "Israel",
    "italy": "Italy", "ivory coast": "Ivory Coast",
    # J
    "jamaica": "Jamaica", "japan": "Japan", "jordan": "Jordan",
    # K
    "kazakhstan": "Kazakhstan", "kenya": "Kenya", "kiribati": "Kiribati",
    "kosovo": "Kosovo", "kuwait": "Kuwait", "kyrgyzstan": "Kyrgyzstan",
    # L
    "laos": "Laos", "latvia": "Latvia", "lebanon": "Lebanon",
    "lesotho": "Lesotho", "liberia": "Liberia", "libya": "Libya",
    "liechtenstein": "Liechtenstein", "lithuania": "Lithuania",
    "luxembourg": "Luxembourg",
    # M
    "madagascar": "Madagascar", "malawi": "Malawi", "malaysia": "Malaysia",
    "maldives": "Maldives", "mali": "Mali", "malta": "Malta",
    "marshall islands": "Marshall Islands", "mauritania": "Mauritania",
    "mauritius": "Mauritius", "mexico": "Mexico", "micronesia": "Micronesia",
    "moldova": "Moldova", "monaco": "Monaco", "mongolia": "Mongolia",
    "montenegro": "Montenegro", "morocco": "Morocco", "mozambique": "Mozambique",
    "myanmar": "Myanmar",
    # N
    "namibia": "Namibia", "nauru": "Nauru", "nepal": "Nepal",
    "netherlands": "Netherlands", "new zealand": "New Zealand",
    "nicaragua": "Nicaragua", "niger": "Niger", "nigeria": "Nigeria",
    "north korea": "North Korea", "north macedonia": "North Macedonia",
    "norway": "Norway",
    # O
    "oman": "Oman",
    # P
    "pakistan": "Pakistan", "palau": "Palau", "palestine": "Palestine",
    "panama": "Panama", "papua new guinea": "Papua New Guinea",
    "paraguay": "Paraguay", "peru": "Peru", "philippines": "Philippines",
    "poland": "Poland", "portugal": "Portugal",
    # Q
    "qatar": "Qatar",
    # R
    "romania": "Romania", "russia": "Russia", "rwanda": "Rwanda",
    # S
    "saint kitts": "Saint Kitts and Nevis", "saint lucia": "Saint Lucia",
    "saint vincent": "Saint Vincent and the Grenadines",
    "samoa": "Samoa", "san marino": "San Marino",
    "sao tome": "Sao Tome and Principe", "saudi arabia": "Saudi Arabia",
    "senegal": "Senegal", "serbia": "Serbia", "seychelles": "Seychelles",
    "sierra leone": "Sierra Leone", "singapore": "Singapore",
    "slovakia": "Slovakia", "slovenia": "Slovenia",
    "solomon islands": "Solomon Islands", "somalia": "Somalia",
    "south africa": "South Africa", "south korea": "South Korea",
    "south sudan": "South Sudan", "spain": "Spain", "sri lanka": "Sri Lanka",
    "sudan": "Sudan", "suriname": "Suriname", "sweden": "Sweden",
    "switzerland": "Switzerland", "syria": "Syria",
    # T
    "taiwan": "Taiwan", "tajikistan": "Tajikistan", "tanzania": "Tanzania",
    "thailand": "Thailand", "togo": "Togo", "tonga": "Tonga",
    "trinidad": "Trinidad and Tobago", "tunisia": "Tunisia",
    "turkey": "Turkey", "turkmenistan": "Turkmenistan", "tuvalu": "Tuvalu",
    # U
    "uganda": "Uganda", "ukraine": "Ukraine",
    "united arab emirates": "UAE", "uae": "UAE",
    "united kingdom": "UK", "uk": "UK", "england": "UK",
    "united states": "USA", "usa": "USA", "america": "USA",
    "uruguay": "Uruguay", "uzbekistan": "Uzbekistan",
    # V
    "vanuatu": "Vanuatu", "vatican city": "Vatican City",
    "venezuela": "Venezuela", "vietnam": "Vietnam",
    # Y
    "yemen": "Yemen",
    # Z
    "zambia": "Zambia", "zimbabwe": "Zimbabwe",
    # Major cities → country (for direct lookup)
    "agadir": "Morocco", "marrakech": "Morocco", "casablanca": "Morocco",
    "rabat": "Morocco", "tangier": "Morocco", "fes": "Morocco",
    "meknes": "Morocco", "essaouira": "Morocco", "chefchaouen": "Morocco",
    "new york": "USA", "los angeles": "USA", "chicago": "USA",
    "miami": "USA", "san francisco": "USA", "seattle": "USA",
    "boston": "USA", "atlanta": "USA", "phoenix": "USA",
    "denver": "USA", "nashville": "USA", "detroit": "USA",
    "philadelphia": "USA", "austin": "USA", "dallas": "USA",
    "houston": "USA", "las vegas": "USA", "washington": "USA",
    "portland": "USA", "san diego": "USA", "detroit": "USA",
    "london": "UK", "manchester": "UK", "birmingham": "UK",
    "edinburgh": "UK", "glasgow": "UK", "liverpool": "UK",
    "paris": "France", "lyon": "France", "marseille": "France",
    "nice": "France", "bordeaux": "France", "toulouse": "France",
    "nantes": "France", "strasbourg": "France",
    "tokyo": "Japan", "osaka": "Japan", "kyoto": "Japan",
    "hiroshima": "Japan", "nagoya": "Japan", "fukuoka": "Japan",
    "sapporo": "Japan",
    "dubai": "UAE", "abu dhabi": "UAE", "sharjah": "UAE",
    "berlin": "Germany", "munich": "Germany", "hamburg": "Germany",
    "frankfurt": "Germany", "cologne": "Germany", "stuttgart": "Germany",
    "dusseldorf": "Germany",
    "madrid": "Spain", "barcelona": "Spain", "seville": "Spain",
    "valencia": "Spain", "malaga": "Spain", "bilbao": "Spain",
    "rome": "Italy", "milan": "Italy", "naples": "Italy",
    "florence": "Italy", "venice": "Italy", "turin": "Italy",
    "seoul": "South Korea", "busan": "South Korea",
    "beijing": "China", "shanghai": "China", "hong kong": "China",
    "shenzhen": "China", "guangzhou": "China",
    "mumbai": "India", "delhi": "India", "bangalore": "India",
    "chennai": "India", "kolkata": "India", "hyderabad": "India",
    "pune": "India",
    "sao paulo": "Brazil", "rio de janeiro": "Brazil",
    "brasilia": "Brazil", "salvador": "Brazil", "fortaleza": "Brazil",
    "buenos aires": "Argentina",
    "mexico city": "Mexico", "cancun": "Mexico",
    "bogota": "Colombia", "medellin": "Colombia",
    "santiago": "Chile", "lima": "Peru",
    "toronto": "Canada", "vancouver": "Canada", "montreal": "Canada",
    "calgary": "Canada", "ottawa": "Canada",
    "sydney": "Australia", "melbourne": "Australia",
    "brisbane": "Australia", "perth": "Australia",
    "moscow": "Russia", "saint petersburg": "Russia",
    "warsaw": "Poland", "krakow": "Poland",
    "prague": "Czech Republic", "budapest": "Hungary",
    "bucharest": "Romania", "athens": "Greece",
    "lisbon": "Portugal", "porto": "Portugal",
    "amsterdam": "Netherlands", "brussels": "Belgium",
    "zurich": "Switzerland", "vienna": "Austria",
    "stockholm": "Sweden", "oslo": "Norway",
    "copenhagen": "Denmark", "helsinki": "Finland",
    "dublin": "Ireland",
    "auckland": "New Zealand", "wellington": "New Zealand",
    "singapore": "Singapore",
    "bangkok": "Thailand", "phuket": "Thailand",
    "ho chi minh": "Vietnam", "hanoi": "Vietnam",
    "jakarta": "Indonesia", "bali": "Indonesia",
    "manila": "Philippines",
    "kuala lumpur": "Malaysia",
    "taipei": "Taiwan",
    "istanbul": "Turkey", "ankara": "Turkey", "izmir": "Turkey",
    "cairo": "Egypt", "alexandria": "Egypt",
    "lagos": "Nigeria", "abuja": "Nigeria",
    "cape town": "South Africa", "johannesburg": "South Africa",
    "durban": "South Africa",
    "nairobi": "Kenya", "addis ababa": "Ethiopia",
    "accra": "Ghana", "dar es salaam": "Tanzania",
    "riyadh": "Saudi Arabia", "jeddah": "Saudi Arabia", "mecca": "Saudi Arabia",
}


class GoogleMapsScraper:
    """Scrapes business data from multiple worldwide sources."""

    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config or ScraperConfig()
        self._overpass_endpoints = [
            "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
            "https://lz4.overpass-api.de/api/interpreter",
            "https://z.overpass-api.de/api/interpreter",
            "https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter",
        ]
        self.web_cache = WebSearchCache()
        self._search_crawler = None
        self._direct_crawler = None

    def _sleep(self, base: float):
        """Sleep with fast_mode reduction."""
        if self.config.fast_mode:
            time.sleep(base * 0.2)
        else:
            time.sleep(base)

    def search(self, query: str, location: str, max_results: int = 30) -> List[Lead]:
        """Search for businesses worldwide using multiple sources."""
        leads = []

        # Detect country from location
        country = self._detect_country(location)

        # Expand query to all relevant languages
        expanded_queries = expand_query(query, country)
        print(f"\n    Searching: '{query}' in {location} ({country})")
        if len(expanded_queries) > 1:
            latin_queries = [q for q in expanded_queries if q.isascii()]
            print(f"    Expanded to: {len(expanded_queries)} languages ({', '.join(latin_queries[:4])})")

        # Get OSM tags
        osm_amenity = get_osm_amenity(query)
        print(f"    OSM amenity: {osm_amenity}")

        # Source 1: Overpass API (worldwide, structured data)
        overpass_leads = self._search_overpass(query, location, max_results, osm_amenity)
        leads.extend(overpass_leads)
        print(f"      Overpass: {len(overpass_leads)} results")

        # Source 2: Nominatim (additional details)
        english_queries = [q for q in expanded_queries if q.isascii()]
        for eq in english_queries[:2]:
            osm_leads = self._search_nominatim(eq, location, max_results // max(len(english_queries[:2]), 1))
            leads.extend(osm_leads)
        nom_count = len(leads) - len(overpass_leads)
        print(f"      Nominatim: {nom_count} results")

        # Source 3: Wikidata SPARQL
        try:
            from lead_generator.scrapers.wikidata import WikidataScraper
            wikidata = WikidataScraper(self.config)
            wikidata_leads = wikidata.search(query, location, country, max_results // 3)
            leads.extend(wikidata_leads)
            print(f"      Wikidata: {len(wikidata_leads)} results")
        except Exception as e:
            print(f"      Wikidata: Error - {e}")

        # Source 4: Bing Search (strongest web source - many query variations)
        try:
            bing_leads = self._search_bing_web(query, location, max_results)
            leads.extend(bing_leads)
            print(f"      Bing Web: {len(bing_leads)} results")
        except Exception as e:
            print(f"      Bing Web: Error - {e}")

        # Source 5: Bing Maps (structured business data)
        try:
            bing_maps_leads = self._search_bing_maps(query, location, max_results // 2)
            leads.extend(bing_maps_leads)
            print(f"      Bing Maps: {len(bing_maps_leads)} results")
        except Exception as e:
            print(f"      Bing Maps: Error - {e}")

        # Source 6: Overpass with ALL expanded queries (different languages)
        for eq in english_queries[1:3]:
            try:
                extra_leads = self._search_overpass(eq, location, max_results // 3, osm_amenity)
                leads.extend(extra_leads)
            except Exception:
                pass

        # Source 7: SearXNG (aggregates multiple search engines)
        if len(leads) < max_results // 2:
            try:
                searxng_leads = self._search_searxng(query, location, max_results // 3)
                leads.extend(searxng_leads)
                if searxng_leads:
                    print(f"      SearXNG: {len(searxng_leads)} results")
            except Exception:
                pass

        # Source 8: Mojeek (independent, no blocking)
        if len(leads) < max_results // 2:
            try:
                mojeek_leads = self._search_mojeek(query, location, max_results // 4)
                leads.extend(mojeek_leads)
                if mojeek_leads:
                    print(f"      Mojeek: {len(mojeek_leads)} results")
            except Exception:
                pass

        # Auto-fill city/country from location parameter
        city_from_location = location.split(",")[0].strip() if location else ""
        for lead in leads:
            if not lead.country:
                lead.country = country
            if not lead.city and city_from_location:
                lead.city = city_from_location

        # Deduplicate - keep best version of each business
        seen = {}
        unique_leads = []
        for lead in leads:
            # Clean business name
            name = lead.business_name.strip()
            if not name or len(name) < 3:
                continue

            key = name.lower()
            if key in seen:
                prev_lead = seen[key]
                # Keep the one with more data
                prev_score = (1 if prev_lead.phone else 0) + (1 if prev_lead.email else 0) + (1 if prev_lead.website else 0) + (1 if prev_lead.address else 0)
                new_score = (1 if lead.phone else 0) + (1 if lead.email else 0) + (1 if lead.website else 0) + (1 if lead.address else 0)
                if new_score > prev_score:
                    idx = unique_leads.index(prev_lead)
                    unique_leads[idx] = lead
                    seen[key] = lead
            else:
                seen[key] = lead
                unique_leads.append(lead)

        print(f"    Total unique: {len(unique_leads)} businesses")
        return unique_leads[:max_results]

    def _detect_country(self, location: str) -> str:
        """Detect country from location string."""
        return detect_country(location)

    def scrape_google_maps_url(self, url: str, max_results: int = 50) -> List[Lead]:
        """Scrape businesses from a Google Maps URL."""
        leads = []
        print(f"\n    Parsing Google Maps URL...")

        # Resolve short URLs
        url = self._resolve_short_url(url)

        query, location = self._parse_maps_url(url)

        if query or location:
            print(f"    Extracted: query='{query}', location='{location}'")
            leads = self.search(query or "business", location or "", max_results)
        else:
            print(f"    Could not parse URL, trying as search term...")
            # Try to extract any useful info from URL
            if "/" in url:
                parts = url.split("/")[-1].replace("+", " ").replace("%20", " ")
                leads = self.search(parts, "", max_results)

        return leads

    def _resolve_short_url(self, url: str) -> str:
        """Resolve short URLs like goo.gl, maps.app.goo.gl"""
        if "goo.gl" in url or "maps.app.goo.gl" in url or "bit.ly" in url:
            try:
                resp = requests.head(url, allow_redirects=True, timeout=10,
                                    headers={"User-Agent": random.choice(USER_AGENTS)})
                return resp.url
            except Exception:
                pass
        return url

    def _search_overpass(self, query: str, location: str, max_results: int, osm_amenity: str = "") -> List[Lead]:
        """Search Overpass API for businesses worldwide with multiple tag strategies."""
        leads = []
        bbox = self._get_bbox(location)
        if not bbox:
            bbox = self._geocode_location(location)
        if not bbox:
            return leads

        s, w, n, e = bbox
        all_tags = get_osm_tags(query)
        tag_variations = []
        if osm_amenity:
            tag_variations.append(f'["amenity"="{osm_amenity}"]')
        for tag_key, tag_val in all_tags[:8]:
            tag_variations.append(f'["{tag_key}"="{tag_val}"]')
        tag_variations.append(f'["name"~"{query}",i]')
        tag_variations.append(f'["name"~"{query.split()[0] if query else query}",i]')
        # Add healthcare and office tag variations for medical/legal businesses
        if any(x in query.lower() for x in ["dentist", "doctor", "clinic", "pharmacy", "hospital"]):
            tag_variations.append(f'["healthcare"="{query.lower()}"]')
            tag_variations.append(f'["amenity"="clinic"]')
        if any(x in query.lower() for x in ["lawyer", "avocat", "accountant", "notaire"]):
            tag_variations.append(f'["office"="lawyer"]')
            tag_variations.append(f'["office"="accountant"]')

        seen_ids = set()
        for tag_filter in tag_variations:
            overpass_query = f"""[out:json][timeout:60];
            (
              node{tag_filter}({s},{w},{n},{e});
              way{tag_filter}({s},{w},{n},{e});
            );
            out body;"""
            for endpoint in self._overpass_endpoints:
                try:
                    r = requests.post(endpoint, data={"data": overpass_query}, timeout=90)
                    if r.status_code == 200:
                        data = r.json()
                        for e in data.get("elements", []):
                            eid = e.get("id")
                            if eid in seen_ids:
                                continue
                            seen_ids.add(eid)
                            lead = self._parse_overpass_element(e)
                            if lead:
                                leads.append(lead)
                        break
                except Exception:
                    continue
            if len(leads) >= max_results:
                break

        return leads[:max_results]

    def _get_bbox(self, location: str) -> Optional[Tuple[float, float, float, float]]:
        """Get bounding box for a location, expanded by ~25km in all directions."""
        loc_lower = location.lower().strip()
        for key, bbox in CITY_BBOX.items():
            if key in loc_lower:
                s, w, n, e = bbox
                # Expand by ~0.25 degrees (~25km)
                return (s - 0.25, w - 0.25, n + 0.25, e + 0.25)
        return None

    def _parse_overpass_element(self, element: dict) -> Optional[Lead]:
        """Parse an Overpass API element into a Lead."""
        try:
            tags = element.get("tags", {})

            # Get name - use amenity type as fallback
            name = tags.get("name", tags.get("name:en", tags.get("name:fr",
                    tags.get("name:ar", tags.get("alt_name", "")))))
            if not name:
                amenity = tags.get("amenity", tags.get("shop", ""))
                if amenity:
                    osm_id = element.get("id", "")
                    name = "%s #%s" % (amenity.replace("_", " ").title(), osm_id)
                else:
                    return None
            if not name:
                return None

            lead = Lead()
            lead.source = "overpass"
            lead.business_name = name

            # Contact info
            from lead_generator.utils.cleaner import clean_phone, clean_email
            raw_phone = tags.get("phone", tags.get("contact:phone", tags.get("phone:international", "")))
            lead.phone = clean_phone(raw_phone)
            raw_email = tags.get("email", tags.get("contact:email", tags.get("email:internet", "")))
            lead.website = tags.get("website", tags.get("contact:website", ""))
            if raw_email:
                from lead_generator.utils.cleaner import clean_email
                cleaned = clean_email(raw_email)
                if cleaned:
                    lead.email = cleaned
                    lead.all_emails = [cleaned]

            # Address
            street = tags.get("addr:street", "")
            number = tags.get("addr:housenumber", "")
            city = tags.get("addr:city", "")
            state = tags.get("addr:state", "")
            postcode = tags.get("addr:postcode", "")
            country = tags.get("addr:country", "")

            if street:
                lead.address = f"{number} {street}".strip() if number else street
            if city:
                lead.city = city
            if state:
                lead.state = state
            if postcode:
                lead.zip_code = postcode
            if country:
                # Convert country code to name
                country_map = {
                    "MA": "Morocco", "US": "USA", "GB": "UK", "FR": "France",
                    "DE": "Germany", "ES": "Spain", "IT": "Italy", "JP": "Japan",
                    "BR": "Brazil", "IN": "India", "AU": "Australia", "CA": "Canada",
                    "AE": "UAE", "SA": "Saudi Arabia", "TR": "Turkey", "EG": "Egypt",
                    "NG": "Nigeria", "ZA": "South Africa", "TH": "Thailand",
                    "SG": "Singapore", "MY": "Malaysia", "ID": "Indonesia",
                    "PH": "Philippines", "VN": "Vietnam", "KR": "South Korea",
                    "TW": "Taiwan", "CN": "China", "RU": "Russia", "NL": "Netherlands",
                    "BE": "Belgium", "CH": "Switzerland", "AT": "Austria", "PT": "Portugal",
                    "IE": "Ireland", "SE": "Sweden", "NO": "Norway", "DK": "Denmark",
                    "FI": "Finland", "PL": "Poland", "CZ": "Czech Republic",
                    "RO": "Romania", "HR": "Croatia", "NZ": "New Zealand",
                    "AR": "Argentina", "CL": "Chile", "CO": "Colombia", "PE": "Peru",
                }
                lead.country = country_map.get(country.upper(), country)

            # Category - read all tag types
            lead.category = tags.get("amenity", tags.get("shop", tags.get("tourism",
                           tags.get("healthcare", tags.get("leisure", tags.get("craft",
                           tags.get("office", "")))))))
            if lead.category:
                lead.category = lead.category.replace("_", " ").title()

            # Social media
            lead.facebook = tags.get("facebook", tags.get("contact:facebook", ""))
            lead.instagram = tags.get("instagram", tags.get("contact:instagram", ""))
            lead.twitter = tags.get("twitter", tags.get("contact:twitter", ""))
            lead.linkedin = tags.get("linkedin", tags.get("contact:linkedin", ""))

            # Hours
            hours = tags.get("opening_hours", "")
            if hours:
                lead.operating_hours = hours

            # OSM link
            osm_id = element.get("id", "")
            osm_type = element.get("type", "node")
            lead.google_maps_url = f"https://www.openstreetmap.org/{osm_type}/{osm_id}"

            # Coordinates
            lat = element.get("lat")
            lon = element.get("lon")
            if lat and lon:
                lead.google_maps_url += f"#map=16/{lat}/{lon}"

            return lead

        except Exception:
            return None

    def _geocode_location(self, location: str) -> Optional[Tuple[float, float, float, float]]:
        """Geocode a location using Nominatim and return bounding box."""
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": location,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
        }
        headers = {"User-Agent": "LeadGenerator/1.0 (research)"}

        for attempt in range(3):
            try:
                r = requests.get(url, params=params, headers=headers, timeout=20)
                if r.status_code == 200:
                    results = r.json()
                    if results:
                        if "boundingbox" in results[0]:
                            bb = results[0]["boundingbox"]
                            bbox = (float(bb[0]), float(bb[2]), float(bb[1]), float(bb[3]))
                            return bbox
                        lat = float(results[0]["lat"])
                        lon = float(results[0]["lon"])
                        delta = 0.15
                        return (lat - delta, lon - delta, lat + delta, lon + delta)
                    return None
                elif r.status_code == 429:
                    self._sleep(2 * (attempt + 1))
                    continue
                else:
                    return None
            except requests.exceptions.Timeout:
                self._sleep(2 * (attempt + 1))
                continue
            except Exception:
                return None
        return None

    def find_website_for_lead(self, lead: Lead) -> Optional[str]:
        """Try to find a website for a business.
        
        1. Check web search cache first (instant)
        2. Try Bing search (fastest, works everywhere)
        """
        if lead.website:
            return lead.website

        cached = self.web_cache.find_website_for_lead(lead)
        if cached:
            return cached

        if not hasattr(self, '_direct_crawler') or self._direct_crawler is None:
            from lead_generator.scrapers.crawler import AntiBypassCrawler
            self._direct_crawler = AntiBypassCrawler(
                timeout=6, max_retries=1, fast_mode=True,
                use_free_proxies=False,
            )

        name = lead.business_name
        city = lead.city or ""
        country = lead.country or ""

        # Build location-aware search queries
        country_domain = ""
        if country:
            country_lower = country.lower()
            if "morocco" in country_lower or "maroc" in country_lower:
                country_domain = "site:.ma"
            elif "france" in country_lower:
                country_domain = "site:.fr"
            elif "usa" in country_lower or "united states" in country_lower:
                country_domain = "site:.com"
            elif "uk" in country_lower or "united kingdom" in country_lower:
                country_domain = "site:.co.uk"

        search_queries = [
            '"%s" %s %s' % (name, city, country_domain) if country_domain else '"%s" %s' % (name, city),
            '"%s" %s official site -facebook' % (name, city),
            '%s %s contact website -wikipedia' % (name, city),
        ]

        skip_domains = ["bing.com", "google.com", "duckduckgo.com",
                        "wikipedia.org", "facebook.com", "linkedin.com",
                        "instagram.com", "twitter.com", "yelp.com",
                        "tripadvisor.com", "yellowpages.com"]

        for idx, search_term in enumerate(search_queries):
            try:
                if idx > 0:
                    time.sleep(1)
                url = f"https://www.bing.com/search?q={quote_plus(search_term)}&count=5"
                html = self._direct_crawler.fetch(url, use_referrer=False, accept_gzip=False)
                if not html or len(html) < 500:
                    html = self._direct_crawler.fetch(url, use_referrer=False, accept_gzip=False)
                if not html:
                    continue
                soup = BeautifulSoup(html, "lxml")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if not href.startswith("http"):
                        continue
                    if any(x in href for x in skip_domains):
                        continue
                    title = a.get_text(strip=True).lower()
                    if name.lower().split()[0] in title or name.lower() in title:
                        return href
            except Exception:
                pass

        return None

    def _search_nominatim(self, query: str, location: str, max_results: int) -> List[Lead]:
        """Search Nominatim for additional business details with multiple queries."""
        leads = []
        seen_names = set()

        try:
            crawler = self._get_search_crawler()
            city = location.split(",")[0].strip()
            country = self._detect_country(location)

            # Multiple query variations to find more businesses
            search_terms = [
                f"{query} {city}",
                f"{query} {city} {country}" if country else f"{query} {city}",
                f"{query} {city} contact",
            ]

            for search_term in search_terms:
                search_url = "https://nominatim.openstreetmap.org/search"
                params = {
                    "q": search_term,
                    "format": "json",
                    "limit": min(max_results, 50),
                    "addressdetails": 1,
                    "extratags": 1,
                    "namedetails": 1,
                }

                headers = {"User-Agent": "LeadGenerator/1.0 (research)", "Accept": "application/json"}
                try:
                    resp = requests.get(search_url, params=params, headers=headers, timeout=15)
                    if resp.status_code != 200:
                        continue
                    results = resp.json()
                except Exception:
                    continue

                for item in results[:max_results]:
                    try:
                        name = item.get("name", "")
                        namedetails = item.get("namedetails", {})
                        if not name and namedetails:
                            name = namedetails.get("name", namedetails.get("name:en", namedetails.get("name:fr", "")))
                        if not name:
                            display = item.get("display_name", "")
                            name = display.split(",")[0].strip()

                        if not name or len(name) < 3:
                            continue
                        name_key = name.lower().strip()
                        if name_key in seen_names:
                            continue
                        seen_names.add(name_key)

                        lead = Lead()
                        lead.source = "nominatim"
                        lead.business_name = name
                        lead.address = item.get("display_name", "")

                        addr = item.get("address", {})
                        lead.city = addr.get("city", addr.get("town", addr.get("village", addr.get("hamlet", ""))))
                        lead.state = addr.get("state", addr.get("region", ""))
                        lead.zip_code = addr.get("postcode", "")
                        lead.country = addr.get("country", "")

                        osm_type = item.get("type", item.get("class", ""))
                        lead.category = osm_type.replace("_", " ").title() if osm_type else ""

                        extras = item.get("extratags", {})
                        from lead_generator.utils.cleaner import clean_phone, clean_email
                        raw_phone = extras.get("phone", extras.get("contact:phone", ""))
                        lead.phone = clean_phone(raw_phone)
                        lead.website = extras.get("website", extras.get("contact:website", ""))
                        raw_email = extras.get("email", extras.get("contact:email", ""))
                        cleaned_email = clean_email(raw_email)
                        if cleaned_email:
                            lead.email = cleaned_email
                            lead.all_emails = [cleaned_email]

                        lead.facebook = extras.get("facebook", extras.get("contact:facebook", ""))
                        lead.instagram = extras.get("instagram", extras.get("contact:instagram", ""))

                        osm_id = item.get("osm_id", "")
                        osm_type_id = item.get("osm_type", "")
                        lead.google_maps_url = f"https://www.openstreetmap.org/{osm_type_id}/{osm_id}"

                        leads.append(lead)

                    except Exception:
                        continue

                if len(leads) >= max_results:
                    break
                self._sleep(1.0)  # Nominatim rate limit

        except Exception as e:
            print(f"      Nominatim error: {e}")

        return leads[:max_results]

    def _parse_maps_url(self, url: str) -> Tuple[str, str]:
        """Extract search query and location from Google Maps URL.
        
        Handles:
        - /maps/search/dentist+agadir
        - /maps/search/dentist+in+agadir
        - /maps?q=dentist+agadir
        - /maps/place/...
        - /maps/@lat,lng,zoom
        - goo.gl/maps/... short links
        - maps.app.goo.gl/... share links
        """
        query = ""
        location = ""

        try:
            clean_url = re.sub(r"@[-\d.]+,[-\d.]+,\d+z.*$", "", url)
            clean_url = re.sub(r"\?.*$", "", clean_url)

            if "/maps/search/" in clean_url:
                search_part = clean_url.split("/maps/search/")[-1]
                search_part = unquote(search_part).replace("+", " ")

                parts = search_part.split(" in ", 1)
                if len(parts) == 2:
                    query, location = parts
                else:
                    parts = search_part.split(" near ", 1)
                    if len(parts) == 2:
                        query, location = parts
                    else:
                        query = search_part

            elif "q=" in url:
                params = parse_qs(urlparse(url).query)
                q = params.get("q", [""])[0]
                q = unquote(q).replace("+", " ")

                parts = q.split(" in ", 1)
                if len(parts) == 2:
                    query, location = parts
                else:
                    parts = q.split(" near ", 1)
                    if len(parts) == 2:
                        query, location = parts
                    else:
                        query = q

            elif "/maps/place/" in clean_url:
                place_match = re.search(r"/maps/place/([^/@]+)", clean_url)
                if place_match:
                    query = unquote(place_match.group(1)).replace("+", " ").replace("-", " ")

                addr_match = re.search(r"place/[^/]+/([^/@]+)", clean_url)
                if addr_match:
                    location = unquote(addr_match.group(1)).replace("+", " ")

            elif "/maps/dir/" in clean_url:
                dir_match = re.search(r"/maps/dir/([^/]+)", clean_url)
                if dir_match:
                    query = unquote(dir_match.group(1)).replace("+", " ")

            else:
                q_match = re.search(r"[?&]q=([^&]+)", url)
                if q_match:
                    query = unquote(q_match.group(1)).replace("+", " ")

            if query:
                query = re.sub(r"@.*$", "", query).strip()
                query = re.sub(r",\s*$", "", query).strip()
                query = re.sub(r"/.*$", "", query).strip()

            if location:
                location = re.sub(r"/.*$", "", location).strip()
                location = re.sub(r"@\d.*$", "", location).strip()

            if query and not location:
                words = query.split()
                if len(words) >= 2:
                    potential_location = " ".join(words[1:])
                    query = words[0]
                    location = potential_location

        except Exception as e:
            print(f"      URL parse error: {e}")

        return query.strip(), location.strip()

    def _get_search_crawler(self):
        """Get or create the anti-bypass search crawler."""
        if not self._search_crawler:
            from lead_generator.scrapers.crawler import AntiBypassCrawler
            self._search_crawler = AntiBypassCrawler(
                timeout=10, max_retries=2, fast_mode=self.config.fast_mode,
                proxy_server=self.config.proxy_server,
                proxy_list_file=self.config.proxy_list_file,
                use_free_proxies=self.config.use_free_proxies,
                free_proxy_refresh_interval=self.config.free_proxy_refresh_interval,
            )
        return self._search_crawler

    def _search_bing_maps(self, query: str, location: str, max_results: int) -> List[Lead]:
        """Search Bing Maps for businesses with structured data."""
        leads = []
        seen_titles = set()
        try:
            crawler = self._get_search_crawler()
            queries = [
                f"{query} in {location}",
                f"{query} near {location}",
            ]
            for search_query in queries:
                url = f"https://www.bing.com/maps?q={quote_plus(search_query)}&count={max_results}"
                html = crawler.fetch(url, use_referrer=False, accept_gzip=False)
                if not html:
                    continue
                soup = BeautifulSoup(html, "lxml")
                # Bing Maps stores data in JSON-LD or data attributes
                for script in soup.find_all("script", type="application/ld+json"):
                    try:
                        data = json.loads(script.string)
                        items = data if isinstance(data, list) else [data]
                        for item in items:
                            if isinstance(item, dict) and item.get("@type") in ("LocalBusiness", "Restaurant", "DentistOffice", "MedicalBusiness", "Store"):
                                name = item.get("name", "")
                                if not name or len(name) < 3 or name.lower() in seen_titles:
                                    continue
                                seen_titles.add(name.lower())
                                lead = Lead(business_name=name, source="bing_maps")
                                addr = item.get("address", {})
                                if isinstance(addr, dict):
                                    parts = [addr.get("streetAddress", ""), addr.get("addressLocality", ""), addr.get("addressRegion", "")]
                                    lead.address = ", ".join(p for p in parts if p)
                                    lead.city = addr.get("addressLocality", "")
                                    lead.country = addr.get("addressCountry", "")
                                lead.phone = item.get("telephone", "")
                                lead.email = item.get("email", "")
                                lead.website = item.get("url", "")
                                if lead.email:
                                    lead.all_emails = [lead.email]
                                leads.append(lead)
                    except Exception:
                        continue
                # Also try to extract from result cards
                for card in soup.find_all("div", class_=re.compile(r"card|result|listing")):
                    try:
                        title_el = card.find(["h2", "h3", "a"], class_=re.compile(r"title|name"))
                        title = title_el.get_text(strip=True) if title_el else ""
                        if not title or len(title) < 3 or title.lower() in seen_titles:
                            continue
                        seen_titles.add(title.lower())
                        lead = Lead(business_name=title, source="bing_maps")
                        phone_el = card.find(["span", "p"], class_=re.compile(r"phone|tel"))
                        if phone_el:
                            lead.phone = phone_el.get_text(strip=True)
                        addr_el = card.find(["span", "p", "address"], class_=re.compile(r"address|location"))
                        if addr_el:
                            lead.address = addr_el.get_text(strip=True)
                        leads.append(lead)
                    except Exception:
                        continue
                if len(leads) >= max_results:
                    break
        except Exception:
            pass
        return leads[:max_results]

    def _search_bing_web(self, query: str, location: str, max_results: int) -> List[Lead]:
        """Search Bing for businesses using anti-bypass crawler with retry logic."""
        leads = []
        seen_titles = set()
        try:
            crawler = self._get_search_crawler()
            city = location.split(",")[0].strip()
            country = self._detect_country(location)

            # Build location-aware queries
            country_domain = ""
            country_name = ""
            country_phone = ""
            if country == "Morocco":
                country_domain = "site:.ma"
                country_name = "Maroc"
                country_phone = "+212"
            elif country == "France":
                country_domain = "site:.fr"
                country_name = "France"
                country_phone = "+33"
            elif country == "USA":
                country_domain = "site:.com"
                country_name = "USA"
                country_phone = "+1"
            elif country == "UK":
                country_domain = "site:.co.uk"
                country_name = "UK"
                country_phone = "+44"
            else:
                country_domain = ""
                country_name = country or ""
                country_phone = ""

            queries = [
                f'{query} {city} {country_name} telephone email contact',
                f'{query} {city} {country_domain} -wikipedia' if country_domain else f'{query} {city} contact website -wikipedia',
                f'annuaire {query} {city} telephone adresse',
                f'{query} {city} site:linkedin.com -wikipedia',
                f'"{query}" "{city}" telephone {country_phone}' if country_phone else f'"{query}" "{city}" telephone contact',
            ]
            skip_domains = ["wikipedia.org", "merriam-webster", "dictionary",
                           "youtube.com", "reddit.com", "quora.com",
                           "facebook.com", "twitter.com", "instagram.com",
                           "linkedin.com/company", "google.com/maps"]

            consecutive_empty = 0
            for idx, search_query in enumerate(queries):
                # Rate-limit: wait between queries
                if idx > 0:
                    wait = 2.0 if consecutive_empty == 0 else 4.0
                    time.sleep(wait)

                url = f"https://www.bing.com/search?q={quote_plus(search_query)}&count={max_results}&setlang=fr"
                html = None
                # Retry up to 2 times per query
                for attempt in range(2):
                    html = crawler.fetch(url, use_referrer=False, accept_gzip=False)
                    if html and len(html) > 500:
                        break
                    if attempt == 0:
                        time.sleep(3)

                if not html or len(html) < 500:
                    consecutive_empty += 1
                    # If 3+ empty in a row, Bing is rate-limiting — stop
                    if consecutive_empty >= 3:
                        break
                    continue

                # Detect CAPTCHA / rate-limit page
                if "captcha" in html.lower() or "verify you are human" in html.lower():
                    consecutive_empty += 1
                    break

                consecutive_empty = 0
                soup = BeautifulSoup(html, "lxml")
                for h2 in soup.find_all("h2"):
                    try:
                        a = h2.find("a", href=True)
                        if not a:
                            continue
                        title = h2.get_text(strip=True)
                        link = a["href"]
                        if not title or len(title) < 5:
                            continue

                        skip_titles = ["wikipedia", "definition", "meaning", "dictionary",
                                       "what is", "how to", "jobs in", "salary",
                                       "amazon", "ebay", "aliexpress"]
                        if any(x in title.lower() for x in skip_titles):
                            continue

                        title_key = title.lower().strip()
                        if title_key in seen_titles:
                            continue
                        seen_titles.add(title_key)

                        if link.startswith("https://www.bing.com/ck/a"):
                            link_match = re.search(r"u=([^&]+)", link)
                            if link_match:
                                from urllib.parse import unquote
                                link = unquote(link_match.group(1))

                        if any(x in link.lower() for x in skip_domains):
                            continue

                        is_directory = any(d in link.lower() for d in [
                            "pagesjaunes.ma", "brownbook.net", "kompass.com",
                            "cylex.de", "mawilaya.com", "yellowpages"
                        ])

                        lead = Lead(business_name=title, source="bing")

                        parent = h2.find_parent("div", class_=re.compile(r"b_algo|b_caption"))
                        snippet = ""
                        if parent:
                            snippet = parent.get_text(strip=True)

                        phone_match = re.search(r"[\+]?[0-9]{2,3}[\s\-]?[0-9]{2,3}[\s\-]?[0-9]{2,3}[\s\-]?[0-9]{2,3}", snippet)
                        if phone_match:
                            lead.phone = phone_match.group(0).strip()

                        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", snippet)
                        if email_match:
                            lead.email = email_match.group(0)
                            lead.all_emails = [lead.email]

                        addr_match = re.search(
                            r"(?:(?:Rue|Avenue|Boulevard|Av\.|Bd\.|Cité|Hay|Quartier|Zone)\s+[A-Za-zÀ-ÿ\s\d,]+(?:\d{5})?)",
                            snippet, re.IGNORECASE
                        )
                        if addr_match:
                            lead.address = addr_match.group(0).strip()

                        if is_directory:
                            lead.source = "bing_directory"
                            if not lead.phone and not lead.email:
                                continue

                        if link.startswith("http"):
                            lead.website = link

                        leads.append(lead)
                    except Exception:
                        continue
                if len(leads) >= max_results:
                    break
        except Exception:
            pass
        return leads[:max_results]

    def _search_searxng(self, query: str, location: str, max_results: int) -> List[Lead]:
        """Search SearXNG (meta-search engine aggregating Google/Bing/DuckDuckGo)."""
        leads = []
        seen_titles = set()
        try:
            crawler = self._get_search_crawler()
            search_query = f"{query} {location} telephone email contact"
            results = crawler.search_searxng(search_query, max_results)
            for item in results:
                title = item.get("title", "")
                url = item.get("url", "")
                snippet = item.get("snippet", "")
                if not title or len(title) < 5:
                    continue
                title_key = title.lower().strip()
                if title_key in seen_titles:
                    continue
                seen_titles.add(title_key)
                skip_titles = ["wikipedia", "dictionary", "meaning", "what is",
                               "how to", "jobs in", "salary", "amazon", "ebay"]
                if any(x in title.lower() for x in skip_titles):
                    continue
                skip_domains = ["wikipedia.org", "merriam-webster", "dictionary",
                                "youtube.com", "reddit.com", "quora.com"]
                if any(x in url.lower() for x in skip_domains):
                    continue
                lead = Lead(business_name=title, source="searxng")
                if url.startswith("http"):
                    lead.website = url
                phone_match = re.search(r"[\+]?[0-9]{2,3}[\s\-]?[0-9]{2,3}[\s\-]?[0-9]{2,3}[\s\-]?[0-9]{2,3}", snippet)
                if phone_match:
                    lead.phone = phone_match.group(0).strip()
                email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", snippet)
                if email_match:
                    lead.email = email_match.group(0)
                leads.append(lead)
        except Exception:
            pass
        return leads[:max_results]

    def _search_mojeek(self, query: str, location: str, max_results: int) -> List[Lead]:
        """Search Mojeek (independent search engine, no blocking)."""
        leads = []
        seen_titles = set()
        try:
            crawler = self._get_search_crawler()
            search_query = f"{query} {location} contact email phone"
            results = crawler.search_mojeek(search_query, max_results)
            for item in results:
                title = item.get("title", "")
                url = item.get("url", "")
                snippet = item.get("snippet", "")
                if not title or len(title) < 5:
                    continue
                title_key = title.lower().strip()
                if title_key in seen_titles:
                    continue
                seen_titles.add(title_key)
                skip_titles = ["wikipedia", "dictionary", "meaning", "what is",
                               "how to", "amazon", "ebay"]
                if any(x in title.lower() for x in skip_titles):
                    continue
                lead = Lead(business_name=title, source="mojeek")
                if url.startswith("http"):
                    lead.website = url
                phone_match = re.search(r"[\+]?[0-9]{2,3}[\s\-]?[0-9]{2,3}[\s\-]?[0-9]{2,3}[\s\-]?[0-9]{2,3}", snippet)
                if phone_match:
                    lead.phone = phone_match.group(0).strip()
                email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", snippet)
                if email_match:
                    lead.email = email_match.group(0)
                leads.append(lead)
        except Exception:
            pass
        return leads[:max_results]
