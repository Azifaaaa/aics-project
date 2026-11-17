# CipherShield — Architecture Documentation

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    USER BROWSER                          │
│  HTML + CSS + Vanilla JS                                 │
│  Dashboard | Analyze | History | Insights | About        │
└────────────────────┬────────────────────────────────────┘
                     │  HTTP/REST (JSON)
                     │  POST /predict
                     │  GET  /api/stats, /api/history, /api/health
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   FLASK BACKEND (app.py)                  │
│                                                           │
│  Route handlers → Input validation → predict()           │
│                              │                            │
│            ┌─────────────────┼──────────────────────┐    │
│            ▼                 ▼                       ▼    │
│      prediction.py    url_features.py        database.py  │
│      (ML inference)   (URL analysis)         (SQLite)     │
│            │                                              │
│            ▼                                              │
│      feature_extraction.py                               │
│      ┌──────────────────────┐                            │
│      │  preprocessing.py    │                            │
│      │  (TF-IDF transform)  │                            │
│      └──────────────────────┘                            │
│            │                                              │
│            ▼                                              │
│    ┌───────────────────┐                                  │
│    │  models/           │                                  │
│    │  classifier.joblib │                                  │
│    │  vectorizer.joblib │                                  │
│    └───────────────────┘                                  │
└─────────────────────────────────────────────────────────┘
                     │
                     ▼  (offline — not at runtime)
┌─────────────────────────────────────────────────────────┐
│                   TRAINING PIPELINE (retrain.py)          │
│                                                           │
│  data_loader.py → preprocessing.py → feature_extraction  │
│  → model_training.py → save models/ artefacts            │
│                                                           │
│  Datasets:                                                │
│  datasets/SMSSpamCollection         (original UCI)        │
│  datasets/modern_sms_dataset.csv    (synthetic supp.)     │
└─────────────────────────────────────────────────────────┘
```

---

## Module Responsibilities

### app.py
- Flask application factory
- Route definitions (page routes + API routes)
- Input validation and error handling
- Model loaded once at startup via `prediction.load_model()`

### config.py
- All configurable constants in one place
- Dataset paths, model paths, TF-IDF settings
- Trusted domain list, URL shortener list
- History enable/disable flag

### src/data_loader.py
- Loads UCI SMSSpamCollection (tab-separated)
- Loads modern_sms_dataset.csv (supplementary)
- Validates schemas, normalises labels, removes duplicates
- Merges datasets and reports class distribution
- Provides `get_dataset_stats()` for the API

### src/preprocessing.py
- `preprocess_text()` — shared function used identically during training and prediction
- Lower-cases, URL-tokenises, normalises, removes stop-words
- `extract_urls_from_message()` — raw URL list extraction

### src/url_features.py
- `extract_url_features()` — 10 structural URL features
- Pure syntactic analysis — no network requests
- `get_url_feature_vector()` — numeric vector for model input
- Uses `urllib.parse` for hostname extraction

### src/feature_extraction.py
- `build_vectorizer()` — creates TF-IDF vectorizer
- `build_feature_matrix()` — combines TF-IDF + URL features into sparse matrix
- `build_single_feature_vector()` — for inference

### src/model_training.py
- Trains MultinomialNB, LogisticRegression, Calibrated SVM
- Stratified train/test split (80/20, seed=42)
- Selects best model by macro F1-score
- Saves artefacts to `models/`

### src/prediction.py
- Loads model artefacts once
- `predict()` — builds features, runs inference, returns full result dict
- Generates human-readable explanation from features
- Combines model output with URL analysis

### database/database.py
- SQLite for analysis history
- Stores label, confidence, URL count, timestamp (not message text)
- `record_analysis()`, `get_history()`, `clear_history()`

---

## Data Flow for Prediction

```
User submits message
        │
        ▼
Flask /predict route
        │
        ├─→ Input validation (empty, too long, non-JSON)
        │
        ├─→ url_features.extract_url_features(message)
        │       │
        │       └─→ Returns 10 URL features dict
        │
        ├─→ feature_extraction.build_single_feature_vector(message, vectorizer)
        │       │
        │       ├─→ preprocessing.preprocess_text(message)
        │       │       └─→ cleaned text
        │       ├─→ vectorizer.transform(cleaned_text)
        │       │       └─→ TF-IDF sparse matrix (1 × 8000)
        │       ├─→ url_features.get_url_feature_vector(url_feats)
        │       │       └─→ numeric vector (1 × 10)
        │       └─→ scipy.hstack([tfidf, url_vec])
        │               └─→ combined matrix (1 × 8010)
        │
        ├─→ classifier.predict(combined_matrix)
        │       └─→ integer class index → "ham"/"spam"/"phishing"
        │
        ├─→ classifier.predict_proba() → confidence
        │
        ├─→ _build_explanation(prediction, url_features, confidence)
        │
        └─→ return JSON response
                │
                └─→ database.record_analysis(label, confidence, ...)
```

---

## Feature Vector Composition

```
[ TF-IDF features (up to 8000) | URL feature vector (10) ]

URL feature order (must be identical during training and inference):
  Index 0: has_url              (0/1)
  Index 1: url_has_ip           (0/1)
  Index 2: url_shortener        (0/1)
  Index 3: url_suspicious_chars (0/1)
  Index 4: url_length_norm      (float, 0-1)
  Index 5: trusted_domain       (0/1)
  Index 6: suspicious_subdomain (0/1)
  Index 7: punycode_domain      (0/1)
  Index 8: multiple_urls        (0/1)
  Index 9: suspicious_scheme    (0/1)
```

---

## Model Selection Rationale

The best model is selected by **macro F1-score**, which:
- Weights all three classes equally
- Penalises poor performance on minority classes (phishing)
- Is more appropriate than accuracy for imbalanced datasets

Accuracy alone would reward the model for predicting ham/spam correctly
while ignoring phishing misclassification.

---

## Important Design Decisions

1. **URL analysis is supporting evidence only** — URL features are appended to the feature matrix and learned by the model. The model is not forced to predict phishing because a URL is present.

2. **Trusted domain matching uses suffix checking** — `amazon.com.evil.net` does NOT match `amazon.com`. Substring matching is explicitly avoided.

3. **Same preprocessing for training and inference** — `preprocess_text()` is called from one module and used in both paths.

4. **Model not trained at Flask startup** — `retrain.py` must be run separately. Flask loads saved artefacts only.

5. **No external network requests** — The application never visits, resolves or follows URLs.

6. **SQLite stores no message text** — Privacy is preserved by storing only metadata.
