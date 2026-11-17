"""
CipherShield — Feature Extraction
Combines TF-IDF text features with URL numeric features into a single
sparse matrix used for both training and inference.
"""
import os
import sys
import numpy as np
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    TFIDF_MAX_FEATURES, TFIDF_NGRAM_RANGE,
    TFIDF_MIN_DF, TFIDF_SUBLINEAR_TF,
)
from src.preprocessing import preprocess_text
from src.url_features import extract_url_features, get_url_feature_vector, URL_FEATURE_NAMES


def build_vectorizer() -> TfidfVectorizer:
    """Create a fresh (unfitted) TF-IDF vectorizer with project settings."""
    return TfidfVectorizer(
        max_features=TFIDF_MAX_FEATURES,
        ngram_range=TFIDF_NGRAM_RANGE,
        min_df=TFIDF_MIN_DF,
        sublinear_tf=TFIDF_SUBLINEAR_TF,
        strip_accents="unicode",
        analyzer="word",
        token_pattern=r"(?u)\b\w\w+\b",
    )


def build_feature_matrix(messages: list, vectorizer: TfidfVectorizer, fit: bool = False):
    """
    Build a combined feature matrix from a list of raw SMS messages.

    Parameters
    ----------
    messages : list of str
        Raw SMS texts (not yet preprocessed).
    vectorizer : TfidfVectorizer
        Already fitted (fit=False) or to be fitted (fit=True) vectorizer.
    fit : bool
        When True, fit the vectorizer on this data before transforming.

    Returns
    -------
    scipy.sparse matrix
        Combined [TF-IDF | URL-features] sparse matrix, shape (n, tfidf+10).
    """
    # Preprocess all messages identically
    cleaned = [preprocess_text(m) for m in messages]

    # TF-IDF
    if fit:
        tfidf_matrix = vectorizer.fit_transform(cleaned)
    else:
        tfidf_matrix = vectorizer.transform(cleaned)

    # URL features
    url_rows = []
    for msg in messages:
        feats = extract_url_features(msg)
        url_rows.append(get_url_feature_vector(feats))

    url_matrix = sp.csr_matrix(np.array(url_rows, dtype=np.float32))

    # Horizontal concatenation
    combined = sp.hstack([tfidf_matrix, url_matrix], format="csr")
    return combined


def build_single_feature_vector(message: str, vectorizer: TfidfVectorizer):
    """
    Build a feature matrix for a single message (for inference).
    Returns shape (1, n_features).
    """
    return build_feature_matrix([message], vectorizer, fit=False)


def get_feature_names(vectorizer: TfidfVectorizer) -> list:
    """Return ordered list of all feature names (TF-IDF vocab + URL names)."""
    tfidf_names = vectorizer.get_feature_names_out().tolist()
    return tfidf_names + URL_FEATURE_NAMES
