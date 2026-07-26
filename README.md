<div align="center">

# Lead Generator Pro

**Free, open-source business lead scraper with email extraction, proxy rotation, and anti-detection.**

**No API keys. No limits. No paywalls.**

> Looking for the **Client Finder** cold email tool? It's in a separate repo: [client-finder](https://github.com/Stoph1723/client-finder)

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey?style=for-the-badge)
![Stars](https://img.shields.io/github/stars/Stoph1723/lead-generator-pro?style=for-the-badge&color=yellow)
![Forks](https://img.shields.io/github/forks/Stoph1723/lead-generator-pro?style=for-the-badge&color=blue)
![Issues](https://img.shields.io/github/issues/Stoph1723/lead-generator-pro?style=for-the-badge&color=red)

</div>

---

## Screenshots

### Interactive Menu
![Interactive Menu](screenshots/menu.png)

### Scraping in Progress
![Scraping Progress](screenshots/scraping.png)

### Excel Dashboard
![Excel Dashboard](screenshots/dashboard.png)

### Excel Leads Sheet
![Excel Leads Sheet](screenshots/leads.png)

---

## What Is This?

Lead Generator Pro is a **Python-based lead generation tool** that scrapes business data from multiple sources, enriches it with emails and social profiles, and exports everything to professional Excel reports with charts and dashboards.

It's built for **small businesses, freelancers, marketers, and anyone** who needs leads without paying for expensive SaaS tools like Apollo, Hunter, or ZoomInfo.

### Key Numbers

| Metric | Value |
|--------|-------|
| Data Sources | 8 active sources |
| Email Fallbacks | 6 extraction methods |
| Business Types | 61 categories |
| Countries | 150+ supported |
| Free Proxies | 200+ auto-fetched |
| Browser Fingerprints | 16 rotating |
| Excel Sheets | 4 (Dashboard, Leads, By Country, By Category) |

---

## Features

| Feature | Description |
|---------|-------------|
| **Multi-Source Scraping** | Overpass API, Nominatim, Wikidata SPARQL, Bing Web, Bing Maps, SearXNG, Mojeek |
| **6 Email Fallbacks** | MX records, Wayback Machine, SMTP verification, Bing site: search, Google cache, Social media bios |
| **Auto Proxy Rotation** | Fetches 200+ free proxies, rotates per request, auto-removes dead proxies |
| **Agent Rotation** | 16 browser fingerprints (Chrome, Firefox, Safari, Edge, mobile + desktop) |
| **6 Search Modes** | Business+Location, Maps URL, Country-wide, Bing Web, Cache, Bulk file |
| **Anti-Detection** | Rate limiting, referrer rotation, country-based Accept-Language, Cloudflare handling |
| **Professional Excel** | 4-sheet export with pie/bar charts, Material Design colors, column groups, alternating rows |
| **Lead Scoring** | 0-100 score based on email, phone, social profiles, website, TripAdvisor |
| **Thread-Safe Parallel** | Configurable workers (4 search + 8 enrichment) with ThreadPoolExecutor |
| **Deduplication** | Keeps best-scored lead per business, prevents duplicates |
| **Data Cleaning** | Validates emails, normalizes phones, strips UTM params, removes generic names |
| **61 Business Types** | Dentists, restaurants, pharmacies, lawyers, and 57 more — with multilingual search |

---

## Quick Start

### Installation

```bash
git clone https://github.com/Stoph1723/lead-generator-pro.git
cd lead-generator-pro
pip install -r requirements.txt
```

### Run

```bash
# Interactive mode (recommended for first use)
python main.py

# CLI mode — fast, no email enrichment
python main.py --query "dentist" --location "London UK" --fast --no-email --max 20

# Full mode — with email enrichment
python main.py --query "pharmacy,restaurant" --location "Casablanca Morocco,Marrakech" --fast --max 50
```

---

## Search Modes Explained

Lead Generator Pro has **6 search modes**. Here's what each does and when to use it:

---

### Mode 1: Search by Business Type + Location (Worldwide)

**What it does:** Searches for businesses by type (dentist, pharmacy, restaurant, etc.) in any city/country worldwide. Uses all 8 data sources for maximum coverage.

**Best for:** General lead generation, local business prospecting, building lists by niche.

**How it works:**
1. You provide a business type and location
2. It automatically detects the country and expands the query into multiple languages
3. Searches Overpass, Nominatim, Wikidata, Bing, SearXNG, Mojeek in parallel
4. Deduplicates and scores each lead
5. Optionally enriches with emails from websites

**Speed tips:**
```bash
# Fast mode (parallel workers + reduced delays)
python main.py --query "dentist" --location "London UK" --fast --max 20

# Skip email enrichment (2-5x faster)
python main.py --query "dentist" --location "London UK" --fast --no-email --max 20

# Multiple queries at once
python main.py --query "dentist,pharmacy,restaurant" --location "Agadir Morocco" --fast --no-email
```

**Example:**
```bash
# Search for dentists in London, fast mode, no email enrichment
python main.py --query "dentist" --location "London UK" --fast --no-email --max 50

# Output: leads_20260724_160558.csv with 50 dentist leads
```

---

### Mode 2: Scrape from Google Maps URL

**What it does:** Extracts businesses directly from a Google Maps search URL. Great for getting the exact businesses you see on Google Maps.

**Best for:** Scraping specific Google Maps results, targeting businesses visible on the map.

**How it works:**
1. You paste a Google Maps search URL
2. It parses the query and location from the URL
3. Searches all data sources using the extracted info
4. Enriches and exports

**Speed tips:**
```bash
# Fast mode with no email (fastest)
python main.py --url "https://www.google.com/maps/search/dentist+agadir" --fast --no-email

# With email enrichment (slower but finds contacts)
python main.py --url "https://www.google.com/maps/search/pharmacy+london" --fast --max 100
```

**Example:**
```bash
python main.py --url "https://www.google.com/maps/search/restaurant+marrakech" --fast --max 50
```

---

### Mode 3: Search by Country-Wide Category

**What it does:** Searches an entire country for a business type. Great for building country-wide databases.

**Best for:** Market research, country-wide business directories, franchise prospecting.

**How it works:**
1. You provide a business type and country name
2. It queries all major cities in that country
3. Uses expanded language queries for better coverage
4. Deduplicates across all cities

**Speed tips:**
```bash
# Fast mode (essential for country-wide)
python main.py --query "pharmacy" --location "Morocco" --fast --no-email --max 100

# Limit to fewer results
python main.py --query "dentist" --location "France" --fast --no-email --max 50
```

**Example:**
```bash
# Find pharmacies across all of Morocco
python main.py --query "pharmacy" --location "Morocco" --fast --no-email --max 200
```

**Note:** Country-wide searches take longer (2-5 minutes) because they query multiple cities.

---

### Mode 4: Search Bing Web Only

**What it does:** Searches only Bing for businesses. Faster than full mode since it skips Overpass/Nominatim/Wikidata.

**Best for:** Quick searches, when you want web results only, testing.

**How it works:**
1. You provide business types and locations
2. Only Bing Web search is used (no OpenStreetMap sources)
3. Extracts business names, phones, emails from search snippets
4. Enriches found websites

**Speed tips:**
```bash
# This mode is inherently fast (single source)
# Just run with --fast for parallel queries
python main.py --query "dentist" --location "Casablanca Morocco" --fast --no-email
```

**Example:**
```bash
# Quick Bing-only search
python main.py --query "restaurant" --location "Paris France" --fast --no-email --max 30
```

---

### Mode 5: Search from Pre-Fetched Cache Only

**What it does:** Searches only from locally cached data (instant, no network requests). The cache gets populated when you run Mode 1, 2, or 3.

**Best for:** Instant results, offline browsing, re-exporting cached data.

**How it works:**
1. You provide business types and locations
2. Searches only the local cache file
3. No network requests — instant results
4. Exports immediately

**Speed tips:**
```bash
# This mode is instant — no flags needed
# First, build cache with Mode 1, then use Mode 5 to browse it
```

**Example:**
```bash
# Step 1: Build cache by running Mode 1
python main.py --query "dentist,pharmacy" --location "Agadir Morocco" --fast --max 50

# Step 2: Browse cache instantly
python main.py
# Select Mode 5, enter "dentist" and "Agadir"
```

---

### Mode 6: Bulk Search from File

**What it does:** Runs multiple searches from a text file. Great for large-scale lead generation campaigns.

**Best for:** Large campaigns, agency work, building massive lead databases.

**How it works:**
1. You create a text file with one search per line (format: `query,location`)
2. The tool reads the file and runs all searches in sequence
3. Deduplicates across all searches
4. Exports a single combined CSV/Excel

**File format:**
```
dentist,Agadir Morocco
pharmacy,Marrakech Morocco
restaurant,Casablanca Morocco
lawyer,Paris France
dentist,London UK
```

**Speed tips:**
```bash
# Fast mode + no email for bulk (fastest)
# Use interactive mode to select Mode 6 and point to your file

# Or create the file and run interactively
python main.py
# Select Mode 6, enter file path, enable fast mode
```

**Example:**
```bash
# Create searches.txt
echo "dentist,Agadir Morocco" > searches.txt
echo "pharmacy,Marrakech" >> searches.txt
echo "restaurant,Casablanca" >> searches.txt

# Run bulk mode
python main.py
# Select Mode 6, enter "searches.txt", enable fast mode, max 30 per search
```

---

### Speed Comparison

| Mode | Speed | Best For |
|------|-------|----------|
| Mode 1 | ~1 min per query | General lead generation |
| Mode 2 | ~1.5 min per URL | Google Maps scraping |
| Mode 3 | ~3-5 min | Country-wide databases |
| Mode 4 | ~30 sec per query | Quick web-only search |
| Mode 5 | Instant | Cached/offline browsing |
| Mode 6 | ~1 min per line | Bulk campaigns |

**Fastest possible run:**
```bash
python main.py --query "dentist" --location "London UK" --fast --no-email --max 10
# ~30 seconds
```

**Most thorough run:**
```bash
python main.py --query "dentist" --location "London UK" --fast --max 100
# ~3-5 minutes (includes email enrichment)
```

---

## CLI Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--url` | — | Google Maps URL to scrape |
| `--query` | — | Business types (comma separated) |
| `--location` | — | Locations (comma separated) |
| `--max` | `50` | Max results per query |
| `--fast` | `false` | Fast mode: parallel workers + reduced delays |
| `--no-email` | `false` | Skip email enrichment (faster) |
| `--search-workers` | `4` | Parallel search threads |
| `--enrich-workers` | `8` | Parallel enrichment threads |
| `--output` | `both` | Output format: `csv`, `excel`, or `both` |
| `--proxy` | — | Single proxy: `http://host:port` |
| `--proxy-file` | — | File with proxies (one per line) |
| `--free-proxies` | `false` | Auto-fetch and rotate free proxies |

---

## Search Sources

| Source | Type | Notes |
|--------|------|-------|
| **Overpass API** | Structured | OpenStreetMap — businesses with phone/email/website |
| **Nominatim** | Structured | OpenStreetMap geocoding |
| **Wikidata SPARQL** | Structured | Wikipedia/Wikidata structured business data |
| **Bing Web** | Web search | Location-aware queries with retry logic |
| **Bing Maps** | Web search | JSON-LD structured data extraction |
| **SearXNG** | Meta-search | Aggregates Google, Bing, DuckDuckGo |
| **Mojeek** | Web search | Independent, no tracking/blocking |
| **Overpass Expanded** | Structured | Multilingual Overpass queries for better coverage |

---

## Email Extraction Pipeline

```
Website Found
    ├── MX Record Check (DNS)
    ├── Wayback Machine (historical pages)
    ├── Contact Page Crawl (/contact, /about, /team)
    ├── Pattern Guessing + SMTP Verification (info@, contact@, hello@...)
    ├── Bing site:domain Search
    ├── Google Cache Search
    └── Social Media Bios (Facebook, LinkedIn, Instagram)
```

---

## Architecture

```
lead_generator/
├── main.py              # Main orchestrator + CLI
├── config.py            # Configuration (workers, delays, proxies)
├── scrapers/
│   ├── crawler.py       # Anti-bypass HTTP client with proxy rotation
│   ├── google_maps.py   # 8-source search pipeline
│   ├── email_finder.py  # Website intelligence + 6 email fallbacks
│   └── wikidata.py      # Wikidata SPARQL scraper
├── models/
│   └── lead.py          # Lead data model + LeadCollection
├── utils/
│   ├── cleaner.py       # Data validation & cleaning
│   ├── exporter.py      # CSV + Excel export (4 sheets, charts)
│   ├── keywords.py      # 61 business types, 590 country mappings
│   ├── ui.py            # Terminal UI (ANSI colors, no dependencies)
│   └── web_cache.py     # Cache layer
└── output/              # Generated files
```

---

## Output Example

Results are saved to `output/` with timestamps:

- **CSV** — Clean, CRM-importable format
- **Excel** — 4 professional sheets:
  - **Dashboard** — Stats, pie charts, bar charts, score distribution
  - **Leads** — All data with column groups and alternating colors
  - **By Country** — Breakdown by country
  - **By Category** — Breakdown by business type

---

## Requirements

- Python 3.10+
- No Playwright/Selenium needed (pure HTTP requests)
- No API keys required
- Works on Windows, macOS, Linux

```
beautifulsoup4>=4.12.0
lxml>=5.0.0
requests>=2.32.0
openpyxl>=3.1.0
urllib3>=2.0.0
```

---

## Disclaimer

This tool is provided for **educational and legitimate business purposes only**. Users are responsible for complying with the terms of service of any website they scrape. The author is not responsible for any misuse of this software.

---

## License

This project is licensed under the **Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0)**.

You are free to:
- **Share** — copy and redistribute the material in any medium or format
- **Adapt** — remix, transform, and build upon the material

Under the following terms:
- **Attribution** — You must give appropriate credit to **Mustapha Elasri**, provide a link to the license, and indicate if changes were made
- **NonCommercial** — You may not use the material for commercial purposes (selling the tool or derivative works)

Full license: [LICENSE](LICENSE)

---

## Credits

**Created by [Mustapha Elasri](https://github.com/Stoph1723)**

If you use this project, please give credit by mentioning:
> Lead Generator Pro by Mustapha Elasri — https://github.com/Stoph1723/lead-generator-pro

---

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Support

If this tool helped you, consider:
- Starring the repo
- Sharing it with others
- Contributing improvements
