# CipherShield — Testing Report

## Test Suite Overview

The test suite covers URL feature extraction, data loading, Flask API routes and prediction behaviour.
Tests are located in `tests/` and can be run with:

```powershell
python -m pytest tests/ -v
```

---

## Test Categories

### 1. URL Feature Tests (`test_url_features.py`)

These tests are independent of the ML model and always run.

| Test | Description | Expected |
|------|-------------|----------|
| TestNoUrl | Message with no URL | has_url=False, url_count=0 |
| TestBasicUrlDetection | HTTP, HTTPS, WWW URLs | has_url=True |
| TestBasicUrlDetection | Multiple URLs | multiple_urls=True |
| TestIpUrl | IPv4 hostname in URL | url_has_ip=True |
| TestIpUrl | Regular hostname | url_has_ip=False |
| TestUrlShortener | bit.ly, tinyurl.com | url_shortener=True |
| TestUrlShortener | Regular domain | url_shortener=False |
| TestSuspiciousChars | @ in URL authority | url_suspicious_chars=True |
| TestTrustedDomain | sbi.co.in, hdfcbank.com | trusted=True |
| TestTrustedDomain | amazon.com.evil.net | trusted=False (not substring) |
| TestSuspiciousSubdomain | sbi brand in untrusted domain | suspicious=True |
| TestPunycode | xn-- domain | punycode=True |
| TestMalformedUrl | Malformed, empty, None | No crash, dict returned |
| TestFeatureVector | Vector length | len=10 |
| TestFeatureVector | Numeric types | all int/float |

### 2. Data Loader Tests (`test_data_loader.py`)

| Test | Description | Requires dataset? |
|------|-------------|-------------------|
| load supplementary exists | Supplementary CSV loads | Yes (supplementary) |
| supplementary columns | All required columns present | Yes |
| supplementary valid labels | Only ham/spam/phishing | Yes |
| supplementary phishing exists | Phishing class present | Yes |
| no empty messages | No empty messages after load | Yes |
| missing original raises | FileNotFoundError for missing original | No |
| stats structure | Stats dict has required keys | Conditional |
| label normalisation | Ham/SPAM/Phishing normalised | No |

### 3. Prediction Tests (`test_prediction.py`)

Tests that require a trained model are automatically skipped if `retrain.py` has not been run.

| Test | Description |
|------|-------------|
| predict no model | Returns error dict (no exception) |
| predict empty | Error for empty string |
| predict none | Error for None input |
| valid message | Returns ham/spam/phishing |
| required keys | All fields in response |
| URL detected | has_url=True for message with URL |
| no URL | has_url=False, url_count=0 |
| IP URL | url_has_ip=True |
| shortener | url_shortener=True |
| multiple URLs | multiple_urls=True |
| misleading subdomain | suspicious_subdomain=True |
| trusted domain override | Prediction not forced to ham |
| no URL not always ham | Prediction can be spam/phishing without URL |
| disclaimer present | Disclaimer always in response |
| feature consistency | Vector dimension matches saved metadata |
| punycode domain | punycode_domain=True |
| very long message | Handles gracefully |

### 4. Route Tests (`test_routes.py`)

| Test | Description | Expected |
|------|-------------|----------|
| Dashboard 200 | GET / | 200 |
| Analyze 200 | GET /analyze | 200 |
| History 200 | GET /history | 200 |
| Insights 200 | GET /insights | 200 |
| About 200 | GET /about | 200 |
| Health OK | GET /api/health | 200, model_loaded key |
| Stats OK | GET /api/stats | 200, dataset/session/model keys |
| History GET | GET /api/history | 200, records key |
| History DELETE | DELETE /api/history | 200 or 500 |
| Empty message | POST /predict {message:""} | 400 or 503 |
| Missing field | POST /predict {text:"hello"} | 400 or 503 |
| Invalid JSON | POST /predict (bad JSON) | 400 or 503 |
| Wrong content type | POST /predict (form data) | 400 |
| Very long message | POST /predict (2001 chars) | 400 or 503 |
| Valid message* | POST /predict with valid text | 200, prediction in response |
| URL in response* | POST /predict with URL message | url keys in response |
| 404 route | GET /nonexistent | 404 |
| Method not allowed | GET /predict | 405 |

*Requires trained model — skipped if model not available.

---

## Test Execution Notes

- Tests with `pytest.skip("Model not trained")` are skipped automatically when `retrain.py` has not been run. This is expected and correct.
- After running `python retrain.py`, all tests including model-dependent ones should pass.
- URL feature tests always pass regardless of model training status.

---

## Important Testing Principles

1. **URL tests do not use hardcoded predictions** — they test structural feature detection only.
2. **Route tests do not assert specific predictions** — they verify response format and status codes.
3. **Prediction tests verify the response structure** — not that a specific message is always classified one way.
4. **Model loading errors are tested explicitly** — the application should return JSON error responses, not Python stack traces.
