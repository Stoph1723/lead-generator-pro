"""
Configuration for Lead Generator Pro
====================================
Edit these settings to customize your scraping.

Created by: Mustapha Elasri
GitHub: https://github.com/Stoph1723/lead-generator-pro
License: CC BY-NC 4.0
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ScraperConfig:
    """Main configuration for the lead generator."""

    # Search settings
    search_queries: List[str] = field(default_factory=lambda: [
        "dentist",
        "plumber",
        "restaurant",
        "lawyer",
        "real estate agent",
        "auto mechanic",
        "hair salon",
        "gym",
        "accountant",
        "marketing agency",
    ])

    locations: List[str] = field(default_factory=lambda: [
        "Austin, TX",
        "Dallas, TX",
        "Houston, TX",
        "San Antonio, TX",
    ])

    # Limits
    max_results_per_query: int = 100
    max_results_per_location: int = 100
    max_pages: int = 10

    # Timing (seconds) - increase if getting blocked
    page_load_wait: float = 3.0
    scroll_delay: float = 1.5
    between_requests_delay: float = 2.0
    random_delay_min: float = 0.5
    random_delay_max: float = 2.0

    # Browser settings
    headless: bool = True
    browser_timeout: int = 30000  # ms
    viewport_width: int = 1920
    viewport_height: int = 1080

    # Email extraction settings
    crawl_website_for_emails: bool = True
    max_pages_per_website: int = 3
    email_patterns_to_check: List[str] = field(default_factory=lambda: [
        "/contact", "/contact-us", "/contact.html",
        "/about", "/about-us", "/about.html",
        "/team", "/our-team", "/staff",
        "/support", "/help",
    ])

    # Output settings
    output_format: str = "both"  # "csv", "excel", or "both"
    output_directory: str = "output"
    output_filename: str = "leads"

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 5.0

    # Speed settings
    fast_mode: bool = False  # Reduce all delays for faster extraction
    search_workers: int = 4  # Parallel threads for search phase
    enrichment_workers: int = 8  # Parallel threads for website enrichment

    # Proxy settings
    proxy_server: Optional[str] = None  # e.g., "http://user:pass@proxy:port"
    proxy_list_file: Optional[str] = None  # Path to file with one proxy per line
    use_free_proxies: bool = True  # Auto-fetch free proxies from public lists (enabled by default)
    free_proxy_refresh_interval: int = 300  # Seconds between free proxy list refresh

    # Anti-detection
    rotate_user_agent: bool = True
    disable_images: bool = True
    disable_css: bool = False


# Default config instance
DEFAULT_CONFIG = ScraperConfig()
