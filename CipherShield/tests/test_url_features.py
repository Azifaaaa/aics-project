"""
CipherShield — URL Feature Tests
Tests url_features.py in isolation from the ML model.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.url_features import extract_url_features, _is_trusted_domain, _has_suspicious_subdomain


class TestNoUrl:
    def test_no_url(self):
        f = extract_url_features("Hello, how are you today?")
        assert f["has_url"] is False
        assert f["url_count"] == 0
        assert f["url_has_ip"] is False


class TestBasicUrlDetection:
    def test_http_url(self):
        f = extract_url_features("Visit http://example.com for details.")
        assert f["has_url"] is True
        assert f["url_count"] == 1

    def test_https_url(self):
        f = extract_url_features("Go to https://example.com now.")
        assert f["has_url"] is True

    def test_www_url(self):
        f = extract_url_features("See www.example.com for info.")
        assert f["has_url"] is True

    def test_multiple_urls(self):
        f = extract_url_features("Links: http://a.com and http://b.com")
        assert f["multiple_urls"] is True
        assert f["url_count"] == 2


class TestIpUrl:
    def test_ipv4_url(self):
        f = extract_url_features("Login at http://203.0.113.45/login")
        assert f["url_has_ip"] is True

    def test_non_ip_url(self):
        f = extract_url_features("Visit http://example.com/page")
        assert f["url_has_ip"] is False


class TestUrlShortener:
    def test_bitly(self):
        f = extract_url_features("Click http://bit.ly/abc123 for offer")
        assert f["url_shortener"] is True

    def test_tinyurl(self):
        f = extract_url_features("See http://tinyurl.com/xyz for details")
        assert f["url_shortener"] is True

    def test_non_shortener(self):
        f = extract_url_features("Visit http://example.com/page")
        assert f["url_shortener"] is False


class TestSuspiciousChars:
    def test_at_in_url(self):
        f = extract_url_features("Login http://user@evil.com/phish")
        assert f["url_suspicious_chars"] is True

    def test_clean_url(self):
        f = extract_url_features("See http://example.com")
        assert f["url_suspicious_chars"] is False


class TestTrustedDomain:
    def test_exact_trusted(self):
        assert _is_trusted_domain("sbi.co.in") is True

    def test_www_trusted(self):
        # www.flipkart.com should be treated as trusted (www is a subdomain of trusted root)
        assert _is_trusted_domain("www.flipkart.com") is True
        assert _is_trusted_domain("flipkart.com") is True

    def test_subdomain_trusted(self):
        assert _is_trusted_domain("netbanking.hdfcbank.com") is True

    def test_misleading_not_trusted(self):
        # amazon.com.evil.net should NOT match amazon.com
        assert _is_trusted_domain("amazon.com.evil.net") is False

    def test_evil_subdomain_not_trusted(self):
        assert _is_trusted_domain("sbi.co.in.verify.com") is False


class TestSuspiciousSubdomain:
    def test_brand_in_subdomain(self):
        result = _has_suspicious_subdomain("sbi.co.in.malicious.test")
        assert result is True

    def test_trusted_domain_not_suspicious(self):
        result = _has_suspicious_subdomain("netbanking.sbi.co.in")
        assert result is False  # it IS trusted

    def test_unrelated_domain_not_suspicious(self):
        result = _has_suspicious_subdomain("shop.randomstore.com")
        assert result is False


class TestPunycode:
    def test_punycode_domain(self):
        f = extract_url_features("Visit http://xn--pple-43d.com/login")
        assert f["punycode_domain"] is True

    def test_normal_domain(self):
        f = extract_url_features("Visit http://example.com")
        assert f["punycode_domain"] is False


class TestMalformedUrl:
    def test_malformed_url(self):
        # Should not crash
        f = extract_url_features("Visit http:// broken url here")
        assert isinstance(f, dict)
        assert "has_url" in f

    def test_empty_message(self):
        f = extract_url_features("")
        assert f["has_url"] is False

    def test_none_message(self):
        f = extract_url_features(None)
        assert f["has_url"] is False


class TestFeatureVector:
    def test_vector_length(self):
        from src.url_features import get_url_feature_vector
        f = extract_url_features("test message http://example.com")
        vec = get_url_feature_vector(f)
        assert len(vec) == 10

    def test_vector_numeric(self):
        from src.url_features import get_url_feature_vector
        f = extract_url_features("test")
        vec = get_url_feature_vector(f)
        assert all(isinstance(v, (int, float)) for v in vec)
