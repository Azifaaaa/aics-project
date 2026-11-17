"""
CipherShield — Model Training
Trains, compares and saves the best SMS classification model.

Run directly:
    python retrain.py

This module is NOT imported by Flask at startup.
"""
import os
import sys
import json
import time
import warnings

import numpy as np
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.metrics import (
    classification_report, confusion_matrix,
    f1_score, precision_score, recall_score, accuracy_score,
)
from sklearn.preprocessing import LabelEncoder
import joblib

warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    CLASSIFIER_PATH, VECTORIZER_PATH,
    FEATURE_METADATA_PATH, EVALUATION_REPORT_PATH,
    MODELS_DIR, RANDOM_SEED, TEST_SIZE,
)
from src.data_loader import load_combined_dataset
from src.feature_extraction import build_vectorizer, build_feature_matrix, get_feature_names


# ── label encoding ────────────────────────────────────────────────────────────

LABEL_ORDER = ["ham", "spam", "phishing"]


def encode_labels(labels):
    """Map string labels to integers using LABEL_ORDER."""
    mapping = {l: i for i, l in enumerate(LABEL_ORDER)}
    return np.array([mapping[l] for l in labels])


def decode_labels(indices):
    """Map integer indices back to string labels."""
    return [LABEL_ORDER[i] for i in indices]


# ── model comparison ──────────────────────────────────────────────────────────

def build_candidate_models():
    """Return a dict of candidate classifiers."""
    return {
        "MultinomialNB": MultinomialNB(alpha=0.1),
        "LogisticRegression": LogisticRegression(
            max_iter=1000,
            C=1.0,
            solver="lbfgs",
            random_state=RANDOM_SEED,
        ),
        "LinearSVC_calibrated": CalibratedClassifierCV(
            LinearSVC(max_iter=2000, C=1.0, random_state=RANDOM_SEED),
            cv=3,
        ),
    }


def evaluate_model(clf, X_test, y_test, label_names):
    """Return a detailed evaluation dict."""
    y_pred = clf.predict(X_test)
    report = classification_report(y_test, y_pred, target_names=label_names, output_dict=True)
    cm = confusion_matrix(y_test, y_pred).tolist()
    return {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "macro_f1": float(f1_score(y_test, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_test, y_pred, average="weighted", zero_division=0)),
        "classification_report": report,
        "confusion_matrix": cm,
    }


# ── main training routine ─────────────────────────────────────────────────────

def train():
    print("\n" + "=" * 60)
    print("  CipherShield — Model Training")
    print("=" * 60)

    # 1. Load data
    df = load_combined_dataset()

    # Identify available classes
    available_labels = set(df["label"].unique())
    print(f"\n[Train] Classes present: {sorted(available_labels)}")

    if "phishing" not in available_labels:
        print("[Train] WARNING — No phishing class found. Training binary ham/spam model.")
        label_names = ["ham", "spam"]
    elif (df["label"] == "phishing").sum() < 20:
        print(
            f"[Train] WARNING — Only {(df['label'] == 'phishing').sum()} phishing samples. "
            "Phishing class metrics will be unreliable."
        )
        label_names = ["ham", "spam", "phishing"]
    else:
        label_names = ["ham", "spam", "phishing"]

    # Filter to available labels only
    df = df[df["label"].isin(label_names)].copy()
    df.reset_index(drop=True, inplace=True)

    messages = df["message"].tolist()
    y_str = df["label"].tolist()

    # Encode labels
    local_label_order = label_names
    label_map = {l: i for i, l in enumerate(local_label_order)}
    y = np.array([label_map[l] for l in y_str])

    # 2. Stratified train/test split
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        messages, y, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y
    )
    print(f"[Train] Training samples: {len(X_train_raw)}  |  Test samples: {len(X_test_raw)}")

    # 3. Feature extraction (fit ONLY on training data)
    vectorizer = build_vectorizer()
    print("[Train] Building feature matrices…")
    X_train = build_feature_matrix(X_train_raw, vectorizer, fit=True)
    X_test = build_feature_matrix(X_test_raw, vectorizer, fit=False)
    print(f"[Train] Feature matrix shape: {X_train.shape}")

    # MultinomialNB requires non-negative features; URL features are already 0-1
    # TF-IDF is always non-negative, so MNB is compatible.

    # 4. Train and compare candidates
    candidates = build_candidate_models()
    results = {}
    best_name = None
    best_macro_f1 = -1.0

    print("\n[Train] Comparing models…")
    for name, clf in candidates.items():
        t0 = time.time()
        clf.fit(X_train, y_train)
        elapsed = time.time() - t0

        eval_res = evaluate_model(clf, X_test, y_test, local_label_order)
        results[name] = eval_res
        results[name]["training_time_s"] = round(elapsed, 3)

        macro_f1 = eval_res["macro_f1"]
        phishing_f1 = (
            eval_res["classification_report"]
            .get("phishing", {})
            .get("f1-score", None)
        )

        status = f"  Macro F1={macro_f1:.4f}  Accuracy={eval_res['accuracy']:.4f}"
        if phishing_f1 is not None:
            status += f"  Phishing-F1={phishing_f1:.4f}"
        print(f"  [{name}]{status}  ({elapsed:.1f}s)")

        if macro_f1 > best_macro_f1:
            best_macro_f1 = macro_f1
            best_name = name

    print(f"\n[Train] Best model: {best_name}  (Macro F1 = {best_macro_f1:.4f})")

    # 5. Refit best model on FULL training set
    best_clf = candidates[best_name]
    best_clf.fit(X_train, y_train)   # already fitted above but ensures consistency

    # 6. Save artefacts
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(best_clf, CLASSIFIER_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    print(f"[Train] Classifier saved  -> {CLASSIFIER_PATH}")
    print(f"[Train] Vectorizer saved  -> {VECTORIZER_PATH}")

    # 7. Save feature metadata
    feature_names = get_feature_names(vectorizer)
    metadata = {
        "label_names": local_label_order,
        "label_map": label_map,
        "n_tfidf_features": X_train.shape[1] - 10,  # subtract URL features
        "n_url_features": 10,
        "n_total_features": X_train.shape[1],
        "feature_names_sample": feature_names[:20] + feature_names[-10:],
        "best_model": best_name,
        "macro_f1": best_macro_f1,
        "tfidf_settings": {
            "max_features": vectorizer.max_features,
            "ngram_range": list(vectorizer.ngram_range),
            "min_df": vectorizer.min_df,
            "sublinear_tf": vectorizer.sublinear_tf,
        },
        "train_size": len(X_train_raw),
        "test_size": len(X_test_raw),
        "random_seed": RANDOM_SEED,
    }
    with open(FEATURE_METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"[Train] Metadata saved    -> {FEATURE_METADATA_PATH}")

    # 8. Save evaluation report
    eval_report = {
        "best_model": best_name,
        "best_model_evaluation": results[best_name],
        "all_model_comparisons": results,
        "label_names": local_label_order,
        "phishing_class_available": "phishing" in local_label_order,
        "phishing_sample_count": int((df["label"] == "phishing").sum()),
    }
    with open(EVALUATION_REPORT_PATH, "w") as f:
        json.dump(eval_report, f, indent=2)
    print(f"[Train] Eval report saved -> {EVALUATION_REPORT_PATH}")

    # 9. Print final classification report
    best_eval = results[best_name]
    print("\n" + "=" * 60)
    print(f"  FINAL EVALUATION — {best_name}")
    print("=" * 60)
    print(f"  Accuracy        : {best_eval['accuracy']:.4f}")
    print(f"  Macro F1        : {best_eval['macro_f1']:.4f}")
    print(f"  Weighted F1     : {best_eval['weighted_f1']:.4f}")
    print("\n  Per-class report:")
    for label in local_label_order:
        rpt = best_eval["classification_report"].get(label, {})
        p = rpt.get("precision", 0)
        r = rpt.get("recall", 0)
        f = rpt.get("f1-score", 0)
        s = rpt.get("support", 0)
        print(f"    {label:<12} P={p:.3f}  R={r:.3f}  F1={f:.3f}  support={s}")

    print("\n  Confusion matrix (rows=actual, cols=predicted):")
    print(f"  Labels: {local_label_order}")
    for row in best_eval["confusion_matrix"]:
        print(f"    {row}")

    if "phishing" in local_label_order:
        ph = best_eval["classification_report"].get("phishing", {})
        ph_recall = ph.get("recall", 0)
        ph_support = ph.get("support", 0)
        if ph_recall < 0.5 and ph_support < 50:
            print(
                "\n  ⚠ PHISHING RECALL IS LOW. This is expected with limited phishing data.\n"
                "  Add more phishing examples to modern_sms_dataset.csv and retrain."
            )

    print("\n[Train] Training complete.\n")
    return best_clf, vectorizer, metadata
