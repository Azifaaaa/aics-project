# CipherShield — Member Contributions

## Project: Intelligent SMS Spam and Phishing Detection Using Machine Learning

---

## Member 1 — Machine Learning and Cybersecurity

### Primary Responsibilities

**Dataset Work**
- Downloaded and inspected the UCI SMS Spam Collection
- Analysed raw dataset statistics (record counts, duplicate counts, class distribution)
- Created `modern_sms_dataset.csv` — supplementary synthetic dataset with 100+ phishing, spam and ham examples
- Wrote `datasets/dataset_review_guide.md` explaining labelling criteria
- Defined and documented the three-class label schema

**Preprocessing Pipeline**
- Implemented `src/preprocessing.py` — shared preprocessing function for training and inference
- Selected and justified the minimal stop-word list
- Implemented URL tokenisation and phone number tokenisation
- Tested preprocessing on sample messages manually

**TF-IDF Configuration**
- Selected and justified TF-IDF parameters (max_features=8000, ngram_range=(1,2), sublinear_tf=True)
- Wrote `src/feature_extraction.py` combining TF-IDF with URL features using SciPy sparse matrices

**URL Feature Analysis**
- Implemented all 10 URL features in `src/url_features.py`
- Developed trusted domain suffix-matching logic (not substring matching)
- Implemented IP detection, punycode detection, URL shortener detection, misleading subdomain detection
- Wrote unit tests for URL feature extraction in `tests/test_url_features.py`

**Model Training**
- Implemented `src/model_training.py` with three candidate algorithms
- Configured stratified train/test split with fixed random seed
- Selected best model by macro F1-score
- Saved artefacts using joblib
- Generated `models/evaluation_report.json`

**Model Evaluation**
- Generated classification report, confusion matrix, per-class F1 scores
- Analysed phishing recall specifically
- Documented limitations of phishing class with limited training data

**Academic Documentation**
- Wrote `docs/viva_questions.md` with 32 questions and answers
- Wrote ML sections of `docs/project_report.md`
- Wrote `docs/architecture.md`

---

## Member 2 — Web Development and Integration

### Primary Responsibilities

**Frontend Design**
- Designed the white-themed professional UI in `static/css/style.css`
- Implemented responsive sidebar navigation layout
- Created all five HTML templates (dashboard, analyze, history, insights, about)
- Designed and implemented result panel with colour-coded classification badges
- Created URL indicator components
- Implemented character counter, example message loader

**JavaScript**
- Wrote `static/js/analyze.js` — full prediction workflow, result rendering, error handling
- Wrote `static/js/dashboard.js` — dashboard statistics loading, recent activity
- Wrote `static/js/charts.js` — Chart.js integration for Dataset Insights page
- Implemented HTML escaping and safe DOM manipulation throughout

**Flask Backend**
- Wrote `app.py` with all route handlers
- Implemented input validation, length limits, JSON error handling
- Implemented proper HTTP status codes for all error conditions
- Connected frontend to prediction, stats and history APIs

**SQLite Integration**
- Implemented `database/database.py` with parameterised SQL queries
- Designed privacy-preserving schema (no message text stored)
- Implemented history recording, retrieval and clearing

**Testing**
- Wrote `tests/test_routes.py` for Flask route and API testing
- Wrote `tests/test_data_loader.py` for dataset loading tests
- Ran full test suite and verified all tests pass

**Documentation**
- Wrote `README.md` with full installation, usage and troubleshooting guide
- Wrote `docs/testing_report.md`
- Wrote web development sections of `docs/project_report.md`

---

## Shared Responsibilities

Both members collaborated on:
- Overall project design decisions
- Dataset labelling review for the supplementary dataset
- Integrating the ML prediction module with the Flask API
- Testing the complete application end-to-end
- Understanding all project components for the viva examination

---

*Both members are expected to understand the entire project — not just their individual contributions.*
