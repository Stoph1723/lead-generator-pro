"""
Lead Generator - Main Orchestrator v3
====================================
Beautiful terminal UI with full worldwide scraping support.
Thread-safe parallel scraping for maximum speed.

Usage:
    python main.py                    # Interactive mode
    python main.py --url "MAPS_URL"  # Scrape from Google Maps URL
    python main.py --query "dentist" --location "London, UK"
    python main.py --fast             # Fast mode (parallel + reduced delays)
    python main.py --help            # Show all options
"""

import sys
import time
import argparse
import warnings
import threading
from typing import List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings("ignore", message=".*Unverified HTTPS request.*")
warnings.filterwarnings("ignore", message=".*InsecureRequestWarning.*")

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from lead_generator.config import ScraperConfig
from lead_generator.models.lead import Lead, LeadCollection
from lead_generator.scrapers.google_maps import GoogleMapsScraper
from lead_generator.scrapers.email_finder import WebsiteIntelligenceExtractor
from lead_generator.utils.cleaner import (
    clean_phone, clean_email, clean_url, clean_address,
    extract_state_from_address, extract_city_from_address, extract_zip_code,
)
from lead_generator.utils.exporter import LeadExporter
from lead_generator.utils.keywords import detect_country, get_languages_for_country
from lead_generator.utils.ui import (
    banner, section_header, success, error, warning, info, found,
    searching, progress_bar, stat_box, menu, ask, ask_yes_no,
    lead_preview, run_complete, instructions, print_line, print_double_line,
    C,
)

sys.stdout.reconfigure(encoding="utf-8")


def safe_name(name: str, max_len: int = 30) -> str:
    """Strip non-Latin characters for safe CMD display."""
    safe = ""
    prev_was_non_ascii = False
    for ch in name:
        if ch.isascii() and (ch.isalnum() or ch in "-_.() &"):
            if prev_was_non_ascii and safe and safe[-1] != " ":
                safe += " "
            safe += ch
            prev_was_non_ascii = False
        else:
            prev_was_non_ascii = True
    result = safe[:max_len].strip()
    return result if result else "business"


class LeadGenerator:
    """Main orchestrator for the lead generation pipeline."""

    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config or ScraperConfig()
        self.leads = LeadCollection()
        self.scraper = GoogleMapsScraper(self.config)
        self.extractor = WebsiteIntelligenceExtractor(self.config)
        self.exporter = LeadExporter(self.config)
        self._start_time = None
        self._total_scraped = 0
        self._total_enriched = 0
        self._lock = threading.Lock()
        self._progress_lock = threading.Lock()

    def run(
        self,
        queries: Optional[List[str]] = None,
        locations: Optional[List[str]] = None,
        maps_url: Optional[str] = None,
        skip_enrichment: bool = False,
    ):
        """Run the full lead generation pipeline."""
        self._start_time = time.time()

        queries = queries or self.config.search_queries
        locations = locations or self.config.locations

        banner()

        mode_str = "Fast Parallel" if self.config.fast_mode else "Standard"
        if maps_url:
            info(f"Mode: {C.BOLD}Google Maps URL{C.RESET} ({C.CYAN}{mode_str}{C.RESET})")
            info(f"URL: {C.CYAN}{maps_url[:70]}...{C.RESET}")
        else:
            info(f"Mode: {C.BOLD}{mode_str}{C.RESET}")
            info(f"Queries: {C.BOLD}{len(queries)}{C.RESET}")
            info(f"Locations: {C.BOLD}{len(locations)}{C.RESET}")
            info(f"Searches: {C.BOLD}{len(queries) * len(locations)}{C.RESET}")

        info(f"Max per query: {C.BOLD}{self.config.max_results_per_query}{C.RESET}")
        info(f"Email enrichment: {C.BOLD}{'ON' if self.config.crawl_website_for_emails and not skip_enrichment else 'OFF'}{C.RESET}")
        if self.config.fast_mode:
            info(f"Workers: {C.BOLD}{self.config.search_workers} search / {self.config.enrichment_workers} enrich{C.RESET}")
        print()

        try:
            if maps_url:
                self._scrape_from_url(maps_url)
            else:
                self._scrape_phase(queries, locations)

            if self.config.crawl_website_for_emails and not skip_enrichment:
                self._enrichment_phase()

            self._export_phase()

        except KeyboardInterrupt:
            print()
            warning("Interrupted by user")
            if self.leads:
                self._export_phase()

        except Exception as e:
            error(f"Fatal error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            self._print_summary()

    def _scrape_from_url(self, url: str):
        """Scrape businesses from a Google Maps URL."""
        section_header("Phase 1: Scraping Google Maps URL")

        leads = self.scraper.scrape_google_maps_url(url, self.config.max_results_per_query)
        cleaned = self._clean_leads(leads)
        added = self.leads.add_batch(cleaned)
        self._total_scraped = len(leads)

        success(f"Scraped: {C.BOLD}{len(leads)}{C.RESET} | Added: {C.BOLD}{added}{C.RESET} | Total: {C.BOLD}{len(self.leads)}{C.RESET}")

    def _scrape_phase(self, queries: List[str], locations: List[str]):
        """Phase 1: Scrape business listings using parallel workers."""
        section_header("Phase 1: Scraping Business Directories (Worldwide)")

        total_combos = len(queries) * len(locations)
        combos = []
        for query in queries:
            for location in locations:
                combos.append((query, location))

        current = [0]
        lock = threading.Lock()

        def process_combo(query_location):
            query, location = query_location
            with lock:
                current[0] += 1
                idx = current[0]

            country = detect_country(location)
            if country:
                self.extractor.set_country(country)
                langs = get_languages_for_country(country)
                searching(f"[{idx}/{total_combos}] {C.BOLD}{query}{C.RESET} in {C.CYAN}{location}{C.RESET} ({country}, langs: {', '.join(langs[:3])})")
            else:
                searching(f"[{idx}/{total_combos}] {C.BOLD}{query}{C.RESET} in {C.CYAN}{location}{C.RESET}")

            try:
                leads = self.scraper.search(
                    query=query,
                    location=location,
                    max_results=self.config.max_results_per_query,
                )

                cleaned_leads = self._clean_leads(leads)
                with self._lock:
                    added = self.leads.add_batch(cleaned_leads)
                    self._total_scraped += len(leads)

                success(f"Scraped: {C.BOLD}{len(leads)}{C.RESET} | Added: {C.BOLD}{added}{C.RESET} | Total: {C.BOLD}{len(self.leads)}{C.RESET}")

            except Exception as e:
                error(f"Error: {e}")

        workers = self.config.search_workers if self.config.fast_mode else 1
        if workers > 1:
            info(f"Running {C.BOLD}{len(combos)}{C.RESET} searches with {C.BOLD}{workers}{C.RESET} parallel workers...")
            with ThreadPoolExecutor(max_workers=workers) as executor:
                list(executor.map(process_combo, combos))
        else:
            for combo in combos:
                process_combo(combo)
                time.sleep(1.0)

    def _enrichment_phase(self):
        """Phase 2: Enrich leads with full website intelligence (parallel)."""
        cache_enriched = 0
        for lead in self.leads:
            if not lead.phone and not lead.email:
                try:
                    if self.scraper.web_cache.enrich_lead_from_cache(lead):
                        cache_enriched += 1
                except Exception:
                    pass
        if cache_enriched:
            info(f"Cache enriched: {C.BOLD}{cache_enriched}{C.RESET} leads (instant data)")

        leads_to_enrich = [
            lead for lead in self.leads
            if lead.website and not lead.email
        ]

        leads_no_website = [
            lead for lead in self.leads
            if not lead.website and not lead.email
        ]

        if not leads_to_enrich and not leads_no_website:
            info("No leads to enrich (all have emails or no websites)")
            return

        total = len(leads_to_enrich) + len(leads_no_website)
        section_header(f"Phase 2: Website Intelligence Extraction ({total} leads)")

        enriched_count = [0]
        emails_found = [0]
        progress_lock = threading.Lock()
        enrich_lock = threading.Lock()

        if leads_no_website:
            max_site_searches = min(len(leads_no_website), 15 if self.config.fast_mode else 10)
            info(f"Finding websites for {max_site_searches} of {len(leads_no_website)} leads (limited for speed)...")

            def find_website_for_lead(lead):
                try:
                    website = self.scraper.find_website_for_lead(lead)
                    if website:
                        lead.website = website
                        return lead
                except Exception:
                    pass
                return None

            workers = self.config.enrichment_workers if self.config.fast_mode else 1
            found_count = [0]

            def process_website_search(lead):
                result = find_website_for_lead(lead)
                with progress_lock:
                    found_count[0] += 1
                    progress_bar(found_count[0], max_site_searches,
                                prefix="Finding site",
                                suffix=safe_name(lead.business_name))

            if workers > 1:
                with ThreadPoolExecutor(max_workers=min(workers, 8)) as executor:
                    futures = [executor.submit(process_website_search, lead) for lead in leads_no_website[:max_site_searches]]
                    for future in as_completed(futures):
                        pass
            else:
                for idx, lead in enumerate(leads_no_website[:max_site_searches]):
                    process_website_search(lead)

            for lead in leads_no_website[:max_site_searches]:
                if lead.website:
                    leads_to_enrich.append(lead)
            print()

        def enrich_lead(lead):
            try:
                intel = self.extractor.find_contacts(lead.website, crawl_pages=True)

                if intel.get("emails"):
                    from lead_generator.utils.cleaner import clean_email
                    cleaned_emails = [clean_email(e) for e in intel["emails"] if clean_email(e)]
                    if cleaned_emails:
                        lead.all_emails = cleaned_emails
                        lead.email = cleaned_emails[0]
                        with progress_lock:
                            emails_found[0] += 1

                if intel.get("phones"):
                    from lead_generator.utils.cleaner import clean_phone
                    for p in intel["phones"]:
                        p_clean = clean_phone(p)
                        if p_clean and not lead.phone:
                            lead.phone = p_clean
                            break

                social = intel.get("social_profiles", {})
                for platform in ["facebook", "instagram", "linkedin", "twitter",
                                 "youtube", "tiktok", "whatsapp", "telegram",
                                 "snapchat", "pinterest", "tripadvisor"]:
                    if social.get(platform) and not getattr(lead, platform):
                        setattr(lead, platform, social[platform])

                if intel.get("whatsapp") and not lead.whatsapp:
                    lead.whatsapp = intel["whatsapp"]
                elif lead.phone and not lead.whatsapp:
                    phone_digits = __import__("re").sub(r"\D", "", lead.phone)
                    if phone_digits and len(phone_digits) >= 8:
                        lead.whatsapp = "https://wa.me/%s" % phone_digits

                if intel.get("telegram") and not lead.telegram:
                    lead.telegram = intel["telegram"]

                if intel.get("owner_name") and not lead.owner_name:
                    lead.owner_name = intel["owner_name"]

                if intel.get("operating_hours") and not lead.operating_hours:
                    lead.operating_hours = intel["operating_hours"]

                if intel.get("address") and not lead.address:
                    lead.address = intel["address"]

                if intel.get("city") and not lead.city:
                    lead.city = intel["city"]

                if intel.get("country") and not lead.country:
                    lead.country = intel["country"]

                if intel.get("description") and not lead.description:
                    lead.description = intel["description"]

                if intel.get("rating_str") and not lead.rating_str:
                    lead.rating_str = intel["rating_str"]

                lead._calculate_score()

                with progress_lock:
                    enriched_count[0] += 1
                    progress_bar(enriched_count[0], len(leads_to_enrich),
                                prefix="Extracting",
                                suffix=safe_name(lead.business_name))

            except Exception:
                with progress_lock:
                    enriched_count[0] += 1
                    progress_bar(enriched_count[0], len(leads_to_enrich),
                                prefix="Extracting",
                                suffix=safe_name(lead.business_name))

        workers = self.config.enrichment_workers if self.config.fast_mode else 1
        if workers > 1:
            info(f"Enriching {C.BOLD}{len(leads_to_enrich)}{C.RESET} leads with {C.BOLD}{workers}{C.RESET} parallel workers...")
            with ThreadPoolExecutor(max_workers=workers) as executor:
                list(executor.map(enrich_lead, leads_to_enrich))
        else:
            for idx, lead in enumerate(leads_to_enrich):
                enrich_lead(lead)
                time.sleep(0.1)

        print()
        success(f"Enriched: {C.BOLD}{enriched_count[0]}{C.RESET} | Emails found: {C.BOLD}{emails_found[0]}{C.RESET}")

    def _clean_leads(self, leads: List[Lead]) -> List[Lead]:
        """Clean and validate lead data for maximum quality."""
        from lead_generator.utils.cleaner import (
            clean_phone, clean_email, clean_url, clean_address,
            clean_business_name, extract_city_from_address,
            extract_state_from_address, extract_zip_code, validate_lead
        )

        cleaned = []
        for lead in leads:
            # Clean business name
            lead.business_name = clean_business_name(lead.business_name)

            # Validate lead has minimum quality
            if not validate_lead(lead):
                continue

            # Clean contact data
            lead.phone = clean_phone(lead.phone)
            lead.email = clean_email(lead.email)
            lead.website = clean_url(lead.website)
            lead.address = clean_address(lead.address)

            # Clean all emails list
            if lead.all_emails:
                lead.all_emails = [clean_email(e) for e in lead.all_emails if clean_email(e)]

            # Extract location data from address
            if lead.address and not lead.city:
                lead.city = extract_city_from_address(lead.address)
            if lead.address and not lead.state:
                lead.state = extract_state_from_address(lead.address)
            if lead.address and not lead.zip_code:
                lead.zip_code = extract_zip_code(lead.address)

            # Generate WhatsApp link from phone
            if lead.phone and not lead.whatsapp:
                phone_digits = __import__("re").sub(r"\D", "", lead.phone)
                if phone_digits and len(phone_digits) >= 8:
                    lead.whatsapp = "https://wa.me/%s" % phone_digits

            # Skip if no useful data at all
            if not lead.phone and not lead.email and not lead.website:
                # Keep only if we have address at least
                if not lead.address:
                    continue

            cleaned.append(lead)

        return cleaned

    def _export_phase(self):
        """Phase 3: Export leads to files."""
        section_header("Phase 3: Exporting Data")

        if not self.leads:
            error("No leads to export")
            return

        for lead in self.leads:
            lead._calculate_score()

        sorted_leads = LeadCollection()
        for lead in self.leads.sort_by_score():
            sorted_leads.add(lead)

        files = self.exporter.export(sorted_leads)

        for f in files:
            success(f"Saved: {C.CYAN}{f}{C.RESET}")

    def _print_summary(self):
        """Print final summary."""
        elapsed = time.time() - self._start_time if self._start_time else 0
        stats = self.leads.stats
        run_complete(stats, elapsed)


def interactive_mode():
    """Run in interactive mode with beautiful UI."""
    banner()

    choice = menu("Choose Search Mode", [
        f"{C.GREEN}Search by business type + location (Worldwide){C.RESET}",
        f"{C.CYAN}Scrape from Google Maps URL{C.RESET}",
        f"{C.YELLOW}Search by country-wide category{C.RESET}",
        f"{C.MAGENTA}Search Bing Web only{C.RESET}",
        f"{C.BLUE}Search from pre-fetched cache only{C.RESET}",
        f"{C.WHITE}Bulk search from file{C.RESET}",
    ])

    config = ScraperConfig()

    if choice == "2":
        section_header("Google Maps URL Mode")
        url = ask("Paste Google Maps URL")
        if not url:
            error("No URL provided")
            return

        max_results = ask("Max results", "50")
        config.max_results_per_query = int(max_results) if max_results.isdigit() else 50

        do_enrich = ask_yes_no("Enable email enrichment (slower but finds emails)?", default=True)
        config.crawl_website_for_emails = do_enrich

        fast = ask_yes_no("Enable fast mode (parallel + faster)?", default=True)
        config.fast_mode = fast

        output = ask("Output format", "both", ["csv", "excel", "both"])
        config.output_format = output

        generator = LeadGenerator(config)
        generator.run(maps_url=url)

    elif choice == "3":
        section_header("Country-Wide Search Mode")
        info(f"{C.YELLOW}Search entire country for a business type!{C.RESET}")
        print()

        query = ask("Business type", "pharmacy")
        country = ask("Country", "Morocco")

        max_results = ask("Max results", "100")
        config.max_results_per_query = int(max_results) if max_results.isdigit() else 100

        do_enrich = ask_yes_no("Enable email enrichment?", default=True)
        config.crawl_website_for_emails = do_enrich

        fast = ask_yes_no("Enable fast mode (parallel + faster)?", default=True)
        config.fast_mode = fast

        output = ask("Output format", "both", ["csv", "excel", "both"])
        config.output_format = output

        config.search_queries = [query]
        config.locations = [country]

        generator = LeadGenerator(config)
        generator.run()

    elif choice == "4":
        section_header("Bing Web Search Mode")
        info(f"{C.BLUE}Search businesses using Bing web search{C.RESET}")
        print()

        queries_str = ask("Business types (comma separated)", "dentist,pharmacy")
        queries = [q.strip() for q in queries_str.split(",") if q.strip()]

        locations_str = ask("Locations (comma separated)", "Casablanca Morocco")
        locations = [l.strip() for l in locations_str.split(",") if l.strip()]

        max_results = ask("Max results per search", "30")
        config.max_results_per_query = int(max_results) if max_results.isdigit() else 30

        fast = ask_yes_no("Enable fast mode?", default=True)
        config.fast_mode = fast

        do_enrich = ask_yes_no("Enable email enrichment?", default=True)
        config.crawl_website_for_emails = do_enrich

        config.search_queries = queries
        config.locations = locations

        generator = LeadGenerator(config)
        generator._start_time = time.time()

        banner()
        section_header("Bing Web Search")

        try:
            from lead_generator.scrapers.google_maps import GoogleMapsScraper
            scraper = GoogleMapsScraper(config)

            for query in queries:
                for location in locations:
                    try:
                        leads = scraper._search_bing_web(query, location, config.max_results_per_query)
                        if not leads:
                            info(f"Bing returned 0 results, waiting 5s and retrying...")
                            time.sleep(5)
                            leads = scraper._search_bing_web(query, location, config.max_results_per_query)
                        cleaned = generator._clean_leads(leads)
                        added = generator.leads.add_batch(cleaned)
                        success(f"Bing Web: {C.BOLD}{len(leads)}{C.RESET} | Added: {C.BOLD}{added}{C.RESET} | Total: {C.BOLD}{len(generator.leads)}{C.RESET}")
                    except Exception as e:
                        error(f"Error: {e}")
                    time.sleep(2.0)

        except Exception as e:
            error(f"Bing search error: {e}")

        if do_enrich and generator.leads:
            generator._enrichment_phase()

        generator._export_phase()
        generator._print_summary()

    elif choice == "5":
        section_header("Cache Search Mode")
        info(f"{C.BLUE}Search only pre-fetched cache data (instant)!{C.RESET}")
        print()

        queries_str = ask("Business types (comma separated)", "restaurant,pharmacy")
        queries = [q.strip() for q in queries_str.split(",") if q.strip()]

        locations_str = ask("Locations (comma separated)", "Agadir,Marrakech")
        locations = [l.strip() for l in locations_str.split(",") if l.strip()]

        output = ask("Output format", "both", ["csv", "excel", "both"])
        config.output_format = output

        generator = LeadGenerator(config)
        generator._start_time = time.time()

        banner()
        section_header("Cache Search")

        try:
            from lead_generator.utils.web_cache import WebSearchCache
            cache = WebSearchCache()

            for query in queries:
                for location in locations:
                    matches = cache.search(query, location)
                    if matches:
                        raw_leads = []
                        for biz in matches:
                            lead = Lead()
                            lead.source = "cache"
                            lead.business_name = biz.get("name", "")
                            lead.phone = biz.get("phone", "")
                            lead.email = biz.get("email", "")
                            lead.website = biz.get("website", "")
                            lead.address = biz.get("address", "")
                            lead.city = biz.get("city", location)
                            if lead.email:
                                lead.all_emails = [lead.email]
                            if lead.business_name:
                                raw_leads.append(lead)

                        cleaned = generator._clean_leads(raw_leads)
                        added = generator.leads.add_batch(cleaned)
                        found(f"Cache '{query}' in {location}: {C.BOLD}{len(cleaned)}{C.RESET} cleaned from {len(matches)} raw")
                    else:
                        found(f"Cache '{query}' in {location}: 0 matches")
                    time.sleep(0.1)

        except Exception as e:
            error(f"Cache search error: {e}")

        generator._export_phase()
        generator._print_summary()

    elif choice == "6":
        section_header("Bulk Search Mode")
        info(f"{C.WHITE}Run multiple searches from a text file!{C.RESET}")
        print()
        info("File format: one search per line: query,location")
        info("Example: dentist,Agadir Morocco")
        print()

        filepath = ask("Path to searches.txt")
        if not filepath:
            error("No file provided")
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        except Exception as e:
            error(f"Cannot read file: {e}")
            return

        if not lines:
            error("File is empty")
            return

        info(f"Found {C.BOLD}{len(lines)}{C.RESET} searches in file")

        max_results = ask("Max results per search", "30")
        config.max_results_per_query = int(max_results) if max_results.isdigit() else 30

        do_enrich = ask_yes_no("Enable email enrichment?", default=False)
        config.crawl_website_for_emails = do_enrich

        fast = ask_yes_no("Enable fast mode (parallel + faster)?", default=True)
        config.fast_mode = fast

        output = ask("Output format", "both", ["csv", "excel", "both"])
        config.output_format = output

        queries = []
        locations = []
        for line in lines:
            parts = line.split(",", 1)
            if len(parts) == 2:
                queries.append(parts[0].strip())
                locations.append(parts[1].strip())
            else:
                queries.append(parts[0].strip())
                locations.append("")

        config.search_queries = list(set(queries))
        config.locations = list(set(locations)) if locations else ["worldwide"]

        generator = LeadGenerator(config)
        generator.run()

    else:
        section_header("Worldwide Search Mode")
        info(f"{C.GREEN}Type business names in ANY language!{C.RESET}")
        info(f"{C.GREEN}Examples: pharmacy, pharmacie, farmacia, apotheke, boulangerie{C.RESET}")
        print()

        queries_str = ask("Business types (comma separated)", "dentist,pharmacy,restaurant")
        queries = [q.strip() for q in queries_str.split(",") if q.strip()]

        locations_str = ask("Locations (comma separated)", "Agadir Morocco,London UK,Tokyo Japan")
        locations = [l.strip() for l in locations_str.split(",") if l.strip()]

        for loc in locations:
            country = detect_country(loc)
            if country:
                langs = get_languages_for_country(country)
                info(f"  {C.CYAN}{loc}{C.RESET} -> {C.BOLD}{country}{C.RESET} (languages: {', '.join(langs[:3])})")

        max_results = ask("Max results per query", "50")
        config.max_results_per_query = int(max_results) if max_results.isdigit() else 50

        do_enrich = ask_yes_no("Enable email enrichment?", default=False)
        config.crawl_website_for_emails = do_enrich

        fast = ask_yes_no("Enable fast mode (parallel + faster)?", default=True)
        config.fast_mode = fast

        output = ask("Output format", "both", ["csv", "excel", "both"])
        config.output_format = output

        config.search_queries = queries
        config.locations = locations

        generator = LeadGenerator(config)
        generator.run()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Lead Generator Pro - WorldWide Business Lead Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                                    # Interactive mode
  python main.py --url "https://www.google.com/maps/search/dentist+agadir"  # Google Maps URL
  python main.py --query "dentist,pharmacy" --location "London UK,Paris FR"  # CLI mode
  python main.py --query "restaurant" --location "Tokyo Japan" --max 100 --fast  # Fast mode
  python main.py --query "dentist" --location "London UK" --free-proxies  # With free proxy rotation
  python main.py --query "dentist" --location "London UK" --proxy "http://user:pass@host:port"
        """,
    )
    parser.add_argument("--url", type=str, help="Google Maps URL to scrape")
    parser.add_argument("--query", type=str, help="Business types (comma separated)")
    parser.add_argument("--location", type=str, help="Locations (comma separated)")
    parser.add_argument("--max", type=int, default=50, help="Max results per query (default: 50)")
    parser.add_argument("--no-email", action="store_true", help="Skip email enrichment (faster)")
    parser.add_argument("--fast", action="store_true", help="Fast mode: parallel workers + reduced delays")
    parser.add_argument("--search-workers", type=int, default=4, help="Parallel search workers (default: 4)")
    parser.add_argument("--enrich-workers", type=int, default=8, help="Parallel enrichment workers (default: 8)")
    parser.add_argument("--output", choices=["csv", "excel", "both"], default="both", help="Output format")
    parser.add_argument("--proxy", type=str, default=None, help="Single proxy: protocol://host:port (e.g. http://user:pass@host:port)")
    parser.add_argument("--proxy-file", type=str, default=None, help="File with proxies (one per line)")
    parser.add_argument("--free-proxies", action="store_true", help="Auto-fetch and rotate free proxies")
    parser.add_argument("--help-usage", action="store_true", help="Show detailed usage instructions")

    args = parser.parse_args()

    if args.help_usage:
        banner()
        instructions()
        return

    if len(sys.argv) == 1:
        interactive_mode()
        return

    config = ScraperConfig(
        max_results_per_query=args.max,
        crawl_website_for_emails=not args.no_email,
        output_format=args.output,
        fast_mode=args.fast,
        search_workers=args.search_workers,
        enrichment_workers=args.enrich_workers,
        proxy_server=args.proxy,
        proxy_list_file=args.proxy_file,
        use_free_proxies=args.free_proxies,
    )

    generator = LeadGenerator(config)

    if args.url:
        generator.run(maps_url=args.url)
    elif args.query:
        queries = [q.strip() for q in args.query.split(",")]
        locations = [l.strip() for l in args.location.split(",")] if args.location else ["worldwide"]
        config.search_queries = queries
        config.locations = locations
        generator.run()
    else:
        banner()
        error("Provide --url, --query, or run without arguments for interactive mode")
        print()
        info("Run with --help-usage for detailed instructions")


if __name__ == "__main__":
    main()
