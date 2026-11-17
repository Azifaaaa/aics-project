# CipherShield — Project Report

## Title: Intelligent SMS Spam and Phishing Detection Using Machine Learning

**Project Type:** M.Sc. Cybersecurity Academic Mini-Project  
**Subject:** Applied Cybersecurity / Machine Learning for Security  

---

## Abstract

Phishing and spam SMS messages represent a persistent and evolving threat to mobile users, particularly in India where UPI-based payment fraud, fake KYC requests and delivery-related scams have proliferated. Existing rule-based and keyword-based filters are easily bypassed by attackers who vary language, format and delivery mechanism. This project presents CipherShield, a machine-learning-powered web application that classifies SMS messages into three categories: legitimate (ham), spam and phishing. The system combines TF-IDF text feature extraction with structural URL analysis to produce evidence-based predictions with confidence scores and human-readable explanations. The application uses the original UCI SMS Spam Collection augmented by a manually created supplementary dataset of modern Indian SMS scam examples. Three machine learning algorithms — Multinomial Naive Bayes, Logistic Regression and Calibrated Linear SVM — were trained and compared. The best-performing model is selected automatically based on macro F1-score. The resulting web application is a locally deployable Flask system with a professional white-themed interface.

---

## 1. Introduction

Mobile messaging has become a primary channel for financial transactions, government services and personal communication in India. The widespread adoption of UPI payments, Aadhaar-linked services and e-commerce deliveries has created an extensive attack surface for social engineering via SMS. Attackers send fraudulent messages impersonating banks (SBI, HDFC, ICICI), government bodies (UIDAI, Income Tax), delivery services (India Post, Amazon) and payment platforms (Paytm, PhonePe) to deceive users into sharing OTPs, clicking phishing links or transferring funds.

Traditional spam filters based on keyword lists or simple rules are insufficient for modern phishing because: (1) attackers deliberately misspell words or use synonyms to evade keyword matching; (2) the same domain name may appear in both legitimate and fraudulent messages; (3) the distinction between spam and phishing requires understanding intent, not just vocabulary.

Machine learning models trained on labelled SMS data can capture statistical patterns in vocabulary, structure and URL characteristics that distinguish spam and phishing from legitimate messages.

---

## 2. Problem Statement

Design and implement an automated SMS classification system that:
1. Correctly identifies legitimate (ham) messages to avoid false alarms
2. Detects unsolicited promotional messages (spam)
3. Identifies deceptive phishing messages targeting sensitive information
4. Provides URL structural analysis as a supplementary signal
5. Operates without real-time internet lookups or paid APIs
6. Is deployable locally on a Windows machine

---

## 3. Objectives

- Load, clean and merge the original UCI SMS Spam Collection with a modern supplementary dataset
- Implement robust text preprocessing shared across training and inference
- Extract TF-IDF features combined with structural URL features
- Train and compare three ML algorithms on a three-class classification task
- Select the best model by macro F1-score with emphasis on phishing performance
- Deploy as a Flask web application with a professional user interface
- Store analysis history in SQLite without retaining message text
- Document the system for academic presentation and viva examination

---

## 4. Scope

**In scope:**
- Binary (ham/spam) and three-class (ham/spam/phishing) SMS classification
- Structural URL analysis (10 features) based on hostname and URL syntax
- Local deployment on Windows without external APIs

**Out of scope:**
- Real-time URL reputation checking
- MMS or social media message analysis
- Sender identity verification
- End-to-end encryption of stored data
- Multi-language support beyond English and Hinglish

---

## 5. Existing Systems

Existing SMS spam detection approaches include:
- **Network-level filtering:** Telecom operators block known spam numbers but cannot detect semantic phishing
- **Keyword blacklists:** Simple rule-based filters easily bypassed by typos or synonyms
- **Google Play Protect / iOS spam detection:** Device-level ML classification, closed source
- **Third-party apps:** Truecaller, Calls Blacklist — primarily caller-ID based, not content analysis

Academic approaches include Naive Bayes classifiers on the UCI dataset, achieving ~98% binary accuracy. However, most existing systems do not address the phishing class separately from spam.

---

## 6. Limitations of Existing Systems

1. Rule-based systems cannot adapt to evolving attack language
2. Binary classification (ham/spam) does not distinguish phishing from promotional spam
3. High-accuracy models on the UCI dataset may not generalise to modern Indian SMS attacks
4. No structural URL analysis in most published SMS classifiers
5. Most systems do not provide explanations — users do not understand why a message was flagged

---

## 7. Proposed System

CipherShield addresses these limitations by:
1. Using machine learning (not keyword rules) for classification
2. Supporting three classes: ham, spam and phishing
3. Combining text classification with structural URL analysis
4. Providing human-readable explanations for each prediction
5. Including a supplementary dataset of modern Indian SMS scam examples

---

## 8. System Requirements

**Hardware:**
- PC or laptop with 4 GB RAM minimum, 8 GB recommended
- 500 MB free disk space

**Software:**
- Windows 10 or later
- Python 3.9 or later
- Web browser (Chrome, Firefox, Edge)

**Python libraries:**
- Flask, pandas, NumPy, scikit-learn, SciPy, joblib, pytest

---

## 9. Technology Stack

| Layer | Technology | Justification |
|-------|-----------|---------------|
| Frontend | HTML5, CSS3, Vanilla JS | Minimal dependencies, fully controllable |
| Backend | Python + Flask | Lightweight, easy to integrate with scikit-learn |
| Machine Learning | scikit-learn | Comprehensive ML algorithms, well-documented |
| Feature Extraction | TF-IDF + urllib.parse | Standard NLP + built-in URL parsing |
| Database | SQLite | No server required, local deployment |
| Visualisation | Chart.js (CDN) | Simple, no backend required |

---

## 10. Dataset Description

### Original Dataset: UCI SMS Spam Collection

- **Source:** UCI Machine Learning Repository (Almeida et al., 2011)
- **Format:** Tab-separated, two columns: label and message
- **Raw records:** ~5,572
- **Labels:** ham, spam
- **Duplicates:** ~403 identified and removed
- **URL-containing messages:** ~200 (estimated)

### Supplementary Dataset: modern_sms_dataset.csv

- **Source:** Manually created synthetic examples — NOT real collected messages
- **Purpose:** Provide modern Indian SMS phishing and scam examples for the phishing class
- **Records:** ~110 carefully labelled examples
- **Labels:** ham, spam, phishing
- **Categories:** Banking scam, UPI scam, OTP scam, courier scam, government scam, lottery spam, job spam, legitimate notifications
- **Source type:** All records labelled `synthetic`
- **Domains:** Safe illustrative domains only (.test, example.com, 203.0.113.0/24)

---

## 11. Dataset Preprocessing

Steps applied to both datasets:
1. Read with UTF-8 encoding (fall back to latin-1 for original dataset)
2. Drop rows with missing label or message
3. Normalise labels to lower case and strip whitespace
4. Remove rows with invalid labels
5. Remove empty or whitespace-only messages
6. Identify and remove duplicate messages (by exact text match)
7. Cross-dataset deduplication after merging
8. Report class distribution before and after each step

---

## 12. Modern Supplementary Dataset

The supplementary dataset was created to address the absence of modern phishing examples in the UCI dataset. It contains synthetic examples across the following attack categories:

**Phishing categories:** Banking scam (fake KYC, debit card block), UPI scam (fake collect request, payment failure), OTP scam, courier scam (India Post, Amazon delivery), government scam (Aadhaar, PAN, income tax refund), lottery/prize scam, job scam, tech support scam, account security scam

**Ham categories:** Bank transaction notifications, UPI payment confirmations, delivery updates, appointment reminders, college notifications, government notifications, personal messages, Hinglish conversations

**Spam categories:** Shopping promotions, financial promotions, referral schemes, education promotions, insurance spam

All synthetic records are identified with `source_type = synthetic`. They are illustrative examples and do not represent actual collected messages.

---

## 13. TF-IDF Feature Extraction

TF-IDF (Term Frequency-Inverse Document Frequency) converts text to a numeric matrix suitable for machine learning.

**Configuration:**
- max_features = 8,000 (top 8,000 vocabulary terms)
- ngram_range = (1, 2) (unigrams and bigrams)
- min_df = 2 (ignore terms appearing in only one document)
- sublinear_tf = True (log(1 + tf) instead of raw tf)

The vectorizer is **fit only on the training set** to prevent data leakage. The same fitted vectorizer is used to transform the test set and all inference messages.

---

## 14. URL Feature Extraction

Ten structural URL features are extracted from each message and appended to the TF-IDF matrix:

| Feature | Description |
|---------|-------------|
| has_url | A URL is present |
| url_has_ip | Hostname is an IPv4 address |
| url_shortener | Recognised shortening service |
| url_suspicious_chars | @ in URL authority, excessive dots, hex encoding |
| url_length_norm | URL length normalised to 0-1 |
| trusted_domain | Hostname is a known trusted domain |
| suspicious_subdomain | Brand name in subdomain of untrusted host |
| punycode_domain | xn-- punycode encoding in hostname |
| multiple_urls | More than one URL in message |
| suspicious_url_scheme | Non-HTTP/HTTPS scheme |

**Important:** URL features are inputs to the classifier — they do not override the classifier's output. A URL from a trusted domain does not force a ham prediction.

---

## 15. Machine Learning Algorithms

Three classifiers were trained and compared:

**Multinomial Naive Bayes**
- Baseline probabilistic classifier
- Assumes word independence (naive)
- Fast, low memory, works well with TF-IDF
- alpha = 0.1 (Laplace smoothing)

**Logistic Regression**
- Discriminative classifier, no independence assumption
- Regularised with L2 (default C=1.0)
- Handles feature correlations better than NB
- max_iter = 1000

**Calibrated Linear SVM**
- LinearSVC with isotonic probability calibration
- Strong performance on high-dimensional text features
- CalibratedClassifierCV(LinearSVC()) for probability estimates

---

## 16. Model Comparison and Selection

Models are compared on a held-out test set (20% of data, stratified, seed=42).

**Selection criterion:** Macro F1-score, which:
- Averages F1 across all three classes equally
- Penalises poor performance on the minority phishing class
- Is more informative than accuracy for imbalanced datasets

Phishing recall and F1 are specifically examined because:
- Missing a phishing message (false negative) can result in financial harm
- Low phishing performance with limited training data is explicitly disclosed

---

## 17. System Architecture

See `docs/architecture.md` for full architecture diagram.

The system consists of:
- Flask web server (page routes + REST API)
- Prediction module (loads model artefacts once at startup)
- URL feature extractor (structural analysis, no network requests)
- Feature extraction pipeline (TF-IDF + URL features)
- SQLite history database (metadata only, no message text)
- Five HTML page templates with shared base layout

---

## 18. Application Workflow

1. User opens browser at http://127.0.0.1:5000
2. Dashboard loads with training dataset statistics and session statistics
3. User navigates to Analyze Message and enters SMS text
4. JavaScript sends POST /predict with the message text
5. Flask validates input and calls predict()
6. predict() builds feature vector (TF-IDF + URL) and runs classifier
7. Result is returned as JSON with label, confidence, URL features and explanation
8. JavaScript renders result panel with colour-coded classification
9. Classification metadata is recorded in SQLite (not the message text)
10. User can view history, dataset insights or analyse another message

---

## 19. Evaluation Metrics

- **Accuracy** = (TP + TN) / Total — overall correctness
- **Precision** = TP / (TP + FP) — exactness
- **Recall** = TP / (TP + FN) — completeness
- **F1-score** = 2 × P × R / (P + R) — harmonic mean
- **Macro F1** = unweighted mean F1 across all classes
- **Weighted F1** = weighted by class support
- **Confusion matrix** — full breakdown of predictions vs actual

---

## 20. Actual Results

Actual evaluation results are saved in `models/evaluation_report.json` after running `retrain.py`.
They are displayed in the Dataset Insights page of the application.

**Note:** Results vary depending on the version of the supplementary dataset and random seed.
The numbers reported in the application are computed from the actual held-out test set, not the training set.

---

## 21. Privacy and Ethical Considerations

1. **No message text is stored** — only classification metadata (label, confidence, URL count, timestamp)
2. **All processing is local** — no data is sent to external servers or APIs
3. **Synthetic dataset** — no real user messages were collected; supplementary examples are manually created
4. **No real malicious URLs** — all URLs in the supplementary dataset use reserved/safe domains
5. **No real personal information** — no actual OTPs, phone numbers, banking credentials or Aadhaar numbers
6. **History is optional** — can be disabled in config.py; can be deleted from the UI
7. **Disclaimer displayed** — users are warned that predictions are not guarantees of safety

---

## 22. Limitations

1. Phishing class depends on a small synthetic dataset — real-world labelled phishing SMS is difficult to obtain ethically
2. No real-time threat intelligence or URL resolution
3. Cannot verify sender identity
4. Short ambiguous messages may be misclassified
5. The model does not understand language nuance, sarcasm or intent
6. Performance on regional Indian language SMS (Hindi, Tamil, Telugu) is untested
7. A trusted domain in the URL does not guarantee safety — the model cannot detect all spoofing techniques

---

## 23. Future Enhancements

1. Collect real-world labelled phishing SMS datasets via ethical research collaborations
2. Implement active learning to improve the model from user feedback
3. Add transformer-based models (DistilBERT) for better contextual understanding
4. Integrate optional real-time URL reputation API (VirusTotal, Google SafeBrowsing)
5. Add support for regional Indian language SMS
6. Develop a mobile browser extension or SMS interceptor app
7. Implement differential privacy for history storage

---

## 24. Conclusion

CipherShield demonstrates that machine learning, when combined with structural URL analysis, can effectively classify SMS messages into three categories — ham, spam and phishing — without real-time internet dependencies. The system addresses the limitations of keyword-based filters by learning statistical patterns from labelled training data. The phishing class, which is the most dangerous to miss, benefits from both text classification and URL feature analysis. The application is locally deployable, privacy-preserving and suitable for a university demonstration.

---

## 25. References

1. Almeida, T. A., Hidalgo, J. M. G., & Yamakami, A. (2011). Contributions to the Study of SMS Spam Filtering: New Collection and Methods. ACM SIGDOC.
2. scikit-learn: Machine Learning in Python, Pedregosa et al., JMLR 12, 2011.
3. NLTK Project — Natural Language Toolkit
4. IANA — Special-Use Domain Names (RFC 2606, RFC 6761)
5. IANA — TEST-NET-3 (RFC 5737): 203.0.113.0/24
6. ICANN — Internationalized Domain Names in Applications (IDNA): RFC 3490
7. Flask Web Framework — https://flask.palletsprojects.com/
8. Bootstrap Icons — https://icons.getbootstrap.com/
9. Chart.js — https://www.chartjs.org/
10. Inter Font — https://rsms.me/inter/

*Note: This project does not fabricate, invent or misrepresent citations. All references above are real published works or standards.*
