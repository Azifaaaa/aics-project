# CipherShield — Viva Questions and Answers

## Dataset and Data Preprocessing

**Q1. What dataset did you use?**  
We used two datasets. The primary dataset is the UCI SMS Spam Collection, a publicly available tab-separated dataset with approximately 5,572 messages labelled ham or spam. The secondary dataset is a manually created supplementary dataset called modern_sms_dataset.csv containing synthetic modern Indian SMS examples labelled ham, spam or phishing.

**Q2. Why did you need a supplementary dataset?**  
The original UCI dataset is from 2012 and contains no phishing examples. Modern phishing attacks — such as fake KYC requests, UPI scams and courier delivery fraud — are not represented. We created a supplementary synthetic dataset with realistic examples of these modern attack types to support a three-class model.

**Q3. How did you handle duplicate messages in the dataset?**  
We used pandas `drop_duplicates()` on the message column, keeping the first occurrence. We also performed cross-dataset deduplication after merging both sources to prevent the same message from appearing in both training and test sets.

**Q4. Why is data leakage a concern in this project?**  
Data leakage occurs when the test set contains information that the model has already seen during training. This can happen if duplicates exist across the train/test split, or if preprocessing steps like TF-IDF vectorizer fitting are applied to the entire dataset before splitting. We fit the vectorizer only on the training portion.

**Q5. What is a stratified train/test split?**  
In a stratified split, the class proportions in the training and test sets match the original dataset proportions. This is important for imbalanced datasets like ours where ham is the dominant class. Without stratification, the test set might not contain any phishing examples.

---

## TF-IDF

**Q6. What is TF-IDF and why did you use it?**  
TF-IDF stands for Term Frequency-Inverse Document Frequency. It converts text into a numeric matrix where each word's weight reflects how frequently it appears in a message (TF) but how rarely it appears across all messages (IDF). Common words like "the" get low weights, while distinctive words like "OTP" or "KYC" get high weights. We used it because it captures vocabulary patterns that distinguish ham from spam from phishing without requiring a neural language model.

**Q7. What is sublinear TF and why did you enable it?**  
Without sublinear scaling, a word appearing 100 times has 100x the weight of a word appearing once. This is usually unrealistic. Sublinear TF uses log(1 + tf) instead, reducing the dominance of high-frequency terms and making feature weights more balanced.

**Q8. Why did you use bigrams (ngram_range = 1,2) in addition to unigrams?**  
Bigrams capture two-word phrases. Phrases like "click here", "verify now", "account suspended" or "share OTP" are more informative together than their individual words. Bigrams improve classification accuracy for short, pattern-rich texts like SMS.

**Q9. What does max_features = 8000 mean?**  
Only the top 8,000 most informative terms (by TF-IDF score across the corpus) are retained. This limits memory and computation while keeping the most relevant vocabulary.

---

## Machine Learning Algorithms

**Q10. Why did you choose Naive Bayes?**  
Multinomial Naive Bayes is a classic baseline for text classification. It works well with TF-IDF features, is fast to train, requires little data and handles high-dimensional sparse matrices efficiently. It is widely used for spam filtering research.

**Q11. What assumption does Naive Bayes make and why is it called "naive"?**  
Naive Bayes assumes that all features (words) are conditionally independent given the class label. This is "naive" because word occurrences are clearly not independent in natural language. Despite this simplification, it often works surprisingly well for text classification.

**Q12. Why did you also train Logistic Regression?**  
Logistic Regression is a discriminative classifier that learns decision boundaries directly. It does not assume feature independence, handles correlated features better than Naive Bayes and usually achieves higher accuracy on text classification tasks when sufficient training data is available.

**Q13. Why did you use a Calibrated SVM instead of a plain SVM?**  
LinearSVC does not natively output probability estimates. We wrapped it with scikit-learn's CalibratedClassifierCV using isotonic or sigmoid calibration to obtain probability scores. This was necessary to report confidence values in the application.

**Q14. How did you select the best model?**  
We selected based on macro F1-score, which averages the F1-score across all three classes equally. This penalises models that perform poorly on the phishing class, which is the most dangerous to miss. We did not select based on accuracy alone because accuracy can be misleadingly high when one class dominates.

---

## Phishing and Cybersecurity

**Q15. What is phishing?**  
Phishing is a social engineering attack where the attacker impersonates a trusted entity — such as a bank, government body, delivery service or technology company — to deceive the victim into revealing sensitive information such as passwords, OTPs, credit card numbers or Aadhaar/PAN details.

**Q16. How is phishing different from spam?**  
Spam is unsolicited bulk communication, typically promotional or advertising in nature. It is annoying but rarely dangerous by itself. Phishing is targeted deception with the intent to steal. Spam may promote a real product; phishing impersonates a trusted entity to cause financial or identity harm.

**Q17. Can a message be both spam and phishing?**  
Yes. A message offering a fake lottery prize and asking for bank details to claim it is both unsolicited (spam-like) and deceptive (phishing). In practice, the boundary can be fuzzy. Our model classifies each message into one primary category based on the strongest detected pattern.

**Q18. Why is URL analysis important for phishing detection?**  
Phishing attacks frequently use deceptive URLs — either typosquatted domains (sbi-login.test), suspicious subdomains (sbi.co.in.malicious.com), IP-based links (http://203.0.113.45/login), URL shorteners (bit.ly/abc) or punycode domains. These structural features are strong indicators of phishing intent and complement text-based classification.

**Q19. What is a misleading subdomain?**  
A misleading subdomain places a trusted brand name as a prefix before an untrusted domain. For example: `sbi.co.in.verify-kyc.test` — the hostname after all dots is `test`, not `sbi.co.in`. The browser resolves this to `verify-kyc.test`, not to the real SBI website. Victims unfamiliar with DNS often mistake the brand name in the URL for a trusted source.

**Q20. What is a punycode or homograph attack?**  
Punycode (ACE encoding, `xn--`) is used to represent international characters in domain names. An attacker can register a domain like `xn--pple-43d.com` which renders as `аpple.com` in some browsers — using a Cyrillic "а" that looks identical to the Latin "a". This is called a homograph attack.

---

## Model Evaluation

**Q21. What is precision?**  
Precision = TP / (TP + FP). Of all messages the model predicted as phishing, what fraction were actually phishing? High precision means few false alarms.

**Q22. What is recall?**  
Recall = TP / (TP + FN). Of all actual phishing messages, what fraction did the model correctly detect? High recall means few phishing messages were missed. For phishing detection, recall is especially important — missing a phishing message is dangerous.

**Q23. What is F1-score?**  
F1 = 2 × (Precision × Recall) / (Precision + Recall). It is the harmonic mean of precision and recall. It balances both metrics and is useful when you care about both false positives and false negatives.

**Q24. What is macro F1-score?**  
Macro F1 averages the F1-score across all classes without weighting by class size. This gives equal importance to phishing, spam and ham performance, even if phishing has fewer samples.

**Q25. What is a false positive in this context?**  
A false positive is when the model classifies a legitimate message (ham) as spam or phishing. This is problematic because users may distrust legitimate bank notifications or fail to act on real security alerts.

**Q26. What is a false negative?**  
A false negative is when the model classifies a phishing message as ham or spam. This is dangerous — the user may interact with the phishing content, share OTPs or visit malicious links.

**Q27. What is overfitting?**  
Overfitting occurs when a model learns the training data too precisely, including noise, and fails to generalise to unseen messages. We prevent this with a held-out test set, min_df filtering in TF-IDF and regularisation in Logistic Regression and SVM.

---

## System Design

**Q28. How does Flask communicate with JavaScript?**  
The frontend JavaScript sends a POST request to `/predict` with a JSON body `{"message": "text"}`. Flask parses the JSON, runs the prediction and returns a JSON response. JavaScript receives the response and updates the DOM to display the result. This is a standard REST API pattern using the fetch() API.

**Q29. Why is the model not trained every time Flask starts?**  
Training is computationally expensive and would significantly delay application startup. The model is trained once using `retrain.py` and saved as joblib files. Flask loads the saved artefacts once at startup. This is standard production ML deployment practice.

**Q30. Why do you use SQLite and not MySQL or PostgreSQL?**  
SQLite is a serverless, file-based database that requires no installation or configuration. It is ideal for a local academic project where simplicity matters. MySQL or PostgreSQL would add unnecessary setup complexity without meaningful benefit for a single-user local application.

**Q31. What would you improve if you had more time?**  
1. Collect more real-world labelled phishing examples to improve phishing recall.
2. Add a transformer-based model (BERT or RoBERTa) for better contextual understanding.
3. Integrate with a real-time URL reputation service (VirusTotal API) for production use.
4. Add multi-language support for regional Indian languages beyond Hinglish.
5. Implement active learning to allow users to flag incorrect predictions and retrain.

**Q32. What are the limitations of your project?**  
1. Phishing class is trained on synthetic data only — real-world labelled phishing SMS is difficult to obtain ethically.
2. No real-time URL analysis — we cannot detect newly registered phishing domains.
3. The model cannot understand language context, sarcasm or intent.
4. Short messages without distinctive keywords may be misclassified.
5. A trusted domain in the URL does not guarantee safety — phishing can use subdomains of legitimate services.
