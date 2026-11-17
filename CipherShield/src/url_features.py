"""
CipherShield — URL Feature Extraction
Analyses URLs found inside SMS messages and returns a structured feature dict.

IMPORTANT: This module never visits or resolves URLs. All analysis is
purely syntactic/structural. It does NOT provide real-time threat intelligence.
"""
import re
import sys
import os
from urllib.parse import urlparse, unquote
import ipaddress

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TRUSTED_DOMAINS, URL_SHORTENERS

# ── regex helpers ─────────────────────────────────────────────────────────────

_URL_RE = re.compile(
    r"(?:https?://|www\.)"          # scheme or www
    r"[^\s\"'<>(){}|\\\[\]`^]+"     # URL body
    ,
    re.IGNORECASE,
)

_IPV4_RE = re.compile(
    r"^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$"
)


# ── individual URL inspectors ─────────────────────────────────────────────────

def _extract_hostname(url: str) -> str:
    """Return the lower-case hostname of a URL, or empty string on failure."""
    try:
        # prepend scheme so urlparse works for www. links
        if url.lower().startswith("www."):
            url = "http://" + url
        parsed = urlparse(url)
        host = parsed.hostname or ""
        return host.lower().strip()
    except Exception:
        return ""


def _is_ip_hostname(hostname: str) -> bool:
    """True if the hostname is an IPv4 address."""
    if not hostname:
        return False
    try:
        ipaddress.IPv4Address(hostname)
        return True
    except ValueError:
        return _IPV4_RE.match(hostname) is not None


def _is_shortener(hostname: str) -> bool:
    """True if the hostname belongs to a known URL shortener."""
    h = hostname.lstrip("www.")
    return h in URL_SHORTENERS or hostname in URL_SHORTENERS


def _has_suspicious_chars(url: str) -> bool:
    """
    True if the URL contains characters that are unusual / commonly abused.
    Currently checks for: @ in the authority portion.
    """
    try:
        parsed = urlparse(url if "://" in url else "http://" + url)
        # @ in netloc indicates credentials embedded in URL
        if "@" in parsed.netloc:
            return True
        # Multiple dots in a suspiciously long path
        if url.count(".") > 6:
            return True
        # Hex-encoded characters in hostname
        if re.search(r"%[0-9a-fA-F]{2}", parsed.netloc):
            return True
    except Exception:
        pass
    return False


def _is_trusted_domain(hostname: str) -> bool:
    """
    True when the hostname EXACTLY matches or is a direct subdomain of a
    trusted root domain. Simple substring matching is intentionally avoided
    to prevent 'amazon.com.evil.net' from matching 'amazon.com'.
    """
    if not hostname:
        return False
    clean = hostname.lstrip("www.")
    for trusted in TRUSTED_DOMAINS:
        # Direct match: hostname == trusted
        if clean == trusted:
            return True
        # Subdomain match: hostname ends with ".trusted"
        if clean.endswith("." + trusted):
            return True
    return False


def _has_suspicious_subdomain(hostname: str) -> bool:
    """
    Detect misleading subdomains, e.g. 'sbi.co.in.verify-kyc.com'
    where a trusted brand name appears as a subdomain of an untrusted host.
    """
    if not hostname:
        return False
    # If the domain is already trusted, it is not suspicious
    if _is_trusted_domain(hostname):
        return False
    # Check whether a trusted brand appears anywhere in the hostname
    # but the registrable domain is NOT trusted
    for trusted in TRUSTED_DOMAINS:
        # Strip the TLD from trusted root to get the brand keyword
        brand = trusted.split(".")[0]
        if brand in hostname and not _is_trusted_domain(hostname):
            return True
    return False


def _is_punycode(hostname: str) -> bool:
    """True if any label in the hostname uses ACE (xn--) punycode encoding."""
    return "xn--" in hostname.lower()


def _suspicious_scheme(url: str) -> bool:
    """True when the scheme is not http or https."""
    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        return scheme not in ("http", "https", "www", "")
    except Exception:
        return False


# ── main public function ──────────────────────────────────────────────────────

def extract_url_features(message: str) -> dict:
    """
    Extract URL-based features from an SMS message.

    Parameters
    ----------
    message : str
        Raw SMS text (before preprocessing).

    Returns
    -------
    dict
        Feature dictionary with the following keys:
        has_url, url_has_ip, url_shortener, url_suspicious_chars,
        url_length, trusted_domain, suspicious_subdomain,
        punycode_domain, multiple_urls, suspicious_url_scheme,
        url_count, detected_urls
    """
    if not isinstance(message, str):
        message = str(message) if message else ""

    urls = _URL_RE.findall(message)

    # Deduplicate while preserving order
    seen = set()
    unique_urls = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique_urls.append(u)

    has_url = len(unique_urls) > 0
    url_count = len(unique_urls)

    if not has_url:
        return {
            "has_url": False,
            "url_has_ip": False,
            "url_shortener": False,
            "url_suspicious_chars": False,
            "url_length": 0,
            "trusted_domain": False,
            "suspicious_subdomain": False,
            "punycode_domain": False,
            "multiple_urls": False,
            "suspicious_url_scheme": False,
            "url_count": 0,
            "detected_urls": [],
        }

    # Analyse each URL and aggregate
    ip_found = False
    shortener_found = False
    suspicious_chars_found = False
    max_url_length = 0
    trusted_found = False
    suspicious_subdomain_found = False
    punycode_found = False
    suspicious_scheme_found = False

    for url in unique_urls:
        hostname = _extract_hostname(url)

        if _is_ip_hostname(hostname):
            ip_found = True
        if _is_shortener(hostname):
            shortener_found = True
        if _has_suspicious_chars(url):
            suspicious_chars_found = True
        max_url_length = max(max_url_length, len(url))
        if _is_trusted_domain(hostname):
            trusted_found = True
        if _has_suspicious_subdomain(hostname):
            suspicious_subdomain_found = True
        if _is_punycode(hostname):
            punycode_found = True
        if _suspicious_scheme(url):
            suspicious_scheme_found = True

    return {
        "has_url": True,
        "url_has_ip": ip_found,
        "url_shortener": shortener_found,
        "url_suspicious_chars": suspicious_chars_found,
        "url_length": max_url_length,
        "trusted_domain": trusted_found,
        "suspicious_subdomain": suspicious_subdomain_found,
        "punycode_domain": punycode_found,
        "multiple_urls": url_count > 1,
        "suspicious_url_scheme": suspicious_scheme_found,
        "url_count": url_count,
        "detected_urls": unique_urls,
    }


def get_url_feature_vector(features: dict) -> list:
    """
    Convert the URL feature dict into a fixed-order numeric vector
    for use in model feature concatenation.

    Feature order MUST remain identical during training and inference.
    """
    return [
        int(features["has_url"]),
        int(features["url_has_ip"]),
        int(features["url_shortener"]),
        int(features["url_suspicious_chars"]),
        min(features["url_length"], 2000) / 2000.0,   # normalised 0-1
        int(features["trusted_domain"]),
        int(features["suspicious_subdomain"]),
        int(features["punycode_domain"]),
        int(features["multiple_urls"]),
        int(features["suspicious_url_scheme"]),
    ]


URL_FEATURE_NAMES = [
    "url_has_url",
    "url_has_ip",
    "url_shortener",
    "url_suspicious_chars",
    "url_length_norm",
    "url_trusted_domain",
    "url_suspicious_subdomain",
    "url_punycode_domain",
    "url_multiple_urls",
    "url_suspicious_scheme",
]
