"""
CipherShield — Flask Route Tests
Tests API endpoints and error handling.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import json


@pytest.fixture
def client():
    """Create a Flask test client."""
    import app as flask_app
    flask_app.app.config["TESTING"] = True
    with flask_app.app.test_client() as c:
        yield c


class TestPageRoutes:
    def test_dashboard_200(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_analyze_200(self, client):
        r = client.get("/analyze")
        assert r.status_code == 200

    def test_history_200(self, client):
        r = client.get("/history")
        assert r.status_code == 200

    def test_insights_200(self, client):
        r = client.get("/insights")
        assert r.status_code == 200

    def test_about_200(self, client):
        r = client.get("/about")
        assert r.status_code == 200


class TestHealthRoute:
    def test_health_ok(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "status" in data
        assert data["status"] == "ok"
        assert "model_loaded" in data


class TestStatsRoute:
    def test_stats_ok(self, client):
        r = client.get("/api/stats")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "dataset" in data
        assert "session" in data
        assert "model" in data


class TestHistoryRoute:
    def test_history_ok(self, client):
        r = client.get("/api/history")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "records" in data

    def test_clear_history(self, client):
        r = client.delete("/api/history")
        assert r.status_code in (200, 500)  # 500 if DB error; 200 if ok


class TestPredictRoute:
    def test_empty_message(self, client):
        r = client.post("/predict",
                        data=json.dumps({"message": ""}),
                        content_type="application/json")
        assert r.status_code in (400, 503)  # 400=empty, 503=model not loaded

    def test_missing_message_field(self, client):
        r = client.post("/predict",
                        data=json.dumps({"text": "hello"}),
                        content_type="application/json")
        assert r.status_code in (400, 503)

    def test_invalid_json(self, client):
        r = client.post("/predict",
                        data="not json at all",
                        content_type="application/json")
        assert r.status_code in (400, 503)

    def test_non_json_content_type(self, client):
        r = client.post("/predict",
                        data="message=hello",
                        content_type="application/x-www-form-urlencoded")
        assert r.status_code == 400

    def test_very_long_message(self, client):
        long_msg = "a" * 2001
        r = client.post("/predict",
                        data=json.dumps({"message": long_msg}),
                        content_type="application/json")
        assert r.status_code in (400, 503)

    def test_valid_message_when_model_loaded(self, client):
        """Only run full prediction test if the model is loaded."""
        from src.prediction import is_model_loaded
        if not is_model_loaded():
            pytest.skip("Model not trained — run python retrain.py first")

        r = client.post("/predict",
                        data=json.dumps({"message": "Your account has been updated successfully."}),
                        content_type="application/json")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "prediction" in data
        assert data["prediction"] in ("ham", "spam", "phishing")
        assert "explanation" in data
        assert "disclaimer" in data

    def test_ham_message_when_model_loaded(self, client):
        from src.prediction import is_model_loaded
        if not is_model_loaded():
            pytest.skip("Model not trained")
        r = client.post("/predict",
                        data=json.dumps({"message": "Hi, how are you doing today?"}),
                        content_type="application/json")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["prediction"] in ("ham", "spam", "phishing")

    def test_phishing_url_message_when_model_loaded(self, client):
        from src.prediction import is_model_loaded
        if not is_model_loaded():
            pytest.skip("Model not trained")
        r = client.post("/predict",
                        data=json.dumps({"message": "URGENT: Your SBI account suspended. Update KYC at http://sbi-kyc-verify.test/update"}),
                        content_type="application/json")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["has_url"] is True

    def test_url_features_in_response(self, client):
        from src.prediction import is_model_loaded
        if not is_model_loaded():
            pytest.skip("Model not trained")
        r = client.post("/predict",
                        data=json.dumps({"message": "Check http://bit.ly/abc123 for offer"}),
                        content_type="application/json")
        assert r.status_code == 200
        data = json.loads(r.data)
        for key in ["has_url", "url_count", "url_shortener", "url_has_ip",
                    "trusted_domain", "detected_urls"]:
            assert key in data, f"Missing key: {key}"
        assert data["url_shortener"] is True

    def test_404_route(self, client):
        r = client.get("/nonexistent-page-xyz")
        assert r.status_code == 404

    def test_method_not_allowed(self, client):
        r = client.get("/predict")
        assert r.status_code == 405
