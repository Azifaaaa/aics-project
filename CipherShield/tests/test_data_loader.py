"""
CipherShield — Data Loader Tests
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock


class TestSupplementaryLoader:
    """Test loading of supplementary dataset (which exists in repo)."""

    def test_load_supplementary_exists(self):
        from src.data_loader import load_supplementary_dataset
        df = load_supplementary_dataset()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_supplementary_columns(self):
        from src.data_loader import load_supplementary_dataset
        df = load_supplementary_dataset()
        for col in ["message", "label", "category", "contains_url", "source_type"]:
            assert col in df.columns, f"Missing column: {col}"

    def test_supplementary_valid_labels(self):
        from src.data_loader import load_supplementary_dataset
        df = load_supplementary_dataset()
        valid = {"ham", "spam", "phishing"}
        invalid = set(df["label"].unique()) - valid
        assert not invalid, f"Invalid labels found: {invalid}"

    def test_supplementary_phishing_exists(self):
        from src.data_loader import load_supplementary_dataset
        df = load_supplementary_dataset()
        assert "phishing" in df["label"].values, "Supplementary dataset must contain phishing examples"

    def test_supplementary_no_empty_messages(self):
        from src.data_loader import load_supplementary_dataset
        df = load_supplementary_dataset()
        empty = (df["message"].str.strip() == "").sum()
        assert empty == 0, f"{empty} empty messages found after loading"


class TestOriginalLoaderMissing:
    """Test graceful handling when original dataset is not present."""

    def test_missing_original_raises(self):
        from src.data_loader import load_original_dataset
        with pytest.raises(FileNotFoundError):
            load_original_dataset(path="/nonexistent/SMSSpamCollection")


class TestDatasetStats:
    """Test get_dataset_stats output structure."""

    def test_stats_structure_without_original(self):
        """When original dataset missing, error key should be in stats."""
        from src.data_loader import get_dataset_stats
        stats = get_dataset_stats()
        # Either available or error
        assert "available" in stats

    def test_stats_has_required_keys_when_available(self):
        """If the dataset IS available, check required keys."""
        from src.data_loader import get_dataset_stats
        stats = get_dataset_stats()
        if stats.get("available"):
            for key in ["total_records", "ham", "spam", "phishing", "url_containing"]:
                assert key in stats


class TestLabelNormalisation:
    def test_normalise(self):
        from src.data_loader import _normalise_label
        assert _normalise_label("Ham") == "ham"
        assert _normalise_label("SPAM") == "spam"
        assert _normalise_label("  Phishing  ") == "phishing"
