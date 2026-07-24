"""
Wikidata SPARQL Scraper
=======================
Queries Wikidata for business data using SPARQL.
Free, no API key needed. Best for well-known businesses and chains.
"""

import sys
import time
from typing import List, Optional, Dict

import requests

from lead_generator.models.lead import Lead
from lead_generator.config import ScraperConfig

sys.stdout.reconfigure(encoding="utf-8")

# Business type to Wikidata QID mapping
WIKIDATA_TYPES = {
    "pharmacy": "Q200157",
    "restaurant": "Q200157",
    "hotel": "Q25112",
    "motel": "Q25112",
    "hostel": "Q44050",
    "dentist": "Q42513",
    "hospital": "Q16917",
    "clinic": "Q4260475",
    "school": "Q3918",
    "university": "Q3918",
    "bank": "Q22687",
    "supermarket": "Q160270",
    "bakery": "Q23399",
    "cafe": "Q186093",
    "bar": "Q186093",
    "gym": "Q847017",
    "hairdresser": "Q37136",
    "car_repair": "Q1336221",
    "lawyer": "Q484876",
    "accountant": "Q1055016",
    "real_estate": "Q134853",
    "optician": "Q180833",
    "jewelry": "Q1336221",
    "furniture": "Q1336221",
    "clothing": "Q1336221",
    "electronics": "Q1336221",
    "hardware": "Q1336221",
    "florist": "Q1336221",
    "bookstore": "Q1336221",
    "spa": "Q210848",
    "travel_agency": "Q1336221",
    "veterinary": "Q25168",
    "post_office": "Q16917",
    "cinema": "Q41253",
    "museum": "Q33506",
    "gas_station": "Q431041",
    "doctor": "Q42513",
    "plumber": "Q28389",
    "electrician": "Q28389",
    "carpenter": "Q28389",
    "locksmith": "Q28389",
    "painter": "Q28389",
    "photographer": "Q132191",
    "cleaning": "Q132191",
    "security": "Q132191",
    "insurance": "Q22687",
    "marketing_agency": "Q43229",
    "it_company": "Q43229",
    "construction_company": "Q43229",
    "pet_shop": "Q160270",
    "toy_store": "Q160270",
    "music_store": "Q160270",
    "bike_shop": "Q160270",
    "car_dealer": "Q160270",
    "shoe_store": "Q160270",
    "sports_store": "Q160270",
    "gift_shop": "Q160270",
    "stationery": "Q160270",
    "dry_cleaner": "Q132191",
    "laundry": "Q132191",
    "fast_food": "Q200157",
    "art_gallery": "Q33506",
    "coworking": "Q43229",
    "nursery": "Q3918",
    "catering": "Q200157",
    "event_hall": "Q200157",
    "marketplace": "Q160270",
    "parking": "Q431041",
    "taxi": "Q431041",
    "car_rental": "Q431041",
    "car_wash": "Q431041",
    "atm": "Q22687",
    "bureau_de_change": "Q22687",
    "ice_cream": "Q200157",
    "food_court": "Q200157",
    "nightclub": "Q186093",
    "theatre": "Q41253",
    "arts_centre": "Q33506",
    "community_centre": "Q33506",
    "library": "Q33506",
    "fuel": "Q431041",
    "convenience": "Q160270",
}

# Country to Wikidata QID mapping
COUNTRIES = {
    "morocco": "Q1007",
    "france": "Q142",
    "uk": "Q145",
    "united kingdom": "Q145",
    "usa": "Q30",
    "united states": "Q30",
    "japan": "Q17",
    "germany": "Q183",
    "spain": "Q29",
    "italy": "Q38",
    "brazil": "Q155",
    "india": "Q668",
    "canada": "Q16",
    "australia": "Q408",
    "china": "Q148",
    "russia": "Q159",
    "turkey": "Q43",
    "egypt": "Q79",
    "nigeria": "Q1033",
    "south africa": "Q258",
    "thailand": "Q869",
    "singapore": "Q334",
    "malaysia": "Q833",
    "indonesia": "Q252",
    "philippines": "Q928",
    "vietnam": "Q881",
    "south korea": "Q884",
    "taiwan": "Q865",
    "mexico": "Q96",
    "argentina": "Q414",
    "colombia": "Q739",
    "chile": "Q298",
    "peru": "Q419",
    "dubai": "Q612",
    "uae": "Q862",
    "saudi arabia": "Q851",
    "qatar": "Q834",
    "kuwait": "Q817",
    "bahrain": "Q398",
    "oman": "Q842",
    "jordan": "Q810",
    "lebanon": "Q822",
    "iraq": "Q796",
    "iran": "Q794",
    "pakistan": "Q843",
    "bangladesh": "Q902",
    "sri lanka": "Q854",
    "nepal": "Q837",
    "new zealand": "Q664",
    "ireland": "Q27",
    "netherlands": "Q55",
    "belgium": "Q31",
    "switzerland": "Q39",
    "portugal": "Q45",
    "poland": "Q20",
    "czech republic": "Q213",
    "hungary": "Q28",
    "romania": "Q218",
    "greece": "Q41",
    "sweden": "Q34",
    "norway": "Q20",
    "denmark": "Q35",
    "finland": "Q244",
    "austria": "Q40",
    "algeria": "Q262",
    "tunisia": "Q34",
    "libya": "Q1016",
    "sudan": "Q1037",
    "ethiopia": "Q115",
    "kenya": "Q114",
    "tanzania": "Q924",
    "ghana": "Q117",
    "cameroon": "Q1009",
    "senegal": "Q1041",
    "mali": "Q912",
    "burkina faso": "Q965",
    "niger": "Q1032",
    "chad": "Q657",
    "guinea": "Q1034",
    "ivory coast": "Q1008",
    "madagascar": "Q1019",
    "mozambique": "Q1029",
    "angola": "Q916",
    "zambia": "Q1039",
    "zimbabwe": "Q1040",
    "botswana": "Q1011",
    "namibia": "Q1030",
    "uganda": "Q1036",
    "rwanda": "Q1028",
    "burundi": "Q990",
    "somalia": "Q1045",
    "cuba": "Q241",
    "jamaica": "Q766",
    "dominican republic": "Q786",
    "trinidad": "Q754",
    "haiti": "Q790",
    "guatemala": "Q801",
    "honduras": "Q806",
    "el salvador": "Q812",
    "nicaragua": "Q811",
    "costa rica": "Q800",
    "panama": "Q804",
    "uruguay": "Q77",
    "paraguay": "Q733",
    "bolivia": "Q750",
    "ecuador": "Q736",
    "venezuela": "Q710",
    "guyana": "Q734",
    "suriname": "Q730",
    "afghanistan": "Q889",
    "albania": "Q222",
    "armenia": "Q399",
    "azerbaijan": "Q227",
    "bangladesh": "Q902",
    "belarus": "Q155",
    "bhutan": "Q918",
    "brunei": "921",
    "cambodia": "Q16917",
    "cyprus": "Q219",
    "east timor": "Q17173",
    "georgia": "Q230",
    "hong kong": "Q8646",
    "kazakhstan": "Q1527",
    "kyrgyzstan": "Q813",
    "laos": "Q816",
    "macau": "Q14773",
    "maldives": "Q826",
    "mongolia": "Q16655",
    "myanmar": "Q836",
    "north korea": "Q16656",
    "palestine": "Q167810",
    "tajikistan": "Q763",
    "turkmenistan": "Q874",
    "uzbekistan": "Q265",
    "yemen": "Q805",
    "andorra": "Q228",
    "liechtenstein": "Q34755",
    "luxembourg": "Q37",
    "malta": "Q233",
    "monaco": "Q336",
    "san marino": "Q239",
    "vatican city": "Q197",
    "estonia": "Q191",
    "latvia": "Q211",
    "lithuania": "Q37",
    "iceland": "Q189",
    "croatia": "Q224",
    "slovenia": "Q215",
    "slovakia": "Q214",
    "serbia": "Q403",
    "bosnia": "Q225",
    "montenegro": "Q236",
    "albania": "Q222",
    "north macedonia": "Q221",
    "moldova": "Q217",
    "ukraine": "Q212",
    "belarus": "Q155",
    "fiji": "Q253",
    "papua new guinea": "Q691",
    "solomon islands": "Q695",
    "vanuatu": "Q686",
    "samoa": "Q683",
    "tonga": "Q689",
    "micronesia": "Q702",
    "marshall islands": "Q700",
    "palau": "Q697",
    "nauru": "Q695",
    "tuvalu": "Q672",
    "kiribati": "Q701",
    "antigua": "Q781",
    "barbados": "Q778",
    "bahamas": "Q778",
    "belize": "Q242",
    "grenada": "Q769",
    "dominica": "Q784",
    "saint lucia": "Q760",
    "saint kitts": "Q763",
    "saint vincent": "Q764",
}


class WikidataScraper:
    """Queries Wikidata SPARQL for business data."""

    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config or ScraperConfig()
        self.base_url = "https://query.wikidata.org/sparql"

    def search(self, query: str, location: str, country: str = "",
               max_results: int = 30) -> List[Lead]:
        """Search Wikidata for businesses."""
        leads = []

        try:
            # Get Wikidata type QID
            query_lower = query.lower().strip()
            type_qid = WIKIDATA_TYPES.get(query_lower)
            if not type_qid:
                print(f"      Wikidata: No QID for '{query}'")
                return leads

            # Get country QID
            country_lower = country.lower().strip() if country else ""
            if not country_lower and location:
                # Try to detect country from location
                for key in COUNTRIES:
                    if key in location.lower():
                        country_lower = key
                        break

            country_qid = COUNTRIES.get(country_lower)
            if not country_qid:
                print(f"      Wikidata: No QID for country '{country_lower}'")
                return leads

            # Build SPARQL query - try with country first, then without
            sparql = f"""
            SELECT ?business ?businessLabel ?phone ?website ?address ?lat ?lon
            WHERE {{
              ?business wdt:P31 wd:{type_qid} .
              ?business wdt:P17 wd:{country_qid} .
              OPTIONAL {{ ?business wdt:P1329 ?phone . }}
              OPTIONAL {{ ?business wdt:P856 ?website . }}
              OPTIONAL {{ ?business wdt:P625 ?coord . }}
              OPTIONAL {{ ?business wdt:P6375 ?address . }}
              BIND(geof:latitude(?coord) AS ?lat)
              BIND(geof:longitude(?coord) AS ?lon)
              SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,ar,fr" . }}
            }}
            LIMIT {max_results}
            """

            # Also try a broader query without country filter if first fails
            sparql_broad = f"""
            SELECT ?business ?businessLabel ?phone ?website ?address ?lat ?lon ?countryLabel
            WHERE {{
              ?business wdt:P31 wd:{type_qid} .
              OPTIONAL {{ ?business wdt:P17 ?country . }}
              OPTIONAL {{ ?business wdt:P1329 ?phone . }}
              OPTIONAL {{ ?business wdt:P856 ?website . }}
              OPTIONAL {{ ?business wdt:P625 ?coord . }}
              OPTIONAL {{ ?business wdt:P6375 ?address . }}
              BIND(geof:latitude(?coord) AS ?lat)
              BIND(geof:longitude(?coord) AS ?lon)
              SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,ar,fr" . }}
            }}
            LIMIT {max_results * 2}
            """

            # Execute query
            headers = {
                "Accept": "application/sparql-results+json",
                "User-Agent": "LeadGenerator/1.0 (research)",
            }

            resp = requests.get(
                self.base_url,
                params={"query": sparql, "format": "json"},
                headers=headers,
                timeout=30,
            )

            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", {}).get("bindings", [])
            else:
                results = []

            # If no results with country filter, try broad query
            if not results:
                try:
                    resp2 = requests.get(
                        self.base_url,
                        params={"query": sparql_broad, "format": "json"},
                        headers=headers,
                        timeout=30,
                    )
                    if resp2.status_code == 200:
                        data2 = resp2.json()
                        results = data2.get("results", {}).get("bindings", [])
                except Exception:
                    pass

            print(f"      Wikidata: Found {len(results)} results")

            for item in results:
                try:
                    lead = Lead()
                    lead.source = "wikidata"

                    # Name
                    name = item.get("businessLabel", {}).get("value", "")
                    if name:
                        lead.business_name = name

                    # Phone
                    phone = item.get("phone", {}).get("value", "")
                    if phone:
                        lead.phone = phone

                    # Website
                    website = item.get("website", {}).get("value", "")
                    if website:
                        lead.website = website

                    # Address
                    address = item.get("address", {}).get("value", "")
                    if address:
                        lead.address = address

                    # Coordinates
                    lat = item.get("lat", {}).get("value", "")
                    lon = item.get("lon", {}).get("value", "")
                    if lat and lon:
                        lead.google_maps_url = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=16/{lat}/{lon}"

                    # Set location info
                    lead.city = location.split(",")[0].strip() if location else ""
                    lead.country = country.title() if country else ""
                    lead.category = query.title()

                    if lead.business_name:
                        leads.append(lead)

                except Exception:
                    continue

            time.sleep(1.0)

        except Exception as e:
            print(f"      Wikidata error: {e}")

        return leads
