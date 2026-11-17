"""
CipherShield — Application Configuration
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Dataset paths ────────────────────────────────────────────────────────────
DATASET_DIR = os.path.join(BASE_DIR, "datasets")
ORIGINAL_DATASET = os.path.join(DATASET_DIR, "SMSSpamCollection")
SUPPLEMENTARY_DATASET = os.path.join(DATASET_DIR, "modern_sms_dataset.csv")

# ── Model artefacts ──────────────────────────────────────────────────────────
MODELS_DIR = os.path.join(BASE_DIR, "models")
CLASSIFIER_PATH = os.path.join(MODELS_DIR, "classifier.joblib")
VECTORIZER_PATH = os.path.join(MODELS_DIR, "vectorizer.joblib")
FEATURE_METADATA_PATH = os.path.join(MODELS_DIR, "feature_metadata.json")
EVALUATION_REPORT_PATH = os.path.join(MODELS_DIR, "evaluation_report.json")

# ── TF-IDF settings ──────────────────────────────────────────────────────────
TFIDF_MAX_FEATURES = 8000
TFIDF_NGRAM_RANGE = (1, 2)
TFIDF_MIN_DF = 2
TFIDF_SUBLINEAR_TF = True

# ── Training settings ────────────────────────────────────────────────────────
RANDOM_SEED = 42
TEST_SIZE = 0.20

# ── Flask settings ───────────────────────────────────────────────────────────
SECRET_KEY = "ciphershield-dev-key-change-in-production"
MAX_MESSAGE_LENGTH = 2000
HISTORY_ENABLED = True          # set False to disable SQLite history

# ── Database ─────────────────────────────────────────────────────────────────
DATABASE_DIR = os.path.join(BASE_DIR, "database")
DATABASE_PATH = os.path.join(DATABASE_DIR, "ciphershield.db")

# ── Trusted domains (hostname must END with one of these after stripping www)─
TRUSTED_DOMAINS = [
    "sbi.co.in", "hdfcbank.com", "icicibank.com", "axisbank.com",
    "kotak.com", "pnbindia.in", "bankofbaroda.in", "canarabank.com",
    "unionbankofindia.co.in", "upi.npci.org.in", "npci.org.in",
    "paytm.com", "phonepe.com", "gpay.app", "bhimupi.org.in",
    "amazon.in", "amazon.com", "flipkart.com", "myntra.com",
    "swiggy.com", "zomato.com", "makemytrip.com", "irctc.co.in",
    "indianpost.gov.in", "indiapost.gov.in", "uidai.gov.in",
    "incometax.gov.in", "mca.gov.in", "nsdl.co.in", "cdslindia.com",
    "google.com", "microsoft.com", "apple.com", "linkedin.com",
    "example.com",          # safe illustrative domain used in test messages
]

# ── URL shortener hostnames ───────────────────────────────────────────────────
URL_SHORTENERS = [
    "bit.ly", "tinyurl.com", "goo.gl", "ow.ly", "t.co",
    "is.gd", "buff.ly", "adf.ly", "rb.gy", "cutt.ly",
    "short.io", "tiny.cc", "shorturl.at", "clck.ru",
    "s.id", "v.gd", "yourls.org",
]
