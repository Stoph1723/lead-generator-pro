"""
Website Intelligence Extractor v3
=================================
Enhanced thread-safe web crawler that extracts EVERYTHING:
- Emails (HTML, JS, CSS, meta, JSON-LD, hidden elements, Cloudflare)
- Phones (all formats, country-aware)
- Social media (FB, IG, LinkedIn, Twitter, YouTube, TikTok, WhatsApp, Telegram, LINE, WeChat, VK, Snapchat, Pinterest, TripAdvisor)
- Names (owner/founder/manager in any language)
- Operating hours (JSON-LD, visible text)
- Full address with country
- Ratings/reviews
- Business descriptions

Uses anti-bypass crawler with fingerprint rotation. Thread-safe.
"""

import re
import json
import sys
import threading
from typing import List, Optional, Dict, Set
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from lead_generator.scrapers.crawler import AntiBypassCrawler
from lead_generator.config import ScraperConfig

sys.stdout.reconfigure(encoding="utf-8")

PHONE_COUNTRY_CODES = {
    "212": "Morocco", "213": "Algeria", "216": "Tunisia",
    "20": "Egypt", "234": "Nigeria", "27": "South Africa",
    "1": "USA/Canada", "44": "UK", "33": "France",
    "49": "Germany", "34": "Spain", "39": "Italy",
    "81": "Japan", "86": "China", "91": "India",
    "61": "Australia", "55": "Brazil", "52": "Mexico",
    "971": "UAE", "966": "Saudi Arabia", "974": "Qatar",
    "965": "Kuwait", "973": "Bahrain", "968": "Oman",
    "90": "Turkey", "380": "Ukraine", "7": "Russia",
    "31": "Netherlands", "32": "Belgium", "41": "Switzerland",
    "43": "Austria", "45": "Denmark", "46": "Sweden",
    "47": "Norway", "48": "Poland", "420": "Czech Republic",
    "36": "Hungary", "40": "Romania", "359": "Bulgaria",
    "385": "Croatia", "386": "Slovenia", "421": "Slovakia",
    "351": "Portugal", "353": "Ireland", "354": "Iceland",
    "358": "Finland", "370": "Lithuania", "371": "Latvia",
    "372": "Estonia", "60": "Malaysia", "62": "Indonesia",
    "63": "Philippines", "65": "Singapore", "66": "Thailand",
    "84": "Vietnam", "82": "South Korea", "886": "Taiwan",
    "64": "New Zealand", "51": "Peru", "57": "Colombia",
    "56": "Chile", "54": "Argentina", "593": "Ecuador",
    "507": "Panama", "506": "Costa Rica",
}

TLD_COUNTRY = {
    ".ma": "Morocco", ".dz": "Algeria", ".tn": "Tunisia",
    ".eg": "Egypt", ".ng": "Nigeria", ".za": "South Africa",
    ".co.uk": "UK", ".uk": "UK", ".us": "USA",
    ".fr": "France", ".de": "Germany", ".es": "Spain",
    ".it": "Italy", ".jp": "Japan", ".cn": "China",
    ".in": "India", ".au": "Australia", ".br": "Brazil",
    ".mx": "Mexico", ".ae": "UAE", ".sa": "Saudi Arabia",
    ".tr": "Turkey", ".ru": "Russia", ".nl": "Netherlands",
    ".be": "Belgium", ".ch": "Switzerland", ".at": "Austria",
    ".pt": "Portugal", ".ie": "Ireland", ".se": "Sweden",
    ".no": "Norway", ".dk": "Denmark", ".fi": "Finland",
    ".pl": "Poland", ".cz": "Czech Republic", ".ro": "Romania",
    ".hr": "Croatia", ".sg": "Singapore", ".my": "Malaysia",
    ".th": "Thailand", ".ph": "Philippines", ".id": "Indonesia",
    ".vn": "Vietnam", ".kr": "South Korea", ".tw": "Taiwan",
    ".nz": "New Zealand", ".ar": "Argentina", ".cl": "Chile",
    ".co": "Colombia", ".pe": "Peru",
}


class WebsiteIntelligenceExtractor:
    """Thread-safe enhanced web crawler that extracts ALL business intelligence."""

    CONTACT_PATHS = [
        "/contact", "/contact-us", "/contact.html", "/contact.php",
        "/about", "/about-us", "/about.html", "/about.php",
        "/team", "/our-team", "/staff", "/people", "/leadership",
        "/support", "/help", "/help-center", "/faq",
        "/get-in-touch", "/reach-us", "/write-to-us",
        "/pages/contact", "/page/contact", "/pages/about",
        "/contactez-nous", "/nous-contacter", "/a-propos", "/notre-equipe",
        "/fr/contact", "/fr/nous-contacter", "/fr/about", "/fr/a-propos",
        "/contacto", "/sobre-nosotros", "/quienes-somos",
        "/kontakt", "/ueber-uns", "/impressum",
        "/contato", "/sobre", "/sobre-nos",
        "/contatti", "/chi-siamo", "/dove-siamo",
        "/iletisim", "/hakkimizda", "/biz-kimiz",
        "/联系我们", "/关于我们", "/团队",
        "/お問い合わせ", "/会社概要",
        "/اتصل بنا", "/من نحن",
        "/legal", "/privacy", "/terms",
        "/directory", "/office", "/customer-service",
        "/who-we-are", "/what-we-do", "/footer",
        "/imprint", "/disclaimer",
    ]

    EMAIL_REGEXES = [
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
        r"mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})",
        r"data-cfemail[\"'\s:=]+([a-fA-F0-9]+)",
        r"email[\"'\s:=]+\"?([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})\"?",
        r"Email:\s*([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})",
        r"(?:var|let|const)\s+\w*[eE]mail\w*\s*=\s*[\"']([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})[\"']",
        r"email\s*:\s*[\"']([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})[\"']",
        r"[\"']([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})[\"']",
        r"(?:contact|info|support|sales|hello|admin|office)[\"'\s:=]+[\"']([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})[\"']",
        r"[\"']([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})[\"']\s*(?:;|,|\))",
        r"(?:e-?mail|courriel|correo)[^a-zA-Z0-9]*([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})",
        r"cdn-cgi/lh[\"'\s]*[\"']([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})[\"']",
        r"window\.__[A-Z_]+__\s*=\s*[\"']([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})[\"']",
        r"__cf_email__\[\"'\s]*=([a-fA-F0-9]+)",
        r"(?:contacte[- ]?nous|email[- ]?us)[^a-zA-Z0-9]*([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})",
        r"String\.fromCharCode\((\d+(?:,\d+)+)\)",
        r"(?:encoded|obfuscated|protect)\s*[\"':=]+\s*([a-fA-F0-9]{8,})",
        r"window\[\"[^\"]+\"\]\s*=\s*[\"']([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})[\"']",
        r"data-[a-z]*email[\"'\s:=]+\"?([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})\"?",
        r"(?:follow|write|send)[^a-zA-Z0-9]*([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})",
    ]

    PHONE_REGEXES = [
        r"(?:\+?\d{1,4}[\s.\-]?)?\(?\d{2,4}\)?[\s.\-]?\d{3,4}[\s.\-]?\d{3,4}",
        r"tel:([+\d\s\-()]+)",
        r"phone[\"'\s:=]+\"?([+\d\s\-()]+)\"?",
        r"(?:\+?212[\s.\-]?)?\(?0?\d{2,3}\)?[\s.\-]?\d{3,4}[\s.\-]?\d{3,4}",
        r"0\d{2}[\s.\-]?\d{2}[\s.\-]?\d{2}[\s.\-]?\d{2}",
        r"(?:\+?81[\s.\-]?)?\(?0?\d{1,4}\)?[\s.\-]?\d{1,4}[\s.\-]?\d{4}",
        r"0\d{1,4}[\s.\-]?\d{1,4}[\s.\-]?\d{4}",
        r"(?:Phone|Tel|Telephone|Mobile|Call|电话|TEL|FAX)[\"'\s:=]+\"?([+\d\s\-()]+)\"?",
        r"\+?\d{1,3}[\s.\-]?\(?\d{2,4}\)?[\s.\-]?\d{3,4}[\s.\-]?\d{3,4}",
        r"(?:phone|tel|mobile|call|whatsapp|fax)[^a-zA-Z0-9]{1,5}(\+?\d[\d\s\-()]{6,15})",
    ]

    SOCIAL_PATTERNS = {
        "facebook": [
            r"(?:https?://)?(?:www\.|m\.)?facebook\.com/([a-zA-Z0-9._\-]+)",
            r"(?:https?://)?(?:www\.|m\.)?fb\.com/([a-zA-Z0-9._\-]+)",
        ],
        "instagram": [
            r"(?:https?://)?(?:www\.)?instagram\.com/([a-zA-Z0-9._\-]+)",
        ],
        "linkedin": [
            r"(?:https?://)?(?:www\.)?linkedin\.com/company/([a-zA-Z0-9._\-]+)",
            r"(?:https?://)?(?:www\.)?linkedin\.com/in/([a-zA-Z0-9._\-]+)",
        ],
        "twitter": [
            r"(?:https?://)?(?:www\.)?twitter\.com/([a-zA-Z0-9._\-]+)",
            r"(?:https?://)?(?:www\.)?x\.com/([a-zA-Z0-9._\-]+)",
        ],
        "youtube": [
            r"(?:https?://)?(?:www\.)?youtube\.com/@([a-zA-Z0-9._\-]+)",
            r"(?:https?://)?(?:www\.)?youtube\.com/channel/([a-zA-Z0-9._\-]+)",
            r"(?:https?://)?(?:www\.)?youtube\.com/user/([a-zA-Z0-9._\-]+)",
        ],
        "tiktok": [
            r"(?:https?://)?(?:www\.)?tiktok\.com/@([a-zA-Z0-9._\-]+)",
        ],
        "whatsapp": [
            r"(?:https?://)?(?:wa\.me|api\.whatsapp\.com/send)(?:\?.*phone=)?(\+?\d[\d\s\-]{6,})",
            r"whatsapp[\"'\s:=]+\"?(\+?\d[\d\s\-]{6,})\"?",
            r"(?:https?://)?wa\.me/(\d+)",
        ],
        "telegram": [
            r"(?:https?://)?(?:t\.me|telegram\.me)/([a-zA-Z0-9._\-]+)",
            r"telegram[\"'\s:=]+\"?([a-zA-Z0-9._\-]+)\"?",
        ],
        "line": [
            r"(?:https?://)?line\.me/R/ti/p/([a-zA-Z0-9._\-]+)",
            r"(?:https?://)?line\.me/ti/@([a-zA-Z0-9._\-]+)",
            r"LINE\s*[\"'\s:=]+@?([a-zA-Z0-9._\-]+)",
        ],
        "wechat": [
            r"(?:https?://)?weixin\.qq\.com/([a-zA-Z0-9._\-]+)",
            r"微信[\"'\s:=]+\"?([a-zA-Z0-9._\-]+)\"?",
            r"WeChat\s*[\"'\s:=]+\"?([a-zA-Z0-9._\-]+)\"?",
        ],
        "vk": [
            r"(?:https?://)?(?:www\.)?vk\.com/([a-zA-Z0-9._\-]+)",
        ],
        "snapchat": [
            r"(?:https?://)?(?:www\.)?snapchat\.com/add/([a-zA-Z0-9._\-]+)",
        ],
        "pinterest": [
            r"(?:https?://)?(?:www\.)?pinterest\.com/([a-zA-Z0-9._\-]+)",
        ],
        "tripadvisor": [
            r"(?:https?://)?(?:www\.)?tripadvisor\.com/(?:Hotel_Review|Restaurant_Review|Attraction_Review).*?-d(\d+)",
        ],
    }

    NAME_PATTERNS = [
        r"(?:owner|founder|ceo|manager|director|president|directeur|proprietaire|gerant|fondateur)[\"'\s:=]+([A-Z][a-z]+ [A-Z][a-z]+(?:\s[A-Z][a-z]+)?)",
        r"(?:owner|founder|ceo|manager|director|president|directeur)[\"'\s:=]+([A-Z][a-z]+ [A-Z]\. [A-Z][a-z]+)",
        r"(?:Dr|Mr|Mrs|Ms|Prof|Dr\.|Sr|Sra)\s+([A-Z][a-z]+ [A-Z][a-z]+)",
        r"(?:Chef|Responsable|Head|Jefe|Director)\s+(?:de\s+\w+)?[\"'\s:=]+([A-Z][a-z]+ [A-Z][a-z]+)",
        r"<(?:h[2-6]|p|span|div)[^>]*>\s*(?:Dr|Mr|Mrs|Ms|Prof)\.?\s+([A-Z][a-z]+ [A-Z][a-z]+)\s*</(?:h[2-6]|p|span|div)>",
    ]

    IGNORE_EMAILS = [
        r".*\.png$", r".*\.jpg$", r".*\.gif$", r".*\.svg$",
        r".*\.css$", r".*\.js$", r".*\.woff$", r".*\.ttf$",
        r".*\.eot$", r".*\.ico$",
        r"sentry", r"no-reply", r"noreply", r"donotreply",
        r"mailer-daemon", r"postmaster@", r"webmaster@", r"abuse@",
        r"wixpress", r"sentry-next", r"@sentry", r"example\.com",
        r"test\.com", r"squarespace", r"wix\.com", r"shopify",
        r"wordpress\.com", r"gravatar\.com", r"wp\.com",
        r"schema\.org", r"w3\.org", r"googleapis\.com",
        r"gstatic\.com", r"googletagmanager\.com",
        r"facebook\.com", r"twitter\.com", r"instagram\.com",
        r"linkedin\.com", r"youtube\.com",
        r"larousse\.fr", r"conso@", r"info@m\.me",
        r"smtp\.", r"mx\.", r"alt[0-9]\.", r"aspmx\.",
        r"google\.com", r"outlook\.com", r"yahoo\.com",
        r"hotmail\.com", r"protonmail\.com", r"zoho\.com",
        r"^nom@", r"^name@", r"^prenom@", r"^votre@",
        r"^votre\.email@", r"^email@", r"^user@",
        r"^fname@", r"^lname@", r"^first\.last@",
        r"^johndoe@", r"^janedoe@", r"^doe@",
        r"^changeme@", r"^replace@", r"^insert@",
        r"^your[_-]?email@", r"^your[_-]?name@",
        r"^me@", r"^someone@", r"^anyone@",
        r"^hello@", r"^hi@", r"^hey@",
        r"^admin@", r"^info@localhost",
        r"^placeholder@", r"^sample@", r"^demo@",
        r"^your@", r"^your\.email@", r"^your_email@",
        r"^example@", r"^example\.",
        r"email@example", r"email@domain", r"email@your",
        r"your@email", r"your_email@domain", r"your@email\.com",
        r"example@mysite", r"test@example", r"name@example",
        r"your@email\.com", r"your_email@example",
        r"antispam", r"antispamcloud", r"rzone\.de",
        r"spam", r"filter[0-9]", r"smtpin\.",
        r"wixsite\.com", r"wix\.com",
        r"cloudflare", r"cloudfront", r"amazonaws\.com",
        r"herokuapp\.com", r"vercel\.app", r"netlify\.app",
        r"mailerlite\.", r"sendgrid\.", r"mailchimp\.",
        r"bounces\.", r"bounce\.", r"returnpath\.",
        r"doubleclick\.net", r"googlesyndication",
        r"archive\.org", r"secureserver\.net", r"go Daddy",
        r"mediarelations@", r"press@", r"media@",
        r"\.\.", r"\.correo$", r"\.com\.", r"\.org\.",
        r"^[a-z](?:info|contact|hello|support|sales|office|admin|booking|reservation|enquiries)@",
        r"^[a-z]{2}(?:info|contact|hello|support|sales|office|admin|booking|reservation|enquiries)@",
        r"^-",
    ]

    FAKE_TLDS = {
        "wct", "xyz", "tk", "ml", "ga", "cf", "gq", "top", "buzz",
        "click", "link", "work", "day", "live", "rock", "ninja",
        "guru", "expert", "today", "date", "chat", "fun", "surf",
        "men", "racing", "win", "bid", "loan", "review", "download",
        "party", "dating", "vegas", "horse", "kitchen", "fashion",
        "plumbing", "plumber", "attorney", "lawyer", "clinic", "dental",
        "dentist", "cleaning", "carpet", "locksmith", "mover", "roofing",
        "hvac", "pest", "tree", "lawn", "electrician", "painter",
        "handyman", "contractor", "construction", "maid", "landscaping",
        "pool", "spa", "fitness", "gym", "yoga", "salon", "beauty",
        "nail", "hair", "barber", "chiro", "optometrist", "physio",
        "therapy", "counseling", "psychiatrist", "psychologist",
        "nutrition", "diet", "weight", "bootcamp", "crossfit", "martial",
        "boxing", "gymnastics", "dance", "music", "art", "photo", "video",
        "film", "dj", "band", "event", "wedding", "rental", "catering",
        "bakery", "coffee", "cafe", "restaurant", "bar", "pub", "brewery",
        "winery", "vineyard", "farm", "garden", "nursery", "pet", "vet",
        "animal", "dog", "cat", "bird", "fish", "reptile", "aquarium",
        "zoo", "museum", "gallery", "theater", "cinema", "park", "beach",
        "mountain", "lake", "river", "island", "forest", "desert",
        "city", "town", "village", "country", "world", "earth", "moon",
        "star", "sun", "sky", "cloud", "rain", "snow", "wind", "fire",
        "water", "air", "space", "time", "love", "peace", "war", "hope",
        "dream", "magic", "fantasy", "adventure", "quest", "journey",
        "travel", "tour", "trip", "vacation", "holiday", "cruise",
        "flight", "hotel", "hostel", "camp", "resort", "wellness",
        "health", "medical", "hospital", "pharmacy", "drug", "pill",
        "vitamin", "supplement", "cbd", "cannabis", "weed", "marijuana",
        "hemp", "thc", "psychedelic", "mushroom", "lsd", "mdma",
        "ecstasy", "cocaine", "heroin", "fentanyl", "meth", "amphetamine",
        "steroid", "testosterone", "hgh", "peptide", "sarm", "prohormone",
        "novelty", "fake", "replica", "counterfeit", "knockoff",
        "discount", "sale", "deal", "offer", "coupon", "promo", "voucher",
        "cashback", "reward", "loyalty", "points", "miles", "credit",
        "debit", "finance", "invest", "stock", "crypto", "bitcoin",
        "ethereum", "blockchain", "nft", "metaverse",
    }

    BUSINESS_TYPES = {
        "barbershop": ["barber", "barbershop", "barber shop", "haircut", "shave", "fade", "trim", "mens hair", "gentlemen", "tonsorial"],
        "hair_salon": ["salon", "hairdresser", "hairdressers", "hair stylist", "hair stylist", "blow dry", "hair color", "highlights", "balayage", "keratin", "extensions", "braids"],
        "gym": ["gym", "fitness", "workout", "exercise", "personal trainer", "crossfit", "weight training", "cardio", "strength training", "muscle", "bodybuilding", "strength", "conditioning", "squats", "deadlift", "bench press", "health club", "training", "trainer", "studio", "pilates", "yoga", "membership", "member", "classes", "group fitness", "equipment", "treadmill", "dumbbell", "barbell", "squat rack", "locker", "sauna", "spa", "pool"],
        "restaurant": ["restaurant", "dining", "menu", "appetizer", "entree", "dessert", "chef", "cuisine", "reservations", "food", "meal", "dinner", "lunch", "breakfast", "brunch"],
        "cafe": ["cafe", "coffee", "espresso", "latte", "cappuccino", "mocha", "brew", "barista", "pastry", "sandwich", "teahouse", "tearoom"],
        "bar": ["bar", "pub", "tavern", "lounge", "cocktail", "beer", "wine", "liquor", "spirits", "drinks", "happy hour", "nightclub"],
        "hotel": ["hotel", "motel", "inn", "resort", "accommodation", "lodging", "suite", "room", "booking", "check-in", "concierge", "hospitality"],
        "dental": ["dentist", "dental", "teeth", "tooth", "cavity", "root canal", "crown", "bridge", "implant", "whitening", "orthodont", "braces", "invisalign", "periodontal", "oral surgery"],
        "medical": ["doctor", "physician", "clinic", "medical", "healthcare", "patient", "diagnosis", "treatment", "prescription", "surgery", "hospital", "care"],
        "lawyer": ["lawyer", "attorney", "legal", "law firm", "litigation", "court", "lawsuit", "counsel", "paralegal", "juris doctor", "esquire"],
        "real_estate": ["real estate", "realtor", "property", "listing", "house", "apartment", "condo", "mortgage", "buyer", "seller", "open house", "foreclosure"],
        "plumber": ["plumber", "plumbing", "pipe", "leak", "drain", "faucet", "toilet", "water heater", "sewer", "clog", "sump pump", "backflow"],
        "electrician": ["electrician", "electrical", "wiring", "circuit", "breaker", "outlet", "switch", "panel", "lighting", "generator", "surge protector"],
        "landscaping": ["landscaping", "lawn", "garden", "mowing", "hedging", "tree trimming", "mulch", "sprinkler", "irrigation", "sod", "design"],
        "cleaning": ["cleaning", "janitorial", "maid", "housekeeping", "carpet cleaning", "window cleaning", "pressure washing", "sanitization", "deep clean"],
        "roofing": ["roofing", "roof", "shingle", "gutter", "siding", "flashing", "membrane", "waterproofing", "inspection", "repair"],
        "construction": ["construction", "contractor", "building", "remodeling", "renovation", "addition", "demolition", "framing", "drywall", "carpentry"],
        "auto_repair": ["auto repair", "mechanic", "garage", "oil change", "brake", "tire", "engine", "transmission", "diagnostic", "inspection"],
        "pet": ["pet", "animal", "dog", "cat", "grooming", "veterinary", "vet", "kennel", "boarding", "adoption", "pet store", "pet shop"],
        "bakery": ["bakery", "bakery", "bread", "cake", "pastry", "cookie", "pie", "donut", "croissant", "baguette", "baking"],
        "photography": ["photography", "photographer", "photo", "portrait", "wedding photo", "event photo", "studio", "headshot", "boudoir", "family photo"],
        "spa": ["spa", "massage", "facial", "skincare", "waxing", "nails", "manicure", "pedicure", "relaxation", "wellness"],
        "yoga": ["yoga", "pilates", "meditation", "mindfulness", "stretching", "breathing", "studio", "class", "mat", "pose"],
        "accounting": ["accountant", "accounting", "tax", "bookkeeping", "payroll", "audit", "financial statement", "cpa", "tax return"],
        "marketing": ["marketing", "advertising", "seo", "social media", "content", "branding", "campaign", "digital marketing", "agency"],
        "web_design": ["web design", "website", "wordpress", "e-commerce", "ui/ux", "graphic design", "logo", "development", "hosting"],
        "default": [],
    }

    HOURS_PATTERNS = [
        r"(?:Mon|Monday|Lundi)\w*[\s:\-]+(\d{1,2}[:.]?\d{2})\s*[\-–to]+\s*(\d{1,2}[:.]?\d{2})",
        r"(?:Lun|Lundi)\w*[\s:\-]+(\d{1,2}[:.]?\d{2})\s*[\-–au]+\s*(\d{1,2}[:.]?\d{2})",
    ]

    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config or ScraperConfig()
        self.crawler = AntiBypassCrawler(
            timeout=5, max_retries=1, fast_mode=self.config.fast_mode,
            proxy_server=self.config.proxy_server,
            proxy_list_file=self.config.proxy_list_file,
            use_free_proxies=False,
        )
        self._lock = threading.Lock()
        self.CONTACT_PATHS = list(self.CONTACT_PATHS)  # Instance copy, not class-level

    def set_country(self, country: str):
        """Thread-safe country setter."""
        with self._lock:
            self.crawler.set_country(country)
            from lead_generator.utils.keywords import get_contact_paths_for_country
            extra_paths = get_contact_paths_for_country(country)
            for path in extra_paths:
                if path not in self.CONTACT_PATHS:
                    self.CONTACT_PATHS.append(path)

    def find_contacts(self, website_url: str, crawl_pages: bool = True) -> Dict[str, any]:
        """Find ALL business intelligence from a website. Early-exits when emails found."""
        result = {
            "emails": [],
            "phones": [],
            "social_profiles": {},
            "owner_name": "",
            "operating_hours": "",
            "address": "",
            "city": "",
            "state": "",
            "zip_code": "",
            "country": "",
            "description": "",
            "rating": "",
            "whatsapp": "",
            "telegram": "",
        }

        if not website_url:
            return result

        if not website_url.startswith(("http://", "https://")):
            website_url = "https://" + website_url

        parsed = urlparse(website_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        domain = parsed.netloc

        pages_to_check = [website_url]
        if crawl_pages:
            max_pages = 4 if self.config.fast_mode else self.config.max_pages_per_website
            priority_paths = ["/contact", "/about", "/about-us", "/contact-us",
                            "/legal", "/privacy", "/terms", "/team", "/staff"]
            for path in priority_paths[:max_pages]:
                page_url = base + path
                if page_url not in pages_to_check:
                    pages_to_check.append(page_url)

            if not self.config.fast_mode:
                try:
                    sitemap_url = base + "/sitemap.xml"
                    sitemap_html = self.crawler.fetch(sitemap_url, use_referrer=False)
                    if sitemap_html and "<url>" in sitemap_html:
                        sitemap_urls = re.findall(r"<loc>(.*?)</loc>", sitemap_html)
                        for surl in sitemap_urls:
                            sl = surl.lower()
                            if any(kw in sl for kw in ["contact", "about", "team", "staff", "email",
                                                       "support", "help", "nous", "contacter",
                                                       "kontakt", "about-us", "impressum",
                               "legal", "privacy", "terms", "directory", "office",
                               "customer-service", "who-we-are", "what-we-do",
                               "imprint", "disclaimer", "footer", "info"]):
                                if surl not in pages_to_check:
                                    pages_to_check.append(surl)
                except Exception:
                    pass

                try:
                    robots_url = base + "/robots.txt"
                    robots_html = self.crawler.fetch(robots_url, use_referrer=False)
                    if robots_html:
                        for line in robots_html.split("\n"):
                            line = line.strip().lower()
                            if line.startswith("disallow:") or line.startswith("allow:"):
                                path_match = re.search(r"[:\s]+(/[^\s]+)", line)
                                if path_match:
                                    rpath = path_match.group(1)
                                    rl = rpath.lower()
                                    if any(kw in rl for kw in ["contact", "about", "team", "email",
                                                               "support", "help", "admin", "staff",
                                                               "legal", "privacy", "info", "office"]):
                                        rurl = base + rpath
                                        if rurl not in pages_to_check:
                                            pages_to_check.append(rurl)
                        rss_match = re.search(r"Sitemap:\s*(.+)", robots_html, re.I)
                        if rss_match:
                            rss_url = rss_match.group(1).strip()
                            if not rss_url.startswith("http"):
                                rss_url = base + rss_url
                            rss_html = self.crawler.fetch(rss_url, use_referrer=False)
                            if rss_html:
                                rss_urls = re.findall(r"<loc>(.*?)</loc>", rss_html)
                                for rurl in rss_urls[:20]:
                                    if rurl not in pages_to_check:
                                        pages_to_check.append(rurl)
                except Exception:
                    pass

        checked_urls: Set[str] = set()
        all_emails: Set[str] = set()
        all_phones: Set[str] = set()
        all_social: Dict[str, str] = {}
        found_names: List[str] = []
        hours_list: List[str] = []
        address_parts: List[str] = []
        city = state = zip_code = country = description = rating = ""
        whatsapp = telegram = ""
        captcha_detected = False
        emails_found = False

        for url in pages_to_check:
            if url in checked_urls or captcha_detected:
                continue
            checked_urls.add(url)

            try:
                html = self.crawler.fetch(url, use_referrer=True)
                if not html:
                    continue

                html_lower = html.lower()
                if any(x in html_lower for x in ["unusual traffic", "verify you are human",
                                                   "challenge-platform", "ray id"]):
                    if "cloudflare" in html_lower and any(x in html_lower for x in ["captcha", "turnstile", "challenge-platform", "verify you are human"]):
                        captcha_detected = True
                        continue
                    elif "cloudflare" not in html_lower:
                        captcha_detected = True
                        continue

                soup = BeautifulSoup(html, "lxml")

                emails = self._extract_emails(soup, html)
                all_emails.update(emails)

                data_emails = self._extract_emails_from_data_attributes(soup)
                all_emails.update(data_emails)

                title_emails = self._extract_emails_from_link_titles(soup)
                all_emails.update(title_emails)

                if all_emails:
                    emails_found = True

                phones = self._extract_phones(soup, html)
                all_phones.update(phones)

                social = self._extract_social_profiles(html)
                all_social.update(social)

                if not whatsapp:
                    wa = self._extract_whatsapp(html)
                    if wa:
                        whatsapp = wa
                if not whatsapp:
                    wa = self._extract_whatsapp_from_buttons(html)
                    if wa:
                        whatsapp = wa

                if not found_names:
                    names = self._extract_names(soup)
                    if names:
                        found_names.extend(names)

                if not hours_list:
                    h = self._extract_hours(soup, html)
                    if h:
                        hours_list.append(h)

                if not address_parts:
                    addr = self._extract_address(soup)
                    if addr:
                        address_parts.append(addr)

                if not city:
                    city = self._extract_city(soup)
                if not country:
                    country = self._extract_country_from_html(html)
                if not description:
                    description = self._extract_description(soup)
                if not rating:
                    rating = self._extract_rating(soup)

                if not telegram:
                    tg = self._extract_telegram(html)
                    if tg:
                        telegram = tg

                inline_js_emails = set()
                for script in soup.find_all("script"):
                    if script.string:
                        js_text = script.string
                        found = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", js_text)
                        for email in found:
                            if self._is_valid_email(email):
                                inline_js_emails.add(email.lower())
                        for match in re.findall(r"String\.fromCharCode\((\d+(?:,\d+)+)\)", js_text):
                            decoded = self._decode_string_fromcharcode(match)
                            if "@" in decoded:
                                found = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", decoded)
                                for email in found:
                                    if self._is_valid_email(email):
                                        inline_js_emails.add(email.lower())
                all_emails.update(inline_js_emails)
                if inline_js_emails:
                    emails_found = True

                if emails_found and all_phones and all_social and found_names:
                    break

            except Exception:
                continue

        if not all_emails:
            try:
                guessed_emails = self._guess_email_patterns(domain)
                all_emails.update(guessed_emails)
                if all_emails:
                    emails_found = True
            except Exception:
                pass

        if not all_emails and not captcha_detected:
            parsed = urlparse(website_url)
            base = f"{parsed.scheme}://{parsed.netloc}"
            try:
                home_html = self.crawler.fetch(website_url, use_referrer=True)
                if home_html:
                    home_soup = BeautifulSoup(home_html, "lxml")
                    internal_links = set()
                    for a_tag in home_soup.find_all("a", href=True):
                        href = a_tag["href"]
                        if href.startswith("/"):
                            href = base + href
                        if not href.startswith(base):
                            continue
                        link_text = (a_tag.get_text() + " " + href).lower()
                        if any(kw in link_text for kw in ["contact", "about", "team", "staff", "email",
                                                           "support", "help", "reach", "touch", "write",
                                                           "nous", "contacter", "about", "kontakt",
                                                           "-contact", "about-us", "team",
                           "legal", "privacy", "terms", "info", "office",
                           "directory", "customer-service", "who-we-are",
                           "imprint", "disclaimer", "footer", "careers",
                           "jobs", "partners", "press", "media"]):
                            if href not in checked_urls:
                                internal_links.add(href)
                    for link_url in list(internal_links)[:15]:
                        if link_url in checked_urls:
                            continue
                        checked_urls.add(link_url)
                        try:
                            html = self.crawler.fetch(link_url, use_referrer=True)
                            if not html:
                                continue
                            soup = BeautifulSoup(html, "lxml")
                            emails = self._extract_emails(soup, html)
                            all_emails.update(emails)
                            if all_emails:
                                emails_found = True
                                phones = self._extract_phones(soup, html)
                                all_phones.update(phones)
                                social = self._extract_social_profiles(html)
                                all_social.update(social)
                                if not found_names:
                                    names = self._extract_names(soup)
                                    if names:
                                        found_names.extend(names)
                                break
                        except Exception:
                            continue
            except Exception:
                pass

        if not all_emails and not captcha_detected:
            try:
                js_emails = self._extract_emails_from_js_files(base)
                all_emails.update(js_emails)
                if all_emails:
                    emails_found = True
            except Exception:
                pass

        if not all_emails and not captcha_detected:
            try:
                pdf_emails = self._extract_emails_from_pdfs(base)
                all_emails.update(pdf_emails)
                if all_emails:
                    emails_found = True
            except Exception:
                pass

        if not all_emails and not captcha_detected:
            try:
                header_emails = self._extract_emails_from_http_headers(website_url)
                all_emails.update(header_emails)
                if all_emails:
                    emails_found = True
            except Exception:
                pass

        if not all_emails:
            try:
                mx_emails = self._lookup_mx_records(domain)
                all_emails.update(mx_emails)
                if all_emails:
                    emails_found = True
            except Exception:
                pass

        if not all_emails and not captcha_detected:
            try:
                wayback_html = self._fetch_wayback_version(website_url)
                if wayback_html:
                    wayback_soup = BeautifulSoup(wayback_html, "lxml")
                    wayback_emails = self._extract_emails(wayback_soup, wayback_html)
                    all_emails.update(wayback_emails)
                    if all_emails:
                        emails_found = True
            except Exception:
                pass

        # Fallback: WordPress REST API
        if not all_emails and not captcha_detected:
            try:
                wp_emails = self._extract_emails_from_wordpress_api(base)
                all_emails.update(wp_emails)
                if all_emails:
                    emails_found = True
            except Exception:
                pass

        # Fallback: CMS paths (WordPress, GraphQL, APIs)
        if not all_emails and not captcha_detected:
            try:
                cms_emails = self._extract_emails_from_cms_paths(base)
                all_emails.update(cms_emails)
                if all_emails:
                    emails_found = True
            except Exception:
                pass

        # Fallback: Bing site: search for emails
        if not all_emails and not captcha_detected:
            try:
                bing_emails = self._search_bing_for_emails(domain)
                all_emails.update(bing_emails)
                if all_emails:
                    emails_found = True
            except Exception:
                pass

        # Fallback: Google cache for emails
        if not all_emails and not captcha_detected:
            try:
                cache_emails = self._search_google_cache_for_emails(domain)
                all_emails.update(cache_emails)
                if all_emails:
                    emails_found = True
            except Exception:
                pass

        # Fallback: Social media bio email extraction
        if not all_emails and not captcha_detected:
            try:
                social_emails = self._search_social_media_for_emails(domain, website_url)
                all_emails.update(social_emails)
                if all_emails:
                    emails_found = True
            except Exception:
                pass

        result["emails"] = self._filter_emails(all_emails)
        result["phones"] = list(all_phones)[:5]
        result["social_profiles"] = all_social
        result["owner_name"] = found_names[0] if found_names else ""
        result["operating_hours"] = hours_list[0] if hours_list else ""
        result["address"] = address_parts[0] if address_parts else ""
        result["city"] = city
        result["state"] = state
        result["zip_code"] = zip_code
        result["country"] = country
        result["description"] = description
        result["rating"] = rating
        result["whatsapp"] = whatsapp
        result["telegram"] = telegram

        if not whatsapp and all_phones:
            phone_digits = re.sub(r"\D", "", list(all_phones)[0])
            if phone_digits and len(phone_digits) >= 8:
                result["whatsapp"] = "https://wa.me/%s" % phone_digits

        if result["emails"]:
            result["email"] = result["emails"][0]
        if result["phones"]:
            result["phone_from_site"] = result["phones"][0]

        return result

    def _extract_emails(self, soup: BeautifulSoup, html: str) -> Set[str]:
        """Aggressive multi-layer email extraction."""
        emails = set()

        for link in soup.find_all("a", href=re.compile(r"mailto:", re.I)):
            href = link.get("href", "")
            email = href.replace("mailto:", "").split("?")[0].strip()
            if self._is_valid_email(email):
                emails.add(email.lower())

        for tag in soup.find_all(attrs={"data-cfemail": True}):
            encoded = tag["data-cfemail"]
            decoded = self._decode_cfemail(encoded)
            if decoded and self._is_valid_email(decoded):
                emails.add(decoded.lower())

        cf_pattern = re.compile(r'data-cfemail\s*=\s*["\']([a-fA-F0-9]+)["\']', re.I)
        for match in cf_pattern.finditer(html):
            decoded = self._decode_cfemail(match.group(1))
            if decoded and self._is_valid_email(decoded):
                emails.add(decoded.lower())

        for pattern in self.EMAIL_REGEXES:
            matches = re.findall(pattern, html, re.I)
            for match in matches:
                email = match.strip().lower().strip("\"'")
                if self._is_valid_email(email):
                    emails.add(email)

        for tag in soup.find_all(["footer", "header", "div", "section", "p", "span", "li", "td", "th", "a", "strong", "b", "em"]):
            text = tag.get_text()
            found = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
            for email in found:
                if self._is_valid_email(email):
                    emails.add(email.lower())

        for tag in soup.find_all(style=re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden", re.I)):
            text = tag.get_text()
            found = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
            for email in found:
                if self._is_valid_email(email):
                    emails.add(email.lower())

        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                emails.update(self._extract_emails_from_json(data))
            except Exception:
                continue

        for meta in soup.find_all("meta"):
            content = meta.get("content", "")
            if "@" in content:
                found = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", content)
                for email in found:
                    if self._is_valid_email(email):
                        emails.add(email.lower())

        for noscript in soup.find_all("noscript"):
            text = noscript.get_text()
            found = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
            for email in found:
                if self._is_valid_email(email):
                    emails.add(email.lower())

        for style in soup.find_all("style"):
            text = style.string or ""
            found = re.findall(r"content\s*:\s*[\"'].*?([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}).*?[\"']", text, re.I)
            for email in found:
                if self._is_valid_email(email):
                    emails.add(email.lower())

        for match in re.findall(r"String\.fromCharCode\((\d+(?:,\d+)+)\)", html):
            decoded = self._decode_string_fromcharcode(match)
            if "@" in decoded:
                found = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", decoded)
                for email in found:
                    if self._is_valid_email(email):
                        emails.add(email.lower())

        for match in re.findall(r"(?:encoded|obfuscated|protect)\s*[\"':=]+\s*([a-fA-F0-9]{8,})", html, re.I):
            decoded = self._decode_cfemail(match)
            if decoded and self._is_valid_email(decoded):
                emails.add(decoded.lower())

        for match in re.findall(r"data-[a-z]*email[\"'\s:=]+\"?([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})\"?", html, re.I):
            if self._is_valid_email(match):
                emails.add(match.lower())

        for encoded in re.findall(r"(?:email|courriel|correo)\s*=\s*[\"']([A-Za-z0-9+/=]{20,})[\"']", html, re.I):
            decoded = self._decode_base64_email(encoded)
            if decoded and self._is_valid_email(decoded):
                emails.add(decoded.lower())

        deobfuscated = self._decode_common_obfuscation(html)
        if "@" in deobfuscated:
            found = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", deobfuscated)
            for email in found:
                if self._is_valid_email(email):
                    emails.add(email.lower())

        for match in re.findall(r'(?:var|let|const)\s+\w+\s*=\s*\[(["\'][^"\']+["\'](?:\s*,\s*["\'][^"\']+["\'])*)\]', html):
            parts = re.findall(r'["\']([^"\']+)["\']', match)
            if parts:
                reconstructed = "".join(parts)
                if "@" in reconstructed:
                    found = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", reconstructed)
                    for email in found:
                        if self._is_valid_email(email):
                            emails.add(email.lower())

        for match in re.findall(r'\\x([0-9a-fA-F]{2})', html):
            pass
        hex_strings = re.findall(r'(?:["\']|`)((?:\\x[0-9a-fA-F]{2}){5,})', html)
        for hstr in hex_strings:
            try:
                decoded = bytes(hstr, 'utf-8').decode('unicode_escape')
                if "@" in decoded:
                    found = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", decoded)
                    for email in found:
                        if self._is_valid_email(email):
                            emails.add(email.lower())
            except Exception:
                pass

        for match in re.findall(r'\\u([0-9a-fA-F]{4})', html):
            pass
        unicode_strings = re.findall(r'(?:["\']|`)((?:\\u[0-9a-fA-F]{4}){5,})', html)
        for ustr in unicode_strings:
            try:
                decoded = bytes(ustr, 'utf-8').decode('unicode_escape')
                if "@" in decoded:
                    found = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", decoded)
                    for email in found:
                        if self._is_valid_email(email):
                            emails.add(email.lower())
            except Exception:
                pass

        for match in re.finditer(r"rgb(?:a)?\((\d{1,3}(?:\s*,\s*\d{1,3}){2,})\)", html):
            nums = re.findall(r"\d{1,3}", match.group(1))
            if len(nums) >= 3:
                try:
                    decoded = "".join(chr(int(n)) for n in nums if 32 <= int(n) <= 126)
                    if "@" in decoded and "." in decoded:
                        found = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", decoded)
                        for email in found:
                            if self._is_valid_email(email):
                                emails.add(email.lower())
                except Exception:
                    pass

        hydration_patterns = [
            r"window\.__NEXT_DATA__\s*=\s*(\{.*?\})\s*(?:;|</script>)",
            r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*(?:;|</script>)",
            r"window\.__APP_DATA__\s*=\s*(\{.*?\})\s*(?:;|</script>)",
        ]
        for hp in hydration_patterns:
            for match in re.finditer(hp, html, re.S):
                blob = match.group(1)
                found = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", blob)
                for email in found:
                    if self._is_valid_email(email):
                        emails.add(email.lower())

        for container in soup.find_all(["div", "span", "p", "a", "td"]):
            text = container.get_text()
            parts = re.split(r"\s+", text.strip())
            for i in range(len(parts) - 1):
                if "@" in parts[i]:
                    combined = parts[i] + parts[i+1]
                    found = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", combined)
                    for email in found:
                        if self._is_valid_email(email):
                            emails.add(email.lower())

        return emails

    def _extract_phones(self, soup: BeautifulSoup, html: str) -> Set[str]:
        """Extract phone numbers from page."""
        phones = set()

        for link in soup.find_all("a", href=re.compile(r"tel:", re.I)):
            href = link.get("href", "")
            phone = href.replace("tel:", "").strip()
            if self._is_valid_phone(phone):
                phones.add(phone)

        for pattern in self.PHONE_REGEXES:
            matches = re.findall(pattern, html, re.I)
            for match in matches:
                phone = match.strip().strip("\"'")
                if self._is_valid_phone(phone):
                    phones.add(phone)

        for tag in soup.find_all(["span", "div", "p", "a", "td", "li", "strong", "b"]):
            text = tag.get_text(strip=True)
            if re.search(r"(?:\+?\d[\d\s\-()]{7,})", text):
                found = re.findall(r"(?:\+?\d[\d\s\-()]{7,})", text)
                for phone in found:
                    if self._is_valid_phone(phone):
                        phones.add(phone.strip())

        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                self._extract_phones_from_json(data, phones)
            except Exception:
                continue

        return phones

    def _extract_social_profiles(self, html: str) -> Dict[str, str]:
        """Extract social media profile URLs."""
        profiles = {}

        for platform, patterns in self.SOCIAL_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, html, re.I)
                for match in matches:
                    clean = match.strip("/").split("/")[0]
                    if clean and len(clean) > 1 and clean not in ("www", "m", "api", "send"):
                        if platform == "facebook":
                            profiles[platform] = f"https://facebook.com/{clean}"
                        elif platform == "instagram":
                            profiles[platform] = f"https://instagram.com/{clean}"
                        elif platform == "linkedin":
                            profiles[platform] = f"https://linkedin.com/company/{clean}"
                        elif platform == "twitter":
                            profiles[platform] = f"https://twitter.com/{clean}"
                        elif platform == "youtube":
                            profiles[platform] = f"https://youtube.com/@{clean}"
                        elif platform == "tiktok":
                            profiles[platform] = f"https://tiktok.com/@{clean}"
                        elif platform == "whatsapp":
                            profiles[platform] = f"https://wa.me/{clean}"
                        elif platform == "telegram":
                            profiles[platform] = f"https://t.me/{clean}"
                        elif platform == "line":
                            profiles[platform] = f"https://line.me/ti/@{clean}"
                        elif platform == "wechat":
                            profiles[platform] = f"WeChat: {clean}"
                        elif platform == "vk":
                            profiles[platform] = f"https://vk.com/{clean}"
                        elif platform == "snapchat":
                            profiles[platform] = f"https://snapchat.com/add/{clean}"
                        elif platform == "pinterest":
                            profiles[platform] = f"https://pinterest.com/{clean}"
                        break
                if platform in profiles:
                    break

        return profiles

    def _extract_names(self, soup: BeautifulSoup) -> List[str]:
        """Try to extract owner/manager names."""
        names = []
        text = soup.get_text()

        for pattern in self.NAME_PATTERNS:
            matches = re.findall(pattern, text, re.I)
            names.extend(matches)

        team_section = soup.find(
            ["section", "div"],
            class_=re.compile(r"team|staff|about|people|equipe|personnel", re.I)
        )
        if team_section:
            for h in team_section.find_all(["h2", "h3", "h4", "h5"]):
                text = h.get_text().strip()
                if re.match(r"^[A-Z][a-z]+ [A-Z][a-z]+(?:\s[A-Z][a-z]+)?$", text):
                    names.append(text)

        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                names.extend(self._extract_names_from_json(data))
            except Exception:
                continue

        return names[:3]

    def _extract_hours(self, soup: BeautifulSoup, html: str) -> str:
        """Extract operating hours."""
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                hours = self._extract_hours_from_json(data)
                if hours:
                    return hours
            except Exception:
                continue

        hours_tag = soup.find(
            ["div", "span", "p", "section"],
            class_=re.compile(r"hours?|horaires?|opening|schedule|time", re.I)
        )
        if hours_tag:
            text = hours_tag.get_text(strip=True)
            if text and len(text) < 200:
                return text

        for pattern in self.HOURS_PATTERNS:
            match = re.search(pattern, html, re.I)
            if match:
                return match.group(0)

        return ""

    def _extract_address(self, soup: BeautifulSoup) -> str:
        """Extract full address."""
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                addr = self._extract_address_from_json(data)
                if addr:
                    return addr
            except Exception:
                continue

        addr_tag = soup.find(
            ["address", "div", "span", "p"],
            class_=re.compile(r"address|adresse|location|lieu|coordonnees", re.I)
        )
        if addr_tag:
            text = addr_tag.get_text(separator=", ", strip=True)
            if text and len(text) < 300:
                return text

        for tag in soup.find_all("address"):
            text = tag.get_text(separator=", ", strip=True)
            if text and len(text) < 300:
                return text

        return ""

    def _extract_city(self, soup: BeautifulSoup) -> str:
        """Extract city name."""
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                city = self._extract_city_from_json(data)
                if city:
                    return city
            except Exception:
                continue
        return ""

    def _extract_country_from_html(self, html: str) -> str:
        """Detect country from HTML content."""
        html_lower = html.lower()
        for tld, country in TLD_COUNTRY.items():
            if country and tld in html_lower:
                return country

        for code, country in PHONE_COUNTRY_CODES.items():
            if f"+{code}" in html or f"+{code} " in html:
                return country

        return ""

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract business description."""
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                desc = self._extract_description_from_json(data)
                if desc:
                    return desc[:500]
            except Exception:
                continue

        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            return meta_desc.get("content", "")[:500]

        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            return og_desc.get("content", "")[:500]

        return ""

    def _extract_rating(self, soup: BeautifulSoup) -> str:
        """Extract rating/review score."""
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                rating = self._extract_rating_from_json(data)
                if rating:
                    return rating
            except Exception:
                continue

        rating_tag = soup.find(
            ["span", "div"],
            class_=re.compile(r"rating|review|note|star", re.I)
        )
        if rating_tag:
            text = rating_tag.get_text(strip=True)
            match = re.search(r"(\d[\d.,]*)\s*(?:/\s*5|\((\d+)\))", text)
            if match:
                return text

        return ""

    def _extract_whatsapp(self, html: str) -> str:
        """Extract WhatsApp number."""
        patterns = [
            r"(?:https?://)?(?:wa\.me|api\.whatsapp\.com/send)(?:\?.*phone=)?(\+?\d[\d\s\-]{6,})",
            r"whatsapp[\"'\s:=]+\"?(\+?\d[\d\s\-]{6,})\"?",
            r"(?:https?://)?wa\.me/(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.I)
            if match:
                return match.group(1).strip()
        return ""

    def _extract_telegram(self, html: str) -> str:
        """Extract Telegram link."""
        patterns = [
            r"(?:https?://)?(?:t\.me|telegram\.me)/([a-zA-Z0-9._\-]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.I)
            if match:
                return match.group(1).strip()
        return ""

    def _decode_cfemail(self, encoded: str) -> str:
        """Decode Cloudflare email obfuscation."""
        try:
            r = int(encoded[:2], 16)
            return "".join(
                chr(int(encoded[i:i+2], 16) ^ r)
                for i in range(2, len(encoded), 2)
            )
        except Exception:
            return ""

    def _decode_string_fromcharcode(self, match: str) -> str:
        """Decode JavaScript String.fromCharCode obfuscation."""
        try:
            codes = re.findall(r"(\d+)", match)
            return "".join(chr(int(c)) for c in codes)
        except Exception:
            return ""

    def _decode_html_entities(self, text: str) -> str:
        """Decode HTML entities like &#64; to @."""
        import html
        decoded = html.unescape(text)
        decoded = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), decoded)
        decoded = re.sub(r"&#x([0-9a-fA-F]+);", lambda m: chr(int(m.group(1), 16)), decoded)
        return decoded

    def _decode_rot13(self, text: str) -> str:
        """Decode ROT13 obfuscation."""
        try:
            import codecs
            return codecs.decode(text, "rot_13")
        except Exception:
            return ""

    def _decode_base64_email(self, encoded: str) -> str:
        """Decode Base64 encoded email."""
        try:
            import base64
            decoded = base64.b64decode(encoded).decode("utf-8", errors="ignore")
            if "@" in decoded:
                return decoded
        except Exception:
            pass
        return ""

    def _decode_common_obfuscation(self, text: str) -> str:
        """Decode [at], [dot], HTML entities, ROT13, and other common obfuscations."""
        import html as html_mod
        decoded = text

        decoded = html_mod.unescape(decoded)
        decoded = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), decoded)
        decoded = re.sub(r"&#x([0-9a-fA-F]+);", lambda m: chr(int(m.group(1), 16)), decoded)

        try:
            import codecs
            rot13 = codecs.decode(text, "rot_13")
            if "@" in rot13:
                decoded += " " + rot13
        except Exception:
            pass

        decoded = re.sub(r"\s*\[at\]\s*", "@", decoded, flags=re.I)
        decoded = re.sub(r"\s*\[dot\]\s*", ".", decoded, flags=re.I)
        decoded = re.sub(r"\s*\(at\)\s*", "@", decoded, flags=re.I)
        decoded = re.sub(r"\s*\(dot\)\s*", ".", decoded, flags=re.I)
        decoded = re.sub(r"\s*\{at\}\s*", "@", decoded, flags=re.I)
        decoded = re.sub(r"\s*\{dot\}\s*", ".", decoded, flags=re.I)
        decoded = re.sub(r"\s*<at>\s*", "@", decoded, flags=re.I)
        decoded = re.sub(r"\s*<dot>\s*", ".", decoded, flags=re.I)
        decoded = re.sub(r"\s*AT\s*", "@", decoded)
        decoded = re.sub(r"\s*DOT\s*", ".", decoded)

        return decoded

    VALID_TLDS = {
        "com", "net", "org", "edu", "gov", "mil", "int",
        "co", "io", "me", "us", "uk", "ca", "au", "de", "fr", "es", "it",
        "nl", "pl", "pt", "ru", "tr", "jp", "cn", "kr", "br", "mx", "ar",
        "at", "ch", "be", "se", "no", "dk", "fi", "cz", "sk", "hu", "ro",
        "bg", "hr", "si", "ee", "lv", "lt", "ie", "gr", "cy", "mt",
        "lu", "sa", "ae", "eg", "ma", "za", "ng", "ke", "in", "pk", "bd",
        "sg", "my", "th", "vn", "ph", "id", "tw", "hk", "nz", "il",
        "info", "biz", "name", "pro", "mobi", "travel", "museum", "aero",
        "coop", "jobs", "cat", "tel", "asia", "xxx", "post",
        "nyc", "tokyo", "berlin", "paris", "amsterdam", "london",
        "vegas", "miami", "sydney", "melbourne", "toronto", "vancouver",
        "page", "dev", "app", "tech", "online", "site", "website",
        "store", "shop", "space", "one", "club",
    }

    def _is_valid_email(self, email: str) -> bool:
        """Validate email address."""
        if not email or len(email) < 5 or len(email) > 100:
            return False
        if not re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email):
            return False
        domain = email.split("@")[-1].lower()
        tld = domain.rsplit(".", 1)[-1] if "." in domain else ""
        if tld in self.FAKE_TLDS:
            return False
        if tld not in self.VALID_TLDS:
            return False
        if domain.startswith("www."):
            return False
        for pattern in self.IGNORE_EMAILS:
            if re.search(pattern, email, re.I):
                return False
        try:
            import codecs
            decoded = codecs.decode(email, "rot_13")
            if decoded != email:
                junk_domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "domain.com", "example.com", "test.com"]
                local = decoded.split("@")[0].lower() if "@" in decoded else ""
                domain = decoded.split("@")[1].lower() if "@" in decoded else ""
                if domain in junk_domains:
                    return False
                junk_locals = ["user", "test", "admin", "info", "contact", "support", "hello", "benutzer", "usuario", "utilisateur", "utente", "nome", "prenom", "votre", "email"]
                if local in junk_locals:
                    return False
        except Exception:
            pass
        return True

    def classify_business(self, text: str) -> str:
        """Classify business type from website content text."""
        if not text:
            return "unknown"
        text_lower = text.lower()
        scores = {}
        for btype, keywords in self.BUSINESS_TYPES.items():
            if not keywords:
                continue
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[btype] = score
        if scores:
            best = max(scores, key=scores.get)
            if scores[best] >= 2:
                return best
        return "unknown"

    def _is_valid_phone(self, phone: str) -> bool:
        """Validate phone number."""
        digits = re.sub(r"\D", "", phone)
        return 7 <= len(digits) <= 15

    def _filter_emails(self, emails: Set[str]) -> List[str]:
        """Sort emails by priority."""
        priority = ["info", "contact", "hello", "support", "sales", "office", "reservation", "booking"]
        personal = ["admin", "webmaster"]

        scored = []
        for email in emails:
            prefix = email.split("@")[0].lower()
            score = 5
            if prefix in priority:
                score = 10
            elif any(p in prefix for p in priority):
                score = 8
            elif prefix in personal:
                score = 2
            scored.append((score, email))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [email for _, email in scored]

    def _extract_emails_from_json(self, data) -> Set[str]:
        """Extract emails from JSON-LD data."""
        emails = set()
        if isinstance(data, dict):
            for key in ("email", "contactEmail"):
                if key in data:
                    val = data[key]
                    if isinstance(val, str) and self._is_valid_email(val):
                        emails.add(val.lower())
            for val in data.values():
                if isinstance(val, (dict, list)):
                    emails.update(self._extract_emails_from_json(val))
        elif isinstance(data, list):
            for item in data:
                emails.update(self._extract_emails_from_json(item))
        return emails

    def _extract_phones_from_json(self, data, phones: set):
        """Extract phones from JSON-LD data."""
        if isinstance(data, dict):
            for key in ("telephone", "phone", "contactPhone"):
                if key in data:
                    val = data[key]
                    if isinstance(val, str) and self._is_valid_phone(val):
                        phones.add(val)
            for val in data.values():
                if isinstance(val, (dict, list)):
                    self._extract_phones_from_json(val, phones)
        elif isinstance(data, list):
            for item in data:
                self._extract_phones_from_json(item, phones)

    def _extract_names_from_json(self, data) -> List[str]:
        """Extract names from JSON-LD data."""
        names = []
        if isinstance(data, dict):
            if data.get("@type") in ("Person", "Organization"):
                name = data.get("name", "")
                if name and len(name) > 2:
                    names.append(name)
            for val in data.values():
                if isinstance(val, (dict, list)):
                    names.extend(self._extract_names_from_json(val))
        elif isinstance(data, list):
            for item in data:
                names.extend(self._extract_names_from_json(item))
        return names

    def _extract_hours_from_json(self, data) -> str:
        """Extract hours from JSON-LD data."""
        if isinstance(data, dict):
            hours = data.get("openingHours") or data.get("openingHoursSpecification")
            if isinstance(hours, str):
                return hours
            if isinstance(hours, list):
                parts = []
                for spec in hours:
                    if isinstance(spec, dict):
                        day = spec.get("dayOfWeek", "")
                        opens = spec.get("opens", "")
                        closes = spec.get("closes", "")
                        if day and opens and closes:
                            parts.append(f"{day}: {opens}-{closes}")
                if parts:
                    return "; ".join(parts)
            for val in data.values():
                if isinstance(val, (dict, list)):
                    result = self._extract_hours_from_json(val)
                    if result:
                        return result
        elif isinstance(data, list):
            for item in data:
                result = self._extract_hours_from_json(item)
                if result:
                    return result
        return ""

    def _extract_address_from_json(self, data) -> str:
        """Extract address from JSON-LD data."""
        if isinstance(data, dict):
            addr = data.get("address")
            if isinstance(addr, dict):
                parts = [
                    addr.get("streetAddress", ""),
                    addr.get("addressLocality", ""),
                    addr.get("addressRegion", ""),
                    addr.get("postalCode", ""),
                    addr.get("addressCountry", ""),
                ]
                parts = [p for p in parts if p]
                if parts:
                    return ", ".join(parts)
            if isinstance(addr, str):
                return addr
            for val in data.values():
                if isinstance(val, (dict, list)):
                    result = self._extract_address_from_json(val)
                    if result:
                        return result
        elif isinstance(data, list):
            for item in data:
                result = self._extract_address_from_json(item)
                if result:
                    return result
        return ""

    def _extract_city_from_json(self, data) -> str:
        """Extract city from JSON-LD data."""
        if isinstance(data, dict):
            addr = data.get("address")
            if isinstance(addr, dict):
                city = addr.get("addressLocality", "")
                if city:
                    return city
            for val in data.values():
                if isinstance(val, (dict, list)):
                    result = self._extract_city_from_json(val)
                    if result:
                        return result
        elif isinstance(data, list):
            for item in data:
                result = self._extract_city_from_json(item)
                if result:
                    return result
        return ""

    def _extract_description_from_json(self, data) -> str:
        """Extract description from JSON-LD data."""
        if isinstance(data, dict):
            desc = data.get("description", "")
            if desc:
                return desc
            for val in data.values():
                if isinstance(val, (dict, list)):
                    result = self._extract_description_from_json(val)
                    if result:
                        return result
        elif isinstance(data, list):
            for item in data:
                result = self._extract_description_from_json(item)
                if result:
                    return result
        return ""

    def _extract_rating_from_json(self, data) -> str:
        """Extract rating from JSON-LD data."""
        if isinstance(data, dict):
            agg = data.get("aggregateRating")
            if isinstance(agg, dict):
                rating = agg.get("ratingValue", "")
                count = agg.get("ratingCount", agg.get("reviewCount", ""))
                if rating:
                    return f"{rating}/5 ({count} reviews)" if count else f"{rating}/5"
            for val in data.values():
                if isinstance(val, (dict, list)):
                    result = self._extract_rating_from_json(val)
                    if result:
                        return result
        elif isinstance(data, list):
            for item in data:
                result = self._extract_rating_from_json(item)
                if result:
                    return result
        return ""

    def _extract_emails_from_js_files(self, base_url: str) -> Set[str]:
        """Scan all linked JavaScript files for email addresses."""
        emails = set()
        try:
            html = self.crawler.fetch(base_url, use_referrer=True)
            if not html:
                return emails
            soup = BeautifulSoup(html, "lxml")
            js_urls = set()
            for script in soup.find_all("script", src=True):
                src = script["src"]
                if not src.startswith("http"):
                    src = urljoin(base_url, src)
                if src.startswith(base_url.rstrip("/")):
                    js_urls.add(src)
            for js_url in list(js_urls)[:20]:
                try:
                    js_html = self.crawler.fetch(js_url, use_referrer=True)
                    if not js_html:
                        continue
                    for pattern in self.EMAIL_REGEXES:
                        matches = re.findall(pattern, js_html, re.I)
                        for match in matches:
                            email = match.strip().lower().strip("\"'")
                            if self._is_valid_email(email):
                                emails.add(email)
                    for match in re.findall(r"String\.fromCharCode\((\d+(?:,\d+)+)\)", js_html):
                        decoded = self._decode_string_fromcharcode(match)
                        if "@" in decoded:
                            found = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", decoded)
                            for email in found:
                                if self._is_valid_email(email):
                                    emails.add(email.lower())
                except Exception:
                    continue
        except Exception:
            pass
        return emails

    def _extract_emails_from_cms_paths(self, base_url: str) -> Set[str]:
        """Check common WordPress/CMS paths for emails."""
        emails = set()
        cms_paths = [
            "/wp-json/wp/v2/users",
            "/wp-json/wp/v2/settings",
            "/wp-json/wp/v2/pages?per_page=100",
            "/xmlrpc.php",
            "/wp-login.php",
            "/wp-admin/admin-ajax.php",
            "/feed/",
            "/comments/feed/",
            "/?rest_route=/wp/v2/users",
            "/graphql",
            "/api/users",
            "/api/contact",
            "/api/settings",
            "/.well-known/security.txt",
            "/security.txt",
        ]
        for path in cms_paths:
            try:
                url = base_url.rstrip("/") + path
                html = self.crawler.fetch(url, use_referrer=False)
                if html:
                    found = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", html)
                    for email in found:
                        if self._is_valid_email(email):
                            emails.add(email.lower())
            except Exception:
                continue
        return emails

    def _extract_emails_from_pdfs(self, base_url: str) -> Set[str]:
        """Find PDF links and extract emails from them."""
        emails = set()
        try:
            html = self.crawler.fetch(base_url, use_referrer=True)
            if not html:
                return emails
            soup = BeautifulSoup(html, "lxml")
            pdf_urls = set()
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                if href.lower().endswith(".pdf"):
                    if not href.startswith("http"):
                        href = urljoin(base_url, href)
                    pdf_urls.add(href)
            for pdf_url in list(pdf_urls)[:5]:
                try:
                    pdf_html = self.crawler.fetch(pdf_url, use_referrer=True)
                    if pdf_html:
                        found = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", pdf_html)
                        for email in found:
                            if self._is_valid_email(email):
                                emails.add(email.lower())
                except Exception:
                    continue
        except Exception:
            pass
        return emails

    def _lookup_mx_records(self, domain: str) -> Set[str]:
        """Lookup DNS MX records to discover email domain."""
        emails = set()
        try:
            import socket
            mx_records = socket.getaddrinfo(f"mail.{domain}", 25, socket.AF_INET, socket.SOCK_STREAM)
            for info in mx_records:
                emails.add(f"info@{domain}")
        except Exception:
            pass
        try:
            import subprocess
            result = subprocess.run(
                ["nslookup", "-type=MX", domain],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "mail exchanger" in line.lower():
                        parts = line.split("=")
                        if len(parts) > 2:
                            mx_domain = parts[2].strip().rstrip(".").strip()
                            # Skip known mail provider MX records
                            skip_mx = ["google.com", "outlook.com", "microsoft.com",
                                       "protonmail.ch", "zoho.com", "yandex.net",
                                       "amazonaws.com", "qq.com", "163.com"]
                            if mx_domain and "." in mx_domain and not any(x in mx_domain for x in skip_mx):
                                emails.add(f"info@{mx_domain}")
                                emails.add(f"contact@{mx_domain}")
        except Exception:
            pass
        return emails

    def _fetch_wayback_version(self, url: str) -> Optional[str]:
        """Fetch archived version from Wayback Machine."""
        try:
            api_url = f"https://web.archive.org/web/2024/{url}"
            html = self.crawler.fetch(api_url, use_referrer=False)
            if html and len(html) > 500:
                return html
        except Exception:
            pass
        return None

    def _extract_emails_from_data_attributes(self, soup: BeautifulSoup) -> Set[str]:
        """Extract emails from all data-* attributes."""
        emails = set()
        for tag in soup.find_all(True):
            for attr, value in tag.attrs.items():
                if attr.startswith("data-") and isinstance(value, str) and "@" in value:
                    found = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", value)
                    for email in found:
                        if self._is_valid_email(email):
                            emails.add(email.lower())
        return emails

    def _extract_whatsapp_from_buttons(self, html: str) -> str:
        """Extract WhatsApp from floating buttons and widgets."""
        patterns = [
            r"wa\.me/(\d+)",
            r"api\.whatsapp\.com/send\?.*?phone=(\d+)",
            r"whatsapp.*?(\d{8,15})",
            r"chat\.whatsapp\.com/([a-zA-Z0-9]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.I)
            if match:
                return match.group(1)
        return ""

    def _extract_emails_from_link_titles(self, soup: BeautifulSoup) -> Set[str]:
        """Extract emails from link titles and image alt text."""
        emails = set()
        for tag in soup.find_all(["a", "img"]):
            for attr in ["title", "alt", "aria-label", "data-original-title"]:
                val = tag.get(attr, "")
                if "@" in val:
                    found = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", val)
                    for email in found:
                        if self._is_valid_email(email):
                            emails.add(email.lower())
        return emails

    def _extract_emails_from_http_headers(self, url: str) -> Set[str]:
        """Extract emails from HTTP response headers."""
        emails = set()
        try:
            from urllib.request import Request, urlopen
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            resp = urlopen(req, timeout=5)
            for header in ["X-Email", "X-Contact-Email", "X-Mailer-Email", "X-Abuse-Contact"]:
                val = resp.headers.get(header, "")
                if "@" in val:
                    found = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", val)
                    for email in found:
                        if self._is_valid_email(email):
                            emails.add(email.lower())
        except Exception:
            pass
        return emails

    def _guess_email_patterns(self, domain: str) -> Set[str]:
        """Try common email patterns by checking MX records exist."""
        emails = set()
        try:
            import dns.resolver
            mx_records = dns.resolver.resolve(domain, "MX")
            if not mx_records:
                return emails
        except Exception:
            return emails

        prefixes = ["info", "contact", "hello", "office", "admin", "support",
                     "reservations", "booking", "reservation", "sales", "team",
                     "mail", "welcome", "service", "help", "general",
                     "press", "media", "careers", "jobs", "hr", "legal",
                     "billing", "accounts", "feedback", "enquiries"]
        for prefix in prefixes:
            emails.add(f"{prefix}@{domain}")
        return emails

    def _verify_email_smtp(self, email: str) -> bool:
        """Verify email exists via SMTP RCPT TO check."""
        try:
            import socket
            import smtplib
            domain = email.split("@")[1]
            mx_records = []
            try:
                result = __import__("subprocess").run(
                    ["nslookup", "-type=MX", domain],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.split("\n"):
                    if "mail exchanger" in line.lower():
                        parts = line.split("=")
                        if len(parts) > 2:
                            mx_domain = parts[2].strip().rstrip(".").strip()
                            if mx_domain:
                                mx_records.append(mx_domain)
            except Exception:
                pass
            if not mx_records:
                return False
            mx_records.sort()
            for port in [25, 587, 465]:
                try:
                    smtp = smtplib.SMTP(timeout=5)
                    smtp.connect(mx_records[0], port)
                    smtp.helo("test.com")
                    smtp.mail("test@test.com")
                    code, _ = smtp.rcpt(email)
                    smtp.quit()
                    return code == 250
                except Exception:
                    continue
            return False
        except Exception:
            return False

    def _extract_emails_from_wordpress_api(self, base_url: str) -> Set[str]:
        """Check WordPress REST API for author emails."""
        emails = set()
        try:
            api_url = base_url.rstrip("/") + "/wp-json/wp/v2/users"
            html = self.crawler.fetch(api_url, use_referrer=False)
            if html:
                found = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", html)
                for email in found:
                    if self._is_valid_email(email):
                        emails.add(email.lower())
        except Exception:
            pass
        return emails

    def _search_bing_for_emails(self, domain: str) -> Set[str]:
        """Search Bing for emails on a specific domain."""
        emails = set()
        try:
            from lead_generator.scrapers.crawler import AntiBypassCrawler
            crawler = AntiBypassCrawler(
                timeout=8, max_retries=1, fast_mode=True,
                proxy_server=self.config.proxy_server,
                proxy_list_file=self.config.proxy_list_file,
                use_free_proxies=False,
            )
            from urllib.parse import quote_plus
            query = f"site:{domain} email contact"
            url = f"https://www.bing.com/search?q={quote_plus(query)}&count=10"
            html = crawler.fetch(url, use_referrer=False, accept_gzip=False)
            if html:
                found = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", html)
                for email in found:
                    if self._is_valid_email(email):
                        emails.add(email.lower())
        except Exception:
            pass
        return emails

    def _search_google_cache_for_emails(self, domain: str) -> Set[str]:
        """Search Google cache for emails on a domain."""
        emails = set()
        try:
            from lead_generator.scrapers.crawler import AntiBypassCrawler
            crawler = AntiBypassCrawler(
                timeout=8, max_retries=1, fast_mode=True,
                proxy_server=self.config.proxy_server,
                proxy_list_file=self.config.proxy_list_file,
                use_free_proxies=False,
            )
            from urllib.parse import quote_plus
            query = f"cache:{domain} email"
            url = f"https://webcache.googleusercontent.com/search?q={quote_plus(query)}"
            html = crawler.fetch(url, use_referrer=False, accept_gzip=False)
            if html:
                found = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", html)
                for email in found:
                    if self._is_valid_email(email):
                        emails.add(email.lower())
        except Exception:
            pass
        return emails

    def _search_social_media_for_emails(self, domain: str, website_url: str) -> Set[str]:
        """Search social media pages for email addresses linked to this domain."""
        emails = set()
        try:
            from lead_generator.scrapers.crawler import AntiBypassCrawler
            crawler = AntiBypassCrawler(
                timeout=8, max_retries=1, fast_mode=True,
                proxy_server=self.config.proxy_server,
                proxy_list_file=self.config.proxy_list_file,
                use_free_proxies=False,
            )
            from urllib.parse import quote_plus

            social_platforms = [
                f"facebook.com",
                f"linkedin.com/company",
                f"instagram.com",
                f"twitter.com",
                f"x.com",
                f"tiktok.com",
                f"youtube.com",
                f"pinterest.com",
            ]

            company_name = domain.split(".")[0].replace("-", " ").replace("_", " ")

            for platform in social_platforms:
                try:
                    query = f"site:{platform} {company_name} email contact"
                    url = f"https://www.bing.com/search?q={quote_plus(query)}&count=5"
                    html = crawler.fetch(url, use_referrer=False, accept_gzip=False)
                    if not html:
                        continue

                    soup = BeautifulSoup(html, "lxml")
                    for h2 in soup.find_all("h2"):
                        a = h2.find("a", href=True)
                        if not a:
                            continue
                        link = a["href"]
                        if platform.split(".")[0] not in link.lower():
                            continue

                        social_html = crawler.fetch(link, use_referrer=True)
                        if social_html:
                            found = re.findall(
                                r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
                                social_html
                            )
                            for email in found:
                                if self._is_valid_email(email):
                                    emails.add(email.lower())
                        break
                except Exception:
                    continue
        except Exception:
            pass
        return emails
