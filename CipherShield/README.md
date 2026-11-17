# CipherShield — README

## Intelligent SMS Spam and Phishing Detection Using Machine Learning

**Project Type:** M.Sc. Cybersecurity Academic Mini-Project  
**Team:** Two-member student project

---

## Overview

CipherShield is a web application that analyses SMS messages and classifies them as:

- **HAM** — Legitimate messages
- **SPAM** — Unsolicited promotional/bulk messages  
- **PHISHING** — Deceptive messages that attempt to steal credentials, OTPs or money

It combines TF-IDF text classification with structural URL feature analysis.

---

## Prerequisites

- Python 3.9 or later
- Windows 10/11 with PowerShell
- VS Code (recommended) or any Python-capable editor
- Internet access only for installing packages (not for running the app)

---

## Installation

### Step 1 — Place the dataset

Place the `SMSSpamCollection` file (tab-separated) inside the `datasets/` folder:

```
CipherShield/
└── datasets/
    └── SMSSpamCollection
```

### Step 2 — Create a virtual environment

Open PowerShell in the `CipherShield/` directory:

```powershell
cd CipherShield
python -m venv .venv
```

### Step 3 — Activate the virtual environment

```powershell
.venv\Scripts\Activate.ps1
```

If you get an execution policy error:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try activating again.

### Step 4 — Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

## Training the Model

**You MUST run this before starting the application.**

```powershell
python retrain.py
```

This will:
1. Load and merge both datasets
2. Preprocess messages
3. Train and compare 3 ML algorithms
4. Save the best model to `models/`
5. Print an evaluation report

Expected output:
```
[Train] Best model: LogisticRegression  (Macro F1 = 0.9xxx)
[Train] Classifier saved → models/classifier.joblib
```

---

## Running the Application

```powershell
python app.py
```

Open your browser and go to: **http://127.0.0.1:5000**

---

## Running Tests

```powershell
python -m pytest tests/ -v
```

Tests that require a trained model are automatically skipped if `retrain.py`
has not been run yet.

---

## Project Structure

```
CipherShield/
├── app.py                      # Flask application
├── retrain.py                  # Model training entry point
├── config.py                   # All configuration settings
├── requirements.txt
│
├── datasets/
│   ├── SMSSpamCollection       # Original UCI dataset (place here)
│   ├── modern_sms_dataset.csv  # Supplementary synthetic dataset
│   └── dataset_review_guide.md
│
├── models/                     # Generated after retrain.py
│   ├── classifier.joblib
│   ├── vectorizer.joblib
│   ├── feature_metadata.json
│   └── evaluation_report.json
│
├── src/
│   ├── data_loader.py          # Dataset loading and merging
│   ├── preprocessing.py        # Text preprocessing
│   ├── url_features.py         # URL structural analysis
│   ├── feature_extraction.py   # TF-IDF + URL feature matrix
│   ├── model_training.py       # Training and comparison logic
│   └── prediction.py           # Inference module
│
├── database/
│   └── database.py             # SQLite history module
│
├── templates/                  # Jinja2 HTML templates
│   ├── index.html              # Base layout
│   ├── dashboard.html
│   ├── analyze.html
│   ├── history.html
│   ├── insights.html
│   └── about.html
│
├── static/
│   ├── css/style.css
│   └── js/
│       ├── app.js
│       ├── dashboard.js
│       ├── analyze.js
│       └── charts.js
│
├── tests/
│   ├── test_url_features.py
│   ├── test_data_loader.py
│   ├── test_prediction.py
│   └── test_routes.py
│
└── docs/
    ├── project_report.md
    ├── architecture.md
    ├── viva_questions.md
    ├── testing_report.md
    └── member_contributions.md
```

---

## API Reference

| Method | Endpoint        | Description |
|--------|-----------------|-------------|
| GET    | `/`             | Dashboard   |
| GET    | `/analyze`      | Analysis page |
| GET    | `/history`      | Detection history |
| GET    | `/insights`     | Dataset insights |
| GET    | `/about`        | About page |
| POST   | `/predict`      | Classify a message |
| GET    | `/api/stats`    | Dataset + session statistics |
| GET    | `/api/history`  | History records (JSON) |
| DELETE | `/api/history`  | Clear history |
| GET    | `/api/health`   | Model health check |
| GET    | `/api/eval`     | Full evaluation report |

### POST /predict

Request body:
```json
{ "message": "Your SMS text here" }
```

Response:
```json
{
  "prediction": "phishing",
  "label": "phishing",
  "confidence": 0.9134,
  "explanation": "...",
  "has_url": true,
  "url_count": 1,
  "url_has_ip": false,
  "url_shortener": false,
  "url_suspicious_chars": false,
  "trusted_domain": false,
  "suspicious_subdomain": true,
  "punycode_domain": false,
  "multiple_urls": false,
  "suspicious_url_scheme": false,
  "detected_urls": ["http://sbi-kyc.test/verify"],
  "disclaimer": "Machine-learning predictions are not guarantees of safety..."
}
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Model artefacts not found` | Run `python retrain.py` |
| `SMSSpamCollection not found` | Place the file in `datasets/` |
| `ModuleNotFoundError` | Activate venv and run `pip install -r requirements.txt` |
| Port 5000 in use | Change port in `app.py` or kill the process |
| Execution policy error | Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| Phishing performance low | Add more phishing examples to `modern_sms_dataset.csv` and retrain |

---

## Privacy

- Messages are processed locally — no data is sent to external servers.
- History stores only classification metadata (label, confidence, URL count, timestamp).
- Message text is never stored in the database.
- History can be disabled in `config.py` by setting `HISTORY_ENABLED = False`.
- History can be deleted from the Detection History page.

---

## Limitations

- No real-time URL threat intelligence checking.
- Cannot verify sender identity or confirm whether a bank message is authentic.
- Phishing class performance depends on the size of the supplementary dataset.
- Short, ambiguous messages may be misclassified.
- Model does not understand language nuance or intent.

---

*CipherShield — M.Sc. Cybersecurity Academic Mini-Project*
