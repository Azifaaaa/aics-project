"""
CipherShield — Text Preprocessing
Shared preprocessing function used identically during training and prediction.
"""
import re
import string


# ── constants ─────────────────────────────────────────────────────────────────

# Minimal stop-words: only the most common function words
# (we keep words like "free", "win", "urgent" because they carry signal)
_STOP_WORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves",
    "you", "your", "yours", "yourself", "yourselves", "he", "him",
    "his", "himself", "she", "her", "hers", "herself", "it", "its",
    "itself", "they", "them", "their", "theirs", "themselves",
    "what", "which", "who", "whom", "this", "that", "these", "those",
    "am", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having", "do", "does", "did", "doing",
    "a", "an", "the", "and", "but", "if", "or", "because", "as",
    "until", "while", "of", "at", "by", "for", "with", "about",
    "against", "between", "into", "through", "during", "before",
    "after", "above", "below", "to", "from", "up", "down", "in",
    "out", "on", "off", "over", "under", "again", "further",
    "then", "once", "here", "there", "when", "where", "why", "how",
    "all", "both", "each", "few", "more", "most", "other", "some",
    "such", "no", "nor", "not", "only", "own", "same", "so",
    "than", "too", "very", "s", "t", "just", "don", "should", "now",
    "d", "ll", "m", "o", "re", "ve", "y", "ain", "aren",
    "couldn", "didn", "doesn", "hadn", "hasn", "haven", "isn",
    "ma", "mightn", "mustn", "needn", "shan", "shouldn", "wasn",
    "weren", "won", "wouldn",
}

# Pattern to detect URLs — preserved as a placeholder token before cleaning
_URL_PATTERN = re.compile(
    r"https?://[^\s]+|www\.[^\s]+", re.IGNORECASE
)

# Pattern to detect phone numbers
_PHONE_PATTERN = re.compile(r"\b(?:\+91[\s\-]?)?\d{10}\b|\b\d{3}[\s\-]\d{3}[\s\-]\d{4}\b")

# Repeated characters (e.g. "freeeeee" → "free")
_REPEAT_PATTERN = re.compile(r"(.)\1{2,}")


def preprocess_text(text: str, preserve_url_token: bool = True) -> str:
    """
    Clean and normalise an SMS message.

    Steps:
    1.  Coerce to string safely.
    2.  Lower-case.
    3.  Replace URLs with a URL_TOKEN placeholder (optionally).
    4.  Replace phone numbers with PHONE_TOKEN.
    5.  Remove HTML entities / tags.
    6.  Expand common SMS abbreviations (minimal — do not over-expand).
    7.  Remove punctuation (keeping apostrophes for contractions).
    8.  Collapse repeated characters.
    9.  Remove digits (after URL/phone replacement).
    10. Remove stop-words.
    11. Normalise whitespace.

    Parameters
    ----------
    text : str
        Raw SMS message.
    preserve_url_token : bool
        When True, insert a URL_TOKEN before removing the URL text.
        This lets TF-IDF learn from URL presence without learning specific URLs.

    Returns
    -------
    str
        Cleaned, normalised text ready for TF-IDF vectorization.
    """
    if not isinstance(text, str):
        text = str(text) if text is not None else ""

    text = text.strip()
    if not text:
        return ""

    # Lower-case
    text = text.lower()

    # Replace URLs
    if preserve_url_token:
        text = _URL_PATTERN.sub(" url_token ", text)
    else:
        text = _URL_PATTERN.sub(" ", text)

    # Replace phone numbers
    text = _PHONE_PATTERN.sub(" phone_token ", text)

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove HTML entities
    text = re.sub(r"&[a-z]+;", " ", text)

    # Minimal SMS abbreviation expansion (only high-signal ones)
    sms_expansions = {
        r"\bu\b": "you",
        r"\bur\b": "your",
        r"\br\b": "are",
        r"\bplz\b": "please",
        r"\bpls\b": "please",
        r"\btxt\b": "text",
        r"\bmsg\b": "message",
        r"\bfr\b": "for",
        r"\bwt\b": "what",
        r"\bgr8\b": "great",
        r"\bbtw\b": "between",
        r"\blol\b": "laugh",
    }
    for pattern, replacement in sms_expansions.items():
        text = re.sub(pattern, replacement, text)

    # Remove punctuation except apostrophes
    text = text.translate(
        str.maketrans(
            "",
            "",
            "".join(c for c in string.punctuation if c != "'"),
        )
    )

    # Collapse 3+ repeated chars (e.g. "loooong" → "long")
    text = _REPEAT_PATTERN.sub(r"\1\1", text)

    # Remove standalone digits (keep digit-containing tokens like "2fa")
    text = re.sub(r"\b\d+\b", " ", text)

    # Remove stop-words
    tokens = text.split()
    tokens = [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]

    return " ".join(tokens)


def extract_urls_from_message(text: str) -> list:
    """
    Return a list of raw URLs found in the message (before preprocessing).
    Used by url_features.py.
    """
    if not isinstance(text, str):
        return []
    return _URL_PATTERN.findall(text)
