"""
CipherShield — Flask Application
"""
import os
import sys
import json

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from flask import Flask, request, jsonify, render_template, abort

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SECRET_KEY, MAX_MESSAGE_LENGTH, HISTORY_ENABLED, EVALUATION_REPORT_PATH
from src.prediction import load_model, predict, is_model_loaded, get_load_error
from src.data_loader import get_dataset_stats
from database.database import init_db, record_analysis, get_history, get_session_stats, clear_history

# ── Application factory ───────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Initialise database
init_db()

# Load ML model once at startup
print("[CipherShield] Loading model artefacts…")
model_ok = load_model()
if not model_ok:
    print(f"[CipherShield] WARNING — {get_load_error()}")
    print("[CipherShield] Run 'python retrain.py' to train the model.")
else:
    print("[CipherShield] Model ready.")


# ── Page routes ───────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/analyze")
def analyze():
    return render_template("analyze.html")


@app.route("/history")
def history_page():
    return render_template("history.html")


@app.route("/insights")
def insights():
    return render_template("insights.html")


@app.route("/about")
def about():
    return render_template("about.html")


# ── API routes ────────────────────────────────────────────────────────────────

@app.route("/predict", methods=["POST"])
def predict_route():
    """
    POST /predict
    Body: {"message": "SMS text here"}
    Returns: prediction JSON
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON."}), 400

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid JSON body."}), 400

    message = data.get("message", "")
    if not message or not isinstance(message, str):
        return jsonify({"error": "Field 'message' is required and must be a non-empty string."}), 400

    message = message.strip()
    if not message:
        return jsonify({"error": "Message cannot be empty."}), 400

    if len(message) > MAX_MESSAGE_LENGTH:
        return jsonify({
            "error": f"Message exceeds maximum length of {MAX_MESSAGE_LENGTH} characters."
        }), 400

    if not is_model_loaded():
        return jsonify({
            "error": "Model is not loaded. Run 'python retrain.py' to train the model first.",
            "model_status": "unavailable"
        }), 503

    result = predict(message)

    if result.get("error"):
        return jsonify(result), 500

    # Record to history (only label, confidence, url stats — not the message text)
    if HISTORY_ENABLED and result.get("prediction"):
        record_analysis(
            label=result["prediction"],
            confidence=result.get("confidence"),
            has_url=result.get("has_url", False),
            url_count=result.get("url_count", 0),
            model_name=result.get("model_name", ""),
        )

    return jsonify(result), 200


@app.route("/api/stats", methods=["GET"])
def api_stats():
    """Return dataset statistics + session analysis statistics."""
    dataset_stats = get_dataset_stats()
    session_stats = get_session_stats()

    # Load evaluation report if available
    eval_report = {}
    if os.path.exists(EVALUATION_REPORT_PATH):
        try:
            with open(EVALUATION_REPORT_PATH) as f:
                eval_report = json.load(f)
        except Exception:
            pass

    return jsonify({
        "dataset": dataset_stats,
        "session": session_stats,
        "model": {
            "loaded": is_model_loaded(),
            "best_model": eval_report.get("best_model"),
            "macro_f1": eval_report.get("best_model_evaluation", {}).get("macro_f1"),
            "accuracy": eval_report.get("best_model_evaluation", {}).get("accuracy"),
            "phishing_class_supported": eval_report.get("phishing_class_available", False),
        },
    }), 200


@app.route("/api/history", methods=["GET"])
def api_history():
    """Return recent analysis history (without message text)."""
    if not HISTORY_ENABLED:
        return jsonify({"enabled": False, "records": []}), 200
    records = get_history(limit=100)
    return jsonify({"enabled": True, "records": records}), 200


@app.route("/api/history", methods=["DELETE"])
def api_clear_history():
    """Clear all stored analysis history."""
    success = clear_history()
    if success:
        return jsonify({"message": "History cleared successfully."}), 200
    return jsonify({"error": "Failed to clear history."}), 500


@app.route("/api/health", methods=["GET"])
def api_health():
    """Return application health status."""
    return jsonify({
        "status": "ok",
        "model_loaded": is_model_loaded(),
        "model_error": get_load_error() if not is_model_loaded() else None,
        "history_enabled": HISTORY_ENABLED,
    }), 200


@app.route("/api/eval", methods=["GET"])
def api_eval():
    """Return full model evaluation report."""
    if not os.path.exists(EVALUATION_REPORT_PATH):
        return jsonify({"error": "Evaluation report not found. Run retrain.py first."}), 404
    try:
        with open(EVALUATION_REPORT_PATH) as f:
            report = json.load(f)
        return jsonify(report), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ── Error handlers ────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found."}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed."}), 405


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "An internal server error occurred."}), 500


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  CipherShield — SMS Spam & Phishing Detection")
    print("  http://127.0.0.1:5000")
    print("=" * 55 + "\n")
    app.run(debug=True, host="127.0.0.1", port=5000)
