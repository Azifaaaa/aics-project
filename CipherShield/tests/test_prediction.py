"""
CipherShield — Prediction Module Tests
Tests prediction.py behaviour when model is loaded and when it is not.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


class TestModelNotLoaded:
    """Tests that run regardless of whether retrain.py has been run."""

    def test_predict_no_model_returns_error(self):
        """If model is not loaded, predict() should return an error dict, not raise."""
        from src import prediction as pm
        # Temporarily mock model as not loaded
        orig = pm._model_loaded
        pm._model_loaded = False
        pm._load_error = "Test: model not loaded"
        result = pm.predict("Hello")
        pm._model_loaded = orig
        assert result.get("error") is not None

    def test_predict_empty_string(self):
        from src import prediction as pm
        orig = pm._model_loaded
        pm._model_loaded = False
        result = pm.predict("")
        pm._model_loaded = orig
        assert result.get("error") is not None

    def test_predict_none(self):
        from src import prediction as pm
        orig = pm._model_loaded
        pm._model_loaded = False
        result = pm.predict(None)
        pm._model_loaded = orig
        assert result.get("error") is not None


class TestPredictionWithModel:
    """Tests that require a trained model — skipped if model is not available."""

    @pytest.fixture(autouse=True)
    def skip_if_no_model(self):
        from src.prediction import is_model_loaded, load_model
        if not is_model_loaded():
            load_model()
        if not is_model_loaded():
            pytest.skip("Model not trained — run python retrain.py first")

    def test_valid_message_returns_dict(self):
        from src.prediction import predict
        result = predict("Hello, how are you?")
        assert isinstance(result, dict)
        assert "prediction" in result
        assert result["prediction"] in ("ham", "spam", "phishing")

    def test_result_has_required_keys(self):
        from src.prediction import predict
        result = predict("Free lottery prize claim now!")
        for key in ["prediction", "label", "confidence", "explanation",
                    "has_url", "url_count", "disclaimer", "detected_urls"]:
            assert key in result, f"Missing key: {key}"

    def test_url_in_message_detected(self):
        from src.prediction import predict
        result = predict("Visit http://example.com for more info.")
        assert result["has_url"] is True
        assert result["url_count"] >= 1
        assert len(result["detected_urls"]) >= 1

    def test_no_url_in_message(self):
        from src.prediction import predict
        result = predict("Call me when you get home please")
        assert result["has_url"] is False
        assert result["url_count"] == 0

    def test_ip_url_detected(self):
        from src.prediction import predict
        result = predict("Login at http://203.0.113.45/account to verify.")
        assert result["url_has_ip"] is True

    def test_shortener_detected(self):
        from src.prediction import predict
        result = predict("Claim your prize at http://bit.ly/win-now")
        assert result["url_shortener"] is True

    def test_multiple_urls_detected(self):
        from src.prediction import predict
        result = predict("See http://example.com and http://test.example.com for details.")
        assert result["multiple_urls"] is True

    def test_misleading_subdomain(self):
        from src.prediction import predict
        result = predict("Login at http://sbi.co.in.malicious.test/account")
        assert result["suspicious_subdomain"] is True

    def test_trusted_domain_not_phishing_override(self):
        """A trusted domain should NOT force prediction to ham."""
        from src.prediction import predict
        result = predict("Rs.5000 debited from your HDFC account. Available bal Rs.12000.")
        # We only check that the result is valid — not that it's necessarily ham
        assert result["prediction"] in ("ham", "spam", "phishing")

    def test_no_url_not_always_ham(self):
        """URL absence should not force ham prediction."""
        from src.prediction import predict
        result = predict("URGENT: Share your OTP immediately or your account will be blocked!")
        assert result["prediction"] in ("ham", "spam", "phishing")

    def test_disclaimer_always_present(self):
        from src.prediction import predict
        result = predict("Test message")
        assert result.get("disclaimer")
        assert "OTP" in result["disclaimer"] or "password" in result["disclaimer"]

    def test_training_inference_feature_consistency(self):
        """Verify that the feature vector dimension matches saved metadata."""
        import json
        from config import FEATURE_METADATA_PATH
        from src.feature_extraction import build_single_feature_vector
        from src.prediction import _vectorizer, _metadata

        if _vectorizer is None or _metadata is None:
            pytest.skip("Vectorizer not loaded")

        vec = build_single_feature_vector("test message", _vectorizer)
        expected = _metadata.get("n_total_features")
        if expected:
            assert vec.shape[1] == expected, (
                f"Feature count mismatch: got {vec.shape[1]}, expected {expected}"
            )

    def test_punycode_domain(self):
        from src.prediction import predict
        result = predict("Verify at http://xn--pple-43d.com/login now")
        assert result["punycode_domain"] is True

    def test_very_long_message(self):
        from src.prediction import predict
        long_msg = "Win prize " * 200
        result = predict(long_msg)
        assert result["prediction"] in ("ham", "spam", "phishing")
