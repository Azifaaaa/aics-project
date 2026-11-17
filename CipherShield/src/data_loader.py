"""
CipherShield — Data Loader
Loads and validates both the original UCI SMSSpamCollection and the
modern supplementary SMS dataset, then merges them cleanly.
"""
import os
import sys
import pandas as pd

# Allow running this module directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ORIGINAL_DATASET, SUPPLEMENTARY_DATASET


# ── helpers ───────────────────────────────────────────────────────────────────

def _normalise_label(label: str) -> str:
    """Lower-case and strip a label string."""
    return str(label).strip().lower()


def _report_distribution(df: pd.DataFrame, title: str) -> None:
    dist = df["label"].value_counts()
    total = len(df)
    print(f"\n{'=' * 50}")
    print(f"  {title}")
    print(f"{'=' * 50}")
    print(f"  Total records : {total}")
    for label, count in dist.items():
        pct = 100 * count / total if total else 0
        print(f"  {label:<12}: {count:>5}  ({pct:.1f} %)")
    print(f"{'=' * 50}")


# ── original dataset ──────────────────────────────────────────────────────────

def load_original_dataset(path: str = ORIGINAL_DATASET) -> pd.DataFrame:
    """
    Load the UCI SMSSpamCollection (tab-separated, no header).
    Returns a DataFrame with columns: message, label, source.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Original dataset not found at: {path}\n"
            "Please place the SMSSpamCollection file in the datasets/ folder."
        )

    print(f"\n[DataLoader] Reading original dataset: {path}")
    try:
        df = pd.read_csv(
            path,
            sep="\t",
            header=None,
            names=["label", "message"],
            encoding="utf-8",
            on_bad_lines="skip",
        )
    except UnicodeDecodeError:
        df = pd.read_csv(
            path,
            sep="\t",
            header=None,
            names=["label", "message"],
            encoding="latin-1",
            on_bad_lines="skip",
        )

    print(f"[DataLoader] Raw rows read: {len(df)}")

    # Drop rows where either column is completely missing
    df.dropna(subset=["label", "message"], inplace=True)

    # Normalise labels
    df["label"] = df["label"].apply(_normalise_label)

    # Keep only recognised labels
    valid_labels = {"ham", "spam"}
    invalid = df[~df["label"].isin(valid_labels)]
    if len(invalid):
        print(f"[DataLoader] WARNING — {len(invalid)} rows with unrecognised labels dropped.")
    df = df[df["label"].isin(valid_labels)].copy()

    # Remove empty / whitespace-only messages
    df["message"] = df["message"].astype(str).str.strip()
    empty_count = (df["message"] == "").sum()
    if empty_count:
        print(f"[DataLoader] Dropping {empty_count} empty-message rows.")
    df = df[df["message"] != ""].copy()

    # Identify and report duplicates (keep first)
    dup_count = df.duplicated(subset=["message"]).sum()
    print(f"[DataLoader] Duplicate messages identified: {dup_count}")
    df.drop_duplicates(subset=["message"], keep="first", inplace=True)

    df["source"] = "original_dataset"
    df["category"] = df["label"].apply(
        lambda l: "legitimate" if l == "ham" else "spam_general"
    )
    df["contains_url"] = df["message"].str.contains(
        r"https?://|www\.", case=False, regex=True
    )
    df["source_type"] = "original_dataset"

    _report_distribution(df, "Original UCI Dataset (after cleaning)")
    return df[["message", "label", "category", "contains_url", "source_type"]].reset_index(drop=True)


# ── supplementary dataset ─────────────────────────────────────────────────────

REQUIRED_SUPP_COLS = {"message", "label", "category", "contains_url", "source_type"}


def load_supplementary_dataset(path: str = SUPPLEMENTARY_DATASET) -> pd.DataFrame:
    """
    Load the modern_sms_dataset.csv supplementary dataset.
    Returns a cleaned DataFrame with columns matching the original loader output.
    """
    if not os.path.exists(path):
        print(f"[DataLoader] Supplementary dataset not found at: {path}")
        print("[DataLoader] Continuing without supplementary data.")
        return pd.DataFrame(columns=["message", "label", "category", "contains_url", "source_type"])

    print(f"\n[DataLoader] Reading supplementary dataset: {path}")
    df = pd.read_csv(path, encoding="utf-8")
    print(f"[DataLoader] Raw rows read: {len(df)}")

    # Schema validation
    missing_cols = REQUIRED_SUPP_COLS - set(df.columns)
    if missing_cols:
        raise ValueError(
            f"Supplementary dataset is missing required columns: {missing_cols}"
        )

    df.dropna(subset=["message", "label"], inplace=True)
    df["label"] = df["label"].apply(_normalise_label)

    valid_labels = {"ham", "spam", "phishing"}
    invalid = df[~df["label"].isin(valid_labels)]
    if len(invalid):
        print(f"[DataLoader] WARNING — {len(invalid)} supplementary rows with invalid labels dropped.")
    df = df[df["label"].isin(valid_labels)].copy()

    df["message"] = df["message"].astype(str).str.strip()
    df = df[df["message"] != ""].copy()

    dup_count = df.duplicated(subset=["message"]).sum()
    print(f"[DataLoader] Duplicate supplementary messages: {dup_count}")
    df.drop_duplicates(subset=["message"], keep="first", inplace=True)

    _report_distribution(df, "Supplementary Dataset (after cleaning)")
    return df[["message", "label", "category", "contains_url", "source_type"]].reset_index(drop=True)


# ── combined dataset ──────────────────────────────────────────────────────────

def load_combined_dataset() -> pd.DataFrame:
    """
    Load, validate and merge both datasets.
    Returns a single cleaned DataFrame ready for ML pipeline consumption.
    If the original dataset is not found, falls back to supplementary-only mode.
    """
    # Try loading original; fall back gracefully if missing
    try:
        original = load_original_dataset()
    except FileNotFoundError as exc:
        print(f"\n[DataLoader] WARNING — {exc}")
        print("[DataLoader] Training on supplementary dataset only.")
        print("[DataLoader] Place SMSSpamCollection in datasets/ for full training.")
        original = pd.DataFrame(columns=["message", "label", "category", "contains_url", "source_type"])

    supplementary = load_supplementary_dataset()

    print(f"\n[DataLoader] Original dataset records   : {len(original)}")
    print(f"[DataLoader] Supplementary dataset records: {len(supplementary)}")

    if supplementary.empty:
        combined = original.copy()
        combined["dataset_source"] = "original"
    else:
        original["dataset_source"] = "original"
        supplementary["dataset_source"] = "supplementary"
        combined = pd.concat([original, supplementary], ignore_index=True)

    # Cross-dataset deduplication
    before = len(combined)
    combined.drop_duplicates(subset=["message"], keep="first", inplace=True)
    after = len(combined)
    if before != after:
        print(f"[DataLoader] Cross-dataset duplicates removed: {before - after}")

    combined.reset_index(drop=True, inplace=True)
    _report_distribution(combined, "Combined Dataset (final)")

    phishing_count = (combined["label"] == "phishing").sum()
    if phishing_count < 50:
        print(
            f"\n[DataLoader] WARNING — Only {phishing_count} phishing samples found.\n"
            "A three-class model may have unreliable phishing performance.\n"
            "Consider adding more phishing examples to modern_sms_dataset.csv."
        )

    return combined


# ── dataset statistics (for API) ─────────────────────────────────────────────

def get_dataset_stats() -> dict:
    """Return a stats dict suitable for the /api/stats endpoint."""
    try:
        combined = load_combined_dataset()
    except Exception as exc:
        return {"error": str(exc), "available": False}

    dist = combined["label"].value_counts().to_dict()
    source_dist = combined["dataset_source"].value_counts().to_dict()
    url_count = int(combined["contains_url"].sum())

    # Per-source breakdown
    orig = combined[combined["dataset_source"] == "original"]
    supp = combined[combined["dataset_source"] == "supplementary"]

    return {
        "available": True,
        "total_records": len(combined),
        "ham": int(dist.get("ham", 0)),
        "spam": int(dist.get("spam", 0)),
        "phishing": int(dist.get("phishing", 0)),
        "url_containing": url_count,
        "original_records": len(orig),
        "supplementary_records": len(supp),
        "original_ham": int((orig["label"] == "ham").sum()),
        "original_spam": int((orig["label"] == "spam").sum()),
        "supplementary_ham": int((supp["label"] == "ham").sum()),
        "supplementary_spam": int((supp["label"] == "spam").sum()),
        "supplementary_phishing": int((supp["label"] == "phishing").sum()),
        "source_distribution": source_dist,
    }


if __name__ == "__main__":
    stats = get_dataset_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")
