"""
Lead Data Model
===============
Represents a business lead with all contact information.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
import re
import threading


@dataclass
class Lead:
    """A single business lead."""

    # Core info
    business_name: str = ""
    phone: str = ""
    email: str = ""
    all_emails: List[str] = field(default_factory=list)
    website: str = ""

    # Location
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    country: str = ""

    # Business details
    category: str = ""
    industry: str = ""
    rating: float = 0.0
    review_count: int = 0
    price_level: str = ""
    operating_hours: str = ""
    description: str = ""

    # Social media
    facebook: str = ""
    instagram: str = ""
    linkedin: str = ""
    twitter: str = ""
    youtube: str = ""
    tiktok: str = ""
    whatsapp: str = ""
    telegram: str = ""
    snapchat: str = ""
    pinterest: str = ""
    tripadvisor: str = ""

    # Decision maker
    owner_name: str = ""
    manager_name: str = ""

    # Additional business info
    rating_str: str = ""

    # Metadata
    source: str = "google_maps"
    google_maps_url: str = ""
    scraped_at: str = ""
    lead_score: int = 0
    data_completeness: float = 0.0

    def __post_init__(self):
        """Calculate lead score after initialization."""
        if not self.scraped_at:
            self.scraped_at = datetime.now().isoformat()
        self._calculate_score()

    def _calculate_score(self):
        """Calculate lead quality score (0-100)."""
        score = 0

        # Core contact info (65 points max)
        if self.business_name:
            score += 10
        if self.phone:
            score += 15
        if self.email:
            score += 25
        elif self.all_emails:
            score += 15
        if self.website:
            score += 15

        # Email + Phone combo bonus (most valuable for outreach)
        if self.phone and self.email:
            score += 10
        elif self.phone and self.all_emails:
            score += 5

        # Location info (15 points max)
        if self.address:
            score += 5
        if self.city:
            score += 5
        if self.country:
            score += 5

        # Business details (10 points max)
        if self.category:
            score += 3
        if self.rating > 0:
            score += 4
        elif self.rating_str:
            score += 2
        if self.operating_hours:
            score += 1
        if self.description:
            score += 2

        # Social media (10 points max)
        social_count = sum([
            bool(self.facebook),
            bool(self.instagram),
            bool(self.linkedin),
            bool(self.twitter),
            bool(self.youtube),
            bool(self.tiktok),
            bool(self.whatsapp),
            bool(self.telegram),
            bool(self.snapchat),
            bool(self.pinterest),
            bool(self.tripadvisor),
        ])
        score += min(social_count * 2, 10)

        # Decision maker (bonus)
        if self.owner_name or self.manager_name:
            score += 5

        self.lead_score = min(int(score), 100)

        # Calculate data completeness
        fields = [
            self.business_name, self.phone, self.email, self.website,
            self.address, self.city, self.state, self.category,
            self.country, self.facebook, self.instagram, self.owner_name,
        ]
        filled = sum(1 for f in fields if f)
        self.data_completeness = round((filled / len(fields)) * 100, 1)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export."""
        return asdict(self)

    def to_csv_row(self) -> Dict[str, str]:
        """Convert to flat CSV-compatible dictionary."""
        return {
            "Business Name": self.business_name,
            "Phone": self.phone,
            "Email": self.email,
            "All Emails": "; ".join(self.all_emails),
            "Website": self.website,
            "Address": self.address,
            "City": self.city,
            "State": self.state,
            "Zip Code": self.zip_code,
            "Country": self.country,
            "Category": self.category,
            "Industry": self.industry,
            "Rating": self.rating_str if self.rating_str else str(self.rating) if self.rating > 0 else "",
            "Review Count": str(self.review_count) if self.review_count > 0 else "",
            "Price Level": self.price_level,
            "Operating Hours": self.operating_hours,
            "Description": self.description,
            "Facebook": self.facebook,
            "Instagram": self.instagram,
            "LinkedIn": self.linkedin,
            "Twitter": self.twitter,
            "YouTube": self.youtube,
            "TikTok": self.tiktok,
            "WhatsApp": self.whatsapp,
            "Telegram": self.telegram,
            "Snapchat": self.snapchat,
            "Pinterest": self.pinterest,
            "TripAdvisor": self.tripadvisor,
            "Owner Name": self.owner_name,
            "Manager Name": self.manager_name,
            "Source": self.source,
            "Google Maps URL": self.google_maps_url,
            "Scraped At": self.scraped_at,
            "Lead Score": str(self.lead_score),
            "Data Completeness": f"{self.data_completeness}%",
        }

    @property
    def has_email(self) -> bool:
        return bool(self.email)

    @property
    def has_phone(self) -> bool:
        return bool(self.phone)

    @property
    def has_website(self) -> bool:
        return bool(self.website)

    @property
    def lead_tier(self) -> str:
        if self.lead_score >= 70:
            return "HOT"
        elif self.lead_score >= 40:
            return "WARM"
        return "COLD"


class LeadCollection:
    """Collection of leads with deduplication and filtering."""

    def __init__(self):
        self.leads: List[Lead] = []
        self._seen_phones: set = set()
        self._seen_websites: set = set()
        self._seen_emails: set = set()
        self._lock = threading.Lock()

    def add(self, lead: Lead) -> bool:
        """Add a lead if not duplicate. Returns True if added. Thread-safe."""
        with self._lock:
            # Deduplicate by phone
            if lead.phone and lead.phone in self._seen_phones:
                return False

            # Deduplicate by website
            if lead.website:
                normalized = self._normalize_url(lead.website)
                if normalized in self._seen_websites:
                    return False
                self._seen_websites.add(normalized)

            # Deduplicate by email
            if lead.email and lead.email.lower() in self._seen_emails:
                return False

            # Track
            if lead.phone:
                self._seen_phones.add(lead.phone)
            if lead.email:
                self._seen_emails.add(lead.email.lower())

            self.leads.append(lead)
            return True

    def add_batch(self, leads: List[Lead]) -> int:
        """Add multiple leads atomically. Returns count of newly added."""
        with self._lock:
            count = 0
            for lead in leads:
                if self._add_unsafe(lead):
                    count += 1
            return count

    def _add_unsafe(self, lead: Lead) -> bool:
        """Add a lead without acquiring the lock (caller must hold lock)."""
        if lead.phone and lead.phone in self._seen_phones:
            return False

        if lead.website:
            normalized = self._normalize_url(lead.website)
            if normalized in self._seen_websites:
                return False
            self._seen_websites.add(normalized)

        if lead.email and lead.email.lower() in self._seen_emails:
            return False

        if lead.phone:
            self._seen_phones.add(lead.phone)
        if lead.email:
            self._seen_emails.add(lead.email.lower())

        self.leads.append(lead)
        return True

    def filter_by_tier(self, tier: str) -> List[Lead]:
        """Filter leads by tier (HOT, WARM, COLD)."""
        return [l for l in self.leads if l.lead_tier == tier.upper()]

    def filter_with_email(self) -> List[Lead]:
        """Get leads that have email addresses."""
        return [l for l in self.leads if l.has_email]

    def filter_with_phone(self) -> List[Lead]:
        """Get leads that have phone numbers."""
        return [l for l in self.leads if l.has_phone]

    def sort_by_score(self, descending: bool = True) -> List[Lead]:
        """Sort leads by score."""
        return sorted(self.leads, key=lambda x: x.lead_score, reverse=descending)

    @property
    def stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        return {
            "total": len(self.leads),
            "with_email": len(self.filter_with_email()),
            "with_phone": len(self.filter_with_phone()),
            "hot_leads": len(self.filter_by_tier("HOT")),
            "warm_leads": len(self.filter_by_tier("WARM")),
            "cold_leads": len(self.filter_by_tier("COLD")),
            "avg_score": round(
                sum(l.lead_score for l in self.leads) / len(self.leads)
                if self.leads else 0, 1
            ),
        }

    @staticmethod
    def _normalize_url(url: str) -> str:
        """Normalize URL for deduplication."""
        url = url.lower().rstrip("/")
        url = re.sub(r"^https?://(www\.)?", "", url)
        return url

    def __len__(self):
        return len(self.leads)

    def __iter__(self):
        return iter(self.leads)

    def __getitem__(self, index):
        return self.leads[index]
