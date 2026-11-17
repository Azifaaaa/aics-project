"""
CipherShield — Prediction Module
Loads saved model artefacts and provides a predict() function used by Flask.
"""
import os
import sys
import json

import joblib
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CLASSIFIER_PATH, VECTORIZER_PATH, FEATURE_METADATA_PATH
from src.feature_extraction import build_single_feature_vector
from src.url_features import extract_url_features


# ── model loading ─────────────────────────────────────────────────────────────

_classifier = None
_vectorizer = None
_metadata = None
_model_loaded = False
_load_error = None


def load_model():
    """
    Load model artefacts from disk.
    Called once at Flask startup.
    Sets _model_loaded = True on success.
    """
    global _classifier, _vectorizer, _metadata, _model_loaded, _load_error

    missing = []
    for path, name in [
        (CLASSIFIER_PATH, "classifier.joblib"),
        (VECTORIZER_PATH, "vectorizer.joblib"),
        (FEATURE_METADATA_PATH, "feature_metadata.json"),
    ]:
        if not os.path.exists(path):
            missing.append(name)

    if missing:
        _load_error = (
            f"Model artefacts not found: {missing}. "
            "Run `python retrain.py` to train the model first."
        )
        _model_loaded = False
        return False

    try:
        _classifier = joblib.load(CLASSIFIER_PATH)
        _vectorizer = joblib.load(VECTORIZER_PATH)
        with open(FEATURE_METADATA_PATH) as f:
            _metadata = json.load(f)

        # Sanity check: feature count consistency
        expected_features = _metadata.get("n_total_features", 0)
        test_vec = build_single_feature_vector("test message", _vectorizer)
        if test_vec.shape[1] != expected_features:
            _load_error = (
                f"Feature count mismatch: model expects {expected_features}, "
                f"got {test_vec.shape[1]}. Retrain the model."
            )
            _model_loaded = False
            return False

        _model_loaded = True
        _load_error = None
        label_names = _metadata.get("label_names", ["ham", "spam"])
        print(f"[Prediction] Model loaded OK — classes: {label_names}")
        return True

    except Exception as exc:
        _load_error = f"Failed to load model: {str(exc)}"
        _model_loaded = False
        return False


def is_model_loaded() -> bool:
    return _model_loaded


def get_load_error() -> str:
    return _load_error or "Unknown error"


# ── confidence ────────────────────────────────────────────────────────────────

def _get_confidence(clf, feature_vector) -> float:
    """Return probability for the predicted class (0-1), or -1 if unavailable."""
    try:
        proba = clf.predict_proba(feature_vector)[0]
        return float(np.max(proba))
    except AttributeError:
        return -1.0


def _get_all_probs(clf, feature_vector, label_names) -> dict:
    """Return per-class probability dict."""
    try:
        proba = clf.predict_proba(feature_vector)[0]
        return {label_names[i]: round(float(p), 4) for i, p in enumerate(proba)}
    except AttributeError:
        return {}


# ── explanation generator ─────────────────────────────────────────────────────

def _build_explanation(prediction: str, url_features: dict, confidence: float) -> str:
    """Generate a human-readable explanation from detected features."""
    indicators = []

    if url_features["url_has_ip"]:
        indicators.append("IP-based URL (unusual for legitimate services)")
    if url_features["url_shortener"]:
        indicators.append("URL shortener detected (hides real destination)")
    if url_features["url_suspicious_chars"]:
        indicators.append("Suspicious URL characters (possible obfuscation)")
    if url_features["suspicious_subdomain"]:
        indicators.append("Misleading subdomain mimicking a trusted brand")
    if url_features["punycode_domain"]:
        indicators.append("Punycode/IDN domain (possible homograph attack)")
    if url_features["multiple_urls"]:
        indicators.append("Multiple URLs in one message")
    if url_features["suspicious_url_scheme"]:
        indicators.append("Unusual URL scheme")

    if prediction == "phishing":
        base = "The message resembles phishing patterns"
        if url_features["has_url"]:
            base += " and contains a suspicious link"
        if indicators:
            base += ". Indicators: " + "; ".join(indicators)
        base += "."
        base += " Do NOT click any links or share OTPs/passwords/banking details."

    elif prediction == "spam":
        base = "The message contains promotional or unsolicited patterns commonly associated with spam"
        if url_features["has_url"]:
            base += " and includes a URL"
        base += "."

    else:  # ham
        base = "The model did not identify strong spam or phishing patterns in this message"
        if url_features["has_url"] and url_features["trusted_domain"]:
            base += " (URL appears to be from a recognised domain)"
        elif url_features["has_url"]:
            base += " (URL present — verify before clicking)"
        base += "."

    return base


def _get_suspicious_indicators(url_features: dict) -> list:
    """Return a list of human-readable suspicious indicators."""
    flags = []
    if url_features["url_has_ip"]:
        flags.append("IP-based URL")
    if url_features["url_shortener"]:
        flags.append("URL shortener")
    if url_features["url_suspicious_chars"]:
        flags.append("Suspicious URL syntax (@, excessive dots)")
    if url_features["suspicious_subdomain"]:
        flags.append("Misleading subdomain")
    if url_features["punycode_domain"]:
        flags.append("Punycode/IDN domain")
    if url_features["multiple_urls"]:
        flags.append("Multiple URLs")
    if url_features["suspicious_url_scheme"]:
        flags.append("Unusual URL scheme")
    if url_features["url_length"] > 100:
        flags.append("Unusually long URL")
    return flags


# ── main prediction function ──────────────────────────────────────────────────

def predict(message: str) -> dict:
    """
    Predict the class of a raw SMS message.

    Parameters
    ----------
    message : str
        Raw SMS text as entered by the user.

    Returns
    -------
    dict
        Full prediction result with label, confidence, URL features, explanation.
    """
    if not _model_loaded:
        return {
            "error": _load_error or "Model not loaded. Run python retrain.py first.",
            "prediction": None,
            "label": None,
        }

    if not message or not isinstance(message, str):
        return {"error": "Empty or invalid message.", "prediction": None, "label": None}

    message = message.strip()
    if not message:
        return {"error": "Message is empty after stripping whitespace.", "prediction": None, "label": None}

    label_names = _metadata.get("label_names", ["ham", "spam"])

    # Build features
    feature_vector = build_single_feature_vector(message, _vectorizer)

    # Predict
    pred_index = int(_classifier.predict(feature_vector)[0])
    prediction = label_names[pred_index] if pred_index < len(label_names) else "unknown"

    # Confidence
    confidence = _get_confidence(_classifier, feature_vector)
    all_probs = _get_all_probs(_classifier, feature_vector, label_names)

    # URL analysis
    url_feats = extract_url_features(message)

    # Explanation
    explanation = _build_explanation(prediction, url_feats, confidence)
    indicators = _get_suspicious_indicators(url_feats)

    return {
        "prediction": prediction,
        "label": prediction,
        "confidence": round(confidence, 4) if confidence >= 0 else None,
        "all_probabilities": all_probs,
        "explanation": explanation,
        "suspicious_indicators": indicators,
        # URL features (flat, for JSON response)
        "has_url": url_feats["has_url"],
        "url_count": url_feats["url_count"],
        "url_has_ip": url_feats["url_has_ip"],
        "url_shortener": url_feats["url_shortener"],
        "url_suspicious_chars": url_feats["url_suspicious_chars"],
        "url_length": url_feats["url_length"],
        "trusted_domain": url_feats["trusted_domain"],
        "suspicious_subdomain": url_feats["suspicious_subdomain"],
        "punycode_domain": url_feats["punycode_domain"],
        "multiple_urls": url_feats["multiple_urls"],
        "suspicious_url_scheme": url_feats["suspicious_url_scheme"],
        "detected_urls": url_feats["detected_urls"],
        "model_name": _metadata.get("best_model", "unknown"),
        "phishing_class_supported": "phishing" in label_names,
        "disclaimer": (
            "Machine-learning predictions are not guarantees of safety. "
            "Never share your password, OTP, banking PIN or sensitive information "
            "based only on this result."
        ),
    }
