"""
Email Dork Finder v5 - FREE PROXY BYPASS
========================================
Fresh free proxies to bypass network blocks.
No account, no API, no installation.

Created by: Mustapha Elasri
"""

import sys
import os
import re
import time
import random
import base64
import requests
from typing import List, Dict, Optional
from urllib.parse import quote_plus, urlparse, parse_qs

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bs4 import BeautifulSoup


EMAIL_DOMAINS = ["@gmail.com", "@hotmail.com", "@yahoo.com", "@outlook.com"]

FINGERPRINTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

PROXY_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/https.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/https/https.txt",
    "https://raw.githubusercontent.com/ErcinDedeworken/proxies/main/http_proxies.txt",
    "https://raw.githubusercontent.com/Zaeem20/PROXY-List/main/http_proxies.txt",
]


class FreeProxyManager:
    def __init__(self):
        self._proxies = []
        self._bad = set()
        self._index = 0
        self._fetch()

    def _fetch(self):
        print("    Fetching fresh proxies...")
        for src in PROXY_SOURCES:
            try:
                r = requests.get(src, timeout=8)
                if r.status_code == 200:
                    for line in r.text.strip().splitlines():
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "://" not in line:
                            line = "http://" + line
                        if line not in self._bad:
                            self._proxies.append(line)
            except Exception:
                continue
        random.shuffle(self._proxies)
        print(f"    Got {len(self._proxies)} proxies")

    def get(self) -> Optional[str]:
        for _ in range(len(self._proxies)):
            p = self._proxies[self._index % len(self._proxies)]
            self._index += 1
            if p not in self._bad:
                return p
        return None

    def mark_bad(self, proxy):
        self._bad.add(proxy)

    def test(self, proxy, timeout=4) -> bool:
        try:
            r = requests.get("https://httpbin.org/ip", proxies={"http": proxy, "https": proxy}, timeout=timeout)
            return r.status_code == 200
        except Exception:
            return False


def _headers():
    return {
        "User-Agent": random.choice(FINGERPRINTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


def _delay(a=0.3, b=0.7):
    time.sleep(random.uniform(a, b))


def find_emails_by_dorking(query, location, max_results=50, proxies=None):
    print(f"  Searching for emails: '{query}' in '{location}'...")
    all_emails = []
    seen = set()

    print(f"\n  [Method 1] Search via Google Translate proxy...")
    for domain in EMAIL_DOMAINS:
        if len(all_emails) >= max_results:
            break
        sq = f"{query} {location} {domain}"
        print(f"  Searching: {sq}")

        for engine in ["translate_bing", "translate_google", "brave", "ecosia", "startpage", "yandex", "duckduckgo"]:
            try:
                results = _search_engine(engine, sq, proxies=proxies)
                if results:
                    print(f"    {engine}: {len(results)} results")
                for r in results:
                    e = r.get("email", "").lower()
                    if e and e not in seen and _valid_email(e):
                        seen.add(e)
                        all_emails.append(r)
            except Exception:
                print(f"    {engine}: failed")
            _delay(0.3, 0.6)
        _delay(0.5, 1.0)

    if len(all_emails) < max_results:
        print(f"\n  [Method 1b] Industry-specific dork queries...")
        dork_templates = [
            '"{query}" "{location}" "email" "@gmail.com"',
            '"{query}" "{location}" "contact@" OR "info@"',
            'inurl:contact "{query}" "{location}" email',
            'intitle:"contact us" "{query}" "{location}" email',
        ]
        for template in dork_templates:
            if len(all_emails) >= max_results:
                break
            dork = template.format(query=query, location=location)
            for engine in ["translate_bing", "brave", "duckduckgo"]:
                try:
                    res = _search_engine(engine, dork, proxies=proxies)
                    for r in res:
                        e = r.get("email", "").lower()
                        if e and e not in seen and _valid_email(e):
                            seen.add(e)
                            all_emails.append(r)
                except Exception:
                    pass

    if len(all_emails) < max_results:
        print(f"\n  [Method 2] Crawling business websites...")
        try:
            wmails = _crawl(query, location, max_results - len(all_emails))
            for item in wmails:
                e = item.get("email", "").lower()
                if e and e not in seen and _valid_email(e):
                    seen.add(e)
                    all_emails.append(item)
        except Exception as ex:
            print(f"    Crawl failed: {ex}")

    print(f"  Found {len(all_emails)} unique emails")
    return all_emails


def _search_engine(engine, query, proxies=None):
    """Route to the correct search engine."""
    if engine == "translate_bing":
        return _translate_proxy("bing", query, proxies=proxies)
    elif engine == "translate_google":
        return _translate_proxy("google", query, proxies=proxies)
    elif engine == "brave":
        return _brave_search(query, proxies=proxies)
    elif engine == "ecosia":
        return _ecosia_search(query, proxies=proxies)
    elif engine == "startpage":
        return _startpage_search(query, proxies=proxies)
    elif engine == "yandex":
        return _yandex(query, proxies=proxies)
    elif engine == "duckduckgo":
        return _duckduckgo(query, proxies=proxies)
    return []


def _translate_proxy(search_engine, query, proxies=None):
    """Use Google Translate as a proxy to access search engines."""
    results = []
    
    if search_engine == "bing":
        original_url = f"https://www.bing.com/search?q={quote_plus(query)}&count=20"
    else:
        original_url = f"https://www.google.com/search?q={quote_plus(query)}&num=20"

    translate_url = f"https://translate.google.com/translate?sl=fr&tl=en&u={quote_plus(original_url)}"

    try:
        h = _headers()
        h["Referer"] = "https://translate.google.com/"
        r = requests.get(translate_url, headers=h, proxies=proxies, timeout=15, allow_redirects=True)
        
        if r.status_code != 200:
            return results

        html = r.text
        if len(html) < 500:
            return results

        soup = BeautifulSoup(html, "lxml")

        for item in soup.select("li.b_algo, div.g"):
            title_el = item.select_one("h2 a, h3")
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            link_el = item.select_one("a[href]")
            url_str = link_el.get("href", "") if link_el else ""

            snippet_el = item.select_one(".b_caption p, div.VwiC3b")
            snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""

            full_text = f"{title} {snippet}"
            for e in _extract_emails(full_text):
                results.append({
                    "name": _clean(title),
                    "email": e,
                    "phone": "",
                    "website": _clean_url(url_str),
                    "source": "dork",
                    "query": query,
                })

        if not results:
            all_text = soup.get_text(" ", strip=True)
            for e in _extract_emails(all_text):
                results.append({"name": "", "email": e, "phone": "", "website": "", "source": "dork", "query": query})

    except Exception:
        pass

    return results


def _brave_search(query, proxies=None):
    """Search Brave search engine."""
    results = []
    url = f"https://search.brave.com/search?q={quote_plus(query)}"

    try:
        h = _headers()
        h["Referer"] = "https://search.brave.com/"
        r = requests.get(url, headers=h, proxies=proxies, timeout=10, allow_redirects=True)
        
        if r.status_code != 200:
            return results

        soup = BeautifulSoup(r.text, "lxml")

        for item in soup.select("div.snippet"):
            title_el = item.select_one("a.snippet-title")
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            url_str = title_el.get("href", "")

            snippet_el = item.select_one("div.snippet-description")
            snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""

            full_text = f"{title} {snippet}"
            for e in _extract_emails(full_text):
                results.append({
                    "name": _clean(title),
                    "email": e,
                    "phone": "",
                    "website": _clean_url(url_str),
                    "source": "dork",
                    "query": query,
                })

    except Exception:
        pass

    return results


def _ecosia_search(query, proxies=None):
    """Search Ecosia search engine."""
    results = []
    url = f"https://www.ecosia.org/search?q={quote_plus(query)}"

    try:
        h = _headers()
        h["Referer"] = "https://www.ecosia.org/"
        r = requests.get(url, headers=h, proxies=proxies, timeout=10, allow_redirects=True)
        
        if r.status_code != 200:
            return results

        soup = BeautifulSoup(r.text, "lxml")

        for item in soup.select("div.result"):
            title_el = item.select_one("a.result__title")
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            url_str = title_el.get("href", "")

            snippet_el = item.select_one("a.result__snippet")
            snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""

            full_text = f"{title} {snippet}"
            for e in _extract_emails(full_text):
                results.append({
                    "name": _clean(title),
                    "email": e,
                    "phone": "",
                    "website": _clean_url(url_str),
                    "source": "dork",
                    "query": query,
                })

    except Exception:
        pass

    return results


def _startpage_search(query, proxies=None):
    """Search Startpage (privacy search engine)."""
    results = []
    url = f"https://www.startpage.com/sp/search?q={quote_plus(query)}"

    try:
        h = _headers()
        h["Referer"] = "https://www.startpage.com/"
        r = requests.get(url, headers=h, proxies=proxies, timeout=10, allow_redirects=True)
        
        if r.status_code != 200:
            return results

        soup = BeautifulSoup(r.text, "lxml")

        for item in soup.select("div.result"):
            title_el = item.select_one("h3 a, a.result-link")
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            url_str = title_el.get("href", "")

            snippet_el = item.select_one("p.result-text")
            snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""

            full_text = f"{title} {snippet}"
            for e in _extract_emails(full_text):
                results.append({
                    "name": _clean(title),
                    "email": e,
                    "phone": "",
                    "website": _clean_url(url_str),
                    "source": "dork",
                    "query": query,
                })

    except Exception:
        pass

    return results


def _duckduckgo(query, proxies=None):
    """Search DuckDuckGo HTML version."""
    results = []
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        h = _headers()
        r = requests.get(url, headers=h, proxies=proxies, timeout=10, allow_redirects=True)
        if r.status_code != 200:
            return results
        soup = BeautifulSoup(r.text, "lxml")
        for item in soup.select(".result"):
            title_el = item.select_one(".result__title a, .result__a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            url_str = title_el.get("href", "")
            snippet_el = item.select_one(".result__snippet")
            snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""
            ft = f"{title} {snippet}"
            for e in _extract_emails(ft):
                results.append({"name": _clean(title), "email": e, "phone": "",
                               "website": _clean_url(url_str), "source": "dork", "query": query})
    except Exception:
        pass
    return results


def _google(query, proxies=None):
    results = []
    url = f"https://www.google.com/search?q={quote_plus(query)}&num=20&hl=en&gl=us"
    try:
        h = _headers()
        h["Referer"] = "https://www.google.com/"
        r = requests.get(url, headers=h, proxies=proxies, timeout=10, allow_redirects=True)
        if r.status_code != 200:
            return results
        if "captcha" in r.text.lower() or "unusual traffic" in r.text.lower():
            return results
        soup = BeautifulSoup(r.text, "lxml")
        for item in soup.select("div.g"):
            te = item.select_one("h3")
            if not te:
                continue
            title = te.get_text(strip=True)
            la = item.select_one("a[href]")
            u = la["href"] if la else ""
            sn = item.select_one("div.VwiC3b, span.aCOpRe")
            s = sn.get_text(" ", strip=True) if sn else ""
            ft = f"{title} {s}"
            for e in _extract_emails(ft):
                results.append({"name": _clean(title), "email": e, "phone": "", "website": _clean_url(u), "source": "dork", "query": query})
    except Exception:
        pass
    return results


def _yandex(query, proxies=None):
    results = []
    url = f"https://yandex.com/search/?text={quote_plus(query)}&lr=84"
    try:
        h = _headers()
        h["Referer"] = "https://yandex.com/"
        r = requests.get(url, headers=h, proxies=proxies, timeout=10, allow_redirects=True)
        if r.status_code != 200:
            return results
        soup = BeautifulSoup(r.text, "lxml")
        for item in soup.select("div.Organic, li.serp-item"):
            ta = item.select_one("h2 a, a.OrganicTitle")
            if not ta:
                continue
            title = ta.get_text(strip=True)
            u = ta.get("href", "")
            sn = item.select_one("div.OrganicText, span.OrganicTextContent")
            s = sn.get_text(" ", strip=True) if sn else ""
            ft = f"{title} {s}"
            for e in _extract_emails(ft):
                results.append({"name": _clean(title), "email": e, "phone": "", "website": _clean_url(u), "source": "dork", "query": query})
    except Exception:
        pass
    return results


def _crawl(query, location, max_emails):
    from client_finder.scraper import scrape_businesses
    from client_finder.emails import find_emails_batch
    print("    Finding businesses...")
    biz = scrape_businesses(query, location, 30)
    ww = [b for b in biz if b.get("website")]
    print(f"    {len(ww)} have websites")
    if not ww:
        return []
    print(f"    Crawling websites...")
    en = find_emails_batch(ww, 4)
    results = []
    for b in en:
        if b.get("email"):
            results.append({"name": b.get("name", ""), "email": b["email"], "phone": b.get("phone", ""), "website": b.get("website", ""), "source": "website_crawl", "query": f"{query} {location}"})
            print(f"    Found: {b['email']}")
            if len(results) >= max_emails:
                break
    return results


def _extract_emails(text):
    raw = re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', text)
    return list(set(e.lower() for e in raw if _valid_email(e)))


def _valid_email(email):
    if not re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', email):
        return False
    local = email.split("@")[0].lower()
    domain = email.split("@")[1].lower() if "@" in email else ""
    tld = domain.rsplit(".", 1)[-1] if "." in domain else ""
    if tld in FAKE_TLDS:
        return False
    if tld not in VALID_TLDS:
        return False
    for j in ["noreply","no-reply","donotreply","mailer-daemon","postmaster","webmaster","abuse","spam","unsubscribe","example","test","root","nobody"]:
        if local == j or local.startswith(j):
            return False
    bad_domains = ["example.com","test.com","localhost","sentry.io","wixpress.com","googleapis.com","w3.org","schema.org","google.com","bing.com","yahoo.com","duckduckgo.com","facebook.com","twitter.com","instagram.com","linkedin.com","youtube.com","github.com","antispamcloud.com","rzone.de","wixsite.com","wix.com","cloudflare.com","cloudfront.net","amazonaws.com","herokuapp.com","vercel.app","netlify.app","mailerlite.com","sendgrid.net","mailchimp.com","bounces.","bounce.","returnpath.net","doubleclick.net","googlesyndication.com","archive.org","secureserver.net"]
    for d in bad_domains:
        if domain.endswith(d):
            return False
    if "antispam" in domain or "antispamcloud" in domain or "smtpin" in domain or "filter" in domain:
        return False
    if ".." in email or ".correo" in email:
        return False
    if local in ["mediarelations", "press", "media"]:
        return False
    if domain.startswith("-"):
        return False
    placeholders = ["nom","name","prenom","votre","email","user","fname","lname","first.last","johndoe","janedoe","doe","changeme","replace","insert","your_email","your_name","me","someone","anyone","hi","hey","admin","placeholder","sample","demo"]
    for p in placeholders:
        if local == p or local.startswith(p + ".") or local.startswith(p + "_") or local.startswith(p + "-"):
            return False
    if local in ["your", "example", "test"] or local.startswith("your@") or local.startswith("example@"):
        return False
    if "email" in local and ("example" in domain or "domain" in domain or "your" in domain):
        return False
    if domain.startswith("www."):
        return False
    good_prefixes = ["info","contact","hello","support","sales","office","admin","booking","reservation","enquiries"]
    for g in good_prefixes:
        if len(local) > len(g) and local.endswith(g):
            prefix_len = len(local) - len(g)
            if prefix_len <= 2:
                return False
    if len(local) < 2:
        return False
    return True


FAKE_TLDS = {
    "wct", "xyz", "tk", "ml", "ga", "cf", "gq", "top", "buzz",
    "click", "link", "work", "day", "rock", "ninja",
    "guru", "expert", "today", "date", "chat", "fun", "surf",
    "men", "racing", "win", "bid", "loan", "review", "download",
    "party", "dating", "horse",
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


def _extract_phones(text):
    phones = []
    for m in re.findall(r'(?:\+\d{1,3}[\s\-]?)?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}', text):
        d = re.sub(r'\D', '', m)
        if 10 <= len(d) <= 15:
            phones.append(m.strip())
    return phones


def _decode_bing(url):
    if "bing.com/ck/a" in url:
        try:
            p = urlparse(url)
            params = parse_qs(p.query)
            for k in ["u","r"]:
                if k in params:
                    enc = params[k][0]
                    if enc.startswith("a1"):
                        enc = enc[2:]
                    dec = base64.b64decode(enc + "==").decode("utf-8", errors="replace")
                    if dec.startswith("http"):
                        return dec
        except Exception:
            pass
    return url


def _clean_url(url):
    if not url:
        return ""
    p = urlparse(url)
    d = p.netloc.lower()
    for s in ["bing.com","google.com","facebook.com","twitter.com","instagram.com","linkedin.com","youtube.com","wikipedia.org","yandex.com","yandex.ru"]:
        if s in d:
            return ""
    return f"{p.scheme}://{d}" if d else ""


def _clean(title):
    for sep in [" - "," | "," · "," — "," – "]:
        if sep in title:
            title = title.split(sep)[0]
    return title.strip()
